# -*- coding: utf-8 -*-
"""
normas/NX_19_puro.py
=======================
Version 100% Python puro del metodo NX-19 "SG + Poder Calorifico + PTB G9"
(ver `normas/NX_19.py`), pensada para un despliegue WEB donde NO se puede
depender de `FlowXpert.xll` (ctypes+pefile, Windows) ni del emulador
Unicorn del `.so` de Android (`normas/_nx19_emulador.py`). Mismo patron que
`normas/AGA_10_puro.py`: NUNCA importa `ctypes`/`pefile`/`unicorn`, en
ningun punto del archivo (confirmado con grep). Misma funcion de entrada
que el modulo original, `nx19_fpv_ghv()`, mismos parametros y mismas
claves de salida (patron identico a como `AGA_10_puro.py` reutiliza el
nombre `calcular_velocidad_sonido_y_fpv`, no un nombre nuevo con sufijo).

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
A diferencia de AGA-10, este metodo NO usa una composicion de 21
componentes -- son 6 entradas puntuales, mas simples y rapidas de armar
(la pantalla real de FlowXpert se llama "NX-19 SG+GHV+PTB G9"):

PASO 1 -- Importar la unica funcion publica:
    from normas.NX_19_puro import nx19_fpv_ghv

PASO 2 -- Reunir las 6 entradas (unidades exactas, no hay selector de
unidad en este modulo -- convertir ANTES de llamar si los datos vienen en
otra unidad):
    p_bar     = 50.0    # Presion ABSOLUTA, bar(a) -- NO manometrica
    t_degc    = 25.0    # Temperatura, grados Celsius
    sg        = 0.6     # Gravedad Especifica (adimensional, aire=1)
    ghv_mj_m3 = 40.0     # Poder Calorifico Bruto, MJ/m3
    n2_frac   = 0.01     # Fraccion molar de Nitrogeno (0.0-1.0, NO porcentaje)
    co2_frac  = 0.02     # Fraccion molar de CO2 (0.0-1.0, NO porcentaje)
    ptb_g9    = True     # Activa la correccion "PTB G9" de FlowXpert

PASO 3 -- Llamar la funcion (ningun parametro es opcional salvo `ptb_g9`,
que por defecto es `True`):
    resultado = nx19_fpv_ghv(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9)

PASO 4 -- Leer el resultado (dict con 5 claves, mas simple que AGA-10):
    resultado["z"]              # Factor de compresibilidad
    resultado["fpv"]            # Factor de supercompresibilidad (1/sqrt(Z))
    resultado["d_mol_m3"]       # Densidad molar, mol/m3
    resultado["fuera_de_rango"] # True/False -- avisa, NO bloquea el calculo
    resultado["fuente"]         # Texto explicando que rama/formula se uso

PASO 5 -- SIEMPRE revisar si `resultado["z"]` es NaN (`z != z` es True solo
si es NaN) antes de usar el numero -- pasa en combinaciones de entrada tan
extremas que ni el algoritmo real del binario da un resultado confiable
(ver "LIMITE CONOCIDO" mas abajo en este docstring). Nunca es un numero
fabricado.

Ejemplo COMPLETO, listo para copiar y correr (`python -m normas.NX_19_puro`
tambien corre un autotest parecido a este):
    from normas.NX_19_puro import nx19_fpv_ghv
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    print(r["z"], r["fpv"], r["fuera_de_rango"])

===============================================================================
ORIGEN DE LA FORMULA (2026-09-01)
===============================================================================
Decompilacion COMPLETA (Ghidra 12.1.2, headless, via PowerShell -- ver
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_scripts_xll/DecompileNx19Xll.java` y el
log completo `ANALISIS_GHIDRA_FLOWXPERT/ghidra_nx19_xll_output.txt`) de las
4 funciones reales dentro de `FlowXpert.xll` mas sus 20 subfunciones
(21 funciones en total, 121 constantes DAT_ resueltas a su valor double
exacto por lectura directa de memoria):

    FUN_1800c9500 (Nx19_Calc, el despachador)
    +-- ptb_g9==False -> FUN_1800c95b8 (Z_AGA_nx19, metodo CLASICO 1962)
    +-- ptb_g9==True:
        +-- GHV <  39.79999923706055 MJ/m3 -> FUN_1800c9db4 (Z_AGA_nx19_mod)
        +-- GHV >= 39.79999923706055 MJ/m3 -> FUN_1800c979c (Z_AGA_nx19_3H)

CONFIRMACION CRUZADA con fuente PUBLICA independiente [CERTAIN]: la rama
clasica (`Z_AGA_nx19`, ptb_g9=False) coincide EXACTA, constante por
constante (156.47/160.8/7.22/226.29/99.15/211.9/1.681/0.392 para Fp/Ft
"Standard Gravity Method"; 0.0330378/0.0221323/0.0161353 para "m";
0.265827/0.0457697/0.133185 para "n"; 0.00075/2.3/20.0/1.4/2.17/0.0011
para el termino "e" con tau>=1.09; 1.317/1.69 para tau<1.09,pii<1.3;
0.00132/3.25 para el factor Zb) con el codigo C fuente PUBLICO de
"Totalflow Technical Bulletin 106 -- NX19 Supercompressibility Equation
using Fixed FtFp" (ABB Inc., 2003-03-24, Appendix 1,
`documentos_normativos/ABB_TotalflowTechBulletin106_NX19_2003.pdf`), que
documenta el metodo NX-19 AGA 1962 "Standard Gravity Method" tal cual lo
implementaban los flow computers Totalflow. Doble confirmacion
independiente (decompilacion + fuente publica de 2003) para esta rama.

Las ramas `_mod`/`_3H` (ptb_g9=True, la "correccion PTB G9" propiamente
dicha) NO tienen equivalente en ninguna fuente publica encontrada (el
bulletin de ABB no las menciona, tampoco el manual Kelton help
`documentos_normativos/NX19_Kelton_help/`) -- se determinaron
EXCLUSIVAMENTE por decompilacion. Reutilizan la MISMA estructura Fp/Ft
"Standard Gravity Method" y las MISMAS formulas "m"/"n"/factor Zb que la
rama clasica, pero con una formula "e" propia (estructuralmente parecida
pero NO identica -- ej. usa la constante 1.692 en vez de 1.69 en el caso
tau<=1.09/pii>1.3) y, criticamente, con `pii` calculado SIN el offset de
"-14.7" (presion manometrica) que si tiene la rama clasica: pii_mod =
(fp*P_psia_absoluta + 14.7)/1000, mientras pii_clasico =
((P_psia_absoluta-14.7)*fp + 14.7)/1000. Esta diferencia es real y
literal en el binario (2 secuencias de instrucciones distintas), confirmada
ademas porque SIN ella el resultado no coincide con el oraculo (ver
VALIDACION). La rama `_3H` ademas aplica, sobre el resultado de `_mod`, un
polinomio multiplicativo propio de 9 terminos en P/T/GHV/SG/CO2
(`FUN_1800c994c`, NO usa N2) -- correccion exclusiva de gas de alto poder
calorifico (GHV>=39.8 MJ/m3).

===============================================================================
LA FORMULA "e" TIENE 8 REGIONES (pii, tau) EN LA RAMA CLASICA
===============================================================================
El ejemplo de codigo del bulletin de ABB (y el de Kelton) solo cubre 3
casos (tau>=1.09; tau<1.09 y pii<1.3; tau<1.09 y pii>=1.3 con 2 sub-casos
por tau>=0.88). El binario real EXTIENDE esto a 8 regiones sobre (pii,tau)
para cubrir pii en [2.0, 5.0] (presiones mas altas que el rango original
de 1962, "hasta 1500 psia"): agrega una correccion bicubica en
(pii-2.0, tau) (`FUN_1800cac8c`, 20 constantes propias) que se RESTA de la
formula base evaluada con pii recortado a 2.0. Las ramas `_mod`/`_3H` NO
tienen esta extension (su formula "e" siempre usa 3 casos, nunca 8) --
otra diferencia real y confirmada entre la rama clasica y las PTB G9.

[LIKELY, resuelto empiricamente -- ver docstring de `_ecalc_region_h()`]
Una unica ambiguedad real de decompilacion quedo en la region MAS extrema
de la rama clasica (pii en [2.0,5.0], tau en [1.32,1.4], `FUN_1800caa6c`):
el pseudocodigo de Ghidra muestra una reasignacion de `param_1` (a
`pii-2.0`) justo antes de una llamada a `FUN_1800caa10()` SIN argumentos
visibles -- ambiguo si esa llamada recibe el `pii` original o `pii-2.0`.
Se probaron AMBAS hipotesis contra el oraculo `.xll` directo en puntos
reales de esa region exacta (P=140bar/T=72-88degC/SG=0.55-0.6,
ptb_g9=False -- fuera del rango oficial documentado pero dentro del rango
de sanidad interno de la rama clasica, T -40..240degF/P 0..5000psig):
"pii original" da error ~0.002-0.003% (residuo pequeño, no cero: alguna
sutileza de la reconstruccion de esta rama tan extrema no quedo 100%
resuelta), "pii-2.0" da error ~2.4-2.6% (claramente incorrecta). Se adopto
"pii original" por ser la unica compatible con el oraculo. Esta region
esta MUY fuera del rango documentado del screen NX-19 (P>120bar(a) Y
T>65degC simultaneos) -- el barrido de validacion sobre el rango
documentado/realista (ver VALIDACION) nunca la alcanza, por lo que este
residuo de ~0.003% no afecta ningun caso de uso real conocido.

===============================================================================
VALIDACION (2026-09-01)
===============================================================================
Oraculo: `normas/_nx19_xll_directo.py` (llamada ctypes directa, sin Excel,
a `FUN_1800C9500` real dentro de `FlowXpert.xll` -- ya validado exacto
contra el dispositivo real/Unicorn en 6 casos que cubren las 3 ramas, ver
docstring de ese modulo). Ver `normas/_sweep_nx19_puro.py` para el barrido
completo.

- Los 2 casos reales conocidos y persistidos en disco (baseline
  P=50bar/T=25degC/SG=0.6/GHV=40/N2=1%/CO2=2%, Z real=0.909911, rama 3H; y
  struct dump Frida P=80/T=50 mismos demas, Z real=0.90975495418227474,
  rama 3H): EXACTOS (0.0000% y 0.000000%).
- Barrido de ~1700 casos cubriendo las 3 ramas dentro y fuera del rango
  documentado (rango real de medicion, fronteras de umbral GHV, barrido
  N2/CO2, barrido SG amplio, aleatorio amplio incl. extremos, caso extremo
  ya documentado Z>1.1): 100% de los casos donde el oraculo dio resultado
  coinciden EXACTOS (peor error tipico ~1e-12%, ruido de punto flotante) y
  el flag `fuera_de_rango` coincide en el 100% de los casos.
- Los unicos casos "sin comparar" en el barrido (SG=0.89-1.0 en rama
  clasica, ~4% de la muestra) son donde el ORACULO MISMO falla
  (`FUN_1800C9500` real devuelve codigo de error -7, el ecalc cae fuera de
  las 8 regiones tabuladas) -- en esos MISMOS casos este modulo tambien
  marca independientemente que no puede dar un resultado confiable
  (`z=None` -> se expone como NaN con aviso explicito, nunca un numero
  fabricado), 100% de correlacion.
- Sin regresion: `python -m normas.NX_19` (camino original .xll/Unicorn,
  no tocado) y `python normas/_prueba_rangos_nx19.py` (script de
  calibracion existente) siguen pasando igual que antes.

CONCLUSION: a diferencia de AGA-10 (32/32=100% en rango real, 72% en el
barrido completo por caos numerico de un solver iterativo anidado), NX-19
al ser formulas cerradas SIN iteracion alcanza 100% de coincidencia exacta
en todo el barrido comparable, sin ninguna zona "caotica" real dentro del
rango documentado.

Uso: python -m normas.NX_19_puro
"""

