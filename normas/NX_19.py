# -*- coding: utf-8 -*-
"""
normas/NX_19.py
================
Metodo NX-19 "SG + Poder Calorifico" de FlowXpert (pantalla NX-19 de la app,
campos Pressure/Temperature/Specific Gravity/Gross Heating Val./Nitrogen
Fraction/Carbon dioxide Frac./PTB G9 Correction). Unica funcion de
produccion: `nx19_fpv_ghv()`, usada por `interfaz_calculo_flujo.py`.

[C-34, 2026-10-06] 100 % Python puro: delega en `normas/NX_19_puro.py`. La
app ya no llama a FlowXpert.xll ni a ningun emulador (decision del proyecto:
ninguna norma usa binarios de ABB al calcular). Antes (desde el 2026-09-25)
este modulo llamaba primero a FlowXpert.xll por ctypes y, sin el .xll, fallaba
porque su respaldo apuntaba a un emulador que ya no existe en el proyecto.

VALIDACION del porte puro: identico a la llamada directa al .xll (diferencia
<= 3e-15 relativa) y a la pantalla real de FlowXpert en los 3 casos del libro
01 (Z 0.912751, 0.876222, 0.936651). Detalle del algoritmo, rangos y limites
del metodo en el docstring de `normas/NX_19_puro.py`.

Uso:
    from normas.NX_19 import nx19_fpv_ghv
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    r["z"], r["fpv"], r["fuera_de_rango"], r["fuente"]
Unidades: p_bar absoluta, t_degc en grados Celsius, ghv_mj_m3 en MJ/m3,
n2_frac y co2_frac en fraccion molar (0-1).
"""
from .NX_19_puro import nx19_fpv_ghv  # noqa: F401


if __name__ == "__main__":
    r = nx19_fpv_ghv(40.0, 15.0, 0.6, 9000 * 0.0041868, 0.01, 0.005, False)
    print(r["z"], r["fpv"], r["fuente"])
