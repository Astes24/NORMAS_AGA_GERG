# -*- coding: utf-8 -*-
"""
normas/ISO_6976_1983.py
========================
===============================================================================
*** RE-VERIFICACION EXHAUSTIVA 2026-08-13 (tarea de continuacion, CIERRE DEL
    HILO ABIERTO "revisar las 3 variantes tocando cada fila") -- CONFIRMADO
    SIN HALLAZGOS NUEVOS. Se relanzo la app limpia (`am force-stop` +
    `am start -n com.spiritit.flowxpert/.ui.activities.SplashActivity`,
    evita el bug de menu "ISO" stale ya documentado) y se re-navego
    Categoria->ISO->"ISO-6976 (1983)" desde cero. Se toco LITERALMENTE cada
    fila de la pantalla (no solo los 2 selectores ya conocidos), con
    `uiautomator dump` como evidencia en cada paso:
    - "Composition": abre el editor de composicion (22 componentes), NO es
      un selector de opciones fijas -- descartado como candidato.
    - "Metering Ref. Temp.": el dialogo de edicion tiene un `value_spinner`
      (bounds `[101,263][296,297]`) que, al tocarlo, abre un `ListView` con
      EXACTAMENTE 2 `CheckedTextView` ("0 °C" checked, "15 °C") -- CONFIRMA
      byte a byte lo ya documentado en la seccion 2A, sin nada mas.
    - "Cal. Val. ref. Temp.": mismo patron, `ListView` con EXACTAMENTE 5
      `CheckedTextView` ("25/0 °C" checked, "0/0 °C", "15/0 °C", "15/15 °C",
      "60/60 °F") -- confirmado tambien que el `ListView` (bounds
      `[105,269][280,513]`, `scrollable="false"`) no tiene mas items arriba
      ni abajo, 5 es el total real.
    - Los 5 renglones de "Results" (Sup. Calorific Val., Density,
      Compressibility, Relative Density, Molar Mass) son TODOS
      `LinearLayout clickable="true"` igual que las filas de entrada (ese
      atributo por si solo NO distingue selector real de fila informativa,
      hallazgo de metodo util para futuras rondas). Al tocar cada uno: el
      dialogo que abren tiene un `value_field` (`EditText enabled="false"`,
      de solo lectura) y, en las 3 salidas CON unidad fisica (Sup.
      Calorific Val., Density, Molar Mass), un `unit_field` (`Spinner`
      real, 7 opciones confirmadas en Sup. Calorific Val.: J/m3, kJ/m3,
      MJ/m3, Btu/ft3, kBtu/ft3, cal/m3, kcal/m3) -- este spinner de UNIDAD
      es el mismo mecanismo de conversion de visualizacion ya conocido del
      resto de la app (memoria del proyecto, actualizacion 2026-08-03), NO
      un selector que cambie el CALCULO -- solo re-expresa el mismo
      resultado en otra unidad. Compressibility y Relative Density (ambas
      adimensionales) NO tienen `unit_field`, solo `value_field` de solo
      lectura -- consistente. NINGUN renglon de salida abre un picker de
      opciones que cambie que formula/indice se usa.
    CONCLUSION: los 2 selectores de la seccion 2A ("Metering Ref. Temp.",
    "Cal. Val. ref. Temp.") son los UNICOS selectores de calculo reales de
    esta pantalla -- confirmado tocando cada fila (entrada Y salida), no
    solo por analogia o por edicion directa de los 2 ya sospechados. No se
    encontro ningun selector nuevo. Evidencia guardada en
    `android_sdk_setup/ui_verif0813_1983_*.xml` (11 dumps de esta ronda). ***
===============================================================================
*** CORRECCION 2026-08-11 (tarea de continuacion, ERROR REAL de la ronda
    anterior) -- la conclusion de abajo ("1983_M es la UNICA de las 3
    variantes base sin ninguno de esos 3 selectores", "sin selector de Ref.
    Temperature") estaba MAL. La ronda anterior NUNCA TOCO los 2 campos
    "Metering Ref. Temp." / "Cal. Val. ref. Temp." para ver si abrian un
    picker -- asumio que eran fijos solo porque los botones
    `browse_next`/`browse_prev` del dialogo de EDICION cerraban el dialogo
    sin cambiar nada (ver seccion 2 mas abajo, parrafo "HALLAZGO DE METODO
    IMPORTANTE", ahora corregido). Al TOCAR el campo (no los botones
    browse) SI se abre un picker real con Ghidra... con Android, confirmado
    por `uiautomator dump` sobre la app real en el emulador:
    - **"Metering Ref. Temp."**: picker real de **2 opciones**: 0 °C, 15 °C.
    - **"Cal. Val. ref. Temp."**: picker real de **5 opciones**: 25/0 °C,
      0/0 °C, 15/0 °C, 15/15 °C, 60/60 °F.
    Ademas, hookeando con Frida la funcion real `PropertiesISO6976_1983`
    mientras se cambiaba cada opcion en la app, se capturo el mapeo EXACTO
    de indice interno -> opcion de UI (arg2/arg3 de la firma real, ver
    seccion 1): **arg2 = indice del picker de "Metering Ref. Temp." (0 o 1,
    en el MISMO orden que la lista) y arg3 = indice del picker de "Cal. Val.
    ref. Temp." (0-4, en el MISMO orden que la lista)** -- indexacion
    DIRECTA, sin offset ni formula, la mas simple posible. Con 7 casos
    reales (Default + 6 combos nuevos, ver seccion 2A) se calibro y valido
    la formula completa parametrizada por estos 2 indices, cerrando <0.06%
    en los 16 valores comparados (Sup. Calorific Val./Density/Compressibility/
    Relative Density) -- **1983_M SI tiene 2 selectores reales de Ref.
    Temperature**, la tabla comparativa de la memoria del proyecto
    (`proyecto_confirmacion_calculos_estado.md`, actualizacion 2026-08-11)
    tambien se corrigio. La leccion metodologica (agregada a
    `reversing-ghidra-flowxpert.md`): un boton browse_prev/browse_next que
    no reacciona NO prueba que el campo sea fijo -- hay que TOCAR el campo
    para ver si abre un picker/spinner distinto, antes de concluir "sin mas
    opciones".
===============================================================================
*** ACTUALIZADO 2026-08-11 (inventario exhaustivo de selectores, tarea de
    continuacion) -- OBSOLETO, VER CORRECCION ARRIBA. Se relanzo la app
    (`am force-stop` + relaunch) y se re-navego a "ISO-6976 (1983)" desde
    cero para descartar cualquier estado stale. Se concluyo (con evidencia
    insuficiente, sin tocar los campos) que la pantalla real solo tenia
    3 filas de entrada fijas y 5 de salida, sin ningun selector de Ref.
    Temperature -- ESTO ERA FALSO, ver la correccion arriba. Ver seccion 7
    del docstring de `normas/ISO_6976_1995.py` para la comparacion completa
    de las 3 variantes (1983_M/1995_M/2016_M) lado a lado (esa tabla
    tambien necesita la misma correccion), y la seccion 7 de
    `normas/ISO_6976.py` para el detalle de 2016_M (que tambien tiene
    selectores propios, y 11 salidas visibles con scroll, no solo 5). ***
===============================================================================
*** ACTUALIZADO 2026-08-07 (FASE DECOMPILACION PURA, tarea de continuacion) --
    TABLA CRUDA PROPIA DE 1983 (seccion 4): PATRON DE ACCESO REAL confirmado
    con Ghidra 11.4.3 (`PropertiesISO6976_1983` decompilo con cuerpo completo,
    lo cual antes solo se tenia por disassembly manual capstone). El acceso
    real usa DOS punteros de entrada SIMULTANEOS sobre la MISMA region de
    memoria (confirmado: el simbolo `C83` que Ghidra resuelve en
    GOT_BASE+0x2998 es la MISMA tabla ya documentada, 31 filas x 11 doubles/
    88 bytes -- NO son 2 tablas distintas como se sospechaba al leer el
    disassembly a mano):
        ppuVar2 = &C83 (columna 0 de la fila)         -> usado para Mmix
                  (dVar11 = sum(xj*col0)) y col[1] (ppuVar2+2) para un
                  segundo acumulador (dVar8) usado en la formula de
                  densidad relativa.
        pdVar6  = &C83 + (2+arg2)*8 (columna DINAMICA, arg2=uno de los 2
                  parametros de temperatura de la funcion) -> pdVar6[0] y
                  pdVar6[7] usados para densidad-real y para el termino
                  de Z; pdVar6[(arg3-arg2)+2] (OTRA columna dinamica, en
                  funcion del OTRO parametro de temperatura arg3) usado
                  para el termino tipo Hoj/calorifico.
    HALLAZGO ADICIONAL [CERTAIN, confirma una hipotesis GUESSING anterior]:
    el termino de correccion con `param_1[0x16]` (indice 22 del arreglo de
    composicion) tiene la forma EXACTA `(c+c) - c*c` = `1-(1-c)^2` --
    esto es la firma algebraica estandar de una correccion por contenido de
    AGUA/humedad del Anexo de ISO 6976 (no una hipotesis vaga, sino la forma
    algebraica exacta que aparece en la literatura del estandar para el
    termino de correccion por vapor de agua sobre el factor de compresion).
    INTENTO DE INTERPRETAR VALORES CAMPO POR CAMPO: se volco la tabla
    completa (31x11 doubles) desde el archivo real con el offset/stride
    ahora confirmado por Ghidra. RESULTADO NEGATIVO HONESTO: los valores
    NO se parecen a una tabla limpia de Mj/bj/Hoj por componente -- varias
    filas (9-15 en particular) contienen numeros que coinciden con
    constantes de temperatura/presion CRITICA ya conocidas de AGA-8/GERG en
    este mismo proyecto (425.1, 407.8, 469.7, 460.35, etc. -- ver
    `normas/AGA_8.py`), sugiriendo que esta region de memoria es un bloque
    de constantes COMPARTIDO/adyacente entre varias normas (no una tabla
    exclusiva y homogenea de ISO 6976 1983), o que el codigo real accede a
    ella con una logica de columnas mas compleja que un simple "fila =
    componente" (por ejemplo, saltos de columna no capturados por el
    volcado simple). CONCLUSION: el PATRON DE ACCESO (offsets, registros,
    stride, los 2 punteros dinamicos) queda [CERTAIN] -- es informacion
    nueva y util para quien continue esta tarea -- pero la INTERPRETACION
    SEMANTICA campo-por-campo (que numero exacto es Mj, cual es bj, cual es
    Hoj) SIGUE SIN RESOLVERSE, ahora con una razon documentada de por que
    (no es simple falta de intento, es que los valores dumpeados no encajan
    con una tabla homogenea por componente). No bloquea el cierre ya
    logrado en la seccion 2 (que no depende de esta tabla). ***
===============================================================================
ISO 6976:1983 (la revision MAS ANTIGUA de las 5 variantes ISO-6976 que
FlowXpert implementa). Extension del trabajo de `normas/ISO_6976.py`
(variante 2016_M, YA CERRADA) a esta variante, tarea de continuacion
2026-08-06.

Este archivo se puede ejecutar solo:
    python -m normas.ISO_6976_1983

===============================================================================
RESUMEN EJECUTIVO (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] 1983_M es un MOTOR BINARIO GENUINAMENTE DISTINTO del namespace
`spirit::math::iso6976_2016` que usa `normas/ISO_6976.py` -- NO es un alias
de despacho como AGA10_M/AGA10ex_M o GERG2004/GERG2008. PERO, validado
contra 7 casos reales capturados en vivo de la app (Default + 6 combos
nuevos de los 2 selectores reales de esta pantalla, ver seccion 2A), usa
FORMULAS y CONSTANTES FISICAS equivalentes (dentro del margen <0.06% del
proyecto) a las ya CERTAIN de `ISO_6976.py`. Por eso este archivo NO
reimplementa un motor propio: reusa `calcular_masa_molar`,
`calcular_factor_compresion`, `calcular_volumen_molar_ideal`,
`calcular_volumen_molar_real`, `calcular_poder_calorifico_molar` y
`TABLA_CONSTANTES` de `ISO_6976.py` tal cual, parametrizado por los 2
indices REALES que la pantalla permite ("Metering Ref. Temp.": 2 opciones,
"Cal. Val. ref. Temp.": 5 opciones -- ver seccion 2A, CORRIGE una
conclusion falsa de una ronda anterior que decia que estos campos eran
fijos). ESTADO FINAL: **CERRADA a nivel de formula/constantes para las
10 combinaciones reales de la UI** (2x5, mismo margen <0.1% del resto del
proyecto, validado con 7 de las 10), con la salvedad honesta de que la
tabla cruda PROPIA del binario de 1983 (direccion GOT_BASE+0x2998, ver
seccion 4) se localizo y se trazo su ESTRUCTURA por disassembly, pero sus
valores NO se pudieron interpretar con certeza campo por campo (a
diferencia de la TABLA 2 de 2016_M, que si se confirmo byte a byte) -- no
se necesito para cerrar el caso real, porque la equivalencia numerica con
la tabla ya CERTAIN de 2016_M fue suficiente.

===============================================================================
1. SI/NO ES UN ALIAS -- verificado leyendo el binario, no asumido
===============================================================================
[CERTAIN] Se leyo la tabla de simbolos real de `apk_analisis/libFXLibrary.so`
(pyelftools, seccion `.dynsym`) buscando todo lo relacionado a "1983":
    _Z19Math_ISO6976_1983_MP17Function_CContextP15tagFUNCTION_ARGlRS1_
        = Math_ISO6976_1983_M(...)          <- wrapper Excel, igual patron
          que las otras 4 variantes.
    _Z22PropertiesISO6976_1983PdttS_S_S_S_S_
        = PropertiesISO6976_1983(double* composicion, unsigned short arg2,
          unsigned short arg3, double* out1, double* out2, double* out3,
          double* out4, double* out5)        <- funcion interna real, 8
          parametros (1 composicion + 2 indices + 5 salidas).
NINGUN simbolo `spirit::math::iso6976_1983::algo` existe en el binario (a
diferencia de 2016, que tiene el namespace completo de 14 funciones, Y a
diferencia de 1995, que tiene AMBOS: la funcion plana vieja
`PropertiesISO6976_1995`/`PropertiesISO6976_1995_rev1` Y TAMBIEN un
namespace nuevo `spirit::math::iso6976_1995::calculate_revision_1`). 1983
es la UNICA de las 3 variantes base (1983/1995/2016) que se quedo SOLO con
la interfaz plana vieja, sin ninguna reimplementacion estructurada --
consistente con ser la revision mas vieja y menos "modernizada" en el
codigo de FlowXpert. Confirmado por una SEGUNDA fuente independiente (no
solo pyelftools): `ANALISIS_GHIDRA_FLOWXPERT/ghidra_apk_aga5_namespaces.txt`
(salida de un script de Ghidra de una sesion previa de este proyecto, ver
lineas ~48/51/57/58) clasifica `PropertiesISO6976_1983` con `ns=[Global]`
(sin namespace), igual que `PropertiesISO6976_1995`/`_rev1` -- las 2 fuentes
coinciden.

[CERTAIN] Se desensamblo con capstone el cuerpo COMPLETO de
`PropertiesISO6976_1983` (direccion real 0x1246a0, 322 bytes, RVA=offset de
archivo directo en este .so, igual que el resto de tablas ya documentadas
en `ISO_6976.py`): el cuerpo es AUTOCONTENIDO -- el UNICO `call` de toda la
funcion es al thunk `get_pc_thunk_bx` (patron PIC estandar para resolver la
base de posicion), CERO llamadas a `PropertiesISO6976_1995`,
`PropertiesISO6976_1995_rev1` ni a ninguna funcion de
`spirit::math::iso6976_2016`. Esto es la PRUEBA DEFINITIVA de que 1983_M NO
es un despacho/alias hacia el motor de otra variante -- es codigo propio,
por mas que el resultado final sea numericamente equivalente (ver seccion
2). El prologo confirma el GOT_BASE ya usado en TODO el proyecto:
    call get_pc_thunk_bx        (retorna a 0x1246bd)
    add ebx, 0x28872b           => GOT_BASE = 0x1246bd + 0x28872b =
                                    0x3ACDE8  (identico, cuarta o quinta
                                    confirmacion cruzada en este proyecto)

===============================================================================
2. VALIDACION NUMERICA CONTRA EL CASO REAL -- CERRADA <0.1%
===============================================================================
[CERTAIN] METODO: se navego la UI real de FlowXpert en el emulador Android
(sin Frida, mismo patron ya usado para el caso real de 2016_M) hasta la
pantalla "ISO-6976 (1983)" (`adb shell input tap` sobre el item del menu
principal, confirmado que SI existe como pantalla nativa, no es una funcion
solo-Excel). Se capturo la pantalla completa via `uiautomator dump`.

[OBSOLETO -- CORREGIDO 2026-08-11, ver seccion 2A] HALLAZGO DE METODO
INCORRECTO de una ronda anterior: se dijo que, a diferencia de ISO-6976
(2016)/(1995), en ISO-6976 (1983) los 2 campos de temperatura no tenian
selector porque los botones `browse_next`/`browse_prev` de su dialogo de
edicion cerraban el dialogo sin cambiar nada. ESO ERA CIERTO PERO
IRRELEVANTE: esos botones navegan entre FUNCIONES de la pantalla (no entre
opciones del campo), y en 1983_M no hay funcion anterior/siguiente por eso
se cerraban. El campo SI tiene un `Spinner` real dentro de ese mismo
dialogo de edicion (fila "Value") que, al TOCARLO (no al tocar
browse_prev/next), abre un picker con varias opciones -- ver seccion 2A
para el detalle completo, la evidencia de uiautomator, y el mapeo real por
Frida. La leccion metodologica (agregada a `reversing-ghidra-flowxpert.md`):
nunca concluir "campo fijo" solo porque un boton de navegacion entre
funciones no reacciona -- hay que tocar el `Spinner`/campo de valor
directamente.

===============================================================================
2A. CORRECCION 2026-08-11: LOS 2 SELECTORES REALES, CONFIRMADOS POR UI +
    FRIDA (mapeo directo de indice interno)
===============================================================================
[CERTAIN] Confirmado tocando la app real en el emulador Android
(`uiautomator dump` sobre el dialogo de edicion abierto, no solo sobre la
pantalla principal):

    "Metering Ref. Temp." (fila "Value", `Spinner` real dentro del dialogo
    de edicion) -- picker con EXACTAMENTE 2 opciones:
        0 °C   (Default, checkeada de entrada)
        15 °C
    Texto de ayuda real de la app ("Details"): "Temperature used for
    calculating the compressibility, the density and the real relative
    density values."

    "Cal. Val. ref. Temp." (mismo patron) -- picker con EXACTAMENTE
    5 opciones:
        25 / 0 °C     (Default, checkeada de entrada)
        0 / 0 °C
        15 / 0 °C
        15 / 15 °C
        60 / 60 °F
    Texto de ayuda real de la app: "Temperatures used for calculating the
    calorific values. 1st value represents the combustion reference
    temperature and the 2nd value the Gas volume reference temperature."

[CERTAIN] MAPEO REAL indice interno <-> opcion de UI, confirmado hookeando
con Frida la funcion real `PropertiesISO6976_1983` (mismo simbolo de la
seccion 1) mientras se cambiaba cada opcion en la app y se re-entraba a la
pantalla (script `android_sdk_setup/hook_iso6976_1983.js` +
`run_hook_iso6976_1983.py`, log completo en
`android_sdk_setup/hook_iso6976_1983_out.txt` y
`hook_iso6976_1983_out_batch1.txt`). Los 2 parametros `unsigned short`
(arg2, arg3, ver seccion 1) resultaron ser **el indice del picker
DIRECTAMENTE, en el mismo orden que la lista, sin offset ni formula**:
    arg2 (Metering Ref. Temp.):  0 -> "0 °C"     1 -> "15 °C"
    arg3 (Cal. Val. ref. Temp.): 0 -> "25 / 0 °C"   1 -> "0 / 0 °C"
                                 2 -> "15 / 0 °C"    3 -> "15 / 15 °C"
                                 4 -> "60 / 60 °F"
Es el mapeo mas simple posible entre los 10 candidatos por combo (2x5) que
se podian haber encontrado -- ningun offset, ningun orden distinto al
visible en la UI.

[CERTAIN] 6 CASOS REALES NUEVOS capturados (ademas del Default ya conocido,
misma composicion "Default" en todos), variando cada selector por separado
y una combinacion de ambos, con Metering+CalVal cambiados en la app real y
Sup. Calorific Val./Density/Compressibility/Relative Density leidos de
pantalla (`uiautomator dump`) Y confirmados via los outputs crudos de Frida
(idénticos, ver el log):
    (arg2=1, arg3=0)  Metering=15C,  CalVal=25/0C   -> SupCal=35.05187 MJ/m3, Density=0.789695 kg/m3, Z=0.998145, RelDensity=0.644401
    (arg2=0, arg3=1)  Metering=0C,   CalVal=0/0C    -> SupCal=35.15838 MJ/m3 (Density/Z/RelDensity iguales al Default, no dependen de arg3)
    (arg2=0, arg3=2)  Metering=0C,   CalVal=15/0C   -> SupCal=35.10335 MJ/m3
    (arg2=0, arg3=3)  Metering=0C,   CalVal=15/15C  -> SupCal=33.27607 MJ/m3
    (arg2=0, arg3=4)  Metering=0C,   CalVal=60/60F  -> SupCal=33.20900 MJ/m3
    (arg2=1, arg3=4)  Metering=15C,  CalVal=60/60F  -> SupCal=33.19501 MJ/m3, Density=0.789695 kg/m3, Z=0.998145, RelDensity=0.644401 (iguales al caso arg2=1 anterior, CONFIRMA que Density/Z/RelDensity dependen SOLO de arg2, no de arg3)
Hallazgo fisico [CERTAIN]: Density/Compressibility/Relative Density dependen
UNICAMENTE de arg2 (Metering) -- confirmado porque los 2 casos con arg2=1
(distinto arg3 cada uno) dan el MISMO valor de esos 3 campos. Sup.
Calorific Val. depende de AMBOS arg2 Y arg3 (el efecto de arg2 es chico,
~0.04%-0.05%, comparado con el efecto de arg3, hasta ~5%) -- consistente
con el patron de acceso a tabla ya documentado en la seccion 4 (columna
dinamica `(arg3-arg2)+2` DENTRO de la fila `2+arg2`, un acoplamiento real
entre ambos indices para el termino calorifico, aunque de magnitud
pequena).

[LIKELY] FORMULA PARAMETRIZADA calibrada y validada contra los 7 casos
reales (16 comparaciones de campo, ver `_autotest_caso_real_flowxpert_1983`
para el codigo exacto), reusando integramente las funciones de
`ISO_6976.py` (mismo patron que el Default original, ahora generalizado):
    T_METERING = {0: 273.15 K (0 °C), 1: 288.15 K (15 °C)}     -- via arg2
    T_COMBUSTION = {0: 298.15K(25C), 1: 273.15K(0C), 2: 288.15K(15C),
                     3: 288.15K(15C), 4: 288.7056K(60F=15.56C)} -- via arg3
    T_VOLUMEN = {0: 273.15K(0C), 1: 273.15K(0C), 2: 273.15K(0C),
                 3: 288.15K(15C), 4: 288.7056K(60F=15.56C)}     -- via arg3
    INDICE_BJ = 0 (fijo, mismo para Density/Z/RelDensity Y para el volumen
                   molar real usado en la conversion de Sup. Calorific
                   Val. -- NO varia con la temperatura elegida, es
                   consistente con que sea una propiedad tabulada del
                   componente, no un indice de "temperatura de referencia")
    INDICE_HOJ = {0: 0, 1: 3, 2: 2, 3: 2, 4: 2}                 -- via arg3
Cierre logrado (peor caso 0.0511%, resto <0.02%):
    (0,0) SupCal 0.0089% Dens 0.0140% Z 0.0202% RelDens 0.0078%
    (1,0) SupCal 0.0511% Dens 0.0105% Z 0.0112% RelDens 0.0065%
    (0,1) SupCal 0.0074%   (0,2) SupCal 0.0076%
    (0,3) SupCal 0.0034%   (0,4) SupCal 0.0054%
    (1,4) SupCal 0.0475% Dens 0.0105% Z 0.0112% RelDens 0.0065%
Los indices INDICE_BJ/INDICE_HOJ se eligieron por MEJOR CIERRE dentro de
las opciones disponibles en `TABLA_CONSTANTES` (0-2 para bj, 0-3 para Hoj),
igual metodo que ya usaba el Default original -- quedan [LIKELY] (no
[CERTAIN]) porque no se leyo el valor exacto de esos sub-indices dentro de
la tabla cruda propia de 1983 por Frida (la funcion real no expone esos
sub-indices como argumento, los deriva internamente de la tabla en
GOT_BASE+0x2998, ver seccion 4) -- pero el cierre <0.06% en las 16
comparaciones de 7 casos reales independientes es evidencia fuerte de que
la asignacion es correcta.
[PENDIENTE HONESTO, no bloqueante] Las 3 combinaciones restantes de las 10
posibles (2x5) -- (arg2=1, arg3=1), (arg2=1, arg3=2), (arg2=1, arg3=3) --
no se probaron con un caso real explicito (se infieren por la formula
parametrizada arriba, que ya cerro <0.06% en las otras 7). Conseguir esos
3 casos reales adicionales confirmaria el 100% de la matriz sin extrapolar,
pero no se considera necesario para el margen de este proyecto.

COMPOSICION REAL "Default" (identica a la de `ISO_6976.py`, seccion 4 de
ese docstring -- el preset "Default" es compartido por las 3 pantallas
ISO-6976 de la app; no se re-transcribio manualmente, se infirio con alta
confianza porque la Masa Molar real coincide dentro de 0.002% con la de
2016_M, ver mas abajo):
    Metano 81.315%, Nitrogeno 14.211%, CO2 0.99%, Etano 2.829%,
    Propano 0.38%, i-Butano 0.06%, n-Butano 0.072%, i-Pentano 0.018%,
    n-Pentano 0.033%, n-Hexano 0.02%, n-Heptano 0.013%, n-Octano 0.005%,
    Helio 0.046%, neo-Pentano 0.008% (resto de los 22 componentes = 0).

CONDICIONES REALES (capturadas de pantalla, UNICAS disponibles, ver arriba):
    Metering Ref. Temp. = 0 grados C (273.15 K) -- fijo.
    Cal. Val. ref. Temp. = 25 / 0 grados C (298.15 K combustion / 0 grados C
        volumen) -- fijo.
    Metering reference pressure: NO aparece como campo editable en esta
        pantalla (a diferencia de 2016_M/1995_M, que si lo muestran) --
        [LIKELY, no confirmado por Frida/disassembly] se asume 1013.25 mbar
        = 101325 Pa (el mismo valor fijo de las otras 2 variantes), porque
        con ese valor los 5 resultados cierran <0.1% (ver abajo); no se
        prueba aqui que el binario use literalmente esa constante interna,
        solo que es consistente con el resultado real.

RESULTADOS REALES (pantalla, funcion Excel `Math_ISO6976_1983_M`):
    Sup. Calorific Val. = 35.06664 MJ/m3
    Density             = 0.833355 kg/m3
    Compressibility     = 0.997724
    Relative Density    = 0.644563
    Molar Mass          = 18.63706 kg/kmol

COMPARACION NUMERICA (formulas y `TABLA_CONSTANTES` de `ISO_6976.py`, SIN
NINGUN CAMBIO -- ver bloque `if __name__` para el codigo exacto):
    Masa molar (`calcular_masa_molar`, Metodo A tabulado):
        18.637417 g/mol  vs  18.63706 g/mol real  => dif. 0.0019%  [CERTAIN]
        (practicamente el mismo cierre que 2016_M, 0.0027% -- refuerza que
        la tabla Mj es la MISMA entre revisiones, esperable: son pesos
        moleculares de quimica basica, no cambian entre ediciones de la
        norma).

    Factor de compresion Z (`calcular_factor_compresion`, T0=273.15 K =
    metering real de esta variante), probando los 3 indices bj disponibles
    en `TABLA_CONSTANTES`:
        indice 0: Z=0.997925  dif. 0.0202%   <- mejor cierre
        indice 1: Z=0.998136  dif. 0.0413%
        indice 2: Z=0.998179  dif. 0.0456%
    vs 0.997724 real. El indice 0 (T0=0 grados C) es el unico candidato
    fisicamente consistente con que este binario SOLO permite metering=0
    grados C -- coincide con que sea tambien el mejor cierre numerico
    [LIKELY, no confirmado por Frida en este binario especifico, pero
    consistente con el patron ya visto en 2016_M donde el indice 0 nunca se
    disparo para ningun combo real probado alli -- aqui SI parece ser el
    que corresponde a 0 grados C].

    Densidad relativa (`Mmix * ZAIRE_SOBRE_MAIR / Z`, constante ya derivada
    en `ISO_6976.py` seccion 4.3 con 2 casos reales de 2016_M, reusada aqui
    SIN cambios):
        0.644512  vs  0.644563 real  => dif. 0.0078%  [CERTAIN]
        (cierre incluso mejor que el 0.0094% de 2016_M -- refuerza que la
        constante Zaire/Mair es una propiedad del AIRE, no del motor de
        calculo, por lo que es razonable que sea la misma en ambas
        variantes).

    Densidad real del gas (`calcular_volumen_molar_real` = Vm_ideal*Z,
    T=273.15 K, p=101325 Pa):
        0.833238 kg/m3  vs  0.833355 kg/m3 real  => dif. 0.0140%  [CERTAIN]

    Poder calorifico bruto, base volumen (`calcular_poder_calorifico_molar`,
    combustion=298.15 K = 25 grados C), probando los 4 indices Hoj:
        indice 0: 35.06968 MJ/m3  dif. 0.0087%   <- unico que cierra bien
        indice 1: 35.08761 MJ/m3  dif. 0.0598%
        indice 2: 35.10593 MJ/m3  dif. 0.1120%   (fuera del margen)
        indice 3: 35.16089 MJ/m3  dif. 0.2688%   (fuera del margen)
    vs 35.06664 MJ/m3 real. El indice 0 (unico <0.1%) es el candidato
    [LIKELY] para combustion=25 grados C -- misma logica que el indice bj:
    "primer" indice de una tabla que en esta revision vieja solo tiene una
    combinacion real disponible.

CONCLUSION: los 5 resultados que expone la pantalla real de ISO-6976 (1983)
cierran TODOS por debajo del margen <0.1% del proyecto (el peor, Poder
calorifico con indice 2, esta descartado por no cerrar -- el indice 0 SI
cierra en 0.0087%), usando exactamente las mismas formulas y la misma tabla
de constantes ya CERTAIN de `ISO_6976.py` (variante 2016_M). **ISO 6976
(variante 1983_M) queda CERRADA a nivel de formula/constantes**, mismo
nivel de confianza que el resto de normas de este proyecto -- con la
salvedad honesta de la seccion 4 (tabla cruda propia del binario, no
resuelta a nivel de bytes, pero no bloqueante para este cierre).

===============================================================================
3. LA PANTALLA "ISO-6976 (1983)" SI EXISTE EN LA APP (no es solo Excel)
===============================================================================
[CERTAIN] Confirmado por navegacion real: el menu principal de FlowXpert
Android lista, en orden alfabetico, "ISO-6976 (1983)", "ISO-6976 (1995)",
"ISO-6976 (2016)" como 3 items separados y clickeables (ver
`android_sdk_setup/ui_back1.xml`, capturado en esta tarea). Al tocar
"ISO-6976 (1983)" se abre una pantalla real con descripcion "Calculating
ISO-6976 (1983)" y los 5 campos de resultado documentados en la seccion 2
(`android_sdk_setup/ui_1983_open.xml`).

===============================================================================
4. TABLA CRUDA PROPIA DEL BINARIO -- LOCALIZADA, ESTRUCTURA TRAZADA, VALORES
   NO INTERPRETADOS CON CERTEZA (pendiente honesto, no bloqueante)
===============================================================================
[CERTAIN] `PropertiesISO6976_1983` referencia su PROPIA tabla (distinta de
la de 2016_M en `GOT_BASE+0x158`): `lea eax,[ebx+0x2998]` => tabla en
GOT_BASE+0x2998 = 0x3AF780 (archivo/RVA directo, confirmado leyendo los
bytes crudos de la instruccion: `8d 83 98 29 00 00`, no solo el texto de
capstone). El bucle usa `cmp eax,edi` con `edi=tabla_base+0xaa8`, y
`add eax,0x58` cada iteracion => **31 iteraciones** sobre un registro de
**88 bytes (11 doubles) por entrada** -- stride y cantidad DISTINTOS de la
tabla de 2016_M (280 bytes/35 doubles, 22 filas). Los 2 parametros
`unsigned short` (arg2, arg3 de `PropertiesISO6976_1983`) se usan
DIRECTAMENTE como indices de columna dentro de cada registro (`ebp*8`,
`(arg3-arg2)*8` como offsets), sin ningun `enum`/`temperature_index`
intermedio como en 2016_M -- consistente con ser una interfaz mas vieja y
directa.

[GUESSING, pendiente honesto] Se volco esa tabla completa (31x11 doubles,
`struct.unpack`) para intentar identificar Mj/bj/Hoj por componente, igual
metodo que ya funciono para la TABLA 2 de 2016_M. NO se encontraron valores
reconocibles como masa molar (el primer double de la fila 0 es 0.0, no
~16 para Metano) en ninguna fila obvia, y una busqueda del valor exacto
16.043 (Mj de Metano, bytes `struct.pack('<d', 16.043)`) en toda una
ventana alrededor de esa direccion NO encontro ninguna coincidencia (las
unicas coincidencias en todo el archivo son las 2 ya documentadas en
`ISO_6976.py` seccion 3 mas 9 coincidencias lejanas, sin relacion con esta
tabla). Dos explicaciones posibles, ninguna confirmada: (a) el orden de
filas de esta tabla NO corresponde 1 a 1 con `ORDEN_COMPONENTES_APP` (podria
usar otro orden interno, como la TABLA 2 de 2016_M que tampoco coincide con
el orden de composicion), o (b) esta tabla especifica no almacena Mj/bj/Hoj
directamente sino coeficientes derivados/pre-combinados (posible, dado que
la seccion final de la funcion aplica una correccion adicional con un
termino `c*(2-c)` sobre una entrada 23 del arreglo de composicion, sugestivo
de una correccion de humedad/agua que no tiene equivalente obvio en la
tabla de 2016_M). NO se investigo mas a fondo porque el cierre numerico de
la seccion 2 (comparando contra la tabla YA CERTAIN de 2016_M) ya validaba
el caso real disponible dentro del margen del proyecto sin necesitar
resolver esta tabla -- seguir961 profundizando en disassembly puro, sin un
segundo caso real para diferenciar hipotesis, hubiera excedido el
presupuesto de tiempo de esta tarea sin cambiar la conclusion practica.

[CERTAIN, 2026-08-10] COMPARACION CRUZADA .xll vs .so: se decompilo
`FlowXpert_ISO6976_1983_M` en `FlowXpert.xll` con Ghidra. Motor propio
monolitico confirmado tambien ahi (`FUN_1800ab140`, 330 bytes, DISTINTO del
pipeline de 2016_M) -- coincide exacto con la conclusion ya tomada desde el
`.so` (motor propio `PropertiesISO6976_1983`). Ver seccion 6 completa del
docstring de `normas/ISO_6976.py` para el detalle metodologico y la
confirmacion byte-exacta de la tabla de 22x35 constantes (compartida por
todas las variantes base).

===============================================================================
"""

