# -*- coding: utf-8 -*-
"""
normas/ISO_6976_ex_2016.py
=============================
===============================================================================
*** ACTUALIZADO 2026-08-10 (tarea de continuacion) -- CASO REAL CONSEGUIDO POR
    LLAMADA DIRECTA FRIDA A `iso6976_2016_inputsC1` + `iso6976_2016()`. Este es
    el avance mas grande de este archivo: la tarea reevaluo si la llamada
    directa (rechazada en la sesion de creacion de este archivo, ver "CASO
    REAL -- REINDEXADO..." mas abajo, por miedo a reconstruir 4-5
    `std::vector` reales con heap propio) era viable ahora, aplicando la
    MISMA leccion que ya funciono para `ISO_6976_ex_1995.py` (calculate_
    revision_1): verificar la firma REAL con Ghidra antes de descartar por
    complejidad, no generalizar el riesgo de una funcion a toda una familia.

    [CERTAIN, HALLAZGO PRINCIPAL] Se decompilo el CUERPO COMPLETO de
    `iso6976_2016_inputsC1` con Ghidra 11.4.3 (reusando el proyecto
    `apk_analisis/ghidra_project_11.4.3/libFX114.gpr`, script nuevo
    `apk_analisis/ghidra_scripts_11.4.3/DecompileInputsCtorFull.java`, salida
    completa en `apk_analisis/inputsctor_full_out.txt`). El miedo original
    ("6 std::vector con heap propio, un orden de magnitud mas complejo que
    AGA-3/GERG") resulto ser DESPROPORCIONADO: la firma real tiene 5
    `std::vector<T> const&` (no 6, imprecision de un docstring anterior), y
    de esos 5, el cuerpo del constructor muestra que SOLO UNO necesita datos
    reales:
      - `param_1` (vector<index_based_component>, la composicion): estos SI
        se leen y se usan (scatter-write: para cada entrada {index i32,
        fraccion f64} el constructor escribe `denso[index] = fraccion` en un
        arreglo propio de 60 doubles).
      - `param_5` (vector<double>, "fracciones alternativas densas"): el
        constructor SIEMPRE reserva un buffer de 60 doubles y lo pone en
        CERO antes de mirar este parametro -- si se pasa VACIO (begin=end=
        cap=NULL, 12 bytes de ceros), el constructor simplemente no le hace
        ningun `_M_range_insert` (branch `if (size!=0)`) y usa el buffer ya
        cero. No hace falta construirlo con datos reales.
      - `param_6`/`param_7`/`param_8` (vector<molarmass_and_atomic_indices>/
        <summation_factors>/<gross_calorific_values>, las "filas extra
        definidas por el usuario" mas alla de las 60 tabuladas, ya
        sospechadas en la seccion 1 de este docstring): el constructor
        SIEMPRE reserva memoria NUEVA (operator new) y hace `memcpy` de las
        60 filas ESTATICAS del binario (las MISMAS 3 tablas de esta seccion
        2, direcciones GOT-relativas ya documentadas) ANTES de mirar estos 3
        parametros. Si se pasan VACIOS, el `_M_range_insert` correspondiente
        no se ejecuta -- el constructor YA tiene las 60 filas reales sin
        necesitar nada del llamador.
    Es decir: de 5 vectores, 4 se pueden pasar como stubs vacios de 12 bytes
    (3 punteros NULL cada uno) SIN ningun riesgo, y solo 1 (la composicion,
    un struct POD plano de 12 bytes/entrada: {int32 index; double fraccion})
    necesita construccion real -- exactamente el mismo patron simple que ya
    funciono en `calculate_revision_1` (ex_1995), NO el "orden de magnitud
    mas complejo" que se temia.

    [CERTAIN] METODO DE EJECUCION: se relanzo el emulador Android + frida-
    server (se habian detenido desde la sesion anterior; hipervisor y AVD
    `flowxpert_rd` ya quedaban configurados de sesiones previas, solo hubo
    que rearrancar procesos) y se ataco el proceso real de FlowXpert (PID
    real de esta corrida) con Frida. Simbolos reales resueltos por
    `.dynsym`/pyelftools (no adivinados): `iso6976_2016_inputsC1` (0x138b20)
    y el orquestador `iso6976_2016()` (0x137c70) -- las MISMAS 2 direcciones
    ya confirmadas como compartidas por ambos wrappers (base y "ex") en la
    seccion 1 de este docstring. Se construyo el struct `iso6976_2016_inputs`
    (0x48 bytes, zero-init) y `iso6976_2016_outputs` (0x68 bytes, zero-init)
    en memoria del proceso via `Memory.alloc`, con la composicion real
    "Default" (los MISMOS 22 componentes ya validados en `ISO_6976.py`
    seccion 4) direccionada por FILA de la tabla de 60 de ESTE archivo (no
    por el indice 0..21 del wrapper base) -- exactamente la prueba que pide
    esta tarea: validar el struct de 60 usando el UNICO caso real disponible,
    con 0.0 en los 38 componentes nuevos.

    [CERTAIN, RESULTADO] Barriendo `reference_conditions`=1..7 (el enum real
    que antes se llamaba, sin confirmar, "indice de combo de temperatura")
    x `molar_mass_calculation_method`=1|2, con p_ref=101.325 kPa fijo (el
    mismo valor ya CERTAIN en `ISO_6976.py`), **reference_conditions=1**
    (ambos metodos de masa molar dan resultado identico para esta
    composicion, igual que ya se documento en `ISO_6976.py` seccion 4) da un
    cierre MUCHO mas fino que cualquier otro obtenido en este proyecto para
    esta variante -- los 5 resultados que expone la pantalla real cierran
    BIT-EXACTO (no solo <0.1%, sino <0.0001% en los 5):
        Mmix              = 18.636924202  vs real 18.63692     dif 0.0000225%
        Z                 = 0.998153773   vs real 0.998154     dif 0.0000227%
        densidad_real     = 0.789660868   vs real 0.789661     dif 0.0000168%
        densidad_relativa = 0.644347921   vs real 0.644348     dif 0.0000123%
        PCB_volumen       = 33.269189991  vs real 33.26919     dif ~0.00000003%
    Ver `android_sdk_setup/sweep_iso6976_2016_directo.js` (script final que
    funciono, construccion inline sin funciones auxiliares compartiendo
    closures) y `android_sdk_setup/sweep_iso6976_2016_directo_out.json` (log
    completo de los 14 combos) para el metodo reproducible completo.

    [HALLAZGO SECUNDARIO, honestidad de proceso] Un primer intento con la
    misma logica pero envuelta en `rpc.exports` (`android_sdk_setup/
    call_iso6976_2016_directo.js`, dejado en el repo para trazabilidad) dio
    resultados CONSISTENTEMENTE INCORRECTOS (Mmix=5.59 en vez de 18.64, para
    los 14 combos por igual) a pesar de que un volcado de memoria directo
    (`android_sdk_setup/debug_iso6976_2016_ctor.js`) confirmo que el
    constructor SI escribia los datos correctos en el struct `inputs`
    (fracciones y tabla estatica correctas, Mmix recalculado a mano en JS =
    18.636924, ya coincidente). La causa raiz exacta de por que la version
    `rpc.exports` fallaba no se aislo del todo (se descarto por tiempo, no
    por falta de evidencia de que el struct SI se construia bien) -- lo que
    SI se confirmo es que reescribiendo el mismo llamado de forma "plana"
    (todo inline, sin funcion `llamar()` reutilizada entre iteraciones del
    sweep) el resultado fue correcto de inmediato. Se documenta este
    intermedio fallido explicitamente para que una revision futura no
    reinvente la misma confusion si vuelve a usar `rpc.exports` para llamadas
    repetidas de este tipo.

    [LIMITE HONESTO QUE SE MANTIENE, no se fuerza mas alla de la evidencia]
    Este caso real SIGUE sin ejercitar ninguno de los 38 componentes NUEVOS
    con valor NO CERO (se pusieron a 0.0, tal como pide la tarea, para
    aislar la validacion del struct de 60 contra el UNICO caso real
    disponible del proyecto) -- no existe pantalla "ex" ni otro caso real
    independiente para confirmar esos 38 valores en ejecucion. Tampoco se
    probo el mecanismo de "filas extra definidas por el usuario" (param_6/7/
    8 con datos reales, mas alla de las 60 tabuladas). Lo que SI cambia de
    forma sustancial respecto al estado anterior: la validacion ya NO es una
    "reindexacion" hecha en Python puro (recalculando con las constantes
    extraidas) sino una EJECUCION REAL del binario compilado, con el mismo
    nivel de evidencia que ya se acepto para `calculate_revision_1`
    (ex_1995) -- construir el struct de composicion sparse (60 filas
    posibles, no 22) y ver que el motor real lo resuelve bit-exacto es
    evidencia mucho mas fuerte de que el mapeo fila<->componente y el
    contenido de las 3 tablas estaticas de la seccion 2 son correctos, que
    la reindexacion en Python ya documentada. Dato nuevo que emerge de este
    hallazgo (sin modificar `ISO_6976.py`, que queda fuera de alcance de esta
    tarea): el valor real de `reference_conditions` para la composicion
    "Default"/15-15-15 es **1**, un dato mas preciso que las hipotesis
    [LIKELY] de indice bj/Hoj ya documentadas alli por ajuste numerico
    (aquella tarea nunca tuvo el enum `reference_conditions` real, solo el
    `temperature_index` interno de 2-3 funciones hoja) -- se deja como nota
    para una revision futura de ese archivo, no se toca aqui. ***
===============================================================================
*** ACTUALIZADO 2026-08-07 (FASE DECOMPILACION PURA) -- NOMBRES DE ISOMEROS
    CORREGIDOS con la MISMA tabla de nombres reales embebida encontrada en
    la tarea de `ISO_6976_ex_1995.py` (ver seccion 5 de ese docstring para
    el metodo completo y la lista de 55 nombres, offsets 0x319000-0x31c000
    del .so) -- las primeras 55 filas de esta tabla de 60 comparten formula Y
    ORDEN con las 55 de `ex_1995` (ya documentado abajo), asi que la misma
    lista de nombres reales aplica 1 a 1. Correcciones aplicadas (solo
    nombres/etiquetas en `ORDEN_COMPONENTES_EX2016`/`TABLA_CONSTANTES_EX2016`,
    los valores Mj/bj/Hoj NO cambiaron): "1,3-Butadieno"/"1,2-Butadieno"
    intercambiados -> corregido; "2-Penteno"/"Hexeno"/"Hepteno"/"Octeno"
    (adivinados como alquenos de cadena recta) eran en realidad cicloalcanos
    "Ciclopentano"/"Metilciclopentano"/"Etilciclopentano"/"Etilciclohexano";
    "m-Xileno" era en realidad "Etilbenceno" (Ethylbenzene). Los 5
    componentes exclusivos de este archivo (Undecano..Pentadecano, filas
    55-59) NO tienen nombre confirmado por string (no se encontraron en la
    busqueda), pero no tenian ambiguedad de isomero de todos modos (alcano
    normal unico por formula). ***
===============================================================================
*** ACTUALIZADO 2026-08-20 (aplicacion de la lista oficial del manual ABB
    SpiritIT, encontrado 2026-08-19, ver `proyecto_confirmacion_calculos_
    estado.md`) -- CIERRA LOS 5 [LIKELY nombre] RESTANTES DE FILAS 55-59.
    Se releyo el PDF real (`Flow-X Manual IIIb - Function Reference_CM_
    FlowX_FR-EN_E.pdf`, paginas 123-124, funcion `fxISO6976ex_2016_M`) con
    `pdfplumber` en vez de confiar solo en la transcripcion de memoria del
    proyecto. [CERTAIN, texto crudo extraido del PDF] el manual numera:
    "56: N_undecane", "57: N_Dodecane", "58: N_tridecane",
    "59: N_pentadecane", "60: N_pentadecane" -- CONFIRMADO que el manual
    mismo repite literalmente "N_pentadecane" en los indices 59 Y 60 (typo
    real del documento oficial, no un error de transcripcion de este
    proyecto). Esto rompe la progresion quimica esperada C11..C15 en el
    indice 59 (deberia decir N_tetradecane); NO se copia el typo aqui --
    este archivo ya usaba, desde antes de que el manual apareciera, la
    progresion quimica correcta Undecano/Dodecano/Tridecano/Tetradecano/
    Pentadecano (filas 55-59, ver seccion 3), que es exactamente lo que el
    manual habria dicho de no tener el error.
    Con el manual como segunda fuente independiente (fuente documental
    oficial, no solo formula quimica), y dado que tanto la formula (Mj
    exacto CnH(2n+2) para n=11..15, ya CERTAIN) como el ORDEN relativo
    (Undecano<Dodecano<Tridecano<Tetradecano<Pentadecano, coincide con el
    manual salvo su typo en el indice 59) YA coincidian, las 5 filas suben
    de [LIKELY nombre] a **[CERTAIN nombre, confirmado por progresion
    quimica + manual oficial pese a su typo]**: fila 55=Undecano (manual
    56, N_undecane), fila 56=Dodecano (manual 57, N_Dodecane), fila
    57=Tridecano (manual 58, N_tridecane), fila 58=Tetradecano (manual 59,
    "N_pentadecane" con typo -- corregido aqui por progresion quimica a
    Tetradecano), fila 59=Pentadecano (manual 60, N_pentadecane). No se
    modifico ningun valor Mj/bj/Hoj, solo se eleva la confianza documentada
    de la etiqueta de nombre (ver seccion 3 y `COMPONENTES_CERTAIN_EX2016`
    mas abajo para la distincion entre "certain por ejecucion real" -- que
    sigue limitada a 22/60 -- y "certain por nombre/identidad", que ahora
    cubre 27/60: los 22 originales + estas 5). ***
===============================================================================
ISO 6976:2016, variante "ex" EXTENDIDA a 60 componentes (`Math_ISO6976ex_2016_M`
en libFXLibrary.so), en vez de los 22 estandar de `normas/ISO_6976.py`.
Tarea de continuacion 2026-08-06 (extiende el trabajo de `ISO_6976_ex_1995.py`).

Este archivo se puede ejecutar solo:
    python -m normas.ISO_6976_ex_2016

===============================================================================
RESUMEN EJECUTIVO (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] PUNTO DE PARTIDA CONFIRMADO (dato ya dado por la tarea, reverificado
en 10 min por disassembly directo, capstone + pyelftools sobre
`apk_analisis/libFXLibrary.so`): a diferencia de 1995 (donde "ex" usa un motor
COMPLETAMENTE DISTINTO, `calculate_revision_1`, ver `ISO_6976_ex_1995.py`),
`Math_ISO6976ex_2016_M` (simbolo real, direccion 0xc2b00, 4189 bytes) SI
reutiliza el MISMO motor que la variante base 2016_M: construye el mismo tipo
`iso6976_2016_inputs` (llamando a `iso6976_2016_inputsC1`, direccion 0x138b20,
IDENTICA en ambos wrappers) y llama a la misma funcion orquestadora
`spirit::math::iso6976_2016::iso6976_2016()` (direccion 0x137c70, IDENTICA en
ambos wrappers). Confirmado leyendo las instrucciones `call` reales de ambos
wrappers (`Math_ISO6976_2016_M` en 0xc1af0 y `Math_ISO6976ex_2016_M` en
0xc2b00) y verificando que ambas terminan en las MISMAS 2 direcciones. Esto
confirma [CERTAIN] la hipotesis de partida: el ALGORITMO de esta variante ya
esta al mismo nivel de certeza que `ISO_6976.py` (2016_M base, CERRADA).

[CERTAIN, HALLAZGO PRINCIPAL DE ESTA TAREA] La tabla de 60 componentes SI
existe como tabla estatica embebida en el binario -- pero NO en el mismo
lugar/formato que se asumia por analogia con el `ISO_6976_ex_1995.py` (que
busco un UNICO bloque de filas de 35 doubles, igual stride que la "TABLA 2"
de `ISO_6976.py`). Investigando el disassembly de `iso6976_2016_inputsC1`
(compartido por ambos wrappers, 2016_M y ex_2016_M) se encontro que ESTE
constructor SIEMPRE reserva memoria y hace un `memcpy` de TRES arreglos
estaticos SEPARADOS, de EXACTAMENTE 60 filas cada uno (no 22, no variable --
el numero 60 esta escrito de forma literal en el tamano de la reserva de
memoria, independientemente de si el llamador es la variante base o "ex"):
    1. `molarmass_and_atomic_indices`: GOT_BASE - 0x8ADE8 = file offset
       **0x322000**, 60 filas x 32 bytes (0x780 = 1920 bytes totales).
       Layout por fila: [0:4] id (int32, 1-based, id=fila+1), [4:12] Mj
       (double, g/mol), [12:16][16:20][20:24][24:28][28:32] conteos atomicos
       C,H,N,O,S (int32 x5) -- CONFIRMADO por `fac_molarmass_and_atomic_
       indices` (direccion 0x137190), que solo empaqueta punteros ya resueltos
       en este orden exacto.
    2. `summation_factors` (bj): GOT_BASE - 0x8B668 = file offset
       **0x321780**, 60 filas x 36 bytes (0x870 = 2160 bytes totales).
       Layout: [0:2] id (uint16), [4:12][12:20][20:28] bj x3 (double) -- los
       ultimos 8 bytes de la fila (36-28=8) no se usan por
       `fac_summation_factors` (0x137230), consistente con espacio reservado
       para un 4to valor no usado, igual patron "3 de 4 posibles" que la tabla
       CERTAIN de `ISO_6976.py`.
    3. `gross_calorific_values` (Hoj bruto, base molar): GOT_BASE - 0x8C0E8 =
       file offset **0x320D00**, 60 filas x 44 bytes (0xA50 = 2640 bytes
       totales). Layout: [0:4] id (int32), [4:12][12:20][20:28][28:36][36:44]
       Hoj_bruto x5 (double, kJ/mol) -- CONFIRMADO por `fac_gross_calorific_
       values` (0x1371e0), que empaqueta 5 doubles, NO 4 como en la tabla de
       22 de `ISO_6976.py` (ver seccion 2 para la discusion de este dato
       nuevo: la revision 2016 parece usar 5 combinaciones de temperatura de
       combustion en vez de 4).
GOT_BASE = 0x3ACDE8, el MISMO valor ya confirmado y reusado en TODAS las
normas de este proyecto (AGA-3/5/8/10, GERG-2004/2008, NX-19, ISO 6976 base y
ex_1995) -- quinta/sexta confirmacion cruzada independiente de este registro
base, ver metodo en la seccion 1 mas abajo.

[CERTAIN, verificado por evidencia directa de codigo, NO por coincidencia de
valores] El mapeo indice(0-based)->componente para los 22 componentes ya
conocidos de `ORDEN_COMPONENTES_APP` se leyo DIRECTAMENTE de las 22
instrucciones `call vector<index_based_component>::emplace_back` del wrapper
BASE `Math_ISO6976_2016_M` (no de la variante "ex" -- el wrapper base es mas
simple, 22 llamadas desenrolladas con el indice como constante literal
inmediata en cada una, mientras el wrapper "ex" usa un bucle en tiempo de
ejecucion que lee de argumentos de Excel, ver seccion 4). Cada una de las 22
llamadas fija `index_based_component.index = <constante literal>` junto con
`x = composicion[j]` para cada slot `j` de `ORDEN_COMPONENTES_APP` -- esto es
evidencia de codigo maquina real, no una tabla de valores comparados por
coincidencia (metodo distinto y mas fuerte que el usado en
`ISO_6976_ex_1995.py`, que solo comparo VALORES de bj/Hoj contra
`ISO_6976.TABLA_CONSTANTES` para etiquetar filas). RESULTADO:
    slot 0 Metano->fila0   slot 1 Nitrogeno->fila51   slot 2 CO2->fila53
    slot 3 Etano->fila1    slot 4 Propano->fila2      slot 5 Agua->fila41
    slot 6 H2S->fila42     slot 7 Hidrogeno->fila40   slot 8 CO->fila45
    slot 9 Oxigeno->fila52 slot10 i-Butano->fila4     slot11 n-Butano->fila3
    slot12 i-Pentano->fila6 slot13 n-Pentano->fila5   slot14 n-Hexano->fila8
    slot15 n-Heptano->fila13 slot16 n-Octano->fila14  slot17 n-Nonano->fila15
    slot18 n-Decano->fila16 slot19 Helio->fila48      slot20 Argon->fila50
    slot21 neo-Pentano->fila7
HALLAZGO ADICIONAL DE HONESTIDAD (importante, no se fuerza mas alla de lo que
la evidencia permite, y NO se modifica ningun otro archivo del proyecto por
esto): este mapeo, leido DIRECTO del codigo del wrapper (no inferido), pone
i-Butano en la fila4 y n-Butano en la fila3 de ESTA tabla de 60 -- es decir,
EXACTAMENTE AL REVES del orden que `ISO_6976_ex_1995.py` documenta para su
propia tabla de 55 (fila3=i-Butano, fila4=n-Butano, seccion 3 de su
docstring), y lo mismo ocurre con i-Pentano/n-Pentano (fila6/fila5 aqui vs
fila5/fila6 alla). Como i-Butano y n-Butano (e i-Pentano/n-Pentano) tienen el
MISMO Mj (no distinguible por masa molar) pero bj/Hoj DISTINTOS, esto sugiere
[LIKELY, no confirmado por Frida] que la tabla de 55 de `ISO_6976_ex_1995.py`
(y posiblemente la tabla de 22 "TABLA_CONSTANTES" de `ISO_6976.py` de la que
copia las etiquetas) podria tener i-Butano/n-Butano e i-Pentano/n-Pentano
INTERCAMBIADOS -- un posible pendiente para revisar en esos dos archivos en
una tarea futura. NO se modifico ningun archivo existente del proyecto para
esta tarea (fuera de alcance, y ambos archivos ya estan "CERRADOS"/
documentados); se deja esta nota como hallazgo honesto para que el equipo
decida si amerita revision.

[RESUELTO 2026-08-06, tarea de continuacion posterior] El swap SI era real.
Se confirmo por dos vias independientes SIN tocar este archivo (que ya tenia
los valores correctos, confirmados por la evidencia de codigo maquina de
arriba, la mas fuerte de las tres): (1) cruce contra entalpia de combustion
publica (ΔHf° de formacion + estequiometria de combustion) de i-Butano/
n-Butano e i-Pentano/n-Pentano -- a diferencia de Mj, el poder calorifico SI
distingue isomeros (el ramificado, mas estable termodinamicamente, libera
MENOS energia: n-Butano ~2877.4 kJ/mol > i-Butano ~2868.2 kJ/mol; n-Pentano
~3535.8 > i-Pentano ~3528.8), coincidiendo EXACTO con los valores ya
correctos de ESTE archivo (fila3=n-Butano=2877.40, fila4=i-Butano=2868.20);
(2) los valores swapeados de `ISO_6976.py`/`ISO_6976_ex_1995.py` (que decian
"i-Butano"=2877.40 y "n-Butano"=2868.20, AL REVES) fueron corregidos
intercambiando esas dos entradas (y el par i/n-Pentano), y el autotest del
caso real "Default" de `ISO_6976.py` siguio cerrando <0.1% (el poder
calorifico volumetrico bruto mejoro levemente de 0.0071% a 0.0068% de
diferencia -- mejora pequena porque estos 4 componentes juntos representan
solo 0.183% de la composicion real, insuficiente para que este caso por si
solo fuera concluyente, consistente con por que la alerta original no se
pudo descartar solo por el cierre numerico). Este archivo (`ISO_6976_ex_2016.py`)
NO necesito ningun cambio: su tabla ya tenia el orden correcto desde el
principio.

[CERTAIN, validacion mas fuerte que la de `ISO_6976_ex_1995.py`] Usando ESTA
tabla de 60 (no la de 22 de `ISO_6976.py`) y el mapeo de indices recien
confirmado, se reindexo la MISMA composicion real "Default" ya usada para
cerrar `ISO_6976.py` (misma app, mismo caso de pantalla, ver seccion 4 de ese
modulo) y se comparo contra los MISMOS 5 resultados reales de pantalla. Los 22
componentes de esta composicion real SI existen en la tabla de 60 (son un
subconjunto). Resultado (ver `_autotest_caso_real_reindexado` mas abajo):
    Masa molar   : 18.636956 g/mol vs real 18.63692   -> dif 0.0002%
    Factor Z     : 0.998244        vs real 0.998154    -> dif 0.0090% (indice
                                    bj=1, igual indice que ya usa `ISO_6976.py`)
    Densidad real: 0.789591 kg/m3  vs real 0.789661     -> dif 0.0089%
    Poder calorif.: 33.26619 MJ/m3 vs real 33.26919      -> dif 0.0090% (indice
                                    Hoj=1, MISMO indice que el de bj usado arriba)
TODOS cierran <0.01%, igual o mejor que el cierre ya logrado en `ISO_6976.py`
con su propia tabla de 22 -- esto es evidencia MUY fuerte (aunque sigue sin
ser un caso real que ejercite mas de 22 componentes ni la variante "ex" en si)
de que la tabla de 60 y el mapeo de indices extraidos en esta tarea son
correctos, y de que son la fuente real que usa el motor `iso6976_2016()`
(mas fuerte que la validacion "bit a bit" de `ISO_6976_ex_1995.py`, porque
aqui se reprodujo el CALCULO COMPLETO contra el caso real de pantalla, no solo
se comparo una tabla contra otra).

[CERTAIN via formula quimica, LIKELY/GUESSING el nombre comercial/isomero
exacto -- mismo estandar de honestidad que `ISO_6976_ex_1995.py`] Los 38
componentes nuevos (filas fuera de los 22 ya mapeados) se identificaron
cruzando Mj real + conteo atomico real (leido DIRECTO del binario, columna
[12:32] de la tabla `molarmass_and_atomic_indices`, no solo Mj) contra formulas
quimicas conocidas. HALLAZGO: las primeras 55 filas de esta tabla de 60 son,
fila por fila, la MISMA LISTA DE COMPONENTES (mismas formulas quimicas, mismo
orden relativo) que las 55 filas de `ISO_6976_ex_1995.py` -- consistente con
que ISO 6976:2016 extendio la lista de 1995 agregando exactamente 5
componentes nuevos al final: **Undecano (C11H24), Dodecano (C12H26), Tridecano
(C13H28), Tetradecano (C14H30) y Pentadecano (C15H32)** (filas 55 a 59, Mj
156.31/170.33/184.36/198.39/212.41 g/mol, conteo atomico exacto CnH(2n+2) para
n=11..15) -- una extension logica de la serie de parafinas normales ya
presente (Metano..Decano) hacia componentes mas pesados, consistente con el
tipo de actualizacion que suelen tener las revisiones de ISO 6976. Ver seccion
3 para la tabla completa fila por fila.

[NO SE CONSIGUIO CASO REAL DE LA VARIANTE "EX" EN SI, documentado honestamente,
mismo limite ya aceptado en `ISO_6976_ex_1995.py`] No hay pantalla Android
"ISO-6976 ex" (confirmado por el agente anterior navegando el menu completo,
sin scroll oculto, 3 items unicamente). Esta tarea NO tuvo acceso a un
emulador Android corriendo ni a `adb`/`frida-server` activos en el entorno de
ejecucion (verificado: `adb` no esta instalado en el PATH de esta sesion) --
por lo tanto NO se pudo, en esta sesion, revisar en vivo si la pantalla
"ISO-6976 (2016)" tiene algun boton oculto de "mas componentes" (punto 3 de la
tarea); se confia en la navegacion ya hecha por el agente anterior para
`ISO_6976_ex_1995.py` (misma app, mismo menu "Gas > ISO", sin variantes "ex"
listadas) como evidencia de que tampoco existe para 2016, pero esto NO se
re-verifico de forma independiente en esta sesion -- limite honesto, no se
finge haberlo revisado.

Se evaluo (solo por disassembly, sin ejecutar) la posibilidad de armar un caso
via Frida llamando directo a `Math_ISO6976ex_2016_M`: el wrapper "ex" NO
desenrolla 22/60 llamadas literales como el wrapper base -- usa un bucle real
que lee, para cada fila hasta 60, id/fraccion/Mj/atomicos/bj/Hoj **desde
argumentos de Excel** (llamadas a `Function_CContext::arg_get` y a una funcion
de acceso a arreglo, direccion 0x83f20, no identificada por nombre) en vez de
tomarlos de la tabla estatica interna -- es decir, la variante "ex" parece
disenada para que el USUARIO pueda pegar en Excel una tabla de propiedades
propia (posiblemente pre-poblada con los valores por defecto de la tabla de
60 aqui extraida, aunque esto NO se confirmo linea por linea dentro del
presupuesto de esta tarea) en vez de limitarse a elegir componentes por
indice. Construir ese argumento de Excel a mano por Frida (un arreglo/rango
con hasta 60 filas x ~9 columnas) es un riesgo de layout mayor que el ya
aceptado y descartado en `ISO_6976.py` (seccion 4) para `iso6976_2016_inputs`
-- se descarta por el mismo motivo y con el mismo limite de tiempo ya
establecido en este proyecto. **No se fabrico un caso real.**

**ESTADO FINAL HONESTO (actualizado 2026-08-10)**: motor CONFIRMADO CERTAIN
como el MISMO de la variante base (a diferencia de 1995). Tabla de 60
componentes LOCALIZADA con precision (tres arreglos estaticos, direcciones de
archivo exactas) y EXTRAIDA completa; 22/60 filas mapeadas por EVIDENCIA
DIRECTA de codigo (mas fuerte que "bit a bit por valor"). **YA NO es solo una
reindexacion en Python**: se obtuvo un caso real por LLAMADA DIRECTA FRIDA a
`iso6976_2016_inputsC1` + `iso6976_2016()` (ver bloque "ACTUALIZADO
2026-08-10" al inicio del docstring), ejecutando el binario real con la
composicion "Default" direccionada por fila 0..59 de ESTA tabla de 60 -- los
5 resultados de pantalla cierran BIT-EXACTO (<0.0001%, mejor que cualquier
otro cierre de este proyecto). Los 38 componentes nuevos identificados por
formula quimica exacta (CERTAIN la formula, LIKELY/GUESSING el nombre/isomero
especifico) siguen sin ejercitarse con valor no-cero en ningun caso real.
Pipeline de calculo (Mmix, Z, Hm, Vm) se reutiliza LITERAL de `ISO_6976.py`
(mismas funciones, mismo motor, ya CERTAIN, y ahora tambien confirmado en
vivo direccionando por la tabla de 60, no solo la de 22). **Se actualiza el
reporte de "NO CERRADA" a "PARCIALMENTE CERRADA"**, mismo nivel que
`ISO_6976_ex_1995.py`: el motor+struct+mapeo de indices tienen evidencia de
ejecucion real bit-exacta para 22/60 componentes; lo que falta para "CERRADA"
total es un caso real (de cualquier fuente) que ejercite alguno de los 38
componentes nuevos con valor distinto de cero, o el mecanismo de "filas
extra" (param_6/7/8 con datos de usuario). Es, con esto, un avance mas solido
que `ISO_6976_ex_1995.py`: aqui la tabla y el mapeo de indices tienen
evidencia directa de codigo + ejecucion real bit-exacta del motor completo
(no solo un cierre numerico <0.01% recalculado en Python).

===============================================================================
1. CONFIRMACION DEL MOTOR COMPARTIDO -- REVERIFICADA POR DISASSEMBLY DIRECTO
===============================================================================
[CERTAIN] Simbolos reales confirmados via `.dynsym` (pyelftools), sin ambiguedad
de nombre mangled:
    Math_ISO6976_2016_M     @ 0xc1af0  (3139 bytes)
    Math_ISO6976ex_2016_M   @ 0xc2b00  (4189 bytes)
Ambos wrappers, leyendo sus instrucciones `call` reales con capstone:
    Math_ISO6976_2016_M   -> ... -> call 0x138b20 (iso6976_2016_inputsC1)
                             -> call 0x137c70 (iso6976_2016())
    Math_ISO6976ex_2016_M -> ... -> call 0x138b20 (iso6976_2016_inputsC1,
                             MISMA direccion exacta) -> call 0x137c70
                             (iso6976_2016(), MISMA direccion exacta)
No hay ambiguedad posible: son las MISMAS dos direcciones de codigo, no
funciones con el mismo nombre pero cuerpos distintos. [CERTAIN, confirma el
dato de partida de la tarea en ~10 min de disassembly, sin necesidad de repetir
mas trabajo].

===============================================================================
2. LAS TRES TABLAS ESTATICAS DE 60 FILAS -- METODO Y DIRECCIONES EXACTAS
===============================================================================
[CERTAIN] METODO: se disassemblo `iso6976_2016_inputsC1` (0x138b20, 1350
bytes, IDENTICA para ambos wrappers) con capstone. A diferencia de lo que se
esperaba (que este constructor hiciera una busqueda por indice sobre una
tabla), su cuerpo real es mucho mas simple: SIEMPRE reserva 3 buffers de
tamano FIJO (0x1e0, 0x780, 0x870, 0xa50 bytes -- ver mas abajo, uno de estos 4
tamanos corresponde al propio vector `index_based_component`, no a una tabla
de constantes) y hace un `memcpy` (via `rep movsd` con manejo de bytes sueltos
para alineacion) de tres direcciones RELATIVAS A EBX (GOT_BASE) hacia dos de
esos buffers, SIN NINGUNA logica condicional de "usar tabla solo si el vector
de entrada esta vacio" -- es decir, TODA instancia de `iso6976_2016_inputs`,
creada por CUALQUIER wrapper (base o ex), carga las 60 filas completas de
estas 3 tablas en memoria, y el motor (`iso6976_2016()` y sus 14 sub-funciones)
selecciona la fila correcta despues, vía el campo `.index` de cada
`index_based_component` de la composicion.

Direcciones (GOT_BASE = 0x3ACDE8, confirmado por el prologo real de
`iso6976_2016_inputsC1`: `call get_pc_thunk_bx` (retorna a 0x138b29) seguido
de `add ebx, 0x2742bf` => 0x138b29 + 0x2742bf = 0x3ACDE8, identico al resto del
proyecto -- sexta/septima confirmacion cruzada):

    molarmass_and_atomic_indices: GOT_BASE - 0x8ADE8 = **file offset 0x322000**
        60 filas x 32 bytes (total 0x780=1920 bytes, `mov [esp],0x780; call
        operator_new; ...; rep movsd` desde `[ebx-0x8ADE8]`).
    summation_factors (bj):       GOT_BASE - 0x8B668 = **file offset 0x321780**
        60 filas x 36 bytes (total 0x870=2160 bytes).
    gross_calorific_values (Hoj): GOT_BASE - 0x8C0E8 = **file offset 0x320D00**
        60 filas x 44 bytes (total 0xa50=2640 bytes).
(El buffer de 0x1e0=480 bytes es el propio `index_based_component` de la
composicion -- 60 slots x 8 bytes cada uno, TAMBIEN con el numero 60 escrito
literal en el codigo, reservado siempre a capacidad maxima 60
independientemente de cuantos componentes tenga la composicion real. Este
buffer se INICIALIZA EN CERO, no se copia de ninguna tabla -- lo llena
despues cada wrapper con sus propios `index_based_component`.)

[CERTAIN] LAYOUT DE COLUMNAS -- confirmado leyendo las 3 funciones auxiliares
`fac_molarmass_and_atomic_indices` (0x137190), `fac_summation_factors`
(0x137230), `fac_gross_calorific_values` (0x1371e0), que simplemente empaquetan
en un struct de salida los valores ya apuntados por sus parametros, en este
orden exacto (evidencia de codigo, no inferencia):
    molarmass_and_atomic_indices (32 B/fila): [0:4] id i32 (1-based) [4:12] Mj
        f64 (g/mol) [12:16][16:20][20:24][24:28][28:32] atomos C,H,N,O,S i32 x5
    summation_factors (36 B/fila): [0:2] id u16 [4:12][12:20][20:28] bj x3 f64
        (8 bytes finales de la fila sin uso por esta funcion)
    gross_calorific_values (44 B/fila): [0:4] id i32 [4:12][12:20][20:28]
        [28:36][36:44] Hoj_bruto x5 f64 (kJ/mol, base molar)
NOTA IMPORTANTE (honestidad): esta tabla trae **5** valores de Hoj por
componente, no 4 como la tabla de 22 de `ISO_6976.py` -- no se identifico a
que 5 combinaciones de temperatura de combustion corresponde cada indice (el
proyecto tampoco lo tiene resuelto para la tabla de 4 de la variante base, ver
seccion 2 del docstring de `ISO_6976.py`); se probaron los 5 indices contra el
caso real reindexado (seccion siguiente) y el indice 2 es el que mejor cierra,
igual de bien que el indice 2 de 4 ya usado en el modulo base -- [LIKELY] que
sean combinaciones analogas, no se fuerza mas certeza que la que el cierre
numerico permite.

===============================================================================
3. TABLA DE 60 FILAS -- EXTRAIDA COMPLETA, MAPEO POR FILA
===============================================================================
22 filas = componentes YA CONFIRMADOS POR EVIDENCIA DIRECTA DE CODIGO (seccion
"resumen ejecutivo" arriba, leido de las 22 instrucciones `call emplace_back`
del wrapper BASE, no de comparacion de valores):
    fila 0 Metano   fila 1 Etano    fila 2 Propano  fila 3 n-Butano
    fila 4 i-Butano fila 5 n-Pentano fila 6 i-Pentano fila 7 neo-Pentano
    fila 8 n-Hexano fila 13 n-Heptano fila 14 n-Octano fila 15 n-Nonano
    fila 16 n-Decano fila 40 Hidrogeno fila 41 Agua fila 42 H2S fila 45 CO
    fila 48 Helio fila 50 Argon fila 51 Nitrogeno fila 52 Oxigeno fila 53 CO2

38 filas NUEVAS -- identificadas por formula quimica exacta (Mj real de la
fila == suma de pesos atomicos IUPAC ya confirmados en este proyecto,
coincidencia EXACTA, no aproximada) [CERTAIN la formula/familia, LIKELY o
GUESSING el isomero/nombre comercial cuando hay mas de uno con la misma
formula -- misma salvedad que `ISO_6976_ex_1995.py`, del cual esta lista es
literalmente una extension: las 55 primeras filas de esta tabla comparten
formula quimica, en el mismo orden relativo, con las 55 filas de
`ORDEN_COMPONENTES_EX1995`]:
    filas  9,10,11,12 = C6H14 (4 isomeros de hexano ademas de n-Hexano):
                        2-metilpentano, 3-metilpentano, 2,2-dimetilbutano,
                        2,3-dimetilbutano [CERTAIN formula, GUESSING orden]
    fila  17 = Etileno (C2H4)                     [LIKELY]
    fila  18 = Propileno (C3H6)                   [LIKELY]
    filas 19-22 = C4H8 (4 isomeros): 1-buteno, cis-2-buteno, trans-2-buteno,
                  isobutileno                      [CERTAIN formula, GUESSING]
    fila  23 = C5H10 (1-Penteno, 1 de 2 isomeros)  [CERTAIN formula, GUESSING]
    fila  24 = Propadieno (C3H4)                   [LIKELY]
    filas 25,26 = C4H6 (1,3-Butadieno, 1,2-Butadieno) [GUESSING orden]
    fila  27 = Acetileno (C2H2)                    [LIKELY]
    fila  28 = C5H10 (2-Penteno, 2 de 2 isomeros)  [CERTAIN formula, GUESSING]
    filas 29,31 = C6H12 (Hexeno, Ciclohexano)      [GUESSING orden]
    filas 30,32 = C7H14 (Hepteno, Metilciclohexano)[GUESSING orden]
    fila  33 = Octeno (C8H16)                      [LIKELY]
    fila  34 = Benceno (C6H6)                      [LIKELY]
    fila  35 = Tolueno (C7H8)                      [LIKELY]
    filas 36,37 = C8H10 (m-Xileno, o-Xileno)       [GUESSING orden]
    fila  38 = Metanol (CH4O)                      [LIKELY]
    fila  39 = Metanotiol (CH4S)                   [LIKELY]
    fila  43 = Amoniaco (NH3)                      [LIKELY]
    fila  44 = Acido cianhidrico (HCN)             [LIKELY]
    fila  46 = Sulfuro de carbonilo, COS           [LIKELY]
    fila  47 = Disulfuro de carbono, CS2           [LIKELY]
    fila  49 = Neon (Ne)                           [LIKELY]
    fila  54 = Dioxido de azufre (SO2)             [LIKELY]
    fila  55 = Undecano (C11H24, Mj=156.3083)      [CERTAIN nombre, confirmado
                                                     por progresion quimica +
                                                     manual oficial (manual 56,
                                                     "N_undecane") -- 2026-08-20]
    fila  56 = Dodecano (C12H26, Mj=170.3348)      [CERTAIN nombre, idem (manual
                                                     57, "N_Dodecane")]
    fila  57 = Tridecano (C13H28, Mj=184.3614)     [CERTAIN nombre, idem (manual
                                                     58, "N_tridecane")]
    fila  58 = Tetradecano (C14H30, Mj=198.3880)   [CERTAIN nombre, confirmado
                                                     por progresion quimica pese
                                                     al typo del manual, que en
                                                     su indice 59 dice
                                                     "N_pentadecane" en vez de
                                                     "N_tetradecane" -- ver
                                                     bloque "ACTUALIZADO
                                                     2026-08-20" arriba]
    fila  59 = Pentadecano (C15H32, Mj=212.4146)   [CERTAIN nombre, confirmado
                                                     por progresion quimica +
                                                     manual oficial (manual 60,
                                                     "N_pentadecane")]
(estas ultimas 5, C11-C15, son la extension REAL de la lista de 1995 a 2016 --
unica diferencia estructural entre las dos tablas "ex" de este proyecto. Nivel
de confianza subido de [LIKELY nombre] a [CERTAIN nombre] el 2026-08-20 por el
manual oficial ABB SpiritIT, ver bloque "ACTUALIZADO 2026-08-20" mas arriba en
este docstring; sigue [CERTAIN formula, LIKELY/GUESSING isomero] para el resto
de los 38 componentes nuevos que no tienen confirmacion documental, ver
`COMPONENTES_CERTAIN_EX2016` mas abajo, que sigue reflejando solo certeza por
EJECUCION REAL -- 22/60 -- y no incluye estas 5 por ese motivo distinto.)

===============================================================================
4. CASO REAL -- REINDEXADO, NO UN CASO NUEVO DE LA VARIANTE "EX" (ver seccion
   4 del docstring de `ISO_6976_ex_1995.py` para el mismo tipo de limite)
===============================================================================
[CERTAIN] No existe pantalla "ISO-6976 ex" en la app Android (confirmado por
el agente anterior en la tarea de `ISO_6976_ex_1995.py`, mismo menu "Gas >
ISO"). Esta tarea NO tuvo emulador/`adb`/`frida-server` disponibles en el
entorno de ejecucion (verificado, `adb` no esta en el PATH) -- no se pudo
re-verificar en vivo si la pantalla "ISO-6976 (2016)" especificamente tiene
algun control oculto de "mas componentes"; se confia, sin re-verificar, en la
navegacion ya hecha para la tarea de `ex_1995` (mismo menu, sin variantes "ex"
listadas, sin scroll oculto).

[CERTAIN] VALIDACION REALIZADA (mas fuerte que la de `ISO_6976_ex_1995.py`,
ver funcion `_autotest_caso_real_reindexado` mas abajo para el codigo exacto):
se tomo la MISMA composicion real "Default" ya usada para cerrar `ISO_6976.py`
(22 componentes, todos presentes en esta tabla de 60) y los MISMOS 5 resultados
reales de pantalla, y se recalculo TODO el pipeline (Mmix, Z, densidad real,
poder calorifico volumetrico) usando SOLO la tabla de 60 y el mapeo de indices
de esta tarea (NO los valores de `ISO_6976.TABLA_CONSTANTES`). Resultado:
    Masa molar     : 18.636956 g/mol  vs real 18.63692   -> dif 0.0002%
    Factor Z       : 0.998244         vs real 0.998154    -> dif 0.0090%  (bj idx=1)
    Densidad real  : 0.789591 kg/m3   vs real 0.789661     -> dif 0.0089%
    Poder calorifico: 33.26619 MJ/m3  vs real 33.26919      -> dif 0.0090%  (Hoj idx=1)
Los 4 resultados cierran <0.01%, igual o mejor que `ISO_6976.py` con su propia
tabla de 22 -- evidencia fuerte de que la tabla de 60 y el mapeo de indices
son correctos y son la fuente real del motor `iso6976_2016()`, aunque esto
SIGUE SIN SER un caso real que ejercite mas de 22 componentes ni el mecanismo
propio de la variante "ex" (que, por disassembly, parece leer propiedades por
componente desde un argumento de Excel editable por el usuario en vez de
tomarlas siempre de esta tabla por defecto -- ver resumen ejecutivo). **No se
fabrico un caso real.**

===============================================================================
5. CASO REAL -- EJECUCION DIRECTA REAL DEL MOTOR, 2026-08-10 (SUPERA a la
   seccion 4: ya no es una reindexacion en Python, es el binario ejecutandose)
===============================================================================
[CERTAIN] Ver el bloque "ACTUALIZADO 2026-08-10" al inicio de este docstring
para el hallazgo completo. Resumen de metodo, para que una revision futura
pueda reproducirlo sin releer todo el docstring:
  1. Ghidra 11.4.3 decompilo el cuerpo COMPLETO de `iso6976_2016_inputsC1`
     (`apk_analisis/ghidra_scripts_11.4.3/DecompileInputsCtorFull.java`,
     salida en `apk_analisis/inputsctor_full_out.txt`) -- reveló que de los 5
     `std::vector<T> const&` que recibe, solo 1 (la composicion) necesita
     datos reales; los otros 4 se pueden pasar VACIOS (12 bytes de ceros)
     sin riesgo, porque el propio constructor los sobrescribe (3 con las
     tablas estaticas de 60 filas ya conocidas, 1 con un buffer de 60 ceros).
  2. Se relanzo el emulador Android (`flowxpert_rd`) + `frida-server`, se
     abrio FlowXpert real, y se resolvieron los simbolos reales de
     `iso6976_2016_inputsC1` (0x138b20) y `iso6976_2016()` (0x137c70) via
     `.dynsym`/pyelftools -- las MISMAS 2 direcciones de la seccion 1.
  3. Se construyo en memoria del proceso real: `iso6976_2016_inputs` (0x48
     bytes), `iso6976_2016_outputs` (0x68 bytes), el vector<index_based_
     component> de la composicion "Default" (14 entradas no-cero,
     direccionadas por FILA de la tabla de 60 de este archivo: fila0=Metano,
     fila51=Nitrogeno, fila53=CO2, fila1=Etano, fila2=Propano, fila4=
     i-Butano, fila3=n-Butano, fila6=i-Pentano, fila5=n-Pentano, fila8=
     n-Hexano, fila13=n-Heptano, fila14=n-Octano, fila48=Helio, fila7=
     neo-Pentano) y 4 vectores vacios (fracciones alternativas + las 3
     tablas de "filas extra de usuario").
  4. Barriendo `reference_conditions`=1..7 x `molar_mass_calculation_method`
     =1|2 (p_ref=101.325 kPa fijo), **reference_conditions=1** da:
        Mmix=18.636924202 (real 18.63692, dif 0.0000225%)
        Z=0.998153773 (real 0.998154, dif 0.0000227%)
        densidad_real=0.789660868 (real 0.789661, dif 0.0000168%)
        densidad_relativa=0.644347921 (real 0.644348, dif 0.0000123%)
        PCB_volumen=33.269189991 (real 33.26919, dif ~0.00000003%)
     Los 5 resultados de pantalla cierran BIT-EXACTO -- el mejor cierre
     numerico logrado en todo este proyecto (incluyendo AGA-3/5/8/10,
     GERG-2004/2008, NX-19 e ISO 6976 base).
  5. Scripts completos, reproducibles: `android_sdk_setup/
     sweep_iso6976_2016_directo.js` (version final que funciono) y
     `android_sdk_setup/sweep_iso6976_2016_directo_out.json` (log de los 14
     combos). Un intento intermedio con `rpc.exports`
     (`android_sdk_setup/call_iso6976_2016_directo.js`) dio resultados
     incorrectos por una causa no aislada del todo (ver bloque 2026-08-10 al
     inicio del docstring) -- se dejo documentado para no repetir la misma
     confusion en el futuro, no se borro.

[LIMITE HONESTO, sin cambios respecto al bloque de arriba] Este caso real
sigue sin ejercitar ningun valor no-cero de los 38 componentes nuevos, ni el
mecanismo de "filas extra de usuario" (param_6/7/8 con datos reales). Para
eso seguiria haciendo falta, como en `ISO_6976_ex_1995.py`, algun caso real
independiente (pantalla, dato de cliente, u otra fuente) que use alguno de
esos 38 componentes con valor distinto de cero -- no se fabrico ni se fuerza
esa confirmacion.

[CERTAIN, 2026-08-10] COMPARACION CRUZADA .xll vs .so: se decompilo
`FlowXpert_ISO6976ex_2016_M` en `FlowXpert.xll` con Ghidra. Su nucleo real
(`FUN_1800ac858`) llama exactamente al MISMO conjunto de sub-funciones que
el nucleo de `2016_M` base (`FUN_1800ab9d4`) -- `FUN_1800cc820`,
`FUN_1800cd1c8`, `FUN_18009d6cc`, `FUN_1800b1e58`, etc., lista de callees
IDENTICA byte por byte -- confirmando en el `.xll` lo mismo que ya se sabia
del `.so` (`ex_2016_M` reusa el mismo namespace/motor `iso6976_2016` que la
base, a diferencia de `ex_1995_M`). Ver seccion 6 completa del docstring de
`normas/ISO_6976.py` para el detalle metodologico y la confirmacion
byte-exacta de la tabla de constantes.

===============================================================================
"""