import math

# ===========================================================================
# Utilidades defensivas (semantica tipo libm: un dominio invalido da NaN,
# no una excepcion Python sin manejar -- mismo criterio de honestidad ya
# usado en AGA_10_puro.py, nunca se fabrica un numero, pero tampoco se
# crashea silenciosamente ante una entrada realmente extrema/fuera de
# cualquier rango probado).
# ===========================================================================

def _pow(x: float, y: float) -> float:
    try:
        if x < 0.0 and not float(y).is_integer():
            return float("nan")
        return math.pow(x, y)
    except (ValueError, OverflowError, ZeroDivisionError):
        return float("nan")


def _sqrt(x: float) -> float:
    if x != x or x < 0.0:
        return float("nan")
    try:
        return math.sqrt(x)
    except ValueError:
        return float("nan")


def _exp(x: float) -> float:
    try:
        return math.exp(x)
    except OverflowError:
        return float("inf")


def _cbrt(x: float) -> float:
    """d = x^(1/3) real (incluye negativos, a diferencia de math.pow)."""
    if x != x:
        return float("nan")
    if x < 0.0:
        r = _pow(-x, 1.0 / 3.0)
        return -r if r == r else float("nan")
    return _pow(x, 1.0 / 3.0)


# --- Umbrales de despacho, Nx19_Calc (FUN_1800c9500) ---
_GHV_MIN_PTB = 31.799999237060547     # DAT_1801d60e0
_GHV_MAX_PTB = 46.20000076293945      # DAT_1801d6108
_GHV_UMBRAL_3H = 39.79999923706055    # DAT_1801d60e8 (>= -> 3H; < -> mod)

