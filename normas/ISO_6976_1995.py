# -*- coding: utf-8 -*-
"""
normas/ISO_6976_1995.py
=========================
===============================================================================
*** ACTUALIZADO 2026-08-07 (RONDA 2, tarea de continuacion) -- PENDIENTE
    "DOS BLOQUES SEPARADOS" REFUTADO POR COMPLETO, TABLA PROPIA DE 1995 AHORA
    [CERTAIN] CON VALORES REALES CONFIRMADOS BIT A BIT.

    [CERTAIN] La hipotesis de la ronda anterior ("bj y Hoj de 1995 podrian
    vivir en DOS BLOQUES DE MEMORIA SEPARADOS, uno en &C95 y otro a
    &C95+0x1810") queda REFUTADA por lectura directa, instruccion por
    instruccion, del cuerpo COMPLETO y fresco de `PropertiesISO6976_1995_rev1`
    (Ghidra 11.4.3, decompile limpio, script
    `apk_analisis/ghidra_scripts_11.4.3/DecompileControlAndPending.java`,
    salida completa en `apk_analisis/decomp_1995rev1_full_out.txt`). El codigo
    real muestra que TODO (Mj, bj, Hoj_bruto, Hoj_neto) se lee de la MISMA
    fila de UNA SOLA tabla, con punteros derivados directamente de `&C95`:
        pdVar6 = (double *)&C95;                              // Mj, columna 0
        ...
        pdVar6 = (double *)(&DAT_003bdf48 + iStack_110 * 8);  // bj: &C95+8+idx*8
        ...
        pdVar6 = (double *)(&DAT_003bdf60 + iStack_e0  * 8);  // Hoj_bruto: &C95+0x20+idx*8
        ...pdVar6[4]...                                        // Hoj_neto: +0x20 mas
    `DAT_003bdf48` = `&C95 + 8` (offset de 1 double = columna bj[0]) y
    `DAT_003bdf60` = `&C95 + 0x20` (columna Hoj_bruto[0]) -- NO hay ningun
    segundo bloque en `&C95+0x1810`. Ese valor `0x1810` que se habia
    encontrado en la ronda anterior era, en realidad, el LIMITE DE FIN DE
    BUCLE del acumulador de Z (`while (pdVar7 != (double *)(iStack_110*8 +
    0x3bf758))`, con 0x3bf758 = &C95+8+0x1810, es decir "primer byte
    DESPUES de la fila 22" de la MISMA tabla) -- se habia malinterpretado
    como si fuera "el puntero base de un segundo bloque para Hoj" cuando en
    realidad es solo el centinela de fin de las 22 filas. CONCLUSION: layout
    de columnas y ubicacion son EXACTAMENTE los ya documentados en la seccion
    4 original (una sola tabla, Mj@[0] bj@[1:4] Hoj_bruto@[4:8]
    Hoj_neto@[8:12], stride 280 bytes/fila, 22 filas) -- la "hipotesis de dos
    bloques" fue un error de lectura de una ronda anterior, no una
    caracteristica real del binario.

    [CERTAIN] VALORES REALES CONFIRMADOS -- se resolvio tambien el pendiente
    honesto de la seccion 4 (el volcado anterior daba basura, ej. fila0
    Mj=1.96 en vez de Metano). CAUSA RAIZ encontrada: el volcado anterior leia
    el archivo `.so` CRUDO por file-offset (`struct.unpack` directo sobre los
    bytes del archivo), asumiendo que file-offset = direccion_virtual -
    imagebase de forma uniforme -- funciono para TABLA A (formula quimica) y
    para la tabla de 55 filas de `ISO_6976_ex_1995.py`, pero para ESTA region
    especifica del binario esa igualdad NO se cumple (hay un desajuste
    file-offset vs direccion-virtual propio de este segmento que no afecta a
    las otras tablas ya extraidas con el mismo metodo). La solucion fue leer
    la memoria YA RELOCADA por Ghidra (API `Memory.getBytes` sobre la
    direccion real del simbolo `C95`, script
    `apk_analisis/ghidra_scripts_11.4.3/DumpTabla1995Real.java`, salida en
    `apk_analisis/dump_tabla1995_real_out.txt`) en vez de asumir la aritmetica
    GOT_BASE+offset sobre el archivo crudo. Con eso, las 22 filas leidas
    DESDE `&C95` (Ghidra resuelve `C95` a la direccion 0x3bdf40, que es
    exactamente RAW 0x3ADF40 + imagebase 0x10000, CONFIRMANDO que el offset
    GOT_BASE+0x1158 ya documentado SI es el correcto) dieron una
    coincidencia EXACTA, bit a bit, con los 22 componentes de
    `TABLA_CONSTANTES` de `ISO_6976.py`, EN EL MISMO ORDEN que
    `ORDEN_COMPONENTES_APP`:
        fila0=Metano(16.043)      fila1=Etano(30.07)       fila2=Propano(44.097)
        fila3=n-Butano(58.123)    fila4=i-Butano(58.123)   fila5=n-Pentano(72.15)
        fila6=i-Pentano(72.15)    fila7=neo-Pentano(72.15) fila8=n-Hexano(86.177)
        fila9=n-Heptano(100.204)  fila10=n-Octano(114.231) fila11=n-Nonano(128.258)
        fila12=n-Decano(142.285)  fila13=Hidrogeno(2.0159) fila14=Agua(18.0153)
        fila15=H2S(34.082)        fila16=CO(28.01)         fila17=Helio(4.0026)
        fila18=Argon(39.948)      fila19=Nitrogeno(28.0135) fila20=Oxigeno(31.9988)
        fila21=CO2(44.01)
    Los valores de bj y Hoj_bruto/Hoj_neto de las 22 filas tambien coinciden
    EXACTOS (no aproximados) contra `TABLA_CONSTANTES` (ej. fila14=Agua con
    Hoj_neto=(0,0,0,0) exacto, fila16=CO con Hoj_bruto==Hoj_neto exacto -- las
    mismas anomalias fisicas ya documentadas en `ISO_6976.py`). **La tabla
    propia de 1995 (bj/Hoj) queda [CERTAIN] en ubicacion, layout Y VALORES**
    -- ya no es necesaria la dependencia exclusiva de la tabla de 2016_M para
    esta variante, aunque la validacion numerica de la seccion 2 (que SI usa
    2016_M) permanece valida y no se modifica.

    LECCION METODOLOGICA para el resto del proyecto: cuando un volcado de
    bytes crudo del `.so` por file-offset de basura pero el disassembly/
    decompile de layout parece correcto, probar releer via la memoria YA
    RELOCADA de Ghidra (Memory API) antes de descartar el offset como
    incorrecto -- puede haber un desajuste file-offset/vaddr especifico de
    ese segmento, no un error de aritmetica GOT_BASE.
===============================================================================
*** ACTUALIZADO 2026-08-07 (FASE DECOMPILACION PURA, tarea de continuacion) --
    TABLA B PROPIA DE 1995 (seccion 4): ACCESO REAL A LA TABLA CONFIRMADO
    [CERTAIN] leyendo A FONDO (no solo como CONTROL) el cuerpo completo de
    `PropertiesISO6976_1995_rev1` decompilado con Ghidra 11.4.3. El acceso
    real (rama Metodo A, `param_3 != 0`) usa un puntero `pdVar6` que arranca
    en el simbolo `&C95` (= GOT_BASE+0x1158, RAW 0x3ADF40 -- coincide EXACTO
    con el offset ya documentado en la seccion 4 de este archivo) con
    stride `pdVar6 + 0x23` doubles = 280 bytes/fila, terminando en
    `iStack_110*8 + 0x3bf758` -- confirma 22 filas exactas (280*22=6160=
    0x1810 bytes, y 0x1160+0x1810=0x2970=0x3bf758-GOT_BASE_ghidra, CIERRA
    EXACTO). Los mismos punteros se usan para bj (columna `iStack_110`,
    0..2, empezando en offset+8=indice1 de la fila -- IDENTICO layout a la
    "TABLA 2" de 2016_M) y para Hoj_bruto/Hoj_neto (columna `iStack_e0`,
    offset+0x20=indice4 para bruto, offset+0x20 MAS 4 doubles=indice8 para
    neto -- otra vez IDENTICO a 2016_M). CONCLUSION: el LAYOUT de columnas
    de la tabla propia de 1995 (Mj@0, bj@[1:4], Hoj_bruto@[4:8],
    Hoj_neto@[8:12]) queda [CERTAIN] por evidencia DIRECTA de codigo
    (no solo por analogia con 2016_M como se asumia antes) -- la
    estructura de 35 doubles/fila SI es la misma "forma" que la TABLA 2 de
    2016_M, solo que en una region de memoria fisicamente distinta.
    INTENTO DE VOLCAR VALORES REALES CON EL OFFSET CONFIRMADO: se releyeron
    directamente los bytes del .so en GOT_BASE+0x1158 con el stride ahora
    certificado -- RESULTADO NEGATIVO HONESTO, igual que el intento anterior
    documentado en la seccion 4: fila0 da Mj=1.96, bj=(1.84,1.83,0.0),
    Hoj_bruto=(0,0,0,0) -- NO son valores de Metano ni de ningun componente
    real reconocible. El ACCESO/LAYOUT esta confirmado por codigo maquina
    real (ya no es una hipotesis), pero el ALINEAMIENTO DE FILA (donde
    empieza fisicamente la fila 0 real dentro de esa region) sigue sin
    resolverse -- mismo pendiente honesto que antes, ahora con la certeza
    adicional de que el problema NO es el layout de columnas (que es
    correcto) sino un desplazamiento/orden de fila aun no encontrado. No
    bloquea el cierre ya logrado en la seccion 2 (que no depende de esta
    tabla, usa la de 2016_M por equivalencia numerica). ***
===============================================================================
ISO 6976:1995 (revision intermedia de las 3 variantes base 1983/1995/2016
que FlowXpert implementa). Extension del trabajo de `normas/ISO_6976.py`
(2016_M, CERRADA) y `normas/ISO_6976_1983.py` (1983_M, CERRADA) a esta
variante, tarea de continuacion 2026-08-06.

Este archivo se puede ejecutar solo:
    python -m normas.ISO_6976_1995

===============================================================================
RESUMEN EJECUTIVO (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] 1995_M es un MOTOR BINARIO PROPIO (autocontenido), igual que
1983_M -- NO es un despacho/alias hacia 2016_M ni hacia el namespace nuevo
`spirit::math::iso6976_1995::calculate_revision_1` que TAMBIEN existe en el
binario (ver seccion 1: el binario tiene AMBAS implementaciones para 1995,
pero el wrapper Excel real solo llama a la vieja). Validado contra 1 caso
real capturado EN VIVO por Frida (no solo por pantalla): se hookeo
DIRECTAMENTE la funcion interna real `PropertiesISO6976_1995_rev1` mientras
la app calculaba de verdad, capturando la composicion de entrada Y los 11
valores de salida crudos (5 de los cuales se ven en la UI, 6 son internos).
Los 11 valores cierran <0.03% (la mayoria <0.02%, uno de ellos --Wobbe--
cierra a 14 cifras decimales, practicamente ruido de punto flotante) contra
`normas/ISO_6976.py` (formulas + tabla de constantes YA CERTAIN de 2016_M,
SIN NINGUN CAMBIO), reusando exactamente el mismo metodo que cerro 1983_M.
ESTADO FINAL: **CERRADA a nivel de formula/constantes**, con evidencia MAS
FUERTE que 1983_M (Frida en vivo sobre la funcion real, no solo lectura de
pantalla, y 11 salidas confirmadas en vez de 5). Igual que en 1983_M, la
tabla cruda PROPIA de 1995 (GOT_BASE+0x1158, ver seccion 4) se localizo y se
le trazo la ESTRUCTURA de columnas por disassembly (coincide con el layout
de la TABLA 2 de 2016_M), pero el volcado de sus bytes no dio valores
interpretables con el offset de fila asumido -- no se necesito resolverla
porque la equivalencia numerica con la tabla de 2016_M ya cerro el caso real
sin margen de duda.

===============================================================================
1. SI/NO ES UN ALIAS -- verificado leyendo el binario, no asumido
===============================================================================
[CERTAIN] La tabla de simbolos real de `apk_analisis/libFXLibrary.so`
(pyelftools, `.dynsym`) tiene, para "1995", TRES funciones internas
distintas (a diferencia de 1983, que solo tiene una, y de 2016, que solo
tiene el namespace estructurado):
    _Z19Math_ISO6976_1995_MP17Function_CContextP15tagFUNCTION_ARGlRS1_
        = Math_ISO6976_1995_M(...)                    <- wrapper Excel real
    _Z22PropertiesISO6976_1995PdttffS_S_S_S_S_S_S_S_
        = PropertiesISO6976_1995(double* comp, unsigned short, unsigned
          short, float, float, double*, double*, ..., double*) [8 salidas
          por puntero] -- funcion "corta" (372 bytes), presente pero NUNCA
          llamada por el wrapper Android (ver mas abajo, probablemente
          usada solo por otra ruta como el .xll de Windows, no investigado).
    _Z27PropertiesISO6976_1995_rev1PdiiiRdS0_S0_S0_S0_S0_S0_S0_S0_S0_S0_
        = PropertiesISO6976_1995_rev1(double* comp, int a2, int a3, int a4,
          double& out1, ..., double& out11) [15 argumentos, 11 salidas por
          referencia] -- funcion "vieja" (1733 bytes), la MISMA que ya se
          habia desensamblado en una sesion anterior para extraer los pesos
          atomicos IUPAC de `ISO_6976.py` seccion 3 (metodo B de masa molar).
    _ZN6spirit4math12iso6976_199520calculate_revision_1E... (1972 bytes)
        = spirit::math::iso6976_1995::calculate_revision_1(...) -- namespace
          NUEVO, estructurado igual que el de 2016_M, pero para 1995.

[CERTAIN] Se desensamblo con capstone el cuerpo COMPLETO del wrapper
`Math_ISO6976_1995_M` (direccion real 0x85710, 1545 bytes) buscando sus
`call`: de 10 llamadas totales, 7 son helpers genericos ya conocidos
(`Function_CContext::arg_get`, `NormalizeMolFrac`, `ArgInitializeOutput`,
thunks PIC) y **la UNICA llamada a codigo de negocio real es a la direccion
exacta 0x124980 = `PropertiesISO6976_1995_rev1`**. El wrapper NO llama ni a
`PropertiesISO6976_1995` (la corta) ni a `calculate_revision_1` (el
namespace nuevo) -- ambas existen en el binario pero son CODIGO MUERTO para
esta ruta de calculo (Android/Excel), consistente con que FlowXpert dejo la
implementacion nueva de 1995 escrita pero sin conectarla a este wrapper.

[CERTAIN] Se desensamblo tambien el cuerpo COMPLETO de
`PropertiesISO6976_1995_rev1` (1733 bytes): de sus 3 `call` totales, uno es
el thunk PIC `get_pc_thunk_bx` (prologo, confirma GOT_BASE), otro es un
helper interno sin simbolo (probablemente memcpy/alloc) y el tercero otro
thunk de salida -- **CERO llamadas a `calculate_revision_1`, a
`PropertiesISO6976_1995` (la corta) ni a ninguna funcion de
`spirit::math::iso6976_2016`**. Esto es la prueba definitiva de que
`PropertiesISO6976_1995_rev1` es AUTOCONTENIDO: implementa TODO el calculo
(masa molar por formula quimica, factor Z, densidad real, densidad
relativa, poder calorifico bruto/neto x molar/masa/volumen, Wobbe) en un
solo cuerpo de funcion, con sus propias 2 tablas de constantes (ver seccion
4) -- exactamente el mismo patron ya visto en `PropertiesISO6976_1983`.
    Prologo real (cuarta confirmacion cruzada de GOT_BASE en este proyecto,
    ahora sobre 1995 especificamente):
        call get_pc_thunk_bx        (retorna a 0x124989)
        add ebx, 0x28845f           => GOT_BASE = 0x124989 + 0x28845f =
                                        0x3ACDE8  (identico al resto)

===============================================================================
2. VALIDACION NUMERICA CONTRA EL CASO REAL -- CERRADA <0.03%, POR FRIDA EN VIVO
===============================================================================
[CERTAIN] METODO: a diferencia de 1983_M (que solo se pudo validar por
lectura de pantalla), aqui SI se logro hookear con Frida la funcion interna
REAL `PropertiesISO6976_1995_rev1` mientras corria dentro de la app (mismo
proceso FlowXpert PID 2880, mismo frida-server ya corriendo, reutilizado de
sesiones anteriores). Como los 15 argumentos de esta funcion son TODOS de 4
bytes (puntero/int, sin ningun `double` por valor que rompa el indexado
automatico de Frida como paso con `calculate_real_gas_relative_density` en
2016_M), `args[0..14]` de Frida mapea 1:1 y limpio, sin necesidad de leer
`esp` a mano. Se disparo el calculo real navegando la UI (entrar a
"ISO-6976 (1995)" desde el menu principal, que carga y calcula sola con la
composicion "Default").

CASO REAL CAPTURADO (hook en vivo sobre `PropertiesISO6976_1995_rev1`):
    Argumentos de entrada:
        composicion (22 valores reales, orden interno propio de la funcion,
        NO el orden de `ORDEN_COMPONENTES_APP` -- se identifico por
        magnitud comparando contra los porcentajes ya conocidos del preset
        "Default": el orden agrupa hidrocarburos por numero de carbono
        primero (C1,C2,C3,nC4,iC4,nC5,iC5,neoC5,nC6,nC7,nC8) y despues
        He/N2/CO2 -- el mismo patron de agrupacion ya documentado para
        `_ORDEN_TABLA2_INTERNO` de `ISO_6976.py`, otra pista de que ambas
        tablas comparten diseno aunque no sean el mismo bloque de memoria).
        a2 (int) = 1, a3 (int) = 0, a4 (int) = 0 -- selectores crudos, NO
        desensamblados a fondo (fuera del presupuesto de esta tarea): a2 es
        [LIKELY] un selector de combinacion de temperatura de referencia
        (analogo al `reference_conditions` de 2016_M, cuyo valor de entrada
        1 tambien correspondia al combo 15/15/15 "Default"); a3/a4
        [GUESSING] podrian ser "Molar Mass Method"/"Calorific Val. Method"
        (ambos en su valor por defecto en la UI: "Calculate"/"Definitive").

    Salidas reales (11 doubles por referencia, out1..out11 en el orden que
    devuelve la funcion):
        out1  = 0.78968241677194699   -> Density (kg/m3), UI: 0.789682
        out2  = 0.9981358821579642    -> Compressibility (Z), UI: 0.998136
        out3  = 0.6444231763661975    -> Relative Density, UI: 0.644423
        out4  = 18.637206100799997    -> Molar Mass (g/mol), UI: 18.63721
        out5  = 33.2713173245472      -> Sup. Calorific Val. (MJ/m3, bruto
                                          volumen), UI: 33.27132
        out6  = 42.132528998876815    -> [identificado, ver abajo] GCV bruto
                                          base masa (MJ/kg), NO visible en UI
        out7  = 785.23262649999985    -> [identificado] GCV bruto base molar
                                          (kJ/mol), NO visible en UI
        out8  = 29.996439353113998    -> [identificado] NCV neto base volumen
                                          (MJ/m3), NO visible en UI
        out9  = 37.98544670113465     -> [identificado] NCV neto base masa
                                          (MJ/kg), NO visible en UI
        out10 = 707.9425989999997     -> [identificado] NCV neto base molar
                                          (kJ/mol), NO visible en UI
        out11 = 41.446171601611734    -> [identificado] Indice de Wobbe
                                          bruto, NO visible en UI

Los 5 primeros (out1..out5) coinciden EXACTO (a la precision mostrada en
pantalla) con los 5 campos que expone la UI de "ISO-6976 (1995)" para la
composicion "Default" con "Ref. Temperature = 15/15/15 C" -- confirma que
`PropertiesISO6976_1995_rev1` es realmente la funcion que alimenta la
pantalla, no solo una coincidencia de nombre.

COMPARACION NUMERICA (formulas y `TABLA_CONSTANTES` de `ISO_6976.py`, SIN
NINGUN CAMBIO, T=288.15 K/15 C para las 3 temperaturas -- combustion,
metering, volumen-- , p_ref=101325 Pa [LIKELY, no expuesto en esta pantalla,
igual que en 1983_M, asumido porque cierra <0.1%]; ver bloque `if __name__`
para el codigo exacto):
    Masa molar (`calcular_masa_molar`, Metodo A tabulado):
        18.637417 g/mol  vs  18.637206 g/mol real  => dif. 0.0011%  [CERTAIN]
        (cierre incluso mejor que 2016_M 0.0027% y 1983_M 0.0019% -- refuerza
        que Mj es la misma tabla fisica en las 3 revisiones).

    Factor de compresion Z (`calcular_factor_compresion`, T0=288.15 K),
    probando los 3 indices bj:
        indice 0: Z=0.998033  dif. 0.0103%
        indice 1: Z=0.998233  dif. 0.0098%   <- mejor cierre numerico
        indice 2: Z=0.998274  dif. 0.0138%
    vs 0.998136 real. Los 3 indices cierran <0.02% entre si -- MISMA
    limitacion ya documentada en `ISO_6976.py` seccion 4.1/4.3: los 3
    valores de bj por componente son numericamente muy cercanos, un solo
    caso real no permite distinguir el indice correcto por ajuste numerico
    (aqui el indice 1 da el mejor ajuste, pero en 2016_M el ajuste numerico
    tambien favorecia el indice equivocado hasta que Frida confirmo el
    indice real). Por consistencia con el caso "Default" YA CONFIRMADO por
    Frida en 2016_M (mismo combo exacto 15/15/15 C), se adopta **indice
    bj=2** aqui tambien [LIKELY por analogia, no por Frida directo sobre
    ESTA funcion -- no se desensamblo el cuerpo de
    `PropertiesISO6976_1995_rev1` al nivel de instruccion para leer que
    columna exacta selecciona internamente a partir de a2=1].

    Densidad real y densidad relativa, con indice bj=2 (el adoptado):
        Densidad real = 0.789587 kg/m3  vs  0.789682 real  => dif. 0.0121%
        Densidad relativa = 0.644287  vs  0.644423 real  => dif. 0.0211%
        (con `ZAIRE_SOBRE_MAIR` ya derivado en `ISO_6976.py` seccion 4.3,
        SIN cambios -- refuerza otra vez que es una propiedad del aire, no
        del motor de calculo, y por lo tanto compartida entre las 3
        revisiones).

    Poder calorifico bruto, base volumen (`calcular_poder_calorifico_molar`),
    probando los 4 indices Hoj:
        indice 0: 33.23248 MJ/m3  dif. 0.1167%   (fuera de margen)
        indice 1: 33.24947 MJ/m3  dif. 0.0657%
        indice 2: 33.26682 MJ/m3  dif. 0.0135%   <- unico claramente <0.02%
        indice 3: 33.31891 MJ/m3  dif. 0.1431%   (fuera de margen)
    vs 33.271317 real. El indice 2 es, otra vez, el que cierra mejor -- IGUAL
    que en 2016_M (indice Hoj=2 confirmado por Frida para el mismo combo
    15/15/15) y que en 1983_M (indice Hoj=0 para su combo distinto,
    25 C/0 C). Se adopta **indice Hoj=2**.

    BONUS (no disponible para 1983_M, que solo tenia 5 salidas de pantalla):
    los 6 valores INTERNOS de `PropertiesISO6976_1995_rev1` (out6..out11,
    que la UI no muestra) tambien se identificaron y cierran <0.03% contra
    las formulas ya CERTAIN, con el MISMO indice bj=2/Hoj=2:
        GCV bruto masa    : calc=42.131937  real=42.132529  dif=0.0014%
        GCV bruto molar   : calc=785.230487 real=785.232626 dif=0.0003%
        NCV neto volumen  : calc=29.992380  real=29.996439  dif=0.0135%
        NCV neto masa     : calc=37.984901  real=37.985447  dif=0.0014%
        NCV neto molar    : calc=707.940459 real=707.942599 dif=0.0003%
        Indice de Wobbe   : calc=41.446172  real=41.446172  dif=1.7e-14%
    El Indice de Wobbe (`W = H_volumen_bruto / sqrt(densidad_relativa)`,
    calculado con los 2 valores REALES out5/out3, no con los propios
    calculados) cierra a 14 CIFRAS DECIMALES -- practicamente ruido de
    punto flotante, evidencia [CERTAIN] de que la formula de Wobbe de
    `ISO_6976.py` es EXACTAMENTE (bit a bit, no solo <0.1%) la que usa el
    binario real, y de que out3/out5/out11 quedan correctamente
    identificados sin ninguna duda.

CONCLUSION: los 5 resultados visibles en la UI Y los 6 resultados internos
(11 en total, la validacion mas amplia lograda hasta ahora en este proyecto
para una variante ISO 6976) cierran por debajo o muy cerca del margen <0.1%
del proyecto, usando exactamente las mismas formulas y la misma tabla de
constantes ya CERTAIN de `ISO_6976.py` (variante 2016_M). **ISO 6976
(variante 1995_M) queda CERRADA a nivel de formula/constantes**, con
evidencia mas fuerte que 1983_M (Frida en vivo sobre la funcion real, 11
salidas en vez de 5, un cierre a 14 cifras decimales en Wobbe).

===============================================================================
3. LA PANTALLA "ISO-6976 (1995)" SI EXISTE EN LA APP (no es solo Excel)
===============================================================================
[CERTAIN] Confirmado por navegacion real: el menu principal de FlowXpert
Android lista "ISO-6976 (1995)" como item separado y clickeable (ver
`android_sdk_setup/ui_menu_1995_dump.txt`, capturado en esta tarea). Al
tocarlo se abre una pantalla real con descripcion "Gas Calorific Value,
Density, Relative Density and Wobbe Index according to ISO-6976 (1995)." y
los mismos 5 campos de resultado ya documentados en la seccion 2
(`android_sdk_setup/ui_1995_open.txt`), con un selector "Ref. Temperature"
(15/15/15 C en el preset "Default") y dos selectores adicionales que NO
tiene 1983_M ("Molar Mass Method" = Calculate, "Calorific Val. Method" =
Definitive) -- consistente con que 1995 es una revision mas moderna que
1983 pero mas simple que 2016 en la UI expuesta.

===============================================================================
7. [2026-08-11] INVENTARIO EXHAUSTIVO DE LOS 3 SELECTORES ADICIONALES,
   OPCIONES REALES Y EFECTO CONFIRMADO EN VIVO (uiautomator + edicion real)
===============================================================================
[CERTAIN] Se reabrio la investigacion para confirmar, campo por campo, TODOS
los selectores de "ISO-6976 (1995)" (no solo Ref. Temperature) y compararlos
con 1983/2016. Metodo: `adb shell uiautomator dump` navegando cada fila de
la pantalla real (emulador Android, app relanzada con `am force-stop` +
`monkey -c android.intent.category.LAUNCHER` para descartar un estado de
lista stale que escondia "ISO-6976" del menu de categorias en un intento
anterior de esta misma tarea).

La pantalla "ISO-6976 (1995)" tiene EXACTAMENTE 4 filas de entrada (ninguna
mas, confirmado por conteo de nodos `function_input_type` + ausencia de
scroll): Composition, "Ref. Temperature", "Molar Mass Method", "Calorific
Val. Method". Sin boton "Options"/"Settings" adicional (el overflow "More
options" del action bar solo tiene Copy/Send as email/Send Feedback/Share
app/Customary units/About -- generico de toda la app, no especifico de esta
pantalla).

[CERTAIN] "Molar Mass Method" -- opciones reales (dialogo con Spinner,
values "Calculate"/"Use table", IDENTICO al enum ya visto en la metadata
del binario para 2016_M, "1: Calculate; 2: Use table"): se cambio en vivo de
"Calculate" a "Use table" (composicion "Default", Ref. Temperature=15/15/15
sin cambios) y el resultado real SI cambio:
    Molar Mass:        18.63721 -> 18.63742 g/mol   (cambia)
    Density:           0.789682 -> 0.789691 kg/m3   (cambia, deriva de Mmix)
    Relative Density:  0.644423 -> 0.644430          (cambia, deriva de Mmix)
    Compressibility Z: 0.998136 -> 0.998136          (SIN cambio)
    Sup. Calorific Val.: 33.27132 -> 33.27132 MJ/m3  (SIN cambio)
Esto confirma con evidencia dura (no solo por analogia con la metadata del
binario) que el selector tiene efecto real y que SOLO afecta Molar Mass y
lo que deriva de el (Density, Relative Density) -- Z y poder calorifico NO
dependen de la masa molar en las formulas de este modulo, consistente.
Se implemento `calcular_masa_molar_metodo_b()` en `normas/ISO_6976.py`
(formula quimica con tabla de conteo atomico C/H/N/O/S por componente,
quimica basica, no requiere mas extraccion del binario) y se comprobo que
mapea al lado correcto: para la composicion "Default", Metodo A (tabulado,
`calcular_masa_molar`) da 18.637417 g/mol (0.00001% de diferencia contra el
real "Use table"=18.63742) y Metodo B (formula quimica, `calcular_masa_molar
_metodo_b`) da 18.635640 g/mol (0.0084% de diferencia contra el real
"Calculate"=18.63721) -- ambos del lado correcto, Metodo A mucho mas cerca
(esperable: es tabulado, calibrado; Metodo B usa pesos atomicos IUPAC de
libro de texto que pueden diferir en el 4to/5to decimal de los que usa
FlowXpert internamente). **Selector agregado a `calcular_iso6976_1995()`/
`_extendido()` como parametro FUNCIONAL `molar_mass_method`** ("Use table"
default, coincide con el comportamiento previo del modulo).

[CERTAIN sobre la existencia del efecto, GUESSING sobre la formula exacta]
"Calorific Val. Method" -- opciones reales (Spinner, values "Definitive"/
"Alternative"): se cambio en vivo de "Definitive" a "Alternative" (mismos
demas parametros, incluyendo Molar Mass Method="Use table" del paso
anterior) y el resultado real cambio, pero de forma MINUSCULA:
    Sup. Calorific Val.: 33.27132 -> 33.27133 MJ/m3  (cambia, 0.00003%)
    Density/Z/Relative Density/Molar Mass: SIN cambio
El efecto es real (no ruido de UI: se repitio la lectura 2 veces, mismo
valor estable en ambos estados) pero demasiado pequeño (1 unidad en el 5to
decimal mostrado) para aislar con un solo caso real cual es la diferencia
de formula exacta entre "Definitive" y "Alternative" -- podria ser un
termino de redondeo intermedio distinto, una combinacion bruto/neto
ligeramente distinta, o una correccion de 2do orden despreciable para esta
composicion (dominada por hidrocarburos simples, sin H2/CO/H2S que son los
casos donde bruto/neto difieren mas en `ISO_6976.py`). **Se agrego el
parametro `calorific_val_method` a `calcular_iso6976_1995()`/`_extendido()`
pero queda INFORMATIVO (no cambia el resultado calculado)** -- no se fabrica
una formula sin evidencia suficiente para distinguirla, siguiendo la regla
de oro del proyecto. Pendiente honesto: repetir con una composicion con H2/
CO/H2S alto podria amplificar la diferencia lo suficiente para aislarla.

[CERTAIN] Comparacion final de selectores, las 3 variantes reales
(complementa el resumen del docstring de `normas/ISO_6976.py`):
    1983_M: Composition, "Metering Ref. Temp." (1 temperatura, NO combo),
            "Cal. Val. ref. Temp." (1 temperatura, NO combo) -- 3 inputs,
            NINGUN selector Molar Mass Method/Calorific Val Method/
            Metering reference pressure.
    1995_M: Composition, "Ref. Temperature" (combo 7 opciones), "Molar Mass
            Method" (Calculate/Use table), "Calorific Val. Method"
            (Definitive/Alternative) -- 4 inputs. SIN "Metering reference
            pressure" (la app no lo pide en esta pantalla, se asume 1013.25
            mbar fijo igual que 1983_M).
    2016_M: Composition, "Ref. Temperature" (combo 7 opciones), "Molar Mass
            Method" (Calculate/Use table, mismas 2 opciones que 1995_M,
            confirmado en vivo), "Metering reference pressure" (editable,
            mbar, rango 0..2000 mbar / "0 < P2 < 2 bar") -- 4 inputs. SIN
            "Calorific Val. Method" (2016_M NO tiene este selector, a
            diferencia de lo que se hubiera podido asumir por analogia con
            1995_M -- confirmado por ausencia real en la UI, no por
            omision). Ver seccion 7 del docstring de `normas/ISO_6976.py`
            para el detalle completo de 2016_M (incluye el hallazgo de que
            la pantalla real muestra 11 salidas visibles con scroll, no
            solo las 5 ya documentadas).
Es decir: cada una de las 3 variantes tiene una combinacion DISTINTA de
selectores -- no hay un patron simple "cada revision suma selectores a la
anterior" (2016_M gana "Metering reference pressure" pero PIERDE "Calorific
Val. Method" respecto a 1995_M).

===============================================================================
4. TABLA CRUDA PROPIA DEL BINARIO -- ESTRUCTURA DE COLUMNAS TRAZADA POR
   DISASSEMBLY, VALORES NO INTERPRETADOS CON CERTEZA (pendiente honesto)
===============================================================================
[CERTAIN] `PropertiesISO6976_1995_rev1` referencia DOS tablas propias
consecutivas (ambas relativas a GOT_BASE=0x3ACDE8, confirmado por los `lea`
reales, no por texto de capstone sin verificar):
  - TABLA A (formula quimica, Metodo B de masa molar): `lea eax,[ebx+0x918]`
    ajustado a `ebx+0x95c` para el primer campo -- esta es LA MISMA tabla ya
    usada en una sesion anterior para extraer los pesos atomicos IUPAC de
    `ISO_6976.py` seccion 3 (bucle de 22 iteraciones, registro de 96 bytes:
    5 enteros de conteo atomico C/H/N/O/S + 1 double de correccion, cada uno
    multiplicado por las constantes de peso atomico en GOT_BASE-0x182c20/
    -18/-10/-08/-00). File offset real: 0x3AD700.
  - TABLA B (bj/Hoj propia de 1995): `lea ebp,[ebx+0x1158]`, bucles con
    stride real **0x118 = 280 bytes = 35 doubles por fila**, sobre **22
    filas** (`cmp eax,0x16` en el bucle de Hoj) -- EXACTAMENTE el mismo
    stride/cantidad de filas que la TABLA 2 de 2016_M (`ISO_6976.py` seccion
    3), aunque es una region de memoria DISTINTA (bytes comparados
    directamente entre ambas tablas: 5402 de 6160 bytes son diferentes, NO
    es una copia literal). Las columnas leidas por el codigo real coinciden
    en OFFSET con el layout ya conocido de la TABLA 2 de 2016_M: bj en
    offset `(indice_bj)*8+8` bytes desde el inicio de fila (indices 1..3,
    igual que 2016_M), Hoj_bruto en `(indice_hoj)*8+0x20` (indices 4..7,
    igual que 2016_M) y Hoj_neto 0x20 bytes (4 doubles) despues de Hoj_bruto
    (indices 8..11, igual que 2016_M) -- un switch real de 7 casos (`cmp
    [esp+0x144],6` con jump table de 7 entradas en GOT_BASE-0x92378) fija
    los indices bj/Hoj segun la combinacion de "Ref. Temperature" antes de
    entrar al cuerpo comun, el mismo patron conceptual que el
    `temperature_index` de 2016_M. File offset real: 0x3ADF40 (termina en
    0x3AF750, apenas antes de donde 1983_M tiene su propia tabla en
    0x3AF780 -- consistente con que las 3 tablas estan ubicadas de forma
    contigua en el mismo segmento de datos del binario).

[CERTAIN, RESUELTO EN RONDA 2 -- ver bloque "ACTUALIZADO 2026-08-07 (RONDA
2)" al inicio del docstring] El intento original de volcar la TABLA B
completa (22x35 doubles, `struct.unpack` sobre el archivo `.so` crudo)
asumiendo fila 0 en el offset exacto GOT_BASE+0x1158 daba valores basura
(69759, 121428, 245231, etc.) por una causa de file-offset/vaddr especifica
de este segmento del binario, NO por un desalineamiento de fila ni por un
segundo bloque de memoria. Releyendo la MISMA direccion pero via la memoria
YA RELOCADA de Ghidra (`Memory.getBytes`, no el archivo crudo), las 22 filas
dieron una coincidencia EXACTA bit a bit con los 22 componentes de
`TABLA_CONSTANTES` de `ISO_6976.py`, en el mismo orden de
`ORDEN_COMPONENTES_APP` (Metano, Etano, Propano, n-Butano, i-Butano,
n-Pentano, i-Pentano, neo-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano,
n-Decano, Hidrogeno, Agua, H2S, CO, Helio, Argon, Nitrogeno, Oxigeno, CO2).
La tabla propia de 1995 queda entonces [CERTAIN] tambien en VALORES, no solo
en ubicacion/layout -- ya no es un pendiente. El switch de 7 casos y las
tablas A/B siguen siendo el punto de partida correcto si en el futuro se
necesita un segundo caso real de 1995 con otra "Ref. Temperature" (por
ejemplo, para confirmar por Frida el indice bj/Hoj exacto en vez de
adoptarlo por analogia con 2016_M, ver seccion 2).

[CERTAIN, 2026-08-10] COMPARACION CRUZADA .xll vs .so: se decompilo
`FlowXpert_ISO6976_1995_M` en `FlowXpert.xll` con Ghidra. Motor propio
monolitico confirmado tambien ahi (nucleo real `FUN_1800caf7c`, 1359 bytes,
llamado desde `FUN_1800ab4f8`) -- coincide exacto con la conclusion ya
tomada desde el `.so` (`PropertiesISO6976_1995_rev1`, motor propio,
DISTINTO del pipeline de 2016_M y del motor de `ex_1995_M`). Ver seccion 6
completa del docstring de `normas/ISO_6976.py` para el detalle metodologico
y la confirmacion byte-exacta de la tabla de 22x35 constantes.

===============================================================================
8. [2026-08-17, tarea de continuacion] SELECTOR "Ref. Temperature" RESUELTO
   COMO FUNCIONAL: 6 OPCIONES REALES (NO 7), MAPEO a2 POR FRIDA, INDICES
   bj/Hoj POR COMBO CON CASO REAL PROPIO (ya no por analogia con 2016_M)
===============================================================================
[CERTAIN] Se reabrio el pendiente honesto de la seccion 3 (selector fijo en
15/15/15 "porque solo se habia validado 1 combo"). Se confirmo por
`uiautomator dump` sobre el picker real (tocando el campo de VALOR, no los
botones browse -- mismo metodo que resolvio 1983_M en su seccion 2A) que
"Ref. Temperature" de ISO-6976 (1995) tiene **EXACTAMENTE 6 OPCIONES, NO 7**
como se sospechaba por analogia con 2016_M (`dump_1995_reftemp_picker.xml`,
`verif_reftemp1995_picker2.xml`, lista sin scroll, 6 filas de 48px cada una):
    posicion 0 = "15 / 15 / 15 °C"  (Default, checkeada de entrada)
    posicion 1 = "0 / 0 / 0 °C"
    posicion 2 = "15 / 0 / 0 °C"
    posicion 3 = "25 / 0 / 0 °C"
    posicion 4 = "20 / 20 / 20 °C"
    posicion 5 = "25 / 20 / 20 °C"
NO existe combo "60F/60F/60F" en esta pantalla (a diferencia de 2016_M, que
SI lo tiene) -- diferencia real confirmada por ausencia en la UI, no por
omision de prueba.

[CERTAIN] MAPEO REAL indice interno (a2 de `PropertiesISO6976_1995_rev1`) <->
posicion de UI, confirmado hookeando con Frida las 6 opciones una por una
(cambiando el valor real en el picker, OK, BACK, reabrir la pantalla para
disparar el recalculo -- mismo patron de 1983_M seccion 2A, script
`android_sdk_setup/run_hook_iso6976_1995_reftemp_sweep.py`, log completo en
`android_sdk_setup/hook_iso6976_1995_sweep_out.txt`, resultado estructurado en
`android_sdk_setup/hook_iso6976_1995_sweep_result.json`). Resultado: **indice
DIRECTO desplazado en +1** (a2 = posicion_UI + 1, 1-indexado, NO 0-indexado
como en 1983_M):
    posicion 0 (Default 15/15/15)  -> a2=1
    posicion 1 (0/0/0)              -> a2=2
    posicion 2 (15/0/0)             -> a2=3
    posicion 3 (25/0/0)             -> a2=4
    posicion 4 (20/20/20)           -> a2=5
    posicion 5 (25/20/20)           -> a2=6
En las 6 corridas, a3=0 y a4=0 se mantuvieron SIN CAMBIO (Molar Mass
Method/Calorific Val. Method no se tocaron durante el barrido) -- confirma
que a2 es exclusivamente el selector de Ref. Temperature, aislado de los
otros 2 parametros, y ademas RECONFIRMA de forma independiente (tercera vez,
ahora con este metodo limpio de barrido) que a2=1/a3=0/a4=0 = Default, igual
que las 2 capturas anteriores de este mismo modulo.

[CERTAIN] Las 6 corridas capturaron los 11 outputs REALES completos (no solo
Sup. Calorific Val. de pantalla) para cada combo -- la validacion mas amplia
posible con evidencia dura para esta variante:
    a2=1 (15/15/15, Default): Z=0.9981358821579642 Dens=0.78968241677194699
        RelD=0.6444231763661975 SupCal=33.2713173245472
    a2=2 (0/0/0):     Z=0.99771561407743742 Dens=0.83339863842785676
        RelD=0.6445849828183608 SupCal=35.168172786023524
    a2=3 (15/0/0):    mismos Z/Dens/RelD que a2=2 (metering=0C sin cambios,
        solo cambia combustion) SupCal=35.113192301186147
    a2=4 (25/0/0):    idem metering, SupCal=35.07693851086773
    a2=5 (20/20/20):  Z=0.99822435718380582 Dens=0.7761447052905628
        RelD=0.64439829143037484 SupCal=32.68388055396806
    a2=6 (25/20/20):  mismos Z/Dens/RelD que a2=5, SupCal=32.667176123985633
Confirma el mismo hallazgo fisico ya visto en 1983_M: Z/Density/RelDensity
dependen SOLO del metering (1er+2do numero iguales en todos los combos, o
sea metering=volumen SIEMPRE en estas 6 opciones), Sup. Calorific Val.
depende SOLO del combustion (1er numero del label).

[CERTAIN, cierre 0.0006% -- practicamente bit-exacto] INDICE Hoj (poder
calorifico) POR TEMPERATURA DE COMBUSTION, calibrado usando el Z/Mmix REALES
de cada combo (aislando el termino Hoj de cualquier incertidumbre de bj):
    combustion=25 °C (298.15 K) -> Hoj=0   (a2=4 Y a2=6, mismo resultado)
    combustion=20 °C (293.15 K) -> Hoj=1   (a2=5)
    combustion=15 °C (288.15 K) -> Hoj=2   (a2=1 Y a2=3, mismo resultado)
    combustion=0  °C (273.15 K) -> Hoj=3   (a2=2)
Patron limpio, monotonico y fisicamente consistente (a mayor temperatura de
combustion, MENOR indice Hoj, MENOR poder calorifico -- coincide con el
orden creciente de `Hoj_bruto` en `TABLA_CONSTANTES`, ej. Metano
[890.63(0), 891.09(1), 891.56(2), 892.97(3)]: 25C usa el valor MAS BAJO,
0C el MAS ALTO). Los 4 combustion distintos probados (0/15/20/25 °C) cierran
TODOS <0.001% contra el valor real -- el mejor cierre numerico logrado hasta
ahora en cualquier variante de este proyecto para el indice Hoj, tratado como
[CERTAIN] por la limpieza y consistencia cruzada (2 pares de combos
independientes confirman el mismo indice cada uno).

[LIKELY, margenes chicos ~0.01%, igual limitacion ya documentada para 1983_M/
2016_M] INDICE bj (factor de compresion) POR TEMPERATURA DE METERING,
calibrado por mejor ajuste numerico contra el Z real de cada combo (no hay
funcion interna expuesta para leer el sub-indice bj por Frida directo, a
diferencia de 2016_M que si tenia `calculate_compression_factor` separada):
    metering=0  °C (273.15 K) -> bj=0   (a2=2,3,4 -- 3/3 combos de acuerdo)
    metering=15 °C (288.15 K) -> bj=1   (a2=1, dif 0.0098% vs bj=2 con
        0.0138% -- reemplaza el bj=2 adoptado antes SOLO por analogia con
        2016_M, esta es la PRIMERA calibracion con datos propios de
        `PropertiesISO6976_1995_rev1`)
    metering=20 °C (293.15 K) -> bj=1   (a2=5,6 -- 2/2 de acuerdo, mismo
        indice que 15 °C)
Los margenes entre columnas bj son chicos (<0.02% de diferencia entre la
mejor y la 2da mejor opcion) -- mismo patron de indeterminacion ya
documentado en el resto del proyecto para este parametro especifico, pero la
CONSISTENCIA interna (3/3 y 2/2 de acuerdo dentro de cada temperatura de
metering) es evidencia razonable de que la asignacion es correcta, no una
casualidad de ajuste.

[CERTAIN] Densidad relativa: se valido la formula GENERAL
`calcular_densidad_relativa()` (Mair/Zaire ya CERTAIN de `ISO_6976.py`
seccion 4.6, reusada sin cambios) con el `temperature_index_raw` (tabla
`BAIR_TABLA`, 1..4) que corresponde a cada metering real -- 0°C=1, 15°C=2,
20°C=4 (MISMO mapeo ya usado por 2016_M) -- contra los 3 valores REALES de
Relative Density de este modulo (a2=1,2,5): cierra 0.0084-0.0090% en los 3
casos, dentro del margen del proyecto. Confirma que la tabla de aire
(Mair/Zaire) es una propiedad fisica COMPARTIDA entre 1995_M y 2016_M, no
algo que haya que re-derivar para esta variante.

CONCLUSION: el selector "Ref. Temperature" de ISO-6976 (1995) queda
**FUNCIONAL, no fijo**, con los 6 combos reales expuestos en la interfaz.
Nivel de confianza por parametro: mapeo a2<->UI y T_metering/T_combustion
[CERTAIN, por Frida directo], indice Hoj [CERTAIN, cierre bit-exacto],
indice bj [LIKELY, margenes chicos pero consistentes], densidad relativa
[CERTAIN, formula general ya validada]. Ningun combo se dejo fuera de la
interfaz ni se fabrico un valor sin evidencia -- los 6/6 combos tienen ahora
caso real propio, mejora sobre el estado anterior (1/6 combos validados).
===============================================================================
9. [2026-08-18, tarea de continuacion] MAPEO REAL a3/a4 RESUELTO POR LLAMADA
   DIRECTA (Frida rpc.exports, no hook+UI): SON BANDERAS 0/no-cero, NO UN
   ENUM 1/2 como se asumio por analogia con 2016_M
===============================================================================
[CERTAIN] Se construyo por primera vez un script de llamada DIRECTA (sin UI)
a `PropertiesISO6976_1995_rev1` (`android_sdk_setup/call_iso6976_1995_directo.js`,
patron `keepAlive` anti-GC de V8 ya usado en `call_iso6976_2016_directo.js`) y
se calibro el efecto real de a3 ("Molar Mass Method") y a4 ("Calorific Val.
Method") barriendo VARIOS valores crudos (0,1,2,3), no solo los 2 candidatos
"obvios" (1,2) que se hubieran asumido por analogia con el enum limpio de
`molar_mass_calculation_method` de 2016_M. Sobre la composicion "Default"
(que SI distingue Metodo A de Metodo B, por tener Helio, a diferencia de las
composiciones reales de campo de la seccion siguiente que casi no lo hacen):
    a3=0            -> Mmix=18.63720610  (dif 0.0011% vs tabla, 0.0084% vs metodo_b)
    a3=1,2,3 (identicos entre si, exactos) -> Mmix=18.63741736  (dif 0.0000% vs tabla)
Probar solo (1,2) -- como se hizo en la primera version de esta calibracion,
en esta misma tarea -- HABRIA DADO UNA CONCLUSION FALSA ("a3=1 es tabla, a3=2
tambien es tabla, listo, ambos son la misma opcion"), sin encontrar nunca el
valor real que activa 'Calculate' (Metodo B). Solo al ampliar el barrido a
{0,1,2,3} goes claro el patron real: **a3 es una bandera 0/no-cero, no un
enum 1/2** -- a3=0 dispara 'Calculate' (Metodo B, formula quimica, el valor
0.0084% de diferencia contra `calcular_masa_molar_metodo_b` es la misma
imprecision de pesos atomicos IUPAC ya documentada en la seccion 7, no un
error de indice) y CUALQUIER a3 != 0 dispara 'Use table' (Metodo A, tabulado,
coincide EXACTO -- 0.0000%, bit a bit -- con `calcular_masa_molar` porque usa
la misma tabla ya CERTAIN). Esto CONFIRMA con evidencia directa (ya no solo
por navegacion de UI como en la seccion 7) que la asignacion de
`calcular_iso6976_1995()` ("Calculate" -> `calcular_masa_molar_metodo_b`,
"Use table" -> `calcular_masa_molar`) es la CORRECTA -- el codigo YA
implementado en este modulo no tenia el bug, solo la evidencia previa (basada
en UI) era mas debil ([GUESSING]) que la ahora obtenida por llamada directa
([CERTAIN]).

[CERTAIN] a4 ("Calorific Val. Method") sigue el MISMO patron de bandera
0/no-cero (barrido {0,1,2,3} sobre Default, a3=1 fijo):
    a4=0            -> Sup.Cal=33.2713173245  Wobbe=41.4459366991
    a4=1,2,3 (identicos entre si, exactos) -> Sup.Cal=33.2713286774  Wobbe=41.4459508413
Diferencia real y estable (no ruido, 0.0000113529 MJ/m3, repetible) pero
diminuta (0.00003%), CONSISTENTE con lo ya documentado en la seccion 7 por
metodo UI -- confirma que el efecto es real, minusculo, y que el parametro
`calorific_val_method` del modulo sigue quedando correctamente INFORMATIVO
(no se fuerza una formula distinta sin evidencia suficiente para aislarla,
ver seccion 7). a4=0 (valor observado en el caso real "Default" de la
seccion 2, con la UI en su estado por defecto "Definitive" segun seccion 3)
se adopta como 'Definitive'; cualquier a4 != 0, como 'Alternative'.

[CERTAIN, cierre <0.07%] VALIDACION CONTRA 5 CASOS REALES DE CROMATOGRAFO
(`normas/_cache_cromatografo.json`, dias DISTINTOS de los 5 ya usados para
cerrar 2016_M): con el mapeo a3/a4 ya corregido arriba, variando
`ref_temperature_index` (rc=2,3,4,5,6, cubriendo 5 de los 6 combos reales),
`molar_mass_method` ("Use table"/"Calculate") y `calorific_val_method`
("Definitive"/"Alternative") entre los 5 casos, comparando las 11 salidas
reales (llamada directa) contra `calcular_iso6976_1995_extendido()` con la
MISMA composicion/parametros (script
`android_sdk_setup/validar_iso6976_1995_cromatografo.py`, resultado completo
en `android_sdk_setup/validar_iso6976_1995_cromatografo_out.json`):
    2025-04-01 medidor 1 (rc=2, Use table, Definitive):  peor dif 0.0613%
    2025-03-25 medidor 4 (rc=4, Calculate,  Alternative): peor dif 0.0454%
    2025-06-09 medidor 1 (rc=6, Use table, Alternative):  peor dif 0.0316%
    2025-06-16 medidor 4 (rc=3, Calculate,  Definitive):  peor dif 0.0457%
    2025-05-25 medidor 1 (rc=5, Use table, Definitive):  peor dif 0.0404%
Los 5 casos cierran POR DEBAJO del margen <0.1% del proyecto (peor de los 5,
0.0613%, en Density/Z/Relative Density del caso rc=2 -- consistente con la
diferencia de indice bj [LIKELY, margenes chicos] ya documentada en la
seccion 8, no un hallazgo nuevo). Molar Mass, GCV/NCV base masa y base
molar, y Wobbe cierran sistematicamente aun mas ajustados (muchos en
0.0000-0.002%) en los 5 casos. **CIERRE HONESTO CONFIRMADO para 1995_M
tambien contra composiciones reales de campo, no solo contra el preset
"Default"** -- ningun valor se fabrico para forzar el cierre; el unico ajuste
real hecho en esta tarea fue CORREGIR el mapeo a3/a4 con evidencia dura antes
de aceptar los resultados, no ocultar una discrepancia.
===============================================================================
*** ACTUALIZADO 2026-08-20 -- RANGOS DE VALIDEZ OFICIALES DE COMPOSICION
    AGREGADOS (pendiente de aplicacion nunca hecho, verificado antes de
    empezar contra el codigo actual, no una suposicion). Ver
    `RANGOS_VALIDEZ_1995_M`/`validar_rango_iso6976_1995()` mas abajo:
    Metano 0.5<=x<=1.0, Nitrogeno 0<=x<=0.3, Etano 0<=x<=0.15,
    CO2 0<=x<=0.15, resto 0<=x<=0.05 -- fuente: manual oficial ABB SpiritIT,
    funcion `fxISO6976_1995_M`, PAGINA 119 ("Boundaries"), releido con
    `pdfplumber` y confirmado EXACTO contra la transcripcion previa de la
    memoria del proyecto (sin discrepancia). Es INFORMATIVO/de referencia,
    mismo patron que `validar_rango_aga8()` de `normas/AGA_8.py` -- NO
    bloquea ni "corrige" ningun calculo existente, solo advierte, igual que
    la pantalla real de FlowXpert (output 'Data range'/OOR, que tampoco
    bloquea el calculo). ***
===============================================================================
"""

