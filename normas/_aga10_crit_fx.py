# -*- coding: utf-8 -*-
"""
normas/_aga10_crit_fx.py
=========================
[C-48, 2026-11-18] critical_flow_factor() usa ahora el port bit a bit de `normas/_aga10_fx.py`. Lo que sigue
(clase _Estado, _hs_mode, _critical_flow_factor_c42) es el porte C-42, conservado solo como referencia/trazas.

Critical Flow Factor (C*) de AGA-10 en Python puro, port FIEL del solver de FlowXpert:
`AGA10::crit` + `CTherm::HS_Mode` + `CTherm::run` + `CDetail::Run/braket/ddetail` de libFXLibrary.so
(decompilados con Ghidra, ANALISIS_GHIDRA_FLOWXPERT/aga10_so_decomp.c, aga10_CTherm_decomp.c y
aga10_CDetail_decomp.c). Son las rutinas del codigo de ejemplo del AGA Report No. 10 (Therm.cpp /
Detail.cpp), no un algoritmo propio de ABB. Constantes leidas del binario (DAT_..., base Ghidra 0x10000).

[C-34] Reemplazo del porte anterior (`_aga10_puro_python.py`).
[C-42, 2026-11-18] Tres diferencias con FlowXpert corregidas:
  1. `AGA10::crit` NO mira el retorno de `HS_Mode` ni marca error si se agotan sus 99 vueltas: solo aborta
     (FlowXpert: "Calculation error") cuando `CTherm::run` falla, y `CTherm::run` solo falla si la densidad
     molar que deja `CDetail::Run` es <= 0. Antes este modulo marcaba `convergio=False` en ambos casos y
     `AGA_10.py` lanzaba error donde FlowXpert da un numero (ej. composicion Default 400 K / 50000 kPa).
  2. La densidad de cada estado sale ahora de `CDetail::braket` + `CDetail::ddetail` (busqueda por
     intervalos + Brent, tolerancia 1e-6, como FlowXpert) y no de `DensityDetail` (Newton de AGA8-2017):
     en estados lejanos que visita el solver las dos pueden dar raices distintas, o una densidad 0
     (FlowXpert: error) donde Newton devolvia la de gas ideal.
  3. Cache de `CDetail::Run`: los coeficientes que dependen de T (`CDetail::temp`) solo se recalculan si T
     cambio mas de 0.001 K, y la densidad solo si P cambio mas de 0.001 Pa (o si se recalculo `temp`).
     Con pasos de T menores a 0.001 K FlowXpert usa coeficientes "viejos"; se replica (en las derivadas en
     T la parte del virial B se deriva en la T vieja y el resto en la T actual, verificado contra el .xll).
  4. H, S, Cp, Cv y W de cada estado se calculan como CTherm (CprCvrHS/H/S/run): parte residual por
     cuadratura de Gauss-Legendre de 10 puntos de dZ/dT sobre la densidad, no por derivadas analiticas de
     Helmholtz (difieren ~1e-9 a densidad alta, lo que basta para cambiar C* en la zona caotica).
La ecuacion de estado (coeficientes de AGA8-DETAIL) es la de `AGA_8.py`; el gas ideal, el de `AGA_10.py`.
Las salidas principales de AGA_10.py (Z, W, H, S... en la condicion de flujo) NO usan este modulo.

Algoritmo (literal del binario):
  crit:   estado de flujo (H, S, W, rho, Z); v0 = velocidad inicial (0);
          dE = 0.5*(W_flujo^2 - v0^2); hasta 99 veces: HS_Mode(H_flujo - dE, S_flujo) partiendo del estado
          actual; CTherm::run (si falla: error); dE_nuevo = 0.5*(W*^2 - v0^2); parar si |dE - dE_nuevo| < 1 J/kg.
          C* = W* * rho* / sqrt(rho_flujo * P_flujo[Pa] * Z_flujo).
  HS_Mode(H_obj, S_obj): secante externa en T (T0, T0+10; T <= 1.5*T0; si T <= 0.67*T0 se toma T+10),
          secante interna en P (P0, 0.1*P0; P en [0.1*P0, 2*P0]) con P0 la presion del estado inicial;
          criterios: |cambio del residuo| / objetivo < 0.001 en S (interno) y en H (externo, desde la
          2a vuelta); maximo 100 iteraciones en cada nivel.
"""
import math

