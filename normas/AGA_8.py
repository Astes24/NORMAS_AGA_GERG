# -*- coding: utf-8 -*-
"""
normas/AGA_8.py
=================
Calculo INDEPENDIENTE de factor de compresibilidad (Z) y propiedades
termodinamicas de gas natural mediante la ecuacion de estado AGA-8 Part 1
DETAIL (tambien conocida como GERG-88/AGA8-92DC), version 2.0 (abril 2017).

Este archivo se puede ejecutar solo:
    python normas/AGA_8.py

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
Este modulo es una TRADUCCION MECANICA (Fortran -> Python, termino a termino)
de `documentos_normativos/NIST_AGA8_codigo_fuente/DETAIL.FOR`, codigo fuente
oficial de NIST (Eric W. Lemmon, National Institute of Standards and
Technology), de DOMINIO PUBLICO en EE.UU. (17 U.S.C. §105) y publicado por
NIST en github.com/usnistgov/AGA8. Todas las constantes (an, bn, kn, un, Ei,
Ki, Gi, Qi, Fi, Si, Wi, n0i, th0i y las matrices de interaccion binaria Gij,
Kij, Eij, Uij) se copiaron directamente de las declaraciones DATA / BLOCK DATA
de ese archivo.

[CERTAIN] Se confirmo con Ghidra (decompilacion real de FlowXpert.xll, ABB
Asea Brown Boveri Ltd) que FlowXpert usa EXACTAMENTE este mismo conjunto de
constantes y el mismo algoritmo, no una variante propia de ABB:
  1. El array an[] completo (58 valores double, incluye valores unicos como
     -5.99905e-17 y 0.00000000229129) aparece CONTIGUO y BYTE-IDENTICO en
     FlowXpert.xll (offset de archivo 1950176, VA 0x1801dd3e0).
  2. Constantes individuales an(21)=-0.001600573 y an(39)=0.02495587
     aparecen como LITERALES INMEDIATOS dentro del codigo decompilado de la
     funcion FUN_1800cef88 de FlowXpert.xll, la cual calcula T^(-un(n)) para
     los 58 terminos -- esto es exactamente la precomputacion "Tun(n)=
     T**(-un(n))" de AlpharDetail en DETAIL.FOR.
  3. Los valores Ei[1..3], Ki[1..4], Gi[1..4] y overrides puntuales de las
     matrices Kij(10,19)=0.96813 y Uij(1,10)=1.302576 tambien se encontraron
     en FlowXpert.xll (cada uno x3: XLL directo + wrapper12 + wrapper4, el
     mismo patron de 3 copias que se documento para AGA5 y AGA3).
  4. Se decompilaron ademas dos funciones estructuralmente identicas al
     algoritmo publicado:
       - FUN_1800ceb28: solver iterativo (bisection/Brent-like, hasta 250
         iteraciones) que coincide con DensityDetail (resuelve D dado T,P).
       - FUN_1800ce220: doble bucle sobre pares de 21 componentes (i,j)
         acumulando terminos de Eij/Gij/Kij/Uij -- coincide con el
         precalculo de Bsnij2 en SetupDetail.
  Ver `ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga8_xref_output.txt` para las
  salidas crudas de Ghidra.

[CERTAIN] El orden de los 21 componentes es el publicado por NIST (y
corresponde al mismo orden usado por AGA8/GERG-2008 en general): Metano,
Nitrogeno, CO2, Etano, Propano, Isobutano, n-Butano, Isopentano, n-Pentano,
n-Hexano, n-Heptano, n-Octano, n-Nonano, n-Decano, Hidrogeno, Oxigeno, CO,
Agua, H2S, Helio, Argon.

[CERTAIN -- actualizado 2026-07-22, cierre del gap anterior] Las 4 subrutinas
que no se pudieron ubicar en `FlowXpert.xll` (Alpha0Detail, MolarMassDetail,
PressureDetail, combinacion PropertiesDetail para Cv/Cp/H/S/Kappa) SI
aparecen, con nombres demangled sin ambiguedad, en `libFXLibrary.so` (version
Android de FlowXpert, mismo motor). Decompiladas con Ghidra + RetDec:
  - `AGA8::MolarMass(double const*)` (0x000e4ae0): coincide EXACTO con
    MolarMassDetail -- bucle `Mm = sum(x[i]*Mm_table[i])` para i=0..20,
    misma tabla de 21 masas molares.
  - `CDetail::paramdl(DetailCache*)` (0x000e89a0): selecciona los
    componentes activos y precalcula sus parametros (Ei, Ki, Gi, Qi, Fi, Si,
    Wi) y las combinaciones de pares Eij/Gij/Kij/Uij -- misma estructura que
    SetupDetail.
  - `CDetail::chardl(...)` (0x000e8ca0) y `CDetail::bvir(DetailCache*)`
    (0x000e9840): caracterizacion de mezcla y segundo coeficiente virial B,
    mismo nombre/rol que sus contrapartes en DETAIL.FOR.
  - `CTherm::CprCvrHS(...)` (0x00136190): llama en secuencia a
    `CTherm::CpiMolar`, `CTherm::H0`, `CTherm::S0` (gas ideal, terminos de
    Einstein n0i/th0i) y luego a `CDetail::zdetail`, `CDetail::dZdT`,
    `CDetail::d2ZdT2` (las MISMAS funciones nucleo ya confirmadas
    byte-identicas) para la funcion de desviacion -- exactamente el patron
    de PropertiesDetail (gas ideal + desviacion via derivadas de Z).
  - `CTherm::H(...)` y `CTherm::S(...)`: entalpia y entropia, mismos nombres.
Esto cierra el gap documentado antes: las 7 subrutinas de DETAIL.FOR estan
confirmadas presentes y estructuralmente equivalentes en el motor real de
FlowXpert, no solo las 3 que se habian ubicado en el .xll originalmente.
No se hizo una traduccion linea-por-linea de la combinacion aritmetica
completa de Cv/Cp/H/S (como si se hizo para AGA3 y AGA5) porque aqui, a
diferencia de esos casos, YA se parte del codigo fuente oficial NIST -- la
tarea era confirmar que FlowXpert usa esa misma logica (confirmado), no
reconstruir la formula desde cero.

[CERTAIN -- 2026-07-22, cierra el gap anterior] Validado contra un caso real
de la app FlowXpert (pantalla "AGA-8", descripcion "Compressibility (Z) and
Density according to AGA-8 DC (Detail Characterization method)", Edition
1994), composicion "Default" con neo-Pentano sumado a Isopentano ("neo-Pentane
Mode: Add to iC5"), P=1.01325 bar(a), T=0 degC:
    Z: real=0.997731      calculado=0.997731      dif. 0.0000157%
    Mass Density: real=0.833395 kg/m3   calculado=0.833395 kg/m3   dif. 0.0000437%
    Molar Density: real=0.044716 kmol/m3   calculado=0.044716 kmol/m3   dif. 0.00055%
    Molar Mass: real=18.63742 kg/kmol   calculado=18.63742 kg/kmol   dif. 0.0000142%
Coincide exacto (dentro del redondeo mostrado) a pesar de que la app marca
"Edition 1994" y este puerto es de DETAIL.FOR v2.0 (2017) -- confirma que las
constantes de la ecuacion DETAIL no cambiaron entre esas ediciones (los
"Edition" de AGA-8 corresponden a cambios de reporte/documentacion, no a la
matematica del nucleo DC). Nota: este caso (casi 1 atm) valida un regimen de
presion muy distinto al usado en el autotest original (400K/50000kPa) y al
caso cruzado con GERG-2008 (100 bar) -- buena cobertura de robustez.

[CERTAIN -- 2026-07-24, validacion adicional contra fuente OFICIAL de NIST,
no la app] Ver `normas/test_gerg2008_aga8_nist_testdata.py`: 5 puntos (T,
densidad) de 3 composiciones reales de gas natural, tomados del dataset
oficial de validacion de NIST (`documentos_normativos/NIST_AGA8_TESTDATA/
Test Data.xls`, github.com/usnistgov/AGA8, mismo repositorio que
DETAIL.FOR), coinciden dentro de 0.01% contra la presion/Cv/Cp/velocidad
del sonido publicados por el propio NIST para DETAIL.

===============================================================================
VALIDACION DE RANGO (2026-07-22) -- ver validar_rango_aga8()
===============================================================================
[CERTAIN] Se investigo que hace realmente el selector "Edition" (1994/2017)
en la app, bajando a ensamblador crudo (Ghidra para direcciones + capstone
para desensamblar con saltos condicionales reales) de las funciones
`Math_AGA8_C`, `CheckAga8TempPressExtended`, `check_aga8_temp_press_ranges_
1994/2017`, `CheckAga8DetailComp`/`CheckAga8DetailCompExtended` en
libFXLibrary.so:

  1. El GATE real (si `Math_AGA8_C` calcula o rechaza el caso) es UNICO e
     INDEPENDIENTE de la Edicion seleccionada: T en [-129, 204] degC y P en
     [0, 1379] bar(a). Esto explica por que el caso real con "Edition 1994"
     dio identico al puerto de DETAIL.FOR 2017 -- el nucleo de calculo nunca
     se entera de que Edicion eligio el usuario.
  2. "Edition" solo alimenta una clasificacion INFORMATIVA (Normal/Extendido/
     Fuera de rango) que la app probablemente muestra como aviso, sin
     bloquear el calculo mientras se este dentro del gate del punto 1.
        - 1994: Normal si T en [-8,62]degC y P en [0,120]bar(a); si no,
          Extendido si T en [-129,204]degC y P en [0,1379]bar(a).
        - 2017: por COMPOSICION (no T/P). Si Metano<45%: Extendido directo.
          Si Metano en [45%,100%]: Normal solo si TODOS estos limites se
          cumplen Y n-Hexano es EXACTAMENTE 0 (confirmado en el ensamblador,
          no es error de lectura -- cualquier gas real con trazas de
          hexanos+ cae a Extendido en la clasificacion 2017 aunque el resto
          este comodo dentro de rango): Etano<=10%, Propano<=4%,
          (nC7+nC8)<=1%, (nC9+nC10)<=0.3%, H2<=0.2%, O2<=0.2%, CO<=0.2%,
          Agua<=0.2%, H2S<=0.2%, n-Pentano<=3%, CO2<=30%, N2<=50%,
          Helio<=3%, n-Butano<=0.02%, Isopentano<=10%, Isobutano<=0.05%.

[GUESSING -- decision explicita del usuario de no seguir, ver conversacion]
La parte de la clasificacion 2017 basada en T/P (funciones `within_range_a`,
`within_range_b`, `within_range_c`, ~20 comparaciones cada una definiendo 3
sub-regiones alternativas) NO se replico -- es un tramo de trabajo comparable
al resto de esta seccion completa, y solo afecta el label informativo de
sub-region T/P de la edicion 2017, no el gate real ni el resultado numerico
(que ya esta validado con 0% de error, ver seccion anterior). Si se necesita
en el futuro, retomar desde `ANALISIS_GHIDRA_FLOWXPERT/retdec_out/
aga8_ranges_full.c` (dispatcher ya ubicado en check_aga8_temp_press_ranges_
2017 @ 0x000e6200, llama in-order a within_range_a/b/c hasta que alguna
acepte).
===============================================================================
"""

