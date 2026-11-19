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

[CERTAIN -- RONDA 55, 2026-09-16] Re-confirmacion de "neo-Pentane Mode" para
las 4 pantallas que usan este motor (AGA8 GERG, GERG-2008 Gas, GERG-2008
Flash -- todas via `Math_GERG2008_Gas`/`Math_GERG2008_Flash` real, ver
arriba -- y GERG-2004 Gas/Flash, ver `normas/GERG_2004.py`, alias fino de
este mismo archivo). Manual oficial (`Flow-X Manual IIIb - Function
Reference`, fxAGA8_GERG pag. 17, fxGERG2008_Gas pag. 87, fxGERG2008_Flash
pag. 86) documenta Default "1: Add to i-Pentane" para las 3 funciones con
tabla propia (fxGERG2004_Gas/_Flash no tienen tabla propia en el manual,
dice literalmente "available for compatibility reasons only... succeeded
by function fxGERG2008_Gas/_Flash"). Confirmado en vivo con AVD
`flowxpert_rd` DESPUES de `pm clear` (reset de fabrica, primera apertura
real de cada pantalla -- importante: se descubrio esta ronda que FlowXpert
persiste el ultimo valor usado POR PANTALLA entre sesiones, asi que una
lectura sin este reset puede ser un valor de prueba viejo, no el default
real, ver nota completa en `normas/GPA_2172.py`): las 4 pantallas
(AGA8 GERG, GERG-2008 Gas, GERG-2008 Flash, GERG-2004 Gas, GERG-2004 Flash
-- 5 en total) muestran "Add to iC5" de fabrica, coincidiendo con el
manual y con el default compartido de `_build_composicion_grid_con_neo`.
Sin cambios de codigo necesarios para estas 5 pantallas.

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

# ---------------------------------------------------------------------------
# neo-Pentano -- "neo-Pentane Mode" (Add to iC5 / Add to nC5 / Neglect), igual
# selector real de la app que en AGA_8.py (ver docstring de
# `aplicar_modo_neo_pentano` alla para el detalle de "Add to iC5"/
# "Add to nC5" -- IDENTICOS aca, confirmado).
#
# [CERTAIN -- RONDA 56, 2026-09-16, INVESTIGACION COMPLETA] Se penso al
# principio de esta ronda que el modo "Neglect" seria un mecanismo distinto
# COMPARTIDO por las 5 pantallas del motor GERG-2008 (AGA8 GERG, GERG-2008
# Gas, GERG-2008 Flash, GERG-2004 Gas, GERG-2004 Flash) frente a AGA8-DETAIL/
# AGA-10 -- ESO ERA INCOMPLETO. Confirmado en vivo (AVD `flowxpert_rd`,
# composicion "Default", neo-Pentano=0.008, P=100 bar(a)/T=25 degC, LAS 5
# pantallas probadas con AMBOS modos "Add to nC5" y "Neglect"):
#   AGA-10 (P=1.01325 bar(a)/T=0 degC), GERG-2008 Gas y GERG-2008 Flash:
#     real Neglect Z=0.865283 (GERG-2008)/Mm=18.63314 (AGA-10) -- coincide
#     EXACTO con renormalizar sobre el total de los 13-14 componentes
#     RESTANTES (excluye neo-Pentano de la suma), el MISMO mecanismo que
#     `AGA_8.aplicar_modo_neo_pentano` (sin cambios) ya implementaba
#     correctamente desde antes de esta ronda.
#   GERG-2004 Gas y GERG-2004 Flash (MISMA composicion/T/P, MISMO Add to
#   nC5 que si coincide con GERG-2008 en ese modo): real Neglect Z=0.865392,
#     Density=86.84751 kg/m3 -- NO coincide con renormalizar sobre el
#     restante (esa hipotesis da Z=0.865283, la de GERG-2008/AGA-10), SI
#     coincide exacto con la hipotesis alternativa: las fracciones molares
#     se calculan dividiendo el valor crudo de cada componente por el total
#     ORIGINAL de 100 (NO 100-neo=99.992), dejando un hueco real en la suma
#     de fracciones molares (99.992/100=0.99992, no 1.0 exacto).
# CONCLUSION: pese a que GERG-2004 Gas/Flash y GERG-2008 Gas/Flash llaman al
# MISMO motor de calculo real (`Math_GERG2008_Gas`/`Math_GERG2008_Flash`,
# ver docstring del modulo mas arriba, y "Add to iC5"/"Add to nC5" SI dan
# resultados identicos entre ambas), el modo "Neglect" especificamente SI
# difiere entre GERG-2004 y GERG-2008 -- son 2 rutinas de "lectura de
# composicion" distintas en el binario (ya se sabia que GERG2004 usa un
# selector de tipo propio, DAT_1802f24f0 vs DAT_1802c7340, ver
# `normas/GERG_2004.py`), y esta ronda confirma que esa diferencia SI tiene
# consecuencias numericas reales para "Neglect" (la unica de las 3 opciones
# donde importa como se recalcula el total). AGA8 GERG (wrapper literal de
# GERG-2008 Gas, confirmado por decompilacion) se comporta como GERG-2008,
# NO como GERG-2004.
# Implementacion (solo para GERG-2004 Gas/Flash): se preserva `neo_pentano`
# bajo `_NEO_PENTANO_NEGLECT_KEY` (nombre reservado, fuera de los 21
# validos) para que `sum(composicion.values())` -- el patron que usa
# `_composicion_a_x` de este archivo -- siga dividiendo por el total
# ORIGINAL (100), sin que la key se confunda con ningun componente real
# (`_composicion_a_x` solo lee los 21 nombres de `NOMBRES_COMPONENTES` via
# `.get(nombre, 0.0)`).
#
# [CERTAIN -- RONDA 57, 2026-09-16] La conclusion de arriba ("AGA8 GERG se
# comporta como GERG-2008, NO como GERG-2004") quedaba sin confirmar en vivo
# para "Neglect" especificamente en la pantalla "AGA8 GERG" (RONDA 56 probo
# las otras 4 pantallas del grupo -- AGA-10, GERG-2008 Gas/Flash, GERG-2004
# Gas/Flash -- pero no esta, y se habia dejado como supuesto por analogia de
# decompilacion). Confirmado en vivo (AVD `flowxpert_rd`, pantalla "AGA8
# GERG", composicion "Default" (neo-Pentano=0.008), P=100 bar(a), T=25 degC
# -- MISMO caso real ya documentado arriba para "Add to iC5" (Z=0.865194),
# ahora con "neo-Pentane Mode: Neglect"):
#   real Neglect: Z=0.865283, Mass Density=86.86535 kg/m3,
#   Molar Density=4.661998 kmol/m3, Molar Mass=18.63264 kg/kmol,
#   Speed of Sound=415.5392 m/s.
# Coincide EXACTO (dentro del redondeo que muestra la app) con
# `AGA_8.aplicar_modo_neo_pentano` (Z calculado=0.865283, D_mass=86.865346,
# D_mol=4.661998, Mm=18.632643, W=415.539204 -- la funcion que YA usa
# `on_calcular_gerg2008` en `interfaz_calculo_flujo.py`), y NO con
# `aplicar_modo_neo_pentano_gerg` (esa da Z=0.865392, distinto). Confirma
# la conclusion de RONDA 56 con evidencia real propia de esta pantalla, no
# solo por analogia de decompilacion. CERO cambio de codigo necesario: el
# handler de "AGA8 GERG" ya estaba correcto.
# ---------------------------------------------------------------------------
_NEO_PENTANO_NEGLECT_KEY = "__neo_pentano_neglected__"


def aplicar_modo_neo_pentano_gerg(composicion_21: dict, neo_pentano: float,
                                   modo: str = "Add to iC5") -> dict:
    """Version SOLO para las pantallas 'GERG-2004 Gas' y 'GERG-2004 Flash'
    (`normas/GERG_2004.py`) de `AGA_8.aplicar_modo_neo_pentano` -- MISMO
    comportamiento en 'Add to iC5'/'Add to nC5', pero 'Neglect' DISTINTO (no
    renormaliza sobre el total restante). NO usar para 'AGA8 GERG',
    'GERG-2008 Gas' ni 'GERG-2008 Flash' -- esas 3 pantallas usan
    `AGA_8.aplicar_modo_neo_pentano` sin cambios (confirmado real, ver nota
    arriba). No modifica el dict de entrada."""
    comp = dict(composicion_21)
    if modo == "Add to iC5":
        comp["Isopentano"] = comp.get("Isopentano", 0.0) + neo_pentano
    elif modo == "Add to nC5":
        comp["n-Pentano"] = comp.get("n-Pentano", 0.0) + neo_pentano
    elif modo == "Neglect":
        if neo_pentano:
            comp[_NEO_PENTANO_NEGLECT_KEY] = neo_pentano
    else:
        raise ValueError(
            f"Modo de neo-Pentano desconocido: {modo!r}. Validos: (\"Add to iC5\", \"Add to nC5\", \"Neglect\")")
    return comp


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


def _exp_c(v):
    """exp con semantica IEEE de C (inf en desborde, sin excepcion) [C-43]: FlowXpert evalua la EOS en densidades
    extrapoladas absurdas (p. ej. negativas) dentro de FindDensity y sigue iterando con el resultado."""
    try:
        return math.exp(v)
    except OverflowError:
        return float("inf")


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
    Expd[1] = _exp_c(-delp[1])
    for i in range(2, 8):
        delp[i] = delp[i - 1] * del_
        Expd[i] = _exp_c(-delp[i])

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
                                   _exp_c(cij0 + eij0 + g_mnk + t_mnk * lntau))
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


