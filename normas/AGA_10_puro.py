# -*- coding: utf-8 -*-
"""
normas/AGA_10_puro.py
=======================
Version 100% Python puro de `calcular_velocidad_sonido_y_fpv()` (ver
`normas/AGA_10.py`), pensada especificamente para un despliegue WEB (ej.
Linux, un contenedor, un servicio sin GUI) donde NO se puede depender de
`FlowXpert.xll` (Windows, cargado con `ctypes.WinDLL`+`pefile` en
`normas/_aga10_xll_directo.py`) ni del emulador Unicorn del `.so` de Android
(`normas/_aga10_emulador.py`, requiere `pip install unicorn` + el binario).

DECISION DE DISEÑO EXPLICITA (pedida por el usuario, 2026-08-31): este
modulo NUNCA intenta esos 2 caminos, ni siquiera como respaldo silencioso
dentro de un try/except. Si el solver de flujo critico no converge, el
campo correspondiente se devuelve como NaN explicito con un aviso en el
dict de salida -- nunca se fabrica un numero ni se recurre al binario.

`normas/AGA_10.py` (el modulo de escritorio, con la cadena de 3 caminos
.xll/puro_python/Unicorn para "Critical Flow") NO se modifico y sigue
siendo la version valida para la interfaz Tkinter -- este archivo es una
alternativa standalone, no un reemplazo del modulo de escritorio.

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
PASO 1 -- Importar la unica funcion publica que hace falta:
    from normas.AGA_10_puro import calcular_velocidad_sonido_y_fpv

PASO 2 -- Armar el diccionario de COMPOSICION del gas. Las claves son los
nombres de componente ya usados en TODO este proyecto (ver `NOMBRES_
COMPONENTES` en `normas/AGA_8.py` para la lista completa de 21 nombres
validos: Metano, Etano, Propano, Isobutano, n-Butano, Isopentano,
n-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano, n-Decano, Hidrogeno,
Oxigeno, Nitrogeno, CO2, CO, Agua, H2S, Helio, Argon). Los valores pueden
ser fraccion molar (suma 1.0) O porcentaje (suma 100) -- el modulo
normaliza solo, no hace falta que sumen exacto:
    composicion = {
        "Metano": 96.5222, "Etano": 1.8186, "Propano": 0.4596,
        "Isobutano": 0.1002, "n-Butano": 0.1015, "Isopentano": 0.0466,
        "n-Pentano": 0.0339, "n-Hexano": 0.0489,
        "Nitrogeno": 0.2595, "CO2": 0.5904,
    }

PASO 3 -- Definir condiciones de FLUJO (T_K en Kelvin, P_kPa en kilopascal
absolutos) y, si hace falta Fpv, tambien las condiciones BASE/referencia
(por defecto 288.7056 K / 101.325 kPa, el estandar ya usado en toda la
familia AGA-8/AGA-10/GERG de este proyecto -- normalmente no hay que
tocarlas):
    T_K = 288.15       # 15 grados Celsius
    P_kPa = 5000.0      # 50 bar(a)

PASO 4 -- Llamar la funcion. `calcular_flujo_critico=True` es OPCIONAL y
mas lento (activa el solver iterativo de Critical Flow Factor) -- dejalo
en `False` (el default) si solo necesitas Z/Fpv/velocidad del sonido/
propiedades termicas:
    resultado = calcular_velocidad_sonido_y_fpv(
        composicion, T_K, P_kPa, calcular_flujo_critico=True)

PASO 5 -- Leer los resultados del dict devuelto (37 campos en total, ver
la lista completa en la seccion "QUE HACE ESTE MODULO" mas abajo). Los mas
usados:
    resultado["Z_flujo"]              # Compresibilidad en condicion de flujo
    resultado["Fpv"]                  # Factor de supercompresibilidad
    resultado["W_m_s"]                # Velocidad del sonido, m/s
    resultado["critical_flow_factor"] # Solo si calcular_flujo_critico=True
    resultado["metodo_critical_flow"] # de donde salio ese numero (ver Paso 6)

PASO 6 -- SIEMPRE revisar 2 campos de aviso antes de confiar el resultado a
un uso real/fiscal (nunca son excepciones, viajan junto al numero):
    resultado["rango_aga10"]["rango_combinado"]  # "Normal"/"Extendido"/
                                                  # "Fuera de rango"
    resultado["aviso_no_convergencia_critical_flow"]  # None si todo OK, o
                                                  # un texto explicando por
                                                  # que Critical Flow dio NaN
Si `critical_flow_factor` sale NaN (`float('nan')`, se compara con
`valor != valor`), es una zona donde ni el algoritmo real converge -- ver
la seccion "LIMITE FISICO/MATEMATICO CONOCIDO" mas abajo, no es un bug.

Ejemplo COMPLETO, listo para copiar y correr (`python -m normas.AGA_10_puro`
tambien corre un autotest parecido a este):
    from normas.AGA_10_puro import calcular_velocidad_sonido_y_fpv
    r = calcular_velocidad_sonido_y_fpv(
        composicion={"Metano": 96.5222, "Etano": 1.8186, "Propano": 0.4596,
                     "Nitrogeno": 0.2595, "CO2": 0.5904},
        T_K=288.15, P_kPa=5000.0, calcular_flujo_critico=True)
    print(r["Z_flujo"], r["Fpv"], r["critical_flow_factor"])
    print(r["rango_aga10"]["rango_combinado"])

===============================================================================
QUE HACE ESTE MODULO (y de donde sale cada parte)
===============================================================================
1. Z / Fpv / densidades base y de flujo / Cp / Cv / Cp0 / Cv0 / H0 / H / S /
   densidad relativa (ideal y real): calculo IDENTICO al "fast path" de
   `normas/AGA_10.py` (`calcular_velocidad_sonido_y_fpv()` con
   `calcular_flujo_critico=False`) -- usa UNICAMENTE `normas/AGA_8.py`
   (DensityDetail/PropertiesDetail/calcular_propiedades, motor AGA8-DETAIL,
   ya 100% Python puro, sin mas dependencia que `math`) mas los offsets
   empiricos aditivos por componente para H0/H/S
   (`_OFFSET_H_KJ_KG_POR_COMPONENTE`/`_OFFSET_S_KJ_KGC_POR_COMPONENTE`).
   Validado <0.006% tipico contra los 8 casos reales de
   `normas/test_aga10_caso_real.py` (ver seccion de validacion abajo).

2. `critical_flow_factor` / `isentropic_ideal_Cstar` / `isentropic_real_Cstar`:
   `isentropic_ideal_Cstar`/`isentropic_real_Cstar` son formulas cerradas
   (una sola evaluacion de AGA8-DETAIL, sin iteracion) -- copiadas tal cual
   de `AGA_10.py` (`_cstar_ideal`/`_cstar_real`), YA eran 100% Python puro
   ahi tambien. `critical_flow_factor` llama UNICAMENTE a
   `normas/_aga10_puro_python.py` (`calcular_critical_flow_factor_puro()`,
   el porte Newton-Raphson amortiguado del solver real `AGA10::crit`,
   validado 32/32=100% en el rango real de medicion de gas -- ver seccion
   de confianza abajo). Si no converge, devuelve NaN y un aviso explicito
   en `aviso_no_convergencia_critical_flow` -- NUNCA intenta `.xll` ni
   Unicorn, ni como fallback.

3. `validar_rango_aga10()`: identica a la de `AGA_10.py` (pura logica de
   composicion/T/P, sin ninguna dependencia binaria -- confirmado al leer
   su codigo fuente, solo usa aritmetica y `NOMBRES_COMPONENTES` de
   `AGA_8.py`), reincluida aqui para avisar cuando una entrada cae fuera de
   "Normal"/"Extendido".

===============================================================================
DUPLICACION DELIBERADA respecto a `AGA_10.py` (no es un descuido)
===============================================================================
Los offsets de H0/H/S por componente, `_cstar_ideal`/`_cstar_real` y
`validar_rango_aga10()` estan COPIADOS aqui, no importados de `AGA_10.py`.
Se hizo asi a proposito, pese a que tecnicamente importar esas funciones
puntuales de `AGA_10.py` tambien seria seguro (los imports de `ctypes`/
`pefile`/`unicorn` en ese archivo son TODOS locales, dentro del cuerpo de
`calcular_velocidad_sonido_y_fpv()`, solo se ejecutan si
`calcular_flujo_critico=True` -- nunca al hacer `import normas.AGA_10`) --
la razon es mantener la cadena de imports de ESTE archivo trivialmente
auditable: un `grep` de este archivo + sus 2 unicas dependencias reales
(`_aga10_puro_python.py`, `AGA_8.py`) basta para confirmar la ausencia total
de rastros de Windows/binario, sin tener que razonar sobre imports
condicionales de un tercer archivo. El costo es mantenimiento manual: si se
recalibra algun offset o el rango de `AGA_10.py` en el futuro, hay que
replicar el cambio aqui a mano. Confirmado sin diferencias con `AGA_10.py`
al momento de crear este archivo (2026-08-31).

===============================================================================
DIFERENCIA DE PRECISION CONOCIDA (no se oculta): H0/H/S/Cp0/Cp/Cv
===============================================================================
`AGA_10.py`, cuando `calcular_flujo_critico=True` Y el camino binario
(.xll o Unicorn) esta disponible, SOBREESCRIBE H0/H/S/Cp0/Cp/Cv con los
valores EXACTOS que vienen de los offsets 37-42 del struct de `AGA10::crit`
(confirmados <0.0001% contra 7 casos reales, ver `_aga10_emulador.py`) --
esa refinacion SOLO existe si se ejecuta el binario real. Este modulo NUNCA
ejecuta el binario, asi que SIEMPRE usa el valor empirico del offset por
componente (el "fast path"), incluso cuando `calcular_flujo_critico=True`.
Esto se documenta explicitamente en el campo de salida
`precision_h_s_cp_cv` de cada resultado, para que ningun consumidor futuro
asuma por error que tiene la refinacion exacta. Precision ya validada del
fast path (ver `AGA_10.py`, actualizaciones 2026-07-25/2026-08-03 y
`test_aga10_caso_real.py`): tipicamente <0.006%, con el peor caso conocido
("Dry Air", antes de calibrar O2/Ar/Argon por componente) en 0.0056% de
error en S tras la calibracion -- todos por debajo del 0.01% usado como
umbral de "OK" en los tests del proyecto.

===============================================================================
NIVEL DE CONFIANZA DE critical_flow_factor (Python puro) -- CITA LA FUENTE
===============================================================================
[CERTAIN] Segun `normas/_aga10_puro_python.py` (docstring, seccion "NIVEL DE
CONFIANZA -- BARRIDO DE VALIDACION 2026-08-31") y el barrido
`normas/_sweep_aga10_puro_python.py` (107 casos, comparados contra el
oraculo `.xll` directo):
  - Rango REAL de medicion de gas natural (mezclas realistas hasta
    100 degC/200 bar(a)): 32/32 = 100% exacto.
  - Cualquier condicion "Normal" segun `validar_rango_aga10()` (incluye
    componentes puros y T/P menos tipicos): 18/21 = 85.7%. Los 3 residuos
    son composiciones "Normal segun el chequeo oficial" pero ya conocidas
    como numericamente caoticas en la practica (Default/GasRicoCO2/
    GasRicoN2 a 200 degC/800 bar(a), ver docstring de `AGA_10.py` y de
    `_aga10_puro_python.py`).
  - Los 107 casos completos (incluye a proposito condiciones muy fuera de
    rango): 77/107 = 72.0%.
En la zona caotica (fuera del rango normal de operacion, o cerca de sus
bordes) NINGUN metodo -- ni este porte, ni el `.xll` real, ni el emulador
Unicorn -- puede garantizar coincidir entre si (el propio binario real es
sensible a perturbaciones de 1 ULP en esa zona, ver "INVESTIGACION DE CAUSA
RAIZ 2026-08-31" en `_aga10_xll_directo.py`) -- este modulo refleja esa
realidad devolviendo NaN quando el solver no converge, en vez de fabricar
un numero que pretenda coincidir con un oraculo que ni siquiera coincide
consigo mismo ahi.

===============================================================================
VALIDACION DE ESTE ARCHIVO EN PARTICULAR (2026-08-31)
===============================================================================
`normas/test_aga10_puro_caso_real.py` (copia adaptada de
`normas/test_aga10_caso_real.py` para usar este modulo) corre los 8 casos
reales conocidos -- ver ese archivo para el resultado exacto por caso.
Se espera el MISMO resultado que el fast path de `AGA_10.py` para los 6
campos que no involucran Critical Flow (W, Fpv, Z, Cp, Cv, densidades,
H0/H/S con el offset empirico) en TODOS los casos, y el MISMO resultado que
`_aga10_puro_python.py` para `critical_flow_factor` en los 3 casos que lo
piden (N2/CO2/Etano puros) -- es la misma logica, solo empaquetada sin los
otros 2 caminos.

===============================================================================
QUE NO SE PUEDE HACER CON ESTE MODULO (honesto, no se esconde)
===============================================================================
- No tiene la refinacion exacta de H0/H/S/Cp0/Cp/Cv via offsets binarios
  37-42 (ver seccion de arriba) -- solo el fast path empirico, siempre.
- En la zona caotica/fuera de rango, `critical_flow_factor` puede devolver
  NaN en vez de un numero (nunca un numero fabricado) -- ver nivel de
  confianza arriba (32/32 en rango real, cayendo fuera de el).
- No expone `T_star`/`P_star`/`V_star` del punto sonico si el solver no
  convergio (todos None en ese caso, igual que `_aga10_puro_python.py`).

Uso: python -m normas.AGA_10_puro
"""

