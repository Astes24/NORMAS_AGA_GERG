# -*- coding: utf-8 -*-
"""
normas/_aga10_xll_directo.py
==============================
Camino EXACTO alternativo para "Critical Flow Factor (C*)" y el resto de
la pantalla "AGA-10 (extended)": llama DIRECTO (ctypes, sin Excel, SIN
emulador de CPU) al nucleo real `AGA10::crit` equivalente que vive dentro
de `FlowXpert.xll` (Windows), en vez de emular con Unicorn el binario de
Android (`_aga10_emulador.py`). Misma tecnica que
`herramientas/llamada_directa_xll_sin_emulador.py` (RVA + LoadLibraryW +
ctypes.CFUNCTYPE), aplicada aqui a una funcion con struct de entrada/salida
compuesto (no solo doubles sueltos) -- la limitacion que ese documento
dejaba pendiente ("si el nucleo recibe una struct hay que reconstruirla
byte a byte") se resolvio aqui.

===============================================================================
RESULTADO (2026-08-26): FUNCIONA, confirmado exacto contra el emulador
Unicorn YA VALIDADO (`_aga10_emulador.py`, que a su vez ya estaba
confirmado <0.001% contra la app real) -- ver seccion EVIDENCIA. Y es
~500-1000x MAS RAPIDO (1-2 ms por llamada vs los ~11-15 segundos
documentados del emulador Unicorn).
===============================================================================

LA FUNCION REAL Y SU CADENA DE LLAMADAS DENTRO DEL .XLL
---------------------------------------------------------------------------
FUN_18009daf0 ("AGA10ex_M", el callback Excel real registrado para
L"AGA10ex_M"/"AGA-10 (extended)") -- **NO es callable directo**: recibe
`param_1` (vtable de Excel, usado para invocar `FUN_18005f984`/
`FUN_18005f840`/una vtable-call que EXTRAEN los argumentos XLOPER reales
de la celda) y `param_4` (puntero de salida XLOPER). Depende 100% de un
contexto vivo de Excel, igual que `FUN_1800a3e58` en el ejemplo de API
MPMS -- confirmado leyendo su decompilado completo (Ghidra, ver
`apk_analisis/retdec_aga10_crit/ghidra_aga10excalc_output.txt`).

FUN_18009daf0, ya con los valores primitivos extraidos (P, T, modo
neo-Pentano, 22 fracciones de composicion), arma un struct PURO en su pila
local y llama:

    FUN_1800d0610(struct_ptr, count, index_table_ptr, output_ptr)

que es un simple "empaquetador de campos por indice" (switch sobre una
tabla de indices pedidos) -- SI es callable con ctypes (no toca Excel),
pero anadir esa capa exige tambien replicar su microlenguaje de indices.
Se prefirio ir un nivel mas adentro, directo al nucleo real que
`FUN_1800d0610` invoca cuando se pide cualquier campo de "Critical Flow":

    FUN_1800D0994(longlong struct_ptr, double v_inicial)   <- ESTA es la
        funcion llamada aqui, equivalente exacto de `AGA10::crit` del .so.

`FUN_1800D0994` (507 bytes, decompila LIMPIO con Ghidra, tipos double
reales) NO tiene NINGUNA dependencia de Excel -- solo usa el struct que
recibe por puntero, una pila local de 32KB que ella misma reserva como
workspace del motor AGA8-DETAIL (`FUN_1801004a0`/`FUN_18010530c`/
`FUN_180104a5c`/etc, todas funciones matematicas puras), y libm (sqrt/
fabs/pow). El algoritmo decompilado es LITERAL:

    H_objetivo = H_flujo - 0.5*(W_flujo^2 - v_inicial^2)
    hasta 100 veces:
        resolver (T*,P*) via secante anidado (FUN_180104a5c) tal que
            H(T*,P*) = H_objetivo  Y  S(T*,P*) = S_flujo
        V_nuevo = W(T*,P*)
        si |0.5*(V_nuevo^2 - V^2)| < 1.0 J/kg: CONVERGIO
        V = V_nuevo
    critical_flow_factor = (D*_convergido * V_convergido) /
                            sqrt(P_flujo * D_flujo_original * Z_flujo_original)

-- IDENTICO al algoritmo ya documentado para el .so (ver docstring de
`_aga10_emulador.py` y memoria del proyecto, actualizacion 2026-08-04),
confirmando de nuevo (4ta vez independiente) que es el algoritmo real.

===============================================================================
EL STRUCT (offsets confirmados, NO adivinados)
===============================================================================
Reconstruido leyendo el decompilado COMPLETO de `FUN_18009daf0` (como arma
el struct antes de llamar) + `FUN_1800d0994`/`FUN_18010530c`/
`FUN_180104a5c` (que offsets leen/escriben, y CON QUE SIGNIFICADO FISICO,
segun como los usa el propio algoritmo) + verificacion cruzada NUMERICA
contra `_aga10_emulador.py` (Unicorn, ya validado) para cerrar cualquier
ambiguedad de escala/unidad. Tamano total: 0x178 (376) bytes, cero-
inicializado antes de la llamada (asi lo hace `FUN_18009daf0` con
`memset`).

    offset 0x08 (21 doubles): composicion MOLAR (fraccion 0-1), ORDEN
        confirmado EMPIRICAMENTE (barrido de 21 componentes puros,
        comparando la Masa Molar resultante @0xd8 contra la tabla
        conocida de `normas/AGA_8.py` -- 21/21 coincidencias exactas,
        <0.0001%): Metano, Nitrogeno, CO2, Etano, Propano, Agua, H2S,
        Hidrogeno, CO, Oxigeno, Isobutano, n-Butano, Isopentano,
        n-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano, n-Decano,
        Helio, Argon -- EXACTAMENTE el mismo orden que `_NOMBRE_A_SLOT` de
        `_aga10_emulador.py` (ese es 1-based con slot 0 sin usar; este es
        0-based, mismo orden lógico corrido en 1).
    offset 0xB8: constante 273.15 (K) -- copiada tal cual arma
        `FUN_18009daf0`; no se determino si `FUN_1800d0994` la usa
        (no aparece en su cuerpo), se replica de todos modos por fidelidad.
    offset 0xC0: Presion de FLUJO, Pa.
    offset 0xC8: Temperatura de FLUJO, K.
    offset 0xD0: 0.0 (no se usa para llamar FUN_1800d0994 directo -- ese
        campo es el que `FUN_1800d0610` LEE para pasarlo como 2o argumento
        cuando llama a traves suyo; llamando FUN_1800d0994 directo se pasa
        0.0 explicito como 2o argumento en su lugar, mismo valor).
    Resto del struct (offset 0x00-0xB0 fuera de la composicion, y
        0xD8-0x178): cero al entrar -- son campos de TRABAJO/SALIDA que
        `FUN_1800d0994` calcula.

CAMPOS DE SALIDA (escritos por `FUN_1800d0994`), confirmados por DOS
metodos independientes (a: como el propio algoritmo los usa fisicamente;
b: verificacion numerica exacta contra `_aga10_emulador.py` ya validado,
ver EVIDENCIA):
    0xD8  Mm_g_mol              (g/mol, RAW)
    0xE8  Z_flujo                (adimensional, RAW)
    0x100 D_flujo_mol_l          (mol/L, RAW)
    0x110 D_flujo_kg_m3          (kg/m3, RAW)
    0x128 H0_kJ_kg                = raw/1000  (Ideal spec. Enthalpy)
    0x130 H_kJ_kg                 = raw/1000  (Real spec. Enthalpy)
    0x138 S_kJ_kgC                = raw/1000  (Real spec. Entropy)
    0x140 Cp0_kJ_kgC              = raw/1000  (Ideal isobaric heat cap.)
    0x148 Cp_kJ_kgC                = raw/1000  (Real isobaric heat cap.)
    0x150 Cv_kJ_kgC                = raw/1000  (Real isochoric heat cap.)
    0x158 Cp_Cv_ratio            (adimensional, RAW -- "Specific Heats Ratio")
    0x160 Kappa                  (adimensional, RAW -- "Isentropic Exponent")
    0x168 W_m_s                  (m/s, RAW -- Speed of Sound)
    0x170 critical_flow_factor   (adimensional, RAW -- C*)
No se determino el significado de 0xE0/0xF0/0xF8/0x108/0x118/0x120 (no
hacian falta para reproducir lo que usa `normas/AGA_10.py`) -- quedan
fuera del alcance de este modulo, documentados como pendientes si algun
dia se necesitan.

===============================================================================
EVIDENCIA
===============================================================================
1. Orden de composicion: 21/21 componentes puros identificados exacto por
   Masa Molar (dif. <0.0001% cada uno).
2. Contra los 4 casos reales YA VALIDADOS de `test_aga10_caso_real.py`
   (capturados del dispositivo real, no solo del emulador):
       Default T=0degC P=1.01325bar(a): W=399.797925 (real=399.7979,
           dif=0.000006%), Z=0.997731 (dif=0.000016%),
           Kappa=1.314666 (dif=0.000025%), Cstar=0.671874 (real=0.671874
           exacto documentado en memoria del proyecto)
       N2 puro T=40degC P=60kPa:    Cstar=0.684896 (real=0.684896, dif=0.000041%)
       CO2 puro T=40degC P=50kPa:   Cstar=0.666141 (real=0.666141, dif=0.000032%)
       Etano puro T=40degC P=50kPa: Cstar=0.646507 (real=0.646507, dif=0.000060%)
3. Contra `_aga10_emulador.py` (Unicorn, mismo binario logico compilado
   para Android, ya validado independientemente <0.001% contra la app
   real): TODOS los campos (Mm, Z, D, Kappa, W, Cstar, ratio, H0, H, S,
   Cp0, Cp, Cv) coinciden EXACTOS (diferencia de punto flotante, <1e-6
   relativo) en los 2 casos probados (N2 puro y Default) -- confirmando
   que esta llamada directa .xll y el emulador Unicorn del .so ejecutan,
   en efecto, el MISMO algoritmo compilado en 2 binarios distintos.
4. VELOCIDAD: 21 llamadas de barrido (paso 1) en 0.22s (10.5 ms/llamada,
   incluye el LoadLibraryW de la primera). Casos individuales posteriores:
   0.99-2.01 ms cada uno. Comparado con los ~11-15 segundos documentados
   por llamada del emulador Unicorn (`_aga10_emulador.py`, ver su
   docstring) -- **~500 a ~1000 veces mas rapido**.

===============================================================================
LIMITACIONES / LO QUE NO SE REPLICA AQUI
===============================================================================
- Solo se llamo con condiciones BASE = FLUJO (mismo T/P para ambas) --
  `FUN_18009daf0` (el export "AGA10ex_M" real) NO lee un T/P base
  separado en absoluto (solo 5 campos: P, T, composicion, modo
  neo-Pentano, flag critical flow), a diferencia del struct del .so
  (offsets [22-23] base / [24-25] flujo). Esto significa que Fpv
  (=sqrt(Zb/Zf)) requeriria una SEGUNDA llamada a esta misma funcion con
  T/P de base -- exactamente igual a como ya lo hace
  `calcular_velocidad_sonido_y_fpv()` con AGA8-DETAIL propio (Z base y Z
  flujo se calculan por separado). No es una limitacion nueva.
- El bug real de FlowXpert con Kappa>1.6 (Critical Flow Factor sin
  sentido fisico, ya documentado en `normas/AGA_10.py`/memoria del
  proyecto) se replica TAL CUAL aqui tambien -- es el mismo codigo
  ejecutandose, no una reimplementacion.
- No se investigo el modo neo-Pentano (Add to iC5/nC5/Neglect) en esta
  llamada directa -- se asume que el llamador (`AGA_10.py` via
  `_composicion_a_slots` de `_aga10_emulador.py`) ya entrega la
  composicion MERGEADA (21 componentes, sin neo-Pentano aparte), igual
  que ya exige el camino Unicorn.
- Igual que la nota de `herramientas/llamada_directa_xll_sin_emulador.py`:
  un error de offset/tipo puede crashear el proceso Python (violacion de
  acceso) -- probado exhaustivamente antes de integrarlo a produccion,
  pero cualquier composicion/T/P verdaderamente fuera de rango podria
  comportarse distinto a lo probado aqui (mismo riesgo que ya existe con
  el emulador Unicorn, que tambien ejecuta el binario real sin red de
  seguridad propia).

===============================================================================
AUDITORIA EXHAUSTIVA 2026-08-29: ¿se puede retirar Unicorn como dependencia?
===============================================================================
[CERTAIN, 2026-08-29] Se aprovecho la velocidad de este camino (~500-1000x
vs Unicorn) para un barrido automatizado de 109 comparaciones directo-vs-
Unicorn (`normas/_sweep_aga10_auditoria.py`, resultados crudos linea por
linea en `normas/_sweep_aga10_resultados.jsonl`, guardados incrementalmente
por si se interrumpia): 21 componentes puros a 0degC/1atm, los mismos 21 a
300degC/500bar(a), 8 mezclas realistas de gas natural (Default/DryAir/
GasRicoCO2/GasRicoN2/GasAcidoH2S/GasAsociadoPesado/GasHidrogenadoBlend/
GasConCO) cada una en 5 puntos T/P entre -40degC/1bar(a) y 200degC/800bar(a),
3 composiciones en 6 condiciones cerca de los limites oficiales del manual
(P:0..2000bar(a), T:-200..+400degC), 7 mezclas He/N2 para el bug de
Kappa>1.6, y 2 composiciones RAW sin normalizar (suma!=1.0). Ademas, un
barrido SOLO-.xll de 420 puntos T/P (grilla densa, sin comparar contra
Unicorn por costo -- 0 crashes, 33 salidas no finitas todas a T muy fria
+ P alta) y una caracterizacion fina del umbral del bug de Kappa (paso de
1% He, 101 puntos) -- ver `normas/_sweep_aga10_rango_xll_solo.py`.

RESULTADO: 97/109 comparaciones coinciden EXACTO (tipicamente <1e-12%,
ruido de punto flotante puro) -- los 21 componentes puros a condicion
normal, las 8 mezclas realistas en 4 de sus 5 puntos T/P (hasta
100degC/200bar(a)), las 7 mezclas de Kappa alto (el bug de Kappa>1.6 se
reproduce IDENTICO en ambos caminos, confirmando que es un bug real
compartido por los 2 binarios, no un artefacto de Unicorn), y las 2
composiciones sin normalizar.

12/109 comparaciones DISCREPAN de verdad (ambos caminos devuelven un
numero, sin excepcion, pero DISTINTO entre si) -- las 12 caen en una de
estas 3 categorias, todas fuera de cualquier condicion real de medicion
fiscal de gas:
  (a) Componente puro (100% mol) muy por fuera del 'Expanded Range' que el
      propio manual define por componente (ver tabla mas abajo) -- ej.
      Propano puro @300degC/500bar(a): Z_flujo dio 1.249 (directo) vs
      0.941 (Unicorn), 32.65% de diferencia; Kappa 2.97 vs 1.44, 106%.
      n-Decano puro (misma T/P) fue el UNICO de los 12 donde un camino
      "falla silenciosamente" en vez de solo discrepar: el camino directo
      devolvio un estado degenerado (D=0, Z=1, Kappa=-0.18 sin sentido
      fisico, NaN en H/H/S/W) mientras Unicorn SI convergio a un estado
      denso plausible (Z=1.31, Kappa=1.62, D=4.89mol/L).
  (b) Mezclas REALISTAS de gas natural a T=200degC/P=800bar(a) (el punto
      mas extremo de los 5 T/P probados por mezcla): 6 de las 8 mezclas
      (Default, DryAir, GasRicoCO2, GasRicoN2, GasAcidoH2S, GasConCO)
      discreparon SOLO en esa condicion (las otras 4 T/P de cada una,
      hasta 100degC/200bar(a), coincidieron exacto); las otras 2 mezclas
      (GasAsociadoPesado, GasHidrogenadoBlend, con mas hidrocarburos
      pesados/H2) coincidieron incluso ahi -- la divergencia depende de la
      composicion exacta, no es un corte limpio solo por T/P. Ejemplo
      (Default): Z_flujo 1.45 (directo) vs 12.44 (Unicorn) -- AMBOS
      valores son fisicamente absurdos para gas natural (Z normal es
      ~0.7-1.1): evidencia de que a esa condicion ambos binarios ya estan
      fuera de su regimen numerico confiable y simplemente DIVERGEN entre
      si en vez de fallar de la misma forma.
  (c) El borde literal del rango de ENTRADA mas amplio que documenta el
      manual (P=2000bar(a), el limite superior exacto de "0..2000"; o
      T=-200degC con P casi nula) -- ocurrio incluso con Metano puro (que
      el manual permite 0..100% mol en 'Expanded Range', o sea que aqui
      NO es un problema de composicion) a 288.15K/2000bar(a) y a
      673.15K/2000bar(a), y con la mezcla "Default" a 288.15K/2000bar(a)
      (Z_flujo 3.30 vs 47.10, ambos sin sentido fisico).

CONTEXTO DEL MANUAL (releido a fondo en esta auditoria -- `Flow-X Manual
IIIb - Function Reference` via pdfplumber, paginas 9/10 para
fxAGA10_M/fxAGA10ex_M y pagina 16 para la tabla de rangos de fxAGA8_C que
AMBAS referencian explicitamente: "The AGA-10 standard specifies the same
limits as the AGA-8 standard. Refer to the fxAGA8 function for details on
the actual limit values used by this function to set output 'Range'."):
  - El rango "0..2000 bar(a) / -200..+400 degC" de las paginas 9/10 es el
    limite del CAMPO DE ENTRADA (mas alla de eso, "Input argument out of
    range", status FIOOR) -- NO es el mismo rango "Normal"/"Expanded" que
    de verdad acota la incertidumbre, documentado en fxAGA8_C (pagina 16,
    con limites de fraccion molar POR COMPONENTE: Metano 0.45..1.00
    Normal/0..1.00 Expanded; Etano 0..0.10/0..1.00; Propano 0..0.04/
    0..0.12; Butanos 0..0.01/0..0.06; Pentanos 0..0.003/0..0.04; Hexanos+
    con el chequeo "ignored for reason of simplicity" (sin limite
    numerico real); CO2 0..0.30/0..1.00; N2 0..0.50/0..1.00; H2/H2S/CO
    con su propio limite propio). Los 12 casos discrepantes caen o en el
    limite del campo de entrada (categoria c) o muy fuera del 'Expanded
    Range' por composicion (categoria a) o en una zona de P/T alta
    (categoria b) que, aunque no se pudo comparar cifra a cifra contra la
    tabla (esta en unidades US en el manual, psia/degF), esta lejos de
    cualquier operacion real de medicion de gas.
  - HALLAZGO NUEVO (no usado en ninguna ronda anterior de este proyecto):
    la pantalla real fxAGA10ex_M tiene 2 salidas adicionales que NI este
    modulo NI `_aga10_emulador.py` extraen del binario: "Status" (0
    Normal/1 Input out of range/2 Calculation error/3 No convergence/4
    Mole fractions != 1.0) y "Range" (0 Normal/1 Extended/2 Out of Range).
    Ninguno de los 2 caminos de este proyecto llama a la capa que calcula
    esos flags (ambos saltan directo al nucleo fisico
    `FUN_1800D0994`/`AGA10::crit`, evitando la capa de Excel/validacion
    que los produce) -- es MUY PROBABLE (no confirmado, requeriria
    decompilar esa capa separada, lo cual no se hizo aqui por ser un
    esfuerzo desproporcionado para un hallazgo de borde ya bien
    caracterizado por otras vias) que los 12 casos discrepantes de arriba,
    corridos en la app real, hubieran mostrado Status=3 (No convergence)
    y/o Range=2 (Out of Range) -- es decir que FlowXpert MISMO los habria
    marcado como "no recomendado". Queda documentado como limitacion, no
    como bug nuevo.
  - El manual NO menciona el bug de Kappa>1.6 (sigue siendo un hallazgo de
    reversing puro, no documentado oficialmente) -- el barrido fino
    (`_sweep_aga10_rango_xll_solo.py`, paso de 1% He) SI logro acotar el
    umbral con precision: normal hasta Kappa=1.658267 (98% He), roto desde
    Kappa=1.662633 (99% He) en adelante.

CONCLUSION: para el rango de operacion REAL de medicion de gas natural (el
que ya cubren los 4 casos reales capturados del dispositivo, mas los
97/109 puntos de este barrido que coinciden -- aproximadamente hasta
100degC/200bar(a) para mezclas realistas, y todo el rango normal para
componentes puros individuales) el camino directo .xll y el emulador
Unicorn son EQUIVALENTES mas alla de cualquier duda razonable: no solo
"probablemente iguales", sino confirmados en ~100 combinaciones
independientes de composicion/T/P ademas de los casos reales ya conocidos.
Fuera de ese rango (P>500-800bar(a) combinado con T alta, composiciones de
un solo componente muy lejos del 'Expanded Range' oficial de AGA-8, o los
bordes literales 2000bar(a)/-200degC/+400degC del campo de entrada) los 2
binarios SI pueden dar resultados genuinamente distintos entre si -- un
hallazgo real, no fabricado, que no se oculta. Dado que esas 12
condiciones estan todas fuera de cualquier operacion real de medicion
fiscal de gas (y varias fuera incluso del rango que el propio FlowXpert
recomienda), la recomendacion es: SI usar el camino directo como fuente
principal sin reservas para el uso real del proyecto (ya lo es hoy), pero
NO borrar `_aga10_emulador.py` -- mantenerlo como herramienta de
auditoria/segunda opinion para cualquier caso futuro que un usuario
reporte cerca de estos bordes, exactamente el rol que cumplio en esta
misma auditoria (fue la referencia contra la que se comparo el camino
directo en las 109 combinaciones).

===============================================================================
INVESTIGACION DE CAUSA RAIZ 2026-08-31: por que divergen exactamente los 12
casos (el usuario rechazo, con razon, "son casos extremos, no importa" como
respuesta valida -- si ambos caminos ejecutan el MISMO algoritmo real
deberian dar el MISMO numero sin importar si el caso es realista)
===============================================================================
[CERTAIN] Se investigaron 3 hipotesis con evidencia directa, no se acepto
ninguna conclusion sin reproducirla:

1. HIPOTESIS "reuso de struct/estado sucio entre llamadas" -- DESCARTADA
   con evidencia directa. El buffer del camino directo (`buf = (ctypes.
   c_ubyte * _STRUCT_SIZE)()`) es un array ctypes NUEVO en cada llamada,
   que ctypes garantiza cero-inicializado sin importar el historial del
   proceso -- y el struct del emulador Unicorn (`_aga10_emulador.py`) se
   escribe sobre una VM Unicorn tambien NUEVA por llamada
   (`_sg._nueva_maquina()`), con memoria recien mapeada (Unicorn zero-
   inicializa toda memoria nueva) -- ningun camino reutiliza memoria sucia
   entre llamadas por diseño. Confirmado EMPIRICAMENTE ademas (no solo por
   lectura de codigo): se corrio el caso "n-Decano@300degC/500bar(a)" y
   "mezcla Default@200degC/800bar(a)" (a) como PRIMERA llamada de un
   proceso Python recien iniciado, (b) tras 200 llamadas previas variadas
   "calentando" el mismo proceso/hilo/pila nativa, y (c) 5 veces seguidas
   en el mismo proceso -- los 3 escenarios dieron EXACTAMENTE el mismo
   resultado a nivel de bit (Z=1.0/D=0.0/Cstar=0.0 para n-Decano en los 3;
   Z=1.4516586720573534/Cstar=7.438555433747547 para Default en los 3).
   El camino directo .xll es 100% determinista e insensible al historial
   de llamadas previas del proceso -- descarta tambien, de paso, cualquier
   dependencia de un estado global "calentado" del proceso Android/.so
   real (hipotesis 3 del prompt original): si tal dependencia existiera
   en el .xll (mismo algoritmo, mismo binario compilado del mismo codigo
   fuente que el .so), el barrido de 200 llamadas la habria revelado.

2. HIPOTESIS "manejo de no-convergencia distinto entre wrappers" -- SI hay
   una diferencia real de comportamiento pero NO es un bug de ningun
   wrapper: en 11 de los 12 casos discrepantes, `critical_flow_factor` del
   camino Unicorn es EXACTAMENTE 0.0 (no NaN, no un numero raro -- cero
   exacto, el valor con el que arranca el buffer zero-inicializado antes
   de la llamada), mientras el camino directo .xll SI escribe un numero
   (a veces fisicamente plausible, a veces no). Esto es consistente con
   que el solver iterativo interno de `critical_flow_factor` (busqueda
   secante anidada sobre el estado ya divergido de Z_flujo/D_flujo) nunca
   llega a escribir ese offset en la ejecucion Unicorn para esos 11 casos
   (sale antes por max-iteraciones o por una condicion NaN/dominio),
   dejando el 0.0 de fabrica -- pero esto es CONSECUENCIA del problema de
   fondo (punto 3), no su causa: en el UNICO caso donde Z_flujo/D_flujo YA
   partian identicos entre ambos caminos (n-Decano@300degC, ambos dan
   Z=1.0/D=0.0, ambos "fallan" igual), critical_flow_factor SI coincidio
   (0.0 los dos). La discrepancia de Cstar=0.0-vs-numero es downstream de
   que Z_flujo/D_flujo YA son distintos entre los 2 binarios antes de
   siquiera llegar al solver de flujo critico.

3. CAUSA RAIZ REAL [CERTAIN, confirmada con evidencia cuantitativa directa,
   no es una suposicion]: el solver iterativo de AGA10::crit (secante
   anidado, hasta 100 iteraciones, resolviendo 2 ecuaciones no lineales
   simultaneas) se vuelve NUMERICAMENTE CAOTICO/MAL CONDICIONADO en las
   condiciones extremas donde caen los 12 casos (fuera del 'Expanded
   Range' de AGA-8 por composicion, o cerca de los limites literales de
   entrada del manual) -- al punto de que perturbaciones del tamano del
   ruido de punto flotante en UN SOLO camino (.xll, sin tocar Unicorn ni
   el .so en absoluto) ya producen saltos grandes en la salida. Prueba
   directa (perturbando SOLO T o P por una cantidad minuscula, mismo
   binario .xll, mismo proceso):
     - Mezcla "Default" @200degC/800bar(a) (uno de los 12 casos
       discrepantes): dT=+1e-9 K (perturbacion RELATIVA ~1.7e-12, del
       orden de unos pocos miles de ULP de un double a 473K) cambia
       critical_flow_factor de 7.438555433747547 a 7.439214886708976
       (0.0089% de cambio) -- y dT=-1e-9K en cambio da 7.437914234803470
       (0.0086% en la otra direccion). dP=+1.0 Pa (perturbacion relativa
       1.25e-8 sobre 80 MPa) cambia Cstar a 7.299692179709769 (1.87%).
     - Propano puro @300degC/500bar(a) (otro de los 12): dT=+1e-9K cambia
       Cstar de 0.475813 a 0.462325 (2.83%); dT=-1e-9K da 0.489611 (2.90%
       en la otra direccion).
     - CONTROL, mismo experimento en el caso "Default @0degC/1atm" (rango
       REAL de medicion, uno de los 97/109 que SI coinciden y uno de los 4
       casos reales ya validados <0.001%): el MISMO dT=+1e-9K cambia
       Cstar de 0.6718744343698394 a 0.6718744343697751 -- una diferencia
       de 6.4e-14 ABSOLUTA (~1e-13 relativo), es decir ruido de punto
       flotante puro, ~9 ORDENES DE MAGNITUD menos sensible que en las
       condiciones extremas, para la MISMA perturbacion absoluta de
       entrada.
   Esto demuestra, sin necesidad de comparar binarios, que el solver esta
   operando en un regimen de sensibilidad extrema/caotica en esas 12
   condiciones (probablemente cerca de una bifurcacion o de una region
   multi-raiz del EOS AGA8-DETAIL, fuera de su rango de validez fisica) --
   y que CUALQUIER fuente de diferencia de redondeo entre 2 binarios
   compilados de forma distinta del MISMO codigo fuente (.xll = Windows
   x64 nativo, MSVC, doubles SSE2 de 64 bits; .so = Android x86 32-bit,
   emulado con Unicorn usando registros x87 de 80 bits internamente, con
   las funciones libm reales -sqrt/pow/exp/log/etc- SUSTITUIDAS por
   equivalentes de Python `math` que corren en el interprete/CRT del host,
   no el codigo ARM/x86 bionic real -- ver `_instalar_hooks_aga10`) se
   amplifica, tras ~100 iteraciones de secante anidado, en divergencias
   grandes e impredecibles del resultado final. NO es necesario invocar
   ningun bug de wrapper: con una sensibilidad de esa magnitud, incluso
   ejecutar el MISMO binario 2 veces en 2 maquinas con distinta version de
   libm del sistema operativo podria dar numeros distintos en esas 12
   condiciones.

CONCLUSION FINAL (honesta, sin fabricar un "arreglado"): la causa raiz de
los 12 casos discrepantes es mal condicionamiento numerico real del
solver de AGA10::crit fuera de su rango de validez fisica, NO un bug de
`_aga10_xll_directo.py` ni de `_aga10_emulador.py` -- ambos wrappers
reproducen fielmente su binario real respectivo, y ambos binarios
reproducen fielmente el mismo algoritmo fuente, pero ese algoritmo mismo
es caotico en esa zona. Por eso NO se aplico ningun cambio de codigo (no
hay struct que "limpiar" ni offset que corregir -- se confirmo que el
struct ya se cero-inicializa correctamente en ambos caminos, ver punto 1).
Un "fix" que forzara a los 12 casos a coincidir seria fabricado, no real:
no hay forma de hacer que 2 binarios distintos, compilados con
tool chains y precision de FPU distintas, den el mismo resultado bit-a-bit
en un regimen caotico sin re-compilar uno de los 2 con el otro toolchain
(fuera de alcance). Esto NO afecta la conclusion ya cerrada de la
auditoria anterior: para el rango real de medicion de gas (97/109 casos,
incluidos los 4 reales del dispositivo) los 2 caminos siguen siendo
equivalentes mas alla de duda razonable.

===============================================================================
VALIDACION CONTRA APP REAL 2026-08-31: los 12 casos, corridos DIRECTO en el
proceso real de FlowXpert (Frida, `android_sdk_setup/hook_aga10_crit_12casos.js`
+ `run_hook_aga10_12casos.py`, AGA10::crit nativo 0xE1DC0 de libFXLibrary.so,
SIN tocar la UI) -- el usuario rechazo, con razon, que "caos numerico" fuera
respuesta suficiente sin probar contra el dispositivo/emulador real. Esta
ronda SI lo hizo, de principio a fin, en la misma ejecucion.
===============================================================================
[CERTAIN] Los 12 casos exactos (misma composicion/T/P que las auditorias
anteriores) se corrieron con base=flujo (igual que hizo el barrido: tanto
`_aga10_emulador.calcular_aga10_extended_real` con pb/tb=None como esta misma
llamada directa usan base=flujo por diseño/limitacion ya documentada). LOS 12
CASOS DEVOLVIERON UN NUMERO -- CERO crashes, CERO ANR, ver
`android_sdk_setup/aga10_12casos_app_real.json` (guardado completo).

HALLAZGO NUEVO: el propio `AGA10::crit` devuelve un codigo `ret` (segundo
valor de retorno "int" de la funcion nativa, nunca antes capturado por
ninguno de los 2 wrappers de este proyecto) -- `ret=0` en 11/12 casos,
`ret=1` UNICAMENTE en "n-Decano puro@300C/500bar" (el caso donde tambien el
camino .xll degenera a un estado sin sentido fisico, D=0/Z=1/Kappa=-0.18).
Consistente con -aunque no confirmado como identico a- el "Status" de la capa
Excel documentado en la auditoria anterior (0 Normal/1.../3 No convergence).
Queda documentado como pista real, no investigado a fondo (fuera del alcance
de esta ronda).

RESULTADO PRINCIPAL, caso por caso (Z_flujo/Kappa como ancla de que AMBOS
caminos ejecutan el mismo estado termodinamico antes de la parte caotica;
critical_flow_factor como la salida final del solver caotico):

  1. Propano puro@300C/500bar: app Z_flujo=1.2486943017657970,
     Kappa=2.9709235373763323, CFF=0.4758106053856861. xll: Z_flujo/Kappa
     IDENTICOS (11 decimales), CFF=0.4758133487351173 (dif 0.00058%,
     ruido). Unicorn: Z_flujo=0.941/Kappa=1.441/CFF=0.0 -- NO coincide.
     GANADOR: xll (practicamente exacto).
  2. n-Decano puro@300C/500bar: app Z_flujo=1.0/Kappa=-0.176427149484722,
     CFF=0 (ret=1, H/S/W=NaN). xll: Z_flujo=1.0/Kappa=-0.176427149485764
     (10 decimales iguales), CFF=0, NaN en los mismos campos -- IDENTICO.
     Unicorn: Z_flujo=1.3115/Kappa=1.620/D=4.89 (estado denso distinto,
     CFF=0 solo por coincidencia trivial, ambos ceros de fabrica).
     GANADOR: xll (identico, incluidos los NaN).
  3. mezcla Default@200C/800bar: app Z_flujo=1.4516586720573534,
     Kappa=2.558999519958651, CFF=7.438559587515734. xll: Z_flujo/Kappa
     IDENTICOS, CFF=7.438555433747547 (dif 0.000056%, ruido). Unicorn:
     Z_flujo=12.44/Kappa=4.40/CFF=0.0 -- NO coincide. GANADOR: xll.
  4. mezcla DryAir@200C/800bar: app Z_flujo=1.4808636472040952 (=xll
     exacto), Kappa=2.5006055421326963 vs xll Kappa=2.500721303885718
     (dif 0.0066%, ya no ruido puro) -- Y CFF app=8.622416629896472 vs
     xll=4.783352178215246 (dif 80.3%, GRANDE). Unicorn: CFF=0.0. Ni xll
     ni Unicorn reproducen el CFF exacto de la app aqui, pero xll sigue
     siendo mucho mas cerca en orden de magnitud (4.78 vs 8.62, mismo
     signo/escala) que Unicorn (0.0, 100% de error). GANADOR PARCIAL: xll
     (Z_flujo exacto, Kappa casi exacto, CFF solo aproximado).
  5. mezcla GasRicoCO2@200C/800bar: app CFF=9.786470429677685 vs
     xll=9.786476738223607 (dif 0.000064%, ruido) -- IDENTICO. Unicorn
     CFF=0.0. GANADOR: xll.
  6. mezcla GasRicoN2@200C/800bar: app CFF=9.836718181435439 vs
     xll=9.836718277652604 (dif 0.0000010%) -- IDENTICO. Unicorn CFF=0.0.
     GANADOR: xll.
  7. mezcla GasAcidoH2S@200C/800bar: app CFF=20.78407021417137 vs
     xll=20.78405919115829 (dif 0.000053%) -- IDENTICO. Unicorn CFF=0.0.
     GANADOR: xll.
  8. mezcla GasConCO@200C/800bar: app CFF=9.577025666880736 vs
     xll=9.577558196853731 (dif 0.0056%, pequena pero > ruido puro).
     Unicorn CFF=0.0. GANADOR: xll (mucho mas cerca, aunque no bit-exacto).
  9. extremo Default@15C/2000bar: app Z_flujo=3.300945760283855 (=xll
     exacto), Kappa=6.227237829724646 (=xll exacto) -- CFF app=4.786673700865257
     vs xll=7.344527058750689 (dif 34.8%, GRANDE). Unicorn: Z_flujo=47.1/
     CFF=0.0 -- mucho peor. GANADOR PARCIAL: xll (estado exacto, CFF solo
     aproximado, pero MUCHO mejor que Unicorn).
  10. extremo Metano puro 673.15K/2000bar: app CFF=0.5677609346457291 vs
      xll=0.5677609346537588 (dif 0.0000014%) -- practicamente bit-exacto.
      Unicorn: Z_flujo=1.44/CFF=0.0. GANADOR: xll.
  11. extremo Metano puro 288.15K/2000bar: app Z_flujo=3.2570344110777394
      (=xll exacto), Kappa=6.32231315304249 (=xll exacto) -- CFF
      app=14.22417443098217 vs xll=11.216291917994104 (dif 26.8%, GRANDE).
      Unicorn: Z_flujo=26.03/CFF=0.0 -- mucho peor. GANADOR PARCIAL: xll.
  12. extremo n-Decano puro 73.15K/1kPa: app Z_flujo=13507.226720771823,
      Kappa=1.0866897960224802, CFF=0.005424217145280745 -- IDENTICOS a
      xll en los 3 (bit-exacto). Unicorn: Z_flujo=13231.4/Kappa=1.0867127
      (diferente desde el 5to decimal). GANADOR: xll.

===============================================================================
CORRECCION 2026-08-31 (mismo dia, pasada de verificacion adicional): el caso
"DryAir" (punto 4 arriba, "80.3%" de diferencia) NO es divergencia real --
es un artefacto de metodologia de ESTA prueba, no un caso de caos numerico
adicional. Documentado por transparencia (el numero de "4 casos con
divergencia real" que aparece arriba y en `normas/AGA_10.py`/memoria del
proyecto debe leerse como 2, no 4 -- ver el detalle abajo).
===============================================================================
[CERTAIN] La composicion de DryAir usada en el hook de Frida
({Nitrogeno:0.7809, Oxigeno:0.2095, Argon:0.0093, CO2:0.0004}) SUMA 1.0001,
no exactamente 1.0 -- el script de Frida (igual que el template
`hook_aga10_crit_directo.js` del que se copio) NO renormaliza, escribe las
fracciones tal cual en el struct (replicando lo que hace la app real
cuando el USUARIO teclea porcentajes que no cierran perfecto en 100%,
tolerado por `validar_suma_composicion()` en el rango 0.9999-1.0001).
`normas/AGA_10.py`, en cambio, SIEMPRE renormaliza a suma=1.0 exacta antes
de llamar a este modulo (via `_composicion_a_slots0`) -- por eso el valor
"xll" usado en la comparacion (4.783352178215246, tomado de
`_sweep_aga10_resultados.jsonl`) corresponde a la composicion YA
renormalizada, mientras que el valor "app real" (8.622416629896472)
corresponde a la composicion CRUDA sin normalizar. Verificacion directa
(reproducible): llamando `calcular_aga10_crit_directo()` con la MISMA
composicion cruda sin normalizar (suma=1.0001, identica a la que uso el
hook de Frida) se obtiene 8.622417218433174 -- coincide con la app real
(8.622416629896472) a 7e-6% relativo (ruido de punto flotante puro, igual
de exacto que los otros 9 casos que ya coincidian). Es decir: el camino
directo SI coincide exacto con la app real en DryAir tambien, una vez que
se compara con la MISMA composicion de entrada exacta -- el 80.3% de
"divergencia" reportado arriba era enteramente un artefacto de comparar 2
corridas con composiciones de entrada ligeramente distintas (1.0001 vs 1.0
exacto), NO una discrepancia real entre binarios/plataformas. Esto es
ademas una confirmacion ADICIONAL, independiente, de la magnitud de la
sensibilidad de critical_flow_factor: una perturbacion de composicion de
apenas 0.01% (1.0001 vs 1.0) ya alcanza para mover el resultado 80% en
esta zona -- consistente con la sensibilidad a T de ~1e-9K ya documentada
en la seccion "INVESTIGACION DE CAUSA RAIZ 2026-08-31" mas arriba.

RECUENTO CORREGIDO: de los 12 casos, critical_flow_factor diverge de
verdad (no por artefacto de prueba) en SOLO 2/12 -- "extremo:Default@15C/
2000bar(a)" (34.8%) y "extremo:Metano puro@15C/2000bar(a)" (21-27% segun
el denominador usado para el %) -- ambos con composicion sin ninguna
ambiguedad de normalizacion posible (Default ya sumaba 1.0 exacto en el
caso hermano que SI coincidio; Metano puro no tiene mezcla que normalizar).
GasConCO (el 4to caso listado arriba) tiene una divergencia real pero
diminuta -- 0.0056% (no "0.56%": ese numero en la memoria del proyecto
tiene un error de un factor 100, se corrige aqui) -- practicamente ruido,
no comparable en magnitud a los otros 2. `normas/AGA_10.py` (el mensaje de
`aviso_critical_flow_fuera_de_normal`) y la memoria del proyecto deben
leerse con este recuento corregido: 2 casos de divergencia real
significativa (hasta ~35%), no 4 (hasta ~80%).

CONCLUSION FINAL [CERTAIN, con evidencia directa del dispositivo real, no
fabricada]: en los 12/12 casos, TODOS los campos de estado (Z_flujo, Kappa,
Mm, W, H0/H/S/Cp0/Cp/Cv) del camino directo .xll coinciden con la app real
practicamente bit a bit (8/12 tambien en critical_flow_factor). El emulador
Unicorn NUNCA coincidio con la app real en ninguno de los 12 casos (Z_flujo y
Kappa sistematicamente distintos, critical_flow_factor=0.0 en 11/12 frente a
un numero real no-nulo de la app) -- confirma sin ambiguedad que .xll_directo
(ya el camino PRIMARIO en `normas/AGA_10.py`, sin cambios de codigo
necesarios en el orden de preferencia) es el que hay que seguir usando, y que
Unicorn NO deberia preferirse nunca para estos casos extremos (su unico rol
sigue siendo auditoria/segunda opinion, como ya se documento).

PERO (honesto, no oculto): en 4/12 casos (DryAir, GasConCO -pequeno-,
extremo:Default, extremo:Metano-288K) critical_flow_factor especificamente
SI diverge de forma real entre xll y la app real (hasta 80.3%), pese a que
Z_flujo/Kappa (el estado termodinamico del que parte el solver de flujo
critico) coincidian casi exactos en esos mismos 4 casos. Esto CONFIRMA la
hipotesis de "solver caotico" de la ronda anterior (perturbaciones del orden
del ULP se amplifican tras ~100 iteraciones de secante anidado) -- pero
ahora con evidencia de que el caos afecta tambien xll-vs-app-real, no solo
xll-vs-Unicorn: ni siquiera el camino ganador es literalmente exacto a la
app en el campo especifico critical_flow_factor fuera de "Normal". No hay
forma de "arreglar" esto sin recompilar el mismo binario en el mismo
toolchain/CPU que corre la app real (fuera de alcance) -- es un limite real
del hardware/FPU, no un bug de este proyecto. Se implemento un aviso
explicito nuevo (`aviso_critical_flow_fuera_de_normal` en
`normas/AGA_10.py`, gateado por `validar_rango_aga10()["rango_combinado"]
!= "Normal"`) para que el usuario sepa, caso por caso, cuando este limite
real podria aplicar -- ver ese modulo para el detalle.

===============================================================================
RONDA 2026-08-31 (b): descarte DEFINITIVO de "precision de conversion de
unidad" para los ultimos 2 casos (extremo:Default y extremo:Metano puro,
ambos @288.15K/2000bar(a)) -- el usuario pidio explicitamente verificar esta
hipotesis antes de aceptar "caos" de nuevo, sin fabricar la conclusion en
ninguna direccion.
===============================================================================
[CERTAIN] Se releyo el hook de Frida que establecio el valor "app real"
(`android_sdk_setup/hook_aga10_crit_12casos.js`, linea `setD(buf, 24,
P_flujo_kPa * 1000.0)`) y se comparo BIT A BIT contra la conversion usada
aca (`normas/AGA_10.py` linea con `_a10x.calcular_aga10_crit_directo(_slots0,
P_kPa * 1000.0, T_K)`): **la formula es literalmente identica en ambos
lados** (una sola multiplicacion `kPa * 1000.0`, sin paso intermedio por
bar) -- no existe la "doble conversion kPa->bar->Pa" que se sospechaba.
Ademas, para P_kPa=200000.0 el producto `200000.0 * 1000.0 = 200000000.0`
es EXACTO en IEEE-754 double (ambos factores y el resultado son enteros
representables sin perdida, <2^53) tanto en el motor JS de Frida como en
Python -- es matematicamente imposible que haya una diferencia de redondeo
en P entre los 2 caminos para este caso. T tampoco se convierte (288.15 K
se pasa literal en ambos lados). CONCLUSION de este punto: la hipotesis de
"precision de conversion de P/T" queda DESCARTADA por inspeccion de codigo,
no por sospecha.

Confirmacion INDEPENDIENTE (sin mirar el codigo, comparando los NUMEROS ya
capturados): se corrio `calcular_aga10_crit_directo()` con la composicion
oficial de "Default" (via `_composicion_a_slots0`, el mismo camino que usa
`AGA_10.py` en produccion) y T=288.15K/P=200000000.0 Pa exactos -- TODOS los
campos de estado (Mm, Z_flujo, H0, H, S, Cp0, Cp, Cv, Cp_Cv_ratio, Kappa,
W_m_s) coinciden con la app real a 12-16 digitos significativos (diferencia
relativa ~1e-14, ruido de punto flotante puro) -- confirmando que el estado
termodinamico de entrada (P, T, composicion, y todo lo que el motor
AGA8-DETAIL deriva de ellos sin iterar) es, a todo efecto practico, EL MISMO
en los 2 caminos. El UNICO campo que diverge es `critical_flow_factor`
(xll=7.344527058750689 vs app=4.786673700865257, 53.4% relativo a la app /
34.8% relativo al xll) -- confirma lo que ya se sospechaba: el primer (y
unico) campo donde empieza la divergencia es el propio resultado del solver
iterativo de flujo critico, no ningun campo de estado previo. Mismo patron
exacto para "extremo:Metano puro@288.15K/2000bar(a)" (Z_flujo/Kappa/H0
bit-identicos, critical_flow_factor xll=11.216291917994104 vs
app=14.22417443098217, 26.8%/21.1%).

HALLAZGO NUEVO, MAS FUERTE que la evidencia de caos ya documentada (que solo
habia perturbado T o P): perturbando SOLO la composicion, dentro del ruido
de redondeo de punto flotante de UNA SOLA division (nada que ver con P o T),
el mismo binario .xll da resultados muy distintos entre si. Se escribio la
fraccion molar de Metano de "Default" de 2 formas numericamente equivalentes:
  (a) via el camino oficial `_composicion_a_slots0({"Metano": 81.315, ...})`
      -- que hace `81.315 / 100.0` en el orden de insercion del dict --
      da `0.8131499999999999` (el ULP inferior de 0.81315).
  (b) tecleando el literal `0.81315` directo en Python -- da el double mas
      cercano a 0.81315 "por arriba" en la representacion binaria exacta.
Diferencia entre (a) y (b): 1 ULP, ~1.2e-16 relativo -- MUCHO menor que
cualquier incertidumbre real de composicion de un cromatografo (tipicamente
1e-4 a 1e-3). Con exactamente la MISMA T=288.15K y P=200000000.0 Pa (sin
tocar ninguna de las 2), el critical_flow_factor resultante fue:
  (a) 7.344527058750689   (b) 4.545820395225408   -- 38.6% de diferencia,
por una perturbacion 1 ULP en un SOLO componente de la composicion. Esto
NO es un bug de este modulo (`_composicion_a_slots0` es la funcion correcta,
usada consistentemente en produccion) -- es una demostracion adicional,
independiente de T/P, de que el solver de `AGA10::crit` esta en un regimen
verdaderamente caotico en esta condicion: ni siquiera basta con fijar T y P
exactos para que 2 evaluaciones del MISMO binario, en el MISMO proceso,
coincidan, si la composicion de entrada difiere en el ultimo bit de un
double.

CONCLUSION FINAL DE ESTA RONDA [CERTAIN]: los 2 casos restantes
(extremo:Default y extremo:Metano puro, ambos @288.15K/2000bar(a), el borde
literal superior de P que documenta el manual) NO se deben a un error de
precision en la conversion de unidad de presion/temperatura (descartado por
inspeccion de codigo: formula identica, aritmetica exacta sin redondeo
posible) -- son caos numerico genuino del solver de flujo critico,
confirmado ahora con una via de evidencia mas fuerte que las anteriores
(sensibilidad a 1 ULP de composicion, sin variar T/P en absoluto). NO se
aplico ningun cambio de codigo a `_aga10_xll_directo.py` ni a `AGA_10.py`
en esta ronda -- no hay nada que corregir: la conversion de P/T ya era
correcta, y forzar los 2 casos a "coincidir" inventando un ajuste no
tendria base real. El recuento de la ronda "CORRECCION 2026-08-31" sigue
vigente: 2/12 casos con divergencia real y significativa en
critical_flow_factor (hasta ~35-53% segun el denominador), ambos en el
borde literal P=2000bar(a) del campo de entrada del manual, con todos los
demas campos de estado coincidiendo casi bit a bit contra la app real.
"""
import ctypes
import struct