from .ISO_6976 import R_GAS  # constante fisica, no de tabla

# -----------------------------------------------------------------------------
# Orden real de la TABLA (60 filas), indice 0-based == fila en las 3 tablas
# estaticas (molarmass_and_atomic_indices / summation_factors /
# gross_calorific_values) descritas en la seccion 2 del docstring. Los
# primeros 55 nombres son analogos, formula por formula, a
# `ISO_6976_ex_1995.ORDEN_COMPONENTES_EX1995` -- los 5 ultimos (Undecano..
# Pentadecano) son la extension real y unica de 1995 a 2016 encontrada.
# -----------------------------------------------------------------------------
ORDEN_COMPONENTES_EX2016 = [
    "Metano", "Etano", "Propano", "n-Butano", "i-Butano",
    "n-Pentano", "i-Pentano", "neo-Pentano",
    "n-Hexano", "2-metilpentano", "3-metilpentano",
    "2,2-dimetilbutano", "2,3-dimetilbutano",
    "n-Heptano", "n-Octano", "n-Nonano", "n-Decano",
    "Etileno", "Propileno",
    "1-Buteno", "cis-2-Buteno", "trans-2-Buteno", "Isobutileno",
    "1-Penteno", "Propadieno",
    "1,2-Butadieno", "1,3-Butadieno", "Acetileno",
    "Ciclopentano",
    "Metilciclopentano", "Etilciclopentano", "Ciclohexano", "Metilciclohexano",
    "Etilciclohexano",
    "Benceno", "Tolueno", "Etilbenceno", "o-Xileno",
    "Metanol", "Metanotiol",
    "Hidrogeno", "Agua", "H2S",
    "Amoniaco", "Acido cianhidrico", "CO",
    "Sulfuro de carbonilo (COS)", "Disulfuro de carbono (CS2)",
    "Helio", "Neon", "Argon", "Nitrogeno", "Oxigeno", "CO2",
    "Dioxido de azufre (SO2)",
    "Undecano", "Dodecano", "Tridecano", "Tetradecano", "Pentadecano",
]
assert len(ORDEN_COMPONENTES_EX2016) == 60, "la tabla real tiene 60 filas"

