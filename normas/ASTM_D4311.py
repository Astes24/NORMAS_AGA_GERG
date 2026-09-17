# -*- coding: utf-8 -*-
"""
normas/ASTM_D4311.py
======================
RONDA 47 (2026-09-10). Familia "ASTM D4311" -- Volume Correction Factor
(Ctl) para Asfalto ("Standard Practice for Determining Asphalt Volume
Correction to a Base Temperature", ASTM D4311/D4311M-09). 4 funciones
reales confirmadas en el `.xll` (`ANALISIS_GHIDRA_FLOWXPERT/
ghidra_astm_d4311_xll_output.txt`, Ghidra 12.1.2):

  - `ASTM_D4311M_09_C` (manual p.78, `FUN_1800a5448` -> nucleo puro
    `FUN_1800fa5b4`): edicion 2009, US customary, API gravity @60F.
  - `ASTM_D4311M_09_M` (manual p.79, `FUN_1800a5548` -> nucleo puro
    `FUN_1800fa4f4`): edicion 2009, metrico, Densidad @15C.
  - `ASTM_D4311C` (SIN sufijo, `FUN_1800a5160` -> nucleo `FUN_1800fa9e8`):
    version generalizada US, NO documentada en el manual de 236 paginas.
  - `ASTM_D4311M` (SIN sufijo, `FUN_1800a52d4` -> nucleo `FUN_1800fa698`):
    version generalizada metrica, tampoco documentada.

===============================================================================
FASE 0 -- MANUAL OFICIAL (p.78-79, `pdfplumber`)
===============================================================================
Titulo REAL confirmado (contradice la hipotesis de partida de "isoteniscope
vapor pressure" -- CONFIRMADO que esa hipotesis era incorrecta):
    "ASTM Designation: D4311/D4311M-09, Standard Practice for Determining
    Asphalt Volume Correction to a Base Temperature."
Formula: "in accordance with appendix X1. FORMULAS USED IN DETERMINING
VOLUME CORRECTIONS TO A BASE TEMPERATURE of the standard" -- el manual NO
transcribe la formula (solo la cita), asi que se tomo integramente de la
decompilacion, cruzada por ORACULO `.xll` directo (ver abajo).

`_09_C`: inputs "API gravity at 60F" (0..34.9, default 0), "Observed
temperature" (°F, 0..500, default 60). Output: Status (0 Normal/1 Input oor/
2 Calc error), Ctl (SIN redondear).
`_09_M`: inputs "Density at 15C" (kg/m3, 800..1200 EN EL MANUAL -- pero la
pantalla REAL en vivo, RONDA 47, muestra Range "850 .. 1200", ver Fase 4),
"Observed temperature" (°C, -25..274.5, default 15). Mismos outputs.

===============================================================================
FASE 1/2 -- DECOMPILACION REAL (Ghidra 12.1.2, RONDA 47) + ORACULO `.xll`
===============================================================================
Script `ANALISIS_GHIDRA_FLOWXPERT/ghidra_scripts_xll/DecompileAstmD4311Xll.java`,
salida `ANALISIS_GHIDRA_FLOWXPERT/ghidra_astm_d4311_xll_output.txt`. Oraculo
de llamada directa (ctypes, sin Excel/emulador) en
`normas/_astm_d4311_xll_directo.py` -- confirma EXACTO (precision de
maquina) la reconstruccion de formula de abajo, 400 casos aleatorios por
funcion en `normas/_sweep_astm_d4311.py` (ver seccion VALIDACION).

--- `_09_C`/`_09_M`: formula CUADRATICA SIMPLE en T, dos grupos por
API-gravity/densidad (SIN dependencia de T en la SELECCION de grupo,
solo en el VALOR) -- NO hay iteracion, NO hay dependencia entre C y M
mas alla de compartir la MISMA estructura con constantes propias:
    Ctl = A*T^2 + B*T + C
  Grupo BAJO (API<=14.9 customary / densidad>=966 metrico -- asfaltos mas
  densos/pesados): A=4.4988E-8, B=-3.549E-4, C=1.021133 (customary, T en
  °F) | A=1.4571E-7, B=-6.3341E-4, C=1.00946793 (metrico, T en °C).
  Grupo ALTO (14.9<API<=34.9 customary / 850<=densidad<966 metrico --
  asfaltos mas livianos): A=6.7918E-8, B=-4.06414E-4, C=1.0241379
  (customary) | A=2.1997E-7, B=-7.23438E-4, C=1.01080222 (metrico).
  Rango valido (status=1 si se sale, Ctl=0.0): API<=34.9 (SIN piso -- el
  nucleo real NO valida API<0 pese al rango de pantalla 0..34.9,
  CONFIRMADO empiricamente con el oraculo, api=-1 devuelve status=0
  normal) y 0<=T<=500°F (customary) | densidad>=850 (con GAP real entre
  800 y 850 kg/m3: la pantalla del manual dice 800..1200 pero el NUCLEO
  matematico de 2009 SOLO cubre desde 850 -- CONFIRMADO ADEMAS en vivo,
  ver Fase 4, la pantalla real de la app muestra Range "850..1200", NO
  "800..1200" como dice el manual) y -25<=T<=274.5°C (metrico, SIN techo
  de densidad -- el nucleo tampoco valida densidad>1200).

--- `ASTM_D4311C`/`ASTM_D4311M` (sin sufijo): generalizacion NO documentada
de la formula de arriba, con 2 diferencias reales confirmadas por
decompilacion+oraculo:
  1. Rango EXTENDIDO con validacion EXPLICITA en ambos extremos (a
     diferencia de `_09_*` que no valida el piso): API 0..45 (antes 0..34.9),
     T -50..700°F (antes 0..500); densidad 800..1200 (antes 850..1200, el
     GAP de 800-850 queda CERRADO aqui), T -50..400°C (antes -25..274.5).
     Fuera de este rango extendido: status=1, Ctl por defecto =1.0 (NO 0.0
     como en `_09_*` -- diferencia real de comportamiento confirmada por
     oraculo).
  2. Un 3er input nuevo, ENTERO con SOLO 2 valores validos (1 o 2, `status=1`
     si es otro valor) -- el manual NO lo documenta, no se pudo confirmar su
     etiqueta real en la app (ver PENDIENTE). Por evidencia de decompilacion
     [CERTAIN]: modo=1 usa las MISMAS constantes A/B/C, bit a bit, que
     `_09_C`/`_09_M` (confirmado: `astm_d4311_c(api,t,1)` da Ctl IDENTICO a
     `astm_d4311_09_c(api,t)` en el rango original 09); modo=2 usa un
     segundo juego de constantes mas PRECISAS (mas cifras significativas,
     mismo orden de magnitud) -- funcionalmente equivalente a un selector
     "constantes originales D4311-09 (redondeadas)" vs "constantes
     refinadas", aplicado sobre el rango YA extendido en ambos modos por
     igual. Ver PENDIENTE para la etiqueta real de este selector en la UI.
     Constantes modo=2: grupo bajo customary A=4.49881E-8,B=-3.54898812E-4,
     C=1.02113262; grupo alto customary A=6.79176E-8,B=-4.0641418E-4,
     C=1.02413769; grupo bajo metrico A=1.45710416E-7,B=-6.33413411E-4,
     C=1.00946841; grupo alto metrico A=2.19965983E-7,B=-7.23435153E-4,
     C=1.010802.
  Ademas hay una 3ra salida (`fuera_de_rango_09`, bool) -- CONFIRMADO por
  decompilacion que se activa cuando el input cae DENTRO del rango
  extendido pero FUERA del rango original de `_09_*` (API>34.9 o T<0/T>500
  customary; densidad<850 o T<-25/T>275 metrico -- el umbral real de T alto
  metrico es 275 EXACTO, no 274.5 como el rango de pantalla de `_09_M`,
  confirmado por barrido empirico). Interpretacion funcional (evidencia
  dura): "el resultado usa el rango extendido, fuera de lo que cubria
  D4311-09" -- la ETIQUETA real en la UI (si la tiene) no se pudo confirmar
  (ver PENDIENTE, sin pantalla propia encontrada).

===============================================================================
FASE 4/5 -- PANTALLA REAL (uiautomator, AVD `flowxpert_rd`, RONDA 47)
===============================================================================
Requirio recuperar el AVD (colgado igual que RONDA 46 -- `adb devices`
"device" pero shell sin respuesta): kill de `qemu-system-x86_64.exe`/
`emulator.exe` + reinicio `-no-snapshot -no-boot-anim -no-audio` (SIN
necesitar restaurar backup de `.qcow2`, la imagen viva arranco limpia en
~40s) -- app+datos siguieron instalados.

Menu raiz -> categoria "ASTM": CONFIRMADO [CERTAIN] por lectura completa del
arbol de UI (ListView `[0,72][320,640]`, sin `scrollable=true`, 3 items que
terminan en y=226 muy por debajo del limite de pantalla y=640 -- NO hay
scroll pendiente, NO hay items ocultos) que la categoria tiene EXACTAMENTE
3 pantallas: "ASTM D1550 CTL", "ASTM D1550 Rel. Density @60F" (RONDA 45) y
**"ASTM D4311M (2009)"** -- y SOLO esta ultima. Al abrirla, sus campos
("Density @15°C" kg/m3, selector de unidad SOLO kg/m3/g/cc/lb/ft3 -- SIN
opcion de API gravity) confirman que es EXCLUSIVAMENTE `ASTM_D4311M_09_M`
(la variante METRICA de 2009). **HALLAZGO CONFIRMADO EN VIVO, no fabricado**:
`ASTM_D4311M_09_C` (customary, API gravity) y las 2 funciones sin sufijo
(`ASTM_D4311C`/`ASTM_D4311M`, "2015") NO TIENEN pantalla propia en esta
version de la app -- existen en el binario (confirmado por decompilacion) y
son llamables por ctypes/oraculo, pero NO son alcanzables por el usuario
final vía la UI Android. Mismo patron ya documentado para `GPA2172_96_C/M`
(RONDA 46, funciones "legado" sin pantalla) pero en sentido inverso: aqui es
la version MAS SIMPLE Y ANTIGUA (customary 2009) y las MAS NUEVAS (2015) las
que quedaron sin pantalla, mientras que la metrica 2009 SI la tiene.

Campos confirmados en vivo de "ASTM D4311M (2009)":
  Density @15°C: kg/m3 (selector real: kg/m3, g/cc, lb/ft3 -- SIN mas
    opciones), Range mostrado en pantalla **"850 .. 1200"** (NO "800..1200"
    del manual -- la app coincide con el nucleo matematico real, no con el
    texto del manual), default 966 kg/m3.
  Temperature: CORREGIDO en RONDA 54 (2026-09-16) -- SI tiene selector real
    de unidad (RONDA 47 solo vio "degree celsius" listado en el dialogo,
    nunca toco el Spinner "Unit" en si para abrir la lista completa). El
    Spinner real ofrece 4 opciones K/°C/°F/R, nativo °C, Range "-25 .. 274.5"
    en esa unidad nativa, default 15°C. Implementado en
    `interfaz_calculo_flujo.py` reusando `API_TEMPERATURA_A_DEGC`
    (`unidades_fisicas.py`, mismo selector ya usado por API Table-59/60
    2004 y NX-19).
  Resultado: CTL (unico output visible, 6 decimales).

FASE 5 -- 2 casos reales EN VIVO:
  1. Densidad=966kg/m3, T=15°C (default) -> CTL=1.000000.
  2. Densidad=900kg/m3, T=200°C -> CTL=0.874913.
Los 2 reproducen EXACTO (`python -m normas.ASTM_D4311`) contra este porte Y
contra el oraculo `.xll` directo (`d4311_09_m(200.0,900.0)` = 0.8749134...).

===============================================================================
VALIDACION [CERTAIN, aritmetica] -- `normas/_sweep_astm_d4311.py`
===============================================================================
400 casos aleatorios por funcion (incluye zona valida Y fuera de rango)
contra el oraculo `.xll` directo (`normas/_astm_d4311_xll_directo.py`,
ctypes, RVA+LoadLibraryW, sin Excel/emulador) -- 400/400 OK en las 4
funciones (Ctl a precision de maquina cuando status=0, status no-cero
coincide en signo cuando corresponde). SOLO la pantalla de `_09_M` tiene
ademas 2 casos reales "de pantalla" (ver Fase 5); las otras 3 funciones
quedan validadas EXCLUSIVAMENTE por decompilacion+oraculo, sin pantalla
propia que las ejercite -- documentado honesto, no fabricado.

===============================================================================
PENDIENTE HONESTO (no fabricado)
===============================================================================
1. `ASTM_D4311M_09_C` (customary 2009), `ASTM_D4311C`/`ASTM_D4311M` (2015,
   sin sufijo): SIN pantalla propia confirmada en vivo (busqueda exhaustiva
   de la categoria "ASTM" completa, sin scroll pendiente) -- se exponen
   igual como funciones publicas de Python (aritmetica [CERTAIN] via
   oraculo) por si el usuario las necesita programaticamente o si una
   version futura de la app las expone, pero NO se agrega pestaña de GUI
   para ellas (no hay pantalla real que replicar sin inventar campos).
2. La etiqueta REAL en la UI del 3er input entero (modo 1/2) de
   `ASTM_D4311C`/`ASTM_D4311M` NO se pudo determinar (sin pantalla). Se
   expone en Python como `modo` con la semantica CONFIRMADA por decompilacion
   (1=constantes D4311-09 originales, 2=constantes refinadas) documentada
   arriba, sin inventar un nombre de etiqueta que la app no mostro.
3. El significado exacto de la salida `fuera_de_rango_09` (3er campo de las
   2 funciones sin sufijo) es una interpretacion funcional respaldada por
   evidencia dura (activa exactamente cuando el input excede el rango
   original de D4311-09) pero SIN confirmar su etiqueta literal en pantalla.
4. Status=2 ("Calculation error") nunca se observo en ningun barrido (la
   formula es polinomial simple, sin division/raiz) -- se mapea el codigo
   por si el nucleo real lo usa en algun input no explorado, sin fabricar
   un caso que lo dispare.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Constantes reales (extraidas por decompilacion + confirmadas por oraculo
# `.xll`, ver docstring del modulo).
# ---------------------------------------------------------------------------

# 2009 / modo=1 de las funciones sin sufijo (BIT-IDENTICAS).
_09_C_LOW = (4.4988e-8, -3.549e-4, 1.021133)          # API<=14.9
_09_C_HIGH = (6.7918e-8, -4.06414e-4, 1.0241379)      # 14.9<API<=34.9(/45)
_09_M_LOW = (1.4571e-7, -6.3341e-4, 1.00946793)       # densidad>=966
_09_M_HIGH = (2.1997e-7, -7.23438e-4, 1.01080222)     # 850(/800)<=dens<966

# 2015 / modo=2 (constantes refinadas).
_2015_C_LOW = (4.49881e-8, -3.54898812e-4, 1.02113262)
_2015_C_HIGH = (6.79176e-8, -4.0641418e-4, 1.02413769)
_2015_M_LOW = (1.45710416e-7, -6.33413411e-4, 1.00946841)
_2015_M_HIGH = (2.19965983e-7, -7.23435153e-4, 1.010802)

# Umbrales de grupo (compartidos por 09 y las 2 versiones de 2015).
_API_GROUP = 14.9
_API_FLAG_09 = 34.9         # "extendido" en 2015 si API>34.9
_DENS_GROUP = 966.0
_DENS_FLAG_09 = 850.0       # "extendido" en 2015 si densidad<850

# Rangos validos NUCLEO real (2009, distintos del rango de pantalla).
_09_C_T_MIN, _09_C_T_MAX = 0.0, 500.0
_09_M_T_MIN, _09_M_T_MAX = -25.0, 274.5
_09_M_DENS_MIN = 850.0      # NUCLEO real -- pantalla del manual dice 800

# Rangos validos NUCLEO real (2015, extendidos, con piso Y techo validados).
_2015_C_API_MIN, _2015_C_API_MAX = 0.0, 45.0
_2015_C_T_MIN, _2015_C_T_MAX = -50.0, 700.0
_2015_M_DENS_MIN, _2015_M_DENS_MAX = 800.0, 1200.0
_2015_M_T_MIN, _2015_M_T_MAX = -50.0, 400.0
_2015_C_T_FLAG_LOW, _2015_C_T_FLAG_HIGH = 0.0, 500.0
_2015_M_T_FLAG_LOW, _2015_M_T_FLAG_HIGH = -25.0, 275.0


def _poly(t: float, coef: tuple) -> float:
    a, b, c = coef
    return a * t * t + b * t + c


def astm_d4311_09_c(api60: float, t_f: float) -> dict:
    """`ASTM_D4311M_09_C` -- NO tiene pantalla propia confirmada en la app
    (ver PENDIENTE del modulo); expuesta por si se necesita programatica.
    [CERTAIN] aritmetica, validada 400 casos vs oraculo `.xll`.

    api60: "API gravity at 60F", adimensional (rango pantalla 0..34.9; el
        nucleo real NO valida el piso, acepta valores negativos igual).
    t_f: "Observed temperature", °F (rango 0..500).

    Devuelve dict: status (0 OK/1 fuera de rango/2 error calc), ctl."""
    if api60 <= _API_GROUP:
        coef = _09_C_LOW
    elif api60 <= _API_FLAG_09:
        coef = _09_C_HIGH
    else:
        return {"status": 1, "ctl": 0.0}
    if not (_09_C_T_MIN <= t_f <= _09_C_T_MAX):
        return {"status": 1, "ctl": 0.0}
    return {"status": 0, "ctl": _poly(t_f, coef)}


def astm_d4311_09_m(dens15c: float, t_c: float) -> dict:
    """`ASTM_D4311M_09_M` -- UNICA pantalla real confirmada de esta familia
    ("ASTM D4311M (2009)", categoria ASTM). [CERTAIN], 2 casos reales de
    pantalla + 400 casos vs oraculo `.xll`.

    dens15c: "Density at 15°C", kg/m3 (rango REAL de pantalla 850..1200,
        confirmado en vivo -- el manual dice 800..1200 pero el nucleo
        matematico y la app coinciden en 850 como piso real).
    t_c: "Observed temperature", °C (rango -25..274.5).

    Devuelve dict: status (0 OK/1 fuera de rango/2 error calc), ctl."""
    if dens15c >= _DENS_GROUP:
        coef = _09_M_LOW
    elif dens15c >= _09_M_DENS_MIN:
        coef = _09_M_HIGH
    else:
        return {"status": 1, "ctl": 0.0}
    if not (_09_M_T_MIN <= t_c <= _09_M_T_MAX):
        return {"status": 1, "ctl": 0.0}
    return {"status": 0, "ctl": _poly(t_c, coef)}


def astm_d4311_c(api60: float, t_f: float, modo: int = 1) -> dict:
    """`ASTM_D4311C` (sin sufijo, "2015" en la app segun RONDA 43 -- SIN
    pantalla propia confirmada, ver PENDIENTE del modulo). [CERTAIN]
    aritmetica (400 casos vs oraculo `.xll`); [LIKELY] la etiqueta real de
    `modo` en una eventual UI (sin poder confirmarla, sin pantalla).

    api60: "API gravity", adimensional (rango extendido 0..45, CON piso Y
        techo validados por el nucleo, a diferencia de `_09_c`).
    t_f: temperatura, °F (rango extendido -50..700).
    modo: 1 = constantes originales D4311-09 (bit-identicas a
        `astm_d4311_09_c` en el rango original) | 2 = constantes refinadas
        ("2015"). Cualquier otro valor -> status=1.

    Devuelve dict: status (0 OK/1 fuera de rango o modo invalido/2 error
    calc), ctl (default 1.0 si status!=0, distinto del default 0.0 de
    `_09_c` -- comportamiento real confirmado por oraculo), fuera_de_rango_09
    (bool -- True si el input cae fuera del rango ORIGINAL que cubria
    D4311-09, dentro del rango extendido de esta version; ver docstring del
    modulo para la evidencia)."""
    if modo not in (1, 2):
        return {"status": 1, "ctl": 1.0, "fuera_de_rango_09": False}
    if not (_2015_C_API_MIN <= api60 <= _2015_C_API_MAX
            and _2015_C_T_MIN <= t_f <= _2015_C_T_MAX):
        return {"status": 1, "ctl": 1.0, "fuera_de_rango_09": False}
    low, high = (_09_C_LOW, _09_C_HIGH) if modo == 1 else (_2015_C_LOW, _2015_C_HIGH)
    coef = low if api60 <= _API_GROUP else high
    ctl = _poly(t_f, coef)
    fuera_09 = (api60 > _API_FLAG_09
                or t_f < _2015_C_T_FLAG_LOW or t_f > _2015_C_T_FLAG_HIGH)
    return {"status": 0, "ctl": ctl, "fuera_de_rango_09": fuera_09}


def astm_d4311_m(dens15c: float, t_c: float, modo: int = 1) -> dict:
    """`ASTM_D4311M` (sin sufijo, "2015" en la app segun RONDA 43 -- SIN
    pantalla propia confirmada, ver PENDIENTE del modulo). [CERTAIN]
    aritmetica (400 casos vs oraculo `.xll`); [LIKELY] la etiqueta real de
    `modo` en una eventual UI.

    dens15c: "Density at 15C", kg/m3 (rango extendido 800..1200 -- CIERRA
        el hueco 800-850 que tenia `_09_m`).
    t_c: temperatura, °C (rango extendido -50..400).
    modo: 1 = constantes originales D4311-09 (bit-identicas a
        `astm_d4311_09_m` en el rango original) | 2 = constantes refinadas.

    Devuelve dict: status, ctl (default 1.0 si status!=0), fuera_de_rango_09
    (bool, True si el input excede el rango original de D4311-09 -- para
    metrico el umbral real de T alto es 275°C exacto, NO 274.5 como en la
    pantalla de `_09_m`, confirmado por barrido empirico)."""
    if modo not in (1, 2):
        return {"status": 1, "ctl": 1.0, "fuera_de_rango_09": False}
    if not (_2015_M_DENS_MIN <= dens15c <= _2015_M_DENS_MAX
            and _2015_M_T_MIN <= t_c <= _2015_M_T_MAX):
        return {"status": 1, "ctl": 1.0, "fuera_de_rango_09": False}
    low, high = (_09_M_LOW, _09_M_HIGH) if modo == 1 else (_2015_M_LOW, _2015_M_HIGH)
    coef = low if dens15c >= _DENS_GROUP else high
    ctl = _poly(t_c, coef)
    fuera_09 = (dens15c < _DENS_FLAG_09
                or t_c < _2015_M_T_FLAG_LOW or t_c > _2015_M_T_FLAG_HIGH)
    return {"status": 0, "ctl": ctl, "fuera_de_rango_09": fuera_09}


if __name__ == "__main__":
    ok = True

    # Casos reales EN VIVO (RONDA 47, uiautomator, AVD flowxpert_rd,
    # pantalla "ASTM D4311M (2009)" -- la UNICA de esta familia con
    # pantalla propia confirmada).
    casos_reales_09m = [
        dict(dens15c=966.0, t_c=15.0, esperado=1.000000),
        dict(dens15c=900.0, t_c=200.0, esperado=0.874913),
    ]
    for i, caso in enumerate(casos_reales_09m, 1):
        esperado = caso.pop("esperado")
        r = astm_d4311_09_m(**caso)
        diff = abs(r["ctl"] - esperado)
        marca = "OK" if diff < 5e-7 and r["status"] == 0 else "FALLO"
        if marca == "FALLO":
            ok = False
        print(f"09_M caso real {i}: ctl={r['ctl']:.6f} esperado={esperado:.6f} "
              f"diff={diff:.2e} [{marca}]")

    # Autotest 09_C (contra oraculo `.xll`, sin pantalla propia).
    casos_09c = [
        dict(api60=20.0, t_f=60.0, esperado=0.9999975648),
        dict(api60=10.0, t_f=60.0, esperado=1.0000009568),
        dict(api60=0.0, t_f=0.0, esperado=1.021133),
    ]
    for i, caso in enumerate(casos_09c, 1):
        esperado = caso.pop("esperado")
        r = astm_d4311_09_c(**caso)
        diff = abs(r["ctl"] - esperado)
        marca = "OK" if diff < 1e-6 and r["status"] == 0 else "FALLO"
        if marca == "FALLO":
            ok = False
        print(f"09_C caso {i}: ctl={r['ctl']:.7f} esperado={esperado:.7f} [{marca}]")

    # Autotest 2015_C modo1==09_C bit-a-bit, modo2 refinado, flag extendido.
    r_modo1 = astm_d4311_c(20.0, 60.0, 1)
    r_09 = astm_d4311_09_c(20.0, 60.0)
    marca = "OK" if abs(r_modo1["ctl"] - r_09["ctl"]) < 1e-12 else "FALLO"
    if marca == "FALLO":
        ok = False
    print(f"2015_C modo1==09_C: {r_modo1['ctl']!r} vs {r_09['ctl']!r} [{marca}]")

    r_ext = astm_d4311_c(40.0, 60.0, 1)
    marca = "OK" if r_ext["status"] == 0 and r_ext["fuera_de_rango_09"] else "FALLO"
    if marca == "FALLO":
        ok = False
    print(f"2015_C api=40 (extendido): status={r_ext['status']} "
          f"fuera_09={r_ext['fuera_de_rango_09']} [{marca}]")

    print("TODOS OK" if ok else "HAY FALLOS")
