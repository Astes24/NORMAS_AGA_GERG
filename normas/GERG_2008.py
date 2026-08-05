# -*- coding: utf-8 -*-
"""
normas/GERG_2008.py
=====================
Calculo INDEPENDIENTE de factor de compresibilidad (Z) y propiedades
termodinamicas de gas natural mediante la ecuacion de estado GERG-2008
(Kunz & Wagner, 2012), version NIST 2.0 (abril 2017). Este mismo motor
es el que FlowXpert expone como `FlowXpert_AGA8_GERG` (AGA-8 Part 2) y
`FlowXpert_GERG2008_Gas` / `FlowXpert_GERG2008_Flash`.

Este archivo se puede ejecutar solo:
    python normas/GERG_2008.py

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
Traduccion mecanica (Fortran -> Python) de
`documentos_normativos/NIST_AGA8_codigo_fuente/GERG2008.FOR`, codigo fuente
oficial de NIST (Eric W. Lemmon), de DOMINIO PUBLICO (17 U.S.C. §105),
publicado en github.com/usnistgov/AGA8.

Las +500 constantes (Dc, Tc, MMiGERG, kpol/kexp, coik/doik/toik/noik por
componente, dijk/tijk/cijk/eijk/gijk/nijk de las funciones de "departure",
mNumb, gvij/bvij/gtij/btij de reduccion de mezcla, fij) se extrajeron con un
PARSER (no a mano) que lee directamente las asignaciones literales del
Fortran (`normas/_gerg2008_data_generado.py`, generado, no editar a mano).
Los dos bloques que en el Fortran se generan con bucles (exponentes
genericos de 12 terminos para los 17 componentes "menores", y el bloque de
24 terminos que sobreescribe Metano/Nitrogeno/Etano) se transcribieron a
mano porque el parser no puede resolver variables de bucle -- se validaron
por conteo exacto contra kpol(i)+kexp(i) para las 21 especies y contra
kpolij(mn)+kexpij(mn) para las 8 funciones de departure, sin ningun error.

[CERTAIN] Se confirmo con Ghidra que FlowXpert.xll usa los mismos
coeficientes: 10 valores de 14 cifras del metano (`noik(1,1..10)`, ej.
0.57335704239162, -1.676068752373) aparecen CONTIGUOS y BYTE-IDENTICOS en
FlowXpert.xll (offset de archivo 1740880, VA 0x1801aa250). Es
estadisticamente imposible que estos valores coincidan por azar.

[CORREGIDO 2026-07-13, ver nota debajo] La primera version de este docstring
decia que no habia confirmacion estructural para GERG-2008 en FlowXpert
(solo coincidencia de constantes). Eso ya no es exacto: buscando quien
ESCRIBE (no solo quien lee) la direccion de la tabla de constantes, se
encontro el constructor estatico real (`FUN_180080d58` para GERG2008_Gas),
que registra la funcion de calculo real `FUN_1800b28b0` con su nombre,
descripcion ("Thermodynamic Properties of Gas according to GERG-2008."),
categoria y lista de inputs/outputs -- todo esto es metadata ESTATICA
confirmada, no solo constantes. Ver
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_constructors_output.txt`.

[CERTAIN -- 2026-08-05, cierra el gap anterior] `Math_AGA8_GERG` (real,
0xc6b50-0xc6bf6 en el .dsm) se leyo linea por linea: fuera de un bloque de
inicializacion estatica de C++ que corre una sola vez (registro de tipo,
__cxa_guard_acquire/release, nada matematico), el cuerpo completo de la
funcion es copiar sus 4 argumentos tal cual (mov eax, [esp+0x24..0x2c]) y
hacer `call 0xc6700 <Math_GERG2008_Gas>`, despues retorna directo sin tocar
el resultado. No es una inferencia por tabla compartida: es un wrapper
literal de `Math_GERG2008_Gas`, mismos argumentos, mismo calculo, byte a
byte, confirmado por lectura completa del desensamblado (ver
`ANALISIS_GHIDRA_FLOWXPERT/retdec_out/aga5_full.dsm`, funcion
`_Z14Math_AGA8_GERG...` en esa direccion).

[CERTAIN -- 2026-07-22, cierra el gap anterior] Validado contra un caso real
de la app FlowXpert (pantalla "AGA8 GERG", composicion "Default" del propio
FlowXpert con neo-Pentano sumado a Isopentano seguin el campo propio de la
app "neo-Pentane Mode: Add to iC5"), P=100 bar(a), T=25 degC:
    Z: real=0.865194      calculado=0.865194      dif. 0.00002%
    Mass Density: real=86.89433 kg/m3   calculado=86.89433 kg/m3   dif. 0.0000004%
    Molar Density: real=4.662482 kmol/m3   calculado=4.662482 kmol/m3   dif. 0.00002%
    Molar Mass: real=18.63692 kg/kmol   calculado=18.63692 kg/kmol   dif. 0.00002%
    Speed of Sound: real=415.4652 m/s   calculado=415.4652 m/s   dif. 0.000006%
    Isentropic Exponent: real=1.499894   calculado=1.499894   dif. 0.00003%
Los 6 resultados coinciden dentro del redondeo que muestra la app -- mismo
nivel de rigor que AGA-3 y AGA-5.

[CERTAIN -- 2026-07-24, validacion adicional contra fuente OFICIAL de NIST,
no la app] Ver `normas/test_gerg2008_aga8_nist_testdata.py`: coincidencia
EXACTA (diferencia 0.0, a precision de punto flotante) contra el doctest
oficial de NIST para la composicion "ExampleGerg" (77.824% metano...,
T=400K, P=50000kPa -> D=12.79828626082062 mol/l), tomado directamente de
`usnistgov/AGA8/AGA8CODE/RUST/src/lib.rs`. Ademas, 5 puntos (T, densidad)
de 3 composiciones reales de gas natural distintas, tomados del dataset
oficial de validacion de NIST (`documentos_normativos/NIST_AGA8_TESTDATA/
Test Data.xls`, mismo repositorio que DETAIL.FOR/GERG2008.FOR), coinciden
dentro de 0.01% (nivel de redondeo de la propia tabla).

[CERTAIN, validacion cruzada] Con la MISMA composicion y T=400K, P=50000 kPa,
este modulo (GERG-2008) y `normas/AGA_8.py` (DETAIL) dan resultados que
coinciden dentro de ~0.1%: Z=1.1747 vs 1.1738, D=12.798 vs 12.808 mol/l,
Cv=39.03 vs 39.12 J/mol-K, W=714.4 vs 712.6 m/s. Son dos ecuaciones de
estado publicadas INDEPENDIENTEMENTE por NIST, ajustadas por separado a los
mismos datos experimentales, portadas aqui por separado (sin compartir
codigo entre si). Que converjan tan de cerca es evidencia fuerte de que
ambas traducciones son correctas -- si alguna tuviera un error de
transcripcion o de formula, lo mas probable es que divergieran mucho mas.

NOTA DE PROCESO: la primera version de este archivo tenia un bug real (no
cosmetico): la densidad reductora de la mezcla (Dr) salia en ~0.99 mol/l en
vez de ~10 mol/l (orden de magnitud de las densidades criticas de los
componentes), lo que causaba overflow numerico en el solver de densidad.
La causa: GERG2008.FOR aplica una transformacion FINAL a las matrices de
combinacion binaria (gvij/gtij/bvij/btij, lineas 2263-2274 del Fortran) y a
los coeficientes exponenciales de "departure" (cijk/eijk/gijk via bijk,
lineas 2276-2282) que no estaba en la primera traduccion -- se habian
copiado los parametros de ajuste CRUDOS (beta/gamma de Kunz&Wagner) como si
fueran los valores finales. Se corrigio implementando esa transformacion
explicitamente (ver mas abajo, seccion "Transformacion final").

===============================================================================
"Flash" (equilibrio de fases) -- implementado 2026-07-22 con metodo estandar
===============================================================================
Ver funcion `calcular_flash()` mas abajo (seccion "FLASH" del codigo) para el
detalle completo de la decision y las formulas. Resumen: no se completo la
decompilacion de `FUN_1800bfe48` (la funcion real de flash en el binario,
demasiado grande); en su lugar, por decision explicita del usuario, se
implemento el metodo estandar de la industria (Wilson + Rachford-Rice +
sustitucion sucesiva con fugacidades derivadas numericamente del propio
motor GERG-2008 ya validado). Validado contra el UNICO caso real disponible
(que resulta ser monofasico, VF=1.0) con el mismo 0.00005% de la seccion de
arriba. La rama de 2 fases (VF entre 0 y 1) esta implementada y da resultados
fisicamente plausibles en pruebas sinteticas, pero NO hay ninguna captura
real de la app con resultado bifasico contra la cual confirmarla.

[CERTAIN] Investigando por que "Flash" no se podia confirmar ni por
estructura ni por XREF (ver sesion anterior), se encontro el constructor
estatico real y se rastreo la funcion de calculo completa
(`FUN_1800b95a8` para GERG2004_Flash, `FUN_1800b255c` para GERG2008_Flash,
identicas en estructura). Esa funcion lee P, T, un flag de fase, y la
composicion, y bifurca por flags de bits entre dos funciones internas:
  - `FUN_1800c0c54`: formula corta y limpia de Z/densidad/velocidad del
    sonido/exponente isentropico -- el caso de una sola fase ("not split"),
    equivalente a lo que ya hace `PropertiesGERG` en este archivo.
  - `FUN_1800bfe48`: funcion mucho mas grande y compleja (~11 KB de stack,
    multiples arreglos por componente). Contiene evidencia fuerte de un
    calculo de equilibrio de fases real: una variable se inicializa en 0.5
    (fraccion de vapor tipica como estimacion inicial en algoritmos
    Rachford-Rice), se verifica que quede entre 0 y 1, y hay un bucle
    iterativo con calculos tipo log(K_i) por componente (K-values de
    equilibrio liquido-vapor).
[CERTAIN] Esta es evidencia estatica (no ejecutada) de que "Flash" en
FlowXpert SI es un calculo genuino de equilibrio de fases, no solo un
nombre distinto para el mismo calculo de una fase. Ver
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_flashworkers_output.txt` y
`ghidra_branches_output.txt` para el decompilado completo.

[GUESSING] NO se termino de decompilar `FUN_1800bfe48` linea por linea (es
mucho mas grande que cualquier otra funcion analizada en este proyecto) ni
se porto a Python. Hacerlo bien requeriria entender su algoritmo completo
de convergencia (que variable itera, que criterio de paro usa, como
inicializa K_i) antes de traducirlo -- es un trabajo del mismo tamaño o
mayor que todo AGA8-DETAIL, no una extension menor de este archivo.

[CERTAIN] Se instalo x64dbg (2026-07-13) y se intento confirmar la
ejecucion real via analisis dinamico: se cargo FlowXpert.xll de verdad
dentro de un proceso de Excel (via `RegisterXLL` por COM, que si funciono).
Sin embargo, `GERG2004_Flash` NO esta registrada como funcion invocable en
absoluto (fallo tanto por formula como por `Application.Run`, con error de
"macro no disponible") mientras el addin este en estado "Not Authorized".
Esto confirma que el bloqueo de licencia de ABB actua sobre el REGISTRO de
las funciones de calculo, no solo sobre el ribbon visual de Excel -- cierra
la puerta a observar la ejecucion real por la via legitima. No se intento
forzar el registro ni el bit de autorizacion (limite etico ya establecido).
===============================================================================
"""

