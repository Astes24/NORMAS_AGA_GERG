# -*- coding: utf-8 -*-
"""
normas/AGA_3_FLOWXPERT.py
=======================
Calculo INDEPENDIENTE de caudal de gas por placa de orificio, traducido
MECANICAMENTE del algoritmo real de FlowXpert.xll (ABB/Spirit-IT), NO de
FocQus_Calculate_proy_sim_v2.dll. Este archivo es un par independiente de
normas/AGA_3.py: mismo problema fisico (AGA-3 / orificio), motor distinto,
para poder comparar los dos resultados entre si.

Este archivo se puede ejecutar solo, sin la interfaz grafica:
    python normas/AGA_3_FLOWXPERT.py

===============================================================================
ORIGEN Y METODO
===============================================================================
FlowXpert.xll esta bloqueado por licencia de hardware ABB ("Not Authorized"),
por lo que NO fue posible ejecutar la funcion real ni verificar dinamicamente
ningun resultado numerico (ver [[reversing-ghidra-flowxpert]] y
[[feedback-limites-reversing]] en la memoria del proyecto: no se intento ni se
debe intentar forzar la licencia). Todo lo de este archivo viene de
decompilacion ESTATICA con Ghidra (tecnica de "buscar el constructor", ver
ANALISIS_GHIDRA_FLOWXPERT/INDICE.md) de la cadena real:

    FlowXpert_AGA3_C (export)
      -> FUN_18009dfac  (lee los 22 argumentos de Excel en orden de registro)
      -> FUN_1800e2614  (proyecta P/T/densidad entre tomas, corrige diametros
                          por temperatura y por orificio de drenaje)
      -> FUN_1800e1fa4  (resuelve Cd y Reynolds por Newton-Raphson, calcula
                          factor de expansion Y, caudal masico final)

Ver decompilado completo en:
  ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga3_ctor_output.txt   (los 22 campos registrados)
  ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga3_real_output.txt   (wrapper, orden de lectura)
  ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga3_core_output.txt   (proyeccion + correccion)
  ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga3_solver_output.txt (Newton-Raphson + caudal)

===============================================================================
HALLAZGO CLAVE: el orden interno de memoria NO es el orden de registro Excel
===============================================================================
[CERTAIN] "Pressure Location" y "Temperature Loc." se declaran como enteros
adyacentes de 4 bytes en el wrapper (local_138/local_134), por lo que quedan
EMPACADOS juntos en un solo slot de 8 bytes del arreglo que recibe
FUN_1800e2614, en vez de ocupar un slot cada uno. Esto corre todos los campos
posteriores (Temperature Corr. en adelante) un lugar respecto del orden de
registro ingenuo. Se resolvio comparando el comportamiento real de cada indice
(que enum se compara contra que valor, que formula usa cada campo) contra el
texto de descripcion de cada campo en el constructor, hasta que las 22
entradas encajaron sin ninguna contradiccion. Mapeo final confirmado:

  0 dP   1 P   2 T   3 rho   4 mu   5 K   6 Dr   7 alphaD   8 TrD
  9 dr   10 alphad   11 Trd
  12 Ploc (mitad baja) / Tloc (mitad alta, empacados en el mismo slot)
  13 Tcorr   14 Texp   15 Dloc   16 Dexp   17 Fluid
  18 DrainHole   19 Fpwl   20 Edition

===============================================================================
[CERTAIN] vs [LIKELY] vs [GUESSING]
===============================================================================
[CERTAIN]: la estructura completa del algoritmo (que campo alimenta que
formula, la secuencia de proyeccion P/T/densidad por ubicacion de toma, la
correccion de diametros por temperatura y por orificio de drenaje, el bucle
Newton-Raphson de Cd+Reynolds con tolerancia 5e-6 y maximo 20 iteraciones, la
ecuacion final de caudal), y TODOS los valores numericos de las ~50
constantes DAT_ usadas (extraidas leyendo bytes crudos de memoria con Ghidra,
no de una tabla publicada). El factor de expansion con Edition=1 coincide
EXACTAMENTE, constante por constante, con la formula AGA-3 (edicion 1992)
publicada: Y = 1 - (0.41 + 0.35*beta^4) * x / kappa.

[LIKELY, reforzado 2026-07-14 con evidencia dura para Temperatura]: las
unidades de entrada. FlowXpert usa constantes de conversion (27.707 = inH2O
a psi; 459.67 = offset Rankine) que indican un sistema de unidades US
customary (psia, inH2O, Rankine/Fahrenheit, pulgadas). Se reviso ademas el
rango minimo/maximo permitido de CADA campo (declarado en el constructor,
ghidra_aga3_ctor_output.txt) para buscar evidencia independiente:
  - Temperature / Pipe ref. Temp.: rango [-400, 2000]. -400 grados NO PUEDE
    ser Celsius (el cero absoluto es -273.15 degC, -400 degC es imposible
    fisicamente) -- en Fahrenheit si es valido (cero absoluto=-459.67 degF).
    Esto CONFIRMA grados Fahrenheit, no es solo inferencia por coincidencia
    de constantes.
  - Diff. Pressure: rango [0, 1000] -- coincide con el fondo de escala
    tipico de transmisores de presion diferencial en inH2O (250-830 inH2O
    es un rango comercial comun).
  - Pipe/Orifice/Drain hole Diameter: rango [0, 100] -- 100 pulgadas es un
    diametro de tuberia grande pero realista (grandes lineas troncales);
    100 mm seria un limite superior absurdamente chico para un medidor
    industrial, 100 m seria absurdo. Apoya pulgadas.
  - Pressure: rango [0, 30000] -- coherente con psia como limite superior
    generoso, aunque menos determinante por si solo que los anteriores.
  - Density: rango [0, 200] -- coherente con lb/ft3 (200 lb/ft3 cubre hasta
    liquidos moderadamente densos, ya que el campo "Fluid" tambien admite
    liquido), aunque tambien menos determinante por si solo.
Con todo esto NO se pudo confirmar dinamicamente (motor bloqueado por
licencia), pero la evidencia de rangos (especialmente temperatura) hace que
la conclusion de sistema US customary sea mucho mas solida que una simple
coincidencia de constantes.

[CERTAIN, CORREGIDO 2026-07-20 -- ver seccion "VALIDACION REAL" mas abajo]:
la viscosidad ("Dyn. Viscosity") se pasa al nucleo TAL CUAL, en cP, SIN
ninguna conversion. La constante DAT_1801941b8=1488.16394356955 SI existe en
el binario y SI es el factor exacto 1 lbm/(ft*s) = 1488.164 cP, pero una
sesion anterior asumio (sin poder validarlo, licencia bloqueada) que
FlowXpert la aplicaba SIEMPRE sobre el valor de entrada antes de llamar al
nucleo. Eso era incorrecto: comparado contra un caso real de la app movil de
FlowXpert (2026-07-20), aplicar esa multiplicacion da 8.5% de error en Cd y
mas de 1000x de error en Reynolds. Sin aplicarla, Cd/Reynolds/Flujo masico
coinciden con el caso real dentro de 0.001%-0.31%. La interpretacion correcta
de la constante: "Dyn. Viscosity" en FlowXpert acepta varias unidades (Pa*s,
poise, cP, kgf*s/m2, lbm/(ft*s)) desde un selector propio de la app -- 1488.164
es la entrada de esa tabla de conversion para "lbm/(ft*s)", no un paso que el
nucleo aplique siempre. El nucleo espera el valor ya en cP.

[CERTAIN, reforzado 2026-07-21 con fuente independiente]: los terminos de
posicion de toma del Cd (exponenciales -8.5 y -6.0, en vez de los -10 y -7 de
tomas en brida RG98 que usa normas/AGA_3.py) y la constante base C_inf=0.5961
y el umbral SMALLD_THRESHOLD_IN=2.8 YA NO dependen solo de la lectura del
.xll: se confirmaron leyendo las constantes reales de
`calc_discharge_coefficient_by_reynolds` dentro de `libFXLibrary.so` (la
libreria nativa del APK oficial de FlowXpert, arquitectura x86 de Android,
un binario COMPLETAMENTE DISTINTO al .xll). Se resolvieron las direcciones
GOT-relativas (`EBX + offset`) del ensamblador real y se leyeron los doubles
en memoria -- 0.5961, 2.8, -8.5 y -6.0 aparecen EXACTOS en ambos binarios
independientes. Esto descarta que fueran un error de transcripcion de una
sola sesion de Ghidra sobre el .xll.

[GUESSING, sin cambios]: a que variante/edicion PUBLICADA corresponde
exactamente el factor de expansion con Edition=2 y estos mismos terminos de
posicion de toma (-8.5/-6.0). La ESTRUCTURA es identica a RG98 (terminos en
beta^2/4/8, terminos de Reynolds, terminos exponenciales de posicion de
toma), pero las constantes numericas exactas no coinciden con la
parametrizacion de tomas en brida ya usada en TABLA_RG98 (normas/AGA_3.py).
Esto sugiere que FlowXpert_AGA3_C asume una configuracion de tomas FIJA
distinta (no hay un campo de entrada para elegir tipo de toma entre los 22
registrados), posiblemente tomas en D y D/2 (norma AGA-3/API 14.3, comun en
Norteamerica) u otra revision de ISO 5167-2. Que las constantes sean
correctas ya es [CERTAIN] (parrafo anterior); lo que sigue sin identificarse
es a que estandar publicado especifico corresponden.

===============================================================================
VALIDACION REAL (2026-07-20) -- ver normas/test_aga3_flowxpert_caso_real.py
===============================================================================
Primer y unico caso de referencia REAL disponible hasta ahora (capturas de la
app movil oficial "AGA-3" de ABB, CAPTURA AGA3 1/2/3.jpeg en la raiz del
proyecto). Entradas (sistema SI, tal cual las muestra la app):

  Diff. Pressure=10.5365 kPa, Pressure=3447.38 kPa(a), Temperature=55 degC,
  Density=22.537978 kg/m3, Dyn. Viscosity=0.0103 cP, Isentropic Exp.=1.3,
  Pipe Diameter=0.2999994 m, Pipe Expansion=0.0000112 1/degC,
  Pipe ref. Temp.=20 degC, Orifice Diameter=0.1800098 m,
  Orifice Expansion=0.0000166 1/degC, Orifice ref. Temp.=20 degC,
  Pressure Location=Upstream, Temperature Loc.=At recovered pressure,
  Temperature Corr.=Isentropic exponent, Temperature Exp.=0,
  Density Location=Upstream, Density Exponent=0, Fluid=Gas,
  Drain hole Diam.=0 mm, Fpwl=1, Edition=2012.

Resultados REALES (app FlowXpert) vs CALCULADOS (este archivo, sin la
conversion de viscosidad incorrecta):

  Flujo masico:    real=11.36063 kg/s     calculado=11.36049 kg/s  (0.001%)
  Cd:              real=0.604113          calculado=0.604115       (0.0004%)
  Beta:            real=0.600150          calculado=0.600148       (exacto)
  Factor exp. Y:   real=0.999071          calculado=0.999071       (exacto)
  Veloc. aprox. E: real=1.071946          calculado=1.071945       (exacto)
  Reynolds:        real=4,693,764         calculado=4,679,271      (0.31%)
  Upstream/Downstream/Recovered P, T, rho: coinciden en las 9 dentro de
  redondeo (ver test para el detalle completo).

[CERTAIN, RESUELTO 2026-07-29] El 0.31% de Reynolds NO era un error de
formula: era que el unico caso disponible hasta entonces venia de LEER
VALORES REDONDEADOS DE UNA CAPTURA DE PANTALLA (no de una llamada en vivo).
Esta sesion se obtuvo acceso dinamico real al mismo dispositivo Android
(app com.spiritit.flowxpert corriendo, Frida attachado) y se llamo DIRECTO
`calc_discharge_coefficient_by_reynolds` (simbolo real, ver arriba) con
`Interceptor.attach`, leyendo cada campo del struct de entrada/salida con
`NativePointer.add(offset).readDouble()/.readS32()` (leer con
`readByteArray` en este mismo dispositivo devolvia arrays vacios sin
lanzar excepcion -- limite especifico de esta combinacion Frida/emulador,
leer campo por campo lo evito). Layout real confirmado del struct de
entrada de esta funcion (9 campos, EMPACADO SIN NINGUN PADDING, distinto
del struct externo de 22 campos): 7 doubles consecutivos (Dr_efectivo@0x00,
dr_efectivo@0x08, dP@0x10, P@0x18, rho@0x20, mu@0x28) seguidos de
Fluid(int32)@0x30, K(double, DESALINEADO)@0x34, Edition(int32)@0x3C.
Con los 9 valores reales exactos (no redondeados) pasados directo a
`_resolver_cd_reynolds()`, Reynolds coincide **EXACTO** (0.000000%, no
0.31%) -- igual que beta/Cd/Y/E/flujo_masico, que ya coincidian antes.
Confirmado tambien de punta a punta con `calcular_flujo_flowxpert()`
completo (incluyendo la correccion de diametros por temperatura) en 2
casos reales distintos (DP=24.88 y DP=35.5 inH2O, mismo resto de campos):
0.00000% de error en flujo_masico/beta/Cd/Y/E/Reynolds/dr_efectivo/
Dr_efectivo en ambos. **La formula/constantes de este archivo quedan
confirmadas exactas, no aproximadas.**
Leccion reutilizable: cuando `NativePointer.readByteArray()` devuelve un
ArrayBuffer vacio sin excepcion (visto tambien intentando volcar el struct
de esta misma funcion con longitudes de 0x80 y 0x48), no asumir que la
memoria es invalida -- probar leyendo campo por campo con
`.readDouble()`/`.readS32()` en offsets individuales, que si funciono en
el mismo puntero en el mismo momento.

===============================================================================
DIFERENCIA DE PROPOSITO CON normas/AGA_3.py
===============================================================================
normas/AGA_3.py verifica el motor REAL de FocQus (llama a la DLL en vivo).
Este archivo es una traduccion pura a Python del algoritmo de FlowXpert, sin
llamar a ningun binario -- sirve para comparar los DOS resultados
(FocQus vs FlowXpert) con los mismos datos de entrada y ver si coinciden
dentro de una tolerancia razonable. Las diferencias esperadas NO son errores:
FocQus usa tomas en brida (RG98 tal cual publicado) y Edition/tipo de toma
fijo distinto en FlowXpert -- ver seccion [GUESSING] arriba.
===============================================================================
"""