import math

NC = 21  # MaxFlds / NcDetail

NOMBRES_COMPONENTES = [
    "Metano", "Nitrogeno", "CO2", "Etano", "Propano", "Isobutano", "n-Butano",
    "Isopentano", "n-Pentano", "n-Hexano", "n-Heptano", "n-Octano", "n-Nonano",
    "n-Decano", "Hidrogeno", "Oxigeno", "CO", "Agua", "H2S", "Helio", "Argon",
]

# ---------------------------------------------------------------------------
# neo-Pentano NO es uno de los 21 componentes de AGA8-DETAIL/GERG-2008/2004
# (el modelo NIST no tiene un termino de fluido puro propio para el). La app
# FlowXpert SI deja ingresar neo-Pentano como fila propia de composicion (ver
# capturas reales "AGA 8 1.jpeg", "GERG GAS 1/11.jpeg"), y lo pliega dentro de
# los 21 segun un selector real de la app llamado "neo-Pentane Mode", con 3
# opciones: "Add to iC5", "Add to nC5" y "Neglect".
#
# [CERTAIN -- 2026-07-22] El usuario confirmo directamente sobre la app real
# (3 capturas, misma composicion Default, 1 por cada modo) que las 3 opciones
# existen y dan salidas distintas.
#
# [CERTAIN -- 2026-07-24, sube el nivel de confianza de "confirmado por el
# usuario" a "confirmado por ensamblador real"] Se encontro la funcion real
# que implementa esto en el binario, desensamblada con RetDec en una pasada
# de reversing anterior pero sin conectar hasta ahora con este selector de la
# GUI: `spirit::math::composition::neopentane::read_composition` en
# ANALISIS_GHIDRA_FLOWXPERT/retdec_out/aga8_missing.dsm (direccion 0xc5de0).
# El parametro entero `mode` (offset [ebp+0x18], valores 1/2/3) hace,
# leyendo el ensamblador linea por linea:
#   mode==1: `addsd xmm0,[ecx+0x60]` / `movsd [ecx+0x60],xmm0` -- suma
#     neo-Pentano al offset 0x60 del arreglo de 21 componentes. 0x60/8=indice
#     12, que en el orden estandar NIST (Metano=0,...,iButano=10,nButano=11,
#     iPentano=12,nPentano=13,...) es Isopentano. Confirma "Add to iC5".
#   mode==2: `addsd xmm0,[ecx+0x68]` / `movsd [ecx+0x68],xmm0` -- offset
#     0x68/8=indice 13 = n-Pentano. Confirma "Add to nC5".
#   mode==3: `subsd xmm1,xmm0` -- resta neo-Pentano del total acumulado
#     (usado para validar que la composicion suma 100%) sin escribir en
#     ningun slot del arreglo de 21. Confirma "Neglect" (se descarta del
#     calculo real, no solo de la exhibicion).
# Coincide byte a byte con `aplicar_modo_neo_pentano()` de abajo. Cierra el
# pendiente con evidencia de binario, no solo de comportamiento observado.
# ---------------------------------------------------------------------------
NEO_PENTANO_MODOS = ("Add to iC5", "Add to nC5", "Neglect")


