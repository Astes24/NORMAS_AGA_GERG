# -*- coding: utf-8 -*-
"""
normas/GPA_TP15.py
===================
RONDA 44 (2026-09-10). Expone como funcion PUBLICA independiente la
pantalla real "GPA-TP15" (categoria "GPA" del menu raiz de FlowXpert) --
"Equilibrium Vapor Pressure for Natural Gas Liquids (NGL) according to
GPA-TP15" (texto literal del registro del `.xll`, simbolo real
`GPA_TP15` -> `FUN_1800a7b50` -> `FUN_1800efcbc`).

NO reimplementa nada nuevo: el nucleo (`_gpa_tp15_psia`, formula
exp()/log() + tabla real de 7 filas) ya estaba 100% Python puro en
`normas/_ngl_lpg_wrappers_puro.py` desde la mision original de "E NGL/LPG
(TP-27)" (RONDA 14, portado a Python puro 2026-09-03) -- este modulo lo
IMPORTA y lo expone bajo su propio nombre publico + firma que coincide
1:1 con los inputs/outputs reales de la pantalla GPA-TP15.

===============================================================================
CONFIRMACION DE PANTALLA PROPIA [CERTAIN, `uiautomator` en vivo, RONDA 44]
===============================================================================
RONDA 43 (reconocimiento, sin emulador) habia dejado esto como sospecha sin
confirmar ("fuerte indicio... pendiente confirmar en vivo"). Confirmado
esta ronda con el AVD `flowxpert_rd` corriendo: el menu raiz -> categoria
"GPA" tiene EXACTAMENTE 2 pantallas, "GPA-2172" y "GPA-TP15" -- DISTINTA
del uso interno dentro de "E NGL/LPG (TP-27)" (que NO la lista como
pantalla separada, ya documentado desde RONDA 14: esa familia tiene 9
pantallas, ni GPA-TP15 ni GPA-2172 entre ellas). Es decir: GPA-TP15 tiene
DOBLE uso real en la app -- pantalla propia bajo "GPA" Y sub-calculo
interno de los 3 wrappers combinados de NGL/LPG -- ambos comparten el
MISMO nucleo `_gpa_tp15_psia`, sin duplicacion de codigo.

Nota sobre la categoria de registro del `.xll`: la metadata interna
(`ghidra_todos_los_nombres_output.txt`, `FUN_180087cc8`) registra
`GPA_TP15` con categoria de host "Math" (no "GPA") -- el mismo patron que
`GasViscosity_2004` (tambien "Math", y SI tiene pantalla propia,
confirmado y cerrado en rondas previas). La categoria de registro del
host NO predice si una funcion tiene pantalla en el menu Android; la
UNICA fuente confiable es `uiautomator` en vivo, como ya establece la
metodologia del proyecto.

===============================================================================
INPUTS/OUTPUTS REALES (`uiautomator` + metadata de registro del `.xll`,
ambas fuentes cruzadas, RONDA 44)
===============================================================================
Inputs (orden real de pantalla, confirmado por captura en vivo):
  1. "Rel. Density @60°F" (interno `rel density`) -- adimensional, rango
     de PANTALLA 0..0.75 (decodificado de la metadata de registro Y
     confirmado por el dialogo de edicion real: "Range: 0 .. 0.75",
     Details: "Relative density at 60 °F."). Default real: 0.6. El
     dominio FISICO interno de la correlacion (que activa "Range Status"
     si se sale) es distinto y mas angosto: [0.35, 0.676] para RD, con un
     limite de temperatura que depende de RD (ver `_TP15_*` en
     `_ngl_lpg_wrappers_puro.py`) -- confirmado con caso real RD=0.75
     (dentro del rango de PANTALLA, fuera del rango FISICO): el calculo
     NO se bloquea, solo aparece "Range Status: Out of range".
  2. "Temperature" -- selector real K/°C/°F/R (mismo patron que el resto
     de la familia API), rango de pantalla -100..200°F (decodificado de
     metadata, confirmado en vivo: "-73.3333333 .. 93.3333333" en °C).
     Default real: 60°F (=15.5555556°C). Descripcion real: "Observed
     temperature."
  3. "API Rounding" (interno `round_tp15`) -- Switch booleano, default 0.
     Redondea el resultado final `evp_psia` a 1 decimal (confirmado con
     caso real, ver VALIDACION -- la etiqueta real de pantalla es "API
     Rounding", NO "GPA TP-15 Rounding" como se le habia puesto en la
     pestaña de NGL/LPG -- ver nota en `interfaz_calculo_flujo.py`).
  4. "P100 Correlation" (interno `p100_correlacion`) -- Switch booleano,
     default 0. Activa el metodo alterno via un valor de Vapor Pressure
     @100°F ya conocido en vez de la tabla de 7 filas.
  5. "Vapor Pres. @100°F" (interno `p100_valor_psia`) -- SOLO aparece en
     pantalla cuando "P100 Correlation"=1 (confirmado en vivo; la
     metadata de registro ya traia la nota real "(p100_cor)" en ese
     campo). Selector real de presion ABSOLUTA (mismo selector de 11
     unidades ya usado en el resto de la familia API: bar(a)/mbar(a)/
     mmHga/mmH2Oa/inHga/inH2Oa). Default real: 100 psia = 6.89476 bar(a)
     (confirmado en vivo Y por la metadata de registro, que trae el
     mismo valor 100.0 como default crudo).
Outputs:
  1. "Equilibrium Pressure" -- selector real de presion ABSOLUTA (mismo
     selector de 11 unidades), default bar(a).
  2. "Range Status" -- SOLO aparece (en rojo, texto "Out of range") cuando
     el resultado cae fuera del dominio FISICO de la correlacion -- NO es
     un tercer valor numerico, es un texto condicional.

===============================================================================
VALIDACION [CERTAIN] -- 7 casos reales NUEVOS capturados en vivo esta
ronda (`uiautomator` sobre AVD `flowxpert_rd`, pantalla real "GPA-TP15",
NO casos indirectos via NGL/LPG) -- TODOS coinciden con `_gpa_tp15_psia`
dentro de ~1e-6 relativo (ruido de precision de conversion de unidades
psia<->bar, no un error de formula):
  1. RD=0.6,  T=60°F, Rounding=0, P100=0          -> EVP=1.157104 bar(a)
  2. RD=0.6,  T=60°F, Rounding=0, P100=1(100psia) -> EVP=3.268000 bar(a)
  3. RD=0.6,  T=60°F, Rounding=1, P100=1(100psia) -> EVP=3.268116 bar(a)
  4. RD=0.6,  T=60°F, Rounding=1, P100=0          -> EVP=1.158320 bar(a)
  5. RD=0.4,  T=60°F, Rounding=0, P100=0          -> EVP=28.99701 bar(a)
  6. RD=0.65, T=60°F, Rounding=0, P100=0          -> EVP=0.467759 bar(a)
  7. RD=0.75, T=60°F, Rounding=0, P100=0          -> EVP=0.201050 bar(a),
     Range Status="Out of range"
Los casos 2/3/4 CIERRAN definitivamente 2 pendientes que llevaban desde
RONDA 15/33/36 como [LIKELY, sin caso real]: "P100 Correlation" (caso 2,
antes NUNCA probado numericamente) y "API Rounding"/`round_tp15` (casos
3/4, antes asumido en 0 "por analogia") -- ambos ahora [CERTAIN].
Los casos 5/6 validan DIRECTAMENTE 2 filas de las 7 de la tabla (filas 1 y
7, los extremos) que el barrido original de NGL/LPG (via el solver
iterativo de RD60F/Dens15C/20C) nunca habia ejercitado de forma directa
con este nivel de certeza (el solver converge casi siempre a valores de
RD cercanos al centro de la tabla). El caso 7 confirma el flag de rango Y
que el calculo NO se bloquea fuera de rango (usa la fila de tabla mas
cercana), igual que el resto de este proyecto.

===============================================================================
CERO REGRESION en los modulos que ya usaban GPA-TP15 como sub-calculo
interno (`normas/_ngl_lpg_wrappers_puro.py` via `_gpa_tp15_psia`,
`normas/API_MPMS_Tables_1980_2004.py` via los 3 wrappers combinados) --
este modulo NO modifica `_gpa_tp15_psia` ni la tabla, solo la EXPONE bajo
un nombre publico nuevo. Confirmado: `python -m normas._ngl_lpg_wrappers_puro`
y `python -m normas.API_MPMS_Tables_1980_2004` siguen con exit 0 y los
mismos resultados exactos de rondas previas.

===============================================================================
CRUCE CONTRA EL MANUAL OFICIAL Y EL ESTANDAR PUBLICO (Fase 0/Fase 3,
`pdfplumber`, pagina 95 del manual, RONDA 44)
===============================================================================
GPA-TP15 ES un estandar PUBLICADO (no propietario de ABB/FlowXpert): "GPA
Technical Publication TP-15, A Simplified Vapor Pressure Correlation for
Commercial NGLs" (1988 y su revision de 2007), tambien referenciado como
"API MPMS 11.2.2 Addendum:1994" (rango angosto original) y "API MPMS
11.2.5:2007" (rango extendido, MISMAS constantes que la version de 1988
segun el manual: "preserving the calculations and constants of the
previous standard"). El manual da los limites EXACTOS del dominio fisico
de la correlacion, que coinciden bit-a-bit con las constantes YA
presentes en `_ngl_lpg_wrappers_puro.py` (decompiladas independientemente
por bytes crudos, RONDA 14):
  Rango bajo:  RD 0.350..0.425, T -50..(695.51*RD-155.51) °F.
  Rango alto:  RD 0.425..0.676, T -50..140 °F.
(`_TP15_RD_MID=0.425`, `_TP15_T_BOUND_A=695.51`, `_TP15_T_BOUND_B=155.51`,
`_TP15_T_MIN_F=-50.0`, `_TP15_T_MAX_F_HIGH_RD=140.0`) -- confirmacion
CRUZADA independiente (texto publico vs. bytes del binario) de la misma
conclusion, sin que una dependiera de la otra. El manual tambien confirma
literal el significado de "API Rounding" (0=Disabled/full precision,
1=Enabled/"Rounding as defined in GPA TP15:1988...") y de "Range" (0=In
Range, 1=Out of Range) -- coincide con lo observado en vivo. Unica
discrepancia menor, sin impacto: el manual imprime el rango de pantalla
del input RD como "0.3..0.75" y el default como "0"; el dialogo real
(`uiautomator`) muestra "0..0.75" y el valor cargado en pantalla es 0.6 --
se prioriza la evidencia EN VIVO (mas confiable que texto de manual
generico) para estos 2 detalles de UI, sin que afecten el CALCULO en si.

===============================================================================
PENDIENTE HONESTO (no fabricado, sin cambios esta ronda)
===============================================================================
Ninguno nuevo sobre la formula/tabla de GPA-TP15 en si (100% [CERTAIN]
ahora, con caso real para las 4 combinaciones de flags). Sigue pendiente,
heredado de RONDA 15 y SIN relacion con esta pantalla propia: la rama
METRICA de "E NGL/LPG (TP-27)" (Dens15C/Dens20C) pasa `x_root` (la
densidad-base candidata del solver) como primer argumento de
`_gpa_tp15_psia` en vez del literal `0` que Ghidra imprime para esa
llamada especifica -- decision de ingenieria ya documentada y validada
por barrido en `_ngl_lpg_wrappers_puro.py`, no una lectura literal del
decompilado. No afecta a este modulo (pantalla propia, sin ese camino
indirecto -- los 5 argumentos de `GPA_TP15`/`FUN_1800a7b50` estan
confirmados sin ambiguedad, a diferencia de esa llamada interna
especifica).
"""
from __future__ import annotations