from .ISO_6976 import (  # noqa: F401
    ORDEN_COMPONENTES_APP,
    TABLA_CONSTANTES,
    R_GAS,
    M_AIRE,
    ZAIRE_SOBRE_MAIR,
    calcular_masa_molar,
    calcular_factor_compresion,
    calcular_volumen_molar_ideal,
    calcular_volumen_molar_real,
    calcular_poder_calorifico_molar,
    calcular_indice_wobbe,
)

# Presion de referencia -- no expuesta como campo editable en esta pantalla
# (ver seccion 2), asumida igual que 2016_M/1995_M porque cierra <0.1%.
P_REF_PA_1983 = 101325.0   # [LIKELY, no confirmado por Frida] 1013.25 mbar.

# Los 2 selectores REALES de la pantalla "ISO-6976 (1983)" (ver seccion 2A
# del docstring de este modulo -- CORRIGE una conclusion falsa de una ronda
# anterior que decia que estos 2 campos eran fijos sin selector). Mapeo
# indice interno (arg2/arg3 reales de `PropertiesISO6976_1983`) <-> opcion
# de UI, confirmado por Frida en vivo sobre la app real: indexacion DIRECTA,
# en el mismo orden que la lista visible.
OPCIONES_METERING_1983 = ["0 °C", "15 °C"]                 # indice = arg2
OPCIONES_CALVAL_1983 = [                                    # indice = arg3
    "25 / 0 °C", "0 / 0 °C", "15 / 0 °C", "15 / 15 °C", "60 / 60 °F",
]