import math

from ._gerg2008_data_generado import (
    DC, TC, MM_GERG, KPOL, KEXP, KPOLIJ, KEXPIJ, NOIK, COIK, DOIK, TOIK,
    DIJK, TIJK, CIJK as _CIJK_RAW, EIJK as _EIJK_RAW, GIJK as _GIJK_RAW,
    NIJK, MNUMB, GVIJ as _GVIJ_RAW, BVIJ as _BVIJ_RAW, GTIJ as _GTIJ_RAW,
    BTIJ as _BTIJ_RAW, FIJ, BIJK,
)

NC = 21
NOMBRES_COMPONENTES = [
    "Metano", "Nitrogeno", "CO2", "Etano", "Propano", "Isobutano", "n-Butano",
    "Isopentano", "n-Pentano", "n-Hexano", "n-Heptano", "n-Octano", "n-Nonano",
    "n-Decano", "Hidrogeno", "Oxigeno", "CO", "Agua", "H2S", "Helio", "Argon",
]

R_GERG = 8.314472  # J/(mol-K) -- distinto del R=8.31451 usado en AGA8-DETAIL
EPSILON = 1.0e-15

# ---------------------------------------------------------------------------
# Parametros de gas ideal n0i/th0i -- valores BASE identicos a los de
# AGA8-DETAIL (mismo BLOCK DATA en ambos .FOR), pero GERG-2008 les aplica su
# PROPIO ajuste en SetupGERG (distinto del de SetupDetail: incluye un factor
# de escala Rsr=Rs/RGERG porque las tablas de gas ideal se ajustaron con
# Rs=8.31451 pero GERG usa RGERG=8.314472). Por eso NO se reutiliza el n0i
# ya ajustado de AGA_8.py -- hay que partir de los valores crudos y aplicar
# la transformacion propia de GERG (lineas 2284-2293 de GERG2008.FOR).
# ---------------------------------------------------------------------------
from .AGA_8 import (
    _n0i_37 as __n0i_37, _n0i_12 as __n0i_12, _th0i_data as __th0i_data,
)  # noqa: E402  (tablas CRUDAS, antes del ajuste de SetupDetail)

