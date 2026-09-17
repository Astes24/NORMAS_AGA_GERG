# -*- coding: utf-8 -*-
"""
normas/GasViscosity_2004.py
============================
Viscosidad dinamica de gas natural segun P. Schley, M. Jaeschke,
C. Kuechenmeister, E. Vogel, "Viscosity Measurements and Predictions for
Natural Gas" (2004) -- tal como esta implementada en FlowXpert
(`GasViscosity_2004`, categoria "Math", grupo "Viscosity").

Este archivo se puede ejecutar solo:
    python -m normas.GasViscosity_2004

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
RONDA 2 (2026-08-18): Fases 4 y 5 COMPLETADAS -- SI existe pantalla real en la
app Android (Gas > Viscosity > "Natural gas dynamic viscosity", categoria con
un unico item), se confirmo la unidad de `temperature` como grados Celsius de
forma EXPLICITA (no inferida) y se validaron 3 casos reales contra el motor
en vivo del `.so`, con coincidencia exacta al redondeo de pantalla (6
decimales) en los 3. Fase 7 (cromatografo) evaluada -- ver detalle abajo.
RONDA 1 habia completado Fases 1, 2 y 3 (identificar, decompilar, cruzar
contra metodo publico).

RONDA 6 (2026-08-19): Se encontro el manual OFICIAL de ABB SpiritIT
(`Flow-X Manual IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf`, pagina 83,
funcion `fxGasViscosity_2004`), leido con `pdfplumber` (Poppler no esta
instalado en este equipo). El manual documenta, de forma EXPLICITA y
TEXTUAL, la tabla completa de reduccion de los 22 componentes estandar a
los 12 que usa el motor real -- ver seccion "REDUCCION OFICIAL 22 A 12
COMPONENTES" mas abajo. Esto CIERRA el pendiente que quedaba abierto en
Ronda 4/5 sobre que hace el motor con Helio/Argon/Hidrogeno/Oxigeno/Agua/
H2S/CO/n-Nonano/n-Decano/neo-Pentano (ya NO es [LIKELY]/[GUESSING], es
[CERTAIN] por fuente documental oficial, no por ingenieria inversa). El
manual tambien documenta el rango de validez fisica real del metodo
publicado (250 K a 450 K, presion hasta 30 MPa) y la incertidumbre estimada
(0.5% gas natural tipico, 0.3% metano puro) -- dato que NUNCA estuvo en el
binario (los rangos de UI -200/400 y 0/2000 son limites genericos de
entrada, no el rango de validez fisica, como ya se documentaba en rondas
anteriores).

RONDA 3 (2026-08-18): Fase 6 COMPLETADA -- se decompilo el nucleo aritmetico
real del `.xll` (funcion callback `FUN_1800a7cec`, proyecto Ghidra reusado
`D:\PROYECTOS FOQUS\analisis xll\ANALISIS .XLL.gpr`, Ghidra 12.1.2, SIN el
bug de cuerpo vacio que afecta solo al `.so` de Android) y se comparo termino
a termino y constante a constante contra el `.so` ya decompilado en rondas
anteriores. Resultado: coincidencia COMPLETA, estructural Y numerica byte a
byte, en las 48 constantes D/A/B/C de los 12 componentes, las 4 constantes
residuales a1..a4, y todas las constantes estructurales (R, xi_K=0.38009,
exponentes 0.25/(1/6)/(2/3), factor 8.0, offset 273.15, escalas
0.001/1e-6/1e-9, factor final 1e-6). Ver seccion "CONFIRMACION CRUZADA
COMPLETA (.xll vs .so) -- Fase 6" mas abajo para el detalle completo.

-------------------------------------------------------------------------------
[CERTAIN] Identificacion del simbolo real (Fase 1)
-------------------------------------------------------------------------------
`.xll` (Windows, `ANALISIS_GHIDRA_FLOWXPERT/ghidra_todos_los_nombres_output.txt`,
funcion [85/124] FUN_180088258): registra el export Excel real con
    FUN_180064600(param_1, &DAT_1802c45a8, FUN_1800a7cec, L"GasViscosity_2004",
        L"Natural gas dynamic viscosity",
        L"Dynamic viscosity of natural gas according to P.Schley et al.
          Viscosity Measurements and Predictions for Natural Gas (2004).",
        L"Math", 4, 4, 3, -2)
Grupo UI: "Viscosity". Tags: "metric,gas".

`.so` (Android, `apk_analisis/libFXLibrary.so`, tabla `.dynsym`, namespace real
tipo `spirit::math::...` -- mismo patron que ISO 6976/ISO 5167): el simbolo
mangled confirma el mismo texto de descripcion palabra por palabra:
    _Z22Math_GasViscosity_2004P17Function_CContextP15tagFUNCTION_ARGlRS1_
    _ZN36Function_Math_GasViscosity_2004_SpecC2Ev  (constructor de metadata,
        decompilado, contiene el mismo string EXACTO "Dynamic viscosity of
        natural gas according to P.Schley et al. Viscosity Measurements and
        Predictions for Natural Gas (2004).")
El namespace completo real es `spirit::math::gas_viscosity_2004`, con
funciones miembro nombradas explicitamente (no ofuscadas):
    do_calculation, from_standard_composition, normalize_composition,
    mixture_molar_mass, mixture_critical_temperature, mixture_critical_volume,
    mixture_critical_pressure, mixture_critical_density,
    component_critical_compressibility, mixture_critical_compressibility,
    residual_viscosity_factor, reduced_density, residual_viscosity,
    viscosity_limit_zero_density_for_component, interaction_parameter,
    viscosity_limit_zero_density.
Esta nomenclatura interna YA revela la estructura del metodo antes de leer una
sola linea de aritmetica (metodo de "estados correspondientes residual" con
limite de densidad cero + termino residual en funcion de densidad reducida).

-------------------------------------------------------------------------------
[CERTAIN] Motor: NO comparte motor con ninguna norma ya cerrada del proyecto
-------------------------------------------------------------------------------
Tiene namespace/tabla de coeficientes PROPIA (`gas_viscosity_2004::*`,
direcciones 0x239f10-0x23a010 y 0x325cf8-0x3260a0 en el `.so`), sin overlap
con las tablas de AGA8/GERG2008 ya extraidas en este proyecto. Es motor 100%
propio, como se sospechaba (viscosidad es un calculo fisico distinto de
densidad/factor de compresibilidad).

-------------------------------------------------------------------------------
[CERTAIN] Decompilacion del nucleo real (Fase 2) -- Ghidra 11.4.3 sobre el
`.so` (proyecto reusado `apk_analisis/ghidra_project_11.4.3/libFX114.gpr`,
sin el bug de cuerpo vacio de Ghidra 12.1.2). Scripts usados:
`apk_analisis/ghidra_scripts_11.4.3/DecompileGasViscosity2004.java` (cuerpos
C) y `DumpGasViscosity2004Consts.java` (bytes reales de cada constante DAT_
via `Memory.getBytes`, NO inferidos). Salidas completas en
`apk_analisis/ghidra_gasviscosity2004_output.txt` y
`apk_analisis/ghidra_gasviscosity2004_consts_output.txt`.
-------------------------------------------------------------------------------

ENTRADAS reales (confirmadas por la firma + el constructor de metadata):
  - density      [kg/m3], rango declarado en UI: 0.0 a 2000.0 kg/m3
                 (unit code 0x1001601)
  - temperature  rango declarado en UI: -200.0 a 400.0 (unit code 0x1002302)
                 [LIKELY, no 100% CERTAIN] en grados Celsius -- ver nota de
                 unidades mas abajo. El rango UI (-200/400) es mucho mas ancho
                 que el rango fisico real de validez del metodo publicado
                 (tipicamente ~-25 a 100 degC); es, como en otras normas de
                 este proyecto, un limite generico de UI, no el rango de
                 validez fisica del ajuste.
  - composition  array de 22 numeros en orden AGA8 (misma convencion que
                 AGA8/GERG en este proyecto), suma debe ser 1. El motor de
                 viscosidad SOLO usa 12 de esos 22 componentes (ver tabla).

SALIDA real: viscosity [Pa.s] (unit code VISCOSITY 0x1000401), mas
"status"/"Range Status"/"calc. range" (metadata de error, igual que el resto
de las normas Math_* de FlowXpert).

===============================================================================
FORMULA REAL DECOMPILADA (transcrita termino a termino desde el C real)
===============================================================================

do_calculation(composicion, T, rho) -> eta:
    x_norm = normalize_composition(x)          # suma-a-1 explicito
    eta0   = viscosity_limit_zero_density(x_norm, T + 273.15)
    eta_r  = residual_viscosity(x_norm, rho)
    eta    = (eta0 + eta_r) * 1e-6              # de microPa.s a Pa.s

Nota de unidades sobre "T + 273.15": el mismo desplazamiento de 273.15 se
resta de vuelta DENTRO de
`viscosity_limit_zero_density_for_component` (ver abajo), por lo que el
efecto neto sobre el resultado es CERO -- el polinomio por componente termina
usando el valor CRUDO de T que recibe `do_calculation` (sin la conversion a
Kelvin). [LIKELY] esto implica que el argumento `temperature` de la funcion
Excel/Android ya viene en grados Celsius (consistente con que el ajuste
publicado de Schley et al. se expresa en grados Celsius) y el codigo hace un
paso a Kelvin y de vuelta que result matematicamente en un no-op -- posible
remanente de refactor interno de FlowXpert, no afecta el resultado numerico.
No se pudo confirmar 100% la unidad de entrada sin un caso real (Fase 5).

-------------------------------------------------------------------------------
1) LIMITE DE DENSIDAD CERO (viscosidad de gas diluido, mezcla) -- MODELO DE
   WILKE (formula publica, Wilke 1950, "A Viscosity Equation for Gas
   Mixtures", J. Chem. Phys. 18) [CERTAIN -- estructura identica formula por
   formula a la publicada]:

   eta0_mix = sum_i [ x_i * eta0_i(T) / sum_j( x_j * phi_ij ) ]

   phi_ij = [ 1 + sqrt(eta0_i/eta0_j) * (M_j/M_i)^0.25 ]^2
            / sqrt( 8 * (1 + M_i/M_j) )

   -- formula de Wilke EXACTA, confirmada termino a termino contra el C
   decompilado de `interaction_parameter` (exponente 0.25 y factor 8.0 leidos
   como bytes reales de memoria, no supuestos).

   Viscosidad de gas diluido por componente puro (funcion propia de
   FlowXpert/Schley, forma cubica en T):

   eta0_i(T) = D_i * ( 1 + 0.001*A_i*t + 1e-6*B_i*t^2 + 1e-9*C_i*t^3 )

   donde t es la temperatura (grados, ver nota de unidades arriba) y D_i,
   A_i, B_i, C_i son coeficientes por componente (tabla completa abajo, 12
   componentes, leidos byte a byte de `apk_analisis/libFXLibrary.so`).

2) TERMINO RESIDUAL (dependiente de densidad reducida de la mezcla) --
   estructura tipo Jossi-Stiel-Thodos (grupo xi de "estados correspondientes
   residual"), pero con un polinomio de 4 coeficientes propios de Schley et
   al. (no los coeficientes clasicos publicados de JST 1966 -- se comparo y
   NO coinciden con 0.1023/0.023364/0.058533/-0.040758/0.0093324; son
   coeficientes REFITEADOS especificos de este metodo de 2004)
   [LIKELY -- estructura confirmada CERTAIN, coeficientes especificos no
   verificados letra por letra contra el PDF original porque no esta en
   `documentos_normativos/` de este proyecto]:

   eta_r(rho_r) = xi_mix * ( a1*rho_r + a2*rho_r^2 + a3*rho_r^3 + a4*rho_r^4 )

   rho_r  = rho / rho_c_mix                          # densidad reducida
   xi_mix = sqrt(M_mix) * Pc_mix^(2/3) / (Tc_mix^(1/6) * 0.38009)

   a1 = 0.23961032
   a2 = 0.57790957
   a3 = -0.24327596
   a4 = 0.12776597

3) REGLAS DE MEZCLA DE PROPIEDADES PSEUDOCRITICAS (todas lineales en fraccion
   molar, tipo Kay, confirmadas termino a termino) [CERTAIN]:

   M_mix  = sum_i ( x_i * M_i )                              # g/mol
   Tc_mix = sum_i ( x_i * Tc_i )                              # K
   Vc_mix = sum_i ( x_i * Vc_i )                              # cm3/mol
   Zc_mix = sum_i ( x_i * Zc_i ),  Zc_i = Pc_i*Vc_i/(R*Tc_i)   # R=8.3144621
   Pc_mix = Zc_mix * R * Tc_mix / Vc_mix                       # MPa
   rho_c_mix = M_mix * 1000 / Vc_mix                           # kg/m3

===============================================================================
TABLA DE COMPONENTES (12, subconjunto del orden AGA8 -- confirmado por Tc/Vc/Pc
digito por digito contra valores GERG-2008 ya usados en este proyecto)
===============================================================================
[CORREGIDO en Ronda 6, 2026-08-19 -- ver seccion "REDUCCION OFICIAL 22 A 12
COMPONENTES" mas abajo] Esta nota estaba INCOMPLETA: no son 10 componentes
descartados, son solo 3 (Agua, H2S, CO). Los otros 7 que no tienen fila
propia (Hidrogeno, Oxigeno, Helio, Argon, n-Nonano, n-Decano, neo-Pentano)
SI participan del calculo, redistribuidos hacia uno de los 12 componentes
segun la tabla oficial del manual ABB SpiritIT (Hidrogeno->Metano,
Oxigeno/Helio/Argon->Nitrogeno, n-Nonano/n-Decano->n-Octano,
neo-Pentano->i-Pentano). Ver `reducir_22_a_12()` mas abajo en el codigo.

idx  Componente     M[g/mol]   Tc[K]      Vc[cm3/mol] Pc[MPa]  D        A      B       C
0    Metano          16.043    190.564    98.63       4.599    10.257   3.230  -1.613   0.000
1    Nitrogeno       28.0135   126.192    89.41       3.396    16.627   2.848  -1.940   1.372
2    CO2             44.01     304.1282   94.12       7.377    13.717   3.539  -1.007  -0.443
3    Etano           30.07     305.322    145.55      4.872     8.487   3.607  -1.319   0.000
4    Propano         44.097    369.825    200.0       4.248     7.461   3.669  -1.052   0.000
5    n-Butano        58.123    425.125    255.1       3.796     6.814   3.613  -0.494   0.000
6    i-Butano        58.123    407.817    259.06      3.64      6.914   3.515  -0.682   0.000
7    n-Pentano       72.15     469.7      310.99      3.37      6.196   3.759  -0.698   0.000
8    i-Pentano       72.15     460.35     305.72      3.396     6.384   3.531  -0.376   0.000
9    n-Hexano        86.177    507.82     369.57      3.034     5.735   3.731  -0.479   0.000
10   n-Heptano       100.204   540.13     431.91      2.736     5.335   3.732  -0.277   0.000
11   n-Octano        114.231   569.32     486.3       2.497     5.095   3.854  -0.014   0.000

[CERTAIN] Cruce contra Tc/Pc/Vc publicos: los 12 juegos de Tc coinciden
digito por digito con los valores GERG-2008 estandar ya usados y validados en
`normas/GERG_2008.py` (metano 190.564 K, nitrogeno 126.192 K, CO2 304.1282 K,
etc., incluyendo el par n-Butano=425.125 K / i-Butano=407.817 K en el orden
correcto -- relevante porque este proyecto ya encontro y corrigio un swap
i-Butano/n-Butano en otra norma, ver memoria del proyecto; aqui el orden Tc
confirma que NO hay swap en GasViscosity_2004). Pc y Vc tambien coinciden con
los valores criticos publicos estandar de estos componentes (ej. Pc(CH4)=
4.599 MPa, Vc(CH4)=98.6 cm3/mol).

[LIKELY, no verificado letra por letra] Los coeficientes D/A/B/C del
polinomio de viscosidad de gas diluido por componente y los 4 coeficientes
a1..a4 del termino residual SON, con alta probabilidad, una transcripcion de
las tablas publicadas en Schley et al. (2004) -- no se pudo verificar
digito por digito porque el PDF original del articulo no esta disponible en
`documentos_normativos/` de este proyecto. Se cruzo la ESTRUCTURA del metodo
(Wilke + xi de Jossi-Stiel-Thodos + reglas de mezcla lineales) contra
conocimiento publico general de metodos de viscosidad por estados
correspondientes residuales, que SI calza exactamente forma por forma; los
valores numericos en si vienen directo del binario (extraidos byte a byte de
memoria real via Ghidra, no adivinados).

===============================================================================
CONFIRMACION CRUZADA COMPLETA (.xll vs .so) -- Fase 6 (RONDA 3, 2026-08-18)
===============================================================================
[CERTAIN] El rango de densidad (0.0 a 2000.0 kg/m3) y el rango de temperatura
(-200.0 a 400.0) son BYTE-IDENTICOS entre el `.xll` (Windows, decodificados de
los literales hexadecimales 0x409f400000000000=2000.0,
0xc069000000000000=-200.0, 0x4079000000000000=400.0 en
`ghidra_todos_los_nombres_output.txt`) y el `.so` (Android, leidos con Ghidra
11.4.3 via `Memory.getBytes`). Mismo texto de descripcion palabra por palabra
en ambas plataformas. Esto ya era evidencia fuerte de una sola fuente de
verdad compartida entre ambos binarios (aunque compilados por separado),
consistente con el patron ya visto en ISO 6976/ISO 5167 -- confirmado ahora
con el nucleo aritmetico completo (ver abajo).

[CERTAIN] DECOMPILACION DEL NUCLEO REAL EN EL `.xll`: se identifico la
funcion callback real de calculo `FUN_1800a7cec` (registrada junto al string
`L"GasViscosity_2004"` dentro de `FUN_180088258`, ver Fase 1 arriba) y se
decompilo en cascada con Ghidra 12.1.2 sobre el proyecto ya existente
`D:\PROYECTOS FOQUS\analisis xll\ANALISIS .XLL.gpr` (sin re-analisis, sin el
bug de cuerpo vacio -- ese bug es especifico de Ghidra 12.1.2 sobre el `.so`
de Android, NO afecta al `.xll`). Scripts usados (nuevos, en
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_scripts_xll/`):
`DecompileGasViscosity2004Xll.java` (decompilacion recursiva de 54 funciones,
profundidad 6, con extraccion automatica de toda direccion `DAT_` referenciada
en el C decompilado) y `DumpGasViscosity2004XllConsts.java` (bytes reales via
`Memory.getBytes` de las tablas completas de 12 componentes y los 4
coeficientes residuales, que el primer script solo capturo parcialmente por
usar aritmetica de punteros en los bucles). Salidas completas en
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_gasviscosity2004_xll_output.txt` y
`ghidra_gasviscosity2004_xll_consts_output.txt`.

El `.xll` usa nombres de simbolo genericos `FUN_xxx` (no tiene los mangled
names C++ legibles que si tiene el `.dynsym` del `.so`), pero la ESTRUCTURA
de llamadas mapea 1 a 1 contra los nombres reales ya conocidos del `.so`:

  FUN_1800a7cec          -> callback Excel (parseo de argumentos + dispatch)
  FUN_1800d83d4          -> mapeo composicion 22->12 (from_standard_composition)
  FUN_1800d8294          -> do_calculation
  FUN_1800d8744          -> normalize_composition (suma y divide, igual al .so)
  FUN_1800d88d8          -> viscosity_limit_zero_density (mezcla de Wilke)
  FUN_1800d89a0          -> viscosity_limit_zero_density_for_component (eta0_i(T))
  FUN_1800d8490          -> interaction_parameter (phi_ij de Wilke)
  FUN_1800d87d4          -> residual_viscosity
  FUN_1800d8874          -> residual_viscosity_factor (xi_mix)
  FUN_1800d87b0          -> reduced_density (rho/rho_c_mix)
  FUN_1800d85b4          -> mixture_critical_density (rho_c_mix)
  FUN_1800d85ec          -> mixture_critical_pressure (Pc_mix)
  FUN_1800d8558          -> mixture_critical_compressibility (Zc_mix)
  FUN_1800d8264          -> component_critical_compressibility (Zc_i)
  FUN_1800d8630          -> mixture_critical_temperature (Tc_mix)
  FUN_1800d8690          -> mixture_critical_volume (Vc_mix)
  FUN_1800d86f0          -> mixture_molar_mass (M_mix)

[CERTAIN] ESTRUCTURA DEL ALGORITMO IDENTICA: se confirmo termino a termino
que `FUN_1800d8294` (do_calculation) hace exactamente
`eta = eta0_mix*1e-6 + eta_r*1e-6` (algebraicamente identico a
`(eta0+eta_r)*1e-6` del `.so`, solo que el `.xll` distribuye la
multiplicacion en vez de factorizarla -- mismo resultado numerico). El
desplazamiento T+273.15 seguido de -273.15 dentro de la funcion por
componente (`FUN_1800d89a0`: `param_2 = param_2 - DAT_180194120` con
DAT_180194120=273.15, tras haber recibido T+273.15 desde `FUN_1800d8294`) es
el MISMO no-op matematico ya documentado en el `.so` (Fase 2/3), confirmado
ahora en un binario compilado de forma completamente independiente.

[CERTAIN] CONSTANTES ESTRUCTURALES BYTE-IDENTICAS (leidas de memoria real del
`.xll`, comparadas contra las ya confirmadas del `.so`):
  R (gas constante)            = 8.3144621   (DAT_1801d8290) -- MATCH exacto
  xi_K (escala residual)       = 0.38009     (DAT_1801e0b68) -- MATCH exacto
  exponente Wilke (M_j/M_i)    = 0.25        (DAT_180195128) -- MATCH exacto
  factor Wilke (denominador)   = 8.0         (DAT_180193fc8) -- MATCH exacto
  exponente Pc_mix en xi_mix   = 2/3 = 0.6666666666666666 (DAT_1801e0b70) -- MATCH
  exponente Tc_mix en xi_mix   = 1/6 = 0.16666666666666666 (DAT_1801e0b60) -- MATCH
  offset Kelvin (no-op)        = 273.15      (DAT_180194120) -- MATCH exacto
  escala termino A (0.001)     = 0.001       (DAT_1801d5ea8) -- MATCH exacto
  escala termino C (1e-9)      = 1.0E-9      (DAT_1801e0b58) -- MATCH exacto
  factor final microPa.s->Pa.s = 1.0E-6      (DAT_180193dc8) -- MATCH exacto
  M_mix*1000 (rho_c_mix)       = 1000.0      (DAT_180124818) -- MATCH exacto
  tolerancia suma composicion  = 0.9999/1.0001 (DAT_180193f00/DAT_180193f08)
                                  -- rango de validacion "suma debe ser 1"
                                  con tolerancia +-0.01%, no documentado antes
                                  en el .so con este nivel de detalle.

[CERTAIN] TABLA DE 12 COMPONENTES BYTE-IDENTICA: se extrajeron via
`Memory.getBytes` las 12 filas completas de M/Tc/Vc/Pc/D/A/B/C del `.xll`
(bases `0x1801e07d0` para M, `0x1801e09b8` con stride 0x20 para Tc/Vc/Pc, y
`0x1801e0830` con stride 0x20 para D/A/B/C) y se compararon digito por digito
contra la tabla ya confirmada del `.so` (seccion "TABLA DE COMPONENTES"
arriba). LAS 12 FILAS x 8 VALORES (96 numeros) COINCIDEN EXACTAMENTE, sin
una sola discrepancia, incluyendo el par n-Butano=425.125 K / i-Butano=407.817
K en el orden correcto (sin swap) y los ceros exactos del coeficiente C para
los componentes que no lo usan.

[CERTAIN] LOS 4 COEFICIENTES RESIDUALES COINCIDEN EXACTAMENTE: extraidos de
`DAT_1801e0b30` (stride 8 bytes) en el `.xll`:
    a1 = 0.23961032   a2 = 0.57790957   a3 = -0.24327596   a4 = 0.12776597
MATCH byte a byte contra los mismos 4 valores ya confirmados en el `.so`.

CONCLUSION DE LA CONFIRMACION CRUZADA: dos binarios compilados de forma
independiente para plataformas distintas (Windows x64 nativo vs Android
ARM, con toolchains y ofuscacion de simbolos distintas) implementan el
MISMO algoritmo con las MISMAS 100+ constantes numericas sin ninguna
discrepancia. Esto no prueba por si solo que los valores coincidan con el
paper original de Schley et al. (2004) -- eso seguiria requiriendo el PDF
original, ver PENDIENTES -- pero es la evidencia mas fuerte posible dentro
del alcance de este proyecto (sin el PDF) de que los valores transcritos NO
son un error de lectura/transcripcion de una sola ronda de Ghidra: la
probabilidad de que dos compilaciones independientes reproduzcan el MISMO
error de transcripcion en 100+ constantes es, a efectos practicos, nula.

===============================================================================
PANTALLA EN LA APP ANDROID (Fase 4/5, CONFIRMADO 2026-08-18)
===============================================================================
[CERTAIN] La busqueda estatica de la ronda 1 (grep de "Viscosity" sobre
`classes.dex` crudo) fue efectivamente NO concluyente como se sospechaba --
la pantalla SI existe. Ruta real en el menu de la app (categorizado por
organismo, NO por nombre de funcion): Gas > Viscosity > "Natural gas dynamic
viscosity" (unico item de esa categoria, se auto-abre al entrar). Capturada
via `adb shell monkey` (relanzamiento limpio del proceso) + `uiautomator
dump` + screenshots.

Layout real confirmado (resource-id de cada campo, util para futuros scripts
de UI/Frida sobre esta misma pantalla):
  - `function_input_type`="density", `function_input_value`, `function_input_unit`="kg/m3"
  - `function_input_type`="Temperature", `function_input_value`, `function_input_unit`="°C"
  - `function_input_type`="Composition", `function_input_component_name`="Default"/custom,
    `function_input_component_content`=string con 14 componentes (12 usados + He +
    un ultimo campo rotulado "C5" sin identificar con certeza, ver nota abajo)
  - `function_output_type`="Dynamic viscosity", `function_output_value`, `function_output_unit`="Pa.s"

[CERTAIN] UNIDAD DE `temperature` = grados Celsius, CONFIRMADA DE FORMA
EXPLICITA (no inferida por matematica de round-trip como en la ronda 1): el
dialogo de edicion del campo "Temperature" muestra literalmente, debajo del
simbolo "°C", el subtitulo "degree celsius" (`unit_description`,
resource-id `com.spiritit.flowxpert:id/unit_description`). Ya no es
[LIKELY] -- es lectura directa de la UI real, mismo dialogo que declara el
rango -200..400 ya conocido de la ronda 1. Esto tambien resuelve la nota de
la ronda 1: el desplazamiento +273.15/-273.15 dentro del codigo es en efecto
un no-op interno confirmado ahora en ambos lados (matematica Y UI).

[CERTAIN] 3 CASOS REALES obtenidos editando los campos in-place (density,
Temperature) y re-leyendo el resultado en pantalla -- en esta app el
resultado SI se recalcula en vivo con cada edicion confirmada con "OK" (no
hizo falta cerrar/reabrir la pantalla para disparar el calculo real, a
diferencia de otras normas de este proyecto; esto se infiere de que el
resultado cambio 3 veces de forma distinta y cada cambio coincide
exactamente con lo que predice la formula para el nuevo input, lo cual seria
estadisticamente improbable si fuera un valor cacheado/no recalculado).
Composicion usada en los 3 casos (composicion "Default" de la app, 12
componentes relevantes + 2 no usados por el motor de viscosidad, ver mapeo
abajo):
  C1=81.315%, N2=14.211%, CO2=0.99%, C2=2.829%, C3=0.38%, iC4=0.06%,
  nC4=0.072%, iC5=0.018%, nC5=0.033%, nC6=0.02%, nC7=0.013%, nC8=0.005%
  (mas He=0.046% y un campo rotulado "C5"=0.008% que el motor de 12
  componentes ignora -- ver nota abajo).

  Caso 1: T=0 degC,  rho=0 kg/m3   -> app: 0.000011 Pa.s | replica Python:
          1.1169323840536065e-05 Pa.s -> redondea a 0.000011 (MATCH exacto
          al redondeo de pantalla, 6 decimales)
  Caso 2: T=20 degC, rho=0 kg/m3   -> app: 0.000012 Pa.s | replica Python:
          1.1875...e-05 Pa.s -> redondea a 0.000012 (MATCH exacto)
  Caso 3: T=20 degC, rho=80 kg/m3  -> app: 0.000014 Pa.s | replica Python:
          1.4363...e-05 Pa.s -> redondea a 0.000014 (MATCH exacto)

Los 3 casos coinciden con el limite de precision que la app muestra (6
decimales de Pa.s = 2-3 cifras significativas a esta magnitud); no se pudo
exigir el margen <0.1% estandar del proyecto en terminos relativos estrictos
porque la UI de esta pantalla no expone mas decimales, pero el Caso 3 SI
ejercita ambos terminos de la formula (Wilke Y el termino residual con
densidad no nula) y el match sigue siendo exacto al redondeo, lo cual es
evidencia fuerte de que la formula completa (no solo el termino de densidad
cero) esta bien replicada.

[LIKELY, RONDA 4 2026-08-19] El campo "C5" (0.008%) SI fue identificado:
es neo-Pentano. Evidencia (uiautomator dump real sobre la pantalla, ver
`dump_visc.xml` de esta ronda):

1. La etiqueta EXACTA del campo, leida byte a byte del
   `function_input_component_content`, es literalmente "C5" (no "neo-C5"
   truncado, no "C5+") -- la app SI usa el rotulo corto "C5" para
   neo-Pentano en esta pantalla en particular (etiqueta de UI mas corta que
   en otras pantallas, pero no un artefacto de truncamiento: el string
   completo cabe sin cortar).
2. El valor 0.008% coincide EXACTO (no solo "parecido") con neo-Pentano de
   la composicion "Default" ya documentada en `normas/ISO_6976.py` (linea
   831 de ese archivo: "Helio 0.046%, neo-Pentano 0.008%"). El campo "He"
   de esta misma pantalla TAMBIEN coincide exacto (0.046%) con el mismo
   registro. Ambos valores idénticos en 2 pantallas distintas de la app
   (ISO 6976 y GasViscosity_2004) es evidencia fuerte de que comparten el
   MISMO objeto de composicion "Default" a nivel de app (no coincidencia).
3. Suma de control: C1 81.315 + N2 14.211 + CO2 0.99 + C2 2.829 + C3 0.38 +
   iC4 0.06 + nC4 0.072 + iC5 0.018 + nC5 0.033 + nC6 0.02 + nC7 0.013 +
   nC8 0.005 + He 0.046 + C5(neo) 0.008 = 100.000% EXACTO. Confirma que
   "C5" es el componente 14/14 que completa la composicion a 100%, no un
   residual de redondeo (un residual de redondeo no habria dado una suma
   perfecta a 3 decimales).

[RESUELTO en Ronda 6, 2026-08-19, ver seccion "REDUCCION OFICIAL 22 A 12
COMPONENTES" mas abajo] Ya NO es [GUESSING]. El manual oficial ABB SpiritIT
confirma la opcion (b) para neo-Pentano, pero de forma FIJA (no via el
selector "neo-Pentane Mode" de AGA8/GERG-2008): neo-Pentano SIEMPRE se pliega
dentro de i-Pentano para este metodo especifico, sin selector configurable.
Nota historica de esta ronda (queda documentada por trazabilidad, ya no es
relevante para la conclusion final): se habia intentado decompilar
`spirit::math::gas_viscosity_2004::from_standard_composition` (Ghidra
11.4.3, ver `apk_analisis/ghidra_gasviscosity2004_output.txt` linea ~137)
para resolverlo por ingenieria inversa; el patron de lectura de esa funcion
no calzaba de forma inequivoca con el orden asumido y no se forzo una
conclusion en su momento -- el manual oficial hizo innecesario continuar
ese camino.

[CERTAIN, verificado numericamente en esta ronda] Lo que SI se pudo
descartar es que esto tenga relevancia practica: se corrio
`calcular_viscosidad()` de este mismo archivo para los 3 casos reales ya
validados (T=0/rho=0, T=20/rho=0, T=20/rho=80) en 3 variantes -- neo-Pentano
ignorado (implementacion actual), sumado a iC5, sumado a nC5 -- y las 3
variantes difieren entre si en el orden de 1e-9 Pa.s absoluto (~0.01%
relativo), invisibles en el redondeo a 6 decimales que muestra la app y muy
por debajo del umbral <0.1% que exige este proyecto. Es decir: sea cual sea
el tratamiento real que el motor le da a neo-Pentano (descartarlo o
plegarlo), el efecto sobre el resultado ya validado es nulo en la practica.
(Nota Ronda 6: el manual oficial confirmo que el tratamiento real es
"plegarlo en i-Pentano" -- ver seccion "REDUCCION OFICIAL 22 A 12
COMPONENTES" -- pero esta medicion numerica de Ronda 4 ya demostraba que la
eleccion no importaba, sea cual fuera la respuesta oficial.)

===============================================================================
UNIDADES DE ENTRADA EN LA UI REAL (RONDA 5, 2026-08-19)
===============================================================================
[CERTAIN] Se confirmo, tocando los 2 campos reales en la app Android (Gas >
Viscosity > "Natural gas dynamic viscosity", `uiautomator dump` sobre el
dialogo de edicion de cada campo, emulador `flowxpert_rd`), que TANTO
`density` COMO `temperature` tienen un selector de unidad real (mismo patron
ya documentado para la presion de referencia de ISO 6976): el selector SOLO
convierte el valor mostrado/ingresado, el motor interno sigue calculando
siempre en la unidad base (kg/m3 y grados Celsius, la que usa
`calcular_viscosidad()` en este archivo).

Opciones REALES de `density` (lista completa del dialogo, no inferida):
  - kg/m3   (default)
  - g/cc    ("gram per cubic centimeter")
  - lb/ft3

Opciones REALES de `temperature` (lista completa del dialogo, no inferida):
  - K
  - °C  (default, subtitulo "degree celsius", ya confirmado en Ronda 2)
  - °F
  - R   (Rankine)

Evidencia de que el cambio de unidad es SOLO de entrada/visualizacion (no
afecta el calculo real): se tomo el Caso 3 ya validado (T=20 degC, rho=80
kg/m3, composicion Default) y se cambio la unidad de cada campo, verificando
que (a) el VALOR mostrado se recalcula al equivalente fisico exacto y (b) el
resultado final de viscosidad en pantalla NO cambia:
  - density: 80 kg/m3 -> selector "g/cc" -> muestra "0.08" (rango tambien
    convertido de "0..2000" a "0..2") -> OK -> viscosidad sigue en
    0.000014 Pa.s.
  - density: 0.08 g/cc -> selector "lb/ft3" -> muestra "4.9942368" -> OK ->
    viscosidad sigue en 0.000014 Pa.s.
  - temperature: 20 degC -> selector "°F" -> muestra "68" (exacto) -> OK,
    con density SIMULTANEAMENTE en lb/ft3 (ambos campos en unidad no base a
    la vez) -> viscosidad sigue en 0.000014 Pa.s.
  - Se revirtieron ambos campos a kg/m3 / degC al cerrar la prueba (density
    quedo en "79.9999992" por acumulacion de redondeo del doble round-trip
    kg/m3->g/cc->lb/ft3->kg/m3, diferencia de 8e-7, sin efecto en el
    resultado mostrado).

Factores de conversion hacia la unidad base usados en `interfaz_calculo_
flujo.py` (`GASVISC2004_DENSIDAD_A_KGM3`, `GASVISC2004_TEMPERATURA_A_DEGC`):
  density:      g/cc -> kg/m3: *1000.0
                lb/ft3 -> kg/m3: *16.018463373960138 (misma constante
                _LBFT3_A_KGM3 exacta ya usada en el resto de la interfaz,
                de 1 lb=0.45359237 kg y 1 ft=0.3048 m, ambos exactos)
  temperature:  K -> degC: -273.15
                degF -> degC: (v-32)/1.8
                R -> degC: v*(5/9) - 273.15

[CERTAIN] La interfaz (`interfaz_calculo_flujo.py`, pestaña "GasViscosity_
2004") YA fue actualizada para reflejar este selector real: cada uno de los
2 campos (Density, Temperature) tiene ahora un Combobox de unidad al lado
del Entry, con conversion hacia la unidad base ANTES de llamar a
`calcular_viscosidad()` -- mismo patron de estilo ya usado para el campo de
presion de referencia de ISO 6976 (`ISO6976_PRESION_A_PA`). Verificado con
los 3 casos reales ya conocidos (T=0/rho=0, T=20/rho=0, T=20/rho=80): dan el
mismo resultado que antes del cambio, y probar con unidades no base (lb/ft3,
degF, g/cc, K) para el Caso 3 reproduce el mismo resultado exacto.

===============================================================================
REDUCCION OFICIAL 22 A 12 COMPONENTES (RONDA 6, 2026-08-19)
===============================================================================
[CERTAIN, fuente: manual oficial ABB SpiritIT, `Flow-X Manual IIIb -
Function Reference_CM_FlowX_FR-EN_E.pdf`, pagina 83, funcion
`fxGasViscosity_2004`] El manual documenta de forma EXPLICITA la tabla
completa de como se reducen los 22 componentes estandar de FlowXpert a los
12 que usa el motor real de Schley et al. Esta tabla reemplaza, con fuente
documental oficial, todo lo que en rondas anteriores era [LIKELY]/[GUESSING]
por ingenieria inversa sobre que pasaba con los 10 componentes sin fila
propia:

    Methane          -> Methane
    Nitrogen         -> Nitrogen
    Carbon Dioxide   -> Carbon Dioxide
    Ethane           -> Ethane
    Propane          -> Propane
    Water            -> DESCARTADO (no soportado por la publicacion)
    Hydrogen Sulphide-> DESCARTADO
    Hydrogen         -> Methane
    Carbon Monoxide  -> DESCARTADO
    Oxygen           -> Nitrogen
    i-Butane         -> i-Butane
    n-Butane         -> n-Butane
    i-Pentane        -> i-Pentane
    n-Pentane        -> n-Pentane
    n-Hexane         -> n-Hexane
    n-Heptane        -> n-Heptane
    n-Octane         -> n-Octane
    n-Nonane         -> n-Octane
    n-Decane         -> n-Octane
    Helium           -> Nitrogen
    Argon            -> Nitrogen
    Neo-Pentane      -> i-Pentane

Es decir: SOLO 3 de los 22 componentes se descartan por completo (Agua,
H2S, CO, "no soportados por la publicacion"); los otros 7 sin fila propia
(Hidrogeno, Oxigeno, Helio, Argon, n-Nonano, n-Decano, neo-Pentano) SI
participan del calculo, redistribuidos hacia el componente de los 12 mas
afin. La composicion resultante (ya con los 22 repartidos en los 12) se
normaliza a 1 antes de calcular -- esto es exactamente lo que ya hacia
`normalizar()` en este archivo, sin cambios.

[CERTAIN, misma fuente] RANGO DE VALIDEZ FISICA OFICIAL del metodo
publicado (distinto de los rangos genericos de UI -200..400 degC / 0..2000
kg/m3 ya documentados arriba, que son limites de entrada, no de validez):
temperatura 250 K a 450 K (-23.15 a +176.85 degC, redondeado en el manual a
"-24 a +177 degC"), presion hasta 30 MPa (300 bar). INCERTIDUMBRE estimada
declarada por el manual: 0.5% para gas natural tipico, 0.3% para metano
puro.

[CERTAIN] Implementado en `reducir_22_a_12()` (mas abajo en este archivo) y
en `calcular_viscosidad_desde_22()`, que envuelve `reducir_22_a_12()` +
`calcular_viscosidad()` para aceptar directamente la composicion completa
de 22 componentes (mismos nombres que `ORDEN_COMPONENTES_APP` de
`normas/AGA_8.py`/`normas/ISO_6976.py`).

[CERTAIN, verificado en esta ronda] Los 3 casos reales ya validados en
Ronda 2 (T=0/rho=0, T=20/rho=0, T=20/rho=80, composicion "Default" con
Helio=0.046% y neo-Pentano=0.008% incluidos ahora via la reduccion oficial
en vez de ignorados) se re-corrieron con `calcular_viscosidad_desde_22()` y
siguen dando el MISMO resultado redondeado a 6 decimales que la app
(0.000011 / 0.000012 / 0.000014 Pa.s) -- la diferencia entre "ignorar
Helio/neo-Pentano" (comportamiento viejo) y "plegarlos oficialmente en
Nitrogeno/i-Pentano" (comportamiento nuevo, correcto) es del orden de 1e-9
Pa.s absoluto (~0.01% relativo), consistente con lo ya medido en Ronda 4
para neo-Pentano solo, y por debajo del umbral <0.1% y de la resolucion de
pantalla (6 decimales) de este proyecto. Ver autotest al final de este
archivo (`if __name__ == "__main__":`).

===============================================================================
FASE 7 -- VALIDACION CONTRA CROMATOGRAFO REAL: EVALUADA, NO APLICA
===============================================================================
[CERTAIN] Se inspecciono `normas/_cache_cromatografo.json` (13408 registros
reales de cromatografo). Cada registro tiene fecha/hora/medidor + fracciones
molares (incluyendo "C6+" agrupado, mismo patron ya documentado para ISO
6976) pero NINGUN campo de temperatura o densidad/presion de proceso. Como
`GasViscosity_2004` requiere `density` y `temperature` como inputs
obligatorios (no solo composicion), no hay forma de construir un caso de
Fase 7 con estos datos sin INVENTAR un valor de T/rho de proceso -- eso
violaria la regla de oro del proyecto de no fabricar validaciones. Se
documenta como pendiente estructural (no como tarea incompleta): Fase 7 NO
aplica a esta norma con los datos de campo disponibles actualmente en el
proyecto, a menos que en el futuro se consiga un registro con T/P de proceso
real asociado a una composicion de cromatografo.

===============================================================================
PENDIENTES (fuera de alcance de esta ronda)
===============================================================================
- Fase 6: CERRADA en Ronda 3 (2026-08-18) -- nucleo aritmetico completo del
  `.xll` decompilado y comparado constante a constante contra el `.so`, sin
  discrepancias. Ver seccion "CONFIRMACION CRUZADA COMPLETA (.xll vs .so)"
  arriba.
- No se verificaron letra por letra los coeficientes D/A/B/C por componente
  ni a1..a4 contra el PDF original de Schley et al. (2004) (no disponible en
  `documentos_normativos/` de este proyecto). La Fase 6 SI confirmo que
  ambos binarios (`.xll` y `.so`, compilados por separado) usan exactamente
  los mismos valores -- evidencia indirecta fuerte de que no hay error de
  transcripcion de una sola ronda de Ghidra, pero esto sigue sin reemplazar
  tener el PDF original para una verificacion 100% contra la fuente
  publicada.
- El campo "C5" (0.008%) visto en la composicion Default de la app Android:
  CERRADO en Ronda 4 (2026-08-19) -- es neo-Pentano, identificado por
  etiqueta de UI + match exacto de valor (0.008%) y de "He" (0.046%) contra
  la misma composicion Default ya documentada en `normas/ISO_6976.py`, y
  confirmado por suma de control a 100.000% exacto. CIERRE TOTAL en Ronda 6
  (2026-08-19): ya no queda [GUESSING] nada -- el manual oficial ABB
  SpiritIT confirma que neo-Pentano se pliega SIEMPRE en i-Pentano (ver
  seccion "REDUCCION OFICIAL 22 A 12 COMPONENTES" arriba), sin selector
  configurable. HILO CERRADO POR COMPLETO, sin pendientes activos.
- Mapeo completo de los 22 componentes estandar a los 12 del motor (que
  hacer con Agua/H2S/H2/CO/O2/He/Ar/n-Nonano/n-Decano): CERRADO en Ronda 6
  (2026-08-19) por fuente documental oficial (manual ABB SpiritIT, pagina
  83). Ver seccion "REDUCCION OFICIAL 22 A 12 COMPONENTES" arriba.
- Rango de validez fisica real (250-450 K, hasta 30 MPa) e incertidumbre
  declarada (0.5%/0.3%): CERRADO en Ronda 6 (2026-08-19), misma fuente
  oficial.

REGLA DE ORO DEL PROYECTO: no se fabrico ni fuerza ningun cierre. Todo lo
marcado [CERTAIN] proviene de bytes reales leidos de memoria del binario via
Ghidra (no de memoria entrenada); todo lo marcado [LIKELY]/[GUESSING] esta
declarado como tal explicitamente arriba.
"""

