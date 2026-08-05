# -*- coding: utf-8 -*-
"""
normas/AGA_9.py
=================
AGA Report No. 9 -- "Measurement of Gas by Multipath Ultrasonic Meters".
Alias documentado sobre `normas/AGA_7.py`, NO una formula independiente.

Este archivo se puede ejecutar solo:
    python -m normas.AGA_9

===============================================================================
FUENTE Y NIVEL DE CONFIANZA
===============================================================================
[CERTAIN] AGA-9 no define su propia formula de conversion de caudal. Segun
la pagina publica de ayuda de Kelton (help.kelton.co.uk/c259-aga-7-aga-9...),
que documenta ambas normas juntas, AGA-9 remite directamente a AGA-7 para el
calculo de caudal -- la diferencia entre las dos normas es el TIPO DE
MEDIDOR (turbina en AGA-7, ultrasonico multi-trayecto en AGA-9) y sus
respectivos requisitos de instalacion/incertidumbre/diagnostico especificos
del medidor, no la relacion matematica entre caudal de flujo, caudal base y
caudal masico.

[CERTAIN] FlowXpert.xll (ABB) no tiene AGA-7 ni AGA-9 en ninguna de sus 373
exportaciones -- no hay nada que confirmar contra el binario para ninguna
de las dos normas. Ver docstring completo en `normas/AGA_7.py`.

[GUESSING] Lo que SI es propio de AGA-9 y no esta cubierto aqui: los
diagnosticos especificos del medidor ultrasonico (perfil de velocidad,
verificacion cruzada entre trayectorias, deteccion de flujo perturbado).
Eso es logica del FIRMWARE del medidor fisico, no una formula de caudal --
no aplica a este proyecto de "confirmacion de calculos" de FocQus salvo que
FocQus tenga su propio medidor ultrasonico (no fue el caso hasta ahora,
FocQus solo tiene AGA-3 en su DLL).
===============================================================================
"""

from .AGA_7 import (  # noqa: F401
    caudal_base_desde_flujo,
    caudal_flujo_desde_base,
    caudal_base_desde_masa,
    caudal_flujo_desde_masa,
    caudal_masico_desde_base,
    caudal_masico_desde_flujo,
)

if __name__ == "__main__":
    print("=== normas/AGA_9.py -- alias sobre AGA_7.py ===")
    Qf = 1000.0
    Pf, Pb = 5000.0, 101.325
    Tf, Tb = 288.15, 288.7056
    Zf, Zb = 0.95, 0.998
    Qb = caudal_base_desde_flujo(Qf, Pf, Pb, Tf, Tb, Zf, Zb)
    print(f"Qf = {Qf} -> Qb = {Qb:.4f}")