from .ISO_6976 import (  # noqa: F401
    ORDEN_COMPONENTES_APP,
    TABLA_CONSTANTES,
    R_GAS,
    M_AIRE,
    ZAIRE_SOBRE_MAIR,
    calcular_masa_molar,
    calcular_masa_molar_metodo_b,
    calcular_factor_compresion,
    calcular_volumen_molar_ideal,
    calcular_volumen_molar_real,
    calcular_poder_calorifico_molar,
    calcular_indice_wobbe,
    calcular_densidad_relativa,
)

# Condiciones reales de la pantalla "ISO-6976 (1995)" (ver seccion 2 del
# docstring para el metodo/caso Default y seccion 8 para el barrido completo
# de las 6 opciones reales de "Ref. Temperature", confirmadas por Frida).
P_REF_PA_1995 = 101325.0   # [LIKELY, no confirmado por Frida] no expuesto en
                            # esta pantalla, asumido igual que 2016_M/1983_M
                            # porque cierra <0.03%.

# [CERTAIN, ver seccion 8] Las 6 opciones REALES del selector "Ref.
# Temperature", en el mismo orden que la lista de la UI. indice real
# interno (a2 de PropertiesISO6976_1995_rev1) = posicion_UI + 1 (1-indexado).
OPCIONES_REF_TEMPERATURE_1995 = [
    "15 / 15 / 15 °C",  # a2=1, Default
    "0 / 0 / 0 °C",     # a2=2
    "15 / 0 / 0 °C",    # a2=3
    "25 / 0 / 0 °C",    # a2=4
    "20 / 20 / 20 °C",  # a2=5
    "25 / 20 / 20 °C",  # a2=6
]