from normas._ngl_lpg_wrappers_puro import _gpa_tp15_psia, NGL_LPG_TP15_TABLE  # noqa: F401

PSI_TO_KPA = 6.894757


def calcular_gpa_tp15(rd: float, t_f: float, round_tp15: int = 0,
                       p100_correlacion: int = 0, p100_valor_psia: float = 0.0) -> dict:
    """API publica de la pantalla real "GPA-TP15" (categoria "GPA" del menu
    raiz de FlowXpert, confirmada en vivo -- ver docstring del modulo).

    Unidades NATIVAS del algoritmo (la conversion de unidades de pantalla
    -- selector K/°C/°F/R de Temperature, selector de presion absoluta de
    11 unidades de Vapor Pres. @100°F y de Equilibrium Pressure -- se hace
    en la capa de interfaz, `interfaz_calculo_flujo.py`, igual que el
    resto de esta familia):
      rd: "Rel. Density @60°F", adimensional, rango de pantalla 0..0.75.
      t_f: "Temperature", °F.
      round_tp15: "API Rounding" (0/1).
      p100_correlacion: "P100 Correlation" (0/1).
      p100_valor_psia: "Vapor Pres. @100°F", psia (solo usado si
        p100_correlacion=1).

    Devuelve dict:
      "status": 0 si ok, 2 si error de calculo (dominio numerico invalido
        -- ver mapeo real de codigos en `FUN_1800a7b50`, que colapsa 0/2/3
        a sus valores literales y cualquier otro caso a 1).
      "equilibrium_pressure_psia": float, o None si status!=0.
      "fuera_de_rango": bool -- "Range Status: Out of range" en la
        pantalla real cuando es True.
    [CERTAIN], ver docstring del modulo para los 7 casos reales de
    validacion (RONDA 44, 2026-09-10)."""
    evp_psia, fuera_de_rango = _gpa_tp15_psia(
        rd, t_f, round_tp15=round_tp15, p100_correlacion=p100_correlacion,
        p100_valor_psia=p100_valor_psia)
    status = 0 if evp_psia is not None else 2
    return {
        "status": status,
        "equilibrium_pressure_psia": evp_psia,
        "fuera_de_rango": fuera_de_rango,
    }