from math import exp, fabs, isfinite, pow as _pow, sqrt

# ---------------------------------------------------------------------------
# Campos de entrada -- nombre interno, etiqueta (igual a la UI de FlowXpert),
# unidad [LIKELY, ver docstring], valor de ejemplo.
# Fuente: ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga3_ctor_output.txt (constructor
# FUN_1800666cc), orden de registro Excel (no es el orden interno -- ver
# _CAMPOS_ORDEN_INTERNO mas abajo para el mapeo real usado en el calculo).
# ---------------------------------------------------------------------------
CAMPOS = [
    ("dP",         "Diff. Pressure",       "inH2O", "42.3"),
    ("P",          "Pressure",             "psia",  "500.0"),
    ("T",          "Temperature",          "degF",  "60.0"),
    ("rho",        "Density",              "lb/ft3","1.5"),
    ("mu",         "Dyn. Viscosity",       "cP",    "0.011"),
    ("K",          "Isentropic Exponent",  "-",     "1.28"),
    ("Dr",         "Pipe Diameter",        "in",    "10.0"),
    ("alphaD",     "Pipe Expansion",       "1/degF","0.0000062"),
    ("TrD",        "Pipe ref. Temp.",      "degF",  "68.0"),
    ("dr",         "Orifice Diameter",     "in",    "5.0"),
    ("alphad",     "Orifice Expansion",    "1/degF","0.0000062"),
    ("Trd",        "Orifice ref. Temp.",   "degF",  "68.0"),
    ("Ploc",       "Pressure Location",    "1=aguas arriba, 2=aguas abajo", "1"),
    ("Tloc",       "Temperature Loc.",     "1/2/3 (arriba/abajo/recuperada)", "1"),
    ("Tcorr",      "Temperature Corr.",    "1=auto (K-1)/K, 2/3=usar Texp", "1"),
    ("Texp",       "Temperature Exp.",     "-",     "0.0"),
    ("Dloc",       "Density Location",     "1=sin corregir, 2/3=corregir", "1"),
    ("Dexp",       "Density Exponent",     "0=usar 1/K, si no valor dado", "0.0"),
    ("Fluid",      "Fluid",                "1=gas, 2=liquido", "1"),
    ("DrainHole",  "Drain hole Diam.",     "in",    "0.0"),
    ("Fpwl",       "Fpwl (Grav. cor. factor)", "-", "1.0"),
    ("Edition",    "Edition",              "1=1992, 2=2012", "1"),
]
# * mu: se ingresa ya en la unidad que consume el nucleo. El wrapper de
#   FlowXpert aplica una conversion propia (constante DAT_1801941b8) antes de
#   llamar al nucleo; ese valor NO se extrajo (esta fuera de las dos funciones
#   centrales analizadas), asi que aqui NO se aplica ninguna conversion --
#   ver seccion [LIKELY] del docstring.

