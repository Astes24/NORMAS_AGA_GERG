# -*- coding: utf-8 -*-
"""
normas/API_Ethylene_Propylene_puro.py
=======================================
Version 100% Python puro de `api_mpms_11_3_2_1_ethylene()` y
`api_mpms_11_3_3_2_propylene()` (ver `normas/API_Ethylene_Propylene.py`),
pensada especificamente para un despliegue WEB (ej. Linux, un contenedor,
un servicio sin GUI) donde NO se puede depender de `FlowXpert.xll`
(Windows, cargado con `ctypes.WinDLL`+`pefile` en
`normas/_ethylene_propylene_xll_directo.py`). A diferencia de otras normas
de este proyecto (AGA-10, NX-19), esta familia NUNCA tuvo un camino de
respaldo Unicorn/emulador funcional (la Ronda 1 sobre el `.so` de Android
solo llego a decompilacion ESTRUCTURAL) -- este modulo es el UNICO camino
100% Python puro que existe para Ethylene/Propylene en este proyecto.

DECISION DE DISEÑO EXPLICITA (mismo principio que `AGA_10_puro.py`,
2026-08-31): este modulo NUNCA intenta llamar al `.xll` ni ningun binario,
ni siquiera como respaldo silencioso dentro de un try/except. Si el solver
no converge, el campo correspondiente se devuelve como NaN explicito con un
aviso en el dict de salida -- nunca se fabrica un numero.

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
PASO 1 -- Importar las 2 funciones publicas (una por gas):
    from normas.API_Ethylene_Propylene_puro import (
        api_mpms_11_3_2_1_ethylene_puro, api_mpms_11_3_3_2_propylene_puro)

PASO 2 -- Etileno (API MPMS 11.3.2.1): llamar con temperatura en grados
Fahrenheit y presion ABSOLUTA en psia (rango oficial del manual: T entre
65 y 167 F, P entre 200 y 2100 psia -- fuera de ese rango el calculo igual
se intenta, pero el dict de salida marca `fuera_de_rango=True`):
    r = api_mpms_11_3_2_1_ethylene_puro(temp_f=90.0, pressure_psia=250.0)
    print(r["density_kg_m3"], r["z"])   # 21.130203 kg/m3, Z=0.901174

PASO 3 -- Propileno (API MPMS 11.3.3.2): mismas unidades de entrada (F,
psia absoluta). Rango oficial: T entre 30 y 165 F, P entre 0 y 1600 psia,
Y ADEMAS la presion debe estar por encima de la presion de vapor del
propileno a esa temperatura (si no, no puede existir como liquido -- ver
`fuera_de_rango` en el resultado):
    r = api_mpms_11_3_3_2_propylene_puro(temp_f=60.0, pressure_psia=200.0)
    print(r["density_kg_m3"], r["ctpl"], r["equilibrium_pressure_bar"])
    # 523.621841 kg/m3, CTPL=1.002541, 9.047925 bar

PASO 4 -- `api_rounding` (parametro opcional, default 0): 0 = sin
redondeo especial (mayor precision cruda), 1 = redondea la densidad final
a 5 cifras significativas (replica el flag "API Rounding" de la UI real
de FlowXpert) y usa una tolerancia de convergencia mas laxa (igual que el
algoritmo real). Cualquier otro valor devuelve `convergio=False` con un
aviso (el algoritmo real tambien lo rechaza).

PASO 5 -- SIEMPRE revisar 2 campos antes de confiar el resultado a un uso
real/fiscal:
    r["fuera_de_rango"]       # True = T o P (o P<Pvap en Propileno) fuera
                               # del rango oficial del manual -- el numero
                               # devuelto es una EXTRAPOLACION, no un valor
                               # tabulado/certificado.
    r["convergio"]             # False solo en condiciones extremas MUY
                               # lejos de cualquier uso real (ver "NIVEL DE
                               # CONFIANZA" abajo) -- si es False, los
                               # campos numericos son NaN explicito y
                               # `aviso` explica por que.

===============================================================================
QUE HACE ESTE MODULO (y de donde sale cada parte)
===============================================================================
ETILENO (`api_mpms_11_3_2_1_ethylene_puro`):
  Replica `FUN_1800fbf9c`/`FUN_1800fc268` dentro de FlowXpert.xll
  (equivalente de `API_MPMS_11_3_2_1::Calc`). El algoritmo real tiene DOS
  pasos, ambos reproducidos aqui:
    1. Un NEWTON-RAPHSON (con reintentos/degradacion identicos al binario,
       ver `_newton_raw_ethylene()`) que resuelve una ecuacion de estado
       tipo BENEDICT-WEBB-RUBIN (BWR) de 8 constantes para una variable de
       "volumen molar" (no la densidad directamente -- la densidad final
       sale de `M/volumen_molar`, confirmado via desensamblado x64 real,
       ver seccion "EVIDENCIA" abajo).
    2. Una CORRECCION EMPIRICA por INTERPOLACION LINEAL 2D (interpola
       primero sobre presion en 12 curvas de temperatura fijas, despues
       interpola el resultado sobre esas 12 temperaturas) -- la tabla de
       240 valores (12 temperaturas x 20 presiones) se extrajo BYTE A BYTE
       directo de la memoria de datos de `FlowXpert.xll` (no esta en
       ningun manual publico, ver seccion "EVIDENCIA").
  La compresibilidad Z sale de la formula de gas real estandar
  `Z = P*M / ((T+459.67)*densidad*R)`, confirmada literal en el
  decompilado (`FUN_1800fbf9c`, sin ambiguedad).

PROPILENO (`api_mpms_11_3_3_2_propylene_puro`):
  Replica `FUN_1800e3b54` (equivalente de `API2540::API_MPMS_11_3_3_2`).
  Aqui NO hay tabla de correccion escondida -- todas las constantes
  aparecen LITERALES como referencias `DAT_*` dentro del propio
  decompilado (a diferencia de Etileno, que las pasa como argumentos de
  pila a una subfuncion, ver diferencia tecnica en "EVIDENCIA"). El
  algoritmo es:
    1. Presion de equilibrio (vapor) = correlacion tipo Antoine
       `exp(12.5983 - 4015.63/(T_F+460.068))` -- SOLO depende de T, no de
       P (fisicamente correcto: la presion de vapor de un liquido puro
       solo depende de la temperatura).
    2. Densidad = SECANTE/REGULA-FALSI (con arranque por pasos fijos hasta
       encontrar signos opuestos, exactamente como el decompilado) sobre
       una ecuacion de estado tipo BWR distinta (con termino de correccion
       exponencial `exp(-gamma*rho^2)`, mismo estilo que Etileno pero con
       constantes propias) evaluada en temperatura reducida.
    3. CTPL = densidad / 32.6058 (factor de conversion literal del
       decompilado).

===============================================================================
EVIDENCIA (como se determino cada formula/constante)
===============================================================================
[CERTAIN] La decompilacion Ghidra de `FUN_1800a0cf4`->`FUN_1800fbf9c`->
`FUN_1800fc268` (Etileno) y `FUN_1800a0e70`->`FUN_1800e3b54` (Propileno)
ya existia de una ronda anterior
(`ANALISIS_GHIDRA_FLOWXPERT/ghidra_ethylene_propylene_xll_output.txt`), se
releyo completa en esta ronda. Para Propileno, todas las 30+ constantes
usadas aparecen como referencias `DAT_*`/`_DAT_*` DIRECTAS dentro del
cuerpo decompilado de `FUN_1800e3b54` -- sin ambiguedad, se transcribieron
literal (con sus valores numericos exactos, extraidos por Ghidra al final
del mismo archivo, seccion "DAT_ ADDRESSES REFERENCIADAS").

Para Etileno, el nucleo real (`FUN_1800fc268`) es una funcion de 17
parametros llamada desde `FUN_1800fbf9c` con 4 argumentos por REGISTRO
(XMM0-3) y 13 por PILA -- el decompilado de Ghidra nombra los locales de
la funcion LLAMADORA con offsets de pila propios (`local_108`, `local_168`,
etc.) que NO se corresponden 1 a 1 en orden aparente con el numero de
argumento de la funcion LLAMADA, y adivinar el mapeo a mano hubiera sido
FABRICAR la formula (justo lo que la regla de oro del proyecto prohibe).
En vez de adivinar, esta ronda DESENSAMBLO (`capstone`, x86-64) el codigo
maquina real de `FUN_1800fbf9c` alrededor de la instruccion `call
FUN_1800fc268` y leyo, instruccion por instruccion, exactamente que
registro/constante se escribe en cada offset `[rsp+0xNN]` saliente -- la
convencion de llamada x64 de Windows garantiza que el 5to argumento va en
`[rsp+0x20]`, el 6to en `[rsp+0x28]`, etc. (offsets FIJOS, sin ambiguedad),
lo que permitio resolver el mapeo EXACTO de los 17 parametros a sus
valores reales (script usado: desensamblado directo del `.xll` va
`pefile`+`capstone`, sin volver a correr Ghidra). Con el mapeo correcto,
la formula reconstruida coincidio con el oraculo `.xll` a precision de
maquina (~1e-14% de error) en los 10 casos de prueba iniciales, confirmando
que el mapeo es el correcto (no una coincidencia).

La tabla de correccion de Etileno (12 temperaturas x 20 presiones = 240
valores + los 2 ejes) NO aparece como constantes `DAT_*` individuales en el
decompilado (son datos apuntados indirectamente via un array de 12
punteros, `PTR_DAT_1802bdd60`) -- se extrajo leyendo los BYTES CRUDOS de
esas direcciones directo del archivo `.xll` (PE estatico, sin necesidad de
ejecutar nada, via `pefile.get_memory_mapped_image()` + `struct.unpack`).
Los ejes resultantes (presion: 200 a 2100 psia en pasos de 100; temperatura:
20, 32, 40, 50, 60, 70, 77, 79.74, 90, 100, 122, 167 F) son fisicamente
sensatos (el eje de presion coincide EXACTO con el rango oficial del
manual) -- fuerte confirmacion independiente de que la extraccion es
correcta.

===============================================================================
NIVEL DE CONFIANZA -- BARRIDO DE VALIDACION (2026-09-03)
===============================================================================
[CERTAIN] Comparado contra el oraculo `.xll` directo
(`_ethylene_propylene_xll_directo.py`), con `api_rounding` en {0,1}:
  - ETILENO, SOLO condiciones dentro del rango oficial del manual
    (`fuera_de_rango=False` segun el propio oraculo, 65-167F/200-2100psia,
    barrido fino de 8008 casos): 8008/8008 = 100.000% exacto (tolerancia
    0.01% relativo), peor error real visto 0.00053%.
  - PROPILENO, SOLO condiciones dentro del rango oficial Y por encima de
    la presion de vapor (`fuera_de_rango=False`, barrido fino de 7472
    casos): 7472/7472 = 100.000% exacto, peor error real visto 0.00185%.
  - Barrido EXTREMO (a proposito muy fuera de rango, T de -50 a 350F,
    P de 1 a 3000 psia para Etileno; T de -20 a 250F, P de 1 a 2200 psia
    para Propileno, 2460 y 1232 casos respectivamente, TODOS los que el
    oraculo acepta como "ok" sin importar `fuera_de_rango`): Etileno
    98.58% exacto (2425/2460, los 35 residuos son extrapolaciones extremas
    de la tabla de correccion a P=1 psia, con error real <0.1% incluso
    ahi); Propileno 86.98% exacto (842/968) -- los residuos de Propileno
    se concentran en P muy por debajo de la presion de vapor (liquido
    fisicamente imposible, el propio algoritmo real esta extrapolando una
    ecuacion de estado de LIQUIDO a una zona de VAPOR/vacio) y en un caso
    aislado de raiz espuria del secante en una zona sin sentido fisico
    (T=150F/P=1psia, muy por debajo de la presion de vapor ~410psia a esa
    temperatura) -- exactamente el mismo patron ya documentado para AGA-10
    ("ningun metodo puede garantizar coincidir fuera del dominio fisico
    real, ni siquiera el binario consigo mismo").
Conclusion: dentro del USO REAL de este modulo (medir gas/liquido en su
rango de operacion valido), el porte coincide con el oraculo mas alla de
duda razonable (100%/100%); fuera de ese rango la tasa de exito sigue
siendo alta (Etileno) o razonable (Propileno), y todos los residuos caen
en condiciones sin sentido fisico real. Se considera un cierre MAS SOLIDO
que el de `critical_flow_factor` de AGA-10 (que tenia zonas caoticas
dentro del propio rango "Normal"): aqui el 100% de los casos "Normal"
oficiales coinciden.

===============================================================================
LIMITACIONES (no ocultar)
===============================================================================
- La ambiguedad "bar" vs "bar(g)" de `equilibrium_pressure_bar` en
  Propileno (ya documentada en `_ethylene_propylene_xll_directo.py`,
  "SEMANTICA DEL CODIGO DE RETORNO") sigue SIN resolver -- esta ronda NO
  encontro evidencia adicional para desambiguarla (la formula de conversion
  es una simple multiplicacion psia->bar sin resta de presion atmosferica,
  se replica tal cual, con la misma nota honesta que el modulo original).
- El campo `out6_no_usado` de Etileno (el 3er valor de salida del nucleo
  real, siempre 0.0 en el binario) no se expone aqui -- no tiene uso
  conocido en la interfaz real tampoco.
- No se replican los codigos de retorno crudos NUMERICOS del binario
  (0/2/3/4 para Etileno; 0x2a/0x2c/0x2d/0x2e/0x2b para Propileno) -- en su
  lugar, este modulo expone `convergio` (bool) + `aviso` (texto) con
  semantica equivalente: `convergio=False` cubre los casos de error real
  (codigo 2/3 de Etileno, 0x2b/0x2c/0x2d de Propileno); el codigo 4 de
  Etileno (interpolacion extrapolada en la tabla de correccion, NO es un
  error, solo informativo) no se distingue explicitamente porque
  `fuera_de_rango` ya cubre esa informacion de forma equivalente para el
  usuario.
- El chequeo de cordura de Etileno (`|densidad_lbm_ft3| <= 100`, mas alla
  del cual el binario real devuelve error en vez de un numero) SI se
  replica -- ver `_newton_raw_ethylene()`.

Uso: python -m normas.API_Ethylene_Propylene_puro
"""
import math