# =============================================================================
# [C-43, 2026-11-18] Seleccion de la raiz de densidad igual que FlowXpert
# =============================================================================
# [Certain, desensamblado de libFXLibrary.so + decompilacion Ghidra de GERG2008::CEquation::TERMO/CalcDensity/
# BracketDensities/FindDensity/FindFirstRoot/CalculateDensity y GERG2008::SolvePengRobinsonEOS/SolveCubicEquation/
# CMixture::CalcXaXb/Init] FlowXpert no usa Newton desde gas ideal: resuelve Peng-Robinson para obtener densidades
# semilla, acota la raiz GERG alrededor de la semilla (dP/dD >= 0) y la refina (regula falsi). Las pantallas "Gas"
# (GERG-2008 Gas, GERG-2004 Gas, AGA8 GERG) piden fase 1 (vapor: con 2-3 raices PR usa la semilla de menor densidad);
# el flash, para la alimentacion monofasica, pide fase 0 (la de menor energia de Gibbs entre vapor y liquido).
# Antes (DensityGERG desde gas ideal) daba la raiz equivocada o ierr=1 en 17 de 240 estados densos; este port
# coincide con FX (emulador Unicorn) en ese barrido. Unidades internas como en FX: MPa, mol/dm3, R = 0.008314472.
# Datos PR del binario (CData::s_TKRIT [K], s_PKRIT [MPa], s_AZT) y kij (CData::s_XKIJ), en el orden de este modulo.
_PR_TC_PC_W = {
    1: (190.56, 4.599, 0.011), 2: (126.2, 3.398, 0.037), 3: (304.12, 7.374, 0.225), 4: (305.32, 4.872, 0.099),
    5: (369.83, 4.248, 0.152), 6: (407.85, 3.64, 0.186), 7: (425.12, 3.796, 0.2), 8: (460.39, 3.381, 0.229),
    9: (469.7, 3.37, 0.252), 10: (507.6, 3.025, 0.3), 11: (540.2, 2.74, 0.35), 12: (568.7, 2.49, 0.399),
    13: (594.6, 2.29, 0.445), 14: (617.7, 2.11, 0.49), 15: (33.25, 1.297, -0.216), 16: (154.58, 5.043, 0.025),
    17: (132.85, 3.494, 0.045), 18: (647.14, 22.064, 0.344), 19: (373.4, 8.963, 0.09), 20: (5.19, 0.227, -0.39),
    21: (150.86, 4.898, -0.002),
}
_PR_KIJ = {
    (1, 2): 0.0311, (1, 3): 0.0919, (1, 4): -0.0026, (1, 5): 0.014, (1, 6): 0.0256, (1, 7): 0.0133,
    (1, 8): -0.0056, (1, 9): 0.023, (1, 10): 0.0422, (1, 11): 0.0352, (1, 12): 0.0496, (1, 13): 0.0474,
    (1, 14): 0.0422, (1, 15): 0.0156, (1, 17): 0.03, (1, 21): 0.023, (2, 3): -0.017, (2, 4): 0.0515,
    (2, 5): 0.0852, (2, 6): 0.1033, (2, 7): 0.08, (2, 8): 0.0922, (2, 9): 0.1, (2, 10): 0.1496,
    (2, 11): 0.1441, (2, 15): 0.103, (2, 16): -0.0119, (2, 17): 0.0307, (2, 19): 0.1767, (2, 21): -0.0026,
    (3, 4): 0.1322, (3, 5): 0.1241, (3, 6): 0.12, (3, 7): 0.1333, (3, 8): 0.1219, (3, 9): 0.1222,
    (3, 10): 0.11, (3, 11): 0.1, (3, 14): 0.1141, (3, 15): -0.1622, (3, 18): 0.12, (3, 19): 0.0974,
    (4, 5): 0.0011, (4, 6): -0.0067, (4, 7): 0.0096, (4, 9): 0.0078, (4, 10): -0.01, (4, 11): 0.0067,
    (4, 12): 0.0185, (4, 14): 0.0144, (4, 15): -0.0667, (4, 17): -0.0226, (4, 19): 0.0833, (5, 6): -0.0078,
    (5, 7): 0.0033, (5, 8): 0.0111, (5, 9): 0.0267, (5, 10): 0.0007, (5, 11): 0.0056, (5, 15): -0.0833,
    (5, 17): 0.0259, (5, 19): 0.0878, (6, 7): -0.0004, (6, 19): 0.0474, (7, 9): 0.0174, (7, 10): -0.0056,
    (7, 11): 0.0033, (7, 14): 0.0078, (7, 15): -0.397, (8, 9): 0.06, (9, 11): 0.0074, (9, 19): 0.063,
    (10, 11): -0.0078, (10, 15): -0.03, (11, 15): -0.1167, (15, 17): 0.0919, (16, 21): 0.0104, (17, 19): 0.0544,
    (18, 19): 0.04,
}
_R_FX = 0.008314472  # MPa dm3/(mol K)
FASE_FX_ESTABLE, FASE_FX_VAPOR, FASE_FX_LIQUIDO = 0, 1, 2