import math

from .AGA_8 import (_composicion_a_x, DensityDetail, PropertiesDetail,
                     calcular_propiedades, NOMBRES_COMPONENTES, MM)
from ._aga10_puro_python import calcular_critical_flow_factor_puro

# ===========================================================================
# Copiado tal cual de normas/AGA_10.py (ver seccion "DUPLICACION DELIBERADA"
# arriba) -- offsets aditivos de entalpia/entropia de gas ideal POR
# COMPONENTE, condiciones base tipicas, constantes de aire seco.
# ===========================================================================
_OFFSET_H_KJ_KG_POR_COMPONENTE = {
    "Metano": 624.4533,
    "Nitrogeno": 309.5101,
    "CO2": 212.8027,
    "Etano": 394.4382,
    "Propano": 334.8450,
    "Oxigeno": 271.2764,
    "Argon": 155.1362,
    "Helio": 1548.338,
    "Hidrogeno": 4269.856,
    "CO": 311.5722,
    "Agua": 549.5127,
    "H2S": 267.8250,
    "Isobutano": 308.6811,
    "n-Butano": 331.6875,
    "Isopentano": 304.7218,
    "n-Pentano": 335.0397,
    "n-Hexano": 332.9987,
    "n-Heptano": 331.6196,
    "n-Octano": 330.7567,
    "n-Nonano": 330.1499,
    "n-Decano": 329.3964,
}
_OFFSET_H_KJ_KG_RESIDUAL = 324.0491

