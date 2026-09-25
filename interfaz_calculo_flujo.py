# -*- coding: utf-8 -*-
"""
interfaz_calculo_flujo.py
==========================
Interfaz de escritorio (Tkinter) que UNE visualmente los calculos
independientes de la carpeta normas/. Este archivo NO contiene logica de
calculo propia -- solo importa cada norma y construye la ventana.

Normas usadas (cada una ejecutable sola, ver su propio docstring de fuente):
    normas/NX_19.py              -> supercompresibilidad NX-19
    normas/AGA_8.py              -> Z y propiedades, ecuacion DETAIL
    normas/GERG_2008.py          -> Z y propiedades, ecuacion GERG-2008
    normas/GERG_2004.py          -> alias de GERG_2008 (Gas) + flash liquido-vapor
    normas/AGA_10.py              -> velocidad del sonido y Fpv (usa AGA_8)
    normas/AGA_7.py               -> conversion de caudal (AGA-9 usa la misma formula)

Pestanas (agrupadas por familia en la barra superior):
    NX-19                 -> supercompresibilidad, independiente del flujo.
    AGA-8 / AGA8 GERG / GERG-2008 Gas / GERG-2008 Flash / GERG-2004 Gas /
    GERG-2004 Flash / AGA-10 -> Z, propiedades termodinamicas, equilibrio
                                liquido-vapor, velocidad del sonido y Fpv,
                                independiente del flujo.
    AGA-5                 -> poder calorifico (CV_MASS, CV_VOL), formula real
                             de FlowXpert validada contra caso real (ver
                             normas/AGA_5.py).
    AGA-7 / AGA-9          -> conversion de caudal (base/flujo/masico).

Requisitos:
    Ninguno externo -- todas las normas importadas son Python puro
    (solo libreria estandar + Tkinter).

Uso:
    python interfaz_calculo_flujo.py
"""

import os
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tema_focqus import (  # noqa: E402
    aplicar_tema, PanelAyudaColapsable, NAVY_SECUNDARIO, TEXTO_CLARO, FONDO_CLARO,
)
from normas.NX_19 import nx19_fpv_ghv  # noqa: E402
from normas.AGA_8 import (  # noqa: E402
    NOMBRES_COMPONENTES as GAS_NOMBRES_COMPONENTES,
    calcular_propiedades as aga8_calcular_propiedades,
    validar_rango_aga8,
    NEO_PENTANO_MODOS, aplicar_modo_neo_pentano, validar_suma_composicion,
)
from normas.GERG_2008 import (  # noqa: E402
    calcular_propiedades as gerg2008_calcular_propiedades,
    aplicar_modo_neo_pentano_gerg,
)
from normas.GERG_2004 import (  # noqa: E402
    calcular_propiedades_gas as gerg2004_calcular_propiedades_gas,
    calcular_flash as gerg2004_calcular_flash,
)
from normas.GERG_2008 import calcular_flash_gerg2008 as gerg2008_calcular_flash  # noqa: E402
from normas.AGA_10 import calcular_velocidad_sonido_y_fpv  # noqa: E402
from normas.AGA_5 import (  # noqa: E402
    ORDEN_COMPONENTES_APP as AGA5_COMPONENTES,
    calcular_poder_calorifico as aga5_calcular_poder_calorifico,
)
from normas.AGA_7 import caudal_base_desde_flujo  # noqa: E402
from normas.AGA_9 import caudal_base_desde_flujo as caudal_base_desde_flujo_AGA9  # noqa: E402
from normas.ISO_6976 import (  # noqa: E402
    ORDEN_COMPONENTES_APP as ISO6976_COMPONENTES,
    calcular_masa_molar as iso6976_calcular_masa_molar,
    calcular_masa_molar_metodo_b as iso6976_calcular_masa_molar_metodo_b,
    calcular_factor_compresion as iso6976_calcular_factor_compresion,
    calcular_volumen_molar_ideal as iso6976_calcular_volumen_molar_ideal,
    calcular_volumen_molar_real as iso6976_calcular_volumen_molar_real,
    calcular_poder_calorifico_molar as iso6976_calcular_poder_calorifico_molar,
    calcular_indice_wobbe as iso6976_calcular_indice_wobbe,
    calcular_densidad_relativa as iso6976_calcular_densidad_relativa,
)
from normas.ISO_6976_1983 import (  # noqa: E402
    calcular_iso6976_1983, OPCIONES_METERING_1983, OPCIONES_CALVAL_1983,
)
from normas.ISO_6976_1995 import (  # noqa: E402
    calcular_iso6976_1995_extendido, OPCIONES_REF_TEMPERATURE_1995,
)
from normas.ISO_6976_ex_1995 import (  # noqa: E402
    ORDEN_COMPONENTES_EX1995,
    calcular_masa_molar_ex1995,
    calcular_factor_compresion_ex1995,
    calcular_poder_calorifico_molar_ex1995,
    calcular_volumen_molar_ideal_ex1995,
    calcular_volumen_molar_real_ex1995,
    CONDITIONS_A_INDICE_BJ as EX1995_CONDITIONS_A_INDICE_BJ,
    CONDITIONS_A_INDICE_HOJ as EX1995_CONDITIONS_A_INDICE_HOJ,
)
from normas.ISO_6976_ex_2016 import (  # noqa: E402
    ORDEN_COMPONENTES_EX2016,
    calcular_masa_molar_ex2016,
    calcular_factor_compresion_ex2016,
    calcular_poder_calorifico_molar_ex2016,
    calcular_volumen_molar_ideal_ex2016,
    calcular_volumen_molar_real_ex2016,
)
from normas.GasViscosity_2004 import (  # noqa: E402
    calcular_viscosidad_desde_22 as gasvisc_calcular_viscosidad_desde_22,
)
from normas.API_MPMS_Tables_1980_2004 import (  # noqa: E402
    api_table5_1980, api_table6_1980, api_table23_1980, api_table24_1980,
    api_table53_1980, api_table54_1980,
    api_table5_2004, api_table6_2004, api_table23_2004, api_table24_2004,
    api_table53_2004, api_table54_2004,
    api_table59_2004, api_table60_2004,
    api_density15c_1980, api_gravity60f_1980, api_reldensity60f_1980,
    api_table53_1952, api_table54_1952, api_density15c_1952,
    api_table5_1952, api_table6_1952, api_table23_1952, api_table24_1952,
    api_gravity60f_1952, api_sg60f_1952,
    api_mpms_11_2_1, api_mpms_11_2_1m, api_mpms_11_2_2, api_mpms_11_2_2m,
    api_table23e, api_table24e, api_table53e, api_table54e,
    api_table59e, api_table60e,
    api_dens15c_ngl_lpg, api_dens20c_ngl_lpg, api_rd60f_ngl_lpg,
)
from normas.GPA_TP15 import calcular_gpa_tp15  # noqa: E402
from normas.ASTM_D1550 import astm_d1550_ctl, astm_d1550_rd60  # noqa: E402
from normas.ASTM_D4311 import astm_d4311_09_m  # noqa: E402
from normas.GPA_2172 import (  # noqa: E402
    calcular_gpa2172, ORDEN_TABLA_GPA2145, _EDICIONES_C as GPA2172_EDICIONES_C,
    _EDICIONES_M as GPA2172_EDICIONES_M,
)
from normas.API_Ethylene_Propylene import (  # noqa: E402
    api_mpms_11_3_2_1_ethylene, api_mpms_11_3_3_2_propylene,
)
# unidades_fisicas.py (RONDA 53, refactor de ubicacion, MISMOS VALORES) --
# tablas de conversion de unidad organizadas por MAGNITUD FISICA (no por
# norma), reusadas por TODA la familia API (1952/1980/2004/11.2/12.2/
# NGL-LPG/Ethylene/Propylene), GasViscosity_2004, NX-19, y las normas
# extraidas en las RONDAS 43-52 (GPA TP-15, ASTM D1550, GPA-2172,
# ASTM D4311M). Se mantienen los MISMOS NOMBRES que ya usaban los ~85
# `_build_tab_*` de este archivo -- ver docstring de unidades_fisicas.py
# para el detalle de que se movio y que se dejo sin tocar a proposito.
from unidades_fisicas import (  # noqa: E402
    _PSI_A_KPA, _LBFT3_A_KGM3,
    API_PRESION_GAUGE_A_BARG, API_PRESION_GAUGE_A_PSIG,
    API_PRESION_ABS_A_BARA, API_PRESION_ABS_A_PSIA,
    API_TEMPERATURA_A_DEGF, API_TEMPERATURA_A_DEGC,
    GASVISC2004_DENSIDAD_A_KGM3,
    NX19_GHV_A_MJM3, NX19_FRACCION_A_MOLMOL,
)

CACHE_DIR = os.path.join(tempfile.gettempdir(), "focqus_calculo_flujo_cache")

# ---------------------------------------------------------------------------
# ISO 6976 (2016_M / ex_2016_M) -- mapeo del selector "Ref. Temperature" (las
# 7 combinaciones reales que expone la UI de FlowXpert: 15/15/15, 0/0/0,
# 15/0/0, 25/0/0, 20/20/20, 25/20/20, 60F -- ver normas/ISO_6976.py, seccion
# 4.5 del docstring, para el switch real de 7 casos de
# `select_reference_temperatures`). Cada tupla es
#   (etiqueta UI, reference_conditions [1..7, valor real del switch],
#    indice_bj [0..2], t0_metering_K, indice_hoj_combustion [0..3],
#    indice_temp_raw_aire [1..4, para calcular_densidad_relativa], nota)
# Los datos NO son inventados por esta interfaz: reference_conditions y el
# orden de la lista salen del switch decompilado (secc. 4.5); metering/aire
# (indice_temp_raw_aire) estan confirmados por Frida en vivo para los casos
# 1/3/5/7 (secc. 4.3/4.4/4.6/4.7); indice_bj/t0 en esos mismos casos son el
# MEJOR AJUSTE NUMERICO ya documentado ahi (LIKELY, no CERTAIN, salvo el caso
# 1 "Default" que SI es CERTAIN por Frida directo). indice_hoj_combustion
# SOLO esta confirmado (=2) para combustion=15 C (casos 1 y 3) -- para el
# resto (combustion 0/20/25 C o 60F, nunca probada por Frida) se reusa ese
# mismo valor 2 como unico candidato disponible en el proyecto, marcado
# explicitamente [SIN CONFIRMAR] en la nota. Los casos 2/4/6 (0/0/0, 25/0/0,
# 25/20/20) nunca se probaron en vivo -- se dejan habilitados (mismo criterio
# de "mejor estimador disponible" que el resto del proyecto usa para casos
# sin caso real, ej. ISO_6976_1983/1995 con p_ref asumida) pero con nota
# [GUESSING] explicita.
# ---------------------------------------------------------------------------
# *** CORREGIDO 2026-08-18 (tarea de continuacion, validacion contra 5 casos
# reales de cromatografo) -- BUG REAL encontrado en T0 de las filas rc=5, 6 y
# 7 (20/20/20, 25/20/20, 60F/60F/60F): el T0 que estaba aqui (288.15 K y
# 273.15 K) era simplemente REUSADO de otras filas (rc=1 y rc=2/3/4) como
# "mejor ajuste numerico" contra Z -- pero Z es CASI INSENSIBLE a T0 (Z esta a
# ~0.002 de 1.0, asi que un error de T0 de hasta 33 K solo mueve Z ~0.001-
# 0.03%, invisible contra el margen <0.1% del proyecto). Cruzando 2 casos
# reales de cromatografo (normas/_cache_cromatografo.json) que SI usan estos
# combos (rc=5 y rc=7) contra `densidad_real`/`PCB_volumen`/`Wobbe` (que
# dependen de T0 LINEALMENTE via Vm_ideal=R*T0/p, mucho mas sensibles que Z)
# se encontro que el T0 viejo daba dif. 1.71% (rc=5) y 5.68% (rc=7) -- muy
# por encima del margen del proyecto -- mientras que el T0 LITERAL de la
# etiqueta de la UI (20 C = 293.15 K; 60 F = 288.70556 K) cierra <0.03% en
# ambos casos, igual de bien que las demas filas ya CERTAIN/LIKELY (que SI
# usaban la conversion literal: 0 C=273.15, 15 C=288.15). Ver
# `android_sdk_setup/validar_iso6976_2016_cromatografo.py` para el metodo y
# los 5 casos completos. indice_bj/indice_temp_raw_aire NO cambian (Z y
# densidad_relativa ya cerraban <0.03% con los valores existentes). ***
REF_TEMPERATURE_ISO6976_2016 = [
    ("15/15/15 (Default)", 1, 2, 288.15, 2, 2,
     "CERTAIN: caso real confirmado por Frida en vivo (ISO_6976.py secc. 4.3/4.5/4.6)."),
    ("0/0/0", 2, 0, 273.15, 2, 1,
     "GUESSING: combo nunca probado en vivo -- indice_bj/T0/indice_hoj son el mejor "
     "estimador disponible (analogia con el caso 15/0/0), sin confirmacion propia."),
    ("15/0/0", 3, 0, 273.15, 2, 1,
     "LIKELY: metering confirmado por Frida (indice_temp_raw=1, secc. 4.3); indice_bj/T0 "
     "por mejor ajuste numerico (secc. 4.4, dif. ~0.018%); indice_hoj=2 CERTAIN por Frida "
     "(combustion=15 C, secc. 4.3 conclusion 2)."),
    ("25/0/0", 4, 0, 273.15, 2, 1,
     "GUESSING: combo nunca probado en vivo -- combustion=25 C no tiene indice_hoj "
     "confirmado, se reusa 2 (unico valor CERTAIN del proyecto) como estimador."),
    ("20/20/20", 5, 2, 293.15, 2, 4,
     "LIKELY: metering confirmado por Frida (indice_temp_raw=4, secc. 4.4); indice_bj por "
     "mejor ajuste numerico de Z (secc. 4.4). T0 CORREGIDO 2026-08-18: el valor viejo "
     "(288.15 K, copiado de rc=1) daba dif. 1.71% en densidad_real/PCB_volumen contra un "
     "caso real de cromatografo -- T0=293.15 K (conversion literal de 20 C, no un ajuste) "
     "cierra 0.02-0.03% en Mmix/Z/densidad_real/densidad_relativa/PCB_volumen/Wobbe contra "
     "ese mismo caso real. indice_hoj=2 sin confirmar para combustion=20 C, reusado como "
     "estimador."),
    ("25/20/20", 6, 2, 293.15, 2, 4,
     "GUESSING: combo nunca probado en vivo -- combustion=25 C sin indice_hoj confirmado, "
     "se reusa 2 como estimador. T0 CORREGIDO 2026-08-18 por analogia directa con rc=5 "
     "(mismo metering=20 C): 293.15 K (conversion literal), no 288.15 K (el valor viejo, "
     "copiado de rc=1, nunca tuvo caso real propio para probarlo con este combo exacto)."),
    ("60F/60F/60F", 7, 1, 288.70555555555555, 2, 3,
     "LIKELY: metering confirmado por Frida (indice_temp_raw=3, secc. 4.7); indice_bj por "
     "mejor ajuste numerico de Z con caso real de Hidrogeno=5% (secc. 4.7). T0 CORREGIDO "
     "2026-08-18: el valor viejo (273.15 K = 0 C) daba dif. 5.68% en densidad_real/"
     "PCB_volumen/Wobbe contra un caso real de cromatografo -- T0=288.70556 K (conversion "
     "literal de 60 F, no 0 C) cierra 0.02-0.03% contra ese mismo caso real. indice_hoj=2 "
     "sin confirmar para combustion=60F, reusado como estimador."),
]


# Unidades reales encontradas en libFXLibrary.so (Pa/kPa/MPa/psia/bar(a)/
# bar(g)/atm/mmHg/inHg/inH2O para Diff.Pressure y Pressure; degC/degF/Kelvin
# para Temperature; kg/m3/lb/ft3/lbm/ft3 para Density; mm/cm/m/in/ft para
# Pipe/Orifice Diameter). Cada factor convierte HACIA kPa (presion) -- luego
# se reusa el factor inverso (si_a_ing) para llegar a la unidad nativa de
# cada campo especifico, evitando una segunda fuente de la misma constante.
# bar(g) es MANOMETRICA (gauge): se suma 101.325 kPa de atmosfera estandar
# para pasarla a absoluta. Reusada por varias pestañas (ej. AGA-10).
PRESION_A_KPA = [
    ("kPa", lambda v: v),
    ("Pa", lambda v: v / 1000.0),
    ("MPa", lambda v: v * 1000.0),
    ("psia", lambda v: v * _PSI_A_KPA),
    ("bar(a)", lambda v: v * 100.0),
    ("bar(g)", lambda v: v * 100.0 + 101.325),
    ("atm", lambda v: v * 101.325),
    ("mmHg", lambda v: v * 0.133322387415),
    ("inHg", lambda v: v * 3.386389),
    # inH2O -> psi: 27.707 (constante fisica estandar, antes reusada via
    # import de normas/AGA_3_FLOWXPERT.py; inlineada aca porque ese modulo
    # no forma parte de este build).
    ("inH2O", lambda v: v * (_PSI_A_KPA / 27.707)),
]

# ---------------------------------------------------------------------------
# Selector de UNIDAD del campo "Metering reference pressure" de la pantalla
# real "ISO-6976 (2016)" -- confirmado tocando la app (uiautomator, 2026-08-18,
# emulador con com.spiritit.flowxpert). Junto al EditText numerico
# (resource-id value_field) hay un Spinner (resource-id unit_field) con
# EXACTAMENTE estas 18 opciones, en este orden (confirmado por scroll completo
# arriba y abajo de la lista, doble verificado sin 19a opcion oculta):
#   Pa, kPa, kgf/m2, kgf/cm2, lbf/ft2, psi, bar, mbar, mmHg, mmH2O,
#   mmH2O @ 60F, inHg con(vencional), inHg @ 32F, inHg @ 60F, inH2O
#   con(vencional), inH2O @ 39.2F, inH2O @ 60F, inH2O @ 68F.
#
# CONFIRMADO EN VIVO que es SOLO conversion de entrada/visualizacion, NO
# cambia el valor fisico usado por el calculo: con la composicion "Default"
# se entro 1013.25 mbar (valor por defecto real de la app), se cambio la
# unidad a kPa (el campo se auto-convirtio a 101.325 kPa, MISMO valor fisico)
# y a psi (14.695943 psi, tambien el MISMO valor fisico) -- las 5 salidas
# visibles en pantalla (17.73312 / 0.958061 / 0.999085 / 0.781759 / 22.63245)
# quedaron IDENTICAS, digito a digito, en las 3 corridas. Por eso esta tabla
# solo necesita convertir HACIA Pa antes de llamar a normas/ISO_6976.py (que
# espera p_ref en Pa, ver calcular_factor_compresion/calcular_volumen_molar_
# ideal) -- no hace falta ninguna constante reversineria del binario, son
# factores fisicos ESTANDAR (mismo criterio ya usado en PRESION_A_KPA arriba).
#
# Fuentes de cada factor (todos hacia Pa):
#   Pa/kPa/bar/mbar/psi: definiciones exactas SI/imperiales estandar.
#   kgf/m2, kgf/cm2: kgf = 9.80665 N exacto (gravedad estandar).
#   lbf/ft2: psi/144 exacto (1 ft2 = 144 in2).
#   mmHg/inHg "con" (convencional) y mmH2O/inH2O "con": definicion
#     convencional ISO 31-3 (Hg=13595.1 kg/m3, H2O=1000 kg/m3, g=9.80665).
#   inHg @32F, inH2O @39.2F, inHg/inH2O @60F: valores publicados NIST SP811
#     Apendice B.9 (densidad real del fluido a esa temperatura especifica).
#   inH2O @68F: NO tiene entrada NIST directa -- [GUESSING, calculado] se
#     obtuvo con la misma formula fisica (densidad del agua a 20 C =
#     998.2071 kg/m3, tabla estandar) * g * 0.0254 m, sin fuente publicada
#     de referencia cruzada -- si se necesitara mas precision en el futuro,
#     confirmar contra una tabla de vapor/agua especifica.
ISO6976_PRESION_A_PA = [
    ("Pa", lambda v: v),
    ("kPa", lambda v: v * 1000.0),
    ("kgf/m2", lambda v: v * 9.80665),
    ("kgf/cm2", lambda v: v * 98066.5),
    ("lbf/ft2", lambda v: v * (_PSI_A_KPA * 1000.0 / 144.0)),
    ("psi", lambda v: v * _PSI_A_KPA * 1000.0),
    ("bar", lambda v: v * 100000.0),
    ("mbar", lambda v: v * 100.0),
    ("mmHg", lambda v: v * 133.322387415),
    ("mmH2O", lambda v: v * 9.80665),
    ("mmH2O @ 60°F", lambda v: v * 9.7969),
    ("inHg con", lambda v: v * 3386.389),
    ("inHg @ 32°F", lambda v: v * 3386.38),
    ("inHg @ 60°F", lambda v: v * 3376.85),
    ("inH2O con", lambda v: v * 249.089),
    ("inH2O @ 39.2°F", lambda v: v * 249.082),
    ("inH2O @ 60°F", lambda v: v * 248.84),
    ("inH2O @ 68°F", lambda v: v * 248.66),
]
ISO6976_PRESION_A_PA_DICT = dict(ISO6976_PRESION_A_PA)

# ---------------------------------------------------------------------------
# Selector REAL de Pressure/Equilibrium Pressure/Atmospheric Pressure de TODA
# la familia "API" (MPMS 1952/1980/2004/11.2/12.2/NGL-LPG/Ethylene/Propylene)
# -- confirmado en vivo (uiautomator, emulador flowxpert_rd, RONDA 39,
# 2026-09-09) tocando el dialogo de edicion de 8 pantallas distintas (API
# Table-5/60 2004, API Density @15°C 1980/1952, API Gravity @60°F 1980/1952,
# API MPMS 11.2.1, API Density @15°C NGL/LPG, API Rel. Density @60°F NGL/LPG,
# API 11.3.2.1 Ethylene). TODAS exponen el MISMO "Unit" Spinner con 11
# opciones (scroll completo hecho en 2 de las 8, lista identica en las
# otras 6 por el mismo widget/texto "bar gauge"/"bar absolute"), en 2
# variantes segun la pantalla:
#   - GAUGE ("bar gauge" en el dialogo real) en 1952/1980/2004/11.2:
#     bar(g), mbar(g), mmHgg, mmH2Og, mmH2Og @ 60°F, inHgg con,
#     inHgg @ 32°F, inHgg @ 60°F, inH2Og con, inH2Og @ 39.2°F, inH2Og @ 60°F.
#   - ABSOLUTA ("bar absolute" en el dialogo real) en NGL/LPG y
#     Ethylene/Propylene: mismos nombres con sufijo "a" en vez de "g"
#     (bar(a), mbar(a), mmHga, mmH2Oa, ... inH2Oa @ 60°F).
# psig/psia NO aparecen como opcion en NINGUNA pantalla -- confirma y
# EXTIENDE la nota operativa ya documentada en
# normas/API_MPMS_Tables_1980_2004.py (RONDA 6: "el selector de Presion de
# las pantallas 2004 NO ofrece psig", vista entonces solo hasta la mitad de
# la lista sin hacer scroll) a TODA la familia, no solo 2004 -- incluye
# pantallas cuyo motor Python es nativamente psig/psia (1980/1952 US,
# 11.2.1, NGL RD60F): la pantalla real SIEMPRE ofrece este mismo selector
# gauge/absoluto, nunca psig/psia, sea cual sea la unidad nativa interna.
# Los 11 factores fisicos son EXACTAMENTE los mismos ya usados en
# ISO6976_PRESION_A_PA (bar..inH2O @ 60°F, ver esa tabla arriba para la
# fuente de cada constante), solo re-escalados de Pa a kPa.
# ---------------------------------------------------------------------------
# _API_PRESION_UNIDADES_BASE_KPA/_api_presion_tabla/API_PRESION_GAUGE_A_BARG/
# API_PRESION_GAUGE_A_PSIG/API_PRESION_ABS_A_BARA/API_PRESION_ABS_A_PSIA
# migradas a unidades_fisicas.py (RONDA 53, ver import arriba) -- MISMOS
# VALORES, solo cambio de ubicacion (ver docstring de unidades_fisicas.py).

# Misma fuente que TEMPERATURA_A_DEGF/PRESION_A_KPA (unidades reales
# confirmadas en libFXLibrary.so), pero convirtiendo hacia Kelvin/kPa --
# las unidades que usan directamente las funciones de normas/GERG_2008.py.
TEMPERATURA_A_KELVIN = [
    ("K", lambda v: v),
    ("degC", lambda v: v + 273.15),
    ("degF", lambda v: (v - 32.0) / 1.8 + 273.15),
]
# GasViscosity_2004 (Gas > Viscosity > "Natural gas dynamic viscosity") -- las
# 3 opciones de unidad de "density" (base real que usa calcular_viscosidad():
# kg/m3) fueron CONFIRMADAS tocando el campo real en la app Android
# (uiautomator dump, 2026-08-19): kg/m3 (default), g/cc, lb/ft3. Se verifico
# que cambiar de unidad SOLO convierte el valor mostrado/ingresado (80 kg/m3
# -> 0.08 g/cc -> 4.9942368 lb/ft3, mismo valor fisico) y que el resultado de
# viscosidad final NO cambia (0.000014 Pa.s en los 3 casos, con density y
# temperature en unidades no base simultaneamente). Ver
# normas/GasViscosity_2004.py, seccion "UNIDADES DE ENTRADA EN LA UI REAL".
# GASVISC2004_DENSIDAD_A_KGM3 migrada a unidades_fisicas.py (RONDA 53, ver
# import arriba) -- MISMOS VALORES, misma tabla, solo cambio de ubicacion.
# Las 4 opciones de unidad de "temperature" (base real: grados Celsius,
# confirmado explicito por la app con el subtitulo "degree celsius") tambien
# CONFIRMADAS tocando el campo real: K, °C (default), °F, R (Rankine).
# Mismo patron: conversion solo de entrada/visualizacion (20°C -> 68°F,
# mismo resultado 0.000014 Pa.s).
GASVISC2004_TEMPERATURA_A_DEGC = [
    ("degC", lambda v: v),
    ("K", lambda v: v - 273.15),
    ("degF", lambda v: (v - 32.0) / 1.8),
    ("R", lambda v: v * (5.0 / 9.0) - 273.15),
]

# ---------------------------------------------------------------------------
# API MPMS Tables (API-2540 / ASTM D1250), ediciones 1980 y 2004 -- ver
# normas/API_MPMS_Tables_1980_2004.py. Selectores reales confirmados tocando
# la app Android en vivo (uiautomator, 2026-08-20, pantallas "Liquid > API
# 11.1 (1980) > API Table-5 (1980)/API Table-6 (1980)", ver
# android_sdk_setup/casos_reales_api_tables.json):
#   - "API Gravity"/"API Gravity @60F": SIN selector de unidad (siempre °API).
#   - "Product": 7 opciones reales via picker: Crude, "Refined, auto",
#     Gasoline, "Transition area", "Jet fuel", "Fuel oil", "Lub oil" ->
#     product=1..7 (coincide con el enum de normas/API_MPMS_Tables_1980_2004.py).
#   - "Temperature": CON selector real K/degC/degF/R.
# La confirmacion en vivo de "Temperature" fue en las pantallas Table-5/6
# (1980, sistema US, nativo en degF). Table-23/24_1980 (RD) y Table-5/6/23/24
# _2004 tambien trabajan en degF internamente (mismo motor US) -- se reusa el
# MISMO selector K/degC/degF/R por ser la misma magnitud fisica, aunque no se
# tocaron esas pantallas especificas una por una. Table-53/54_1980 (metrico,
# nativo en degC) NO se tocaron en vivo esta ronda; se le da el MISMO selector
# K/degC/degF/R (misma magnitud fisica, solo cambia la unidad nativa a
# degC) siguiendo el mismo criterio que el resto del proyecto usa para
# selectores de unidad estandar (fisicos, no especificos de un binario) --
# decision documentada, no un caso real verificado para esas 2 pestañas.
# "API Gravity"/"RD"/"Density" de entrada: SIN selector de unidad en las 10
# pestañas (confirmado para Table5/6; Table23/24/53/54 son variantes RD/
# densidad puntual del mismo motor, mismo criterio de UI aplicado por
# consistencia).
API_PRODUCTOS = [
    ("Crude", 1), ("Refined, auto", 2), ("Gasoline", 3), ("Transition area", 4),
    ("Jet fuel", 5), ("Fuel oil", 6), ("Lub oil", 7),
]
# Enum real "API Rounding" (Tipo B, Table6/24/54_1980) y "API-2540 Rounding"
# (wrappers combinados 1980 con presion) -- MISMAS 4 opciones, confirmadas en
# vivo: solo el valor 2 ("Enabled (table values)") redondea el resultado
# principal (ctl) a 4 decimales, las otras 3 no cambian el numero.
API_ROUNDING_ENUM_OPCIONES = [
    ("Disabled", 0), ("Enabled", 1),
    ("Enabled (table values)", 2), ("Enabled (5 decimal places)", 3),
]
# API_TEMPERATURA_A_DEGF/API_TEMPERATURA_A_DEGC migradas a
# unidades_fisicas.py (RONDA 53, ver import arriba) -- MISMOS VALORES, solo
# cambio de ubicacion.

# ---------------------------------------------------------------------------
# RONDA 52 (2026-09-14): selectores REALES de la pantalla "NX-19" (categoria
# "Gas > AGA"), confirmados en vivo (uiautomator, emulador flowxpert_rd)
# tocando los 5 campos numericos del dialogo de edicion -- HASTA esta ronda
# el codigo asumia (RONDA 51, sin AVD) que ninguno tenia selector; la
# confirmacion en vivo REFUTA esa suposicion, los 5 SI tienen "Unit" Spinner
# real:
#   - Pressure: MISMO selector absoluto de 11 unidades que la familia API
#     (bar(a)/mbar(a)/mmHga/mmH2Oa/.../inH2Oa @ 60F, default bar(a)) --
#     reusa API_PRESION_ABS_A_BARA (normas/NX_19.py espera p_bar nativo en
#     bar(a) absoluto, coincide exacto).
#   - Temperature: MISMO selector K/degC/degF/R que la familia API --
#     reusa API_TEMPERATURA_A_DEGC (normas/NX_19.py espera t_degc nativo).
#   - Gross Heating Val.: selector NUEVO de 6 unidades (kJ/m3, MJ/m3,
#     Btu/ft3, kBtu/ft3, cal/m3, kcal/m3; default real de la pantalla es
#     kcal/m3, NO MJ/m3 como asumia el codigo anterior) -- confirmado con
#     el valor por defecto real de la pantalla, 11943 kcal/m3 = 50.0030
#     MJ/m3 (redondeo de 50 MJ/m3, ver NX19_GHV_A_MJM3 abajo). Factores:
#     Btu(IT)=1.05505585262 kJ, ft3=0.028316846592 m3 (conversion estandar),
#     cal/kcal(IT)=4.1868 J/kJ.
#   - Nitrogen/CO2 Fraction: selector NUEVO de 2 unidades (mole/mole,
#     %mole) -- confirmado en vivo en ambos campos por separado.
# Specific Gravity SIGUE sin selector (campo "function_input_unit" vacio en
# la pantalla real, adimensional, confirmado que no abre dialogo con Unit
# Spinner -- no se toco).
# ---------------------------------------------------------------------------
# NX19_GHV_A_MJM3/NX19_FRACCION_A_MOLMOL migradas a unidades_fisicas.py
# (RONDA 53, ver import arriba) -- MISMOS VALORES, solo cambio de ubicacion.

os.makedirs(CACHE_DIR, exist_ok=True)

# Las 16 composiciones guardadas reales de FlowXpert (boton "LOAD" de la
# app, disponible en toda pantalla con composicion) -- son las mezclas de
# referencia clasicas de la industria (GPA 2145 / AGA Report No. 8).
# Extraidas directamente de la app real (2026-08-01/03, ver memoria del
# proyecto), % molar exactos. Cada entrada: (composicion_21_dict,
# neo_pentano_valor, neo_pentano_modo) -- "Slochteren" es BYTE A BYTE la
# misma composicion que "Default" (confirmado), solo cambia el modo de
# neo-Pentano (Add to nC5 en vez de Add to iC5).
COMPOSICIONES_GUARDADAS_FLOWXPERT = {
    "Amarillo": ({
        "Metano": 90.6724, "Nitrogeno": 3.1284, "CO2": 0.4676, "Etano": 4.5279,
        "Propano": 0.8280, "Isobutano": 0.1037, "n-Butano": 0.1563,
        "Isopentano": 0.0321, "n-Pentano": 0.0443, "n-Hexano": 0.0393,
    }, 0.0, "Add to iC5"),
    "Default": ({
        "Metano": 81.3150, "Nitrogeno": 14.2110, "CO2": 0.9900, "Etano": 2.8290,
        "Propano": 0.3800, "Isobutano": 0.0600, "n-Butano": 0.0720,
        "Isopentano": 0.0180, "n-Pentano": 0.0330, "n-Hexano": 0.0200,
        "n-Heptano": 0.0130, "n-Octano": 0.0050, "Helio": 0.0460,
    }, 0.008, "Add to iC5"),
    "Dry Air": ({
        "Metano": 0.0002, "Nitrogeno": 78.1020, "CO2": 0.0330, "Hidrogeno": 0.0001,
        "Oxigeno": 20.9460, "Helio": 0.0005, "Argon": 0.9160,
    }, 0.0, "Add to iC5"),
    "Ekofisk": ({
        "Metano": 85.9063, "Nitrogeno": 1.0068, "CO2": 1.4954, "Etano": 8.4919,
        "Propano": 2.3015, "Isobutano": 0.3486, "n-Butano": 0.3506,
        "Isopentano": 0.0509, "n-Pentano": 0.0480,
    }, 0.0, "Add to iC5"),
    "Groningen": ({
        "Metano": 81.29, "Nitrogeno": 14.32, "CO2": 0.89, "Etano": 2.87,
        "Propano": 0.38, "Oxigeno": 0.01, "n-Butano": 0.15, "n-Pentano": 0.04,
        "n-Hexano": 0.05,
    }, 0.0, "Add to iC5"),
    "Gulf Coast": ({
        "Metano": 96.5222, "Nitrogeno": 0.2595, "CO2": 0.5956, "Etano": 1.8186,
        "Propano": 0.4596, "Isobutano": 0.0977, "n-Butano": 0.1007,
        "Isopentano": 0.0473, "n-Pentano": 0.0324, "n-Hexano": 0.0664,
    }, 0.0, "Add to iC5"),
    "HiCal": ({
        "Metano": 87.8750, "Nitrogeno": 3.8260, "CO2": 1.6930, "Etano": 4.9470,
        "Propano": 0.9740, "Isobutano": 0.1600, "n-Butano": 0.1890,
        "Isopentano": 0.0600, "n-Pentano": 0.1280, "n-Hexano": 0.0470,
        "n-Heptano": 0.0320, "n-Octano": 0.0040, "Helio": 0.0600,
    }, 0.005, "Add to iC5"),
    "High CO2-N2": ({
        "Metano": 81.2120, "Nitrogeno": 5.7020, "CO2": 7.5850, "Etano": 4.3030,
        "Propano": 0.8950, "Isobutano": 0.1510, "n-Butano": 0.1520,
    }, 0.0, "Add to iC5"),
    "High N2": ({
        "Metano": 81.4410, "Nitrogeno": 13.4650, "CO2": 0.9850, "Etano": 3.3000,
        "Propano": 0.6050, "Isobutano": 0.1000, "n-Butano": 0.1040,
    }, 0.0, "Add to iC5"),
    "Nordic": ({
        "Metano": 85.4237, "Nitrogeno": 0.7006, "CO2": 1.6515, "Etano": 8.9537,
        "Propano": 2.4568, "Isobutano": 0.2252, "n-Butano": 0.4393,
        "Isopentano": 0.0569, "n-Pentano": 0.0601, "n-Hexano": 0.0208,
        "n-Heptano": 0.0075, "n-Octano": 0.0010,
    }, 0.0024, "Add to iC5"),
    "Pure CO2": ({"CO2": 100.0}, 0.0, "Add to iC5"),
    "Pure Methane": ({"Metano": 100.0}, 0.0, "Add to iC5"),
    "Pure Nitrogen": ({"Nitrogeno": 100.0}, 0.0, "Add to iC5"),
    "Sleen": ({
        "Metano": 45.131, "Nitrogeno": 53.651, "CO2": 0.084, "Etano": 0.929,
        "Propano": 0.047, "n-Butano": 0.01, "Isopentano": 0.002,
        "n-Pentano": 0.001, "n-Hexano": 0.007, "n-Heptano": 0.003, "Helio": 0.13,
    }, 0.005, "Add to iC5"),
    "Slochteren": ({
        "Metano": 81.3150, "Nitrogeno": 14.2110, "CO2": 0.9900, "Etano": 2.8290,
        "Propano": 0.3800, "Isobutano": 0.0600, "n-Butano": 0.0720,
        "Isopentano": 0.0180, "n-Pentano": 0.0330, "n-Hexano": 0.0200,
        "n-Heptano": 0.0130, "n-Octano": 0.0050, "Helio": 0.0460,
    }, 0.008, "Add to nC5"),
    "Wet Gas": ({
        "Metano": 69.0, "Nitrogeno": 14.0, "CO2": 1.0, "Etano": 0.7,
        "Propano": 0.3, "Agua": 15.0,
    }, 0.0, "Add to iC5"),
}

# AGA-5 usa su propia grilla de 22 componentes (`normas/AGA_5.py
# ORDEN_COMPONENTES_APP`), con 2 nombres distintos de los que usa el resto
# de la app (`normas/AGA_8.py NOMBRES_COMPONENTES`) y neo-Pentano como fila
# propia SIN modo de plegado (a diferencia de las otras 7 pestañas). Mapeo
# para poder reusar `COMPOSICIONES_GUARDADAS_FLOWXPERT` ahi tambien.
_AGA5_MAPEO_NOMBRES = {"Isobutano": "i-Butano", "Isopentano": "i-Pentano"}

# GasViscosity_2004 (RONDA 6, 2026-08-19): ya NO usa una grilla propia de 12
# componentes -- el manual oficial ABB SpiritIT (ver docstring de
# normas/GasViscosity_2004.py, seccion "REDUCCION OFICIAL 22 A 12
# COMPONENTES") documento la tabla completa de como se reparten los 22
# componentes estandar en los 12 reales del motor, asi que la pestaña ahora
# muestra la grilla COMPLETA de 22 (mismo `ISO6976_COMPONENTES`/
# `ORDEN_COMPONENTES_APP` que ya usan ISO 6976/AGA-5), y
# `normas.GasViscosity_2004.calcular_viscosidad_desde_22()` hace la reduccion
# 22->12 internamente antes de calcular. Reusa directamente `self.EJEMPLO_AGA5`
# (misma composicion "Default", ya con los 22 nombres) como ejemplo -- no hace
# falta un mapeo de nombres propio ni un dict de ejemplo separado.


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FocQus - Confirmacion de Calculos")
        self.geometry("1180x760")
        aplicar_tema(self)

        self._fx_unit_actual = "SI"
        self._api_mpms_tabs = {}

        header = tk.Frame(self, bg=NAVY_SECUNDARIO, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="FocQus — Confirmacion de Calculos", bg=NAVY_SECUNDARIO,
                 fg=TEXTO_CLARO, font=("Segoe UI Semibold", 14)).pack(side="left", padx=18)

        barra_familia = ttk.Frame(self, padding=(14, 10, 14, 4))
        barra_familia.pack(fill="x")
        ttk.Label(barra_familia, text="Familia:", style="Subtitulo.TLabel").pack(
            side="left", padx=(0, 8))

        self.sub_notebook = ttk.Notebook(self)
        self.sub_notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tab_nx19 = ttk.Frame(self.sub_notebook)
        tab_aga8 = ttk.Frame(self.sub_notebook)
        tab_gerg2008 = ttk.Frame(self.sub_notebook)
        tab_gerg2008_gas = ttk.Frame(self.sub_notebook)
        tab_gerg2008_flash = ttk.Frame(self.sub_notebook)
        tab_gerg2004_gas = ttk.Frame(self.sub_notebook)
        tab_gerg2004_flash = ttk.Frame(self.sub_notebook)
        tab_aga10 = ttk.Frame(self.sub_notebook)
        tab_aga5 = ttk.Frame(self.sub_notebook)
        tab_aga7 = ttk.Frame(self.sub_notebook)
        tab_aga9 = ttk.Frame(self.sub_notebook)
        tab_iso6976_1983 = ttk.Frame(self.sub_notebook)
        tab_iso6976_1995 = ttk.Frame(self.sub_notebook)
        tab_iso6976_2016 = ttk.Frame(self.sub_notebook)
        tab_iso6976_ex1995 = ttk.Frame(self.sub_notebook)
        tab_iso6976_ex2016 = ttk.Frame(self.sub_notebook)
        tab_gasvisc2004 = ttk.Frame(self.sub_notebook)
        tab_api_table5_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table6_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table23_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table24_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table53_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table54_1980 = ttk.Frame(self.sub_notebook)
        tab_api_table5_2004 = ttk.Frame(self.sub_notebook)
        tab_api_table6_2004 = ttk.Frame(self.sub_notebook)
        tab_api_table23_2004 = ttk.Frame(self.sub_notebook)
        tab_api_table24_2004 = ttk.Frame(self.sub_notebook)
        tab_api_table53_2004 = ttk.Frame(self.sub_notebook)
        tab_api_table54_2004 = ttk.Frame(self.sub_notebook)
        # Placeholders confirmados 2026-08-25 contra la app real (emulador
        # flowxpert_rd) -- ver memoria del proyecto, seccion "MENU REAL API".
        tab_api1952_dens15c = ttk.Frame(self.sub_notebook)
        tab_api1952_gravity60f = ttk.Frame(self.sub_notebook)
        tab_api1952_sg60f = ttk.Frame(self.sub_notebook)
        tab_api1952_table23 = ttk.Frame(self.sub_notebook)
        tab_api1952_table24 = ttk.Frame(self.sub_notebook)
        tab_api1952_table5 = ttk.Frame(self.sub_notebook)
        tab_api1952_table53 = ttk.Frame(self.sub_notebook)
        tab_api1952_table54 = ttk.Frame(self.sub_notebook)
        tab_api1952_table6 = ttk.Frame(self.sub_notebook)
        tab_api112_1 = ttk.Frame(self.sub_notebook)
        tab_api112_1m = ttk.Frame(self.sub_notebook)
        tab_api112_2 = ttk.Frame(self.sub_notebook)
        tab_api112_2m = ttk.Frame(self.sub_notebook)
        tab_api1980_dens15c = ttk.Frame(self.sub_notebook)
        tab_api1980_gravity60f = ttk.Frame(self.sub_notebook)
        tab_api1980_reldensity60f = ttk.Frame(self.sub_notebook)
        tab_api2004_table59 = ttk.Frame(self.sub_notebook)
        tab_api2004_table60 = ttk.Frame(self.sub_notebook)
        tab_api_table23e = ttk.Frame(self.sub_notebook)
        tab_api_table24e = ttk.Frame(self.sub_notebook)
        tab_api_table53e = ttk.Frame(self.sub_notebook)
        tab_api_table54e = ttk.Frame(self.sub_notebook)
        tab_api_table59e = ttk.Frame(self.sub_notebook)
        tab_api_table60e = ttk.Frame(self.sub_notebook)
        tab_api_dens15c_ngl_lpg = ttk.Frame(self.sub_notebook)
        tab_api_dens20c_ngl_lpg = ttk.Frame(self.sub_notebook)
        tab_api_rd60f_ngl_lpg = ttk.Frame(self.sub_notebook)
        tab_api_ethylene = ttk.Frame(self.sub_notebook)
        tab_api_propylene = ttk.Frame(self.sub_notebook)
        tab_gpa_tp15 = ttk.Frame(self.sub_notebook)
        tab_gpa2172_c = ttk.Frame(self.sub_notebook)
        tab_gpa2172_m = ttk.Frame(self.sub_notebook)
        tab_astm_d1550_ctl = ttk.Frame(self.sub_notebook)
        tab_astm_d1550_rd60 = ttk.Frame(self.sub_notebook)
        tab_astm_d4311m_09_m = ttk.Frame(self.sub_notebook)

        self._build_tab_nx19(tab_nx19)
        self._build_tab_aga8(tab_aga8)
        self._build_tab_gerg2008(tab_gerg2008)
        self._build_tab_gerg2008_gas(tab_gerg2008_gas)
        self._build_tab_gerg2008_flash(tab_gerg2008_flash)
        self._build_tab_gerg2004_gas(tab_gerg2004_gas)
        self._build_tab_gerg2004_flash(tab_gerg2004_flash)
        self._build_tab_aga10(tab_aga10)
        self._build_tab_aga5(tab_aga5)
        self._build_tab_aga7(tab_aga7)
        self._build_tab_aga9(tab_aga9)
        self._build_tab_iso6976_1983(tab_iso6976_1983)
        self._build_tab_iso6976_1995(tab_iso6976_1995)
        self._build_tab_iso6976_2016(tab_iso6976_2016)
        self._build_tab_iso6976_ex1995(tab_iso6976_ex1995)
        self._build_tab_iso6976_ex2016(tab_iso6976_ex2016)
        self._build_tab_gasviscosity2004(tab_gasvisc2004)
        self._build_tab_api_table5_1980(tab_api_table5_1980)
        self._build_tab_api_table6_1980(tab_api_table6_1980)
        self._build_tab_api_table23_1980(tab_api_table23_1980)
        self._build_tab_api_table24_1980(tab_api_table24_1980)
        self._build_tab_api_table53_1980(tab_api_table53_1980)
        self._build_tab_api_table54_1980(tab_api_table54_1980)
        self._build_tab_api_table5_2004(tab_api_table5_2004)
        self._build_tab_api_table6_2004(tab_api_table6_2004)
        self._build_tab_api_table23_2004(tab_api_table23_2004)
        self._build_tab_api_table24_2004(tab_api_table24_2004)
        self._build_tab_api_table53_2004(tab_api_table53_2004)
        self._build_tab_api_table54_2004(tab_api_table54_2004)
        self._build_tab_api1952_dens15c(tab_api1952_dens15c)
        self._build_tab_api1952_gravity60f(tab_api1952_gravity60f)
        self._build_tab_api1952_sg60f(tab_api1952_sg60f)
        self._build_tab_api1952_table23(tab_api1952_table23)
        self._build_tab_api1952_table24(tab_api1952_table24)
        self._build_tab_api1952_table5(tab_api1952_table5)
        self._build_tab_api1952_table53(tab_api1952_table53)
        self._build_tab_api1952_table54(tab_api1952_table54)
        self._build_tab_api1952_table6(tab_api1952_table6)
        self._build_tab_api112_1(tab_api112_1)
        self._build_tab_api112_1m(tab_api112_1m)
        self._build_tab_api112_2(tab_api112_2)
        self._build_tab_api112_2m(tab_api112_2m)
        self._build_tab_api1980_dens15c(tab_api1980_dens15c)
        self._build_tab_api1980_gravity60f(tab_api1980_gravity60f)
        self._build_tab_api1980_reldensity60f(tab_api1980_reldensity60f)
        self._build_tab_api2004_table59(tab_api2004_table59)
        self._build_tab_api2004_table60(tab_api2004_table60)
        self._build_tab_api_table23e(tab_api_table23e)
        self._build_tab_api_table24e(tab_api_table24e)
        self._build_tab_api_table53e(tab_api_table53e)
        self._build_tab_api_table54e(tab_api_table54e)
        self._build_tab_api_table59e(tab_api_table59e)
        self._build_tab_api_table60e(tab_api_table60e)
        self._build_tab_api_dens15c_ngl_lpg(tab_api_dens15c_ngl_lpg)
        self._build_tab_api_dens20c_ngl_lpg(tab_api_dens20c_ngl_lpg)
        self._build_tab_api_rd60f_ngl_lpg(tab_api_rd60f_ngl_lpg)
        self._build_tab_api_ethylene(tab_api_ethylene)
        self._build_tab_api_propylene(tab_api_propylene)
        self._build_tab_gpa_tp15(tab_gpa_tp15)
        self._build_tab_gpa2172(tab_gpa2172_c, sistema="C")
        self._build_tab_gpa2172(tab_gpa2172_m, sistema="M")
        self._build_tab_astm_d1550_ctl(tab_astm_d1550_ctl)
        self._build_tab_astm_d1550_rd60(tab_astm_d1550_rd60)
        self._build_tab_astm_d4311m_09_m(tab_astm_d4311m_09_m)

        # Agrupacion por familia (tema fisico), no por norma individual --
        # asi el selector no se rompe cuando se agreguen las 5 normas
        # ISO5167 (Orifice/ISA1932/LongRadius/Venturi/VenturiNozzle) que se
        # estan reversando en normas/. Cada valor guarda el FRAME YA
        # CONSTRUIDO (no se reconstruye al cambiar de familia, para no
        # perder lo que el usuario haya escrito en otra familia).
        self._familias = {
            "Termodinamica (Z, Fpv)": [
                (tab_nx19, "NX-19 SG+GHV (PTB G9)"),
                (tab_aga8, "AGA-8 Compressibility (Z)"),
                (tab_gerg2008, "AGA8 GERG (Thermodynamic Properties)"),
                (tab_gerg2008_gas, "GERG-2008 Gas"),
                (tab_gerg2008_flash, "GERG-2008 Flash"),
                (tab_gerg2004_gas, "GERG-2004 Gas"),
                (tab_gerg2004_flash, "GERG-2004 Flash"),
                (tab_aga10, "AGA-10 (extended)"),
                (tab_aga5, "AGA-5 (Calorific Value)"),
            ],
            "Conversion de caudal": [
                (tab_aga7, "AGA-7"),
                (tab_aga9, "AGA-9"),
            ],
            "Poder Calorifico (ISO 6976)": [
                (tab_iso6976_1983, "ISO 6976 (1983)"),
                (tab_iso6976_1995, "ISO 6976 (1995)"),
                (tab_iso6976_2016, "ISO 6976 (2016)"),
                (tab_iso6976_ex1995, "ISO 6976 ex (1995, 55 comp.)"),
                (tab_iso6976_ex2016, "ISO 6976 ex (2016, 60 comp.)"),
            ],
            "Viscosidad (Schley 2004)": [
                (tab_gasvisc2004, "GasViscosity_2004"),
            ],
            # Las 3 familias API 11.1 de abajo reproducen EXACTO (mismos 9/9/8
            # items, mismo orden alfabetico por texto visible, mismos nombres
            # literales) lo que muestra la app real FlowXpert al entrar en
            # API > "API 11.1 (1952)" / "(1980)" / "(2004)" -- confirmado con
            # uiautomator sobre el emulador flowxpert_rd el 2026-08-25 (ver
            # memoria del proyecto). Los tabs marcados [PLACEHOLDER] no tienen
            # calculo real todavia (ver el motivo dentro de cada pestaña).
            "API 11.1 (1952)": [
                (tab_api1952_dens15c, "API Density @15°C (1952)"),
                (tab_api1952_gravity60f, "API Gravity @60°F (1952)"),
                (tab_api1952_sg60f, "API Specific Gravity @60°F (1952)"),
                (tab_api1952_table23, "API Table-23 (1952)"),
                (tab_api1952_table24, "API Table-24 (1952)"),
                (tab_api1952_table5, "API Table-5 (1952)"),
                (tab_api1952_table53, "API Table-53 (1952)"),
                (tab_api1952_table54, "API Table-54 (1952)"),
                (tab_api1952_table6, "API Table-6 (1952)"),
            ],
            "API 11.1 (1980)": [
                (tab_api1980_dens15c, "API Density @15°C (1980)"),
                (tab_api1980_gravity60f, "API Gravity @60°F (1980)"),
                (tab_api1980_reldensity60f, "API Rel. Density @60°F (1980)"),
                (tab_api_table23_1980, "API Table-23 (1980)"),
                (tab_api_table24_1980, "API Table-24 (1980)"),
                (tab_api_table5_1980, "API Table-5 (1980)"),
                (tab_api_table53_1980, "API Table-53 (1980)"),
                (tab_api_table54_1980, "API Table-54 (1980)"),
                (tab_api_table6_1980, "API Table-6 (1980)"),
            ],
            "API 11.1 (2004)": [
                (tab_api_table23_2004, "API Table-23 (2004)"),
                (tab_api_table24_2004, "API Table-24 (2004)"),
                (tab_api_table5_2004, "API Table-5 (2004)"),
                (tab_api_table53_2004, "API Table-53 (2004)"),
                (tab_api_table54_2004, "API Table-54 (2004)"),
                (tab_api2004_table59, "API Table-59 (2004)"),
                (tab_api_table6_2004, "API Table-6 (2004)"),
                (tab_api2004_table60, "API Table-60 (2004)"),
            ],
            # "API 11.2/12.2" -- 4 pantallas reales confirmadas por uiautomator
            # el 2026-08-26 (RONDA 13): "API MPMS 11.2.1/11.2.1M/11.2.2/11.2.2M",
            # ni mas ni menos. Las 4 estan CERRADAS [CERTAIN] con caso real
            # DIRECTO (11.2.1/11.2.1M suben de caso indirecto a directo; 11.2.2/
            # 11.2.2M son formulas nuevas decompiladas esta ronda) -- ver
            # normas/API_MPMS_Tables_1980_2004.py, docstring RONDA 13.
            "API 11.2/12.2": [
                (tab_api112_1, "API MPMS 11.2.1"),
                (tab_api112_1m, "API MPMS 11.2.1M"),
                (tab_api112_2, "API MPMS 11.2.2"),
                (tab_api112_2m, "API MPMS 11.2.2M"),
            ],
            # "E NGL/LPG (TP-27)" -- 9 pantallas reales confirmadas por
            # uiautomator el 2026-08-26 (RONDA 14), orden literal del menu de
            # la app. Las 9 CERRADAS: 6 [CERTAIN] con caso real o round-trip
            # exacto (RONDA 14) + 3 wrappers combinados cerrados via llamada
            # DIRECTA a FlowXpert.xll (RONDA 15, ver
            # normas/_ngl_lpg_wrappers_xll_directo.py y docstring RONDA 15 en
            # normas/API_MPMS_Tables_1980_2004.py). Familia COMPLETA, 9/9.
            "E NGL/LPG (TP-27)": [
                (tab_api_dens15c_ngl_lpg, "API Density @15°C NGL/LPG"),
                (tab_api_dens20c_ngl_lpg, "API Density @20°C NGL/LPG"),
                (tab_api_rd60f_ngl_lpg, "API Rel. Density @60°F NGL/LPG"),
                (tab_api_table23e, "API Table-23E"),
                (tab_api_table24e, "API Table-24E"),
                (tab_api_table53e, "API Table-53E"),
                (tab_api_table54e, "API Table-54E"),
                (tab_api_table59e, "API Table-59E"),
                (tab_api_table60e, "API Table-60E"),
            ],
            # "API 11.3.2.1 Ethylene" / "API 11.3.3.2 Propylene" -- las 2
            # entradas restantes del menu raiz "API" cerradas numericamente
            # (2026-08-27, ver normas/_ethylene_propylene_xll_directo.py):
            # Ronda 1 (sobre el .so de Android) habia quedado bloqueada por
            # faltar las ~15-20 constantes DAT_ propias de cada ecuacion --
            # bloqueo resuelto llamando DIRECTO al nucleo real dentro del
            # .xll (mismo binario que ya tiene esas constantes), sin
            # necesidad de extraer ninguna a mano. Ambas CERRADAS [CERTAIN]
            # con el caso real ya documentado en Ronda 1, exacto a 5-6
            # decimales.
            "API 11.3.2.1/11.3.3.2 (Ethylene/Propylene)": [
                (tab_api_ethylene, "API 11.3.2.1 Ethylene"),
                (tab_api_propylene, "API 11.3.3.2 Propylene"),
            ],
            # "GPA" -- categoria propia del menu raiz (RONDA 44, 2026-09-10):
            # confirmada en vivo por uiautomator con 2 pantallas, "GPA-2172"
            # (NO implementada aun, ver estado.md RONDA 43) y "GPA-TP15"
            # (CERRADA esta ronda, [CERTAIN] con 7 casos reales nuevos --
            # ver normas/GPA_TP15.py). GPA-TP15 tambien se usa como
            # sub-calculo interno dentro de "E NGL/LPG (TP-27)" (mismo
            # nucleo Python, sin duplicar codigo).
            "GPA": [
                (tab_gpa_tp15, "GPA-TP15"),
                (tab_gpa2172_c, "GPA-2172 (US)"),
                (tab_gpa2172_m, "GPA-2172 (Metric)"),
            ],
            # "ASTM" -- categoria propia del menu raiz. Las 2 pantallas de
            # D1550 CERRADAS [CERTAIN] en RONDA 45 -- ver
            # normas/ASTM_D1550.py. `RD60` REUSA el mismo nucleo de
            # `api_mpms_11_2_2` (familia "API 11.2/12.2") como sub-paso de
            # compresibilidad, confirmado por decompilacion directa.
            # RONDA 47 (2026-09-10): confirmado EN VIVO (arbol de UI completo,
            # sin scroll pendiente) que la categoria "ASTM" tiene EXACTAMENTE
            # 3 pantallas -- las 2 de D1550 arriba, mas "ASTM D4311M (2009)"
            # (UNICA pantalla real de toda la familia D4311, exclusivamente
            # la variante METRICA de 2009; la customary 2009 y las 2
            # variantes sin sufijo "2015" existen en el binario pero NO
            # tienen pantalla propia -- ver normas/ASTM_D4311.py).
            "ASTM": [
                (tab_astm_d1550_ctl, "ASTM D1550 CTL"),
                (tab_astm_d1550_rd60, "ASTM D1550 Rel. Density @60F"),
                (tab_astm_d4311m_09_m, "ASTM D4311M (2009)"),
            ],
        }

        self.familia_var = tk.StringVar(value=list(self._familias.keys())[0])
        combo_familia = ttk.Combobox(barra_familia, textvariable=self.familia_var,
                                      values=list(self._familias.keys()),
                                      state="readonly", width=34)
        combo_familia.pack(side="left")
        combo_familia.bind("<<ComboboxSelected>>", self._cambiar_familia)

        self._cambiar_familia()

    def _cambiar_familia(self, event=None):
        """Cambia que grupo de pestanas ya construidas muestra el Notebook.
        sub_notebook.forget() NO destruye los frames (solo los desasocia
        del notebook) -- todo el estado (StringVars, texto escrito) se
        conserva al volver a una familia visitada antes."""
        for tab_id in list(self.sub_notebook.tabs()):
            self.sub_notebook.forget(tab_id)
        for frame, titulo in self._familias[self.familia_var.get()]:
            self.sub_notebook.add(frame, text=titulo)

    def _crear_frame_scrollable(self, parent):
        """Envuelve 'parent' en un Canvas + Scrollbar vertical Y horizontal
        (mismo patron que ya usaba la pestaña Memoria de Calculo) y devuelve
        el frame interno donde va el contenido real. La barra horizontal solo
        aparece/se necesita si el contenido real es mas ancho que la ventana
        (la mayoria de las pestañas no la necesitan porque el texto usa
        wraplength, pero pestañas con muchas columnas de entradas si pueden
        llegar a necesitarla). La rueda del mouse scrollea vertical (rueda
        normal) u horizontal (Shift+rueda) solo mientras el cursor esta
        encima de este canvas -- no afecta otras pestañas."""
        canvas = tk.Canvas(parent, highlightthickness=0, bg=FONDO_CLARO)
        scroll_y = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_x = ttk.Scrollbar(parent, orient="horizontal", command=canvas.xview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_mousewheel_shift(event):
            canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_rueda(_e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Shift-MouseWheel>", _on_mousewheel_shift)

        def _unbind_rueda(_e):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Shift-MouseWheel>")

        canvas.bind("<Enter>", _bind_rueda)
        canvas.bind("<Leave>", _unbind_rueda)
        return inner

    def _build_tab_nx19(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="NX-19 -- metodo SG + Poder Calorifico (pantalla 'NX-19' de la "
                              "app, con el interruptor 'PTB G9 Correction'). El motor real es "
                              "Nx19_Calc, que despacha a Z_AGA_nx19 / Z_AGA_nx19_mod / "
                              "Z_AGA_nx19_3H segun PTB G9 y el GHV. Se ejecuta el binario REAL: "
                              "por defecto una llamada directa (ctypes) al mismo codigo dentro de "
                              "FlowXpert.xll (~1 ms, sin Excel), con respaldo automatico a "
                              "emulacion de CPU (Unicorn) sobre libFXLibrary.so si el primero no "
                              "esta disponible -- en ambos casos, resultado exacto, no aproximado. "
                              "Ver normas/NX_19.py, normas/_nx19_xll_directo.py y "
                              "normas/_nx19_emulador.py.",
                  font=("Segoe UI", 10, "bold"), foreground="#1F497D", wraplength=760
                  ).pack(anchor="w", pady=(4, 8))

        cols2 = ttk.Frame(outer)
        cols2.pack(fill="both", expand=True, pady=(0, 10))
        left2 = ttk.LabelFrame(cols2, text="Entradas", padding=10)
        left2.grid(row=0, column=0, sticky="n", padx=(0, 10))

        # [RONDA 52 (2026-09-14)] Pressure/Temperature/Gross Heating Val./
        # Nitrogen Fraction/CO2 Fraction: selectores REALES de unidad
        # confirmados en vivo (uiautomator, ver comentario junto a
        # NX19_GHV_A_MJM3/NX19_FRACCION_A_MOLMOL mas arriba) -- antes de
        # esta ronda los 5 eran Entry con unidad fija en la etiqueta, sin
        # Combobox (hueco documentado en RONDA 51). Specific Gravity SIGUE
        # sin selector (confirmado adimensional en la pantalla real).
        self.nx19_ghv_entries = {}
        fila = 0
        ttk.Label(left2, text="Pressure").grid(row=fila, column=0, sticky="w", pady=3)
        self.nx19_ghv_entries["p_bar"] = self._agregar_fila_presion(
            left2, fila, API_PRESION_ABS_A_BARA, valor_default=10.0)
        fila += 1
        ttk.Label(left2, text="Temperature").grid(row=fila, column=0, sticky="w", pady=3)
        self.nx19_ghv_entries["t_degc"] = self._agregar_fila_presion(
            left2, fila, API_TEMPERATURA_A_DEGC, valor_default=25.0, unidad_default="degC")
        fila += 1
        ttk.Label(left2, text="Specific Gravity [-]", wraplength=260).grid(
            row=fila, column=0, sticky="w", pady=3)
        sg_var = tk.StringVar(value="0.6")
        ttk.Entry(left2, textvariable=sg_var, width=12).grid(row=fila, column=1, padx=6, pady=3)
        self.nx19_ghv_entries["sg"] = sg_var
        fila += 1
        ttk.Label(left2, text="Gross Heating Val.", wraplength=260).grid(
            row=fila, column=0, sticky="w", pady=3)
        self.nx19_ghv_entries["ghv"] = self._agregar_fila_presion(
            left2, fila, NX19_GHV_A_MJM3, valor_default=11943.0, unidad_default="kcal/m3")
        fila += 1
        ttk.Label(left2, text="Nitrogen Fraction", wraplength=260).grid(
            row=fila, column=0, sticky="w", pady=3)
        self.nx19_ghv_entries["n2"] = self._agregar_fila_presion(
            left2, fila, NX19_FRACCION_A_MOLMOL, valor_default=0.01)
        fila += 1
        ttk.Label(left2, text="Carbon dioxide Frac.", wraplength=260).grid(
            row=fila, column=0, sticky="w", pady=3)
        self.nx19_ghv_entries["co2"] = self._agregar_fila_presion(
            left2, fila, NX19_FRACCION_A_MOLMOL, valor_default=0.02)
        fila += 1

        row = fila
        self.nx19_ptb_g9_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left2, text="PTB G9 Correction", variable=self.nx19_ptb_g9_var).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Label(left2, text="PTB G9=0 usa Z_AGA_nx19; PTB G9=1 usa Z_AGA_nx19_mod (GHV<39.8 "
                              "MJ/m3) o Z_AGA_nx19_3H (GHV>=39.8). Resultado por emulacion exacta "
                              "del binario real (validado contra 21 casos reales, error "
                              "promedio 0.00002%). Ver normas/NX_19.py para el detalle.",
                  foreground="#1F497D", wraplength=280).grid(
            row=row + 1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Button(left2, text="Calcular Z (SG+GHV)", style="Accento.TButton",
                   command=self.on_calcular_nx19_ghv).grid(
            row=row + 2, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        right2 = ttk.LabelFrame(cols2, text="Resultado", padding=10)
        right2.grid(row=0, column=1, sticky="n")
        self.nx19_ghv_result_vars = self._build_result_labels(
            right2, ["z", "fpv", "rango_status"],
            {"z": "Compressibility (Z)",
             "fpv": "Supercompressibility Factor (Fpv) = 1/sqrt(Z)",
             "rango_status": "Range Status"})

    def _build_composicion_grid(self, parent, ejemplo=None):
        """Widget compartido (solo layout, sin logica de calculo) para
        ingresar la composicion de 21 componentes. Devuelve el dict de
        StringVars. Cada pestaña que lo usa mantiene su propio dict --
        no hay estado compartido entre AGA-8/GERG-2008/AGA-10."""
        ejemplo = ejemplo or {}
        entradas = {}
        mitad = (len(GAS_NOMBRES_COMPONENTES) + 1) // 2
        for i, nombre in enumerate(GAS_NOMBRES_COMPONENTES):
            col_base = 0 if i < mitad else 2
            fila = i if i < mitad else i - mitad
            ttk.Label(parent, text=nombre).grid(
                row=fila, column=col_base, sticky="w", pady=1, padx=(0, 4))
            var = tk.StringVar(value=str(ejemplo.get(nombre, 0.0)))
            ttk.Entry(parent, textvariable=var, width=8).grid(
                row=fila, column=col_base + 1, pady=1, padx=(0, 12))
            entradas[nombre] = var
        return entradas

    def _build_composicion_grid_con_neo(self, parent, ejemplo=None):
        """Igual que `_build_composicion_grid`, pero agrega el campo
        'neo-Pentano' como la fila 22 (ultima) de la MISMA grilla -- sin
        separador -- tal como lo muestra la app real (ahi neo-Pentane es
        simplemente el ultimo renglon de la lista continua de composicion,
        ver capturas AGA 8 3.jpeg / GERG GAS 2-3.jpeg / AGA 10 6.jpeg, NO
        una seccion aparte). neo-Pentano en si NO es uno de los 21
        componentes de AGA8-DETAIL/GERG (ver normas/AGA_8.py), pero se
        integra visualmente como si lo fuera, igual que en la app.
        El selector 'neo-Pentane Mode' (Add to iC5/nC5/Neglect) va debajo
        de toda la grilla -- en la app esta en otro paso de navegacion, no
        pegado a la composicion, pero aqui no hay pantallas separadas.
        Devuelve (entradas_21, neo_pentano_var, modo_var)."""
        entradas = self._build_composicion_grid(parent, ejemplo)
        ejemplo = ejemplo or {}
        mitad = (len(GAS_NOMBRES_COMPONENTES) + 1) // 2
        fila_neo = len(GAS_NOMBRES_COMPONENTES) - mitad  # hueco libre en la 2a columna
        ttk.Label(parent, text="neo-Pentano (C5)").grid(
            row=fila_neo, column=2, sticky="w", pady=1, padx=(0, 4))
        neo_var = tk.StringVar(value=str(ejemplo.get("neo-Pentano", 0.0)))
        ttk.Entry(parent, textvariable=neo_var, width=8).grid(
            row=fila_neo, column=3, pady=1, padx=(0, 12))
        fila_modo = mitad
        ttk.Label(parent, text="neo-Pentane Mode").grid(
            row=fila_modo, column=0, sticky="w", pady=(6, 1), padx=(0, 4))
        modo_var = tk.StringVar(value="Add to iC5")
        ttk.Combobox(parent, textvariable=modo_var, values=list(NEO_PENTANO_MODOS),
                     width=12, state="readonly").grid(
            row=fila_modo, column=1, columnspan=2, sticky="w", pady=(6, 1))

        fila_load = fila_modo + 1
        ttk.Label(parent, text="Cargar composicion guardada").grid(
            row=fila_load, column=0, sticky="w", pady=(6, 1), padx=(0, 4))
        composicion_guardada_var = tk.StringVar(value="")

        def _cargar(event=None):
            nombre = composicion_guardada_var.get()
            if not nombre:
                return
            comp_21, neo_val, modo = COMPOSICIONES_GUARDADAS_FLOWXPERT[nombre]
            for n in GAS_NOMBRES_COMPONENTES:
                entradas[n].set(str(comp_21.get(n, 0.0)))
            neo_var.set(str(neo_val))
            modo_var.set(modo)

        combo_load = ttk.Combobox(
            parent, textvariable=composicion_guardada_var,
            values=list(COMPOSICIONES_GUARDADAS_FLOWXPERT.keys()),
            width=14, state="readonly")
        combo_load.grid(row=fila_load, column=1, columnspan=2, sticky="w", pady=(6, 1))
        combo_load.bind("<<ComboboxSelected>>", _cargar)
        ttk.Label(parent, text="(16 composiciones reales de referencia\n"
                                "guardadas en FlowXpert, boton LOAD)",
                  foreground="gray", font=("Segoe UI", 7)).grid(
            row=fila_load + 1, column=0, columnspan=4, sticky="w", pady=(2, 0))
        return entradas, neo_var, modo_var

    def _build_composicion_grid_lista(self, parent, orden_componentes, ejemplo=None, n_columnas=2,
                                       combo_guardada=False):
        """Version generica de `_build_composicion_grid` para una lista de
        componentes ARBITRARIA (no la fija de GAS_NOMBRES_COMPONENTES) --
        usada por las 5 pestañas ISO 6976, que tienen listas propias de 22
        (1983/1995/2016), 55 (ex_1995) o 60 (ex_2016) componentes.
        n_columnas: cantidad de grupos label+entry en paralelo (2 para las
        listas de 22, mas para las listas largas de 55/60 -- todas estas
        pestañas ya van dentro de un frame scrollable, ver
        `_crear_frame_scrollable`, asi que una lista alta tambien es valida,
        pero mas columnas la hace mas legible sin tanto scroll).
        combo_guardada: si True, agrega debajo de la grilla el combobox
        "Cargar composicion guardada" (ver `_agregar_selector_composicion_guardada`)."""
        ejemplo = ejemplo or {}
        entradas = {}
        total = len(orden_componentes)
        por_columna = (total + n_columnas - 1) // n_columnas
        for i, nombre in enumerate(orden_componentes):
            grupo = i // por_columna
            fila = i % por_columna
            col_base = grupo * 2
            ttk.Label(parent, text=nombre).grid(
                row=fila, column=col_base, sticky="w", pady=1, padx=(0, 4))
            var = tk.StringVar(value=str(ejemplo.get(nombre, 0.0)))
            ttk.Entry(parent, textvariable=var, width=8).grid(
                row=fila, column=col_base + 1, pady=1, padx=(0, 12))
            entradas[nombre] = var
        if combo_guardada:
            self._agregar_selector_composicion_guardada(
                parent, entradas, orden_componentes, fila=por_columna)
        return entradas

    def _agregar_selector_composicion_guardada(self, parent, entradas, orden_componentes, fila):
        """Agrega, debajo de una grilla ya construida por
        `_build_composicion_grid_lista` (`entradas`: dict nombre->StringVar),
        el combobox "Cargar composicion guardada" que carga una de las 16
        composiciones reales guardadas en FlowXpert (boton LOAD,
        `COMPOSICIONES_GUARDADAS_FLOWXPERT`).

        Confirmado en vivo 2026-08-18 (uiautomator sobre el emulador real,
        pantalla "ISO-6976 (2016)"): el boton LOAD de esa pantalla abre la
        MISMA activity "Compositions" / "Select composition to load" con las
        MISMAS 16 opciones (Amarillo, Default, Dry Air, Ekofisk, Groningen,
        Gulf Coast, HiCal, High CO2-N2, High N2, Nordic, Pure CO2, Pure
        Methane, Pure Nitrogen, Sleen, Slochteren, Wet Gas) ya extraidas y
        documentadas en `COMPOSICIONES_GUARDADAS_FLOWXPERT` -- es decir, el
        selector es GENUINAMENTE COMPARTIDO entre normas, no exclusivo de
        AGA-8. Se verifico ademas que los VALORES cargados en la grilla de
        ISO 6976 coinciden EXACTOS con el dict ya guardado para 2 casos
        (Ekofisk: 9 valores no-cero, Total 100.0000%; Dry Air: 5 valores
        no-cero, Total 99.9978% -- el mismo total "raro" ya documentado, una
        huella fuerte de que es la misma fuente de datos).

        Los nombres 'Isobutano'/'Isopentano' de ese dict se traducen a
        'i-Butano'/'i-Pentano' via `_AGA5_MAPEO_NOMBRES` (ISO 6976 usa el
        MISMO orden/nombres de 22 componentes que AGA5_COMPONENTES, ver
        `normas/ISO_6976.py` ORDEN_COMPONENTES_APP). Los componentes de
        `orden_componentes` que no forman parte de ninguna composicion
        guardada (las variantes 'ex_1995'/'ex_2016' tienen 55/60 nombres,
        la data guardada solo cubre 22) se ponen en 0.0 -- comportamiento
        explicitamente pedido, no un descuido."""
        ttk.Label(parent, text="Cargar composicion guardada").grid(
            row=fila, column=0, sticky="w", pady=(6, 1), padx=(0, 4))
        var_sel = tk.StringVar(value="")
        inverso_aga5 = {v: k for k, v in _AGA5_MAPEO_NOMBRES.items()}

        def _cargar(event=None):
            nombre = var_sel.get()
            if not nombre:
                return
            comp_21, neo_val, _modo = COMPOSICIONES_GUARDADAS_FLOWXPERT[nombre]
            for n in orden_componentes:
                if n == "neo-Pentano":
                    entradas[n].set(str(neo_val))
                    continue
                n_origen = inverso_aga5.get(n, n)
                entradas[n].set(str(comp_21.get(n_origen, 0.0)))

        combo = ttk.Combobox(parent, textvariable=var_sel,
                              values=list(COMPOSICIONES_GUARDADAS_FLOWXPERT.keys()),
                              width=14, state="readonly")
        combo.grid(row=fila, column=1, columnspan=2, sticky="w", pady=(6, 1))
        combo.bind("<<ComboboxSelected>>", _cargar)
        ttk.Label(parent, text="(16 composiciones reales de FlowXpert, boton LOAD --\n"
                                "confirmado que ISO 6976 comparte el mismo selector/datos\n"
                                "que AGA-8/GERG/AGA-10/AGA-5, ver comentario del codigo)",
                  foreground="gray", font=("Segoe UI", 7)).grid(
            row=fila + 1, column=0, columnspan=4, sticky="w", pady=(2, 0))
        return var_sel

    def _build_condiciones_con_unidad(self, parent, campos=None, t_default_K=None, p_default_kPa=None):
        """Campos de condiciones (Temperatura/Presion, una o varias veces)
        CON selector de unidad, igual que la app real (que deja elegir
        K/degC/degF y kPa/Pa/MPa/psia/bar(a)/bar(g)/atm/mmHg/inHg/inH2O --
        unidades confirmadas contra libFXLibrary.so, ver
        TEMPERATURA_A_KELVIN/PRESION_A_KPA). El valor por defecto se
        muestra en la unidad NATIVA de las funciones de calculo (K, kPa)
        para no alterar los casos ya validados; el usuario puede cambiar
        la unidad sin tocar el valor.

        `campos`: lista de (clave, etiqueta, tabla, unidad_nativa, default).
        Si se omite, usa el caso simple de 2 campos "T"/"P" (compatibilidad
        con las pantallas de 1 sola condicion, usando t_default_K/
        p_default_kPa).
        Devuelve un dict {clave: (valor_var, unidad_var)}."""
        if campos is None:
            campos = [
                ("T", "Temperatura", TEMPERATURA_A_KELVIN, "K", t_default_K),
                ("P", "Presion", PRESION_A_KPA, "kPa", p_default_kPa),
            ]
        entradas = {}
        for fila, (clave, etiqueta, tabla, unidad_nativa, default) in enumerate(campos):
            ttk.Label(parent, text=etiqueta, wraplength=150).grid(row=fila, column=0, sticky="w", pady=3)
            valor_var = tk.StringVar(value=str(default))
            ttk.Entry(parent, textvariable=valor_var, width=12).grid(
                row=fila, column=1, padx=(6, 4), pady=3)
            unidad_var = tk.StringVar(value=unidad_nativa)
            ttk.Combobox(parent, textvariable=unidad_var, values=[u for u, _ in tabla],
                         width=8, state="readonly").grid(row=fila, column=2, pady=3)
            entradas[clave] = (valor_var, unidad_var)
        return entradas

    @staticmethod
    def _leer_valor_convertido(entradas, clave, tabla):
        """Lee un campo de `_build_condiciones_con_unidad` y lo convierte a
        la unidad nativa de la tabla (Kelvin para TEMPERATURA_A_KELVIN,
        kPa para PRESION_A_KPA). Puede lanzar ValueError (numero invalido)
        -- el llamador ya captura eso."""
        valor_var, unidad_var = entradas[clave]
        conv = dict(tabla)[unidad_var.get()]
        return conv(float(valor_var.get()))

    @classmethod
    def _leer_T_P_en_kelvin_kpa(cls, entradas):
        """Atajo para el caso simple de 2 campos ('T', 'P')."""
        T_K = cls._leer_valor_convertido(entradas, "T", TEMPERATURA_A_KELVIN)
        P_kPa = cls._leer_valor_convertido(entradas, "P", PRESION_A_KPA)
        return T_K, P_kPa

    @staticmethod
    def _revisar_suma_composicion_o_avisar(composicion_21, neo_pentano, modo_neo_pentano,
                                            grupos_result_vars):
        """Replica 'Status: Composition 100% error' de la app real (ver
        `validar_suma_composicion` en normas/AGA_8.py): si la composicion no
        suma ~100%, deja todos los resultados en ese texto, muestra el aviso,
        y devuelve False (el llamador debe `return` de inmediato, antes de
        intentar calcular nada -- asi se comporta la app real)."""
        valido, suma = validar_suma_composicion(composicion_21, neo_pentano, modo_neo_pentano)
        if valido:
            return True
        for grupo in grupos_result_vars:
            for var in grupo.values():
                var.set("Composition 100% error")
        messagebox.showerror(
            "Composition 100% error",
            f"La composicion suma {suma:.4f}%, no 100% (con neo-Pentano ya plegado "
            f"segun el modo '{modo_neo_pentano}'). Revisa los 21 campos + neo-Pentano.")
        return False

    # Composicion "Default" REAL de FlowXpert (no la NIST "ExampleGerg" que
    # estaba antes aqui) -- validada con 3 capturas reales de la app, una por
    # cada modo de neo-Pentano (Add to iC5 / Add to nC5 / Neglect), todas a
    # T=273.15 K, P=101.325 kPa, Edition 1994, pantalla "AGA-8":
    #   Add to iC5: Z=0.997731, Mass Density=0.833395 kg/m3
    #   Add to nC5: Z=0.997731, Mass Density=0.833395 kg/m3
    #   Neglect:    Z=0.997732, Mass Density=0.833203 kg/m3
    # (ver normas/AGA_8.py, coincide <0.001% en los 3 modos).
    EJEMPLO_GAS_NATURAL = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "Isobutano": 0.06, "n-Butano": 0.072,
        "Isopentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "n-Nonano": 0.0,
        "n-Decano": 0.0, "Hidrogeno": 0.0, "Oxigeno": 0.0,
        "CO": 0.0, "Agua": 0.0, "H2S": 0.0, "Helio": 0.046, "Argon": 0.0,
        "neo-Pentano": 0.008,
    }

    # ------------------------------------------------------------------ #
    def _build_tab_aga8(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Factor de compresibilidad (Z) y densidad del gas natural segun "
                              "AGA-8 DETAIL (Part 1).", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "En FlowXpert esta pantalla se llama 'AGA-8 DC' -- 'Compressibility (Z) and "
            "Density according to AGA-8 DC (Detail Characterization method)'.",
            "Traduccion de DETAIL.FOR (NIST, dominio publico), confirmada contra FlowXpert.xll "
            "y validada contra caso real. Ver normas/AGA_8.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.aga8_comp_entries, self.aga8_neo_var, self.aga8_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.aga8_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="273.15", p_default_kPa="101.325")

        row = len(self.aga8_entries)
        ttk.Label(cond_frame, text="Edition (referencia)").grid(row=row, column=0, sticky="w", pady=3)
        self.aga8_edition_var = tk.StringVar(value="1994")
        ttk.Combobox(cond_frame, textvariable=self.aga8_edition_var, values=["1994", "2017"],
                     width=10, state="readonly").grid(row=row, column=1, padx=6, pady=3)
        ttk.Label(cond_frame, text="El calculo NO depende de la Edicion (confirmado\n"
                                    "en el motor real) -- solo cambia cual clasificacion\n"
                                    "de rango se resalta abajo.",
                  foreground="gray", wraplength=230).grid(row=row + 1, column=0, columnspan=2,
                                                           sticky="w", pady=(2, 0))

        ttk.Button(right_col, text="Calcular (AGA-8 DETAIL)", style="Accento.TButton",
                   command=self.on_calcular_aga8).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.aga8_result_vars = self._build_result_labels(
            result_frame, ["Z", "D_mass_kg_m3", "D_mol_l", "Mm_g_mol"],
            {"Z": "Compressibility (Z)", "D_mass_kg_m3": "Mass Density [kg/m3]",
             "D_mol_l": "Molar Density [kmol/m3]", "Mm_g_mol": "Molar Mass [kg/kmol]"})

        rango_frame = ttk.LabelFrame(right_col, text="Rango valido (Edition 1994 / 2017)", padding=10)
        rango_frame.pack(fill="x", pady=(10, 0))
        self.aga8_rango_vars = self._build_result_labels(
            rango_frame, ["clasificacion_1994", "clasificacion_2017", "gate"],
            {"clasificacion_1994": "Edition 1994", "clasificacion_2017": "Edition 2017",
             "gate": "El motor calcula?"})

    def on_calcular_aga8(self):
        try:
            composicion_21 = {n: float(self.aga8_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
                composicion_21, float(self.aga8_neo_var.get()), self.aga8_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.aga8_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.aga8_neo_var.get()), self.aga8_modo_neo_var.get(),
                [self.aga8_result_vars]):
            return
        rango = validar_rango_aga8(composicion, T_K, P_kPa)
        self.aga8_rango_vars["clasificacion_1994"].set(rango["clasificacion_1994"])
        self.aga8_rango_vars["clasificacion_2017"].set(rango["clasificacion_2017"])
        self.aga8_rango_vars["gate"].set("Si" if rango["valido"] else "No (fuera de -129..204 degC / 0..1379 bar)")
        if not rango["valido"]:
            messagebox.showerror("Fuera de rango", rango["mensaje"])
            return
        try:
            prop = aga8_calcular_propiedades(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        # DensityDetail() ya devuelve ierr!=0 cuando el metodo DETAIL no
        # converge (tipicamente composicion/condicion en fase liquida,
        # fuera del rango valido de la ecuacion) -- antes esto se ignoraba
        # y se mostraban numeros sin sentido (Z en miles, densidades
        # negativas). Confirmado 2026-07-31 contra la app real (n-Octano
        # puro, 870 psia/104degF): FlowXpert muestra "Status: Calculation
        # error" y NINGUN numero, no un valor equivocado. Replicamos ese
        # comportamiento en vez de mostrar el numero de gas ideal de
        # respaldo que devuelve DensityDetail() internamente.
        if prop.get("ierr", 0) != 0:
            for var in self.aga8_result_vars.values():
                var.set("Calculation error")
            messagebox.showerror(
                "Calculation error",
                f"El metodo DETAIL no convergio para esta composicion/condicion "
                f"(probablemente fase liquida, fuera del rango valido de la ecuacion).\n\n"
                f"{prop.get('msg_error', '')}")
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.aga8_result_vars.items():
            var.set(f"{prop[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2008(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Propiedades termodinamicas del gas natural segun AGA-8 Part 2 "
                              "(ecuacion GERG-2008).", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "En FlowXpert esta pantalla se llama 'AGA8 GERG' -- 'Thermodynamic Properties of "
            "Gas according to AGA8 2007 Part 2 (GERG)'.",
            "Traduccion de GERG2008.FOR (NIST, dominio publico), confirmada contra FlowXpert.xll "
            "y validada contra caso real. Ver normas/GERG_2008.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gerg_comp_entries, self.gerg_neo_var, self.gerg_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.gerg_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="298.15", p_default_kPa="10000")
        ttk.Button(right_col, text="Calcular (GERG-2008)", style="Accento.TButton",
                   command=self.on_calcular_gerg2008).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gerg_result_vars = self._build_result_labels(
            result_frame, ["Z", "D_mass_kg_m3", "D_mol_l", "Mm_g_mol", "W_m_s", "Kappa"],
            {"Z": "Compressibility (Z)", "D_mass_kg_m3": "Mass Density [kg/m3]",
             "D_mol_l": "Molar Density [kmol/m3]", "Mm_g_mol": "Molar Mass [kg/kmol]",
             "W_m_s": "Speed of Sound [m/s]", "Kappa": "Isentropic Exponent"})

    def on_calcular_gerg2008(self):
        try:
            composicion_21 = {n: float(self.gerg_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
                composicion_21, float(self.gerg_neo_var.get()), self.gerg_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.gerg_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.gerg_neo_var.get()), self.gerg_modo_neo_var.get(),
                [self.gerg_result_vars]):
            return
        try:
            prop = gerg2008_calcular_propiedades(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        # Ver on_calcular_aga8() para el detalle: el solver de densidad
        # puede no converger (fase liquida) y devolver un numero de
        # respaldo sin sentido -- FlowXpert muestra "Calculation error" en
        # vez de un numero en ese caso, confirmado 2026-07-31.
        if prop.get("ierr", 0) != 0:
            for var in self.gerg_result_vars.values():
                var.set("Calculation error")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.gerg_result_vars.items():
            var.set(f"{prop[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2008_gas(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Propiedades termodinamicas del gas natural en una sola fase segun "
                              "GERG-2008.", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Pantalla real de FlowXpert: 'GERG-2008 Gas' -- 'Thermodynamic Properties of Gas "
            "according to GERG-2008.'",
            "Es una entrada de menu distinta de 'AGA8 GERG', aunque ambas usan el mismo motor "
            "real y dan los mismos valores -- se muestra por separado para comparar cada una "
            "contra su propia captura. Ver normas/GERG_2008.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gerg2008g_comp_entries, self.gerg2008g_neo_var, self.gerg2008g_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.gerg2008g_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="298.15", p_default_kPa="10000")
        ttk.Button(right_col, text="Calcular (GERG-2008 Gas)", style="Accento.TButton",
                   command=self.on_calcular_gerg2008_gas).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gerg2008g_result_vars = self._build_result_labels(
            result_frame, ["Z", "D_mass_kg_m3", "D_mol_l", "Mm_g_mol", "W_m_s", "Kappa"],
            {"Z": "Compressibility (Z)", "D_mass_kg_m3": "Mass Density [kg/m3]",
             "D_mol_l": "Molar Density [kmol/m3]", "Mm_g_mol": "Molar Mass [kg/kmol]",
             "W_m_s": "Speed of Sound [m/s]", "Kappa": "Isentropic Exponent"})

    def on_calcular_gerg2008_gas(self):
        try:
            composicion_21 = {n: float(self.gerg2008g_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
                composicion_21, float(self.gerg2008g_neo_var.get()), self.gerg2008g_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.gerg2008g_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.gerg2008g_neo_var.get()), self.gerg2008g_modo_neo_var.get(),
                [self.gerg2008g_result_vars]):
            return
        try:
            prop = gerg2008_calcular_propiedades(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if prop.get("ierr", 0) != 0:
            for var in self.gerg2008g_result_vars.values():
                var.set("Calculation error")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.gerg2008g_result_vars.items():
            var.set(f"{prop[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2008_flash(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Equilibrio liquido-vapor (flash) del gas natural segun GERG-2008.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente, unidades y alcance de la validacion", [
            "Pantalla real de FlowXpert: 'GERG-2008 Flash' -- 'Flash calculation according to "
            "GERG-2008.' Validada contra el caso real disponible (monofasico, VF=1.0, dif. "
            "0.00005%).",
            "La densidad se muestra en kg/m3 (masica real, coincide con 'GERG-2008 Gas'). "
            "Cuando el resultado es monofasico, la fase liquida repite el valor de vapor (no "
            "va en cero) -- asi se comporta la pantalla real.",
            "[2026-08-01] Se confirmo (rastreo de call graph + Frida en vivo sobre la app real) "
            "que la pantalla 'Flash' de FlowXpert SI corre un solver real de equilibrio de fases "
            "(minimizacion de energia de Gibbs), pero en TODOS los casos reales probados -- "
            "incluidos casos extremos (15% de Agua) -- el resultado real es monofasico "
            "(Vapour Fraction=1.0 o 0.0). Por decision del proyecto, esta funcion ya NO calcula "
            "un resultado de 2 fases genuino (0<VF<1): siempre devuelve monofasico, clasificando "
            "vapor/liquido por energia de Gibbs entre las 2 raices posibles de la ecuacion de "
            "estado -- igual que el resultado real observado. Ver normas/GERG_2008.py.",
            "[2026-08-01] Bug corregido: en la region liquida (T por debajo de la critica de la "
            "mezcla) la version anterior podia converger a una raiz de densidad espuria. Ahora "
            "se resuelven ambas raices candidatas y se elige la de menor energia de Gibbs -- "
            "validado contra 2 casos reales nuevos (CO2 100% y CO2 99%/n-Pentano 1%, ambos a "
            "100 bar(a)/0 degC, region liquida real del CO2).",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gerg2008f_comp_entries, self.gerg2008f_neo_var, self.gerg2008f_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.gerg2008f_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="298.15", p_default_kPa="10000")
        ttk.Button(right_col, text="Calcular (GERG-2008 Flash)", style="Accento.TButton",
                   command=self.on_calcular_gerg2008_flash).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gerg2008f_result_vars = self._build_result_labels(
            result_frame,
            ["vapor_fraction", "Z_vapor", "Z_liquido", "Z_total",
             "D_vapor_kg_m3", "D_liquido_kg_m3", "D_total_kg_m3"],
            {"vapor_fraction": "Vapour Fraction",
             "Z_vapor": "Vapour Compr.", "Z_liquido": "Liquid Compr.", "Z_total": "Total Compr.",
             "D_vapor_kg_m3": "Vapour Density [kg/m3]",
             "D_liquido_kg_m3": "Liquid Density [kg/m3]",
             "D_total_kg_m3": "Total Density [kg/m3]"})

    def on_calcular_gerg2008_flash(self):
        try:
            composicion_21 = {n: float(self.gerg2008f_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
                composicion_21, float(self.gerg2008f_neo_var.get()), self.gerg2008f_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.gerg2008f_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.gerg2008f_neo_var.get()), self.gerg2008f_modo_neo_var.get(),
                [self.gerg2008f_result_vars]):
            return
        try:
            res = gerg2008_calcular_flash(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        # Mismo chequeo que se agrego a los modos "Gas" (2026-07-31):
        # DensityGERG() puede no converger (fase liquida) -- calcular_flash()
        # YA propaga ese ierr en la rama monofasica (confirmado), pero
        # nadie lo revisaba aqui.
        if res.get("ierr", 0) != 0:
            for var in self.gerg2008f_result_vars.values():
                var.set("Calculation error")
            messagebox.showerror("Calculation error", res.get("msg_error", ""))
            return
        for key, var in self.gerg2008f_result_vars.items():
            var.set(f"{res[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2004_gas(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Propiedades termodinamicas del gas natural en una sola fase segun "
                              "GERG-2004.", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Pantalla real de FlowXpert: 'GERG-2004 Gas' -- 'Thermodynamic properties of gas "
            "according to GERG-2004 (not split).'",
            "Es una ruta de codigo distinta de GERG-2008 Gas, pero comparte la misma tabla de "
            "coeficientes (publicados tambien en la monografia tecnica GERG-2004). Validado "
            "contra caso real (dif. <0.00005%). Ver normas/GERG_2004.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gerg2004_comp_entries, self.gerg2004_neo_var, self.gerg2004_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.gerg2004_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="400", p_default_kPa="50000")
        ttk.Button(right_col, text="Calcular (GERG-2004 Gas)", style="Accento.TButton",
                   command=self.on_calcular_gerg2004_gas).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gerg2004_result_vars = self._build_result_labels(
            result_frame, ["Z", "D_mass_kg_m3", "W_m_s", "Kappa"],
            {"Z": "Compressibility (Z)", "D_mass_kg_m3": "Density [kg/m3]",
             "W_m_s": "Speed of Sound [m/s]", "Kappa": "Isentropic Exponent"})

    def on_calcular_gerg2004_gas(self):
        try:
            composicion_21 = {n: float(self.gerg2004_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano_gerg(
                composicion_21, float(self.gerg2004_neo_var.get()), self.gerg2004_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.gerg2004_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.gerg2004_neo_var.get()), self.gerg2004_modo_neo_var.get(),
                [self.gerg2004_result_vars]):
            return
        try:
            prop = gerg2004_calcular_propiedades_gas(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if prop.get("ierr", 0) != 0:
            for var in self.gerg2004_result_vars.values():
                var.set("Calculation error")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.gerg2004_result_vars.items():
            var.set(f"{prop[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2004_flash(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Equilibrio liquido-vapor (flash) del gas natural segun GERG-2004.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente, unidades y alcance de la validacion", [
            "Pantalla real de FlowXpert: 'GERG-2004 Flash' -- 'Flash calculation according to "
            "GERG-2004.' Validada contra el caso real disponible (monofasico, VF=1.0, dif. "
            "0.00005%).",
            "Aviso de unidad: la app etiqueta la densidad como 'kg/m3' pero el numero que "
            "muestra coincide con la densidad molar (kmol/m3), no la masica real -- se replica "
            "tal cual la app.",
            "[2026-08-01] Se confirmo (rastreo de call graph + Frida en vivo sobre la app real) "
            "que la pantalla 'Flash' de FlowXpert SI corre un solver real de equilibrio de fases "
            "(minimizacion de energia de Gibbs), pero en TODOS los casos reales probados -- "
            "incluidos casos extremos (15% de Agua) -- el resultado real es monofasico "
            "(Vapour Fraction=1.0 o 0.0). Por decision del proyecto, esta funcion ya NO calcula "
            "un resultado de 2 fases genuino (0<VF<1): siempre devuelve monofasico, clasificando "
            "vapor/liquido por energia de Gibbs entre las 2 raices posibles de la ecuacion de "
            "estado -- igual que el resultado real observado. Ver normas/GERG_2008.py.",
            "[2026-08-01] Bug corregido: en la region liquida (T por debajo de la critica de la "
            "mezcla) la version anterior podia converger a una raiz de densidad espuria, o incluso "
            "no converger (ej. CO2 100%/CO2 99%+n-Pentano 1% a 100 bar(a)/0 degC daban un Z "
            "incorrecto o 'Calculation error'). Ahora se resuelven ambas raices candidatas y se "
            "elige la de menor energia de Gibbs -- validado contra esos 2 casos reales nuevos.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gerg2004f_comp_entries, self.gerg2004f_neo_var, self.gerg2004f_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        self.gerg2004f_entries = self._build_condiciones_con_unidad(cond_frame, t_default_K="298.15", p_default_kPa="10000")
        ttk.Button(right_col, text="Calcular (GERG-2004 Flash)", style="Accento.TButton",
                   command=self.on_calcular_gerg2004_flash).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gerg2004f_result_vars = self._build_result_labels(
            result_frame,
            ["vapor_fraction", "Z_vapor", "Z_liquido", "Z_total",
             "D_vapor_mol_l", "D_liquido_mol_l", "D_total_mol_l"],
            {"vapor_fraction": "Vapour Fraction",
             "Z_vapor": "Vapour Compr.", "Z_liquido": "Liquid Compr.", "Z_total": "Total Compr.",
             "D_vapor_mol_l": "Vapour Density [kg/m3] (app)",
             "D_liquido_mol_l": "Liquid Density [kg/m3] (app)",
             "D_total_mol_l": "Total Density [kg/m3] (app)"})

        masica_frame = ttk.LabelFrame(right_col, text="Densidad masica real (kg/m3, no la etiqueta de la app)",
                                       padding=10)
        masica_frame.pack(fill="x", pady=(10, 0))
        self.gerg2004f_masica_vars = self._build_result_labels(
            masica_frame, ["D_vapor_kg_m3", "D_liquido_kg_m3", "D_total_kg_m3"],
            {"D_vapor_kg_m3": "Vapor [kg/m3]", "D_liquido_kg_m3": "Liquido [kg/m3]",
             "D_total_kg_m3": "Total [kg/m3]"})

    def on_calcular_gerg2004_flash(self):
        try:
            composicion_21 = {n: float(self.gerg2004f_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano_gerg(
                composicion_21, float(self.gerg2004f_neo_var.get()), self.gerg2004f_modo_neo_var.get())
            T_K, P_kPa = self._leer_T_P_en_kelvin_kpa(self.gerg2004f_entries)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.gerg2004f_neo_var.get()), self.gerg2004f_modo_neo_var.get(),
                [self.gerg2004f_result_vars, self.gerg2004f_masica_vars]):
            return
        try:
            res = gerg2004_calcular_flash(composicion, T_K, P_kPa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if res.get("ierr", 0) != 0:
            for var in self.gerg2004f_result_vars.values():
                var.set("Calculation error")
            for var in self.gerg2004f_masica_vars.values():
                var.set("Calculation error")
            messagebox.showerror("Calculation error", res.get("msg_error", ""))
            return
        for key, var in self.gerg2004f_result_vars.items():
            var.set(f"{res[key]:.6f}")
        for key, var in self.gerg2004f_masica_vars.items():
            var.set(f"{res[key]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_aga10(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Velocidad del sonido, factor de supercompresibilidad (Fpv) y "
                              "propiedades termicas del gas natural segun AGA-10.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "En FlowXpert esta pantalla se llama 'AGA-10 (extended)' -- 'Thermodynamic "
            "Properties according to AGA-10'. Usa el motor AGA8-DETAIL para calcular Fpv, "
            "densidades relativas y propiedades termicas. Base fija en 0 degC/1 atm (no editable, "
            "igual que la app real).",
            "'Critical Flow: Don't calculate (fast)' usa un offset empirico por componente para "
            "H0/H/S/Cp/Cv (los 21 componentes tienen offset propio, validado <0.02% contra 8 casos "
            "reales -- mezclas y componentes puros). 'Calculate (slow)' ejecuta el binario real de "
            "FlowXpert para H0/H/S/Cp/Cv Y Critical Flow Factor -- resultado EXACTO (no una "
            "aproximacion), confirmado <0.0001% contra 7 casos reales incluyendo una mezcla. Desde "
            "2026-08-26 el camino por defecto es una llamada directa (ctypes) al mismo codigo "
            "dentro de FlowXpert.xll (~1-2 ms, sin Excel ni CPU emulada -- el nombre 'slow' ya no "
            "describe el tiempo real), con respaldo automatico a la emulacion Unicorn anterior "
            "(~11-15s) si la llamada directa no esta disponible en esta maquina. Si NINGUNO de los "
            "2 caminos esta disponible o falla puntualmente, el calculo se detiene con un error "
            "explicito -- "
            "por decision deliberada, este sistema NO tiene una formula aproximada de respaldo "
            "para Critical Flow Factor (existio una version anterior basada en NASA TM X-2308 "
            "que podia diferir hasta ~1% a presion alta; se elimino para no arriesgar un numero "
            "impreciso sin que se note).",
            "Bug REAL de FlowXpert (no de este proyecto), replicado tal cual: con gases casi "
            "monoatomicos puros (Kappa>1.6, ej. Helio/Argon puro) 'Critical Flow Factor' da un "
            "numero sin sentido fisico (~87-89 en vez de ~0.5-0.8). Se muestra un aviso visible "
            "cuando pasa -- no se oculta ni se corrige, para ser fiel a la app real.",
            "Rango valido: fase gaseosa (igual que la app real -- 'Range Status: Extended range' o "
            "'Calculation error' si la condicion cae en fase liquida o fuera del rango de AGA8-"
            "DETAIL). Barrido sistematico de condiciones extremas confirmado sin crashes.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.aga10_comp_entries, self.aga10_neo_var, self.aga10_modo_neo_var = \
            self._build_composicion_grid_con_neo(comp_frame, self.EJEMPLO_GAS_NATURAL)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        # [CERTAIN, 2026-08-03] La pantalla real "AGA-10 (extended)" de
        # FlowXpert NO tiene campos editables de Temperatura/Presion base --
        # confirmado por el usuario en el dispositivo real (no aparecen en
        # pantalla ni en el menu de opciones, que solo tiene "Customary
        # units"). PRIMERA hipotesis (base=flujo siempre) fue INCORRECTA --
        # descartada con un 2do caso real (Ekofisk, flujo=25 degC/100 bar(a)):
        # ahi Base Density=44.75857 mol/m3 != Flowing Density=5129.822 mol/m3,
        # Fpv=1.125870 (no 1.0). La base esta FIJA, no sigue al flujo.
        # CONFIRMADO CON EXACTITUD (6 valores, todos <0.00001% de diferencia):
        # la base fija real es Tb=273.15 K (0 degC), Pb=101.325 kPa (1 atm) --
        # el mismo "estandar" ya usado en todo el proyecto para validar la
        # composicion Default en AGA-8/GERG. Por eso se quitaron los campos
        # editables de la GUI (aunque `calcular_velocidad_sonido_y_fpv()` en
        # normas/AGA_10.py sigue aceptando Tb_K/Pb_kPa independientes para
        # uso programatico) y `on_calcular_aga10()` ahora fuerza
        # Tb_K=273.15, Pb_kPa=101.325 siempre (NO Tb_K=T_K/Pb_kPa=P_kPa,
        # que fue el intento anterior, descartado).
        self.aga10_entries = self._build_condiciones_con_unidad(cond_frame, campos=[
            ("T_K", "Temperatura de flujo", TEMPERATURA_A_KELVIN, "K", "400"),
            ("P_kPa", "Presion de flujo", PRESION_A_KPA, "kPa", "50000"),
        ])
        row = len(self.aga10_entries)
        ttk.Label(cond_frame, text="Critical Flow").grid(row=row, column=0, sticky="w", pady=3)
        self.aga10_critflow_var = tk.StringVar(value="Don't calculate (fast)")
        ttk.Combobox(cond_frame, textvariable=self.aga10_critflow_var,
                     values=["Don't calculate (fast)", "Calculate (slow)"],
                     width=20, state="readonly").grid(row=row, column=1, padx=6, pady=3)
        self.aga10_calc_button = ttk.Button(
            right_col, text="Calcular (AGA-10)", style="Accento.TButton",
            command=self.on_calcular_aga10)
        self.aga10_calc_button.pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.aga10_result_vars = self._build_result_labels(
            result_frame,
            ["Mm_g_mol", "D_base_mol_m3", "D_flujo_mol_m3", "D_base_kg_m3", "D_flujo_kg_m3",
             "rel_density_ideal", "rel_density_real", "W_m_s", "Z_base", "Z_flujo", "Fpv",
             "H0_kJ_kg", "H_kJ_kg", "S_kJ_kgC",
             "Cp0_kJ_kgC", "Cp_kJ_kgC", "Cv_kJ_kgC",
             "Cp0_kJ_kmolC", "Cp_kJ_kmolC", "Cv_kJ_kmolC",
             "Cp_Cv_ratio", "Kappa", "critical_flow_factor",
             "H0_kJ_kmol", "H_kJ_kmol", "isentropic_ideal_Cstar", "isentropic_real_Cstar"],
            {"Mm_g_mol": "Molar Mass [kg/kmol]",
             "D_base_mol_m3": "Base Density [mol/m3]",
             "D_flujo_mol_m3": "Flowing Density [mol/m3]",
             "D_base_kg_m3": "Base Density [kg/m3]",
             "D_flujo_kg_m3": "Flowing Density [kg/m3]",
             "rel_density_ideal": "Ideal rel. Density",
             "rel_density_real": "Real rel. Density",
             "W_m_s": "Speed of Sound [m/s]",
             "Z_base": "Base Compressibility", "Z_flujo": "Flowing Compressibility",
             "Fpv": "Fpv (supercompr.)",
             "H0_kJ_kg": "Ideal spec. Enthalpy [kJ/kg]",
             "H_kJ_kg": "Real spec. Enthalpy [kJ/kg]",
             "S_kJ_kgC": "Real spec. Entropy [kJ/kg-degC]",
             "Cp0_kJ_kgC": "Ideal isobaric Heat cap. [kJ/kg-degC]",
             "Cp_kJ_kgC": "Real isobaric Heat cap. [kJ/kg-degC]",
             "Cv_kJ_kgC": "Real isochoric Heat cap. [kJ/kg-degC]",
             "Cp0_kJ_kmolC": "Ideal isobaric Heat cap. [kJ/kmol-degC]",
             "Cp_kJ_kmolC": "Real isobaric Heat cap. [kJ/kmol-degC]",
             "Cv_kJ_kmolC": "Real isochoric Heat cap. [kJ/kmol-degC]",
             "Cp_Cv_ratio": "Specific Heats Ratio",
             "Kappa": "Isentropic Exponent",
             "critical_flow_factor": "Critical flow factor (C*)",
             "H0_kJ_kmol": "Ideal spec. Enthalpy [kJ/kmol]",
             "H_kJ_kmol": "Real spec. Enthalpy [kJ/kmol]",
             "isentropic_ideal_Cstar": "Isentropic ideal C*",
             "isentropic_real_Cstar": "Isentropic real C*"})
        ttk.Label(result_frame, text="Enthalpy: offset por componente (Metano/N2 exactos, resto "
                                      "aproximado). Entropy: constante unica, solo exacta cerca "
                                      "de 'Default' (ver nota arriba).",
                  foreground="#1F497D", wraplength=280).grid(
            row=len(self.aga10_result_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.aga10_advertencia_critflow_var = tk.StringVar(value="")
        self.aga10_advertencia_critflow_label = ttk.Label(
            result_frame, textvariable=self.aga10_advertencia_critflow_var,
            foreground="#B03A2E", font=("Segoe UI", 9, "bold"), wraplength=280)
        self.aga10_advertencia_critflow_label.grid(
            row=len(self.aga10_result_vars) + 1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # [CERTAIN, 2026-08-31] "Range" real de fxAGA10ex_M (Normal/Extendido/
        # Fuera de rango), decompilado de FlowXpert.xll -- ver
        # validar_rango_aga10() en normas/AGA_10.py. Informativo, NO
        # bloqueante (igual que el "Rango valido" de AGA-8, pero aqui nunca
        # se impide el calculo -- la app real tampoco lo hace, solo marca
        # "Range" y sigue calculando).
        rango_frame = ttk.LabelFrame(right_col, text="Rango valido (Range real de FlowXpert)", padding=10)
        rango_frame.pack(fill="x", pady=(10, 0))
        self.aga10_rango_vars = self._build_result_labels(
            rango_frame, ["rango_composicion", "rango_pt", "rango_combinado"],
            {"rango_composicion": "Por composicion", "rango_pt": "Por T/P",
             "rango_combinado": "Range combinado"})
        self.aga10_advertencia_rango_var = tk.StringVar(value="")
        self.aga10_advertencia_rango_label = ttk.Label(
            rango_frame, textvariable=self.aga10_advertencia_rango_var,
            foreground="#B03A2E", font=("Segoe UI", 9, "bold"), wraplength=280)
        self.aga10_advertencia_rango_label.grid(
            row=len(self.aga10_rango_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

    def on_calcular_aga10(self):
        try:
            composicion_21 = {n: float(self.aga10_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
                composicion_21, float(self.aga10_neo_var.get()), self.aga10_modo_neo_var.get())
            T_K = self._leer_valor_convertido(self.aga10_entries, "T_K", TEMPERATURA_A_KELVIN)
            P_kPa = self._leer_valor_convertido(self.aga10_entries, "P_kPa", PRESION_A_KPA)
            # Base FIJA (0 degC/1 atm), NO igual al flujo -- ver nota en
            # _build_tab_aga10 (confirmado contra 2 casos reales).
            Tb_K, Pb_kPa = 273.15, 101.325
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        if not self._revisar_suma_composicion_o_avisar(
                composicion_21, float(self.aga10_neo_var.get()), self.aga10_modo_neo_var.get(),
                [self.aga10_result_vars]):
            return
        calcular_flujo_critico = self.aga10_critflow_var.get() == "Calculate (slow)"

        def _mostrar_resultado(res):
            # Mismo chequeo que se agrego a AGA-8 (2026-07-31): DensityDetail()
            # puede no converger (fase liquida, fuera del rango valido) y
            # devolver un numero de gas ideal de respaldo que arrastra todo el
            # resto de propiedades derivadas a valores sin sentido. AGA-10
            # llama a DensityDetail() dos veces (flujo y base) -- si CUALQUIERA
            # de las dos no converge, todo lo derivado de esa densidad es
            # invalido.
            if res.get("ierr_flujo", 0) != 0 or res.get("ierr_base", 0) != 0:
                for var in self.aga10_result_vars.values():
                    var.set("Calculation error")
                messagebox.showerror(
                    "Calculation error",
                    "El metodo DETAIL no convergio para esta composicion/condicion "
                    "(flujo y/o base, probablemente fase liquida, fuera del rango "
                    "valido de la ecuacion).")
                self.aga10_advertencia_critflow_var.set("")
                for var in self.aga10_rango_vars.values():
                    var.set("")
                self.aga10_advertencia_rango_var.set("")
                return
            for key, var in self.aga10_result_vars.items():
                var.set(f"{res[key]:.6f}")
            # El aviso lo calcula normas/AGA_10.py (campo "aviso_bug_flowxpert_
            # critical_flow", viaja con el resultado sin importar quien llame
            # la funcion, no solo esta GUI -- ver docstring de esa funcion).
            avisos = []
            aviso_bug = res.get("aviso_bug_flowxpert_critical_flow")
            if aviso_bug:
                avisos.append(aviso_bug)
            # [CERTAIN, 2026-08-31] Nuevo, tras validar los 12 casos discrepantes
            # DIRECTO contra la app real via Frida (ver normas/AGA_10.py y
            # normas/_aga10_xll_directo.py, "VALIDACION CONTRA APP REAL"):
            # critical_flow_factor especificamente puede diverger de la app
            # real hasta ~80% fuera de "Normal", aunque el resto de campos
            # (Z_flujo/Kappa/W/H/S/Cp/Cv) siguen validados <0.0001%.
            aviso_cf_extremo = res.get("aviso_critical_flow_fuera_de_normal")
            if aviso_cf_extremo:
                avisos.append(aviso_cf_extremo)
            # [CERTAIN, 2026-08-04] Ya no existe un "plan B" aproximado para
            # Critical Flow Factor -- si el emulador no esta disponible,
            # normas/AGA_10.py levanta un error ANTES de llegar aca (ver
            # el except mas abajo), en vez de devolver un resultado con
            # metodo_critical_flow="formula_respaldo". Por eso no hace
            # falta chequear ese caso en esta pantalla.
            self.aga10_advertencia_critflow_var.set(
                "ADVERTENCIA: " + " / ".join(avisos) if avisos else "")

            # [CERTAIN, 2026-08-31] "Range" real (Normal/Extendido/Fuera de
            # rango), decompilado de FlowXpert.xll -- ver
            # normas.AGA_10.validar_rango_aga10(). NO bloquea el calculo (la
            # app real tampoco lo hace), solo se muestra bien visible --
            # mas fuerte si "Fuera de rango" (el numero puede caer en la
            # zona numericamente caotica documentada en
            # normas/_aga10_xll_directo.py, seccion "INVESTIGACION DE CAUSA
            # RAIZ 2026-08-31") que si solo "Extendido" (mayor incertidumbre,
            # pero la app real SI lo recomienda usar).
            rango = res.get("rango_aga10")
            if rango:
                self.aga10_rango_vars["rango_composicion"].set(rango["rango_composicion"])
                self.aga10_rango_vars["rango_pt"].set(rango["rango_pt"])
                self.aga10_rango_vars["rango_combinado"].set(rango["rango_combinado"])
                if rango["rango_combinado"] == "Fuera de rango":
                    self.aga10_advertencia_rango_label.config(foreground="#B03A2E")
                    self.aga10_advertencia_rango_var.set(
                        "FUERA DE RANGO: " + rango["mensaje"] + " FlowXpert desaconseja usar este "
                        "resultado (fuera del 'Expanded range' oficial); este caso puede caer en la "
                        "zona numericamente caotica ya documentada (2 caminos exactos distintos "
                        "pueden divergir entre si aqui).")
                elif rango["rango_combinado"] == "Extendido":
                    self.aga10_advertencia_rango_label.config(foreground="#B36B00")
                    self.aga10_advertencia_rango_var.set(
                        "Rango Extendido: " + rango["mensaje"] + " Mayor incertidumbre que en rango "
                        "Normal (la app real SI recomienda usar el resultado, con esa salvedad).")
                else:
                    self.aga10_advertencia_rango_var.set("")
                if not rango["valido_entrada"]:
                    self.aga10_advertencia_rango_var.set(
                        self.aga10_advertencia_rango_var.get()
                        + " ADEMAS, T/P esta fuera del campo de entrada propio de AGA-10 "
                          "(0..2000 bar(a), -200..+400 degC).")
            else:
                for var in self.aga10_rango_vars.values():
                    var.set("")
                self.aga10_advertencia_rango_var.set("")

        if not calcular_flujo_critico:
            # Camino rapido (sin emulador, sin busqueda iterativa cara) --
            # no se percibe ningun bloqueo, no hace falta hilo.
            try:
                res = calcular_velocidad_sonido_y_fpv(
                    composicion, T_K, P_kPa, Tb_K, Pb_kPa, calcular_flujo_critico=False)
            except Exception as e:
                messagebox.showerror("Error de calculo", str(e))
                return
            _mostrar_resultado(res)
            return

        # [CERTAIN, 2026-08-03] "Calculate (slow)" corre el emulador Unicorn
        # del binario real (~11s, ver docstring de normas/AGA_10.py) -- eso
        # es lo que hacia que la ventana se congelara ("No responde" de
        # Windows, reportado por el usuario), porque corria en el mismo
        # hilo que dibuja la interfaz. Se ejecuta en un hilo de fondo para
        # que la ventana siga respondiendo mientras dura el calculo.
        # Tkinter no es thread-safe: el hilo de fondo NO toca ningun widget
        # directamente, solo calcula: `self.after(0, ...)` reprograma la
        # actualizacion de resultados en el hilo principal cuando termina.
        self.aga10_calc_button.config(state="disabled")
        for var in self.aga10_result_vars.values():
            var.set("Calculando... (normalmente <1s; hasta ~11s si usa el respaldo Unicorn)")
        self.aga10_advertencia_critflow_var.set("")

        def _trabajo_en_hilo():
            try:
                res = calcular_velocidad_sonido_y_fpv(
                    composicion, T_K, P_kPa, Tb_K, Pb_kPa, calcular_flujo_critico=True)
            except Exception as e:
                self.after(0, lambda: (
                    self.aga10_calc_button.config(state="normal"),
                    messagebox.showerror("Error de calculo", str(e))))
                return

            def _terminar():
                self.aga10_calc_button.config(state="normal")
                _mostrar_resultado(res)
            self.after(0, _terminar)

        threading.Thread(target=_trabajo_en_hilo, daemon=True).start()

    # ------------------------------------------------------------------ #
    EJEMPLO_AGA5 = {
        "Metano": 81.3150, "Nitrogeno": 14.2110, "CO2": 0.9900, "Etano": 2.8290,
        "Propano": 0.3800, "Agua": 0.0, "H2S": 0.0, "Hidrogeno": 0.0, "CO": 0.0,
        "Oxigeno": 0.0, "i-Butano": 0.0600, "n-Butano": 0.0720, "i-Pentano": 0.0180,
        "n-Pentano": 0.0330, "n-Hexano": 0.0200, "n-Heptano": 0.0130, "n-Octano": 0.0050,
        "n-Nonano": 0.0, "n-Decano": 0.0, "Helio": 0.0460, "Argon": 0.0, "neo-Pentano": 0.0080,
    }

    def _build_tab_aga5(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Poder calorifico del gas natural segun AGA-5. La Gravedad "
                              "Especifica es un dato independiente, no se calcula a partir de "
                              "la composicion.", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "En FlowXpert esta pantalla se llama 'AGA-5 (Calorific Value)'. Formula "
            "reconstruida directamente del binario de FlowXpert y validada contra un caso "
            "real (diferencia <0.00002%). Ver normas/AGA_5.py.",
            "Solo N2, CO2, H2O, H2S, H2, CO, O2 y He entran en la formula; el resto de la "
            "composicion se valida pero no se usa (su efecto ya esta implicito en la Gravedad "
            "Especifica).",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (% o fraccion, 22 componentes)",
                                     padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))

        self.aga5_comp_entries = {}
        mitad = (len(AGA5_COMPONENTES) + 1) // 2
        for i, nombre in enumerate(AGA5_COMPONENTES):
            col_base = 0 if i < mitad else 2
            fila = i if i < mitad else i - mitad
            ttk.Label(comp_frame, text=nombre).grid(
                row=fila, column=col_base, sticky="w", pady=1, padx=(0, 4))
            var = tk.StringVar(value=str(self.EJEMPLO_AGA5.get(nombre, 0.0)))
            ttk.Entry(comp_frame, textvariable=var, width=8).grid(
                row=fila, column=col_base + 1, pady=1, padx=(0, 12))
            self.aga5_comp_entries[nombre] = var

        fila_load = mitad
        ttk.Label(comp_frame, text="Cargar composicion guardada").grid(
            row=fila_load, column=0, sticky="w", pady=(6, 1), padx=(0, 4))
        aga5_composicion_guardada_var = tk.StringVar(value="")

        def _cargar_aga5(event=None):
            nombre_comp = aga5_composicion_guardada_var.get()
            if not nombre_comp:
                return
            comp_21, neo_val, _modo = COMPOSICIONES_GUARDADAS_FLOWXPERT[nombre_comp]
            for n in AGA5_COMPONENTES:
                if n == "neo-Pentano":
                    continue
                n_origen = {v: k for k, v in _AGA5_MAPEO_NOMBRES.items()}.get(n, n)
                self.aga5_comp_entries[n].set(str(comp_21.get(n_origen, 0.0)))
            self.aga5_comp_entries["neo-Pentano"].set(str(neo_val))

        combo_load_aga5 = ttk.Combobox(
            comp_frame, textvariable=aga5_composicion_guardada_var,
            values=list(COMPOSICIONES_GUARDADAS_FLOWXPERT.keys()),
            width=14, state="readonly")
        combo_load_aga5.grid(row=fila_load, column=1, columnspan=2, sticky="w", pady=(6, 1))
        combo_load_aga5.bind("<<ComboboxSelected>>", _cargar_aga5)
        ttk.Label(comp_frame, text="(16 composiciones reales de referencia\n"
                                    "guardadas en FlowXpert, boton LOAD. Aqui\n"
                                    "neo-Pentano NO se pliega, se pone directo.)",
                  foreground="gray", font=("Segoe UI", 7)).grid(
            row=fila_load + 1, column=0, columnspan=4, sticky="w", pady=(2, 0))

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Gravedad Especifica", padding=10)
        cond_frame.pack(fill="x")
        ttk.Label(cond_frame, text="SG (gas/aire, medido) [-]").grid(
            row=0, column=0, sticky="w", pady=3)
        self.aga5_sg_var = tk.StringVar(value="0.7")
        ttk.Entry(cond_frame, textvariable=self.aga5_sg_var, width=12).grid(
            row=0, column=1, padx=6, pady=3)
        ttk.Label(cond_frame, text="Dato independiente, no se calcula\nde la composicion.",
                  foreground="gray", wraplength=220).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Button(right_col, text="Calcular (AGA-5)", style="Accento.TButton",
                   command=self.on_calcular_aga5).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.aga5_result_vars = self._build_result_labels(
            result_frame, ["cv_mass_kJ_kg", "cv_vol_kJ_sm3", "cv_mass_BTU_lbm", "cv_vol_BTU_scf"],
            {"cv_mass_kJ_kg": "Poder calorifico masico [kJ/kg]",
             "cv_vol_kJ_sm3": "Poder calorifico volumetrico [kJ/Sm3]",
             "cv_mass_BTU_lbm": "(nativo) [BTU/lbm]",
             "cv_vol_BTU_scf": "(nativo) [BTU/scf]"})

    def on_calcular_aga5(self):
        try:
            composicion = {n: float(self.aga5_comp_entries[n].get()) for n in AGA5_COMPONENTES}
            sg = float(self.aga5_sg_var.get())
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            res = aga5_calcular_poder_calorifico(composicion, sg)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        self.aga5_result_vars["cv_mass_kJ_kg"].set(f"{res['cv_mass_kJ_kg']:.2f}")
        self.aga5_result_vars["cv_vol_kJ_sm3"].set(f"{res['cv_vol_kJ_sm3']:.2f}")
        self.aga5_result_vars["cv_mass_BTU_lbm"].set(f"{res['cv_mass_BTU_lbm']:.4f}")
        self.aga5_result_vars["cv_vol_BTU_scf"].set(f"{res['cv_vol_BTU_scf']:.4f}")

    # ================================================================== #
    # ISO 6976 -- poder calorifico, densidad, densidad relativa e indice
    # de Wobbe. 5 variantes reales de FlowXpert (ver normas/ISO_6976*.py,
    # familia COMPLETAMENTE CERRADA sin pendientes bloqueantes). Composicion
    # "Default" real precargada en las 5 (mismos 14 componentes no-nulos,
    # ver seccion 4 del docstring de normas/ISO_6976.py).
    # ================================================================== #
    def _build_tab_iso6976_1983(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ISO 6976:1983 -- poder calorifico, densidad y densidad relativa. "
                              "Motor binario propio de FlowXpert (distinto del de 2016_M), CERRADO "
                              "a nivel de formula/constantes contra 7 casos reales de pantalla.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        ttk.Label(outer, text="CORREGIDO 2026-08-11: una ronda anterior habia concluido (sin tocar "
                              "los campos) que esta pantalla no tenia selectores de Ref. Temperature. "
                              "Era FALSO -- la app real SI tiene 2 selectores (abajo), confirmados "
                              "por UI + Frida sobre PropertiesISO6976_1983.",
                  foreground="#b05000", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Validado contra 7 casos reales de pantalla (composicion 'Default', 2 selectores "
            "variados): los 16 valores comparados cierran <0.06%. Ver normas/ISO_6976_1983.py, "
            "seccion 2A del docstring.",
            "Mapeo indice interno <-> opcion de UI confirmado con Frida en vivo sobre "
            "PropertiesISO6976_1983 (arg2=indice de Metering, arg3=indice de Cal. Val., "
            "indexacion DIRECTA en el mismo orden de la lista, sin offset).",
            "Density/Compressibility/Relative Density dependen SOLO de 'Metering Ref. Temp.'; "
            "Sup. Calorific Val. depende de ambos selectores (efecto de Metering es chico, "
            "~0.04%-0.05%, comparado con el de Cal. Val., hasta ~5%).",
            "Sub-indices internos (bj/Hoj) calibrados por mejor cierre numerico, no leidos "
            "directamente por Frida -- quedan LIKELY, no CERTAIN (igual estandar que el resto "
            "del proyecto). 3 de las 10 combinaciones (2x5) no se probaron con caso real explicito "
            "(se infieren de la formula ya validada en las otras 7) -- pendiente honesto menor.",
            "22 componentes, mismo orden que AGA-5/AGA-8 (ORDEN_COMPONENTES_APP).",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 22 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.iso6976_1983_entries = self._build_composicion_grid_lista(
            comp_frame, ISO6976_COMPONENTES, ejemplo=self.EJEMPLO_AGA5, n_columnas=2,
            combo_guardada=True)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        sel_frame = ttk.LabelFrame(right_col, text="Selectores reales de la pantalla", padding=10)
        sel_frame.pack(fill="x")
        ttk.Label(sel_frame, text="Metering Ref. Temp.").grid(row=0, column=0, sticky="w", pady=3)
        self.iso6976_1983_metering_var = tk.StringVar(value=OPCIONES_METERING_1983[0])
        ttk.Combobox(sel_frame, textvariable=self.iso6976_1983_metering_var,
                     values=OPCIONES_METERING_1983, state="readonly", width=14).grid(
            row=0, column=1, padx=6, pady=3)
        ttk.Label(sel_frame, text="Cal. Val. ref. Temp.").grid(row=1, column=0, sticky="w", pady=3)
        self.iso6976_1983_calval_var = tk.StringVar(value=OPCIONES_CALVAL_1983[0])
        ttk.Combobox(sel_frame, textvariable=self.iso6976_1983_calval_var,
                     values=OPCIONES_CALVAL_1983, state="readonly", width=14).grid(
            row=1, column=1, padx=6, pady=3)
        ttk.Button(right_col, text="Calcular (ISO 6976 - 1983)", style="Accento.TButton",
                   command=self.on_calcular_iso6976_1983).pack(fill="x", pady=(10, 0))
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        claves_1983 = ["Molar Mass (g/mol)", "Compressibility (Z)", "Density (kg/m3)",
                       "Relative Density", "Sup. Calorific Val. (MJ/m3)"]
        self.iso6976_1983_result_vars = self._build_result_labels(
            result_frame, claves_1983, {k: k for k in claves_1983})

    def on_calcular_iso6976_1983(self):
        try:
            comp = {n: float(self.iso6976_1983_entries[n].get()) / 100.0
                    for n in ISO6976_COMPONENTES}
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        indice_metering = OPCIONES_METERING_1983.index(self.iso6976_1983_metering_var.get())
        indice_calval = OPCIONES_CALVAL_1983.index(self.iso6976_1983_calval_var.get())
        try:
            res = calcular_iso6976_1983(
                comp, indice_metering=indice_metering, indice_calval=indice_calval)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        for clave, var in self.iso6976_1983_result_vars.items():
            var.set(f"{res[clave]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_iso6976_1995(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ISO 6976:1995 -- poder calorifico, densidad, densidad relativa e "
                              "indice de Wobbe. Motor binario propio de FlowXpert, CERRADO con "
                              "evidencia mas fuerte que 1983 (Frida en vivo sobre la funcion real, "
                              "11 salidas confirmadas).", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Validado con Frida en vivo sobre PropertiesISO6976_1995_rev1: 11 salidas reales "
            "(5 de pantalla + 6 internas) cierran <0.03% para el combo Default. Ver "
            "normas/ISO_6976_1995.py, seccion 2.",
            "'Ref. Temperature' (2026-08-17): la pantalla real SI tiene selector con 6 opciones "
            "(NO 7 como en 2016_M, no existe combo 60F/60F/60F aqui). Las 6 se mapearon por Frida "
            "(indice real a2 = posicion en la lista + 1) y las 6 se validaron con caso real propio "
            "(peor cierre 0.029%, ver seccion 8 del docstring). Indice Hoj (poder calorifico) por "
            "temperatura de combustion queda CERTAIN (cierre 0.0006%, practicamente bit-exacto); "
            "indice bj (factor de compresion) por temperatura de metering queda LIKELY (margenes "
            "chicos ~0.01% entre columnas, pero consistente 3/3 y 2/2 dentro de cada metering).",
            "'Molar Mass Method' (Calculate/Use table) y 'Calorific Val. Method' (Definitive/"
            "Alternative): 2 selectores reales que la app SI muestra en esta pantalla (2026-08-11, "
            "confirmado con uiautomator + edicion real en el emulador). 'Molar Mass Method' es "
            "FUNCIONAL aqui (cambia Molar Mass/Density/Relative Density, confirmado en vivo). "
            "'Calorific Val. Method' SI tiene un efecto real pero minusculo (0.00003% en Sup. "
            "Calorific Val. para el caso probado) -- la formula exacta no se pudo aislar con un "
            "solo caso real, asi que queda INFORMATIVO (no cambia el resultado). Ver seccion 7 del "
            "docstring de normas/ISO_6976_1995.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 22 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.iso6976_1995_entries = self._build_composicion_grid_lista(
            comp_frame, ISO6976_COMPONENTES, ejemplo=self.EJEMPLO_AGA5, n_columnas=2,
            combo_guardada=True)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        sel_frame = ttk.LabelFrame(right_col, text="Selectores reales de la pantalla", padding=10)
        sel_frame.pack(fill="x")
        ttk.Label(sel_frame, text="Ref. Temperature").grid(row=0, column=0, sticky="w", pady=3)
        self.iso6976_1995_reftemp_var = tk.StringVar(value=OPCIONES_REF_TEMPERATURE_1995[0])
        ttk.Combobox(sel_frame, textvariable=self.iso6976_1995_reftemp_var,
                     values=OPCIONES_REF_TEMPERATURE_1995, state="readonly", width=14).grid(
            row=0, column=1, padx=6, pady=3)
        ttk.Label(sel_frame, text="Molar Mass Method").grid(row=1, column=0, sticky="w", pady=3)
        self.iso6976_1995_mmm_var = tk.StringVar(value="Use table")
        ttk.Combobox(sel_frame, textvariable=self.iso6976_1995_mmm_var,
                     values=["Calculate", "Use table"], state="readonly", width=14).grid(
            row=1, column=1, padx=6, pady=3)
        ttk.Label(sel_frame, text="Calorific Val. Method").grid(row=2, column=0, sticky="w", pady=3)
        self.iso6976_1995_cvm_var = tk.StringVar(value="Definitive")
        ttk.Combobox(sel_frame, textvariable=self.iso6976_1995_cvm_var,
                     values=["Definitive", "Alternative"], state="readonly", width=14).grid(
            row=2, column=1, padx=6, pady=3)
        ttk.Label(sel_frame, text="Las 6 opciones de 'Ref. Temperature' tienen caso real propio "
                                   "(2026-08-17, cierre <0.03%). Indice Hoj CERTAIN por opcion; "
                                   "indice bj LIKELY (margenes chicos entre columnas).\n"
                                   "'Calorific Val. Method' es informativo: efecto real confirmado "
                                   "pero minusculo (<0.0001%), formula exacta no aislada.",
                  foreground="gray", wraplength=280).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Button(right_col, text="Calcular (ISO 6976 - 1995)", style="Accento.TButton",
                   command=self.on_calcular_iso6976_1995).pack(fill="x", pady=(10, 0))
        result_frame = ttk.LabelFrame(right_col, text="Resultados (pantalla real)", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        claves_1995 = ["Molar Mass (g/mol)", "Compressibility (Z)", "Density (kg/m3)",
                       "Relative Density", "Sup. Calorific Val. (MJ/m3)"]
        self.iso6976_1995_result_vars = self._build_result_labels(
            result_frame, claves_1995, {k: k for k in claves_1995})
        ext_frame = ttk.LabelFrame(right_col, text="Resultados internos (no visibles en UI, "
                                                     "confirmados por Frida)", padding=10)
        ext_frame.pack(fill="x", pady=(10, 0))
        claves_1995_ext = ["GCV bruto, base masa (MJ/kg)", "GCV bruto, base molar (kJ/mol)",
                            "NCV neto, base volumen (MJ/m3)", "NCV neto, base masa (MJ/kg)",
                            "NCV neto, base molar (kJ/mol)", "Indice de Wobbe bruto"]
        self.iso6976_1995_result_ext_vars = self._build_result_labels(
            ext_frame, claves_1995_ext, {k: k for k in claves_1995_ext})

    def on_calcular_iso6976_1995(self):
        try:
            comp = {n: float(self.iso6976_1995_entries[n].get()) / 100.0
                    for n in ISO6976_COMPONENTES}
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            ref_temperature_index = OPCIONES_REF_TEMPERATURE_1995.index(
                self.iso6976_1995_reftemp_var.get()) + 1
            res = calcular_iso6976_1995_extendido(
                comp, molar_mass_method=self.iso6976_1995_mmm_var.get(),
                calorific_val_method=self.iso6976_1995_cvm_var.get(),
                ref_temperature_index=ref_temperature_index)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        for clave, var in self.iso6976_1995_result_vars.items():
            var.set(f"{res[clave]:.6f}")
        for clave, var in self.iso6976_1995_result_ext_vars.items():
            var.set(f"{res[clave]:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_iso6976_2016(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ISO 6976:2016 -- poder calorifico, densidad, densidad relativa e "
                              "indice de Wobbe. Variante MAS confirmada de todo el proyecto ISO "
                              "6976 (namespace real spirit::math::iso6976_2016, CERRADA sin "
                              "pendientes bloqueantes).", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente, alcance de la validacion y confianza por combo", [
            "Caso real 'Default' (15/15/15 C) confirmado BIT-EXACTO por Frida en vivo -- ver "
            "normas/ISO_6976.py, secciones 4.3/4.5/4.6.",
            "Los otros 6 combos de 'Ref. Temperature' tienen distinto nivel de confianza (ver "
            "nota que aparece abajo al elegir cada uno): 15/0/0, 20/20/20 y 60F tienen el METERING "
            "confirmado por Frida (LIKELY en el resto de parametros); 0/0/0, 25/0/0 y 25/20/20 "
            "NUNCA se probaron en vivo (GUESSING).",
            "indice_hoj_combustion=2 solo esta CERTAIN para combustion=15 C (combos 1 y 3) -- para "
            "el resto se reusa como unico estimador disponible, sin forzar una confirmacion que "
            "el proyecto no tiene (ver normas/ISO_6976.py seccion 2/4.4).",
            "'Molar Mass Method' (Calculate/Use table) y 'Metering reference pressure' (aqui en "
            "Pa): 2 selectores reales confirmados en vivo 2026-08-11 (uiautomator + edicion real). "
            "Ambos son FUNCIONALES en este modulo. 2016_M NO tiene 'Calorific Val. Method' (a "
            "diferencia de 1995_M) -- confirmado por ausencia real en la pantalla, no por omision. "
            "La pantalla real ademas muestra 11 salidas con scroll (no solo las 6 de antes) -- ver "
            "seccion 7 del docstring de normas/ISO_6976.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 22 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.iso6976_2016_entries = self._build_composicion_grid_lista(
            comp_frame, ISO6976_COMPONENTES, ejemplo=self.EJEMPLO_AGA5, n_columnas=2,
            combo_guardada=True)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones de referencia", padding=10)
        cond_frame.pack(fill="x")
        ttk.Label(cond_frame, text="Ref. Temperature").grid(row=0, column=0, sticky="w", pady=3)
        self.iso6976_2016_reftemp_var = tk.StringVar(value=REF_TEMPERATURE_ISO6976_2016[0][0])
        combo_reftemp = ttk.Combobox(
            cond_frame, textvariable=self.iso6976_2016_reftemp_var,
            values=[c[0] for c in REF_TEMPERATURE_ISO6976_2016], state="readonly", width=18)
        combo_reftemp.grid(row=0, column=1, padx=6, pady=3)
        ttk.Label(cond_frame, text="Molar Mass Method").grid(row=1, column=0, sticky="w", pady=3)
        self.iso6976_2016_mmm_var = tk.StringVar(value="Use table")
        ttk.Combobox(cond_frame, textvariable=self.iso6976_2016_mmm_var,
                     values=["Calculate", "Use table"], state="readonly", width=14).grid(
            row=1, column=1, padx=6, pady=3)
        ttk.Label(cond_frame, text="Metering ref. pressure").grid(row=2, column=0, sticky="w", pady=3)
        pref_row = ttk.Frame(cond_frame)
        pref_row.grid(row=2, column=1, padx=6, pady=3, sticky="w")
        self.iso6976_2016_pref_var = tk.StringVar(value="1013.25")
        ttk.Entry(pref_row, textvariable=self.iso6976_2016_pref_var, width=10).pack(side="left")
        self.iso6976_2016_pref_unidad_var = tk.StringVar(value="mbar")
        ttk.Combobox(pref_row, textvariable=self.iso6976_2016_pref_unidad_var,
                     values=[u for u, _f in ISO6976_PRESION_A_PA], state="readonly",
                     width=11).pack(side="left", padx=(4, 0))
        self.iso6976_2016_nota_var = tk.StringVar(value=REF_TEMPERATURE_ISO6976_2016[0][6])
        ttk.Label(cond_frame, textvariable=self.iso6976_2016_nota_var, foreground="gray",
                  wraplength=260).grid(row=3, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def _actualizar_nota(event=None):
            etiqueta = self.iso6976_2016_reftemp_var.get()
            for c in REF_TEMPERATURE_ISO6976_2016:
                if c[0] == etiqueta:
                    self.iso6976_2016_nota_var.set(c[6])
                    break
        combo_reftemp.bind("<<ComboboxSelected>>", _actualizar_nota)

        ttk.Button(right_col, text="Calcular (ISO 6976 - 2016)", style="Accento.TButton",
                   command=self.on_calcular_iso6976_2016).pack(fill="x", pady=(10, 0))
        result_frame = ttk.LabelFrame(right_col, text="Resultados (pantalla real, 11 salidas con scroll)", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        claves_2016 = [
            "Molar Mass (g/mol)", "Compressibility (Z)", "Density (kg/m3)",
            "Relative Density", "Sup. Calorific Val. (MJ/m3)",
            "Sup. Calorific Val. (MJ/kg)", "Sup. Calorific Val. (MJ/kmol)",
            "Inf. Calorific Val. (MJ/m3)", "Inf. Calorific Val. (MJ/kg)",
            "Inf. Calorific Val. (MJ/kmol)", "Indice de Wobbe",
        ]
        self.iso6976_2016_result_vars = self._build_result_labels(
            result_frame, claves_2016, {k: k for k in claves_2016})

    def on_calcular_iso6976_2016(self):
        try:
            comp = {n: float(self.iso6976_2016_entries[n].get()) / 100.0
                    for n in ISO6976_COMPONENTES}
            p_ref_valor = float(self.iso6976_2016_pref_var.get())
            p_ref_unidad = self.iso6976_2016_pref_unidad_var.get()
            p_ref = ISO6976_PRESION_A_PA_DICT[p_ref_unidad](p_ref_valor)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        etiqueta = self.iso6976_2016_reftemp_var.get()
        combo = next((c for c in REF_TEMPERATURE_ISO6976_2016 if c[0] == etiqueta), None)
        if combo is None:
            messagebox.showerror("Error", "Combo de Ref. Temperature invalido.")
            return
        _, _rc, indice_bj, t0, indice_hoj, indice_temp_raw_aire, _nota = combo
        try:
            if self.iso6976_2016_mmm_var.get() == "Calculate":
                mmix = iso6976_calcular_masa_molar_metodo_b(comp)
            else:
                mmix = iso6976_calcular_masa_molar(comp)
            z = iso6976_calcular_factor_compresion(comp, indice_temp=indice_bj, p_ref=p_ref, t0=t0)
            vm_ideal = iso6976_calcular_volumen_molar_ideal(t=t0, p=p_ref)
            vm_real = iso6976_calcular_volumen_molar_real(vm_ideal, z)
            densidad_real = (mmix / 1000.0) / vm_real
            densidad_relativa = iso6976_calcular_densidad_relativa(
                mmix, z, indice_temp_raw=indice_temp_raw_aire, p_ref=p_ref)
            hm_bruto = iso6976_calcular_poder_calorifico_molar(
                comp, "bruto", indice_temp_combustion=indice_hoj)
            hm_neto = iso6976_calcular_poder_calorifico_molar(
                comp, "neto", indice_temp_combustion=indice_hoj)
            pcb_volumen = (hm_bruto / vm_real) / 1000.0
            pcn_volumen = (hm_neto / vm_real) / 1000.0
            wobbe = iso6976_calcular_indice_wobbe(pcb_volumen, densidad_relativa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        self.iso6976_2016_result_vars["Molar Mass (g/mol)"].set(f"{mmix:.6f}")
        self.iso6976_2016_result_vars["Compressibility (Z)"].set(f"{z:.6f}")
        self.iso6976_2016_result_vars["Density (kg/m3)"].set(f"{densidad_real:.6f}")
        self.iso6976_2016_result_vars["Relative Density"].set(f"{densidad_relativa:.6f}")
        self.iso6976_2016_result_vars["Sup. Calorific Val. (MJ/m3)"].set(f"{pcb_volumen:.6f}")
        self.iso6976_2016_result_vars["Sup. Calorific Val. (MJ/kg)"].set(f"{hm_bruto / mmix:.6f}")
        self.iso6976_2016_result_vars["Sup. Calorific Val. (MJ/kmol)"].set(f"{hm_bruto:.6f}")
        self.iso6976_2016_result_vars["Inf. Calorific Val. (MJ/m3)"].set(f"{pcn_volumen:.6f}")
        self.iso6976_2016_result_vars["Inf. Calorific Val. (MJ/kg)"].set(f"{hm_neto / mmix:.6f}")
        self.iso6976_2016_result_vars["Inf. Calorific Val. (MJ/kmol)"].set(f"{hm_neto:.6f}")
        self.iso6976_2016_result_vars["Indice de Wobbe"].set(f"{wobbe:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_iso6976_ex1995(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ISO 6976:1995 'ex' (55 componentes) -- Math_ISO6976ex_1995_M. Motor "
                              "binario DISTINTO al de la variante base (calculate_revision_1), SIN "
                              "pantalla propia en la app Android (solo Excel/.xll). PARCIALMENTE "
                              "CERRADA: caso real directo por Frida cubre el motor completo y "
                              "22/55 componentes; los 33 nuevos NUNCA se ejercitaron con valor no-cero.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        ttk.Label(outer, text="El parametro real de esta funcion no es 'Ref. Temperature' (esa "
                              "pantalla no existe para 'ex') sino 'conditions' (0..5), cuyo "
                              "significado fisico exacto (que temperatura en C/F representa cada "
                              "valor) nunca se identifico -- ver normas/ISO_6976_ex_1995.py.",
                  foreground="#b05000", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Formula de Z real: Z = 1 - (suma xj*bj_columna)^2, SIN sqrt y SIN p_ref/T0 -- "
            "confirmado por llamada DIRECTA Frida a calculate_revision_1 (RONDA 3, dif. 0.0000384%).",
            "Densidad real/volumetrica usan Vm_ideal=R*T/p con T=288.15 K y p=101325 Pa fijos -- "
            "estos 2 valores NO estan confirmados para esta funcion en particular (el factor real "
            "que el binario usa en su lugar sigue sin aislar, ver docstring RONDA 2): resultado "
            "de referencia, no validado <0.1% contra ningun caso real.",
            "22/55 componentes CERTAIN (bit-exacto contra ISO_6976.TABLA_CONSTANTES); 33 nuevos "
            "identificados solo por formula quimica (Mj exacto), nunca ejercitados en ejecucion.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 55 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.iso6976_ex1995_entries = self._build_composicion_grid_lista(
            comp_frame, ORDEN_COMPONENTES_EX1995, ejemplo=self.EJEMPLO_AGA5, n_columnas=3,
            combo_guardada=True)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        ttk.Label(cond_frame, text="conditions (0..5)").grid(row=0, column=0, sticky="w", pady=3)
        self.iso6976_ex1995_conditions_var = tk.StringVar(value="0")
        ttk.Combobox(cond_frame, textvariable=self.iso6976_ex1995_conditions_var,
                     values=["0", "1", "2", "3", "4", "5"], state="readonly", width=6).grid(
            row=0, column=1, padx=6, pady=3)
        ttk.Label(cond_frame, text="0 = combo real confirmado por Frida\n(conditions=0, caso "
                                    "'Default'). El resto\nnunca se probo en vivo.",
                  foreground="gray", wraplength=240).grid(row=1, column=0, columnspan=2, sticky="w")

        ttk.Button(right_col, text="Calcular (ISO 6976 - ex 1995)", style="Accento.TButton",
                   command=self.on_calcular_iso6976_ex1995).pack(fill="x", pady=(10, 0))
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        claves_ex1995 = ["Molar Mass (g/mol)", "Compressibility (Z)",
                         "GCV bruto, base molar (kJ/mol)",
                         "Sup. Calorific Val. (MJ/m3, no validado)",
                         "Density (kg/m3, no validado)"]
        self.iso6976_ex1995_result_vars = self._build_result_labels(
            result_frame, claves_ex1995, {k: k for k in claves_ex1995})

    def on_calcular_iso6976_ex1995(self):
        try:
            comp = {n: float(self.iso6976_ex1995_entries[n].get()) / 100.0
                    for n in ORDEN_COMPONENTES_EX1995}
            conditions = int(self.iso6976_ex1995_conditions_var.get())
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        indice_bj = EX1995_CONDITIONS_A_INDICE_BJ[conditions]
        indice_hoj = EX1995_CONDITIONS_A_INDICE_HOJ[conditions]
        try:
            mmix = calcular_masa_molar_ex1995(comp)
            z = calcular_factor_compresion_ex1995(comp, indice_temp=indice_bj)
            hm_bruto = calcular_poder_calorifico_molar_ex1995(
                comp, "bruto", indice_temp_combustion=indice_hoj)
            vm_ideal = calcular_volumen_molar_ideal_ex1995(t=288.15, p=101325.0)
            vm_real = calcular_volumen_molar_real_ex1995(vm_ideal, z)
            pcb_volumen = (hm_bruto / vm_real) / 1000.0
            densidad_real = (mmix / 1000.0) / vm_real
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        self.iso6976_ex1995_result_vars["Molar Mass (g/mol)"].set(f"{mmix:.6f}")
        self.iso6976_ex1995_result_vars["Compressibility (Z)"].set(f"{z:.6f}")
        self.iso6976_ex1995_result_vars["GCV bruto, base molar (kJ/mol)"].set(f"{hm_bruto:.6f}")
        self.iso6976_ex1995_result_vars["Sup. Calorific Val. (MJ/m3, no validado)"].set(f"{pcb_volumen:.6f}")
        self.iso6976_ex1995_result_vars["Density (kg/m3, no validado)"].set(f"{densidad_real:.6f}")

    # ------------------------------------------------------------------ #
    def _build_tab_iso6976_ex2016(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ISO 6976:2016 'ex' (60 componentes) -- Math_ISO6976ex_2016_M. "
                              "Reusa el MISMO motor namespace iso6976_2016 que la variante base "
                              "(confirmado byte a byte) -- PARCIALMENTE CERRADA: caso real "
                              "DIRECTO por Frida (llamada al motor real, no reindexacion en "
                              "Python) cierra BIT-EXACTO para 22/60 componentes; los 38 nuevos "
                              "nunca se ejercitaron con valor no-cero.", wraplength=760).pack(
            anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Mismo selector 'Ref. Temperature' (reference_conditions 1..7) que la variante base "
            "2016_M -- mismo motor, misma tabla de indices bj/T0/aire (ver normas/ISO_6976_ex_2016.py "
            "seccion 5 del docstring, sweep reference_conditions=1..7 con caso real).",
            "El indice de Hoj/combustion NO tiene mapeo por combo confirmado para esta tabla de 60 "
            "(que trae 5 valores de Hoj, no 4) -- se usa fijo el indice 1, el mismo que ya usa "
            "`calcular_poder_calorifico_molar_ex2016` por defecto (mejor cierre encontrado, "
            "dif. 0.0090%), sin variar por combo.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 60 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.iso6976_ex2016_entries = self._build_composicion_grid_lista(
            comp_frame, ORDEN_COMPONENTES_EX2016, ejemplo=self.EJEMPLO_AGA5, n_columnas=3,
            combo_guardada=True)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones de referencia", padding=10)
        cond_frame.pack(fill="x")
        ttk.Label(cond_frame, text="Ref. Temperature").grid(row=0, column=0, sticky="w", pady=3)
        self.iso6976_ex2016_reftemp_var = tk.StringVar(value=REF_TEMPERATURE_ISO6976_2016[0][0])
        combo_reftemp_ex = ttk.Combobox(
            cond_frame, textvariable=self.iso6976_ex2016_reftemp_var,
            values=[c[0] for c in REF_TEMPERATURE_ISO6976_2016], state="readonly", width=18)
        combo_reftemp_ex.grid(row=0, column=1, padx=6, pady=3)
        # [RONDA 50] Selector de unidad agregado (antes campo fijo en Pa,
        # copy-paste incompleto de _build_tab_iso6976_2016 -- ver auditoria de
        # selectores de unidad, 2026-09-14): reusa LITERAL la misma tabla
        # ISO6976_PRESION_A_PA/ISO6976_PRESION_A_PA_DICT ya confirmada en vivo
        # para la pestaña hermana "ISO 6976 (2016)" (mismo parametro fisico
        # p_ref, mismo motor namespace iso6976_2016). No hay pantalla Android
        # propia de "ISO-6976 ex" para re-confirmar en vivo (ver nota
        # [CERTAIN] "No existe pantalla ISO-6976 ex" en
        # normas/ISO_6976_ex_2016.py) -- se agrega por consistencia con la
        # variante base, sin fabricar una confirmacion que no existe.
        ttk.Label(cond_frame, text="Metering ref. pressure").grid(row=1, column=0, sticky="w", pady=3)
        pref_row_ex = ttk.Frame(cond_frame)
        pref_row_ex.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        self.iso6976_ex2016_pref_var = tk.StringVar(value="1013.25")
        ttk.Entry(pref_row_ex, textvariable=self.iso6976_ex2016_pref_var, width=10).pack(side="left")
        self.iso6976_ex2016_pref_unidad_var = tk.StringVar(value="mbar")
        ttk.Combobox(pref_row_ex, textvariable=self.iso6976_ex2016_pref_unidad_var,
                     values=[u for u, _f in ISO6976_PRESION_A_PA], state="readonly",
                     width=11).pack(side="left", padx=(4, 0))
        self.iso6976_ex2016_nota_var = tk.StringVar(value=REF_TEMPERATURE_ISO6976_2016[0][6])
        ttk.Label(cond_frame, textvariable=self.iso6976_ex2016_nota_var, foreground="gray",
                  wraplength=260).grid(row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        def _actualizar_nota_ex(event=None):
            etiqueta = self.iso6976_ex2016_reftemp_var.get()
            for c in REF_TEMPERATURE_ISO6976_2016:
                if c[0] == etiqueta:
                    self.iso6976_ex2016_nota_var.set(c[6])
                    break
        combo_reftemp_ex.bind("<<ComboboxSelected>>", _actualizar_nota_ex)

        ttk.Button(right_col, text="Calcular (ISO 6976 - ex 2016)", style="Accento.TButton",
                   command=self.on_calcular_iso6976_ex2016).pack(fill="x", pady=(10, 0))
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        claves_ex2016 = ["Molar Mass (g/mol)", "Compressibility (Z)", "Density (kg/m3)",
                         "Relative Density", "Sup. Calorific Val. (MJ/m3)", "Indice de Wobbe"]
        self.iso6976_ex2016_result_vars = self._build_result_labels(
            result_frame, claves_ex2016, {k: k for k in claves_ex2016})

    def on_calcular_iso6976_ex2016(self):
        try:
            comp = {n: float(self.iso6976_ex2016_entries[n].get()) / 100.0
                    for n in ORDEN_COMPONENTES_EX2016}
            p_ref_valor = float(self.iso6976_ex2016_pref_var.get())
            p_ref_unidad = self.iso6976_ex2016_pref_unidad_var.get()
            p_ref = ISO6976_PRESION_A_PA_DICT[p_ref_unidad](p_ref_valor)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        etiqueta = self.iso6976_ex2016_reftemp_var.get()
        combo = next((c for c in REF_TEMPERATURE_ISO6976_2016 if c[0] == etiqueta), None)
        if combo is None:
            messagebox.showerror("Error", "Combo de Ref. Temperature invalido.")
            return
        _, _rc, _indice_bj_base, t0, _indice_hoj, indice_temp_raw_aire, _nota = combo
        # NOTA (verificado 2026-08-08, con las 2 opciones probadas a mano contra
        # el caso real): NO se reusa indice_bj del mapeo base (2016_M, calibrado
        # sobre ISO_6976.TABLA_CONSTANTES). El docstring de ISO_6976_ex_2016.py
        # menciona un cierre "bit-exacto" con reference_conditions=1, pero ESE
        # resultado viene de ejecutar el binario real directo via Frida (otro
        # camino de codigo, que resuelve el indice interno el mismo), NO de esta
        # reimplementacion en Python. Probando ambos valores directamente contra
        # el caso real con ESTA formula: indice_bj=1 da Z=0.998244 (dif. 0.0090%);
        # indice_bj=2 (el del mapeo base) da Z=0.998249 (dif. 0.0095%, PEOR). Se
        # mantiene fijo en 1 -- el mejor ajuste empirico confirmado para esta
        # implementacion en particular, sin variar por combo (no hay evidencia de
        # que otro indice sea mejor para otro combo distinto de Default).
        indice_bj = 1
        try:
            mmix = calcular_masa_molar_ex2016(comp)
            z = calcular_factor_compresion_ex2016(comp, indice_temp=indice_bj, p_ref=p_ref, t0=t0)
            vm_ideal = calcular_volumen_molar_ideal_ex2016(t=t0, p=p_ref)
            vm_real = calcular_volumen_molar_real_ex2016(vm_ideal, z)
            densidad_real = (mmix / 1000.0) / vm_real
            densidad_relativa = iso6976_calcular_densidad_relativa(
                mmix, z, indice_temp_raw=indice_temp_raw_aire, p_ref=p_ref)
            hm_bruto = calcular_poder_calorifico_molar_ex2016(comp)
            pcb_volumen = (hm_bruto / vm_real) / 1000.0
            wobbe = iso6976_calcular_indice_wobbe(pcb_volumen, densidad_relativa)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        self.iso6976_ex2016_result_vars["Molar Mass (g/mol)"].set(f"{mmix:.6f}")
        self.iso6976_ex2016_result_vars["Compressibility (Z)"].set(f"{z:.6f}")
        self.iso6976_ex2016_result_vars["Density (kg/m3)"].set(f"{densidad_real:.6f}")
        self.iso6976_ex2016_result_vars["Relative Density"].set(f"{densidad_relativa:.6f}")
        self.iso6976_ex2016_result_vars["Sup. Calorific Val. (MJ/m3)"].set(f"{pcb_volumen:.6f}")
        self.iso6976_ex2016_result_vars["Indice de Wobbe"].set(f"{wobbe:.6f}")

    def _build_result_labels(self, parent, keys, etiquetas):
        result_vars = {}
        for i, key in enumerate(keys):
            ttk.Label(parent, text=etiquetas[key], wraplength=220).grid(
                row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar(value="-")
            ttk.Label(parent, textvariable=var, font=("Consolas", 10, "bold")).grid(
                row=i, column=1, sticky="e", padx=6)
            result_vars[key] = var
        return result_vars

    # ------------------------------------------------------------------ #
    # Fila Entry+Combobox para un campo de Presion de la familia API, MISMO
    # patron ya usado para Temperature (`temp_tabla`/Combobox) -- ver
    # comentario de API_PRESION_GAUGE_A_BARG/_PSIG/API_PRESION_ABS_A_BARA/
    # _PSIA (RONDA 39, confirmado en vivo) mas arriba en el archivo.
    # ------------------------------------------------------------------ #
    def _agregar_fila_presion(self, parent, row, tabla, valor_default=0.0,
                               unidad_default=None, width=10, columnspan_label=1):
        unidad_default = unidad_default or tabla[0][0]
        row_frame = ttk.Frame(parent)
        row_frame.grid(row=row, column=1, padx=6, pady=3, sticky="w")
        valor_var = tk.StringVar(value=str(valor_default))
        ttk.Entry(row_frame, textvariable=valor_var, width=width).pack(side="left")
        unidad_var = tk.StringVar(value=unidad_default)
        ttk.Combobox(row_frame, textvariable=unidad_var, values=[u for u, _f in tabla],
                     state="readonly", width=12).pack(side="left", padx=(4, 0))
        return valor_var, unidad_var, dict(tabla)

    # ------------------------------------------------------------------ #
    def _build_tab_gasviscosity2004(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GasViscosity_2004 -- viscosidad dinamica del gas natural segun "
                              "P.Schley, M.Jaeschke, C.Kuechenmeister, E.Vogel (2004), 'Viscosity "
                              "Measurements and Predictions for Natural Gas'. Motor propio de "
                              "FlowXpert (namespace spirit::math::gas_viscosity_2004), CERRADO.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
                "Formula = mezcla de Wilke (1950) para el limite de densidad cero + termino "
                "residual tipo Jossi-Stiel-Thodos (coeficientes propios de Schley et al., no los "
                "clasicos de JST 1966). Estructura y las ~100 constantes (12 componentes x 8 "
                "valores + 4 coeficientes residuales + constantes estructurales) confirmadas "
                "BYTE A BYTE contra .xll y .so, compilados por separado (Fase 6). Ver "
                "normas/GasViscosity_2004.py.",
                "3 casos reales (composicion 'Default', T=0/rho=0, T=20/rho=0, T=20/rho=80) "
                "validados contra la app Android en vivo, coincidencia exacta al redondeo de "
                "pantalla (6 decimales) en los 3.",
                "El motor interno solo usa 12 de los 22 componentes AGA8, pero la reduccion "
                "COMPLETA de los 22 a esos 12 es [CERTAIN], fuente: manual oficial ABB SpiritIT "
                "('Flow-X Manual IIIb - Function Reference', pag. 83): solo Agua/H2S/CO se "
                "descartan; Hidrogeno->Metano, Oxigeno/Helio/Argon->Nitrogeno, "
                "n-Nonano/n-Decano->n-Octano y neo-Pentano->i-Pentano. Esta grilla ya carga los "
                "22 y aplica esa reduccion oficial antes de calcular (ver "
                "`reducir_22_a_12()`/`calcular_viscosidad_desde_22()`).",
                "Rango de validez fisica OFICIAL del metodo publicado (misma fuente): 250 K a "
                "450 K (-24 a +177 degC), presion hasta 30 MPa (300 bar). Incertidumbre estimada: "
                "0.5% para gas natural tipico, 0.3% para metano puro. Es DISTINTO del rango "
                "generico de entrada de la UI (density 0..2000 kg/m3, temperature -200..400 "
                "degC), que es solo un limite de campo, no de validez fisica.",
                "'temperature' es en grados Celsius, CONFIRMADO EXPLICITO por la UI real de la app "
                "('degree celsius' bajo el simbolo °C) -- no inferido.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composicion molar (%, 22 componentes)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        self.gasvisc_entries = self._build_composicion_grid_lista(
            comp_frame, ISO6976_COMPONENTES, ejemplo=self.EJEMPLO_AGA5, n_columnas=2,
            combo_guardada=True)
        ttk.Label(comp_frame, text="Solo 12 de estos 22 alimentan el motor real (los otros 10 se "
                                    "redistribuyen segun la tabla oficial, ver panel de arriba;\n"
                                    "solo Agua/H2S/CO se descartan por completo).",
                  foreground="gray", wraplength=380).grid(
            row=(len(ISO6976_COMPONENTES) + 1) // 2 + 2, column=0, columnspan=4,
            sticky="w", pady=(4, 0))

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        cond_frame = ttk.LabelFrame(right_col, text="Condiciones", padding=10)
        cond_frame.pack(fill="x")
        ttk.Label(cond_frame, text="Density").grid(row=0, column=0, sticky="w", pady=3)
        density_row = ttk.Frame(cond_frame)
        density_row.grid(row=0, column=1, padx=6, pady=3, sticky="w")
        self.gasvisc_density_var = tk.StringVar(value="0.0")
        ttk.Entry(density_row, textvariable=self.gasvisc_density_var, width=10).pack(side="left")
        self.gasvisc_density_unidad_var = tk.StringVar(value="kg/m3")
        ttk.Combobox(density_row, textvariable=self.gasvisc_density_unidad_var,
                     values=[u for u, _f in GASVISC2004_DENSIDAD_A_KGM3], state="readonly",
                     width=8).pack(side="left", padx=(4, 0))
        ttk.Label(cond_frame, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temperature_row = ttk.Frame(cond_frame)
        temperature_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        self.gasvisc_temperature_var = tk.StringVar(value="20.0")
        ttk.Entry(temperature_row, textvariable=self.gasvisc_temperature_var, width=10).pack(
            side="left")
        self.gasvisc_temperature_unidad_var = tk.StringVar(value="degC")
        ttk.Combobox(temperature_row, textvariable=self.gasvisc_temperature_unidad_var,
                     values=[u for u, _f in GASVISC2004_TEMPERATURA_A_DEGC], state="readonly",
                     width=8).pack(side="left", padx=(4, 0))
        ttk.Label(cond_frame, text="Rango UI declarado: density 0..2000 kg/m3,\n"
                                    "temperature -200..400 degC (limite generico de\n"
                                    "UI, no el rango de validez fisica del ajuste).\n"
                                    "El selector de unidad de cada campo SOLO convierte\n"
                                    "lo mostrado/ingresado -- confirmado tocando la app\n"
                                    "real (uiautomator, 2026-08-19); el calculo interno\n"
                                    "sigue siempre en kg/m3 y grados Celsius.\n"
                                    "Rango de validez FISICA oficial (manual ABB SpiritIT):\n"
                                    "250..450 K (-24..+177 degC), presion hasta 30 MPa.",
                  foreground="gray", wraplength=230).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))
        self.gasvisc_rango_var = tk.StringVar(value="")
        ttk.Label(cond_frame, textvariable=self.gasvisc_rango_var,
                  foreground="#b05000", wraplength=230).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Button(right_col, text="Calcular (GasViscosity_2004)", style="Accento.TButton",
                   command=self.on_calcular_gasviscosity2004).pack(fill="x", pady=(10, 0))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x", pady=(10, 0))
        self.gasvisc_result_vars = self._build_result_labels(
            result_frame, ["viscosity"], {"viscosity": "Dynamic viscosity [Pa.s]"})

    def on_calcular_gasviscosity2004(self):
        try:
            composicion_22 = {n: float(self.gasvisc_entries[n].get()) for n in ISO6976_COMPONENTES}
            densidad_valor = float(self.gasvisc_density_var.get())
            densidad_unidad = self.gasvisc_density_unidad_var.get()
            densidad = dict(GASVISC2004_DENSIDAD_A_KGM3)[densidad_unidad](densidad_valor)
            temperatura_valor = float(self.gasvisc_temperature_var.get())
            temperatura_unidad = self.gasvisc_temperature_unidad_var.get()
            temperatura = dict(GASVISC2004_TEMPERATURA_A_DEGC)[temperatura_unidad](temperatura_valor)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            eta = gasvisc_calcular_viscosidad_desde_22(composicion_22, temperatura, densidad)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        self.gasvisc_result_vars["viscosity"].set(f"{eta:.6f}")
        # Advertencia informativa (NO bloqueante) si T/densidad quedan fuera del
        # rango de validez fisica OFICIAL del metodo (manual ABB SpiritIT):
        # 250-450 K (-23.15 a +176.85 degC), presion asociada hasta 30 MPa (no
        # se valida presion aca porque esta pestaña no pide presion, solo
        # density/temperature).
        temperatura_k = temperatura + 273.15
        if not (250.0 <= temperatura_k <= 450.0):
            self.gasvisc_rango_var.set(
                f"Aviso: temperature ({temperatura:.2f} degC = {temperatura_k:.2f} K) esta fuera "
                f"del rango de validez fisica OFICIAL del metodo (250..450 K). El resultado se "
                f"calcula igual, pero fuera de este rango la incertidumbre declarada por el "
                f"manual (0.3-0.5%) puede no aplicar.")
        else:
            self.gasvisc_rango_var.set("")

    # ------------------------------------------------------------------ #
    # API MPMS Tables (API-2540 / ASTM D1250), 1980 y 2004 -- 14 pestañas,
    # UNA por tabla (regla del proyecto: nunca consolidar varias normas/
    # tablas en una sola pestaña aunque compartan motor). Todas comparten un
    # unico helper de layout `_build_tab_api_mpms` + un unico handler
    # `_on_calcular_api_mpms` (factorizacion de CODIGO, no de PESTAÑA -- cada
    # tabla sigue siendo su propio tab visible con su propio estado). Cubre
    # las 6 de 1980 (US+metrico), las 6 de 2004 sistema US y las 4 metricas
    # de 2004 (Table53/54 a 15°C, Table59/60 a 20°C -- RONDA 11: Table59/60
    # NO tienen tabla K0/K1/K2 propia, comparten K_US con Table53/54 y solo
    # cambia la referencia de temperatura, confirmado por decompilacion
    # cruzada .xll+.so, ver normas/API_MPMS_Tables_1980_2004.py).
    # ------------------------------------------------------------------ #
    def _build_tab_api_mpms(self, parent, state_key, descripcion, ayuda_items,
                             input_label, input_default, funcion, input_kwarg,
                             temp_tabla, temp_native, temp_default,
                             salida_principal_clave, salida_principal_label,
                             alpha_convertir_a_c, boton_texto, tiene_presion=False,
                             tiene_hidrometro=False, presion_kwarg="pressure_psig",
                             tipo_rounding=None, rounding_kwarg="rounding",
                             auto_select_disponible=False):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", ayuda_items,
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)

        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(
            row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(
            row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value=str(temp_default))
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value=temp_native)
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in temp_tabla], state="readonly",
                     width=7).pack(side="left", padx=(4, 0))

        fila = 2
        presion_valor_var = None
        presion_unidad_var = None
        presion_tabla_dict = None
        if tiene_presion:
            ttk.Label(izq, text="Pressure").grid(row=fila, column=0, sticky="w", pady=3)
            presion_tabla = (API_PRESION_GAUGE_A_PSIG if presion_kwarg == "pressure_psig"
                              else API_PRESION_GAUGE_A_BARG)
            presion_valor_var, presion_unidad_var, presion_tabla_dict = (
                self._agregar_fila_presion(izq, fila, presion_tabla, valor_default=0.0))
            fila += 1

        hidrometro_var = None
        if tiene_hidrometro:
            hidrometro_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(izq, text="Hydrometer Corr. (confirmado, ver panel de arriba)",
                            variable=hidrometro_var).grid(
                row=fila, column=0, columnspan=2, sticky="w", pady=3)
            fila += 1

        rounding_var = None
        rounding_enum_var = None
        if tipo_rounding == "bool":
            rounding_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(izq, text="API Rounding (ver panel de arriba)",
                            variable=rounding_var).grid(
                row=fila, column=0, columnspan=2, sticky="w", pady=3)
            fila += 1
        elif tipo_rounding == "enum":
            ttk.Label(izq, text="API Rounding").grid(row=fila, column=0, sticky="w", pady=3)
            rounding_enum_var = tk.StringVar(value=API_ROUNDING_ENUM_OPCIONES[0][0])
            ttk.Combobox(izq, textvariable=rounding_enum_var,
                         values=[o[0] for o in API_ROUNDING_ENUM_OPCIONES],
                         state="readonly", width=24).grid(row=fila, column=1, padx=6, pady=3)
            fila += 1

        ttk.Label(izq, text="Product").grid(row=fila, column=0, sticky="w", pady=3)
        producto_var = tk.StringVar(value=API_PRODUCTOS[0][0])
        ttk.Combobox(izq, textvariable=producto_var, values=[p[0] for p in API_PRODUCTOS],
                     state="readonly", width=16).grid(row=fila, column=1, padx=6, pady=3)
        if auto_select_disponible:
            ttk.Label(izq, text="\"Refined, auto\" (RONDA 44): selecciona automaticamente "
                                "Gasoline/Transition/Jet/FuelOil segun la densidad (breakpoints "
                                "del motor real, confirmados por decompilacion y validados "
                                "contra el oraculo .xll). El producto realmente elegido se "
                                "muestra abajo en \"Product (selected)\".",
                        foreground="gray", wraplength=220).grid(
                row=fila + 1, column=0, columnspan=2, sticky="w", pady=(4, 0))
        else:
            ttk.Label(izq, text="\"Refined, auto\" no esta implementado en el motor de "
                                "referencia (breakpoints de auto-seleccion no confirmados) -- "
                                "de elegirlo, el calculo mostrara un error explicito en vez de "
                                "un numero fabricado.", foreground="gray", wraplength=220).grid(
                row=fila + 1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_api_mpms(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = []
        etiquetas_resultado = {}
        if salida_principal_clave:
            claves_resultado.append("principal")
            etiquetas_resultado["principal"] = salida_principal_label
        claves_resultado.append("ctl")
        etiquetas_resultado["ctl"] = "CTL, Correction for Temperature on Liquid [adimensional]"
        if tiene_presion:
            claves_resultado += ["cpl", "ctpl", "f"]
            etiquetas_resultado["cpl"] = "CPL, Correction for Pressure on Liquid [adimensional]"
            etiquetas_resultado["ctpl"] = "CTPL = CTL x CPL [adimensional]"
            etiquetas_resultado["f"] = ("Factor de Compresibilidad F [1/bar]"
                                        if presion_kwarg == "pressure_bar"
                                        else "Factor de Compresibilidad F [1/psi]")
        claves_resultado.append("alpha")
        etiquetas_resultado["alpha"] = "Alpha, Coeficiente de Expansion Termica [1/gradoC]"
        claves_resultado += ["k0", "k1", "k2"]
        etiquetas_resultado["k0"] = "K0 (constante de tabla, segun Product) [adimensional]"
        etiquetas_resultado["k1"] = "K1 (constante de tabla, segun Product) [adimensional]"
        etiquetas_resultado["k2"] = "K2 (constante de tabla, segun Product; 0 si no aplica) [adimensional]"
        if auto_select_disponible:
            claves_resultado.append("product_efectivo")
            etiquetas_resultado["product_efectivo"] = (
                "Product (selected) -- producto realmente usado cuando Product=\"Refined, "
                "auto\" (1=Crude/3=Gasoline/4=Transition/5=Jet/6=FuelOil/7=Lube)")

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api_mpms_tabs[state_key] = {
            "valor_input_var": valor_input_var,
            "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var,
            "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(temp_tabla),
            "temp_kwarg": "observed_temp_f" if temp_native == "degF" else "observed_temp_c",
            "presion_valor_var": presion_valor_var,
            "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict,
            "presion_kwarg": presion_kwarg,
            "producto_var": producto_var,
            "result_vars": result_vars,
            "funcion": funcion,
            "salida_principal_clave": salida_principal_clave,
            "alpha_convertir_a_c": alpha_convertir_a_c,
            "tiene_presion": tiene_presion,
            "tiene_hidrometro": tiene_hidrometro,
            "hidrometro_var": hidrometro_var,
            "tipo_rounding": tipo_rounding,
            "rounding_var": rounding_var,
            "rounding_enum_var": rounding_enum_var,
            "rounding_kwarg": rounding_kwarg,
            "auto_select_disponible": auto_select_disponible,
        }

    def _on_calcular_api_mpms(self, state_key):
        st = self._api_mpms_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_convertida = st["temp_tabla_dict"][temp_unidad](temp_valor)
            if st["tiene_presion"]:
                presion_unidad = st["presion_unidad_var"].get()
                presion = st["presion_tabla_dict"][presion_unidad](
                    float(st["presion_valor_var"].get()))
            else:
                presion = None
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        producto = dict(API_PRODUCTOS)[st["producto_var"].get()]
        kwargs = {
            st["input_kwarg"]: valor_input,
            st["temp_kwarg"]: temp_convertida,
            "product": producto,
        }
        if st["tiene_presion"]:
            kwargs[st["presion_kwarg"]] = presion
        if st["tiene_hidrometro"]:
            kwargs["hydrometer_correction"] = bool(st["hidrometro_var"].get())
        if st["tipo_rounding"] == "bool":
            kwargs[st["rounding_kwarg"]] = bool(st["rounding_var"].get())
        elif st["tipo_rounding"] == "enum":
            etiqueta = st["rounding_enum_var"].get()
            kwargs[st["rounding_kwarg"]] = dict(API_ROUNDING_ENUM_OPCIONES)[etiqueta]
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        if st["salida_principal_clave"]:
            result_vars["principal"].set(f"{r[st['salida_principal_clave']]:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.6f}")
        if st["tiene_presion"]:
            result_vars["cpl"].set(f"{r['cpl']:.6f}")
            result_vars["ctpl"].set(f"{r['ctpl']:.6f}")
            result_vars["f"].set(f"{r['f']:.9f}")
        alpha = r["alpha"]
        if st["alpha_convertir_a_c"]:
            alpha = alpha * 1.8
        result_vars["alpha"].set(f"{alpha:.6f}")
        result_vars["k0"].set(f"{r['k0']:.4f}")
        result_vars["k1"].set(f"{r['k1']:.6f}")
        result_vars["k2"].set(f"{r['k2']:.6f}")
        if st.get("auto_select_disponible") and "product_efectivo" in result_vars:
            result_vars["product_efectivo"].set(str(r.get("product_efectivo", "-")))

    _AYUDA_API_1980_COMUN = [
        "Motor API MPMS 11.1 / API-2540 / ASTM D1250 Adjunct, edicion 1980/1984. "
        "Formula VCF/CTL clasica: alpha=(K0+K1*rho+K2*rho^2)/rho^2, x=alpha*(T-T_ref), "
        "CTL=exp(-(x+0.8*x^2)) -- CTL (Correction for Temperature on Liquid) es el "
        "factor que ajusta un volumen medido a la temperatura de referencia (60°F/15°C).",
        "'API Gravity'/'RD'/'Density' de entrada: sin selector de unidad (confirmado "
        "contra la pantalla real). 'Product': 7 opciones reales (Crude, Gasoline, Jet "
        "fuel, etc., cada una con su propia tabla de constantes K0/K1/K2). "
        "'Temperature': selector K/degC/degF/R.",
        "El campo Alpha (coeficiente de expansion termica) se calcula internamente en "
        "1/gradoF (sistema US) o 1/gradoC (metrico) segun corresponda, pero esta "
        "pestaña siempre lo muestra en 1/gradoC, igual que la app real.",
        "'Hydrometer correction': corrige la lectura de un hidrometro real (que tiene "
        "su propio error de escala/graduacion) antes de calcular el CTL. Disponible en "
        "Table-5, Table-23 (US) y Table-53 (metrico); no aplica en Table-6/24/54 "
        "porque esas tablas no reciben una lectura observada que corregir.",
        "'API Rounding': en Table-5/23/53 es un simple On/Off que redondea el "
        "resultado principal a 1 decimal (cambia el numero devuelto por el motor, no "
        "solo el formato de pantalla). En Table-6/24/54 es un selector de 4 opciones, "
        "donde solo 'Enabled (table values)' redondea el CTL a 4 decimales.",
        "Validado con 9 casos reales (Table-5/6, Crude/Gasoline/Lub oil) contra la "
        "app Android: API Gravity a 60°F y CTL coinciden con error menor a 0.0001%.",
    ]

    _AYUDA_API_2004_COMUN = [
        "Motor API MPMS 11.1 / API-2540 / ASTM D1250, edicion 2004, sistema US.",
        "Ademas del CTL clasico (misma formula que 1980), la edicion 2004 agrega el "
        "factor de compresibilidad F del liquido y CPL (Correction for Pressure on "
        "Liquid): CPL=1/(1-P*F), CTPL=CTL*CPL -- CTPL es el factor combinado que "
        "ajusta el volumen medido tanto por temperatura como por presion. La "
        "temperatura de referencia real que usa el motor es 60.0068749°F (no 60.0° "
        "exacto).",
        "Validado con casos reales de la app (Table5/6_2004, US, con presion "
        "variada): error menor a 0.004%. 'API Gravity'/'RD' de entrada: sin selector "
        "de unidad. 'Product': mismas 7 opciones que 1980. 'Temperature': selector "
        "K/degC/degF/R. 'Pressure': selector real de 11 unidades (bar(g)/mbar(g)/ "
        "mmHgg/mmH2Og/inHgg/inH2Og, confirmado tocando la pantalla real -- psig NO "
        "es una opcion, aunque el motor interno trabaje nativamente en psig).",
        "PENDIENTE, no fabricado: la app real muestra un residuo de ~0.00068% en el "
        "CTL de Table-6 (2004) que viene de una micro-correccion adicional de "
        "temperatura no reproducida aqui (informacion insuficiente para "
        "reconstruirla sin inventar coeficientes). Residuo pequeño y documentado, no "
        "bloqueante para uso normal.",
    ]

    _AYUDA_API_2004_METRICO_COMUN = [
        "Motor API MPMS 11.1 / API-2540, edicion 2004, sistema metrico (Table-53/54). "
        "Validado con casos reales de la app: error menor a 0.004%.",
        "Internamente usa el mismo nucleo de calculo que Table-5/23 (2004, referencia "
        "60.0068749°F) y agrega una segunda evaluacion a 15°C para expresar el "
        "resultado en la referencia metrica -- 'density_15c' es ese resultado final.",
        "Esta pestaña muestra los 3 campos CTL/CPL/CTPL por separado (verificados "
        "exactos contra la app real): CTL y CTPL son distintos incluso con Presion=0, "
        "asi que conviene revisar los 3 y no asumir que son iguales.",
        "'Density' de entrada: sin selector de unidad, siempre kg/m3. 'Pressure': "
        "selector real de 11 unidades gauge (bar(g)/mbar(g)/mmHgg/mmH2Og/inHgg/"
        "inH2Og), confirmado tocando la pantalla real (RONDA 39).",
    ]

    _AYUDA_API_2004_TABLE5960_COMUN = [
        "Motor API MPMS 11.1 / API-2540, edicion 2004, sistema metrico, referencia "
        "20°C (Table-59/60).",
        "Table-59/60 (2004) usan, en la practica, la MISMA formula y las mismas "
        "constantes K0/K1/K2 que Table-53/54 (2004) -- la unica diferencia real es la "
        "temperatura de referencia (20°C en vez de 15°C). Por eso esta pestaña no "
        "tiene una tabla de constantes propia: reusa la de Table-53/54, seleccionada "
        "por 'Product' de la misma forma.",
        "'Density' de entrada: sin selector de unidad, siempre kg/m3. 'Pressure': "
        "selector real de 11 unidades gauge (bar(g)/mbar(g)/mmHgg/mmH2Og/inHgg/"
        "inH2Og), confirmado tocando la pantalla real (RONDA 39).",
        "Validado por comparacion cruzada entre 2 implementaciones independientes del "
        "motor real (Windows y Android); sin un caso propio capturado en pantalla "
        "para esta tabla en particular (Table-53/54, que comparten la misma formula, "
        "si tienen ese caso).",
    ]

    def _build_tab_api_table5_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table5_1980",
            descripcion="API Table-5 (1980/1984) -- API MPMS 11.1 Tables 5A/5B/5D. Convierte "
                        "API Gravity OBSERVADA (a una temperatura T) a API Gravity a 60°F "
                        "(iterativo, direccion observado->base).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="Observed API Gravity [°API]", input_default=30.0,
            funcion=api_table5_1980, input_kwarg="observed_api",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave="api_60f", salida_principal_label="API Gravity a 60°F [°API]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-5, 1980)",
            tiene_hidrometro=True, tipo_rounding="bool", auto_select_disponible=True)

    def _build_tab_api_table6_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table6_1980",
            descripcion="API Table-6 (1980/1984) -- API MPMS 11.1 Tables 6A/6B/6D. Convierte "
                        "API Gravity a 60°F en el factor CTL a una temperatura observada T "
                        "(directo, sin iteracion).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="API Gravity @ 60°F [°API]", input_default=30.0,
            funcion=api_table6_1980, input_kwarg="api_60f",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-6, 1980)",
            tipo_rounding="enum", auto_select_disponible=True)

    def _build_tab_api_table23_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table23_1980",
            descripcion="API Table-23 (1980/1984) -- API MPMS 11.1 Tables 23A/23B. Variante en "
                        "Densidad Relativa (RD) directa de Table-5 (sin pasar por API Gravity): "
                        "RD observada (a T) -> RD a 60°F (iterativo).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="Observed Relative Density (RD) [adimensional]", input_default=0.85,
            funcion=api_table23_1980, input_kwarg="observed_rd",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave="rd_60f", salida_principal_label="Relative Density a 60°F [adimensional]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-23, 1980)",
            tiene_hidrometro=True, tipo_rounding="bool", auto_select_disponible=True)

    def _build_tab_api_table24_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table24_1980",
            descripcion="API Table-24 (1980/1984) -- API MPMS 11.1 Tables 24A/24B(/24D). "
                        "Variante RD directa de Table-6: RD a 60°F -> CTL a T observada "
                        "(directo, sin iteracion).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="Relative Density (RD) @ 60°F [adimensional]", input_default=0.85,
            funcion=api_table24_1980, input_kwarg="rd_60f",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-24, 1980)",
            tipo_rounding="enum", auto_select_disponible=True)

    def _build_tab_api_table53_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table53_1980",
            descripcion="API Table-53 (1980/1984) -- API MPMS 11.1 Tables 53A/53B/53D "
                        "(metrico). Densidad OBSERVADA (a T) -> densidad a 15°C (iterativo, "
                        "mismo motor de Table-5, constantes metricas).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="Observed Density [kg/m3]", input_default=850.0,
            funcion=api_table53_1980, input_kwarg="observed_density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=32.0,
            salida_principal_clave="density_15c", salida_principal_label="Density a 15°C [kg/m3]",
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-53, 1980)",
            tiene_hidrometro=True, tipo_rounding="bool", auto_select_disponible=True)

    def _build_tab_api_table54_1980(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table54_1980",
            descripcion="API Table-54 (1980/1984) -- API MPMS 11.1 Tables 54A/54B/54D "
                        "(metrico). Densidad a 15°C -> CTL a T observada (directo, sin "
                        "iteracion, mismo motor de Table-6, constantes metricas).",
            ayuda_items=self._AYUDA_API_1980_COMUN,
            input_label="Density @ 15°C [kg/m3]", input_default=850.0,
            funcion=api_table54_1980, input_kwarg="density_15c_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=32.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-54, 1980)",
            tipo_rounding="enum", auto_select_disponible=True)

    def _build_tab_api_table5_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table5_2004",
            descripcion="API Table-5 (2004) -- API MPMS 11.1 Tables 5A/5B/5D, edicion 2004 "
                        "(sistema US). API Gravity observada (a T, P) -> API Gravity a 60°F, "
                        "0 psig (iterativo, <=15 iteraciones, incluye CPL/factor de "
                        "compresibilidad F).",
            ayuda_items=self._AYUDA_API_2004_COMUN,
            input_label="Observed API Gravity [°API]", input_default=30.0,
            funcion=api_table5_2004, input_kwarg="observed_api",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave="api_60f_0psig",
            salida_principal_label="API Gravity a 60°F, 0 psig [°API]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-5, 2004)",
            tiene_presion=True, tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api_table6_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table6_2004",
            descripcion="API Table-6 (2004) -- API MPMS 11.1 Tables 6A/6B/6D, edicion 2004 "
                        "(sistema US). API Gravity a 60°F -> CTPL (CTL x CPL) a T, P "
                        "observadas (directo, sin iteracion).",
            ayuda_items=self._AYUDA_API_2004_COMUN,
            input_label="API Gravity @ 60°F [°API]", input_default=30.0,
            funcion=api_table6_2004, input_kwarg="api_60f",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-6, 2004)",
            tiene_presion=True, tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api_table23_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table23_2004",
            descripcion="API Table-23 (2004) -- API MPMS 11.1 Tables 23A/23B, edicion 2004 "
                        "(sistema US). Variante RD directa de Table-5 (2004): RD observada "
                        "(a T, P) -> RD a 60°F, 0 psig (iterativo).",
            ayuda_items=self._AYUDA_API_2004_COMUN,
            input_label="Observed Relative Density (RD) [adimensional]", input_default=0.85,
            funcion=api_table23_2004, input_kwarg="observed_rd",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave="rd_60f_0psig",
            salida_principal_label="Relative Density a 60°F, 0 psig [adimensional]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-23, 2004)",
            tiene_presion=True, tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api_table24_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table24_2004",
            descripcion="API Table-24 (2004) -- API MPMS 11.1 Tables 24A/24B, edicion 2004 "
                        "(sistema US). Variante RD directa de Table-6 (2004): RD a 60°F -> "
                        "CTPL a T, P observadas (directo, sin iteracion).",
            ayuda_items=self._AYUDA_API_2004_COMUN,
            input_label="Relative Density (RD) @ 60°F [adimensional]", input_default=0.85,
            funcion=api_table24_2004, input_kwarg="rd_60f",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=True, boton_texto="Calcular (API Table-24, 2004)",
            tiene_presion=True, tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api_table53_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table53_2004",
            descripcion="API Table-53 (2004) -- API MPMS 11.1 Tables 53A/53B/53D, edicion "
                        "2004 (metrico). Densidad OBSERVADA (a T, P) -> densidad a 15°C, 0 "
                        "bar(g) (iterativo, <=15 iteraciones, incluye CPL/factor de "
                        "compresibilidad F).",
            ayuda_items=self._AYUDA_API_2004_METRICO_COMUN,
            input_label="Observed Density [kg/m3]", input_default=850.0,
            funcion=api_table53_2004, input_kwarg="observed_density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=20.0,
            salida_principal_clave="density_15c", salida_principal_label="Density a 15°C, 0 bar(g) [kg/m3]",
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-53, 2004)",
            tiene_presion=True, presion_kwarg="pressure_bar",
            tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api_table54_2004(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table54_2004",
            descripcion="API Table-54 (2004) -- API MPMS 11.1 Tables 54A/54B/54D, edicion "
                        "2004 (metrico). Densidad a 15°C -> CTPL a T, P observadas (requiere "
                        "una iteracion previa para invertir la entrada, luego evaluacion "
                        "directa).",
            ayuda_items=self._AYUDA_API_2004_METRICO_COMUN,
            input_label="Density @ 15°C [kg/m3]", input_default=850.0,
            funcion=api_table54_2004, input_kwarg="density_15c_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=20.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-54, 2004)",
            tiene_presion=True, presion_kwarg="pressure_bar",
            tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    # ------------------------------------------------------------------ #
    # Placeholders de la familia API 11.1 -- funciones reales confirmadas
    # contra la app (uiautomator, emulador flowxpert_rd, 2026-08-25) y contra
    # el manual oficial "Flow-X Manual IIIb - Function Reference" (capitulo
    # "2 API MPMS Tables"), que hoy NO tienen calculo implementado en este
    # proyecto. Mismo patron honesto que _build_tab_aga7/_build_tab_aga9: se
    # explica el motivo real, sin fabricar un resultado.
    # ------------------------------------------------------------------ #
    def _build_tab_api_placeholder(self, parent, titulo, io_texto, motivo_lineas, fuente_lineas):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=titulo, font=("Segoe UI", 10, "bold"), foreground="#1F497D",
                  wraplength=760).pack(anchor="w", pady=(4, 2))
        if io_texto:
            ttk.Label(outer, text=io_texto, wraplength=760).pack(anchor="w", pady=(0, 6))
        ttk.Label(outer, text="No implementado en esta interfaz.", foreground="#b05000",
                  font=("Segoe UI", 10, "bold"), wraplength=760).pack(anchor="w", pady=(6, 4))
        for linea in motivo_lineas:
            ttk.Label(outer, text="• " + linea, wraplength=760, justify="left").pack(
                anchor="w", pady=(0, 4))
        PanelAyudaColapsable(outer, "Fuente y alcance de la confirmacion", fuente_lineas,
                             wraplength=740).pack(fill="x", pady=(10, 0))

    _FUENTE_API_MENU_COMUN = [
        "Pantalla confirmada en la app real FlowXpert (emulador flowxpert_rd, "
        "com.spiritit.flowxpert), navegando API > \"API 11.1 (1952/1980/2004)\" y "
        "leyendo la lista con uiautomator -- el nombre de esta pestaña es literal, "
        "no traducido.",
        "Descripcion y formulas segun el manual oficial \"Flow-X Manual IIIb - "
        "Function Reference\" (CM/FLOWX/FR-EN), capitulo \"2 API MPMS Tables\".",
    ]

    # RONDA 10: Table53/54 (1952, metrico) y su wrapper Density@15C se
    # CERRARON -- la tabla real de interpolacion embebida en el `.xll`
    # (`&DAT_18028a680`) se decodifico dumpeando bytes crudos con `pefile`
    # (ver docstring de RONDA 10 en normas/API_MPMS_Tables_1980_2004.py) y
    # se valido contra el caso real del usuario (<0.00005% de error en las
    # 3 salidas: density_15c/ctl/cpl). Table5/6/23/24 (1952, sistema US)
    # usan tablas DISTINTAS (direcciones y cantidad de segmentos distintas,
    # localizadas pero NO decodificadas esta ronda) -- siguen bloqueadas,
    # ver el placeholder actualizado mas abajo.
    _AYUDA_API1952_METRICO_COMUN = [
        "Tabla real de interpolacion CTL (API 1952, Table 53/54, sistema "
        "metrico): no es una formula analitica, son los valores reales de la "
        "tabla impresa del manual, interpolados en 2 ejes (temperatura en "
        "pasos de 0.5°C, densidad en pasos de 5 kg/m3).",
        "ADVERTENCIA REAL (hallazgo del proyecto, no oculto): la tabla interna "
        "que usa el motor real para la pantalla 'API Table-53 (1952)' de la "
        "app es DISTINTA de la que usa 'API Density @15°C (1952)' (aunque "
        "ambas se llaman parecido). Esta pestaña esta validada contra el caso "
        "real de 'API Density @15°C (1952)', no contra una prueba aislada de "
        "'API Table-53 (1952)' -- tener ese matiz en cuenta si se compara "
        "directo contra esa otra pantalla.",
        "Validado contra un caso real completo (Density observada=1000 kg/m3, "
        "T=25°C, P=20 bar(g), EVP=0): density_15c=1005.4817 (real 1005.482), "
        "ctl=0.9935096 (real 0.993510), cpl=1.0010454 (real 1.001045) -- las "
        "3 salidas dentro de ~0.00004% del valor real de la app.",
        "'Density' de entrada: sin selector de unidad, siempre kg/m3 (mismo "
        "criterio que el resto de la familia 1980/2004).",
    ]

    def _build_tab_api1952_ctl_tabla(self, parent, state_key, descripcion,
                                      input_label, input_default, funcion, input_kwarg,
                                      salida_principal_clave, salida_principal_label,
                                      boton_texto, ayuda_items=None,
                                      temp_tabla=None, temp_native="degC", temp_default=25.0,
                                      temp_kwarg="observed_temp_c"):
        if temp_tabla is None:
            temp_tabla = API_TEMPERATURA_A_DEGC
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             ayuda_items if ayuda_items is not None else self._AYUDA_API1952_METRICO_COMUN,
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value=str(temp_default))
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value=temp_native)
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in temp_tabla], state="readonly",
                     width=7).pack(side="left", padx=(4, 0))

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_api1952_ctl_tabla(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = []
        etiquetas_resultado = {}
        if salida_principal_clave:
            claves_resultado.append("principal")
            etiquetas_resultado["principal"] = salida_principal_label
        claves_resultado.append("ctl")
        etiquetas_resultado["ctl"] = "CTL, Correction for Temperature on Liquid [adimensional]"

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api1952_ctl_tabla_tabs = getattr(self, "_api1952_ctl_tabla_tabs", {})
        self._api1952_ctl_tabla_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(temp_tabla), "temp_kwarg": temp_kwarg,
            "result_vars": result_vars, "funcion": funcion,
            "salida_principal_clave": salida_principal_clave,
        }

    def _on_calcular_api1952_ctl_tabla(self, state_key):
        st = self._api1952_ctl_tabla_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_convertida = st["temp_tabla_dict"][temp_unidad](temp_valor)
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        kwargs = {st["input_kwarg"]: valor_input, st["temp_kwarg"]: temp_convertida}
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        if st["salida_principal_clave"]:
            result_vars["principal"].set(f"{r[st['salida_principal_clave']]:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.7f}")

    def _build_tab_api1952_table53(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table53_1952",
            descripcion="API Table-53 (1952, metrico) -- Densidad OBSERVADA (a T) -> "
                        "densidad a 15°C (iterativo). Tabla real de interpolacion "
                        "(valores tabulados del manual, no una formula analitica).",
            input_label="Observed Density [kg/m3]", input_default=1000.0,
            funcion=api_table53_1952, input_kwarg="observed_density_kgm3",
            salida_principal_clave="density_15c", salida_principal_label="Density a 15°C [kg/m3]",
            boton_texto="Calcular (API Table-53, 1952)",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=25.0,
            temp_kwarg="observed_temp_c")

    def _build_tab_api1952_table54(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table54_1952",
            descripcion="API Table-54 (1952, metrico) -- Densidad a 15°C -> CTL a T "
                        "observada (directo, sin iteracion). Tabla real de "
                        "interpolacion (valores tabulados del manual).",
            input_label="Density @ 15°C [kg/m3]", input_default=1000.0,
            funcion=api_table54_1952, input_kwarg="density_15c_kgm3",
            salida_principal_clave=None, salida_principal_label=None,
            boton_texto="Calcular (API Table-54, 1952)",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=25.0,
            temp_kwarg="observed_temp_c")

    # ------------------------------------------------------------------ #
    # RONDA 12: Table5/6/23/24_1952 (sistema US) -- tablas reales de
    # interpolacion decodificadas via dump de bytes crudos del `.xll`
    # (mismo metodo de RONDA 10) mas validacion cruzada entre las 2 parejas
    # de tablas independientes (Table5/6 en °API, Table23/24 en RD). Ver
    # docstring RONDA 12 en normas/API_MPMS_Tables_1980_2004.py.
    # ------------------------------------------------------------------ #
    _AYUDA_API1952_US_COMUN = [
        "Tabla real de interpolacion CTL del sistema US (1952) -- son los "
        "valores reales de la tabla impresa del manual, no una formula "
        "analitica.",
        "Validacion: a T=60°F, CTL=1.0 exacto (Table-6/24) o el valor de "
        "salida coincide con el de entrada (Table-5/23), en ambos casos "
        "surge de los datos reales de la tabla, no esta forzado. Ademas, "
        "Table-5/6 (eje °API) y Table-23/24 (eje RD) son 2 pares de tablas "
        "independientes que describen la misma superficie fisica -- "
        "coinciden en el CTL final a menos de 0.01% en 5 puntos (API, T) "
        "distintos, evidencia cruzada fuerte.",
        "PENDIENTE, no fabricado: todavia no hay un caso de esta pantalla "
        "capturado en la app Android en vivo.",
        "'API Gravity'/'RD' de entrada: sin selector de unidad (mismo "
        "criterio que el resto de la familia). 'Temperature': selector "
        "degF/degC/K/R.",
    ]

    def _build_tab_api1952_table5(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table5_1952",
            descripcion="API Table-5 (1952, sistema US) -- API Gravity OBSERVADA (a T) -> "
                        "API Gravity a 60°F (iterativo). Tabla real de interpolacion "
                        "(valores tabulados del manual).",
            input_label="Observed API Gravity [°API]", input_default=30.0,
            funcion=api_table5_1952, input_kwarg="observed_api",
            salida_principal_clave="api_60f", salida_principal_label="API Gravity a 60°F [°API]",
            boton_texto="Calcular (API Table-5, 1952)", ayuda_items=self._AYUDA_API1952_US_COMUN,
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            temp_kwarg="observed_temp_f")

    def _build_tab_api1952_table6(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table6_1952",
            descripcion="API Table-6 (1952, sistema US) -- API Gravity a 60°F -> CTL a T "
                        "observada (directo, sin iteracion). Tabla real de "
                        "interpolacion (valores tabulados del manual).",
            input_label="API Gravity @ 60°F [°API]", input_default=30.0,
            funcion=api_table6_1952, input_kwarg="api_60f",
            salida_principal_clave=None, salida_principal_label=None,
            boton_texto="Calcular (API Table-6, 1952)", ayuda_items=self._AYUDA_API1952_US_COMUN,
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            temp_kwarg="observed_temp_f")

    def _build_tab_api1952_table23(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table23_1952",
            descripcion="API Table-23 (1952, sistema US) -- Relative Density OBSERVADA (a "
                        "T) -> RD a 60°F (iterativo). Tabla real de interpolacion "
                        "(valores tabulados del manual).",
            input_label="Observed Relative Density (RD) [adimensional]", input_default=0.85,
            funcion=api_table23_1952, input_kwarg="observed_rd",
            salida_principal_clave="rd_60f",
            salida_principal_label="Relative Density a 60°F [adimensional]",
            boton_texto="Calcular (API Table-23, 1952)", ayuda_items=self._AYUDA_API1952_US_COMUN,
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            temp_kwarg="observed_temp_f")

    def _build_tab_api1952_table24(self, parent):
        self._build_tab_api1952_ctl_tabla(
            parent, state_key="table24_1952",
            descripcion="API Table-24 (1952, sistema US) -- Relative Density a 60°F -> CTL "
                        "a T observada (directo, sin iteracion). Tabla real de "
                        "interpolacion (valores tabulados del manual).",
            input_label="Relative Density (RD) @ 60°F [adimensional]", input_default=0.85,
            funcion=api_table24_1952, input_kwarg="rd_60f",
            salida_principal_clave=None, salida_principal_label=None,
            boton_texto="Calcular (API Table-24, 1952)", ayuda_items=self._AYUDA_API1952_US_COMUN,
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            temp_kwarg="observed_temp_f")

    def _build_tab_api1952_dens15c(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="API Density @15°C (1952) -- Density Conversion to and from "
                              "15°C and EVP, segun API MPMS Tables 53/54 (1952, tabla real "
                              "de interpolacion) mas el modulo de presion API MPMS 11.2.1M.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Que calcula esta pestaña",
                             self._AYUDA_API1952_METRICO_COMUN
                             + ["Esta pantalla combina la tabla de Density@15°C (arriba) con "
                                "el modulo de presion API MPMS 11.2.1M (CPL): primero converge "
                                "la densidad a 15°C por temperatura, y con ese resultado ya "
                                "convergido calcula la correccion adicional por presion.",
                                "'Conversion': 'Observed -> Standard' (default, iterativo) o "
                                "'Standard -> Observed' (directo). 'API-11.2.1M Rounding': "
                                "redondeo opcional de pantalla, verificado exacto contra el "
                                "caso real (conversion=Standard->Observed, density_15c=1000 "
                                "kg/m3, T=25°C, P=20 bar(g)): Rounding=0 da 994.5497, "
                                "Rounding=1 da 994.5502, ambos coinciden con la app real a la "
                                "precision mostrada."],
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text="Observed Density [kg/m3]", wraplength=220).grid(
            row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value="1000.0")
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value="25.0")
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value="degC")
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in API_TEMPERATURA_A_DEGC], state="readonly",
                     width=7).pack(side="left", padx=(4, 0))

        ttk.Label(izq, text="Pressure").grid(row=2, column=0, sticky="w", pady=3)
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, 2, API_PRESION_GAUGE_A_BARG, valor_default=0.0)

        ttk.Label(izq, text="Equilibrium Pressure").grid(row=3, column=0, sticky="w", pady=3)
        evp_valor_var, evp_unidad_var, _evp_tabla_dict = self._agregar_fila_presion(
            izq, 3, API_PRESION_GAUGE_A_BARG, valor_default=0.0)

        _CONVERSION_OPCIONES_1952 = [("Observed -> Standard", 1), ("Standard -> Observed", 0)]
        ttk.Label(izq, text="Conversion").grid(row=4, column=0, sticky="w", pady=3)
        conversion_var = tk.StringVar(value=_CONVERSION_OPCIONES_1952[0][0])
        ttk.Combobox(izq, textvariable=conversion_var,
                     values=[o[0] for o in _CONVERSION_OPCIONES_1952], state="readonly",
                     width=20).grid(row=4, column=1, padx=6, pady=3)

        ttk.Label(izq, text="API-11.2.1M Rounding\n(0=Disabled, 1=Enabled -- ver panel de "
                             "arriba)", wraplength=220).grid(row=5, column=0, sticky="w", pady=3)
        rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, variable=rounding_var).grid(row=5, column=1, sticky="w", padx=6, pady=3)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text="Calcular (API Density @15°C, 1952)", style="Accento.TButton",
                   command=self._on_calcular_api1952_dens15c).pack(fill="x", pady=(0, 10))

        claves_resultado = ["principal", "ctl", "cpl", "ctpl", "f"]
        etiquetas_resultado = {
            "principal": "Density a 15°C, EVP [kg/m3]",
            "ctl": "CTL, Correction for Temperature on Liquid [adimensional]",
            "cpl": "CPL, Correction for Pressure on Liquid [adimensional]",
            "ctpl": "CTPL = CTL x CPL [adimensional]",
            "f": "Factor de Compresibilidad F [1/kPa]",
        }
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api1952_dens15c_vars = {
            "valor_input_var": valor_input_var,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(API_TEMPERATURA_A_DEGC),
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict,
            "evp_valor_var": evp_valor_var, "evp_unidad_var": evp_unidad_var,
            "result_vars": result_vars,
            "conversion_var": conversion_var, "rounding_var": rounding_var,
        }

    def _on_calcular_api1952_dens15c(self):
        st = self._api1952_dens15c_vars
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_c = st["temp_tabla_dict"][temp_unidad](temp_valor)
            presion_unidad = st["presion_unidad_var"].get()
            presion = st["presion_tabla_dict"][presion_unidad](float(st["presion_valor_var"].get()))
            evp_unidad = st["evp_unidad_var"].get()
            evp = st["presion_tabla_dict"][evp_unidad](float(st["evp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        conversion = {"Observed -> Standard": 1, "Standard -> Observed": 0}[st["conversion_var"].get()]
        rounding = int(bool(st["rounding_var"].get()))
        try:
            r = api_density15c_1952(observed_density_kgm3=valor_input, observed_temp_c=temp_c,
                                     pressure_bar_g=presion, equilibrium_pressure_bar_g=evp,
                                     conversion=conversion, rounding=rounding)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars["principal"].set(f"{r['density_15c']:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.7f}")
        result_vars["cpl"].set(f"{r['cpl']:.7f}")
        result_vars["ctpl"].set(f"{r['ctpl']:.7f}")
        result_vars["f"].set(f"{r['f']:.9f}")

    # ------------------------------------------------------------------ #
    # RONDA 12: wrappers combinados API_Gravity60F_1952/API_SG60F_1952 --
    # tabla CTL real (Table5/6 o Table23/24_1952) + CPL de api_mpms_11_2_1
    # (US, ya [CERTAIN] desde RONDA 9), confirmado por decompilacion que
    # ambos wrappers SI llaman al modulo de presion. Mismo patron visual
    # que `_build_tab_api1952_dens15c` (metrico), generalizado para US
    # (temperatura en degF, presion en psig).
    # ------------------------------------------------------------------ #
    def _build_tab_api1952_wrapper_us(self, parent, state_key, descripcion,
                                       input_label, input_default, input_kwarg, funcion,
                                       salida_principal_clave, salida_principal_label,
                                       boton_texto):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Que calcula esta pestaña",
                             self._AYUDA_API1952_US_COMUN
                             + ["Esta pantalla combina la tabla CTL de arriba (Table-5/6 o "
                                "Table-23/24, sistema US) con el modulo de presion API MPMS "
                                "11.2.1 para obtener el resultado corregido tanto por "
                                "temperatura como por presion.",
                                "'Conversion': 'Observed -> Standard' (default, iterativo) o "
                                "'Standard -> Observed' (directo, sin iterar). 'API-11.2.1 "
                                "Rounding': 0=Disabled, 1=Enabled, se reenvia tal cual al "
                                "modulo de presion interno -- validado con caso real solo en "
                                "la familia metrica equivalente, no en esta tabla US "
                                "especifica."],
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value="90.0")
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value="degF")
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in API_TEMPERATURA_A_DEGF], state="readonly",
                     width=7).pack(side="left", padx=(4, 0))

        ttk.Label(izq, text="Pressure").grid(row=2, column=0, sticky="w", pady=3)
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, 2, API_PRESION_GAUGE_A_PSIG, valor_default=0.0)

        ttk.Label(izq, text="Equilibrium Pressure").grid(row=3, column=0, sticky="w", pady=3)
        evp_valor_var, evp_unidad_var, _evp_tabla_dict = self._agregar_fila_presion(
            izq, 3, API_PRESION_GAUGE_A_PSIG, valor_default=0.0)

        _CONVERSION_OPCIONES_1952US = [("Observed -> Standard", 1), ("Standard -> Observed", 0)]
        ttk.Label(izq, text="Conversion").grid(row=4, column=0, sticky="w", pady=3)
        conversion_var = tk.StringVar(value=_CONVERSION_OPCIONES_1952US[0][0])
        ttk.Combobox(izq, textvariable=conversion_var,
                     values=[o[0] for o in _CONVERSION_OPCIONES_1952US], state="readonly",
                     width=20).grid(row=4, column=1, padx=6, pady=3)

        ttk.Label(izq, text="API-11.2.1 Rounding\n(0=Disabled, 1=Enabled -- ver panel de "
                             "arriba)", wraplength=220).grid(row=5, column=0, sticky="w", pady=3)
        rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, variable=rounding_var).grid(row=5, column=1, sticky="w", padx=6, pady=3)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_api1952_wrapper_us(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = ["principal", "ctl", "cpl", "ctpl", "f"]
        etiquetas_resultado = {
            "principal": salida_principal_label,
            "ctl": "CTL, Correction for Temperature on Liquid [adimensional]",
            "cpl": "CPL, Correction for Pressure on Liquid [adimensional]",
            "ctpl": "CTPL = CTL x CPL [adimensional]",
            "f": "Factor de Compresibilidad F [1/psi]",
        }
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api1952_wrapper_us_tabs = getattr(self, "_api1952_wrapper_us_tabs", {})
        self._api1952_wrapper_us_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(API_TEMPERATURA_A_DEGF),
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict,
            "evp_valor_var": evp_valor_var, "evp_unidad_var": evp_unidad_var,
            "result_vars": result_vars, "funcion": funcion,
            "salida_principal_clave": salida_principal_clave,
            "conversion_var": conversion_var, "rounding_var": rounding_var,
        }

    def _on_calcular_api1952_wrapper_us(self, state_key):
        st = self._api1952_wrapper_us_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_f = st["temp_tabla_dict"][temp_unidad](temp_valor)
            presion_unidad = st["presion_unidad_var"].get()
            presion = st["presion_tabla_dict"][presion_unidad](float(st["presion_valor_var"].get()))
            evp_unidad = st["evp_unidad_var"].get()
            evp = st["presion_tabla_dict"][evp_unidad](float(st["evp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        conversion = {"Observed -> Standard": 1, "Standard -> Observed": 0}[st["conversion_var"].get()]
        rounding = int(bool(st["rounding_var"].get()))
        kwargs = {st["input_kwarg"]: valor_input, "observed_temp_f": temp_f,
                  "pressure_psig": presion, "equilibrium_pressure_psig": evp,
                  "conversion": conversion, "rounding": rounding}
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars["principal"].set(f"{r[st['salida_principal_clave']]:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.7f}")
        result_vars["cpl"].set(f"{r['cpl']:.7f}")
        result_vars["ctpl"].set(f"{r['ctpl']:.7f}")
        result_vars["f"].set(f"{r['f']:.9f}")

    def _build_tab_api1952_gravity60f(self, parent):
        self._build_tab_api1952_wrapper_us(
            parent, state_key="gravity60f_1952",
            descripcion="API Gravity @60°F (1952) -- °API (T, P) <--> °API (60°F, "
                        "equilibrium pressure), segun API MPMS Tables 5/6 (1952, tabla "
                        "real de interpolacion) mas el modulo de presion API MPMS 11.2.1.",
            input_label="Observed API Gravity [°API]", input_default=30.0,
            input_kwarg="observed_api", funcion=api_gravity60f_1952,
            salida_principal_clave="api_60f", salida_principal_label="API Gravity a 60°F, EVP [°API]",
            boton_texto="Calcular (API Gravity @60°F, 1952)")

    def _build_tab_api1952_sg60f(self, parent):
        self._build_tab_api1952_wrapper_us(
            parent, state_key="sg60f_1952",
            descripcion="API Specific Gravity @60°F (1952) -- RD (T, P) <--> RD (60°F, "
                        "equilibrium pressure), segun API MPMS Tables 23/24 (1952, tabla "
                        "real de interpolacion) mas el modulo de presion API MPMS 11.2.1.",
            input_label="Observed Relative Density (RD) [adimensional]", input_default=0.85,
            input_kwarg="observed_rd", funcion=api_sg60f_1952,
            salida_principal_clave="rd_60f", salida_principal_label="Relative Density a 60°F, EVP [adimensional]",
            boton_texto="Calcular (API Specific Gravity @60°F, 1952)")

    # ------------------------------------------------------------------ #
    # RONDA 9 (correccion de un error previo -- ver memoria del proyecto,
    # "CORRECCION IMPORTANTE 2026-08-25"): estos 3 wrappers de 1980
    # combinan el motor CTL ya [CERTAIN] de Table5/6/23/24/53/54_1980 con
    # el modulo de presion API MPMS 11.2.1/11.2.1M, tambien [CERTAIN] esta
    # ronda -- validado con el caso real capturado por el usuario en la app
    # (Density_obs=1000kg/m3, T=25°C, P=20bar(g), EVP=0 -> CPL=1.001045,
    # reproducido a 0.00003% de diferencia). Un peldano por debajo del resto
    # de la familia: la combinacion completa (wrapper) no tiene su PROPIO
    # caso real todavia, solo el modulo de presion por separado.
    # ------------------------------------------------------------------ #
    def _build_tab_api_wrapper_presion(self, parent, state_key, descripcion, ayuda_items,
                                        input_label, input_default, funcion, input_kwarg,
                                        temp_tabla, temp_native, temp_default,
                                        presion_kwarg, evp_kwarg, presion_unidad,
                                        salida_principal_clave, salida_principal_label,
                                        alpha_convertir_a_c, boton_texto,
                                        auto_select_disponible=False):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", ayuda_items,
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value=str(temp_default))
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value=temp_native)
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in temp_tabla], state="readonly", width=7).pack(
            side="left", padx=(4, 0))

        presion_tabla = (API_PRESION_GAUGE_A_PSIG if presion_kwarg == "pressure_psig"
                          else API_PRESION_GAUGE_A_BARG)
        ttk.Label(izq, text="Pressure").grid(row=2, column=0, sticky="w", pady=3)
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, 2, presion_tabla, valor_default=0.0)

        ttk.Label(izq, text="Equilibrium Pressure").grid(row=3, column=0, sticky="w", pady=3)
        evp_valor_var, evp_unidad_var, _evp_tabla_dict = self._agregar_fila_presion(
            izq, 3, presion_tabla, valor_default=0.0)

        ttk.Label(izq, text="Product").grid(row=4, column=0, sticky="w", pady=3)
        producto_var = tk.StringVar(value=API_PRODUCTOS[0][0])
        ttk.Combobox(izq, textvariable=producto_var, values=[p[0] for p in API_PRODUCTOS],
                     state="readonly", width=16).grid(row=4, column=1, padx=6, pady=3)
        if auto_select_disponible:
            ttk.Label(izq, text="\"Refined, auto\" (RONDA 44): selecciona automaticamente "
                                "Gasoline/Transition/Jet/FuelOil segun la densidad (breakpoints "
                                "del motor real, validados contra el oraculo .xll). El producto "
                                "realmente elegido se muestra en \"Product (selected)\".",
                        foreground="gray", wraplength=220).grid(
                row=4, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=3)
        else:
            ttk.Label(izq, text="\"Refined, auto\" no esta implementado para esta funcion -- "
                                "de elegirlo, el calculo mostrara un error explicito en vez de "
                                "un numero fabricado.", foreground="gray", wraplength=220).grid(
                row=4, column=2, columnspan=2, sticky="w", padx=(10, 0), pady=3)

        _CONVERSION_OPCIONES = [("Observed -> Standard", 1), ("Standard -> Observed", 0)]
        ttk.Label(izq, text="Conversion").grid(row=5, column=0, sticky="w", pady=3)
        conversion_var = tk.StringVar(value=_CONVERSION_OPCIONES[0][0])
        ttk.Combobox(izq, textvariable=conversion_var,
                     values=[o[0] for o in _CONVERSION_OPCIONES], state="readonly",
                     width=20).grid(row=5, column=1, padx=6, pady=3)

        ttk.Label(izq, text="API-11.2.1(M) Rounding\n(0=Disabled, 1=Enabled -- ver panel de "
                             "arriba)", wraplength=220).grid(row=6, column=0, sticky="w", pady=3)
        rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, variable=rounding_var).grid(row=6, column=1, sticky="w", padx=6, pady=3)

        hidrometro_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="Hydrometer Corr. (ver panel de arriba)",
                        variable=hidrometro_var).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=3)

        ttk.Label(izq, text="API-2540 Rounding").grid(row=8, column=0, sticky="w", pady=3)
        api2540_rounding_var = tk.StringVar(value=API_ROUNDING_ENUM_OPCIONES[0][0])
        ttk.Combobox(izq, textvariable=api2540_rounding_var,
                     values=[o[0] for o in API_ROUNDING_ENUM_OPCIONES], state="readonly",
                     width=24).grid(row=8, column=1, padx=6, pady=3)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_api_wrapper_presion(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = ["principal", "ctl", "cpl", "ctpl", "f", "alpha", "k0", "k1", "k2"]
        etiquetas_resultado = {
            "principal": salida_principal_label,
            "ctl": "CTL, Correction for Temperature on Liquid [adimensional]",
            "cpl": "CPL, Correction for Pressure on Liquid [adimensional]",
            "ctpl": "CTPL = CTL x CPL [adimensional]",
            "f": "Factor de Compresibilidad F [ver docstring de la funcion Python]",
            "alpha": "Alpha, Coeficiente de Expansion Termica [1/gradoC]",
            "k0": "K0 (constante de tabla, segun Product) [adimensional]",
            "k1": "K1 (constante de tabla, segun Product) [adimensional]",
            "k2": "K2 (constante de tabla, segun Product; 0 si no aplica) [adimensional]",
        }
        if auto_select_disponible:
            claves_resultado.append("product_efectivo")
            etiquetas_resultado["product_efectivo"] = (
                "Product (selected) -- producto realmente usado cuando Product=\"Refined, "
                "auto\" (1=Crude/3=Gasoline/4=Transition/5=Jet/6=FuelOil/7=Lube)")
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api_wrapper_presion_tabs = getattr(self, "_api_wrapper_presion_tabs", {})
        self._api_wrapper_presion_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(temp_tabla),
            "temp_kwarg": "observed_temp_f" if temp_native == "degF" else "observed_temp_c",
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict, "presion_kwarg": presion_kwarg,
            "evp_valor_var": evp_valor_var, "evp_unidad_var": evp_unidad_var,
            "evp_kwarg": evp_kwarg,
            "producto_var": producto_var, "result_vars": result_vars, "funcion": funcion,
            "salida_principal_clave": salida_principal_clave,
            "alpha_convertir_a_c": alpha_convertir_a_c,
            "conversion_var": conversion_var,
            "rounding_var": rounding_var,
            "hidrometro_var": hidrometro_var,
            "api2540_rounding_var": api2540_rounding_var,
            "auto_select_disponible": auto_select_disponible,
        }

    def _on_calcular_api_wrapper_presion(self, state_key):
        st = self._api_wrapper_presion_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_convertida = st["temp_tabla_dict"][temp_unidad](temp_valor)
            presion_unidad = st["presion_unidad_var"].get()
            presion = st["presion_tabla_dict"][presion_unidad](float(st["presion_valor_var"].get()))
            evp_unidad = st["evp_unidad_var"].get()
            evp = st["presion_tabla_dict"][evp_unidad](float(st["evp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        producto = dict(API_PRODUCTOS)[st["producto_var"].get()]
        conversion = {"Observed -> Standard": 1, "Standard -> Observed": 0}[st["conversion_var"].get()]
        api2540_rounding = dict(API_ROUNDING_ENUM_OPCIONES)[st["api2540_rounding_var"].get()]
        kwargs = {
            st["input_kwarg"]: valor_input, st["temp_kwarg"]: temp_convertida,
            st["presion_kwarg"]: presion, st["evp_kwarg"]: evp, "product": producto,
            "conversion": conversion, "rounding": int(bool(st["rounding_var"].get())),
            "hydrometer_correction": bool(st["hidrometro_var"].get()),
            "api2540_rounding": api2540_rounding,
        }
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars["principal"].set(f"{r[st['salida_principal_clave']]:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.6f}")
        result_vars["cpl"].set(f"{r['cpl']:.6f}")
        result_vars["ctpl"].set(f"{r['ctpl']:.6f}")
        result_vars["f"].set(f"{r['f']:.9f}")
        alpha = r["alpha"]
        if st["alpha_convertir_a_c"]:
            alpha = alpha * 1.8
        result_vars["alpha"].set(f"{alpha:.6f}")
        result_vars["k0"].set(f"{r['k0']:.4f}")
        result_vars["k1"].set(f"{r['k1']:.6f}")
        result_vars["k2"].set(f"{r['k2']:.6f}")
        if st.get("auto_select_disponible") and "product_efectivo" in result_vars:
            result_vars["product_efectivo"].set(str(r.get("product_efectivo", "-")))

    _AYUDA_API_WRAPPER_1980_COMUN = [
        "Combina el motor CTL de API Table-53/54 (metrico) o Table-5/6/23/24 (US), "
        "1980, con el modulo de presion API MPMS 11.2.1/11.2.1M (CPL): primero "
        "converge la densidad/gravedad por temperatura, y con ese resultado calcula "
        "la correccion adicional por presion.",
        "El modulo de presion (CPL) esta validado contra un caso real capturado en "
        "la app (Density_obs=1000 kg/m3, T=25°C, P=20 bar(g), EVP=0 -> CPL=1.001045, "
        "reproducido con un error de 0.00003%). La combinacion completa de esta "
        "pestaña (CTL+CPL iterando juntos) no tiene todavia su propio caso real "
        "capturado end-to-end.",
        "'Equilibrium Pressure' (EVP): presion de vapor de equilibrio, tipicamente "
        "0 bar(g)/0 psig segun el manual -- se resta de la presion observada antes "
        "de aplicar CPL. 'Product': mismas 7 opciones que el resto de la familia.",
        "'Conversion': 'Observed -> Standard' (default, iterativo) o 'Standard -> "
        "Observed' (directo, sin iterar) -- confirmado con una prueba de ida y "
        "vuelta (round-trip) contra el motor real, diferencia menor a 1e-6%.",
        "'API-11.2.1(M) Rounding': redondeo opcional de pantalla, verificado con el "
        "caso real de la familia metrica equivalente: 994.5497 (Off) vs 994.5502 "
        "(On) para Density=1000 kg/m3, T=25°C, P=20 bar(g). Se aplica solo al modulo "
        "de presion, no afecta el CTL.",
        "'Hydrometer Corr.' y 'API-2540 Rounding': confirmados como campos reales de "
        "la pantalla (captura de pantalla en vivo), aunque su efecto numerico exacto "
        "en esta combinacion especifica es una inferencia razonable, no un caso real "
        "propio. 'Hydrometer Corr.' reusa la misma correccion de lectura de "
        "hidrometro de Table5/23/53 (1980), aplicada solo en direccion "
        "Observed->Standard. 'API-2540 Rounding' reusa el mismo patron de "
        "Table6/24/54 (1980): solo 'Enabled (table values)' redondea el CTL a 4 "
        "decimales. PENDIENTE, no fabricado: el motor real aplica ademas un "
        "redondeo intermedio adicional sobre pasos internos del calculo (densidad, "
        "temperatura, coeficiente de expansion) que no se replico a ese nivel de "
        "detalle -- ver docstring de api_density15c_1980 en "
        "normas/API_MPMS_Tables_1980_2004.py.",
    ]

    def _build_tab_api1980_dens15c(self, parent):
        self._build_tab_api_wrapper_presion(
            parent, state_key="dens15c_1980",
            descripcion="API Density @15°C (1980) -- Density Conversion to and from 15°C "
                        "and EVP, segun API MPMS Tables 53/54 (1980) + API MPMS 11.2.1M.",
            ayuda_items=self._AYUDA_API_WRAPPER_1980_COMUN,
            input_label="Observed Density [kg/m3]", input_default=1000.0,
            funcion=api_density15c_1980, input_kwarg="observed_density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=25.0,
            presion_kwarg="pressure_bar_g", evp_kwarg="equilibrium_pressure_bar_g",
            presion_unidad="bar(g)",
            salida_principal_clave="density_15c", salida_principal_label="Density a 15°C, EVP [kg/m3]",
            alpha_convertir_a_c=False, boton_texto="Calcular (API Density @15°C, 1980)",
            auto_select_disponible=True)

    def _build_tab_api1980_gravity60f(self, parent):
        self._build_tab_api_wrapper_presion(
            parent, state_key="gravity60f_1980",
            descripcion="API Gravity @60°F (1980) -- °API Conversion to and from 60°F "
                        "and EVP, segun API MPMS Tables 5/6 (1980) + API MPMS 11.2.1.",
            ayuda_items=self._AYUDA_API_WRAPPER_1980_COMUN,
            input_label="Observed API Gravity [°API]", input_default=30.0,
            funcion=api_gravity60f_1980, input_kwarg="observed_api",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            presion_kwarg="pressure_psig", evp_kwarg="equilibrium_pressure_psig",
            presion_unidad="psig",
            salida_principal_clave="api_60f", salida_principal_label="API Gravity a 60°F, EVP [°API]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Gravity @60°F, 1980)",
            auto_select_disponible=True)

    def _build_tab_api1980_reldensity60f(self, parent):
        self._build_tab_api_wrapper_presion(
            parent, state_key="reldensity60f_1980",
            descripcion="API Rel. Density @60°F (1980) -- RD Conversion to and from 60°F "
                        "and EVP, segun API MPMS Tables 23/24 (1980) + API MPMS 11.2.1.",
            ayuda_items=self._AYUDA_API_WRAPPER_1980_COMUN,
            input_label="Observed Relative Density (RD) [adimensional]", input_default=0.85,
            funcion=api_reldensity60f_1980, input_kwarg="observed_rd",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            presion_kwarg="pressure_psig", evp_kwarg="equilibrium_pressure_psig",
            presion_unidad="psig",
            salida_principal_clave="rd_60f", salida_principal_label="Relative Density a 60°F, EVP [adimensional]",
            alpha_convertir_a_c=True, boton_texto="Calcular (API Rel. Density @60°F, 1980)",
            auto_select_disponible=True)

    def _build_tab_api_mpms_112(self, parent, state_key, descripcion, ayuda_items,
                                 input_label, input_default, funcion, input_kwarg,
                                 temp_tabla, temp_native, temp_default,
                                 presion_kwarg, evp_kwarg, presion_unidad,
                                 f_unidad, boton_texto):
        """Constructor generico para las 4 pantallas de "API 11.2/12.2"
        (11.2.1/11.2.1M/11.2.2/11.2.2M): a diferencia de `_build_tab_api_mpms`
        (que tiene Product/CTL/CTPL/Alpha, familia 11.1) estas 4 funciones son
        MAS SIMPLES -- solo Densidad/RD/API + Temperature + Pressure + EVP ->
        F + CPL, sin selector de Product ni CTL (ver RONDA 13)."""
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", ayuda_items,
                             wraplength=740).pack(fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_row = ttk.Frame(izq)
        temp_row.grid(row=1, column=1, padx=6, pady=3, sticky="w")
        temp_valor_var = tk.StringVar(value=str(temp_default))
        ttk.Entry(temp_row, textvariable=temp_valor_var, width=10).pack(side="left")
        temp_unidad_var = tk.StringVar(value=temp_native)
        ttk.Combobox(temp_row, textvariable=temp_unidad_var,
                     values=[u for u, _f in temp_tabla], state="readonly", width=7).pack(
            side="left", padx=(4, 0))

        presion_tabla = (API_PRESION_GAUGE_A_PSIG if presion_kwarg == "pressure_psig"
                          else API_PRESION_GAUGE_A_BARG)
        ttk.Label(izq, text="Pressure").grid(row=2, column=0, sticky="w", pady=3)
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, 2, presion_tabla, valor_default=0.0)

        ttk.Label(izq, text="Equilibrium Pressure").grid(row=3, column=0, sticky="w", pady=3)
        evp_valor_var, evp_unidad_var, _evp_tabla_dict = self._agregar_fila_presion(
            izq, 3, presion_tabla, valor_default=0.0)

        # [RONDA 36 (2026-09-09)] "API-11.2.x(M) Rounding" -- las 4 funciones
        # (`api_mpms_11_2_1`/`_1m`/`_2`/`_2m`) YA tienen el parametro `rounding`
        # en Python (11.2.1/11.2.1M desde RONDA 19, 11.2.2/11.2.2M NUEVO esta
        # ronda, [CERTAIN via decompilacion] en ambos casos) pero esta pestaña
        # generica nunca lo conectaba -- agregado aqui, unico checkbox para las
        # 4 pantallas (mismo nombre de parametro en las 4).
        rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API Rounding", variable=rounding_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=3)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_api_mpms_112(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = ["cpl", "f"]
        etiquetas_resultado = {
            "cpl": "CPL, Correction for Pressure on Liquid [adimensional]",
            "f": f"Factor de Compresibilidad F [{f_unidad}]",
        }
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._api_mpms_112_tabs = getattr(self, "_api_mpms_112_tabs", {})
        self._api_mpms_112_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": dict(temp_tabla),
            "temp_kwarg": "temp_f" if temp_native == "degF" else "temp_c",
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict, "presion_kwarg": presion_kwarg,
            "evp_valor_var": evp_valor_var, "evp_unidad_var": evp_unidad_var,
            "evp_kwarg": evp_kwarg,
            "rounding_var": rounding_var,
            "result_vars": result_vars, "funcion": funcion,
        }

    def _on_calcular_api_mpms_112(self, state_key):
        st = self._api_mpms_112_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_valor = float(st["temp_valor_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_convertida = st["temp_tabla_dict"][temp_unidad](temp_valor)
            presion_unidad = st["presion_unidad_var"].get()
            presion = st["presion_tabla_dict"][presion_unidad](float(st["presion_valor_var"].get()))
            evp_unidad = st["evp_unidad_var"].get()
            evp = st["presion_tabla_dict"][evp_unidad](float(st["evp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        kwargs = {
            st["input_kwarg"]: valor_input, st["temp_kwarg"]: temp_convertida,
            st["presion_kwarg"]: presion, st["evp_kwarg"]: evp,
            "rounding": 1 if st["rounding_var"].get() else 0,
        }
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars["cpl"].set(f"{r['cpl']:.6f}")
        result_vars["f"].set(f"{r['f']:.9f}")
        # Mismo patron ya usado en Ethylene/Propylene y en los wrappers NGL/LPG
        # para el flag interno "fuera_de_rango_oficial" que estas 4 funciones
        # (api_mpms_11_2_1/11_2_1m/11_2_2/11_2_2m) YA devuelven -- aqui no se
        # mostraba, agregado por consistencia (mismo flag, mismo significado).
        if r.get("fuera_de_rango_oficial"):
            messagebox.showwarning(
                "Fuera de rango",
                "El nucleo real senializo esta entrada como fuera del rango "
                "fisico oficial de esta norma (ver panel de ayuda para los "
                "limites) -- el resultado mostrado es el que el binario real "
                "devuelve de todos modos, igual que hace la app.")

    _AYUDA_API_11_2_1_COMUN = [
        "API MPMS 11.2.1/11.2.1M/12.2 -- 'Compressibility Factors for "
        "Hydrocarbons: 0-90 API Gravity Range', 1st Edition, August 1984.",
        "Formula: F=exp(T*A-B+C/rho_r^2+T*D/rho_r^2)/escala, CPL=1/(1-(P1-P2)*F) "
        "(US, P en psi) o CPL=1/(1-(P1-P2)*0.01*F) (metrico, P en kPa) -- F es el "
        "factor de compresibilidad del liquido y CPL (Correction for Pressure on "
        "Liquid) el factor que ajusta el volumen medido por la diferencia de "
        "presion (P1-P2).",
        "Validado EXACTO (6 decimales) contra caso real, tocando esta misma "
        "pantalla en la app: metrico (rho=800 kg/m3, T=25°C, P=50 bar(g): "
        "CPL=1.004590, F=0.000091 1/bar) y US (API=50, T=90°F, P=50 psig: "
        "CPL=1.000360, F=0.000007 1/psi).",
        "'API Gravity'/'Density@15C' de entrada: sin selector de unidad "
        "(confirmado contra la pantalla real). 'Temperature': selector "
        "K/degC/degF/R. 'Pressure'/'Equilibrium Pressure': selector real de 11 "
        "unidades gauge (bar(g)/mbar(g)/mmHgg/mmH2Og/inHgg/inH2Og, confirmado "
        "tocando la pantalla real, RONDA 39) -- convierte automaticamente a la "
        "unidad nativa del motor (psig US / bar(g) metrico).",
    ]

    _AYUDA_API_11_2_2_COMUN = [
        "API MPMS 11.2.2/11.2.2M/12.2 -- 'Compressibility Factors for "
        "Hydrocarbons: 0.350-0.637 Relative Density (60/60F) and -50F to 140F "
        "Metering Temperature', 2nd Edition, October 1986 -- norma DISTINTA de "
        "11.2.1/11.2.1M (rango de densidad mas bajo, tipico NGL/LPG), no una "
        "simple extension con las mismas constantes.",
        "Estructuralmente distinto de 11.2.1: usa un polinomio de grado alto en "
        "T (Rankine) y en la densidad reducida, con 2 pasos de redondeo "
        "obligatorios (no opcionales, forman parte de la propia formula) -- ver "
        "docstring de normas/API_MPMS_Tables_1980_2004.py para el detalle "
        "completo.",
        "Validado EXACTO (6 decimales) contra caso real capturado en la app: "
        "metrico (Density@15C=600 kg/m3, T=25°C, P=20 bar(g): CPL=1.005227, "
        "F=0.000260 1/bar) y US (RD@60F=0.5, T=90°F, P=50 psig: CPL=1.002857, "
        "F=0.000057 1/psi).",
        "'Rel.Density@60F'/'Density@15C' de entrada: sin selector de unidad "
        "(confirmado contra la pantalla real). 'Temperature': selector "
        "K/degC/degF/R. 'Pressure'/'Equilibrium Pressure': igual que 11.2.1 -- "
        "selector real de 11 unidades gauge, convierte automaticamente a la "
        "unidad nativa del motor (psig US / bar(g) metrico).",
        "PENDIENTE de baja prioridad, no bloqueante: el flag 'API-11.2.2(M) "
        "Rounding' de la app no se probo activado -- se espera que solo afecte "
        "la presentacion, igual que los flags analogos ya documentados en el "
        "resto de la familia, pero no hay un caso real propio que lo confirme.",
    ]

    def _build_tab_api112_1(self, parent):
        self._build_tab_api_mpms_112(
            parent, state_key="mpms_11_2_1",
            descripcion="API MPMS 11.2.1 (US) -- Compressibility Factor F and CPL, "
                        "0-90 API Gravity Range.",
            ayuda_items=self._AYUDA_API_11_2_1_COMUN,
            input_label="API Gravity @60°F [°API]", input_default=50.0,
            funcion=api_mpms_11_2_1, input_kwarg="api_gravity",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            presion_kwarg="pressure_psig", evp_kwarg="equilibrium_pressure_psig",
            presion_unidad="psig", f_unidad="1/psi",
            boton_texto="Calcular (API MPMS 11.2.1)")

    def _build_tab_api112_1m(self, parent):
        self._build_tab_api_mpms_112(
            parent, state_key="mpms_11_2_1m",
            descripcion="API MPMS 11.2.1M (metrico) -- Compressibility Factor F and "
                        "CPL, 638-1074 kg/m3 Density Range.",
            ayuda_items=self._AYUDA_API_11_2_1_COMUN,
            input_label="Density @15°C [kg/m3]", input_default=800.0,
            funcion=api_mpms_11_2_1m, input_kwarg="density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=25.0,
            presion_kwarg="pressure_bar_g", evp_kwarg="equilibrium_pressure_bar_g",
            presion_unidad="bar(g)", f_unidad="1/bar",
            boton_texto="Calcular (API MPMS 11.2.1M)")

    def _build_tab_api112_2(self, parent):
        self._build_tab_api_mpms_112(
            parent, state_key="mpms_11_2_2",
            descripcion="API MPMS 11.2.2 (US) -- Compressibility Factor F and CPL, "
                        "0.350-0.637 Relative Density Range.",
            ayuda_items=self._AYUDA_API_11_2_2_COMUN,
            input_label="Rel. Density @60°F [adimensional]", input_default=0.5,
            funcion=api_mpms_11_2_2, input_kwarg="rd_60f",
            temp_tabla=API_TEMPERATURA_A_DEGF, temp_native="degF", temp_default=90.0,
            presion_kwarg="pressure_psig", evp_kwarg="equilibrium_pressure_psig",
            presion_unidad="psig", f_unidad="1/psi",
            boton_texto="Calcular (API MPMS 11.2.2)")

    def _build_tab_api112_2m(self, parent):
        self._build_tab_api_mpms_112(
            parent, state_key="mpms_11_2_2m",
            descripcion="API MPMS 11.2.2M (metrico) -- Compressibility Factor F and "
                        "CPL, 350-637 kg/m3 Density Range.",
            ayuda_items=self._AYUDA_API_11_2_2_COMUN,
            input_label="Density @15°C [kg/m3]", input_default=600.0,
            funcion=api_mpms_11_2_2m, input_kwarg="density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=25.0,
            presion_kwarg="pressure_bar_g", evp_kwarg="equilibrium_pressure_bar_g",
            presion_unidad="bar(g)", f_unidad="1/bar",
            boton_texto="Calcular (API MPMS 11.2.2M)")

    # ===========================================================================
    # "E NGL/LPG (TP-27)" -- ULTIMA categoria del menu raiz "API" (RONDA 14,
    # 2026-08-26). 9 pantallas reales confirmadas en vivo (uiautomator): las 6
    # de abajo (Table23E/24E/53E/54E/59E/60E) estan CERRADAS [CERTAIN] con
    # caso real directo o round-trip exacto -- ver
    # normas/API_MPMS_Tables_1980_2004.py, docstring RONDA 14. Los otros 3
    # ("API Density @15°C NGL/LPG", "API Density @20°C NGL/LPG", "API Rel.
    # Density @60°F NGL/LPG") son wrappers combinados (motor de abajo + API
    # MPMS 11.2.1/11.2.2 + GPA TP-15) CERRADOS en RONDA 15 via llamada
    # DIRECTA al nucleo real dentro de FlowXpert.xll (ctypes, sin Excel/
    # emulador) -- ver la seccion RONDA 15 mas abajo en este archivo y
    # normas/_ngl_lpg_wrappers_xll_directo.py.
    _AYUDA_NGL_LPG_COMUN = [
        "API 11.2.4 / GPA TP-27 (2007), Tables 23E/24E/53E/54E/59E/60E -- motor "
        "propio de esta familia (distinto del K0/K1/K2 por producto de API 11.1 "
        "1980/2004, y distinto del motor de API MPMS 11.2.2): un polinomio "
        "racional por tramos (12 segmentos) en densidad relativa reducida, "
        "tomado de la tabla real del manual.",
        "Validado EXACTO (6 decimales) contra 4 casos reales capturados en la "
        "app, mas 3 pruebas de ida y vuelta (round-trip) entre pares inversos "
        "(23E<->24E, 53E<->54E, 59E<->60E).",
        "'Relative Density'/'Density' de entrada: sin selector de unidad "
        "(siempre RD adimensional o kg/m3). 'Temperature': selector real "
        "K/°C/°F/R (confirmado tocando la pantalla real, RONDA 39; antes se "
        "creia fija en °C sin selector). 'API Rounding': redondea la entrada "
        "(a la graduacion real de un "
        "hidrometro o termometro, segun el campo) y la salida principal a la "
        "precision de pantalla real de la app -- SI cambia el numero devuelto, "
        "verificado contra el motor real de FlowXpert.",
    ]

    def _build_tab_ngl_lpg_ctl(self, parent, state_key, descripcion,
                                input_label, input_default, input_kwarg,
                                funcion, salidas, boton_texto):
        """Constructor generico para las 6 pantallas puras de 'E NGL/LPG
        (TP-27)': todas reciben (valor, Temperature[°C]) y devuelven un dict
        con 'ctl' y 0-1 salidas adicionales -- mas simple que
        `_build_tab_api_mpms`/`_build_tab_api_mpms_112` porque no hay
        Product/Pressure/EVP en estas 6. `salidas` es una lista de tuplas
        (clave_dict, etiqueta, formato) para las salidas ademas de CTL."""
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_NGL_LPG_COMUN, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        ttk.Label(izq, text=input_label, wraplength=220).grid(row=0, column=0, sticky="w", pady=3)
        valor_input_var = tk.StringVar(value=str(input_default))
        ttk.Entry(izq, textvariable=valor_input_var, width=12).grid(row=0, column=1, padx=6, pady=3)

        # Temperature: selector real K/degC/degF/R -- confirmado en vivo
        # (uiautomator, RONDA 39, "API Table-23E") que estas 6 pantallas
        # puras TAMBIEN tienen el mismo "Unit" Spinner del resto de la
        # familia API (antes solo un Entry fijo, sin selector).
        ttk.Label(izq, text="Temperature").grid(row=1, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, 1, API_TEMPERATURA_A_DEGC, valor_default=25.0, unidad_default="degC")

        # [RONDA 37 (2026-09-09)] "API Rounding" -- campo real de pantalla
        # confirmado en las 6 pantallas puras (Switch booleano, ya visto en
        # RONDA 14 pero nunca conectado). Redondea entradas y salida a la
        # graduacion real de instrumento (hidrometro/termometro) igual que
        # el resto de la familia -- ver docstring de cada funcion en
        # normas/API_MPMS_Tables_1980_2004.py para el detalle exacto por
        # tabla, validado EMPIRICAMENTE contra `FlowXpert.xll` (ctypes
        # directo, sin Excel/emulador) esta ronda.
        rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API Rounding",
                         variable=rounding_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=3)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_ngl_lpg_ctl(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = [clave for clave, _et, _fmt in salidas] + ["ctl"]
        etiquetas_resultado = {clave: et for clave, et, _fmt in salidas}
        etiquetas_resultado["ctl"] = "CTL, Correction for Temperature on Liquid [adimensional]"
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._ngl_lpg_tabs = getattr(self, "_ngl_lpg_tabs", {})
        self._ngl_lpg_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict, "rounding_var": rounding_var,
            "funcion": funcion, "salidas": salidas, "result_vars": result_vars,
        }

    def _on_calcular_ngl_lpg_ctl(self, state_key):
        st = self._ngl_lpg_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp_c = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        kwargs = {
            st["input_kwarg"]: valor_input, "observed_temp_c": temp_c,
            "rounding": 1 if st["rounding_var"].get() else 0,
        }
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        for clave, _et, fmt in st["salidas"]:
            result_vars[clave].set(fmt.format(r[clave]))
        result_vars["ctl"].set(f"{r['ctl']:.6f}")

    def _build_tab_api_table23e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table23e",
            descripcion="API Table-23E -- LPG/NGL Relative Density at 60°F "
                        "according to GPA TP-27 Table 23E.",
            input_label="Relative Density [adimensional]", input_default=0.65,
            input_kwarg="observed_rd", funcion=api_table23e,
            salidas=[("rd_60f", "Rel. Density @60°F [adimensional]", "{:.6f}")],
            boton_texto="Calcular (API Table-23E)")

    def _build_tab_api_table24e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table24e",
            descripcion="API Table-24E -- LPG/NGL CTL (Correction Factor for "
                        "Temperature) at 60°F according to API 11.2.4 / GPA "
                        "TP-27 Table 24E.",
            input_label="Rel. Density @60°F [adimensional]", input_default=0.6,
            input_kwarg="rd_60f", funcion=api_table24e,
            salidas=[], boton_texto="Calcular (API Table-24E)")

    def _build_tab_api_table53e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table53e",
            descripcion="API Table-53E -- LPG/NGL Density at 15°C according "
                        "to GPA TP-27 Table 53E.",
            input_label="Density [kg/m3]", input_default=600.0,
            input_kwarg="observed_density_kgm3", funcion=api_table53e,
            salidas=[("density_15c", "Density @15°C [kg/m3]", "{:.4f}")],
            boton_texto="Calcular (API Table-53E)")

    def _build_tab_api_table54e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table54e",
            descripcion="API Table-54E -- LPG/NGL Density observed from "
                        "Density @15°C (inversa de Table 53E).",
            input_label="Density @15°C [kg/m3]", input_default=610.4798,
            input_kwarg="density_15c_kgm3", funcion=api_table54e,
            salidas=[("density_obs_predicted", "Density observed [kg/m3]", "{:.4f}")],
            boton_texto="Calcular (API Table-54E)")

    def _build_tab_api_table59e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table59e",
            descripcion="API Table-59E -- LPG/NGL Density at 20°C according "
                        "to API 11.2.4 / GPA TP-27 Table 59E.",
            input_label="Density [kg/m3]", input_default=600.0,
            input_kwarg="observed_density_kgm3", funcion=api_table59e,
            salidas=[("density_20c", "Density @20°C [kg/m3]", "{:.4f}")],
            boton_texto="Calcular (API Table-59E)")

    def _build_tab_api_table60e(self, parent):
        self._build_tab_ngl_lpg_ctl(
            parent, state_key="table60e",
            descripcion="API Table-60E -- LPG/NGL Density observed from "
                        "Density @20°C (inversa de Table 59E).",
            input_label="Density @20°C [kg/m3]", input_default=605.2727,
            input_kwarg="density_20c_kgm3", funcion=api_table60e,
            salidas=[("density_obs_predicted", "Density observed [kg/m3]", "{:.4f}")],
            boton_texto="Calcular (API Table-60E)")

    # ===========================================================================
    # RONDA 15 (2026-08-27): los 3 wrappers combinados CIERRAN via llamada
    # DIRECTA a FlowXpert.xll (ctypes, sin Excel/emulador -- misma tecnica que
    # ya funciono para AGA-10/NX-19). Ver normas/_ngl_lpg_wrappers_xll_directo.py
    # y la seccion RONDA 15 en normas/API_MPMS_Tables_1980_2004.py.
    _AYUDA_NGL_LPG_WRAPPER_COMUN = [
        "Wrapper combinado: motor CTL 'E' (Table23E/24E/53E/54E/59E/60E) mas "
        "el modulo de presion API MPMS 11.2.2/11.2.2M mas GPA TP-15 (presion "
        "de vapor en equilibrio), dentro de un solver iterativo (hasta 100 "
        "iteraciones, con aceleracion tipo Aitken para converger mas rapido).",
        "'API Rel. Density @60°F NGL/LPG': validado EXACTO a 6 decimales "
        "contra un caso real completo (RD=0.5, T=110°F=43.33°C, P=200 "
        "psia=13.79 bar(a), Atm=14.696 psia=1.0133 bar(a)) -> RD60F=0.537512, "
        "CTL=0.927163, CPL=1.003289, CTPL=0.930212, F=0.000047 1/psi, "
        "Equilibrium Pressure=9.020282 bar(a). Es la unica pantalla de esta "
        "familia que trabaja nativamente en unidades US (°F/psia).",
        "'API Density @15°C/@20°C NGL/LPG': sin caso real propio capturado -- "
        "validados por una prueba algebraica de ida y vuelta (round-trip) "
        "contra Table53E/54E y Table59E/60E con Pressure=Equilibrium "
        "Pressure=0 bar(g) (CPL debe dar 1.0 exacto, y da). Sin presion el "
        "resultado esta confirmado; con presion distinta de 0 se apoya en el "
        "mismo modulo de presion/TP-15 ya validado en el caso de RD60F, pero "
        "sin un caso real propio con presion distinta de cero.",
        "'GPA TP-15 Rounding' y 'API-11.2.4/11.2.2(M) Rounding': redondeos "
        "opcionales de pantalla ya conectados a sus parametros internos "
        "correspondientes. 'P100 Correlation': metodo alterno de GPA TP-15 "
        "que usa un valor de Vapor Pressure @100°F ya conocido en vez de la "
        "tabla por defecto -- validado con caso real.",
        "'Temperature': selector real K/°C/°F/R. 'Pressure'/'Equilibrium "
        "Pressure'/'Atmospheric Pressure' (esta ultima solo en RD60F) Y "
        "'Vapor Pressure @100°F': selector real ABSOLUTO de 11 unidades "
        "(bar(a)/mbar(a)/mmHga/mmH2Oa/inHga/inH2Oa, default bar(a)) -- "
        "confirmado tocando la pantalla real en las 3 pestañas (RONDA 39 "
        "para Pressure/Equilibrium/Atmospheric; RONDA 52 para Vapor "
        "Pressure @100°F, que corrige la nota anterior de RONDA 51 que lo "
        "daba por unidad fija sin confirmar).",
    ]

    def _build_tab_ngl_lpg_wrapper(self, parent, state_key, titulo, descripcion,
                                     input_label, input_default, input_kwarg,
                                     temp_label, temp_default, temp_kwarg,
                                     presion_label, presion_default, presion_kwarg,
                                     evp_label, evp_kwarg, evp_unidad,
                                     atm_kwarg, atm_default,
                                     resultado_principal_kwarg, resultado_principal_label,
                                     f_label, evp_result_kwarg, evp_result_label,
                                     funcion, boton_texto, evp_mode_default="Calculate (TP-15)",
                                     p100_kwarg="p100_valor", p100_unidad="bar(a)"):
        # NOTA (RONDA 52): `p100_unidad` ya NO fija la unidad del campo --
        # desde que se agrego el selector real (ver comentario en la fila
        # "Vapor Pressure @100°F" abajo) la unidad activa es SIEMPRE la del
        # Combobox (`presion_tabla_real`, mismo criterio que el resto de la
        # pestaña); se deja el parametro solo por compatibilidad de firma
        # con los 3 call sites existentes, no tiene efecto en el calculo.
        """Constructor generico para los 3 wrappers combinados de 'E NGL/LPG
        (TP-27)': a diferencia de `_build_tab_ngl_lpg_ctl` (las 6 pantallas
        puras) estos tienen Pressure/Equilibrium Pressure/Conversion ademas
        de valor+Temperature, y devuelven CTL+CPL+CTPL+F+Equilibrium
        Pressure en vez de solo CTL. `atm_kwarg`=None para las 2 pantallas
        metricas (sin ese campo, ver docstring RONDA 15); `atm_kwarg`=
        "atm_psia" solo para RD60F (US)."""
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_NGL_LPG_WRAPPER_COMUN, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        fila = 0

        def _agregar_entry(label, default, width=12):
            nonlocal fila
            lbl = ttk.Label(izq, text=label, wraplength=230)
            lbl.grid(row=fila, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(izq, textvariable=var, width=width)
            entry.grid(row=fila, column=1, padx=6, pady=3)
            fila += 1
            return var, lbl, entry

        valor_input_var, _valor_input_label, _valor_input_entry = _agregar_entry(
            input_label, input_default)

        # Temperature: selector real K/degC/degF/R -- confirmado en vivo
        # (uiautomator, RONDA 39, "API Density @15°C NGL/LPG") que esta
        # pantalla SI tiene el mismo "Unit" Spinner ya usado en el resto de
        # la familia API (antes esta pestaña solo tenia un Entry fijo, sin
        # selector, a diferencia de las 6 pantallas CTL puras de NGL/LPG que
        # ya lo tenian desde antes via `_build_tab_ngl_lpg_ctl`).
        temp_es_f = (temp_kwarg == "observed_temp_f")
        temp_tabla_real = API_TEMPERATURA_A_DEGF if temp_es_f else API_TEMPERATURA_A_DEGC
        ttk.Label(izq, text="Temperature").grid(row=fila, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, fila, temp_tabla_real, valor_default=temp_default,
            unidad_default=("degF" if temp_es_f else "degC"))
        fila += 1

        # Pressure/Equilibrium Pressure/Atmospheric Pressure: selector real
        # ABSOLUTO de 11 unidades (bar(a)/mbar(a)/mmHga/mmH2Oa/inHga/inH2Oa),
        # confirmado en vivo (RONDA 39) tocando el dialogo de edicion de "API
        # Density @15°C NGL/LPG" y "API Rel. Density @60°F NGL/LPG" -- la
        # pantalla real muestra "bar(a)" por defecto en LAS 3 pantallas
        # (incluida RD60F, aunque el motor Python reciba ese valor via un
        # kwarg llamado "pressure_psia"/"atm_psia": la pantalla NUNCA ofrece
        # psia como opcion, siempre bar(a)/derivados, igual que el resto de
        # la familia API con presion "absoluta" -- ver Ethylene/Propylene).
        presion_tabla_real = (API_PRESION_ABS_A_PSIA if presion_kwarg == "pressure_psia"
                               else API_PRESION_ABS_A_BARA)
        ttk.Label(izq, text="Pressure").grid(row=fila, column=0, sticky="w", pady=3)
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, fila, presion_tabla_real, valor_default=presion_default)
        fila += 1

        ttk.Label(izq, text="Equilibrium Pressure Mode", wraplength=230).grid(
            row=fila, column=0, sticky="w", pady=3)
        evp_mode_var = tk.StringVar(value=evp_mode_default)
        ttk.Combobox(izq, textvariable=evp_mode_var,
                     values=["Calculate (TP-15)", "Override"], state="readonly",
                     width=16).grid(row=fila, column=1, padx=6, pady=3, sticky="w")
        fila += 1

        # [RONDA 41 (2026-09-10)] visibilidad condicional real (antes solo
        # una nota de texto "(solo si Mode=Input)" -- corregida ademas a
        # "Override", el nombre real de la opcion en el Combobox de arriba,
        # nunca "Input"): confirmado por el usuario (captura de la pantalla
        # real "API Density @15°C NGL/LPG") que "P100 Correlation"/"Vapor
        # Pressure @100°F" DESAPARECEN cuando Equil. Pressure Mode=Override
        # (solo aplican cuando se esta CALCULANDO la presion de equilibrio
        # via GPA TP-15) y, a la inversa, el valor de "Equilibrium Pressure"
        # solo tiene sentido cuando Mode=Override (se ignora por completo
        # cuando Mode=Calculate, ver `evp_mode` en
        # `_ngl_lpg_wrappers_puro.py`/`_ngl_lpg_wrappers_xll_directo.py`).
        # Los 3 widgets (label+fila EVP, checkbox P100, label+entry P100)
        # se ocultan/muestran con el patron estandar `.grid()`/
        # `.grid_remove()` ligado a un `trace_add` sobre `evp_mode_var`.
        evp_valor_label = ttk.Label(izq, text=f"{evp_label} (solo si Mode=Override)",
                                     wraplength=230)
        evp_valor_label.grid(row=fila, column=0, sticky="w", pady=3)
        evp_valor_var, evp_unidad_var, _evp_tabla_dict = self._agregar_fila_presion(
            izq, fila, presion_tabla_real, valor_default=0.0)
        evp_valor_row_frame = izq.grid_slaves(row=fila, column=1)[0]
        fila += 1

        if atm_kwarg is not None:
            ttk.Label(izq, text="Atmospheric Pressure").grid(row=fila, column=0, sticky="w", pady=3)
            atm_valor_var, atm_unidad_var, _atm_tabla_dict = self._agregar_fila_presion(
                izq, fila, presion_tabla_real, valor_default=atm_default)
            fila += 1
        else:
            atm_valor_var = None
            atm_unidad_var = None

        ttk.Label(izq, text="Conversion", wraplength=230).grid(row=fila, column=0, sticky="w", pady=3)
        conversion_var = tk.StringVar(value="Observed -> Standard")
        ttk.Combobox(izq, textvariable=conversion_var,
                     values=["Observed -> Standard", "Standard -> Observed"],
                     state="readonly", width=18).grid(row=fila, column=1, padx=6, pady=3, sticky="w")
        fila += 1

        round1_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API-11.2.4 Rounding",
                         variable=round1_var).grid(row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1
        round2_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API-11.2.2 Rounding",
                         variable=round2_var).grid(row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1

        # [RONDA 36 (2026-09-09)] "GPA TP-15 Rounding" -- campo separado
        # confirmado por el usuario en las 3 pantallas reales (parametro
        # interno `round_tp15`, ya implementado en `_ngl_lpg_wrappers_puro.py`
        # desde RONDA 33 pero nunca conectado desde esta pestaña ni desde las
        # funciones publicas de `API_MPMS_Tables_1980_2004.py` hasta esta
        # ronda).
        round_tp15_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="GPA TP-15 Rounding",
                         variable=round_tp15_var).grid(row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1

        # [RONDA 36] "P100 Correlation" -- metodo alterno de GPA TP-15 via un
        # valor de Vapor Pressure @100°F ya conocido (en vez del metodo de
        # tabla por defecto). Validado esta ronda con caso real (ver docstring
        # de `api_dens20c_ngl_lpg`/`api_rd60f_ngl_lpg`).
        # [RONDA 37 (2026-09-09)] Renombrado/recorregido: la pantalla real
        # (uiautomator, 3 pantallas) muestra literalmente "P100 Correlation"
        # como un Switch booleano (`function_input_boolean`, valores 0/1
        # simples) -- NO un Combobox de texto "Table (default)"/"Vapor
        # Pressure @100°F" como se habia rotulado antes (ese nombre/formato
        # era invencion de RONDA 36, el comportamiento interno -- que kwarg
        # `p100_correlacion` recibe -- ya era correcto, solo la etiqueta y
        # el tipo de widget no coincidian con la pantalla real).
        p100_correlacion_var = tk.BooleanVar(value=False)
        p100_check = ttk.Checkbutton(izq, text="P100 Correlation",
                                      variable=p100_correlacion_var)
        p100_check.grid(row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1
        # [RONDA 52 (2026-09-14)] "Vapor Pressure @100°F" SI tiene selector
        # real de unidad -- confirmado en vivo (uiautomator) en las 3
        # pantallas ("API Density @15°C/@20°C NGL/LPG" y "API Rel. Density
        # @60°F NGL/LPG"): al tocar el campo (con P100 Correlation
        # activado) se abre el MISMO dialogo "Unit" Spinner de 11 unidades
        # absolutas ya usado por Pressure/Equilibrium Pressure/Atmospheric
        # Pressure en esta misma pestaña (bar(a)/mbar(a)/mmHga/mmH2Oa/.../
        # inH2Oa @ 60°F) -- refuta la nota anterior ("sigue con unidad fija,
        # no se confirmo si tiene selector propio"). Reusa `presion_tabla_
        # real` (ya calculada arriba: API_PRESION_ABS_A_PSIA para RD60F,
        # API_PRESION_ABS_A_BARA para las 2 metricas), MISMO criterio que
        # Equilibrium Pressure/Atmospheric Pressure en esta pestaña -- el
        # rango real mostrado en la pantalla (0..173.058476 bar(a) en
        # RD60F) confirma que la unidad nativa interna sigue siendo psia
        # ahi, igual que el resto de esa pantalla.
        p100_valor_label = ttk.Label(izq, text="Vapor Pressure @100°F\n"
                                                 "(solo si Method=VP@100°F)", wraplength=230)
        p100_valor_label.grid(row=fila, column=0, sticky="w", pady=3)
        p100_valor_var, p100_unidad_var, p100_tabla_dict = self._agregar_fila_presion(
            izq, fila, presion_tabla_real, valor_default=0.0)
        p100_valor_entry = izq.grid_slaves(row=fila, column=1)[0]

        # [RONDA 41] toggle real de visibilidad ligado a evp_mode_var -- ver
        # comentario en la fila "Equilibrium Pressure Mode" mas arriba para
        # la evidencia. `.grid()` sin argumentos restaura la MISMA posicion
        # que tenia el widget antes de `.grid_remove()` (comportamiento
        # estandar de Tkinter, no hace falta volver a pasar row/column).
        def _actualizar_visibilidad_evp(*_args):
            calculando_tp15 = evp_mode_var.get().startswith("Calculate")
            if calculando_tp15:
                evp_valor_label.grid_remove()
                evp_valor_row_frame.grid_remove()
                p100_check.grid()
                p100_valor_label.grid()
                p100_valor_entry.grid()
            else:
                evp_valor_label.grid()
                evp_valor_row_frame.grid()
                p100_check.grid_remove()
                p100_valor_label.grid_remove()
                p100_valor_entry.grid_remove()

        evp_mode_var.trace_add("write", _actualizar_visibilidad_evp)
        _actualizar_visibilidad_evp()

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_ngl_lpg_wrapper(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = [resultado_principal_kwarg, "ctl", "cpl", "ctpl", "f", evp_result_kwarg]
        etiquetas_resultado = {
            resultado_principal_kwarg: resultado_principal_label,
            "ctl": "CTL, Correction for Temperature on Liquid [adimensional]",
            "cpl": "CPL, Correction for Pressure on Liquid [adimensional]",
            "ctpl": "CTPL = CTL x CPL [adimensional]",
            "f": f_label,
            evp_result_kwarg: evp_result_label,
        }
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._ngl_lpg_wrapper_tabs = getattr(self, "_ngl_lpg_wrapper_tabs", {})
        self._ngl_lpg_wrapper_tabs[state_key] = {
            "valor_input_var": valor_input_var, "input_kwarg": input_kwarg,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict, "temp_kwarg": temp_kwarg,
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict, "presion_kwarg": presion_kwarg,
            "evp_mode_var": evp_mode_var, "evp_valor_var": evp_valor_var,
            "evp_unidad_var": evp_unidad_var, "evp_kwarg": evp_kwarg,
            "atm_valor_var": atm_valor_var, "atm_unidad_var": atm_unidad_var,
            "atm_kwarg": atm_kwarg,
            "conversion_var": conversion_var,
            "round1_var": round1_var, "round2_var": round2_var,
            "round_tp15_var": round_tp15_var,
            "p100_correlacion_var": p100_correlacion_var, "p100_valor_var": p100_valor_var,
            "p100_unidad_var": p100_unidad_var, "p100_tabla_dict": p100_tabla_dict,
            "p100_kwarg": p100_kwarg,
            "funcion": funcion, "resultado_principal_kwarg": resultado_principal_kwarg,
            "evp_result_kwarg": evp_result_kwarg, "result_vars": result_vars,
        }

    def _on_calcular_ngl_lpg_wrapper(self, state_key):
        st = self._ngl_lpg_wrapper_tabs[state_key]
        try:
            valor_input = float(st["valor_input_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            temp = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
            presion_unidad = st["presion_unidad_var"].get()
            presion = st["presion_tabla_dict"][presion_unidad](float(st["presion_valor_var"].get()))
            evp_unidad = st["evp_unidad_var"].get()
            evp = st["presion_tabla_dict"][evp_unidad](float(st["evp_valor_var"].get()))
            if st["atm_valor_var"] is not None:
                atm_unidad = st["atm_unidad_var"].get()
                atm = st["presion_tabla_dict"][atm_unidad](float(st["atm_valor_var"].get()))
            else:
                atm = None
            p100_unidad = st["p100_unidad_var"].get()
            p100_valor = st["p100_tabla_dict"][p100_unidad](float(st["p100_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        evp_mode = 2 if st["evp_mode_var"].get().startswith("Calculate") else 1
        conversion = 1 if st["conversion_var"].get().startswith("Observed") else 0
        p100_correlacion = 1 if st["p100_correlacion_var"].get() else 0
        kwargs = {
            st["input_kwarg"]: valor_input, st["temp_kwarg"]: temp,
            st["presion_kwarg"]: presion, st["evp_kwarg"]: evp,
            "equilibrium_pressure_mode": evp_mode, "conversion": conversion,
            "round_11_2_4": 1 if st["round1_var"].get() else 0,
            "round_tp15": 1 if st["round_tp15_var"].get() else 0,
            "p100_correlacion": p100_correlacion, st["p100_kwarg"]: p100_valor,
        }
        # El nombre del segundo flag de rounding difiere entre RD60F
        # (round_11_2_2) y Dens15C/20C (round_11_2_2m) -- se detecta por la
        # presencia de atm_kwarg (solo RD60F lo tiene).
        kwargs["round_11_2_2" if st["atm_kwarg"] is not None else "round_11_2_2m"] = (
            1 if st["round2_var"].get() else 0)
        if st["atm_kwarg"] is not None:
            kwargs[st["atm_kwarg"]] = atm
        try:
            r = st["funcion"](**kwargs)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars[st["resultado_principal_kwarg"]].set(f"{r[st['resultado_principal_kwarg']]:.6f}")
        result_vars["ctl"].set(f"{r['ctl']:.6f}")
        result_vars["cpl"].set(f"{r['cpl']:.6f}")
        result_vars["ctpl"].set(f"{r['ctpl']:.6f}")
        result_vars["f"].set(f"{r['f']:.9f}")
        result_vars[st["evp_result_kwarg"]].set(f"{r[st['evp_result_kwarg']]:.6f}")
        if r.get("fuera_de_rango"):
            result_vars[st["resultado_principal_kwarg"]].set(
                result_vars[st["resultado_principal_kwarg"]].get() + "  [fuera de rango]")

    def _build_tab_api_dens15c_ngl_lpg(self, parent):
        self._build_tab_ngl_lpg_wrapper(
            parent, state_key="dens15c_ngl_lpg", titulo="API Density @15°C NGL/LPG",
            descripcion="API Density @15°C NGL/LPG -- Density Conversion to and from "
                        "15°C and EVP according to API 11.2.4 / GPA TP-27 Tables 53E "
                        "and 54E, API MPMS 11.2.2M and GPA TP-15.",
            input_label="Density [kg/m3]\n(Observed o @15°C segun Conversion)",
            input_default=600.0, input_kwarg="observed_density_kgm3",
            temp_label="Temperature", temp_default=25.0, temp_kwarg="observed_temp_c",
            presion_label="Pressure", presion_default=0.0, presion_kwarg="pressure_bar_g",
            evp_label="Equilibrium Pressure", evp_kwarg="equilibrium_pressure_bar_g",
            evp_unidad="bar(a)", atm_kwarg=None, atm_default=0.0,
            resultado_principal_kwarg="density_15c",
            resultado_principal_label="Density @15°C / Observed [kg/m3]\n(segun Conversion)",
            f_label="Factor de Compresibilidad F [1/bar]",
            evp_result_kwarg="equilibrium_pressure_barg",
            evp_result_label="Equilibrium Pressure [bar(a)]",
            funcion=api_dens15c_ngl_lpg, boton_texto="Calcular (API Density @15°C NGL/LPG)",
            evp_mode_default="Override")

    def _build_tab_api_dens20c_ngl_lpg(self, parent):
        self._build_tab_ngl_lpg_wrapper(
            parent, state_key="dens20c_ngl_lpg", titulo="API Density @20°C NGL/LPG",
            descripcion="API Density @20°C NGL/LPG -- Density Conversion to and from "
                        "20°C and EVP according to API 11.2.4 / GPA TP-27 Tables 59E "
                        "and 60E, API MPMS 11.2.2M and GPA TP-15.",
            input_label="Density [kg/m3]\n(Observed o @20°C segun Conversion)",
            input_default=600.0, input_kwarg="observed_density_kgm3",
            temp_label="Temperature", temp_default=25.0, temp_kwarg="observed_temp_c",
            presion_label="Pressure", presion_default=0.0, presion_kwarg="pressure_bar_g",
            evp_label="Equilibrium Pressure", evp_kwarg="equilibrium_pressure_bar_g",
            evp_unidad="bar(a)", atm_kwarg=None, atm_default=0.0,
            resultado_principal_kwarg="density_20c",
            resultado_principal_label="Density @20°C / Observed [kg/m3]\n(segun Conversion)",
            f_label="Factor de Compresibilidad F [1/bar]",
            evp_result_kwarg="equilibrium_pressure_barg",
            evp_result_label="Equilibrium Pressure [bar(a)]",
            funcion=api_dens20c_ngl_lpg, boton_texto="Calcular (API Density @20°C NGL/LPG)",
            evp_mode_default="Override")

    def _build_tab_api_rd60f_ngl_lpg(self, parent):
        self._build_tab_ngl_lpg_wrapper(
            parent, state_key="rd60f_ngl_lpg", titulo="API Rel. Density @60°F NGL/LPG",
            descripcion="API Rel. Density @60°F NGL/LPG -- Relative Density Conversion "
                        "to and from 60°F and EVP according to API 11.2.4 / GPA TP-27 "
                        "Tables 23E and 24E, API MPMS 11.2 and GPA TP-15.",
            input_label="Relative Density [adimensional]\n(Observed o @60°F segun Conversion)",
            input_default=0.5, input_kwarg="observed_rd",
            temp_label="Temperature", temp_default=110.0, temp_kwarg="observed_temp_f",
            # presion_default/atm_default: ahora en bar(a) (unidad por defecto
            # real de la pantalla, RONDA 39), NO en psia -- 13.78952 bar(a) =
            # 200 psia y 1.0132539 bar(a) = 14.696 psia, MISMOS valores nativos
            # de siempre, solo expresados en la unidad que la app realmente
            # muestra por defecto (confirmado en vivo, "API Rel. Density @60°F
            # NGL/LPG": Pressure=13.78952 bar(a), Atmospheric Pressure=
            # 1.0132539 bar(a)).
            presion_label="Pressure", presion_default=13.78952, presion_kwarg="pressure_psia",
            evp_label="Equilibrium Pressure", evp_kwarg="equilibrium_pressure_psia",
            evp_unidad="bar(a)", atm_kwarg="atm_psia", atm_default=1.0132539,
            resultado_principal_kwarg="rd_60f",
            resultado_principal_label="Rel. Density @60°F / Observed [adimensional]\n(segun Conversion)",
            f_label="Factor de Compresibilidad F [1/psi]",
            evp_result_kwarg="equilibrium_pressure_psia",
            evp_result_label="Equilibrium Pressure [psia]",
            funcion=api_rd60f_ngl_lpg, boton_texto="Calcular (API Rel. Density @60°F NGL/LPG)",
            p100_kwarg="p100_valor_psia", p100_unidad="psia")

    # ===========================================================================
    # "API 11.3.2.1 Ethylene" / "API 11.3.3.2 Propylene" (2026-08-27) -- las 2
    # entradas restantes del menu raiz "API" sin cerrar numericamente. Camino:
    # llamada DIRECTA (ctypes, sin Excel, SIN emulador) al nucleo real dentro
    # de FlowXpert.xll -- ver normas/_ethylene_propylene_xll_directo.py para
    # toda la evidencia de decompilacion/validacion. Ambas devuelven Density;
    # Ethylene agrega Z (compresibilidad), Propylene agrega CTPL y Equilibrium
    # Pressure -- por eso comparten un builder generico con `salidas`
    # configurable (mismo patron ya usado en `_build_tab_ngl_lpg_ctl`).
    # ===========================================================================
    _AYUDA_ETHYLENE_PROPYLENE_COMUN = [
        "Etileno (API MPMS 11.3.2.1): la densidad se obtiene resolviendo (por "
        "Newton-Raphson) una ecuacion de estado tipo Benedict-Webb-Rubin (BWR) "
        "para el volumen molar a la temperatura y presion dadas; la densidad "
        "final es masa_molar/volumen_molar. A ese resultado se le aplica una "
        "correccion empirica por tabla (interpolacion en 2 ejes: 12 valores de "
        "temperatura x 20 de presion) para ajustar el modelo BWR al "
        "comportamiento real medido del etileno. La compresibilidad Z sale de "
        "la ecuacion de gas real: Z = P*M / ((T+459.67)*densidad*R).",
        "Propileno (API MPMS 11.3.3.2): primero se calcula la 'Equilibrium "
        "Pressure' (presion de vapor del liquido a esa temperatura, formula "
        "tipo Antoine: exp(12.5983 - 4015.63/(T[°F]+460.068)) -- solo depende "
        "de T, no de P, como corresponde fisicamente a la presion de vapor de "
        "un liquido puro). Luego la densidad se resuelve por el metodo de la "
        "secante sobre otra ecuacion de estado tipo BWR (con un termino de "
        "correccion exponencial propio). CTPL (Correction for Temperature on "
        "Liquid) es esa densidad dividida por una constante de referencia.",
        "Validado contra la pantalla real de la app (captura de pantalla, no "
        "solo formula): Etileno T=90°F (32.2222°C), P=250 psia (17.2369 "
        "bar(a)) -> Density=21.13020 kg/m3, Z=0.901174. Propileno T=60°F "
        "(15.5556°C), P=200 psia (13.78952 bar(a)) -> Density=523.6218 kg/m3, "
        "CTPL=1.002541, Equilibrium Pressure=9.047929 bar(g).",
        "'Temperature'/'Pressure' de entrada: la pantalla real SI tiene un "
        "selector de unidad (confirmado en vivo, RONDA 39) -- Temperature "
        "ofrece K/°C/°F/R (default °C) y Pressure ofrece 11 unidades "
        "ABSOLUTAS (bar(a)/mbar(a)/mmHga/mmH2Oa/inHga/inH2Oa, default "
        "bar(a); psia NO es opcion), aunque el motor de calculo internamente "
        "trabaja en °F/psia (esta pestaña hace esa conversion en segundo "
        "plano, igual que el resto de la GUI). Rango oficial del manual: "
        "Etileno T entre 65 y 167°F (18.3 a 75°C), P entre 200 y 2100 psia "
        "(13.8 a 144.8 bar(a)).",
        "'API Rounding': switch booleano de la pantalla real (Off/On). Solo "
        "'Off' tiene un caso real de referencia verificado digito a digito -- "
        "'On' se probo sin errores mas no cambio el resultado en el unico "
        "caso probado; no hay un caso real propio que confirme su efecto "
        "exacto en otras condiciones (documentado honesto, no se fabrica).",
        "Nota pendiente (no bloqueante): en Propileno, la pantalla real "
        "rotula 'Equilibrium Pressure' como bar(g) (manometrica) pero el "
        "numero que reproduce el caso real conocido sale de una conversion "
        "DIRECTA psia->bar (sin restar la presion atmosferica, que si "
        "convertiria a verdadera presion manometrica) -- no se determino si "
        "es una convencion propia de FlowXpert o una etiqueta heredada de la "
        "norma; no se inventa la explicacion.",
        "Esta familia (a diferencia de otras normas del proyecto) no tiene "
        "camino de respaldo alternativo: si el motor de calculo real no esta "
        "disponible, estas 2 pestañas fallan con un error explicito en vez de "
        "mostrar un numero sin respaldo.",
    ]

    def _build_tab_ethylene_propylene(self, parent, state_key, descripcion,
                                       funcion, salidas, boton_texto,
                                       temp_default=90.0, presion_default=250.0):
        """Constructor generico para las 2 pantallas de Etileno/Propileno.
        El motor de calculo (normas/API_Ethylene_Propylene_puro.py) trabaja
        en °F/psia (unidades nativas de la formula). RONDA 39 (uiautomator,
        en vivo) confirmo que Temperature Y Pressure SI tienen un selector
        real de unidad en la pantalla (antes se creia que no lo tenian,
        etiqueta fija, ver RONDA 38): Temperature ofrece K/°C/°F/R (mismo
        "Unit" Spinner ya usado en el resto de la familia API, default real
        °C) y Pressure ofrece el selector ABSOLUTO de 11 unidades
        (bar(a)/mbar(a)/mmHga/mmH2Oa/inHga/inH2Oa, default real bar(a) --
        psia NO es una opcion, igual que en NGL/LPG).
        Devuelve density_kg_m3 + `salidas` (lista de tuplas (clave,
        etiqueta, formato) para los campos adicionales que cada una expone:
        Z para Etileno; ctpl/equilibrium_pressure_bar para Propileno).
        `temp_default`/`presion_default`: valor nativo (°F/psia) del caso ya
        validado -- se muestran convertidos a °C/bar(a) en el formulario."""
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text=descripcion, wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Que calcula esta pestaña",
                             self._AYUDA_ETHYLENE_PROPYLENE_COMUN, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        def _fmt_num(v):
            texto = f"{v:.7f}".rstrip("0").rstrip(".")
            return texto if texto else "0"

        temp_c_default = (temp_default - 32.0) / 1.8
        presion_bar_a_default = presion_default * _PSI_A_KPA / 100.0

        ttk.Label(izq, text="Temperature").grid(row=0, column=0, sticky="w", pady=(3, 10))
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, 0, API_TEMPERATURA_A_DEGC, valor_default=_fmt_num(temp_c_default),
            unidad_default="degC")

        ttk.Label(izq, text="Pressure").grid(row=1, column=0, sticky="w", pady=(3, 10))
        presion_valor_var, presion_unidad_var, presion_tabla_dict = self._agregar_fila_presion(
            izq, 1, API_PRESION_ABS_A_PSIA, valor_default=_fmt_num(presion_bar_a_default))

        api_rounding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API Rounding",
                         variable=api_rounding_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(3, 10))

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text=boton_texto, style="Accento.TButton",
                   command=lambda: self._on_calcular_ethylene_propylene(state_key)).pack(
            fill="x", pady=(0, 10))

        claves_resultado = ["density_kg_m3"] + [clave for clave, _et, _fmt in salidas]
        etiquetas_resultado = {"density_kg_m3": "Density [kg/m3]"}
        etiquetas_resultado.update({clave: et for clave, et, _fmt in salidas})
        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        result_vars = self._build_result_labels(result_frame, claves_resultado, etiquetas_resultado)

        self._ethylene_propylene_tabs = getattr(self, "_ethylene_propylene_tabs", {})
        self._ethylene_propylene_tabs[state_key] = {
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict,
            "presion_valor_var": presion_valor_var, "presion_unidad_var": presion_unidad_var,
            "presion_tabla_dict": presion_tabla_dict,
            "api_rounding_var": api_rounding_var, "funcion": funcion,
            "salidas": salidas, "result_vars": result_vars,
        }

    def _on_calcular_ethylene_propylene(self, state_key):
        st = self._ethylene_propylene_tabs[state_key]
        try:
            temp_unidad = st["temp_unidad_var"].get()
            temp_c = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
            presion_unidad = st["presion_unidad_var"].get()
            temp_f = temp_c * 1.8 + 32.0
            presion_psia = st["presion_tabla_dict"][presion_unidad](
                float(st["presion_valor_var"].get()))
            api_rounding = 1 if st["api_rounding_var"].get() else 0
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            r = st["funcion"](temp_f, presion_psia, api_rounding)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        result_vars = st["result_vars"]
        result_vars["density_kg_m3"].set(f"{r['density_kg_m3']:.6f}")
        for clave, _et, fmt in st["salidas"]:
            result_vars[clave].set(fmt.format(r[clave]))
        if r.get("fuera_de_rango"):
            messagebox.showwarning(
                "Fuera de rango",
                "El nucleo real senializo esta entrada como fuera del rango "
                "fisico valido de la correlacion (ver panel de ayuda para los "
                "limites) -- el resultado mostrado es el que el binario real "
                "devuelve de todos modos, igual que hace la app.")

    def _build_tab_api_ethylene(self, parent):
        self._build_tab_ethylene_propylene(
            parent, state_key="ethylene",
            descripcion="API 11.3.2.1 Ethylene -- Density of Ethylene (C2H4) "
                        "according to API MPMS 11.3.2.1.",
            funcion=api_mpms_11_3_2_1_ethylene,
            salidas=[("z", "Compressibility (Z) [adimensional]", "{:.6f}")],
            boton_texto="Calcular (API 11.3.2.1 Ethylene)")

    def _build_tab_api_propylene(self, parent):
        self._build_tab_ethylene_propylene(
            parent, state_key="propylene",
            descripcion="API 11.3.3.2 Propylene -- Density of Propylene "
                        "Liquid according to API MPMS 11.3.3.2.",
            funcion=api_mpms_11_3_3_2_propylene,
            salidas=[("ctpl", "CTPL, Correction for Temperature and Pressure "
                              "on Liquid [adimensional]", "{:.6f}"),
                     ("equilibrium_pressure_bar", "Equilibrium Pressure [bar(g)]", "{:.6f}")],
            boton_texto="Calcular (API 11.3.3.2 Propylene)",
            temp_default=60.0, presion_default=200.0)

    # ===========================================================================
    # GPA-TP15 (RONDA 44, 2026-09-10): pantalla propia confirmada en vivo
    # (uiautomator, AVD flowxpert_rd) bajo la categoria "GPA" del menu raiz
    # -- ver normas/GPA_TP15.py para el detalle completo de decompilacion y
    # los 7 casos reales de validacion.
    # ===========================================================================
    _AYUDA_GPA_TP15 = [
        "'GPA-TP15' -- Equilibrium Vapor Pressure for Natural Gas Liquids "
        "(NGL) according to GPA-TP15: exp(polinomio(RD)/(T+443) + "
        "polinomio(RD)) con 7 filas de coeficientes por rango de densidad "
        "relativa reducida (RD), tabla real extraida a bytes crudos del "
        "binario. CERRADA [CERTAIN] con 7 casos reales nuevos capturados "
        "en vivo -- ver normas/GPA_TP15.py.",
        "Confirmada como pantalla PROPIA del menu raiz (categoria 'GPA', "
        "junto a 'GPA-2172' -- esta ultima aun no implementada). TAMBIEN "
        "se usa como sub-calculo interno de los 3 wrappers combinados de "
        "'E NGL/LPG (TP-27)' (mismo motor Python, sin duplicar codigo).",
        "Caso real: RD=0.6, T=60°F (15.5555556°C), API Rounding=0, P100 "
        "Correlation=0 -> Equilibrium Pressure=1.157104 bar(a). Con P100 "
        "Correlation=1 (Vapor Pres. @100°F=100 psia=6.89476 bar(a)) -> "
        "3.268000 bar(a). Con API Rounding=1 (redondea el resultado a 1 "
        "decimal en psia antes de convertir a la unidad de pantalla) -> "
        "1.158320/3.268116 bar(a) respectivamente.",
        "'Rel. Density @60°F': rango de PANTALLA 0..0.75 (no bloquea el "
        "calculo fuera de el). El dominio FISICO real de la correlacion "
        "es mas angosto (aprox. [0.35,0.676], con un limite de "
        "temperatura que depende de RD) -- fuera de ese dominio, 'Range "
        "Status' muestra 'Out of range' pero el resultado se calcula "
        "igual (con la fila de tabla mas cercana), confirmado con caso "
        "real RD=0.75.",
        "'Vapor Pres. @100°F' solo aplica (y solo se muestra en la "
        "pantalla real) cuando 'P100 Correlation' esta activo.",
    ]

    def _build_tab_gpa_tp15(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="GPA-TP15 -- Equilibrium Vapor Pressure for "
                              "Natural Gas Liquids (NGL) according to GPA-TP15.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_GPA_TP15, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        fila = 0
        ttk.Label(izq, text="Rel. Density @60°F\n(rango de pantalla 0 .. 0.75)",
                  wraplength=230).grid(row=fila, column=0, sticky="w", pady=3)
        rd_var = tk.StringVar(value="0.6")
        ttk.Entry(izq, textvariable=rd_var, width=12).grid(row=fila, column=1, padx=6, pady=3)
        fila += 1

        ttk.Label(izq, text="Temperature").grid(row=fila, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_TEMPERATURA_A_DEGF, valor_default=60.0, unidad_default="degF")
        fila += 1

        round_tp15_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API Rounding",
                         variable=round_tp15_var).grid(
            row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1

        p100_correlacion_var = tk.BooleanVar(value=False)
        p100_check = ttk.Checkbutton(izq, text="P100 Correlation",
                                      variable=p100_correlacion_var)
        p100_check.grid(row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1

        p100_label = ttk.Label(izq, text="Vapor Pres. @100°F\n(solo si P100 Correlation=1)",
                                wraplength=230)
        p100_label.grid(row=fila, column=0, sticky="w", pady=3)
        p100_valor_var, p100_unidad_var, p100_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_PRESION_ABS_A_PSIA, valor_default=100.0)
        p100_valor_row_frame = izq.grid_slaves(row=fila, column=1)[0]
        fila += 1

        def _actualizar_visibilidad_p100(*_args):
            if p100_correlacion_var.get():
                p100_label.grid()
                p100_valor_row_frame.grid()
            else:
                p100_label.grid_remove()
                p100_valor_row_frame.grid_remove()

        p100_correlacion_var.trace_add("write", _actualizar_visibilidad_p100)
        _actualizar_visibilidad_p100()

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text="Calcular (GPA-TP15)", style="Accento.TButton",
                   command=self._on_calcular_gpa_tp15).pack(fill="x", pady=(0, 10))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        ttk.Label(result_frame, text="Equilibrium Pressure").grid(
            row=0, column=0, sticky="w", pady=2)
        evp_valor_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=evp_valor_var,
                  font=("Consolas", 10, "bold")).grid(row=0, column=1, sticky="e", padx=6)
        evp_out_unidad_var = tk.StringVar(value="bar(a)")
        ttk.Combobox(result_frame, textvariable=evp_out_unidad_var,
                     values=[u for u, _f in API_PRESION_ABS_A_PSIA], state="readonly",
                     width=12).grid(row=0, column=2, padx=(4, 0), pady=2)
        range_status_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=range_status_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))

        self._gpa_tp15_state = {
            "rd_var": rd_var,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict,
            "round_tp15_var": round_tp15_var,
            "p100_correlacion_var": p100_correlacion_var,
            "p100_valor_var": p100_valor_var, "p100_unidad_var": p100_unidad_var,
            "p100_tabla_dict": p100_tabla_dict,
            "evp_valor_var": evp_valor_var, "evp_out_unidad_var": evp_out_unidad_var,
            "range_status_var": range_status_var,
            "ultimo_evp_psia": None, "ultimo_oor": False,
        }
        evp_out_unidad_var.trace_add("write", self._actualizar_resultado_gpa_tp15)

    def _on_calcular_gpa_tp15(self):
        st = self._gpa_tp15_state
        try:
            rd = float(st["rd_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            t_f = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
            p100_unidad = st["p100_unidad_var"].get()
            p100_valor_psia = st["p100_tabla_dict"][p100_unidad](
                float(st["p100_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        round_tp15 = 1 if st["round_tp15_var"].get() else 0
        p100_correlacion = 1 if st["p100_correlacion_var"].get() else 0
        try:
            r = calcular_gpa_tp15(rd=rd, t_f=t_f, round_tp15=round_tp15,
                                   p100_correlacion=p100_correlacion,
                                   p100_valor_psia=p100_valor_psia)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if r["status"] != 0 or r["equilibrium_pressure_psia"] is None:
            st["ultimo_evp_psia"] = None
            st["evp_valor_var"].set("-")
            st["range_status_var"].set("Error de calculo (status={})".format(r["status"]))
            return
        st["ultimo_evp_psia"] = r["equilibrium_pressure_psia"]
        st["ultimo_oor"] = r["fuera_de_rango"]
        self._actualizar_resultado_gpa_tp15()

    # ===========================================================================
    # RONDA 46 (2026-09-10): GPA-2172 -- "Calculation of Gross Heating Value,
    # Relative Density, Compressibility and Theoretical Hydrocarbon Liquid
    # Content for Natural Gas Mixtures for Custody Transfer". El nombre del
    # estandar menciona "Liquid Content" pero la funcion REAL de FlowXpert
    # (`FUN_1800deb44`, decompilada y aislada por ctypes) NO lo calcula --
    # sus 21 salidas reales son unicamente Gross/Net Heating Value, Molar
    # Mass, Molar Mass Ratio, Relative Density y Compressibility, para 3
    # bases (Wet/Dry/Saturated). Ver normas/GPA_2172.py para el detalle
    # completo de evidencia (decompilacion + oraculo .xll, barrido de 3000
    # casos aleatorios cerrado a precision de maquina).
    # PENDIENTE HONESTO: la pantalla real de Android para "GPA-2172" NO fue
    # confirmada en vivo en esta ronda (a diferencia de GPA-TP15/ASTM D1550)
    # -- el listado de campos viene del manual oficial (paginas 96-100),
    # [LIKELY] fiel pero no [CERTAIN] hasta abrir la pantalla.
    # ===========================================================================
    _GPA2172_NOMBRE_AGA8_A_TABLA = {
        "Metano": "Metano", "Nitrogeno": "Nitrogeno", "CO2": "CO2", "Etano": "Etano",
        "Propano": "Propano", "Isobutano": "i-Butano", "n-Butano": "n-Butano",
        "Isopentano": "i-Pentano", "n-Pentano": "n-Pentano", "n-Hexano": "n-Hexano",
        "n-Heptano": "n-Heptano", "n-Octano": "n-Octano", "n-Nonano": "n-Nonano",
        "n-Decano": "n-Decano", "Hidrogeno": "Hidrogeno", "Oxigeno": "Oxigeno",
        "CO": "CO", "Agua": "Agua", "H2S": "H2S", "Helio": "Helio", "Argon": "Argon",
    }
    _AYUDA_GPA2172 = [
        "'GPA-2172' -- Calculation of Gross Heating Value, Relative Density, "
        "Compressibility (y, segun el nombre del estandar, Theoretical "
        "Hydrocarbon Liquid Content -- ESA parte NO esta implementada: el "
        "nucleo real de FlowXpert (`FUN_1800deb44`, decompilado y validado "
        "por llamada directa ctypes, sin Excel) solo produce las 21 salidas "
        "de calor/densidad/compresibilidad de mas abajo, ninguna de liquid "
        "content -- documentado honesto, no se fabrica esa salida).",
        "Motor CERRADO [CERTAIN]: 4 variantes reales en el .xll "
        "(`GPA2172_C`/`GPA2172_M` vigentes + `GPA2172_96_C`/`GPA2172_96_M`, "
        "confirmado que estas 2 ultimas son alias de compatibilidad SIN "
        "logica propia, saltan directo a las vigentes). Formulas ajustadas "
        "y validadas contra el oraculo .xll real (3000 casos aleatorios, "
        "editions/sistemas/modos neo-Pentano variados, error maximo "
        "~1e-15, precision de maquina) -- ver normas/GPA_2172.py.",
        "Tablas de propiedades GPA2145 extraidas byte a byte del binario "
        "para las 5 ediciones customary (1989/2000/2003/2009/2016) y las 4 "
        "metricas (2000/2003/2009/2016 -- NO existe edicion 1989 metrica, "
        "confirmado por decompilacion Y por el manual). Confirmado que las "
        "ediciones 2000/2003 (ambos sistemas) NO tienen propiedades de "
        "Hidrogeno/CO/Argon (todas en 0), tal como dice el manual literal.",
        "'neo-Pentane mode' usa el MISMO selector 'Add to iC5'/'Add to nC5'/"
        "'Neglect' que AGA-8/GERG/ISO 6976, pero el PLIEGUE lo hace el motor "
        "propio de GPA_2172.py (parametro neo_pentano_modo de "
        "calcular_gpa2172), NO la funcion compartida AGA_8.aplicar_modo_"
        "neo_pentano -- para 'Add to iC5'/'Add to nC5' dan el mismo numero "
        "(misma operacion matematica), pero para 'Neglect' la funcion "
        "compartida no renormaliza (deja hueco en la suma, pensada para "
        "que el CONSUMIDOR renormalice, como hacen AGA8-DETAIL/AGA-10) "
        "mientras que calcular_gpa2172 exige que los 22 valores crudos "
        "sumen ~100% y renormaliza el internamente -- usar la funcion "
        "compartida para pre-plegar y despues llamar con neo_pentano_"
        "modo=1 fijo (bug real, RONDA 60) hacia que 'Neglect' con "
        "neo-Pentano >~0.01%% fallara con 'composicion invalida' (el total "
        "pre-plegado quedaba en 100-neo, no 100). Corregido: la GUI ahora "
        "pasa la composicion CRUDA (22 valores) + neo_pentano_modo mapeado "
        "de NEO_PENTANO_MODOS, dejando que calcular_gpa2172 haga el pliegue.",
        "PANTALLA CONFIRMADA EN VIVO [CERTAIN, uiautomator, AVD flowxpert_rd, "
        "RONDA 54, 2026-09-16]: categoria 'GPA' -> 'GPA-2172' junto a "
        "'GPA-TP15', tal como esperaba el manual. Composicion: mismo grid de "
        "21+neo-Pentano que el resto de la app (la pantalla real la presenta "
        "como un registro de libreria editable con nombre + resumen, aqui se "
        "usa el mismo grid de entradas del resto del proyecto, decision de "
        "diseño ya establecida, no un hueco). 'Edition' (etiqueta real en "
        "pantalla: 'GPA-2145 Edition'): RONDA 54 (sin `pm clear`, leyendo un "
        "dump no reseteado) concluyo default '2003' para Metric, dando por "
        "cerrado el campo. RONDA 59 (con `pm clear` + checked=\"true\" real en "
        "el dropdown, mismo metodo de RONDA 55) corrigio: el default real de "
        "fabrica es 'GPA2145-00 (2000)' tanto en Customary (clave 2 de "
        "GPA2172_EDICIONES_C) como en Metric (clave 1 de GPA2172_EDICIONES_M, "
        "NO la clave 2 = '2003' que asumia RONDA 54) -- confirmado con 4 "
        "capturas independientes (fresh + dropdown, 2 visitas separadas a la "
        "pestaña Metric) siempre mostrando '2000' sin tocar el campo. "
        "Corregido el default de la GUI para no depender de un mismo indice "
        "numerico compartido entre sistemas. 'neo-Pentane "
        "Mode': default real de pantalla es 'Add to nC5' (el codigo comparte "
        "default 'Add to iC5' con el resto de la app -- ver "
        "_build_composicion_grid_con_neo -- se sobreescribe aqui a 'Add to "
        "nC5' solo en esta pestaña). Resultados: los 7 campos x 3 bases (Wet/"
        "Dry/Saturated) confirmados 1 a 1 contra la pantalla real (la app los "
        "muestra en una lista vertical Wet->Dry->Saturated en vez de una "
        "tabla de 3 columnas, presentacion distinta, mismos campos/unidades/"
        "orden) -- unidades MJ/m3, kg/kmol, adimensional, adimensional, "
        "adimensional, MJ/kg, MJ/m3 en Metric, todas confirmadas. 2 CASOS "
        "REALES capturados en pantalla (composicion 'Default' del proyecto y "
        "un gas humedo con Agua 15%, edicion 2003) validados 1 a 1 contra "
        "normas/GPA_2172.py: 16/16 valores coinciden a la precision mostrada "
        "en pantalla (6 cifras) -- el motor sube de [CERTAIN via oraculo "
        ".xll] a [CERTAIN via oraculo + 2 casos reales de pantalla].",
    ]

    def _build_tab_gpa2172(self, parent, sistema):
        es_c = sistema == "C"
        ediciones = GPA2172_EDICIONES_C if es_c else GPA2172_EDICIONES_M
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        titulo_sis = "Customary (US)" if es_c else "Metric"
        ttk.Label(outer, text=f"GPA-2172 ({titulo_sis}) -- Gross Heating Value, "
                              "Relative Density and Compressibility for Natural "
                              "Gas Mixtures for Custody Transfer.",
                  wraplength=820).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_GPA2172, wraplength=800).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        comp_frame = ttk.LabelFrame(cols, text="Composition (mol %)", padding=10)
        comp_frame.grid(row=0, column=0, sticky="n", padx=(0, 10))
        entradas, neo_var, modo_var = self._build_composicion_grid_con_neo(
            comp_frame, self.EJEMPLO_GAS_NATURAL)
        # RONDA 55 (corrige RONDA 54): el default real de pantalla, confirmado
        # con `pm clear` (reset de fabrica) + verificacion del atributo
        # checked="true" en el dropdown real (no solo el texto de resumen,
        # que en RONDA 54 resulto ser un valor de prueba persistido de una
        # sesion anterior, no el default de fabrica -- FlowXpert recuerda el
        # ultimo valor usado por pantalla entre sesiones), es "Neglect" --
        # NI "Add to nC5" (RONDA 54) NI "Add to iC5" (default compartido de
        # _build_composicion_grid_con_neo). Confirmado igual en Customary y
        # Metric. Ver docstring de normas/GPA_2172.py para el detalle
        # completo, incluyendo que esto tampoco coincide con el manual
        # oficial (que documenta "Add to i-Pentane" como default de fabrica
        # de fxGPA2172_C/_M) -- se prioriza el comportamiento real de la app.
        modo_var.set("Neglect")

        opciones_frame = ttk.LabelFrame(cols, text="Opciones", padding=10)
        opciones_frame.grid(row=0, column=1, sticky="n", padx=(0, 10))
        ttk.Label(opciones_frame, text="Edition").grid(row=0, column=0, sticky="w", pady=3)
        etiquetas_edicion = {n: etq for n, (_t, _p, _b, _w, etq) in ediciones.items()}
        # RONDA 59 (corrige RONDA 54): el default real de pantalla, confirmado
        # en vivo con `pm clear` (reset de fabrica) + verificacion del
        # atributo checked="true" en el dropdown real (NO solo el texto de
        # resumen de un dump viejo), es DISTINTO por sistema pese a que antes
        # se usaba el mismo indice numerico "2" para ambos: Customary real =
        # "GPA2145-00 (2000)" (indice 2 de _EDICIONES_C, coincide con el
        # codigo previo, sin cambio) pero Metric real = "GPA2145-00 (2000)"
        # TAMBIEN (indice 1 de _EDICIONES_M, NO indice 2 = "2003" que tenia
        # el codigo previo por el hardcodeo compartido -- "indice 2" da 2000
        # en Customary y 2003 en Metric, dos años DISTINTOS, coincidencia
        # numerica sin diseño real detras). Corregido con default EXPLICITO
        # por sistema. Ver docstring _AYUDA_GPA2172 para el detalle completo.
        _default_edicion_idx = {"C": 2, "M": 1}
        edicion_var = tk.StringVar(
            value=etiquetas_edicion[_default_edicion_idx[sistema]])
        ttk.Combobox(opciones_frame, textvariable=edicion_var,
                     values=[etiquetas_edicion[k] for k in sorted(etiquetas_edicion)],
                     state="readonly", width=20).grid(row=0, column=1, pady=3, padx=6)

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=2, sticky="n")
        ttk.Button(right_col, text=f"Calcular (GPA-2172 {sistema})",
                   style="Accento.TButton",
                   command=lambda: self._on_calcular_gpa2172(sistema)).pack(
            fill="x", pady=(0, 10))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="both", expand=True)
        unidad_vol = "Btu/ft3" if es_c else "MJ/m3"
        unidad_masa = "lbm/lbmol" if es_c else "kg/kmol"
        unidad_ghv_masa = "Btu/lbm" if es_c else "MJ/kg"
        campos = [
            ("ghv_vol", f"Gross Heating Value ({unidad_vol})"),
            ("molar_mass", f"Molar Mass ({unidad_masa})"),
            ("molar_mass_ratio", "Molar Mass Ratio (ISG)"),
            ("rel_density", "Relative Density (RRD)"),
            ("compresibilidad", "Compressibility (Z)"),
            ("ghv_mass", f"Gross Heating Value ({unidad_ghv_masa})"),
            ("nhv_vol", f"Net Heating Value ({unidad_vol})"),
        ]
        ttk.Label(result_frame, text="").grid(row=0, column=0)
        ttk.Label(result_frame, text="Wet", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=1, padx=4)
        ttk.Label(result_frame, text="Dry", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=2, padx=4)
        ttk.Label(result_frame, text="Saturated", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=3, padx=4)
        valor_vars = {}
        for i, (clave, etiqueta) in enumerate(campos):
            ttk.Label(result_frame, text=etiqueta).grid(row=i + 1, column=0, sticky="w", pady=1)
            valor_vars[clave] = {}
            for j, base in enumerate(("wet", "dry", "sat")):
                v = tk.StringVar(value="-")
                ttk.Label(result_frame, textvariable=v, font=("Consolas", 9)).grid(
                    row=i + 1, column=j + 1, padx=4, pady=1)
                valor_vars[clave][base] = v
        status_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=status_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=len(campos) + 1, column=0, columnspan=4, sticky="w", pady=(6, 0))

        state = {
            "entradas": entradas, "neo_var": neo_var, "modo_var": modo_var,
            "edicion_var": edicion_var, "etiquetas_edicion": etiquetas_edicion,
            "valor_vars": valor_vars, "status_var": status_var,
        }
        if es_c:
            self._gpa2172_c_state = state
        else:
            self._gpa2172_m_state = state

    def _on_calcular_gpa2172(self, sistema):
        es_c = sistema == "C"
        st = self._gpa2172_c_state if es_c else self._gpa2172_m_state
        try:
            comp_pct = {n: float(v.get()) for n, v in st["entradas"].items()}
            neo_pct = float(st["neo_var"].get())
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        modo = st["modo_var"].get()
        # GPA_2172.py tiene su PROPIO mecanismo de plegado de neo-Pentano
        # (calcular_gpa2172, parametro neo_pentano_modo), distinto del de
        # AGA_8.aplicar_modo_neo_pentano -- ver docstring de calcular_gpa2172:
        # espera la composicion CRUDA de 22 valores (21 componentes + neo-
        # Pentano como ultima entrada) sumando ~100 en total, y hace el
        # pliegue/renormalizacion el mismo. Pre-plegar aca con la funcion de
        # AGA_8.py (que en "Neglect" NO renormaliza, solo quita neo del
        # dict) y despues llamar con neo_pentano_modo=1 fijo hacia dejaba el
        # total en (100-neo) en vez de 100, lo que el chequeo interno de
        # calcular_gpa2172 (tolerancia 0.01%) rechazaba como "composicion
        # invalida" para cualquier neo-Pentano > ~0.01% en modo "Neglect".
        suma_cruda = sum(comp_pct.values()) + neo_pct
        if abs(suma_cruda - 100.0) > 0.01:
            messagebox.showerror(
                "Composicion invalida",
                f"La composicion (21 componentes + neo-Pentano) suma "
                f"{suma_cruda:.4f}%, no 100%. Revisa los 21 campos + neo-Pentano.")
            return
        comp22 = [0.0] * 22
        for nombre_aga8, nombre_tabla in self._GPA2172_NOMBRE_AGA8_A_TABLA.items():
            idx = ORDEN_TABLA_GPA2145.index(nombre_tabla)
            comp22[idx] = comp_pct.get(nombre_aga8, 0.0) / 100.0
        comp22[21] = neo_pct / 100.0
        neo_pentano_modo = NEO_PENTANO_MODOS.index(modo) + 1
        etiqueta_sel = st["edicion_var"].get()
        ediciones = GPA2172_EDICIONES_C if es_c else GPA2172_EDICIONES_M
        edicion_num = next(n for n, (_t, _p, _b, _w, etq) in ediciones.items() if etq == etiqueta_sel)
        try:
            r = calcular_gpa2172(comp22, edicion=edicion_num, neo_pentano_modo=neo_pentano_modo, sistema=sistema)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if r.status != 0:
            st["status_var"].set(f"Status={r.status} (0=OK, 1=fuera de rango, 3=composicion)")
            for clave_dict in st["valor_vars"].values():
                for v in clave_dict.values():
                    v.set("-")
            return
        st["status_var"].set("")
        for clave, base_map in st["valor_vars"].items():
            for base_nombre, resultado in (("wet", r.wet), ("dry", r.dry), ("sat", r.sat)):
                base_map[base_nombre].set(f"{getattr(resultado, clave):.6g}")

    def _actualizar_resultado_gpa_tp15(self, *_args):
        st = getattr(self, "_gpa_tp15_state", None)
        if not st or st.get("ultimo_evp_psia") is None:
            return
        unidad = st["evp_out_unidad_var"].get()
        factor_psia_por_unidad = st["p100_tabla_dict"][unidad](1.0)
        valor_en_unidad = st["ultimo_evp_psia"] / factor_psia_por_unidad
        st["evp_valor_var"].set(f"{valor_en_unidad:.6f}")
        st["range_status_var"].set("Out of range" if st["ultimo_oor"] else "")

    # ===========================================================================
    # RONDA 45 (2026-09-10): ASTM D1550 (Butadieno) -- 2 pantallas propias
    # confirmadas EN VIVO bajo la categoria "ASTM" del menu raiz. `RD60`
    # reusa el mismo nucleo de `api_mpms_11_2_2` como sub-paso de
    # compresibilidad (confirmado por decompilacion directa, mismo patron
    # ya establecido por GPA-TP15/11.2.2 en RONDA 44). Ver
    # normas/ASTM_D1550.py para la evidencia completa (casos reales,
    # nivel de certeza y el pendiente honesto documentado para presion
    # absoluta <0.01psig).
    # ===========================================================================
    _AYUDA_ASTM_D1550_CTL = [
        "'ASTM D1550 CTL' -- Correction Factor for Temperature (CTL) de "
        "Butadieno a 60°F, segun ASTM D1550-94 (Reapproved 2005), Tabla 2. "
        "Interpolacion bilineal PURA sobre una tabla real de 14 filas (RD@60°F "
        "0.621-0.634) x 121 columnas (T -10..110°F), extraida a bytes crudos "
        "del binario -- SIN iteracion, SIN dependencia de otra norma. "
        "CERRADA [CERTAIN]: 400 casos aleatorios validados a precision de "
        "maquina (diff=0.0) contra el nucleo real, mas 3 casos reales "
        "capturados en vivo -- ver normas/ASTM_D1550.py.",
        "Ejemplo: RD@60°F=0.63, T=60°F -> CTL=1.000000 (T=60°F es la "
        "temperatura de referencia, CTL=1 para cualquier densidad). "
        "RD@60°F=0.625, T=30°F -> CTL=1.032000.",
        "'Rel. Density @60°F': rango de PANTALLA 0..0.75 (no bloquea el "
        "calculo fuera de el). El dominio FISICO real de la tabla es mas "
        "angosto (0.621-0.634 x -10..110°F) -- fuera de ese dominio (o si "
        "el CTL resultante se sale de 0.941-1.074), 'Range Status' muestra "
        "'Out of range' pero el resultado se calcula igual (recortado al "
        "limite mas cercano), confirmado con caso real RD@60°F=0.70, "
        "T=30°F -> CTL=1.031000, Range Status='Out of range'.",
    ]
    _AYUDA_ASTM_D1550_RD60 = [
        "'ASTM D1550 Rel. Density @60F' -- convierte densidad relativa "
        "OBSERVADA (a T, P) a densidad relativa a 60°F, segun ASTM D1550, "
        "Tabla 1. Itera (hasta 20 pasos) la relacion RD_obs = RD60 x "
        "CTL(RD60,T) x CPL(RD60,T,P) -- CONFIRMADO por decompilacion "
        "directa que el factor de compresibilidad (F, CPL) se calcula "
        "llamando LITERALMENTE al mismo nucleo que 'API MPMS 11.2.2' "
        "(pantalla 'API 11.2/12.2'), tal como cita el manual oficial "
        "('the compressibility factor is calculated in accordance with "
        "API MPMS 11.2.2:1984'). CERRADO [CERTAIN] para presion absoluta "
        ">=0.01psig (cubre el 100% del uso realista de la pantalla, rango "
        "-10..2500psig) -- ver normas/ASTM_D1550.py para el detalle "
        "completo, incluido un pendiente honesto (sin caso real, sin "
        "formula confiable decompilada) para presion practicamente 0.",
        "4 casos reales capturados en vivo: (1) RD_obs=0.63, T=60°F, "
        "P=100psig, Rounding=0 -> RD60=0.629204, CPL=1.001266. (2) igual "
        "con Rounding=1 -> RD60=0.629182, CPL=1.001300. (3) RD_obs=0.63, "
        "T=30°F, P=100psig, Rounding=0 -> Status='No convergence' (el "
        "solver real NO converge para esta combinacion -- reproducido "
        "exacto por este porte). (4) RD_obs=0.63, T=60°F, P=50bar(g) "
        "(=725.19psig), Rounding=0 -> RD60=0.624181, CPL=1.009322.",
        "'Status' solo aparece en pantalla cuando NO es OK (ej. 'No "
        "convergence' tras 20 iteraciones sin converger) -- en los casos "
        "OK el campo queda oculto, igual que en la app real.",
        "'Pressure': selector real de presion MANOMETRICA (bar(g)/mbar(g)/"
        "mmHgg/mmH2Og/... -- NO absoluta), rango de pantalla -10..2500psig "
        "(=-0.689476..172.369 bar(g)), default 100psig.",
        "'Compressibility [1/psi]' (resultado): CONFIRMADO en vivo (RONDA "
        "54, uiautomator, AVD flowxpert_rd) que la pantalla real SI abre un "
        "selector de unidad al tocar este campo (Spinner con 5 opciones: "
        "1/Pa, 1/kPa, 1/MPa, 1/psi, 1/bar) -- igual que otros resultados de "
        "la app real (ej. 1983 Sup.Calorific Val.). Por decision de producto "
        "ya establecida (ver memoria 'feedback-unidades-en-cada-campo-"
        "numerico'), este proyecto NO agrega selectores de unidad en "
        "campos de RESULTADO/SALIDA aunque la app real los tenga -- se "
        "deja fijo en 1/psi (unidad nativa del nucleo), sin cambio de "
        "codigo, la etiqueta fija YA era correcta.",
    ]

    # ===========================================================================
    # RONDA 47 (2026-09-10): ASTM D4311M (2009) -- Volume Correction Factor
    # (Ctl) para Asfalto, segun ASTM D4311/D4311M-09 ("Standard Practice for
    # Determining Asphalt Volume Correction to a Base Temperature"). UNICA
    # pantalla real confirmada de toda la familia D4311 (la customary 2009 y
    # las 2 variantes sin sufijo "2015" existen en el binario pero NO tienen
    # pantalla propia en esta version de la app -- ver normas/ASTM_D4311.py
    # para la evidencia completa y el pendiente honesto).
    # ===========================================================================
    _AYUDA_ASTM_D4311M_09_M = [
        "'ASTM D4311M (2009)' -- Volume Correction Factor (CTL) para "
        "Asfalto a la temperatura base, segun ASTM D4311/D4311M-09 "
        "(formula directa del Appendix X1 del estandar, SIN iteracion). "
        "Formula real (confirmada por decompilacion + oraculo `.xll`, 400 "
        "casos aleatorios a precision de maquina): CTL = A*T^2 + B*T + C, "
        "con 2 juegos de constantes segun la densidad caiga por encima o "
        "por debajo de 966 kg/m3 -- ver normas/ASTM_D4311.py para el "
        "detalle completo.",
        "2 casos reales capturados en vivo: (1) Densidad=966kg/m3, "
        "T=15°C (default) -> CTL=1.000000. (2) Densidad=900kg/m3, "
        "T=200°C -> CTL=0.874913.",
        "'Density @15°C': rango REAL de pantalla 850..1200 kg/m3 "
        "(confirmado en vivo -- el manual oficial dice 800..1200, pero la "
        "app y el nucleo matematico real coinciden en 850 como piso, un "
        "hueco real del estandar 2009 entre 800 y 850 kg/m3). Selector de "
        "unidad real: kg/m3, g/cc, lb/ft3.",
        "'Temperature': CORREGIDO en RONDA 54 (2026-09-16, uiautomator, AVD "
        "flowxpert_rd) -- SI tiene selector real de unidad (se habia "
        "asumido fijo en RONDA 47 sin haber tocado el campo en vivo). El "
        "dialogo de edicion real muestra un Spinner 'Unit' con 4 opciones "
        "K/°C/°F/R, nativo °C -- mismo selector que API_TEMPERATURA_A_DEGC "
        "ya usado por API Table-59/60 (2004) y NX-19, reusado aqui sin "
        "duplicar la tabla. Rango de pantalla -25..274.5°C.",
        "El binario tiene ADEMAS 'ASTM_D4311M_09_C' (variante US customary, "
        "API gravity) y 2 funciones sin sufijo ('ASTM_D4311C'/'ASTM_D4311M', "
        "rango extendido, un selector interno de 'constantes originales vs "
        "refinadas') -- NINGUNA de las 3 tiene pantalla propia confirmada en "
        "esta version de la app (busqueda completa de la categoria 'ASTM', "
        "sin scroll pendiente). Quedan expuestas como funciones Python "
        "puras (`astm_d4311_09_c`/`astm_d4311_c`/`astm_d4311_m`) validadas "
        "por decompilacion + oraculo, sin pestaña de GUI dedicada.",
    ]

    def _build_tab_astm_d1550_ctl(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ASTM D1550 CTL -- Correction Factor for Temperature of "
                              "Butadiene at 60°F according to ASTM D1550.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_ASTM_D1550_CTL, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        fila = 0
        ttk.Label(izq, text="Rel. Density @60°F\n(rango de pantalla 0 .. 0.75)",
                  wraplength=230).grid(row=fila, column=0, sticky="w", pady=3)
        rd_var = tk.StringVar(value="0.63")
        ttk.Entry(izq, textvariable=rd_var, width=12).grid(row=fila, column=1, padx=6, pady=3)
        fila += 1

        ttk.Label(izq, text="Temperature").grid(row=fila, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_TEMPERATURA_A_DEGF, valor_default=60.0, unidad_default="degF")
        fila += 1

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text="Calcular (ASTM D1550 CTL)", style="Accento.TButton",
                   command=self._on_calcular_astm_d1550_ctl).pack(fill="x", pady=(0, 10))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        ttk.Label(result_frame, text="CTL").grid(row=0, column=0, sticky="w", pady=2)
        ctl_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=ctl_var,
                  font=("Consolas", 10, "bold")).grid(row=0, column=1, sticky="e", padx=6)
        range_status_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=range_status_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self._astm_d1550_ctl_state = {
            "rd_var": rd_var,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict,
            "ctl_var": ctl_var, "range_status_var": range_status_var,
        }

    def _on_calcular_astm_d1550_ctl(self):
        st = self._astm_d1550_ctl_state
        try:
            rd = float(st["rd_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            t_f = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            r = astm_d1550_ctl(rd60=rd, t_f=t_f)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        st["ctl_var"].set(f"{r['ctl']:.6f}")
        st["range_status_var"].set("Out of range" if r["fuera_de_rango"] else "")

    def _build_tab_astm_d1550_rd60(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ASTM D1550 Rel. Density @60F -- Relative Density of "
                              "Butadiene at 60°F according to ASTM D1550.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_ASTM_D1550_RD60, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        fila = 0
        ttk.Label(izq, text="Relative Density\n(observada, rango de pantalla 0 .. 1.0)",
                  wraplength=230).grid(row=fila, column=0, sticky="w", pady=3)
        rd_obs_var = tk.StringVar(value="0.63")
        ttk.Entry(izq, textvariable=rd_obs_var, width=12).grid(row=fila, column=1, padx=6, pady=3)
        fila += 1

        ttk.Label(izq, text="Temperature").grid(row=fila, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_TEMPERATURA_A_DEGF, valor_default=60.0, unidad_default="degF")
        fila += 1

        ttk.Label(izq, text="Pressure").grid(row=fila, column=0, sticky="w", pady=3)
        p_valor_var, p_unidad_var, p_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_PRESION_GAUGE_A_PSIG, valor_default=6.89476,
            unidad_default="bar(g)")
        fila += 1

        round_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(izq, text="API Rounding",
                         variable=round_var).grid(
            row=fila, column=0, columnspan=2, sticky="w", pady=3)
        fila += 1

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text="Calcular (ASTM D1550 RD60)", style="Accento.TButton",
                   command=self._on_calcular_astm_d1550_rd60).pack(fill="x", pady=(0, 10))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        status_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=status_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Label(result_frame, text="Rel. Density @60°F").grid(row=1, column=0, sticky="w", pady=2)
        rd60_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=rd60_var,
                  font=("Consolas", 10, "bold")).grid(row=1, column=1, sticky="e", padx=6)

        ttk.Label(result_frame, text="Compressibility [1/psi]").grid(row=2, column=0, sticky="w", pady=2)
        f_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=f_var,
                  font=("Consolas", 10, "bold")).grid(row=2, column=1, sticky="e", padx=6)

        ttk.Label(result_frame, text="CTL").grid(row=3, column=0, sticky="w", pady=2)
        ctl_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=ctl_var,
                  font=("Consolas", 10, "bold")).grid(row=3, column=1, sticky="e", padx=6)

        ttk.Label(result_frame, text="CPL").grid(row=4, column=0, sticky="w", pady=2)
        cpl_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=cpl_var,
                  font=("Consolas", 10, "bold")).grid(row=4, column=1, sticky="e", padx=6)

        astm_range_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=astm_range_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(6, 0))
        mpms_range_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=mpms_range_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(2, 0))

        self._astm_d1550_rd60_state = {
            "rd_obs_var": rd_obs_var,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict,
            "p_valor_var": p_valor_var, "p_unidad_var": p_unidad_var,
            "p_tabla_dict": p_tabla_dict,
            "round_var": round_var,
            "status_var": status_var, "rd60_var": rd60_var, "f_var": f_var,
            "ctl_var": ctl_var, "cpl_var": cpl_var,
            "astm_range_var": astm_range_var, "mpms_range_var": mpms_range_var,
        }

    def _on_calcular_astm_d1550_rd60(self):
        st = self._astm_d1550_rd60_state
        try:
            rd_obs = float(st["rd_obs_var"].get())
            temp_unidad = st["temp_unidad_var"].get()
            t_f = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
            p_unidad = st["p_unidad_var"].get()
            p_psig = st["p_tabla_dict"][p_unidad](float(st["p_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        api_rounding = 1 if st["round_var"].get() else 0
        try:
            r = astm_d1550_rd60(rd_obs=rd_obs, t_f=t_f, pressure_psig=p_psig,
                                 api_rounding=api_rounding)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if r["status"] == 3:
            st["status_var"].set("No convergence")
        elif r["status"] != 0:
            st["status_var"].set(f"Error de calculo (status={r['status']})")
        else:
            st["status_var"].set("")
        st["rd60_var"].set(f"{r['rd60']:.6f}")
        st["f_var"].set(f"{r['compressibility']:.6f}")
        st["ctl_var"].set(f"{r['ctl']:.6f}")
        st["cpl_var"].set(f"{r['cpl']:.6f}")
        st["astm_range_var"].set("ASTM Range Status: Out of range" if r["astm_oor"] else "")
        st["mpms_range_var"].set("MPMS Range Status: Out of range" if r["mpms_oor"] else "")

    def _build_tab_astm_d4311m_09_m(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="ASTM D4311M (2009) -- Volume Correction Factor (Ctl) for "
                              "Asphalt according to ASTM D4311/D4311M-09, metric units.",
                  wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion",
                             self._AYUDA_ASTM_D4311M_09_M, wraplength=740).pack(
            fill="x", pady=(0, 10))

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)
        izq = ttk.LabelFrame(cols, text="Entradas", padding=10)
        izq.grid(row=0, column=0, sticky="n", padx=(0, 10))

        fila = 0
        ttk.Label(izq, text="Density @15°C").grid(row=fila, column=0, sticky="w", pady=3)
        dens_valor_var, dens_unidad_var, dens_tabla_dict = self._agregar_fila_presion(
            izq, fila, GASVISC2004_DENSIDAD_A_KGM3, valor_default=966.0,
            unidad_default="kg/m3")
        fila += 1

        ttk.Label(izq, text="Temperature\n(rango de pantalla -25 .. 274.5 °C)",
                  wraplength=230).grid(row=fila, column=0, sticky="w", pady=3)
        temp_valor_var, temp_unidad_var, temp_tabla_dict = self._agregar_fila_presion(
            izq, fila, API_TEMPERATURA_A_DEGC, valor_default=15.0, unidad_default="degC")
        fila += 1

        right_col = ttk.Frame(cols)
        right_col.grid(row=0, column=1, sticky="n")
        ttk.Button(right_col, text="Calcular (ASTM D4311M 2009)", style="Accento.TButton",
                   command=self._on_calcular_astm_d4311m_09_m).pack(fill="x", pady=(0, 10))

        result_frame = ttk.LabelFrame(right_col, text="Resultados", padding=10)
        result_frame.pack(fill="x")
        status_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=status_var, foreground="red",
                  font=("Consolas", 10, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(result_frame, text="CTL").grid(row=1, column=0, sticky="w", pady=2)
        ctl_var = tk.StringVar(value="-")
        ttk.Label(result_frame, textvariable=ctl_var,
                  font=("Consolas", 10, "bold")).grid(row=1, column=1, sticky="e", padx=6)

        self._astm_d4311m_09_m_state = {
            "dens_valor_var": dens_valor_var, "dens_unidad_var": dens_unidad_var,
            "dens_tabla_dict": dens_tabla_dict,
            "temp_valor_var": temp_valor_var, "temp_unidad_var": temp_unidad_var,
            "temp_tabla_dict": temp_tabla_dict,
            "status_var": status_var, "ctl_var": ctl_var,
        }

    def _on_calcular_astm_d4311m_09_m(self):
        st = self._astm_d4311m_09_m_state
        try:
            dens_unidad = st["dens_unidad_var"].get()
            dens_kgm3 = st["dens_tabla_dict"][dens_unidad](float(st["dens_valor_var"].get()))
            temp_unidad = st["temp_unidad_var"].get()
            t_c = st["temp_tabla_dict"][temp_unidad](float(st["temp_valor_var"].get()))
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            r = astm_d4311_09_m(dens15c=dens_kgm3, t_c=t_c)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        if r["status"] != 0:
            st["status_var"].set(f"Input argument out of range (status={r['status']})")
        else:
            st["status_var"].set("")
        st["ctl_var"].set(f"{r['ctl']:.6f}")

    def _build_tab_api2004_table59(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table59_2004",
            descripcion="API Table-59 (2004) -- API MPMS 11.1 Tables 59A/59B/59D, edicion "
                        "2004 (metrico, referencia 20°C). Densidad OBSERVADA (a T, P) -> "
                        "densidad a 20°C, 0 bar(g) (iterativo, hasta 15 iteraciones, incluye "
                        "CPL/factor de compresibilidad F). Usa la misma tabla de constantes "
                        "que Table-53 (2004), solo con temperatura de referencia 20°C en vez "
                        "de 15°C -- ver panel de ayuda.",
            ayuda_items=self._AYUDA_API_2004_TABLE5960_COMUN,
            input_label="Observed Density [kg/m3]", input_default=850.0,
            funcion=api_table59_2004, input_kwarg="observed_density_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=20.0,
            salida_principal_clave="density_20c", salida_principal_label="Density a 20°C, 0 bar(g) [kg/m3]",
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-59, 2004)",
            tiene_presion=True, presion_kwarg="pressure_bar",
            tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    def _build_tab_api2004_table60(self, parent):
        self._build_tab_api_mpms(
            parent, state_key="table60_2004",
            descripcion="API Table-60 (2004) -- API MPMS 11.1 Tables 59A/59B/59D, edicion "
                        "2004 (metrico, referencia 20°C). Densidad a 20°C -> CTPL a T, P "
                        "observadas (requiere una iteracion previa para invertir la "
                        "entrada, luego evaluacion directa). Usa la misma tabla de "
                        "constantes que Table-54 (2004), solo con temperatura de "
                        "referencia 20°C en vez de 15°C -- ver panel de ayuda.",
            ayuda_items=self._AYUDA_API_2004_TABLE5960_COMUN,
            input_label="Density @ 20°C [kg/m3]", input_default=850.0,
            funcion=api_table60_2004, input_kwarg="density_20c_kgm3",
            temp_tabla=API_TEMPERATURA_A_DEGC, temp_native="degC", temp_default=20.0,
            salida_principal_clave=None, salida_principal_label=None,
            alpha_convertir_a_c=False, boton_texto="Calcular (API Table-60, 2004)",
            tiene_presion=True, presion_kwarg="pressure_bar",
            tipo_rounding="bool", rounding_kwarg="api_rounding",
            auto_select_disponible=True)

    # ------------------------------------------------------------------ #
    def _build_tab_aga7(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="AGA-7 (turbinas): conversion de caudal entre condiciones de flujo, "
                              "base y masa.", wraplength=760).pack(anchor="w", pady=(0, 4))
        ttk.Label(outer, text="Formula no confirmada contra FlowXpert.xll -- ABB no implemento "
                              "esta norma en el archivo.",
                  foreground="#b05000", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "Formula (Qb=Qf*(Pf/Pb)*(Tb/Tf)*(Zb/Zf)) confirmada por 2 fuentes independientes: "
            "pagina publica de Kelton y el manual oficial Emerson/ROC800 (que cita los numeros "
            "reales de ecuacion del AGA Report No. 7, ediciones 1985 y 1996).",
            "Es una identidad basica de ley de gas real, no una ecuacion empirica ajustada -- "
            "el riesgo de error es bajo aunque no se haya confirmado contra el binario de ABB. "
            "Ver normas/AGA_7.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))
        self.aga7_entries, self.aga7_result_vars = self._build_caudal_tab(
            outer, on_calcular=self.on_calcular_aga7)

    def on_calcular_aga7(self):
        self._calcular_caudal(self.aga7_entries, self.aga7_result_vars, caudal_base_desde_flujo)

    # ------------------------------------------------------------------ #
    def _build_tab_aga9(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="AGA-9 (medidores ultrasonicos multi-trayecto): usa la misma formula "
                              "de caudal que AGA-7.", wraplength=760).pack(anchor="w", pady=(0, 4))
        ttk.Label(outer, text="Formula no confirmada contra FlowXpert.xll -- ABB no implemento "
                              "esta norma en el archivo.",
                  foreground="#b05000", wraplength=760).pack(anchor="w", pady=(0, 6))
        PanelAyudaColapsable(outer, "Fuente y alcance de la validacion", [
            "AGA-9 no define formula de caudal propia: confirmado por 2 fuentes independientes "
            "(Kelton y el manual Emerson/ROC800, que cita textualmente 'AGA Report No. 9... "
            "Section 7.3, refers the reader to AGA No. 7 for calculations').",
            "Ver normas/AGA_9.py.",
        ], wraplength=740).pack(fill="x", pady=(0, 10))
        self.aga9_entries, self.aga9_result_vars = self._build_caudal_tab(
            outer, on_calcular=self.on_calcular_aga9)

    def on_calcular_aga9(self):
        self._calcular_caudal(self.aga9_entries, self.aga9_result_vars, caudal_base_desde_flujo_AGA9)

    def _build_caudal_tab(self, outer, on_calcular):
        """Widget compartido (solo layout) para AGA-7/AGA-9 -- misma formula,
        pestañas y estado (entries/resultados) completamente separados."""
        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)

        left = ttk.LabelFrame(cols, text="Entradas", padding=10)
        left.grid(row=0, column=0, sticky="n", padx=(0, 10))
        campos = [
            ("Qf", "Caudal en condiciones de flujo", "m3/h", "1000"),
            ("Pf", "Presion de flujo", "kPa", "5000"),
            ("Pb", "Presion base", "kPa", "101.325"),
            ("Tf", "Temperatura de flujo", "K", "288.15"),
            ("Tb", "Temperatura base", "K", "288.7056"),
            ("Zf", "Factor Z de flujo", "-", "0.95"),
            ("Zb", "Factor Z base", "-", "0.998"),
        ]
        entradas = {}
        for i, (key, label, unit, default) in enumerate(campos):
            ttk.Label(left, text=f"{label} [{unit}]", wraplength=220).grid(
                row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(left, textvariable=var, width=12).grid(row=i, column=1, padx=6, pady=3)
            entradas[key] = var
        ttk.Label(left, text="Zf/Zb se calculan con las pestañas AGA-8, GERG-2008 o NX-19, "
                             "no aca.", foreground="gray", wraplength=260).grid(
            row=len(campos), column=0, columnspan=2, sticky="w", pady=(4, 0))
        ttk.Button(left, text="Calcular (Qf -> Qb)", style="Accento.TButton",
                   command=on_calcular).grid(
            row=len(campos) + 1, column=0, columnspan=2, pady=(12, 0), sticky="ew")

        right = ttk.LabelFrame(cols, text="Resultado", padding=10)
        right.grid(row=0, column=1, sticky="n")
        resultados = self._build_result_labels(right, ["Qb"], {"Qb": "Qb [m3/h]"})
        return entradas, resultados

    def _calcular_caudal(self, entradas, resultados, funcion_caudal):
        try:
            Qf = float(entradas["Qf"].get())
            Pf = float(entradas["Pf"].get())
            Pb = float(entradas["Pb"].get())
            Tf = float(entradas["Tf"].get())
            Tb = float(entradas["Tb"].get())
            Zf = float(entradas["Zf"].get())
            Zb = float(entradas["Zb"].get())
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            Qb = funcion_caudal(Qf, Pf, Pb, Tf, Tb, Zf, Zb)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            return
        resultados["Qb"].set(f"{Qb:,.4f}")

    # ------------------------------------------------------------------ #
    @staticmethod
    def _nx19_leer_convertido(entrada):
        """Lee un campo de `_build_tab_nx19` armado con `_agregar_fila_presion`
        (tupla valor_var/unidad_var/tabla_dict) y lo convierte a la unidad
        nativa que espera `nx19_fpv_ghv` (bar(a), degC, MJ/m3 o mole/mole
        segun el campo). Puede lanzar ValueError (numero invalido)."""
        valor_var, unidad_var, tabla_dict = entrada
        return tabla_dict[unidad_var.get()](float(valor_var.get()))

    def on_calcular_nx19_ghv(self):
        try:
            p_bar = self._nx19_leer_convertido(self.nx19_ghv_entries["p_bar"])
            t_degc = self._nx19_leer_convertido(self.nx19_ghv_entries["t_degc"])
            sg = float(self.nx19_ghv_entries["sg"].get())
            ghv = self._nx19_leer_convertido(self.nx19_ghv_entries["ghv"])
            n2 = self._nx19_leer_convertido(self.nx19_ghv_entries["n2"])
            co2 = self._nx19_leer_convertido(self.nx19_ghv_entries["co2"])
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return
        try:
            res = nx19_fpv_ghv(p_bar, t_degc, sg, ghv, n2, co2, self.nx19_ptb_g9_var.get())
        except (ValueError, RuntimeError) as e:
            # ValueError: entrada sin sentido fisico (P<=0, T<=-273.15).
            # RuntimeError: no se pudo ejecutar el emulador real (falta
            # unicorn o el .so). En ambos casos se prefiere ser honesto y
            # no inventar un numero. Ver normas/NX_19.py.
            self.nx19_ghv_result_vars["z"].set("-")
            self.nx19_ghv_result_vars["fpv"].set("-")
            self.nx19_ghv_result_vars["rango_status"].set(f"Fuera de rango del metodo ({e})")
            return
        self.nx19_ghv_result_vars["z"].set(f"{res['z']:.6f}")
        self.nx19_ghv_result_vars["fpv"].set(f"{res['fpv']:.6f}")
        self.nx19_ghv_result_vars["rango_status"].set(
            "Out of range (GHV, P, T o SG fuera del rango valido de la funcion real)"
            if res["fuera_de_rango"] else "OK")


if __name__ == "__main__":
    app = App()
    app.mainloop()