RESULTADOS = [
    ("status",              "Codigo de estado (0=OK)",        "-"),
    ("beta",                "Beta (β = d/D, corregido)",       "-"),
    ("Cd",                  "Coef. descarga (Cd)",             "-"),
    ("reynolds",            "Reynolds (Re_D)",                 "-"),
    ("factor_expansion",    "Factor de expansion (Y)",         "-"),
    ("factor_veloc_aprox",  "Factor veloc. aproximacion (E)",  "-"),
    ("flujo_masico",        "Flujo masico",                    "lb/h"),
    ("dr_efectivo",         "Diametro orificio efectivo",      "in"),
    ("Dr_efectivo",         "Diametro tuberia efectivo",       "in"),
    ("iteraciones",         "Iteraciones Newton-Raphson",       "-"),
    # Proyeccion por ubicacion de toma (Ploc/Tloc/Dloc) -- ya se calculaba
    # internamente en calcular_flujo_flowxpert() para derivar T_up/T_dn/T_rec
    # y las densidades, pero se descartaba antes del return. FlowXpert SI
    # las registra como salidas propias (PRESUP/PRESDN/PRESREC/TEMPUP/TEMPDN/
    # TEMPREC/DENSUP/DENSDN/DENSREC en ghidra_aga3_ctor_output.txt).
    ("P_upstream",          "Presion aguas arriba",            "psia"),
    ("P_downstream",        "Presion aguas abajo",              "psia"),
    ("P_recovered",         "Presion recuperada",               "psia"),
    ("T_upstream",          "Temperatura aguas arriba",         "degF"),
    ("T_downstream",        "Temperatura aguas abajo",          "degF"),
    ("T_recovered",         "Temperatura recuperada",           "degF"),
    ("rho_upstream",        "Densidad aguas arriba",            "lb/ft3"),
    ("rho_downstream",      "Densidad aguas abajo",             "lb/ft3"),
    ("rho_recovered",       "Densidad recuperada",              "lb/ft3"),
]