_OFFSET_S_KJ_KGC_POR_COMPONENTE = {
    "Metano": 11.61070, "Nitrogeno": 6.83497, "CO2": 4.85527,
    "Etano": 7.61755, "Propano": 6.13024, "Isobutano": 5.08249,
    "n-Butano": 5.33111, "Isopentano": 4.76170, "n-Pentano": 4.84417,
    "n-Hexano": 4.51137, "n-Heptano": 4.27150, "n-Octano": 4.08998,
    "n-Nonano": 3.94822, "n-Decano": 3.83517, "Hidrogeno": 64.80666,
    "Oxigeno": 6.40760, "CO": 7.05316, "Agua": 10.47497,
    "H2S": 6.032846, "Helio": 31.49076, "Argon": 3.87348,
}
_OFFSET_S_KJ_KGC = 10.14724

TB_DEFAULT_K = 288.7056   # 60 F
PB_DEFAULT_KPA = 101.325  # 14.696 psia

MM_AIRE = 28.9625
COMPOSICION_AIRE_SECO = {"Nitrogeno": 78.09, "Oxigeno": 20.95, "Argon": 0.93, "CO2": 0.04}


def _offset_h_kj_kg(x) -> float:
    """[USO INTERNO -- no llamar directo, la usa `calcular_velocidad_sonido_
    y_fpv()` mas abajo] Calcula el offset aditivo de entalpia (kJ/kg) que
    hay que sumarle al valor "crudo" de AGA8-DETAIL para que coincida con
    la convencion real de FlowXpert (cada gas tiene una referencia de
    entalpia distinta, FlowXpert usa un promedio ponderado por masa entre
    los offsets conocidos de cada componente puro).

    Parametros: `x` -- lista de 22 posiciones (indice 0 sin usar, 1-21 son
    los 21 componentes en el MISMO orden que `NOMBRES_COMPONENTES` de
    `normas/AGA_8.py`), cada posicion con la fraccion molar (0.0-1.0) de
    ese componente. Normalmente no arma esta lista a mano -- sale de
    `_composicion_a_x()` (ver `normas/AGA_8.py`), que ya se llama
    automaticamente dentro de `calcular_velocidad_sonido_y_fpv()`.

    Devuelve: el offset en kJ/kg (float), listo para sumar a H0/H.
    Identica a `AGA_10._offset_h_kj_kg` -- ver docstring de ese modulo."""
    masa_total = sum(x[i] * MM[i] for i in range(1, 22))
    if masa_total <= 0:
        return _OFFSET_H_KJ_KG_RESIDUAL
    offset = 0.0
    for i in range(1, 22):
        if x[i] <= 0:
            continue
        w_i = x[i] * MM[i] / masa_total
        delta_i = _OFFSET_H_KJ_KG_POR_COMPONENTE.get(NOMBRES_COMPONENTES[i - 1],
                                                       _OFFSET_H_KJ_KG_RESIDUAL)
        offset += w_i * delta_i
    return offset