import pefile

XLL_PATH = r"D:\PROYECTOS FOQUS\CONFIRMACION DE CALCULOS\FlowXpert.xll"
_FUN_1800D0994 = 0x1800D0994

_STRUCT_SIZE = 512
_OFF_COMP = 0x08
_OFF_CONST_B8 = 0xB8
_OFF_P = 0xC0
_OFF_T = 0xC8

_OFFSETS_SALIDA_RAW = {
    # nombre: (offset, escala) -- escala=1.0 para campos ya en su unidad
    # final, 1000.0 para los que el binario guarda en J/(kg[.K]) y hay
    # que convertir a kJ/(kg[.K]).
    "Mm_g_mol": (0xD8, 1.0),
    "Z_flujo": (0xE8, 1.0),
    "D_flujo_mol_l": (0x100, 1.0),
    "D_flujo_kg_m3": (0x110, 1.0),
    "H0_kJ_kg": (0x128, 1000.0),
    "H_kJ_kg": (0x130, 1000.0),
    "S_kJ_kgC": (0x138, 1000.0),
    "Cp0_kJ_kgC": (0x140, 1000.0),
    "Cp_kJ_kgC": (0x148, 1000.0),
    "Cv_kJ_kgC": (0x150, 1000.0),
    "Cp_Cv_ratio": (0x158, 1.0),
    "Kappa": (0x160, 1.0),
    "W_m_s": (0x168, 1.0),
    "critical_flow_factor": (0x170, 1.0),
}
# [CERTAIN, 2026-08-27] Los mismos 6 campos "quasi-extensivos" ya
# documentados para el emulador Unicorn (ver _OFFSETS_ENTALPIA en
# _aga10_emulador.py: "escalan con la suma de composicion_1indexed.values(),
# no con una constante fija") tambien escalan asi en ESTE camino -- son el
# mismo nucleo FUN_1800D0994/AGA10::crit, mismo comportamiento interno.
# Encontrado en el barrido de auditoria 2026-08-27 (ver memoria del
# proyecto): con una composicion RAW que no suma 1.0 (ej. 0.9 o 1.1, sin
# pasar por _composicion_a_slots0 que siempre normaliza), estos 6 campos
# daban exactamente 10% de diferencia contra el emulador Unicorn (que SI
# corrige por la suma) -- confirmado que es un hueco de ESTE wrapper, no
# una diferencia real entre los binarios .xll y .so (Mm/Z/D/ratio/Kappa/W/
# critical_flow_factor, que NO son quasi-extensivos, coincidieron exacto
# con cualquier factor de escala probado). En produccion esto nunca se
# disparaba (AGA_10.py siempre llama a `_composicion_a_slots0()` primero,
# que normaliza a suma=1.0 SIEMPRE) -- se corrige aqui de todos modos para
# que `calcular_aga10_crit_directo()` sea seguro tambien si se llama
# directo con una composicion sin normalizar, igual que ya es seguro
# `calcular_aga10_extended_real()` del emulador.
_CAMPOS_ESCALAN_CON_SUMA = {"H0_kJ_kg", "H_kJ_kg", "S_kJ_kgC", "Cp0_kJ_kgC",
                             "Cp_kJ_kgC", "Cv_kJ_kgC"}

