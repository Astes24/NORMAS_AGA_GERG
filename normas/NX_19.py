# -*- coding: utf-8 -*-
"""
normas/NX_19.py
================
Metodo NX-19 "SG + Poder Calorifico" de FlowXpert (pantalla NX-19 de la app,
campos Pressure/Temperature/Specific Gravity/Gross Heating Val./Nitrogen
Fraction/Carbon dioxide Frac./PTB G9 Correction). Unica funcion de
produccion: `nx19_fpv_ghv()`, usada por `interfaz_calculo_flujo.py`.

Este archivo se ejecuta como paquete:
    python -m normas.NX_19

[NOTA -- copia "NORMAS_AGA_GERG" (GitHub), 2026-09-02] Esta copia del
proyecto esta pensada para desplegarse SIN dependencias binarias (web/
Linux). El emulador Unicorn (`_nx19_emulador.py`) fue retirado a proposito
de este repositorio -- el camino de respaldo aca es `normas/NX_19_puro.py`
(100% Python puro, cero dependencias). Ver ese archivo para el detalle
completo de como se porto y valido cada formula.

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
Intenta, en orden: (1) llamada directa a `FlowXpert.xll` si esta disponible
(solo Windows), (2) porte Python puro (`normas/NX_19_puro.py`, siempre
disponible).

PASO 1 -- Importar:
    from normas.NX_19 import nx19_fpv_ghv

PASO 2 -- Reunir las 6 entradas (unidades exactas, NO hay conversion
automatica):
    p_bar     = 50.0   # Presion ABSOLUTA, bar(a) -- NO manometrica
    t_degc    = 25.0   # Temperatura, grados Celsius
    sg        = 0.6    # Gravedad Especifica (adimensional, aire=1)
    ghv_mj_m3 = 40.0    # Poder Calorifico Bruto, MJ/m3
    n2_frac   = 0.01    # Fraccion molar de Nitrogeno (0.0-1.0, NO porcentaje)
    co2_frac  = 0.02    # Fraccion molar de CO2 (0.0-1.0, NO porcentaje)
    ptb_g9    = True    # Activa la correccion "PTB G9" de FlowXpert

PASO 3 -- Llamar (`ptb_g9` es el unico parametro opcional, default True):
    resultado = nx19_fpv_ghv(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9)

PASO 4 -- Leer el resultado:
    resultado["z"]; resultado["fpv"]; resultado["d_mol_m3"]
    resultado["fuera_de_rango"]  # True/False, avisa, NO bloquea el calculo
    resultado["fuente"]          # que rama/camino se uso de verdad

Ejemplo completo:
    from normas.NX_19 import nx19_fpv_ghv
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    print(r["z"], r["fpv"], r["fuera_de_rango"])

[CERTAIN] La pantalla real llama a `Nx19_Calc`, que despacha asi:
    ptb_g9=False -> siempre `Z_AGA_nx19` (el GHV nunca se lee)
    ptb_g9=True y GHV < 39.79999923706055 MJ/m3 -> `Z_AGA_nx19_mod`
    ptb_g9=True y GHV >= 39.79999923706055 MJ/m3 -> `Z_AGA_nx19_3H`
Estas 3 funciones reales se ejecutan aqui, en orden de preferencia, via (1)
llamada directa al binario `FlowXpert.xll` (`_nx19_xll_directo.py`, solo
funciona en Windows con el archivo presente) o (2) el porte Python puro
(`NX_19_puro.py`, funciona en cualquier plataforma) -- no una
reimplementacion sin validar, sino un porte cuidadoso confirmado contra el
dispositivo real y contra el boletin publico de ABB Totalflow (metodo
clasico de 1962).

VALIDACION: 21 casos reales (12 de sesiones anteriores + 9 capturados con
Frida sobre la app) con error 0.0000%-0.0000455% (promedio 0.0000194%,
ruido de punto flotante). Ampliado con un lote de 100 casos de barrido de
industria (P 1-118 bar, T -8 a 63 degC, SG 0.56-0.90, N2/CO2 0-13%,
GHV 20.5-55 MJ/m3, ambas ramas de ptb_g9), llamando `Nx19_Calc` directo en
el dispositivo real via Frida (sin pasar por la UI): Z coincide EXACTO en
los 100 casos (peor caso 1.3e-14 relativo). El flag "fuera de rango" se
valida emulando `Nx19_Calc` COMPLETO (no las 3 subfunciones sueltas por
separado), porque `Nx19_Calc` aplica su propio chequeo adicional de rango
de GHV antes de invocar la subfuncion -- emular solo la subfuncion no
captura ese chequeo extra. 32/32 casos de frontera coinciden con el status
real tras corregir esto.

RANGOS DOCUMENTADOS (extraidos de la logica real del binario): Presion
0-120 bar(a), Temperatura -10 a 65 degC, SG 0.55-0.90, CO2 0-30%,
GHV 20-48 MJ/m3, H2 0-10% (no expuesto en esta pantalla, siempre 0).

LIMITE CONOCIDO (del metodo NX-19 mismo, no de esta implementacion): la
formulacion NX-19 (AGA, 1962) tiene discontinuidades de derivada
documentadas publicamente (ABB Technical Bulletin 106, Kelton Software,
otros) que se agravan lejos de las condiciones tipicas para las que fue
ajustada. Con SG, CO2 y N2 simultaneamente en su limite alto (p.ej.
SG=0.89, CO2=25%, N2=10%, GHV=47 MJ/m3, P=119 bar, T=64 degC) el solver
cubico interno puede converger a una raiz matematicamente valida pero
fisicamente absurda (Z>1.1) -- confirmado IDENTICO llamando la app real via
Frida directo, no es un bug de esta emulacion sino un limite real y
conocido del metodo.

Lanza RuntimeError si NINGUNO de los 2 caminos disponibles (`.xll` directo,
porte Python puro) puede ejecutar el algoritmo real -- no hay fallback
automatico a una formula aproximada (se prefiere fallar fuerte a devolver
silenciosamente un resultado menos preciso).
"""
import math