def _offset_s_kj_kgc(x) -> float:
    """[USO INTERNO -- no llamar directo] Igual que `_offset_h_kj_kg()`
    pero para el offset de entropia (kJ/kg-degC) en vez de entalpia --
    mismo parametro `x` (lista de 22 posiciones, fraccion molar por
    componente), mismo uso automatico dentro de
    `calcular_velocidad_sonido_y_fpv()`. Identica a
    `AGA_10._offset_s_kj_kgc` -- ver docstring de ese modulo."""
    masa_total = sum(x[i] * MM[i] for i in range(1, 22))
    if masa_total <= 0:
        return _OFFSET_S_KJ_KGC
    offset = 0.0
    for i in range(1, 22):
        if x[i] <= 0:
            continue
        w_i = x[i] * MM[i] / masa_total
        delta_i = _OFFSET_S_KJ_KGC_POR_COMPONENTE.get(NOMBRES_COMPONENTES[i - 1],
                                                        _OFFSET_S_KJ_KGC)
        offset += w_i * delta_i
    return offset


def _cstar_ideal(kappa: float) -> float:
    """SI se puede llamar directo si solo te interesa este numero puntual
    (no hace falta pasar por `calcular_velocidad_sonido_y_fpv()` completo).
    Calcula el "Isentropic ideal C*" -- una formula CERRADA (una sola
    cuenta, sin iterar, sin depender de ningun binario) que solo necesita
    Kappa (la relacion Cp/Cv del gas, adimensional, sale de
    `calcular_velocidad_sonido_y_fpv()["Kappa"]` o de
    `AGA_8.PropertiesDetail()`).

    Devuelve: float. Si Kappa<=1.0 (fisicamente imposible) devuelve NaN
    explicito en vez de crashear. Identica a `AGA_10._cstar_ideal`."""
    if kappa <= 1.0:
        return float("nan")
    try:
        return math.sqrt(kappa) * (2.0 / (kappa + 1.0)) ** ((kappa + 1.0) / (2.0 * (kappa - 1.0)))
    except (ValueError, OverflowError):
        return float("nan")