class _SinRaizFX(Exception):
    pass


def _pr_mezcla(T, x):
    """(a, b) de Peng-Robinson de la mezcla (CMixture::CalcXaXb + Init): solo componentes con x > 1e-10,
    fracciones normalizadas."""
    comp = [i for i in range(1, 22) if x[i] > 1e-10]
    s = sum(x[i] for i in comp)
    ai, bi = {}, {}
    for i in comp:
        tc, pc, w = _PR_TC_PC_W[i]
        m = 0.37464 + 1.54226 * w - w * (0.26992 * w)
        alfa = (1.0 + m * (1.0 - math.sqrt(T / tc))) ** 2
        ai[i] = alfa * (3.160920450663759e-05 * tc * tc / pc)
        bi[i] = 0.0006468659215999999 * tc / pc
    a = b = 0.0
    for i in comp:
        xi = x[i] / s
        for j in comp:
            k = _PR_KIJ.get((i, j) if i < j else (j, i), 0.0) if i != j else 0.0
            a += math.sqrt(ai[j] * ai[i]) * (1.0 - k) * (x[j] / s) * xi
        b += bi[i] * xi
    return a, b


def _cubica_fx(p1, p2, p3):
    """GERG2008::SolveCubicEquation: raices reales de z^3 + p1 z^2 + p2 z + p3 = 0 (1, 2 o 3)."""
    q = (3.0 * p2 - p1 * p1) / 9.0
    r = ((p2 * 9.0 * p1 - 27.0 * p3) - (p1 + p1) * p1 * p1) / 54.0
    disc = q * q * q + r * r
    if disc >= 0.0:
        sq = math.sqrt(disc)
        s = r + sq
        s = -math.pow(-s, 1.0 / 3.0) if s < 0.0 else math.pow(s, 1.0 / 3.0)
        t = r - sq
        t = -math.pow(-t, 1.0 / 3.0) if t < 0.0 else math.pow(t, 1.0 / 3.0)
        z0 = (s + t) - p1 / 3.0
        if abs(s - t) < 1e-20:
            z1 = (s + t) * -0.5 - p1 / 3.0
            return [z0, z1] if abs(z1 - z0) >= 1e-20 else [z0]
        return [z0]
    th = math.acos(r / math.sqrt(q * -q * q))
    dos = 2.0 * math.sqrt(-q)
    return [math.cos(th / 3.0) * dos - p1 / 3.0, math.cos((th + 6.283185307179586) / 3.0) * dos - p1 / 3.0,
            math.cos((th + 12.566370614359172) / 3.0) * dos - p1 / 3.0]


def _semillas_pr(T, P, x):
    """GERG2008::SolvePengRobinsonEOS -> (ok, [rho_max, rho_min], n_raices (0, 1 o 2), b)."""
    if T < 1e-6 or P < 1e-6:
        return False, None, 0, 0.0
    a, b = _pr_mezcla(T, x)
    rt = _R_FX * T
    A = a * P / (rt * rt)
    B = P * b / rt
    zs = _cubica_fx(B - 1.0, (A - 3.0 * B * B) - (B + B), (B * B * B + B * B) - A * B)
    validas = []
    for z in zs:
        rho = P / (z * rt) if z != 0.0 else -1.0
        if 0.0 < rho < 1.0 / b:
            validas.append(rho)
    if not validas:
        return True, [0.0, 1e100], 0, b
    return True, [max(validas), min(validas)], min(len(validas), 2), b