import math

# -----------------------------------------------------------------------------
# Tabla de 12 componentes (orden interno de FlowXpert para este calculo, NO el
# orden completo AGA8 de 22 componentes del array de entrada -- ver mapeo mas
# abajo). Fuente: bytes reales de apk_analisis/libFXLibrary.so
# (ghidra_gasviscosity2004_consts_output.txt), CONFIRMADA byte a byte contra
# FlowXpert.xll en Fase 6 / Ronda 3 (ghidra_gasviscosity2004_xll_consts_output.txt).
# -----------------------------------------------------------------------------
COMPONENTES = [
    "metano", "nitrogeno", "co2", "etano", "propano", "n_butano",
    "i_butano", "n_pentano", "i_pentano", "n_hexano", "n_heptano", "n_octano",
]

# Indices del array AGA8 de 22 componentes (orden estandar de este proyecto,
# ver normas/AGA_8.py) que corresponden a cada uno de los 12 usados aqui.
# [LIKELY] mapeo por nombre/orden de Tc, no confirmado con un caso real que
# use composicion con trazas para verificar el indexado exacto.
INDICES_AGA8 = {
    "metano": 0, "nitrogeno": 1, "co2": 2, "etano": 3, "propano": 4,
    "n_butano": 5, "i_butano": 6, "n_pentano": 7, "i_pentano": 8,
    "n_hexano": 9, "n_heptano": 10, "n_octano": 11,
}