if __name__ == "__main__":
    # Autotest: reproduce los 7 casos reales documentados arriba (captura
    # en vivo, AVD flowxpert_rd, RONDA 44).
    def _to_bar_a(psia):
        return psia * PSI_TO_KPA / 100.0

    casos = [
        dict(rd=0.6, t_f=60.0, round_tp15=0, p100_correlacion=0, p100_valor_psia=0.0,
             esperado_bar_a=1.157104),
        dict(rd=0.6, t_f=60.0, round_tp15=0, p100_correlacion=1, p100_valor_psia=100.0,
             esperado_bar_a=3.268000),
        dict(rd=0.6, t_f=60.0, round_tp15=1, p100_correlacion=1, p100_valor_psia=100.0,
             esperado_bar_a=3.268116),
        dict(rd=0.6, t_f=60.0, round_tp15=1, p100_correlacion=0, p100_valor_psia=0.0,
             esperado_bar_a=1.158320),
        dict(rd=0.4, t_f=60.0, round_tp15=0, p100_correlacion=0, p100_valor_psia=0.0,
             esperado_bar_a=28.99701),
        dict(rd=0.65, t_f=60.0, round_tp15=0, p100_correlacion=0, p100_valor_psia=0.0,
             esperado_bar_a=0.467759),
        dict(rd=0.75, t_f=60.0, round_tp15=0, p100_correlacion=0, p100_valor_psia=0.0,
             esperado_bar_a=0.201050, esperado_oor=True),
    ]
    ok = True
    for i, caso in enumerate(casos, 1):
        esperado = caso.pop("esperado_bar_a")
        esperado_oor = caso.pop("esperado_oor", False)
        r = calcular_gpa_tp15(**caso)
        obtenido = _to_bar_a(r["equilibrium_pressure_psia"])
        diff = abs(obtenido - esperado)
        marca = "OK" if diff < 2e-4 and r["fuera_de_rango"] == esperado_oor else "FALLO"
        if marca == "FALLO":
            ok = False
        print(f"caso {i}: obtenido={obtenido:.6f} esperado={esperado:.6f} "
              f"diff={diff:.2e} oor={r['fuera_de_rango']} "
              f"esperado_oor={esperado_oor} [{marca}]")
    print("TODOS OK" if ok else "HAY FALLOS")
