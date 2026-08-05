# -*- coding: utf-8 -*-
"""
interfaz_calculo_flujo.py
==========================
Interfaz de escritorio (Tkinter) que UNE visualmente los calculos
independientes de la carpeta normas/. Este archivo NO contiene logica de
calculo propia -- solo importa cada norma y construye la ventana.

Normas usadas (cada una ejecutable sola, ver su propio docstring de fuente):
    normas/AGA_3_FLOWXPERT.py    -> caudal por orificio, algoritmo real FlowXpert
    normas/NX_19.py              -> supercompresibilidad NX-19
    normas/AGA_8.py              -> Z y propiedades, ecuacion DETAIL
    normas/GERG_2008.py          -> Z y propiedades, ecuacion GERG-2008
    normas/GERG_2004.py          -> alias de GERG_2008 (Gas) + flash liquido-vapor
    normas/AGA_10.py              -> velocidad del sonido y Fpv (usa AGA_8)
    normas/AGA_7.py               -> conversion de caudal (AGA-9 usa la misma formula)

[COPIA PARA PRODUCCION -- ver NORMAS_AGA_GERG, 2026-08-05] AGA-7/AGA-9
(normas/AGA_7.py, AGA_9.py) SI se incluyen en esta copia. No hay binario de
FlowXpert.xll contra el cual compararlas (ABB no implemento estas 2 normas,
0 coincidencias en 373 exportaciones) -- por eso no llegan al mismo nivel de
evidencia que el resto (comparacion bit a bit contra el dispositivo real).
Lo que SI se hizo: (1) la formula Qb=Qf*(Pf/Pb)*(Tb/Tf)*(Zb/Zf) se deriva
directo de la ley de gas real (PV=ZnRT, conservacion de moles entre
condiciones de flujo y base) y coincide, digito a digito, con 5 fuentes
publicas independientes (Kelton, manual Emerson/ROC800 citando las
ecuaciones reales del AGA Report No. 7 1985/1996, SCADACore, un seminario
tecnico, un articulo de ingenieria); (2) se probo con parametros realistas
de industria (transporte 5-7 MPa, distribucion 0.4-1.5 MPa, -5 a 45 degC) y
una composicion REAL de cromatografo, usando el Z de normas/AGA_8.py (ya
validado) -- los Z bajan con mas presion/menos temperatura como se espera
fisicamente, los factores Qb/Qf (4x a 90x segun la clase de presion) son
del orden que se usa en la industria real, y el round-trip Qf->Qb->Qf da
error 0% o ruido de punto flotante en los 5 casos. Ver normas/AGA_7.py para
el detalle completo.

Pestanas (agrupadas por familia en la barra superior):
    AGA-3 (FlowXpert)      -> caudal por orificio, algoritmo real FlowXpert
                              (ver normas/AGA_3_FLOWXPERT.py).
    NX-19                 -> supercompresibilidad, independiente del flujo.
    AGA-8 / AGA8 GERG / GERG-2008 Gas / GERG-2008 Flash / GERG-2004 Gas /
    GERG-2004 Flash / AGA-10 -> Z, propiedades termodinamicas, equilibrio
                                liquido-vapor, velocidad del sonido y Fpv,
                                independiente del flujo.
    AGA-5                 -> poder calorifico (CV_MASS, CV_VOL), formula real
                             de FlowXpert validada contra caso real (ver
                             normas/AGA_5.py).
    AGA-7 / AGA-9          -> conversion de caudal (base/flujo/masico), ver
                             nota arriba sobre nivel de evidencia.

Requisitos (ver requirements.txt):
    pip install -r requirements.txt
    Ademas requiere el archivo apk_analisis/libFXLibrary.so junto al
    proyecto (motor real de AGA-10 y NX-19, ver normas/_sgerg_emulador.py).

Uso:
    python interfaz_calculo_flujo.py
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tema_focqus import (  # noqa: E402
    aplicar_tema, NAVY_SECUNDARIO, TEXTO_CLARO, FONDO_CLARO,
)
from normas.NX_19 import nx19_fpv_ghv  # noqa: E402
from normas.AGA_8 import (  # noqa: E402
    NOMBRES_COMPONENTES as GAS_NOMBRES_COMPONENTES,
    calcular_propiedades as aga8_calcular_propiedades,
    validar_rango_aga8,
    NEO_PENTANO_MODOS, aplicar_modo_neo_pentano, validar_suma_composicion,
)
from normas.GERG_2008 import calcular_propiedades as gerg2008_calcular_propiedades  # noqa: E402
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
from normas.AGA_3_FLOWXPERT import (  # noqa: E402
    CAMPOS as CAMPOS_FX, RESULTADOS as RESULTADOS_FX,
    calcular_flujo_flowxpert, VISC_CONVERSION, INH2O_A_PSI,
)

# ---------------------------------------------------------------------------
# Conversion de unidades para la pestana "AGA-3 (FlowXpert)". El motor de
# FlowXpert (normas/AGA_3_FLOWXPERT.py) trabaja SIEMPRE en Sistema Ingles
# (US customary) -- ver docstring de ese archivo. Estas son conversiones
# fisicas ESTANDAR (no reversineria: sin incertidumbre), usadas solo para
# que la pestana pueda mostrar/recibir los valores tambien en SI.
# Cada entrada: (unidad_SI, unidad_Ingles, ingles->si, si->ingles)
#
# Constantes con precision completa (no aproximadas a 6-7 cifras como antes,
# 2026-07-20 -- ver hallazgo de Reynolds con 0.31% de diferencia contra el
# caso real, causado por acumulacion de redondeo en estas conversiones):
#   1 psi = 6.894757293168361 kPa EXACTO (de 1 lbf=4.4482216152605 N y
#           1 in=0.0254 m, ambos exactos por definicion).
#   1 lb/ft3 = 16.018463373960138 kg/m3 EXACTO (de 1 lb=0.45359237 kg y
#           1 ft=0.3048 m, ambos exactos por definicion).
#   inH2O -> psi: se reusa INH2O_A_PSI=27.707 de normas/AGA_3_FLOWXPERT.py
#           (la MISMA constante que usa el nucleo real, no una aproximacion
#           propia de la interfaz).
# ---------------------------------------------------------------------------
_PSI_A_KPA = 6.894757293168361
_LBFT3_A_KGM3 = 16.018463373960138
FX_UNIT_CONV = {
    "dP":        ("kPa",   "inH2O",
                  lambda v: (v / INH2O_A_PSI) * _PSI_A_KPA,
                  lambda v: (v / _PSI_A_KPA) * INH2O_A_PSI),
    "P":         ("kPa",   "psia",  lambda v: v * _PSI_A_KPA,        lambda v: v / _PSI_A_KPA),
    "T":         ("degC",  "degF",  lambda v: (v - 32.0) / 1.8,      lambda v: v * 1.8 + 32.0),
    "rho":       ("kg/m3", "lb/ft3", lambda v: v * _LBFT3_A_KGM3,    lambda v: v / _LBFT3_A_KGM3),
    "mu":        ("cP",    "cP",    lambda v: v,                    lambda v: v),
    "K":         ("-",     "-",     lambda v: v,                    lambda v: v),
    "Dr":        ("m",     "in",    lambda v: v * 0.0254,            lambda v: v / 0.0254),
    "alphaD":    ("1/degC", "1/degF", lambda v: v * 1.8,             lambda v: v / 1.8),
    "TrD":       ("degC",  "degF",  lambda v: (v - 32.0) / 1.8,      lambda v: v * 1.8 + 32.0),
    "dr":        ("m",     "in",    lambda v: v * 0.0254,            lambda v: v / 0.0254),
    "alphad":    ("1/degC", "1/degF", lambda v: v * 1.8,             lambda v: v / 1.8),
    "Trd":       ("degC",  "degF",  lambda v: (v - 32.0) / 1.8,      lambda v: v * 1.8 + 32.0),
    "Ploc":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Tloc":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Tcorr":     ("-",     "-",     lambda v: v,                    lambda v: v),
    "Texp":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Dloc":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Dexp":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Fluid":     ("-",     "-",     lambda v: v,                    lambda v: v),
    "DrainHole": ("m",     "in",    lambda v: v * 0.0254,            lambda v: v / 0.0254),
    "Fpwl":      ("-",     "-",     lambda v: v,                    lambda v: v),
    "Edition":   ("-",     "-",     lambda v: v,                    lambda v: v),
}
# Rangos minimo/maximo declarados por FlowXpert para cada campo NUMERICO, en
# unidad NATIVA (Inglesa) -- ver ghidra_aga3_ctor_output.txt. Tloc/Tcorr/Dloc
# no tienen rango numerico declarado en el constructor (solo se validan por
# logica de codigo), por eso no aparecen aca -- ver docstring de
# AGA_3_FLOWXPERT.py, seccion de rangos.
FX_RANGOS = {
    "dP": (0.0, 1000.0), "P": (0.0, 30000.0), "T": (-400.0, 2000.0),
    "rho": (0.0, 200.0), "mu": (0.0, 10.0), "K": (0.0, 10.0),
    "Dr": (0.0, 100.0), "alphaD": (0.0, 1.0), "TrD": (-400.0, 2000.0),
    "dr": (0.0, 100.0), "alphad": (0.0, 1.0), "Trd": (0.0, 150.0),
    "Texp": (-1e8, 1e8), "Dexp": (-1e8, 1e8),
    "DrainHole": (0.0, 100.0), "Fpwl": (0.9, 1.1),
}

# Decimales EXACTOS que muestra la app real de FlowXpert en la pantalla de
# resultados de AGA-3, confirmado leyendo "CAP AGA 3 3.jpeg" campo por campo
# (2026-07-24) -- NO es un formato generico (".4f" o ".6f" para todo), cada
# campo tiene su propia cantidad real: Mass Flow Rate=5, Beta/Cd/Expansion
# Factor/Velocity of Appr.=6, Orifice/Pipe Diameter=4, Upstream/Downstream/
# Recovered Pres./Temp./Dens.=5, Reynolds=0 (entero). Solo aplica en modo SI
# (no hay captura real del modo Ingles para confirmar sus decimales).
FX_DECIMALES_SI = {
    "flujo_masico": 5,
    "beta": 6, "Cd": 6, "factor_expansion": 6, "factor_veloc_aprox": 6,
    "dr_efectivo": 4, "Dr_efectivo": 4,
    "reynolds": 0,
    "P_upstream": 3, "P_downstream": 3, "P_recovered": 3,
    "T_upstream": 5, "T_downstream": 5, "T_recovered": 5,
    "rho_upstream": 5, "rho_downstream": 5, "rho_recovered": 5,
}


def _fx_texto_rango(key, sistema):
    """Texto '(min a max)' con el rango de FX_RANGOS convertido a la unidad
    que se esta mostrando (SI o Ingles). None si el campo no tiene rango
    declarado (Tloc/Tcorr/Dloc) o el rango es tan amplio que no aporta
    (Texp/Dexp, +-1e8)."""
    if key not in FX_RANGOS:
        return None
    minimo, maximo = FX_RANGOS[key]
    if maximo >= 1e8:
        return None
    if sistema == "SI":
        ing_a_si = FX_UNIT_CONV[key][2]
        minimo, maximo = ing_a_si(minimo), ing_a_si(maximo)
    return f"({minimo:.4g} a {maximo:.4g})"
# Unidades que FlowXpert acepta para "Dyn. Viscosity" (selector propio de la
# app, independiente del toggle SI/Ingles). El nucleo consume el valor en cP
# sin ninguna conversion (ver normas/AGA_3_FLOWXPERT.py, seccion "VALIDACION
# REAL" del docstring) -- por eso todos los factores de esta tabla convierten
# HACIA cP, y calcular_flujo_flowxpert() recibe siempre cP ya convertido.
VISC_UNIDADES = [
    ("cP", 1.0),
    ("Pa·s", 1000.0),
    ("poise", 100.0),
    ("kgf·s/m2", 9806.65),
    ("lbm/(ft·s)", VISC_CONVERSION),
]

# Unidades reales encontradas en libFXLibrary.so (Pa/kPa/MPa/psia/bar(a)/
# bar(g)/atm/mmHg/inHg/inH2O para Diff.Pressure y Pressure; degC/degF/Kelvin
# para Temperature; kg/m3/lb/ft3/lbm/ft3 para Density; mm/cm/m/in/ft para
# Pipe/Orifice Diameter). Cada factor convierte HACIA kPa (presion) -- luego
# se reusa FX_UNIT_CONV[key][3] (si_a_ing) para llegar a la unidad nativa de
# cada campo especifico (dP->inH2O, P->psia), evitando una segunda fuente de
# la misma constante. bar(g) es MANOMETRICA (gauge): se suma 101.325 kPa de
# atmosfera estandar para pasarla a absoluta (confirmado con el usuario,
# 2026-07-21 -- no hay campo de presion atmosferica local en esta pestaña).
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
    ("inH2O", lambda v: v * (_PSI_A_KPA / INH2O_A_PSI)),
]
TEMPERATURA_A_DEGF = [
    ("degF", lambda v: v),
    ("degC", lambda v: v * 1.8 + 32.0),
    ("Kelvin", lambda v: (v - 273.15) * 1.8 + 32.0),
]
# Misma fuente que TEMPERATURA_A_DEGF/PRESION_A_KPA (unidades reales
# confirmadas en libFXLibrary.so), pero convirtiendo hacia Kelvin/kPa --
# las unidades que usan directamente las funciones de normas/GERG_2008.py.
TEMPERATURA_A_KELVIN = [
    ("K", lambda v: v),
    ("degC", lambda v: v + 273.15),
    ("degF", lambda v: (v - 32.0) / 1.8 + 273.15),
]
DENSIDAD_A_LBFT3 = [
    ("lb/ft3", lambda v: v),
    ("lbm/ft3", lambda v: v),
    ("kg/m3", lambda v: v / _LBFT3_A_KGM3),
]
LONGITUD_A_IN = [
    ("in", lambda v: v),
    ("mm", lambda v: v / 25.4),
    ("cm", lambda v: v / 2.54),
    ("m", lambda v: v / 0.0254),
    ("ft", lambda v: v * 12.0),
]
FX_RESULT_UNIT_CONV = {
    # lb -> kg exacto: 0.45359237. /3600 s/h.
    "flujo_masico": ("kg/s", "lb/h", lambda v: v * 0.45359237 / 3600.0),
    "dr_efectivo":  ("mm",   "in",   lambda v: v * 25.4),
    "Dr_efectivo":  ("mm",   "in",   lambda v: v * 25.4),
    # Presion/temperatura/densidad proyectadas por toma -- misma conversion
    # fisica (y misma precision) que los campos de entrada P/T/rho en FX_UNIT_CONV.
    "P_upstream":     ("kPa",   "psia",  lambda v: v * _PSI_A_KPA),
    "P_downstream":   ("kPa",   "psia",  lambda v: v * _PSI_A_KPA),
    "P_recovered":    ("kPa",   "psia",  lambda v: v * _PSI_A_KPA),
    "T_upstream":     ("degC",  "degF",  lambda v: (v - 32.0) / 1.8),
    "T_downstream":   ("degC",  "degF",  lambda v: (v - 32.0) / 1.8),
    "T_recovered":    ("degC",  "degF",  lambda v: (v - 32.0) / 1.8),
    "rho_upstream":   ("kg/m3", "lb/ft3", lambda v: v * _LBFT3_A_KGM3),
    "rho_downstream": ("kg/m3", "lb/ft3", lambda v: v * _LBFT3_A_KGM3),
    "rho_recovered":  ("kg/m3", "lb/ft3", lambda v: v * _LBFT3_A_KGM3),
}
# Los 6 campos selectores de AGA-3 FlowXpert (enteros con significado
# categorico, no valores continuos) -- ver docstring de
# normas/AGA_3_FLOWXPERT.py para el detalle de que hace cada opcion.
FX_ENUM_LABELS = {
    "Ploc":    {1: "1 - Aguas arriba", 2: "2 - Aguas abajo"},
    "Tloc":    {1: "1 - Aguas arriba", 2: "2 - Aguas abajo", 3: "3 - Recuperada"},
    "Tcorr":   {1: "1 - Automático (K-1)/K, fórmula potencia", 2: "2 - Exponente propio, fórmula potencia",
                3: "3 - Exponente propio, fórmula lineal"},
    "Dloc":    {1: "1 - Aguas arriba", 2: "2 - Aguas abajo", 3: "3 - Recuperada"},
    "Fluid":   {1: "1 - Gas", 2: "2 - Líquido"},
    "Edition": {1: "1992", 2: "2012"},
}
FX_ENUM_LABELS_INV = {campo: {v: k for k, v in tabla.items()} for campo, tabla in FX_ENUM_LABELS.items()}
# Cada nota separa DOS cosas distintas:
#  - "FlowXpert dice:" -> texto TEXTUAL encontrado en el constructor de
#    FlowXpert.xll (ghidra_aga3_ctor_output.txt), entre comillas, o
#    "(sin descripción propia)" si el campo no tiene ningún texto ahi.
#  - "Confirmado en el código:" -> lo que se verificó rastreando el
#    comportamiento real (no es texto de FlowXpert, es reconstrucción).
FX_ENUM_NOTAS = {
    "Ploc": "FlowXpert dice: (sin descripción propia -- solo el nombre \"Pressure Location\"). "
            "Confirmado en el código: define si dP se resta (1=aguas arriba) o se suma "
            "(2=aguas abajo) para proyectar la otra toma.",
    "Tloc": "FlowXpert dice: \"Temperature location.\" (no enumera qué es 1/2/3). "
            "Confirmado en el código: define desde cuál de las 3 tomas (arriba/abajo/recuperada) "
            "se proyectan las otras 2.",
    "Tcorr": "FlowXpert dice: \"Temperature correction.\" (no enumera valores). "
             "Confirmado en el código (corregido 2026-07-24, la nota anterior estaba mal): "
             "1=fórmula de potencia (razón de presiones) con exponente automático (K-1)/K; "
             "2=la MISMA fórmula de potencia pero con el exponente del campo \"Temperature Exp.\"; "
             "3=fórmula LINEAL (diferencia de presiones, no razón), también con el exponente de "
             "\"Temperature Exp.\" -- 2 y 3 comparten de dónde sale el exponente, pero NO la "
             "fórmula matemática (2 usa potencia, 3 usa diferencia lineal).",
    "Dloc": "FlowXpert dice: \"The density location specifies if and how the density should be "
            "corrected from downstream to upstream conditions.\" (no enumera 1/2/3). "
            "Confirmado en el código: define desde cuál toma (arriba/abajo/recuperada) se proyectan "
            "las otras 2 -- exactamente igual que Tloc. (Nota 2026-07-24: el código fuente tiene "
            "ADEMÁS un chequeo de validación temprano, separado, que compara Dloc==1 contra "
            "Dloc in (2,3) de forma binaria -- ese chequeo NO determina el resultado final, solo "
            "detecta densidades inválidas antes de calcular; las etiquetas de este desplegable ya "
            "no reflejan ese chequeo temprano, reflejan la proyección real de 3 tomas.)",
    "Fluid": "FlowXpert dice: \"Type of Fluid being measured. For liquid the expansion factor is "
             "set to 1, i.e. the fluid is considered to be incompressible.\" -- coincide con el código.",
    "Edition": "FlowXpert dice: \"Year of edition.; 1: 1992; 2: 2012\" -- es el único de los 6 campos "
               "que FlowXpert mismo enumera explícitamente. Confirmado en el código: solo cambia la "
               "fórmula del factor de expansión (Y); el resto del cálculo es igual en ambas ediciones.",
}
# Campos NUMERICOS (no selectores) cuyo valor por defecto (0 o 1) significa
# "sin efecto especial" / "automático", no una categoria -- distinto de los
# 6 campos de FX_ENUM_NOTAS.
FX_NUMERIC_HINT = {
    "Texp": "0=auto", "Dexp": "0=auto", "DrainHole": "0=sin orificio", "Fpwl": "1=sin corrección",
}
FX_NUMERIC_NOTAS = {
    "Texp": "FlowXpert dice: \"...the formula (K-1)/K (isentropic expansion) will be used when the "
            "input value is set to 0, else the input value will be used.\" Default 0.0 = fórmula "
            "automática. Solo se usa si Tcorr=2 o 3.",
    "Dexp": "FlowXpert dice: \"This factor is used when density correction is enabled. The formula "
            "1/K will be used when the input value is set to 0, else the input value will be used.\" "
            "Default 0.0 = usar 1/κ automático.",
    "DrainHole": "FlowXpert dice: \"Drain hole diameter. When input is > 0 then an additional "
                 "correction on the orifice diameter will be applied to account for the drain hole.\" "
                 "Default 0.0 = sin orificio de drenaje (sin corrección).",
    "Fpwl": "FlowXpert dice: \"Local Gravitational Correction Factor for Deadweight Calibrators... "
            "Directly applied on the calculated mass flow rate within each iteration.\" Default "
            "1.0 = factor neutro (no corrige nada, ya que multiplica al caudal).",
}

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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FocQus - Confirmacion de Calculos - AGA3 / ISO 5167")
        self.geometry("1180x760")
        aplicar_tema(self)

        self._fx_unit_actual = "SI"

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

        tab_aga3_fx = ttk.Frame(self.sub_notebook)
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

        self._build_tab_aga3_fx(tab_aga3_fx)
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

        # Agrupacion por familia (tema fisico), no por norma individual --
        # asi el selector no se rompe cuando se agreguen las 5 normas
        # ISO5167 (Orifice/ISA1932/LongRadius/Venturi/VenturiNozzle) que se
        # estan reversando en normas/. Cada valor guarda el FRAME YA
        # CONSTRUIDO (no se reconstruye al cambiar de familia, para no
        # perder lo que el usuario haya escrito en otra familia).
        self._familias = {
            "Orificio ISO 5167 / AGA-3": [
                (tab_aga3_fx, "AGA-3 (FlowXpert)"),
            ],
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
        """Envuelve 'parent' en un Canvas + Scrollbar vertical (mismo patron
        que ya usaba la pestaña Memoria de Calculo) y devuelve el frame
        interno donde va el contenido real. La rueda del mouse solo
        scrollea este canvas mientras el cursor esta encima -- no afecta
        otras pestañas."""
        canvas = tk.Canvas(parent, highlightthickness=0, bg=FONDO_CLARO)
        scroll_y = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        return inner

    def _build_tab_aga3_fx(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

        cols = ttk.Frame(outer)
        cols.pack(fill="both", expand=True)

        left = ttk.LabelFrame(cols, text="Entradas", padding=10)
        left.grid(row=0, column=0, sticky="n", padx=(0, 10))

        unit_frame = ttk.Frame(left)
        unit_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(unit_frame, text="Sistema de unidades:").pack(side="left", padx=(0, 8))
        self.fx_unit_var = tk.StringVar(value="SI")
        ttk.Radiobutton(unit_frame, text="SI", variable=self.fx_unit_var, value="SI",
                         command=self.on_fx_cambiar_unidades).pack(side="left")
        ttk.Radiobutton(unit_frame, text="Ingles (nativo de FlowXpert)", variable=self.fx_unit_var,
                         value="ING", command=self.on_fx_cambiar_unidades).pack(side="left", padx=(8, 0))

        self.fx_entries = {}
        self.fx_unit_labels = {}
        mitad = (len(CAMPOS_FX) + 1) // 2
        CAMPOS_CON_SELECTOR_PROPIO = ("mu", "dP", "P", "T", "rho", "Dr", "dr")
        for i, (key, label, _unidad_nativa, default) in enumerate(CAMPOS_FX):
            if key in CAMPOS_CON_SELECTOR_PROPIO:
                continue  # fila propia, con selector de unidad -- ver mas abajo
            col_base = 0 if i < mitad else 2
            fila = (i if i < mitad else i - mitad) + 1
            si_u, ing_u, _ing_a_si, _si_a_ing = FX_UNIT_CONV[key]
            unidad_mostrada = si_u if self.fx_unit_var.get() == "SI" else ing_u
            texto_lbl = f"{label} [{unidad_mostrada}]"
            if key in FX_NUMERIC_HINT:
                texto_lbl += f" ({FX_NUMERIC_HINT[key]})"
            texto_rango = _fx_texto_rango(key, self.fx_unit_var.get())
            if texto_rango:
                texto_lbl += f" {texto_rango}"
            lbl = ttk.Label(left, text=texto_lbl, wraplength=190)
            lbl.grid(row=fila, column=col_base, sticky="w", pady=2, padx=(0, 4))
            self.fx_unit_labels[key] = lbl
            if key in FX_ENUM_LABELS:
                tabla = FX_ENUM_LABELS[key]
                var = tk.StringVar(value=tabla[int(float(default))])
                # Ancho segun la opcion mas larga de CADA campo (no un numero
                # fijo) para que nunca se trunque texto como el de Tcorr
                # ("2 - Valor explícito (Temperature Exp.)").
                ancho = max(12, max(len(v) for v in tabla.values()) + 2)
                ttk.Combobox(left, textvariable=var, values=list(tabla.values()),
                             width=ancho, state="readonly").grid(
                    row=fila, column=col_base + 1, padx=(0, 14), pady=2, sticky="w")
                self.fx_entries[key] = var
                continue
            valor_default = default
            if self.fx_unit_var.get() == "SI" and key not in FX_ENUM_LABELS:
                # .15g conserva el double completo en la ida y vuelta string<->float
                # (antes .6g truncaba a 6 cifras significativas, ver hallazgo Reynolds 0.31%).
                valor_default = f"{FX_UNIT_CONV[key][2](float(default)):.15g}"
            var = tk.StringVar(value=valor_default)
            ttk.Entry(left, textvariable=var, width=10).grid(
                row=fila, column=col_base + 1, padx=(0, 14), pady=2)
            self.fx_entries[key] = var

        # ------------------------------------------------------------------
        # Campos con selector de unidad PROPIO (no siguen el toggle SI/
        # Ingles de arriba): son los 7 donde FlowXpert realmente ofrece
        # varias unidades -- confirmado leyendo libFXLibrary.so, 2026-07-21.
        # Van en su propia sub-seccion, en una grilla de 3 columnas limpia
        # (Campo | Valor | Unidad), separados del resto para no romper la
        # alineacion de la grilla de 2 columnas de arriba.
        # unidad_default DEBE coincidir con la unidad nativa del campo (la
        # que ya trae el valor default de CAMPOS_FX sin conversion) -- dP y
        # P comparten la misma lista de presion pero cada uno tiene una
        # unidad nativa distinta (inH2O vs psia), por eso no alcanza con
        # "la primera de la lista" para las dos.
        # ------------------------------------------------------------------
        fila_multi = mitad + 1
        frame_multi = ttk.LabelFrame(
            left, text="Campos con varias unidades (elegir antes de calcular)", padding=(10, 6))
        frame_multi.grid(row=fila_multi, column=0, columnspan=4, sticky="ew", pady=(12, 0))

        CAMPOS_UNIDAD_PROPIA = {
            "mu":  (VISC_UNIDADES, "cP"),
            "dP":  (PRESION_A_KPA, "inH2O"),
            "P":   (PRESION_A_KPA, "psia"),
            "T":   (TEMPERATURA_A_DEGF, "degF"),
            "rho": (DENSIDAD_A_LBFT3, "lb/ft3"),
            "Dr":  (LONGITUD_A_IN, "in"),
            "dr":  (LONGITUD_A_IN, "in"),
        }
        self.fx_unidad_propia_var = {}
        for fila, (key, (unidades, unidad_default)) in enumerate(CAMPOS_UNIDAD_PROPIA.items()):
            _, _label_campo, _, _default_campo = next(c for c in CAMPOS_FX if c[0] == key)
            ttk.Label(frame_multi, text=_label_campo, wraplength=170).grid(
                row=fila, column=0, sticky="w", pady=2, padx=(0, 8))
            var = tk.StringVar(value=_default_campo)
            entry = ttk.Entry(frame_multi, textvariable=var, width=11)
            entry.grid(row=fila, column=1, padx=(0, 8), pady=2, sticky="w")
            unidad_var = tk.StringVar(value=unidad_default)
            ttk.Combobox(frame_multi, textvariable=unidad_var, values=[u for u, _ in unidades],
                         width=10, state="readonly").grid(row=fila, column=2, pady=2, sticky="w")
            if key == "mu":
                self.fx_mu_var = var
                self.fx_mu_unidad_var = unidad_var
            else:
                self.fx_entries[key] = var
                self.fx_unidad_propia_var[key] = unidad_var

        ttk.Label(frame_multi, text="(unidades confirmadas contra libFXLibrary.so, no adivinadas)",
                  foreground="gray", font=("Segoe UI", 7)).grid(
            row=len(CAMPOS_UNIDAD_PROPIA), column=0, columnspan=3, sticky="w", pady=(6, 0))

        fila_boton = fila_multi + 1
        ttk.Button(left, text="Calcular (FlowXpert)", style="Accento.TButton",
                   command=self.on_calcular_fx).grid(
            row=fila_boton, column=0, columnspan=4, pady=(14, 0), sticky="ew")

        right = ttk.LabelFrame(cols, text="Resultados", padding=10)
        right.grid(row=0, column=1, sticky="n")
        self.fx_result_vars = {}
        self.fx_result_unit_labels = {}
        for i, (key, label, unidad_nativa) in enumerate(RESULTADOS_FX):
            unidad_mostrada = FX_RESULT_UNIT_CONV.get(key, (unidad_nativa, unidad_nativa, None))[0] \
                if self.fx_unit_var.get() == "SI" else unidad_nativa
            lbl = ttk.Label(right, text=f"{label} [{unidad_mostrada}]", wraplength=220)
            lbl.grid(row=i, column=0, sticky="w", pady=2)
            self.fx_result_unit_labels[key] = lbl
            var = tk.StringVar(value="-")
            ttk.Label(right, textvariable=var, width=16, anchor="e",
                      font=("Consolas", 10, "bold")).grid(row=i, column=1, sticky="e", padx=6)
            self.fx_result_vars[key] = var

        self.fx_status_var = tk.StringVar(value="Listo.")
        ttk.Label(outer, textvariable=self.fx_status_var, foreground="gray").pack(
            anchor="w", pady=(10, 0))

    def on_fx_cambiar_unidades(self):
        """Convierte los valores YA cargados en los campos al sistema recien
        seleccionado (no pisa con el default, respeta lo que el usuario haya
        escrito) y actualiza las etiquetas de unidad."""
        nuevo = self.fx_unit_var.get()
        for key, _label, _unidad, _default in CAMPOS_FX:
            if key in ("mu", "dP", "P", "T", "rho", "Dr", "dr"):
                continue  # unidad propia (selector Pa*s/psia/degC/kg-m3/mm/...), no sigue el toggle SI/Ingles
            si_u, ing_u, ing_a_si, si_a_ing = FX_UNIT_CONV[key]
            if key in FX_ENUM_LABELS:
                self.fx_unit_labels[key].config(text=f"{self._fx_label(key)} [{'-'}]")
                continue
            try:
                actual = float(self.fx_entries[key].get())
            except ValueError:
                continue
            # self.fx_prev_unit guarda en que sistema estaba el valor ANTES del cambio
            anterior = getattr(self, "_fx_unit_actual", "SI")
            if anterior == nuevo:
                continue
            convertido = ing_a_si(actual) if (anterior == "ING" and nuevo == "SI") else (
                si_a_ing(actual) if (anterior == "SI" and nuevo == "ING") else actual)
            self.fx_entries[key].set(f"{convertido:.15g}")
            unidad_mostrada = si_u if nuevo == "SI" else ing_u
            texto_lbl = f"{self._fx_label(key)} [{unidad_mostrada}]"
            if key in FX_NUMERIC_HINT:
                texto_lbl += f" ({FX_NUMERIC_HINT[key]})"
            texto_rango = _fx_texto_rango(key, nuevo)
            if texto_rango:
                texto_lbl += f" {texto_rango}"
            self.fx_unit_labels[key].config(text=texto_lbl)
        for key, label, unidad_nativa in RESULTADOS_FX:
            unidad_mostrada = FX_RESULT_UNIT_CONV.get(key, (unidad_nativa, unidad_nativa, None))[0] \
                if nuevo == "SI" else unidad_nativa
            self.fx_result_unit_labels[key].config(text=f"{label} [{unidad_mostrada}]")
        self._fx_unit_actual = nuevo

    def _fx_label(self, key):
        for k, label, _u, _d in CAMPOS_FX:
            if k == key:
                return label
        return key

    # Campos con selector de unidad propio (no siguen el toggle SI/Ingles) y
    # la tabla de conversion (hacia kPa/degF/lb-ft3/in segun corresponda) que
    # usa cada uno -- ver CAMPOS_UNIDAD_PROPIA en _build_tab_aga3_fx.
    _FX_TABLAS_UNIDAD_PROPIA = {
        "dP": PRESION_A_KPA, "P": PRESION_A_KPA, "T": TEMPERATURA_A_DEGF,
        "rho": DENSIDAD_A_LBFT3, "Dr": LONGITUD_A_IN, "dr": LONGITUD_A_IN,
    }

    def on_calcular_fx(self):
        sistema = self.fx_unit_var.get()
        campos_unidad_propia = self._FX_TABLAS_UNIDAD_PROPIA
        try:
            crudos = {key: float(self.fx_entries[key].get()) for key, _, _, _ in CAMPOS_FX
                      if key not in FX_ENUM_LABELS and key != "mu"
                      and key not in campos_unidad_propia}
            crudos_unidad_propia = {key: float(self.fx_entries[key].get())
                                     for key in campos_unidad_propia}
            enteros = {key: FX_ENUM_LABELS_INV[key][self.fx_entries[key].get()]
                       for key in FX_ENUM_LABELS}
            mu_bruto = float(self.fx_mu_var.get())
        except ValueError as e:
            messagebox.showerror("Entrada invalida", f"Revisa los valores numericos.\n{e}")
            return

        valores_ingles = dict(enteros)
        for key, valor in crudos.items():
            si_u, ing_u, ing_a_si, si_a_ing = FX_UNIT_CONV[key]
            valores_ingles[key] = si_a_ing(valor) if sistema == "SI" else valor

        # Campos con selector propio: convertir HACIA la unidad nativa del
        # campo (kPa->psia/inH2O via FX_UNIT_CONV; degF/lb-ft3/in ya son la
        # unidad nativa, sin paso adicional).
        for key, valor in crudos_unidad_propia.items():
            unidad_elegida = self.fx_unidad_propia_var[key].get()
            factor_fn = dict(campos_unidad_propia[key])[unidad_elegida]
            valor_base = factor_fn(valor)  # -> kPa (presion) o ya nativo (T/rho/Dr/dr)
            if key in ("dP", "P"):
                valores_ingles[key] = FX_UNIT_CONV[key][3](valor_base)  # kPa -> nativo (SI "kPa" -> ing)
            else:
                valores_ingles[key] = valor_base

        # Viscosidad: convertir de la unidad elegida (Pa*s/poise/cP/kgf*s/m2/
        # lbm/(ft*s)) a cP, que es lo que el nucleo espera sin ninguna otra
        # conversion (ver normas/AGA_3_FLOWXPERT.py, "VALIDACION REAL").
        factor_mu = dict(VISC_UNIDADES)[self.fx_mu_unidad_var.get()]
        valores_ingles["mu"] = mu_bruto * factor_mu

        # Validar contra los rangos que FlowXpert declara para cada campo
        # (ver ghidra_aga3_ctor_output.txt) ANTES de calcular -- si alguno
        # esta fuera de rango, se avisa y no se ejecuta el calculo.
        violaciones = []
        for key, (minimo, maximo) in FX_RANGOS.items():
            valor = valores_ingles.get(key)
            if valor is None:
                continue
            if not (minimo <= valor <= maximo):
                if key == "mu":
                    unidad_mostrada = "cP"
                    valor_mostrado = self.fx_mu_var.get()
                    texto_rango = _fx_texto_rango(key, sistema) or f"({minimo:.4g} a {maximo:.4g})"
                elif key in campos_unidad_propia:
                    unidad_mostrada = self.fx_unidad_propia_var[key].get()
                    valor_mostrado = self.fx_entries[key].get()
                    texto_rango = f"({minimo:.4g} a {maximo:.4g}) en unidad nativa " \
                        f"({FX_UNIT_CONV[key][1]})"
                else:
                    unidad_mostrada = FX_UNIT_CONV[key][0] if sistema == "SI" else FX_UNIT_CONV[key][1]
                    valor_mostrado = self.fx_entries[key].get()
                    texto_rango = _fx_texto_rango(key, sistema) or f"({minimo:.4g} a {maximo:.4g})"
                violaciones.append(
                    f"  - {self._fx_label(key)}: {valor_mostrado} {unidad_mostrada}, "
                    f"rango valido {texto_rango}")

        if violaciones:
            messagebox.showerror(
                "Valores fuera de rango",
                "FlowXpert no acepta estos valores (ver rango declarado para cada campo):\n\n"
                + "\n".join(violaciones))
            self.fx_status_var.set("Calculo bloqueado: hay valores fuera de rango.")
            return

        try:
            res = calcular_flujo_flowxpert(valores_ingles)
        except Exception as e:
            messagebox.showerror("Error de calculo", str(e))
            self.fx_status_var.set("Error en el ultimo calculo.")
            return

        status = res.get("status")
        if status not in (0, None) or "beta" not in res:
            self.fx_status_var.set(f"FlowXpert rechazo o marco error en la entrada -- status={status}")
            for key, _label, _unidad in RESULTADOS_FX:
                self.fx_result_vars[key].set("-")
            return

        for key, _label, unidad_nativa in RESULTADOS_FX:
            val = res.get(key)
            if val is None:
                self.fx_result_vars[key].set("-")
                continue
            if sistema == "SI" and key in FX_RESULT_UNIT_CONV:
                val = FX_RESULT_UNIT_CONV[key][2](val)
            if key in ("iteraciones", "status"):
                self.fx_result_vars[key].set(f"{val:.0f}")
            elif sistema == "SI" and key in FX_DECIMALES_SI:
                decimales = FX_DECIMALES_SI[key]
                self.fx_result_vars[key].set(f"{val:,.{decimales}f}")
            elif key in ("beta", "Cd", "factor_expansion", "factor_veloc_aprox"):
                self.fx_result_vars[key].set(f"{val:.6f}")
            else:
                self.fx_result_vars[key].set(f"{val:,.4f}")

        self.fx_status_var.set(f"Calculado (motor FlowXpert, sistema {sistema}). status={status}")

    # ------------------------------------------------------------------ #
    def _build_tab_nx19(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

        cols2 = ttk.Frame(outer)
        cols2.pack(fill="both", expand=True, pady=(0, 10))
        left2 = ttk.LabelFrame(cols2, text="Entradas", padding=10)
        left2.grid(row=0, column=0, sticky="n", padx=(0, 10))

        nx19_ghv_campos = [
            ("p_bar", "Pressure", "bar(a)", "10"),
            ("t_degc", "Temperature", "°C", "25"),
            ("sg", "Specific Gravity", "-", "0.6"),
            ("ghv", "Gross Heating Val.", "MJ/m3", "40"),
            ("n2", "Nitrogen Fraction", "mole/mole", "0.01"),
            ("co2", "Carbon dioxide Frac.", "mole/mole", "0.02"),
        ]
        self.nx19_ghv_entries = {}
        for i, (key, label, unit, default) in enumerate(nx19_ghv_campos):
            ttk.Label(left2, text=f"{label} [{unit}]", wraplength=260).grid(
                row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(left2, textvariable=var, width=12).grid(row=i, column=1, padx=6, pady=3)
            self.nx19_ghv_entries[key] = var

        row = len(nx19_ghv_campos)
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
            right2, ["z", "rango_status"],
            {"z": "Compressibility (Z)", "rango_status": "Range Status"})

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
        self.gerg_aviso_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.gerg_aviso_var, foreground="#B03A2E",
                  font=("Segoe UI", 9, "bold"), wraplength=280).grid(
            row=len(self.gerg_result_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

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
            self.gerg_aviso_var.set("")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.gerg_result_vars.items():
            var.set(f"{prop[key]:.6f}")
        self.gerg_aviso_var.set(prop.get("aviso_baja_presion_flowxpert") or "")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2008_gas(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

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
        self.gerg2008g_aviso_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.gerg2008g_aviso_var, foreground="#B03A2E",
                  font=("Segoe UI", 9, "bold"), wraplength=280).grid(
            row=len(self.gerg2008g_result_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

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
            self.gerg2008g_aviso_var.set("")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        prop["D_mass_kg_m3"] = prop["D_mol_l"] * prop["Mm_g_mol"]
        for key, var in self.gerg2008g_result_vars.items():
            var.set(f"{prop[key]:.6f}")
        self.gerg2008g_aviso_var.set(prop.get("aviso_baja_presion_flowxpert") or "")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2008_flash(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

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
        self.gerg2008f_aviso_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.gerg2008f_aviso_var, foreground="#B03A2E",
                  font=("Segoe UI", 9, "bold"), wraplength=280).grid(
            row=len(self.gerg2008f_result_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

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
            self.gerg2008f_aviso_var.set("")
            messagebox.showerror("Calculation error", res.get("msg_error", ""))
            return
        for key, var in self.gerg2008f_result_vars.items():
            var.set(f"{res[key]:.6f}")
        self.gerg2008f_aviso_var.set(res.get("aviso_baja_presion_flowxpert") or "")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2004_gas(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

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
            result_frame, ["Mm_g_mol", "D_mol_l", "Z", "Cv_J_molK", "Cp_J_molK",
                           "H_J_mol", "S_J_molK", "Kappa"],
            {"Mm_g_mol": "Masa molar [g/mol]", "D_mol_l": "Densidad [mol/l]",
             "Z": "Factor Z", "Cv_J_molK": "Cv [J/mol-K]", "Cp_J_molK": "Cp [J/mol-K]",
             "H_J_mol": "Entalpia [J/mol]", "S_J_molK": "Entropia [J/mol-K]",
             "Kappa": "Exponente isentropico"})
        self.gerg2004_aviso_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.gerg2004_aviso_var, foreground="#B03A2E",
                  font=("Segoe UI", 9, "bold"), wraplength=280).grid(
            row=len(self.gerg2004_result_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

    def on_calcular_gerg2004_gas(self):
        try:
            composicion_21 = {n: float(self.gerg2004_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
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
            self.gerg2004_aviso_var.set("")
            messagebox.showerror("Calculation error", prop.get("msg_error", ""))
            return
        for key, var in self.gerg2004_result_vars.items():
            var.set(f"{prop[key]:.6f}")
        self.gerg2004_aviso_var.set(prop.get("aviso_baja_presion_flowxpert") or "")

    # ------------------------------------------------------------------ #
    def _build_tab_gerg2004_flash(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

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
        self.gerg2004f_aviso_var = tk.StringVar(value="")
        ttk.Label(masica_frame, textvariable=self.gerg2004f_aviso_var, foreground="#B03A2E",
                  font=("Segoe UI", 9, "bold"), wraplength=280).grid(
            row=len(self.gerg2004f_masica_vars), column=0, columnspan=2, sticky="w", pady=(6, 0))

    def on_calcular_gerg2004_flash(self):
        try:
            composicion_21 = {n: float(self.gerg2004f_comp_entries[n].get()) for n in GAS_NOMBRES_COMPONENTES}
            composicion = aplicar_modo_neo_pentano(
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
            self.gerg2004f_aviso_var.set("")
            messagebox.showerror("Calculation error", res.get("msg_error", ""))
            return
        for key, var in self.gerg2004f_result_vars.items():
            var.set(f"{res[key]:.6f}")
        for key, var in self.gerg2004f_masica_vars.items():
            var.set(f"{res[key]:.6f}")
        self.gerg2004f_aviso_var.set(res.get("aviso_baja_presion_flowxpert") or "")

    # ------------------------------------------------------------------ #
    def _build_tab_aga10(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)

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
            # [CERTAIN, 2026-08-04] Ya no existe un "plan B" aproximado para
            # Critical Flow Factor -- si el emulador no esta disponible,
            # normas/AGA_10.py levanta un error ANTES de llegar aca (ver
            # el except mas abajo), en vez de devolver un resultado con
            # metodo_critical_flow="formula_respaldo". Por eso no hace
            # falta chequear ese caso en esta pantalla.
            self.aga10_advertencia_critflow_var.set(
                "ADVERTENCIA: " + " / ".join(avisos) if avisos else "")

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
            var.set("Calculando... (~11 s, emulacion real del binario)")
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
    def _build_tab_aga7(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
        self.aga7_entries, self.aga7_result_vars = self._build_caudal_tab(
            outer, on_calcular=self.on_calcular_aga7)

    def on_calcular_aga7(self):
        self._calcular_caudal(self.aga7_entries, self.aga7_result_vars, caudal_base_desde_flujo)

    # ------------------------------------------------------------------ #
    def _build_tab_aga9(self, parent):
        scroll_parent = self._crear_frame_scrollable(parent)
        outer = ttk.Frame(scroll_parent, padding=12)
        outer.pack(fill="both", expand=True)
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
    def on_calcular_nx19_ghv(self):
        try:
            p_bar = float(self.nx19_ghv_entries["p_bar"].get())
            t_degc = float(self.nx19_ghv_entries["t_degc"].get())
            sg = float(self.nx19_ghv_entries["sg"].get())
            ghv = float(self.nx19_ghv_entries["ghv"].get())
            n2 = float(self.nx19_ghv_entries["n2"].get())
            co2 = float(self.nx19_ghv_entries["co2"].get())
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
            self.nx19_ghv_result_vars["rango_status"].set(f"Fuera de rango del metodo ({e})")
            return
        self.nx19_ghv_result_vars["z"].set(f"{res['z']:.6f}")
        self.nx19_ghv_result_vars["rango_status"].set(
            "Out of range (GHV, P, T o SG fuera del rango valido de la funcion real)"
            if res["fuera_de_rango"] else "OK")


if __name__ == "__main__":
    app = App()
    app.mainloop()