from . import AGA_8 as _A8
from .AGA_8 import AlpharDetail, MolarMassDetail, R_DETAIL, xTermsDetail

_TOL = 0.001          # DAT_00237f88
_DT = 10.0            # DAT_00237898
_FP_MIN = 0.1         # DAT_00237890
_FP_MAX = 2.0
_FT_MAX = 1.5         # DAT_00237b60
_FT_MIN = 0.67        # DAT_0023a7a0
_TOL_E = 1.0          # DAT_00237818, J/kg
_MAX = 100

# CDetail (Detail.cpp del AGA Report 10), constantes del binario
_RGASKJ = 0.00831451  # DAT_00238108, kJ/(mol K)
_PA_A_MPA = 1e-6      # DAT_00237800
_TOL_CACHE = 0.001    # DAT_00237f88 (K y Pa)


def _div(a, b):
    """Division con la semantica IEEE del C++ original (a/0 -> +-inf, 0/0 -> NaN) en vez de excepcion."""
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0.0 or a != a:
            return float("nan")
        return math.copysign(math.inf, a) * math.copysign(1.0, b)


def _u_mezcla(x):
    """Parametro de energia de la mezcla U [K] (mismo calculo que xTermsDetail, que no lo devuelve)."""
    U = 0.0
    for i in range(1, 22):
        if x[i] > 0:
            U += x[i] * _A8.Ei25[i]
    U = U ** 2
    for i in range(1, 21):
        if x[i] > 0.0:
            for j in range(i + 1, 22):
                if x[j] > 0.0:
                    U += 2.0 * x[i] * x[j] * _A8.Uij5[i][j]
    return U ** 0.2


def _alphar(itau, T, Tc, D, xterms):
    """AlpharDetail con los coeficientes dependientes de T evaluados en Tc (cache de CDetail::temp) y R*T
    con la T actual. Con Tc == T es exactamente AlpharDetail."""
    if Tc == T:
        return AlpharDetail(itau, T, D, xterms)
    ar = AlpharDetail(itau, Tc, D, xterms)
    f = T / Tc
    for k in ((0, 0), (0, 1), (0, 2), (0, 3)):
        ar[k] *= f
    return ar


def _z(T, Tc, D, xterms):
    """CDetail::zdetail."""
    ar = _alphar(0, T, Tc, D, xterms)
    return 1.0 + ar[(0, 1)] / R_DETAIL / T


def _pdetail(T, Tc, D, xterms):
    """CDetail::pdetail: P [MPa] = Z * D * R * T."""
    return _z(T, Tc, D, xterms) * D * _RGASKJ * T


def _bvir(Tc, xterms):
    """Segundo coeficiente virial B [dm3/mol] (CDetail::bvir, evaluado en la T de CDetail::temp)."""
    Bs = xterms[4]
    return sum(Bs[n] * Tc ** (-_A8.un[n]) for n in range(1, 19))


def _braket(T, Tc, P, xterms, U, B):
    """CDetail::braket (FlowXpert.xll, comparaciones con la misma semantica NaN que el binario). P en MPa.
    Devuelve (estado, rhoL, rhoH, pL, pH, D): 9000 = intervalo encontrado; 0x232c = 200 iteraciones
    agotadas; 0x232d = P dejo de crecer (D = ultima densidad buena)."""
    rhomax = 1.0 / xterms[0]                     # 1/K^3
    if T > 1.2593 * U:                           # DAT_00238100
        rhomax = rhomax * 20.0
    videal = (T * _RGASKJ) / P
    if 0.167 * videal > abs(B):                  # DAT_00238110
        rho2 = 0.95 / (videal + B)               # DAT_00237f30
    else:
        rho2 = 1.15 / videal                     # DAT_00238118
    dl = rho2 / 20.0
    rho1 = p1 = 0.0
    code2 = False                                # estado 0x232e: se paso de rhomax
    for _ in range(200):
        if rho2 > rhomax and not code2:
            code2 = True
            dl = (P / (T * _RGASKJ)) / 20.0 + (rhomax - rho1) * 0.01   # DAT_00237bc0
            rho2 = dl + rho1
            continue
        p2 = _pdetail(T, Tc, rho2, xterms)
        if p2 > P:
            return 9000, rho1, rho2, p1, p2, 0.0
        if not p2 > p1:
            return 0x232d, None, None, None, None, rho1
        if code2:
            dl = dl * 2.0
        rho1, p1 = rho2, p2
        rho2 = rho2 + dl
    return 0x232c, None, None, None, None, rho2