# ---------------------------------------------------------------------------
# Constantes extraidas de FUN_1800e2614 y FUN_1800e1fa4 (valores leidos de
# memoria byte a byte con Ghidra -- ver ANALISIS_GHIDRA_FLOWXPERT/
# ghidra_aga3_constants_output.txt). Nombres descriptivos donde el uso en el
# codigo lo confirma con certeza; DAT_<direccion> donde no se identifico un
# nombre publicado (se usa el valor extraido tal cual, sin adaptarlo).
# ---------------------------------------------------------------------------
VISC_CONVERSION = 1488.16394356955  # DAT_1801941b8 -- factor exacto cP -> lbm/(ft*s).
                                     # [CORREGIDO 2026-07-20, ver docstring "VALIDACION REAL"]:
                                     # esta constante SI existe en el binario, pero NO se
                                     # aplica automaticamente sobre el valor de entrada --
                                     # es la entrada de la TABLA de unidades del campo "Dyn.
                                     # Viscosity" (que en FlowXpert acepta Pa*s, poise, cP,
                                     # kgf*s/m2 o lbm/(ft*s)) para cuando el usuario elige
                                     # lbm/(ft*s) como unidad. El nucleo consume el valor ya
                                     # convertido a cP; calcular_flujo_flowxpert() YA NO
                                     # multiplica por esta constante (ver mas abajo). Queda
                                     # aca solo como factor de conversion reusable por quien
                                     # construya un selector de unidades (ver
                                     # interfaz_calculo_flujo.py, selector "Dyn. Viscosity").