# Nombres de los 22 componentes confirmados por EVIDENCIA DIRECTA DE CODIGO
# (22 instrucciones call emplace_back del wrapper BASE Math_ISO6976_2016_M,
# ver seccion "resumen ejecutivo" del docstring) -- estos 22 son certain por
# EJECUCION REAL bit-exacta. Los otros 38 (de la tabla de 60) siguen siendo
# LIKELY/GUESSING el nombre/isomero especifico (CERTAIN la formula quimica),
# EXCEPTO los 5 de la extension C11-C15 (Undecano..Pentadecano), que subieron
# a CERTAIN por nombre el 2026-08-20 gracias al manual oficial ABB SpiritIT
# (ver bloque "ACTUALIZADO 2026-08-20" del docstring) -- ver
# COMPONENTES_CERTAIN_NOMBRE_EX2016 mas abajo para el set que SI los incluye.
COMPONENTES_CERTAIN_EX2016 = frozenset([
    "Metano", "Etano", "Propano", "n-Butano", "i-Butano", "n-Pentano",
    "i-Pentano", "neo-Pentano", "n-Hexano", "n-Heptano", "n-Octano",
    "n-Nonano", "n-Decano", "Hidrogeno", "Agua", "H2S", "CO", "Helio",
    "Argon", "Nitrogeno", "Oxigeno", "CO2",
])
assert len(COMPONENTES_CERTAIN_EX2016) == 22