M = {   # g/mol
    "metano": 16.043, "nitrogeno": 28.0135, "co2": 44.01, "etano": 30.07,
    "propano": 44.097, "n_butano": 58.123, "i_butano": 58.123,
    "n_pentano": 72.15, "i_pentano": 72.15, "n_hexano": 86.177,
    "n_heptano": 100.204, "n_octano": 114.231,
}
TC = {  # K
    "metano": 190.564, "nitrogeno": 126.192, "co2": 304.1282,
    "etano": 305.322, "propano": 369.825, "n_butano": 425.125,
    "i_butano": 407.817, "n_pentano": 469.7, "i_pentano": 460.35,
    "n_hexano": 507.82, "n_heptano": 540.13, "n_octano": 569.32,
}
VC = {  # cm3/mol
    "metano": 98.63, "nitrogeno": 89.41, "co2": 94.12, "etano": 145.55,
    "propano": 200.0, "n_butano": 255.1, "i_butano": 259.06,
    "n_pentano": 310.99, "i_pentano": 305.72, "n_hexano": 369.57,
    "n_heptano": 431.91, "n_octano": 486.3,
}
PC = {  # MPa
    "metano": 4.599, "nitrogeno": 3.396, "co2": 7.377, "etano": 4.872,
    "propano": 4.248, "n_butano": 3.796, "i_butano": 3.64,
    "n_pentano": 3.37, "i_pentano": 3.396, "n_hexano": 3.034,
    "n_heptano": 2.736, "n_octano": 2.497,
}
# D, A, B, C: coeficientes del polinomio de viscosidad de gas diluido puro
DABC = {
    "metano":    (10.257, 3.230, -1.613, 0.000),
    "nitrogeno": (16.627, 2.848, -1.940, 1.372),
    "co2":       (13.717, 3.539, -1.007, -0.443),
    "etano":     (8.487, 3.607, -1.319, 0.000),
    "propano":   (7.461, 3.669, -1.052, 0.000),
    "n_butano":  (6.814, 3.613, -0.494, 0.000),
    "i_butano":  (6.914, 3.515, -0.682, 0.000),
    "n_pentano": (6.196, 3.759, -0.698, 0.000),
    "i_pentano": (6.384, 3.531, -0.376, 0.000),
    "n_hexano":  (5.735, 3.731, -0.479, 0.000),
    "n_heptano": (5.335, 3.732, -0.277, 0.000),
    "n_octano":  (5.095, 3.854, -0.014, 0.000),
}