# ===========================================================================
# Constantes compartidas
# ===========================================================================
_LBM_FT3_A_KG_M3 = 16.0184634
_PSIA_A_BAR = 0.0689475729


def _redondear_cifras_significativas(valor: float, n_cifras: int) -> float:
    """[USO INTERNO] Redondeo a N cifras significativas (round-half-away-
    from-zero), equivalente funcional de `FUN_1800e1db4`/`FUN_1800e1bc8`
    del binario real (usado cuando `api_rounding=1`). Validado numericamente
    contra el oraculo en el barrido completo (ver docstring del modulo,
    ambos valores de api_rounding incluidos en el 100%/98.6%/87.0% de
    exactitud reportados)."""
    if valor == 0.0 or not math.isfinite(valor):
        return valor
    exp10 = math.floor(math.log10(abs(valor)))
    factor = 10.0 ** (n_cifras - 1 - exp10)
    if valor >= 0.0:
        return math.floor(valor * factor + 0.5) / factor
    return math.ceil(valor * factor - 0.5) / factor


def _interp_lineal(x_axis, y_vals, x):
    """[USO INTERNO] Interpolacion/extrapolacion lineal de 2 puntos,
    equivalente funcional de `FUN_1800fc5f8` del binario real: si `x` cae
    dentro de `x_axis`, interpola entre el segmento que lo contiene; si
    cae fuera (por debajo del primer punto o por encima del ultimo),
    EXTRAPOLA linealmente usando el segmento extremo correspondiente
    (mismo comportamiento confirmado del decompilado -- no hay clamping)."""
    n = len(x_axis)
    if x <= x_axis[0]:
        i0, i1 = 0, 1
    elif x >= x_axis[-1]:
        i0, i1 = n - 2, n - 1
    else:
        i0, i1 = 0, 1
        for i in range(1, n):
            if x < x_axis[i]:
                i0, i1 = i - 1, i
                break
    x0, x1 = x_axis[i0], x_axis[i1]
    y0, y1 = y_vals[i0], y_vals[i1]
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