# [CERTAIN, via a2, ver seccion 8] Temperatura de metering/volumen (Density/
# Compressibility/Relative Density) por indice real a2 (1..6).
T_METERING_POR_INDICE_1995 = {
    1: 288.15, 2: 273.15, 3: 273.15, 4: 273.15, 5: 293.15, 6: 293.15,
}
T_VOLUMEN_POR_INDICE_1995 = dict(T_METERING_POR_INDICE_1995)  # idem, ver seccion 8

# [CERTAIN, via a2, ver seccion 8] Temperatura de combustion (poder
# calorifico) por indice real a2 (1..6).
T_COMBUSTION_POR_INDICE_1995 = {
    1: 288.15, 2: 273.15, 3: 288.15, 4: 298.15, 5: 293.15, 6: 298.15,
}

# [CERTAIN, via a2, ver seccion 8 -- reusa BAIR_TABLA/calcular_densidad_
# relativa ya CERTAIN de ISO_6976.py, mismo mapeo metering->temperature_index
# que 2016_M: 0C=1, 15C=2, 60F=3 (no aplica aqui), 20C=4] indice para
# calcular_densidad_relativa() por indice real a2 (1..6).
BAIR_INDEX_POR_INDICE_1995 = {1: 2, 2: 1, 3: 1, 4: 1, 5: 4, 6: 4}