_BAR_A_PSI_DIV = 0.06894757           # DAT_180193ea0 (bar por psi; rama clasica: P_bar/esto)
_BAR_A_PSI_MUL = 14.50377             # DAT_1801d60c8 (psi por bar; ramas mod/3H: P_bar*esto)


# ===========================================================================
# ECALC CLASICO (FUN_1800cab2c y sus 8 regiones) -- usado SOLO por la rama
# clasica ptb_g9=False (Z_AGA_nx19), via FUN_1800c9b04.
# ===========================================================================

def _ecalc_region_a(pii: float, tau: float) -> float:
    """FUN_1800ca4d4 -- tau >= 1.09 (bulletin ABB, primer caso 'if')."""
    t = tau - 1.09                       # DAT_1801d6018
    s = _sqrt(t)
    e = 1.0 - _exp(t * -20.0) * _pow(pii, 2.3) * 7.5e-4
    s1 = _pow((s * 1.4 + 2.17) - pii, 2.0)
    return e - s1 * s * 0.0011 * pii * pii


def _ecalc_region_b(pii: float, tau: float) -> float:
    """FUN_1800ca5a4 -- tau < 1.09 y pii < 1.3 (bulletin ABB, 'else if
    pii<1.3'). TAMBIEN es la formula de respaldo/extrapolacion cuando
    (pii,tau) cae fuera de las 8 regiones definidas (misma que usa el
    binario real -- ver `_ecalc_dispatch`)."""
    t = 1.09 - tau
    e = 1.0 - _pow(pii, 2.3) * 7.5e-4 * (2.0 - _exp(t * -20.0))
    return e - _pow(t, 4.0) * 1.317 * pii * (1.69 - pii * pii)


def _ecalc_region_c(pii: float, tau: float) -> float:
    """FUN_1800ca65c -- 1.3<=pii<2.0, 0.88<=tau<1.09 (bulletin ABB,
    branch 3, sub-caso tau>=0.88 => e34exp=1.25 fijo)."""
    t = 1.09 - tau
    t2 = t * t
    t4 = t2 * t2
    e = 1.0 - _pow(pii, 2.3) * 7.5e-4 * (2.0 - _exp(t * -20.0))
    poly = ((((t4 * t2 * 200.0 - t * 0.03249) + t2 * 2.0167) - t2 * t * 18.028) + t4 * 42.844) * 0.455
    return poly * (pii - 1.3) * (_pow(2.0, 1.25) * 1.69 - pii * pii) + e


