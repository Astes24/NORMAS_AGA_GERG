# -*- coding: utf-8 -*-
"""
normas/API_Ethylene_Propylene.py
==============================
Funciones de alto nivel para las 2 pantallas del menu raiz "API" que
quedaban sin cerrar numericamente: "API 11.3.2.1 Ethylene" y
"API 11.3.3.2 Propylene".

CAMINO PRINCIPAL (desde 2026-09-03): el porte 100% Python puro
`normas/API_Ethylene_Propylene_puro.py` (Newton-Raphson + tabla de
correccion para Etileno, secante/regula-falsi para Propileno -- ver
docstring de ese modulo para la evidencia completa de decompilacion y el
barrido de validacion: 100% exacto dentro del rango oficial del manual en
ambos gases, contra el oraculo `.xll` real). Sigue la misma preferencia de
diseno ya establecida en todo el proyecto (ver `normas/AGA_10_puro.py`,
`normas/NX_19_puro.py`): produccion en Python puro, sin depender de
`ctypes`/`pefile`/Windows.

CAMINO OPCIONAL: llamada DIRECTA (ctypes, sin Excel, sin emulador) al
binario real `FlowXpert.xll` (ver `normas/_ethylene_propylene_xll_directo.py`
para la evidencia de decompilacion/validacion original) -- solo se usa si
se pasa `usar_xll=True` explicitamente, pensado para revalidar/depurar
contra el oraculo real durante desarrollo, NUNCA necesario para el uso
normal de estas funciones. Si se pide `usar_xll=True` pero el binario o
`pefile` no estan disponibles en la maquina (ej. despliegue Linux/web), o
el binario devuelve un codigo de error, se cae automaticamente al porte
puro (con las mismas garantias de "nunca fabricar un numero": si el porte
puro tampoco converge, se lanza RuntimeError explicito).

No hay camino de respaldo tipo emulador Unicorn para esta familia (la
Ronda 1 sobre el `.so` de Android solo llego a decompilacion ESTRUCTURAL,
bloqueada por las constantes DAT_ propias de cada ecuacion) -- no hace
falta: el porte puro YA es el camino de produccion reusando el mismo
principio de "codigo Python, sin binario en tiempo de ejecucion" que la
familia Unicorn hubiera dado, con la ventaja de estar 100% validado.

Con esto, de las 7 entradas del menu "API": 5 quedan CERRADAS numericamente
(11.1 x3, 11.2/12.2, y Ethylene+Propylene juntas, ahora en Python puro) --
solo quedan los 3 wrappers combinados de "E NGL/LPG (TP-27)"
(API_Dens15C_NGL_LPG/API_Dens20C_NGL_LPG/API_RD60F_NGL_LPG) documentados
como PENDIENTE en `normas/API_MPMS_Tables_1980_2004.py` (RONDA 14).
"""
from .API_Ethylene_Propylene_puro import (
    api_mpms_11_3_2_1_ethylene_puro, api_mpms_11_3_3_2_propylene_puro)


def api_mpms_11_3_2_1_ethylene(temp_f: float, pressure_psia: float,
                                api_rounding: int = 0, usar_xll: bool = False) -> dict:
    """Densidad y compresibilidad (Z) de Etileno (C2H4) segun API MPMS
    11.3.2.1.

    temp_f: temperatura en grados Fahrenheit. pressure_psia: presion
    absoluta en psia. api_rounding: 0 o 1 (flag "API Rounding" de la UI
    real). usar_xll: si True, intenta primero la llamada DIRECTA al
    binario real `FlowXpert.xll` (solo Windows, requiere `pefile`) en vez
    del porte Python puro -- pensado UNICAMENTE para revalidar/depurar
    contra el oraculo original; si el binario no esta disponible o
    devuelve error, cae automaticamente al porte puro sin avisar (no es un
    fallo, es el comportamiento esperado en un despliegue sin `.xll`).

    [CERTAIN, camino puro (default), ver `API_Ethylene_Propylene_puro.py`]
    Validado 100% exacto (8008/8008 casos) contra el oraculo `.xll` dentro
    del rango oficial del manual (65-167F/200-2100psia), mas los 2 casos
    reales conocidos: T=90F,P=250psia -> Density=21.13020 kg/m3 (real
    21.13020), Z=0.901174 (real 0.901174).

    Devuelve dict con density_kg_m3, z, fuera_de_rango (bool).
    Lanza RuntimeError SOLO si el porte puro no converge para esta T/P (ver
    `aviso` interno para el detalle) -- condicion extrema, ver "NIVEL DE
    CONFIANZA" en el docstring de `API_Ethylene_Propylene_puro.py`."""
    if usar_xll:
        try:
            from . import _ethylene_propylene_xll_directo as _epx
            if _epx.disponible():
                r = _epx.calcular_ethylene_directo(temp_f, pressure_psia, api_rounding)
                if r["ok"]:
                    return {
                        "density_kg_m3": r["density_kg_m3"],
                        "z": r["z"],
                        "fuera_de_rango": r["fuera_de_rango"],
                    }
        except Exception:
            pass  # cae al porte puro, ver docstring

    r = api_mpms_11_3_2_1_ethylene_puro(temp_f, pressure_psia, api_rounding)
    if not r["convergio"]:
        raise RuntimeError(
            f"API_MPMS_11_3_2_1 (Ethylene, porte Python puro) no convergio para "
            f"T={temp_f}F P={pressure_psia}psia api_rounding={api_rounding}: {r['aviso']}"
        )
    return {
        "density_kg_m3": r["density_kg_m3"],
        "z": r["z"],
        "fuera_de_rango": r["fuera_de_rango"],
    }