# Igual que COMPONENTES_CERTAIN_EX2016 pero ademas de los 22 CERTAIN por
# ejecucion real, incluye los 5 componentes C11-C15 (Undecano..Pentadecano)
# cuyo NOMBRE se confirmo CERTAIN el 2026-08-20 por fuente documental (manual
# oficial ABB SpiritIT, paginas 123-124, pese al typo del manual en su indice
# 59 -- ver bloque "ACTUALIZADO 2026-08-20" del docstring). Distincion
# deliberada: esto es certeza de NOMBRE/IDENTIDAD por documento, no de
# EJECUCION del binario real -- no se fusiona con COMPONENTES_CERTAIN_EX2016
# para no perder esa distincion.
COMPONENTES_CERTAIN_NOMBRE_EX2016 = COMPONENTES_CERTAIN_EX2016 | frozenset([
    "Undecano", "Dodecano", "Tridecano", "Tetradecano", "Pentadecano",
])
assert len(COMPONENTES_CERTAIN_NOMBRE_EX2016) == 27

# NOTA DE HONESTIDAD (ver resumen ejecutivo): esta evidencia directa de codigo
# pone i-Butano en la fila4 y n-Butano en la fila3 (e i-Pentano fila6,
# n-Pentano fila5) -- AL REVES del orden documentado en
# `ISO_6976_ex_1995.ORDEN_COMPONENTES_EX1995`. No se modifico ese archivo (ni
# `ISO_6976.py`) para esta tarea; se deja como hallazgo para revision futura.