def _ecalc_region_d(pii: float, tau: float) -> float:
    """FUN_1800ca7cc -- 1.3<=pii<2.0, 0.84<=tau<0.88 (bulletin ABB,
    branch 3, sub-caso tau<0.88 => e34exp=1.25+80*(0.88-tau)^2)."""
    t = 1.09 - tau
    t2 = t * t
    t4 = t2 * t2
    e34 = _pow(2.0, _pow(0.88 - tau, 2.0) * 80.0 + 1.25) * 1.69
    poly = ((((t4 * t2 * 200.0 - t * 0.03249) + t2 * 2.0167) - t2 * t * 18.028) + t4 * 42.844) * 0.455
    e = 1.0 - _pow(pii, 2.3) * 7.5e-4 * (2.0 - _exp(t * -20.0))
    return e + (e34 - pii * pii) * poly * (pii - 1.3)


def _correccion_bicubica_pii_alto(pii: float, tau: float) -> float:
    """FUN_1800cac8c -- correccion bicubica en (u=pii-2.0, v=tau), usada
    SOLO para pii>=2.0 (fuera del rango real de medicion, ver docstring
    del modulo). 20 constantes propias, sin equivalente en ninguna fuente
    publica -- exclusivas del binario."""
    u = pii - 2.0
    v = tau
    v2 = v * v
    v3 = v2 * v
    v4 = v3 * v
    term1 = (0.016299 - v * 0.028094 + v2 * 0.48782 - v3 * 0.728221 + v4 * 0.27839) * u * u
    term2 = (1.7172 - v * 2.33123 - v2 * 1.56796 + v3 * 3.47644 - v4 * 1.28603) * u
    term3 = (v * 0.51419 - 0.35978 + v2 * 0.16453 - v3 * 0.52216 + v4 * 0.19687) * u * u * u
    term4 = (0.075255 - v * 0.10573 - v2 * 0.058598 + v3 * 0.14416 - v4 * 0.054533) * u * u * u * u
    return term1 + term2 + term3 + term4


def _ecalc_region_e(pii: float, tau: float) -> float:
    """FUN_1800ca958 -- 2.0<=pii<=5.0, 0.84<=tau<0.88."""
    return _ecalc_region_d(min(pii, 2.0), tau) - _correccion_bicubica_pii_alto(pii, tau)


def _ecalc_region_f(pii: float, tau: float) -> float:
    """FUN_1800ca9b4 -- 2.0<=pii<=5.0, 0.88<=tau<1.09."""
    return _ecalc_region_c(min(pii, 2.0), tau) - _correccion_bicubica_pii_alto(pii, tau)


def _ecalc_region_g(pii: float, tau: float) -> float:
    """FUN_1800caa10 -- 2.0<=pii<=5.0, 1.09<=tau<1.32."""
    return _ecalc_region_a(min(pii, 2.0), tau) - _correccion_bicubica_pii_alto(pii, tau)


def _ecalc_region_h(pii: float, tau: float) -> float:
    """FUN_1800caa6c -- 2.0<=pii<=5.0, 1.32<=tau<=1.4. Ver docstring del
    modulo, seccion de la ambiguedad [LIKELY] resuelta EMPIRICAMENTE
    contra el oraculo (se llama a `_ecalc_region_g` con el pii ORIGINAL,
    no pii-2.0 -- la unica de las 2 hipotesis probadas que se acerca al
    oraculo, con un residuo pequeño ~0.002-0.003% sin resolver del todo,
    en una zona muy fuera del rango documentado)."""
    u = pii - 2.0
    base = _ecalc_region_g(pii, tau)
    dt2 = _pow(tau - 1.32, 2.0)
    poly_u = (3.0 - u * 1.483) - u * u * 0.1 + u * u * u * 0.0833
    return base - dt2 * u * poly_u


def _ecalc_dispatch(pii: float, tau: float):
    """FUN_1800cab2c -- dispatch por region de (pii,tau). Devuelve
    (e_value, valido) -- valido=False si el punto cae fuera de las 8
    regiones definidas (usa la formula de respaldo `_ecalc_region_b` de
    todas formas, igual que el binario real -- pero el binario real
    ADEMAS devuelve un codigo de error -7 en ese caso, que este modulo
    replica tratando el resultado como no-confiable, ver
    `_core_classic`)."""
    if pii >= 0.0:
        if pii < 2.0 and 1.09 <= tau <= 1.4:
            return _ecalc_region_a(pii, tau), True
        if pii < 1.3 and 0.84 <= tau < 1.09:
            return _ecalc_region_b(pii, tau), True
    if 1.3 <= pii < 2.0:
        if 0.88 <= tau < 1.09:
            return _ecalc_region_c(pii, tau), True
        if 0.84 <= tau < 0.88:
            return _ecalc_region_d(pii, tau), True
    if 2.0 <= pii <= 5.0:
        if 0.84 <= tau < 0.88:
            return _ecalc_region_e(pii, tau), True
        if 0.88 <= tau < 1.09:
            return _ecalc_region_f(pii, tau), True
        if 1.09 <= tau < 1.32:
            return _ecalc_region_g(pii, tau), True
        if 1.32 <= tau <= 1.4:
            return _ecalc_region_h(pii, tau), True
    return _ecalc_region_b(pii, tau), False


# ===========================================================================
# NUCLEO CLASICO (FUN_1800c9b04) -- resuelve la cubica de Kelton/AGA-1962
# dado (P_gauge_psi, T_degF, fp, ft). Devuelve Z_flujo puro (1/fpv_raw).
# ===========================================================================