INH2O_A_PSI = 27.707            # DAT_1801ea458 -- conversion inH2O -> psi
RANKINE_OFFSET = 459.67         # DAT_180194158 -- degF -> Rankine
RE_MINIMO = 4000.0              # DAT_1801ea470 -- Reynolds minimo valido AGA-3
TOLERANCIA_NR = 5.0e-6          # DAT_1801ea3b8 -- tolerancia Newton-Raphson
MAX_ITERACIONES = 20            # 0x14 en el decompilado
BETA_MIN = 0.2                  # DAT_180193eb8
BETA_MAX = 0.75                 # DAT_180195138
DR_EFECTIVO_MIN = 0.45          # DAT_1801dd6c0 (in)
DR_TUB_EFECTIVO_MIN = 2.0       # DAT_180124438 (in)
DRAIN_HOLE_FACTOR = 0.55        # DAT_1801df168 -- factor de correccion de area por orificio de drenaje
CD_C_INF = 0.5961               # DAT_1801ea228 -- termino base (coincide con C_inf de RG98)
# Factor de expansion Y, Edition=1 (1992) -- coincide EXACTO con AGA-3 1992 publicado
Y1992_COEF_BETA4 = 0.35         # DAT_1801ea410
Y1992_COEF_CONST = 0.41         # DAT_1801df158
# Factor de expansion Y, Edition=2 (2012) -- constantes propias de FlowXpert, ver [GUESSING]
Y2012_COEF_BETA4 = 0.1027       # DAT_1801ea3f0
Y2012_COEF_CONST = 0.3625       # DAT_1801ea418
Y2012_COEF_BETA8 = 1.132        # DAT_1801ea428
# Terminos del Cd (estructura RG98, constantes propias de FlowXpert, ver [GUESSING])
CD_COEF_BETA2 = 0.0291          # DAT_1801ea3d8
CD_COEF_BETA8 = 0.229           # DAT_1801ea408
CD_COEF_RE07 = 5.11e-4          # DAT_1801ea3c0 (termino c, exponente Re^0.7)
CD_EXP_RE07 = 0.7               # DAT_180193ed8
CD_EXP_RE08 = 0.8               # DAT_180193ee0 (exponente de A y del propio Re en el bucle)
CD_D_BASE = 0.0049              # DAT_1801ea3c8
CD_E_BASE = 0.021               # DAT_1801ea3d0
CD_TAP_EXP1 = -8.5              # DAT_1801ea490 (posicion de toma, termino "f")
CD_TAP_EXP2 = -6.0              # DAT_1801ea488 (posicion de toma, termino "h")
CD_TAP_F_COEF = 0.0712          # DAT_1801ea3e8
CD_TAP_F_CONST = 0.0433         # DAT_1801ea3e0
CD_TAP_H_COEF = 0.1145          # DAT_1801ea3f8
CD_M2_EXP = 1.3                 # DAT_180193f38
CD_M2_COEF = 0.52               # DAT_1801ea420
CD_M2_SCALE = -0.0116           # DAT_1801ea478
CD_FH_SCALE = -0.23             # DAT_1801ea480
CD_BETA8_EXP = 1.1              # DAT_180194e50
CD_BETA8_SCALE = 0.14           # DAT_1801ea400
SMALLD_THRESHOLD_IN = 2.8       # DAT_1801ea2b8 -- 71.12 mm = 2.8 in
SMALLD_COEF = 0.003             # DAT_1801dd600
CD_RE_A_COEF = 1.15             # DAT_1801dd710
REYNOLDS_K = 2.494328           # DAT_1801ea438 -- constante de la formula inicial de Reynolds
REYNOLDS_CAP = 1000.0           # DAT_180124818 -- tope del valor inicial iterado
# NOTA: DAT_1801ea460=215.4432 se usa en FUN_1800e2614 para una "Raw Mass Rate"
# preliminar (ver "Raw Mass Rate"/"Raw Prev. Mass Rate" del constructor) que
# el propio FlowXpert descarta y sobrescribe con el resultado del solver
# (linea 286 de ghidra_aga3_core_output.txt: *param_2 = local_c0*param_1[0x13]).
# No se traduce aqui por no afectar ningun resultado final.
REYNOLDS_SCALE_FINAL = 253.9025184025  # DAT_1801ea468
UMBRAL_X = 1.142139337256165    # DAT_1801ea430 -- umbral que separa las 2 ramas del bucle
COEF_A = 4.343524261523267      # DAT_1801ea448
COEF_B = 3.764387693320165      # DAT_1801ea440
CONST_250 = 250.0                # DAT_180194110
CONST_475 = 4.75                 # DAT_1801ea450
# --- Validaciones de entrada del WRAPPER (FUN_18009dfac), NO del nucleo ---
# Extraidas y confirmadas 2026-07-14 (ghidra_wrapperconsts_output.txt),
# releyendo el contexto exacto (ghidra_aga3_real_output.txt lineas 261-266)
# para no asumir su rol. Si fallan, FlowXpert rechaza la entrada ANTES de
# llamar a FUN_1800e2614 -- no afectan ninguna formula de calculo, solo
# deciden si se acepta o se rechaza el dato.
DRAIN_HOLE_MAX_FRACTION = 0.5    # DAT_180124428 -- limite: DrainHole <= (Dr-dr)*0.5
# NOTA: la otra validacion encontrada en el wrapper (Dr != 0.0, DAT_180123e30
# = 0.0 exacto) NO se traduce como chequeo aparte porque ya queda cubierta
# sin ningun codigo adicional: el chequeo "dr<=0 or Dr<=dr" de mas abajo
# (ya presente en el nucleo, FUN_1800e2614) rechaza TODO caso con Dr=0,
# sea cual sea el valor de dr (si dr>0, Dr=0<=dr es verdadero; si dr<=0, ya
# se rechaza por eso). Agregar un chequeo separado seria codigo redundante.