R = 8.3144621  # J/(mol.K) -- valor real leido del binario (DAT_0023a010)
XI_K = 0.38009  # constante de escala del grupo xi (DAT_0023a028)
A_RESIDUAL = (0.23961032, 0.57790957, -0.24327596, 0.12776597)


def _zc(comp):
    return PC[comp] * VC[comp] / (R * TC[comp])


def normalizar(x):
    """x: dict componente->fraccion molar (de los 12 usados). Devuelve dict
    normalizado a suma 1 (replica normalize_composition())."""
    s = sum(x.values())
    return {k: v / s for k, v in x.items()}


def viscosidad_gas_diluido_componente(comp, t):
    """eta0_i(t) en microPa.s. t: temperatura en el mismo valor crudo que
    recibe do_calculation (ver nota [LIKELY] de unidades en el docstring)."""
    D, A, B, C = DABC[comp]
    return D * (1.0 + 0.001 * A * t + 1e-6 * B * t * t + 1e-9 * C * t ** 3)


def _phi_ij(i, j, t):
    """Formula de Wilke (1950), confirmada termino a termino contra el
    binario."""
    eta_i = viscosidad_gas_diluido_componente(i, t)
    eta_j = viscosidad_gas_diluido_componente(j, t)
    mij = (M[j] / M[i]) ** 0.25
    num = (1.0 + math.sqrt(eta_i / eta_j) * mij) ** 2
    den = math.sqrt(8.0 * (1.0 + M[i] / M[j]))
    return num / den


