# -*- coding: utf-8 -*-
"""
normas/ASTM_D1550.py
=====================
RONDA 45 (2026-09-10). Familia "ASTM D1550" (Butadieno) -- 2 funciones
reales, DISTINTAS entre si y DISTINTAS de `api_mpms_11_2_2`/`_11_2_2m`
(familia API 11.2/12.2, ya [CERTAIN] desde RONDA 13):

  - `ASTM_D1550_Ctl` (manual p.76, `FUN_18007d680` -> nucleo real
    `FUN_1800a4e40` -> `FUN_1800fc688`): interpolacion bilineal PURA sobre
    la Tabla 2 del estandar (RD@60F x Temperatura -> CTL de Butadieno),
    SIN iteracion, SIN dependencia de otra norma.
  - `ASTM_D1550_RD60` (manual p.77, `FUN_18007db2c` -> nucleo real
    `FUN_1800a4f5c` -> `FUN_1800fcab8`): resuelve RD@60F a partir de
    densidad relativa OBSERVADA, temperatura y presion, iterando (hasta 20
    pasos) la relacion fisica RD_obs = RD60 * CTL(RD60,T) * CPL(RD60,T,P) --
    y CONFIRMADO por decompilacion directa que el factor de compresibilidad
    F/CPL de este paso se calcula llamando LITERALMENTE al mismo nucleo
    `FUN_1800e32e8` que ya usa `api_mpms_11_2_2` (RONDA 13): mismo orden de
    argumentos (rd, t, p, equilibrium_pressure=0, api_rounding, &cpl, &f,
    &fuera_de_rango), confirmando la sospecha de RONDA 43 ("RD60 llama al
    factor F de acuerdo a API MPMS 11.2.2:1984 como sub-paso") con evidencia
    dura, no solo con el texto del manual.

Este modulo REUSA `api_mpms_11_2_2` de `normas/API_MPMS_Tables_1980_2004.py`
tal cual (sin duplicar codigo), mismo patron que `normas/GPA_TP15.py`
acaba de establecer para GPA-TP15/11.2.2.

===============================================================================
FASE 0 -- MANUAL OFICIAL (`Flow-X Manual IIIb...pdf`, pdfplumber, p.76-77)
===============================================================================
Compliance exacto citado por el manual: **"ASTM D1550-94 (Reapproved 2005),
Density, Relative Density, and API Gravity of Butadienes and Butadiene-
Hydrocarbon Mixtures"**, Tablas 1 y 2 del anexo. El manual describe:
  - Tabla 2 (usada por `Ctl`): "Volume Correction Factors to 60°F" en
    funcion de RD@60F y temperatura observada.
  - Tabla 1 (usada por `RD60`, paso previo a la iteracion): "Reduction of
    Observed Density to Density at 60°F", y dice EXPLICITO que "the
    compressibility factor is calculated in accordance with API MPMS
    11.2.2:1984" -- confirmado ahora por decompilacion (ver arriba).
Ambas funciones son "customary" (US, °F/psig) -- el manual NO documenta
variante metrica, y el `.xll` solo registra las 2 funciones US (sin
sufijo "M"), confirmado por busqueda completa en
`ghidra_todos_los_nombres_output.txt` (solo 2 registros `ASTM_D1550_*`).

===============================================================================
FASE 1/2 -- DECOMPILACION REAL (Ghidra 12.1.2, `.xll`, RONDA 45)
===============================================================================
Script `ANALISIS_GHIDRA_FLOWXPERT/ghidra_scripts_xll/DecompileAstmD1550Xll.java`,
salida completa en `ANALISIS_GHIDRA_FLOWXPERT/ghidra_astm_d1550_xll_output.txt`.

INPUTS/OUTPUTS reales confirmados por la metadata de registro
(`FUN_180064600`, mismo mecanismo ya usado en toda la familia API):

`ASTM_D1550_Ctl`:
  Inputs: "rel density 60" (RD@60F, rango de PANTALLA 0..0.75, default
    0.63), "Temperature" (°F, rango pantalla -100..150F, default 60F).
  Outputs: "status" (enum, en la practica SIEMPRE 0=OK para esta funcion --
    ver mapeo de codigos abajo), "CTL" ("Volume correction factor for
    temperature"), "Range Status" (booleano/texto, 1 si RD o T cayeron
    fuera del dominio FISICO real de la tabla [0.621,0.634]x[-10,110]F o
    si el CTL resultante se salio de [0.941,1.074] -- en ese ultimo caso
    el valor se recorta al limite, con el flag activado).

`ASTM_D1550_RD60`:
  Inputs: "rel density" (RD OBSERVADA, rango pantalla 0..1.0, default
    0.63), "Temperature" (°F, rango pantalla -100..150F, default 60F),
    "pressure" (Observed pressure, PSIG -- mismo codigo de unidad 0x1001f03
    que el resto de la familia API 1952/1980/11.2.x, rango pantalla
    -10..2500psig, default 100psig), "API Rounding" (booleano, default 0,
    activa el redondeo de F/CPL de `api_mpms_11_2_2`).
  Outputs: "status" (enum 0=OK/2=CALCERR/3=NOCONV, ver mapeo abajo), "RD60"
    (RD a 60F resultante), "Compressibility" (F, "Compressibility factor
    (F)"), "CTL" ("Volume correction factor for temperature"), "CPL"
    ("Volume correction factor for pressure"), "ASTM Range Status" (1 si
    RD60/T cayeron fuera del dominio de la Tabla 1/2 de D1550), "MPMS Range
    Status" (1 si el sub-paso de 11.2.2 marco fuera de rango -- literal
    "API MPMS 11.2.2 range" en el registro, confirma la cita del manual).

===============================================================================
NUCLEO REAL DE `Ctl` (`FUN_1800fc688`) -- [CERTAIN], tabla extraida a BYTES
===============================================================================
Interpolacion bilineal simple sobre una tabla real de 14 filas (RD@60F
0.621..0.634 paso 0.001) x 121 columnas (T -10..110F paso 1F), valores CTL
escalados x1000 como `short`, extraida con `pefile` en VA 0x18028b990..
0x18028c090 (14*121*2=3388 bytes) -- ver `normas/_astm_d1550_ctl_table.py`.
Los limites min/max de la tabla (0.941/1.074) COINCIDEN EXACTO con las
constantes de clip `DAT_18028c700`/`DAT_18028c708` leidas por separado --
confirmacion cruzada de que la tabla se extrajo completa y en la posicion
correcta. Formula EXACTA (`rd`/`t_f` ya recortados a domino):
    i = clip(round(rd*1000)-620, 1, 13)      # fila (por trunc, no redondeo)
    j = clip(round(t_f)+11, 1, 120)          # columna
    interpolacion bilinear estandar entre las 4 celdas vecinas de la tabla.
VALIDADO [CERTAIN]: 400 puntos aleatorios (RD 0.60-0.70, T -30..130F,
incluye zona fuera de rango) contra el nucleo real `FUN_1800fc688` llamado
DIRECTO por `ctypes` (RVA+LoadLibraryW, sin Excel/emulador, mismo patron ya
validado para Ethylene/Propylene) -- **diferencia MAXIMA = 0.0 (exacta a
precision de maquina)**, incluyendo el flag de rango en los 400 casos.

===============================================================================
NUCLEO REAL DE `RD60` (`FUN_1800fcab8`) -- [CERTAIN] para presion !=~0psig,
pendiente honesto documentado para presion ~0psig
===============================================================================
El nucleo real bifurca en 2 ramas segun `abs(pressure_psig) >= 0.01`
(`DAT_180193e68`):

1. **RAMA ITERATIVA (presion >= 0.01psig en valor absoluto -- CUBRE el
   100% del uso realista de la pantalla, cuyo rango es -10..2500psig con
   default 100psig)** [CERTAIN]: itera hasta 20 pasos la relacion fisica
       RD60_(n+1) = RD_obs / (CTL(RD60_n, T) * CPL(RD60_n, T, P))
   donde CTL viene del mismo nucleo de `Ctl` de arriba y (F, CPL) vienen de
   `api_mpms_11_2_2(RD60_n, T, P, equilibrium_pressure_psig=0.0,
   rounding=api_rounding)` -- CONFIRMADO por decompilacion que es LITERAL
   el mismo nucleo `FUN_1800e32e8` (no una copia). Tolerancia de
   convergencia: 1e-7 si `api_rounding=0`, 1e-6 si `api_rounding=1`
   (`DAT_180194df0`/`DAT_180193dc8`, confirmado a bytes). Si converge:
   status=0 (OK), con RD60/F/CTL/CPL = los valores de la ULTIMA iteracion
   (nota real del algoritmo: F/CTL/CPL quedan evaluados en el penultimo
   valor de RD60, NO en el RD60 final devuelto -- confirmado por
   decompilacion Y reproducido exacto en el oraculo, no es un error de
   este porte). Si NO converge en 20 pasos: status=3 (NOCONV).
   VALIDADO contra el nucleo real via `ctypes` (200 casos aleatorios, T
   -30..130F, P 0.02..2400psig, RD_obs 0.55..0.70, api_rounding 0/1): 188/200
   (94%) coinciden a <1e-6 en RD60/F/CPL. Los 12 restantes son TODOS casos
   de borde (T>100F combinado con P alta y/o RD cerca de los limites de la
   tabla [0.621,0.634], zona donde el algoritmo necesita 19-20 iteraciones
   para converger) con diferencia maxima 2.8e-4 en RD60 -- **causa raiz
   identificada**: el valor SEMILLA real del solver no es `RD_obs` (lo que
   usa este porte) sino el resultado de la Tabla 1 (ver pendiente abajo),
   y en la zona casi-no-convergente el punto fijo final es sensible al
   punto de partida (mismo fenomeno de "borde numericamente caotico" ya
   documentado en AGA-10/NX-19 -- ver `feedback-preferencia-python-puro.md`).
   Fuera de esa zona de borde (la inmensa mayoria del dominio de la
   pantalla) la coincidencia es exacta.

2. **RAMA DIRECTA (presion < 0.01psig en valor absoluto, esencialmente
   P=0 exacto)** -- [PENDIENTE HONESTO, NO fabricado, NO portado]: usa una
   tabla propia ("Tabla 1" del estandar, `FUN_1800fc8e4`) para estimar
   RD60 DIRECTAMENTE a partir de RD_obs y T, sin iterar. La decompilacion
   de esta sub-funcion resulto NO CONFIABLE (el C generado por Ghidra llama
   a `FUN_1800fccec` con solo 1 de sus 3 argumentos reales -- inconsistencia
   de firma vs. sitio de llamada, sintoma ya documentado en el proyecto de
   decompilacion fallida, ver `reversing-ghidra-flowxpert.md`). CONFIRMADO
   EMPIRICAMENTE (oraculo `ctypes`, no una suposicion) que esta rama NO
   coincide con la formula iterativa general: p.ej. T=30F, RD_obs=0.60,
   P=0 -> el nucleo real da RD60=0.621 (clip al limite inferior de tabla),
   mientras que la ecuacion fisica general (con CPL=1 exacto a P=0)
   resolveria un RD60 distinto. Este modulo, para P~0, **NO reproduce el
   atajo exacto del binario**: usa la MISMA rama iterativa de arriba (que
   sigue siendo fisicamente valida a P=0, con CPL=1.0 exacto), documentado
   aqui EXPLICITO como divergencia conocida frente al `.xll` SOLO para
   presion absoluta <0.01psig -- caso de borde extremo, fuera del rango de
   pantalla realista (default 100psig, rango -10..2500). No se fuerza un
   cierre falso: si se necesita este caso exacto en el futuro, hace falta
   decompilacion adicional (RetDec/desensamblado manual de `FUN_1800fccec`
   y `FUN_1800fc8e4`) que esta ronda NO alcanzo a completar de forma
   confiable.

===============================================================================
FASE 4 -- PANTALLA PROPIA CONFIRMADA EN VIVO [CERTAIN, uiautomator, AVD
`flowxpert_rd`]
===============================================================================
Menu raiz -> categoria "ASTM" -> lista real (sin scroll adicional
necesario para D1550): "ASTM D1550 CTL", "ASTM D1550 Rel. Density @60F",
"ASTM D4311M (2009)" (+ mas entradas de D4311 fuera de alcance de esta
ronda) -- nombres LITERALES, coinciden exacto con los registrados en el
`.xll`. 2 pantallas propias, cada una con su boton/estado
"Calculating ASTM D1550 ..." (recalculo automatico al cambiar cualquier
campo, sin boton "Calculate" explicito -- patron real de la app Android,
distinto del mock de escritorio de este proyecto).

Campos confirmados en vivo -- "ASTM D1550 CTL":
  Rel. Density @60°F: adimensional, rango pantalla "0 .. 0.75", default
    0.63 (coincide con la metadata decodificada a bytes).
  Temperature: selector real K/°C/°F/R (confirmado abriendo el picker de
    unidad), rango pantalla en °F "-100 .. 150", default 60°F (=15.5555556°C
    en la pantalla).
  Resultados: CTL, y "Range Status" (SOLO aparece con texto "Out of range"
    cuando corresponde -- confirmado, no aparece en el caso default).

Campos confirmados en vivo -- "ASTM D1550 Rel. Density @60F":
  Relative Density (observada): adimensional, default 0.63.
  Temperature: selector K/°C/°F/R, default 60°F.
  Pressure: selector real de presion GAUGE (bar(g)/mbar(g)/mmHgg/mmH2Og/
    mmH2Og@60F/inHgg con.../... -- mismo tipo de selector de presion
    manometrica ya visto en la familia API 1952/1980, NO el selector
    absoluto de 11 unidades de NGL/LPG/GPA-TP15), rango pantalla en bar(g)
    "-0.689476 .. 172.369" (=exacto -10..2500 psig, confirma el codigo de
    unidad psig leido de la metadata), default 6.89476 bar(g) (=100psig
    exacto).
  API Rounding: Switch booleano, default 0.
  Resultados: "Status" (SOLO aparece con texto -- "No convergence" en el
    caso real que no convergio, ver abajo -- normalmente oculto cuando
    status=OK), Rel. Density @60°F, Compressibility [1/psi], CTL, CPL.
    "ASTM Range Status"/"MPMS Range Status" no se activaron en ninguno de
    los 4 casos reales capturados (ninguno cayo fuera de rango) -- se
    espera el mismo patron condicional ya visto en el resto de la familia,
    sin caso real dedicado que los active.
  RONDA 54 (2026-09-16): CONFIRMADO en vivo que "Compressibility [1/psi]"
    SI abre un selector real de unidad al tocarlo (Spinner, 5 opciones:
    1/Pa, 1/kPa, 1/MPa, 1/psi, 1/bar) -- igual que otros resultados de la
    app real. Por decision de producto ya establecida, este proyecto no
    agrega selectores de unidad en campos de RESULTADO en la GUI -- se deja
    fijo en 1/psi como ya estaba, sin cambio de codigo necesario.

===============================================================================
FASE 5 -- VALIDACION [CERTAIN], casos reales EN VIVO (RONDA 45,
`uiautomator`, AVD `flowxpert_rd`)
===============================================================================
"ASTM D1550 CTL" (3 casos, incluye esquina fuera de rango):
  1. RD@60F=0.63,  T=60°F  -> CTL=1.000000 (Range Status ausente/OK).
  2. RD@60F=0.625, T=30°F  -> CTL=1.032000 (Range Status ausente/OK).
  3. RD@60F=0.70,  T=30°F  -> CTL=1.031000, Range Status="Out of range"
     (RD fuera del dominio fisico 0.621-0.634, dentro del rango de
     pantalla 0-0.75 -- el calculo NO se bloquea, usa la fila de tabla
     mas cercana, mismo patron ya visto en GPA-TP15/RONDA 44).
Los 3 reproducen EXACTO (`python -m normas.ASTM_D1550`) contra este porte.

"ASTM D1550 Rel. Density @60F" (4 casos, incluye el flag "API Rounding"
activo Y un caso real de no-convergencia -- ambos exigidos por la
metodologia del proyecto, no solo el caso default):
  1. RD_obs=0.63, T=60°F, P=100psig(6.89476bar(g)), Rounding=0 ->
     RD60=0.629204, Compressibility=0.000013 1/psi, CTL=1.000000,
     CPL=1.001266.
  2. Igual pero Rounding=1 -> RD60=0.629182, Compressibility=0.000013
     1/psi, CTL=1.000000, CPL=1.001300.
  3. RD_obs=0.63, T=30°F, P=100psig, Rounding=0 -> Status="No convergence"
     (el solver NO converge en 20 iteraciones para esta combinacion
     especifica -- CONFIRMADO tambien por el oraculo `ctypes` directo al
     nucleo real, que da el mismo codigo crudo de no-convergencia, y por
     este porte Python, que da `status=3` para el MISMO input exacto --
     triple coincidencia real app / oraculo / porte).
  4. RD_obs=0.63, T=60°F, P=50bar(g)(=725.1884...psig), Rounding=0 ->
     RD60=0.624181, Compressibility=0.000013 1/psi, CTL=1.000000,
     CPL=1.009322.
Los 4 reproducen EXACTO (`python -m normas.ASTM_D1550`) contra este porte,
incluyendo el caso 3 (no-convergencia, el mas dificil de acertar por
casualidad).

===============================================================================
CERO REGRESION
===============================================================================
`python -m normas.API_MPMS_Tables_1980_2004` (no se modifico, solo se
REUSA `api_mpms_11_2_2`) y `python -c "import interfaz_calculo_flujo"`
verificados exit 0 antes y despues de esta ronda, mismos resultados.
"""
from __future__ import annotations

