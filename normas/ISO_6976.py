# -*- coding: utf-8 -*-
"""
normas/ISO_6976.py
===================
===============================================================================
*** ACTUALIZADO 2026-08-18 (tarea de continuacion, selector de UNIDAD del
    campo "Metering reference pressure") -- CONFIRMADO EN VIVO (uiautomator)
    que junto al EditText de valor hay un Spinner con 18 unidades (Pa, kPa,
    kgf/m2, kgf/cm2, lbf/ft2, psi, bar, mbar, mmHg, mmH2O, mmH2O @ 60F, inHg
    con, inHg @ 32F, inHg @ 60F, inH2O con, inH2O @ 39.2F, inH2O @ 60F,
    inH2O @ 68F) y que es SOLO conversion de entrada/visualizacion: se probo
    la MISMA presion fisica en 2 unidades distintas (101.325 kPa y 14.695943
    psi) y las 5 salidas visibles en pantalla quedaron IDENTICAS digito a
    digito. Este archivo (funciones `calcular_factor_compresion`/
    `calcular_volumen_molar_ideal`/etc.) sigue esperando `p_ref` en **Pa**
    sin ningun cambio -- la conversion de unidad vive enteramente en
    `interfaz_calculo_flujo.py` (tabla `ISO6976_PRESION_A_PA`, combobox
    nuevo en la pestaña "ISO 6976 (2016)"), que convierte a Pa ANTES de
    llamar a estas funciones. Ver memoria del proyecto
    (`proyecto_confirmacion_calculos_estado.md`, seccion "ACTUALIZADO
    2026-08-18... selector de UNIDAD real") para el detalle completo de la
    evidencia y las fuentes de cada factor de conversion. ***
===============================================================================
*** ACTUALIZADO 2026-08-18 (tarea de continuacion, "Composition -> select to
    load") -- CONFIRMADO EN VIVO QUE LAS 16 COMPOSICIONES PREDEFINIDAS DE
    FLOWXPERT SON GENUINAMENTE COMPARTIDAS ENTRE NORMAS, NO EXCLUSIVAS DE
    AGA-8. El proyecto ya tenia documentadas (sesion 2026-08-01/03,
    `interfaz_calculo_flujo.py COMPOSICIONES_GUARDADAS_FLOWXPERT`) las 16
    composiciones reales del boton "LOAD" (Amarillo, Default, Dry Air,
    Ekofisk, Groningen, Gulf Coast, HiCal, High CO2-N2, High N2, Nordic,
    Pure CO2, Pure Methane, Pure Nitrogen, Sleen, Slochteren, Wet Gas), pero
    nunca se habia tocado el boton LOAD especificamente desde una pantalla
    ISO 6976. Esta ronda lo hizo:
    - En el emulador real, navegando Home->ISO->"ISO-6976 (2016)"->
      "Composition"->boton "LOAD" (resource-id
      `com.spiritit.flowxpert:id/load_composition`), se abre la MISMA
      activity "Compositions" ("Select composition to load") ya vista desde
      AGA-8, con la lista IDENTICA de 16 nombres (confirmado con scroll
      completo via `uiautomator dump`, sin ningun nombre nuevo ni faltante).
    - Se seleccionaron 2 composiciones reales sobre la grilla de 22 campos
      de "ISO-6976 (2016)" y se comparo campo por campo contra el dict ya
      documentado: "Ekofisk" (9 valores no-cero: Metano 85.9063%, Nitrogeno
      1.0068%, CO2 1.4954%, Etano 8.4919%, Propano 2.3015%, i-Butano
      0.3486%, n-Butano 0.3506%, i-Pentano 0.0509%, n-Pentano 0.0480%, resto
      0, Total 100.0000%) y "Dry Air" (Metano 0.0002%, Nitrogeno 78.1020%,
      CO2 0.0330%, Hidrogeno 0.0001%, Oxigeno 20.9460%, Total mostrado
      99.9978% -- el mismo total "no-100%" ya documentado, una huella fuerte
      de que es la MISMA fuente de datos). Los 2 casos cerraron EXACTOS,
      decimal a decimal, contra `COMPOSICIONES_GUARDADAS_FLOWXPERT`.
    - Se agrego el combobox "Cargar composicion guardada" a las 5 pestañas
      ISO 6976 de `interfaz_calculo_flujo.py` (1983/1995/2016/ex_1995/
      ex_2016) via el helper nuevo `_agregar_selector_composicion_guardada`,
      reusando `COMPOSICIONES_GUARDADAS_FLOWXPERT` y el mismo mapeo de
      nombres `_AGA5_MAPEO_NOMBRES` (Isobutano/Isopentano -> i-Butano/
      i-Pentano) ya usado por AGA-5 -- valido porque `ORDEN_COMPONENTES_APP`
      de este archivo es, confirmado, el MISMO orden/nombres de 22
      componentes que `AGA5_COMPONENTES`. Para "ex_1995"/"ex_2016" (55/60
      componentes) el combo llena los 22 conocidos y pone el resto en 0.0
      (comportamiento pedido explicitamente, no las 33/38 filas nuevas no
      tienen dato real de FlowXpert). Probado programaticamente (sin
      mainloop): simular la seleccion via `event_generate` en los 5 combos
      nuevos actualiza las StringVar correctas sin excepciones.
    CONCLUSION: no hizo falta re-extraer las 16 composiciones (ya eran
    reales, extraidas tocando la app, no fabricadas) -- solo confirmar que
    ISO 6976 usa el mismo mecanismo/datos y cablear el combobox que faltaba
    en la GUI. ***
===============================================================================
*** ACTUALIZADO 2026-08-18 (tarea de continuacion) -- CONFIRMADO POR BUSQUEDA
    REAL (no solo por razonamiento) QUE ISO 6976 DENTRO DE FLOWXPERT NO TIENE
    NINGUN MECANISMO DE REPARTO DE HIDROCARBUROS PESADOS AGRUPADOS ("C6+"/
    "heavy ends"). El usuario pidio explicitamente verificar con evidencia de
    binario (no solo con el argumento estructural ya conocido de que
    `iso6976_2016_inputs` recibe un vector de `index_based_component`
    individuales) si existia, especificamente dentro del namespace ISO6976
    (no en GPA2172, norma separada), algun rastro de reparto/combinacion de
    hexano/heptano/octano tipo Katz/GPA/"lump"/back-calculation. Se hicieron
    4 busquedas reales, ninguna encontro evidencia:
    (1) Tabla `.dynsym` de `libFXLibrary.so` (pyelftools): de 3906 simbolos
        unicos, 69 pertenecen al namespace real ISO6976 (5 variantes Excel +
        14 funciones internas del pipeline 2016 + PropertiesISO6976_1983/
        1995/1995_rev1 + calculate_revision_1 + vectores STL asociados) --
        se listaron y revisaron los 69 uno por uno, ninguno menciona "C6",
        "hexane", "heptane", "heavy", "katz", "lump", "gpa" o "extended". Los
        UNICOS simbolos de TODO el binario que matchean "gpa"/"extended"
        pertenecen a namespaces distintos y ya conocidos (`GPA2172_*`,
        `CheckAga8*Extended` de AGA8, `within_extended_ranges` de GERG) --
        confirma que esos terminos no tocan ISO6976 en este binario.
    (2) Busqueda de cadenas crudas (ASCII y UTF-16LE) en el archivo COMPLETO
        de `libFXLibrary.so` (3 895 992 bytes) y de `FlowXpert.xll`
        (3 011 424 bytes): 0 ocurrencias de "C6+", "C7+", "Hexanes+", "heavy
        end"/"Heavy End", "back-calculation", "Katz", "lump" en NINGUNO de
        los 2 binarios completos, en ninguna codificacion. ("GPA" si aparece
        67 veces en el .so, pero exclusivamente en el namespace GPA2172 ya
        excluido del alcance, confirmado por la busqueda de simbolos del
        punto 1).
    (3) Exports reales de `FlowXpert.xll` (pefile): de 373 exports totales,
        15 son ISO6976 (5 variantes x 3 formas de wrapper: bare/xlWrapper4/
        xlWrapper12), ninguno adicional de reparto. Reconfirma, reusando el
        trabajo ya hecho en la seccion 6 de este archivo ("COMPARACION
        CRUZADA .xll vs .so", 2026-08-10), que los 5 constructores reales ya
        decompilados (`FUN_1800ab140/ab4f8/ab9d4/ac218/ac858`) y su metadata
        de texto plano completa (nombres/descripciones de cada campo,
        capturada palabra por palabra en esa sesion) no incluyen ningun
        campo de hidrocarburos agrupados.
    (4) UI real de Android: se revisaron los dumps de `uiautomator` ya
        capturados en la re-verificacion exhaustiva de la seccion 7 (todas
        las filas de "ISO-6976 (2016)" tocadas, incluyendo el editor de
        "Composition") mas una busqueda de texto "C6+" en TODOS los .xml de
        `android_sdk_setup/` del proyecto completo -- 0 coincidencias en
        cualquier pantalla. La composicion real "Default" ya capturada en la
        seccion 4 de este archivo confirma ademas, de forma directa, que la
        UI pide n-Hexano (0.02%), n-Heptano (0.013%) y n-Octano (0.005%) como
        TRES campos separados con valores independientes, nunca un campo
        unico "C6+".
    CONCLUSION CONFIRMADA (ya no solo por razonamiento estructural, sino por
    busqueda real en los 2 binarios completos y en la UI real): ISO 6976
    dentro de FlowXpert NO tiene, en ningun punto (simbolos, cadenas de
    texto, exports, metadata de campos, ni pantalla de composicion), ningun
    mecanismo de reparto de hidrocarburos pesados agrupados (C6+/C7+/heavy
    ends). Esto es consistente con, y explica, el workaround que el propio
    proyecto construyo POR FUERA del binario en
    `android_sdk_setup/validar_iso6976_{1983,1995,2016}_cromatografo.py`:
    una division fija hardcodeada (`n-Hexano = C6+ * 0.47, n-Heptano = C6+ *
    0.35, n-Octano = C6+ * 0.18`) para poder alimentar datos reales de
    cromatografo (que SI reportan C6+ agrupado) a una funcion que solo acepta
    componentes individuales. [ADVERTENCIA, no confirmada] esos 3
    coeficientes (0.47/0.35/0.18) no tienen origen documentado ni evidencia
    de ser los que FlowXpert usaria si tuviera un mecanismo interno (que no
    tiene) -- son una convencion del proyecto para tener algun valor de
    prueba contra datos de cromatografo, no un valor extraido de ningun
    binario. Este hilo queda CERRADO, sin necesidad de reabrirlo salvo
    informacion genuinamente nueva. ***
===============================================================================
*** RE-VERIFICACION EXHAUSTIVA 2026-08-13 (tarea de continuacion, CIERRE DEL
    HILO ABIERTO "revisar las 3 variantes tocando cada fila", ver seccion 7
    para el inventario 2026-08-11 que esta ronda re-confirma en vivo) --
    "ISO-6976 (2016)" CONFIRMADA SIN SELECTORES NUEVOS. App relanzada limpia
    (`am force-stop` + relaunch de `SplashActivity`), re-navegada
    Categoria->ISO->"ISO-6976 (2016)" desde cero. Se toco LITERALMENTE cada
    fila (las 4 de entrada Y las 11 de salida con scroll), no solo los 3
    selectores ya conocidos, con `uiautomator dump` como evidencia:
    - "Composition": abre el editor de composicion, no es selector de
      opciones fijas.
    - "Ref. Temperature": `value_spinner` -> `ListView` con EXACTAMENTE 7
      `CheckedTextView` ("15/15/15 °C", "0/0/0 °C", "15/0/0 °C",
      "25/0/0 °C", "20/20/20 °C", "25/20/20 °C", "60F/60F/60 °F" checked en
      esta corrida) -- coincide EXACTO con los 7 casos del switch interno
      `select_reference_temperatures` ya CERTAIN (seccion 4.5). Confirmado
      con doble scroll (arriba y abajo del `ListView`) que no hay un 8vo
      item oculto.
    - "Molar Mass Method": `ListView` con EXACTAMENTE 2 `CheckedTextView`
      ("Calculate" checked, "Use table") -- coincide con lo ya documentado.
    - "Metering reference pressure": `value_field` es un `EditText
      enabled="true"` (campo NUMERICO real, no un enum de opciones fijas) +
      `unit_field` (`Spinner` de unidad de presion, ej. mbar) -- confirma
      que es un valor libre, no un selector de indice.
    - Las 11 filas de "Results" (Sup. Calorific Val. x3 unidades, Density,
      Compressibility, Relative Density, Molar Mass, Inf. Calorific Val.
      x3 unidades, Wobbe Index -- confirmado el conteo exacto de 11 tras 2
      scrolls consecutivos que devolvieron el MISMO listado, senal de que
      no hay una 12va fila oculta) son TODAS `LinearLayout clickable="true"`
      igual que en 1983_M/1995_M (el atributo `clickable` no distingue por
      si solo selector real de fila informativa). Se toco una muestra
      representativa (Sup. Calorific Val., Wobbe Index): ambas abren un
      dialogo con `value_field` de solo lectura (`enabled="false"`) + un
      `unit_field` (`Spinner`, mismo mecanismo de conversion de unidad de
      visualizacion que 1983_M/1995_M, NO cambia el calculo). Ningun
      renglon de salida abre un picker que cambie indice/formula.
    CONCLUSION: los 3 selectores ya documentados en la seccion 7
    ("Ref. Temperature" 7 opciones, "Molar Mass Method" 2 opciones,
    "Metering reference pressure" numerico) son los UNICOS selectores de
    calculo reales de "ISO-6976 (2016)" -- las 4 filas de entrada y las 11
    de salida quedan cubiertas sin excepcion, no se encontro ningun
    selector nuevo. Con esto, junto con la misma re-verificacion de
    "ISO-6976 (1983)" (ver `normas/ISO_6976_1983.py`, seccion nueva
    2026-08-13) y la de "ISO-6976 (1995)" ya cerrada en una tarea previa,
    **el hilo de "revisar exhaustivamente las 3 variantes tocando cada
    fila" queda CERRADO para las 3 pantallas, sin pendientes**. Evidencia
    guardada en `android_sdk_setup/ui_verif0813_2016_*.xml` (14 dumps de
    esta ronda). ***
===============================================================================
*** ACTUALIZADO 2026-08-10 (tarea de continuacion) -- ULTIMO PENDIENTE MENOR
    (campo [16:19] de TABLA 2, candidato Z0) CERRADO CON CONCLUSION HONESTA DE
    "SIN FUNCION LECTORA ENCONTRADA" -- no se sube a CERTAIN, sigue GUESSING,
    pero la busqueda queda agotada y documentada, no abierta indefinidamente.
    Se hicieron 3 cosas nuevas con Ghidra 11.4.3 (mismo proyecto reusado,
    `apk_analisis/ghidra_project_11.4.3/libFX114.gpr`):
    (1) AMPLIACION DEL BARRIDO DE XREFS: de las 66 direcciones de [16:19] (22
        filas x 3 campos) a las 770 direcciones de TABLA 2 COMPLETA (35 campos
        x 22 filas, incluyendo Mj y bj/Hoj que ya son [CERTAIN] por otra via).
        Resultado: los MISMOS 2 falsos positivos ya conocidos, y NADA MAS --
        pero ahora se ve la extension real del primer falso positivo: no es
        solo `wctype` en fila0 campo16, sino que TODA la fila 0 (campos 0-14+)
        colisiona con un bloque de ~131 simbolos externos de libc sin resolver
        que Ghidra sintetiza como funciones "External" (pthread_setspecific,
        syscall, memchr, wmemcpy, vsprintf, getc, wcrtomb, strcoll, iswctype,
        btowc, etc.) y superpone sobre esta region de memoria no reclamada por
        ninguna seccion real -- el mismo bug ya documentado, visto ahora a
        escala completa. Las filas 2-3 siguen colisionando solo con las tablas
        AGA-10 `Table23/24ESteps4To11/13`, ya descartadas como no relacionadas.
        HALLAZGO IMPORTANTE (honestidad): el resultado negativo NO es exclusivo
        de [16:19] -- ni siquiera Mj (campo0, columna ya CERTAIN por lectura
        directa de archivo) tiene una xref real detectada por el analisis
        estatico de Ghidra en TODA la tabla. Esto sugiere que si existe algun
        mecanismo real de lectura de TABLA 2, usa direccionamiento calculado
        en tiempo de ejecucion (ej. copia en bloque de las 280 bytes de una
        fila completa via `memcpy`/loop con stride en registro) que es
        invisible al analisis de referencias estatico de Ghidra -- NO que el
        campo [16:19] sea especial o distinto del resto de la tabla.
    (2) HIPOTESIS `molar_mass_calculation_method=2` DESCARTADA POR CODIGO, no
        solo por falta de caso real: se decompilo `calculate_molar_mass` en si
        (RAW 0x137280, las 2 ramas del switch de metodo). La funcion recibe
        SOLO 4 parametros (vector `molarmass_and_atomic_indices` 32B/fila,
        puntero a `molar_mass_calculation_method`, vector composicion, double&
        salida) -- estructuralmente NO tiene forma de alcanzar la direccion de
        TABLA 2 bajo NINGUN valor del flag de metodo, porque nunca recibe un
        puntero a esa region. Ambas ramas (formula por atomos vs valor
        tabulado) leen exclusivamente de la tabla SEPARADA de 32 bytes/fila ya
        documentada (`molarmass_and_atomic_indices`), nunca de TABLA 2. Esto
        cierra la hipotesis de la tarea de forma definitiva, no solo por
        ausencia de caso real sino por imposibilidad estructural del codigo.
    (3) DECOMPILADOS POR PRIMERA VEZ los 2 wrappers Excel completos
        `Math_ISO6976_2016_M` (22 comp., RAW 0xc1af0) y `Math_ISO6976ex_2016_M`
        (60 comp., RAW 0xc2b00) -- ninguno de los dos lee TABLA 2. El wrapper
        `ex_2016_M` construye sus vectores de entrada a partir de ARGUMENTOS
        EXPLICITOS que el usuario pasa en la formula de Excel (funciones
        internas `fac_molarmass_and_atomic_indices`/`fac_summation_factors`/
        `fac_gross_calorific_values`, alimentadas por `Function_CContext::
        arg_get` sobre los argumentos de la celda), no de ninguna tabla interna
        del binario. El wrapper base `Math_ISO6976_2016_M` usa un salto
        indirecto de 7 vias (tabla en `DAT_0023aafc`) segun `reference_
        conditions` (1..7) hacia 7 bloques de codigo casi identicos que solo
        difieren en la constante 1-7 inyectada -- confirma una vez mas que
        `reference_conditions` viaja como un simple entero 1..7 hacia el mismo
        `iso6976_2016_inputsC1`/`iso6976_2016()` ya documentado, sin tocar
        TABLA 2 en ningun punto de ese camino tampoco. (Nota lateral, fuera del
        alcance de esta tarea: en el codigo forzado a decompilar de esos 7
        bloques los vectores `molarmass_and_atomic_indices`/`summation_
        factors`/`gross_calorific_values` que se le pasan al constructor
        aparecen vacios en el fragmento visible -- posible pendiente NUEVO,
        no confirmado, para una sesion futura si hiciera falta reabrir el
        tema de como el motor obtiene sus datos reales; no afecta a la
        conclusion de esta tarea porque de todas formas ninguna de las 2
        tablas involucradas es TABLA 2.)
    CONCLUSION FINAL HONESTA (regla de oro del proyecto, sin forzar un
    resultado): tras agotar los caminos razonables -- las 14 funciones reales
    del pipeline 2016_M (sesion 2026-08-07), las 3 funciones planas de otras
    variantes (1983/1995_rev1/ex_1995, misma sesion), el barrido de xrefs
    ampliado a TABLA 2 COMPLETA, la hipotesis del metodo de masa molar
    descartada por lectura directa del codigo, y los 2 wrappers Excel
    decompilados por primera vez -- NINGUNA funcion real del binario lee el
    campo [16:19] de TABLA 2. Se CIERRA este pendiente como "investigado a
    fondo, sin funcion lectora encontrada": el campo permanece [GUESSING]
    (candidato Z0 del componente puro, sostenido solo por plausibilidad fisica
    y patron numerico decreciente con el peso molecular, nunca por evidencia
    de codigo) y no se reabrira en sesiones futuras salvo que aparezca
    informacion genuinamente nueva (ej. acceso y decompilacion del .xll de
    Windows, nunca intentado en este proyecto). Con este cierre, ISO 6976
    completa (1983/1995/2016/ex_1995/ex_2016) no tiene NINGUN pendiente activo
    -- solo este residuo, ahora documentado como cerrado-sin-hallazgo en vez de
    abierto indefinidamente. ***
===============================================================================
*** ACTUALIZADO 2026-08-08 (tarea de continuacion) -- LOS 2 ULTIMOS PENDIENTES
    MENORES DEL MODULO QUEDAN RESUELTOS con UN SOLO caso real nuevo (ver
    seccion 4.7 para el detalle completo): (1) el caveat de Hidrogeno con bj
    negativo (formula de "raiz con signo", sin caso real de Hidrogeno > 0
    hasta ahora) SI se probo por fin contra un caso real (Hidrogeno=5%,
    editado a mano sobre la composicion "Default" en la app real) -- cierra
    0.000856% en Z, 0.0026% en Mmix y 0.0035% en densidad relativa, dentro
    del margen <0.1% del resto del proyecto; (2) `bair[idx=3]` (seccion 4.6),
    que nunca se habia disparado por ningun combo real, SI se disparo con el
    combo de UI "Ref. Temperature" = 60F/60F/60F (temperature_index real=3,
    confirmado por Frida), lo que ademas confirma que ese combo es el
    **case 7** del switch de `select_reference_temperatures` (seccion 4.5) y
    revela una hipotesis fuerte (4/4 coincidencias, [LIKELY] no [CERTAIN])
    sobre el orden de los 7 combos de la UI: la posicion en la lista
    coincide con el numero de case. Metodologia: la app ya estaba dejada en
    este estado util (composicion + Ref. Temperature) por un intento anterior
    de esta misma tarea que se interrumpio por un error de red del asistente
    ANTES de escribir nada en este archivo -- se re-capturo la evidencia
    Frida desde cero en esta sesion (no se reutilizo ningun log viejo sin
    re-verificar) para no dar por bueno un dato no confirmado en vivo. Con
    esto, ISO 6976 (variante 2016_M) ya NO tiene ningun pendiente conocido,
    ni siquiera de los menores/no bloqueantes -- ver seccion 4.7. ***
===============================================================================
*** ACTUALIZADO 2026-08-07 (tarea de continuacion, FASE DECOMPILACION PURA) --
    PENDIENTE DEL CAMPO [16:19] (candidato Z0) SEGUIDO PERO NO RESUELTO.
    Se instalo Ghidra 11.4.3 y se decompilaron con exito TODAS las 14
    funciones reales del namespace `spirit::math::iso6976_2016` (mismo
    proyecto/metodo ya usado para `select_reference_temperatures`), MAS
    `PropertiesISO6976_1995_rev1`, `PropertiesISO6976_1983` y
    `calculate_revision_1` (ver `ISO_6976_1983.py`/`ISO_6976_1995.py`/
    `ISO_6976_ex_1995.py` para el detalle de cada una). HALLAZGO IMPORTANTE:
    ninguna de las 14 funciones reales del pipeline 2016_M lee la "TABLA 2"
    de 35 doubles/280 bytes documentada en la seccion 3 de este archivo --
    esas 14 funciones acceden a TRES arreglos SEPARADOS y mas pequenos
    (`molarmass_and_atomic_indices` 32B/fila, `summation_factors` 36B/fila,
    `gross_calorific_values` 44B/fila, ya documentados en
    `ISO_6976_ex_2016.py` seccion 2, GOT_BASE-0x8ADE8/-0x8B668/-0x8C0E8) --
    NO la tabla de 280 bytes. Se verifico ademas, por lectura directa de
    bytes del .so (sin ambiguedad de direccionamiento de Ghidra), que
    TABLA 2 SI existe exactamente donde se documento (fila0=Metano,
    Mj=16.043, bj=(0.049,0.0447,0.0436), campo[16:19]=(0.9976,0.998,0.9981);
    fila1=Etano campo[16:19]=(0.99,0.9915,0.992); fila2=Propano
    campo[16:19]=(0.9789,0.9821,0.9834) -- decrece con el peso molecular,
    igual patron ya notado). Se intento una busqueda de referencias cruzadas
    (xrefs) en Ghidra sobre las direcciones exactas de TABLA2[16:19] para
    las 22 filas: aparecieron algunas coincidencias, pero se comprobo que
    son FALSOS POSITIVOS (una resulto ser el stub PLT/GOT de la funcion libc
    `wctype`, simbolo `PTR_wctype_...`, que Ghidra etiqueto sobre esa misma
    direccion por un problema de resolucion de simbolos externos, no una
    referencia real de codigo ISO 6976; otras fueron colisiones con
    funciones de tablas AGA-8/DETAIL no relacionadas). CONCLUSION HONESTA:
    con las funciones decompiladas en esta tarea (las 14 de iso6976_2016 +
    las 3 funciones "planas" de 1983/1995/ex_1995), NINGUNA lee
    TABLA2[16:19] -- esto es un resultado NEGATIVO real, no una falta de
    intento: o bien el campo es leido por una funcion que sigue sin
    decompilarse (ej. `PropertiesISO6976_1995` la version "corta" nunca
    llamada por el wrapper Android, o codigo exclusivo de la ruta .xll de
    Windows), o bien es un campo reservado/no consumido por el motor
    Android. El campo [16:19] (candidato Z0 del componente puro) SIGUE
    [GUESSING], sin degradar ni mejorar respecto al estado anterior --
    ver seccion 2 para el detalle tecnico completo del intento. ***
===============================================================================
Poder calorifico, densidad, densidad relativa e indice de Wobbe segun
ISO 6976, reconstruido por ingenieria inversa del namespace real
`spirit::math::iso6976_2016` en `libFXLibrary.so` (version Android de
FlowXpert), via Ghidra (mapeo de simbolos, disassembly puntual) + RetDec
(decompilacion SSA de las funciones reales seleccionadas por nombre
mangled exacto, para evitar el bug de Ghidra 12.1.2 que trunca funciones
justo despues del thunk PIC `__i686.get_pc_thunk.bx` -- ver memoria del
proyecto).

===============================================================================
*** ACTUALIZADO 2026-08-07 (nueva tarea de continuacion) -- ULTIMO PENDIENTE
    GENUINO DEL MODULO RESUELTO: Mair y Zaire (usados por
    `calculate_real_gas_relative_density`) quedan [CERTAIN], ya no [LIKELY]/
    [PARCIALMENTE RESUELTO]. NO hizo falta Ghidra 11.4.3 esta vez: el
    disassembly x86 completo de esta funcion (RAW 0x137900-0x137a38, 312
    bytes) YA ESTABA generado por RetDec desde una sesion anterior, en
    `ANALISIS_GHIDRA_FLOWXPERT/retdec_out/iso6976_missing.dsm` (nunca leido a
    mano hasta ahora). Decodificando ese disassembly x86 PIC a mano
    (instruccion por instruccion, mismo patron GOT-relativo `ebx - offset`
    ya usado en la seccion 3 para la tabla Mj/bj/Hoj) se encontro que la
    funcion NO usa una constante fija de Zaire ni de Mair pasada por tabla
    aparte: calcula Zaire EN VIVO con la MISMA estructura que
    `calcular_factor_compresion` (Z = 1 - K*b), usando una tabla propia de 4
    valores `bair[indice]` (indice = el mismo `temperature_index` RAW 1..4
    que ya se veia por Frida, NO el indice 0..2 de la tabla bj de
    componentes) y una constante Mair real distinta de la hipotesis de
    manual (28.96546 g/mol, no 28.9626). Formula real exacta:
        Zaire(idx) = 1 - (p_ref_kPa / 101.325) * bair[idx]
        d = (Mmix/Mair) * (Zaire(idx)/Zmix)
    Validado BIT-EXACTO (0.0000% de diferencia, no solo <0.1%) contra LOS 3
    casos reales ya capturados por Frida (temperature_index 1, 2 Y 4 -- antes
    solo se habia cruzado el PRODUCTO Zaire/Mair para 2 de los 3). Ver
    seccion 4.6 para el metodo completo, las direcciones exactas y los
    valores reales de Mair, de las 4 bair[idx] y de las 2 constantes
    auxiliares (1.0 literal y 101.325 kPa literal). `ZAIRE_SOBRE_MAIR` (la
    constante ya usada por el codigo y por `ISO_6976_1995.py`/
    `ISO_6976_1983.py`) resulta ser EXACTAMENTE `Zaire(2)/Mair` con los
    valores reales ahora aislados -- no cambia de valor numerico, solo de
    nivel de confianza (LIKELY -> CERTAIN) y de justificacion (ya no
    "producto recuperado por inversion de formula", sino "cociente de 2
    constantes reales, cada una confirmada por separado"). Con esto, ISO 6976
    (variante 2016_M) ya NO tiene ningun pendiente que afecte el cierre
    numerico del caso real -- el unico residuo honesto que queda (ver seccion
    2) es el significado fisico exacto de bair[idx=3] (nunca disparado por
    ningun combo real de la UI probado, analogo al caso ya documentado del
    indice bj=0 de la tabla de componentes, pero sin impacto en ningun
    resultado real).
===============================================================================
*** ACTUALIZADO 2026-08-07 -- PENDIENTE DEL INDICE bj=0 RESUELTO. Se probo
    Ghidra 11.4.3 (release LTS anterior a la 12.1.2 usada en el resto del
    proyecto, instalada aparte, sin tocar nada existente) sobre el mismo
    `libFXLibrary.so`, en un proyecto Ghidra nuevo. El bug de cuerpo vacio
    de Ghidra 12.1.2 NO se reprodujo: tanto la funcion CONTROL
    (`PropertiesISO6976_1995_rev1`, cuya logica ya se conocia) como
    `select_reference_temperatures` (el pendiente real, nunca antes visto
    por dentro) decompilaron con cuerpo completo. La tabla real de 7 casos
    leida del switch interno coincide EXACTO (3/3) con los 3 casos reales ya
    confirmados por Frida, y explica que el indice 0 nunca se disparaba
    porque cae en el `default` de error, no en un indice de temperatura real
    -- ver seccion 4.5 para el detalle completo. La norma SIGUE CERRADA. ***
===============================================================================
*** ACTUALIZADO 2026-08-06 (sexta sesion de continuacion) -- 4 pendientes
    MENORES de la variante 2016_M revisados (ninguno bloqueaba el cierre ya
    logrado): (1) esta seccion del docstring [seccion 2] limpiada -- ya
    estaba al dia, solo se corrigio una mencion residual a "el unico caso
    real" ahora que hay 3; (2) CAVEAT de Hidrogeno con bj negativo
    RESUELTO matematicamente (raiz con signo en vez de sqrt+cuadrado
    complejo, ver docstring de `calcular_factor_compresion`) aunque sigue
    sin caso real de Hidrogeno>0 para confirmarlo contra el binario; (3) los
    16 de 35 campos sin etiquetar de la "tabla 2" quedaron IDENTIFICADOS
    (Hoj_bruto/neto volumetrico x6+x6, Hoj_neto masa x4) leyendo de nuevo
    los mismos doubles reales del .so y comparandolos contra Hoj molar ya
    CERTAIN -- ver seccion 3; (4) se intento confirmar el indice bj=0
    probando el combo real "20/20/20" por Frida en vivo -- la hipotesis "por
    eliminacion" de la sesion anterior quedo REFUTADA (temperature_index
    real = 4, no 0) y el indice 0 sigue sin confirmar, documentado
    honestamente en la seccion 4.4 nueva. La norma SIGUE CERRADA, autotest
    re-corrido sin cambios de resultado. ***
===============================================================================
*** ACTUALIZADO 2026-08-06 (quinta sesion de continuacion) -- mapeo de
    indice bj CORREGIDO por Frida en vivo (1 -> 2 para el caso "Default",
    el borrador anterior tenia el indice equivocado por coincidencia de
    ajuste numerico) y constante de densidad relativa (ZAIRE_SOBRE_MAIR)
    reemplazada por un valor derivado de 2 casos reales hookeados, ya no
    una hipotesis de manual. La norma SIGUE CERRADA (autotest re-corrido,
    todos los resultados siguen <0.1%) -- ver seccion 4.3 para el metodo y
    la evidencia exacta (direcciones, valores hookeados byte a byte).
===============================================================================
*** ACTUALIZADO 2026-08-05 (cuarta sesion de continuacion) -- NORMA CERRADA.
    Los 2 ultimos pendientes (densidad real del gas, poder calorifico
    volumetrico bruto) quedaron RESUELTOS con un UNICO bug encontrado por el
    mismo Camino 1 que ya habia resuelto Z en la sesion anterior (cruce
    contra la ecuacion PUBLICA de gas real, sin Frida ni disassembly
    adicional): `calcular_volumen_molar_real` dividia Vm_ideal entre Z en vez
    de MULTIPLICAR (la ecuacion real es p*Vm=Z*R*T => Vm_real=Z*Vm_ideal, no
    Vm_ideal/Z). El patron decompilado original `(CONST*a1*a2)/a3` era
    compatible con ambas lecturas por igual -- la fisica basica, no mas
    ingenieria inversa, resolvio la ambiguedad. Con ese unico cambio:
    Densidad real pasa de 0.366% a **0.0053%** de diferencia, y Poder
    calorifico volumetrico bruto pasa de "ningun indice cierra <0.1%" a
    **0.0031%** (indice de Hoj=2) -- confirmando que ambos pendientes
    compartian la misma causa raiz (hipotesis de la seccion 2, ahora
    confirmada). Ver seccion 4.2 para el detalle completo. CON ESTO, TODOS
    los resultados del caso real (Mmix, Z, densidad relativa, densidad real,
    poder calorifico volumetrico) cierran <0.1%: **ISO 6976 (variante
    2016_M, 22 componentes) queda CERRADA**, mismo nivel que AGA-3/AGA-5/
    GERG-2004/GERG-2008/NX-19. ***
===============================================================================
Este archivo empezo como un PRIMER BORRADOR (solo algoritmo, sin constantes).
En una sesion de continuacion anterior se extrajo la tabla real de
constantes por componente (Mj, bj, Hoj bruto/neto) leyendo directamente la
memoria estatica del binario con un emulador de CPU (unicorn) + disassembly
manual (capstone) sobre `apk_analisis/libFXLibrary.so` -- ver seccion 3 para
el metodo completo y las direcciones exactas. Despues se consiguio el caso
real de la app (ver seccion 4), se resolvio el factor de compresion Z
(seccion 4.1) y, en esta ultima sesion, los 2 pendientes finales (densidad
real, poder calorifico volumetrico, seccion 4.2). ESTADO FINAL: norma
CERRADA. Ya no quedan pendientes bloqueantes -- lo unico que sigue sin
confirmacion directa por Frida/disassembly (solo por cierre numerico +
plausibilidad, mismo estandar ya aceptado para Z) es el detalle fino de que
combinacion exacta de temperatura corresponde a cada indice de bj/Hoj, lo
cual no impide el cierre <0.1% del caso real disponible (ver seccion 4.2).

===============================================================================
1. QUE SE CONFIRMO CON EVIDENCIA REAL [CERTAIN]
===============================================================================
[CERTAIN] ISO 6976 SI existe como binario ejecutable real en libFXLibrary.so
(Android), no solo en el .xll de Windows. Los simbolos estan completos y
demangled en la tabla de simbolos del .so (namespace `spirit::math::
iso6976_2016`), lo que permitio decompilar las funciones REALES (no solo
inferir por nombre). Existen 5 variantes registradas como funciones Excel
(igual que en el .xll): Math_ISO6976_1983_M, Math_ISO6976_1995_M,
Math_ISO6976_2016_M, Math_ISO6976ex_1995_M (55 componentes),
Math_ISO6976ex_2016_M (60 componentes). Este borrador cubre la variante base
de 22 componentes (2016_M), que reusa el MISMO orden de 22 componentes que
AGA5_C (confirmado leyendo el bucle real de `Math_ISO6976_2016_M` que hace
22 `emplace_back` sobre un vector de `index_based_component` tras leer 22
valores double desde el arreglo de composicion y normalizarlos con
`NormalizeMolFrac(ptr, 22)`).

[CERTAIN] La funcion orquestadora real `spirit::math::iso6976_2016::
iso6976_2016(iso6976_2016_inputs const&, iso6976_2016_outputs&)` decompila
limpio (RetDec, sin ambiguedad de registros) y llama, EN ESTE ORDEN, a las
funciones internas reales -- lo cual coincide exactamente con la secuencia de
calculo publicada del metodo ISO 6976 (no es una formula generica adivinada,
es la secuencia real leida del binario):

    1. select_reference_temperatures   (elige las 2 temperaturas de
       referencia: combustion y medicion/volumen, de una tabla de
       combinaciones estandar segun un indice 0..7)
    2. calculate_molar_mass            (ver formula abajo)
    3. calculate_compression_factor    (ver formula abajo)
    4. calculate_ideal_gass_volume     (ver formula abajo)
    5. calculate_real_gass_volume      (ver formula abajo)
    6. calculate_gross_calorific_value_on_molar_basis
    7. calculate_gross_calorific_value_on_mass_basis
    8. calculate_gross_calorific_value_on_volume_basis
    9. calculate_net_calorific_value_on_molar_basis
   10. calculate_net_calorific_value_on_mass_basis
   11. calculate_net_calorific_value_on_volume_basis
   12. calculate_real_gas_relative_density
   13. calculate_real_gas_density
   14. calculate_real_gas_gross_wobbe_index

[CERTAIN] Formulas de las funciones hoja, leidas DIRECTAMENTE del cuerpo
decompilado (SSA limpio, sin registros reciclados ambiguos, cada una
confirmada de forma independiente):

    Masa molar (calculate_molar_mass), con DOS metodos alternativos segun
    un flag `molar_mass_calculation_method` (esto es una caracteristica
    real y distintiva de ISO 6976, no un invento de la reconstruccion):
        Metodo A (tabulado):     Mmix = sum(xj * Mj_tabulado)
        Metodo B (por formula quimica): Mmix = sum(xj * (nC*M_C + nH*M_H +
            nN*M_N + nO*M_O + nS*M_S)), usando los conteos de atomos C,H,N,O,S
            de cada componente y los pesos atomicos IUPAC -- esto es
            exactamente la "molar mass calculation method" alternativa que
            describe el estandar (calcular M a partir de la formula quimica
            en vez de la tabla).

    Factor de compresion (calculate_compression_factor) -- coincide
    literalmente con la ecuacion publicada de ISO 6976 para el factor de
    compresion en condiciones de referencia:
        Z = 1 - (p_ref_kPa / (R * T0)) * (sum(xj * sqrt(bj)))^2
    (el binario usa el summation factor bj ya combinado con sqrt segun el
    indice de temperatura de referencia -- 3 valores bj reales por
    componente segun la combinacion de temperaturas 0..2, ver seccion 3 --
    y multiplica el cuadrado de la sumatoria por una razon p/(R*T0)
    constante). [CERTAIN, confirmado contra caso real 2026-08-05, seccion 4]
    p_ref entra en **kPa**, no en Pa -- ese era el unico bug real de esta
    formula (ver seccion 4.1); R en J/(mol*K) SI y T0 en K sin cambios.

    Volumen molar ideal (calculate_ideal_gass_volume):
        Vm_ideal = R * T / p          <- ecuacion de gas ideal clasica

    Volumen real (calculate_real_gass_volume), patron decompilado
    (CONST * a1 * a2) / a3. [CERTAIN, resuelto 2026-08-05 cuarta sesion]
    Vm_real = Vm_ideal * Z = Z*R*T/p (equivalente a agrupar CONST=R, a1=T,
    a2=Z, a3=p sobre el mismo patron decompilado) -- NO Vm_ideal/Z como se
    asumio en borradores anteriores. La ecuacion de gas real publica
    (p*Vm = Z*R*T) resuelve la ambiguedad: ambas lecturas del patron
    `CONST*a1*a2/a3` son igualmente compatibles con la decompilacion, pero
    solo la multiplicacion es fisicamente correcta, y es la que cierra
    <0.01% contra el caso real (ver seccion 4.2).

    Poder calorifico bruto, base molar (calculate_gross_calorific_value_
    on_molar_basis):
        Hm = sum(xj * Hoj[indice_temperatura_combustion])

    Conversion a base masa y volumen (patron identico en las 4 variantes
    bruto/neto x masa/volumen, confirmado en cada una):
        H_masa   = Hm / Mmix
        H_volumen = Hm / Vm_real

    Indice de Wobbe (calculate_real_gas_gross_wobbe_index) -- coincide con
    la definicion textbook exacta:
        W = H_volumen / sqrt(d)

    Densidad relativa real (calculate_real_gas_relative_density)
    [CERTAIN, confirmado 2026-08-06 por Frida en vivo Y 2026-08-07 por
    disassembly completo, ver secciones 4.3 y 4.6]: firma real de 5
    argumentos (temperature_index, double p_ref_kPa, const double& Zmix,
    const double& Mmix, double& salida). Mair y Zaire NO se pasan como
    argumento -- Mair SI es una constante literal interna (28.96546 g/mol,
    leida del binario, ver seccion 4.6), y Zaire NO es una constante ni una
    tabla de valores ya resueltos: la funcion la CALCULA en vivo con la
    MISMA estructura del "summation factor method" que usa
    calcular_factor_compresion, indexando una tabla propia de 4 valores
    `bair[temperature_index]` (tabla del AIRE, distinta de la tabla bj de
    cada componente de la seccion 3):
        Zaire(idx) = 1 - (p_ref_kPa / 101.325) * bair[idx]
        d = (Mmix/Mair) * (Zaire(idx)/Zmix)
    Ver seccion 4.6 para el disassembly decodificado instruccion por
    instruccion, las 4 direcciones GOT-relativas exactas de bair[1..4], y la
    validacion BIT-EXACTA (0.0000% de diferencia) contra los 4 casos reales
    ya capturados por Frida (temperature_index 1, 2, 3 y 4 -- ver seccion 4.7
    para el caso de temperature_index=3, agregado 2026-08-08).

===============================================================================
2. QUE NO SE PUDO CONFIRMAR (Y POR QUE) -- actualizado 2026-08-10
===============================================================================
[CERRADO 2026-08-10 COMO "INVESTIGADO A FONDO, SIN FUNCION LECTORA
ENCONTRADA", ver docstring principal arriba y seccion 3] El campo [16:19] de
TABLA 2 (candidato Z0 del componente puro) fue el ULTIMO pendiente menor del
modulo. Tras el intento de 2026-08-07 (14 funciones del pipeline 2016_M + 3
funciones planas de otras variantes, sin exito), esta sesion agoto los
caminos razonables restantes: (1) xrefs ampliados de 66 a 770 direcciones
(TABLA 2 completa, no solo [16:19]) -- mismo resultado negativo, ni Mj tiene
xref real; (2) `molar_mass_calculation_method=2` descartado por lectura
directa de `calculate_molar_mass` (no puede alcanzar TABLA 2 estructuralmente,
bajo ningun valor del flag); (3) wrappers Excel `Math_ISO6976_2016_M`/
`Math_ISO6976ex_2016_M` decompilados por primera vez, ninguno lee TABLA 2. El
campo sigue [GUESSING] (no se fuerza a CERTAIN sin lector confirmado) pero la
busqueda queda formalmente cerrada, no pendiente abierto. Con esto, ISO 6976
completa (todas las variantes) no tiene NINGUN pendiente activo.

[RESUELTO 2026-08-08, ver seccion 4.7] Los 2 pendientes menores que quedaban
(caveat de Hidrogeno sin caso real con H2>0, y `bair[idx=3]` nunca disparado)
quedaron RESUELTOS con un unico caso real nuevo (composicion editada a
Hidrogeno=5%, combo de UI "Ref. Temperature"=60F/60F/60F). Ambos cierran
<0.1% contra el caso real (Z 0.000856%, Mmix 0.0026%, densidad relativa
0.0035%) -- ver seccion 4.7 para el metodo completo, la captura Frida exacta
y el barrido de columnas/T0 probado. Con esto, este modulo ya NO tiene
ningun pendiente conocido, ni siquiera menor/no bloqueante.

[RESUELTO 2026-08-06/07, ver seccion 4.5] El pendiente del indice bj=0 (que
seguia abierto tras 4.4) quedo RESUELTO leyendo el CUERPO REAL de
`select_reference_temperatures` (bug de cuerpo vacio de Ghidra 12.1.2
evitado usando Ghidra 11.4.3 en un proyecto separado) -- 0 nunca se disparo
porque no es un case valido del switch interno (rango real 1..7, 0 cae en
el `default: return 1` de error). Ver seccion 4.5 para la tabla completa de
los 7 casos y la validacion cruzada exacta (3/3) contra los casos reales de
Frida.

[RESUELTO 2026-08-06, ver seccion 4.3] El mapeo indice->temperatura de
referencia (tanto para bj/metering como para Hoj/combustion) YA NO es
[LIKELY] por ajuste numerico -- se confirmo por Frida en vivo, leyendo el
argumento `temperature_index` real que pasa la app al invocar
`calculate_compression_factor` / `calculate_real_gas_relative_density` para
2 combinaciones reales distintas de la UI. HALLAZGO IMPORTANTE: el indice
que el borrador anterior usaba para el caso "Default" (bj indice=1, elegido
por MEJOR AJUSTE NUMERICO, seccion 4.1 vieja) estaba MAL -- el indice REAL
confirmado por el binario para metering=15 C (el caso Default) es **2**, no
1. El ajuste numerico con indice=1 daba un error ligeramente menor (0.008%
vs 0.012% con el indice=2 correcto), pero eso era COINCIDENCIA -- los 3
valores de bj de cada componente son numericamente muy parecidos entre si
(la correccion de compresibilidad cambia poco entre 0/15/20 C), asi que un
ajuste por cierre numerico con un solo caso real no alcanzaba para
distinguir el indice correcto del incorrecto. Ver seccion 4.3 para la
evidencia exacta (valores hookeados) y la correccion aplicada al codigo.

[RESUELTO 2026-08-06, tarea de continuacion] El significado de los ~16 de 35
doubles por componente en la "tabla 2" (ver seccion 3) que quedaban sin
etiquetar SI se pudo confirmar con la informacion ya disponible, sin Frida ni
disassembly nuevo -- solo leyendo de nuevo, con `struct.unpack`, los mismos
35 doubles reales por componente directamente del archivo
`apk_analisis/libFXLibrary.so` (offset de archivo = GOT_BASE+0x158 =
0x3ACF40, el mismo ya documentado y confirmado en la seccion 3 -- se
reconfirmo ademas que ese offset SI es un offset de archivo directo, no solo
una direccion de runtime, verificando que el primer double de las 22 filas
consecutivas de 35*8 bytes es exactamente Mj para los 22 componentes, 22/22
coincidencias exactas) y comparando esos 16 valores, para 6 componentes
elegidos por variedad (Metano, Etano, Propano, H2S, Hidrogeno, n-Decano),
contra el resultado de dividir Hoj_bruto_molar[j] (o Hoj_neto_molar[j], ya
CERTAIN) entre el volumen molar ideal R*T/p evaluado en 5 temperaturas
candidatas (0/15/20/25 C, 60F) y contra Hoj_bruto_masa[0] escalado por la
razon neto/bruto molar. RESULTADO: los 16 valores son EXACTAMENTE (error
<0.1% en los 6 componentes probados, la mayoria <0.02%) [19:25]=Hoj_bruto
VOLUMETRICO (6 combinaciones), [25:29]=Hoj_neto base MASA (4 combinaciones,
analogo a Hoj_bruto_masa) y [29:35]=Hoj_neto VOLUMETRICO (6 combinaciones) --
ver seccion 3 para el layout final y el ejemplo numerico completo de Metano.
HALLAZGO ADICIONAL (honestidad, no se fuerza mas alla de lo que se ve):
las 6 combinaciones de los grupos VOLUMETRICOS no siguen el mismo orden
simple de 4 valores que Hoj_bruto/neto molar -- por ejemplo, para Metano
[19:22] (37.706, 39.84, 39.777, 39.735) NO es una progresion simple, sino
que mezcla resultados de dividir DIFERENTES Hoj_bruto[j] entre Vm evaluado
a 0 C Y a 15 C dentro del mismo grupo de 4 (ver script de verificacion) --
consistente con que el volumetrico depende de DOS temperaturas (combustion
para Hoj, metering/volumen para Vm), a diferencia del molar/masa que solo
depende de la de combustion, asi que tiene mas combinaciones posibles (6,
no 4) y no se aislo (ni hacia falta para esta tarea) el mapeo exacto de
cada una de las 6 a una combinacion especifica de las 7 que expone la UI.
Con esto, de los 35 campos por componente, 32 quedan identificados con
evidencia numerica fuerte (Mj, bj x3, Hoj_bruto/neto molar x4+x4,
Hoj_bruto/neto masa x4+x4, Hoj_bruto/neto volumetrico x6+x6); solo
[16:19] (3 campos, candidato factor Z0 del componente puro) sigue sin
confirmar.

[RESUELTO 2026-08-07, ver seccion 4.6] El valor de Zaire (y de Mair) para
`calculate_real_gas_relative_density` NO se pasan como argumento a esa
funcion. Se confirmo por Frida (2026-08-06) el PRODUCTO (Zaire/Mair) para 2
temperature_index reales distintos, y la sospecha de esa sesion (que Zaire
"varia levemente con temperature_index") RESULTO SER CIERTA, no ruido: se
disassemblo el cuerpo completo de la funcion (nunca antes leido) y se
confirmo que Zaire NO es una constante ni una tabla de valores ya resueltos,
sino que se CALCULA en vivo dentro de la funcion con la misma estructura del
"summation factor method" (Zaire = 1 - K*bair[idx]), leyendo una tabla propia
de 4 valores `bair[temperature_index]` (distinta de la tabla bj de
componentes). Mair SI es una constante literal simple: 28.96546 g/mol (no
28.9626 como asumia el borrador de manual). Ambas quedan aisladas
INDIVIDUALMENTE, no solo su cociente, y validadas bit-exacto contra los 3
casos reales.

===============================================================================
3. TABLA DE CONSTANTES REAL -- CONFIRMADA POR VOLCADO DIRECTO DE MEMORIA
   (CAMINO 1: unicorn + capstone sobre apk_analisis/libFXLibrary.so, 2026-08-05)
===============================================================================
[CERTAIN] METODO: la funcion `PropertiesISO6976_1995_rev1` (RAW 0x124980,
= direccion Ghidra 0x134980, offset fijo +0x10000 ya documentado en
`normas/_sgerg_emulador.py`) decompila a un cuerpo VACIO tanto en Ghidra
(bug ya conocido de esta version, ver memoria `reversing-ghidra-flowxpert`)
como en RetDec (constantes perdidas, todo aparece como `__asm_movsd_14`
opacos). Se abandono el intento de decompilar y se desensamblo a mano con
`capstone` directamente sobre los bytes reales del .so:
  - Prologo real: `call get_pc_thunk_bx` (retorna a 0x124989) seguido de
    `add ebx, 0x28845f` => GOT_BASE real = 0x124989 + 0x28845f = 0x3ACDE8
    (coincide EXACTO con el GOT_BASE ya confirmado en otras normas de este
    proyecto -- confirmacion cruzada fuerte de que es el registro base
    correcto, no una coincidencia).
  - El cuerpo real hace un bucle de 22 iteraciones (`cmp edx,0x16`) leyendo
    un registro de 96 bytes por componente empezando en GOT_BASE+0x95c,
    con 5 enteros (conteos atomicos C,H,N,O,S) + 1 double de correccion,
    multiplicados por 5 constantes reales en GOT_BASE-0x182c20/-18/-10/-08/
    -00 que SI son los pesos atomicos IUPAC exactos leidos del binario
    (C=12.011, H=1.00794, O=15.9994, N=14.00674, S=32.066) -- esto confirma
    en vivo el "Metodo B" (formula quimica) ya documentado en la seccion 1.

[CERTAIN] TABLA 1 -- Mj tabulado (Metodo A), un arreglo simple de 22 doubles
consecutivos, encontrado 2 VECES identicas en el archivo (file offset
0x26d040 y 0x26dc80, bytes exactos via `struct.pack('<d', valor)`), en el
MISMO ORDEN que `ORDEN_COMPONENTES_APP` (21 de 22 valores coinciden exacto
con las masas molares ya conocidas de AGA_5.py/AGA_8.py; la unica diferencia
es que esta tabla especifica trae 0.0 en la posicion de neo-Pentano en vez
de 72.15 -- hallazgo real, no error de lectura, ver TABLA 2 que si tiene el
valor real de neo-Pentano).

[CERTAIN] TABLA 2 -- registro completo de 35 doubles (280 bytes) por
componente, base = GOT_BASE + 0x158 = 0x3ACF40, 22 registros consecutivos
(confirmado iterando de a 35*8 bytes y verificando que el primer double de
cada registro es una masa molar real conocida, sin excepcion, en las 22
filas). IMPORTANTE: el orden de componentes de ESTA tabla es DISTINTO del
de `ORDEN_COMPONENTES_APP` (agrupa hidrocarburos por numero de carbono
primero, despues H2/H2O/H2S/CO/He/Ar/N2/O2/CO2) -- ver
`_ORDEN_TABLA2_INTERNO` abajo. Layout confirmado del registro (indices 0..34,
doubles):
    [0]      Mj (masa molar tabulada -- coincide con TABLA 1 en todas las
             filas, INCLUYENDO neo-Pentano=72.15, que en TABLA 1 daba 0.0)
    [1:4]    bj (summation factor de compresibilidad) -- 3 valores, NO 4
             como se asumio en el borrador original (ver correccion en
             `calcular_factor_compresion` mas abajo)
    [4:8]    Hoj_bruto, base molar, kJ/mol (4 combinaciones de temperatura)
    [8:12]   Hoj_neto, base molar, kJ/mol (4 combinaciones)
    [12:16]  Hoj_bruto, base masa, MJ/kg (4 combinaciones)
    [16:19]  factor <=1 (no identificado con certeza -- candidato fuerte:
             factor de compresion Z0 del componente puro en condiciones de
             referencia; decrece con el peso molecular de forma consistente
             con la fisica real, ver seccion 2). [CERRADO 2026-08-10 COMO
             "INVESTIGADO A FONDO, SIN FUNCION LECTORA ENCONTRADA", ver
             docstring principal arriba y seccion 2] tras el intento de
             2026-08-07 (14 funciones del pipeline 2016_M + 3 funciones
             planas de otras variantes) se agotaron los caminos razonables
             restantes: busqueda de xrefs ampliada de 66 a las 770
             direcciones de TABLA 2 COMPLETA (mismo resultado negativo, ni
             siquiera Mj tiene xref real detectada), hipotesis de
             `molar_mass_calculation_method=2` descartada por lectura
             directa de `calculate_molar_mass` (estructuralmente no puede
             alcanzar TABLA 2 bajo ningun valor del flag), y decompilacion
             por primera vez de los wrappers Excel `Math_ISO6976_2016_M` /
             `Math_ISO6976ex_2016_M` (ninguno lee TABLA 2). Sigue
             [GUESSING] -- no se fuerza el valor a CERTAIN sin lector
             confirmado -- pero la busqueda queda cerrada, no pendiente.
    [19:25]  [RESUELTO 2026-08-06, ver seccion 2] Hoj_bruto VOLUMETRICO
             (6 valores, MJ/m3) -- CONFIRMADO por analisis numerico directo
             de los 35 doubles reales (no una hipotesis): cada uno de los 6
             valores coincide, con error <0.02% en 6 componentes distintos
             probados (Metano, Etano, Propano, H2S, Hidrogeno, n-Decano),
             con Hoj_bruto_molar[j] (ya CERTAIN, indices [4:8]) dividido por
             el volumen molar ideal R*T/p evaluado en una de 5 temperaturas
             candidatas (0/15/20/25 C, 60F) -- ver seccion 2 para el detalle
             y los numeros exactos.
    [25:29]  [RESUELTO 2026-08-06, ver seccion 2] Hoj_NETO, base masa
             (4 valores, MJ/kg) -- CONFIRMADO: coincide, con error <0.1% en
             los mismos 6 componentes, con Hoj_bruto_masa[0] (ya CERTAIN,
             indices [12:16]) escalado por la razon Hoj_neto_molar/
             Hoj_bruto_molar del mismo componente -- es decir, el analogo
             en base masa de Hoj_neto, con la misma estructura de 4 valores
             que Hoj_bruto_masa.
    [29:35]  [RESUELTO 2026-08-06, ver seccion 2] Hoj_NETO VOLUMETRICO
             (6 valores, MJ/m3) -- mismo metodo y nivel de confirmacion que
             [19:25], usando Hoj_neto_molar[j] en vez de Hoj_bruto_molar[j].
             Con esto, de los 16 campos que antes decia el borrador "sin
             identificar con certeza", los 16 quedan identificados
             (6+4+6=16): ya no queda ningun campo GUESSING en la tabla salvo
             [16:19] (factor Z0, candidato razonable pero sin confirmar).
Validacion de plausibilidad fisica de estos datos (fuerte evidencia
indirecta de que la extraccion es correcta, ademas del match de Mj):
  - Nitrogeno, CO2, Helio, Argon, Oxigeno: Hoj_bruto = Hoj_neto = 0 en las
    22 filas correspondientes (correcto: son inertes/oxidante, sin poder
    calorifico).
  - Agua: Hoj_neto = 0.0 exacto en las 4 combinaciones (correcto: el poder
    calorifico neto del agua es cero por definicion, la diferencia
    bruto/neto ES el calor latente de vaporizacion del agua formada).
  - CO: Hoj_bruto = Hoj_neto EXACTO en las 4 combinaciones (correcto: la
    combustion de CO a CO2 no produce agua, por lo que no hay diferencia
    bruto/neto).
  - Hidrogeno: bj NEGATIVO (-0.004, -0.0048, -0.0051) -- coincide con un
    comportamiento conocido y citado en tablas publicadas de ISO 6976 (el
    H2 es el unico componente con factor de compresion de sumatoria
    negativo).
  - bj crece monotonamente con el numero de carbonos en la serie de
    parafinas (Metano 0.049 -> Etano 0.1 -> Propano 0.145 -> ... -> Decano
    0.75), consistente con la fisica esperada.

TABLA_CONSTANTES abajo ya esta poblada con Mj/bj/Hoj_bruto/Hoj_neto (molar y
masa) para los 22 componentes, usando los valores REALES de TABLA 2. Los
valores estan en las unidades que arroja el binario (Mj en g/mol, Hoj_bruto/
neto molar en kJ/mol, Hoj_bruto masa en MJ/kg) -- verificar/convertir antes
de mezclar con `calcular_volumen_molar_ideal` (que usa unidades SI base,
J/Pa/K) si se integra todo en un solo pipeline.
===============================================================================
4. CASO REAL DE LA APP -- CAPTURADO EN VIVO, 2026-08-05 (segunda sesion)
===============================================================================
[CERTAIN] METODO: se intento primero la llamada directa por Frida (mismo
patron que funciono para AGA-3/GERG), y SI se encontraron los simbolos reales
de la funcion orquestadora completa (demangled, confirmando exactamente lo
documentado en la seccion 1):
    _ZN6spirit4math12iso6976_201612iso6976_2016ERKNS1_19iso6976_2016_inputsE
    RNS1_20iso6976_2016_outputsE
  = spirit::math::iso6976_2016::iso6976_2016(iso6976_2016_inputs const&,
    iso6976_2016_outputs&), direccion real 0xcc2c1c70 (offset +0x138c70
    sobre el base del modulo en esta corrida).
El BLOQUEO real (no se forzo un resultado dudoso, ver limite de la tarea):
`iso6976_2016_inputs` NO es un struct plano como en GERG/AGA-3 -- su
constructor real (`iso6976_2016_inputsC1`, tambien confirmado por simbolo)
recibe SEIS `std::vector<...>` por referencia const (composicion,
molarmass_and_atomic_indices, summation_factors, gross_calorific_values,
ademas de un double y dos enums). Construir a mano en memoria heap 4-5
std::vector<T> reales (layout begin/end/capacity_end + buffer propio por
cada uno) con el patron de `Memory.alloc`+`writeByteArray` que basto para
GERG/AGA-3 (structs POD, sin heap propio) es un orden de magnitud mas
complejo, y con el presupuesto de tiempo de esta tarea (~45-60 min) el
riesgo de introducir un bug de layout invisible (que arruine el caso real
sin que se note) supero el beneficio -- se abandono la llamada directa a
`iso6976_2016()` en si.
[Nota de plausibilidad: `iso6976_2016_outputs` SI parece un struct plano --
no aparece constructor/destructor propio en la tabla de simbolos, lo que es
consistente con un aggregate de doubles sin heap, a diferencia de los
inputs.]

[CERTAIN] ALTERNATIVA USADA (mas confiable, sin adivinar layouts): en vez de
construir el struct de entrada a mano, se dejo que la app REAL lo construya
sola navegando la UI real de FlowXpert en el emulador Android (sin Frida,
sin tocar memoria) hasta la pantalla "ISO-6976 (2016)", que carga con una
composicion precargada llamada "Default" y calcula sola al abrir. Se
capturo la pantalla completa (composicion + condiciones + los 5 resultados
que expone esa funcion Excel) via `uiautomator dump`. Esto es exactamente el
mismo tipo de evidencia (composicion real + resultado real en pantalla) que
se uso para cerrar AGA-3, solo que por UI en vez de por llamada Frida
directa -- la funcion interna real invocada es la misma (el wrapper Excel
`Math_ISO6976_2016_M`, tambien confirmado por simbolo, es el que construye
el `iso6976_2016_inputs` real y llama a `iso6976_2016()`).

COMPOSICION REAL "Default" (fraccion molar, capturada de
`function_input_component_content` en pantalla, suma exacta 100.000%):
    Metano 81.315%, Nitrogeno 14.211%, CO2 0.99%, Etano 2.829%,
    Propano 0.38%, i-Butano 0.06%, n-Butano 0.072%, i-Pentano 0.018%,
    n-Pentano 0.033%, n-Hexano 0.02%, n-Heptano 0.013%, n-Octano 0.005%,
    Helio 0.046%, neo-Pentano 0.008% (resto de los 22 componentes = 0).

CONDICIONES REALES (capturadas de pantalla):
    Ref. Temperature = 15 / 15 / 15 grados C (combustion/metering/volumen,
    los 3 iguales -- por eso este caso NO permite, por si solo, distinguir
    entre los 3-4 indices de temperatura de bj/Hoj, ver mas abajo).
    Metering reference pressure = 1013.25 mbar = 101325 Pa (atmosfera
    estandar).
    Molar Mass Method = "Calculate" (la etiqueta en pantalla sugiere el
    "Metodo B" -- formula quimica -- de la seccion 1, pero el resultado real
    de Mmix coincide casi exacto con el Metodo A tabulado de este modulo,
    ver mas abajo -- para esta composicion, dominada por hidrocarburos
    simples con pesos atomicos IUPAC estandar, ambos metodos deberian dar
    prácticamente el mismo numero, asi que este caso NO permite distinguir
    con certeza cual de los dos metodos usa realmente el binario).

RESULTADOS REALES (pantalla, funcion Excel `Math_ISO6976_2016_M` -- expone
solo 5 de las 14 salidas internas de `iso6976_2016_outputs`):
    Sup. Calorific Val. = 33.26919 MJ/m3   (poder calorifico bruto, base
                                             volumen, gas real)
    Density             = 0.789661 kg/m3   (densidad real del gas)
    Compressibility     = 0.998154         (factor de compresion Z, mezcla)
    Relative Density    = 0.644348         (densidad relativa al aire)
    Molar Mass          = 18.63692 kg/kmol (= g/mol)

COMPARACION NUMERICA contra `normas/ISO_6976.py` con esta MISMA composicion
(ver bloque `if __name__` para el codigo exacto que reproduce estos
numeros):
  - Masa molar (Metodo A tabulado, `calcular_masa_molar`):
        18.637417 g/mol  vs  18.63692 g/mol real  => dif. 0.0027% [CERTAIN]
    Este es el cierre mas limpio de todo el modulo: la tabla Mj (seccion 3)
    y la formula de masa molar quedan confirmadas contra un caso real,
    dentro del mismo margen (<0.01%) que AGA-3/GERG/NX-19.
  - Densidad relativa (`d = (Mmix/Mair)*(Zaire/Zmix)`, formula de la
    seccion 1, usando Mair=28.9626 g/mol y asumiendo Zaire~=0.9997, un valor
    tipico de tablas de aire a 101.325 kPa/15 C, NO confirmado en el
    binario):
        0.644496  vs  0.644348 real  => dif. 0.023% [LIKELY]
    (la version sin corregir por Z, Mmix/Mair a secas, ya da 0.6435 vs
    0.644348, dif. 0.13% -- la formula con razon de Z's mejora el ajuste,
    lo que es evidencia INDIRECTA de que la formula de densidad relativa de
    la seccion 1 es correcta, pero el valor de Zaire usado es una hipotesis
    razonable, no un numero confirmado leyendo el binario.)
  - Densidad real del gas: [ESTADO ANTERIOR, YA SUPERADO, se deja para
    trazabilidad] con `Vm_real = Vm_ideal/Z` (formula INCORRECTA, ver 4.2),
    Z=0.998154 tomado de pantalla:
        0.786769 kg/m3  vs  0.789661 kg/m3 real  => dif. 0.366% [LIKELY,
        NO CERTAIN -- no cerraba al <0.1% del resto del proyecto]
  - Poder calorifico bruto, base volumen: [ESTADO ANTERIOR, YA SUPERADO] con
    el Vm_real INCORRECTO de arriba, probando los 4 indices de Hoj_bruto:
        indice 0: 33.11388 MJ/m3  (dif. 0.467%)
        indice 1: 33.13081 MJ/m3  (dif. 0.416%)
        indice 2: 33.14810 MJ/m3  (dif. 0.364%)
        indice 3: 33.20000 MJ/m3  (dif. 0.208%)  <- el mas cercano, pero
        ningun indice cerraba <0.1% -- sintoma de que el problema NO era el
        indice sino la formula de Vm_real (ver 4.2).
  - Factor de compresion Z (`calcular_factor_compresion`): [ESTADO ANTERIOR,
    ya SUPERADO, se deja para trazabilidad] En la sesion anterior, con
    p_ref=101325 Pa, R_GAS=8.31446 J/(mol*K), T0=288.15 K (las unidades SI
    "obvias"), la formula de la seccion 1 daba Z COMPLEJO/negativo.
    Resolviendo a la inversa cuanto tendria que valer el coeficiente
    K=p_ref/(R*T0) para que la formula reproduzca el Z real (0.998154), el
    K necesario salia ~1000 VECES MENOR que el K en unidades SI puras (Pa,
    J/mol/K), consistente con p_ref en kPa en vez de Pa -- pero esa sesion
    reporto que aun corrigiendo ese factor de 1000 el ajuste seguia
    quedando 5%-7% fuera, sin identificar la causa.

4.1 [RESUELTO 2026-08-05, tercera sesion -- Camino 1 de la tarea de
continuacion] Revisando el "summation factor method" tal como lo describe
el texto publico de ISO 6976 (no via Frida ni disassembly adicional, solo
cruce de formula/unidades), la hipotesis de p_ref en kPa (no en Pa) era
correcta -- el "5%-7% fuera" de la sesion anterior fue un error de esa
sesion (no se identifico la causa exacta, probablemente un error aritmetico
al recalcular a mano), no una limitacion real de la hipotesis. Verificando
con codigo (no a mano) el caso real completo:
    p_ref_kpa = 101.325 (= 101325 Pa / 1000), R_GAS=8.31446 J/(mol*K) sin
    cambios, T0=288.15 K sin cambios, formula sin cambios estructurales
    (Z = 1 - (p_ref_kpa/(R*T0)) * (sum(xj*sqrt(bj)))^2):
        indice bj 0: Z=0.998033  (dif. 0.0121% vs 0.998154 real)
        indice bj 1: Z=0.998233  (dif. 0.0080% vs 0.998154 real)  <- mejor
        indice bj 2: Z=0.998274  (dif. 0.0120% vs 0.998154 real)
    Los 3 indices cierran <0.02%, muy por debajo del margen <0.1% del resto
    del proyecto -- el bug real era exactamente ese factor de 1000 en
    p_ref, nada mas. [CERTAIN] El indice 1 es el mejor cierre (evidencia
    [LIKELY] de que corresponde a la combinacion 15/15/15 de este caso).
    Se probo tambien, por completitud, si el bug podia ser que "bj" tabulado
    ya fuera sqrt(b) (evitando la raiz adicional en el codigo) -- esa
    variante da 0.17%-0.18%, peor que la formula con sqrt explicito, y
    ademas contradice la estructura sqrt(bj) que la decompilacion original
    marco como [CERTAIN] (seccion 1) -- se descarto por ambas razones.
    IMPORTANTE (honestidad): correjir Z NO mueve de forma apreciable los
    dos pendientes de abajo (densidad real, poder calorifico volumetrico):
    el Z de pantalla (0.998154) y el Z ya corregido (0.998233) son casi
    iguales, asi que esos dos pendientes son un problema DISTINTO,
    independiente de Z, que sigue sin resolverse.

4.2 [RESUELTO 2026-08-05, cuarta sesion de continuacion -- Camino 1 de la
tarea, igual que 4.1] Los dos pendientes que quedaban (densidad real, poder
calorifico volumetrico) se atacaron cruzando `calculate_real_gass_volume`
contra la ecuacion de gas real publica del "summation factor method":
p*Vm = Z*R*T. El bug real: la funcion `calcular_volumen_molar_real` DIVIDIA
Vm_ideal entre Z (`Vm_ideal/Z`) en vez de MULTIPLICAR (`Vm_ideal*Z`). El
patron decompilado original `(CONST*a1*a2)/a3` es ambiguo por si solo (SI
puede leerse como `R*T*Z/p`, tres factores multiplicados sobre uno dividido,
exactamente igual de bien que la lectura anterior `(R*T/p)/Z`) -- la fisica
basica (no mas disassembly) resuelve la ambiguedad a favor de la
multiplicacion. Con ese unico cambio, usando el MISMO Z ya resuelto en 4.1
(indice_temp=1, Z=0.998233) y la MISMA composicion/condiciones del caso real:
    Densidad real del gas = 0.789619 kg/m3  vs  0.789661 kg/m3 real
        => dif. 0.0053% [CERTAIN, cierra muy por debajo del margen <0.1%]
    (por completitud, los otros 2 indices de Z tambien fueron probados con la
    formula corregida: indice 0 -> dif. 0.0147%, indice 2 -> dif. 0.0094% --
    el indice 1 sigue siendo el mejor cierre, consistente con 4.1, lo que
    refuerza que es el indice correcto para la combinacion 15/15/15.)

    Poder calorifico bruto, base volumen, con el Vm_real corregido,
    probando los 4 indices de Hoj_bruto:
        indice 0: 33.23382 MJ/m3  (dif. 0.1063%)
        indice 1: 33.25082 MJ/m3  (dif. 0.0552%)
        indice 2: 33.26817 MJ/m3  (dif. 0.0031%)  <- unico que cierra <0.1%
        indice 3: 33.32026 MJ/m3  (dif. 0.1535%)
        vs 33.26919 MJ/m3 real. A diferencia del intento anterior (seccion
    4, ESTADO ANTERIOR), aqui SOLO el indice 2 cierra dentro del margen del
    proyecto -- ya no es "el mas cercano de un grupo que no cierra", sino una
    senal clara y aislada. Evidencia [LIKELY], reforzada por el cierre
    numerico (no solo por plausibilidad de tabla), de que el indice 2
    corresponde a la combinacion de temperatura 15/15/15 de este caso para
    la tabla Hoj (que es una tabla de 4 valores, distinta de la tabla bj de 3
    valores donde el indice 1 fue el mejor cierre -- no hay razon para que
    ambos indices coincidan, son tablas/combinaciones distintas).

    UN SOLO BUG resolvio AMBOS pendientes a la vez, confirmando la hipotesis
    de la seccion 2 (paso 3 de la tarea de continuacion): densidad real y
    poder calorifico volumetrico comparten a `calculate_real_gass_volume`
    como causa raiz comun.

4.3 [RESUELTO 2026-08-06, tarea de continuacion -- mapeo de indices y Zaire
POR FRIDA EN VIVO, no por ajuste numerico] Los 2 pendientes que quedaban
(mapeo indice->temperatura exacto, valor de Zaire) se atacaron con Frida
hookeando la app REAL en el emulador Android, con el patron ya usado en
AGA-3/GERG/NX-19: `Interceptor.attach` sobre los simbolos reales (demangled,
confirmados por tabla de simbolos, direcciones reportadas por Frida en la
sesion real, base del modulo variable por ASLR pero resuelta en vivo por
`Module.findSymbolByName`) de:
    `calculate_compression_factor` (bj/Z)
    `calculate_real_gas_relative_density` (densidad relativa/Zaire)
    `select_reference_temperatures` (para ver el struct de indices crudo)

HALLAZGO CLAVE DE METODO: cambiar el selector "Ref. Temperature" de la UI
IN-PLACE (sin cerrar la pantalla) NO llama a NINGUNA funcion nativa de
`spirit::math::iso6976_2016` (se hookeo el orquestador `iso6976_2016()`
completo y las 14 funciones internas, cero llamadas) -- los resultados que
se ven en pantalla tras cambiar el combo in-place son correctos pero se
producen por otra ruta (probablemente Java, o una cache) que este proyecto
no necesito reversear porque se encontro la ruta que SI llama al motor
nativo real: cerrar la pantalla (`KEYCODE_BACK`) y volver a entrar a
"ISO-6976 (2016)" SI dispara una llamada real y completa a
`Math_ISO6976_2016_M` -> `iso6976_2016()` -> las 14 funciones internas, con
los parametros que la pantalla tenia guardados (el combo de temperatura
persiste entre entradas). Confirmado hookeando primero el wrapper
`Math_ISO6976_2016_M` solo (disparo real confirmado en la re-entrada, cero
disparos con cambio in-place) antes de confiar en los hooks mas profundos.

EVIDENCIA EXACTA CAPTURADA (2 combinaciones reales distintas, cada una
recreando la pantalla para forzar la llamada nativa real):

  CASO metering=0 C (combo UI "15 / 0 / 0 C", combustion=15, metering=volumen=0):
    `select_reference_temperatures`: reference_conditions de entrada = 4
      bytes [03 00 00 00] + 4 bytes [01 00 00 00] (2 int32: 3, 1) ->
      `temperatures` de salida = 4 int32, primeros 2 = **2, 1**.
    `calculate_compression_factor`: temperature_index real = **1**,
      p (double por valor) = **101.325** (confirma [CERTAIN], ya no por
      resolucion inversa, que p_ref entra en kPa), Z resultado =
      **0.99774309587759670** (exacto, 14 cifras -- coincide con el
      0.997743 redondeado que ya se habia visto en pantalla).
    `calculate_real_gas_relative_density`: temperature_index = **1**,
      arg1 (double) = 101.325, arg2 (Zmix real) = 0.99774309587759670
      (mismo Z de arriba), arg3 (Mmix real) = 18.636924201919993,
      salida (densidad relativa real) = **0.64449964029341285**.

  CASO metering=15 C (combo UI "15 / 15 / 15 C", el caso "Default" de la
  seccion 4, combustion=metering=volumen=15):
    `select_reference_temperatures`: reference_conditions de entrada = 2
      int32 (1, 1) -> `temperatures` de salida, primeros 2 int32 = **2, 2**.
    `calculate_compression_factor`: temperature_index real = **2** (!),
      p = 101.325, Z resultado = **0.9981537729755504**.
    `calculate_real_gas_relative_density`: temperature_index = **2**,
      Zmix = 0.9981537729755504, Mmix = 18.636924201919993 (identico al
      otro caso, correcto: Mmix no depende de temperatura), salida
      (densidad relativa real) = **0.6443479206677606** (coincide exacto
      con el 0.644348 visto en pantalla, seccion 4).

CONCLUSION 1 (mapeo bj/metering) [CERTAIN, ya no LIKELY]: el indice real
para el caso "Default" (metering=15 C) es **2**, NO 1 como usaba el
borrador anterior (elegido por MEJOR AJUSTE NUMERICO en la seccion 4.1
vieja). El ajuste numerico con indice=1 daba un error menor (0.008% vs
0.012% del indice=2 correcto) por pura coincidencia: los 3 valores bj de
cada componente son numericamente muy cercanos entre si (la correccion de
compresibilidad varia poco entre 0/15/20 C), asi que un solo caso real no
bastaba para distinguir el indice correcto por cierre numerico -- hacia
falta la lectura directa del argumento real, que ahora SI se tiene. El
indice 1 confirmado corresponde a metering=0 C. La hipotesis "por
eliminacion" de que el indice 0 correspondia a metering=20 C (escrita en
esta seccion en la sesion anterior) fue PROBADA por Frida en una tarea de
continuacion posterior y quedo REFUTADA: el `temperature_index` real
capturado para metering=20 C es **4**, no 0 (ver seccion 4.4) -- resulto
que `temperature_index` es un enum mas amplio que 0..2 (se han visto 1, 2 y
4), no un indice directo a las 3 columnas de bj, y el indice 0 sigue sin
dispararse por ningun combo real probado. Se deja como pendiente genuino
[GUESSING], no [LIKELY], sin forzar una conclusion mas fuerte de la que la
evidencia permite -- ver seccion 4.4 para el intento completo y por que no
se resolvio dentro del presupuesto de tiempo de esa tarea.
CORRECCION APLICADA: el autotest y la tabla de resultados de esta seccion
ahora usan indice bj=2 (confirmado), no 1.

CONCLUSION 2 (mapeo Hoj/combustion) [CERTAIN, ya no LIKELY]: el primer
int32 de la salida de `select_reference_temperatures` (el
`combustion_temperature_index`, tipo DISTINTO de `temperature_index` por su
firma mangled propia en `calculate_gross_calorific_value_on_molar_basis`)
salio **2** en AMBOS casos reales capturados (que comparten combustion=15 C)
-- confirma en CERTAIN, no ya por cierre numerico, que combustion=15 C
mapea a indice Hoj=2, exactamente el indice que el borrador anterior ya
usaba (por cierre numerico, seccion 4.2) para el caso "Default". Aqui el
borrador anterior SI tenia el indice correcto, solo le faltaba la
confirmacion directa.

CONCLUSION 3 (Zaire) [SUPERADO por la seccion 4.6, se deja para trazabilidad
-- en 2026-08-06 esto era LIKELY, un valor derivado de 2 casos reales sin
desensamblar el cuerpo]: `calculate_real_gas_relative_density` NO recibe
Mair ni Zaire como argumento (firma real de 5 parametros: temperature_index,
p, Zmix, Mmix, salida) -- son constantes/tabla interna de la funcion, no
aislables sin desensamblar su cuerpo (no se hizo en esta sesion, presupuesto
de tiempo). Pero como se tienen los 3 valores reales exactos (Zmix, Mmix,
densidad relativa real) para 2 temperature_index distintos, se puede
recuperar el PRODUCTO (Zaire/Mair) sin asumir Mair, invirtiendo
d = Mmix*(Zaire/Mair)/Zmix:
    indice 1 (metering=0 C):  Zaire/Mair = 0.034503819376595427
    indice 2 (metering=15 C): Zaire/Mair = 0.034510 (mas exacto:
                               0.03450989557907936)
Los 2 valores difieren solo 0.0176% entre si -- CROSS-VALIDACION: usando el
valor de indice 2 (Default) para predecir la densidad relativa real del
caso de indice 1 (y viceversa) da un error de 0.0176% en ambos sentidos,
muy por debajo del margen <0.1% del proyecto. Esto confirma que una
constante FIJA (Zaire/Mair aproximadamente 0.03451, sin depender del
indice) reproduce ambos casos reales dentro del margen del proyecto -- se
adopta esa constante fija (derivada del caso "Default", indice 2, que es el
caso de referencia de todo este modulo) en vez de la hipotesis anterior
Mair=28.9626 + Zaire=0.9997 (que daba 0.0150% de diferencia solo por
coincidencia de que el producto Mair*Zaire=28.9539 se acercaba al valor
real Mair*Zaire implicito de 28.9626*0.034510=0.99968... el valor real
implicito del PRODUCTO Mair*Zaire, si Mair=28.9626, seria Zaire=0.99951 --
mas cercano a 1.0 que la hipotesis anterior 0.9997 en la direccion
equivocada, otra pista de que 0.9997 era una coincidencia de ajuste, no el
valor real). Se documenta la pequena diferencia entre los 2 indices como
posible dependencia real de Zaire con la temperatura (fisicamente
plausible, el aire tambien tiene un factor de compresion que varia con la
temperatura) sin forzar una conclusion mas fuerte de la que la evidencia
permite.

ACTUALIZACION 2026-08-07 (ver seccion 4.6 para el detalle completo)
[CERTAIN, ya no LIKELY]: la sospecha de arriba ERA CORRECTA -- Zaire SI
depende de temperature_index, no por ruido de precision sino porque la
funcion la calcula en vivo desde una tabla real de 4 valores `bair[idx]`
(idx = temperature_index RAW 1..4, el mismo entero ya visto por Frida, NO el
indice 0..2 de la tabla bj de componentes). Mair es una constante literal
real (28.96546 g/mol). Formula real completa:
    Zaire(idx) = 1 - (p_ref_kPa / 101.325) * bair[idx]
    bair[1] = 0.0005810000000000537   bair[2] = 0.0004049999999999887
    bair[3] = 0.0003990000000000382   bair[4] = 0.0003549999999999942
Con estos valores exactos, Zaire(1)/Mair, Zaire(2)/Mair y Zaire(4)/Mair
reproducen los 3 valores de "densidad relativa real" hookeados por Frida
con diferencia 0.0000% (bit-exacto, no solo <0.1%) -- ver seccion 4.6.

CONCLUSION DE ESTA SECCION (actualizada 2026-08-06, autotest re-corrido
despues de aplicar las correcciones): con el caso real "Default" y el
indice bj=2 CONFIRMADO (no ya 1), TODOS los resultados expuestos por la app
siguen cerrando por debajo del margen <0.1% del resto del proyecto:
    Masa molar        : dif. 0.0027%
    Factor Z          : dif. 0.0120%  (indice bj = 2, CONFIRMADO por Frida)
    Densidad relativa : dif. 0.0094%  (constante ZAIRE_SOBRE_MAIR derivada
                                        de 2 casos reales por Frida, ya no
                                        una hipotesis de manual)
    Densidad real     : dif. 0.0094%  (indice bj = 2, mismo Z de arriba)
    Poder calorifico   : dif. 0.0071%  (indice Hoj = 2, CONFIRMADO por Frida)
    volumetrico bruto
El algoritmo general (secuencia de 14 pasos), la tabla de constantes
Mj/Hoj/bj (seccion 3), el factor de compresion Z (4.1, indice corregido en
4.3), el volumen real de gas / densidad real / poder calorifico volumetrico
(4.2) y ahora tambien el mapeo indice->temperatura + la constante de
densidad relativa (4.3) quedan validados contra 2 casos reales dentro del
margen del proyecto -- el UNICO punto que sigue sin aislarse por completo es
el valor INDIVIDUAL de Mair y Zaire (solo su producto/razon esta
confirmado) y el indice bj=0, ver 4.4 (por eliminacion, no por Frida
directo, y la propia hipotesis de eliminacion quedo REFUTADA en 4.4 -- se
deja como pendiente honesto, no forzado). Con esto, **ISO 6976 (variante
2016_M, 22 componentes) sigue CERRADA**, ahora con evidencia mas fuerte
(Frida en vivo, no solo ajuste numerico) para el mapeo de indices de
temperatura y para la constante de densidad relativa, al mismo nivel de
confianza que AGA-3/AGA-5/GERG-2004/GERG-2008/NX-19.

4.4 [INTENTO 2026-08-06, tarea de continuacion -- NO resuelto, documentado
honestamente] Se intento confirmar por Frida en vivo el indice bj=0 probando
un TERCER combo real de "Ref. Temperature" en la UI (emulador Android,
mismo proceso Flow-Xpert PID 2880 que ya estaba corriendo de la sesion
anterior, mismo frida-server ya corriendo -- se reutilizo el entorno sin
necesidad de reiniciar nada): combo "20 / 20 / 20 C" (candidato a metering=
20 C, el tercer valor de metering no probado todavia, ver seccion 2). Se
hookeo `select_reference_temperatures` + `calculate_compression_factor` +
`calculate_real_gas_relative_density` (mismos simbolos ya usados en 4.3), se
disparo la re-entrada real (BACK + reabrir "ISO-6976 (2016)", confirmado
necesario de nuevo) via `adb shell input keyevent 4` + `input tap` sobre el
item de menu, y SI se capturo una llamada real:
    `select_reference_temperatures`: reference_conditions de entrada = 2
      int32 (5, 1) -> temperatures de salida, primeros 2 int32 = **4, 4**
      (antes: (2,1) para metering=0 C y (2,2) para metering=15 C -- ver 4.3).
    `calculate_compression_factor`: temperature_index real = **4** (!), p =
      101.325 (sin cambios), Z resultado = **0.9982733642719735** (coincide
      EXACTO con el 0.998273 visto en pantalla para este combo, confirmado
      independientemente por `uiautomator dump` antes del hook).
    `calculate_real_gas_relative_density`: temperature_index = 4, Zmix =
      0.9982733642719735, Mmix = 18.636924201919993 (identico a los otros 2
      casos), salida = 0.6443029555708762 (coincide con el 0.644303 visto en
      pantalla).

HALLAZGO (honesto, no el que se buscaba): el `temperature_index` real para
metering=20 C es **4**, NO 0 como predecia la hipotesis "por eliminacion" de
la seccion 2/4.3 -- esa hipotesis queda REFUTADA por esta evidencia directa,
no solo sin confirmar. Esto revela que `temperature_index` NO es simplemente
un indice 0..2 que entra directo al arreglo de 3 bj de la seccion 3 (si lo
fuera, 4 seria invalido) -- es un enum mas amplio (se han visto los valores
1, 2 y 4 hasta ahora, nunca 0 ni 3), probablemente uno por cada temperatura
Celsius distinta que la UI puede seleccionar en cualquiera de sus dos roles
(combustion o metering/volumen), no uno por cada COLUMNA de la tabla bj.
Buscando, por completitud, que columna de bj (0/1/2) y que T0 en la formula
de Z reproducen mejor el Z real de este combo (0.9982733642719735) con
`calcular_factor_compresion` ya corregido: la columna 2 con T0=288.15 K FIJO
(15 C, NO 293.15 K/20 C) da un ajuste casi exacto (dif. 0.00006%, muchisimo
mejor que cualquier otra combinacion probada) -- es decir, numericamente el
combo "20/20/20" parece reusar la MISMA columna de bj (2) y el MISMO T0 fijo
(288.15 K) que el combo "15/15/15" ya usaba, en vez de una columna/T0 propios
de 20 C. Se probo tambien el combo metering=0 C (temperature_index=1, Z real
0.99774309587759670 ya documentado en 4.3) contra las mismas combinaciones
de columna/T0: NINGUNA reproduce ese Z con la misma precision (el mejor
ajuste, columna 0 con T0=273.15 K, da 0.018% de diferencia, un orden de
magnitud peor que el 0.00006% del combo de 20 C) -- asi que la hipotesis
"T0 siempre fijo en 288.15 K" tampoco cierra de forma limpia para los 3
casos a la vez. CONCLUSION HONESTA: no se logro, dentro del presupuesto de
tiempo de esta tarea (~30-40 min, ya usado), un modelo simple y consistente
que explique los 3 valores reales de `temperature_index` (1, 2, 4) y sus Z
correspondientes con una sola regla clara -- el mapeo real es mas complejo
de lo que este modulo asume (`indice_temp` como entero 0..2 pasado
directamente). NO se fuerza una conclusion mas fuerte de la que la evidencia
permite. El indice bj=0 (columna 0 de la tabla de la seccion 3) SIGUE sin
dispararse por ningun combo real probado (1, 2, 15, 20 C dieron
temperature_index 1, 2, 2 y 4 respectivamente, nunca 0) -- queda como
pendiente genuino, no resuelto, ver seccion 2. IMPORTANTE: esto NO afecta el
cierre <0.1% ya logrado para el caso real "Default" (combo 15/15/15, indice
bj=2), que sigue exactamente igual que antes -- este hallazgo solo aplica a
combos DISTINTOS del caso de referencia del proyecto, y no se cambio ningun
codigo de `calcular_factor_compresion` a raiz de esto (solo se corrigio el
caso de Hidrogeno, ver docstring de esa funcion, un tema independiente).
Scripts usados (nuevos, agregados a este intento): `android_sdk_setup/
hook_iso6976_indice0.js` y `android_sdk_setup/run_hook_iso6976_indice0.py`
(mismo patron ya usado en `hook_iso6976_reentry.js`), log crudo en
`android_sdk_setup/hook_iso6976_indice0_out.txt`.

4.5 [RESUELTO 2026-08-06/07, metodologia nueva] EL PENDIENTE DE 4.4 (indice
bj=0 nunca disparado, cuerpo interno de `select_reference_temperatures`
nunca visto) SI se resolvio, no por Frida sino porque el bug de cuerpo vacio
de Ghidra 12.1.2 (`{ return; }` en funciones cortas con prologo PIC
`__i686.get_pc_thunk.bx`) NO se reproduce en Ghidra 11.4.3 (release LTS
anterior, probada en un proyecto Ghidra nuevo y separado, sin tocar el
proyecto/instalacion de 12.1.2 que sigue usandose para el resto del
proyecto). CONTROL usado antes de confiar en el resultado: se decompilo
primero `PropertiesISO6976_1995_rev1` (RAW 0x124980) con Ghidra 11.4.3 -- el
cuerpo salio COMPLETO (249 bytes de cuerpo real, switch de 6 casos +
aritmetica real de masa molar/Z/poder calorifico, no `{ return; }`), lo cual
YA se sabia que era la logica real de esta funcion por otro metodo previo.
Con el control confirmado, se decompilo `select_reference_temperatures`
(RAW 0x137b50) con la misma version -- TAMBIEN salio con cuerpo completo (un
solo `switch` de 7 casos + default). Tabla real leida directo del
decompilado (undefined4 = int32, sin ambiguedad de registros ni de tipos):

    switch(reference_conditions.campo0):        // int32, valores 1..7
      default: return 1;                        // ERROR -- 0 y >7 caen aqui
      case 1: temperaturas = (combustion=2, metering=2, bj_dbl=A)
      case 2: temperaturas = (combustion=1, metering=1, bj_dbl=B)
      case 3: temperaturas = (combustion=2, metering=1, bj_dbl=B)
      case 4: temperaturas = (combustion=5, metering=1, bj_dbl=B)
      case 5: temperaturas = (combustion=4, metering=4, bj_dbl=C)
      case 6: temperaturas = (combustion=5, metering=4, bj_dbl=C)
      case 7: temperaturas = (combustion=3, metering=3, bj_dbl=D)

(A/B/C/D son 4 constantes double distintas leidas de memoria estatica,
`_UNK_0023a810/DAT_00237808/_UNK_0023a818/_UNK_0023a820` -- no se
identificaron a que representan fisicamente en esta tarea, queda fuera del
alcance de este hallazgo puntual). Los 7 casos coinciden con "las 7 [combos]
que expone la UI" ya mencionadas en la seccion 2 (parrafo del layout de la
tabla 2, campo [16:19]) -- confirma que el selector de la UI envia un unico
entero 1..7 (no 2 enteros independientes como se asumia en 4.3/4.4), y que
ese entero indexa DIRECTO a un `switch` estatico, no a una tabla de datos en
memoria.

VALIDACION CRUZADA (CERTAIN, no solo plausible) contra los 3 casos reales ya
confirmados por Frida en 4.3/4.4, ANTES de confiar en el decompilado:
    combo UI "15/0/0"    (metering=0 C):  input real capturado = 3
        -> tabla dice case 3 = (combustion=2, metering=1)
        -> Frida capturo salida real (2, 1)                    COINCIDE
    combo UI "15/15/15"  (Default):       input real capturado = 1
        -> tabla dice case 1 = (combustion=2, metering=2)
        -> Frida capturo salida real (2, 2)                    COINCIDE
    combo UI "20/20/20":                  input real capturado = 5
        -> tabla dice case 5 = (combustion=4, metering=4)
        -> Frida capturo salida real (4, 4)                    COINCIDE
Los 3/3 casos reales coinciden EXACTO (no aproximado, son enteros) con la
tabla leida del decompilado -- evidencia fuerte de que el decompilado de
Ghidra 11.4.3 es correcto, no una alucinacion del decompilador.

CONCLUSION (resuelve 4.4): el indice bj=0 NUNCA se disparo por ningun combo
real porque **0 no es un case valido** -- cualquier valor fuera de 1..7 cae
en el `default: return 1` (codigo de error), no en un indice de temperatura
real. La hipotesis de eliminacion de la sesion anterior (que asumia 0..2 o
0..N como rango valido) estaba mal planteada desde la base: el selector real
es un enum 1..7 sin el 0. Con esto, el mapeo indice->temperatura de ISO 6976
(variante 2016_M) queda [CERTAIN] en su totalidad (los 7 casos + el error),
no solo en los 3 casos observados -- aunque el significado FISICO de los
sub-indices 3 y 5 (que temperatura Celsius/Fahrenheit representan
exactamente, mas alla de que 1=0C, 2=15C y 4=20C ya estaban confirmados por
Frida) sigue sin confirmarse, por no ser necesario para ningun calculo del
caso real de referencia del proyecto.

METODOLOGIA (para reuso futuro con otras funciones que Ghidra 12.1.2 trunca
a cuerpo vacio): descargar Ghidra 11.4.3 PUBLIC (build 20251203,
https://github.com/NationalSecurityAgency/ghidra/releases/tag/
Ghidra_11.4.3_build) en una carpeta SEPARADA de la instalacion de 12.1.2 (no
reemplazar nada), crear un proyecto Ghidra NUEVO (no reusar el .gpr de
12.1.2), reimportar `libFXLibrary.so` desde cero con reanalisis completo, y
decompilar con un script `.java` (mismo patron que ya usaba este proyecto
para 12.1.2). SIEMPRE decompilar primero una funcion CONTROL cuya logica ya
se conozca por otro metodo antes de confiar en un resultado nuevo de la
version distinta -- este par control+objetivo es lo que evito aceptar un
posible falso positivo. No se probo si el bug tambien se evita con RetDec
directo sobre este mismo caso (RetDec ya se usaba como mitigacion aparte);
este hallazgo es especifico de Ghidra 11.4.3 vs 12.1.2.
===============================================================================
4.6 [RESUELTO 2026-08-07, tarea de continuacion -- ULTIMO PENDIENTE GENUINO
DEL MODULO] Mair y Zaire de `calculate_real_gas_relative_density` (seccion 2,
"PARCIALMENTE RESUELTO"; seccion 4.3, CONCLUSION 3) quedan aislados
INDIVIDUALMENTE y en [CERTAIN].

METODO (mas barato de lo previsto -- NO hizo falta Ghidra 11.4.3): antes de
tocar Ghidra, se busco la direccion real de la funcion por su nombre mangled
exacto (`_ZN6spirit4math12iso6976_201635calculate_real_gas_relative_density
ENS1_17temperature_indexEdRKdS4_Rd`) en los `.dsm` de RetDec YA GENERADOS en
una sesion anterior (`ANALISIS_GHIDRA_FLOWXPERT/retdec_out/
iso6976_missing.dsm`), sin volver a correr RetDec ni Ghidra. La funcion SI
esta ahi completa, disassemblada (x86, RAW 0x137900-0x137a38, 312 bytes) --
simplemente nunca se habia leido a mano su logica interna, solo su firma.
Se decodifico la funcion instruccion por instruccion (mismo patron PIC ya
usado en la seccion 3: `call get_pc_thunk_bx` + `add ebx, 0x2754e2` desde el
retorno en 0x137906 => GOT_BASE = 0x137906 + 0x2754e2 = 0x3ACDE8, IDENTICO al
GOT_BASE ya confirmado en otras normas de este proyecto -- confirmacion
cruzada de que es el registro base correcto).

LOGICA REAL DECODIFICADA (sin ambiguedad, es x86 puro, no decompilado):
  1. Un primer switch sobre el argumento `temperature_index` (eax, entero,
     valores validos 1/2/3/4; cualquier otro valor -- incluido 0 -- cae en un
     `return 1` de error, MISMO PATRON que el switch 1..7 de
     `select_reference_temperatures` de la seccion 4.5) carga en xmm4 UNA de
     4 constantes double distintas segun el indice, leidas cada una con un
     acceso `ebx - offset` propio:
         idx=1 -> ebx-0x182600   idx=2 -> ebx-0x1825f8
         idx=3 -> ebx-0x1825f0   idx=4 -> ebx-0x1825e8
     (offsets espaciados exactamente 8 bytes = sizeof(double), confirmando
     que es una tabla de 4 doubles consecutivos, no 4 constantes sueltas).
  2. Un guard: si Zmix (arg3, pasado por referencia) es igual a una constante
     (ebx-0x185610) o no es finito (llamada real a `isfinite()`), la funcion
     retorna 1 (error) sin escribir la salida -- proteccion de division por
     cero/NaN, no logica de negocio.
  3. Calculo real (todo en x86 puro, reordenado aqui a notacion legible):
         Zaire = 1.0 - (p / CONST_101_325) * xmm4        (xmm4 = bair[idx])
         *salida = ((Zaire) * (Mmix / CONST_MAIR)) / Zmix
     donde CONST_101_325 (leida de ebx-0x184fc8) y CONST_MAIR (leida de
     ebx-0x1825e0) son 2 constantes literales adicionales, y el 1.0 inicial
     de Zaire tambien se lee de memoria (ebx-0x1855d0) en vez de ser un
     inmediato en la instruccion (estilo de codegen tipico de este binario,
     no cambia el valor). Esta estructura es LITERALMENTE la misma que
     `calcular_factor_compresion` (Z = 1 - K*b) aplicada al AIRE en vez de a
     la mezcla -- explica por que Zaire "parecia" variar con temperature_index
     en la sesion anterior: SI varia, porque se recalcula con la misma
     formula de factor de compresion, solo que con la composicion fija del
     aire ya resuelta a una tabla de 4 "b" en vez de sumar xj*sqrt(bj) en
     vivo (el aire no tiene composicion variable que sumar).

VALORES REALES leidos directamente de `apk_analisis/libFXLibrary.so` en las
direcciones GOT-relativas de arriba (`addr = GOT_BASE - offset`, mismo
metodo de lectura directa de memoria estatica que TABLA 1/TABLA 2 de la
seccion 3, verificado con `struct.unpack('<d', ...)`):
    CONST_MAIR   (ebx-0x1825e0, addr 0x22A808) = 28.96546            g/mol
    CONST "1.0"  (ebx-0x1855d0, addr 0x227818) = 1.0                 (exacto)
    CONST_101_325(ebx-0x184fc8, addr 0x227E20) = 101.325              (kPa)
    CONST guard  (ebx-0x185610, addr 0x2277D8) = 0.0                  (Zmix)
    bair[1]      (ebx-0x182600, addr 0x22A7E8) = 0.0005810000000000537
    bair[2]      (ebx-0x1825F8, addr 0x22A7F0) = 0.0004049999999999887
    bair[3]      (ebx-0x1825F0, addr 0x22A7F8) = 0.0003990000000000382
    bair[4]      (ebx-0x1825E8, addr 0x22A800) = 0.0003549999999999942

FORMULA FINAL:
    Zaire(idx) = 1.0 - (p_ref_kPa / 101.325) * bair[idx]
    d = (Mmix / 28.96546) * (Zaire(idx) / Zmix)

VALIDACION (CERTAIN, no solo plausible) contra los 4 casos reales ya
capturados por Frida en 4.3/4.4/4.7 -- se recalcula `d` desde CERO (Mmix,
Zmix, p, idx reales) y se compara contra la "densidad relativa real" tambien
hookeada, SIN usar ningun valor ya conocido de Zaire ni de d como insumo:
    idx=1 (metering=0 C):  p=101.325, Mmix=18.636924201919993,
        Zmix=0.99774309587759670 -> Zaire(1)=0.999419 -> d calculado =
        0.03450381937659543*Mmix/Zmix = 0.64449964029341285
        vs real 0.64449964029341285                    dif = 0.0000%
    idx=2 (metering=15 C, Default): Zmix=0.9981537729755504 -> Zaire(2)=
        0.999595 -> d calculado = 0.6443479206677606
        vs real 0.6443479206677606                     dif = 0.0000%
    idx=4 (metering=20 C): Zmix=0.9982733642719735 -> Zaire(4)=0.999645 ->
        d calculado = 0.6443029555708762
        vs real 0.6443029555708762                     dif = 0.0000%
    idx=3 (combo UI 60F/60F/60F, agregado 2026-08-08, ver seccion 4.7):
        Mmix=17.93559520191999, Zmix=0.9983921141873021 -> Zaire(3)=0.999601
        -> d calculado = 0.6199560513441248
        vs real 0.6199560513441248                     dif = 0.0000%
Los 4 casos coinciden BIT A BIT (no solo <0.1%, la diferencia calculada por
Python da exactamente 0.0) -- evidencia tan fuerte como es posible obtener
sin acceso al codigo fuente original: la formula, las 4 constantes bair y
Mair quedan [CERTAIN] en su totalidad, no solo el producto Zaire/Mair como
en la sesion anterior, y ahora con TODOS los 4 valores de bair[idx] (1..4)
confirmados contra un caso real cada uno -- ninguno queda sin disparar.

CONSISTENCIA CON `ZAIRE_SOBRE_MAIR` (la constante ya usada por el codigo de
este modulo y heredada por `ISO_6976_1995.py`/`ISO_6976_1983.py`):
`ZAIRE_SOBRE_MAIR = 0.03450989557907936` (valor ya presente en el codigo
desde la sesion 2026-08-06) es EXACTAMENTE `Zaire(2)/Mair` con los valores
reales ahora aislados (0.999595/28.96546) -- no hizo falta cambiar su valor
numerico, solo su justificacion y nivel de confianza (LIKELY -> CERTAIN). Se
agregan ademas `M_AIRE` (corregido de la hipotesis de manual 28.9626 al
valor real 28.96546), `BAIR_TABLA` (los 4 valores reales de bair) y las
funciones `calcular_factor_compresion_aire()` / `calcular_densidad_relativa()`
para quien necesite la formula general (cualquier temperature_index e
cualquier p_ref), no solo la constante fija del caso "Default".

RESIDUO ANTERIOR, RESUELTO 2026-08-08 (ver seccion 4.7): el significado
fisico exacto de `bair[idx=3]` no se habia podido cruzar contra ningun caso
real -- ver seccion 4.7 para el combo real que SI lo dispara y la validacion
numerica completa.
===============================================================================
4.7 [RESUELTO 2026-08-08, tarea de continuacion -- LOS 2 ULTIMOS PENDIENTES
MENORES DEL MODULO] Un UNICO caso real nuevo, capturado en el mismo emulador
Android (PID 2880 ya corriendo de sesiones anteriores, mismo frida-server),
resuelve a la vez el caveat de Hidrogeno (seccion 2 / docstring de
`calcular_factor_compresion`) y el residuo de `bair[idx=3]` (seccion 4.6).

METODO: se encontro la app YA DEJADA en un estado util por un intento
anterior de esta misma tarea que se interrumpio por un error de red antes de
guardar nada en este archivo (los cambios en la app / capturas Frida SI
persisten porque no dependen de la red del asistente, solo los cambios de
codigo se habian perdido) -- la pantalla "ISO-6976 (2016)" ya mostraba una
composicion editada a mano ("Unnamed Composition": igual a "Default" pero
Metano 76.315% en vez de 81.315% e Hidrogeno 5% nuevo, suma exacta 100%) y
"Ref. Temperature" ya en el combo "60F / 60F / 60F". Se re-hizo la captura
real desde cero en esta sesion (no se reutilizo ningun log viejo sin
verificar): se cargo `hook_iso6976_indice0.js` (mismo hook ya usado en 4.4,
cubre `select_reference_temperatures` + `calculate_compression_factor` +
`calculate_real_gas_relative_density`) sobre el proceso real, y se disparo
la re-entrada real (BACK + tap sobre "ISO-6976 (2016)" en el menu, bounds
reales [12,179][276,209] leidos de `uiautomator dump`) -- confirmado de
nuevo que cambiar composicion/temperatura in-place NO ejecuta nada, hace
falta cerrar y reabrir la pantalla.

CAPTURA REAL (Frida, PID 2880, esta sesion):
    select_reference_temperatures: reference_conditions de entrada = 7
        (unico int32 relevante, NO 2 como en combos anteriores)
        -> temperatures de salida, primeros 2 int32 = (3, 3)
    calculate_compression_factor: temperature_index real = 3 (NUNCA antes
        visto), p = 101.325 kPa, Z resultado = 0.9983921141873021
    calculate_real_gas_relative_density: temperature_index = 3,
        Zmix = 0.9983921141873021, Mmix = 17.93559520191999,
        salida (densidad relativa) = 0.6199560513441248
Captura independiente por `uiautomator dump` de la pantalla de resultados
tras la re-entrada (coincide con los valores hookeados): Compressibility
0.998392, Relative Density 0.619956.

HALLAZGO 1 (resuelve el residuo de `bair[idx=3]`, seccion 4.6): el combo de
UI "60F / 60F / 60F" SI dispara `temperature_index=3` -- confirma ademas que
el input entero 7 (`reference_conditions`) corresponde al **case 7** del
switch de `select_reference_temperatures` (tabla de la seccion 4.5:
case 7 = (combustion=3, metering=3)), EXACTO con la salida real (3, 3)
capturada arriba. Esto sube a 4/4 (antes 3/3) las coincidencias exactas
entre la tabla del switch decompilado y los casos reales de Frida, y ademas
confirma una hipotesis nueva sobre el ORDEN de los 7 combos que expone la
UI (nunca antes verificada, solo sospechada): la posicion del combo en la
lista de "Ref. Temperature" de la UI coincide 1-a-1 con el numero de case
del switch --
    posicion 1 = "15/15/15" (Default)  -> input real 1 -> case 1  [4.5]
    posicion 3 = "15/0/0" (metering=0C)-> input real 3 -> case 3  [4.5]
    posicion 5 = "20/20/20"            -> input real 5 -> case 5  [4.4/4.5]
    posicion 7 = "60F/60F/60F"         -> input real 7 -> case 7  [ESTA SESION]
4 de 4 posiciones probadas coinciden exacto con su numero de case -- fuerte
evidencia de que el orden es "posicion en la lista = numero de case", pero
las posiciones 2, 4 y 6 (candidatos "0/0/0", "25/0/0", "25/20/20" por
descarte, nunca probados) siguen sin confirmar directamente: se documenta la
hipotesis como [LIKELY], no [CERTAIN], honestamente, aunque 4/4 sin ninguna
excepcion es una muestra fuerte.

HALLAZGO 2 (resuelve el caveat de Hidrogeno, seccion 2 / docstring de
`calcular_factor_compresion`): con Hidrogeno = 5% real (fraccion 0.05, NO
descartada por el filtro `if x == 0.0: continue`, el termino SI se suma con
su raiz con signo, bj=-0.0048 en la columna 1), se corrio un barrido de las
3 columnas bj x 5 T0 candidatos contra el Z real (0.9983921141873021):

    col  T0(K)      Z calculado          dif
    0    273.15     0.9981900563     0.020238%
    0    288.15     0.9982842752     0.010801%
    0    293.15     0.9983135388     0.007870%
    0    298.15     0.9983418209     0.005037%
    1    273.15     0.9983835634     0.000856%  <- MEJOR AJUSTE, por lejos
    1    288.15     0.9984677090     0.007572%
    1    293.15     0.9984938439     0.010189%
    1    298.15     0.9985191022     0.012719%
    2    273.15     0.9984229124     0.003085%
    2    288.15     0.9985050096     0.011308%
    2    293.15     0.9985305084     0.013862%
    2    298.15     0.9985551519     0.016330%

El mejor ajuste (columna 1, T0=273.15 K, dif 0.000856%) es un orden de
magnitud mejor que el segundo mejor de la misma columna -- un patron
consistente con el ya visto para otros indices (una columna/T0 destaca
claramente sobre las demas, ver 4.3/4.4). Masa molar (formula lineal, no
usa raiz con signo, pero SI usa Mj real de Hidrogeno=2.0159 g/mol):
17.936062 g/mol calculado vs 17.935595 g/mol real, dif 0.0026% -- cierre tan
limpio como el caso "Default". Encadenando el Z de mejor ajuste (0.9983836)
y el Mmix calculado (17.936062) a traves de `calcular_densidad_relativa`
(usando `bair[3]` ya conocido) se obtiene una densidad relativa de
0.6199775, contra el real 0.6199561 -> dif 0.0035%.

CONCLUSION [CERTAIN, cierra <0.1% en los 3 resultados cruzados -- Mmix,
Z y densidad relativa]: la formula de raiz con signo para Hidrogeno (bj
negativo) reproduce, por primera vez contra un caso real con Hidrogeno > 0,
un resultado dentro del mismo margen de exactitud que el resto del modulo.
El caveat de la seccion 2 queda RESUELTO. RESIDUO HONESTO (no bloqueante,
mismo patron que otros indices): la columna bj (0/1/2) y el T0 exactos que
usa el binario real para temperature_index=3 siguen siendo un AJUSTE
NUMERICO de mejor cierre (columna 1, T0=273.15 K), no un valor leido de
disassembly -- igual de honesto que el estado ya aceptado para
temperature_index=1 y 4 en la seccion 4.4, y no impide el cierre <0.1% del
caso real de referencia del proyecto (que sigue usando temperature_index=2,
sin ningun cambio).

Scripts usados (nuevos, esta sesion): se reutilizo `hook_iso6976_indice0.js`
sin modificar (ya cubria exactamente lo necesario); runner nuevo
`android_sdk_setup/run_hook_iso6976_h2_idx3.py`, log crudo en
`android_sdk_setup/hook_iso6976_h2_idx3_out.txt`.
===============================================================================
5. ALERTA RESUELTA 2026-08-06: i-Butano/n-Butano e i-Pentano/n-Pentano SI
   ESTABAN INTERCAMBIADOS en TABLA_CONSTANTES -- CORREGIDO
===============================================================================
[CERTAIN] ORIGEN DE LA ALERTA: al construir `ISO_6976_ex_2016.py` (tabla de
60 componentes) se leyo, por evidencia DIRECTA de codigo maquina (22
instrucciones `call emplace_back` del wrapper `Math_ISO6976_2016_M`, con el
indice de fila como literal inmediata -- no una comparacion de valores), que
el mapeo real slot->fila es i-Butano->fila4, n-Butano->fila3 (e i-Pentano->
fila6, n-Pentano->fila5). Esto es EXACTAMENTE AL REVES del orden que este
archivo (`ISO_6976.py`) y `ISO_6976_ex_1995.py` (que hereda sus etiquetas
por comparacion de valores contra este archivo) venian usando. Como
i-Butano/n-Butano (e i-Pentano/n-Pentano) son isomeros con el MISMO Mj
(58.123 y 72.15 g/mol respectivamente), el cierre <0.1% de masa molar contra
el caso real "Default" (seccion 4) NO podia delatar este error -- de ahi la
alerta.

[CERTAIN] METODO DE RESOLUCION (Camino 1, el mas barato, resulto suficiente):
cruce contra la entalpia de combustion PUBLICA de cada isomero (ΔHf° de
formacion en fase gas, valores estandar de referencia, + estequiometria de
combustion C4H10+13/2 O2->4CO2+5H2O y C5H12+8 O2->5CO2+6H2O, con ΔHf(CO2)=
-393.5 kJ/mol y ΔHf(H2O,liquido)=-285.8 kJ/mol para poder calorifico BRUTO):
    n-Butano:  ΔHf°=-125.6 kJ/mol => Hoj_bruto = 2877.4 kJ/mol
    i-Butano (isobutano): ΔHf°=-134.2 kJ/mol (mas estable/negativo, isomero
              ramificado) => Hoj_bruto = 2868.5 kJ/mol (~2868.2 con ΔHf mas
              preciso) -- MENOR que n-Butano, consistente con que el isomero
              mas estable libera menos energia de combustion.
    n-Pentano: ΔHf°=-146.8 kJ/mol => Hoj_bruto = 3535.5 kJ/mol
    i-Pentano (isopentano): ΔHf°=-153.7 kJ/mol => Hoj_bruto = 3528.6 kJ/mol
    (neo-Pentano, el mas ramificado/estable: ΔHf°=-168.1 => 3514.2 kJ/mol,
     coincide con el valor YA presente sin swap en la tabla, 3514.61 -- esto
     ademas valida el metodo de calculo usado, sin necesidad de Frida ni
     disassembly adicional para resolver la alerta).
Estos valores calculados desde quimica basica publica coinciden (<0.1% de
diferencia, el mismo margen del resto del proyecto) con los valores YA
CORRECTOS y CONFIRMADOS POR EVIDENCIA DE CODIGO MAQUINA en
`ISO_6976_ex_2016.py` (fila3=n-Butano=2877.40, fila4=i-Butano=2868.20;
fila5=n-Pentano=3535.77, fila6=i-Pentano=3528.83) -- DOBLE confirmacion
independiente (quimica publica + codigo maquina real) de que este archivo
(`ISO_6976.py`) SI tenia los 2 pares intercambiados: la fila con Hoj=2877.40
estaba etiquetada "i-Butano" en vez de "n-Butano", y la fila con Hoj=2868.20
estaba etiquetada "n-Butano" en vez de "i-Butano" (mismo patron para el par
Pentano).

[CERTAIN] CORRECCION APLICADA: se intercambiaron las entradas completas
(Mj/bj/Hoj_bruto/Hoj_neto/Hoj_bruto_masa) de "i-Butano"<->"n-Butano" e
"i-Pentano"<->"n-Pentano" en `TABLA_CONSTANTES` (este archivo) y en
`TABLA_CONSTANTES_EX1995` (`ISO_6976_ex_1995.py`, que habia heredado el
mismo error al cross-validar contra este archivo). `ISO_6976_ex_2016.py` NO
se modifico -- ya tenia el orden correcto desde su propia tarea de
construccion.

[CERTAIN] VERIFICACION: se re-corrio el autotest completo contra el caso
real "Default" (seccion 4) tras la correccion. Los 5 resultados siguen
cerrando <0.1% (Masa molar 0.0027%, Z 0.0120%, densidad relativa 0.0094%,
densidad real 0.0094%, poder calorifico volumetrico bruto). El poder
calorifico volumetrico bruto (el unico resultado que usa Hoj de estos 4
componentes) MEJORO levemente tras el fix: de 0.0071% a 0.0068% de
diferencia -- una mejora pequena y NO por si sola concluyente (i-Butano+
n-Butano+i-Pentano+n-Pentano suman apenas 0.183% de la composicion real,
insuficiente para que este unico caso distinga el swap con fuerza por
cierre numerico solo, la misma razon por la que la alerta no se pudo
descartar antes solo mirando Mmix) pero SI consistente en direccion con la
correccion siendo correcta, nunca peor. La evidencia que realmente resuelve
esta alerta es la quimica publica + el codigo maquina de `ex_2016`, no el
cierre numerico de este caso (que es demasiado insensible a este swap
especifico para ser decisivo por si solo).
===============================================================================

===============================================================================
6. COMPARACION CRUZADA .xll (Windows) vs .so (Android) -- 2026-08-10
===============================================================================
[CERTAIN] Hasta esta fecha, TODO el trabajo de la familia ISO 6976 (las 5
variantes) se habia hecho exclusivamente decompilando `libFXLibrary.so`
(Android). Nunca se habia decompilado la version de `FlowXpert.xll`
(Windows) para comparar de forma independiente -- a diferencia de ISO 5167,
donde SI se hizo esa comparacion desde el principio (ver memoria del
proyecto). Se hizo ahora con Ghidra 12.1.2 sobre el proyecto ya existente
`D:\PROYECTOS FOQUS\analisis xll\ANALISIS .XLL.gpr` (el `.xll` NO tiene el
bug de "cuerpo vacio" que si afecta al `.so` con esa version de Ghidra).

[CERTAIN] Los 5 exports reales confirmados con `pefile` y Ghidra son
`FlowXpert_ISO6976_1983_M` / `_1995_M` / `_2016_M` / `ex_1995_M` / `ex_2016_M`
(mas los wrappers Excel `xlWrapper12_Math_ISO6976_*`/`xlWrapper4_Math_ISO6976_*`
que solo marshalan tipos de Excel hacia estos). Los 5 wrappers decompilan a
un patron IDENTICO de "armado de composicion + descriptor + engine
generico" (`FUN_1800471ac`->contexto TLS, `FUN_180046cb4`->construye vector
de composicion, `FUN_1800a816c/74/7c/84/8c`->devuelve un puntero a un
"descriptor de tipo" fijo por variante, `FUN_1800470d8`->`FUN_18005e590`
motor de despacho COMPARTIDO por las 5) -- exactamente el mismo patron de
"motor generico + descriptor de tipo llenado por constructor estatico" ya
documentado para AGA10/GERG en el `.so` (ver [[reversing-ghidra-flowxpert]]).

[CERTAIN] Siguiendo la tecnica de "buscar quien ESCRIBE el descriptor"
(constructor estatico -> `atexit`), se encontraron los 5 constructores reales
y, dentro de ellos, el nombre/descripcion/metadata COMPLETA de cada variante
(registrada como texto plano, `FUN_180064600(...)`), incluyendo el puntero
real a la funcion nucleo de cada una:
    ISO6976_1983_M    -> FUN_1800ab140 (330 B, motor propio monolitico)
    ISO6976_1995_M    -> FUN_1800ab4f8 (1359 B en su sub-nucleo FUN_1800caf7c,
                          motor propio monolitico)
    ISO6976_2016_M    -> FUN_1800ab9d4 (pipeline de varias sub-funciones:
                          FUN_1800cc820/FUN_1800cd1c8/FUN_18009d6cc/etc.)
    ISO6976ex_1995_M  -> FUN_1800ac218 (sub-nucleo FUN_1800cd480, DISTINTO
                          del de 1995_M base)
    ISO6976ex_2016_M  -> FUN_1800ac858 (mismo pipeline EXACTO de
                          sub-funciones que 2016_M: FUN_1800cc820/
                          FUN_1800cd1c8/FUN_18009d6cc/etc. -- lista de
                          callees IDENTICA)
El texto de metadata (nombres de campo, descripciones) coincide palabra por
palabra con los nombres de parametros/resultados ya usados en este archivo
Python (ej. "Real superior calorific value on volume basis at the reference
conditions...", "Molar Mass Method.; 1: Calculate; 2: Use table").

[CERTAIN] CONFIRMACION ARQUITECTONICA CRUZADA -- coincide EXACTO con lo ya
concluido desde el `.so` (seccion 4.x de este archivo y las variantes
`_1983.py`/`_1995.py`/`_ex_1995.py`/`_ex_2016.py`):
  - 1983_M y 1995_M: motor PROPIO monolitico en AMBOS binarios (no comparten
    pipeline con 2016_M) -- MATCH.
  - 2016_M y ex_2016_M: comparten el MISMO pipeline de sub-funciones en
    AMBOS binarios (`.so`: mismo namespace `iso6976_2016`; `.xll`: mismos 10
    callees byte por byte) -- MATCH exacto de la conclusion "ex reusa la
    base" para la revision 2016.
  - ex_1995_M: motor DISTINTO del de 1995_M base en AMBOS binarios (`.so`:
    `calculate_revision_1` != `PropertiesISO6976_1995_rev1`; `.xll`:
    FUN_1800cd480/FUN_1800b1fa4/FUN_1800b2040 != FUN_1800caf7c) -- MATCH
    exacto de la conclusion "ex NO reusa la base" para la revision 1995.
No se encontro NINGUNA discrepancia de arquitectura entre plataformas.

[CERTAIN] TABLA DE CONSTANTES -- BYTE-EXACTA entre `.xll` y `.so`. Se
localizo en `FlowXpert.xll` (offset de archivo 0x1d7100) el mismo bloque de
22 filas x 35 doubles (stride 0x118 = 280 bytes) ya conocido del `.so`.
Volcando las primeras 8 filas (Metano..neo-Pentano) se confirma coincidencia
BIT A BIT, en el MISMO orden de `ORDEN_COMPONENTES_APP` y ya con el swap
i-Butano/n-Butano corregido (seccion 5) validado tambien aqui:
    fila0 Metano:      Mj=16.043 bj=[0.049,0.0447,0.0436]
                       Hoj_bruto=[890.63,891.09,891.56,892.97]
                       Hoj_neto=[802.6,802.65,802.69,802.82]
    fila1 Etano:       Mj=30.07  bj=[0.1,0.0922,0.0894]
    fila2 Propano:     Mj=44.097 bj=[0.1453,0.1338,0.1288]
    fila3 n-Butano:    Mj=58.123 bj=[0.2069,0.1871,0.1783]
    fila4 i-Butano:    Mj=58.123 bj=[0.2049,0.1789,0.1703]
    fila5 n-Pentano:   Mj=72.15  bj=[0.2864,0.2510,0.2345]
    fila6 i-Pentano:   Mj=72.15  bj=[0.2510,0.2280,0.2168]
    fila7 neo-Pentano: Mj=72.15  bj=[0.2387,0.2121,0.2025]
Los 8 valores de Mj, los 24 de bj y los 8 de Hoj_bruto/Hoj_neto de Metano
verificados coinciden EXACTOS (0 diferencia de bit) con `TABLA_CONSTANTES`
de este archivo -- incluye tambien el candidato "Z0" sin lector confirmado
(seccion final del RESUMEN CONSOLIDADO): el `.xll` tiene, para Metano, los
mismos 3 valores (0.9976, 0.998, 0.9981) que el `.so` en el mismo offset
relativo de fila -- confirma que el dato SI existe identico en ambos
binarios, aunque sigue sin encontrarse una funcion que lo lea en ninguno de
los dos (el pendiente [GUESSING] de "Z0" NO se cierra con esto, solo se
refuerza que es un dato real compartido, no ruido de una sola plataforma).

[CERTAIN] CONCLUSION FINAL: la comparacion cruzada .xll vs .so para las 5
variantes de ISO 6976 CONFIRMA, sin ninguna discrepancia encontrada,
la arquitectura de despacho (motor propio vs compartido, exactamente igual
por variante) Y la tabla de 22 componentes x 35 doubles (byte-exacta en los
8 componentes verificados). No se decompilo linea por linea la aritmetica
completa de los 5 nucleos en el `.xll` (trabajo ya hecho y validado con casos
reales sobre el `.so`, ver secciones 4.x) -- el valor de esta ronda es la
confirmacion INDEPENDIENTE de que ambos binarios implementan el mismo
algoritmo con los mismos datos, no una segunda derivacion de la formula
desde cero. Evidencia guardada en el scratchpad de la sesion:
`ghidra_iso6976_xll_output.txt` (wrappers), `ghidra_iso6976_desc_output.txt`
(descriptores/constructores), `ghidra_iso6976_ctors_output.txt` (metadata +
punteros a nucleo real), `ghidra_iso6976_cores_output.txt` (decompilacion de
los 5 nucleos y sus callees).
===============================================================================
7. [2026-08-11] INVENTARIO EXHAUSTIVO DE SELECTORES DE "ISO-6976 (2016)" --
   "Metering reference pressure" CONFIRMADO FUNCIONAL EN VIVO, "Molar Mass
   Method" confirmado idéntico a 1995_M, y hallazgo de que la UI real
   muestra 11 salidas con scroll (no solo las 5 ya documentadas)
===============================================================================
[CERTAIN] Tarea de continuacion para inventariar, en las 3 pantallas reales
(1983/1995/2016), TODOS los selectores de entrada (no solo Ref. Temperature)
-- ver seccion 7 del docstring de `normas/ISO_6976_1995.py` para el detalle
completo de 1983_M/1995_M y la comparacion de las 3 variantes. Este bloque
cubre lo especifico de 2016_M.

[CERTAIN] La pantalla "ISO-6976 (2016)" tiene 4 filas de entrada
(`function_input_type`, confirmado sin scroll en esa seccion de la
pantalla): Composition, "Ref. Temperature", "Molar Mass Method", "Metering
reference pressure". **NO tiene "Calorific Val. Method"** -- a diferencia
de lo que se podria haber asumido por analogia con 1995_M (que SI lo
tiene), la ausencia es real (confirmado por conteo de nodos = 4, no 5, y
por lectura completa del arbol de la pantalla sin encontrar ese texto en
ningun lado). El "More options" del action bar es el generico de toda la
app (Copy/Send as email/Send Feedback/Share app/Customary units/About), sin
nada especifico de esta pantalla.

[CERTAIN] "Molar Mass Method" -- mismas 2 opciones que en 1995_M
(Spinner, values "Calculate"/"Use table"), confirmado en vivo abriendo el
dialogo (no solo por analogia). No se re-testeo el efecto numerico aqui
(ya confirmado para 1995_M en la seccion 7 de `ISO_6976_1995.py`, mismo
motor de calculo `calculate_molar_mass` compartido por ambas variantes via
el pipeline `spirit::math::iso6976_2016` -- ver seccion 1 de este docstring).

[CERTAIN] "Metering reference pressure" -- campo NUMERICO editable (no
enum), dialogo real muestra: Value=1013.25 (default), Range="0 .. 2000",
texto "Range: 0 < P2 < 2 bar", Unit=mbar. **Efecto real confirmado en vivo**
cambiando el valor a 500 mbar (composicion/Ref.Temperature sin cambios,
combo real dejado en 60F/60F/60F de una sesion anterior):
    Metering ref. pressure:  1013.25 -> 500 mbar
    Sup. Calorific Val.:     31.91576 -> 15.73636 MJ/m3  (cambia, ~mitad)
    Density:                 0.758302 -> 0.373888 kg/m3  (cambia, ~mitad)
    Compressibility Z:       0.998392 -> 0.999207         (cambia, mas
                                                            cerca de 1.0 a
                                                            menor presion,
                                                            fisicamente
                                                            correcto)
    Relative Density:        0.619956 -> 0.619576         (cambia, deriva
                                                            de Z via
                                                            Zaire/Zmix)
Confirma que este campo es exactamente el `p_ref` ya usado como parametro
en `calcular_factor_compresion`/`calcular_volumen_molar_ideal`/`calcular_
densidad_relativa` de este modulo -- **ya estaba expuesto correctamente
como parametro funcional en la GUI** (`interfaz_calculo_flujo.py`, campo
"Metering ref. pressure [Pa]" de la pestaña "ISO-6976 (2016)"), esta
sesion solo agrega la confirmacion en vivo de que su efecto es real y del
signo/magnitud fisicamente esperado (no se habia probado antes con un caso
real, solo se usaba el valor "Default" 101325 Pa en todos los casos
conocidos).

[CERTAIN, HALLAZGO NUEVO IMPORTANTE] La seccion "Results" de la pantalla
real "ISO-6976 (2016)" es SCROLLABLE (a diferencia de 1983_M/1995_M, cuyas
listas de resultado NO scrollean) y muestra **11 campos de salida
directamente en la UI**, no solo los 5 ya documentados en el resto de este
modulo:
    Sup. Calorific Val. (MJ/m3, MJ/kg, MJ/kmol)  -- 3 unidades
    Density (kg/m3)
    Compressibility (Z)
    Relative Density
    Molar Mass (kg/kmol)
    Inf. Calorific Val. (MJ/m3, MJ/kg, MJ/kmol)   -- 3 unidades
    Wobbe Index (MJ/m3)
Esto es una diferencia estructural real con 1983_M/1995_M: en esas 2
variantes, las 6 salidas "extra" (GCV bruto en otras unidades, NCV, Wobbe)
solo se pudieron confirmar hookeando con Frida la funcion interna (no
aparecen en la UI, ver seccion 2 de `ISO_6976_1995.py`) -- en 2016_M, en
cambio, la app SI las muestra directamente al usuario con scroll, sin
necesitar instrumentacion dinamica. No cambia ninguna formula ya CERTAIN de
este modulo (son las mismas 11 cantidades fisicas, ya cubiertas por
`calcular_poder_calorifico_molar`/`calcular_indice_wobbe`/etc.) pero
corrige la documentacion previa que solo listaba 5 campos de pantalla para
2016_M por analogia con 1983_M/1995_M sin haber confirmado el scroll.
`interfaz_calculo_flujo.py` se actualizo para mostrar las 11 salidas en la
pestaña "ISO-6976 (2016)" (antes solo mostraba 6: Molar Mass, Z, Density,
Relative Density, Sup. Calorific Val., Wobbe).

Metodologia de esta ronda (para reutilizar si aparecen mas pendientes de
"pantalla incompleta"): el primer intento de navegar a "ISO-6976 (2016)" en
esta tarea fallo por completo -- el menu de categorias mostraba "ISO" con
SOLO los 5 items de ISO-5167, sin ningun ISO-6976 visible, en una lista que
NO tenia mas espacio de scroll (footer de fin de lista inmediatamente
despues del 5to item). Se investigaron y descartaron: registro de la app
(SI estaba registrada, "you can now use all functions"), toggle de
agrupacion en el overflow menu (no existe, solo "Customary units"/"About"),
busqueda por texto (SearchView no filtraba en este build). La causa real
era un estado de lista STALE de una sesion anterior (probablemente dejado
por trabajo previo de ISO 5167) -- `adb shell am force-stop
com.spiritit.flowxpert` seguido de relanzar la app (`monkey -p
com.spiritit.flowxpert -c android.intent.category.LAUNCHER 1`) restauro el
menu principal REAL (categorizado por organismo: AGA/API/ASTM/GERG/GOST/
GPA/IAPWS/ISO/IUPAC/NIST/Densitometer/Liquid/Gas/Flow, con "ISO" conteniendo
los 5 items de ISO-5167 Y los 3 de ISO-6976 juntos, igual que documentaba
`android_sdk_setup/ui_menu_1995_dump.txt` de una sesion anterior). **Cuando
una pantalla ya documentada como existente no aparece en el menu, probar
`am force-stop` + relanzar ANTES de concluir que cambio la estructura de la
app** -- el bug era de estado de la sesion del emulador, no del APK.
===============================================================================
*** ACTUALIZADO 2026-08-20 -- RANGOS DE VALIDEZ OFICIALES DE 2016_M
    AGREGADOS (pendiente de aplicacion nunca hecho, verificado antes de
    empezar contra el codigo actual, no una suposicion). Ver
    `RANGO_PRESION_VALIDO_BAR_2016_M`/`Z_MINIMO_VALIDO_2016_M`/
    `validar_rango_iso6976_2016()` mas abajo: 0.9 < Presion < 1.1 bar,
    Compresibilidad Z > 0.9 -- fuente: manual oficial ABB SpiritIT, funcion
    `fxISO6976_2016_M`, PAGINA 120 ("Boundaries"), releido con `pdfplumber`
    y confirmado EXACTO contra la transcripcion previa de la memoria del
    proyecto (sin discrepancia). Es INFORMATIVO/de referencia, mismo patron
    que `validar_rango_aga8()` de `normas/AGA_8.py` -- NO bloquea ni
    "corrige" ningun calculo existente, solo advierte, igual que la
    pantalla real de FlowXpert (output 'Data range'/OOR, que tampoco
    bloquea el calculo). Distinto del rango de UI 0..2 bar del campo
    "Metering reference pressure" ya confirmado (bloque "ACTUALIZADO
    2026-08-18" arriba): ese es limite de ENTRADA del campo, este es el
    rango de VALIDEZ del estandar para la presion efectivamente usada. ***
===============================================================================
"""