def viscosidad_limite_densidad_cero(x, t):
    """eta0_mix en microPa.s -- mezcla de Wilke de las viscosidades de gas
    diluido puras."""
    total = 0.0
    for i in COMPONENTES:
        xi = x.get(i, 0.0)
        if xi == 0.0:
            continue
        eta_i = viscosidad_gas_diluido_componente(i, t)
        denom = sum(x.get(j, 0.0) * _phi_ij(i, j, t) for j in COMPONENTES)
        total += xi * eta_i / denom
    return total


def masa_molar_mezcla(x):
    return sum(x.get(c, 0.0) * M[c] for c in COMPONENTES)


def tc_mezcla(x):
    return sum(x.get(c, 0.0) * TC[c] for c in COMPONENTES)


def vc_mezcla(x):
    return sum(x.get(c, 0.0) * VC[c] for c in COMPONENTES)


def zc_mezcla(x):
    return sum(x.get(c, 0.0) * _zc(c) for c in COMPONENTES)


def pc_mezcla(x):
    """MPa."""
    return zc_mezcla(x) * R * tc_mezcla(x) / vc_mezcla(x)


def rho_c_mezcla(x):
    """kg/m3."""
    return masa_molar_mezcla(x) * 1000.0 / vc_mezcla(x)


def factor_viscosidad_residual(x):
    """xi_mix, grupo de Jossi-Stiel-Thodos con la constante de escala real
    del binario (0.38009)."""
    mm = masa_molar_mezcla(x)
    pcm = pc_mezcla(x)
    tcm = tc_mezcla(x)
    return math.sqrt(mm) * pcm ** (2.0 / 3.0) / (tcm ** (1.0 / 6.0) * XI_K)