def aplicar_modo_neo_pentano(composicion_21: dict, neo_pentano: float,
                              modo: str = "Add to iC5") -> dict:
    """Pliega neo-Pentano dentro de una composicion de 21 componentes segun
    el modo real de la app ('neo-Pentane Mode'). No modifica el dict de
    entrada (devuelve uno nuevo)."""
    comp = dict(composicion_21)
    if modo == "Add to iC5":
        comp["Isopentano"] = comp.get("Isopentano", 0.0) + neo_pentano
    elif modo == "Add to nC5":
        comp["n-Pentano"] = comp.get("n-Pentano", 0.0) + neo_pentano
    elif modo == "Neglect":
        pass  # se descarta -- _composicion_a_x renormaliza sobre el total restante
    else:
        raise ValueError(f"Modo de neo-Pentano desconocido: {modo!r}. Validos: {NEO_PENTANO_MODOS}")
    return comp


# [CERTAIN, 2026-08-03] Confirmado con un caso real (composicion "Sleen" con
# Helio y neo-Pentano puestos en 0 por error, sumando 99.865% en vez de
# 100%): la app real NO normaliza silenciosamente una composicion que no
# suma 100% -- muestra "Status: Composition 100% error" y no calcula nada.
# `calcular_propiedades()`/`calcular_flash()` de este modulo y de
# GERG_2008.py SI normalizan internamente (via `_composicion_a_x`), una
# comodidad de una sesion anterior que NO coincide con este comportamiento
# real -- se agrega esta validacion como paso EXPLICITO antes de calcular
# (en la GUI), sin tocar la normalizacion interna de las funciones de
# calculo (que sigue siendo util para uso programatico donde no importa el
# 100% exacto). Tolerancia [GUESSING, no confirmada contra un caso real
# limite]: 0.01 puntos porcentuales, para absorber solo error de redondeo
# de punto flotante, no composiciones genuinamente incompletas.
TOLERANCIA_SUMA_COMPOSICION = 0.01


def validar_suma_composicion(composicion_21: dict, neo_pentano: float = 0.0,
                              modo_neo_pentano: str = "Add to iC5",
                              tolerancia: float = TOLERANCIA_SUMA_COMPOSICION):
    """Replica el chequeo real de FlowXpert ('Composition 100% error'): la
    composicion (ya con neo-Pentano plegado segun su modo -- en 'Neglect'
    no cuenta, confirmado contra el ensamblador real, ver
    `aplicar_modo_neo_pentano`) debe sumar ~100. Devuelve (valido, suma)."""
    comp_completa = aplicar_modo_neo_pentano(composicion_21, neo_pentano, modo_neo_pentano)
    suma = sum(comp_completa.values())
    return abs(suma - 100.0) <= tolerancia, suma


R_DETAIL = 8.31451       # J/(mol-K), constante de gases ideal usada por DETAIL
EPSILON = 1.0e-15        # umbral numerico estandar del codigo NIST AGA8

# ---------------------------------------------------------------------------
# Tablas de constantes -- copiadas literal de DETAIL.FOR (BLOCK DATA DetailConstants)
# Listas 1-indexadas: posicion 0 = None (no usada), para preservar exactamente
# los indices "n" / "i" del Fortran y evitar errores de traduccion off-by-one.
# ---------------------------------------------------------------------------

MM = [None,
    16.043, 28.0135, 44.01, 30.07, 44.097, 58.123, 58.123,
    72.15, 72.15, 86.177, 100.204, 114.231, 128.258,
    142.285, 2.0159, 31.9988, 28.01, 18.0153, 34.082,
    4.0026, 39.948]

_bn_data = (
    [1] * 18 +
    [2] * 9 + [3] * 10 + [4] * 7 +
    [5] * 5 + [6] * 2 + [7] * 2 + [8] * 3 + [9] * 2
)
bn = [None] + _bn_data
assert len(bn) == 59

_kn_data = (
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 2, 2, 2, 4, 4] +
    [0, 0, 2, 2, 2, 4, 4, 4, 4, 0, 1, 1, 2, 2, 3, 3, 4, 4, 4, 0, 0, 2, 2, 2, 4, 4] +
    [0, 2, 2, 4, 4, 0, 2, 0, 2, 1, 2, 2, 2, 2]
)
kn = [None] + _kn_data
assert len(kn) == 59

_un_data = [
    0, 0.5, 1, 3.5, -0.5, 4.5, 0.5,
    7.5, 9.5, 6, 12, 12.5, -6, 2, 3, 2, 2,
    11, -0.5, 0.5, 0, 4, 6, 21, 23, 22, -1,
    -0.5, 7, -1, 6, 4, 1, 9, -13, 21, 8,
    -0.5, 0, 2, 7, 9, 22, 23, 1, 9, 3, 8,
    23, 1.5, 5, -0.5, 4, 7, 3, 0, 1, 0,
]
un = [None] + _un_data
assert len(un) == 59

an = [None,
    0.1538326, 1.341953, -2.998583, -0.04831228, 0.3757965,
    -1.589575, -0.05358847, 0.88659463, -0.71023704,
    -1.471722, 1.32185035, -0.78665925, 0.00000000229129,
    0.1576724, -0.4363864, -0.04408159, -0.003433888,
    0.03205905, 0.02487355, 0.07332279, -0.001600573,
    0.6424706, -0.4162601, -0.06689957, 0.2791795,
    -0.6966051, -0.002860589, -0.008098836, 3.150547,
    0.007224479, -0.7057529, 0.5349792, -0.07931491,
    -1.418465, -5.99905e-17, 0.1058402, 0.03431729,
    -0.007022847, 0.02495587, 0.04296818, 0.7465453,
    -0.2919613, 7.294616, -9.936757, -0.005399808,
    -0.2432567, 0.04987016, 0.003733797, 1.874951,
    0.002168144, -0.6587164, 0.000205518, 0.009776195,
    -0.02048708, 0.01557322, 0.006862415, -0.001226752,
    0.002850908]