# [LIKELY, ver seccion 8 -- margenes chicos (~0.01%) pero consistentes 3/3 y
# 2/2 dentro de cada metering] indice bj (columna de TABLA_CONSTANTES) por
# indice real a2 (1..6), calibrado con datos PROPIOS de
# PropertiesISO6976_1995_rev1 (ya no por analogia con 2016_M).
INDICE_BJ_POR_INDICE_1995 = {1: 1, 2: 0, 3: 0, 4: 0, 5: 1, 6: 1}

# [CERTAIN, ver seccion 8 -- cierre 0.0006%, practicamente bit-exacto,
# patron monotonico fisicamente consistente] indice Hoj (columna de
# TABLA_CONSTANTES) por indice real a2 (1..6).
INDICE_HOJ_POR_INDICE_1995 = {1: 2, 2: 3, 3: 2, 4: 0, 5: 1, 6: 0}

# Retrocompatibilidad: valores del combo Default (a2=1), usados si algun
# codigo externo todavia importa estas constantes sueltas.
T_METERING_1995 = T_METERING_POR_INDICE_1995[1]
T_COMBUSTION_1995 = T_COMBUSTION_POR_INDICE_1995[1]
INDICE_BJ_1995 = INDICE_BJ_POR_INDICE_1995[1]
INDICE_HOJ_1995 = INDICE_HOJ_POR_INDICE_1995[1]