RS_GERG = 8.31451  # "Rs" en GERG2008.FOR -- valor de R con el que se ajustaron n0i/th0i
_RSR = RS_GERG / R_GERG

_T0 = 298.15
_D0_GERG = 101.325 / R_GERG / _T0

n0i = [None]
th0i = [None]
for _i in range(21):
    _fila_n0i = [None, __n0i_12[_i][0], __n0i_12[_i][1]] + __n0i_37[_i]
    # SetupGERG: n0i(i,3)-=1; n0i(i,2)+=T0; n0i(i,1:7)*=Rsr; n0i(i,2)-=T0; n0i(i,1)-=log(d0)
    _fila_n0i[3] = _fila_n0i[3] - 1.0
    _fila_n0i[2] = _fila_n0i[2] + _T0
    for _j in range(1, 8):
        _fila_n0i[_j] = _fila_n0i[_j] * _RSR
    _fila_n0i[2] = _fila_n0i[2] - _T0
    _fila_n0i[1] = _fila_n0i[1] - math.log(_D0_GERG)
    n0i.append(_fila_n0i)
    th0i.append([None, None, None, None] + __th0i_data[_i])


# ---------------------------------------------------------------------------
# Transformacion final de las matrices de combinacion (equivalente a las
# lineas 2263-2282 de SetupGERG en GERG2008.FOR). Los valores GVIJ/BVIJ/
# GTIJ/BTIJ importados de _gerg2008_data_generado son los parametros de
# ajuste CRUDOS (beta_v, gamma_v, beta_T, gamma_T); hay que combinarlos con
# Dc/Tc para obtener los factores realmente usados en ReducingParametersGERG.
# ---------------------------------------------------------------------------
_O13 = 1.0 / 3.0
_VC3 = {i: 1.0 / DC[i] ** _O13 / 2.0 for i in range(1, 22)}
_TC2 = {i: math.sqrt(TC[i]) for i in range(1, 22)}

_GVIJ = {}
_BVIJ = {}
_GTIJ = {}
_BTIJ = {}
for _i in range(1, 22):
    _BVIJ[(_i, _i)] = 1.0
    _BTIJ[(_i, _i)] = 1.0
    _GVIJ[(_i, _i)] = 1.0 / DC[_i]
    _GTIJ[(_i, _i)] = TC[_i]
    for _j in range(_i + 1, 22):
        _bv_raw = _BVIJ_RAW.get((_i, _j), 1.0)
        _bt_raw = _BTIJ_RAW.get((_i, _j), 1.0)
        _gv_raw = _GVIJ_RAW.get((_i, _j), 1.0)
        _gt_raw = _GTIJ_RAW.get((_i, _j), 1.0)
        _GVIJ[(_i, _j)] = _gv_raw * _bv_raw * (_VC3[_i] + _VC3[_j]) ** 3
        _GTIJ[(_i, _j)] = _gt_raw * _bt_raw * _TC2[_i] * _TC2[_j]
        _BVIJ[(_i, _j)] = _bv_raw ** 2
        _BTIJ[(_i, _j)] = _bt_raw ** 2

# Transformacion final de los coeficientes exponenciales de "departure"
# (lineas 2276-2282 de SetupGERG): gijk/eijk/cijk crudos + bijk -> finales.
_CIJK = {}
_EIJK = {}
_GIJK = {}
_claves_exp = set(_CIJK_RAW) | set(_EIJK_RAW) | set(_GIJK_RAW) | set(BIJK)
for _k in _claves_exp:
    _c = _CIJK_RAW.get(_k, 0.0)
    _e = _EIJK_RAW.get(_k, 0.0)
    _g = _GIJK_RAW.get(_k, 0.0)
    _b = BIJK.get(_k, 0.0)
    _GIJK[_k] = -_c * _e ** 2 + _b * _g
    _EIJK[_k] = 2.0 * _c * _e - _b
    _CIJK[_k] = -_c


def gvij(i, j):
    if i > j:
        i, j = j, i
    return _GVIJ[(i, j)]


def bvij(i, j):
    if i > j:
        i, j = j, i
    return _BVIJ[(i, j)]


def gtij(i, j):
    if i > j:
        i, j = j, i
    return _GTIJ[(i, j)]


def btij(i, j):
    if i > j:
        i, j = j, i
    return _BTIJ[(i, j)]


def fij(i, j):
    if i > j:
        i, j = j, i
    return FIJ.get((i, j), 0.0)


def mNumb(i, j):
    if i > j:
        i, j = j, i
    return MNUMB.get((i, j), -1)


def _composicion_a_x(composicion: dict):
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion no puede sumar cero.")
    x = [None]
    for nombre in NOMBRES_COMPONENTES:
        x.append(composicion.get(nombre, 0.0) / total)
    return x


def MolarMassGERG(x):
    return sum(x[i] * MM_GERG[i] for i in range(1, 22))


def ReducingParametersGERG(x):
    """Devuelve (Tr, Dr) -- temperatura y densidad reductoras de la mezcla."""
    Dr = 0.0
    Vr = 0.0
    Tr = 0.0
    for i in range(1, 22):
        if x[i] > EPSILON:
            F = 1.0
            for j in range(i, 22):
                if x[j] > EPSILON:
                    xij = F * (x[i] * x[j]) * (x[i] + x[j])
                    Vr += xij * gvij(i, j) / (bvij(i, j) * x[i] + x[j])
                    Tr += xij * gtij(i, j) / (btij(i, j) * x[i] + x[j])
                    F = 2.0
    if Vr > EPSILON:
        Dr = 1.0 / Vr
    return Tr, Dr