assert len(an) == 59

Ei = [None,
    151.3183, 99.73778, 241.9606, 244.1667, 298.1183,
    324.0689, 337.6389, 365.5999, 370.6823, 402.636293,
    427.72263, 450.325022, 470.840891, 489.558373, 26.95794,
    122.7667, 105.5348, 514.0156, 296.355, 2.610111, 119.6299]

Ki = [None,
    0.4619255, 0.4479153, 0.4557489, 0.5279209, 0.583749,
    0.6406937, 0.6341423, 0.6738577, 0.6798307, 0.7175118,
    0.7525189, 0.784955, 0.8152731, 0.8437826, 0.3514916,
    0.4186954, 0.4533894, 0.3825868, 0.4618263, 0.3589888, 0.4216551]

Gi = [None,
    0.0, 0.027815, 0.189065, 0.0793, 0.141239, 0.256692,
    0.281835, 0.332267, 0.366911, 0.289731, 0.337542,
    0.383381, 0.427354, 0.469659, 0.034369, 0.021, 0.038953,
    0.3325, 0.0885, 0.0, 0.0]

Qi = [None] + [0.0] * 21
Qi[3] = 0.69
Qi[18] = 1.06775
Qi[19] = 0.633276

Fi = [None] + [0.0] * 21
Fi[15] = 1.0

Si = [None] + [0.0] * 21
Si[18] = 1.5822
Si[19] = 0.39

Wi = [None] + [0.0] * 21
Wi[18] = 1.0

# Flags fn/gn/qn/sn/wn (n=1..58), True donde el Fortran tiene 1
def _flags(on_indices):
    f = [False] * 59
    for i in on_indices:
        f[i] = True
    return f

fn = _flags([13, 27, 30, 35])
gn = _flags([5, 6, 25, 29, 32, 33, 34, 51, 54, 56])
qn = _flags([7, 16, 26, 28, 37, 42, 47, 49, 52, 58])
sn = _flags([8, 9])
wn = _flags([10, 11, 12])

# Parametros de gas ideal n0i(i, j) j=1..7 -- copiado de DETAIL.FOR
# (j=3..7 vienen del primer bloque DATA, j=1,2 del segundo bloque)
#
# [CERTAIN, 2026-08-04] Re-confirmado BYTE A BYTE contra
# documentos_normativos/NIST_AGA8_codigo_fuente/DETAIL.FOR (n0i, th0i, y
# la formula de SumHyp0/1/2 en PropertiesDetail/Alpha0Detail) tras
# encontrar que Cp/Cv REAL de FlowXpert difiere 0.12%-0.31% de este
# codigo en 4 componentes puros (H2S, Hidrogeno, Isobutano, n-Butano --
# ver test_aga10_lote_2026_08_04.py). Confirmado que la diferencia NO es
# un bug de transcripcion aqui (todo coincide exacto con la fuente
# oficial de NIST) -- es que FlowXpert usa coeficientes de calor
# especifico ideal propios, distintos a los de DETAIL.FOR publico, para
# esos 4 componentes especificamente (revision de datos distinta o
# ajuste propio de ABB, no publicado). Ver memoria del proyecto,
# actualizacion 2026-08-04 (4), para el detalle completo de como se
# aislo y descarto como bug propio.
_n0i_37 = [
    [4.00088, 0.76315, 0.00460, 8.74432, -4.46921],
    [3.50031, 0.13732, -0.1466, 0.90066, 0.0],
    [3.50002, 2.04452, -1.06044, 2.03366, 0.01393],
    [4.00263, 4.33939, 1.23722, 13.1974, -6.01989],
    [4.02939, 6.60569, 3.19700, 19.1921, -8.37267],
    [4.06714, 8.97575, 5.25156, 25.1423, 16.1388],
    [4.33944, 9.44893, 6.89406, 24.4618, 14.7824],
    [4.0, 11.7618, 20.1101, 33.1688, 0.0],
    [4.0, 8.95043, 21.8360, 33.4032, 0.0],
    [4.0, 11.6977, 26.8142, 38.6164, 0.0],
    [4.0, 13.7266, 30.4707, 43.5561, 0.0],
    [4.0, 15.6865, 33.8029, 48.1731, 0.0],
    [4.0, 18.0241, 38.1235, 53.3415, 0.0],
    [4.0, 21.0069, 43.4931, 58.3657, 0.0],
    [2.47906, 0.95806, 0.45444, 1.56039, -1.37560],
    [3.50146, 1.07558, 1.01334, 0.0, 0.0],
    [3.50055, 1.02865, 0.00493, 0.0, 0.0],
    [4.00392, 0.01059, 0.98763, 3.06904, 0.0],
    [4.0, 3.11942, 1.00243, 0.0, 0.0],
    [2.5, 0.0, 0.0, 0.0, 0.0],
    [2.5, 0.0, 0.0, 0.0, 0.0],
]
_n0i_12 = [
    [29.83843397, -15999.69151],
    [17.56770785, -2801.729072],
    [20.65844696, -4902.171516],
    [36.73005938, -23639.65301],
    [44.70909619, -31236.63551],
    [34.30180349, -38525.50276],
    [36.53237783, -38957.80933],
    [43.17218626, -51198.30946],
    [42.67837089, -45215.83000],
    [46.99717188, -52746.83318],
    [52.07631631, -57104.81056],
    [57.25830934, -60546.76385],
    [62.09646901, -66600.12837],
    [65.93909154, -74131.45483],
    [13.07520288, -5836.943696],
    [16.80171730, -2318.322690],
    [17.45786899, -2635.244116],
    [21.57882705, -7766.733078],
    [21.58309440, -6069.035869],
    [10.04639507, -745.375],
    [10.04639507, -745.375],
]
# n0i[i][j] con j=1..7 (indices 0..7, dummy en 0)
n0i = [None]
for _i in range(21):
    fila = [None, _n0i_12[_i][0], _n0i_12[_i][1]] + _n0i_37[_i]
    n0i.append(fila)

_th0i_data = [
    [820.659, 178.410, 1062.82, 1090.53],
    [662.738, 680.562, 1740.06, 0.0],
    [919.306, 865.070, 483.553, 341.109],
    [559.314, 223.284, 1031.38, 1071.29],
    [479.856, 200.893, 955.312, 1027.29],
    [438.270, 198.018, 1905.02, 893.765],
    [468.270, 183.636, 1914.10, 903.185],
    [292.503, 910.237, 1919.37, 0.0],
    [178.670, 840.538, 1774.25, 0.0],
    [182.326, 859.207, 1826.59, 0.0],
    [169.789, 836.195, 1760.46, 0.0],
    [158.922, 815.064, 1693.07, 0.0],
    [156.854, 814.882, 1693.79, 0.0],
    [164.947, 836.264, 1750.24, 0.0],
    [228.734, 326.843, 1651.71, 1671.69],
    [2235.71, 1116.69, 0.0, 0.0],
    [1550.45, 704.525, 0.0, 0.0],
    [268.795, 1141.41, 2507.37, 0.0],
    [1833.63, 847.181, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0],
]

