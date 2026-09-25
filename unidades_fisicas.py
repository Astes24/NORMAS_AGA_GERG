# -*- coding: utf-8 -*-
"""
unidades_fisicas.py
====================
Libreria COMPARTIDA de conversion de unidades para `interfaz_calculo_flujo.py`,
organizada por MAGNITUD FISICA (Temperatura, Presion, Densidad, Energia
volumetrica, Fraccion molar) -- NO por norma. Varias normas independientes
(familia API MPMS 1952/1980/2004/11.2/12.2, NGL/LPG, Ethylene/Propylene,
GasViscosity_2004, NX-19, y las normas extraidas en las RONDAS 43-52: GPA
TP-15, ASTM D1550 -Ctl y RD60-, GPA-2172, ASTM D4311M) exponen en su pantalla
real EL MISMO selector de unidad (mismo widget, mismas opciones, misma
magnitud fisica) aunque sean binarios/normas distintas -- por eso conviene
UNA sola tabla por magnitud, reusada por quien la necesite, en vez de una
copia por norma.

REFACTOR RONDA 53 (2026-09-14): este modulo se creo moviendo (NO
duplicando, NO reinventando valores) las tablas que ya vivian sueltas en
`interfaz_calculo_flujo.py` (dispersas aprox. entre las lineas 240 y 610 de
ese archivo, antes del refactor) hacia aca. Mismos nombres de variable,
mismo formato -- lista de tuplas `(nombre_unidad, funcion_lambda_a_nativa)`
-- y los MISMOS valores numericos que ya estaban validados en produccion.
`interfaz_calculo_flujo.py` sigue exponiendo estos nombres tal cual (los
importa desde aca) para no tener que tocar los ~85 `_build_tab_*` que ya
los consumen: esto es un refactor de UBICACION del codigo, no de nombres ni
de interfaz publica ni de valores.

Que NO se movio a proposito (ver comentario de cada seccion abajo y la nota
final de este docstring):
    - `_agregar_fila_presion`: sigue siendo un METODO de la clase `App` en
      `interfaz_calculo_flujo.py` porque arma un widget real de Tkinter
      (Entry+Combobox) -- es codigo de UI, no de conversion. Este modulo
      solo tiene la parte de "logica de conversion" (las tablas), la parte
      de "widget" se queda donde vive el resto de Tkinter.
    - Tablas usadas por una sola pantalla, SIN reuso confirmado entre normas
      (ej. `TEMPERATURA_A_DEGF`/`TEMPERATURA_A_KELVIN`/`DENSIDAD_A_LBFT3` de
      AGA-3/AGA-10, `GASVISC2004_TEMPERATURA_A_DEGC` de GasViscosity_2004,
      `ISO6976_PRESION_A_PA` de ISO-6976, `PRESION_A_KPA`/`FX_UNIT_CONV` de
      AGA-3): quedan en `interfaz_calculo_flujo.py` tal como estaban. Varias
      de estas comparten el MISMO valor fisico que alguna tabla ya migrada
      (ej. `_PSI_A_KPA`/`_LBFT3_A_KGM3`, importadas de vuelta desde aca) pero
      NO se unificaron mas alla de esas 2 constantes base por precaucion: la
      consigna del refactor es no romper nada que ya funciona, no maximizar
      la limpieza del codigo. `ISO6976_PRESION_A_PA` en particular es
      candidato a unificarse con la familia de Presion de aca en una ronda
      futura (misma fuente NIST/ISO 31-3 de cada constante, mismo criterio
      de conversion) pero queda pendiente, sin tocar, por las dudas.
"""

# ---------------------------------------------------------------------------
# Constantes base (factores de conversion "crudos", EXACTOS por definicion de
# unidad SI/imperial -- ver detalle de la fuente de cada una en el comentario
# original, ahora abajo). MISMOS VALORES que ya estaban en
# interfaz_calculo_flujo.py, solo cambia la ubicacion.
#   1 psi = 6.894757293168361 kPa EXACTO (de 1 lbf=4.4482216152605 N y
#           1 in=0.0254 m, ambos exactos por definicion).
#   1 lb/ft3 = 16.018463373960138 kg/m3 EXACTO (de 1 lb=0.45359237 kg y
#           1 ft=0.3048 m, ambos exactos por definicion).
# ---------------------------------------------------------------------------
_PSI_A_KPA = 6.894757293168361
_LBFT3_A_KGM3 = 16.018463373960138