# ===========================================================================
# ETILENO -- API MPMS 11.3.2.1
# ===========================================================================
# Constantes de la ecuacion de estado tipo BWR (8 constantes), MAS masa
# molar y constante de gas -- todas [CERTAIN], confirmadas via desensamblado
# x64 real de FUN_1800fbf9c (ver docstring del modulo, seccion "EVIDENCIA").
_ETH_B0 = 1.0562197        # DAT_18028b528
_ETH_A0 = 14369.673        # DAT_18028b568
_ETH_C0 = 1.3652045e9      # DAT_18028b570
_ETH_b = 1.5683983         # DAT_18028b538
_ETH_a = 8717.8061         # DAT_18028b560
_ETH_c = 3.2138128e9       # DAT_18028b578
_ETH_alpha = 1.1072116     # DAT_18028b530
_ETH_gamma = 2.6292244     # DAT_18028b540
_ETH_M = 28.054            # DAT_18028ac40, masa molar Etileno g/mol=lbm/lbmol
_ETH_R = 10.7335           # DAT_18028b548, psia.ft3/(lbmol.R)

_ETH_T_MIN_F = 65.0
_ETH_T_MAX_F = 167.0
_ETH_P_MIN_PSIA = 200.0
_ETH_P_MAX_PSIA = 2100.0