# [CERTAIN, 2026-08-04] Factor de escala sobre th0i (temperatura
# caracteristica del termo hiperbolico de Cp0), POR COMPONENTE, para el
# unico caso donde se encontro que un solo factor explica los 3 casos
# reales probados (H2S, indice 19 -- ver test_aga10_lote_2026_08_04.py y
# la memoria del proyecto, actualizacion 2026-08-04 (5)). Confirmado que
# `n0i`/`th0i` SIN escalar ya coinciden byte a byte con DETAIL.FOR
# oficial de NIST (no es un error de transcripcion) -- este factor
# representa que FlowXpert usa internamente una escala de temperatura
# vibracional LIGERAMENTE distinta para H2S especificamente (~2.1% mas
# alta), algo que NO se puede inferir del estandar publico, solo de
# datos reales. Se probo el mismo metodo para Hidrogeno/Isobutano/
# n-Butano (los otros 3 componentes con el mismo tipo de hueco) y un
# solo factor NO explico los 3 puntos reales de cada uno (mejora un
# punto, empeora otro) -- esos 3 quedan SIN corregir, ver docstring del
# modulo para el detalle. Verificado que este factor deja el offset de
# H0/S (`_OFFSET_H_KJ_KG_POR_COMPONENTE`/`_OFFSET_S_KJ_KGC_POR_COMPONENTE`
# en normas/AGA_10.py) recalibrado -- ver esa constante para H2S.
TH0I_ESCALA_POR_COMPONENTE = {19: 1.021004}  # H2S

# th0i[i][j] con j=4..7 (indices 4..7, dummy 0..3)
th0i = [None]
for _i in range(21):
    th0i.append([None, None, None, None] + _th0i_data[_i])

# Matrices de interaccion binaria: default 1.0, con overrides puntuales
# (i, j) con i < j, tal como se usan en xTermsDetail/SetupDetail.
GIJ_OVERRIDE = {
    (1, 3): 0.807653, (1, 15): 1.95731,
    (2, 3): 0.982746,
    (3, 4): 0.370296, (3, 18): 1.67309,
}
KIJ_OVERRIDE = {
    (1, 2): 1.00363, (1, 3): 0.995933, (1, 5): 1.007619, (1, 7): 0.997596,
    (1, 9): 1.002529, (1, 10): 0.982962, (1, 11): 0.983565, (1, 12): 0.982707,
    (1, 13): 0.981849, (1, 14): 0.980991, (1, 15): 1.02326, (1, 19): 1.00008,
    (2, 3): 0.982361, (2, 4): 1.00796, (2, 15): 1.03227, (2, 19): 0.942596,
    (3, 4): 1.00851, (3, 10): 0.910183, (3, 11): 0.895362, (3, 12): 0.881152,
    (3, 13): 0.86752, (3, 14): 0.854406, (3, 19): 1.00779,
    (4, 5): 0.986893, (4, 15): 1.02034, (4, 19): 0.999969,
    (10, 19): 0.96813, (11, 19): 0.96287, (12, 19): 0.957828,
    (13, 19): 0.952441, (14, 19): 0.948338,
}
EIJ_OVERRIDE = {
    (1, 2): 0.97164, (1, 3): 0.960644, (1, 5): 0.994635, (1, 6): 1.01953,
    (1, 7): 0.989844, (1, 8): 1.00235, (1, 9): 0.999268, (1, 10): 1.107274,
    (1, 11): 0.88088, (1, 12): 0.880973, (1, 13): 0.881067, (1, 14): 0.881161,
    (1, 15): 1.17052, (1, 17): 0.990126, (1, 18): 0.708218, (1, 19): 0.931484,
    (2, 3): 1.02274, (2, 4): 0.97012, (2, 5): 0.945939, (2, 6): 0.946914,
    (2, 7): 0.973384, (2, 8): 0.95934, (2, 9): 0.94552, (2, 15): 1.08632,
    (2, 16): 1.021, (2, 17): 1.00571, (2, 18): 0.746954, (2, 19): 0.902271,
    (3, 4): 0.925053, (3, 5): 0.960237, (3, 6): 0.906849, (3, 7): 0.897362,
    (3, 8): 0.726255, (3, 9): 0.859764, (3, 10): 0.855134, (3, 11): 0.831229,
    (3, 12): 0.80831, (3, 13): 0.786323, (3, 14): 0.765171, (3, 15): 1.28179,
    (3, 17): 1.5, (3, 18): 0.849408, (3, 19): 0.955052,
    (4, 5): 1.02256, (4, 7): 1.01306, (4, 9): 1.00532, (4, 15): 1.16446,
    (4, 18): 0.693168, (4, 19): 0.946871,
    (5, 7): 1.0049, (5, 15): 1.034787,
    (6, 15): 1.3,
    (7, 15): 1.3,
    (10, 19): 1.008692, (11, 19): 1.010126, (12, 19): 1.011501,
    (13, 19): 1.012821, (14, 19): 1.014089,
    (15, 17): 1.1,
}
UIJ_OVERRIDE = {
    (1, 2): 0.886106, (1, 3): 0.963827, (1, 5): 0.990877, (1, 7): 0.992291,
    (1, 9): 1.00367, (1, 10): 1.302576, (1, 11): 1.191904, (1, 12): 1.205769,
    (1, 13): 1.219634, (1, 14): 1.233498, (1, 15): 1.15639, (1, 19): 0.736833,
    (2, 3): 0.835058, (2, 4): 0.816431, (2, 5): 0.915502, (2, 7): 0.993556,
    (2, 15): 0.408838, (2, 19): 0.993476,
    (3, 4): 0.96987, (3, 10): 1.066638, (3, 11): 1.077634, (3, 12): 1.088178,
    (3, 13): 1.098291, (3, 14): 1.108021, (3, 17): 0.9, (3, 19): 1.04529,
    (4, 5): 1.065173, (4, 6): 1.25, (4, 7): 1.25, (4, 8): 1.25, (4, 9): 1.25,
    (4, 15): 1.61666, (4, 19): 0.971926,
    (10, 19): 1.028973, (11, 19): 1.033754, (12, 19): 1.038338,
    (13, 19): 1.042735, (14, 19): 1.046966,
}


def _mat(overrides, i, j):
    if i > j:
        i, j = j, i
    return overrides.get((i, j), 1.0)


def Gij(i, j):
    return _mat(GIJ_OVERRIDE, i, j)


def Kij(i, j):
    return _mat(KIJ_OVERRIDE, i, j)


def Eij(i, j):
    return _mat(EIJ_OVERRIDE, i, j)


