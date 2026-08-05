# -*- coding: utf-8 -*-
"""
normas/AGA_7.py
=================
AGA Report No. 7 -- "Measurement of Natural Gas by Turbine Meters".
Conversion de caudal entre condiciones de flujo, condiciones base, y masa.

Este archivo se puede ejecutar solo:
    python -m normas.AGA_7

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] FlowXpert.xll (ABB) NO tiene AGA-7 ni AGA-9 en ninguna de sus 373
exportaciones (se busco explicitamente, cero coincidencias). Esto es
consistente con que FlowXpert es una herramienta de placa de orificio +
propiedades de gas (AGA3/5/8/10/GERG/NX-19), no de medidores de turbina o
ultrasonicos. Por lo tanto, a diferencia de TODO lo demas en `normas/`, este
archivo NO fue ni pudo ser confirmado contra el binario de ABB -- no hay
nada que confirmar, la norma simplemente no esta implementada ahi.

[CERTAIN] Las 6 ecuaciones de conversion se extrajeron de una pagina de
ayuda PUBLICA del proveedor Kelton (help.kelton.co.uk/c259-aga-7-aga-9...),
que documenta su implementacion del "AGA-7 Appendix B". Se descargaron y
leyeron las 6 imagenes de formula (C259_1 a C259_6) directamente. Son
identidades basicas de conservacion de masa + ley de gas real (P*V/(Z*T) =
constante), no ajustes empiricos propios de AGA-7 -- cualquier norma de
medicion de gas usa esta misma relacion. No se leyo el texto completo del
reporte AGA-7 original (de pago, no se compro).

[CERTAIN] AGA-9 ("Measurement of Gas by Multipath Ultrasonic Meters") NO
tiene formula de caudal propia: la misma pagina de Kelton indica
explicitamente que AGA-9 remite a AGA-7 para el calculo de caudal (la
diferencia entre ambas normas es el tipo de medidor -- turbina vs
ultrasonico multi-trayecto -- y sus respectivos requisitos de incertidumbre
y configuracion, no la formula de conversion en si).

[CERTAIN -- 2026-07-23, segunda fuente independiente, confirmacion cruzada]
Se releyo en vivo la pagina de Kelton (sin cambios respecto a lo ya usado) y
ademas se encontro y leyo el manual oficial "Flow Measurement User Manual"
de Emerson/ROC800 (RAS-EN-133856, Rev Mar/05), que en su Sec. 2.1 cita
TEXTUALMENTE los numeros de ecuacion del AGA Report No. 7 real (no una
pagina de un proveedor externo): "Ecuacion 12/13" (ley de gas real en
condiciones de flujo/base, ambas versiones 1985 y 1996) y "Ecuacion 16"
(1996) / "Ecuacion 15" (1985) para el caudal base:
    Qb = Qf * (Pf/Pb) * (Tb/Tf) * (Zb/Zf)
Coincide DIGITO A DIGITO con `caudal_base_desde_flujo` de este archivo. Esta
segunda fuente, independiente de Kelton y citando la numeracion real del
reporte AGA-7 (ediciones 1985 Y 1996), es una confirmacion cruzada fuerte de
que la formula esta bien -- no se encontro, en ninguna de las 2 fuentes, un
ejemplo numerico resuelto (P, T, Z, Q reales) para comparar 1 a 1; ambas
fuentes documentan solo la formula, no un caso de validacion con numeros.
Sec. 2.3 del mismo manual confirma tambien, en las mismas palabras que
Kelton, que AGA-9 remite a AGA-7 para el caudal ("AGA Report No. 9... Section
7.3, refers the reader to AGA No. 7 for calculations").

[GUESSING] Los factores de compresibilidad Zf (condiciones de flujo) y Zb
(condiciones base) NO se calculan aqui -- se esperan como parametro de
entrada. En un caso real, calcularlos con `normas/AGA_8.py` o
`normas/NX_19.py` (ya confirmados por separado), no inventar un valor.
===============================================================================
"""


def caudal_base_desde_flujo(Qf: float, Pf: float, Pb: float, Tf: float, Tb: float,
                             Zf: float, Zb: float) -> float:
    """Qb = Qf * (Pf/Pb) * (Tb/Tf) * (Zb/Zf) -- Ec. C259_1."""
    return Qf * (Pf / Pb) * (Tb / Tf) * (Zb / Zf)


def caudal_flujo_desde_base(Qb: float, Pf: float, Pb: float, Tf: float, Tb: float,
                             Zf: float, Zb: float) -> float:
    """Qf = Qb * (Pb/Pf) * (Tf/Tb) * (Zf/Zb) -- Ec. C259_3."""
    return Qb * (Pb / Pf) * (Tf / Tb) * (Zf / Zb)


def caudal_base_desde_masa(Qm: float, rho_b: float) -> float:
    """Qb = Qm / rho_b -- Ec. C259_2."""
    return Qm / rho_b


def caudal_flujo_desde_masa(Qm: float, rho_f: float) -> float:
    """Qf = Qm / rho_f -- Ec. C259_4."""
    return Qm / rho_f


def caudal_masico_desde_base(Qb: float, rho_b: float) -> float:
    """Qm = Qb * rho_b -- Ec. C259_5."""
    return Qb * rho_b


def caudal_masico_desde_flujo(Qf: float, rho_f: float) -> float:
    """Qm = Qf * rho_f -- Ec. C259_6."""
    return Qf * rho_f


# AGA-9 (medidores ultrasonicos multi-trayecto) reutiliza la misma formula de
# caudal que AGA-7 -- ver docstring. Alias explicitos, no una copia de codigo.
caudal_base_desde_flujo_AGA9 = caudal_base_desde_flujo
caudal_flujo_desde_base_AGA9 = caudal_flujo_desde_base


if __name__ == "__main__":
    # Ejemplo numerico de plausibilidad (no un caso de validacion publicado)
    Qf = 1000.0     # m3/h en condiciones de flujo
    Pf, Pb = 5000.0, 101.325   # kPa
    Tf, Tb = 288.15, 288.7056  # K
    Zf, Zb = 0.95, 0.998

    print("=== normas/AGA_7.py -- autotest ===")
    Qb = caudal_base_desde_flujo(Qf, Pf, Pb, Tf, Tb, Zf, Zb)
    print(f"Qf = {Qf} -> Qb = {Qb:.4f}")
    Qf_recuperado = caudal_flujo_desde_base(Qb, Pf, Pb, Tf, Tb, Zf, Zb)
    print(f"Qb = {Qb:.4f} -> Qf (recuperado) = {Qf_recuperado:.4f} (debe dar {Qf})")