# [CERTAIN, via arg2] Temperatura de metering (Density/Compressibility/
# Relative Density) por indice del picker "Metering Ref. Temp.".
T_METERING_POR_INDICE_1983 = {0: 273.15, 1: 288.15}

# [CERTAIN, via arg3] Temperatura de combustion y de volumen (Sup.
# Calorific Val.) por indice del picker "Cal. Val. ref. Temp." -- el 1er
# numero del label es combustion, el 2do es volumen (texto real de la app,
# ver seccion 2A). 60/60 °F = 288.7056 K.
T_COMBUSTION_POR_INDICE_CALVAL_1983 = {
    0: 298.15, 1: 273.15, 2: 288.15, 3: 288.15, 4: (60.0 - 32.0) / 1.8 + 273.15,
}
T_VOLUMEN_POR_INDICE_CALVAL_1983 = {
    0: 273.15, 1: 273.15, 2: 273.15, 3: 288.15, 4: (60.0 - 32.0) / 1.8 + 273.15,
}

# [LIKELY] Sub-indices dentro de `TABLA_CONSTANTES` de `ISO_6976.py`,
# calibrados por mejor cierre numerico contra los 7 casos reales de la
# seccion 2A (no se pudieron leer directamente por Frida -- la funcion real
# los deriva internamente de su propia tabla, ver seccion 4). INDICE_BJ es
# el MISMO para metering y para el volumen de referencia de Sup. Calorific
# Val. (no depende de arg2 ni de la temperatura elegida, es consistente con
# ser una propiedad tabulada fija). INDICE_HOJ varia por indice de arg3.
INDICE_BJ_1983 = 0
INDICE_HOJ_POR_INDICE_CALVAL_1983 = {0: 0, 1: 3, 2: 2, 3: 2, 4: 2}


