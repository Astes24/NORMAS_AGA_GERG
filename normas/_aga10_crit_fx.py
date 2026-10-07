# -*- coding: utf-8 -*-
"""
normas/_aga10_crit_fx.py
=========================
Critical Flow Factor (C*) de AGA-10 en Python puro, port FIEL del solver de FlowXpert:
`AGA10::crit` + `CTherm::HS_Mode` de libFXLibrary.so (decompilados con Ghidra el 2026-10-06,
ANALISIS_GHIDRA_FLOWXPERT/aga10_so_decomp.c y aga10_CTherm_decomp.c). Son las rutinas del codigo de
ejemplo del AGA Report No. 10 (Therm.cpp / Detail.cpp), no un algoritmo propio de ABB.

[C-34] Reemplaza al porte anterior (`_aga10_puro_python.py`), que usaba semillas y criterios propios y
difería de FlowXpert hasta ~1e-3 en C*. Las propiedades H, S, W, densidad y Z salen del motor propio
(AGA8-DETAIL + gas ideal del AGA Report 10, `AGA_10._termicas_aga10`), iguales a las de FlowXpert.

Algoritmo (literal del binario):
  crit:   estado de flujo (H, S, W, rho, Z); v0 = velocidad inicial (0);
          dE = 0.5*(W_flujo^2 - v0^2); hasta 99 veces: HS_Mode(H_flujo - dE, S_flujo) partiendo del estado
          actual; dE_nuevo = 0.5*(W*^2 - v0^2); parar si |dE - dE_nuevo| < 1 J/kg.
          C* = W* * rho* / sqrt(rho_flujo * P_flujo[Pa] * Z_flujo).
  HS_Mode(H_obj, S_obj): secante externa en T (T0, T0+10; T <= 1.5*T0; si T <= 0.67*T0 se toma T+10),
          secante interna en P (P0, 0.1*P0; P en [0.1*P0, 2*P0]) con P0 la presion del estado inicial;
          criterios: |cambio del residuo| / objetivo < 0.001 en S (interno) y en H (externo, desde la
          2a vuelta); maximo 100 iteraciones en cada nivel.
"""
import math

from .AGA_8 import DensityDetail, PropertiesDetail

_TOL = 0.001          # DAT_00237f88
_DT = 10.0            # DAT_00237898
_FP_MIN = 0.1         # DAT_00237890
_FP_MAX = 2.0
_FT_MAX = 1.5         # DAT_00237b60
_FT_MIN = 0.67        # DAT_0023a7a0
_TOL_E = 1.0          # DAT_00237818, J/kg
_MAX = 100


def _div(a, b):
    """Division con la semantica IEEE del C++ original (a/0 -> +-inf, 0/0 -> NaN) en vez de excepcion."""
    try:
        return a / b
    except ZeroDivisionError:
        if a == 0.0 or a != a:
            return float("nan")
        return math.copysign(math.inf, a) * math.copysign(1.0, b)


class _Estado:
    """Equivalente al struct de AGA10: T [K], P [kPa] y las propiedades del ultimo CTherm::run."""

    def __init__(self, composicion, x, T, P_kPa):
        self.comp, self.x, self.T, self.P = composicion, x, T, P_kPa
        self.run()

    def run(self):
        from .AGA_10 import _termicas_aga10
        D, _ierr, _ = DensityDetail(self.T, self.P, self.x)
        prop = PropertiesDetail(self.T, D, self.x)
        t = _termicas_aga10(self.comp, self.T, self.P, prop)
        self.H = t["H"] * 1000.0          # J/kg
        self.S = t["S"] * 1000.0          # J/(kg K)
        self.W = t["W"]                   # m/s
        self.rho = D * prop["Mm_g_mol"]   # kg/m3
        self.Z = prop["Z"]
        # CTherm::run devuelve error si la densidad no es valida (CDetail::Run marca 0x232b con Z <= 0)
        self.valido = D > 0.0 and self.Z > 0.0


def _hs_mode(e, H_obj, S_obj):
    """CTherm::HS_Mode(param_5=true). Modifica e.T / e.P. Devuelve True si convergio."""
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
            p_nuevo = p_nuevo if p_nuevo > p_min else p_min
            p_sig = p_nuevo if p_nuevo < p_max else p_max
            f0, p_ant = f1, p_act
        rH = e.H - H_obj
        if _div(abs(rH_prev - rH), H_obj) < _TOL and k != 0:
            return conv_s
        t_nuevo = _div(t_prev * rH - t_act * rH_prev, rH - rH_prev)
        t_nuevo = t_nuevo if t_nuevo < t_max else t_max
        rH_prev = rH
        if t_nuevo <= t_min:
            t_nuevo = _DT + t_act
            e.T = t_nuevo
            e.run()
            rH_prev = e.H - H_obj
        t_prev, t_act = t_act, t_nuevo
    return ok


def critical_flow_factor(composicion, x, T_K, P_kPa, v0=0.0):
    """AGA10::crit. Devuelve dict con critical_flow_factor, T_star, P_star_kPa, W_star, convergio."""
    e = _Estado(composicion, x, T_K, P_kPa)
    if not e.valido:
        return {"critical_flow_factor": 0.0, "T_star": None, "P_star_kPa": None, "W_star": None, "convergio": False}
    H_f, S_f, rho_f, Z_f, W_f = e.H, e.S, e.rho, e.Z, e.W
    dE = (W_f * W_f - v0 * v0) * 0.5
    convergio = True
    for _ in range(99):
        if not _hs_mode(e, H_f - dE, S_f):
            convergio = False
        e.run()
        if not e.valido:  # CTherm::run con error: crit aborta y C* queda en 0 (FlowXpert: Calculation error)
            return {"critical_flow_factor": 0.0, "T_star": e.T, "P_star_kPa": e.P, "W_star": None,
                    "convergio": False}
        dE_nuevo = (e.W * e.W - v0 * v0) * 0.5
        if abs(dE - dE_nuevo) < _TOL_E:
            break
        dE = dE_nuevo
    else:
        convergio = False
    cstar = (e.W * e.rho) / math.sqrt(rho_f * P_kPa * 1000.0 * Z_f)
    return {"critical_flow_factor": cstar, "T_star": e.T, "P_star_kPa": e.P, "W_star": e.W,
            "convergio": convergio and math.isfinite(cstar)}