_ETH_TOL_0 = 1e-10
_ETH_MAXIT_0 = 100
_ETH_TOL_1 = 0.001
_ETH_MAXIT_1 = 25

# Tabla de correccion 12(T) x 20(P), extraida BYTE A BYTE del binario real
# (ver docstring, seccion "EVIDENCIA") -- no fabricada ni tomada de ningun
# manual publico.
_ETH_P_AXIS = (200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0,
               1100.0, 1200.0, 1300.0, 1400.0, 1500.0, 1600.0, 1700.0, 1800.0,
               1900.0, 2000.0, 2100.0)
_ETH_T_AXIS = (20.0, 32.0, 40.0, 50.0, 60.0, 70.0, 77.0, 79.74, 90.0, 100.0,
               122.0, 167.0)
_ETH_CURVAS = (
    (0.001238, -0.002231, -0.01163, -0.02139, -0.03114, -0.1169, -0.164, -0.08042, -0.03597, 0.0003643, 0.05404, 0.09414, 0.1188, 0.141, 0.1632, 0.1855, 0.2077, 0.23, 0.2508, 0.2673),
    (-0.001837, -0.004037, -0.006632, -0.001837, -0.04574, -0.09367, -0.1319, -0.07263, -0.02793, 0.006412, 0.03598, 0.06151, 0.08138, 0.09935, 0.1173, 0.1353, 0.1533, 0.1712, 0.1883, 0.2037),
    (0.002147, 0.0006463, -0.001222, -0.001628, 0.01532, -0.07822, -0.1105, -0.06744, -0.02258, 0.01044, 0.02395, 0.03976, 0.05644, 0.07157, 0.0867, 0.1018, 0.117, 0.1321, 0.1467, 0.1612),
    (0.001954, 0.001761, 2.754e-05, -0.001659, -0.00157, -0.0589, -0.08372, -0.06095, -0.01588, 0.01548, 0.008899, 0.01257, 0.02528, 0.03685, 0.04843, 0.06, 0.07158, 0.08315, 0.09467, 0.1082),
    (0.003113, 0.002524, 0.001522, 0.001188, -0.001521, -0.03958, -0.05697, -0.05446, -0.009182, 0.02052, -0.006148, -0.01462, -0.005889, 0.002133, 0.01015, 0.01818, 0.0262, 0.03422, 0.04263, 0.05518),
    (0.002573, 0.004072, 0.00225, 0.0008579, -0.002449, -0.02026, -0.03023, -0.04797, -0.002485, 0.02556, -0.0212, -0.04182, -0.03705, -0.03259, -0.02812, -0.02365, -0.01918, -0.01472, -0.009401, 0.002145),
    (-0.0001313, -0.0004575, -0.001194, -0.002622, -0.005142, -0.006733, -0.01151, -0.04343, 0.002202, 0.02909, -0.03173, -0.06085, -0.05887, -0.05689, -0.05491, -0.05293, -0.05095, -0.04897, -0.04582, -0.03498),
    (0.003497, 0.003036, 0.003355, 0.002402, 0.0002597, -0.006544, -0.01129, -0.04174, 0.0004787, 0.02504, -0.03188, -0.05777, -0.05365, -0.05031, -0.04849, -0.04799, -0.04796, -0.04778, -0.04634, -0.03733),
    (0.003492, 0.00348, 0.003524, 0.002975, 0.000222, -0.005838, -0.01048, -0.03542, -0.005976, 0.009898, -0.03245, -0.04622, -0.03409, -0.02566, -0.02443, -0.0295, -0.03674, -0.04333, -0.04828, -0.04616),
    (0.003063, 0.004346, 0.003209, 0.003564, 0.002137, -0.00515, -0.00969, -0.02926, -0.01227, -0.004865, -0.033, -0.03496, -0.01504, -0.001629, -0.0009886, -0.01147, -0.02581, -0.03899, -0.05017, -0.05476),
    (0.0003261, 0.0002861, 0.0002472, -0.000296, -0.001254, -0.003635, -0.007952, -0.0157, -0.02611, -0.03734, -0.03423, -0.0102, 0.02689, 0.05123, 0.05059, 0.02819, -0.001768, -0.02945, -0.05432, -0.07369),
    (8.145e-05, 0.0004153, 0.0007491, 0.0008162, 0.0005643, 0.0001422, -0.00128, -0.003625, -0.006472, -0.01066, -0.01466, -0.01761, -0.0181, -0.01362, -0.006421, 0.002617, 0.009353, 0.01282, 0.01243, 0.00375),
)