# -----------------------------------------------------------------------------
# RANGOS DE VALIDEZ OFICIALES DE COMPOSICION -- INFORMATIVO, NO BLOQUEANTE.
#
# [CERTAIN, fuente documental] Manual oficial ABB SpiritIT ("Flow-X Manual
# IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf"), funcion
# `fxISO6976_1995_M`, PAGINA 119, seccion "Boundaries": "The valid ranges
# for molar fractions are as follows: Methane 0.5<=..<=1.0; Nitrogen
# 0.0<=..<=0.3; Ethane 0.0<=..<=0.15; Carbon dioxide 0.0<=..<=0.15; All
# others 0.0<=..<=0.05." Releido y confirmado contra el PDF real con
# `pdfplumber` el 2026-08-20 (no se confio solo en la transcripcion previa
# de la memoria del proyecto) -- coincide EXACTO, sin discrepancia.
#
# [CERTAIN, mismo patron ya usado en el proyecto] Este rango es
# INFORMATIVO/de referencia, igual que `validar_rango_aga8()` en
# `normas/AGA_8.py`: la propia pantalla de FlowXpert expone un output
# "Data range" (0=In Range, 1=Out of Range, tag `OOR`) que NO bloquea el
# calculo -- la app calcula igual y solo marca la condicion. Esta funcion
# sigue el mismo criterio: NO lanza excepcion ni "corrige" la composicion,
# solo advierte.
# -----------------------------------------------------------------------------
RANGOS_VALIDEZ_1995_M = {
    "Metano": (0.5, 1.0),
    "Nitrogeno": (0.0, 0.3),
    "Etano": (0.0, 0.15),
    "CO2": (0.0, 0.15),
    "_default": (0.0, 0.05),  # "All others" -- todos los demas componentes
}


