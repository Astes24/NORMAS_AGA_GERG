# -*- coding: utf-8 -*-
"""
normas/ISO_6976_ex_1995.py
=============================
===============================================================================
*** ACTUALIZADO 2026-08-08 (RONDA 3, tarea de continuacion) -- CASO REAL
    CONSEGUIDO POR LLAMADA DIRECTA FRIDA A `calculate_revision_1`. Este es el
    avance mas grande de este archivo desde que se creo: se reevaluo si la
    firma de `calculate_revision_1` era construible a mano (la RONDA 2 de
    esta misma fecha ya habia decompilado el cuerpo completo pero no habia
    llegado a intentar la llamada), y la respuesta es SI -- la firma real es
    MUCHO mas simple que `iso6976_2016_inputs` (nada de `std::vector`/heap
    propio, solo 3 words):

        undefined4 calculate_revision_1(uint *composicion, uint conditions,
            int molar_mass_method, int cv_method, double *results)

    con `composicion` = puntero a un struct POD de 12 bytes {uint32 count;
    double* fractions; void* extra_table_o_NULL} -- confirmado LEYENDO EL
    CUERPO COMPLETO decompilado (Ghidra 11.4.3, `apk_analisis/task5obj_out.txt`,
    OBJETIVO 4, ya generado en la RONDA 2 de este mismo dia, solo que esta
    ronda SI lo uso para construir el struct en vez de solo leerlo), no
    adivinado del disassembly parcial de sesiones previas. `results` es un
    struct POD de 11 doubles (88 bytes, confirmado por el bucle de zeroing
    inicial de 22 dwords). Se construyo el struct en memoria con
    `Memory.alloc`+`writeDouble`/`writeU32` (mismo patron ya usado con exito
    para AGA-3/GERG, NUNCA antes intentado aqui porque la RONDA 1 solo conocia
    el disassembly parcial y sobreestimo el riesgo) y se llamo la funcion REAL
    dentro del proceso vivo de FlowXpert (PID 2880, emulador + frida-server ya
    corriendo) con la composicion real "Default" ya conocida. Scripts:
    `android_sdk_setup/call_iso6976_ex1995_directo.js` (construccion del
    struct + `rpc.exports`) y
    `android_sdk_setup/run_call_iso6976_ex1995_directo.py` (barrido de las 24
    combinaciones conditions=0..5 x molar_mass_method=1|2 x
    cv_calculation_method=1|2, log completo en
    `android_sdk_setup/call_iso6976_ex1995_directo_out.json`).

    [CERTAIN, HALLAZGO PRINCIPAL] Con conditions=0, molar_mass_method=1,
    cv_calculation_method=1, la llamada REAL a `calculate_revision_1` con la
    composicion "Default" (22 componentes conocidos, ninguno de los 33 nuevos)
    devuelve Mmix=18.6372061008 g/mol y Z=0.998136265018026 -- estos son
    PRACTICAMENTE IDENTICOS (Mmix bit-exacto a 6 decimales, Z bit-exacto a 4
    decimales) a los valores YA VALIDADOS por pantalla real en
    `ISO_6976_1995.py` (Molar Mass=18.637206 g/mol, Compressibility=0.998136,
    motor `PropertiesISO6976_1995_rev1`, DISTINTO de `calculate_revision_1`).
    Esto prueba, de la forma mas fuerte posible sin una pantalla dedicada a
    "ex": (1) el struct `composicion`/`results` construido a mano tiene el
    layout EXACTO correcto (si estuviera mal, Mmix/Z no cerrarian ni remotamente
    con el valor real); (2) los DOS motores distintos de 1995 (el "corto"
    `PropertiesISO6976_1995_rev1` de la variante base y el "largo"
    `calculate_revision_1` de la variante "ex") dan el MISMO resultado para la
    MISMA composicion/condiciones -- consistente con que ambos implementan la
    misma fisica ISO 6976:1995 sobre el mismo subconjunto de 22 componentes,
    solo que uno soporta 55. Limite honesto: esta composicion NO ejercita
    ninguno de los 33 componentes nuevos de la tabla de 55, asi que NO
    confirma sus valores de Mj/bj/Hoj contra ejecucion real (solo contra
    formula quimica, ver seccion 3 sin cambios) -- pero SI confirma que el
    MOTOR/PIPELINE que los va a consumir (`calculate_revision_1`) funciona
    exactamente como se documento por decompilacion, con datos reales.

    [CERTAIN, BUG REAL ENCONTRADO Y CORREGIDO EN ESTE ARCHIVO] La formula de Z
    que este archivo usaba ANTES de esta ronda (`Z = 1 - (p_ref_kPa/(R*T0)) *
    (suma(xj*sqrt(bj)))^2`, copiada por similitud de `ISO_6976.py`) es
    INCORRECTA para `calculate_revision_1`. La llamada real, aislando un solo
    componente por vez (composicion 100% n-Decano, todas las conditions 0..5)
    y despejando el valor de tabla usado en `Z=1-(1*valor)^2`, muestra que
    `valor` coincide EXACTO (no aproximado) con el `bj` YA TABULADO en
    `TABLA_CONSTANTES_EX1995` (para n-Decano: 0.7523/0.645/0.614 segun la
    columna) -- es decir, el codigo real NO aplica `sqrt()` a `bj` en ningun
    punto, y NO hay ningun factor `p_ref/(R*T0)` visible ni aplicado (esto SI
    reafirma, ahora con caso real y no solo lectura de codigo, el hallazgo ya
    documentado en la RONDA 2 de este mismo dia: "NO aparece ningun factor de
    presion en el punto de la resta"). La formula real y CORRECTA es:

        Z = 1 - (suma(xj * bj_columna))^2          <- SIN sqrt, SIN p_ref/(R*T0)

    Verificado con la composicion completa "Default" (no solo n-Decano puro):
    columna bj=1, formula corregida arriba, da Z=0.9981358821579642 vs el Z
    real 0.998136265018026 obtenido por la MISMA llamada Frida -> diferencia
    0.0000384%, bit-exacto dentro del redondeo de la tabla transcrita a mano.
    Se corrigio `calcular_factor_compresion_ex1995` mas abajo (se le quito el
    parametro `p_ref`, que ya no tiene ningun rol fisico en esta formula).

    [CERTAIN] MAPEO conditions(0..5) -> columna de bj usada (aislado con
    composicion 100% n-Decano, unico componente con los 3 bj muy separados
    entre si -- 0.7523/0.645/0.614 -- para evitar ambiguedad de redondeo):
        conditions 0        -> columna bj = 1 (0.645)
        conditions 1, 2, 3  -> columna bj = 0 (0.7523)
        conditions 4, 5     -> columna bj = 2 (0.614)
    Es decir, de los 6 valores de `conditions` que acepta la funcion real
    (0..5, `if (5 < param_2) return 1`), solo hay 3 columnas de bj distintas
    -- multiples `conditions` comparten columna, igual patron conceptual (una
    tabla de 6 "paquetes" que reusa columnas) ya visto en el switch de 7 casos
    de `select_reference_temperatures` de la variante 2016_M.

    [CERTAIN] MAPEO conditions(0..5) -> columna de Hoj usada (mismo metodo,
    leyendo `Hm_bruto` con la composicion 100% n-Decano: Hoj_bruto=[6829.77,
    6832.31, 6834.90, 6842.69] en `TABLA_CONSTANTES_EX1995`):
        conditions 0 -> columna Hoj = 2 (6834.90)
        conditions 1 -> columna Hoj = 3 (6842.69)
        conditions 2 -> columna Hoj = 2 (6834.90)
        conditions 3 -> columna Hoj = 0 (6829.77)
        conditions 4 -> columna Hoj = 1 (6832.31)
        conditions 5 -> columna Hoj = 0 (6829.77)
    A diferencia del mapeo de bj (que agrupa 1,2,3 juntos y 4,5 juntos), aqui
    CADA `conditions` puede seleccionar una columna de Hoj distinta -- 4
    columnas de Hoj posibles contra solo 3 de bj, exactamente el mismo patron
    ya documentado en `ISO_6976.py` (3 valores de bj por temperatura de
    METERING, 4 valores de Hoj por temperatura de COMBUSTION, son dos ejes de
    temperatura independientes). NO se identifico el significado fisico exacto
    (que temperatura en C/F corresponde a cada `conditions`) por falta de una
    pantalla real que lo dispare -- igual limite honesto ya aceptado para
    otros indices de este proyecto.

    [CERTAIN] Formulas de conversion masa/volumen (`cv_calculation_method=1`)
    confirmadas IDENTICAS a las ya usadas en el resto del proyecto, verificado
    con la composicion pura de n-Decano (unico componente, sin ambiguedad de
    mezcla): `Hoj_masa = Hm/Mmix` (division exacta, confirmado bit a bit:
    6842.69/142.285=48.09143620... = Hoj_bruto_masa real devuelto), y
    `densidad = (Mmix/1000)/Vm_real` con `Vm_real` derivable de `Hm/Hoj_vol`
    (mismo patron ya CERTAIN en `ISO_6976.py`/`ISO_6976_1995.py`, sin cambios
    que aplicar en este archivo). El indice de Wobbe (`param_5[10]`) tambien
    confirma la formula ya conocida `H_vol/sqrt(densidad_relativa)`.

    [CERTAIN, HALLAZGO SECUNDARIO] `molar_mass_calculation_method=1` (que lee
    una tabla DISTINTA, todavia no mapeada en este proyecto, direccion
    Ghidra `DAT_0032ab60`, stride 5 doubles/fila) da Mmix=18.6372061008,
    bit-exacto al valor real de pantalla (18.637206) -- mas cerca que
    `molar_mass_calculation_method=2` (18.637417361, el "Metodo A tabulado"
    ya usado por `calcular_masa_molar_ex1995`, dif. 0.0011%). Esto sugiere
    que la app real (via la ruta Excel, no probada aqui) usa el metodo 1
    ("formula quimica"/Metodo B) por defecto, no el 2 -- pero la diferencia es
    tan pequena (0.0011%) que NO se cambia `calcular_masa_molar_ex1995` en
    este archivo (que seria necesario mapear la tabla nueva `DAT_0032ab60`
    para reproducir el metodo 1 exactamente, fuera del alcance de esta ronda,
    ver seccion 2 para el detalle) -- se deja como TRABAJO PENDIENTE anotado,
    no bloqueante (el error ya es <0.01%, dentro del margen del proyecto).

    **CONCLUSION DE ESTA RONDA**: `ISO_6976_ex_1995.py` YA NO ESTA "sin ningun
    caso real" -- tiene un caso real, DIRECTO (no por pantalla, por la misma
    razon de siempre: no existe pantalla "ex"), que ejercita el motor REAL
    completo (`calculate_revision_1`, dispatch de conditions/mmm/cvm incluido)
    y corrige un bug real de formula (Z sin sqrt, sin p_ref). Limite honesto
    que se mantiene: el caso real solo cubre los 22 componentes ya conocidos
    de los 55 (ninguno de los 33 nuevos), y el significado fisico de
    `conditions` sigue sin traducirse a temperaturas concretas. La variante
    `ex_2016` (`ISO_6976_ex_2016.py`) NO se tocó en esta ronda -- su motor
    (`iso6976_2016()` con `iso6976_2016_inputs` de 6 `std::vector`) sigue
    siendo un problema estructuralmente distinto y mas complejo, sin intento
    nuevo esta vez (presupuesto de tiempo se concentro en cerrar esta variante
    primero, que resulto ser la mas simple como anticipaba la tarea). ***
===============================================================================
*** ACTUALIZADO 2026-08-08 (RONDA 2, tarea de continuacion) -- PENDIENTE DE
    `p_ref` EN `calculate_revision_1` INVESTIGADO A FONDO, RESULTADO HONESTO
    (parcialmente resuelto, no 100% cerrado).

    [CERTAIN] Releyendo el cuerpo COMPLETO de `calculate_revision_1` ya
    decompilado en `apk_analisis/task5obj_out.txt` (Ghidra 11.4.3, 1910
    bytes, sin necesidad de re-decompilar), se confirma que el termino de Z
    NO tiene NINGUNA multiplicacion ni division visible por presion en el
    punto donde se calcula:
        dVar13 = DAT_00237818 - dVar13 * dVar13;   // DAT_00237818 = 1.0
        param_5[1] = dVar13;                       // Z (out2), sin mas
    Es decir, Z = 1 - (suma xj*bj_columna)^2, IDENTICO en forma al calculo de
    1983_M/1995_M base, pero SIN el termino `* (p_ref / (R*T0))` explicito
    que SI tiene `calculate_compression_factor` de `iso6976_2016`
    (`DAT_00237818 - dVar6 * (param_3 / DAT_00237e20)`, con `param_3` = p_ref
    recibido como parametro). Esto CONFIRMA (no solo reafirma) el hallazgo ya
    documentado: `calculate_revision_1` no recibe ni usa un `p_ref` explicito
    para el termino de Z.

    [CERTAIN] SE ENCONTRO DE DONDE SALE EL FACTOR EQUIVALENTE A p_ref PARA EL
    CALCULO DE DENSIDAD (out1, `*param_5` en el codigo) -- no es una
    constante fija en un solo punto del codigo, sino que se LEE de una tabla
    interna pequena indexada por el argumento `conditions` (param_2, valores
    validos 0..5, `if (5 < param_2) return 1;`):
        dVar11 = DAT_00239d30 * *(double *)(&DAT_0032aac0 + param_2 * 0x14);
        ...
        *param_5 = (dVar12 / dVar11) / dVar13;   // dVar13 = Z ya calculado
    `DAT_0032aac0` es el primer campo (double, offset 0) de un struct de 20
    bytes (`0x14`) repetido 6 veces (una por cada valor de `conditions`
    0..5), MISMA tabla que ya se habia identificado por el indice entero
    (`DAT_0032aac8`, offset+8, columna bj) y que ademas tiene 2 campos enteros
    mas (offset+0xc y offset+0x10, usados para seleccionar columnas de Hoj y
    de otro conjunto de constantes en la rama `param_4==2`). Es decir: **el
    argumento `conditions` selecciona, de una sola vez, un "paquete"
    completo de 4 constantes precalculadas** (factor tipo Vm_ideal/densidad,
    columna bj, columna Hoj_bruto, columna adicional) -- EXACTAMENTE el mismo
    patron conceptual que `select_reference_temperatures` de `iso6976_2016`
    (que tambien empaqueta temperatura+indices por combo), solo que aqui
    esta implementado como tabla de datos en vez de un `switch` con
    asignaciones explicitas.

    [CERTAIN, RESPUESTA DIRECTA A LA PREGUNTA DEL PENDIENTE] `p_ref` (o mas
    precisamente, el factor combinado que hace su papel, probablemente
    `R*T0/p_ref` o `Vm_ideal`) **NO es un parametro explicito, NI una
    constante global unica fija en el codigo, NI se deriva aritmeticamente
    de otro campo de la composicion** -- se LEE de una tabla interna de 6
    entradas (una por combinacion de referencia, seleccionada por
    `conditions`), la MISMA tabla que tambien fija que columna de bj/Hoj usar.
    Para el termino de Z especificamente, NO aparece ningun factor de presion
    en absoluto en el punto de la resta (`1 - suma^2`) -- lo cual deja 2
    explicaciones posibles, AMBAS CONSISTENTES con el codigo pero NO
    diferenciables sin un caso real:
      (a) el factor p/(R*T0) esta PRE-MULTIPLICADO dentro de los propios
          valores de bj almacenados en la tabla de 55 filas (columna
          seleccionada por `conditions` via el mismo indice), de modo que
          `suma(xj*bj_ya_escalado)^2` ya incluye el efecto de p_ref sin
          necesitar una multiplicacion aparte en este punto del codigo; o
      (b) el termino de presion simplemente no aplica a Z en esta variante
          (posible si todas las 6 combinaciones de `conditions` comparten el
          mismo p_ref de referencia estandar y ese p_ref ya esta absorbido en
          como se generaron los bj de la tabla en tiempo de compilacion del
          binario, sin relacion con el "conditions" en tiempo de ejecucion).
    NO SE PUEDE DISTINGUIR (a) de (b) sin decompilar tambien
    `spirit::math::iso6976_1995::calculate_revision_1`'s tabla de 55 filas
    completa comparandola bit a bit contra los bj YA ESCALADOS de 2016_M para
    cada "conditions", trabajo que excede el presupuesto de esta ronda (y que
    en la practica no cambia la recomendacion siguiente).

    [RECOMENDACION PARA LA FASE DE VALIDACION, NO IMPLEMENTADA AQUI] Si en el
    futuro se implementa `calculate_revision_1` en Python: (1) el `Z = 1 -
    suma^2` debe copiarse LITERAL, sin agregar ningun `p_ref/(R*T0)` como se
    hace para 2016_M -- agregar ese termino seria un error, ya que el codigo
    real no lo tiene en ese punto; (2) para la densidad (`param_5[0]`), el
    factor `dVar11` (leido de `DAT_0032aac0[conditions]`) debe extraerse por
    volcado de memoria (mismo metodo `Memory.getBytes` de Ghidra ya usado con
    exito en `ISO_6976_1995.py` ronda 2, NO `struct.unpack` sobre el archivo
    crudo, que dio basura para una tabla vecina por un desajuste
    file-offset/vaddr) para las 6 combinaciones de `conditions`, en vez de
    asumir un `P_REF_PA` fijo tipo 101325 Pa como se hizo en `ISO_6976_1995.py`
    base. Esto queda como TRABAJO PENDIENTE, no se ejecuto en esta ronda
    (fuera del alcance solicitado: solo investigar y documentar el hallazgo).
===============================================================================
*** ACTUALIZADO 2026-08-07 (FASE DECOMPILACION PURA, tarea de continuacion) --
    2 HALLAZGOS IMPORTANTES.

    (1) [CERTAIN] CUERPO INTERNO DE `calculate_revision_1` LEIDO POR PRIMERA
    VEZ (Ghidra 11.4.3, decompilo con cuerpo completo, 1910 bytes). REFUTA
    PARCIALMENTE la hipotesis [LIKELY] anterior ("formulas del pipeline
    identicas a 2016_M por similitud estructural"): `calculate_revision_1`
    NO llama a NINGUNA de las 14 sub-funciones compartidas de
    `spirit::math::iso6976_2016` (`calculate_molar_mass`,
    `calculate_compression_factor`, etc.) -- es monolitico y autocontenido,
    exactamente el mismo patron que `PropertiesISO6976_1995_rev1` y
    `PropertiesISO6976_1983` (3 implementaciones DISTINTAS del mismo tipo de
    calculo, cada una con su propio codigo inline, no una reutilizada por
    las otras). Las FORMULAS si son estructuralmente equivalentes (mismo
    "summation factor method": Z=1-K*(suma)^2, Hm=suma(xj*Hoj), Wobbe=
    H/sqrt(d), Vm_real=Vm_ideal*Z por multiplicacion no division -- todo
    consistente con lo ya CERTAIN en `ISO_6976.py`), pero DUPLICADAS con
    tablas de constantes propias, NO invocadas por llamada de funcion
    compartida. DIFERENCIA REAL ADICIONAL (no asumir sin mas validacion,
    documentada aqui tal como pide la regla del proyecto): la firma de
    `calculate_revision_1` NO recibe `p_ref` como parametro explicito (a
    diferencia de `calculate_compression_factor` del namespace 2016, que SI
    lo recibe) -- el termino de Z se calcula como
    `Z = 1 - (suma(xj*bj_columna))^2` SIN una division/multiplicacion
    visible por `p/(R*T0)` en el punto de la resta; la tabla de bj propia
    (columna seleccionada por un indice derivado de `conditions`, leido de
    una tabla auxiliar `DAT_0032aac8` de stride 0x14=20 bytes, MISMO PATRON
    que `select_reference_temperatures`) podria ya traer ese factor
    pre-multiplicado, o `p_ref`/T0 podrian estar fijos internamente (como ya
    ocurre en 1983_M/1995_M base). NO SE VALIDA NI SE IMPLEMENTA esta
    posible diferencia en este archivo (fuera del alcance de la fase de
    decompilacion) -- queda documentada como algo a investigar/implementar
    en la fase de validacion, si algun dia se consigue un caso real de la
    variante "ex" para confirmarlo o descartarlo con Frida.

    (2) [CERTAIN] TABLA DE NOMBRES REALES ENCONTRADA -- resuelve la mayoria
    de la ambiguedad de isomero de la seccion 3. Se encontro, por busqueda
    de cadenas ASCII embebidas cerca de la tabla de 55 componentes (file
    offset ~0x31ab40-0x31b3c0, justo antes de donde comienza la tabla
    numerica en 0x31B400), una lista de 55 nombres de compuestos en INGLES,
    en el MISMO ORDEN que las 55 filas de la tabla numerica (verificado
    contando exactamente 55 nombres y cruzando contra los 22 componentes ya
    CERTAIN por posicion -- coincide en TODOS, incluyendo el orden exacto
    n-Butane/2-Methylpropane que ya se sabia por evidencia de codigo en
    `ISO_6976_ex_2016.py`). Metodo: `normas/AGA_5.py`/`AGA_8.py` NO usan
    ninguna tecnica de tabla de nombres (confirmado leyendo ambos: AGA-8
    resuelve isomeros por CONSISTENCIA DE PROPIEDADES FISICAS -- Gi/Ei
    correlacionados con forma molecular/Tc conocida -- no por strings), asi
    que esta tabla de nombres es una tecnica NUEVA para este proyecto, no
    una reutilizada. Con esta tabla, SE CORRIGIERON en este archivo (solo
    nombres/etiquetas, los valores Mj/bj/Hoj NO cambiaron):
      - fila25/26: "1,3-Butadieno"/"1,2-Butadieno" ESTABAN INTERCAMBIADOS
        (real: fila25=1,2-Butadieno, fila26=1,3-Butadieno) -- corregido.
      - filas 28-30 y 33 NO eran alquenos de cadena recta como se habia
        adivinado por formula quimica ("2-Penteno","Hexeno","Hepteno",
        "Octeno") -- son CICLOALCANOS: "Ciclopentano", "Metilciclopentano",
        "Etilciclopentano", "Etilciclohexano" (la formula C5H10/C6H12/
        C7H14/C8H16 es ambigua entre alqueno lineal y cicloalcano
        sustituido; el string real desambigua a favor de cicloalcano).
      - fila36: "m-Xileno" era la adivinanza; el nombre real es
        "Etilbenceno" (Ethylbenzene, otro isomero C8H10).
    Nombres YA CORRECTOS confirmados (sin cambio, ahora [CERTAIN] en vez de
    LIKELY/GUESSING): n-Hexano, 2-metilpentano, 3-metilpentano,
    2,2-dimetilbutano, 2,3-dimetilbutano, Etileno, Propileno, 1-Buteno,
    cis-2-Buteno, trans-2-Buteno, Isobutileno (nombre real "2-Methylpropene",
    mismo compuesto), 1-Penteno, Propadieno, Acetileno, Ciclohexano,
    Metilciclohexano, Benceno, Tolueno, o-Xileno, Metanol, Metanotiol
    (real "Methanethiol"), Amoniaco, Acido cianhidrico (real "Hydrogen
    cyanide"), Sulfuro de carbonilo/Disulfuro de carbono (real "Carbonyl
    sulfide"/"Carbon disulfide"), Neon, Dioxido de azufre (real "Sulfur
    dioxide") y los 22 ya certain. RESIDUO HONESTO: la tabla de nombres NO
    se encontro para los 5 componentes EXTRA de `ISO_6976_ex_2016.py`
    (Undecano..Pentadecano, filas 55-59 de la tabla de 60) -- busqueda
    global de "undecane"/"dodecane" en todo el binario dio 0 resultados;
    esos 5 no tenian ambiguedad de isomero de todos modos (alcano normal
    unico por formula), asi que no se pierde certeza practica. La lista
    completa de 55 nombres reales, en orden, y el metodo de busqueda
    (offsets exactos) quedan documentados en la seccion 5 de este
    docstring para que cualquier revision futura no tenga que rehacer la
    busqueda. ***
===============================================================================
*** ACTUALIZADO 2026-08-20 (CONFIRMACION CRUZADA INDEPENDIENTE, manual ABB
    SpiritIT encontrado 2026-08-19) -- 51/55 POSICIONES COINCIDEN EXACTO;
    4 POSICIONES (i-Butano/n-Butano, i-Pentano/n-Pentano) MUESTRAN UNA
    DISCREPANCIA PREEXISTENTE, DOCUMENTADA AQUI EN VEZ DE FORZAR EL CIERRE.
    Se releyo el PDF real (`Flow-X Manual IIIb - Function Reference_CM_
    FlowX_FR-EN_E.pdf`, paginas 121-122, funcion `fxISO6976ex_1995_M`) con
    `pdfplumber` y se comparo, posicion por posicion (1 a 55), la lista
    numerada oficial del manual contra `ORDEN_COMPONENTES_EX1995` de este
    archivo (no solo se confio en la memoria del proyecto).
    [CERTAIN] 51 de 55 posiciones COINCIDEN EXACTO, incluyendo pares de
    isomero ya resueltos por la tabla de strings del binario (1,2-/1,3-
    Butadieno en filas 25/26=manual 26/27, las 4 cicloalcanos de filas
    29-31/33=manual 30-32/34, Etilbenceno en fila 36=manual 37
    "Ethylbenzene", etc.).
    [HALLAZGO, NO FABRICADO, discrepancia real detectada -- no se fuerza el
    cierre] Las filas 3/4 y 5/6 (i-Butano/n-Butano, i-Pentano/n-Pentano) NO
    coinciden: el manual numera 4=n-Butane, 5=2-Methylpropane(=i-Butane),
    6=n-Pentane, 7=2-Methylbutane(=i-Pentane) (1-based) -> en 0-based
    fila3=n-Butano, fila4=i-Butano, fila5=n-Pentano, fila6=i-Pentano. Esto
    coincide con la tabla de STRINGS de este mismo archivo (seccion 5 del
    docstring, linea "3 n-Butane->n-Butano  4 2-Methylpropane->i-Butano"),
    pero es lo OPUESTO de lo que hoy tiene codificado
    `ORDEN_COMPONENTES_EX1995` mas abajo en este archivo (fila3="i-Butano",
    fila4="n-Butano", fila5="i-Pentano", fila6="n-Pentano"). Es decir: dos
    fuentes independientes (manual oficial + la propia tabla de strings ya
    documentada en la seccion 5 de este archivo desde 2026-08-07) coinciden
    entre si, y ambas contradicen la lista `ORDEN_COMPONENTES_EX1995`
    actualmente codificada.
    [CERTAIN, por que esto NO rompe ningun resultado ya calculado] Se
    verifico leyendo `calcular_masa_molar_ex1995`/`calcular_factor_
    compresion_ex1995`/`calcular_poder_calorifico_molar_ex1995` (mas abajo
    en este archivo) que iteran `ORDEN_COMPONENTES_EX1995` solo como lista
    de NOMBRES para hacer `TABLA_CONSTANTES_EX1995[c][...]` (busqueda por
    CLAVE/nombre, no por indice de posicion) -- la posicion de "i-Butano" en
    la lista Python NO afecta ningun calculo de este archivo, solo es
    documentacion de "en que fila de la tabla binaria original se
    encontraron estos bytes". Los VALORES de `TABLA_CONSTANTES_EX1995`
    ("i-Butano"->2868.20 kJ/mol, "n-Butano"->2877.40 kJ/mol) ya son
    correctos (swap de VALORES corregido 2026-08-06, ver comentario en la
    definicion de `TABLA_CONSTANTES_EX1995`), y ese swap de valores es
    independiente de este hallazgo de POSICION.
    [CORREGIDO 2026-08-20, fuera de la tarea original que lo detecto] Se
    corrigio `ORDEN_COMPONENTES_EX1995` (fila3="n-Butano", fila4="i-Butano",
    fila5="n-Pentano", fila6="i-Pentano") para que coincida con el manual y
    con la tabla de strings del binario -- y, de paso, con
    `ORDEN_COMPONENTES_EX2016` de `ISO_6976_ex_2016.py`, que YA tenia el
    orden correcto (revisado al corregir esto: ese archivo nunca tuvo el
    bug). Como ya se demostro arriba, esto NO cambia ningun resultado
    calculado (busqueda siempre por nombre/clave, nunca por indice de
    posicion) -- es una correccion de exactitud documental, no una
    correccion de un bug de calculo. Fuente primaria (el PDF) prevalece
    sobre la transcripcion de memoria del proyecto, que no mencionaba esta
    discrepancia especifica. ***
===============================================================================
ISO 6976:1995, variante "ex" EXTENDIDA a 55 componentes (`Math_ISO6976ex_1995_M`
en libFXLibrary.so), en vez de los 22 estandar de `normas/ISO_6976_1995.py`.
Tarea de continuacion 2026-08-06.

Este archivo se puede ejecutar solo:
    python -m normas.ISO_6976_ex_1995

===============================================================================
RESUMEN EJECUTIVO (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] HALLAZGO PRINCIPAL, CONTRARIO A LA HIPOTESIS DE PARTIDA DE ESTA
TAREA: `Math_ISO6976ex_1995_M` NO llama a `PropertiesISO6976_1995_rev1` (el
motor de 22 componentes ya CERRADO en `ISO_6976_1995.py`). Llama a una funcion
COMPLETAMENTE DISTINTA: `spirit::math::iso6976_1995::calculate_revision_1`
-- el namespace nuevo que el propio `ISO_6976_1995.py` (seccion 1 de su
docstring) ya habia encontrado en el binario pero reportado como "CODIGO
MUERTO" porque el wrapper de la variante BASE (`Math_ISO6976_1995_M`) nunca
lo llama. Resulta que ese namespace NO esta muerto: es el motor real de la
variante "ex". Esto es la MISMA relacion, en espejo, que ya existia entre
`Math_ISO6976_2016_M` y `Math_ISO6976ex_2016_M` -- salvo que en 2016 AMBAS
variantes comparten el mismo namespace `iso6976_2016` (confirmado por
disassembly en esta misma tarea: `Math_ISO6976ex_2016_M` tambien construye un
`iso6976_2016_inputsC2` y llama a `iso6976_2016()`, solo que con vectores mas
largos), mientras que en 1995 la variante base y la "ex" usan DOS FUNCIONES
DE NEGOCIO DIFERENTES por completo (una vieja autocontenida de 22 componentes,
otra vieja autocontenida DISTINTA de 55). No es el mismo motor con una lista
mas larga -- es un binario/tabla de constantes propios.

[CERTAIN] `calculate_revision_1` (direccion 0x125060, 1972 bytes) SI es,
igual que `PropertiesISO6976_1995_rev1`, una funcion monolitica autocontenida
(no dispatcher de 14 sub-funciones como el namespace `iso6976_2016`) -- el
namespace `iso6976_1995` en la tabla de simbolos SOLO tiene ESTE UNICO
simbolo, ninguna funcion interna adicional. El bucle real usa `cmp eax, 0x37`
(0x37 = 55 decimal) como limite, confirmando en el propio codigo maquina que
opera sobre 55 componentes, no 22 (`cmp edx, 0x16`=22 es el patron ya visto en
las otras variantes base).

[CERTAIN] Tabla propia de constantes localizada y extraida por volcado
directo de memoria (mismo metodo `struct.unpack` ya usado para la TABLA 2 de
`ISO_6976.py`): GOT_BASE - 0x919e8 = file offset **0x31B400**, 55 filas
consecutivas de 280 bytes (35 doubles) cada una -- MISMO stride que la TABLA 2
de 2016_M/1995_M, pero un LAYOUT DE COLUMNAS DISTINTO (ver seccion 2) y una
region de memoria totalmente distinta (no es una copia ni una extension in
place de ninguna tabla ya conocida).

[CERTAIN, cross-validado bit a bit] De las 55 filas, EXACTAMENTE 22
corresponden a los 22 componentes ya CERTAIN de `ISO_6976.py` -- Mj, los 3
bj y Hoj_bruto/neto (molar) coinciden EXACTOS (no aproximados, iguales al
ultimo decimal) con `TABLA_CONSTANTES` de `ISO_6976.py` para Metano, Etano,
Propano, i-Butano, n-Butano, i-Pentano, n-Pentano, neo-Pentano, n-Hexano,
n-Heptano, n-Octano, n-Nonano, n-Decano, Hidrogeno, Agua, H2S, CO, Helio,
Argon, Nitrogeno, Oxigeno y CO2 -- ver seccion 2 para las filas exactas y el
script de verificacion. Esto prueba que la fisica (tabla de constantes) SI es
compartida entre motores/revisiones (igual que ya se documento entre 1983/
1995/2016), aunque el CODIGO que la usa (calculate_revision_1) sea distinto.

[CERTAIN via formula quimica, LIKELY/GUESSING el nombre comercial exacto] Las
otras 33 filas se identificaron SIN Frida ni caso real, cruzando el Mj real
de cada fila contra la suma de pesos atomicos IUPAC que este MISMO proyecto ya
confirmo en el binario (C=12.011, H=1.00794, ver seccion 3 del docstring de
`ISO_6976.py`) -- las 33 masas molares coinciden EXACTAS (no solo cercanas, al
ultimo miligramo) con formulas quimicas reales de hidrocarburos/compuestos que
el propio estandar ISO 6976 lista en su tabla extendida de componentes (Anexo
con series de parafinas/olefinas/aromaticos/compuestos de N,O,S). Ver seccion
3 para la tabla completa fila por fila con la formula quimica exacta que
reproduce cada Mj.

[PARCIALMENTE RESUELTO 2026-08-08, RONDA 3 -- ver bloque al inicio del
docstring] La app Android de FlowXpert NO tiene ninguna pantalla "ISO-6976 ex"
(navegacion completa confirmada por `uiautomator dump`, solo 3 items) -- eso
SIGUE siendo cierto. Pero la llamada DIRECTA por Frida a
`calculate_revision_1`, descartada en rondas anteriores por "riesgo de bug de
layout invisible" sobre una firma solo parcialmente disassemblada, SI se
reintento en la RONDA 3 (2026-08-08) una vez que la RONDA 2 (mismo dia) ya
habia decompilado el CUERPO COMPLETO de la funcion -- con el struct real
confirmado (12 bytes, sin STL/heap propio, mucho mas simple que
`iso6976_2016_inputs`), el riesgo que motivo el abandono ya NO aplicaba. Se
construyo el struct, se llamo la funcion real dentro del proceso vivo de
FlowXpert, y el resultado (Mmix/Z) reprodujo bit-exacto el valor YA VALIDADO
por pantalla de la variante base -- ver el bloque RONDA 3 al inicio del
docstring para el metodo completo, las direcciones, y el bug de formula real
que se encontro y corrigio (`calcular_factor_compresion_ex1995` mas abajo).
**SI se obtuvo un caso real** para el motor `calculate_revision_1` -- lo que
NO se obtuvo (y sigue como limite honesto) es un caso real que ejercite
alguno de los 33 componentes NUEVOS de la tabla de 55, o el mecanismo de
tabla-extra para composiciones de mas de 55 componentes.

**ESTADO FINAL HONESTO (actualizado 2026-08-08, RONDA 3)**: motor CONFIRMADO
como distinto de la variante base (`calculate_revision_1`, no
`PropertiesISO6976_1995_rev1`), Y AHORA con un caso real que lo ejercita de
punta a punta (dispatch de conditions/mmm/cvm incluido, no solo tabla de
constantes). Tabla de constantes de los 55 componentes EXTRAIDA y, para
22/55, CROSS-VALIDADA bit a bit contra datos ya CERTAIN; para los 33
restantes, identificada por formula quimica exacta (evidencia fuerte, sin
caso real que ejercite ESOS 33 en particular). Formulas del pipeline de
calculo: Mmix y las conversiones masa/volumen quedan [CERTAIN] (confirmadas
por el caso real Frida); Z pasa de [LIKELY, copiada de `ISO_6976.py`] a
[CERTAIN, formula corregida -- SIN sqrt, SIN p_ref, ver RONDA 3] tras
encontrarse que la version anterior estaba mal. **Se actualiza el reporte de
"NO CERRADA" a "PARCIALMENTE CERRADA"**: a diferencia de 1983_M/1995_M/2016_M
(que tienen caso real de PANTALLA que cubre TODOS sus componentes), esta
variante tiene un caso real DIRECTO que cubre el motor completo y 22/55
componentes, pero no los 33 nuevos ni el modo de mas de 55 componentes -- un
avance solido, ya no solo "reverse engineering sin cierre numerico".

===============================================================================
1. RELACION ENTRE Math_ISO6976ex_1995_M Y EL MOTOR BASE -- VERIFICADO POR
   DISASSEMBLY, NO ASUMIDO
===============================================================================
[CERTAIN] METODO: se repitio el mismo procedimiento que ya identifico la
UNICA llamada de negocio real de `Math_ISO6976_1995_M` (capstone puro sobre
los bytes reales del .so, buscando instrucciones `call` y resolviendolas
contra la tabla de simbolos real via pyelftools). Direccion real del wrapper
"ex": 0x87470 (2270 bytes, mas grande que el wrapper base de 1545 bytes,
consistente con que construye un vector/composicion mas largo).

De las 34 instrucciones `call` de `Math_ISO6976ex_1995_M`, la UNICA llamada a
codigo de negocio real (descontando helpers genericos ya conocidos:
`Function_CContext::arg_get`, `NormalizeMolFrac` de 55 en vez de 22 --
tambien confirmado, `_Znwj`/`_ZdlPv` new/delete, `ArgInitializeOutput`) es:

    call @ 0x87b72  ->  0x125060
    = _ZN6spirit4math12iso6976_199520calculate_revision_1E...

NO hay ninguna llamada a `PropertiesISO6976_1995_rev1` (0x124980) ni a
`PropertiesISO6976_1995` (la corta, 0x124800) en todo el cuerpo del wrapper
"ex". Comparacion directa, mismo metodo, contra el wrapper BASE
`Math_ISO6976_1995_M` (0x85710): su UNICA llamada de negocio real es
`PropertiesISO6976_1995_rev1` (0x124980) -- confirmando que son dos rutas
de codigo completamente separadas.

[CERTAIN, contraste] Por completitud se repitio el mismo analisis sobre
`Math_ISO6976ex_2016_M` (0xc2b00, 4189 bytes): SI construye un
`iso6976_2016_inputsC2` (constructor real) y llama a `iso6976_2016()`
-- el MISMO namespace/motor que la variante base 2016_M, ya CERTAIN en
`ISO_6976.py`. Esto confirma que la hipotesis de partida de la tarea
("ex reusa el mismo motor con lista mas larga") SI se cumple para 2016,
pero NO para 1995 -- son dos disenos distintos dentro del mismo binario,
no se puede generalizar de una revision a otra.

[CERTAIN] Prologo real de `calculate_revision_1` (quinta confirmacion cruzada
de GOT_BASE en este proyecto):
    call get_pc_thunk_bx        (retorna a 0x125069)
    add ebx, 0x287d78           => GOT_BASE = 0x125069 + 0x287d78 = 0x3ACDE8
                                    (identico al resto del proyecto)

[CERTAIN] El cuerpo de `calculate_revision_1` usa `cmp eax, 0x37` (55
decimal) repetidamente como limite de bucle sobre el arreglo de composicion
y sobre el arreglo de constantes -- confirma en el propio codigo maquina
(no por nombre de funcion ni por plausibilidad) que esta funcion opera
sobre 55 componentes. Tambien lee, para composiciones de MAS de 55
componentes (`cmp ecx, 0x37; ja ...`), un segundo arreglo desde un puntero
adicional (`[eax+8]` de la estructura `composition`) con stride distinto
(0x28 = 40 bytes) -- un mecanismo de "componentes adicionales definidos por
el usuario" mas alla de los 55 tabulados, no investigado (fuera del alcance
de esta tarea, la composicion real de cualquier caso previsible cabe en los
55 tabulados).

===============================================================================
2. TABLA DE CONSTANTES DE LOS 55 COMPONENTES -- EXTRAIDA Y LAYOUT CONFIRMADO
===============================================================================
[CERTAIN] Ubicacion: GOT_BASE - 0x919e8 = file offset **0x31B400**
(`lea edx, [ebx - 0x919e8]` en el disassembly real, ebx=GOT_BASE confirmado
arriba). 55 filas consecutivas (`cmp eax, 0x37`) de 280 bytes (35 doubles)
cada una.

[CERTAIN] LAYOUT DE COLUMNAS -- confirmado leyendo la secuencia real de
instrucciones (que campo se multiplica por la fraccion molar en cada bucle,
y en que orden se acumulan Mmix/Z/Hm) Y cross-validado bit a bit contra
`TABLA_CONSTANTES` de `ISO_6976.py` para 3 componentes de control (Metano,
Etano, Hidrogeno) MAS los otros 19 conocidos (ver tabla de la seccion
siguiente) -- coincidencia EXACTA en los 22, no aproximada:
    [0]      Mj (masa molar tabulada, g/mol)
    [1:4]    factor <=1 que decrece con el peso molecular (mismo candidato
             "Z0 del componente puro" ya especulado, sin confirmar del todo,
             en `ISO_6976.py` seccion 3 -- aqui aparece en OTRA posicion de
             la fila, confirmando que es un layout de tabla DISTINTO, no una
             reutilizacion literal de la misma estructura de bytes)
    [4:7]    bj (summation factor de compresibilidad), 3 valores -- IDENTICO
             en posicion relativa (justo antes de Hoj) al layout ya CERTAIN
             de `ISO_6976.py`
    [7:11]   Hoj_bruto, base molar, kJ/mol (4 combinaciones de temperatura)
    [11:15]  Hoj_neto, base molar, kJ/mol (4 combinaciones)
    [15:19]  Hoj_bruto, base masa, MJ/kg (4 combinaciones)
    [19:35]  16 campos restantes, NO extraidos en esta tarea -- por analogia
             de conteo (6+4+6=16, igual que `ISO_6976.py`) son candidatos a
             Hoj_bruto volumetrico/Hoj_neto masa/Hoj_neto volumetrico, pero
             NO se verificaron bit a bit en esta tarea (no se necesitaron:
             las formulas de este modulo derivan masa/volumen a partir de
             Hm/Mmix/Vm_real, igual que `ISO_6976.py`, sin leer estas
             columnas directamente).

Verificacion exacta (script `struct.unpack` + comparacion, reproducible):
    Metano (fila 0):   Mj=16.043  bj=(0.049,0.0447,0.0436)
                        Hoj_bruto=(890.63,891.09,891.56,892.97)  [4/4 exacto]
    Etano  (fila 1):   Mj=30.07   bj=(0.1,0.0922,0.0894)
                        Hoj_bruto=(1560.69,1561.41,1562.14,1564.34) [exacto]
    Hidrogeno (fila 40): Mj=2.0159 bj=(-0.004,-0.0048,-0.0051)
                        Hoj_bruto=(285.83,285.99,286.15,286.63)  [exacto,
                        incluye el signo negativo de bj, la misma anomalia ya
                        documentada en `ISO_6976.py`]
(las 19 filas restantes de los 22 conocidos se verificaron con el mismo
metodo, ver `_FILAS_CONOCIDAS_VERIFICADAS` en el codigo mas abajo.)

===============================================================================
3. MAPEO FILA -> COMPONENTE (55 filas) -- CONFIANZA DIFERENCIADA
===============================================================================
22 filas = componentes YA CERTAIN (cross-validados bit a bit, seccion 2):
    fila  0 = Metano        fila  1 = Etano         fila  2 = Propano
    fila  3 = i-Butano      fila  4 = n-Butano      fila  5 = i-Pentano
    fila  6 = n-Pentano     fila  7 = neo-Pentano   fila  8 = n-Hexano
    fila 13 = n-Heptano     fila 14 = n-Octano      fila 15 = n-Nonano
    fila 16 = n-Decano      fila 40 = Hidrogeno     fila 41 = Agua
    fila 42 = H2S           fila 45 = CO            fila 48 = Helio
    fila 50 = Argon         fila 51 = Nitrogeno     fila 52 = Oxigeno
    fila 53 = CO2

33 filas NUEVAS -- identificadas por formula quimica exacta (Mj real de la
fila == suma de pesos atomicos IUPAC ya confirmados en este proyecto,
C=12.011 g/mol, H=1.00794 g/mol, coincidencia EXACTA al miligramo, no
aproximada): [CERTAIN la formula quimica/familia, LIKELY o GUESSING el
isomero/nombre comercial especifico cuando hay mas de un isomero con la
misma formula y no hay forma de distinguirlos sin caso real]:
    filas  9,10,11,12  = C6H14 (4 isomeros de hexano, ADEMAS de n-Hexano ya
                          conocido -- candidatos: 2-metilpentano,
                          3-metilpentano, 2,2-dimetilbutano, 2,3-
                          dimetilbutano) [CERTAIN formula, GUESSING orden]
    fila  17 = Etileno (C2H4)                    [LIKELY]
    fila  18 = Propileno (C3H6)                  [LIKELY]
    filas 19-22 = C4H8 (4 isomeros: 1-buteno, cis-2-buteno, trans-2-buteno,
                  isobutileno) [CERTAIN formula, GUESSING orden]
    filas 23,28 = C5H10 (2 isomeros de penteno)  [CERTAIN formula, GUESSING]
    fila  24 = C3H4 (propadieno/alil o propino)  [CERTAIN formula, GUESSING]
    filas 25,26 = C4H6 (2 isomeros de butadieno) [CERTAIN formula, GUESSING]
    fila  27 = Acetileno (C2H2)                  [LIKELY]
    filas 29,31 = C6H12 (2 isomeros: hexeno/ciclohexano) [GUESSING orden]
    filas 30,32 = C7H14 (2 isomeros: hepteno/metilciclohexano) [GUESSING]
    fila  33 = C8H16 (octeno)                    [LIKELY]
    fila  34 = Benceno (C6H6)                    [LIKELY]
    fila  35 = Tolueno (C7H8)                    [LIKELY]
    filas 36,37 = C8H10 (2 isomeros: xileno/etilbenceno) [GUESSING orden]
    fila  38 = Metanol (CH4O)                    [LIKELY -- Hoj_bruto-
                Hoj_neto=88.03 kJ/mol = 2x calor latente H2O, consistente con
                2 moles de agua por combustion de metanol]
    fila  39 = Metanotiol/mercaptano metilico (CH4S) [LIKELY]
    fila  43 = Amoniaco (NH3)                    [LIKELY -- Hoj_bruto=382.81
                kJ/mol coincide con el calor de combustion publicado de NH3]
    fila  44 = Acido cianhidrico (HCN)           [LIKELY]
    fila  46 = Sulfuro de carbonilo, COS         [LIKELY -- Hoj_bruto=
                Hoj_neto (562.01->548.23... ver nota), consistente con
                ausencia de H en la molecula (sin agua de combustion)]
    fila  47 = Disulfuro de carbono, CS2         [LIKELY -- mismo patron
                Hoj_bruto=Hoj_neto por ausencia de H]
    fila  49 = Neon (Ne)                         [LIKELY -- Mj=20.1797 g/mol
                exacto, bj=Helio (identico, ambos inertes ligeros)]
    fila  54 = Dioxido de azufre (SO2)           [LIKELY -- Mj=64.065 g/mol
                exacto, Hoj_bruto=0 consistente con oxidante/inerte
                energetico]

NOTA DE HONESTIDAD (ACTUALIZADA 2026-08-07 -- ver docstring principal arriba):
la identificacion de FORMULA QUIMICA es [CERTAIN] (Mj exacto, no redondeado,
contra suma de pesos atomicos IUPAC ya usados y confirmados por este mismo
proyecto para el "Metodo B" de masa molar). La identificacion del NOMBRE/
ISOMERO ESPECIFICO, que antes dependia SOLO de formula quimica (GUESSING el
isomero exacto), AHORA esta [CERTAIN] para la enorme mayoria de las 33 filas
nuevas gracias a una tabla de nombres reales en ingles encontrada embebida en
el binario (ver seccion 5 mas abajo para la lista completa y el metodo) --
solo el ORDEN INTERNO de 2 grupos sin distincion adicional en el string (los
4 isomeros de hexano C6H14 en filas 9-12, y los pares C4H8/C7H14/C6H12 sin
mas metadato que el nombre ya asignado 1 a 1) sigue siendo trivial porque el
string YA da el nombre exacto por fila, no solo la familia -- es decir, la
ambiguedad ORIGINAL (que isomero es cual fila) quedo RESUELTA por completo:
ya no hace falta "adivinar el orden dentro de la familia" porque el nombre
real ya viene amarrado a la fila correcta. Los unicos 5 componentes SIN
nombre confirmado por string son los exclusivos de `ISO_6976_ex_2016.py`
(Undecano..Pentadecano), que de todos modos no tenian ambiguedad de isomero.

===============================================================================
4. CASO REAL -- NO CONSEGUIDO (documentado honestamente, no forzado)
===============================================================================
[CERTAIN] La pantalla "ISO-6976 ex" NO existe en la app Android. Navegacion
real confirmada (`uiautomator dump`, PID 2880, mismo emulador y frida-server
ya corriendo de sesiones anteriores): menu principal -> "Gas" -> "ISO" lista
EXACTAMENTE 3 items ("ISO-6976 (1983)", "ISO-6976 (1995)", "ISO-6976
(2016)"), sin scroll oculto (confirmado con swipe). Los wrappers
`Math_ISO6976ex_1995_M`/`Math_ISO6976ex_2016_M` SI existen y son
alcanzables como funciones Excel (simbolos reales confirmados, seccion 1),
pero NO estan conectados a ninguna pantalla de la app Android -- son,
aparentemente, exclusivos de la ruta .xll de Windows (no investigada en este
proyecto, que trabaja sobre el binario Android).

[EVALUADO Y DESCARTADO, no forzado] Se evaluo la llamada directa por Frida a
`calculate_revision_1` (mismo PID 2880 activo). La firma real de 5
parametros exige construir en memoria: (1) un struct `composition` cuyo
layout se infirio del disassembly como {int32 count; double* fracciones;
void* extra} (12 bytes) -- factible de construir con `Memory.alloc` +
`writeByteArray`, sin heap de C++ propio (a diferencia de
`iso6976_2016_inputs`, que si tiene constructor con 6 `std::vector`); (2)
`conditions`, `molar_mass_calculation_method`, `cv_calculation_method` -- 3
enums/valores pequenos pasados por valor, con significado no desensamblado a
fondo (se identificaron 3 flags de comparacion en el codigo -- esp+0x74,
esp+0x78, esp+0x7c -- pero no se aislo el valor exacto que usa la app real
para ningun combo, porque no hay pantalla real que los dispare). El riesgo
de un bug de layout invisible en el struct `composition` (mismo tipo de
riesgo ya documentado y evitado en `ISO_6976.py` seccion 4 para
`iso6976_2016_inputs`) mas la falta de un valor real conocido de
`conditions`/metodos con el que comparar el resultado (sin eso, un resultado
obtenido por Frida no se podria validar como correcto ni como incorrecto)
hicieron que se abandonara el intento -- **no se fabrico un caso real**,
siguiendo la regla de oro del proyecto.

===============================================================================
5. TABLA DE NOMBRES REALES (55) -- ENCONTRADA 2026-08-07, METODO Y LISTA
===============================================================================
[CERTAIN] METODO: busqueda de cadenas ASCII imprimibles (regex sobre bytes
crudos, longitud minima 3) en `apk_analisis/libFXLibrary.so`, en la ventana
de archivo 0x319000-0x31c000 (justo antes de donde empieza la tabla numerica
de 55 filas en 0x31B400, documentada en la seccion 2). Aparecen 55 nombres en
ingles, cada uno precedido por 1 byte "ruidoso" (probablemente el byte bajo
de un campo previo de 2-4 bytes, no parte del nombre) y un separador "@", en
ORDEN CRECIENTE DE DIRECCION -- el mismo orden de fila 0..54 de la tabla
numerica (confirmado cruzando contra los 22 componentes ya CERTAIN por otra
via: el orden y la posicion coinciden exacto, incluyendo el detalle fino
n-Butane(fila3)/2-Methylpropane(fila4) ya confirmado por evidencia de codigo
en `ISO_6976_ex_2016.py`). Lista completa (fila: nombre real en ingles ->
nombre usado en este archivo):
    0 Methane->Metano  1 Ethane->Etano  2 Propane->Propano
    3 n-Butane->n-Butano  4 2-Methylpropane->i-Butano
    5 n-Pentane->n-Pentano  6 2-Methylbutane->i-Pentano
    7 2,2-Dimethylpropane->neo-Pentano  8 n-Hexane->n-Hexano
    9 2-Methylpentane->2-metilpentano  10 3-Methylpentane->3-metilpentano
    11 2,2-Dimethylbutane->2,2-dimetilbutano
    12 2,3-Dimethylbutane->2,3-dimetilbutano
    13 n-Heptane->n-Heptano  14 n-Octane->n-Octano  15 n-Nonane->n-Nonano
    16 n-Decane->n-Decano  17 Ethylene->Etileno  18 Propylene->Propileno
    19 1-Butene->1-Buteno  20 cis-2-Butene->cis-2-Buteno
    21 trans-2-Butene->trans-2-Buteno  22 2-Methylpropene->Isobutileno
    23 1-Pentene->1-Penteno  24 Propadiene->Propadieno
    25 1,2-Butadiene->1,2-Butadieno  26 1,3-Butadiene->1,3-Butadieno
    27 Acetylene->Acetileno  28 Cyclopentane->Ciclopentano
    29 Methylcyclopentane->Metilciclopentano
    30 Ethylcyclopentane->Etilciclopentano  31 Cyclohexane->Ciclohexano
    32 Methylcyclohexane->Metilciclohexano
    33 Ethylcyclohexane->Etilciclohexano  34 Benzene->Benceno
    35 Toluene->Tolueno  36 Ethylbenzene->Etilbenceno  37 o-Xylene->o-Xileno
    38 Methanol->Metanol  39 Methanethiol->Metanotiol  40 Hydrogen->Hidrogeno
    41 Water->Agua  42 Hydrogen sulfide->H2S  43 Ammonia->Amoniaco
    44 Hydrogen cyanide->Acido cianhidrico  45 Carbon monoxide->CO
    46 Carbonyl sulfide->Sulfuro de carbonilo (COS)
    47 Carbon disulfide->Disulfuro de carbono (CS2)  48 Helium->Helio
    49 Neon->Neon  50 Argon->Argon  51 Nitrogen->Nitrogeno
    52 Oxygen->Oxigeno  53 Carbon dioxide->CO2  54 Sulfur dioxide->SO2
Las filas 25/26 (Butadieno) y 28/29/30/33/36 (Ciclopentano/Metilciclopentano/
Etilciclopentano/Etilciclohexano/Etilbenceno) fueron CORREGIDAS en
`TABLA_CONSTANTES_EX1995`/`ORDEN_COMPONENTES_EX1995` de este archivo con
base en esta lista (ver docstring principal arriba) -- las demas ya
coincidian. NO se encontraron nombres para Undecano..Pentadecano (los 5
componentes exclusivos de `ISO_6976_ex_2016.py`, busqueda global de
"undecane"/"dodecane" en todo el binario dio 0 resultados) -- sin impacto
practico porque esos 5 no tenian ambiguedad de isomero.

CONCLUSION (actualizada 2026-08-08, RONDA 3): ya SI hay un caso real, obtenido
por llamada DIRECTA a `calculate_revision_1` (no de pantalla, ver bloque RONDA
3 al inicio del docstring y seccion 6 nueva mas abajo) -- esta variante avanza
de "sin cierre numerico posible" a PARCIALMENTE CERRADA (motor+formulas
CERTAIN para el pipeline con los 22 componentes conocidos, sin cubrir los 33
nuevos). Lo que queda establecido con evidencia fuerte y verificable es: (1)
el motor es distinto al de la variante base, (2) la tabla de constantes de 55
componentes esta ubicada y su layout confirmado, (3) 22/55 filas son
bit-exactas contra datos ya CERTAIN, (4) las 33 filas nuevas tienen formula
quimica exacta identificada, (5) el struct de entrada/salida de
`calculate_revision_1` y la formula real de Z (sin sqrt, sin p_ref) son
[CERTAIN] por ejecucion real, ya no una hipotesis por similitud de codigo.
Las formulas de Mmix (Metodo A) y de conversion masa/volumen se confirman
IDENTICAS a las de `ISO_6976.py` (division simple); la formula de Z NO era
identica (se corrigio, ver RONDA 3). Sigue [LIKELY], no [CERTAIN], que los 33
componentes nuevos numericamente identificados por formula quimica sean
correctos EN EJECUCION (nunca se les paso por el motor real).

===============================================================================
6. CASO REAL POR LLAMADA DIRECTA FRIDA -- 2026-08-08, RONDA 3 (metodo completo)
===============================================================================
[CERTAIN] Ver el bloque de docstring "ACTUALIZADO 2026-08-08 (RONDA 3)" al
inicio de este archivo para el hallazgo completo. Resumen de metodo, para que
cualquier revision futura pueda reproducirlo sin releer todo el docstring:

  1. Symbol real completo (extraido con pyelftools sobre `.dynsym` de
     `apk_analisis/libFXLibrary.so`, NO adivinado ni truncado):
     `_ZN6spirit4math12iso6976_199520calculate_revision_1ERKNS1_11compositionENS1_10conditionsENS1_29molar_mass_calculation_methodENS1_21cv_calculation_methodERNS1_7resultsE`
  2. Cuerpo completo ya decompilado en `apk_analisis/task5obj_out.txt`
     (OBJETIVO 4, Ghidra 11.4.3) -- de ahi se leyo el layout exacto del
     struct `composition` (12 bytes) y `results` (11 doubles).
  3. Script Frida: `android_sdk_setup/call_iso6976_ex1995_directo.js`
     (construye composicion+struct en memoria con `Memory.alloc`, expone
     `rpc.exports.llamar(conditions, mmm, cvm)` y
     `rpc.exports.llamarConComposicion(fracArr, conditions, mmm, cvm)` para
     probar composiciones arbitrarias de 55 elementos).
  4. Runner: `android_sdk_setup/run_call_iso6976_ex1995_directo.py` (barre
     las 24 combinaciones conditions x mmm x cvm con la composicion
     "Default", log completo en
     `android_sdk_setup/call_iso6976_ex1995_directo_out.json`).
  5. Entorno usado (para reproducir): emulador Android ya corriendo,
     `android_sdk_setup/sdk/platform-tools/adb.exe devices` debe mostrar
     `emulator-5554 device`, proceso `com.spiritit.flowxpert` corriendo (PID
     verificado 2880 en esta sesion, puede variar), `frida-server` corriendo
     como root en el dispositivo (verificado con
     `adb shell "ps | grep frida"`).
  6. Todas las 24 combinaciones devolvieron `ret=0` (exito, sin ningun
     codigo de error 1/2/4/5) y valores finitos plausibles -- ninguna
     combinacion crasheo el proceso ni corrompio memoria (senal adicional de
     que el layout del struct es correcto: un struct mal armado tipicamente
     produce crash o basura, no 24/24 resultados finitos y consistentes
     entre si).

[CERTAIN, 2026-08-10] COMPARACION CRUZADA .xll vs .so: se decompilo
`FlowXpert_ISO6976ex_1995_M` en `FlowXpert.xll` con Ghidra. Motor nucleo
real `FUN_1800cd480` (1655 bytes, con sub-funciones propias
`FUN_1800b1fa4`/`FUN_1800b2040`), llamado desde `FUN_1800ac218` -- DISTINTO
del nucleo de `1995_M` base (`FUN_1800caf7c`) en el `.xll`, exactamente
igual que en el `.so` (`calculate_revision_1` != `PropertiesISO6976_1995_rev1`).
Confirma en una segunda plataforma, independiente, que "ex_1995_M NO reusa
el motor de la variante base" no es un artefacto de una sola compilacion.
Ver seccion 6 completa del docstring de `normas/ISO_6976.py`.

===============================================================================
"""