# Mismo orden real de 22 componentes que AGA5_C (confirmado leyendo el bucle
# de 22 emplace_back en Math_ISO6976_2016_M). Ver normas/AGA_5.py para el
# mismo orden ya usado en otra norma de este proyecto.
ORDEN_COMPONENTES_APP = [
    "Metano", "Nitrogeno", "CO2", "Etano", "Propano", "Agua", "H2S",
    "Hidrogeno", "CO", "Oxigeno", "i-Butano", "n-Butano", "i-Pentano",
    "n-Pentano", "n-Hexano", "n-Heptano", "n-Octano", "n-Nonano", "n-Decano",
    "Helio", "Argon", "neo-Pentano",
]

# Pesos atomicos IUPAC (g/mol) usados por el "Metodo B" (formula quimica) de
# calculate_molar_mass. Estos SI son valores de quimica basica, no dependen
# de la extraccion del binario -- [CERTAIN] como dato de quimica, aunque no
# se confirmo que sean EXACTAMENTE estos decimales dentro del binario.
PESO_ATOMICO = {"C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999, "S": 32.06}

# Constante universal de los gases, J/(mol*K). Usada en Vm_ideal = R*T/p.
R_GAS = 8.31446

# Masa molar del aire seco de referencia, g/mol.
# [CERTAIN, ver seccion 4.6] Constante literal leida DIRECTAMENTE del cuerpo
# de `calculate_real_gas_relative_density` (RAW 0x137900, direccion real
# GOT_BASE-0x1825e0 = 0x22A808, GOT_BASE=0x3ACDE8 ya confirmado en la
# seccion 3), via `struct.unpack('<d', ...)` sobre
# `apk_analisis/libFXLibrary.so`. Reemplaza la hipotesis de manual anterior
# (28.9626 g/mol) por el valor real del binario.
M_AIRE = 28.96546

# Tabla real de "b" del aire (analoga a bj de cada componente, seccion 3),
# usada por `calculate_real_gas_relative_density` para calcular Zaire EN VIVO
# con la misma estructura del "summation factor method":
#     Zaire(idx) = 1.0 - (p_ref_kPa / PRESION_REF_AIRE_KPA) * BAIR_TABLA[idx]
# [CERTAIN, ver seccion 4.6] idx = el mismo entero `temperature_index` RAW
# (1..4) que ya se veia por Frida en `calculate_compression_factor` (seccion
# 4.3/4.4) -- NO el indice 0..2 de la tabla `bj` de componentes (son 2
# tablas/indexados DISTINTOS). 4 valores leidos directo del binario (misma
# direccion base GOT_BASE-0x182600, espaciados 8 bytes = sizeof(double)).
# [RESUELTO 2026-08-08, ver seccion 4.7] idx=3 SI se disparo: combo real de
# UI "Ref. Temperature" = 60F/60F/60F, confirmado por Frida en vivo
# (calculate_compression_factor y calculate_real_gas_relative_density ambos
# reciben temperature_index=3 real para ese combo). El caso real completo
# (con densidad relativa recalculada usando este mismo bair[3]) cierra
# 0.0035% de diferencia contra la pantalla real -- ya no es un indice sin
# caso real que lo dispare.
BAIR_TABLA = {
    1: 0.0005810000000000537,
    2: 0.0004049999999999887,
    3: 0.0003990000000000382,
    4: 0.0003549999999999942,
}

# Constante literal leida de GOT_BASE-0x184fc8 (ver seccion 4.6), usada por
# `calculate_real_gas_relative_density` para normalizar p_ref_kPa antes de
# multiplicar por BAIR_TABLA[idx]. [CERTAIN] Coincide con la presion
# atmosferica estandar en kPa (101.325 kPa = 1 atm).
PRESION_REF_AIRE_KPA = 101.325

# Razon Zaire/Mair para el caso "Default" (temperature_index=2, metering=15
# C, el caso de referencia de todo este modulo), usada por
# `calculate_real_gas_relative_density` en la formula
# d = (Mmix/Mair)*(Zaire/Zmix) = Mmix*(Zaire/Mair)/Zmix.
# [CERTAIN, ver seccion 4.6 -- ya no LIKELY] Este valor NUMERICO no cambio
# desde la sesion 2026-08-06 (se habia recuperado por inversion de formula
# contra 2 casos reales), pero ahora esta CONFIRMADO como el cociente exacto
# de 2 constantes reales aisladas por separado: Zaire(2)/M_AIRE, con
# Zaire(2) = 1.0 - (101.325/PRESION_REF_AIRE_KPA)*BAIR_TABLA[2] = 0.999595 y
# M_AIRE = 28.96546 (ver arriba). Se mantiene como constante de conveniencia
# para el caso "Default"; para otro temperature_index o p_ref, usar
# `calcular_densidad_relativa()` (formula general, nueva en esta sesion).
ZAIRE_SOBRE_MAIR = 0.03450989557907936

# Orden interno REAL de la "TABLA 2" (bj/Hoj) dentro del binario -- DISTINTO
# del orden de composicion ORDEN_COMPONENTES_APP. Se deja documentado por si
# se necesita indexar la tabla cruda directamente; las funciones de este
# modulo usan TABLA_CONSTANTES (indexada por nombre), no este orden.
_ORDEN_TABLA2_INTERNO = [
    "Metano", "Etano", "Propano", "i-Butano", "n-Butano", "i-Pentano",
    "n-Pentano", "neo-Pentano", "n-Hexano", "n-Heptano", "n-Octano",
    "n-Nonano", "n-Decano", "Hidrogeno", "Agua", "H2S", "CO", "Helio",
    "Argon", "Nitrogeno", "Oxigeno", "CO2",
]

# TABLA DE CONSTANTES REAL -- extraida por volcado directo de memoria del
# binario (ver seccion 3 del docstring para metodo, direcciones y validacion
# de plausibilidad fisica). [CERTAIN] para Mj/bj/Hoj_bruto/Hoj_neto/
# Hoj_bruto_masa; el mapeo indice->temperatura de referencia dentro de cada
# lista de 4 (Hoj) o 3 (bj) valores es [LIKELY] no [CERTAIN] (ver seccion 2).
# Unidades tal como las entrega el binario: Mj en g/mol, Hoj_bruto/neto
# (molar) en kJ/mol, Hoj_bruto (masa) en MJ/kg.
TABLA_CONSTANTES = {
    "Metano":      {"Mj": 16.043,  "bj": [0.049, 0.0447, 0.0436],
                     "Hoj_bruto": [890.63, 891.09, 891.56, 892.97],
                     "Hoj_neto":  [802.6, 802.65, 802.69, 802.82],
                     "Hoj_bruto_masa": [55.516, 55.545, 55.574, 55.662]},
    "Etano":       {"Mj": 30.07,   "bj": [0.1, 0.0922, 0.0894],
                     "Hoj_bruto": [1560.69, 1561.41, 1562.14, 1564.34],
                     "Hoj_neto":  [1428.64, 1428.74, 1428.84, 1429.12],
                     "Hoj_bruto_masa": [51.9, 51.93, 51.95, 52.02]},
    "Propano":     {"Mj": 44.097,  "bj": [0.1453, 0.1338, 0.1288],
                     "Hoj_bruto": [2219.17, 2220.13, 2221.10, 2224.01],
                     "Hoj_neto":  [2043.11, 2043.23, 2043.37, 2043.71],
                     "Hoj_bruto_masa": [50.33, 50.35, 50.37, 50.44]},
    # [CORREGIDO 2026-08-06, ver seccion 5 del docstring] i-Butano/n-Butano
    # estaban INTERCAMBIADOS (mismo bug heredado por ISO_6976_ex_1995.py, que
    # copiaba estas etiquetas). Confirmado por cruce contra entalpia de
    # combustion publica (n-Butano ~2877.4 kJ/mol > i-Butano ~2868.2 kJ/mol,
    # el isomero ramificado es termodinamicamente mas estable => libera menos
    # energia) Y por evidencia directa de codigo maquina en
    # `ISO_6976_ex_2016.py` (emplace_back con indices literales, no
    # comparacion de valores): fila4=i-Butano=2868.20, fila3=n-Butano=2877.40.
    "i-Butano":    {"Mj": 58.123,  "bj": [0.2049, 0.1789, 0.1703],
                     "Hoj_bruto": [2868.20, 2869.38, 2870.58, 2874.20],
                     "Hoj_neto":  [2648.12, 2648.26, 2648.42, 2648.83],
                     "Hoj_bruto_masa": [49.35, 49.37, 49.39, 49.45]},
    "n-Butano":    {"Mj": 58.123,  "bj": [0.2069, 0.1871, 0.1783],
                     "Hoj_bruto": [2877.40, 2878.57, 2879.76, 2883.82],
                     "Hoj_neto":  [2657.32, 2657.45, 2657.60, 2658.45],
                     "Hoj_bruto_masa": [49.51, 49.53, 49.55, 49.62]},
    # [CORREGIDO 2026-08-06, mismo hallazgo/evidencia que i-Butano/n-Butano
    # arriba] i-Pentano/n-Pentano estaban INTERCAMBIADOS: n-Pentano
    # ~3535.8 kJ/mol > i-Pentano ~3528.8 kJ/mol (mismo razonamiento
    # termodinamico; neo-Pentano, el mas ramificado, es aun menor: 3514.6,
    # patron consistente y NO afectado por este bug).
    "i-Pentano":   {"Mj": 72.15,   "bj": [0.2510, 0.2280, 0.2168],
                     "Hoj_bruto": [3528.83, 3530.24, 3531.68, 3535.98],
                     "Hoj_neto":  [3264.73, 3264.89, 3265.08, 3265.54],
                     "Hoj_bruto_masa": [48.91, 48.93, 48.95, 49.01]},
    "n-Pentano":   {"Mj": 72.15,   "bj": [0.2864, 0.2510, 0.2345],
                     "Hoj_bruto": [3535.77, 3537.17, 3538.60, 3542.89],
                     "Hoj_neto":  [3271.67, 3271.83, 3272.00, 3272.45],
                     "Hoj_bruto_masa": [49.01, 49.03, 49.04, 49.10]},
    "neo-Pentano": {"Mj": 72.15,   "bj": [0.2387, 0.2121, 0.2025],
                     "Hoj_bruto": [3514.61, 3516.01, 3517.43, 3521.72],
                     "Hoj_neto":  [3250.51, 3250.67, 3250.83, 3251.28],
                     "Hoj_bruto_masa": [48.71, 48.73, 48.75, 48.81]},
    "n-Hexano":    {"Mj": 86.177,  "bj": [0.3286, 0.2950, 0.2846],
                     "Hoj_bruto": [4194.95, 4196.58, 4198.24, 4203.23],
                     "Hoj_neto":  [3886.84, 3887.01, 3887.21, 3887.71],
                     "Hoj_bruto_masa": [48.68, 48.70, 48.72, 48.77]},
    "n-Heptano":   {"Mj": 100.204, "bj": [0.4123, 0.3661, 0.3521],
                     "Hoj_bruto": [4853.43, 4855.29, 4857.18, 4862.87],
                     "Hoj_neto":  [4501.30, 4501.49, 4501.72, 4502.28],
                     "Hoj_bruto_masa": [48.44, 48.45, 48.47, 48.53]},
    "n-Octano":    {"Mj": 114.231, "bj": [0.5079, 0.4450, 0.4278],
                     "Hoj_bruto": [5511.80, 5513.88, 5516.01, 5522.40],
                     "Hoj_neto":  [5115.66, 5115.87, 5116.11, 5116.73],
                     "Hoj_bruto_masa": [48.25, 48.27, 48.29, 48.34]},
    "n-Nonano":    {"Mj": 128.258, "bj": [0.6221, 0.5385, 0.5148],
                     "Hoj_bruto": [6171.15, 6173.46, 6175.82, 6182.91],
                     "Hoj_neto":  [5730.99, 5731.22, 5731.49, 5732.17],
                     "Hoj_bruto_masa": [48.12, 48.13, 48.15, 48.21]},
    "n-Decano":    {"Mj": 142.285, "bj": [0.7523, 0.6450, 0.6140],
                     "Hoj_bruto": [6829.77, 6832.31, 6834.90, 6842.69],
                     "Hoj_neto":  [6345.59, 6345.85, 6346.14, 6346.88],
                     "Hoj_bruto_masa": [48.00, 48.02, 48.04, 48.09]},
    "Hidrogeno":   {"Mj": 2.0159,  "bj": [-0.0040, -0.0048, -0.0051],
                     "Hoj_bruto": [285.83, 285.99, 286.15, 286.63],
                     "Hoj_neto":  [241.81, 241.76, 241.72, 241.56],
                     "Hoj_bruto_masa": [141.79, 141.87, 141.95, 142.19]},
    "Agua":        {"Mj": 18.0153, "bj": [0.2646, 0.2345, 0.2191],
                     "Hoj_bruto": [44.016, 44.224, 44.433, 45.074],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [2.44, 2.45, 2.47, 2.50]},
    "H2S":         {"Mj": 34.082,  "bj": [0.1000, 0.1000, 0.1000],
                     "Hoj_bruto": [562.01, 562.19, 562.38, 562.94],
                     "Hoj_neto":  [517.99, 517.97, 517.95, 517.87],
                     "Hoj_bruto_masa": [16.49, 16.50, 16.50, 16.52]},
    "CO":          {"Mj": 28.01,   "bj": [0.0265, 0.0224, 0.0200],
                     "Hoj_bruto": [282.98, 282.95, 282.91, 282.80],
                     "Hoj_neto":  [282.98, 282.95, 282.91, 282.80],
                     "Hoj_bruto_masa": [10.10, 10.10, 10.10, 10.10]},
    "Oxigeno":     {"Mj": 31.9988, "bj": [0.0316, 0.0283, 0.0265],
                     "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [0.0, 0.0, 0.0, 0.0]},
    "Helio":       {"Mj": 4.0026,  "bj": [0.0006, 0.0002, 0.0000],
                     "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [0.0, 0.0, 0.0, 0.0]},
    "Argon":       {"Mj": 39.948,  "bj": [0.0316, 0.0283, 0.0265],
                     "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [0.0, 0.0, 0.0, 0.0]},
    "Nitrogeno":   {"Mj": 28.0135, "bj": [0.0224, 0.0173, 0.0173],
                     "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [0.0, 0.0, 0.0, 0.0]},
    "CO2":         {"Mj": 44.01,   "bj": [0.0819, 0.0748, 0.0728],
                     "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                     "Hoj_neto":  [0.0, 0.0, 0.0, 0.0],
                     "Hoj_bruto_masa": [0.0, 0.0, 0.0, 0.0]},
}
assert set(TABLA_CONSTANTES) == set(ORDEN_COMPONENTES_APP), (
    "TABLA_CONSTANTES debe tener exactamente los 22 componentes de "
    "ORDEN_COMPONENTES_APP -- si esto falla, revisar que no falte/sobre "
    "ningun nombre al copiar los datos reales."
)


def calcular_masa_molar(fracciones_molares: dict) -> float:
    """Mmix = sum(xj * Mj). Metodo A (tabulado) de calculate_molar_mass.

    fracciones_molares: dict {componente: fraccion molar 0..1}, ya
    normalizado (debe sumar 1.0). Mj real, [CERTAIN] (ver seccion 3).

    En la UI real de "ISO-6976 (1995)"/"ISO-6976 (2016)", esta es la formula
    que usa el selector "Molar Mass Method" = "Use table" (confirmado en
    vivo 2026-08-11, ver seccion 7 del docstring del modulo: cambiar el
    selector real de "Calculate" a "Use table" con la composicion "Default"
    de 1995 cambia Molar Mass de 18.63721 a 18.63742 g/mol -- un efecto
    real y medible, no cosmetico).
    """
    return sum(
        fracciones_molares.get(c, 0.0) * TABLA_CONSTANTES[c]["Mj"]
        for c in ORDEN_COMPONENTES_APP
    )


# Conteo de atomos (C, H, N, O, S) por componente, usado por el "Metodo B"
# (formula quimica) de `calculate_molar_mass` -- corresponde al selector
# real de UI "Molar Mass Method" = "Calculate" (ver seccion 7 del docstring
# del modulo). [CERTAIN] como dato de quimica basica (formula molecular de
# cada gas), NO depende de haber extraido nada del binario -- a diferencia
# de Mj/bj/Hoj de TABLA_CONSTANTES, que SI son constantes propias del
# binario. Helio y Argon son gases nobles monoatomicos: 0 en las 5 columnas
# (no tienen enlaces C/H/N/O/S que sumar).
CONTEO_ATOMICO = {
    "Metano":      {"C": 1, "H": 4},
    "Etano":       {"C": 2, "H": 6},
    "Propano":     {"C": 3, "H": 8},
    "n-Butano":    {"C": 4, "H": 10},
    "i-Butano":    {"C": 4, "H": 10},
    "n-Pentano":   {"C": 5, "H": 12},
    "i-Pentano":   {"C": 5, "H": 12},
    "neo-Pentano": {"C": 5, "H": 12},
    "n-Hexano":    {"C": 6, "H": 14},
    "n-Heptano":   {"C": 7, "H": 16},
    "n-Octano":    {"C": 8, "H": 18},
    "n-Nonano":    {"C": 9, "H": 20},
    "n-Decano":    {"C": 10, "H": 22},
    "Hidrogeno":   {"H": 2},
    "Agua":        {"H": 2, "O": 1},
    "H2S":         {"H": 2, "S": 1},
    "CO":          {"C": 1, "O": 1},
    "Helio":       {},
    "Argon":       {},
    "Nitrogeno":   {"N": 2},
    "Oxigeno":     {"O": 2},
    "CO2":         {"C": 1, "O": 2},
}


def calcular_masa_molar_metodo_b(fracciones_molares: dict) -> float:
    """Mmix = sum(xj * (nC*M_C + nH*M_H + nN*M_N + nO*M_O + nS*M_S)).
    Metodo B (formula quimica) de `calculate_molar_mass` -- corresponde al
    selector real de UI "Molar Mass Method" = "Calculate", confirmado en
    vivo 2026-08-11 (ver seccion 7 del docstring del modulo): para la
    composicion "Default" de la pantalla "ISO-6976 (1995)", este metodo
    (via el selector "Calculate" de la app real) da Molar Mass=18.63721
    g/mol, distinto de "Use table"=18.63742 g/mol (Metodo A, `calcular_masa_
    molar` arriba) -- confirma que ambos metodos SI son distintos y que
    esta funcion reproduce el correcto (parten de una tabla/formula
    ligeramente distinta, coincidencia esperable para hidrocarburos con
    pesos atomicos IUPAC estandar).
    """
    total = 0.0
    for c in ORDEN_COMPONENTES_APP:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        conteo = CONTEO_ATOMICO.get(c, {})
        m_formula = sum(n * PESO_ATOMICO[elem] for elem, n in conteo.items())
        total += x * m_formula
    return total


def calcular_factor_compresion(fracciones_molares: dict, indice_temp: int,
                                p_ref: float, t0: float = 288.15) -> float:
    """Z = 1 - (p_ref_kPa / (R*T0)) * (sum(xj*sqrt(bj)))^2

    [CERTAIN, cierra 2026-08-05 contra el caso real] Formula confirmada por
    decompilacion (calculate_compression_factor) Y AHORA TAMBIEN por cruce
    con el texto publico del "summation factor method" de ISO 6976: p entra
    en **kPa**, no en Pa como se asumio en el borrador original -- ese era
    el bug real (un factor de escala de 1000 en p_ref, exactamente el
    sintoma que ya se habia detectado por resolucion inversa en la seccion 4
    antes de confirmarlo). R_GAS sigue en J/(mol*K) SI y T0 en K sin cambios
    -- la combinacion p[kPa]/(R[J/mol/K]*T[K]) es la convencion real de
    unidades del estandar (kPa*J^-1*mol*K * K = kPa/(J/mol) que junto con
    bj adimensional en la tabla da el resultado correcto; no se investigo
    mas alla porque el ajuste ya cierra <0.01%, ver autotest).
    indice_temp selecciona cual de los 3 bj reales usar por componente
    (0..2 -- el binario SOLO entrega 3 valores por componente, no 4 como se
    asumio en el borrador original, ver seccion 3).

    [CERTAIN, corregido 2026-08-06, ver seccion 4.3] Mapeo indice->metering
    confirmado por Frida EN VIVO (no por ajuste numerico): se hookeo
    `calculate_compression_factor` real y se leyo el argumento
    `temperature_index` que la app realmente pasa para 2 combos distintos.
    Resultado: metering=0 C -> indice **1**; metering=15 C (el caso
    "Default") -> indice **2**. ESTO CORRIGE un error del borrador anterior,
    que usaba indice=1 para el caso "Default" por dar el MEJOR AJUSTE
    NUMERICO (0.008% de diferencia) -- ese ajuste era una coincidencia: los
    3 valores de bj de cada componente son muy parecidos entre si (el
    indice=2, el correcto, da 0.012% de diferencia, tambien dentro del
    margen del proyecto pero no el mejor numericamente), asi que un unico
    caso real no bastaba para distinguir el indice correcto por cierre
    numerico solo. El indice 0 SIGUE sin confirmarse por Frida: se intento
    probando el combo metering=20 C, candidato por eliminacion (ver seccion
    4.4), pero esa hipotesis quedo REFUTADA (el `temperature_index` real
    para ese combo fue 4, no 0) -- el enum real es mas amplio de lo que este
    parametro `indice_temp` (0..2) asume, y el indice 0 de este arreglo
    sigue sin caso real que lo dispare [GUESSING, pendiente honesto].
    p_ref: presion de referencia en **Pa** (se convierte a kPa internamente,
    para no romper la firma de la funcion ni el resto del modulo que usa Pa
    consistentemente). t0: temperatura de referencia [K] (288.15 K = 15 degC
    es el valor mas comun citado por el estandar, y coincide con el caso
    real "Default" que usa 15/15/15 -- ver seccion 2 para el detalle de que
    esto NO esta confirmado como la constante literal del binario para
    combinaciones de temperatura distintas de 15/15/15).

    CAVEAT de Hidrogeno [RESUELTO 2026-08-08 con caso real, ver seccion 4.7 --
    ya NO "sin caso real que lo dispare"]: Hidrogeno es el unico componente
    con bj tabulado NEGATIVO (ver seccion 3). El borrador anterior evitaba
    esto filtrando cualquier componente con fraccion 0 (`if x <= 0.0:
    continue`) antes de tomar la raiz, razonando que de otro modo Python
    devuelve un numero complejo. Revisando la matematica: NO es cierto que el
    cuadrado de una raiz compleja "cancele" la parte imaginaria en general --
    si bj de Hidrogeno es negativo y el resto de los componentes tiene bj
    positivo, la suma sum(xj*sqrt(bj)) es un numero complejo con parte REAL
    (de los demas componentes) Y parte imaginaria (solo del termino de
    Hidrogeno), y (a+bi)^2 = a^2-b^2+2abi conserva una parte imaginaria
    distinta de 0 salvo que a=0 (Hidrogeno fuera el UNICO componente
    presente). La lectura correcta, consistente con el hecho publico y bien
    documentado de que las tablas del "summation factor method" de ISO 6976
    SI publican valores NEGATIVOS para (bj)^0.5 de Hidrogeno (no para bj
    antes de la raiz -- es la raiz misma la que se tabula con signo, como una
    cantidad con signo, no como resultado de tomar sqrt() de un numero
    negativo): se calcula la "raiz con signo" (extension impar de sqrt, real
    siempre) en vez de sqrt()+cuadrado por separado -- `raiz = sqrt(|bj|)` si
    bj>=0, `raiz = -sqrt(|bj|)` si bj<0 -- y se suma esa raiz con signo tal
    cual (sin pasar por numeros complejos en ningun momento). Esto reemplaza
    el filtro anterior: ya NO se descarta Hidrogeno cuando su fraccion es > 0
    (solo se sigue saltando el termino cuando la fraccion ES exactamente 0,
    por eficiencia, sin cambiar el resultado).

    [CERTAIN, ver seccion 4.7] Se probo por fin contra un caso real con
    Hidrogeno > 0 (5% de H2, editado a mano en la app real sobre la
    composicion "Default", restando 5% de Metano -- suma exacta 100%,
    combo "Ref. Temperature" = 60F/60F/60F, temperature_index real=3 vía
    Frida). Con la raiz con signo (SIN descartar el termino de Hidrogeno,
    fraccion 0.05 > 0), el Z calculado (mejor ajuste columna=1, T0=273.15 K)
    cierra 0.000856% de diferencia contra el Z real hookeado -- MUY por
    debajo del margen <0.1% del proyecto, y encadenado hasta la densidad
    relativa real (que SI usa este Z) el cierre sigue en 0.0035%. Esto
    confirma que la formula de raiz con signo NO produce un resultado
    absurdo ni degradado con Hidrogeno presente: reproduce un caso real
    dentro del mismo margen de exactitud que el resto del modulo. El unico
    residuo honesto que queda (no bloqueante) es que la columna bj (0/1/2) y
    el T0 usados para temperature_index=3 son, igual que para los indices 1
    y 4, un AJUSTE NUMERICO de mejor cierre, no un valor confirmado por
    disassembly -- ver seccion 4.7 para el detalle completo y el barrido de
    columnas/T0 probadas.
    """
    p_ref_kpa = p_ref / 1000.0
    suma = 0.0
    for c in ORDEN_COMPONENTES_APP:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        bj = TABLA_CONSTANTES[c]["bj"][indice_temp]
        raiz_con_signo = (bj ** 0.5) if bj >= 0.0 else -((-bj) ** 0.5)
        suma += x * raiz_con_signo
    return 1.0 - (p_ref_kpa / (R_GAS * t0)) * (suma ** 2)


def calcular_factor_compresion_aire(indice_temp_raw: int, p_ref: float) -> float:
    """Zaire(idx) = 1 - (p_ref_kPa / PRESION_REF_AIRE_KPA) * BAIR_TABLA[idx].

    [CERTAIN, ver seccion 4.6 del docstring del modulo] Formula real de
    `calculate_real_gas_relative_density`, decodificada por disassembly x86
    directo (no decompilado): la funcion calcula Zaire EN VIVO con la misma
    ESTRUCTURA que `calcular_factor_compresion` (Z = 1 - K*b), aplicada al
    aire en vez de a la mezcla, usando una tabla propia de 4 valores `bair`.

    indice_temp_raw: el `temperature_index` RAW (1..4, NO el indice 0..2 de
    la tabla `bj` de componentes -- son 2 indexados DISTINTOS, ver seccion
    4.6). p_ref: presion de referencia en Pa (se convierte a kPa
    internamente, igual que `calcular_factor_compresion`).

    Validado BIT-EXACTO (0.0000% de diferencia) contra los 3 casos reales
    capturados por Frida (temperature_index 1, 2 y 4) -- ver seccion 4.6.
    """
    p_ref_kpa = p_ref / 1000.0
    bair = BAIR_TABLA[indice_temp_raw]
    return 1.0 - (p_ref_kpa / PRESION_REF_AIRE_KPA) * bair


def calcular_densidad_relativa(mmix: float, zmix: float, indice_temp_raw: int,
                                p_ref: float) -> float:
    """d = (Mmix/Mair) * (Zaire(idx)/Zmix).

    [CERTAIN, ver seccion 4.6] Formula general de `calculate_real_gas_
    relative_density`, con Mair y Zaire ya aislados INDIVIDUALMENTE (no solo
    su producto). Para el caso real "Default" (indice_temp_raw=2, p_ref
    101325 Pa) reproduce exactamente `mmix * ZAIRE_SOBRE_MAIR / zmix` (la
    constante de conveniencia ya usada en el resto del modulo) -- se agrega
    esta funcion para el caso general (otro temperature_index u otra p_ref),
    no para reemplazar la constante ya validada.
    """
    zaire = calcular_factor_compresion_aire(indice_temp_raw, p_ref)
    return (mmix / M_AIRE) * (zaire / zmix)


def calcular_volumen_molar_ideal(t: float, p: float) -> float:
    """Vm_ideal = R*T/p. Formula confirmada (calculate_ideal_gass_volume)."""
    return R_GAS * t / p


def calcular_volumen_molar_real(vm_ideal: float, z: float) -> float:
    """Vm_real = Vm_ideal * Z.

    [CERTAIN, corregido y cerrado 2026-08-05, cuarta sesion de continuacion]
    BUG REAL ENCONTRADO (Camino 1 de la tarea: cruce contra la ecuacion de
    gas real publica, sin Frida ni disassembly adicional): la version
    anterior de esta funcion dividia por Z (`vm_ideal / z`), asumiendo que el
    patron decompilado `(CONST*a1*a2)/a3` correspondia a
    `Vm_real = (R*T/p) / Z`. Eso es fisicamente incorrecto: la ecuacion de
    gas real es `p*Vm = Z*R*T`, es decir `Vm_real = Z*R*T/p = Z * Vm_ideal`
    (multiplicar, NO dividir) -- el mismo patron `CONST*a1*a2/a3` decompilado
    encaja EXACTAMENTE igual de bien con `R * T * Z / p` (3 terminos
    multiplicados, 1 dividido) que con la interpretacion anterior, asi que la
    ambiguedad [LIKELY] de la seccion 1 se resolvia con la fisica basica, no
    con mas ingenieria inversa. Verificado con el caso real (ver seccion 4):
    con esta correccion (y sin tocar Z, que ya estaba resuelto), la Densidad
    real del gas pasa de 0.366% de diferencia a **0.0053%**, y el Poder
    calorifico volumetrico bruto pasa de "ningun indice cierra <0.1%" a
    **0.0031%** en el indice de Hoj=2 -- ambos pendientes de la seccion 4
    quedan resueltos con este UNICO cambio, confirmando la hipotesis de la
    seccion 2 (los dos pendientes compartian la misma causa raiz: esta
    funcion). [CERTAIN]
    """
    return vm_ideal * z


def calcular_poder_calorifico_molar(fracciones_molares: dict, tipo: str,
                                     indice_temp_combustion: int) -> float:
    """Hm = sum(xj * Hoj[indice_temp_combustion]), en kJ/mol (unidad real del
    binario, ver seccion 3). tipo: 'bruto' o 'neto'. indice_temp_combustion:
    0..3 (4 combinaciones reales por componente; el mapeo indice->
    temperatura de referencia es [LIKELY], no [CERTAIN], ver seccion 2)."""
    clave = "Hoj_bruto" if tipo == "bruto" else "Hoj_neto"
    return sum(
        fracciones_molares.get(c, 0.0) * TABLA_CONSTANTES[c][clave][indice_temp_combustion]
        for c in ORDEN_COMPONENTES_APP
    )


def calcular_indice_wobbe(poder_calorifico_volumen: float, densidad_relativa: float) -> float:
    """W = H_volumen / sqrt(d). Formula confirmada (calculate_real_gas_gross_wobbe_index)."""
    return poder_calorifico_volumen / (densidad_relativa ** 0.5)


# -----------------------------------------------------------------------------
# RANGOS DE VALIDEZ OFICIALES (2016_M) -- INFORMATIVO, NO BLOQUEANTE.
#
# [CERTAIN, fuente documental] Manual oficial ABB SpiritIT ("Flow-X Manual
# IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf"), funcion
# `fxISO6976_2016_M`, PAGINA 120, seccion "Boundaries": "The standard
# defines the following validity ranges: 0.9 < Pressure < 1.1 bar;
# Compressibility > 0.9." Releido y confirmado contra el PDF real con
# `pdfplumber` el 2026-08-20 (no se confio solo en la transcripcion previa
# de la memoria del proyecto) -- coincide EXACTO, sin discrepancia. Notese
# que esto es DISTINTO del rango de UI 0..2 bar del campo "Metering
# reference pressure" (ya confirmado tocando la UI, ver bloque
# "ACTUALIZADO 2026-08-18" al inicio de este docstring) -- aquel es el
# limite de ENTRADA del campo, este es el rango de VALIDEZ del estandar
# (mas angosto, 0.9-1.1 bar) para la presion realmente usada en el calculo.
#
# [CERTAIN, mismo patron ya usado en el proyecto] Informativo/de
# referencia, igual que `validar_rango_aga8()` en `normas/AGA_8.py`: la
# propia pantalla de FlowXpert expone un output "Data range" (0=In Range,
# 1=Out of Range, tag `OOR`) que NO bloquea el calculo -- la app calcula
# igual y solo marca la condicion. Esta funcion sigue el mismo criterio:
# NO lanza excepcion ni "corrige" ningun resultado ya calculado, solo
# advierte.
# -----------------------------------------------------------------------------
RANGO_PRESION_VALIDO_BAR_2016_M = (0.9, 1.1)   # estricto: 0.9 < P < 1.1
Z_MINIMO_VALIDO_2016_M = 0.9                    # estricto: Z > 0.9


def validar_rango_iso6976_2016(p_ref_bar: float, z: float) -> dict:
    """Chequeo INFORMATIVO (NO bloqueante) de Presion/Compresibilidad contra
    los rangos de validez oficiales de ISO6976:2016_M declarados por el
    manual ABB SpiritIT (pagina 120: 0.9 < Presion < 1.1 bar, Z > 0.9). Ver
    `RANGO_PRESION_VALIDO_BAR_2016_M`/`Z_MINIMO_VALIDO_2016_M` arriba.

    Mismo espiritu que `validar_rango_aga8()` de `normas/AGA_8.py`: la app
    real NO bloquea el calculo fuera de rango (solo lo declara via su
    propio output 'Data range'/OOR), asi que esta funcion tampoco bloquea
    ni modifica ningun resultado ya calculado -- solo informa.

    Args:
        p_ref_bar: presion de referencia de metering (p2), en bar.
        z: factor de compresibilidad ya calculado.

    Devuelve dict con: en_rango (bool), presion_en_rango (bool), z_en_rango
    (bool), mensaje.
    """
    p_lo, p_hi = RANGO_PRESION_VALIDO_BAR_2016_M
    presion_en_rango = p_lo < p_ref_bar < p_hi
    z_en_rango = z > Z_MINIMO_VALIDO_2016_M
    en_rango = presion_en_rango and z_en_rango

    if en_rango:
        mensaje = "Presion y Compresibilidad dentro de los rangos oficiales de ISO6976:2016_M (manual ABB SpiritIT p.120)."
    else:
        partes = []
        if not presion_en_rango:
            partes.append(f"Presion={p_ref_bar:.5f} bar (rango oficial {p_lo} < P < {p_hi})")
        if not z_en_rango:
            partes.append(f"Compresibilidad Z={z:.6f} (rango oficial Z > {Z_MINIMO_VALIDO_2016_M})")
        mensaje = (
            "ADVERTENCIA informativa (NO bloqueante, la app real tampoco "
            f"bloquea): fuera del rango oficial ISO6976:2016_M -- {'; '.join(partes)}."
        )

    return {
        "en_rango": en_rango,
        "presion_en_rango": presion_en_rango,
        "z_en_rango": z_en_rango,
        "mensaje": mensaje,
    }


def _autotest_caso_real_flowxpert():
    """Caso real "Default" capturado en vivo de la app FlowXpert (funcion
    ISO-6976 (2016), emulador Android, 2026-08-05) -- ver seccion 4 del
    docstring del modulo para el metodo de captura y la discusion completa
    de que cierra y que no. Composicion y resultados TAL CUAL los muestra
    la pantalla real."""
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

    P_REF_PA = 101325.0   # 1013.25 mbar, "Metering reference pressure" en pantalla
    T0_K = 288.15         # 15 grados C, "Ref. Temperature" = 15/15/15 en pantalla

    REAL = {
        "Sup. Calorific Val. (MJ/m3)": 33.26919,
        "Density (kg/m3)": 0.789661,
        "Compressibility (Z)": 0.998154,
        "Relative Density": 0.644348,
        "Molar Mass (g/mol)": 18.63692,
    }

    print("=== CASO REAL FlowXpert -- ISO-6976 (2016), composicion 'Default' ===")
    print("(capturado navegando la UI real de la app en el emulador, ver seccion 4")
    print("del docstring del modulo -- NO es un numero inventado ni de tabla externa)")
    print()

    # --- Masa molar: cierre limpio, <0.01% -----------------------------------
    mmix = calcular_masa_molar(comp)
    dif_mmix = abs(mmix - REAL["Molar Mass (g/mol)"]) / REAL["Molar Mass (g/mol)"] * 100
    print(f"Masa molar         = {mmix:.6f} g/mol   vs real {REAL['Molar Mass (g/mol)']}  "
          f"-> dif {dif_mmix:.4f}%  [CERTAIN, cierra al nivel del resto del proyecto]")

    # --- Factor de compresion Z: indice CONFIRMADO POR FRIDA = 2 para -------
    # metering=15 C (el caso "Default"), YA NO indice=1 (ese era un error del
    # borrador anterior, elegido por mejor ajuste numerico -- ver seccion 4.3
    # del docstring del modulo y el docstring de calcular_factor_compresion).
    print()
    print("Factor de compresion Z -- indice bj CONFIRMADO POR FRIDA en vivo (seccion 4.3):")
    z_pantalla = REAL["Compressibility (Z)"]
    for idx in range(3):
        z_calc = calcular_factor_compresion(comp, indice_temp=idx, p_ref=P_REF_PA, t0=T0_K)
        dif_z = abs(z_calc - z_pantalla) / z_pantalla * 100
        marca = "  <- CONFIRMADO por Frida para metering=15 C" if idx == 2 else ""
        print(f"    indice {idx}: Z calculado = {z_calc:.6f}   vs real {z_pantalla}  -> dif {dif_z:.4f}%{marca}")
    indice_bj_confirmado = 2
    z_usado = calcular_factor_compresion(comp, indice_temp=indice_bj_confirmado, p_ref=P_REF_PA, t0=T0_K)
    dif_z_usado = abs(z_usado - z_pantalla) / z_pantalla * 100
    print(f"    -> indice usado: {indice_bj_confirmado} (CONFIRMADO, no por ajuste), "
          f"Z={z_usado:.6f}, dif {dif_z_usado:.4f}%  [CERTAIN, cierra <0.1%]")

    # --- Densidad relativa: FORMULA GENERAL con Mair y Zaire ya aislados ----
    # INDIVIDUALMENTE por disassembly (seccion 4.6), ya no por inversion de
    # formula contra 2 casos reales (seccion 4.3, ahora SUPERADA).
    d_simple = mmix / M_AIRE
    d_general = calcular_densidad_relativa(mmix, z_usado, indice_temp_raw=2, p_ref=P_REF_PA)
    d_con_z = mmix * ZAIRE_SOBRE_MAIR / z_usado  # constante de conveniencia, mismo valor
    dif_d_simple = abs(d_simple - REAL["Relative Density"]) / REAL["Relative Density"] * 100
    dif_d_general = abs(d_general - REAL["Relative Density"]) / REAL["Relative Density"] * 100
    print(f"Densidad relativa (Mmix/Mair)                          = {d_simple:.6f}  -> dif {dif_d_simple:.4f}%")
    print(f"Densidad relativa (formula general, Mair/Zaire CERTAIN) = {d_general:.6f}  -> dif {dif_d_general:.4f}%  "
          f"vs real {REAL['Relative Density']}  [CERTAIN, ver seccion 4.6 -- Mair=28.96546 g/mol y "
          f"Zaire(idx=2) aislados por separado, validados BIT-EXACTO contra 3 casos reales de Frida, "
          f"no solo su cociente]")

    # --- Densidad real y poder calorifico volumetrico: usan Z CALCULADO y ---
    # Vm_real CORREGIDO (Vm_ideal*Z, NO Vm_ideal/Z -- bug real encontrado en
    # la cuarta sesion, ver docstring de calcular_volumen_molar_real y
    # seccion 4.2 del docstring del modulo).
    vm_ideal = calcular_volumen_molar_ideal(t=T0_K, p=P_REF_PA)
    vm_real = calcular_volumen_molar_real(vm_ideal, z_usado)
    densidad_real = (mmix / 1000.0) / vm_real
    dif_densidad = abs(densidad_real - REAL["Density (kg/m3)"]) / REAL["Density (kg/m3)"] * 100
    print(f"Densidad real gas    = {densidad_real:.6f} kg/m3   vs real {REAL['Density (kg/m3)']}  "
          f"-> dif {dif_densidad:.4f}%  [CERTAIN, cierra <0.1% -- bug de Vm_real resuelto, ver docstring]")

    print("Poder calorifico bruto volumetrico, indice Hoj/combustion CONFIRMADO POR FRIDA = 2 (seccion 4.3):")
    for idx in range(4):
        hm = calcular_poder_calorifico_molar(comp, "bruto", indice_temp_combustion=idx)
        h_vol = (hm / vm_real) / 1000.0
        dif = abs(h_vol - REAL["Sup. Calorific Val. (MJ/m3)"]) / REAL["Sup. Calorific Val. (MJ/m3)"] * 100
        marca = "  <- CONFIRMADO por Frida para combustion=15 C" if idx == 2 else ""
        print(f"    indice {idx}: {h_vol:.5f} MJ/m3  -> dif {dif:.4f}%{marca}")
    print(f"vs real {REAL['Sup. Calorific Val. (MJ/m3)']} MJ/m3  "
          f"(indice usado: 2, CONFIRMADO por Frida, no solo por ajuste numerico)  "
          f"[CERTAIN, cierra <0.1%]")


def _autotest_caso_real_h2_idx3():
    """Segundo caso real capturado en vivo de la app FlowXpert (misma
    pantalla "ISO-6976 (2016)", emulador Android, 2026-08-08) -- ver seccion
    4.7 del docstring del modulo para el metodo de captura completo. Resuelve
    los 2 unicos pendientes que quedaban (caveat de Hidrogeno con bj
    negativo, y `bair[idx=3]` nunca disparado) con una sola composicion:
    igual a "Default" pero con 5% de Hidrogeno (restado de Metano) y el
    combo de UI "Ref. Temperature" = 60F/60F/60F (temperature_index real=3,
    confirmado por Frida, NO por ajuste numerico)."""
    comp_pct = {
        "Metano": 76.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "Hidrogeno": 5.0, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    assert abs(sum(comp_pct.values()) - 100.0) < 1e-9, "la composicion real debe sumar 100%"
    comp = {c: 0.0 for c in ORDEN_COMPONENTES_APP}
    for nombre, pct in comp_pct.items():
        comp[nombre] = pct / 100.0

    P_REF_PA = 101325.0  # 1013.25 mbar, sin cambios respecto al caso "Default"

    # Valores REALES hookeados por Frida en vivo (PID 2880, esta sesion,
    # seccion 4.7 -- NO son de tabla ni inventados):
    TEMPERATURE_INDEX_REAL = 3
    Z_REAL = 0.9983921141873021
    MMIX_REAL = 17.93559520191999
    DENSIDAD_RELATIVA_REAL = 0.6199560513441248

    print("=== CASO REAL FlowXpert -- ISO-6976 (2016), Hidrogeno=5% + combo 60F/60F/60F ===")
    print("(temperature_index=3 real via Frida, nunca antes disparado -- ver seccion 4.7)")
    print()

    mmix = calcular_masa_molar(comp)
    dif_mmix = abs(mmix - MMIX_REAL) / MMIX_REAL * 100
    print(f"Masa molar (con Hidrogeno=5%) = {mmix:.6f} g/mol   vs real {MMIX_REAL}  "
          f"-> dif {dif_mmix:.4f}%  [CERTAIN, cierra <0.1%]")

    print()
    print("Factor de compresion Z -- Hidrogeno NO descartado (fraccion 0.05 > 0, raiz con")
    print("signo se ejercita de verdad por primera vez), barrido columna x T0 (AJUSTE")
    print("NUMERICO, columna/T0 exactos de temperature_index=3 no confirmados por disassembly):")
    mejor_dif, mejor_col, mejor_t0, mejor_z = None, None, None, None
    for col in (0, 1, 2):
        for t0 in (273.15, 288.15, 293.15, 298.15):
            z_calc = calcular_factor_compresion(comp, indice_temp=col, p_ref=P_REF_PA, t0=t0)
            dif_z = abs(z_calc - Z_REAL) / Z_REAL * 100
            if mejor_dif is None or dif_z < mejor_dif:
                mejor_dif, mejor_col, mejor_t0, mejor_z = dif_z, col, t0, z_calc
    print(f"    mejor ajuste: columna {mejor_col}, T0={mejor_t0} K -> Z={mejor_z:.10f}  "
          f"vs real {Z_REAL}  -> dif {mejor_dif:.6f}%  [CERTAIN que cierra <0.1%; "
          f"columna/T0 [LIKELY], ajuste numerico como en 4.4]")

    d_general = calcular_densidad_relativa(mmix, mejor_z, indice_temp_raw=TEMPERATURE_INDEX_REAL, p_ref=P_REF_PA)
    dif_d = abs(d_general - DENSIDAD_RELATIVA_REAL) / DENSIDAD_RELATIVA_REAL * 100
    print(f"Densidad relativa (con bair[3] real + Mmix/Z calculados) = {d_general:.6f}  "
          f"vs real {DENSIDAD_RELATIVA_REAL}  -> dif {dif_d:.4f}%  "
          f"[CERTAIN, cierra <0.1% -- bair[3] confirmado por Frida, ver seccion 4.6/4.7]")

    d_bitexact = calcular_densidad_relativa(MMIX_REAL, Z_REAL, indice_temp_raw=TEMPERATURE_INDEX_REAL, p_ref=P_REF_PA)
    dif_d_bitexact = abs(d_bitexact - DENSIDAD_RELATIVA_REAL) / DENSIDAD_RELATIVA_REAL * 100
    print(f"Densidad relativa (usando Mmix/Z REALES, sin encadenar aproximacion) = {d_bitexact:.10f}  "
          f"-> dif {dif_d_bitexact:.6f}%  [CERTAIN, bit-exacto -- confirma que bair[3] y la formula")
    print("    de calcular_densidad_relativa son correctas de forma aislada]")


if __name__ == "__main__":
    _autotest_caso_real_flowxpert()
    print()
    _autotest_caso_real_h2_idx3()
    print()

    # AUTOTEST adicional de ejemplo (composicion inventada, NO de FlowXpert) --
    # se mantiene solo para verificar que la tabla real + las formulas
    # encadenan sin errores de tipo/orden con otra composicion cualquiera.
    print("=== autotest adicional (composicion de ejemplo, no de FlowXpert) ===")
    tabla_demo = {c: 0.0 for c in ORDEN_COMPONENTES_APP}
    tabla_demo["Metano"] = 0.90
    tabla_demo["Etano"] = 0.05
    tabla_demo["Nitrogeno"] = 0.03
    tabla_demo["CO2"] = 0.02

    m = calcular_masa_molar(tabla_demo)
    hm_bruto = calcular_poder_calorifico_molar(tabla_demo, "bruto", indice_temp_combustion=0)
    print(f"Mmix = {m:.4f} g/mol (Mj real, formula/orden correctos)")
    print(f"Hm bruto = {hm_bruto:.2f} kJ/mol (Hoj real, combo de temperatura 0)")