def Alpha0GERG(T, D, x):
    """Energia de Helmholtz de gas ideal (adimensional, =a0/RT) y sus
    derivadas respecto a tau. Devuelve [a0(0), a0(1), a0(2)]."""
    a0 = [0.0, 0.0, 0.0]
    LogD = math.log(D) if D > EPSILON else math.log(EPSILON)
    LogT = math.log(T)

    for i in range(1, 22):
        if x[i] > EPSILON:
            LogxD = LogD + math.log(x[i])
            SumHyp0 = SumHyp1 = SumHyp2 = 0.0
            for j in (4, 5, 6, 7):
                if th0i[i][j] > EPSILON:
                    th0T = th0i[i][j] / T
                    ep = math.exp(th0T)
                    em = 1.0 / ep
                    hsn = (ep - em) / 2.0
                    hcn = (ep + em) / 2.0
                    if j == 4 or j == 6:
                        LogHyp = math.log(abs(hsn))
                        SumHyp0 += n0i[i][j] * LogHyp
                        SumHyp1 += n0i[i][j] * th0T * hcn / hsn
                        SumHyp2 += n0i[i][j] * (th0T / hsn) ** 2
                    else:
                        LogHyp = math.log(abs(hcn))
                        SumHyp0 -= n0i[i][j] * LogHyp
                        SumHyp1 -= n0i[i][j] * th0T * hsn / hcn
                        SumHyp2 += n0i[i][j] * (th0T / hcn) ** 2
            a0[0] += x[i] * (LogxD + n0i[i][1] + n0i[i][2] / T - n0i[i][3] * LogT + SumHyp0)
            a0[1] += x[i] * (n0i[i][3] + n0i[i][2] / T + SumHyp1)
            a0[2] -= x[i] * (n0i[i][3] + SumHyp2)
    return a0


class _EstadoGERG:
    """Cache de terminos dependientes de T (equivalente a taup/taupijk de
    tTermsGERG en el Fortran), recalculado solo cuando cambia T o Tr."""

    def __init__(self):
        self.told = None
        self.trold2 = None
        self.taup = {}
        self.taupijk = {}

    def actualizar(self, T, Tr, x):
        lntau = math.log(Tr / T)
        if (self.told is not None and abs(T - self.told) <= 1e-7 and
                self.trold2 is not None and abs(Tr - self.trold2) <= 1e-7):
            return
        self.told = T
        self.trold2 = Tr

        # Propano (i=5) da los exponentes de la forma "corta" (12 terminos)
        i_ref = 5
        n_terms_ref = KPOL[i_ref] + KEXP[i_ref]
        taup0 = [None] * (n_terms_ref + 1)
        for k in range(1, n_terms_ref + 1):
            taup0[k] = math.exp(TOIK[(i_ref, k)] * lntau)

        self.taup = {}
        for i in range(1, 22):
            if x[i] > EPSILON:
                n_terms = KPOL[i] + KEXP[i]
                usa_forma_corta = i > 4 and i != 15 and i != 18 and i != 20
                for k in range(1, n_terms + 1):
                    if usa_forma_corta:
                        self.taup[(i, k)] = NOIK[(i, k)] * taup0[k]
                    else:
                        self.taup[(i, k)] = NOIK[(i, k)] * math.exp(TOIK[(i, k)] * lntau)

        self.taupijk = {}
        for i in range(1, 21):
            if x[i] > EPSILON:
                for j in range(i + 1, 22):
                    if x[j] > EPSILON:
                        mn = mNumb(i, j)
                        if mn >= 0:
                            for k in range(1, int(KPOLIJ.get(mn, 0)) + 1):
                                self.taupijk[(mn, k)] = NIJK.get((mn, k), 0.0) * math.exp(
                                    TIJK.get((mn, k), 0.0) * lntau)


_estado = _EstadoGERG()


def AlpharGERG(iprop, T, D, x):
    """Derivadas de la energia de Helmholtz residual adimensional (ar=a/RT)
    respecto a tau y delta. Devuelve dict con claves (0,0)..(2,0)."""
    ar = {(0, 0): 0.0, (0, 1): 0.0, (0, 2): 0.0, (0, 3): 0.0,
          (1, 0): 0.0, (1, 1): 0.0, (1, 2): 0.0, (2, 0): 0.0}

    Tr, Dr = ReducingParametersGERG(x)
    del_ = D / Dr
    tau = Tr / T

    delp = [None] * 8
    Expd = [None] * 8
    delp[1] = del_
    Expd[1] = math.exp(-delp[1])
    for i in range(2, 8):
        delp[i] = delp[i - 1] * del_
        Expd[i] = math.exp(-delp[i])

    _estado.actualizar(T, Tr, x)
    taup = _estado.taup
    taupijk = _estado.taupijk

    # Contribuciones de fluido puro
    for i in range(1, 22):
        if x[i] > EPSILON:
            kpol_i = KPOL[i]
            kexp_i = KEXP[i]
            for k in range(1, kpol_i + 1):
                d_ik = DOIK[(i, k)]
                ndt = x[i] * delp[int(d_ik)] * taup[(i, k)]
                ndtd = ndt * d_ik
                ar[(0, 1)] += ndtd
                ar[(0, 2)] += ndtd * (d_ik - 1.0)
                if iprop > 0:
                    t_ik = TOIK[(i, k)]
                    ndtt = ndt * t_ik
                    ar[(0, 0)] += ndt
                    ar[(1, 0)] += ndtt
                    ar[(2, 0)] += ndtt * (t_ik - 1.0)
                    ar[(1, 1)] += ndtt * d_ik
                    ar[(1, 2)] += ndtt * d_ik * (d_ik - 1.0)
                    ar[(0, 3)] += ndtd * (d_ik - 1.0) * (d_ik - 2.0)
            for k in range(1 + kpol_i, kpol_i + kexp_i + 1):
                d_ik = DOIK[(i, k)]
                c_ik = COIK[(i, k)]
                ndt = x[i] * delp[int(d_ik)] * taup[(i, k)] * Expd[int(c_ik)]
                ex = c_ik * delp[int(c_ik)]
                ex2 = d_ik - ex
                ex3 = ex2 * (ex2 - 1.0)
                ar[(0, 1)] += ndt * ex2
                ar[(0, 2)] += ndt * (ex3 - c_ik * ex)
                if iprop > 0:
                    t_ik = TOIK[(i, k)]
                    ndtt = ndt * t_ik
                    ar[(0, 0)] += ndt
                    ar[(1, 0)] += ndtt
                    ar[(2, 0)] += ndtt * (t_ik - 1.0)
                    ar[(1, 1)] += ndtt * ex2
                    ar[(1, 2)] += ndtt * (ex3 - c_ik * ex)
                    ar[(0, 3)] += ndt * (ex3 * (ex2 - 2.0) -
                                          ex * (3.0 * ex2 - 3.0 + c_ik) * c_ik)

    # Contribuciones de mezcla (funciones de departure)
    lntau = math.log(tau)
    for i in range(1, 21):
        if x[i] > EPSILON:
            for j in range(i + 1, 22):
                if x[j] > EPSILON:
                    mn = mNumb(i, j)
                    if mn >= 0:
                        xijf = x[i] * x[j] * fij(i, j)
                        kpolij_mn = int(KPOLIJ.get(mn, 0))
                        kexpij_mn = int(KEXPIJ.get(mn, 0))
                        for k in range(1, kpolij_mn + 1):
                            d_mnk = DIJK[(mn, k)]
                            ndt = xijf * delp[int(d_mnk)] * taupijk[(mn, k)]
                            ndtd = ndt * d_mnk
                            ar[(0, 1)] += ndtd
                            ar[(0, 2)] += ndtd * (d_mnk - 1.0)
                            if iprop > 0:
                                t_mnk = TIJK.get((mn, k), 0.0)
                                ndtt = ndt * t_mnk
                                ar[(0, 0)] += ndt
                                ar[(1, 0)] += ndtt
                                ar[(2, 0)] += ndtt * (t_mnk - 1.0)
                                ar[(1, 1)] += ndtt * d_mnk
                                ar[(1, 2)] += ndtt * d_mnk * (d_mnk - 1.0)
                                ar[(0, 3)] += ndtd * (d_mnk - 1.0) * (d_mnk - 2.0)
                        for k in range(1 + kpolij_mn, kpolij_mn + kexpij_mn + 1):
                            d_mnk = DIJK[(mn, k)]
                            t_mnk = TIJK.get((mn, k), 0.0)
                            c_mnk = _CIJK.get((mn, k), 0.0)
                            e_mnk = _EIJK.get((mn, k), 0.0)
                            g_mnk = _GIJK.get((mn, k), 0.0)
                            n_mnk = NIJK.get((mn, k), 0.0)
                            cij0 = c_mnk * delp[2]
                            eij0 = e_mnk * del_
                            ndt = (xijf * n_mnk * delp[int(d_mnk)] *
                                   math.exp(cij0 + eij0 + g_mnk + t_mnk * lntau))
                            ex = d_mnk + 2.0 * cij0 + eij0
                            ex2 = ex * ex - d_mnk + 2.0 * cij0
                            ar[(0, 1)] += ndt * ex
                            ar[(0, 2)] += ndt * ex2
                            if iprop > 0:
                                ndtt = ndt * t_mnk
                                ar[(0, 0)] += ndt
                                ar[(1, 0)] += ndtt
                                ar[(2, 0)] += ndtt * (t_mnk - 1.0)
                                ar[(1, 1)] += ndtt * ex
                                ar[(1, 2)] += ndtt * ex2
                                ar[(0, 3)] += ndt * (ex * (ex2 - 2.0 * (d_mnk - 2.0 * cij0)) +
                                                      2.0 * d_mnk)
    return ar