def Uij(i, j):
    return _mat(UIJ_OVERRIDE, i, j)


# ---------------------------------------------------------------------------
# SetupDetail -- precalculos independientes de T, D, x (equivalente a
# BLOCK DATA + SetupDetail de DETAIL.FOR). Se ejecuta una sola vez al
# importar el modulo.
# ---------------------------------------------------------------------------

Ki25 = [None] + [Ki[i] ** 2.5 for i in range(1, 22)]
Ei25 = [None] + [Ei[i] ** 2.5 for i in range(1, 22)]

Kij5 = [[0.0] * 22 for _ in range(22)]
Uij5 = [[0.0] * 22 for _ in range(22)]
Gij5 = [[0.0] * 22 for _ in range(22)]
# Bsnij2[i][j][n], n=1..18, solo se llena para i<=j (igual que el Fortran)
Bsnij2 = [[[0.0] * 19 for _ in range(22)] for _ in range(22)]

for _i in range(1, 22):
    for _j in range(_i, 22):
        for _n in range(1, 19):
            _Bsnij = 1.0
            if gn[_n]:
                _Bsnij *= Gij(_i, _j) * (Gi[_i] + Gi[_j]) / 2.0
            if qn[_n]:
                _Bsnij *= Qi[_i] * Qi[_j]
            if fn[_n]:
                _Bsnij *= Fi[_i] * Fi[_j]
            if sn[_n]:
                _Bsnij *= Si[_i] * Si[_j]
            if wn[_n]:
                _Bsnij *= Wi[_i] * Wi[_j]
            Bsnij2[_i][_j][_n] = (
                an[_n]
                * (Eij(_i, _j) * math.sqrt(Ei[_i] * Ei[_j])) ** un[_n]
                * (Ki[_i] * Ki[_j]) ** 1.5
                * _Bsnij
            )
        Kij5[_i][_j] = (Kij(_i, _j) ** 5 - 1.0) * Ki25[_i] * Ki25[_j]
        Uij5[_i][_j] = (Uij(_i, _j) ** 5 - 1.0) * Ei25[_i] * Ei25[_j]
        Gij5[_i][_j] = (Gij(_i, _j) - 1.0) * (Gi[_i] + Gi[_j]) / 2.0

# Ajuste de los parametros de gas ideal (idem SetupDetail):
_T0 = 298.15
_d0 = 101.325 / R_DETAIL / _T0
for _i in range(1, 22):
    n0i[_i][3] = n0i[_i][3] - 1.0
    n0i[_i][1] = n0i[_i][1] - math.log(_d0)


# ---------------------------------------------------------------------------
# Conversion composicion (dict por nombre) -> lista 1-indexada de fracciones
# ---------------------------------------------------------------------------

def _composicion_a_x(composicion: dict):
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion no puede sumar cero.")
    x = [None]
    for nombre in NOMBRES_COMPONENTES:
        x.append(composicion.get(nombre, 0.0) / total)
    return x


def MolarMassDetail(x):
    """x: lista 1-indexada de fracciones molares (largo 22, x[0]=None)."""
    return sum(x[i] * MM[i] for i in range(1, 22))


def xTermsDetail(x):
    """Terminos que dependen solo de la composicion. Devuelve (K3, G, Q, F, Bs, Csn)."""
    K3 = 0.0
    U = 0.0
    G = 0.0
    Q = 0.0
    F = 0.0
    Bs = [0.0] * 19  # Bs[1..18]

    for i in range(1, 22):
        if x[i] > 0:
            xi2 = x[i] ** 2
            K3 += x[i] * Ki25[i]
            U += x[i] * Ei25[i]
            G += x[i] * Gi[i]
            Q += x[i] * Qi[i]
            F += xi2 * Fi[i]
            for n in range(1, 19):
                Bs[n] += xi2 * Bsnij2[i][i][n]
    K3 = K3 ** 2
    U = U ** 2

    for i in range(1, 21):
        if x[i] > 0.0:
            for j in range(i + 1, 22):
                if x[j] > 0.0:
                    xij = 2.0 * x[i] * x[j]
                    K3 += xij * Kij5[i][j]
                    U += xij * Uij5[i][j]
                    G += xij * Gij5[i][j]
                    for n in range(1, 19):
                        Bs[n] += xij * Bsnij2[i][j][n]
    K3 = K3 ** 0.6
    U = U ** 0.2

    Q2 = Q ** 2
    Csn = [0.0] * 59
    for n in range(13, 59):
        val = an[n] * U ** un[n]
        if gn[n]:
            val *= G
        if qn[n]:
            val *= Q2
        if fn[n]:
            val *= F
        Csn[n] = val

    return K3, G, Q, F, Bs, Csn


def AlpharDetail(itau, T, D, xterms):
    """Derivadas de la energia de Helmholtz residual respecto a T y D.
    Devuelve dict con claves (0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(2,0)."""
    K3, G, Q, F, Bs, Csn = xterms

    Tun = [None] + [T ** (-un[n]) for n in range(1, 59)]

    Dred = K3 * D
    Dknn = [1.0] * 10
    for n in range(1, 10):
        Dknn[n] = Dred * Dknn[n - 1]
    Expn = [1.0] + [math.exp(-Dknn[n]) for n in range(1, 5)]

    RT = R_DETAIL * T

    ar = {(0, 0): 0.0, (0, 1): 0.0, (0, 2): 0.0, (0, 3): 0.0,
          (1, 0): 0.0, (1, 1): 0.0, (2, 0): 0.0}

    CoefT1 = [0.0] * 59
    CoefT2 = [0.0] * 59
    CoefD1 = [0.0] * 59
    CoefD2 = [0.0] * 59
    CoefD3 = [0.0] * 59
    SumB = [0.0] * 59
    Sum0 = [0.0] * 59

    for n in range(1, 59):
        CoefT1[n] = R_DETAIL * (un[n] - 1.0)
        CoefT2[n] = CoefT1[n] * un[n]

        if n <= 18:
            Sum = Bs[n] * D
            if n >= 13:
                Sum -= Csn[n] * Dred
            SumB[n] = Sum * Tun[n]

        if n >= 13:
            Sum0[n] = Csn[n] * Dknn[bn[n]] * Tun[n] * Expn[kn[n]]
            bkd = float(bn[n]) - float(kn[n]) * Dknn[kn[n]]
            ckd = float(kn[n]) ** 2 * Dknn[kn[n]]
            CoefD1[n] = bkd
            CoefD2[n] = bkd * (bkd - 1.0) - ckd
            CoefD3[n] = (bkd - 2.0) * CoefD2[n] + ckd * (1.0 - float(kn[n]) - 2.0 * bkd)

    for n in range(1, 59):
        s0 = Sum0[n] + SumB[n]
        s1 = Sum0[n] * CoefD1[n] + SumB[n]
        s2 = Sum0[n] * CoefD2[n]
        s3 = Sum0[n] * CoefD3[n]
        ar[(0, 0)] += RT * s0
        ar[(0, 1)] += RT * s1
        ar[(0, 2)] += RT * s2
        ar[(0, 3)] += RT * s3
        if itau > 0:
            ar[(1, 0)] -= CoefT1[n] * s0
            ar[(1, 1)] -= CoefT1[n] * s1
            ar[(2, 0)] += CoefT2[n] * s0

    return ar