def _proyectar_y_corregir(dP, P, T, rho, mu, K, Dr, alphaD, TrD, dr, alphad, Trd,
                           Ploc, Tloc, Tcorr, Texp, Dloc, Dexp, Fluid,
                           DrainHole, Fpwl, Edition):
    """Traduccion literal de FUN_1800e2614: proyecta P/T/densidad entre tomas
    aguas arriba/abajo/recuperada segun la ubicacion configurada, corrige
    diametros de tuberia y placa por dilatacion termica y por orificio de
    drenaje. Devuelve dict con status!=0 si hay error (mismos codigos que
    "AGA-3 specific error status" del constructor de FlowXpert, EXCEPTO
    status=-1, que es un rechazo del WRAPPER -- ver DRAIN_HOLE_MAX_FRACTION
    arriba -- no un codigo de FUN_1800e2614)."""

    # Validaciones del WRAPPER (antes de llegar al nucleo real de FlowXpert).
    # Orden preservado del original: en FUN_18009dfac es una sola condicion
    # encadenada con AND, evaluada de izquierda a derecha (cortocircuito) --
    # "dr<=Dr" se evalua ANTES que el limite del orificio de drenaje, por
    # eso el chequeo de geometria va primero tambien aqui.
    if dr <= 0.0 or Dr <= dr:
        return {"status": 1}
    if DrainHole > (Dr - dr) * DRAIN_HOLE_MAX_FRACTION:
        return {"status": -1}
    if dP < 0.0:
        return {"status": 5}

    # Proyeccion de presion por ubicacion de toma (Ploc)
    if Ploc == 1:
        P_up = P
        P_dn = P - dP / INH2O_A_PSI
    elif Ploc == 2:
        P_dn = P
        P_up = dP / INH2O_A_PSI + P
    else:
        return {"status": 4}
    P_rec = P_dn

    rho_up = rho_dn = rho_rec = rho

    # Correccion de densidad simple por ubicacion (Dloc == 2 o 3)
    if Dloc in (2, 3):
        if P_dn == 0.0:
            return {"status": 9}
        ratio = P_up / P_dn
        if ratio == 0.0 and Dexp == 0.0:
            return {"status": 10}
        rho_up = _pow(ratio, Dexp) * rho

    if rho_up <= 0.0:
        return {"status": 2}
    if K <= 0.0:
        return {"status": 6}
    if P <= 0.0:
        return {"status": 3}

    T_up = T_dn = T_rec = T

    if dP == 0.0:
        return {"status": 0, "flujo_masico": 0.0, "beta": 0.0, "Cd": 0.0,
                "factor_expansion": 1.0, "reynolds": 0.0,
                "factor_veloc_aprox": 0.0, "dr_efectivo": 0.0,
                "Dr_efectivo": 0.0, "iteraciones": 0,
                "P_upstream": P_up, "P_downstream": P_dn, "P_recovered": P_rec,
                "T_upstream": T_up, "T_downstream": T_dn, "T_recovered": T_rec,
                "rho_upstream": rho_up, "rho_downstream": rho_dn, "rho_recovered": rho_rec}

    # Exponente de proyeccion de temperatura (Tcorr selecciona la formula)
    if Tcorr == 1:
        t_exp = (1.0 - K) / K
    elif Tcorr in (2, 3):
        t_exp = Texp
    else:
        t_exp = 0.0

    d_exp = Dexp if Dexp != 0.0 else 1.0 / K

    # Proyeccion de temperatura por ubicacion de toma (Tloc)
    if Tcorr == 3:
        # variante lineal (diferencias), no razon de presiones absolutas
        d_up_rec = (P_up - P_rec) * t_exp
        d_up_dn = (P_up - P_dn) * t_exp
        d_dn_rec = (P_dn - P_rec) * t_exp
        if Tloc == 1:
            T_up = T
            T_rec = T_up - d_up_rec
            T_dn = T_up - d_up_dn
        elif Tloc == 2:
            T_dn = T
            T_rec = T_dn - d_dn_rec
            T_up = T_dn + d_up_dn
        elif Tloc == 3:
            T_rec = T
            T_dn = d_dn_rec + T_rec
            T_up = d_up_rec + T_rec
        else:
            return {"status": 0, "_no_conv": True}
    else:
        R = RANKINE_OFFSET
        if Tloc == 1:
            T_up = T
            T_dn = _pow(P_up / P_dn, t_exp) * (T + R) - R
            T_rec = _pow(P_up / P_rec, t_exp) * (T + R) - R
        elif Tloc == 2:
            T_up = _pow(P_dn / P_up, t_exp) * (T + R) - R
            T_dn = T
            T_rec = _pow(P_dn / P_rec, t_exp) * (T + R) - R
        elif Tloc == 3:
            T_up = _pow(P_rec / P_up, t_exp) * (T + R) - R
            T_dn = _pow(P_rec / P_dn, t_exp) * (T + R) - R
            T_rec = T
        else:
            return {"status": 0, "_no_conv": True}

    # Correccion de densidad completa (3 tomas) por ubicacion (Dloc)
    if Dloc == 1:
        rho_up = rho
        rho_dn = _pow(P_dn / P_up, d_exp) * rho
        rho_rec = _pow(P_rec / P_up, d_exp) * rho
    elif Dloc == 2:
        rho_up = _pow(P_up / P_dn, d_exp) * rho
        rho_dn = rho
        rho_rec = _pow(P_rec / P_dn, d_exp) * rho
    elif Dloc == 3:
        rho_up = _pow(P_up / P_rec, d_exp) * rho
        rho_dn = _pow(P_dn / P_rec, d_exp) * rho
        rho_rec = rho
    else:
        return {"status": 0, "_no_conv": True}

    # Correccion de diametros: dilatacion termica (a T_up) + orificio de drenaje
    dr_efectivo = ((T_up - Trd) * alphad + 1.0) * dr * (
        (DrainHole * DrainHole * DRAIN_HOLE_FACTOR) / (dr * dr) + 1.0)
    Dr_efectivo = ((T_up - TrD) * alphaD + 1.0) * Dr
    if Dr_efectivo <= 0.0:
        return {"status": 1}

    # NOTA: el solver recibe P y rho SIN PROYECTAR (los mismos valores crudos
    # de entrada, param_1[1] y param_1[3] de la funcion OUTER), no P_up/rho_up.
    # La proyeccion por ubicacion de toma (Ploc/Tloc/Dloc) solo alimenta los
    # campos de salida "Upstream/Downstream/Recovered" -- confirmado releyendo
    # local_a0=param_1[1] (P crudo) y local_98=param_1[3] (rho crudo) en
    # ghidra_aga3_core_output.txt justo antes de la llamada a FUN_1800e1fa4.
    solver_in = (Dr_efectivo, dr_efectivo, dP, P, rho, mu, Fluid, K, Edition)
    salida = _resolver_cd_reynolds(*solver_in)
    if salida is None:
        return {"status": 11}

    beta, Y, E, Cd, reynolds, mass_rate, iteraciones = salida
    mass_rate *= Fpwl

    status = 0
    if dr_efectivo <= DR_EFECTIVO_MIN:
        status = 1
    if Dr_efectivo <= DR_TUB_EFECTIVO_MIN:
        status = 1
    if beta < BETA_MIN or beta > BETA_MAX:
        status = 1

    return {
        "status": status,
        "beta": beta,
        "Cd": Cd,
        "factor_expansion": Y,
        "factor_veloc_aprox": E,
        "flujo_masico": mass_rate,
        "dr_efectivo": dr_efectivo,
        "Dr_efectivo": Dr_efectivo,
        "iteraciones": iteraciones,
        "reynolds": reynolds,
        "P_upstream": P_up,
        "P_downstream": P_dn,
        "P_recovered": P_rec,
        "T_upstream": T_up,
        "T_downstream": T_dn,
        "T_recovered": T_rec,
        "rho_upstream": rho_up,
        "rho_downstream": rho_dn,
        "rho_recovered": rho_rec,
    }