def viscosidad_residual(x, rho):
    """eta_r en microPa.s. rho: densidad real de la mezcla [kg/m3]."""
    rho_r = rho / rho_c_mezcla(x)
    xi = factor_viscosidad_residual(x)
    poly = sum(a * rho_r ** (n + 1) for n, a in enumerate(A_RESIDUAL))
    return xi * poly


def calcular_viscosidad(composicion_12, temperatura, densidad):
    """Replica do_calculation(). composicion_12: dict con las 12 claves de
    COMPONENTES (fracciones molares, se normalizan internamente).
    temperatura: mismo valor crudo que recibe FlowXpert (ver nota [LIKELY] de
    unidades). densidad: kg/m3. Devuelve viscosidad dinamica en Pa.s."""
    x = normalizar(composicion_12)
    eta0 = viscosidad_limite_densidad_cero(x, temperatura)
    eta_r = viscosidad_residual(x, densidad)
    return (eta0 + eta_r) * 1e-6


# -----------------------------------------------------------------------------
# Reduccion oficial de los 22 componentes estandar de FlowXpert a los 12 de
# este motor. [CERTAIN, fuente: manual oficial ABB SpiritIT, "Flow-X Manual
# IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf", pagina 83, funcion
# fxGasViscosity_2004] -- ver seccion "REDUCCION OFICIAL 22 A 12 COMPONENTES"
# del docstring arriba para la tabla completa y el detalle de la fuente. Las
# claves de entrada son los 22 nombres de `ORDEN_COMPONENTES_APP` (ver
# normas/AGA_8.py / normas/ISO_6976.py).
# -----------------------------------------------------------------------------
MAPEO_22_A_12 = {
    "Metano": "metano",
    "Nitrogeno": "nitrogeno",
    "CO2": "co2",
    "Etano": "etano",
    "Propano": "propano",
    # "Agua": DESCARTADO -- no soportado por la publicacion.
    # "H2S": DESCARTADO -- no soportado por la publicacion.
    "Hidrogeno": "metano",
    # "CO": DESCARTADO -- no soportado por la publicacion.
    "Oxigeno": "nitrogeno",
    "i-Butano": "i_butano",
    "n-Butano": "n_butano",
    "i-Pentano": "i_pentano",
    "n-Pentano": "n_pentano",
    "n-Hexano": "n_hexano",
    "n-Heptano": "n_heptano",
    "n-Octano": "n_octano",
    "n-Nonano": "n_octano",
    "n-Decano": "n_octano",
    "Helio": "nitrogeno",
    "Argon": "nitrogeno",
    "neo-Pentano": "i_pentano",
}