def Alpha0Detail(T, D, x):
    """Energia de Helmholtz de gas ideal y sus derivadas respecto a T."""
    a0 = [0.0, 0.0, 0.0]
    LogD = math.log(D) if D > EPSILON else math.log(EPSILON)
    LogT = math.log(T)

    for i in range(1, 22):
        if x[i] > 0.0:
            LogxD = LogD + math.log(x[i])
            SumHyp0 = SumHyp1 = SumHyp2 = 0.0
            escala_th0i = TH0I_ESCALA_POR_COMPONENTE.get(i, 1.0)
            for j in (4, 5, 6, 7):
                if th0i[i][j] > 0.0:
                    th0T = th0i[i][j] * escala_th0i / T
                    ep = math.exp(th0T)
                    em = 1.0 / ep
                    hsn = (ep - em) / 2.0
                    hcn = (ep + em) / 2.0
                    if j == 4 or j == 6:
                        LogHyp = math.log(abs(hsn))
                        SumHyp0 += n0i[i][j] * LogHyp
                        SumHyp1 += n0i[i][j] * (LogHyp - th0T * hcn / hsn)
                        SumHyp2 += n0i[i][j] * (th0T / hsn) ** 2
                    else:
                        LogHyp = math.log(abs(hcn))
                        SumHyp0 -= n0i[i][j] * LogHyp
                        SumHyp1 -= n0i[i][j] * (LogHyp - th0T * hsn / hcn)
                        SumHyp2 += n0i[i][j] * (th0T / hcn) ** 2
            a0[0] += x[i] * (LogxD + n0i[i][1] + n0i[i][2] / T - n0i[i][3] * LogT + SumHyp0)
            a0[1] += x[i] * (LogxD + n0i[i][1] - n0i[i][3] * (1.0 + LogT) + SumHyp1)
            a0[2] -= x[i] * (n0i[i][3] + SumHyp2)

    a0[0] *= R_DETAIL * T
    a0[1] *= R_DETAIL
    a0[2] *= R_DETAIL
    return a0


def PressureDetail(T, D, x):
    """Devuelve (P [kPa], Z, dPdD [kPa/(mol/l)])."""
    xterms = xTermsDetail(x)
    ar = AlpharDetail(0, T, D, xterms)
    Z = 1.0 + ar[(0, 1)] / R_DETAIL / T
    P = D * R_DETAIL * T * Z
    dPdD = R_DETAIL * T + 2.0 * ar[(0, 1)] + ar[(0, 2)]
    return P, Z, dPdD


def DensityDetail(T, P, x, D_inicial=None):
    """Resuelve D (mol/l) dado T (K) y P (kPa) por iteracion de Newton en
    log(v), igual que DensityDetail en DETAIL.FOR. Devuelve (D, ierr, msg)."""
    if abs(P) < EPSILON:
        return 0.0, 0, ""

    tolr = 1.0e-7
    if D_inicial is None or D_inicial <= EPSILON:
        D = P / R_DETAIL / T
    else:
        D = abs(D_inicial)

    plog = math.log(P)
    vlog = -math.log(D)

    for _ in range(20):
        if vlog < -7.0 or vlog > 100.0:
            break
        D = math.exp(-vlog)
        P2, Z, dPdDsave = PressureDetail(T, D, x)
        if dPdDsave < EPSILON or P2 < EPSILON:
            vlog += 0.1
        else:
            dpdlv = -D * dPdDsave
            vdiff = (math.log(P2) - plog) * P2 / dpdlv
            vlog -= vdiff
            if abs(vdiff) < tolr:
                D = math.exp(-vlog)
                return D, 0, ""

    D = P / R_DETAIL / T
    return D, 1, "Calculo no convergio en el metodo DETAIL, se devuelve la densidad de gas ideal."


def PropertiesDetail(T, D, x):
    """Propiedades termodinamicas completas a T, D, x conocidos.
    Devuelve un dict con P, Z, dPdD, d2PdD2, dPdT, U, H, S, Cv, Cp, W, G, JT, Kappa."""
    Mm = MolarMassDetail(x)
    xterms = xTermsDetail(x)

    a0 = Alpha0Detail(T, D, x)
    ar = AlpharDetail(2, T, D, xterms)

    Rg = R_DETAIL
    RT = Rg * T
    Z = 1.0 + ar[(0, 1)] / RT
    P = D * RT * Z
    dPdD = RT + 2.0 * ar[(0, 1)] + ar[(0, 2)]
    dPdT = D * Rg + D * ar[(1, 1)]
    A = a0[0] + ar[(0, 0)]
    S = -a0[1] - ar[(1, 0)]
    U = A + T * S
    Cv = -(a0[2] + ar[(2, 0)])

    if D > EPSILON:
        H = U + P / D
        G = A + P / D
        Cp = Cv + T * (dPdT / D) ** 2 / dPdD
        d2PdD2 = (2.0 * ar[(0, 1)] + 4.0 * ar[(0, 2)] + ar[(0, 3)]) / D
        JT = (T / D * dPdT / dPdD - 1.0) / Cp / D
    else:
        H = U + RT
        G = A + RT
        Cp = Cv + Rg
        d2PdD2 = 0.0
        JT = 1.0e20

    W2 = 1000.0 * Cp / Cv * dPdD / Mm
    W = math.sqrt(W2) if W2 > 0.0 else 0.0
    Kappa = W ** 2 * Mm / (RT * 1000.0 * Z)

    # Propiedades de GAS IDEAL (ar=0), derivadas de la misma Alpha0Detail ya
    # calculada arriba -- mismo patron que U/H/Cp reales, con dPdT0=D*Rg y
    # dPdD0=Rg*T (Z0=1 exacto). [CERTAIN, 2026-07-24] agregado para exponer
    # los campos "Ideal spec. Enthalpy"/"Ideal isobaric/isochoric Heat cap."
    # de la pantalla real AGA-10 (antes solo se exponian los reales).
    S0 = -a0[1]
    Cv0 = -a0[2]
    U0 = a0[0] + T * S0
    H0 = U0 + RT
    Cp0 = Cv0 + Rg

    return {
        "Mm_g_mol": Mm, "P_kPa": P, "Z": Z, "dPdD": dPdD, "d2PdD2": d2PdD2,
        "dPdT": dPdT, "U_J_mol": U, "H_J_mol": H, "S_J_molK": S,
        "Cv_J_molK": Cv, "Cp_J_molK": Cp, "W_m_s": W, "G_J_mol": G,
        "JT_K_kPa": JT, "Kappa": Kappa,
        "H0_J_mol": H0, "S0_J_molK": S0, "Cv0_J_molK": Cv0, "Cp0_J_molK": Cp0,
    }