def _p_fx(T, D, x):
    """CEquation::PB en MPa. Fuera de rango (densidad extrapolada absurda) el C de FX da inf/NaN sin excepcion;
    aqui se devuelve NaN para que las comparaciones sigan la misma rama (todas falsas)."""
    try:
        return PressureGERG(T, D, x)[0] / 1000.0
    except (OverflowError, ValueError, ZeroDivisionError):
        return float("nan")


def _dpdd_fx(T, D, x):
    """CEquation::DPDDB: (P [MPa], dP/dD [MPa dm3/mol])."""
    try:
        p, _z, dpdd = PressureGERG(T, D, x)
    except (OverflowError, ValueError, ZeroDivisionError):
        return float("nan"), float("nan")
    return p / 1000.0, dpdd / 1000.0


def _acotar_fx(T, P, x, rho, vapor, una_raiz):
    """CEquation::BracketDensities -> (ok, lo, hi)."""
    if P < 1e-5:
        return True, 0.95 * rho, 1.05 * rho
    if vapor:
        f_lo, mult, f_hi = 0.95, 0.9900990099009901, 1.05
    else:
        f_lo, mult, f_hi = 0.88, 1.01, 1.08
    r = rho
    for it in range(51):
        p_r, d_r = _dpdd_fx(T, r, x)
        if d_r >= 0.0:
            lo, hi = f_lo * r, f_hi * r
            if it != 0:
                if vapor:
                    hi = r
                else:
                    lo = r
            break
        r *= mult
    else:
        return False, 0.0, 0.0
    n = 51
    while True:
        p_lo, d_lo = _dpdd_fx(T, lo, x)
        if d_lo >= 0.0:
            if r < lo:
                p_lo, lo = p_r, r
            break
        n -= 1
        lo *= 1.01
        if n == 0:
            return False, 0.0, 0.0
    n = 51
    while True:
        p_hi, d_hi = _dpdd_fx(T, hi, x)
        if d_hi >= 0.0:
            break
        n -= 1
        hi /= 1.01
        if n == 0:
            return False, 0.0, 0.0
    if hi < r:
        p_hi, hi = p_r, r
        intercambiar = r < lo
    else:
        intercambiar = hi < lo
    if intercambiar:
        lo, hi, p_lo, p_hi, d_lo, d_hi = hi, lo, p_hi, p_lo, d_hi, d_lo
    pend = (p_hi - p_lo) / (hi - lo)
    if (d_lo < pend < d_hi) or (pend < d_lo and d_hi < pend) or una_raiz:
        if p_lo < P < p_r:
            hi = r
        if p_r < P < p_hi:
            lo = r
    return True, lo, hi


def _refinar_fx(T, P, x, x1, x2, tol=1e-7):
    """CEquation::FindDensity (regula falsi con extrapolacion acotada, 40 pasos) -> (ok, D)."""
    f1 = _p_fx(T, x1, x) - P
    f2 = _p_fx(T, x2, x) - P
    if (f1 - f2) * (x1 - x2) < 0.0:
        return False, 0.0
    sal = x1  # [C-43] FX deja la salida en 0 si converge sin iterar; aqui se devuelve x1 (raiz exacta)
    for _ in range(40):
        if abs(x1 - x2) <= 1e-10 or abs(f1) <= 1e-10:
            return True, sal
        x3 = (x2 - x1) * f1 / (f1 - f2) + x1
        if x3 < 0.0:
            x3 = (x1 + x2) * 0.5
        sal = x3
        dx = x3 - x1
        if abs(x3) >= 1e-8:
            dx = dx / x3
        if abs(dx) < tol:
            return True, sal
        f3 = _p_fx(T, x3, x) - P
        a = f1 * f3
        bb = f2 * f3
        medio = 0.5 * (x2 - x1) + x1
        if a < 0.0 and bb < 0.0:
            a, bb = -a, -bb
        if bb <= a:
            x1n, x2n, f2n = x3, x2, f2
        else:
            x1n, x2n, f2n = x3, x1, f1
        x1, x2, f2, f1 = x1n, x2n, f2n, f3
        if (medio - x1) * (medio - x2) <= 0.0:
            r = abs(f3 / f2)
            if r < 0.3:
                xn = r * 1.5 * (x2 - x1) + x1
                usar_medio = None
            elif r > 3.0:
                xn = x2 - r * 1.5 * (x2 - x1)
                usar_medio = None
            else:
                xn = (x1 + x2) * 0.5
                usar_medio = True
            sal = xn
            fn = _p_fx(T, xn, x) - P
            prod = f3 * fn
            if usar_medio is None and prod > 0.0:
                xn = (x1 + x2) * 0.5
                sal = xn
                fn = _p_fx(T, xn, x) - P
                prod = f3 * fn
            if fn * f2 <= prod:
                x2n, f2n = x2, f2
            else:
                x2n, f2n = x1, f3
            x1, x2, f2, f1 = xn, x2n, f2n, fn
    return False, 0.0


def _primera_raiz_fx(f, a, b, n):
    """CEquation::FindFirstRoot: barrido de a hacia b en n pasos hasta el primer cambio de signo de f y
    refinamiento biseccion + regula falsi (tolerancia 1e-7). -> (ok, raiz)."""
    paso = (b - a) / float(n)
    medio_paso = abs(0.5 * paso)
    xi = a
    f_ant = f(a)
    while True:
        xi = xi + paso
        if abs(xi - b) < medio_paso:
            xi = b - 1e-8
        if (b - xi) * (b - a) < 0.0:
            return False, 0.0
        f_act = f(xi)
        prod = f_ant * f_act
        if prod < 0.0:
            break
        f_ant = f_act
        if abs(prod) > 1.7976931348623157e+308:
            return False, 0.0
    # refinamiento (variables como en la decompilacion: [x9 (f8) ... x18 (f50)], x28 = ultimo punto)
    x9, f8, x18, f50, x28 = a, f_ant, xi, f_act, xi
    for _ in range(1000):  # FX no tiene limite; aqui se corta para no colgar
        xm = (x18 + x9) * 0.5
        fm = f(xm)
        if f8 * fm <= 0.0:
            x5, f7, f50, x18 = x9, f8, fm, xm
        else:
            x5, f7 = xm, fm
        xn = (x18 - x5) * f7 / (f7 - f50) + x5
        if (abs(xn) > 1e-8 and abs((xn - x28) / xn) < 1e-7) or abs(xn - x28) < 1e-7:
            return True, xn
        fn = f(xn)
        x28 = xn
        if f7 * fn <= 0.0:
            f8, x9, f50, x18 = f7, x5, fn, xn
        else:
            f8, x9 = fn, xn
    return False, 0.0