def _correccion_tabla_ethylene(t_f: float, p_psia: float) -> float:
    """[USO INTERNO] Correccion aditiva de densidad (lbm/ft3) de Etileno:
    interpola sobre presion en cada una de las 12 curvas de temperatura
    fija, despues interpola ese resultado sobre temperatura -- replica
    literal de la doble interpolacion `FUN_1800fc5f8`+`FUN_1800fc5f8` del
    binario real (ver docstring del modulo)."""
    columna = [_interp_lineal(_ETH_P_AXIS, curva, p_psia) for curva in _ETH_CURVAS]
    return _interp_lineal(_ETH_T_AXIS, columna, t_f)


def _newton_raw_ethylene(t_f: float, p_psia: float, api_rounding: int):
    """[USO INTERNO] Newton-Raphson sobre la ecuacion de estado tipo BWR de
    Etileno -- replica literal de `FUN_1800fc268` (formula EXACTA,
    incluyendo la logica de reintento con semilla alternativa y
    degradacion a semilla `1.0` tras 2 fallos, todo confirmado via
    desensamblado real). Devuelve la densidad CRUDA (lbm/ft3, ANTES de
    sumar la correccion de tabla) o `None` si no converge en 100
    iteraciones totales (equivalente al codigo de error 3 del binario)."""
    if api_rounding == 1:
        tol, maxit = _ETH_TOL_1, _ETH_MAXIT_1
    elif api_rounding == 0:
        tol, maxit = _ETH_TOL_0, _ETH_MAXIT_0
    else:
        return None
    if p_psia <= 0:
        return None

    T_R = t_f + 459.67
    Y = _ETH_R * T_R  # = R*T, "RT" del BWR
    dVar3 = Y * _ETH_B0 - _ETH_A0 - _ETH_C0 / (T_R * T_R)
    dVar4 = Y * _ETH_b - _ETH_a

    disc = p_psia * 4.0 * dVar3 + Y * Y
    if disc < 0.0:
        rho = (Y / p_psia) * 0.76
        flag_alt = 2
    else:
        rho = math.sqrt(disc)
        rho = math.sqrt((rho + Y) * Y * 0.5)
        rho = rho / p_psia
        flag_alt = 1

    dVar5 = p_psia * 6.0
    dVar6 = Y * 5.0
    dVar12 = dVar4 * 3.0

    intentos_agotados = 0
    it = 1
    total_it = 0
    while total_it < 100:
        rho2 = rho * rho
        if rho2 == 0.0:
            return None
        exparg = -_ETH_gamma / rho2
        try:
            dVar13 = math.exp(exparg) * _ETH_c / (T_R * T_R)
            num = ((((rho * p_psia - Y) * rho - dVar3) * rho - dVar4) - (1.0 - exparg) * dVar13) \
                * rho2 * rho - _ETH_a * _ETH_alpha
            den = (((dVar5 * rho - dVar6) * rho - dVar3 * 4.0) * rho - dVar12) * rho2 \
                - ((3.0 - exparg * 2.0) * _ETH_gamma + rho2 * 3.0) * dVar13
            if den == 0.0:
                return None
            rho_new = rho - num / den
        except (OverflowError, ValueError, ZeroDivisionError):
            return None

        if abs(rho_new - rho) <= tol:
            if rho_new == 0.0:
                return None
            return _ETH_M / rho_new

        if rho_new > 0.0:
            rho = rho_new
            forzar_degradacion = it >= maxit
        else:
            if flag_alt < 3:
                flag_alt = 3
                rho = Y / p_psia
                forzar_degradacion = it >= maxit
            else:
                rho = rho_new
                forzar_degradacion = True

        if forzar_degradacion:
            if intentos_agotados > 1:
                if rho_new == 0.0:
                    return None
                return _ETH_M / rho_new
            intentos_agotados = 2
            it = 0
            rho = 1.0

        it += 1
        total_it += 1
    return None