def _ddetail(T, Tc, P, xterms, U, B):
    """CDetail::ddetail (Brent sobre el intervalo de braket), literal del .xll (orden de operaciones y
    semantica NaN). P en MPa. Devuelve D [mol/dm3]."""
    st, x1, x2, y1, y2, D = _braket(T, Tc, P, xterms, U, B)
    if st != 9000:
        return D
    y1 = y1 - P
    y2 = y2 - P
    delx = x1 - x2
    delprv = delx
    x3, y3 = x1, y1
    for _ in range(150):
        if y3 * y2 > 0.0:
            delx = x1 - x2
            x3, y3 = x1, y1
            delprv = delx
        if abs(y2) > abs(y3):
            x1, y1, x2, y2, x3, y3 = x2, y2, x3, y3, x2, y2
        delbis = (x3 - x2) * 0.5
        delmin = abs(x2) * 1e-7                  # DAT_00237ec0
        interpolado = False
        if not (delmin > abs(delprv)) and not (abs(y2) > abs(y1)):
            if x3 == x1:
                xden = y1 - y2
                xnum = (x2 - x1) * y2
            else:
                a_ = y3 - y1
                b_ = y1 - y2
                c_ = y2 - y3
                xden = -((b_ * c_) * a_)
                xnum = (((((y2 * x1) * y3) * c_) + (((y3 * x2) * y1) * a_)) + (((x3 * y1) * y2) * b_)) - xden * x2
            if abs(xden * delprv) > abs(xnum) * 2.0:
                delprv = delx
                delx = _div(xnum, xden)
                interpolado = True
        if not interpolado:
            delprv = delbis
            delx = delbis
        if P * 1e-6 > abs(y2) and abs(x2) * 1e-6 > abs(delx):      # DAT_00237800
            return delx + x2
        if delmin > abs(delx):
            delx = _div(delbis, abs(delbis)) * 1.0000009 * delmin   # DAT_00238130
            delprv = delx
        if ((delx + x2) - x3) * delx > 0.0:
            delx = delbis
            delprv = delbis
        x1, y1 = x2, y2
        x2 = x2 + delx
        y2 = _pdetail(T, Tc, x2, xterms) - P
    return x2


# Cuadratura de Gauss-Legendre de 10 puntos de CTherm (DAT_00330c40 nodos, DAT_00330c00 pesos)
_GL_X = (0.14887433898163122, 0.4333953941292472, 0.6794095682990244, 0.8650633666889845, 0.9739065285171717)
_GL_W = (0.29552422471475287, 0.26926671930999635, 0.21908636251598204, 0.1494513491505806, 0.06667134430868814)
_R_J = 8314.51        # DAT_0023a778, J/(kmol K)
_P_REF_PA = 101325.0  # DAT_002379a8


_TUN_CACHE = {}


def _tun(Tc):
    """Tc**(-u_n), n = 1..58 (solo cache de calculo, mismos valores)."""
    v = _TUN_CACHE.get(Tc)
    if v is None:
        if len(_TUN_CACHE) > 256:
            _TUN_CACHE.clear()
        v = [None] + [Tc ** (-_A8.un[n]) for n in range(1, 59)]
        _TUN_CACHE[Tc] = v
    return v