def api_mpms_11_3_3_2_propylene(temp_f: float, pressure_psia: float,
                                 api_rounding: int = 0, usar_xll: bool = False) -> dict:
    """Densidad de Propileno Liquido (CTPL, Equilibrium Pressure incluidos)
    segun API MPMS 11.3.3.2.

    temp_f: temperatura en grados Fahrenheit. pressure_psia: presion
    absoluta en psia. api_rounding: 0 o 1. usar_xll: ver docstring de
    `api_mpms_11_3_2_1_ethylene()` -- mismo comportamiento (opcional, solo
    para revalidar contra el binario real).

    [CERTAIN, camino puro (default), ver `API_Ethylene_Propylene_puro.py`]
    Validado 100% exacto (7472/7472 casos) contra el oraculo `.xll` dentro
    del rango oficial del manual (30-165F/0-1600psia, por encima de la
    presion de vapor), mas el caso real conocido: T=60F,P=200psia ->
    Density=523.6218 kg/m3 (real 523.6218), CTPL=1.002541 (real 1.002541),
    Equilibrium Pressure=9.047925 bar (real 9.047929) -- NOTA sobre unidad
    heredada sin resolver: el caso real documenta "bar(g)" pero la
    conversion que reproduce el numero exacto es psia->bar DIRECTA sin
    resta de presion atmosferica, ver docstring de
    `API_Ethylene_Propylene_puro.py` para la discrepancia honesta.

    Devuelve dict con density_kg_m3, ctpl, equilibrium_pressure_bar,
    fuera_de_rango (bool). Lanza RuntimeError SOLO si el porte puro no
    converge para esta T/P."""
    if usar_xll:
        try:
            from . import _ethylene_propylene_xll_directo as _epx
            if _epx.disponible():
                r = _epx.calcular_propylene_directo(temp_f, pressure_psia, api_rounding)
                if r["ok"]:
                    return {
                        "density_kg_m3": r["density_kg_m3"],
                        "ctpl": r["ctpl"],
                        "equilibrium_pressure_bar": r["equilibrium_pressure_bar"],
                        "fuera_de_rango": r["fuera_de_rango"],
                    }
        except Exception:
            pass  # cae al porte puro, ver docstring

    r = api_mpms_11_3_3_2_propylene_puro(temp_f, pressure_psia, api_rounding)
    if not r["convergio"]:
        raise RuntimeError(
            f"API_MPMS_11_3_3_2 (Propylene, porte Python puro) no convergio para "
            f"T={temp_f}F P={pressure_psia}psia api_rounding={api_rounding}: {r['aviso']}"
        )
    return {
        "density_kg_m3": r["density_kg_m3"],
        "ctpl": r["ctpl"],
        "equilibrium_pressure_bar": r["equilibrium_pressure_bar"],
        "fuera_de_rango": r["fuera_de_rango"],
    }


if __name__ == "__main__":
    print("=== normas/API_Ethylene_Propylene.py -- autotest vs casos reales (camino puro) ===")
    r1 = api_mpms_11_3_2_1_ethylene(90.0, 250.0)
    print(f"Ethylene T=90F P=250psia: density={r1['density_kg_m3']:.6f} kg/m3 "
          f"(real=21.13020), z={r1['z']:.6f} (real=0.901174)")

    r2 = api_mpms_11_3_3_2_propylene(60.0, 200.0)
    print(f"Propylene T=60F P=200psia: density={r2['density_kg_m3']:.6f} kg/m3 "
          f"(real=523.6218), ctpl={r2['ctpl']:.6f} (real=1.002541), "
          f"eq_p={r2['equilibrium_pressure_bar']:.6f} bar (real=9.047929)")