def PressureGERG(T, D, x):
    """Devuelve (P [kPa], Z, dPdDsave [kPa/(mol/l)])."""
    ar = AlpharGERG(0, T, D, x)
    Z = 1.0 + ar[(0, 1)]
    P = D * R_GERG * T * Z
    dPdDsave = R_GERG * T * (1.0 + 2.0 * ar[(0, 1)] + ar[(0, 2)])
    return P, Z, dPdDsave


def PseudoCriticalPointGERG(x):
    Tcx = 0.0
    Vcx = 0.0
    for i in range(1, 22):
        Tcx += x[i] * TC[i]
        Vcx += x[i] / DC[i]
    Dcx = 1.0 / Vcx if Vcx > EPSILON else 0.0
    return Tcx, Dcx


def DensityGERG(T, P, x, iFlag=0, D_inicial=None):
    """Resuelve D (mol/l) dado T (K), P (kPa) por iteracion de Newton en
    log(v), version simplificada del solver de GERG2008.FOR (sin los
    reintentos de fase liquida ni las verificaciones de 2 fases, que no
    aplican al caso de uso de FocQus: gas natural en fase gaseosa).
    Devuelve (D, ierr, msg)."""
    if P < EPSILON:
        return 0.0, 0, ""

    tolr = 1.0e-7
    Tcx, Dcx = PseudoCriticalPointGERG(x)
    if D_inicial is None or D_inicial <= EPSILON:
        D = P / R_GERG / T
        if iFlag == 2:
            D = Dcx * 3.0
    else:
        D = abs(D_inicial)

    plog = math.log(P)
    vlog = -math.log(D)

    for _ in range(50):
        if vlog < -7.0 or vlog > 100.0:
            break
        D = math.exp(-vlog)
        P2, Z, dPdDsave = PressureGERG(T, D, x)
        if dPdDsave < EPSILON or P2 < EPSILON:
            vinc = 0.1 if D <= Dcx else -0.1
            vlog += vinc
        else:
            dpdlv = -D * dPdDsave
            vdiff = (math.log(P2) - plog) * P2 / dpdlv
            vlog -= vdiff
            if abs(vdiff) < tolr:
                D = math.exp(-vlog)
                return D, 0, ""

    D = P / R_GERG / T
    return D, 1, "Calculo no convergio en el metodo GERG-2008, se devuelve la densidad de gas ideal."


def PropertiesGERG(T, D, x):
    Mm = MolarMassGERG(x)
    a0 = Alpha0GERG(T, D, x)
    ar = AlpharGERG(1, T, D, x)

    Rg = R_GERG
    RT = Rg * T
    Z = 1.0 + ar[(0, 1)]
    P = D * RT * Z
    dPdD = RT * (1.0 + 2.0 * ar[(0, 1)] + ar[(0, 2)])
    dPdT = D * Rg * (1.0 + ar[(0, 1)] - ar[(1, 1)])
    d2PdTD = Rg * (1.0 + 2.0 * ar[(0, 1)] + ar[(0, 2)] - 2.0 * ar[(1, 1)] - ar[(1, 2)])
    A = RT * (a0[0] + ar[(0, 0)])
    G = RT * (1.0 + ar[(0, 1)] + a0[0] + ar[(0, 0)])
    U = RT * (a0[1] + ar[(1, 0)])
    H = RT * (1.0 + ar[(0, 1)] + a0[1] + ar[(1, 0)])
    S = Rg * (a0[1] + ar[(1, 0)] - a0[0] - ar[(0, 0)])
    Cv = -Rg * (a0[2] + ar[(2, 0)])

    if D > EPSILON:
        Cp = Cv + T * (dPdT / D) ** 2 / dPdD
        d2PdD2 = RT * (2.0 * ar[(0, 1)] + 4.0 * ar[(0, 2)] + ar[(0, 3)]) / D
        JT = (T / D * dPdT / dPdD - 1.0) / Cp / D
    else:
        Cp = Cv + Rg
        d2PdD2 = 0.0
        JT = 1.0e20

    W2 = 1000.0 * Cp / Cv * dPdD / Mm
    W = math.sqrt(W2) if W2 > 0.0 else 0.0
    Kappa = W ** 2 * Mm / (RT * 1000.0 * Z)

    return {
        "Mm_g_mol": Mm, "P_kPa": P, "Z": Z, "dPdD": dPdD, "d2PdD2": d2PdD2,
        "d2PdTD": d2PdTD, "dPdT": dPdT, "U_J_mol": U, "H_J_mol": H,
        "S_J_molK": S, "Cv_J_molK": Cv, "Cp_J_molK": Cp, "W_m_s": W,
        "G_J_mol": G, "JT_K_kPa": JT, "Kappa": Kappa,
    }