def _resolver_cd_reynolds(Dr_efectivo, dr_efectivo, dP, P, rho, mu, Fluid, K, Edition):
    """Traduccion literal de FUN_1800e1fa4: resuelve Cd y Reynolds de forma
    simultanea por Newton-Raphson (maximo 20 iteraciones, tolerancia 5e-6),
    calcula el factor de expansion Y y el caudal masico final. Devuelve
    (beta, Y, E, Cd, reynolds, flujo_masico, iteraciones) o None si no converge
    o el resultado no es finito (equivalente al status 0xb de FlowXpert).

    NOTA sobre el mapeo de parametros del solver (distinto del de _proyectar_y_
    corregir): confirmado por el ORDEN DE DIRECCION de las variables locales
    del llamador (local_b8 < local_b0 < local_a8 < local_a0 < local_98 <
    local_90 < local_88 < local_80 < local_78), no por el orden de registro:
    [0]=Dr_efectivo [1]=dr_efectivo [2]=dP [3]=P(crudo) [4]=rho(crudo)
    [5]=mu [6]=Fluid [7]=K [8]=Edition."""

    beta = dr_efectivo / Dr_efectivo
    if beta > 1.0 or beta < 0.0:
        return None
    beta2 = beta * beta
    beta4 = beta2 * beta2
    beta_re07 = _pow(beta, CD_EXP_RE07)          # beta^0.7
    beta_re08 = _pow(beta, CD_EXP_RE08)          # beta^0.8 (llamado "dVar8" en el decompilado)

    const_250_035 = _pow(250.0, 0.35)            # DAT_180194110^DAT_1801ea410 (constante fija)
    const_475_08 = _pow(4.75, CD_EXP_RE08)        # DAT_1801ea450^DAT_180193ee0 (constante fija)

    # --- Factor de expansion Y (usa P crudo, no proyectado) ---
    if Fluid == 1:
        x = dP / (P * INH2O_A_PSI)
        if Edition == 1:
            Y_term = ((beta4 * Y1992_COEF_BETA4 + Y1992_COEF_CONST) * x) / K
        elif Edition == 2:
            Y_term = _pow(1.0 - x, 1.0 / K)
            Y_term = (1.0 - Y_term) * (beta4 * Y2012_COEF_BETA4 + Y2012_COEF_CONST
                                        + beta4 * beta4 * Y2012_COEF_BETA8)
        else:
            return None
        Y = 1.0 - Y_term
    else:
        Y = 1.0

    E = _pow(1.0 - beta4, -0.5)  # factor de velocidad de aproximacion

    # --- Terminos de posicion de toma (dependientes de Dr_efectivo, no de Re) ---
    inv_D = 1.0 / Dr_efectivo
    small_d_corr = SMALLD_THRESHOLD_IN - Dr_efectivo
    if small_d_corr <= 0.0:
        small_d_corr = 0.0

    m2 = (inv_D * 2.0) / (1.0 - beta)
    f_term = exp(inv_D * CD_TAP_EXP1) * CD_TAP_F_COEF + CD_TAP_F_CONST
    h_term = exp(inv_D * CD_TAP_EXP2)
    f_h_term = (f_term - h_term * CD_TAP_H_COEF) * (beta4 / (1.0 - beta4))

    m2_pow = _pow(m2, CD_M2_EXP)
    m2_term = (m2 - m2_pow * CD_M2_COEF) * CD_M2_SCALE   # dVar14 final

    beta11_m2 = _pow(beta, CD_BETA8_EXP) * m2_term        # beta^1.1 * m2_term (dVar11)

    if Dr_efectivo <= SMALLD_THRESHOLD_IN:
        smalld_term = (1.0 - beta) * SMALLD_COEF * small_d_corr
    else:
        smalld_term = 0.0

    cd_base = (beta2 * CD_COEF_BETA2 + CD_C_INF) - beta4 * beta4 * CD_COEF_BETA8 \
        + smalld_term + f_h_term + beta11_m2

    # Terminos que se llevan al bucle de Newton-Raphson (NO forman parte de
    # cd_base -- son correcciones adicionales dependientes de Reynolds).
    # Nombrados TERM_A.._E para poder cotejarlos linea a linea contra
    # ghidra_aga3_solver_output.txt (dVar14, dVar10, dVar6, dVar13 alli).
    termino_A = beta_re07 * CD_COEF_RE07 * const_250_035 * const_250_035
    termino_C = beta4 * CD_E_BASE * const_250_035
    termino_D_base = beta4 * CD_D_BASE
    beta11_m2_014 = beta11_m2 * CD_BETA8_SCALE

    termino_D = (f_h_term * CD_FH_SCALE - beta11_m2_014) * beta_re08 * const_475_08
    termino_E = termino_D_base * beta_re08 * const_475_08 * const_250_035

    # --- Estimacion inicial de la variable iterada (constante, NO se recalcula en el bucle) ---
    raiz = sqrt(rho * 2.0 * dP)
    if not isfinite(raiz):
        return None
    base_iter = (mu * REYNOLDS_K * Dr_efectivo) / (Y * E * dr_efectivo * dr_efectivo * raiz)
    if REYNOLDS_CAP < base_iter:
        base_iter = REYNOLDS_CAP

    x_re = 0.0
    Cd = cd_base
    iteraciones = 0
    while True:
        x_re = base_iter / Cd
        if x_re < 0.0:
            return None
        p035 = _pow(x_re, 0.35)
        p08 = _pow(x_re, CD_EXP_RE08)
        term_p08_E = p08 * termino_E

        if UMBRAL_X <= x_re:
            f_x = (COEF_A - COEF_B / x_re) * (term_p08_E + termino_C) \
                + p035 * p035 * termino_A + cd_base
        else:
            f_x = (p035 * termino_A + termino_C + term_p08_E) * p035 + cd_base

        if UMBRAL_X <= x_re:
            df_x = ((term_p08_E + termino_C) * COEF_B) / x_re \
                + termino_A * CD_EXP_RE07 * p035 * p035 \
                + (COEF_A - COEF_B / x_re) * termino_E * CD_EXP_RE08 * p08
        else:
            df_x = (termino_A * CD_EXP_RE07 * p035 + termino_C * Y1992_COEF_BETA4
                    + termino_E * CD_RE_A_COEF * p08) * p035
            # NOTA: el 0.35 aqui es DAT_1801ea410, la MISMA constante que
            # Y1992_COEF_BETA4, reutilizada por FlowXpert en una formula
            # totalmente distinta (derivada del termino "c" del Cd, no del
            # factor de expansion). Se referencia por nombre para dejar
            # explicito que es un valor confirmado, no una casualidad.

        Cd_anterior = Cd
        iteraciones += 1
        delta = (Cd_anterior - (f_x + p08 * termino_D)) / (
            (df_x + termino_D * CD_EXP_RE08 * p08) / Cd_anterior + 1.0)
        Cd = Cd_anterior - delta

        if iteraciones >= MAX_ITERACIONES or fabs(delta) < TOLERANCIA_NR:
            break

    reynolds = RE_MINIMO / x_re
    flujo_final = E * REYNOLDS_SCALE_FINAL * dr_efectivo * dr_efectivo * Cd * Y * raiz
    if not isfinite(flujo_final):
        return None

    return beta, Y, E, Cd, reynolds, flujo_final, iteraciones


