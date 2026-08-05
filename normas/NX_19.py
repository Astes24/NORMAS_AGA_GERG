# -*- coding: utf-8 -*-
"""
normas/NX_19.py
================
Metodo NX-19 "SG + Poder Calorifico" de FlowXpert (pantalla NX-19 de la app,
campos Pressure/Temperature/Specific Gravity/Gross Heating Val./Nitrogen
Fraction/Carbon dioxide Frac./PTB G9 Correction). Unica funcion de
produccion: `nx19_fpv_ghv()`, usada por `interfaz_calculo_flujo.py`.

Este archivo se ejecuta como paquete (usa import relativo a `_nx19_emulador`):
    python -m normas.NX_19

[CERTAIN] La pantalla real llama a `Nx19_Calc`, que despacha asi:
    ptb_g9=False -> siempre `Z_AGA_nx19` (el GHV nunca se lee)
    ptb_g9=True y GHV < 39.79999923706055 MJ/m3 -> `Z_AGA_nx19_mod`
    ptb_g9=True y GHV >= 39.79999923706055 MJ/m3 -> `Z_AGA_nx19_3H`
Estas 3 funciones reales se ejecutan aqui via emulacion EXACTA de CPU
(Unicorn sobre `apk_analisis/libFXLibrary.so`, ver `_nx19_emulador.py`), no
una reimplementacion en Python de sus formulas -- por eso el resultado
coincide con el dispositivo real a precision de punto flotante, no por
ajuste/correccion medida.

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

Lanza RuntimeError si el emulador no esta disponible (falta 'unicorn' o
`apk_analisis/libFXLibrary.so`) -- no hay fallback automatico a una
formula aproximada (se prefiere fallar fuerte a devolver silenciosamente
un resultado menos preciso).
"""
import math


def nx19_fpv_ghv(p_bar: float, t_degc: float, sg: float, ghv_mj_m3: float,
                  n2_frac: float, co2_frac: float, ptb_g9: bool = True) -> dict:
    """Calcula Z y FPV por el metodo NX-19 "SG + Poder Calorifico + PTB G9"
    de FlowXpert, emulando el algoritmo real (`Nx19_Calc`) via CPU (Unicorn).

    Presion en bar(a), temperatura en degC, SG adimensional, GHV en MJ/m3,
    N2/CO2 como fraccion molar (0-1). Ver el docstring del modulo para el
    detalle de validacion y rangos documentados.

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

    from . import _nx19_emulador as _nx19_emu

    r = _nx19_emu.calcular_nx19_dispatch_real(
        p_bar=p_bar, t_degc=t_degc, sg=sg, ghv_mj_m3=ghv_mj_m3,
        n2_frac=n2_frac, co2_frac=co2_frac, ptb_g9=ptb_g9,
    )
    z = r["z"]
    # Guardia adicional (defensiva): si por alguna OTRA combinacion de
    # entradas el algoritmo real degrada a Z=0.0, no crashear -- devolver
    # NaN en density en vez de ZeroDivisionError (mismo patron ya usado en
    # normas/AGA_10.py para _cstar_ideal/_cstar_real).
    if z > 0.0:
        d_mol_m3 = (p_bar * 100.0) / (z * 8.31451 * (t_degc + 273.15)) * 1000.0
    else:
        d_mol_m3 = float("nan")
    _, nombre_funcion = _nx19_emu._elegir_funcion(ptb_g9, ghv_mj_m3)

    return {
        "z": z, "fpv": 1.0 / math.sqrt(z) if z > 0 else float("nan"),
        "fuera_de_rango": r["fuera_de_rango"],
        "d_mol_m3": d_mol_m3,
        "fuente": f"Nx19_Calc -> {nombre_funcion} (emulacion real exacta, Unicorn sobre libFXLibrary.so)",
    }


if __name__ == "__main__":
    print("=== normas/NX_19.py -- autotest metodo SG+GHV+PTB G9 vs caso real NX-19.jpeg ===")
    r = nx19_fpv_ghv(p_bar=50.0, t_degc=25.0, sg=0.6, ghv_mj_m3=40.0,
                      n2_frac=0.01, co2_frac=0.02, ptb_g9=True)
    z_real = 0.909911
    dif = abs(r["z"] - z_real) / z_real * 100.0
    print(f"  Z real={z_real}  Z calculado={r['z']:.6f}  dif={dif:.4f}%  "
          f"[{'OK' if dif < 0.02 else 'DESVIACION'}]")