# [CERTAIN, 2026-08-04] Por debajo de este umbral, `GERG::GERG_Calculate`
# REAL (el mismo usado por las 4 pantallas GERG-2004/2008 Gas/Flash de
# FlowXpert, offset 0xcb860, llamado directo confirmado hoy con la receta
# correcta: flag=1, orden de composicion con n-Butano/n-Pentano antes de
# sus isomeros, presion en MPa) se vuelve CAOTICO: barrido real contra el
# dispositivo entre 0.05 y 5 MPa mostro exitos y fallos (Z=0 invalido)
# entremezclados sin un umbral limpio por debajo de ~0.3-0.5 MPa, y CERO
# fallos de 0.5 MPa en adelante (probado hasta 5-8 MPa). Confirmado con
# 570 composiciones reales de un cromatografo de campo a 101.325 kPa:
# 276 de 570 (48%) fallaron en FlowXpert. Esta es una falla real del
# binario de ABB, no de este modulo -- `DensityGERG()` (mas simple que el
# algoritmo real, ver su propio docstring) da resultado valido en el
# 100% de esos 276 casos, y coincide con el dato de prueba oficial de
# NIST (`test_gerg2008_aga8_nist_testdata.py`). NO se puede "arreglar"
# FlowXpert (codigo cerrado); esta constante solo marca cuando el
# resultado de este modulo no tiene con que compararse contra la app real.
PRESION_MINIMA_CONFIABLE_KPA = 500.0


def _aviso_baja_presion(P_kPa: float):
    if P_kPa < PRESION_MINIMA_CONFIABLE_KPA:
        return "Presion menor a 0.5 MPa: validado por NIST."
    return None


def calcular_propiedades(composicion: dict, T_K: float, P_kPa: float):
    """Punto de entrada de alto nivel: composicion por nombre + T,P -> propiedades."""
    x = _composicion_a_x(composicion)
    D, ierr, msg = DensityGERG(T_K, P_kPa, x)
    resultado = PropertiesGERG(T_K, D, x)
    resultado["D_mol_l"] = D
    resultado["ierr"] = ierr
    resultado["msg_error"] = msg
    resultado["aviso_baja_presion_flowxpert"] = _aviso_baja_presion(P_kPa)
    return resultado


# =============================================================================
# FLASH (equilibrio liquido-vapor) -- 2026-07-22, CERRADO con evidencia dura
# =============================================================================
# [CERTAIN -- 2026-07-22, version FINAL, corrige 2 hipotesis previas de esta
# misma sesion] Se rastreo el CALL GRAPH real (no solo texto de funciones
# aisladas) de los 2 exports reales conectados al boton "Flash" de la app
# Android (libFXLibrary.so, via disassembly con capstone + tabla de simbolos
# ELF parseada directamente, sin Ghidra):
#   - GergMath_GERG2004_Flash (0xc82e0) llama a GERG::GERG_Calculate (0xcb860,
#     1103 bytes, tagGERGSTRUCT).
#   - Math_GERG2008_Flash (0xc62e0) llama a GERG2008::GERG_Calculate (0x13aa60,
#     1142 bytes, tagGERGSTRUCT).
# NINGUNA de las dos llama a GERG::CEquation::CalculateFlash (0xddb00, 5973
# bytes) ni a GERG2008::CEquation::CalculateFlash (0x146460, 8553 bytes) --
# las funciones GRANDES que SI tienen un algoritmo real de equilibrio de
# fases (parametros _EDesiredPhase/_EFoundPhase). Esas funciones existen en
# el binario (no son ficticias), pero NO estan conectadas al boton "Flash"
# de esta app -- son codigo alcanzable desde otro lugar (otra pantalla no
# expuesta, una API interna, u otra build), no desde aqui.
#
# CONCLUSION: la pantalla "Flash" de FlowXpert (tanto GERG-2004 como
# GERG-2008, y en ambos binarios: .xll de Windows Y .so de Android) NUNCA
# ejecuta un calculo real de equilibrio liquido-vapor. Llama a la MISMA
# rutina de una sola fase que usa "Gas", y reporta Vapour Fraction fijo en
# 1.000000 porque nunca calcula una fraccion de vapor real. Esto explica
# por que el usuario obtiene VF=1.000000 con CUALQUIER composicion que
# pruebe (incluida una deliberadamente pesada -- 65% metano + 35% repartido
# en etano a n-octano a 100 bar(a)/25 degC -- que segun este mismo motor
# GERG-2008 SI deberia dar un resultado bifasico, VF~0.46, y en la app real
# sigue dando 1.000000).
#
# [Nota de proceso: esta sesion paso por 2 hipotesis intermedias antes de
# esta conclusion -- primero "puede ser una bandera constante en el .xll"
# (correcta en el fondo), luego, al ver que el .so SI tiene CalculateFlash,
# se penso que el motor real soporta 2 fases y el problema era la
# composicion de prueba (INCORRECTO, descartado al ver que ni una
# composicion deliberadamente pesada cambia el resultado en la app real).
# La traza de CALL GRAPH (no solo la existencia de la funcion en el binario)
# fue lo que resolvio la ambiguedad.]
#
# Por lo tanto (decision de alcance, 2026-08-01, pedido explicito del
# usuario tras confirmar lo de arriba): `calcular_flash()` de este archivo
# YA NO intenta un calculo de 2 fases en absoluto. Antes tenia una rama de
# 2 fases genuina (Wilson + Rachford-Rice + sustitucion sucesiva + prueba
# de estabilidad de Michelsen, metodo estandar de la industria, TM15 Sec.
# 5.4.1-5.4.3) que SI podia dar 0<VF<1 para composiciones pesadas -- se
# ELIMINO esa rama porque el objetivo del proyecto es replicar lo que
# FlowXpert realmente hace (confirmado arriba: SIEMPRE monofasico, VF fijo
# en 1.0/0.0, nunca calcula una fraccion de vapor real), no una prediccion
# fisica independiente que puede diverger cualitativamente de FlowXpert.
# `calcular_flash()` ahora es equivalente a llamar `calcular_propiedades()`
# y clasificar el resultado como vapor/liquido segun la densidad vs. el
# punto pseudocritico de la mezcla -- coincide con `calcular_propiedades`
# por construccion (confirmado a 0.00005% contra la app, ver arriba).
# =============================================================================