def _zterms(T, Tc, D, xterms):
    """Z, dZ/dT, d2Z/dT2 y D*dZ/dD de AGA8-DETAIL (CDetail::zdetail/dZdT/d2ZdT2/dZdD) a la densidad D.
    Coeficientes dependientes de T evaluados en Tc (cache de CDetail::temp). En las derivadas en T, la parte
    del segundo virial B (CDetail::bvir: B, dB/dT, d2B/dT2) se deriva en Tc y el resto (coeficientes C*_n)
    se divide por la T actual, como el binario (verificado contra FlowXpert.xll con T - Tc < 0.001 K)."""
    K3, G, Q, F, Bs, Csn = xterms
    un, bn, kn = _A8.un, _A8.bn, _A8.kn
    Dred = K3 * D
    Dknn = [1.0] * 10
    for n in range(1, 10):
        Dknn[n] = Dred * Dknn[n - 1]
    Expn = [1.0] + [math.exp(-Dknn[n]) for n in range(1, 5)]
    s1 = s2 = 0.0
    dB1 = dB2 = dC1 = dC2 = 0.0
    tuns = _tun(Tc)
    for n in range(1, 59):
        tun = tuns[n]
        tb = tc = t2 = 0.0
        if n <= 18:
            tb = Bs[n] * D * tun
            if n >= 13:
                tc = -Csn[n] * Dred * tun
        if n >= 13:
            s0n = Csn[n] * Dknn[bn[n]] * tun * Expn[kn[n]]
            bkd = float(bn[n]) - float(kn[n]) * Dknn[kn[n]]
            ckd = float(kn[n]) ** 2 * Dknn[kn[n]]
            tc += s0n * bkd
            t2 = s0n * (bkd * (bkd - 1.0) - ckd)
        s1 += tb + tc
        s2 += t2
        dB1 += un[n] * tb
        dB2 += un[n] * (un[n] + 1.0) * tb
        dC1 += un[n] * tc
        dC2 += un[n] * (un[n] + 1.0) * tc
    return 1.0 + s1, -dB1 / Tc - dC1 / T, dB2 / (Tc * Tc) + dC2 / (T * T), s1 + s2


def _termo_fx(comp, T, Tc, P_pa, D, x, xterms):
    """CTherm::CprCvrHS / H / S / run: H [J/kg], S [J/(kg K)], W [m/s], rho [kg/m3], Z, como FlowXpert
    (parte residual por cuadratura de dZ/dT sobre la densidad, no por derivadas analiticas de Helmholtz)."""
    from .AGA_10 import TABLA_GAS_IDEAL_AGA10, _gas_ideal_puro_aga10
    tot = sum(v for v in comp.values() if v)
    xi = {k: v / tot for k, v in comp.items() if v and k in TABLA_GAS_IDEAL_AGA10}
    cp0 = h0 = s0 = 0.0
    for n, f in xi.items():
        c, h, s = _gas_ideal_puro_aga10(TABLA_GAS_IDEAL_AGA10[n], T)
        cp0 += f * c
        h0 += f * h
        s0 += f * s
    s0 -= R_DETAIL * sum(f * math.log(f) for f in xi.values())
    Mm = MolarMassDetail(x)
    H0 = h0 * 1000.0 / Mm
    S0 = s0 * 1000.0 / Mm
    Z, dZdT, d2ZdT2, DdZdD = _zterms(T, Tc, D, xterms)
    # densidad masica con el Z de zdetail; luego CDetail::Run pone Z = 0 en el struct si Z <= 0 (0x232b)
    rho = _div(P_pa * _PA_A_MPA * Mm, Z * _RGASKJ * T)
    if not Z > 0.0:
        Z = 0.0
    iH = iS = iC = 0.0
    for xg, wg in zip(_GL_X, _GL_W):
        for r in ((1.0 + xg) * D * 0.5, D * (1.0 - xg) * 0.5):
            zr, dzr, d2zr, _ = _zterms(T, Tc, r, xterms)
            iH += _div(wg * dzr, r)
            iS += _div(((T * dzr + zr) - 1.0) * wg, r)
            iC += _div((d2zr * T + dzr + dzr) * wg, r)
    cv = cp0 - (iC * T * 0.5 * D + 1.0) * R_DETAIL
    a = dZdT * T + Z
    b = DdZdD + Z
    cp = _div(a * a, b) * R_DETAIL + cv
    H = _div(_R_J * T * ((Z - 1.0) - D * T * iH * 0.5), Mm) + H0
    lnz = math.log(Z) if Z > 0.0 else -math.inf
    S = S0 - _div((0.5 * iS * D + (math.log(P_pa / _P_REF_PA) - lnz)) * _R_J, Mm)
    w2 = b * _div(_div(cp, cv) * R_DETAIL * 1000.0 * T, Mm)
    W = math.sqrt(w2) if w2 >= 0.0 else float("nan")
    return H, S, W, rho, Z