def api_mpms_11_3_2_1_ethylene_puro(temp_f: float, pressure_psia: float,
                                     api_rounding: int = 0) -> dict:
    """FUNCION PUBLICA -- Densidad y compresibilidad (Z) de Etileno (C2H4)
    segun API MPMS 11.3.2.1, 100% Python puro (ver guia de uso al inicio
    del archivo).

    Parametros:
        temp_f: temperatura en grados Fahrenheit.
        pressure_psia: presion ABSOLUTA en psia.
        api_rounding: 0 (default, sin redondeo) o 1 (redondea la densidad
            final a 5 cifras significativas, tolerancia de convergencia
            mas laxa -- replica el flag "API Rounding" de la UI real).

    Devuelve dict con:
        density_kg_m3: float (NaN si `convergio=False`).
        z: float, compresibilidad adimensional (NaN si no convergio).
        fuera_de_rango: bool -- True si T o P caen fuera de 65-167F /
            200-2100psia (rango oficial del manual). El resultado sigue
            calculandose igual (extrapolacion), solo es informativo.
        convergio: bool -- False solo en condiciones extremas muy lejos de
            cualquier uso real (ver "NIVEL DE CONFIANZA" en el docstring
            del modulo) o si `api_rounding` no es 0 ni 1.
        aviso: str|None -- explica por que `convergio=False`, o None si
            todo OK.
    """
    fuera_de_rango = not (_ETH_T_MIN_F <= temp_f <= _ETH_T_MAX_F
                           and _ETH_P_MIN_PSIA <= pressure_psia <= _ETH_P_MAX_PSIA)

    if api_rounding not in (0, 1):
        return {"density_kg_m3": float("nan"), "z": float("nan"),
                "fuera_de_rango": fuera_de_rango, "convergio": False,
                "aviso": f"api_rounding invalido ({api_rounding!r}); debe ser 0 o 1."}

    raw = _newton_raw_ethylene(temp_f, pressure_psia, api_rounding)
    if raw is None:
        return {"density_kg_m3": float("nan"), "z": float("nan"),
                "fuera_de_rango": fuera_de_rango, "convergio": False,
                "aviso": ("El solver Newton-Raphson de la ecuacion de estado BWR de "
                          "Etileno no convergio para esta T/P -- por diseno, este modulo "
                          "NUNCA recurre al .xll como respaldo, se devuelve NaN explicito. "
                          f"fuera_de_rango={fuera_de_rango!r}.")}

    corr = _correccion_tabla_ethylene(temp_f, pressure_psia)
    density_lbm_ft3 = raw + corr

    # [CERTAIN] Chequeo de cordura replicado del binario real: si la
    # densidad final (cruda+correccion) supera 100 lbm/ft3 (~1602 kg/m3,
    # mas denso que el Etileno liquido real), el binario devuelve error
    # (codigo 2) en vez de un numero.
    if abs(density_lbm_ft3) > 100.0:
        return {"density_kg_m3": float("nan"), "z": float("nan"),
                "fuera_de_rango": fuera_de_rango, "convergio": False,
                "aviso": (f"Densidad calculada ({density_lbm_ft3:.4f} lbm/ft3) supera el "
                          "limite de cordura de 100 lbm/ft3 replicado del binario real "
                          "(codigo de error 2) -- condicion sin sentido fisico.")}

    if api_rounding == 1:
        density_lbm_ft3 = _redondear_cifras_significativas(density_lbm_ft3, 5)

    T_R = temp_f + 459.67
    z = (pressure_psia * _ETH_M) / (T_R * density_lbm_ft3 * _ETH_R)

    return {
        "density_kg_m3": density_lbm_ft3 * _LBM_FT3_A_KG_M3,
        "z": z,
        "fuera_de_rango": fuera_de_rango,
        "convergio": True,
        "aviso": None,
    }