def _core_classic(p_gauge_psi: float, t_degf: float, fp: float, ft: float):
    """FUN_1800c9b04. Devuelve (Z, ecalc_valido). Z=None si el termino
    cubico 'd' no es finito O si ecalc cayo fuera de sus 8 regiones
    tabuladas (`ecalc_valido=False`) -- en AMBOS casos el binario real
    devuelve un codigo de error (no un Z utilizable), confirmado contra
    el oraculo (ver docstring del modulo): se replica tratando el
    resultado como no-confiable, nunca se fabrica un numero ahi."""
    pii = (p_gauge_psi * fp + 14.7) / 1000.0
    tau = ((t_degf + 460.0) * ft) / 500.0

    tau2 = tau * tau
    tau3 = tau2 * tau
    tau4 = tau3 * tau
    m = (1.0 / tau2) * 0.0330378 - (1.0 / tau3) * 0.0221323 + (1.0 / (tau4 * tau)) * 0.0161353
    n = (((1.0 / tau4) * 0.0457697 + (1.0 / tau2) * 0.265827) - (1.0 / tau) * 0.133185) / m

    b2 = (3.0 - m * n * n) / (9.0 * m * pii * pii)
    e, ecalc_valido = _ecalc_dispatch(pii, tau)
    b1 = (9.0 * n - 2.0 * m * n * n * n) / (54.0 * m * pii * pii * pii) - e / (2.0 * m * pii * pii)

    raiz = _sqrt(b2 * b2 * b2 + b1 * b1)
    d = _cbrt(raiz + b1)
    if not (d == d) or d == 0.0 or not math.isfinite(d) or not ecalc_valido:
        return None, ecalc_valido

    fpv_raw = n / (pii * 3.0) + (b2 / d - d)
    if fpv_raw == 0.0 or not math.isfinite(fpv_raw):
        return None, ecalc_valido
    z = 1.0 / fpv_raw
    return z, ecalc_valido


def z_aga_nx19(p_bar: float, t_degc: float, sg: float, n2_frac: float, co2_frac: float):
    """SI se puede llamar directo si sabes de antemano que querés la rama
    CLASICA (equivalente a llamar `nx19_fpv_ghv(..., ptb_g9=False)`, pero
    sin el chequeo de P/T<=0 ni el empaquetado en dict -- uso avanzado, la
    mayoria de los casos deberia usar `nx19_fpv_ghv()` en su lugar).

    Parametros (unidades EXACTAS, sin conversion automatica):
        p_bar: presion ABSOLUTA de flujo, bar(a).
        t_degc: temperatura de flujo, grados Celsius.
        sg: Gravedad Especifica, adimensional (aire=1).
        n2_frac, co2_frac: fraccion molar (0.0-1.0, NO porcentaje).

    Devuelve una TUPLA (no un dict): (Z o None, fuera_de_rango: bool,
    ecalc_valido: bool). Z=None cuando el termino cubico interno no da un
    numero finito -- en ese caso el llamador (`nx19_calc_puro`) lo
    convierte a NaN, nunca fabrica un valor.

    FUN_1800c95b8 -- rama clasica (ptb_g9=False), metodo "Standard
    Gravity Method" de NX-19 (AGA 1962), confirmado byte-a-byte contra el
    codigo publico de ABB Technical Bulletin 106 (ver docstring del
    modulo). GHV nunca se usa en esta rama (confirmado tanto por
    decompilacion como empiricamente en el proyecto)."""
    p_gauge_psi = (p_bar / _BAR_A_PSI_DIV) - 14.7
    t_degf = t_degc * 1.8 + 32.0
    mc = co2_frac * 100.0
    mn = n2_frac * 100.0

    fuera = False
    if t_degf < -40.0 or t_degf > 240.0:
        fuera = True
    if p_gauge_psi < 0.0 or p_gauge_psi > 5000.0:
        fuera = True
    if sg < 0.554 or sg > 1.0:
        fuera = True
    if mc < 0.0 or mc > 15.0:
        fuera = True
    if mn < 0.0 or mn > 15.0:
        fuera = True

    denom_fp = (mc - mn * 0.392) + (160.8 - sg * 7.22)
    denom_ft = (sg * 211.9 + 99.15) - (mn * 1.681 + mc)
    if denom_fp == 0.0 or denom_ft == 0.0:
        return None, True, False
    fp = 156.47 / denom_fp
    ft = 226.29 / denom_ft

    z, ecalc_valido = _core_classic(p_gauge_psi, t_degf, fp, ft)
    return z, fuera, ecalc_valido


# ===========================================================================
# NUCLEO "PTB G9" (FUN_1800c9f08) -- compartido por las ramas _mod y _3H.
# Misma estructura Fp/Ft "Standard Gravity Method" que la rama clasica,
# pero con: (a) formula 'e' propia de 3 casos (no 8 regiones -- el
# binario no extiende esta rama a pii alto), (b) pii SIN el offset
# "-14.7" de presion manometrica, (c) Z devuelto YA multiplicado por
# 1/Zb (ver docstring del modulo). Recibe T en Kelvin y P en bar(a)
# directo (sin convertir a psi/degF primero -- el binario usa
# Rankine=1.8*K y psi=bar*14.50377 inline, sin el paso intermedio por
# Fahrenheit/gauge).
# ===========================================================================