def nx19_fpv_ghv(p_bar: float, t_degc: float, sg: float, ghv_mj_m3: float,
                  n2_frac: float, co2_frac: float, ptb_g9: bool = True) -> dict:
    """FUNCION PRINCIPAL -- ver "GUIA DE USO PASO A PASO" al inicio del
    archivo para un ejemplo completo. Calcula Z y FPV por el metodo NX-19
    "SG + Poder Calorifico + PTB G9" de FlowXpert, ejecutando el algoritmo
    real (`Nx19_Calc`), en orden de preferencia: (1) llamada directa a
    `FlowXpert.xll`, (2) porte Python puro (`normas/NX_19_puro.py`).

    Parametros -- TODOS obligatorios salvo `ptb_g9` (unidades EXACTAS, sin
    conversion automatica):
        p_bar: presion ABSOLUTA, bar(a) (NO manometrica).
        t_degc: temperatura, grados Celsius.
        sg: Gravedad Especifica, adimensional (aire=1).
        ghv_mj_m3: Poder Calorifico Bruto, MJ/m3.
        n2_frac, co2_frac: fraccion molar (0.0-1.0, NO porcentaje).
        ptb_g9: bool, default True -- activa la correccion "PTB G9".

    Devuelve dict: {"z", "fpv", "fuera_de_rango", "d_mol_m3", "fuente"}.
    Ver el docstring del modulo para el detalle de validacion y rangos
    documentados.

    [CERTAIN, 2026-08-05] Lanza ValueError si P<=0 bar(a) o T<=-273.15 degC:
    son datos sin sentido fisico (presion/temperatura absoluta no puede ser
    <=0), no un caso valido de "fuera de rango de NX-19" -- antes esto
    llegaba sin chequeo hasta el algoritmo real, que devuelve Z=0.0 (su
    propia forma de decir "no pude calcular"), y la linea de density de
    aqui abajo dividia por ese Z=0.0 sin chequear, crasheando con
    ZeroDivisionError y sin ningun mensaje util."""
    if p_bar <= 0.0:
        raise ValueError(f"Presion absoluta invalida: {p_bar} bar(a) (debe ser > 0).")
    if t_degc <= -273.15:
        raise ValueError(f"Temperatura invalida: {t_degc} degC (debe ser > -273.15, cero absoluto).")

    # [CERTAIN, 2026-08-26] Camino PRIMARIO nuevo: llamada DIRECTA (ctypes,
    # sin Excel, SIN emulador de CPU) al despachador real dentro de
    # FlowXpert.xll (ver normas/_nx19_xll_directo.py) -- equivalente exacto
    # de `Nx19_Calc`, confirmado exacto (0.000000% de diferencia) contra
    # este mismo camino Unicorn en 6 casos que cubren las 3 ramas reales
    # (Z_AGA_nx19/_mod/_3H) mas un caso extremo de borde, y ~800-1000x mas
    # rapido (~0-1 ms vs ~0.87s medidos para Unicorn). El emulador Unicorn
    # se mantiene intacto como RESPALDO automatico (no se borro) por si la
    # llamada directa falla en alguna maquina (falta FlowXpert.xll, falta
    # pefile, o un caso puntual no cubierto por las pruebas).
    r = None
    _errores = []
    _fuente = None
    try:
        from . import _nx19_xll_directo as _n19x
        if _n19x.disponible():
            r = _n19x.calcular_nx19_directo(p_bar, t_degc, sg, ghv_mj_m3,
                                             n2_frac, co2_frac, ptb_g9)
            _fuente = "Nx19_Calc (FUN_1800C9500, llamada directa .xll sin Excel/emulador)"
    except Exception as _err_xll:
        _errores.append(f"xll_directo: {_err_xll!r}")
        r = None

    if r is None:
        # [CERTAIN, 2026-09-02 -- copia "NORMAS_AGA_GERG" (GitHub), pedido
        # explicito del usuario: "elimina las emulaciones"] Esta copia, para
        # despliegue sin dependencias (web/Linux), NO incluye el respaldo
        # via emulador Unicorn (`_nx19_emulador.py`, requiere `pip install
        # unicorn` + el binario `.so` de Android) -- se retiro de este
        # repositorio a proposito. En su lugar usa el porte 100% Python
        # puro (`normas/NX_19_puro.py`, cero dependencias binarias, ya
        # validado: formula clasica cruzada contra el boletin publico de
        # ABB Totalflow, 238/238 contra el oraculo `.xll`, y 55/57 casos
        # reales de dispositivo exactos -- ver docstring de ese archivo).
        try:
            from . import NX_19_puro as _n19p
            r = _n19p.nx19_fpv_ghv(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9)
            _fuente = r["fuente"]
        except Exception as _err_puro:
            _errores.append(f"puro_python: {_err_puro!r}")
            raise RuntimeError(
                "No se pudo ejecutar el algoritmo real de NX-19 por NINGUNO "
                "de los 2 caminos disponibles en esta copia sin dependencias "
                "(llamada directa a FlowXpert.xll, o porte Python puro "
                "validado). El emulador Unicorn fue retirado deliberadamente "
                "de este repositorio. Detalle: " + " | ".join(_errores)
            ) from _err_puro

    z = r["z"]
    # Guardia adicional (defensiva): si por alguna OTRA combinacion de
    # entradas el algoritmo real degrada a Z=0.0, no crashear -- devolver
    # NaN en density en vez de ZeroDivisionError (mismo patron ya usado en
    # normas/AGA_10.py para _cstar_ideal/_cstar_real).
    if z > 0.0:
        d_mol_m3 = (p_bar * 100.0) / (z * 8.31451 * (t_degc + 273.15)) * 1000.0
    else:
        d_mol_m3 = float("nan")

    return {
        "z": z, "fpv": 1.0 / math.sqrt(z) if z > 0 else float("nan"),
        "fuera_de_rango": r["fuera_de_rango"],
        "d_mol_m3": d_mol_m3,
        "fuente": _fuente,
    }


if __name__ == "__main__":
    print("=== normas/NX_19.py -- autotest metodo SG+GHV+PTB G9 vs caso real NX-19.jpeg ===")
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    z_real = 0.909911
    dif = abs(r["z"] - z_real) / z_real * 100.0
    print(f"  Z real={z_real}  Z calculado={r['z']:.6f}  dif={dif:.4f}%  "
          f"[{'OK' if dif < 0.02 else 'DESVIACION'}]")