class _Estado:
    """Equivalente al struct de AGA10 + DetailCache: T [K], P [kPa] y las propiedades del ultimo run."""

    def __init__(self, composicion, x, T, P_kPa):
        self.comp, self.x, self.T, self.P = composicion, x, T, P_kPa
        self._xt = xTermsDetail(x)
        self._U = _u_mezcla(x)
        self._Tc = None        # T de la ultima llamada a CDetail::temp
        self._B = None
        self._T_cache = None   # DetailCache+0x78 / +0x70 (T [K] y P [Pa] del ultimo ddetail)
        self._P_cache = None
        self._D = 0.0
        self.run()

    def run(self):
        """CDetail::Run + propiedades de CTherm (H, S, W). `valido` = CTherm::run sin error (densidad > 0)."""
        T = self.T
        P_pa = self.P * 1000.0
        recalc = self._T_cache is None
        if recalc or abs(T - self._T_cache) > _TOL_CACHE:
            self._Tc = T
            self._B = _bvir(T, self._xt)
            recalc = True
        if recalc or abs(P_pa - self._P_cache) > _TOL_CACHE:
            self._D = _ddetail(T, self._Tc, P_pa * _PA_A_MPA, self._xt, self._U, self._B)
            self._T_cache, self._P_cache = T, P_pa
        D = self._D
        self.H, self.S, self.W, self.rho, self.Z = _termo_fx(self.comp, T, self._Tc, P_pa, D, self.x, self._xt)
        # CTherm::run devuelve error solo si la densidad molar de CDetail::Run es <= 0 (DAT_002377d8 = 0)
        self.valido = D > 0.0


def _hs_mode(e, H_obj, S_obj):
    """CTherm::HS_Mode(param_5=true). Modifica e.T / e.P. El valor devuelto (True si convergio) es solo
    informativo: AGA10::crit no lo usa."""
    P0, T0 = e.P, e.T
    p_max, p_min = 2.0 * P0, _FP_MIN * P0
    t_max, t_min = _FT_MAX * T0, _FT_MIN * T0
    t_prev, t_act = T0, T0 + _DT
    e.run()
    rH_prev = e.H - H_obj
    ok = False
    for k in range(_MAX):
        e.T, e.P = t_act, P0
        e.run()
        f0 = e.S - S_obj
        p_ant, p_sig = P0, _FP_MIN * P0
        conv_s = False
        for _ in range(_MAX):
            p_act = p_sig
            e.P = p_act
            e.run()
            f1 = e.S - S_obj
            if _div(abs(f0 - f1), S_obj) < _TOL:
                conv_s = True
                break
            p_nuevo = _div(p_ant * f1 - p_act * f0, f1 - f0)
            # clamps como el .xll (comisd/jb): un NaN pasa sin recortar
            p_nuevo = p_min if p_min >= p_nuevo else p_nuevo
            p_sig = p_max if p_nuevo >= p_max else p_nuevo
            f0, p_ant = f1, p_act
        rH = e.H - H_obj
        if _div(abs(rH_prev - rH), H_obj) < _TOL and k != 0:
            return conv_s
        t_nuevo = _div(t_prev * rH - t_act * rH_prev, rH - rH_prev)
        t_nuevo = t_max if t_nuevo >= t_max else t_nuevo
        rH_prev = rH
        if t_nuevo <= t_min:
            t_nuevo = _DT + t_act
            e.T = t_nuevo
            e.run()
            rH_prev = e.H - H_obj
        t_prev, t_act = t_act, t_nuevo
    return ok