# ---------------------------------------------------------------------------
# PRESION -- selector REAL de Pressure/Equilibrium Pressure/Atmospheric
# Pressure de TODA la familia "API" (MPMS 1952/1980/2004/11.2/12.2/NGL-LPG/
# Ethylene/Propylene) y de las normas nuevas que reusan el mismo selector
# (GPA TP-15, ASTM D1550, GPA-2172, ASTM D4311M) -- confirmado en vivo
# (uiautomator, emulador flowxpert_rd, RONDA 39, 2026-09-09) tocando el
# dialogo de edicion de 8 pantallas distintas (API Table-5/60 2004, API
# Density @15C 1980/1952, API Gravity @60F 1980/1952, API MPMS 11.2.1, API
# Density @15C NGL/LPG, API Rel. Density @60F NGL/LPG, API 11.3.2.1
# Ethylene). TODAS exponen el MISMO "Unit" Spinner con 11 opciones (scroll
# completo hecho en 2 de las 8, lista identica en las otras 6 por el mismo
# widget/texto "bar gauge"/"bar absolute"), en 2 variantes segun la pantalla:
#   - GAUGE ("bar gauge" en el dialogo real) en 1952/1980/2004/11.2:
#     bar(g), mbar(g), mmHgg, mmH2Og, mmH2Og @ 60°F, inHgg con,
#     inHgg @ 32°F, inHgg @ 60°F, inH2Og con, inH2Og @ 39.2°F, inH2Og @ 60°F.
#   - ABSOLUTA ("bar absolute" en el dialogo real) en NGL/LPG y
#     Ethylene/Propylene: mismos nombres con sufijo "a" en vez de "g"
#     (bar(a), mbar(a), mmHga, mmH2Oa, ... inH2Oa @ 60°F).
# psig/psia NO aparecen como opcion en NINGUNA pantalla -- confirmado para
# TODA la familia, no solo 2004: pantallas cuyo motor Python es nativamente
# psig/psia (1980/1952 US, 11.2.1, NGL RD60F) tambien muestran SIEMPRE este
# mismo selector gauge/absoluto, nunca psig/psia.
# Los 11 factores fisicos son los mismos usados en ISO6976_PRESION_A_PA (que
# se queda en interfaz_calculo_flujo.py, ver docstring de este modulo), solo
# re-escalados de Pa a kPa. Fuente de cada constante:
#   kgf/m2, kgf/cm2: kgf = 9.80665 N exacto (gravedad estandar).
#   lbf/ft2: psi/144 exacto (1 ft2 = 144 in2).
#   mmHg/inHg "con" (convencional) y mmH2O/inH2O "con": definicion
#     convencional ISO 31-3 (Hg=13595.1 kg/m3, H2O=1000 kg/m3, g=9.80665).
#   inHg @32F, inH2O @39.2F, inHg/inH2O @60F: valores publicados NIST SP811
#     Apendice B.9 (densidad real del fluido a esa temperatura especifica).
# ---------------------------------------------------------------------------
_API_PRESION_UNIDADES_BASE_KPA = [
    ("bar", 100.0),
    ("mbar", 0.1),
    ("mmHg", 0.133322387415),
    ("mmH2O", 0.00980665),
    ("mmH2O @ 60°F", 0.0097969),
    ("inHg con", 3.386389),
    ("inHg @ 32°F", 3.38638),
    ("inHg @ 60°F", 3.37685),
    ("inH2O con", 0.249089),
    ("inH2O @ 39.2°F", 0.249082),
    ("inH2O @ 60°F", 0.24884),
]


def _api_presion_tabla(letra, factor_kpa_a_nativa):
    """Genera la tabla (etiqueta, funcion) del selector real de Presion de la
    familia API (ver comentario arriba). `letra`: "g" (gauge, bar(g)/mbar(g)/
    mmHgg/...) o "a" (absoluta, bar(a)/mbar(a)/mmHga/...). `factor_kpa_a_
    nativa`: cuantas unidades NATIVAS (las que espera la funcion Python:
    psig/psia o bar(g)/bar(a)) hay por 1 kPa -- 1/100.0 para nativa=bar,
    1/_PSI_A_KPA para nativa=psi."""
    tabla = []
    for nombre, factor_kpa in _API_PRESION_UNIDADES_BASE_KPA:
        if nombre in ("bar", "mbar"):
            etiqueta = f"{nombre}({letra})"
        else:
            base, _, resto = nombre.partition(" ")
            etiqueta = f"{base}{letra}" + (f" {resto}" if resto else "")
        factor_total = factor_kpa * factor_kpa_a_nativa
        tabla.append((etiqueta, (lambda v, f=factor_total: v * f)))
    return tabla