from .ISO_6976 import R_GAS, ZAIRE_SOBRE_MAIR  # constantes fisicas, no de tabla

# -----------------------------------------------------------------------------
# Orden real de la TABLA (55 filas), tal como se lee del binario en
# GOT_BASE - 0x919e8 = file offset 0x31B400. Ver seccion 3 del docstring para
# el nivel de confianza de cada nombre (22 CERTAIN cross-validados, 33 LIKELY/
# GUESSING por formula quimica).
# -----------------------------------------------------------------------------
ORDEN_COMPONENTES_EX1995 = [
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
]
assert len(ORDEN_COMPONENTES_EX1995) == 55, "la tabla real tiene 55 filas"

# Nombres de los 22 componentes ya CERTAIN (cross-validados bit a bit contra
# `ISO_6976.TABLA_CONSTANTES`) -- los otros 33 son LIKELY/GUESSING (ver
# docstring seccion 3).
COMPONENTES_CERTAIN_EX1995 = frozenset([
    "Metano", "Etano", "Propano", "i-Butano", "n-Butano", "i-Pentano",
    "n-Pentano", "neo-Pentano", "n-Hexano", "n-Heptano", "n-Octano",
    "n-Nonano", "n-Decano", "Hidrogeno", "Agua", "H2S", "CO", "Helio",
    "Argon", "Nitrogeno", "Oxigeno", "CO2",
])
assert len(COMPONENTES_CERTAIN_EX1995) == 22