# Los 3 componentes de los 22 que la publicacion no soporta (ver tabla
# oficial arriba) -- se descartan por completo, no se redistribuyen.
COMPONENTES_DESCARTADOS_22 = ("Agua", "H2S", "CO")


def reducir_22_a_12(composicion_22: dict) -> dict:
    """Reparte una composicion de 22 componentes estandar (nombres de
    `ORDEN_COMPONENTES_APP`, fracciones molares o porcentajes -- la escala no
    importa porque `normalizar()`/`calcular_viscosidad()` normalizan a suma 1
    despues) en los 12 componentes que usa el motor real de Schley et al.,
    segun la tabla OFICIAL del manual ABB SpiritIT (ver `MAPEO_22_A_12` y el
    docstring, seccion "REDUCCION OFICIAL 22 A 12 COMPONENTES").

    NO normaliza el resultado -- eso lo sigue haciendo `normalizar()`
    (llamada internamente por `calcular_viscosidad()`), sin cambios respecto
    a antes de esta funcion.

    Los 3 componentes sin destino (Agua, H2S, CO) se descartan silenciosamente
    (no soportados por la publicacion, [CERTAIN] por la misma fuente
    oficial). Cualquier nombre en `composicion_22` que no sea ninguno de los
    22 estandar tambien se ignora (defensivo; no deberia ocurrir si se usa
    `ORDEN_COMPONENTES_APP` como fuente de claves)."""
    resultado_12 = {c: 0.0 for c in COMPONENTES}
    for nombre_22, valor in composicion_22.items():
        if not valor:
            continue
        destino_12 = MAPEO_22_A_12.get(nombre_22)
        if destino_12 is None:
            continue  # Agua/H2S/CO (descartados) o nombre desconocido.
        resultado_12[destino_12] += valor
    return resultado_12