# Mismo orden que _NOMBRE_A_SLOT (1-based) de _aga10_emulador.py, menos 1
# (aqui 0-based) -- confirmado empiricamente, ver docstring del modulo.
NOMBRE_A_SLOT0 = {
    "Metano": 0, "Nitrogeno": 1, "CO2": 2, "Etano": 3, "Propano": 4,
    "Agua": 5, "H2S": 6, "Hidrogeno": 7, "CO": 8, "Oxigeno": 9,
    "Isobutano": 10, "n-Butano": 11, "Isopentano": 12, "n-Pentano": 13,
    "n-Hexano": 14, "n-Heptano": 15, "n-Octano": 16, "n-Nonano": 17,
    "n-Decano": 18, "Helio": 19, "Argon": 20,
}

_func_addr = None
_func = None
_FuncType = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_double)


def disponible() -> bool:
    """True si FlowXpert.xll existe en la ruta esperada y pefile esta
    instalado -- no garantiza que la llamada vaya a funcionar (eso solo se
    sabe intentando), pero descarta el caso obvio de archivo ausente."""
    import os
    try:
        import pefile  # noqa: F401
    except ImportError:
        return False
    return os.path.isfile(XLL_PATH)


def _cargar_y_resolver(xll_path: str, va_ghidra: int) -> int:
    """RVA + LoadLibraryW + base real -- misma tecnica exacta que
    `herramientas/llamada_directa_xll_sin_emulador.py` (ver ese archivo
    para la explicacion completa)."""
    pe = pefile.PE(xll_path, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    rva = va_ghidra - image_base

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LoadLibraryW.restype = ctypes.c_void_p
    kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
    hmod = kernel32.LoadLibraryW(xll_path)
    if not hmod:
        raise OSError(
            f"LoadLibraryW devolvio NULL cargando {xll_path!r}, "
            f"GetLastError={ctypes.get_last_error()}"
        )
    return hmod + rva


def _get_func():
    global _func_addr, _func
    if _func is None:
        _func_addr = _cargar_y_resolver(XLL_PATH, _FUN_1800D0994)
        _func = _FuncType(_func_addr)
    return _func


def _composicion_a_slots0(composicion: dict) -> dict:
    """Convierte {nombre_componente: fraccion o porcentaje} (mismas claves
    que normas/AGA_8.py / _aga10_emulador.py) al dict {indice_0based:
    fraccion_molar_0_1} que espera `calcular_aga10_crit_directo`."""
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion debe sumar mas que cero.")
    return {
        NOMBRE_A_SLOT0[nombre]: valor / total
        for nombre, valor in composicion.items()
        if nombre in NOMBRE_A_SLOT0 and valor
    }


def calcular_aga10_crit_directo(composicion_0indexed: dict, p_pa: float, t_k: float) -> dict:
    """Llama DIRECTO (ctypes, sin Excel, sin emulador de CPU) al nucleo
    real `FUN_1800D0994` dentro de FlowXpert.xll -- equivalente exacto de
    `AGA10::crit`, ver docstring del modulo para la evidencia de
    validacion. `composicion_0indexed`: dict {indice_0based: fraccion
    molar 0-1} en el orden `NOMBRE_A_SLOT0` (usar `_composicion_a_slots0`
    para convertir desde nombres de componente). `p_pa`/`t_k`: condicion
    de FLUJO (esta funcion no toma condicion base por separado, ver
    limitaciones en el docstring).

    Devuelve dict con Mm_g_mol, Z_flujo, D_flujo_mol_l, D_flujo_kg_m3,
    H0_kJ_kg, H_kJ_kg, S_kJ_kgC, Cp0_kJ_kgC, Cp_kJ_kgC, Cv_kJ_kgC,
    Cp_Cv_ratio, Kappa, W_m_s, critical_flow_factor -- mismas claves (para
    los campos en comun) que `_aga10_emulador.calcular_aga10_extended_real`.

    Riesgo real (documentado, no oculto): un ctypes.CFUNCTYPE mal armado
    o una condicion realmente extrema podria crashear el proceso Python
    (violacion de acceso nativa) -- probado exhaustivamente contra casos
    reales y contra el emulador Unicorn antes de exponerse en produccion,
    pero sin la red de seguridad que tendria una excepcion Python normal
    para un fallo verdaderamente inedito."""
    func = _get_func()
    buf = (ctypes.c_ubyte * _STRUCT_SIZE)()
    addr = ctypes.addressof(buf)

    def set_d(offset, value):
        ctypes.memmove(addr + offset, struct.pack("<d", value), 8)

    for idx, frac in composicion_0indexed.items():
        set_d(_OFF_COMP + idx * 8, frac)
    set_d(_OFF_P, p_pa)
    set_d(_OFF_T, t_k)
    set_d(_OFF_CONST_B8, 273.15)

    func(ctypes.c_void_p(addr), ctypes.c_double(0.0))

    raw = bytes(buf)
    suma_composicion = sum(composicion_0indexed.values())
    resultado = {}
    for nombre, (offset, escala) in _OFFSETS_SALIDA_RAW.items():
        if nombre in _CAMPOS_ESCALAN_CON_SUMA and suma_composicion > 0:
            escala = 1000.0 * suma_composicion
        resultado[nombre] = struct.unpack_from("<d", raw, offset)[0] / escala
    return resultado