def _cstar_real(kappa: float, Z: float) -> float:
    """SI se puede llamar directo (igual que `_cstar_ideal()`). Calcula el
    "Isentropic real C*" -- toma Kappa (adimensional) Y Z (factor de
    compresibilidad, adimensional, sale de `PropertiesDetail()["Z"]`).

    Devuelve: float. Si Z<=0 (fisicamente imposible) devuelve NaN explicito
    en vez de crashear con "math domain error". Identica a
    `AGA_10._cstar_real`."""
    if Z <= 0:
        return float("nan")
    return _cstar_ideal(kappa) / math.sqrt(Z)


def validar_rango_aga10(composicion: dict, T_K: float, P_kPa: float) -> dict:
    """SI se puede llamar directo -- util si solo queres saber si una
    entrada esta dentro de rango ANTES de correr el calculo completo (mas
    rapido, no evalua AGA8-DETAIL).

    Parametros:
        composicion: dict {nombre_componente: fraccion_o_porcentaje}. Mismo
            formato que `calcular_velocidad_sonido_y_fpv()` (no hace falta
            que sume exacto 1.0 o 100, se normaliza internamente).
        T_K: temperatura de flujo en Kelvin.
        P_kPa: presion de flujo en kilopascal absolutos.

    Devuelve un dict con 5 claves:
        "valido_entrada": bool -- False si P o T estan fuera del campo de
            entrada literal de la app (0-2000 bar(a), -200 a +400 degC).
        "rango_composicion": "Normal"/"Extendido"/"Fuera de rango (Expandido)"
        "rango_pt": "Dentro de rango"/"Fuera de rango (T/P)"
        "rango_combinado": el peor de los 2 anteriores -- ESTE es el campo
            que normalmente importa mirar.
        "mensaje": texto legible que resume los 3 anteriores.

    Replica el "Range" real de `fxAGA10ex_M` (decompilado, ver docstring de
    `AGA_10.py`, seccion "[CERTAIN -- 2026-08-31, NUEVO...]"). Pura logica
    de composicion/T/P, sin ninguna dependencia binaria. Es INFORMATIVO,
    NUNCA bloquea el calculo (mismo comportamiento que la app real)."""
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion no puede sumar cero.")
    f = {nombre: composicion.get(nombre, 0.0) / total for nombre in NOMBRES_COMPONENTES}

    T_C = T_K - 273.15
    P_bar = P_kPa / 100.0

    valido_entrada = (-200.0 <= T_C <= 400.0) and (0.0 <= P_bar <= 2000.0)
    pt_normal = (-129.0 <= T_C <= 204.0) and (0.0 <= P_bar <= 1379.0)

    butanos = f["Isobutano"] + f["n-Butano"]
    pentanos = f["Isopentano"] + f["n-Pentano"]

    fuera_de_normal = (
        not (0.45 <= f["Metano"] <= 1.0)
        or f["Etano"] > 0.10
        or f["Propano"] > 0.04
        or butanos > 0.01
        or pentanos > 0.003
        or f["n-Hexano"] > 0.002 or f["n-Heptano"] > 0.002 or f["n-Octano"] > 0.002
        or f["n-Nonano"] > 0.002 or f["n-Decano"] > 0.002
        or f["CO"] > 0.03
        or f["CO2"] > 0.30
        or f["Nitrogeno"] > 0.50
        or f["Helio"] > 0.002
        or f["Argon"] > 0.0
        or f["Oxigeno"] > 0.0
        or f["H2S"] > 0.0002
        or f["Hidrogeno"] > 0.10
        or f["Agua"] > 0.0005
    )

    dentro_de_expandido = (
        f["Metano"] <= 1.0 and f["Nitrogeno"] <= 1.0 and f["CO2"] <= 1.0
        and f["Etano"] <= 1.0 and f["Propano"] <= 0.12
        and butanos <= 0.06 and pentanos <= 0.04
        and f["Helio"] <= 0.03 and f["Hidrogeno"] <= 1.0 and f["CO"] <= 0.03
        and f["Argon"] <= 0.01
        and f["Oxigeno"] <= 0.21
        and f["H2S"] <= 1.0
    )

    if not dentro_de_expandido:
        clas_composicion = "Fuera de rango (Expandido)"
    elif fuera_de_normal:
        clas_composicion = "Extendido"
    else:
        clas_composicion = "Normal"

    clas_pt = "Dentro de rango" if pt_normal else "Fuera de rango (T/P)"

    if clas_composicion == "Fuera de rango (Expandido)" or not pt_normal:
        rango_combinado = "Fuera de rango"
    elif clas_composicion == "Extendido":
        rango_combinado = "Extendido"
    else:
        rango_combinado = "Normal"

    mensaje = f"Composicion: {clas_composicion}. T/P: {clas_pt}. Range combinado: {rango_combinado}."
    if not valido_entrada:
        mensaje += (" ADEMAS, T/P esta fuera del campo de entrada propio de AGA-10 "
                    "(0..2000 bar(a), -200..+400 degC) -- la app real probablemente "
                    "ni siquiera aceptaria esta entrada (Status='Input argument out of range').")

    return {
        "valido_entrada": valido_entrada,
        "rango_composicion": clas_composicion,
        "rango_pt": clas_pt,
        "rango_combinado": rango_combinado,
        "mensaje": mensaje,
    }