def calcular_flujo_flowxpert(valores: dict) -> dict:
    """Punto de entrada. `valores` debe traer las 22 claves de CAMPOS.

    `mu` se recibe en cP (rango [0,10] confirmado en el campo "Dyn. Viscosity"
    del constructor -- ese rango solo tiene sentido fisico en cP, no en
    lbm/(ft*s)) y se pasa TAL CUAL al nucleo, sin ninguna conversion.

    [CORREGIDO 2026-07-20]: una version anterior de este archivo multiplicaba
    `mu` por VISC_CONVERSION=1488.164 antes de llamar al nucleo, asumiendo que
    el wrapper de FlowXpert convertia cP -> lbm/(ft*s). Se comparo contra un
    caso REAL de la app movil de FlowXpert (ver CAPTURA AGA3 1/2/3.jpeg) y esa
    conversion resulto ser incorrecta: con ella, Cd salia con 8.5% de error y
    Reynolds con >1000x de error. Sin aplicar ninguna conversion (mu tal cual
    en cP), Cd, Reynolds y Flujo masico coinciden con el caso real dentro de
    0.001%-0.31% (ver normas/test_aga3_flowxpert_caso_real.py). VISC_CONVERSION
    sigue siendo un valor real extraido del binario (factor cP<->lbm/(ft*s)),
    pero es para el SELECTOR DE UNIDADES del campo (que en FlowXpert acepta
    Pa*s, poise, cP, kgf*s/m2 o lbm/(ft*s)), no una conversion automatica que
    el nucleo aplique siempre."""
    mu_nucleo = valores["mu"]
    return _proyectar_y_corregir(
        valores["dP"], valores["P"], valores["T"], valores["rho"], mu_nucleo,
        valores["K"], valores["Dr"], valores["alphaD"], valores["TrD"],
        valores["dr"], valores["alphad"], valores["Trd"],
        int(valores["Ploc"]), int(valores["Tloc"]), int(valores["Tcorr"]),
        valores["Texp"], int(valores["Dloc"]), valores["Dexp"],
        int(valores["Fluid"]), valores["DrainHole"], valores["Fpwl"],
        int(valores["Edition"]),
    )


if __name__ == "__main__":
    valores = {clave: float(default) if clave not in
               ("Ploc", "Tloc", "Tcorr", "Dloc", "Fluid", "Edition")
               else int(default)
               for clave, _, _, default in CAMPOS}
    res = calcular_flujo_flowxpert(valores)
    print("=== normas/AGA_3_FLOWXPERT.py -- autotest (caso de ejemplo, unidades US customary) ===")
    print(f"  status = {res.get('status')}")
    for clave, etiqueta, unidad in RESULTADOS[1:]:
        val = res.get(clave)
        if val is None:
            print(f"  {etiqueta:32s} {'N/D':>14s}  {unidad}")
        else:
            print(f"  {etiqueta:32s} {val:>14,.6f}  {unidad}")
    print()
    print("NOTA: sin FlowXpert.xll ejecutable (licencia bloqueada) no hay forma de")
    print("comparar este resultado contra un valor de referencia real. Ver docstring")
    print("del modulo para el detalle de que esta confirmado [CERTAIN] y que es")
    print("inferencia [LIKELY]/[GUESSING].")