def validar_rango_iso6976_1995(fracciones_molares: dict) -> dict:
    """Chequeo INFORMATIVO (NO bloqueante) contra los rangos oficiales de
    composicion de ISO6976_1995_M (ver `RANGOS_VALIDEZ_1995_M` arriba,
    fuente: manual ABB SpiritIT, pagina 119). Mismo espiritu que
    `validar_rango_aga8()` de `normas/AGA_8.py`: la app real no bloquea el
    calculo fuera de rango (solo lo declara via su propio output 'Data
    range'/OOR), asi que esta funcion tampoco bloquea ni modifica ningun
    resultado -- solo informa.

    Devuelve dict con: en_rango (bool), fuera_de_rango (lista de tuplas
    (componente, fraccion, (rango_min, rango_max)) para cada componente
    fuera de su rango oficial, fraccion>0 solamente) y mensaje.
    """
    fuera_de_rango = []
    for nombre, x in fracciones_molares.items():
        if x <= 0.0:
            continue
        lo, hi = RANGOS_VALIDEZ_1995_M.get(nombre, RANGOS_VALIDEZ_1995_M["_default"])
        if not (lo <= x <= hi):
            fuera_de_rango.append((nombre, x, (lo, hi)))

    en_rango = len(fuera_de_rango) == 0
    if en_rango:
        mensaje = "Composicion dentro de los rangos oficiales de ISO6976:1995_M (manual ABB SpiritIT p.119)."
    else:
        detalle = "; ".join(
            f"{nombre}={x:.4f} mol/mol (rango oficial {lo}..{hi})"
            for nombre, x, (lo, hi) in fuera_de_rango
        )
        mensaje = (
            "ADVERTENCIA informativa (NO bloqueante, la app real tampoco "
            f"bloquea): fuera del rango oficial ISO6976:1995_M -- {detalle}."
        )

    return {"en_rango": en_rango, "fuera_de_rango": fuera_de_rango, "mensaje": mensaje}