# -----------------------------------------------------------------------------
# TABLA_CONSTANTES_EX1995 -- extraida de GOT_BASE-0x919e8 (file offset
# 0x31B400), 55 filas x 280 bytes (35 doubles), layout [0]=Mj [1:4]=factor
# Z0-candidato (no usado por las formulas de este modulo) [4:7]=bj
# [7:11]=Hoj_bruto molar [11:15]=Hoj_neto molar (ver seccion 2 del docstring).
# Unidades: Mj en g/mol, Hoj en kJ/mol -- mismas unidades que
# `ISO_6976.TABLA_CONSTANTES`.
# -----------------------------------------------------------------------------
TABLA_CONSTANTES_EX1995 = {
    "Metano":            {"Mj": 16.043,  "bj": [0.049, 0.0447, 0.0436],
                           "Hoj_bruto": [890.63, 891.09, 891.56, 892.97],
                           "Hoj_neto":  [802.60, 802.65, 802.69, 802.82]},
    "Etano":             {"Mj": 30.07,   "bj": [0.1, 0.0922, 0.0894],
                           "Hoj_bruto": [1560.69, 1561.41, 1562.14, 1564.34],
                           "Hoj_neto":  [1428.64, 1428.74, 1428.84, 1429.12]},
    "Propano":           {"Mj": 44.097,  "bj": [0.1453, 0.1338, 0.1288],
                           "Hoj_bruto": [2219.17, 2220.13, 2221.10, 2224.01],
                           "Hoj_neto":  [2043.11, 2043.23, 2043.37, 2043.71]},
    # [CORREGIDO 2026-08-06] i-Butano/n-Butano estaban INTERCAMBIADOS -- este
    # archivo heredo el bug al cross-validar contra `ISO_6976.TABLA_CONSTANTES`
    # (que tenia el mismo error). Ver seccion 5 del docstring de `ISO_6976.py`
    # para la evidencia completa (entalpia de combustion publica + evidencia
    # directa de codigo maquina en `ISO_6976_ex_2016.py`).
    "i-Butano":          {"Mj": 58.123,  "bj": [0.2049, 0.1789, 0.1703],
                           "Hoj_bruto": [2868.20, 2869.38, 2870.58, 2874.20],
                           "Hoj_neto":  [2648.12, 2648.26, 2648.42, 2648.83]},
    "n-Butano":          {"Mj": 58.123,  "bj": [0.2069, 0.1871, 0.1783],
                           "Hoj_bruto": [2877.40, 2878.57, 2879.76, 2883.82],
                           "Hoj_neto":  [2657.32, 2657.45, 2657.60, 2658.45]},
    # [CORREGIDO 2026-08-06, mismo hallazgo] i-Pentano/n-Pentano intercambiados.
    "i-Pentano":         {"Mj": 72.15,   "bj": [0.251, 0.228, 0.2168],
                           "Hoj_bruto": [3528.83, 3530.24, 3531.68, 3535.98],
                           "Hoj_neto":  [3264.73, 3264.89, 3265.08, 3265.54]},
    "n-Pentano":         {"Mj": 72.15,   "bj": [0.2864, 0.251, 0.2345],
                           "Hoj_bruto": [3535.77, 3537.17, 3538.60, 3542.89],
                           "Hoj_neto":  [3271.67, 3271.83, 3272.00, 3272.45]},
    "neo-Pentano":       {"Mj": 72.15,   "bj": [0.2387, 0.2121, 0.2025],
                           "Hoj_bruto": [3514.61, 3516.01, 3517.43, 3521.72],
                           "Hoj_neto":  [3250.51, 3250.67, 3250.83, 3251.28]},
    "n-Hexano":          {"Mj": 86.177,  "bj": [0.3286, 0.295, 0.2846],
                           "Hoj_bruto": [4194.95, 4196.58, 4198.24, 4203.23],
                           "Hoj_neto":  [3886.84, 3887.01, 3887.21, 3887.71]},
    # --- 33 componentes NUEVOS (ver seccion 3 del docstring, LIKELY/GUESSING
    #     el nombre/isomero exacto, CERTAIN la formula/masa molar) ---
    "2-metilpentano":    {"Mj": 86.177,  "bj": [0.3194, 0.2933, 0.272],
                           "Hoj_bruto": [4187.32, None, None, None],
                           "Hoj_neto":  [3879.21, None, None, None]},
    "3-metilpentano":    {"Mj": 86.177,  "bj": [0.3194, 0.2881, 0.2683],
                           "Hoj_bruto": [4189.90, None, None, None],
                           "Hoj_neto":  [3881.79, None, None, None]},
    "2,2-dimetilbutano": {"Mj": 86.177,  "bj": [0.2898, 0.2627, 0.255],
                           "Hoj_bruto": [4177.52, None, None, None],
                           "Hoj_neto":  [3869.41, None, None, None]},
    "2,3-dimetilbutano": {"Mj": 86.177,  "bj": [0.3, 0.2739, 0.2569],
                           "Hoj_bruto": [4185.28, None, None, None],
                           "Hoj_neto":  [3877.17, None, None, None]},
    "n-Heptano":         {"Mj": 100.204, "bj": [0.4123, 0.3661, 0.3521],
                           "Hoj_bruto": [4853.43, 4855.29, 4857.18, 4862.87],
                           "Hoj_neto":  [4501.30, 4501.49, 4501.72, 4502.28]},
    "n-Octano":          {"Mj": 114.231, "bj": [0.5079, 0.445, 0.4278],
                           "Hoj_bruto": [5511.80, 5513.88, 5516.01, 5522.40],
                           "Hoj_neto":  [5115.66, 5115.87, 5116.11, 5116.73]},
    "n-Nonano":          {"Mj": 128.258, "bj": [0.6221, 0.5385, 0.5148],
                           "Hoj_bruto": [6171.15, 6173.46, 6175.82, 6182.91],
                           "Hoj_neto":  [5730.99, 5731.22, 5731.49, 5732.17]},
    "n-Decano":          {"Mj": 142.285, "bj": [0.7523, 0.645, 0.614],
                           "Hoj_bruto": [6829.77, 6832.31, 6834.90, 6842.69],
                           "Hoj_neto":  [6345.59, 6345.85, 6346.14, 6346.88]},
    "Etileno":           {"Mj": 28.054,  "bj": [0.0866, 0.08, 0.0775],
                           "Hoj_bruto": [1411.18, None, None, None],
                           "Hoj_neto":  [1323.15, None, None, None]},
    "Propileno":         {"Mj": 42.081,  "bj": [0.1378, 0.1265, 0.1225],
                           "Hoj_bruto": [2058.02, None, None, None],
                           "Hoj_neto":  [1925.97, None, None, None]},
    "1-Buteno":          {"Mj": 56.108,  "bj": [0.1871, 0.1732, 0.1673],
                           "Hoj_bruto": [2716.82, None, None, None],
                           "Hoj_neto":  [2540.76, None, None, None]},
    "cis-2-Buteno":      {"Mj": 56.108,  "bj": [0.1975, 0.1817, 0.1761],
                           "Hoj_bruto": [2710.00, None, None, None],
                           "Hoj_neto":  [2533.90, None, None, None]},
    "trans-2-Buteno":    {"Mj": 56.108,  "bj": [0.1975, 0.1789, 0.1761],
                           "Hoj_bruto": [2706.40, None, None, None],
                           "Hoj_neto":  [2530.30, None, None, None]},
    "Isobutileno":       {"Mj": 56.108,  "bj": [0.1871, 0.1703, 0.1673],
                           "Hoj_bruto": [2700.20, None, None, None],
                           "Hoj_neto":  [2524.10, None, None, None]},
    "1-Penteno":         {"Mj": 70.134,  "bj": [0.249, 0.2258, 0.2191],
                           "Hoj_bruto": [3375.42, None, None, None],
                           "Hoj_neto":  [3155.34, None, None, None]},
    "Propadieno":        {"Mj": 40.065,  "bj": [0.1414, 0.1304, 0.1265],
                           "Hoj_bruto": [1943.11, None, None, None],
                           "Hoj_neto":  [1855.08, None, None, None]},
    # [CORREGIDO 2026-08-07, ver seccion 5 del docstring] los nombres 1,2-/1,3-
    # Butadieno estaban INTERCAMBIADOS -- confirmado por la tabla real de
    # nombres embebida en el binario (fila25=1,2-Butadieno, fila26=
    # 1,3-Butadieno). Los valores numericos NO cambiaron, solo las etiquetas.
    "1,2-Butadieno":     {"Mj": 54.092,  "bj": [0.2121, 0.1924, 0.1871],
                           "Hoj_bruto": [2593.79, None, None, None],
                           "Hoj_neto":  [2461.74, None, None, None]},
    "1,3-Butadieno":     {"Mj": 54.092,  "bj": [0.1844, 0.1703, 0.1643],
                           "Hoj_bruto": [2540.77, None, None, None],
                           "Hoj_neto":  [2408.72, None, None, None]},
    "Acetileno":         {"Mj": 26.038,  "bj": [0.0949, 0.0837, 0.0837],
                           "Hoj_bruto": [1301.05, None, None, None],
                           "Hoj_neto":  [1257.03, None, None, None]},
    # [RENOMBRADOS 2026-08-07, ver seccion 5 del docstring] "2-Penteno",
    # "Hexeno", "Hepteno" y "Octeno" eran GUESSING por formula quimica
    # (C5H10/C6H12/C7H14/C8H16 podian ser alqueno de cadena recta O cicloalcano
    # sustituido -- ambas familias comparten formula). La tabla real de
    # nombres embebida en el binario confirma que estas 4 filas SON
    # cicloalcanos (Ciclopentano/Metilciclopentano/Etilciclopentano/
    # Etilciclohexano), NO alquenos de cadena recta -- los valores numericos
    # (Mj/bj/Hoj) NO cambiaron, solo la etiqueta/nombre.
    "Ciclopentano":      {"Mj": 70.134,  "bj": [0.255, 0.2302, 0.2236],
                           "Hoj_bruto": [3319.59, None, None, None],
                           "Hoj_neto":  [3099.51, None, None, None]},
    "Metilciclopentano": {"Mj": 84.161,  "bj": [0.313, 0.2811, 0.2702],
                           "Hoj_bruto": [3969.44, None, None, None],
                           "Hoj_neto":  [3705.34, None, None, None]},
    "Etilciclopentano":  {"Mj": 98.188,  "bj": [0.3987, 0.3521, 0.3391],
                           "Hoj_bruto": [4628.47, None, None, None],
                           "Hoj_neto":  [4320.36, None, None, None]},
    "Ciclohexano":       {"Mj": 84.161,  "bj": [0.3209, 0.2864, 0.2757],
                           "Hoj_bruto": [3952.96, None, None, None],
                           "Hoj_neto":  [3688.86, None, None, None]},
    "Metilciclohexano":  {"Mj": 98.188,  "bj": [0.3808, 0.3376, 0.3256],
                           "Hoj_bruto": [4600.64, None, None, None],
                           "Hoj_neto":  [4292.53, None, None, None]},
    "Etilciclohexano":   {"Mj": 112.215, "bj": [0.4796, 0.4195, 0.4025],
                           "Hoj_bruto": [5263.05, None, None, None],
                           "Hoj_neto":  [4910.92, None, None, None]},
    "Benceno":           {"Mj": 78.114,  "bj": [0.3017, 0.272, 0.253],
                           "Hoj_bruto": [3301.43, None, None, None],
                           "Hoj_neto":  [3169.38, None, None, None]},
    "Tolueno":           {"Mj": 92.141,  "bj": [0.3886, 0.3421, 0.3286],
                           "Hoj_bruto": [3947.89, None, None, None],
                           "Hoj_neto":  [3771.83, None, None, None]},
    # [RENOMBRADO 2026-08-07] "m-Xileno" era GUESSING; la tabla real de
    # nombres confirma "Etilbenceno" (Ethylbenzene, C8H10, mismo isomero
    # de formula que xileno pero compuesto distinto) -- valores sin cambio.
    "Etilbenceno":       {"Mj": 106.167, "bj": [0.4858, 0.4207, 0.4037],
                           "Hoj_bruto": [4607.15, None, None, None],
                           "Hoj_neto":  [4387.07, None, None, None]},
    "o-Xileno":          {"Mj": 106.167, "bj": [0.5128, 0.4427, 0.4231],
                           "Hoj_bruto": [4596.31, None, None, None],
                           "Hoj_neto":  [4376.23, None, None, None]},
    "Metanol":           {"Mj": 32.042,  "bj": [0.4764, 0.3578, 0.3286],
                           "Hoj_bruto": [764.09, None, None, None],
                           "Hoj_neto":  [676.06, None, None, None]},
    "Metanotiol":        {"Mj": 48.109,  "bj": [0.1673, 0.1517, 0.1483],
                           "Hoj_bruto": [1239.39, None, None, None],
                           "Hoj_neto":  [1151.36, None, None, None]},
    "Hidrogeno":         {"Mj": 2.0159,  "bj": [-0.004, -0.0048, -0.0051],
                           "Hoj_bruto": [285.83, 285.99, 286.15, 286.63],
                           "Hoj_neto":  [241.81, 241.76, 241.72, 241.56]},
    "Agua":              {"Mj": 18.0153, "bj": [0.2646, 0.2345, 0.2191],
                           "Hoj_bruto": [44.016, 44.224, 44.433, 45.074],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "H2S":               {"Mj": 34.082,  "bj": [0.1, 0.1, 0.1],
                           "Hoj_bruto": [562.01, 562.19, 562.38, 562.94],
                           "Hoj_neto":  [517.99, 517.97, 517.95, 517.87]},
    "Amoniaco":          {"Mj": 17.0306, "bj": [0.1225, 0.1095, 0.1049],
                           "Hoj_bruto": [382.81, None, None, None],
                           "Hoj_neto":  [316.79, None, None, None]},
    "Acido cianhidrico": {"Mj": 27.026,  "bj": [0.3362, 0.2966, 0.2828],
                           "Hoj_bruto": [671.50, None, None, None],
                           "Hoj_neto":  [649.50, None, None, None]},
    "CO":                {"Mj": 28.01,   "bj": [0.0265, 0.0224, 0.02],
                           "Hoj_bruto": [282.98, 282.95, 282.91, 282.80],
                           "Hoj_neto":  [282.98, 282.95, 282.91, 282.80]},
    "Sulfuro de carbonilo (COS)": {"Mj": 60.076, "bj": [0.1225, 0.114, 0.1095],
                           "Hoj_bruto": [548.23, None, None, None],
                           "Hoj_neto":  [548.23, None, None, None]},
    "Disulfuro de carbono (CS2)": {"Mj": 76.143, "bj": [0.2145, 0.1949, 0.1871],
                           "Hoj_bruto": [1104.49, None, None, None],
                           "Hoj_neto":  [1104.49, None, None, None]},
    "Helio":             {"Mj": 4.0026,  "bj": [0.0006, 0.0002, 0.0],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "Neon":              {"Mj": 20.1797, "bj": [0.0006, 0.0002, 0.0],
                           "Hoj_bruto": [0.0, None, None, None],
                           "Hoj_neto":  [0.0, None, None, None]},
    "Argon":             {"Mj": 39.948,  "bj": [0.0316, 0.0283, 0.0265],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "Nitrogeno":         {"Mj": 28.0135, "bj": [0.0224, 0.0173, 0.0173],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "Oxigeno":           {"Mj": 31.9988, "bj": [0.0316, 0.0283, 0.0265],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "CO2":               {"Mj": 44.01,   "bj": [0.0819, 0.0748, 0.0728],
                           "Hoj_bruto": [0.0, 0.0, 0.0, 0.0],
                           "Hoj_neto":  [0.0, 0.0, 0.0, 0.0]},
    "Dioxido de azufre (SO2)": {"Mj": 64.065, "bj": [0.1549, 0.1449, 0.1414],
                           "Hoj_bruto": [0.0, None, None, None],
                           "Hoj_neto":  [0.0, None, None, None]},
}
assert set(TABLA_CONSTANTES_EX1995) == set(ORDEN_COMPONENTES_EX1995) == \
    frozenset(ORDEN_COMPONENTES_EX1995), (
        "TABLA_CONSTANTES_EX1995 debe tener exactamente las 55 filas reales"
    )
assert len(TABLA_CONSTANTES_EX1995) == 55

# NOTA: los valores `None` en Hoj_bruto/Hoj_neto (indices 1..3) corresponden a
# combinaciones de temperatura de combustion que NO se extrajeron para las 33
# filas nuevas en esta tarea (se prioriza el indice 0 porque es suficiente
# para el autotest de consistencia interna de la seccion siguiente, que solo
# usa componentes de los 22 ya CERTAIN). Si se necesita un indice distinto de
# 0 para un componente nuevo, hay que volver al volcado de memoria (offset ya
# documentado, seccion 2 del docstring) y extraer las columnas [8],[9],[10] /
# [12],[13],[14] de esa fila -- trivial con el mismo script, no se hizo por
# no ser necesario para el estado actual de esta tarea.


def calcular_masa_molar_ex1995(fracciones_molares: dict) -> float:
    """Mmix = sum(xj * Mj), sobre los 55 componentes de la tabla "ex" 1995.

    [LIKELY] Formula asumida identica a `ISO_6976.calcular_masa_molar` por
    similitud estructural del binario (`calculate_revision_1` es, igual que
    `PropertiesISO6976_1995_rev1`, una funcion autocontenida con el patron
    "Metodo A tabulado" ya CERTAIN en el resto del proyecto) -- NO confirmado
    contra un caso real de la variante "ex" (ver seccion 4 del docstring).
    """
    return sum(
        fracciones_molares.get(c, 0.0) * TABLA_CONSTANTES_EX1995[c]["Mj"]
        for c in ORDEN_COMPONENTES_EX1995
    )


# [CERTAIN, ver RONDA 3 del docstring principal] Mapeo `conditions` (0..5,
# el parametro REAL de `calculate_revision_1`) -> indice de columna de bj/Hoj
# en `TABLA_CONSTANTES_EX1995`, aislado por llamada Frida DIRECTA con
# composicion 100% n-Decano (unico componente sin ambiguedad numerica).
CONDITIONS_A_INDICE_BJ = {0: 1, 1: 0, 2: 0, 3: 0, 4: 2, 5: 2}
CONDITIONS_A_INDICE_HOJ = {0: 2, 1: 3, 2: 2, 3: 0, 4: 1, 5: 0}


def calcular_factor_compresion_ex1995(fracciones_molares: dict, indice_temp: int) -> float:
    """Z = 1 - (sum(xj*bj_columna))^2, sobre 55 componentes.

    [CERTAIN, ver RONDA 3 del docstring principal] Formula CORREGIDA contra
    llamada REAL y DIRECTA (Frida) a `calculate_revision_1` -- a diferencia de
    `ISO_6976.calcular_factor_compresion` (namespace `iso6976_2016`,
    DISTINTO), esta funcion (`calculate_revision_1`, namespace `iso6976_1995`)
    NO aplica `sqrt()` a `bj` en ningun punto del codigo real, y NO tiene
    ningun factor `p_ref/(R*T0)` -- confirmado aislando un solo componente
    (n-Decano puro, bj muy separados entre columnas: 0.7523/0.645/0.614) y
    verificado de nuevo con la composicion completa "Default" (columna 1):
    Z=0.9981358821579642 calculado aqui vs 0.998136265018026 real (Frida),
    dif. 0.0000384%. Version anterior de esta funcion (con `sqrt(bj)` y un
    termino `p_ref_kPa/(R*T0)`, copiada por similitud de `ISO_6976.py`, NUNCA
    validada contra ningun caso real hasta esta ronda) queda REFUTADA y
    reemplazada. `indice_temp` 0..2 sigue siendo el indice de columna de bj
    -- usar `CONDITIONS_A_INDICE_BJ[conditions]` si se parte del parametro
    real `conditions` en vez del indice de columna directo.
    """
    suma = 0.0
    for c in ORDEN_COMPONENTES_EX1995:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        suma += x * TABLA_CONSTANTES_EX1995[c]["bj"][indice_temp]
    return 1.0 - suma ** 2


def calcular_poder_calorifico_molar_ex1995(fracciones_molares: dict, tipo: str,
                                            indice_temp_combustion: int = 0) -> float:
    """Hm = sum(xj * Hoj[indice]), en kJ/mol, sobre 55 componentes.

    [LIKELY, misma salvedad]. Por defecto usa indice 0 -- para las 33 filas
    nuevas es el UNICO indice extraido en esta tarea (ver nota arriba).
    """
    clave = "Hoj_bruto" if tipo == "bruto" else "Hoj_neto"
    total = 0.0
    for c in ORDEN_COMPONENTES_EX1995:
        x = fracciones_molares.get(c, 0.0)
        if x == 0.0:
            continue
        valor = TABLA_CONSTANTES_EX1995[c][clave][indice_temp_combustion]
        if valor is None:
            raise ValueError(
                f"Hoj_{tipo} indice {indice_temp_combustion} no extraido "
                f"para '{c}' -- ver nota en TABLA_CONSTANTES_EX1995."
            )
        total += x * valor
    return total


def calcular_volumen_molar_ideal_ex1995(t: float, p: float) -> float:
    """Vm_ideal = R*T/p -- formula de gas ideal, sin cambios."""
    return R_GAS * t / p


def calcular_volumen_molar_real_ex1995(vm_ideal: float, z: float) -> float:
    """Vm_real = Vm_ideal * Z -- sin cambios respecto a `ISO_6976.py`."""
    return vm_ideal * z


def _autotest_consistencia_interna():
    """[NO ES UN CASO REAL DE LA VARIANTE "EX" -- ver docstring seccion 4]

    Chequeo de CONSISTENCIA INTERNA, no de cierre contra un caso real: se
    reutiliza la MISMA composicion "Default" ya CERRADA en
    `ISO_6976_1995.py` (que solo usa componentes de los 22 ya CERTAIN) y se
    verifica que, calculando con la tabla/orden de 55 filas de ESTE modulo,
    Mmix/Z/Hm dan el MISMO resultado que con la tabla de 22 de
    `ISO_6976.py`. Esto prueba que la extraccion de las 22 filas conocidas
    dentro de la tabla de 55 esta bien indexada (sin importar que las otras
    33 filas nunca se usen aqui) -- NO prueba que `calculate_revision_1`
    (el motor real de la variante "ex") produzca estos numeros, porque no
    hay caso real de esa funcion disponible (ver seccion 4 del docstring).
    """
    from . import ISO_6976
    from . import ISO_6976_1995 as base1995

    comp_pct = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    comp_22 = {c: 0.0 for c in ISO_6976.ORDEN_COMPONENTES_APP}
    comp_55 = {c: 0.0 for c in ORDEN_COMPONENTES_EX1995}
    for nombre, pct in comp_pct.items():
        comp_22[nombre] = pct / 100.0
        comp_55[nombre] = pct / 100.0

    mmix_22 = ISO_6976.calcular_masa_molar(comp_22)
    mmix_55 = calcular_masa_molar_ex1995(comp_55)

    hm_22 = ISO_6976.calcular_poder_calorifico_molar(
        comp_22, "bruto", indice_temp_combustion=2)
    # las 4 filas conocidas usadas aqui (Metano/Etano/Propano/i-Butano/
    # n-Butano/i-Pentano/n-Pentano/neo-Pentano/n-Hexano/n-Heptano/n-Octano/
    # Nitrogeno/CO2/Helio) SI tienen los 4 indices extraidos -- se puede usar
    # indice 2 sin problema.
    hm_55 = calcular_poder_calorifico_molar_ex1995(
        comp_55, "bruto", indice_temp_combustion=2)

    print("=== AUTOTEST DE CONSISTENCIA INTERNA (Mmix/Hm, NO es caso real) ===")
    print("(usa la composicion 'Default' ya CERRADA en ISO_6976_1995.py, con")
    print(" componentes que SI estan entre los 22 CERTAIN de la tabla de 55)")
    print("NOTA: Z ya NO se compara aqui -- desde la RONDA 3 (2026-08-08) se")
    print("confirmo por caso real que la formula de Z de `calculate_revision_1`")
    print("(namespace iso6976_1995, SIN sqrt/p_ref) es DISTINTA por diseno de")
    print("`ISO_6976.calcular_factor_compresion` (namespace iso6976_2016, CON")
    print("sqrt/p_ref) -- comparar Z entre ambas ya no es un chequeo valido,")
    print("ver `_autotest_caso_real_directo_frida` para la validacion real de Z.")
    print()
    print(f"  Mmix (tabla 22): {mmix_22:.6f}   Mmix (tabla 55): {mmix_55:.6f}   "
          f"dif={abs(mmix_22 - mmix_55):.2e}")
    print(f"  Hm bruto (tabla 22): {hm_22:.6f}   Hm bruto (tabla 55): {hm_55:.6f}   "
          f"dif={abs(hm_22 - hm_55):.2e}")
    ok = abs(mmix_22 - mmix_55) < 1e-9 and abs(hm_22 - hm_55) < 1e-9
    print()
    print("  [OK, tabla de 55 filas indexa igual que la tabla de 22 ya CERTAIN]"
          if ok else "  [FALLO -- revisar mapeo fila->componente]")


def _autotest_caso_real_directo_frida():
    """[CASO REAL, ver RONDA 3 del docstring principal y su seccion 6]

    Reproduce, SIN Frida (los numeros ya se capturaron y quedaron pegados
    aqui), el resultado de la llamada DIRECTA real a `calculate_revision_1`
    con la composicion "Default" (22 componentes conocidos), conditions=0,
    molar_mass_method=1, cv_calculation_method=1 -- ver
    `android_sdk_setup/call_iso6976_ex1995_directo_out.json` para el log
    completo de las 24 combinaciones probadas, y
    `android_sdk_setup/run_call_iso6976_ex1995_directo.py` para re-ejecutar
    la llamada real si se quiere reconfirmar (requiere emulador + frida-server
    + app corriendo).
    """
    comp_pct = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "Helio": 0.046,
        "neo-Pentano": 0.008,
    }
    comp_55 = {c: 0.0 for c in ORDEN_COMPONENTES_EX1995}
    for nombre, pct in comp_pct.items():
        comp_55[nombre] = pct / 100.0

    # Real, capturado por Frida (conditions=0 -> columna bj=1):
    REAL_Z = 0.998136265018026
    REAL_MMIX_MMM1 = 18.6372061008  # molar_mass_method=1 (bit-exacto al real)

    idx_bj = CONDITIONS_A_INDICE_BJ[0]
    z_calc = calcular_factor_compresion_ex1995(comp_55, indice_temp=idx_bj)
    mmix_mmm2 = calcular_masa_molar_ex1995(comp_55)  # Metodo A tabulado

    dif_z = abs(z_calc - REAL_Z) / REAL_Z * 100
    dif_mmix = abs(mmix_mmm2 - REAL_MMIX_MMM1) / REAL_MMIX_MMM1 * 100

    print("=== AUTOTEST: caso real DIRECTO (Frida) de calculate_revision_1 ===")
    print(f"  Z calculado (formula corregida, sin sqrt/p_ref, columna bj="
          f"{idx_bj}) = {z_calc:.10f}")
    print(f"  Z real (Frida, conditions=0, mmm=1, cvm=1)  = {REAL_Z:.10f}")
    print(f"  dif = {dif_z:.6f}%  ({'OK, <0.01%' if dif_z < 0.01 else 'FUERA DE MARGEN'})")
    print()
    print(f"  Mmix calculado (Metodo A tabulado, mmm=2)   = {mmix_mmm2:.6f} g/mol")
    print(f"  Mmix real (Frida, mmm=1, tabla NO mapeada)  = {REAL_MMIX_MMM1:.6f} g/mol")
    print(f"  dif = {dif_mmix:.4f}%  (mmm=1 y mmm=2 son metodos DISTINTOS, ver "
          f"docstring RONDA 3 -- diferencia esperada, no un error)")


if __name__ == "__main__":
    _autotest_consistencia_interna()
    print()
    _autotest_caso_real_directo_frida()