def _e_calc_mod(pii: float, tau: float) -> float:
    """Parte interna de FUN_1800c9f08 (el switch de 3 casos por
    (pii,tau), ANTES de dividir por m/n/b1/b2 -- estructuralmente
    identica a _ecalc_region_a/b/(c+d fusionadas), pero con la constante
    1.692 en vez de 1.69 en el caso 3 (diferencia real confirmada en el
    binario, no un error de transcripcion) y sin el 'e34exp' variable de
    la rama clasica (siempre usa el equivalente de 2.0^1.25 fijo)."""
    if tau > 1.09:
        t = tau - 1.09
        s = _sqrt(t)
        e = 1.0 - _exp(t * -20.0) * _pow(pii, 2.3) * 7.5e-4
        s1 = _pow((s * 1.4 + 2.17) - pii, 2.0)
        return e - s1 * s * 0.0011 * pii * pii
    t = 1.09 - tau
    if pii <= 1.3:
        t4 = t * t * t * t
        e = 1.0 - _pow(pii, 2.3) * 7.5e-4 * (2.0 - _exp(t * -20.0))
        return e - t4 * 1.317 * pii * (1.69 - pii * pii)
    t2 = t * t
    t3 = t2 * t
    t4 = t3 * t
    t6 = t4 * t2
    poly = t6 * 200.0 - t * 0.03249 + t2 * 2.0167 - t3 * 18.028 + t4 * 42.844
    e = 1.0 - _pow(pii, 2.3) * 7.5e-4 * (2.0 - _exp(t * -20.0))
    return (_pow(2.0, 1.25) * 1.692 - pii * pii) * poly * 0.455 * (pii - 1.3) + e


def _core_mod(t_k: float, p_bar: float, sg: float, co2_frac: float, n2_frac: float):
    """FUN_1800c9f08. Devuelve (Z_mod o None, valido) donde Z_mod =
    Z_flujo/Zb (no Z_flujo puro -- ver docstring del modulo)."""
    denom_ft = (sg * 2.119 + 0.9915) - co2_frac - n2_frac * 1.681
    denom_fp = (1.608 - sg * 0.0722) + co2_frac - n2_frac * 0.392
    if denom_ft == 0.0 or denom_fp == 0.0:
        return None, False
    ft = 2.2629 / denom_ft
    tau = ft * (1.8 * t_k) / 500.0
    fp = 1.5647 / denom_fp
    pii = (fp * (p_bar * _BAR_A_PSI_MUL) + 14.7) / 1000.0

    e = _e_calc_mod(pii, tau)

    tau2 = tau * tau
    tau3 = tau2 * tau
    tau4 = tau3 * tau
    m = (1.0 / tau2) * 0.0330378 - (1.0 / tau3) * 0.0221323 + (1.0 / (tau4 * tau)) * 0.0161353
    n = (((1.0 / tau4) * 0.0457697 + (1.0 / tau2) * 0.265827) - (1.0 / tau) * 0.133185) / m

    b1 = (9.0 * n - 2.0 * m * n * n * n) / (54.0 * m * pii * pii * pii) - e / (2.0 * m * pii * pii)
    b2 = (3.0 - m * n * n) / (9.0 * m * pii * pii)

    raiz = _sqrt(b2 * b2 * b2 + b1 * b1)
    d = _cbrt(raiz + b1)
    if not (d == d) or d == 0.0 or not math.isfinite(d):
        return None, True

    fpv_raw = n / (pii * 3.0) + (b2 / d - d)
    if fpv_raw == 0.0 or not math.isfinite(fpv_raw):
        return None, True
    inv_zb = _pow(1.0 + 0.00132 / _pow(tau, 3.25), 2.0)   # = 1/Zb
    z_mod = inv_zb / fpv_raw
    return z_mod, True


def z_aga_nx19_mod(p_bar: float, t_degc: float, sg: float, n2_frac: float, co2_frac: float):
    """SI se puede llamar directo si sabes que querés la rama "PTB G9,
    GHV bajo" en especifico (uso avanzado -- para el uso normal, llamar
    `nx19_fpv_ghv(..., ptb_g9=True)` con un `ghv_mj_m3 < 39.8`, que elige
    esta rama automaticamente).

    Mismos parametros y unidades que `z_aga_nx19()` (bar(a)/degC/
    adimensional/fraccion 0-1) -- OJO que esta rama NO recibe GHV como
    parametro (el chequeo de umbral ya se hizo en `nx19_calc_puro()` antes
    de llegar aca).

    Devuelve tupla (Z o None, fuera_de_rango, valido) -- mismo formato que
    `z_aga_nx19()`.

    FUN_1800c9db4 -- rama ptb_g9=True, GHV<39.8 MJ/m3."""
    t_k = t_degc + 273.15
    fuera = False
    if t_degc < -40.0 or t_degc > 115.6:
        fuera = True
    if p_bar < 0.0 or p_bar > 137.9:
        fuera = True
    if sg < 0.554 or sg > 0.75:
        fuera = True
    if co2_frac < 0.0 or co2_frac > 0.15:
        fuera = True
    if n2_frac < 0.0 or n2_frac > 0.15:
        fuera = True
    if t_degc < -28.9 and p_bar > 89.63:
        fuera = True

    z, valido = _core_mod(t_k, p_bar, sg, co2_frac, n2_frac)
    return z, fuera, valido