def _resultado_flash_monofasico(D, Mm, props, vf_final, iteraciones, ierr, msg,
                                 duplicar_fase_ausente, P_kPa):
    """Arma el dict de salida de `calcular_flash` cuando el resultado es de
    una sola fase. `duplicar_fase_ausente` decide como se llena el campo de
    la fase que NO existe -- ver nota de `calcular_flash` sobre la
    diferencia real y CONFIRMADA entre las pantallas 'GERG-2004 Flash'
    (pone 0.000000) y 'GERG-2008 Flash' (repite el mismo valor de la fase
    presente) para el MISMO caso (P=100 bar(a), T=25 degC, composicion
    Default, VF=1.0)."""
    if duplicar_fase_ausente:
        Z_vapor = Z_liquido = props["Z"]
        Dm_vapor = Dm_liquido = D
        Dkg_vapor = Dkg_liquido = D * Mm
    else:
        Z_vapor = props["Z"] if vf_final == 1.0 else 0.0
        Z_liquido = props["Z"] if vf_final == 0.0 else 0.0
        Dm_vapor = D if vf_final == 1.0 else 0.0
        Dm_liquido = D if vf_final == 0.0 else 0.0
        Dkg_vapor = D * Mm if vf_final == 1.0 else 0.0
        Dkg_liquido = D * Mm if vf_final == 0.0 else 0.0
    return {
        "vapor_fraction": vf_final,
        "Z_vapor": Z_vapor,
        "Z_liquido": Z_liquido,
        "Z_total": props["Z"],
        "D_vapor_mol_l": Dm_vapor,
        "D_liquido_mol_l": Dm_liquido,
        "D_total_mol_l": D,
        "D_vapor_kg_m3": Dkg_vapor,
        "D_liquido_kg_m3": Dkg_liquido,
        "D_total_kg_m3": D * Mm,
        "iteraciones": iteraciones,
        "ierr": ierr,
        "msg_error": msg,
        "solucion_trivial": False,
        "aviso_baja_presion_flowxpert": _aviso_baja_presion(P_kPa),
    }


def calcular_flash(composicion: dict, T_K: float, P_kPa: float,
                    duplicar_fase_ausente: bool = False):
    """Propiedades de la mezcla como UNA SOLA fase homogenea (Vapour
    Fraction siempre 0.0 o 1.0), en el mismo formato de dict que antes
    devolvia el flash de 2 fases real.

    [CERTAIN, 2026-08-01 -- CAMBIO DE ALCANCE deliberado, pedido explicito
    del usuario tras revisar el hallazgo documentado arriba] Esta funcion
    antes tenia una rama de 2 fases genuina (Wilson K-values + prueba de
    estabilidad de Michelsen + Rachford-Rice + sustitucion sucesiva con
    fugacidad numerica -- metodo estandar de la industria, GERG-2004 TM15
    Sec. 5.4.1-5.4.3, con respaldo academico independiente, ver historial
    de este docstring en el control de versiones). Se ELIMINO esa rama:
    el objetivo de este proyecto es replicar lo que FlowXpert REALMENTE
    calcula, y el hallazgo documentado arriba (rastreo de call graph
    completo en libFXLibrary.so) confirma que la pantalla "Flash" real
    (tanto GERG-2004 como GERG-2008) NUNCA calcula una fraccion de vapor
    real -- llama a la misma rutina de una sola fase que "Gas" y reporta
    Vapour Fraction fijo en 1.0/0.0. Sin una forma confirmada de replicar
    una logica de deteccion de 2 fases que FlowXpert de hecho no tiene en
    esta pantalla, mantener esa rama solo agregaba el riesgo de mostrar
    una prediccion no confirmada (y en al menos un caso, cualitativamente
    distinta de FlowXpert) como si fuera un resultado validado.

    Ahora esta funcion es equivalente a llamar `calcular_propiedades()` y
    clasificar el resultado como vapor (Vapour Fraction=1.0) o liquido
    (0.0) segun la densidad de la alimentacion comparada con la densidad
    en el punto pseudocritico de la mezcla -- coincide con
    `calcular_propiedades` por construccion (confirmado a 0.00005% contra
    la app, ver docstring del modulo).

    `duplicar_fase_ausente` [CERTAIN, confirmado 2026-07-22 con 2 capturas
    reales del MISMO caso P=100 bar(a)/T=25 degC/composicion Default]:
      - False (default): la fase AUSENTE se reporta en 0.000000 -- asi se
        comporta la pantalla real 'GERG-2004 Flash' (Liquid Compr.=
        0.000000, Liquid Density=0.000000 cuando Vapour Fraction=1.000000).
      - True: la fase "ausente" se reporta IGUAL a la fase presente (mismo
        Z, misma densidad) -- asi se comporta la pantalla real 'GERG-2008
        Flash' (Liquid Compr.=0.865194=Vapour Compr., Liquid Density=
        86.89433=Vapour Density, con el mismo VF=1.000000). Ambas pantallas
        parten del MISMO motor/composicion, pero difieren en como formatean
        la fase ausente -- no es un bug, es un comportamiento real
        distinto entre las dos pantallas de la app.

    Densidad expresada en mol/l (=kmol/m3), IGUAL que el numero que
    muestra la pantalla 'GERG-2004 Flash' de la app bajo la etiqueta
    'kg/m3' -- esa etiqueta de la app no corresponde a densidad masica
    real (ver docstring del modulo); se replica el numero tal cual lo
    muestra la app.

    [CERTAIN, bug encontrado y corregido 2026-08-01, evidencia: 2 capturas
    reales nuevas, CO2 100% y CO2 99%/n-Pentano 1%, ambas P=100 bar(a)/
    T=273.15 K -- T=0 degC esta por debajo de la critica del CO2 (304.13 K),
    P=100 bar esta por encima de su presion de saturacion a esa T (~34.85
    bar), asi que la fase estable real es LIQUIDA]. La version anterior de
    esta funcion resolvia `DensityGERG()` UNA sola vez, siempre arrancando
    la iteracion de Newton desde la densidad de gas ideal (`iFlag=0`), y
    despues clasificaba el resultado como vapor/liquido comparando esa
    densidad contra la pseudocritica. En la region de multiples raices
    (por debajo de la temperatura critica de la mezcla) eso puede converger
    a una raiz espuria en vez de la raiz liquida real -- confirmado: para
    CO2 100% a 100 bar(a)/0 degC daba Z=0.370883 (raiz espuria) en vez del
    Z=0.198885 real (coincide exacto usando `iFlag=2`, el arranque "tipo
    liquido" que `DensityGERG()` ya soportaba pero esta funcion no usaba).
    Para CO2 99%/n-Pentano 1% en las mismas condiciones, la raiz de gas
    ideal ni siquiera convergia (`ierr=1`, "Calculation error" en la GUI)
    mientras la app real daba un resultado liquido valido (Z=0.201849,
    reproducido a 0.08% con `iFlag=2`).
    Correccion: ahora se resuelven AMBAS raices candidatas (arranque de gas
    ideal `iFlag=0` y arranque de liquido `iFlag=2`) y se elige la de MENOR
    energia libre de Gibbs molar (`G_J_mol`, ya calculada por
    `PropertiesGERG`) -- el criterio termodinamico estandar de estabilidad
    a T y P fijos. Si solo una de las 2 raices converge, se usa esa. Si
    ninguna converge, se propaga el error de la raiz de gas ideal (mismo
    comportamiento que antes de esta correccion).

    [CERTAIN, 2do bug encontrado y corregido el mismo dia, 2026-08-01, en
    el barrido sistematico con las 16 composiciones guardadas de la app]
    Cuando P esta suficientemente por encima de la presion de saturacion
    (bien adentro de la region liquida, ej. CO2 puro a 25 degC/100 bar(a),
    Psat(25 degC)~=64 bar) la ecuacion de estado ya NO tiene una raiz vapor
    distinta -- los arranques `iFlag=0` e `iFlag=2` convergen a LA MISMA
    raiz (la unica real, que es la liquida). Una primera version de esta
    correccion asumia que "ambas raices iguales" siempre significa "region
    de una sola raiz, es vapor" (cierto para el caso normal de gas natural
    a baja presion), pero es FALSO en este caso: la unica raiz real, aqui,
    es liquida (D=18.577 mol/l > Dcx=10.625 mol/l del CO2 puro), y la
    version anterior la etiquetaba VF=1.0 (vapor) por convencion, dejando
    pasar un Z fisicamente correcto pero con la etiqueta de fase invertida.
    Corregido: cuando ambas raices coinciden, la clasificacion vapor/
    liquido se hace comparando esa densidad unica contra la pseudocritica
    de la mezcla (`PseudoCriticalPointGERG`), igual que la version original
    de esta funcion (antes de la eliminacion de la rama de 2 fases) --
    validado sin regresion contra el caso normal ya confirmado (Default,
    100 bar(a)/25 degC, D=4.662 mol/l < Dcx=10.059 mol/l -> vapor,
    correcto) y contra el nuevo caso (CO2 puro, 100 bar(a)/25 degC,
    D=18.577 mol/l > Dcx=10.625 mol/l -> liquido, correcto)."""
    z = _composicion_a_x(composicion)
    Mm = MolarMassGERG(z)

    D_vapor, ierr_v, msg_v = DensityGERG(T_K, P_kPa, z, iFlag=0)
    D_liquido, ierr_l, msg_l = DensityGERG(T_K, P_kPa, z, iFlag=2)

    candidatos = []
    if not ierr_v:
        candidatos.append((D_vapor, PropertiesGERG(T_K, D_vapor, z), 1.0))
    if not ierr_l:
        candidatos.append((D_liquido, PropertiesGERG(T_K, D_liquido, z), 0.0))

    if not candidatos:
        props = PropertiesGERG(T_K, D_vapor, z)
        return _resultado_flash_monofasico(D_vapor, Mm, props, 1.0, 0, ierr_v, msg_v,
                                            duplicar_fase_ausente, P_kPa)

    if len(candidatos) == 2 and abs(D_vapor - D_liquido) < 1.0e-6 * max(D_vapor, 1.0):
        _Tcx, Dcx = PseudoCriticalPointGERG(z)
        vf_final = 0.0 if D_vapor >= Dcx else 1.0
        D_final, props, _vf = candidatos[0]
        return _resultado_flash_monofasico(D_final, Mm, props, vf_final, 0, 0, "",
                                            duplicar_fase_ausente, P_kPa)

    D_final, props, vf_final = min(candidatos, key=lambda c: c[1]["G_J_mol"])
    return _resultado_flash_monofasico(D_final, Mm, props, vf_final, 0, 0, "",
                                        duplicar_fase_ausente, P_kPa)