def _gibbs_residual_fx(T, D, x):
    """CEquation::GRTPB: g_res = R T (ar + Z - 1 - ln Z) (misma escala relativa que FX)."""
    ar = AlpharGERG(1, T, D, x)
    d = ar[(0, 1)]
    return (ar[(0, 0)] + d - math.log(d + 1.0)) * _R_FX * T * 1000.0


def _calc_density_fx(T, P, x, fase, semillas, n_raices):
    """CEquation::CalcDensity -> (D, fase_encontrada) o None."""
    if n_raices not in (1, 2, 3):
        return None
    una = n_raices == 1
    nula = lambda D: _p_fx(T, D, x) - P  # noqa: E731

    def buscar(rho, vapor):
        ok, lo, hi = _acotar_fx(T, P, x, rho, vapor, una)
        if not ok:
            return None, 0.0
        ok, D = _refinar_fx(T, P, x, lo, hi)
        if ok:
            return True, D
        ok, D = _primera_raiz_fx(nula, hi, lo, 50) if vapor else _primera_raiz_fx(nula, lo, hi, 50)
        return ok, (D if ok else 0.0)

    if una or fase in (FASE_FX_ESTABLE, FASE_FX_LIQUIDO):
        ok_l, d_l = buscar(semillas[0], False)
        ok_l = bool(ok_l) and d_l >= 0.0
        if una or fase == FASE_FX_LIQUIDO:
            return (d_l, FASE_FX_LIQUIDO) if ok_l else None
        ok_v, d_v = buscar(semillas[1], True)
        if ok_v is None or d_v < 0.0:
            return (d_l, FASE_FX_LIQUIDO) if ok_l else None
        if ok_v and ok_l:
            g_l = _gibbs_residual_fx(T, d_l, x)
            g_v = _gibbs_residual_fx(T, d_v, x)
            if (g_l - g_v) / (_R_FX * T * 1000.0) >= 0.0:
                return d_v, FASE_FX_VAPOR
            return d_l, FASE_FX_LIQUIDO
        if ok_l:
            return d_l, FASE_FX_LIQUIDO
        if ok_v:
            return d_v, FASE_FX_VAPOR
        return None
    if fase == FASE_FX_VAPOR:
        ok_v, d_v = buscar(semillas[1], True)
        if ok_v and d_v >= 0.0:
            return d_v, FASE_FX_VAPOR
        return None
    return None


def _calculate_density_fx(T, P, x, b):
    """CEquation::CalculateDensity (respaldo por barrido). Devuelve D o None (FX devuelve 0)."""
    dmin, dmax = 1e-5, 0.99 / b
    n = int(10.0 / b)
    nula = lambda D: _p_fx(T, D, x) - P  # noqa: E731
    deriv = lambda D: _dpdd_fx(T, D, x)[1]  # noqa: E731
    ok, d_sv = _primera_raiz_fx(deriv, dmin, dmax, n)
    if ok:
        if _p_fx(T, d_sv, x) < P:
            ok2, D = _primera_raiz_fx(nula, dmax, dmin, n)
            if ok2:
                return D
        else:
            return None
    ok, d_sl = _primera_raiz_fx(deriv, dmax, dmin, n)
    if ok:
        if P < _p_fx(T, d_sl, x):
            ok2, D = _primera_raiz_fx(nula, dmin, dmax, n)
            if ok2:
                return D
        else:
            return None
    ok, D = _primera_raiz_fx(nula, dmin, dmax, n)
    return D if ok else None


def DensidadFX(T, P_kPa, x, fase=FASE_FX_VAPOR):
    """Densidad [mol/l] como GERG2008::CEquation::TERMO de FlowXpert (semillas Peng-Robinson + CalcDensity con la
    fase pedida + CalculateDensity de respaldo). Devuelve None si FX no obtendria una densidad valida."""
    P = P_kPa / 1000.0
    try:
        ok, semillas, n, b = _semillas_pr(T, P, x)
        if not ok:
            return None
        r = _calc_density_fx(T, P, x, fase, semillas, n)
        if r is not None:
            D = r[0]
        else:
            D = _calculate_density_fx(T, P, x, b)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None
    if D is None or not (D > 0.0) or D != D:
        return None
    return D


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
        return (
            f"P={P_kPa:.3f} kPa esta por debajo de {PRESION_MINIMA_CONFIABLE_KPA:.0f} kPa "
            "(0.5 MPa): a presion cercana a la atmosferica la busqueda de densidad "
            "de GERG-2004/2008 es menos robusta. El resultado sigue la formulacion "
            "publica de NIST (GERG2008.FOR); revisarlo con precaucion."
        )
    return None