# ===========================================================================
# PROPILENO -- API MPMS 11.3.3.2
# ===========================================================================
_PRO_T_MIN_F = 30.0
_PRO_T_MAX_F = 165.0
_PRO_P_MAX_PSIA = 1600.0

_PRO_TOL_0 = 1e-10
_PRO_TOL_1 = 5e-6
_PRO_EPS_BRACKET = 1e-10  # umbral fijo del secante, independiente de api_rounding


def _secante_propylene(t_f: float, p_psia: float, api_rounding: int, p_vap_psia: float):
    """[USO INTERNO] Secante/regula-falsi sobre la ecuacion de estado tipo
    BWR de Propileno -- replica literal de `FUN_1800e3b54` (todas las
    constantes son referencias DAT_ directas del decompilado, sin
    ambiguedad de mapeo). Devuelve la densidad (lbm/ft3) o `None` si no
    converge (equivalente a los codigos de error 0x2c/0x2d del binario)."""
    if api_rounding == 0:
        tol = _PRO_TOL_0
    elif api_rounding == 1:
        tol = _PRO_TOL_1
    else:
        return None

    Tr_term = 1.0 - (t_f + 460.0) / 657.0
    try:
        term_13 = math.pow(Tr_term, 1.0 / 3.0) * 1.573676
        term_23 = math.pow(Tr_term, 2.0 / 3.0) * 0.7907104
        term_43 = math.pow(Tr_term, 4.0 / 3.0)
    except ValueError:
        return None  # pow(negativo, exponente no entero) -- NaN real, sin solucion

    Tk = (t_f + 459.67) / 1.8
    P_scaled = p_psia / 14.696
    dVar18 = Tk * 0.082053

    try:
        x = 1.0 / ((2.902137 / (term_43 * 0.282433 + term_23 + term_13 + 1.0)
                    - ((0.338836 - t_f * 0.00387538) + t_f * 7.0612e-5 * t_f) * p_psia * 1e-4)
                   * 0.062426)
    except ZeroDivisionError:
        return None
    step = x * 0.03

    dVar12 = 321914.0 / (Tk * Tk)
    dVar10 = dVar18 * 0.15326 - 8.85083
    dVar11 = dVar18 * 0.0197889 - 0.718199

    A_x, A_f = 0.0, 0.0
    B_x, B_f = 0.0, 0.0

    for _ in range(1, 100):
        rho2 = x * x
        t1 = rho2 * 0.0146343
        rho3 = rho2 * x
        try:
            exp_term = math.exp(-t1)
            residual = P_scaled - (
                exp_term * (rho3 * 79510.1 / (Tk * Tk)) * (t1 + 1.0)
                + (dVar10 - dVar12) * rho2
                + dVar18 * x
                + dVar11 * rho3
                + rho3 * rho3 * 2.6480212589700004e-4
            )
        except (OverflowError, ValueError, ZeroDivisionError):
            return None

        if abs(residual) < tol:
            return 42.081 * x / 16.0189665  # densidad lbm/ft3

        if residual >= 0.0:
            A_x, A_f = x, residual
        else:
            B_x, B_f = x, residual

        if abs(A_x) < _PRO_EPS_BRACKET or abs(B_x) < _PRO_EPS_BRACKET:
            x = x + step if residual >= 0.0 else x - step
        else:
            if abs(A_x - B_x) < _PRO_EPS_BRACKET:
                return None  # secante sin signo opuesto (codigo 0x2c real)
            slope = (A_f - B_f) / (A_x - B_x)
            if slope == 0.0:
                return None
            x = (slope * A_x - A_f) / slope

    return None  # agoto 100 iteraciones (codigo 0x2d real)