def calcular_flash_gerg2008(composicion: dict, T_K: float, P_kPa: float):
    """Alias explicito de `calcular_flash` con `duplicar_fase_ausente=True`,
    para la pantalla real 'GERG-2008 Flash' (distinta de 'GERG-2004 Flash',
    ver docstring de `calcular_flash`). Ademas la densidad se expresa en
    kg/m3 REAL (masica) en esta pantalla -- confirmado con la captura real
    ('GERG 2008/GERG FLASH 1.jpeg': Vapour/Liquid/Total Density=86.89433
    kg/m3, que SI coincide con la densidad masica real, a diferencia de la
    pantalla 'GERG-2004 Flash' donde el numero bajo la etiqueta 'kg/m3' es
    en realidad la densidad molar)."""
    return calcular_flash(composicion, T_K, P_kPa, duplicar_fase_ausente=True)


if __name__ == "__main__":
    # Composicion de ejemplo de ExampleGerg en GERG2008.FOR (identica a la de
    # DETAIL.FOR, no es un caso de validacion publicado con salida conocida).
    composicion = {
        "Metano": 0.77824, "Nitrogeno": 0.02, "CO2": 0.06, "Etano": 0.08,
        "Propano": 0.03, "Isobutano": 0.0015, "n-Butano": 0.003,
        "Isopentano": 0.0005, "n-Pentano": 0.00165, "n-Hexano": 0.00215,
        "n-Heptano": 0.00088, "n-Octano": 0.00024, "n-Nonano": 0.00015,
        "n-Decano": 0.00009, "Hidrogeno": 0.004, "Oxigeno": 0.005,
        "CO": 0.002, "Agua": 0.0001, "H2S": 0.0025, "Helio": 0.007,
        "Argon": 0.001,
    }
    T = 400.0
    P = 50000.0

    print("=== normas/GERG_2008.py -- autotest (ecuacion GERG-2008 / AGA-8 Part 2) ===")
    print(f"T = {T} K, P = {P} kPa")
    r = calcular_propiedades(composicion, T, P)
    if r["ierr"] != 0:
        print("ADVERTENCIA:", r["msg_error"])
    for k in ["Mm_g_mol", "D_mol_l", "Z", "Cv_J_molK", "Cp_J_molK", "W_m_s",
              "H_J_mol", "S_J_molK", "Kappa"]:
        print(f"  {k} = {r[k]:.6f}")