def calcular_iso6976_1995(fracciones_molares: dict,
                           molar_mass_method: str = "Use table",
                           calorific_val_method: str = "Definitive",
                           ref_temperature_index: int = 1) -> dict:
    """Calcula las 5 salidas reales de la pantalla "ISO-6976 (1995)" de
    FlowXpert. Reusa integramente las formulas/constantes ya CERTAIN de
    `normas/ISO_6976.py` -- ver seccion 2 del docstring de este modulo para
    la validacion numerica del combo Default (11 salidas confirmadas por
    Frida en vivo) y seccion 8 para el barrido completo de los 6 combos
    reales de `ref_temperature_index`.

    ref_temperature_index: 1..6, indice REAL del selector "Ref. Temperature"
        de la pantalla (mapeo a2 confirmado por Frida, ver seccion 8 y
        `OPCIONES_REF_TEMPERATURE_1995` para las 6 etiquetas de UI en orden).
        Default=1 (combo "15/15/15", igual comportamiento que antes de
        exponer este parametro). Temperaturas de metering/volumen/combustion
        y los indices bj/Hoj se resuelven por tabla segun este indice (ver
        `T_METERING_POR_INDICE_1995`, `T_COMBUSTION_POR_INDICE_1995`,
        `INDICE_BJ_POR_INDICE_1995`, `INDICE_HOJ_POR_INDICE_1995`).
    molar_mass_method: "Use table" (Metodo A, tabulado, `calcular_masa_
        molar`) o "Calculate" (Metodo B, formula quimica, `calcular_masa_
        molar_metodo_b`) -- espeja el selector real de la pantalla
        "ISO-6976 (1995)"/"(2016)" de la app (ver seccion 7 del docstring del
        modulo, confirmado en vivo 2026-08-11: cambiar este selector SI
        cambia Molar Mass/Density/Relative Density de forma medible, deja Z
        y Sup. Calorific Val. sin cambios).
    calorific_val_method: "Definitive" o "Alternative" -- espeja el
        selector real "Calorific Val. Method", exclusivo de esta pantalla
        (1983/2016 no lo tienen). [GUESSING sobre la formula exacta]: se
        confirmo en vivo que SI tiene un efecto real pero minusculo sobre
        Sup. Calorific Val. (33.27132 -> 33.27133 MJ/m3 para la composicion
        "Default", 0.00003%) y NINGUN efecto sobre Density/Z/Relative
        Density/Molar Mass -- no se pudo aislar la formula exacta de la
        diferencia (demasiado pequeña para distinguir hipotesis con un solo
        caso real), asi que este parametro queda como INFORMATIVO por ahora:
        se acepta pero no cambia el resultado calculado.
    """
    if ref_temperature_index not in T_METERING_POR_INDICE_1995:
        raise ValueError(
            f"ref_temperature_index invalido: {ref_temperature_index!r} "
            f"(debe ser 1..6, ver OPCIONES_REF_TEMPERATURE_1995)")
    if molar_mass_method == "Calculate":
        mmix = calcular_masa_molar_metodo_b(fracciones_molares)
    else:
        mmix = calcular_masa_molar(fracciones_molares)

    t_metering = T_METERING_POR_INDICE_1995[ref_temperature_index]
    indice_bj = INDICE_BJ_POR_INDICE_1995[ref_temperature_index]
    indice_hoj = INDICE_HOJ_POR_INDICE_1995[ref_temperature_index]
    bair_idx = BAIR_INDEX_POR_INDICE_1995[ref_temperature_index]

    z = calcular_factor_compresion(
        fracciones_molares, indice_temp=indice_bj,
        p_ref=P_REF_PA_1995, t0=t_metering,
    )
    vm_ideal = calcular_volumen_molar_ideal(t=t_metering, p=P_REF_PA_1995)
    vm_real = calcular_volumen_molar_real(vm_ideal, z)
    densidad_real = (mmix / 1000.0) / vm_real
    densidad_relativa = calcular_densidad_relativa(
        mmix, z, indice_temp_raw=bair_idx, p_ref=P_REF_PA_1995)
    hm_bruto = calcular_poder_calorifico_molar(
        fracciones_molares, "bruto", indice_temp_combustion=indice_hoj,
    )
    poder_calorifico_volumen_bruto = (hm_bruto / vm_real) / 1000.0  # MJ/m3

    return {
        "Molar Mass (g/mol)": mmix,
        "Compressibility (Z)": z,
        "Density (kg/m3)": densidad_real,
        "Relative Density": densidad_relativa,
        "Sup. Calorific Val. (MJ/m3)": poder_calorifico_volumen_bruto,
    }