def calcular_propiedades(composicion: dict, T_K: float, P_kPa: float):
    """Punto de entrada de alto nivel: composicion por nombre + T,P -> propiedades."""
    x = _composicion_a_x(composicion)
    # [C-43] Raiz como FlowXpert (semillas Peng-Robinson, fase vapor pedida por las pantallas Gas). FX reporta
    # Z = P / (D R T) con la P de entrada (TERMO), aunque FindDensity corte por paso antes de cerrar la presion.
    D_fx = DensidadFX(T_K, P_kPa, x, FASE_FX_VAPOR)
    if D_fx is not None:
        resultado = PropertiesGERG(T_K, D_fx, x)
        resultado["Z"] = P_kPa / (D_fx * R_GERG * T_K)
        resultado["D_mol_l"] = D_fx
        resultado["ierr"] = 0
        resultado["msg_error"] = ""
        resultado["aviso_baja_presion"] = _aviso_baja_presion(P_kPa)
        return resultado
    # Respaldo (FX no obtendria densidad valida): metodo anterior a C-43.
    D, ierr, msg = DensityGERG(T_K, P_kPa, x)
    if ierr:
        # [CERTAIN, 2026-10-05, captura real libro 01 caso 11] CO2 puro supercritico (308.15 K / 9600 kPa): el
        # arranque de gas no converge y antes se devolvia la densidad de gas ideal. Con arranque de liquido
        # (iFlag = 2) da 696.291 kg/m3; FlowXpert 696.2872 kg/m3 (0.0006 %). Hallazgo D-43.
        D2, ierr2, msg2 = DensityGERG(T_K, P_kPa, x, iFlag=2)
        if not ierr2:
            D, ierr, msg = D2, ierr2, msg2
    resultado = PropertiesGERG(T_K, D, x)
    resultado["D_mol_l"] = D
    resultado["ierr"] = ierr
    resultado["msg_error"] = msg
    resultado["aviso_baja_presion"] = _aviso_baja_presion(P_kPa)
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
        "aviso_baja_presion": _aviso_baja_presion(P_kPa),
    }


def calcular_flash(composicion: dict, T_K: float, P_kPa: float,
                    duplicar_fase_ausente: bool = False, vf_regla_fx: bool = False):
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
    res = _calcular_flash_monofasico_previo(z, T_K, P_kPa, duplicar_fase_ausente)
    # [C-43] Densidad de la alimentacion como el primer TERMO de CEquation::CalculateFlash de FlowXpert (fase 0:
    # la de menor energia de Gibbs entre las raices sembradas con Peng-Robinson). La fraccion de vapor se sigue
    # clasificando como antes; solo si la raiz cambia se clasifica contra la densidad pseudocritica.
    D_fx = DensidadFX(T_K, P_kPa, z, FASE_FX_ESTABLE)
    if D_fx is None:
        return res
    D_prev = res["D_total_mol_l"]
    if vf_regla_fx:
        # [C-43, GERG-2008 Flash] Fase como TERMO de FX: liquido si el volumen molar 1/D <= 3 b (b de Peng-Robinson
        # de la mezcla), vapor si no. Confirmado contra el emulador en 240 estados densos (propano/etano/n-butano
        # liquidos: VF 0; C1/C2 50/50 supercritico 290 K 10000 kPa y 330 K 15000 kPa: VF 1), donde la regla anterior
        # (D vs densidad pseudocritica / raiz de arranque) fallaba.
        _a_pr, b_pr = _pr_mezcla(T_K, z)
        vf_final = 0.0 if 1.0 / D_fx <= 3.0 * b_pr else 1.0
    elif res["ierr"] == 0 and abs(D_fx - D_prev) <= 1e-6 * max(D_prev, 1e-12):
        vf_final = res["vapor_fraction"]
    else:
        _Tcx, Dcx = PseudoCriticalPointGERG(z)
        vf_final = 0.0 if D_fx >= Dcx else 1.0
    props = PropertiesGERG(T_K, D_fx, z)
    props["Z"] = P_kPa / (D_fx * R_GERG * T_K)
    return _resultado_flash_monofasico(D_fx, MolarMassGERG(z), props, vf_final, 0, 0, "",
                                        duplicar_fase_ausente, P_kPa)


def _calcular_flash_monofasico_previo(z, T_K, P_kPa, duplicar_fase_ausente):
    """Seleccion de raiz anterior a C-43 (Newton desde gas y desde liquido, menor Gibbs). Se conserva como
    respaldo y para mantener la clasificacion de fase de los casos ya validados."""
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


# =============================================================================
# FLASH BIFASICO (solo pantalla "GERG-2008 Flash")
# =============================================================================
# [CERTAIN, 2026-10-05, captura real de la app FlowXpert] La pantalla "GERG-2008 Flash" SI calcula equilibrio de
# fases (Wet Gas 5000 kPa / 263.15 K: Vapour Fraction 0.850062, liquido = agua 999.9247 kg/m3; Nordic 5000 kPa /
# 253.15 K: VF 0.999314). La decision del 2026-08-01 de dejar solo una fase era correcta para "GERG-2004 Flash",
# pero no para esta pantalla. Metodo: prueba de estabilidad de Michelsen (fases de prueba tipo vapor, liquido y
# casi puras) + Rachford-Rice con sustitucion sucesiva. Fugacidades: ln phi_i = d(n*alpha_r)/dn_i (T, V) - ln Z,
# por diferencia central. Reproduce los 4 puntos bifasicos reales con las 6 cifras de la app.

# Tc [K], Pc [kPa], factor acentrico: solo para la estimacion inicial de Wilson (no cambian el resultado final).
_CRIT_WILSON = {1: (190.56, 4599.2, 0.011), 2: (126.19, 3395.8, 0.037), 3: (304.13, 7377.3, 0.224),
                4: (305.32, 4872.2, 0.099), 5: (369.83, 4248.0, 0.152), 6: (407.81, 3629.0, 0.184),
                7: (425.13, 3796.0, 0.200), 8: (460.35, 3378.0, 0.229), 9: (469.70, 3370.0, 0.251),
                10: (507.82, 3034.0, 0.300), 11: (540.13, 2736.0, 0.350), 12: (569.32, 2497.0, 0.400),
                13: (594.55, 2281.0, 0.443), 14: (617.70, 2103.0, 0.490), 15: (33.15, 1296.4, -0.219),
                16: (154.58, 5043.0, 0.022), 17: (132.86, 3494.0, 0.050), 18: (647.10, 22064.0, 0.344),
                19: (373.10, 9000.0, 0.100), 20: (5.20, 227.6, -0.390), 21: (150.69, 4863.0, -0.002)}