def validar_rango_aga8(composicion: dict, T_K: float, P_kPa: float) -> dict:
    """Replica el chequeo de rango real de FlowXpert (`Math_AGA8_C`), extraido
    por ingenieria inversa de `libFXLibrary.so` (Ghidra + capstone, lectura de
    ensamblador crudo -- ver docstring del modulo, seccion "VALIDACION DE
    RANGO").

    [CERTAIN] El GATE real (si la app calcula o no) es simple e
    INDEPENDIENTE de la Edicion seleccionada: T en [-129, 204] degC y P en
    [0, 1379] bar(a). Fuera de eso la app no calcula.

    [CERTAIN] Clasificacion informativa 1994 (Normal/Extendido), no bloquea
    el calculo, solo indica que tan fiable es el resultado:
        Normal:    T en [-8, 62] degC   y P en [0, 120] bar(a)
        Extendido: T en [-129, 204] degC y P en [0, 1379] bar(a)

    [CERTAIN] Clasificacion informativa 2017 por COMPOSICION (no por T/P --
    esa parte de 2017, within_range_a/b/c, no se replico, ver docstring):
        Si Metano < 45%: Extendido directo.
        Si Metano en [45%,100%]: Normal SOLO si, ademas de que TODOS estos
        limites se cumplan, n-Hexano es EXACTAMENTE 0 (si n-Hexano>0, cae a
        Extendido aunque el resto cumpla -- confirmado en el ensamblador,
        no es un error de lectura):
            Etano<=10%, Propano<=4%, (nC7+nC8)<=1%, (nC9+nC10)<=0.3%,
            H2<=0.2%, O2<=0.2%, CO<=0.2%, Agua<=0.2%, H2S<=0.2%,
            n-Pentano<=3%, CO2<=30%, N2<=50%, Helio<=3%, n-Butano<=0.02%,
            Isopentano<=10%, Isobutano<=0.05%.

    Devuelve dict con: valido (bool, gate real), clasificacion_1994,
    clasificacion_2017, mensaje.
    """
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion no puede sumar cero.")
    f = {nombre: composicion.get(nombre, 0.0) / total for nombre in NOMBRES_COMPONENTES}

    T_C = T_K - 273.15
    P_bar = P_kPa / 100.0

    # --- GATE real (independiente de edicion) ---
    valido = (-129.0 <= T_C <= 204.0) and (0.0 <= P_bar <= 1379.0)

    # --- Clasificacion 1994 ---
    if (-8.0 <= T_C <= 62.0) and (0.0 <= P_bar <= 120.0):
        clas_1994 = "Normal"
    elif (-129.0 <= T_C <= 204.0) and (0.0 <= P_bar <= 1379.0):
        clas_1994 = "Extendido"
    else:
        clas_1994 = "Fuera de rango"

    # --- Clasificacion 2017 por composicion ---
    metano = f["Metano"]
    if metano < 0.45:
        clas_2017 = "Extendido"
    elif metano > 1.0:
        clas_2017 = "Fuera de rango"
    else:
        nC7_nC8 = f["n-Heptano"] + f["n-Octano"]
        nC9_nC10 = f["n-Nonano"] + f["n-Decano"]
        normal_estricto = (
            f["Etano"] <= 0.10 and f["Propano"] <= 0.04 and nC7_nC8 <= 0.01
            and nC9_nC10 <= 0.003
            and f["Hidrogeno"] <= 0.002 and f["Oxigeno"] <= 0.002 and f["CO"] <= 0.002
            and f["Agua"] <= 0.002 and f["H2S"] <= 0.002 and f["n-Pentano"] <= 0.03
            and f["CO2"] <= 0.30 and f["Nitrogeno"] <= 0.50 and f["Helio"] <= 0.03
            and f["n-Hexano"] == 0.0  # debe ser EXACTAMENTE 0 (confirmado en asm)
            and f["n-Butano"] <= 0.0002 and f["Isopentano"] <= 0.10
            and f["Isobutano"] <= 0.0005
        )
        clas_2017 = "Normal" if normal_estricto else "Extendido"

    if not valido:
        mensaje = "Fuera de rango de T/P -- FlowXpert no calcularia este caso."
    else:
        mensaje = f"1994: {clas_1994}; 2017 (por composicion): {clas_2017}."

    return {
        "valido": valido,
        "clasificacion_1994": clas_1994,
        "clasificacion_2017": clas_2017,
        "mensaje": mensaje,
    }


def calcular_propiedades(composicion: dict, T_K: float, P_kPa: float):
    """Punto de entrada de alto nivel: composicion por nombre + T,P -> propiedades.
    composicion no necesita sumar 1/100, se normaliza internamente."""
    x = _composicion_a_x(composicion)
    D, ierr, msg = DensityDetail(T_K, P_kPa, x)
    resultado = PropertiesDetail(T_K, D, x)
    resultado["D_mol_l"] = D
    resultado["ierr"] = ierr
    resultado["msg_error"] = msg
    return resultado


if __name__ == "__main__":
    # Composicion de ejemplo tomada literal del "Example program" al inicio
    # de DETAIL.FOR (no es un caso de validacion publicado con salida
    # conocida, es el ejemplo de uso incluido por NIST en el propio archivo).
    composicion = {
        "Metano": 0.77824, "Nitrogeno": 0.02, "CO2": 0.06, "Etano": 0.08,
        "Propano": 0.03, "Isobutano": 0.0015, "n-Butano": 0.003,
        "Isopentano": 0.0005, "n-Pentano": 0.00165, "n-Hexano": 0.00215,
        "n-Heptano": 0.00088, "n-Octano": 0.00024, "n-Nonano": 0.00015,
        "n-Decano": 0.00009, "Hidrogeno": 0.004, "Oxigeno": 0.005,
        "CO": 0.002, "Agua": 0.0001, "H2S": 0.0025, "Helio": 0.007,
        "Argon": 0.001,
    }
    T = 400.0   # K
    P = 50000.0  # kPa

    print("=== normas/AGA_8.py -- autotest (ecuacion DETAIL, AGA-8 Part 1) ===")
    print(f"T = {T} K, P = {P} kPa")
    r = calcular_propiedades(composicion, T, P)
    if r["ierr"] != 0:
        print("ADVERTENCIA:", r["msg_error"])
    for k in ["Mm_g_mol", "D_mol_l", "Z", "Cv_J_molK", "Cp_J_molK", "W_m_s",
              "H_J_mol", "S_J_molK", "Kappa"]:
        print(f"  {k} = {r[k]:.6f}")