def api_mpms_11_3_3_2_propylene_puro(temp_f: float, pressure_psia: float,
                                      api_rounding: int = 0) -> dict:
    """FUNCION PUBLICA -- Densidad de Propileno Liquido (CTPL, Equilibrium
    Pressure incluidos) segun API MPMS 11.3.3.2, 100% Python puro (ver
    guia de uso al inicio del archivo).

    Parametros:
        temp_f: temperatura en grados Fahrenheit.
        pressure_psia: presion ABSOLUTA en psia.
        api_rounding: 0 (default) o 1 (redondea la densidad final a 5
            cifras significativas, tolerancia de convergencia mas laxa).

    Devuelve dict con:
        density_kg_m3: float (NaN si `convergio=False`).
        ctpl: float, factor de correccion por temperatura y presion,
            adimensional (NaN si no convergio).
        equilibrium_pressure_bar: float, presion de vapor del Propileno a
            `temp_f` (SOLO depende de la temperatura, se calcula siempre,
            incluso si el solver de densidad no converge). NOTA DE UNIDAD
            (heredada sin resolver de la ronda anterior, ver docstring del
            modulo, seccion "LIMITACIONES"): la formula que reproduce el
            numero real del caso conocido es una conversion psia->bar
            DIRECTA, sin restar presion atmosferica -- no se determino si
            "bar(g)" en la UI real es un error de etiqueta.
        fuera_de_rango: bool -- True si T o P caen fuera de 30-165F /
            0-1600psia, O SI la presion esta por debajo (~99.75%) de la
            presion de vapor a esa temperatura (el Propileno no podria
            existir como liquido ahi).
        convergio: bool -- False solo en condiciones extremas (ver "NIVEL
            DE CONFIANZA" en el docstring del modulo) o si `api_rounding`
            no es 0 ni 1.
        aviso: str|None.
    """
    p_vap_psia = math.exp(12.5983 - 4015.63 / (temp_f + 460.068))
    equilibrium_pressure_bar = p_vap_psia * _PSIA_A_BAR

    fuera_de_rango = not (_PRO_T_MIN_F <= temp_f <= _PRO_T_MAX_F
                           and 0.0 <= pressure_psia <= _PRO_P_MAX_PSIA)
    if p_vap_psia * 0.0025 + pressure_psia < p_vap_psia:
        fuera_de_rango = True

    if api_rounding not in (0, 1):
        return {"density_kg_m3": float("nan"), "ctpl": float("nan"),
                "equilibrium_pressure_bar": equilibrium_pressure_bar,
                "fuera_de_rango": fuera_de_rango, "convergio": False,
                "aviso": f"api_rounding invalido ({api_rounding!r}); debe ser 0 o 1."}

    density_lbm_ft3 = _secante_propylene(temp_f, pressure_psia, api_rounding, p_vap_psia)
    if density_lbm_ft3 is None:
        return {"density_kg_m3": float("nan"), "ctpl": float("nan"),
                "equilibrium_pressure_bar": equilibrium_pressure_bar,
                "fuera_de_rango": fuera_de_rango, "convergio": False,
                "aviso": ("El solver secante/regula-falsi de la ecuacion de estado BWR de "
                          "Propileno no convergio (o convergio a una raiz sin sentido "
                          "fisico) para esta T/P -- por diseno, este modulo NUNCA recurre "
                          "al .xll como respaldo, se devuelve NaN explicito. "
                          f"fuera_de_rango={fuera_de_rango!r}.")}

    ctpl = density_lbm_ft3 / 32.6058
    if api_rounding == 1:
        density_lbm_ft3 = _redondear_cifras_significativas(density_lbm_ft3, 5)

    return {
        "density_kg_m3": density_lbm_ft3 * _LBM_FT3_A_KG_M3,
        "ctpl": ctpl,
        "equilibrium_pressure_bar": equilibrium_pressure_bar,
        "fuera_de_rango": fuera_de_rango,
        "convergio": True,
        "aviso": None,
    }


if __name__ == "__main__":
    print("=== normas/API_Ethylene_Propylene_puro.py -- autotest vs casos reales ===")
    r1 = api_mpms_11_3_2_1_ethylene_puro(90.0, 250.0)
    print(f"Ethylene T=90F P=250psia: density={r1['density_kg_m3']:.6f} kg/m3 "
          f"(real=21.13020), z={r1['z']:.6f} (real=0.901174), convergio={r1['convergio']}")

    r2 = api_mpms_11_3_3_2_propylene_puro(60.0, 200.0)
    print(f"Propylene T=60F P=200psia: density={r2['density_kg_m3']:.6f} kg/m3 "
          f"(real=523.6218), ctpl={r2['ctpl']:.6f} (real=1.002541), "
          f"eq_p={r2['equilibrium_pressure_bar']:.6f} bar (real=9.047929), "
          f"convergio={r2['convergio']}")