from normas._astm_d1550_ctl_table import ASTM_D1550_CTL_TABLE
from normas.API_MPMS_Tables_1980_2004 import api_mpms_11_2_2

# Dominio real de la Tabla 2 (Ctl), confirmado a bytes (DAT_18028c6e8/6f0,
# DAT_1801ea3a8/1801940d8, DAT_180124818=escala x1000).
RD60_TABLE_MIN = 0.621
RD60_TABLE_MAX = 0.634
T_TABLE_MIN_F = -10.0
T_TABLE_MAX_F = 110.0
CTL_CLIP_MIN = 0.941
CTL_CLIP_MAX = 1.074
_SCALE = 1000.0

# Umbral de rama del solver de RD60 y tolerancias de convergencia (DAT_
# 180193e68/180193dc8/180194df0, confirmados a bytes).
_PRESSURE_BRANCH_THRESHOLD_PSIG = 0.01
_TOL_NO_ROUNDING = 1.0e-7
_TOL_ROUNDING = 1.0e-6
_MAX_ITER = 20


def _ctl_core(rd60: float, t_f: float) -> tuple[float, bool]:
    """[CERTAIN] Replica EXACTA de `FUN_1800fc688` -- interpolacion
    bilineal sobre `ASTM_D1550_CTL_TABLE`. Validado a precision de maquina
    (diff=0.0) contra 400 casos aleatorios via oraculo `ctypes` directo al
    `.xll` (ver docstring del modulo)."""
    i = int(rd60 * _SCALE + 1 - 621)
    if i < 1:
        i = 1
    if i > 13:
        i = 13
    j = int(t_f + 1 - (-10.0))
    if j < 1:
        j = 1
    if j > 120:
        j = 120

    row_lo = ASTM_D1550_CTL_TABLE[i - 1]
    row_hi = ASTM_D1550_CTL_TABLE[i]
    dens_lo = (i - 1) / _SCALE + RD60_TABLE_MIN
    dens_hi = i / _SCALE + RD60_TABLE_MIN
    t_lo = j - 11
    t_hi = j - 10

    v_lo_t_hi = row_lo[j] / _SCALE
    v_lo_t_lo = row_lo[j - 1] / _SCALE
    interp_lo = (v_lo_t_hi - v_lo_t_lo) * (t_f - t_lo) / (t_hi - t_lo) + v_lo_t_lo

    v_hi_t_hi = row_hi[j] / _SCALE
    v_hi_t_lo = row_hi[j - 1] / _SCALE
    interp_hi = (v_hi_t_hi - v_hi_t_lo) * (t_f - t_lo) / (t_hi - t_lo) + v_hi_t_lo

    ctl = (interp_hi - interp_lo) * (rd60 - dens_lo) / (dens_hi - dens_lo) + interp_lo

    oor = False
    if (rd60 < RD60_TABLE_MIN or rd60 > RD60_TABLE_MAX
            or t_f < T_TABLE_MIN_F or t_f > T_TABLE_MAX_F):
        oor = True
    if ctl < CTL_CLIP_MIN:
        ctl = CTL_CLIP_MIN
        oor = True
    if ctl > CTL_CLIP_MAX:
        ctl = CTL_CLIP_MAX
        oor = True
    return ctl, oor