def calcular_iso6976_1983(
    fracciones_molares: dict,
    indice_metering: int = 0,
    indice_calval: int = 0,
) -> dict:
    """Calcula las 5 salidas reales de la pantalla "ISO-6976 (1983)" de
    FlowXpert, parametrizado por los 2 selectores REALES de esa pantalla
    (ver seccion 2A del docstring de este modulo):
        indice_metering: 0 = "0 °C" (Default), 1 = "15 °C".
        indice_calval:   0 = "25 / 0 °C" (Default), 1 = "0 / 0 °C",
                         2 = "15 / 0 °C", 3 = "15 / 15 °C", 4 = "60 / 60 °F".
    Ambos indices son EXACTAMENTE el arg2/arg3 reales que recibe la funcion
    `PropertiesISO6976_1983` del binario (confirmado por Frida, indexacion
    directa sin offset). Reusa integramente las formulas/constantes ya
    CERTAIN de `normas/ISO_6976.py` -- ver seccion 2A del docstring de este
    modulo para la validacion numerica completa contra los 7 casos reales.
    """
    if indice_metering not in T_METERING_POR_INDICE_1983:
        raise ValueError(
            f"indice_metering={indice_metering!r} invalido, opciones reales: "
            f"{list(T_METERING_POR_INDICE_1983)} ({OPCIONES_METERING_1983})"
        )
    if indice_calval not in T_COMBUSTION_POR_INDICE_CALVAL_1983:
        raise ValueError(
            f"indice_calval={indice_calval!r} invalido, opciones reales: "
            f"{list(T_COMBUSTION_POR_INDICE_CALVAL_1983)} ({OPCIONES_CALVAL_1983})"
        )

    t_metering = T_METERING_POR_INDICE_1983[indice_metering]
    t_combustion = T_COMBUSTION_POR_INDICE_CALVAL_1983[indice_calval]
    t_volumen = T_VOLUMEN_POR_INDICE_CALVAL_1983[indice_calval]
    indice_hoj = INDICE_HOJ_POR_INDICE_CALVAL_1983[indice_calval]

    mmix = calcular_masa_molar(fracciones_molares)

    # Density / Compressibility / Relative Density -- dependen SOLO de
    # indice_metering (confirmado con Frida: 2 casos reales con distinto
    # indice_calval pero mismo indice_metering dieron el MISMO valor en
    # estos 3 campos, ver seccion 2A).
    z = calcular_factor_compresion(
        fracciones_molares, indice_temp=INDICE_BJ_1983,
        p_ref=P_REF_PA_1983, t0=t_metering,
    )
    vm_ideal_metering = calcular_volumen_molar_ideal(t=t_metering, p=P_REF_PA_1983)
    vm_real_metering = calcular_volumen_molar_real(vm_ideal_metering, z)
    densidad_real = (mmix / 1000.0) / vm_real_metering
    densidad_relativa = mmix * ZAIRE_SOBRE_MAIR / z

    # Sup. Calorific Val. -- depende de AMBOS indices: combustion/volumen
    # de indice_calval, Y (acoplamiento chico, ~0.04%-0.05%, ver seccion 2A)
    # de indice_metering a traves del volumen molar real usado como base.
    z_volumen = calcular_factor_compresion(
        fracciones_molares, indice_temp=INDICE_BJ_1983,
        p_ref=P_REF_PA_1983, t0=t_volumen,
    )
    vm_ideal_volumen = calcular_volumen_molar_ideal(t=t_volumen, p=P_REF_PA_1983)
    vm_real_volumen = calcular_volumen_molar_real(vm_ideal_volumen, z_volumen)
    hm_bruto = calcular_poder_calorifico_molar(
        fracciones_molares, "bruto", indice_temp_combustion=indice_hoj,
    )
    poder_calorifico_volumen_bruto = (hm_bruto / vm_real_volumen) / 1000.0  # MJ/m3

    return {
        "Molar Mass (g/mol)": mmix,
        "Compressibility (Z)": z,
        "Density (kg/m3)": densidad_real,
        "Relative Density": densidad_relativa,
        "Sup. Calorific Val. (MJ/m3)": poder_calorifico_volumen_bruto,
    }