def _correccion_3h(z_mod: float, t_k: float, p_bar: float, ghv: float, sg: float, co2_frac: float) -> float:
    """FUN_1800c994c -- polinomio multiplicativo de 9 terminos aplicado
    SOLO en la rama _3H (GHV alto), sobre P/T/GHV/SG/CO2 (NO usa N2).
    9 constantes propias (1e-12 a 1e-6), exclusivas de esta rama."""
    ghv2 = ghv * ghv
    ghv3 = ghv2 * ghv
    t2 = t_k * t_k
    p2 = p_bar * p_bar
    sg2 = sg * sg
    co2_2 = co2_frac * co2_frac

    correccion = (
        1.0
        - p_bar * 1.233507e-8 * ghv3 * sg2
        + p_bar * 9.58405e-7 * t_k
        - p_bar * 9.213982e-6 * t_k * ghv2 * sg2 * co2_2
        - p_bar * 1.76419e-8 * t2 * ghv2 * co2_2
        + p_bar * 5.449614e-8 * t2 * ghv2 * sg * co2_2
        - p_bar * 1.350988e-12 * t2 * ghv3 * co2_frac
        - p2 * 7.622085e-10 * ghv3 * co2_frac
        - p2 * 5.43367e-9 * t_k * sg2
        + p2 * 1.47958e-9 * t2 * sg2 * co2_frac
    )
    return z_mod * correccion


def z_aga_nx19_3h(p_bar: float, t_degc: float, sg: float, ghv: float, n2_frac: float, co2_frac: float):
    """SI se puede llamar directo si sabes que querés la rama "PTB G9, GHV
    alto" en especifico (uso avanzado -- para el uso normal, llamar
    `nx19_fpv_ghv(..., ptb_g9=True)` con un `ghv_mj_m3 >= 39.8`, que elige
    esta rama automaticamente).

    Mismos parametros/unidades que `z_aga_nx19_mod()` MAS `ghv` (Poder
    Calorifico Bruto, MJ/m3 -- a diferencia de `z_aga_nx19_mod()`, esta
    rama SI lo usa).

    Devuelve tupla (Z o None, fuera_de_rango, valido) -- mismo formato que
    las otras 2 ramas.

    FUN_1800c979c -- rama ptb_g9=True, GHV>=39.8 MJ/m3. Llama al mismo
    nucleo _core_mod() y APLICA ADEMAS la correccion polinomica de
    _correccion_3h()."""
    t_k = t_degc + 273.15
    fuera = False
    if ghv < 39.8 or ghv > 46.2:
        fuera = True
    if t_degc < 0.0 or t_degc > 30.0:
        fuera = True
    if p_bar < 0.0 or p_bar > 80.0:
        fuera = True
    if sg < 0.554 or sg > 0.691:
        fuera = True
    if co2_frac < 0.0 or co2_frac > 0.025:
        fuera = True
    if n2_frac < 0.0 or n2_frac > 0.07:
        fuera = True

    z_mod, valido = _core_mod(t_k, p_bar, sg, co2_frac, n2_frac)
    if z_mod is None:
        return None, fuera, valido
    z = _correccion_3h(z_mod, t_k, p_bar, ghv, sg, co2_frac)
    return z, fuera, valido


# ===========================================================================
# DESPACHADOR (FUN_1800c9500, Nx19_Calc) -- replica exacta de la logica de
# 3 ramas ya documentada en normas/NX_19.py y normas/_nx19_emulador.py,
# ahora en Python puro.
# ===========================================================================

def nx19_calc_puro(p_bar: float, t_degc: float, sg: float, ghv_mj_m3: float,
                    n2_frac: float, co2_frac: float, ptb_g9: bool):
    """Despachador -- elige automaticamente cual de las 3 ramas
    (`z_aga_nx19`/`z_aga_nx19_mod`/`z_aga_nx19_3h`) llamar, segun `ptb_g9`
    y `ghv_mj_m3` (umbral 39.79999923706055 MJ/m3, ver constante
    `_GHV_UMBRAL_3H` arriba). Mismos parametros y unidades que
    `nx19_fpv_ghv()` (ver esa funcion, mas abajo, para el uso normal --
    esta funcion devuelve un dict "crudo", `nx19_fpv_ghv()` le agrega Fpv/
    densidad/manejo de NaN encima).

    FUN_1800c9500. Devuelve dict con: z (float o None si el nucleo real
    no habria podido dar un resultado -- termino cubico no finito, o
    ecalc fuera de sus regiones tabuladas -- mismos casos en que el
    binario real devuelve un codigo de error interno, ver docstring del
    modulo), fuera_de_rango (bool), ecalc_valido (bool, informativo)."""
    if not ptb_g9:
        z, fuera, valido = z_aga_nx19(p_bar, t_degc, sg, n2_frac, co2_frac)
        return {"z": z, "fuera_de_rango": fuera, "ecalc_valido": valido, "funcion": "Z_AGA_nx19"}

    fuera_dispatch = ghv_mj_m3 < _GHV_MIN_PTB or ghv_mj_m3 > _GHV_MAX_PTB
    if ghv_mj_m3 >= _GHV_UMBRAL_3H:
        z, fuera_rama, valido = z_aga_nx19_3h(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac)
        nombre = "Z_AGA_nx19_3H"
    else:
        z, fuera_rama, valido = z_aga_nx19_mod(p_bar, t_degc, sg, n2_frac, co2_frac)
        nombre = "Z_AGA_nx19_mod"
    return {"z": z, "fuera_de_rango": fuera_dispatch or fuera_rama, "ecalc_valido": valido, "funcion": nombre}