def calcular_velocidad_sonido_y_fpv(composicion: dict, T_K: float, P_kPa: float,
                                      Tb_K: float = TB_DEFAULT_K, Pb_kPa: float = PB_DEFAULT_KPA,
                                      calcular_flujo_critico: bool = False):
    """FUNCION PRINCIPAL de este modulo -- es la que hay que llamar (ver
    "GUIA DE USO PASO A PASO" al inicio del archivo para un ejemplo
    completo copiar-y-pegar).

    Parametros:
        composicion: dict {nombre_componente: fraccion_o_porcentaje}.
            Claves validas: los 21 nombres de `NOMBRES_COMPONENTES` en
            `normas/AGA_8.py` (Metano, Etano, Propano, Isobutano, n-Butano,
            Isopentano, n-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano,
            n-Decano, Hidrogeno, Oxigeno, Nitrogeno, CO2, CO, Agua, H2S,
            Helio, Argon). Los valores pueden sumar 1.0 (fraccion) o 100
            (porcentaje) indistintamente -- se normaliza solo.
        T_K: temperatura de FLUJO, Kelvin.
        P_kPa: presion de FLUJO, kilopascal absolutos.
        Tb_K: temperatura BASE/referencia, Kelvin (default 288.7056 K =
            15.556 degC, el estandar de FlowXpert). Solo importa si vas a
            usar `Fpv` -- para el resto de los campos (Z_flujo, W_m_s,
            Cp, etc.) es irrelevante.
        Pb_kPa: presion BASE/referencia, kilopascal absolutos (default
            101.325 kPa = 1 atm).
        calcular_flujo_critico: bool, default False. Poner en True SOLO si
            necesitas `critical_flow_factor`/`isentropic_ideal_Cstar`/
            `isentropic_real_Cstar` -- activa el solver iterativo (mas
            lento que el resto del calculo, aunque en Python puro sigue
            siendo del orden de milisegundos, no segundos).

    Devuelve: dict de 37 claves (Mm_g_mol, Z_flujo, Z_base, Fpv, W_m_s,
    densidades, Cp/Cv en 2 unidades, H0/H/S, Kappa, critical_flow_factor,
    rango_aga10, avisos, etc. -- ver el cuerpo de la funcion mas abajo para
    la lista literal de claves en el `return`).

    Equivalente 100% Python puro de
    `normas.AGA_10.calcular_velocidad_sonido_y_fpv()` -- mismos parametros,
    mismas claves de salida (mas 2 nuevas: `precision_h_s_cp_cv` y
    `aviso_no_convergencia_critical_flow`), pensado como reemplazo directo
    para un despliegue web sin `.xll` ni Unicorn. Ver docstring del modulo
    para el detalle completo de que es identico y que difiere.
    """
    x = _composicion_a_x(composicion)

    rango_aga10 = validar_rango_aga10(composicion, T_K, P_kPa)

    Df, ierr_f, _ = DensityDetail(T_K, P_kPa, x)
    prop_flujo = PropertiesDetail(T_K, Df, x)

    Db, ierr_b, _ = DensityDetail(Tb_K, Pb_kPa, x)
    prop_base = PropertiesDetail(Tb_K, Db, x)

    Zf = prop_flujo["Z"]
    Zb = prop_base["Z"]
    Fpv = (Zb / Zf) ** 0.5

    Mm = prop_flujo["Mm_g_mol"]
    rd_ideal = Mm / MM_AIRE
    prop_aire = calcular_propiedades(COMPOSICION_AIRE_SECO, T_K, P_kPa)
    Z_aire = prop_aire["Z"]
    rd_real = rd_ideal * (Z_aire / Zf)

    # [Fast path, siempre -- ver seccion "DIFERENCIA DE PRECISION CONOCIDA"
    # del docstring del modulo] Nunca se sobreescribe con la refinacion
    # exacta de offsets 37-42 (eso requiere binario real).
    Cp_kJ_kgC = prop_flujo["Cp_J_molK"] / Mm
    Cv_kJ_kgC = prop_flujo["Cv_J_molK"] / Mm
    H0_kJ_kg = prop_flujo["H0_J_mol"] / Mm + _offset_h_kj_kg(x)
    H_kJ_kg = prop_flujo["H_J_mol"] / Mm + _offset_h_kj_kg(x)
    S_kJ_kgC = prop_flujo["S_J_molK"] / Mm + _offset_s_kj_kgc(x)
    Cp0_kJ_kgC = prop_flujo["Cp0_J_molK"] / Mm
    Cv0_kJ_kgC = prop_flujo["Cv0_J_molK"] / Mm

    Base_Density_mol_m3 = Db * 1000.0
    Flowing_Density_mol_m3 = Df * 1000.0
    Base_Density_kg_m3 = Db * Mm
    Flowing_Density_kg_m3 = Df * Mm

    precision_h_s_cp_cv = (
        "empirica (fast path, offset aditivo por componente), NO refinada -- "
        "requiere binario (.xll o Unicorn) para el offset exacto via los "
        "campos 37-42 del struct AGA10::crit. Este modulo, por diseno, nunca "
        "ejecuta ese binario. Ver seccion 'DIFERENCIA DE PRECISION CONOCIDA' "
        "en el docstring de normas/AGA_10_puro.py."
    )

    if calcular_flujo_critico:
        kappa_f = prop_flujo["Kappa"]
        isentropic_ideal_Cstar = _cstar_ideal(kappa_f)
        isentropic_real_Cstar = _cstar_real(kappa_f, Zf)

        # [CERTAIN, 2026-08-31] Unico camino permitido para critical_flow_factor
        # en este modulo -- ver seccion "NIVEL DE CONFIANZA" del docstring.
        # Jamas se intenta .xll ni Unicorn, ni como fallback.
        _res_puro = calcular_critical_flow_factor_puro(x, T_K, P_kPa)
        _cff = _res_puro["critical_flow_factor"]
        if _res_puro["convergio"] and _cff == _cff:  # descarta NaN aunque 'convergio' fuera True
            critical_flow_factor = _cff
            metodo_critical_flow = "puro_python_newton"
            aviso_no_convergencia_critical_flow = None
        else:
            critical_flow_factor = float("nan")
            metodo_critical_flow = "no_convergio"
            aviso_no_convergencia_critical_flow = (
                "El solver Python puro del algoritmo real AGA10::crit "
                "(normas/_aga10_puro_python.py) no convergio para esta "
                "composicion/T/P. Por diseno, este modulo NUNCA recurre a "
                ".xll ni a Unicorn como respaldo -- se devuelve NaN explicito "
                "en vez de un numero fabricado. "
                f"rango_aga10.rango_combinado={rango_aga10['rango_combinado']!r}."
            )
    else:
        critical_flow_factor = 0.0
        isentropic_ideal_Cstar = 0.0
        isentropic_real_Cstar = 0.0
        metodo_critical_flow = "no_solicitado"
        aviso_no_convergencia_critical_flow = None

    # Mismo aviso de bug real de FlowXpert que AGA_10.py (Kappa>1.6, gas casi
    # monoatomico) -- informativo, no depende de ningun binario.
    aviso_bug_flowxpert_critical_flow = (
        "Kappa > 1.6 (gas casi monoatomico, ej. Helio/Argon): FlowXpert tiene un bug real "
        "confirmado que da un Critical Flow Factor sin sentido fisico (~87-89) en este rango. "
        "critical_flow_factor replica ese bug tal cual (no es un valor confiable)."
        if calcular_flujo_critico and prop_flujo["Kappa"] > 1.6 else None
    )

    aviso_critical_flow_fuera_de_normal = (
        f"Composicion/T/P fuera de 'Normal' (rango_aga10.rango_combinado="
        f"{rango_aga10['rango_combinado']!r}). En esta zona el solver Python "
        "puro puede no converger (NaN explicito) o, aunque converja, no hay "
        "garantia de coincidir con el binario real -- ver seccion 'NIVEL DE "
        "CONFIANZA' del docstring de normas/AGA_10_puro.py (32/32=100% en el "
        "rango real de medicion de gas, cayendo fuera de el)."
        if calcular_flujo_critico and rango_aga10["rango_combinado"] != "Normal" else None
    )

    return {
        "W_m_s": prop_flujo["W_m_s"],
        "Z_flujo": Zf,
        "Z_base": Zb,
        "Fpv": Fpv,
        "Mm_g_mol": Mm,
        "D_flujo_mol_l": Df,
        "D_base_mol_l": Db,
        "D_base_mol_m3": Base_Density_mol_m3,
        "D_flujo_mol_m3": Flowing_Density_mol_m3,
        "D_base_kg_m3": Base_Density_kg_m3,
        "D_flujo_kg_m3": Flowing_Density_kg_m3,
        "rel_density_ideal": rd_ideal,
        "rel_density_real": rd_real,
        "Cp_kJ_kgC": Cp_kJ_kgC,
        "Cv_kJ_kgC": Cv_kJ_kgC,
        "Cp_kJ_kmolC": Cp_kJ_kgC * Mm,
        "Cv_kJ_kmolC": Cv_kJ_kgC * Mm,
        "Cp0_kJ_kgC": Cp0_kJ_kgC,
        "Cv0_kJ_kgC": Cv0_kJ_kgC,
        "Cp0_kJ_kmolC": Cp0_kJ_kgC * Mm,
        "Cv0_kJ_kmolC": Cv0_kJ_kgC * Mm,
        "H0_kJ_kg": H0_kJ_kg,
        "H_kJ_kg": H_kJ_kg,
        "S_kJ_kgC": S_kJ_kgC,
        "H0_kJ_kmol": H0_kJ_kg * Mm,
        "H_kJ_kmol": H_kJ_kg * Mm,
        "Kappa": prop_flujo["Kappa"],
        "Cp_Cv_ratio": prop_flujo["Cp_J_molK"] / prop_flujo["Cv_J_molK"],
        "critical_flow_factor": critical_flow_factor,
        "isentropic_ideal_Cstar": isentropic_ideal_Cstar,
        "isentropic_real_Cstar": isentropic_real_Cstar,
        "aviso_bug_flowxpert_critical_flow": aviso_bug_flowxpert_critical_flow,
        "aviso_critical_flow_fuera_de_normal": aviso_critical_flow_fuera_de_normal,
        "aviso_no_convergencia_critical_flow": aviso_no_convergencia_critical_flow,
        "precision_h_s_cp_cv": precision_h_s_cp_cv,
        "metodo_critical_flow": metodo_critical_flow,
        "ierr_flujo": ierr_f,
        "ierr_base": ierr_b,
        "rango_aga10": rango_aga10,
    }


if __name__ == "__main__":
    composicion = {
        "Metano": 0.77824, "Nitrogeno": 0.02, "CO2": 0.06, "Etano": 0.08,
        "Propano": 0.03, "Isobutano": 0.0015, "n-Butano": 0.003,
        "Isopentano": 0.0005, "n-Pentano": 0.00165, "n-Hexano": 0.00215,
        "n-Heptano": 0.00088, "n-Octano": 0.00024, "n-Nonano": 0.00015,
        "n-Decano": 0.00009, "Hidrogeno": 0.004, "Oxigeno": 0.005,
        "CO": 0.002, "Agua": 0.0001, "H2S": 0.0025, "Helio": 0.007,
        "Argon": 0.001,
    }
    print("=== normas/AGA_10_puro.py -- autotest ===")
    r = calcular_velocidad_sonido_y_fpv(composicion, 400.0, 50000.0)
    for k, v in r.items():
        print(f"  {k} = {v}")