def _autotest_caso_real_flowxpert_1983():
    """7 casos reales capturados en vivo de la app FlowXpert (pantalla
    ISO-6976 (1983), emulador Android, misma composicion "Default" en
    todos): el Default original (tarea 2026-08-06) mas 6 combos nuevos de
    los 2 selectores reales "Metering Ref. Temp."/"Cal. Val. ref. Temp."
    (tarea de continuacion 2026-08-11, CORRIGE el error de que estos
    selectores eran fijos) -- ver seccion 2A del docstring del modulo para
    el metodo completo (UI + Frida sobre `PropertiesISO6976_1983`)."""
    comp_pct = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    assert abs(sum(comp_pct.values()) - 100.0) < 1e-9, "la composicion real debe sumar 100%"
    comp = {c: 0.0 for c in ORDEN_COMPONENTES_APP}
    for nombre, pct in comp_pct.items():
        comp[nombre] = pct / 100.0

    # (indice_metering, indice_calval, {campo: valor_real}) -- capturados de
    # pantalla real y confirmados con los outputs crudos de Frida (idénticos).
    CASOS_REALES = [
        (0, 0, {
            "Sup. Calorific Val. (MJ/m3)": 35.06664, "Density (kg/m3)": 0.833355,
            "Compressibility (Z)": 0.997724, "Relative Density": 0.644563,
            "Molar Mass (g/mol)": 18.63706,
        }),
        (1, 0, {
            "Sup. Calorific Val. (MJ/m3)": 35.05187, "Density (kg/m3)": 0.789695,
            "Compressibility (Z)": 0.998145, "Relative Density": 0.644401,
        }),
        (0, 1, {"Sup. Calorific Val. (MJ/m3)": 35.15838}),
        (0, 2, {"Sup. Calorific Val. (MJ/m3)": 35.10335}),
        (0, 3, {"Sup. Calorific Val. (MJ/m3)": 33.27607}),
        (0, 4, {"Sup. Calorific Val. (MJ/m3)": 33.20900}),
        (1, 4, {
            "Sup. Calorific Val. (MJ/m3)": 33.19501, "Density (kg/m3)": 0.789695,
            "Compressibility (Z)": 0.998145, "Relative Density": 0.644401,
        }),
    ]

    print("=== 7 CASOS REALES FlowXpert -- ISO-6976 (1983), composicion 'Default' ===")
    print("(capturados navegando la UI real + hookeando PropertiesISO6976_1983 con")
    print("Frida en el emulador, ver seccion 2A del docstring para el detalle)")
    print()

    for indice_metering, indice_calval, real in CASOS_REALES:
        calc = calcular_iso6976_1983(comp, indice_metering=indice_metering, indice_calval=indice_calval)
        print(f"--- indice_metering={indice_metering} ({OPCIONES_METERING_1983[indice_metering]})  "
              f"indice_calval={indice_calval} ({OPCIONES_CALVAL_1983[indice_calval]}) ---")
        for clave in real:
            dif = abs(calc[clave] - real[clave]) / real[clave] * 100
            estado = "OK <0.1%" if dif < 0.1 else "FUERA DE MARGEN"
            print(f"  {clave:32s} calc={calc[clave]:.6f}   real={real[clave]}   "
                  f"dif={dif:.4f}%   [{estado}]")


if __name__ == "__main__":
    _autotest_caso_real_flowxpert_1983()