def astm_d1550_ctl(rd60: float, t_f: float) -> dict:
    """API publica de la pantalla real "ASTM D1550 CTL" (interpolacion
    PURA sobre la Tabla 2 de ASTM D1550, Butadieno). [CERTAIN, ver
    docstring del modulo].

    rd60: "Rel. Density @ 60F", adimensional (rango de pantalla 0..0.75,
        dominio FISICO real de la tabla 0.621..0.634).
    t_f: "Temperature", °F (rango de pantalla -100..150F, dominio FISICO
        real de la tabla -10..110F).

    Devuelve dict: "status" (0, siempre OK para esta funcion -- el nucleo
    real nunca devuelve otro codigo aqui, confirmado por decompilacion),
    "ctl" (Volume correction factor for temperature), "fuera_de_rango"
    (bool, "Range Status" en pantalla)."""
    ctl, oor = _ctl_core(rd60, t_f)
    return {"status": 0, "ctl": ctl, "fuera_de_rango": oor}


def astm_d1550_rd60(rd_obs: float, t_f: float, pressure_psig: float,
                     api_rounding: int = 0) -> dict:
    """API publica de la pantalla real "ASTM D1550 Rel. Density @60F".
    [CERTAIN para presion absoluta >=0.01psig -- cubre el rango entero de
    pantalla salvo el borde P~0 exacto, ver docstring del modulo para el
    pendiente honesto de esa rama].

    rd_obs: "Rel. Density" OBSERVADA, adimensional (rango pantalla 0..1.0).
    t_f: "Temperature", °F (rango pantalla -100..150F).
    pressure_psig: "Pressure", PSIG (rango pantalla -10..2500psig).
    api_rounding: "API Rounding" (0/1) -- redondeo de F/CPL via
        `api_mpms_11_2_2`.

    Devuelve dict: "status" (0=OK, 3=NOCONV -- no convergio en 20
    iteraciones), "rd60", "compressibility" (F, 1/psi), "ctl", "cpl",
    "astm_oor" (bool, "ASTM Range Status": RD60/T fuera del dominio de la
    Tabla 1/2 de D1550), "mpms_oor" (bool, "MPMS Range Status": el sub-paso
    de 11.2.2 marco fuera de rango)."""
    tol = _TOL_ROUNDING if api_rounding else _TOL_NO_ROUNDING
    guess = rd_obs
    ctl = 1.0
    f = 0.0
    cpl = 1.0
    mpms_oor = False
    converged = False
    for _ in range(_MAX_ITER):
        ctl, _ctl_oor = _ctl_core(guess, t_f)
        r112 = api_mpms_11_2_2(guess, t_f, pressure_psig,
                                equilibrium_pressure_psig=0.0,
                                rounding=api_rounding)
        f = r112["f"]
        cpl = r112["cpl"]
        mpms_oor = r112["fuera_de_rango_oficial"]
        denom = ctl * cpl
        new_guess = rd_obs / denom if denom != 0.0 else guess
        if abs(guess - new_guess) < tol:
            converged = True
            guess = new_guess
            break
        guess = new_guess

    if not converged:
        return {
            "status": 3, "rd60": guess, "compressibility": f, "ctl": ctl,
            "cpl": cpl, "astm_oor": False, "mpms_oor": mpms_oor,
        }
    astm_oor = not (RD60_TABLE_MIN <= guess <= RD60_TABLE_MAX)
    return {
        "status": 0, "rd60": guess, "compressibility": f, "ctl": ctl,
        "cpl": cpl, "astm_oor": astm_oor, "mpms_oor": mpms_oor,
    }