API_PRESION_GAUGE_A_BARG = _api_presion_tabla("g", 1.0 / 100.0)
API_PRESION_GAUGE_A_PSIG = _api_presion_tabla("g", 1.0 / _PSI_A_KPA)
API_PRESION_ABS_A_BARA = _api_presion_tabla("a", 1.0 / 100.0)
API_PRESION_ABS_A_PSIA = _api_presion_tabla("a", 1.0 / _PSI_A_KPA)


# ---------------------------------------------------------------------------
# TEMPERATURA -- selector REAL K/degC/degF/R de TODA la familia API (nativo
# degF en 1980/1952 US, 11.2.x, NGL RD60F; nativo degC en 1952/1980
# metricas) y de NX-19 (RONDA 52, reusa API_TEMPERATURA_A_DEGC porque
# normas/NX_19.py espera t_degc nativo).
# ---------------------------------------------------------------------------
API_TEMPERATURA_A_DEGF = [
    ("degF", lambda v: v),
    ("degC", lambda v: v * 1.8 + 32.0),
    ("K", lambda v: (v - 273.15) * 1.8 + 32.0),
    ("R", lambda v: v - 459.67),
]
API_TEMPERATURA_A_DEGC = [
    ("degC", lambda v: v),
    ("K", lambda v: v - 273.15),
    ("degF", lambda v: (v - 32.0) / 1.8),
    ("R", lambda v: v * (5.0 / 9.0) - 273.15),
]


# ---------------------------------------------------------------------------
# DENSIDAD -- GasViscosity_2004 (Gas > Viscosity > "Natural gas dynamic
# viscosity"). Las 3 opciones de unidad de "density" (base real que usa
# calcular_viscosidad(): kg/m3) fueron CONFIRMADAS tocando el campo real en
# la app Android (uiautomator dump, 2026-08-19): kg/m3 (default), g/cc,
# lb/ft3. Ver normas/GasViscosity_2004.py, seccion "UNIDADES DE ENTRADA EN
# LA UI REAL".
# ---------------------------------------------------------------------------
GASVISC2004_DENSIDAD_A_KGM3 = [
    ("kg/m3", lambda v: v),
    ("g/cc", lambda v: v * 1000.0),
    ("lb/ft3", lambda v: v * _LBFT3_A_KGM3),
]


# ---------------------------------------------------------------------------
# ENERGIA VOLUMETRICA (Gross Heating Value) -- NX-19 (RONDA 52), selector
# real de 6 unidades confirmado en vivo (uiautomator, emulador flowxpert_rd)
# tocando el campo "Gross Heating Val." de la pantalla NX-19 (categoria
# "Gas > AGA"); default real de la pantalla es kcal/m3 (11943 kcal/m3 =
# 50.0030 MJ/m3, redondeo de 50 MJ/m3), NO MJ/m3. Factores:
# Btu(IT)=1.05505585262 kJ, ft3=0.028316846592 m3 (conversion estandar),
# cal/kcal(IT)=4.1868 J/kJ.
# ---------------------------------------------------------------------------
NX19_GHV_A_MJM3 = [
    ("MJ/m3", lambda v: v),
    ("kJ/m3", lambda v: v / 1000.0),
    ("Btu/ft3", lambda v: v * 0.03725894580783128),
    ("kBtu/ft3", lambda v: v * 37.25894580783128),
    ("cal/m3", lambda v: v * 4.1868e-6),
    ("kcal/m3", lambda v: v * 0.0041868),
]


# ---------------------------------------------------------------------------
# FRACCION MOLAR -- NX-19 (RONDA 52), selector real de 2 unidades confirmado
# en vivo en los campos Nitrogen/CO2 Fraction.
# ---------------------------------------------------------------------------
NX19_FRACCION_A_MOLMOL = [
    ("mole/mole", lambda v: v),
    ("%mole", lambda v: v / 100.0),
]