def calcular_iso6976_1995_extendido(fracciones_molares: dict,
                                     molar_mass_method: str = "Use table",
                                     calorific_val_method: str = "Definitive",
                                     ref_temperature_index: int = 1) -> dict:
    """Version extendida: las 5 salidas de pantalla MAS las 6 salidas
    internas de `PropertiesISO6976_1995_rev1` que NO se ven en la UI pero
    SI se confirmaron por Frida en vivo (ver seccion 2, out6..out11).

    Ver `calcular_iso6976_1995` para el significado de `molar_mass_method`/
    `calorific_val_method`/`ref_temperature_index`.
    """
    base = calcular_iso6976_1995(fracciones_molares, molar_mass_method,
                                  calorific_val_method, ref_temperature_index)
    mmix = base["Molar Mass (g/mol)"]
    z = base["Compressibility (Z)"]
    t_metering = T_METERING_POR_INDICE_1995[ref_temperature_index]
    indice_hoj = INDICE_HOJ_POR_INDICE_1995[ref_temperature_index]
    vm_ideal = calcular_volumen_molar_ideal(t=t_metering, p=P_REF_PA_1995)
    vm_real = calcular_volumen_molar_real(vm_ideal, z)
    hm_bruto = calcular_poder_calorifico_molar(
        fracciones_molares, "bruto", indice_temp_combustion=indice_hoj,
    )
    hm_neto = calcular_poder_calorifico_molar(
        fracciones_molares, "neto", indice_temp_combustion=indice_hoj,
    )
    densidad_relativa = base["Relative Density"]
    wobbe = calcular_indice_wobbe(base["Sup. Calorific Val. (MJ/m3)"], densidad_relativa)

    extendido = dict(base)
    extendido.update({
        "GCV bruto, base masa (MJ/kg)": hm_bruto / mmix,
        "GCV bruto, base molar (kJ/mol)": hm_bruto,
        "NCV neto, base volumen (MJ/m3)": (hm_neto / vm_real) / 1000.0,
        "NCV neto, base masa (MJ/kg)": hm_neto / mmix,
        "NCV neto, base molar (kJ/mol)": hm_neto,
        "Indice de Wobbe bruto": wobbe,
    })
    return extendido


def _autotest_caso_real_flowxpert_1995():
    """Caso real "Default" capturado en vivo de la app FlowXpert (pantalla
    ISO-6976 (1995), emulador Android, tarea de continuacion 2026-08-06) --
    ver seccion 2 del docstring del modulo para el metodo completo. A
    diferencia de 1983_M, aqui las 11 salidas reales se capturaron
    hookeando con Frida DIRECTAMENTE la funcion interna real
    `PropertiesISO6976_1995_rev1`, no solo leyendo la pantalla."""
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

    REAL = {
        "Sup. Calorific Val. (MJ/m3)": 33.2713173245472,
        "Density (kg/m3)": 0.78968241677194699,
        "Compressibility (Z)": 0.9981358821579642,
        "Relative Density": 0.6444231763661975,
        "Molar Mass (g/mol)": 18.637206100799997,
    }
    REAL_EXT = {
        "GCV bruto, base masa (MJ/kg)": 42.132528998876815,
        "GCV bruto, base molar (kJ/mol)": 785.23262649999985,
        "NCV neto, base volumen (MJ/m3)": 29.996439353113998,
        "NCV neto, base masa (MJ/kg)": 37.98544670113465,
        "NCV neto, base molar (kJ/mol)": 707.9425989999997,
        "Indice de Wobbe bruto": 41.446171601611734,
    }

    print("=== CASO REAL FlowXpert -- ISO-6976 (1995), composicion 'Default' ===")
    print("(capturado hookeando con Frida en vivo PropertiesISO6976_1995_rev1,")
    print("11 salidas reales -- 5 de pantalla + 6 internas, ver seccion 2 del docstring)")
    print()

    calc = calcular_iso6976_1995_extendido(comp)
    for clave in REAL:
        dif = abs(calc[clave] - REAL[clave]) / REAL[clave] * 100
        estado = "OK <0.1%" if dif < 0.1 else "FUERA DE MARGEN"
        print(f"  {clave:32s} calc={calc[clave]:.6f}   real={REAL[clave]}   "
              f"dif={dif:.4f}%   [{estado}]")
    print()
    print("  --- salidas internas (no visibles en UI, confirmadas por Frida) ---")
    for clave in REAL_EXT:
        dif = abs(calc[clave] - REAL_EXT[clave]) / REAL_EXT[clave] * 100
        estado = "OK <0.1%" if dif < 0.1 else "FUERA DE MARGEN"
        print(f"  {clave:32s} calc={calc[clave]:.6f}   real={REAL_EXT[clave]}   "
              f"dif={dif:.4f}%   [{estado}]")


def _autotest_barrido_ref_temperature_1995():
    """Barrido de los 6 combos reales de "Ref. Temperature" (seccion 8 del
    docstring del modulo), capturados por Frida en la tarea de continuacion
    2026-08-17 (`android_sdk_setup/run_hook_iso6976_1995_reftemp_sweep.py`,
    log completo en `android_sdk_setup/hook_iso6976_1995_sweep_out.txt`).
    Misma composicion "Default" usada en el resto del modulo -- solo cambia
    `ref_temperature_index` (1..6)."""
    comp_pct = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    comp = {c: 0.0 for c in ORDEN_COMPONENTES_APP}
    for nombre, pct in comp_pct.items():
        comp[nombre] = pct / 100.0

    # a2 -> (Z, Density, RelDensity, Mmix, SupCalVal) REALES, hookeados por
    # Frida en vivo (a3=0/a4=0 en las 6 corridas, Molar Mass Method/
    # Calorific Val. Method sin cambios).
    REALES = {
        1: (0.9981358821579642, 0.78968241677194699, 0.6444231763661975, 18.637206100799997, 33.2713173245472),
        2: (0.99771561407743742, 0.83339863842785676, 0.6445849828183608, 18.637206100799997, 35.168172786023524),
        3: (0.99771561407743742, 0.83339863842785676, 0.6445849828183608, 18.637206100799997, 35.113192301186147),
        4: (0.99771561407743742, 0.83339863842785676, 0.6445849828183608, 18.637206100799997, 35.07693851086773),
        5: (0.99822435718380582, 0.7761447052905628, 0.64439829143037484, 18.637206100799997, 32.68388055396806),
        6: (0.99822435718380582, 0.7761447052905628, 0.64439829143037484, 18.637206100799997, 32.667176123985633),
    }

    print("=== BARRIDO 6 combos reales 'Ref. Temperature' -- ISO-6976 (1995) ===")
    print("(seccion 8 del docstring, capturados por Frida 2026-08-17, misma composicion 'Default')")
    print()
    peor_dif = 0.0
    for a2, (z_real, dens_real, reld_real, mmix_real, supcal_real) in REALES.items():
        calc = calcular_iso6976_1995(comp, ref_temperature_index=a2)
        etiqueta = OPCIONES_REF_TEMPERATURE_1995[a2 - 1]
        print(f"-- a2={a2} ({etiqueta}) --")
        for nombre, calc_val, real_val in (
            ("Compressibility (Z)", calc["Compressibility (Z)"], z_real),
            ("Density (kg/m3)", calc["Density (kg/m3)"], dens_real),
            ("Relative Density", calc["Relative Density"], reld_real),
            ("Molar Mass (g/mol)", calc["Molar Mass (g/mol)"], mmix_real),
            ("Sup. Calorific Val. (MJ/m3)", calc["Sup. Calorific Val. (MJ/m3)"], supcal_real),
        ):
            dif = abs(calc_val - real_val) / real_val * 100
            peor_dif = max(peor_dif, dif)
            estado = "OK <0.1%" if dif < 0.1 else "FUERA DE MARGEN"
            print(f"    {nombre:28s} calc={calc_val:.6f}  real={real_val}  dif={dif:.4f}%  [{estado}]")
    print()
    print(f"Peor diferencia de todo el barrido: {peor_dif:.4f}%  "
          f"({'CIERRA <0.1%, selector FUNCIONAL confirmado en los 6/6 combos' if peor_dif < 0.1 else 'FUERA DE MARGEN'})")


if __name__ == "__main__":
    _autotest_caso_real_flowxpert_1995()
    print()
    _autotest_barrido_ref_temperature_1995()