def _raices_densidad(T, P, x, dmin=1e-6, npts=150):
    """Raices mecanicamente estables (dP/dD > 0) de P(T, D, x) = P por barrido logaritmico y biseccion,
    entre dmin y la densidad maxima razonable de la mezcla."""
    _tc, dcx = PseudoCriticalPointGERG(x)
    dmax = max(4.0 * dcx, 60.0)
    pts = [dmin * (dmax / dmin) ** (k / float(npts)) for k in range(npts + 1)]
    f = []
    for D in pts:
        try:
            f.append(PressureGERG(T, D, x)[0] - P)
        except (OverflowError, ValueError):
            f.append(float("nan"))
    raices = []
    for k in range(npts):
        a, b = f[k], f[k + 1]
        if a != a or b != b or not (a < 0 <= b):
            continue
        lo, hi = pts[k], pts[k + 1]
        for _ in range(80):
            m = 0.5 * (lo + hi)
            if PressureGERG(T, m, x)[0] - P < 0:
                lo = m
            else:
                hi = m
        raices.append(0.5 * (lo + hi))
    return raices


def _densidad_fase(T, P, x, fase):
    """Densidad [mol/l] de la fase "V" (raiz menor) o "L" (raiz mayor). Primero Newton (DensityGERG) con
    verificacion (presion reproducida y dP/dD > 0); si no converge o cae en la raiz de la otra fase, barrido
    completo de la isoterma (_raices_densidad)."""
    _tc, dcx = PseudoCriticalPointGERG(x)
    D, ierr, _ = DensityGERG(T, P, x, iFlag=0 if fase == "V" else 2)
    if not ierr and D > 0:
        p2, z2, dpdd = PressureGERG(T, D, x)
        if z2 > 0 and dpdd > 0 and abs(p2 - P) <= 1e-6 * P:
            if (fase == "V" and D <= dcx) or (fase == "L" and D >= dcx):
                return D
            if fase == "L":
                # Newton cayo en la raiz tipo gas: se busca una raiz liquida solo por encima de la pseudocritica
                r = _raices_densidad(T, P, x, dmin=0.5 * dcx, npts=60)
                return r[-1] if r and r[-1] > D else D
    r = _raices_densidad(T, P, x)
    if not r:
        return None
    return r[0] if fase == "V" else r[-1]


def _ln_phi(T, P, x, fase):
    """(ln phi[1..21], D [mol/l], Z) de la fase "V" (raiz menor) o "L" (raiz mayor); (None, 0, 0) si no hay raiz."""
    D = _densidad_fase(T, P, x, fase)
    if D is None:
        return None, 0.0, 0.0
    Z = PressureGERG(T, D, x)[1]
    if Z <= 0:
        return None, 0.0, 0.0
    V = 1.0 / D

    def n_alfa_r(nv):
        # [C-31] la cache de terminos en tau (_estado, tolerancia 1e-7 en T y Tr) devolvia valores viejos para
        # perturbaciones de composicion de 1e-6 y falseaba ln phi hasta 1e-3 (agua en GERG-2008 Flash caso 16).
        _estado.told = None
        n = sum(nv[1:])
        return n * AlpharGERG(1, T, n / V, [None] + [ni / n for ni in nv[1:]])[(0, 0)]

    res = [None]
    for i in range(1, 22):
        if x[i] <= 0.0:
            res.append(0.0)
            continue
        # [C-31] derivada de segundo orden tambien para componentes traza. [C-33] Si x < 2h se usa la formula hacia
        # adelante de 3 puntos con h = 1e-6 (la centrada con h = x/2 diminuto tenia ruido de redondeo ~1e-8 que
        # impedia cerrar el criterio de convergencia del flash).
        h = 1e-6
        nv = list(x)
        if x[i] > 2.0 * h:
            nv[i] = x[i] + h
            fp = n_alfa_r(nv)
            nv[i] = x[i] - h
            fm = n_alfa_r(nv)
            deriv = (fp - fm) / (2.0 * h)
        else:
            f0 = n_alfa_r(nv)
            nv[i] = x[i] + h
            f1 = n_alfa_r(nv)
            nv[i] = x[i] + 2.0 * h
            f2 = n_alfa_r(nv)
            deriv = (-3.0 * f0 + 4.0 * f1 - f2) / (2.0 * h)
        res.append(deriv - math.log(Z))
    _estado.told = None
    return res, D, Z


def _k_wilson(T, P):
    return [None] + [_CRIT_WILSON[i][1] / P * math.exp(5.373 * (1 + _CRIT_WILSON[i][2]) * (1 - _CRIT_WILSON[i][0] / T))
                     for i in range(1, 22)]


def _rachford_rice(z, K):
    comp = [i for i in range(1, 22) if z[i] > 0]

    def f(b):
        return sum(z[i] * (K[i] - 1) / (1 + b * (K[i] - 1)) for i in comp)

    if f(0.0) < 0:
        return 0.0
    if f(1.0) > 0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if f(m) > 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def _es_estable(T, P, z):
    """Prueba de estabilidad de Michelsen. Devuelve (estable, tpd_minimo)."""
    lnf_v, _, _ = _ln_phi(T, P, z, "V")
    lnf_l, _, _ = _ln_phi(T, P, z, "L")
    cand = [lf for lf in (lnf_v, lnf_l) if lf is not None]
    if not cand:
        return True, 0.0

    def g_ref(lf):
        return sum(z[i] * (math.log(z[i]) + lf[i]) for i in range(1, 22) if z[i] > 0)

    lnf_ref = min(cand, key=g_ref)
    d = [None] + [(math.log(z[i]) + lnf_ref[i]) if z[i] > 0 else 0.0 for i in range(1, 22)]
    K = _k_wilson(T, P)
    pruebas = [("V", [None] + [z[i] * K[i] for i in range(1, 22)]),
               ("L", [None] + [z[i] / K[i] for i in range(1, 22)])]
    for i in range(1, 22):
        if z[i] >= 1e-3:  # fases de prueba casi puras solo de componentes con al menos 0.1 %
            w = [None] + [1e-6 if z[j] > 0 else 0.0 for j in range(1, 22)]
            w[i] = 1.0
            pruebas.append(("L", w))
    tpd_min = 0.0
    for fase, W in pruebas:
        for _ in range(60):
            s = sum(W[1:])
            lnf, _, _ = _ln_phi(T, P, [None] + [W[i] / s for i in range(1, 22)], fase)
            if lnf is None:
                W = None
                break
            Wn = [None] + [math.exp(d[i] - lnf[i]) if z[i] > 0 else 0.0 for i in range(1, 22)]
            cambio = sum((Wn[i] - W[i]) ** 2 for i in range(1, 22))
            W = Wn
            if cambio < 1e-14:
                break
        if W is not None:
            tpd_min = min(tpd_min, 1.0 - sum(W[1:]))
            if tpd_min < -1e-8:  # ya se encontro una fase de prueba inestable
                return False, tpd_min
    return True, tpd_min