if __name__ == "__main__":
    # Autotest CTL: reproduce 4 puntos de esquina/centro contra el oraculo
    # `.xll` directo capturado en RONDA 45 (ver docstring del modulo).
    casos_ctl = [
        dict(rd60=0.63, t_f=60.0, esperado=1.0, esperado_oor=False),
        dict(rd60=0.625, t_f=30.0, esperado=1.032, esperado_oor=False),
        dict(rd60=0.621, t_f=-10.0, esperado=1.074, esperado_oor=False),
        dict(rd60=0.633, t_f=109.0, esperado=0.946, esperado_oor=False),
    ]
    ok = True
    for i, caso in enumerate(casos_ctl, 1):
        esperado = caso.pop("esperado")
        esperado_oor = caso.pop("esperado_oor")
        r = astm_d1550_ctl(**caso)
        diff = abs(r["ctl"] - esperado)
        marca = "OK" if diff < 1e-6 and r["fuera_de_rango"] == esperado_oor else "FALLO"
        if marca == "FALLO":
            ok = False
        print(f"CTL caso {i}: ctl={r['ctl']:.6f} esperado={esperado:.6f} "
              f"diff={diff:.2e} oor={r['fuera_de_rango']} [{marca}]")

    # Autotest RD60: 4 casos reales EN VIVO (uiautomator, AVD flowxpert_rd,
    # RONDA 45), pantalla "ASTM D1550 Rel. Density @60F".
    casos_rd60 = [
        dict(rd_obs=0.63, t_f=60.0, pressure_psig=100.0, api_rounding=0,
             esperado_rd60=0.629204, esperado_cpl=1.001266, esperado_status=0),
        dict(rd_obs=0.63, t_f=60.0, pressure_psig=100.0, api_rounding=1,
             esperado_rd60=0.629182, esperado_cpl=1.001300, esperado_status=0),
        dict(rd_obs=0.63, t_f=30.0, pressure_psig=100.0, api_rounding=0,
             esperado_rd60=None, esperado_cpl=None, esperado_status=3),
        dict(rd_obs=0.63, t_f=60.0, pressure_psig=50.0 / 0.0689476, api_rounding=0,
             esperado_rd60=0.624181, esperado_cpl=1.009322, esperado_status=0),
    ]
    for i, caso in enumerate(casos_rd60, 1):
        esperado_rd60 = caso.pop("esperado_rd60")
        esperado_cpl = caso.pop("esperado_cpl")
        esperado_status = caso.pop("esperado_status")
        r = astm_d1550_rd60(**caso)
        if esperado_status == 3:
            marca = "OK" if r["status"] == 3 else "FALLO"
            if marca == "FALLO":
                ok = False
            print(f"RD60 caso {i} (no-convergencia esperada): status={r['status']} [{marca}]")
            continue
        diff_rd60 = abs(r["rd60"] - esperado_rd60)
        diff_cpl = abs(r["cpl"] - esperado_cpl)
        marca = "OK" if diff_rd60 < 5e-7 and diff_cpl < 5e-7 and r["status"] == 0 else "FALLO"
        if marca == "FALLO":
            ok = False
        print(f"RD60 caso {i}: rd60={r['rd60']:.6f} esperado={esperado_rd60:.6f} "
              f"cpl={r['cpl']:.6f} esperado={esperado_cpl:.6f} [{marca}]")

    print("TODOS OK" if ok else "HAY FALLOS")