def _critical_flow_factor_c42(composicion, x, T_K, P_kPa, v0=0.0):
    """[Historico C-42, ya no se usa en el calculo: ver critical_flow_factor()] AGA10::crit. Devuelve dict con critical_flow_factor, T_star, P_star_kPa, W_star, error y convergio.

    error=True solo cuando FlowXpert da "Calculation error": CTherm::run falla (densidad <= 0) en el estado
    de flujo o en algun estado intermedio; critical_flow_factor queda en 0.0 (campo sin escribir en el binario).
    Si no hay error se devuelve el C* que calcula FlowXpert aunque HS_Mode no haya convergido o se hayan
    agotado las 99 vueltas (convergio=False solo informa eso; FlowXpert no lo usa).
    """
    e = _Estado(composicion, x, T_K, P_kPa)
    if not e.valido:
        return {"critical_flow_factor": 0.0, "T_star": None, "P_star_kPa": None, "W_star": None,
                "error": True, "convergio": False}
    H_f, S_f, rho_f, Z_f, W_f = e.H, e.S, e.rho, e.Z, e.W
    dE = (W_f * W_f - v0 * v0) * 0.5
    convergio = True
    for _ in range(99):
        if not _hs_mode(e, H_f - dE, S_f):
            convergio = False
        e.run()
        if not e.valido:  # CTherm::run con error: crit aborta (FlowXpert: Calculation error)
            return {"critical_flow_factor": 0.0, "T_star": e.T, "P_star_kPa": e.P, "W_star": None,
                    "error": True, "convergio": False}
        dE_nuevo = (e.W * e.W - v0 * v0) * 0.5
        if _TOL_E > abs(dE - dE_nuevo):   # .xll: con NaN NO sale (sigue hasta las 99 vueltas)
            break
        dE = dE_nuevo
    else:
        convergio = False
    arg = rho_f * P_kPa * 1000.0 * Z_f
    cstar = _div(e.W * e.rho, math.sqrt(arg) if arg >= 0.0 else float("nan"))
    return {"critical_flow_factor": cstar, "T_star": e.T, "P_star_kPa": e.P, "W_star": e.W,
            "error": False, "convergio": convergio and math.isfinite(cstar)}


# [C-48, 2026-11-18] Camino de calculo vigente: port bit a bit del binario (`normas/_aga10_fx.py`).
_SLOT_FX = {"Metano": 0, "Nitrogeno": 1, "CO2": 2, "Etano": 3, "Propano": 4, "Agua": 5, "H2S": 6, "Hidrogeno": 7,
            "CO": 8, "Oxigeno": 9, "Isobutano": 10, "n-Butano": 11, "Isopentano": 12, "n-Pentano": 13,
            "n-Hexano": 14, "n-Heptano": 15, "n-Octano": 16, "n-Nonano": 17, "n-Decano": 18, "Helio": 19,
            "Argon": 20}


def fracciones_fx(composicion):
    """21 fracciones molares en el orden del struct de FlowXpert, normalizadas como el oraculo (v / suma)."""
    tot = sum(composicion.values())
    f = [0.0] * 21
    for nombre, v in composicion.items():
        if nombre in _SLOT_FX and v:
            f[_SLOT_FX[nombre]] = v / tot
    return f


def critical_flow_factor(composicion, x=None, T_K=None, P_kPa=None, v0=0.0, Tb_K=273.15, Pb_kPa=0.0):
    """AGA10::crit de FlowXpert, bit a bit (C-48): `_aga10_fx.crit` reproduce AGA10::crit, CTherm y CDetail
    (AGA8-1994 tal como esta compilado en FlowXpert.xll, con su exp de MSVCR110), incluida la zona caotica de
    alta presion donde el valor no tiene sentido fisico (decision del usuario: igual a FlowXpert).

    Devuelve dict con critical_flow_factor, T_star, P_star_kPa, W_star, error y convergio. error=True solo
    cuando FlowXpert da "Calculation error" (CTherm::run falla: densidad <= 0); critical_flow_factor queda en
    0.0. `x` se acepta por compatibilidad y no se usa (las fracciones se toman de `composicion`)."""
    from . import _aga10_fx
    st, m = _aga10_fx.crit(fracciones_fx(composicion), T_K, P_kPa * 1000.0, Tb_K, Pb_kPa * 1000.0, v0)
    if st:
        return {"critical_flow_factor": 0.0, "T_star": None, "P_star_kPa": None, "W_star": None,
                "error": True, "convergio": False}
    cst = m.s[0x170 >> 3]
    return {"critical_flow_factor": cst, "T_star": m.T_star, "P_star_kPa": m.P_star_Pa / 1000.0,
            "W_star": m.W_star, "error": False, "convergio": math.isfinite(cst)}