def _flash_bifasico(z, T, P, P_kPa):
    """[C-43] Si la iteracion desborda (OverflowError/ValueError en exp/log, p. ej. liquido comprimido C1/C3 50/50 a
    240 K y >= 7000 kPa) devuelve None: el que llama usa la rama monofasica, que es lo que entrega FlowXpert (VF = 0,
    liquido). Si no converge en 500 vueltas devuelve ierr = 1 sin valores, como FX cuando SOLMIN agota sus 20 pasos
    (GERG_Calculate devuelve 3 y la pantalla muestra error)."""
    try:
        return _flash_bifasico_iterar(z, T, P, P_kPa)
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def _flash_bifasico_iterar(z, T, P, P_kPa):
    K = _k_wilson(T, P)
    convergido = False
    b, x, y = 1.0, z, z
    Dl = Dv = Zl = Zv = 0.0
    fuera = 0  # vueltas con Rachford-Rice fuera de (0, 1): iteracion degenerada hacia una sola fase
    for it in range(500):
        b = _rachford_rice(z, K)
        if not (0.0 < b < 1.0):
            fuera += 1
        x = [None] + [z[i] / (1 + b * (K[i] - 1)) if z[i] > 0 else 0.0 for i in range(1, 22)]
        y = [None] + [K[i] * x[i] for i in range(1, 22)]
        sx, sy = sum(x[1:]), sum(y[1:])
        x = [None] + [v / sx for v in x[1:]]
        y = [None] + [v / sy for v in y[1:]]
        lfl, Dl, Zl = _ln_phi(T, P, x, "L")
        lfv, Dv, Zv = _ln_phi(T, P, y, "V")
        if lfl is None or lfv is None:
            return None
        Kn = [None] + [math.exp(lfl[i] - lfv[i]) if z[i] > 0 else K[i] for i in range(1, 22)]
        # [C-33] criterio por encima del ruido numerico de ln phi (~3e-8 en ln K, derivada numerica): max|dlnK| < 1e-7
        # (la misma tolerancia de FlowXpert). Antes sum(dlnK^2) < 1e-14 no se cerraba por ese ruido y el flash daba
        # ~144 vueltas (24 s) aunque ya estaba convergido en ~5; al cortar aqui el error remanente es ~1e-10.
        err = max(abs(math.log(Kn[i]) - math.log(K[i])) for i in range(1, 22) if z[i] > 0)
        K = Kn
        if err < 1e-7:
            convergido = True
            break
    if not (0.0 < b < 1.0):
        return None
    if not convergido and (fuera > 0 or max(abs(math.log(K[i])) for i in range(1, 22) if z[i] > 0) > 50.0):
        # [C-43] La sustitucion no convergio porque degenero (RR pegado en 0/1, K divergentes: C3/C1 90/10 270 K
        # 6000 y 10000 kPa, 70/30 250 K 15000 kPa). Antes se devolvia la ultima vuelta (VF ~0.88, Z falso); FX da
        # una sola fase liquida, que es lo que entrega la rama monofasica.
        return None
    if not convergido:
        return {"vapor_fraction": float("nan"), "iteraciones": it + 1, "ierr": 1,
                "msg_error": "Calculation error: el flash GERG-2008 no convergio en 500 iteraciones.",
                "solucion_trivial": False, "aviso_baja_presion": _aviso_baja_presion(P_kPa)}
    Mv, Ml, Mt = MolarMassGERG(y), MolarMassGERG(x), MolarMassGERG(z)
    Dt = 1.0 / (b / Dv + (1.0 - b) / Dl)
    return {
        "vapor_fraction": b,
        "Z_vapor": Zv, "Z_liquido": Zl, "Z_total": b * Zv + (1.0 - b) * Zl,
        "D_vapor_mol_l": Dv, "D_liquido_mol_l": Dl, "D_total_mol_l": Dt,
        "D_vapor_kg_m3": Dv * Mv, "D_liquido_kg_m3": Dl * Ml, "D_total_kg_m3": Dt * Mt,
        "iteraciones": it + 1, "ierr": 0, "msg_error": "", "solucion_trivial": False,
        "aviso_baja_presion": _aviso_baja_presion(P_kPa),
        "composicion_vapor": y, "composicion_liquido": x,
    }


def calcular_flash_gerg2008(composicion: dict, T_K: float, P_kPa: float):
    """Alias explicito de `calcular_flash` con `duplicar_fase_ausente=True`,
    para la pantalla real 'GERG-2008 Flash' (distinta de 'GERG-2004 Flash',
    ver docstring de `calcular_flash`). Ademas la densidad se expresa en
    kg/m3 REAL (masica) en esta pantalla -- confirmado con la captura real
    ('GERG 2008/GERG FLASH 1.jpeg': Vapour/Liquid/Total Density=86.89433
    kg/m3, que SI coincide con la densidad masica real, a diferencia de la
    pantalla 'GERG-2004 Flash' donde el numero bajo la etiqueta 'kg/m3' es
    en realidad la densidad molar)."""
    z = _composicion_a_x(composicion)
    try:
        estable, _tpd = _es_estable(T_K, P_kPa, z)
    except (OverflowError, ValueError, ZeroDivisionError):  # [C-43] mismo criterio que _flash_bifasico
        estable = True
    if not estable:
        res = _flash_bifasico(z, T_K, P_kPa, P_kPa)
        if res is not None:
            return res
    return calcular_flash(composicion, T_K, P_kPa, duplicar_fase_ausente=True, vf_regla_fx=True)


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