def calcular_viscosidad_desde_22(composicion_22: dict, temperatura, densidad):
    """Version de `calcular_viscosidad()` que acepta la composicion COMPLETA
    de 22 componentes estandar de FlowXpert (nombres de
    `ORDEN_COMPONENTES_APP`) en vez de los 12 internos de este motor --
    aplica `reducir_22_a_12()` (tabla oficial) y despues normaliza y calcula
    exactamente igual que `calcular_viscosidad()`. temperatura/densidad:
    mismas unidades y convenciones que `calcular_viscosidad()`."""
    composicion_12 = reducir_22_a_12(composicion_22)
    return calcular_viscosidad(composicion_12, temperatura, densidad)


if __name__ == "__main__":
    # Ejemplo ilustrativo (NO es un caso real validado -- ver PENDIENTES).
    gas_natural_tipico = {
        "metano": 0.90, "nitrogeno": 0.01, "co2": 0.01, "etano": 0.05,
        "propano": 0.02, "n_butano": 0.005, "i_butano": 0.005,
    }
    t_ejemplo = 20.0     # grados (unidad no confirmada con caso real)
    rho_ejemplo = 0.75   # kg/m3 (gas a baja presion, valor ilustrativo)
    eta = calcular_viscosidad(gas_natural_tipico, t_ejemplo, rho_ejemplo)
    print(f"Viscosidad (ejemplo ilustrativo, NO validado): {eta:.6e} Pa.s "
          f"({eta * 1e6:.4f} microPa.s)")

    # ---------------------------------------------------------------------
    # Autotest Ronda 6 (2026-08-19): los 3 casos reales ya validados en
    # Ronda 2, ahora corridos con la composicion COMPLETA de 22 componentes
    # (incluyendo Helio y neo-Pentano, que la reduccion oficial pliega en
    # Nitrogeno e i-Pentano respectivamente) via calcular_viscosidad_desde_22
    # + reducir_22_a_12, en vez de con el dict de 12 que los ignoraba.
    # ---------------------------------------------------------------------
    composicion_22_default = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "Agua": 0.0, "H2S": 0.0, "Hidrogeno": 0.0, "CO": 0.0,
        "Oxigeno": 0.0, "i-Butano": 0.06, "n-Butano": 0.072,
        "i-Pentano": 0.018, "n-Pentano": 0.033, "n-Hexano": 0.02,
        "n-Heptano": 0.013, "n-Octano": 0.005, "n-Nonano": 0.0,
        "n-Decano": 0.0, "Helio": 0.046, "Argon": 0.0, "neo-Pentano": 0.008,
    }
    casos = [
        ("Caso 1 (T=0 degC, rho=0)", 0.0, 0.0, 0.000011),
        ("Caso 2 (T=20 degC, rho=0)", 20.0, 0.0, 0.000012),
        ("Caso 3 (T=20 degC, rho=80)", 20.0, 80.0, 0.000014),
    ]
    print("\nAutotest Ronda 6 -- 3 casos reales via calcular_viscosidad_desde_22():")
    for nombre, t, rho, esperado_pantalla in casos:
        eta22 = calcular_viscosidad_desde_22(composicion_22_default, t, rho)
        redondeado = round(eta22, 6)
        ok = "OK" if redondeado == esperado_pantalla else "DIFERENTE"
        print(f"  {nombre}: {eta22:.10e} Pa.s -> redondeado {redondeado:.6f} "
              f"(app: {esperado_pantalla:.6f}) [{ok}]")