def nx19_fpv_ghv(p_bar: float, t_degc: float, sg: float, ghv_mj_m3: float,
                  n2_frac: float, co2_frac: float, ptb_g9: bool = True) -> dict:
    """Equivalente 100% Python puro de `normas.NX_19.nx19_fpv_ghv()` --
    MISMOS parametros y MISMAS claves de salida (z, fpv, fuera_de_rango,
    d_mol_m3, fuente), pensado para un despliegue web sin `.xll` ni
    Unicorn. Ver docstring del modulo para el detalle completo de la
    formula y su validacion.

    [CERTAIN, mismo criterio que NX_19.py] Lanza ValueError si P<=0
    bar(a) o T<=-273.15 degC (datos sin sentido fisico).

    Si el nucleo real no puede dar un resultado confiable (termino cubico
    no finito, o el punto (pii,tau) cae fuera de las regiones tabuladas
    de la rama clasica -- mismos casos en que el BINARIO REAL devuelve un
    codigo de error interno en vez de un Z, confirmado contra el oraculo),
    se devuelve z=NaN explicito con un aviso -- nunca un numero fabricado."""
    if p_bar <= 0.0:
        raise ValueError(f"Presion absoluta invalida: {p_bar} bar(a) (debe ser > 0).")
    if t_degc <= -273.15:
        raise ValueError(f"Temperatura invalida: {t_degc} degC (debe ser > -273.15, cero absoluto).")

    r = nx19_calc_puro(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9)
    z = r["z"]

    aviso_no_calculable = None
    if z is None:
        z = float("nan")
        aviso_no_calculable = (
            "El nucleo cubico real (equivalente Python puro de "
            f"FUN_1800c9b04/FUN_1800c9f08, rama {r['funcion']}) no dio un "
            "resultado confiable para esta combinacion de entradas -- el "
            "binario real devuelve un codigo de error interno en este "
            "mismo caso (confirmado contra el oraculo .xll directo), no "
            "un Z utilizable. Se devuelve NaN explicito, no se fabrica un "
            "numero."
        )

    if z == z and z > 0.0:
        d_mol_m3 = (p_bar * 100.0) / (z * 8.31451 * (t_degc + 273.15)) * 1000.0
        fpv = 1.0 / math.sqrt(z)
    else:
        d_mol_m3 = float("nan")
        fpv = float("nan")

    return {
        "z": z,
        "fpv": fpv,
        "fuera_de_rango": r["fuera_de_rango"],
        "d_mol_m3": d_mol_m3,
        "fuente": f"Nx19_Calc puro Python (equivalente {r['funcion']}, "
                  "porte directo de FUN_1800c9500 y subfunciones reales de "
                  "FlowXpert.xll -- ver normas/NX_19_puro.py)",
        "ecalc_valido": r["ecalc_valido"],
        "aviso_no_calculable": aviso_no_calculable,
    }


if __name__ == "__main__":
    print("=== normas/NX_19_puro.py -- autotest metodo SG+GHV+PTB G9 vs casos reales ===")
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    z_real = 0.909911
    dif = abs(r["z"] - z_real) / z_real * 100.0
    print(f"  [caso real NX-19.jpeg] Z real={z_real}  Z calculado={r['z']:.6f}  dif={dif:.4f}%  "
          f"[{'OK' if dif < 0.02 else 'DESVIACION'}]")

    print()
    print("  Caso 2 (ptb_g9=False, struct dump real P=80/T=50/SG=0.6/GHV=40/N2=1%/CO2=2%):")
    r2 = nx19_fpv_ghv(p_bar=80.0, t_degc=50.0, sg=0.6, ghv_mj_m3=40.0,
                       n2_frac=0.01, co2_frac=0.02, ptb_g9=False)
    print(f"    Z calculado={r2['z']:.6f}")

    print()
    print("  Caso 3 (ptb_g9=True, GHV=40>=39.8 -> rama 3H, mismo struct dump real):")
    r3 = nx19_fpv_ghv(p_bar=80.0, t_degc=50.0, sg=0.6, ghv_mj_m3=40.0,
                       n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    z_real3 = 0.90975495418227474
    dif3 = abs(r3["z"] - z_real3) / z_real3 * 100.0
    print(f"    Z real(frida)={z_real3}  Z calculado={r3['z']:.8f}  dif={dif3:.6f}%  "
          f"fuera_de_rango={r3['fuera_de_rango']}  [{'OK' if dif3 < 0.02 else 'DESVIACION'}]")

    print()
    print("  Caso 4 (extremo documentado, Z>1.1 fisicamente absurdo -- limite del")
    print("  metodo NX-19 mismo, no un bug de este porte):")
    r4 = nx19_fpv_ghv(p_bar=119.0, t_degc=64.0, sg=0.89, ghv_mj_m3=47.0,
                       n2_frac=0.10, co2_frac=0.25, ptb_g9=True)
    z_real4 = 15.020379470355968
    dif4 = abs(r4["z"] - z_real4) / z_real4 * 100.0
    print(f"    Z real(frida)={z_real4}  Z calculado={r4['z']:.6f}  dif={dif4:.6f}%  "
          f"[{'OK' if dif4 < 0.02 else 'DESVIACION'}]")

    _imports = [l for l in open(__file__, encoding="utf-8")
                if l.startswith("import ") or l.startswith("from ")]
    print()
    print("  unicas lineas de import de este archivo:", [l.strip() for l in _imports])