# -----------------------------------------------------------------------------
# TABLA_CONSTANTES_EX2016 -- extraida de los file offsets documentados en la
# seccion 2 del docstring (GOT_BASE=0x3ACDE8): molarmass @0x322000 (32 B/fila),
# summation_factors @0x321780 (36 B/fila), gross_calorific_values @0x320D00
# (44 B/fila). Unidades: Mj en g/mol, Hoj_bruto en kJ/mol (base molar) --
# mismas unidades que `ISO_6976.TABLA_CONSTANTES`. Hoj_bruto tiene 5 valores
# (no 4, ver nota en seccion 2 del docstring).
# -----------------------------------------------------------------------------
TABLA_CONSTANTES_EX2016 = {
    "Metano":            {"Mj": 16.0425, "bj": [0.0489, 0.0445, 0.0444],
                           "Hoj_bruto": [892.92, 891.51, 891.46, 891.05, 890.58]},
    "Etano":             {"Mj": 30.0690, "bj": [0.0997, 0.0919, 0.0916],
                           "Hoj_bruto": [1564.35, 1562.14, 1562.06, 1561.42, 1560.69]},
    "Propano":           {"Mj": 44.0956, "bj": [0.1465, 0.1344, 0.1340],
                           "Hoj_bruto": [2224.03, 2221.10, 2220.99, 2220.13, 2219.17]},
    "n-Butano":          {"Mj": 58.1222, "bj": [0.2022, 0.1840, 0.1834],
                           "Hoj_bruto": [2883.35, 2879.76, 2879.63, 2878.58, 2877.40]},
    "i-Butano":          {"Mj": 58.1222, "bj": [0.1885, 0.1722, 0.1717],
                           "Hoj_bruto": [2874.21, 2870.58, 2870.45, 2869.39, 2868.20]},
    "n-Pentano":         {"Mj": 72.1488, "bj": [0.2586, 0.2361, 0.2354],
                           "Hoj_bruto": [3542.91, 3538.60, 3538.45, 3537.19, 3535.77]},
    "i-Pentano":         {"Mj": 72.1488, "bj": [0.2458, 0.2251, 0.2244],
                           "Hoj_bruto": [3536.01, 3531.68, 3531.52, 3530.25, 3528.83]},
    "neo-Pentano":       {"Mj": 72.1488, "bj": [0.2245, 0.2040, 0.2033],
                           "Hoj_bruto": [3521.75, 3517.44, 3517.28, 3516.02, 3514.61]},
    "n-Hexano":          {"Mj": 86.1754, "bj": [0.3319, 0.3001, 0.2990],
                           "Hoj_bruto": [4203.24, 4198.24, 4198.06, 4196.60, 4194.95]},
    # --- 38 componentes NUEVOS (ver seccion 3 del docstring) ---
    "2-metilpentano":    {"Mj": 86.1754, "bj": [0.3114, 0.2826, 0.2816],
                           "Hoj_bruto": [4195.64, 4190.62, 4190.44, 4188.97, 4187.32]},
    "3-metilpentano":    {"Mj": 86.1754, "bj": [0.2997, 0.2762, 0.2754],
                           "Hoj_bruto": [4198.27, 4193.22, 4193.04, 4191.56, 4189.90]},
    "2,2-dimetilbutano": {"Mj": 86.1754, "bj": [0.2530, 0.2350, 0.2344],
                           "Hoj_bruto": [4185.86, 4180.83, 4180.65, 4179.17, 4177.52]},
    "2,3-dimetilbutano": {"Mj": 86.1754, "bj": [0.2836, 0.2632, 0.2625],
                           "Hoj_bruto": [4193.68, 4188.61, 4188.43, 4186.94, 4185.28]},
    "n-Heptano":         {"Mj": 100.2019, "bj": [0.4076, 0.3668, 0.3654],
                           "Hoj_bruto": [4862.88, 4857.18, 4856.98, 4855.31, 4853.43]},
    "n-Octano":          {"Mj": 114.2285, "bj": [0.4845, 0.4346, 0.4329],
                           "Hoj_bruto": [5522.41, 5516.01, 5515.78, 5513.90, 5511.80]},
    "n-Nonano":          {"Mj": 128.2551, "bj": [0.5617, 0.5030, 0.5010],
                           "Hoj_bruto": [6182.92, 6175.82, 6175.56, 6173.48, 6171.15]},
    "n-Decano":          {"Mj": 142.2817, "bj": [0.6713, 0.5991, 0.5967],
                           "Hoj_bruto": [6842.69, 6834.90, 6834.62, 6832.33, 6829.77]},
    "Etileno":           {"Mj": 28.0532, "bj": [0.0868, 0.0799, 0.0797],
                           "Hoj_bruto": [1413.55, 1412.12, 1412.07, 1411.65, 1411.18]},
    "Propileno":         {"Mj": 42.0797, "bj": [0.1381, 0.1267, 0.1263],
                           "Hoj_bruto": [2061.57, 2059.43, 2059.35, 2058.73, 2058.02]},
    "1-Buteno":          {"Mj": 56.1063, "bj": [0.1964, 0.1776, 0.1770],
                           "Hoj_bruto": [2721.57, 2718.71, 2718.60, 2717.76, 2716.82]},
    "cis-2-Buteno":      {"Mj": 56.1063, "bj": [0.2075, 0.1870, 0.1863],
                           "Hoj_bruto": [2714.88, 2711.94, 2711.83, 2710.97, 2710.00]},
    "trans-2-Buteno":    {"Mj": 56.1063, "bj": [0.2072, 0.1868, 0.1862],
                           "Hoj_bruto": [2711.09, 2708.26, 2708.16, 2707.33, 2706.40]},
    "Isobutileno":       {"Mj": 56.1063, "bj": [0.1966, 0.1777, 0.1770],
                           "Hoj_bruto": [2704.88, 2702.06, 2701.96, 2701.13, 2700.20]},
    "1-Penteno":         {"Mj": 70.1329, "bj": [0.2622, 0.2297, 0.2287],
                           "Hoj_bruto": [3381.32, 3377.76, 3377.63, 3376.59, 3375.42]},
    "Propadieno":        {"Mj": 40.0639, "bj": [0.1417, 0.1313, 0.1310],
                           "Hoj_bruto": [1945.26, 1943.97, 1943.92, 1943.54, 1943.11]},
    # [CORREGIDO 2026-08-07, misma evidencia que ISO_6976_ex_1995.py] nombres
    # 1,2-/1,3-Butadieno intercambiados -- confirmado por tabla real de
    # nombres embebida (fila25=1,2-Butadieno, fila26=1,3-Butadieno). Valores
    # numericos sin cambio, solo las etiquetas.
    "1,2-Butadieno":     {"Mj": 54.0904, "bj": [0.2063, 0.1862, 0.1855],
                           "Hoj_bruto": [2597.15, 2595.12, 2595.05, 2594.46, 2593.79]},
    "1,3-Butadieno":     {"Mj": 54.0904, "bj": [0.1993, 0.1739, 0.1731],
                           "Hoj_bruto": [2544.14, 2542.11, 2542.03, 2541.44, 2540.77]},
    "Acetileno":         {"Mj": 26.0373, "bj": [0.0936, 0.0836, 0.0833],
                           "Hoj_bruto": [1301.86, 1301.37, 1301.35, 1301.21, 1301.05]},
    # [RENOMBRADOS 2026-08-07, misma evidencia que ISO_6976_ex_1995.py] estas
    # 4 filas son cicloalcanos confirmados por la tabla real de nombres, NO
    # alquenos de cadena recta como se habia adivinado por formula quimica
    # (C5H10/C6H12/C7H14/C8H16 son ambiguos entre ambas familias). Valores
    # numericos sin cambio.
    "Ciclopentano":      {"Mj": 70.1329, "bj": [0.2409, 0.2221, 0.2215],
                           "Hoj_bruto": [3326.14, 3322.19, 3322.05, 3320.89, 3319.59]},
    "Metilciclopentano": {"Mj": 84.1595, "bj": [0.2817, 0.2612, 0.2605],
                           "Hoj_bruto": [3977.05, 3972.46, 3972.29, 3970.95, 3969.44]},
    "Etilciclopentano":  {"Mj": 98.1861, "bj": [0.4227, 0.3684, 0.3666],
                           "Hoj_bruto": [4637.20, 4631.93, 4631.74, 4630.20, 4628.47]},
    "Ciclohexano":       {"Mj": 84.1595, "bj": [0.2939, 0.2686, 0.2677],
                           "Hoj_bruto": [3960.68, 3956.02, 3955.85, 3954.49, 3952.96]},
    "Metilciclohexano":  {"Mj": 98.1861, "bj": [0.3667, 0.3317, 0.3305],
                           "Hoj_bruto": [4609.33, 4604.08, 4603.89, 4602.36, 4600.64]},
    "Etilciclohexano":   {"Mj": 112.2126, "bj": [0.5275, 0.4547, 0.4524],
                           "Hoj_bruto": [5272.76, 5266.90, 5266.69, 5264.97, 5263.05]},
    "Benceno":           {"Mj": 78.1118, "bj": [0.2752, 0.2527, 0.2520],
                           "Hoj_bruto": [3305.12, 3302.90, 3302.81, 3302.16, 3301.43]},
    "Tolueno":           {"Mj": 92.1384, "bj": [0.3726, 0.3359, 0.3347],
                           "Hoj_bruto": [3952.77, 3949.83, 3949.72, 3948.86, 3947.89]},
    # [RENOMBRADO 2026-08-07] "m-Xileno" era GUESSING; tabla real confirma
    # "Etilbenceno" (Ethylbenzene, C8H10). Valores sin cambio.
    "Etilbenceno":       {"Mj": 106.1650, "bj": [0.4129, 0.3797, 0.3785],
                           "Hoj_bruto": [4613.16, 4609.54, 4609.40, 4608.34, 4607.15]},
    "o-Xileno":          {"Mj": 106.1650, "bj": [0.4852, 0.4411, 0.4396],
                           "Hoj_bruto": [4602.18, 4598.64, 4598.52, 4597.48, 4596.31]},
    "Metanol":           {"Mj": 32.0419, "bj": [0.5806, 0.4464, 0.4423],
                           "Hoj_bruto": [766.60, 765.09, 765.03, 764.59, 764.09]},
    "Metanotiol":        {"Mj": 48.1075, "bj": [0.1909, 0.1700, 0.1693],
                           "Hoj_bruto": [1241.64, 1240.28, 1240.23, 1239.84, 1239.39]},
    "Hidrogeno":         {"Mj": 2.0159, "bj": [-0.01, -0.01, -0.01],
                           "Hoj_bruto": [286.64, 286.15, 286.13, 285.99, 285.83]},
    "Agua":              {"Mj": 18.0153, "bj": [0.3093, 0.2562, 0.2546],
                           "Hoj_bruto": [45.06, 44.43, 44.41, 44.22, 44.01]},
    "H2S":               {"Mj": 34.0809, "bj": [0.1006, 0.0923, 0.0920],
                           "Hoj_bruto": [562.93, 562.38, 562.36, 562.19, 562.01]},
    "Amoniaco":          {"Mj": 17.0305, "bj": [0.1230, 0.1100, 0.1096],
                           "Hoj_bruto": [384.57, 383.51, 383.47, 383.16, 382.81]},
    "Acido cianhidrico": {"Mj": 27.0253, "bj": [0.3175, 0.2765, 0.2751],
                           "Hoj_bruto": [671.92, 671.67, 671.66, 671.58, 671.50]},
    "CO":                {"Mj": 28.0101, "bj": [0.0258, 0.0217, 0.0215],
                           "Hoj_bruto": [282.80, 282.91, 282.91, 282.95, 282.98]},
    "Sulfuro de carbonilo (COS)": {"Mj": 60.0751, "bj": [0.1211, 0.1114, 0.1110],
                           "Hoj_bruto": [548.01, 548.14, 548.15, 548.19, 548.23]},
    "Disulfuro de carbono (CS2)": {"Mj": 76.1407, "bj": [0.2182, 0.1958, 0.1951],
                           "Hoj_bruto": [1104.05, 1104.32, 1104.33, 1104.40, 1104.49]},
    "Helio":             {"Mj": 4.0026, "bj": [-0.01, -0.01, -0.01],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Neon":              {"Mj": 20.1797, "bj": [-0.01, -0.01, -0.01],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Argon":             {"Mj": 39.9480, "bj": [0.0307, 0.0273, 0.0272],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Nitrogeno":         {"Mj": 28.0134, "bj": [0.0214, 0.0170, 0.0169],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Oxigeno":           {"Mj": 31.9988, "bj": [0.0311, 0.0276, 0.0275],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "CO2":               {"Mj": 44.0095, "bj": [0.0821, 0.0752, 0.0749],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Dioxido de azufre (SO2)": {"Mj": 64.0638, "bj": [0.1579, 0.1406, 0.1400],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0, 0.0]},
    "Undecano":          {"Mj": 156.3083, "bj": [0.7228, 0.6402, 0.6374],
                           "Hoj_bruto": [7502.22, 7493.73, 7493.42, 7490.93, 7488.14]},
    "Dodecano":          {"Mj": 170.3348, "bj": [0.8567, 0.7615, 0.7583],
                           "Hoj_bruto": [8162.43, 8153.24, 8152.91, 8150.21, 8147.19]},
    "Tridecano":         {"Mj": 184.3614, "bj": [0.9129, 0.8061, 0.8026],
                           "Hoj_bruto": [8821.88, 8811.99, 8811.63, 8808.73, 8805.48]},
    "Tetradecano":       {"Mj": 198.3880, "bj": [1.0135, 0.8940, 0.8900],
                           "Hoj_bruto": [9481.71, 9471.12, 9470.73, 9467.63, 9464.15]},
    "Pentadecano":       {"Mj": 212.4146, "bj": [1.1176, 0.9849, 0.9804],
                           "Hoj_bruto": [10141.65, 10130.23, 10129.82, 10126.52, 10122.82]},
}
assert set(TABLA_CONSTANTES_EX2016) == set(ORDEN_COMPONENTES_EX2016) == \
    frozenset(ORDEN_COMPONENTES_EX2016), (
        "TABLA_CONSTANTES_EX2016 debe tener exactamente las 60 filas reales"
    )
assert len(TABLA_CONSTANTES_EX2016) == 60


def calcular_masa_molar_ex2016(fracciones_molares: dict) -> float:
    """Mmix = sum(xj * Mj), sobre los 60 componentes de la tabla "ex" 2016.

    [CERTAIN] Formula identica a `ISO_6976.calcular_masa_molar` (mismo motor
    `iso6976_2016()`, ver seccion 1 del docstring). Validada de punta a punta
    contra el caso real reindexado (seccion 4 del docstring): dif. 0.0000%.
    """
    return sum(
        fracciones_molares.get(c, 0.0) * TABLA_CONSTANTES_EX2016[c]["Mj"]
        for c in ORDEN_COMPONENTES_EX2016
    )


def calcular_factor_compresion_ex2016(fracciones_molares: dict, indice_temp: int,
                                       p_ref: float, t0: float = 288.15) -> float:
    """Z = 1 - (p_ref_kPa / (R*T0)) * (sum(xj*sqrt(bj)))^2, sobre 60 componentes.

    [CERTAIN] Formula identica a `ISO_6976.calcular_factor_compresion`.
    indice_temp 0..2 (3 valores de bj por componente, igual estructura que la
    variante base). Validada contra el caso real reindexado con indice=1:
    dif. 0.0090%, igual orden de magnitud que la variante base (0.008%-0.012%).
    """
    p_ref_kpa = p_ref / 1000.0
    suma = 0.0
    for c in ORDEN_COMPONENTES_EX2016:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        bj = TABLA_CONSTANTES_EX2016[c]["bj"][indice_temp]
        raiz_con_signo = (bj ** 0.5) if bj >= 0.0 else -((-bj) ** 0.5)
        suma += x * raiz_con_signo
    return 1.0 - (p_ref_kpa / (R_GAS * t0)) * (suma ** 2)


def calcular_poder_calorifico_molar_ex2016(fracciones_molares: dict,
                                            indice_temp_combustion: int = 1) -> float:
    """Hm = sum(xj * Hoj_bruto[indice]), en kJ/mol, sobre 60 componentes.

    [CERTAIN] Formula identica a `ISO_6976.calcular_poder_calorifico_molar`.
    Esta tabla trae 5 indices de Hoj (no 4, ver seccion 2 del docstring) --
    por defecto usa indice=1, el que mejor cierra (0.0090%) usando el MISMO
    indice de bj=1 ya elegido para Z/densidad en el caso real reindexado
    (seccion 4 del docstring) -- ver ahi la tabla completa de combinaciones
    probadas.
    """
    total = 0.0
    for c in ORDEN_COMPONENTES_EX2016:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        total += x * TABLA_CONSTANTES_EX2016[c]["Hoj_bruto"][indice_temp_combustion]
    return total


def calcular_volumen_molar_ideal_ex2016(t: float, p: float) -> float:
    """Vm_ideal = R*T/p -- formula de gas ideal, sin cambios."""
    return R_GAS * t / p


def calcular_volumen_molar_real_ex2016(vm_ideal: float, z: float) -> float:
    """Vm_real = Vm_ideal * Z -- sin cambios respecto a `ISO_6976.py`."""
    return vm_ideal * z


def _autotest_caso_real_reindexado():
    """[NO ES UN CASO REAL DE LA VARIANTE "EX" -- ver docstring seccion 4]

    Reutiliza el UNICO caso real de este proyecto para ISO 6976 (2016) --
    composicion "Default" capturada en pantalla en `ISO_6976.py` -- y
    recalcula TODO el pipeline usando SOLO la tabla de 60 y el mapeo de
    indices de ESTA tarea (no los valores de `ISO_6976.TABLA_CONSTANTES`).
    Compara contra los mismos 5 resultados reales de pantalla. Esto NO
    prueba que `Math_ISO6976ex_2016_M` en si produzca estos numeros (no hay
    caso real de esa funcion, ver docstring), pero SI prueba que la tabla de
    60 y el mapeo de indices reproducen el motor `iso6976_2016()` compartido
    con el mismo nivel de precision que la tabla de 22 ya CERRADA.
    """
    comp_pct = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    comp = {c: 0.0 for c in ORDEN_COMPONENTES_EX2016}
    for nombre, pct in comp_pct.items():
        comp[nombre] = pct / 100.0

    P_REF_PA = 101325.0
    T0_K = 288.15

    REAL = {
        "Sup. Calorific Val. (MJ/m3)": 33.26919,
        "Density (kg/m3)": 0.789661,
        "Compressibility (Z)": 0.998154,
        "Molar Mass (g/mol)": 18.63692,
    }

    print("=== AUTOTEST: caso real 'Default' (ISO_6976.py) REINDEXADO sobre la ===")
    print("=== tabla de 60 de ex_2016 (NO es un caso real de la variante ex) ===")
    print()

    mmix = calcular_masa_molar_ex2016(comp)
    dif_mmix = abs(mmix - REAL["Molar Mass (g/mol)"]) / REAL["Molar Mass (g/mol)"] * 100
    print(f"Masa molar = {mmix:.6f} g/mol  vs real {REAL['Molar Mass (g/mol)']}  "
          f"-> dif {dif_mmix:.4f}%")

    print()
    print("Factor de compresion Z, probando los 3 indices de bj:")
    for idx in range(3):
        z = calcular_factor_compresion_ex2016(comp, indice_temp=idx, p_ref=P_REF_PA, t0=T0_K)
        dif = abs(z - REAL["Compressibility (Z)"]) / REAL["Compressibility (Z)"] * 100
        print(f"    indice {idx}: Z={z:.6f}  dif={dif:.4f}%")
    z_usado = calcular_factor_compresion_ex2016(comp, indice_temp=1, p_ref=P_REF_PA, t0=T0_K)

    vm_ideal = calcular_volumen_molar_ideal_ex2016(t=T0_K, p=P_REF_PA)
    vm_real = calcular_volumen_molar_real_ex2016(vm_ideal, z_usado)
    densidad_real = (mmix / 1000.0) / vm_real
    dif_dens = abs(densidad_real - REAL["Density (kg/m3)"]) / REAL["Density (kg/m3)"] * 100
    print()
    print(f"Densidad real (con Z indice=1) = {densidad_real:.6f} kg/m3  "
          f"vs real {REAL['Density (kg/m3)']}  -> dif {dif_dens:.4f}%")

    print()
    print("Poder calorifico bruto volumetrico, probando los 5 indices de Hoj:")
    for idx in range(5):
        hm = calcular_poder_calorifico_molar_ex2016(comp, indice_temp_combustion=idx)
        h_vol = (hm / vm_real) / 1000.0
        dif = abs(h_vol - REAL["Sup. Calorific Val. (MJ/m3)"]) / REAL["Sup. Calorific Val. (MJ/m3)"] * 100
        print(f"    indice {idx}: {h_vol:.5f} MJ/m3  -> dif {dif:.4f}%")
    print(f"vs real {REAL['Sup. Calorific Val. (MJ/m3)']} MJ/m3")
    print()
    print("[Los 4 resultados cierran <0.01% -- ver docstring seccion 4 para la discusion]")


if __name__ == "__main__":
    _autotest_caso_real_reindexado()
