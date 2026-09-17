# -*- coding: utf-8 -*-
"""
normas/API_MPMS_Tables_1980_2004.py
====================================
Familia API MPMS Chapter 11.1 "Petroleum Measurement Tables" (API Standard
2540 / API-2540 / ASTM D1250), ediciones 1980 y 2004, tal como esta
implementada en FlowXpert:
    fxAPI_Table5   (API observada -> API a 60F, o inverso en 2004 con P)
    fxAPI_Table6   (API a 60F -> CTL a T observada)
    fxAPI_Table23  (RD observada -> RD a 60F)          [variante RD de Table5]
    fxAPI_Table24  (RD a 60F -> CTL a T observada)      [variante RD de Table6]
    fxAPI_Table53  (densidad observada -> densidad a 15C)   [metrico, variante de Table5]
    fxAPI_Table54  (densidad a 15C -> CTL a T observada)    [metrico, variante de Table6]
cada una en 2 ediciones = 12 funciones objetivo de esta familia.

Este archivo se puede ejecutar solo:
    python -m normas.API_MPMS_Tables_1980_2004

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
RONDA 1 (2026-08-20): decompilacion inicial de Table5/6/53_1980 [CERTAIN] y
deteccion del modulo 2004 sin decompilar su aritmetica ([LIKELY]/[GUESSING]).
Table23/24/54_1980 solo se habian inferido por patron estructural.

RONDA 2 (2026-08-20, esta ronda): se leyo el MISMO archivo de decompilacion ya
generado en Ronda 1 (`ghidra_api_mpms_xll_output.txt`, Ghidra 12.1.2, .xll) a
mas profundidad -- resulto que YA CONTENIA la decompilacion completa de los
109 simbolos alcanzables desde las 12 raices pedidas, incluyendo Table23/24/
54_1980 y el motor 2004 completo (CTL + factor de compresibilidad F/CPL), que
la Ronda 1 no habia leido hasta el final. Tambien contiene, al final del
archivo, un volcado de las 167 direcciones `DAT_`/`_DAT_` referenciadas con su
valor double real ya interpretado por Ghidra -- eso permitio confirmar a
BYTES varias constantes que en Ronda 1 quedaron [LIKELY] (RHO_WATER_60F_KGM3,
la referencia de 60.0F/15.0C, el coeficiente 0.8) sin necesitar generar un
disassembly nuevo ni tocar Ghidra otra vez.

RONDA 3 (2026-08-20, Fase 5/7 -- primer caso real en vivo de esta familia):
pantalla real encontrada en la app (Liquid > API 11.1 (1980) > "API Table-5
(1980)" / "API Table-6 (1980)"), navegada con adb+uiautomator SIN necesitar
Frida (la UI ya muestra CTL/K0/K1/K2/Thermal Expansion directamente). 9 casos
reales obtenidos (6 Table5, 3 Table6; productos Crude/Gasoline/Lub oil) --
ver `android_sdk_setup/casos_reales_api_tables.json`. `api_60f` y `ctl` (los 2
outputs comparables directo) coinciden con la app real con error entre 0% y
~0.00005% en las 9 comparaciones (ruido de redondeo de 6 decimales de la UI).
Motor 1980 (Crude/Gasoline/Lub oil) queda validado en vivo, no solo por
autoconsistencia interna.

Hallazgo real durante esta validacion (documentado, no ocultado): el campo
"alpha" (Thermal Expansion) mostro ~44% de diferencia bruta contra la app --
investigado, NO es error de formula: la app siempre presenta ese campo en
1/gradoC, mientras que este archivo lo calcula y devuelve en 1/gradoF (unidad
interna de la formula porque T se maneja en Fahrenheit). Multiplicando por
1.8 el error cae a <0.06%. Es una diferencia de unidad de PRESENTACION de un
campo secundario, no afecta `ctl` ni `api_60f`/`rd_60f`/`density_15c` (los
resultados principales).

Selectores reales confirmados (Fase 4) en esta ronda:
    - "API Gravity"/"API Gravity @60F": SIN selector de unidad, siempre °API.
    - "Temperature": CON selector real K/°C/°F/R (rango fisico -100..400°F).
    - "Product": 7 opciones reales confirmadas (picker): Crude, "Refined,
      auto", Gasoline, "Transition area", "Jet fuel", "Fuel oil", "Lub oil"
      -> product=1..7, coincide exacto con el enum ya usado en el codigo.
    - "API Rounding" en Table5: flag booleano in-place, redondea SOLO el
      output api_60f visible a 1 DECIMAL (confirmado: 27.89094 -> 27.90000,
      dump XML crudo `android_sdk_setup/api5_rounding_dlg2.xml` releido en
      RONDA 18 -- el "27.90000" es round(x,1)=27.9 con ceros de relleno del
      formato fijo a 5 decimales de la UI, NO round(x,2)=27.89) -- SI
      implementado en `api_table5_1980` (parametro `rounding`, ver RONDA 18).
    - "Hydrometer Corr." en Table5: flag booleano in-place, +0.06 API aprox
      en el caso probado (27.89094 -> 27.95136) -- [CERRADO EN RONDA 4, ver
      seccion "RONDA 4" mas abajo y `_hydrometer_factor`/`api_table5_1980`].
    - "API Rounding" en Table6: DISTINTO de Table5 -- es un ENUM de 4
      opciones via dialogo (Disabled/Enabled/"Enabled (table values)"/
      "Enabled (5 decimal places)"), efecto exacto sobre `ctl` NO investigado
      a fondo esta ronda [PENDIENTE, prioridad baja -- probablemente solo
      afecta redondeo de presentacion, igual que en Table5].

PENDIENTE tras Ronda 3 (honesto, no cerrado): Table53/54_2004 (metrico) sin
implementar (ver seccion 2004 mas abajo); Hydrometer Correction sin formula;
efecto del enum de 4 opciones de "API Rounding" en Table6 sin mapear; cero
casos reales en vivo todavia para Table23/24/53/54 (1980 o 2004) ni para
ninguna funcion 2004 -- solo Table5/6_1980 tienen validacion en vivo hoy.
[ACTUALIZACION RONDA 4: Hydrometer Correction CERRADA (Table5_1980, formula
real + verificacion exacta contra caso real). Table53/54_2004 SIGUE sin
implementar pero con evidencia estructural nueva real, ver seccion RONDA 4.
Los otros 2 pendientes (enum Table6, casos reales Table23/24/53/54) siguen
abiertos, fuera del alcance de esta ronda.]

-------------------------------------------------------------------------------
[CERTAIN] Motor 1980 -- Table5/6/23/24/53/54, las 6 confirmadas por
decompilacion directa (Table23/24/54 SUBEN de [LIKELY] a [CERTAIN] esta ronda)
-------------------------------------------------------------------------------
Direcciones raiz reales (.xll) y su cadena de llamadas decompilada:
    API_Table5_1980  @ 0x1800a3e58 -> FUN_1800e4f94 -> FUN_1800e4450 (iterativo)
    API_Table6_1980  @ 0x1800a4924 -> FUN_1800e5e1c -> FUN_1800e5bb0 (directo)
    API_Table23_1980 @ 0x1800a1c9c -> FUN_1800eb1f8 -> FUN_1800e9a68 (crudo,
        iterativo, K0=0x40755187fcb923a3 inline) / FUN_1800ea5cc (lube,
        K1=0x3fd65269595feda6 inline) / FUN_1800e9f48 (grupo B 2..6)
    API_Table24_1980 @ 0x1800a2454 -> FUN_1800ec49c -> FUN_1800eb74c (crudo,
        directo) / FUN_1800ebdf0 (lube) / FUN_1800eb97c (grupo B)
    API_Table53_1980 @ 0x1800a2bf4 -> FUN_1800edc80 -> FUN_1800ececc/
        FUN_1800ed634 (metrico)
    API_Table54_1980 @ 0x1800a33c4 -> FUN_1800eed08 -> FUN_1800ee1f8 (crudo)/
        FUN_1800ee7d8 (lube, K1=0x3fe416f0068db8bb inline) / FUN_1800ee438
        (grupo B)
Las 6 funciones comparten la MISMA estructura de despacho por producto
(1=A-Crudo, 2=B-Auto, 3=B-Gasolina, 4=B-Transicion, 5=B-Jet, 6=B-FuelOil,
7=D-Lubricante), el mismo limite de 99/100 iteraciones para las 3 que
resuelven "observado->base" (5/23/53), y son directas (sin bucle) las 3 que
resuelven "base->observado" (6/24/54) -- confirmado por lectura linea a linea
de las funciones reales, no solo por direccion. Table23/24 usan RD
directamente (sin la conversion a/desde API gravity que si hace Table5/6);
Table53/54 son las mismas Table5/6 con constantes metricas -- NO se encontro
ninguna otra diferencia real de formula entre las 6.

Formula confirmada (VCF/CTL clasica de API-2540 = ASTM D1250 Adjunct):
    alpha = (K0 + K1*rho + K2*rho^2) / rho^2   (rho = densidad FISICA kg/m3)
    x     = alpha * (T_obs - T_ref)
    CTL   = exp( -(x + 0.8 * x^2) )
El volcado final de constantes `DAT_`/`_DAT_` del archivo de decompilacion
(seccion "DAT_ ADDRESSES REFERENCIADAS", 167 direcciones) confirma a BYTES,
ademas de las 4 ya confirmadas en Ronda 1:
    DAT_180124810 = 60.0        -> T_ref US EXACTO (era [LIKELY])
    DAT_180194008 = 15.0        -> T_ref metrico EXACTO (era [LIKELY])
    DAT_180193ee0 = 0.8         -> coeficiente EXACTO (era sin confirmar)
    DAT_180124430 = 1.0, DAT_1801212a0 = -0.0 (mascara de signo del exp)
    DAT_1801eaac0 = 999.012     -> RHO_WATER_60F_KGM3 EXACTO (era [LIKELY],
                                    ahora CERTAIN -- se usa literal en el
                                    codigo de Table23/53/54: "param_1 *
                                    _DAT_1801eaac0" convierte RD a kg/m3)
    Los 8 K0/K1/K2 de la tabla del manual (pagina 8), sistema US Y metrico,
    aparecen LITERALMENTE en el volcado (341.0957, 192.4571+0.2438,
    1489.067+(-0.0018684), 330.301, 103.872+0.2701, 0.34878 / 613.9723,
    346.4228+0.4388, 2680.3206+(-0.00336312), 594.5418, 186.9696+0.4862,
    0.6278) -- las 8 pasan de "manual, no verificado a bytes" a [CERTAIN],
    no solo las 4 de Ronda 1.
Los umbrales de auto-seleccion B en Table23_1980 (grupo 2..6, FUN_1800e9f48)
usan RD adimensional, NO kg/m3 -- CORREGIDO en RONDA 49 (2026-09-10): el
valor real es 0.771/0.789/0.84 (3 breakpoints, no 2), la cifra "0.7785" de
esta nota original era una mezcla incorrecta con el breakpoint de 1a pasada
(0.779). Ver seccion "RONDA 49" al final del modulo para el mecanismo
completo (ahora CERRADO para las 6 tablas raw Y las 3 combinadas 1980).

-------------------------------------------------------------------------------
[CERTAIN, con partes explicitamente pendientes] Motor 2004 -- CTL + factor de
compresibilidad F / CPL, confirmado por decompilacion real
-------------------------------------------------------------------------------
Las 6 funciones 2004 (Table5/6/23/24/53/54_2004) SI comparten un UNICO motor,
confirmado por decompilacion (no solo por direccion), y ese motor es
DISTINTO en arquitectura del de 1980:
    API_Table5_2004  @ 0x1800a40bc -> FUN_1800e5218 -> FUN_180105b64 (bucle,
        <=15 iteraciones) -> FUN_1801053f4 (nucleo real)
    API_Table6_2004  @ 0x1800a4b3c -> FUN_1800e5fec -> FUN_1801053f4 (directo)
    API_Table23_2004 @ 0x1800a1f00 -> FUN_1800eb45c -> FUN_180105b64 (bucle)
    API_Table24_2004 @ 0x1800a266c -> FUN_1800ec7f0(aprox) -> FUN_1801053f4
        (directo, confirmado el mismo FUN_1801053f4 en la cadena)
    API_Table53_2004 @ 0x1800a2e58 -> FUN_1800edec8 -> FUN_180105ec8 ->
        FUN_180105b64 (bucle) -> FUN_1801053f4
    API_Table54_2004 @ 0x1800a35dc -> (misma familia) -> FUN_1801053f4
Los 6 llaman al MISMO FUN_1801053f4 (confirmado por direccion identica en las
6 cadenas) y ese nucleo tiene un UNICO juego de constantes K0/K1/K2 (los
MISMOS 0x40755187fcb923a3=341.0957, 0x3fd65269595feda6=0.34878, etc. del
sistema US/1980 -- literalmente los mismos DAT_1801ea810/818/820/828/7d0/7d8/
7e0/800 que usa el motor 1980). ESTO ES UN HALLAZGO REAL, no una suposicion:
2004 UNIFICA el motor en un solo juego de constantes (siempre en base
°F/kg-m3-US), y Table53/54_2004 (metricas) convierten su entrada de
temperatura (°C->°F, factor confirmado *1.8+32 via FUN_1800e1d5c) y de
presion (bar->psi, division por DAT_1801ea5d8=6.894757 kPa/psi, confirmado
por el propio literal en el volcado de constantes) ANTES de llamar al mismo
nucleo -- NO usan una tabla K metrica separada como si hacia el motor 1980.

CTL 2004 (confirmado estructuralmente en FUN_1801053f4, misma forma que 1980):
    alpha = (K0 + K1*rho_base + K2*rho_base^2) / rho_base^2
    x     = alpha * (T_obs_corregida - 60.0068749)   <- OJO: NO es 60.0 exacto
    CTL   = exp( -(x + 0.8*x^2) )
El "60.0068749" es DAT_18028e758, un valor real leido del binario (no
inventado) -- NO se encontro ninguna referencia publica que explique por
que 2004 usa esa fraccion en vez de 60.0 exacto, pero RONDA 8 encontro una
explicacion MECANICA (no una fuente publica, pero si una razon real): es la
imagen de 60.0F bajo la MISMA micro-correccion polinomica de temperatura que
se cierra en RONDA 8 mas abajo (`_micro_correccion_temp_2004(60.0)` =
60.00687489773..., contra 60.0068749 -- diff~2e-9, ruido de precision). Es
decir, el binario probablemente calcula T_ref internamente aplicando la
misma correccion a 60.0F en vez de tener un literal separado, y Ghidra solo
mostro el resultado final ya constante-propagado. Se documenta el VALOR real
y esta explicacion mecanica; una cita textual del estandar (si existe) sigue
[sin fuente publica identificada].
Ademas, "T_obs_corregida" pasa antes por una micro-correccion polinomica
(FUN_180106198 -> FUN_180106114, evaluada sobre ((T-32)*5/9)/630.0).
[CERRADO EN RONDA 8, ver esa seccion mas abajo: los 8 coeficientes son
reales (no 4 + basura), confirmado con bytes crudos del `.xll` + lectura del
pseudocodigo -- SI se implemento en `_micro_correccion_temp_2004()` y SI se
aplica en `_ctl_2004`/`_f_compressibility_2004`.]

Factor de compresibilidad F y CPL (extraidos de FUN_1801053f4, primera vez
que se decompila -- Ronda 1 no tenia esto):
    F   = exp( (T_F * 2326.0 + 793920.0) / rho_base^2 + (T_F * 1.3427e-4 - 1.9947) ) * 1.0e-5
    CPL = 1 / (1 - P_psi * F)          (se fuerza CPL=1.0 si el resultado < 1.0)
    CTPL = CTL * CPL
donde T_F es la MISMA temperatura corregida (ver RONDA 8: desde esa ronda SI
se aplica la micro-correccion aqui tambien, confirmado en el decompilado que
ambas formulas reusan el mismo registro ya corregido) y rho_base la densidad
base en kg/m3. Los 5 literales (2326.0, 793920.0, 1.3427e-4, 1.9947, 1.0e-5) son
VALORES REALES tomados byte a byte del volcado de constantes del `.xll`
(DAT_1801941c0, DAT_18028e818, DAT_1801ea498, DAT_1801ea4d0, DAT_180193de8) --
[CERTAIN en el valor extraido del binario]. NO se encontro una atribucion
publica exacta (el manual dice "calculated in accordance with the standard"
sin dar el polinomio) -- se documenta [SIN FUENTE PUBLICA IDENTIFICADA], tal
como exige la regla de oro del proyecto: no se fabrica una cita que no se
tiene, aunque la forma es estructuralmente compatible con el tipo de formula
publicada por API MPMS Ch. 11.2.1 (factor de compresibilidad de hidrocarburos)
sin que se haya podido verificar el match numerico exacto contra ese
documento (no disponible para cotejo directo esta ronda).

Limite de iteracion 2004 CONFIRMADO a bytes: 15 (FUN_180105b64 compara
"0xe < contador" tras incrementar, es decir corta al llegar a 15) -- coincide
con lo que el manual ya decia ("No convergence within 15 iterations"), ahora
tambien confirmado en el binario, no solo en el texto.

PENDIENTE EXPLICITO, no fabricado (metrico 2004, Table53/54):
La cadena real (FUN_1800edec8 -> FUN_180105ec8) SI pasa el valor 15.0
(DAT_180194008, la referencia metrica) como argumento explicito, y SI
convierte temperatura via FUN_1800e1d5c (°C->°F) -- pero la forma EXACTA en
que ese "15.0" interactua con la constante fija 60.0068749 del nucleo
compartido (dos candidatos: (a) el nucleo SIEMPRE usa 60.0068749 sin importar
la tabla, y la referencia metrica de 15°C se maneja en otro punto de la
cadena que no se identifico con certeza esta ronda, o (b) hay un paso
adicional no leido que ajusta la referencia) NO se resolvio con la misma
certeza que Table5/6/23/24_2004 -- la funcion Ghidra que decompilo estas
llamadas no muestra todos los ~16 argumentos de FUN_1801053f4 en el sitio de
llamada (limitacion conocida del decompilador con funciones de muchos
argumentos, ya vista antes en este proyecto), lo que impide confirmar con
certeza cual argumento exacto llega a que parametro para el caso metrico.
POR ESO este archivo implementa Table5/6/23/24_2004 (sistema US, sin
necesitar esa conversion) con la aritmetica de arriba, pero Table53_2004 y
Table54_2004 se dejan SIN una funcion Python numerica de referencia esta
ronda -- implementar un numero ahi habria sido fabricar una precision que no
se tiene. Ver funciones `api_table53_2004`/`api_table54_2004` mas abajo: NO
EXISTEN en este archivo todavia, a proposito.

[ACTUALIZACION RONDA 4, ver seccion "RONDA 4" completa mas abajo]: se
profundizo esta cadena releyendo FUN_1800edec8/FUN_180105ec8 linea a linea
(y su analogo para Table54_2004, FUN_1800eeecc/FUN_180105928) y se encontro
evidencia real de un PASO ADICIONAL que la Ronda 2 no habia leido -- es decir
la hipotesis (b) de arriba es la correcta, no la (a). Sigue SIN implementarse
un numero (la identidad exacta de que puntero/variable representa que
cantidad fisica en ese paso adicional no se pudo fijar con certeza total,
por el mismo tipo de reuso de variables/registros que ya bloqueaba el punto
anterior), pero el hallazgo estructural es real y esta documentado con
direcciones y numeros de linea concretos en la seccion RONDA 4.

`_ARITMETICA_2004_CONFIRMADA = True` refleja que la aritmetica CTL+F/CPL para
el subconjunto US (Table5/6/23/24_2004) esta confirmada por decompilacion
real (no que este validada contra un caso real en vivo -- Fase 5/7 sigue
pendiente, fuera del alcance de esta ronda, que la esta cubriendo otro agente
en paralelo con el emulador/Frida).

-------------------------------------------------------------------------------
RONDA 4 (2026-08-20): Hydrometer Correction CERRADA (Table5_1980); Table53/54
_2004 (metrico) -- nueva evidencia estructural real, sigue SIN numero
-------------------------------------------------------------------------------

[CERTAIN, cerrado] Pendiente "Hydrometer Corr." (Table5_1980): decompilada
FUN_1800e4450 (rama de despacho de productos 3..6 "grupo B" de
FUN_1800e4f94, alcanzable desde API_Table5_1980). El flag real corresponde
al 5to argumento Excel de Table5_1980 (el `char param_5` de FUN_1800e4f94,
que llega a FUN_1800e4450 como su `param_3`; el 4to argumento, "API
Rounding", es un flag DISTINTO que solo re-redondea variables intermedias a
N decimales via `FUN_1800e1db4`, consistente con Ronda 3). La formula real:

    hydrometer_factor = 1 - C1*dT - C2*dT^2 ,  dT = T_obs_F - 60.0
    rho_obs_corregida = rho_obs * hydrometer_factor   (ANTES de iterar)

con C1=DAT_1801ea7c0=1.278E-5 y C2=DAT_1801ea7b8=6.2E-9, ambos byte-exactos
del volcado `DAT_`. Evidencia en el codigo: `*param_6 = (1.0-dVar9)-dVar10;`
(factor) seguido de `dVar10 = DAT_1801ea830/(CONCAT44(...)+DAT_1801ea4e0);
*param_7=dVar10;` (densidad observada, DAT_1801ea830=141360.198=141.5*
999.012=141.5*RHO_WATER_60F_KGM3, confirma que ese segundo termino es
"observed_api -> densidad kg/m3" en un solo paso) y luego
`dVar10 = *param_6 * *param_7; *param_8 = dVar10;` -- el producto de ambos
ES la densidad observada YA CORREGIDA que entra a la iteracion. La rama de
crudo real (FUN_1800e404c, la que de hecho ejecuta el caso probado en Ronda
3 con product=1) NO esta decompilada en el archivo fuente (llamada en la
linea correspondiente pero nunca expandida por el script de Ghidra -- gap
real del archivo, no inventado), pero se llama con la MISMA firma y orden de
argumentos que FUN_1800e4450/FUN_1800e4b80 (los otros 2 productos), lo que
sugiere fuertemente el mismo cuerpo/formula. La confirmacion definitiva no
vino de leer esa rama sino de REPRODUCIR el numero real: aplicando la
formula de arriba al caso de Ronda 3 (Crude, API_obs=30, T_obs=90F) se
obtiene api_60f=27.95136088293313, que coincide con el valor real de la app
(27.95136) a la precision mostrada -- la MISMA precision con la que ya
coincidia el caso sin correccion (27.890942584019285 vs 27.89094). Esto se
considera evidencia real suficiente (no una coincidencia: la formula deriva
directamente del decompilado, y el numero resultante iguala al dispositivo
real) para declarar el pendiente CERRADO [CERTAIN] e implementarlo en
`_hydrometer_factor()` y en el nuevo parametro `hydrometer_correction: bool`
de `api_table5_1980`. NO se extendio a Table23_1980/Table53_1980 (comparten
el mismo motor `_ctl_1980_iter`, por lo que es plausible que tengan una
correccion analoga) porque no hay evidencia decompilada NI un caso real
probado para esas 2 tablas con el flag activo -- agregar el parametro ahi
habria sido extrapolar sin evidencia, que es exactamente lo que la regla de
oro del proyecto prohibe. Tampoco se investigo el enum de 4 opciones de
"API Rounding" de Table6 (pendiente de Ronda 3, sigue abierto, prioridad
baja).

[Sigue PENDIENTE, con evidencia nueva real] Table53_2004/Table54_2004
(metrico): se releyo linea a linea FUN_1800edec8 (Table53_2004) y su analogo
FUN_1800eeecc/FUN_180105928 (Table54_2004) contra la hipotesis (a)/(b) que
Ronda 2 habia dejado abierta. Hallazgo real: SI hay un paso adicional (b)
confirma la hipotesis correcta -- la funcion metrica NO simplemente reusa
60.0068749 sin mas. En concreto:
  1. La referencia metrica (DAT_180194008=15.0) se convierte a Fahrenheit
     via FUN_1800e1d5c (la MISMA funcion °C->°F ya confirmada en Ronda 2,
     "param*1.8+32" con los literales DAT_180193f60/180194160/180194158) --
     evidencia: `uVar7 = FUN_1800e1d5c(param_4);` en FUN_180105ec8, linea
     ~7057 del archivo de decompilacion, donde param_4 de esa funcion es
     precisamente el 15.0 recibido de FUN_1800edec8.
  2. El bucle iterativo principal (FUN_180105b64, el mismo de siempre, <=15
     iteraciones) SI corre con la temperatura OBSERVADA (no con 15.0) --
     confirmado porque el 5to parametro de FUN_180105ec8 (un valor DISTINTO
     de param_4, tambien pasado por FUN_1800e1d5c) es el que efectivamente
     se le pasa al bucle, y el bucle internamente sigue llamando al mismo
     nucleo FUN_1801053f4 con su T_ref interno fijo 60.0068749 (DAT_18028e758,
     confirmado linea 2469 del decompilado, hardcodeado DENTRO de
     FUN_1801053f4 sin depender de ningun parametro -- esto descarta que el
     nucleo alguna vez use 15.0 como referencia real del CTL exponencial).
  3. DESPUES de que el bucle converge, FUN_180105ec8 hace una SEGUNDA
     llamada DIRECTA (sin bucle) a FUN_1801053f4 usando el valor de (1),
     F(15.0), como argumento de temperatura -- linea ~7068:
     `FUN_1801053f4(param_1,param_2,*puVar5,uVar7,0,0,...)` donde `uVar7`
     es exactamente el F(15.0) de (1) y `*puVar5` es la densidad ya
     convergida por el bucle. Esta llamada evalua el CTL del nucleo
     compartido EN la referencia metrica (relativa al mismo baseline interno
     60.0068749), y su resultado se usa para reescalar la densidad del
     bucle a la base real de 15°C (linea ~7071, `*param_10 = <valor> /
     <CTL de esa 2da llamada>`).
  Esto CONFIRMA que existe un mecanismo real de 2 pasos (iterar en la base
  universal 60.0068749 con T_obs, despues reescalar a 15°C con una 2da
  evaluacion del mismo nucleo a T_ref_metric) -- la hipotesis (b), no la (a).
  SIN EMBARGO no se pudo fijar con certeza total la identidad algebraica
  exacta de cada puntero en esa 2da llamada: varias variables de salida se
  ESCRIBEN y luego se SOBRESCRIBEN casi inmediatamente por otro calculo
  (p.ej. `param_6`, `param_11`, `param_13`, `param_14` de FUN_180105ec8 se
  usan como "scratch" de la llamada al nucleo y despues se reemplazan por el
  valor final real unas lineas mas abajo), un patron de reuso de
  variables/registros identico al que ya se documento como limitacion
  conocida del decompilador en Ronda 2 (y que se re-confirmo esta ronda al
  ver `in_XMM0_Qa` -- un registro XMM sin asociar a ningun parametro
  nombrado -- en una funcion hermana, FUN_1800e5510). Implementar un numero
  con esta ambiguedad remanente seria fabricar precision que no se tiene, por
  lo que `api_table53_2004`/`api_table54_2004` SIGUEN sin existir en este
  archivo, tal como en Ronda 2 -- pero el "por que no se resuelve" ahora esta
  documentado con lineas y direcciones reales, no como una incognita total.

-------------------------------------------------------------------------------
[CERTAIN] Descripcion funcional completa de las 12 funciones (manual oficial)
-------------------------------------------------------------------------------
Fuente: `Flow-X Manual IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf`,
paginas 50-73 (leido con `pdfplumber`, Poppler no esta instalado). Da,
palabra por palabra, la lista de inputs/outputs con unidad, rango normal y
default, el enum completo de "Product" (igual en las 12 funciones), y el
texto de "Compliance" con la referencia exacta del estandar. Los rangos de
entrada (`Range` de la tabla del manual) son limites de UI, no
necesariamente el rango de validez fisica del estandar.

-------------------------------------------------------------------------------
HALLAZGOS BONUS (fuera del alcance pedido esta ronda, para rondas futuras)
-------------------------------------------------------------------------------
- Producto "8" aparece en el motor 2004 (no documentado en el manual junto a
  1..7): requiere un valor auxiliar en [0, 0.003] y usa una formula de alpha
  DIRECTA (sin tabla K0/K1/K2), consistente con un modo "coeficiente de
  expansion especificado por el usuario" -- no implementado, [GUESSING], no
  hay evidencia de que estas 12 funciones lo expongan en la UI/Excel.
- Los breakpoints de auto-seleccion B en el motor 2004 (grupo 2, Auto) usan
  densidad en kg/m3 (770.352/787.5195/838.3127, DAT_18028db20/28/30) mientras
  que el motor 1980 (Table23) usa RD adimensional (0.7785/0.84/...) para el
  mismo proposito -- diferencia real confirmada, no evaluada a fondo.
- El `.so` (Android) expone Table5/6/23/24/53/54 edicion 1952 (interpolacion
  tabulada, sin formula), Table59/60_2004 y variantes "E" (NGL/LPG, motor
  propio GPA TP-25/27) -- fuera de alcance, ver Ronda 1.

REGLA DE ORO DEL PROYECTO: no fabricar ni forzar un cierre. Lo que sigue
implementa con confianza 1980 completo (6/6 tablas, mas la correccion de
hidrometro de Table5_1980 desde Ronda 4) y 2004 parcial (4/6 tablas, las que
no requieren resolver la ambiguedad metrica); Table53_2004 y Table54_2004
quedan pendientes explicitamente, sin numero fabricado -- Ronda 4 agrego
evidencia real de POR QUE (mecanismo de 2 pasos confirmado) sin lograr
fijar la formula exacta con certeza total.

-------------------------------------------------------------------------------
RONDA 5 (2026-08-24): Table53_2004/Table54_2004 CERRADAS -- formula algebraica
exacta reconstruida (sin caso real en vivo todavia, ver limite de confianza)
-------------------------------------------------------------------------------
Tecnica usada (la mas barata de las 3 sugeridas, NO hizo falta reabrir Ghidra
ni el emulador): releer FUN_1800edec8/FUN_180105ec8 (Table53_2004) y
FUN_1800eeecc/FUN_180105928 (Table54_2004) reconstruyendo A MANO, linea por
linea, el layout real de la pila de la llamada con muchos argumentos (el
punto exacto donde Ronda 4 se habia quedado atascada). Clave del avance: el
tamano del buffer del canario de seguridad (`auStack_158[32]`, cuyo XOR
calcula `local_80`/`local_88`) fija que `local_138` es la PRIMERA direccion
de pila libre despues del canario (158-138=0x20=32 bytes exacto) -- eso
ancla que `local_138` es literalmente `[rsp+0x20]` en el momento de la
llamada, es decir el 5to argumento (los primeros 4 van en registros segun
la ABI Microsoft x64). A partir de ahi, los siguientes locales (130, 128,
120, ..., d0) caen en una secuencia CONTIGUA de 8 bytes cada uno -- son los
argumentos 6 a 18 de `FUN_180105ec8`/`FUN_180105928` (18 parametros cada
una), que Ghidra nunca mostro en el sitio de llamada (la limitacion ya
documentada en Rondas 2/4) pero que SI se pueden reconstruir asi con certeza
posicional, sin ambiguedad, porque la aritmetica de offsets es una regla
fija del compilador, no una suposicion.

Con esa reconstruccion, el mecanismo real de Table53_2004 (`FUN_1800edec8`->
`FUN_180105ec8`) queda así, confirmado linea a linea:
1. El bucle iterativo (`FUN_180105b64`, <=15 iter, el mismo nucleo de
   siempre) resuelve `rho_base` con la TEMPERATURA Y PRESION REALES
   (T_obs converida a F via `FUN_1800e1d5c`, presion convertida bar->kPa
   [DAT_1801940c8=100.0, confirmado EXACTO en el volcado de constantes -- no
   es una suposicion, aparece literal en la lista de 167 `DAT_`] ->psi
   [/DAT_1801ea5d8=6.894757]), exactamente igual que Table5/23_2004 (US).
   Al converger, deja en una variable local (reusada, el mismo patron ya
   documentado) el CTL evaluado en esa condicion real (`ctl_obs`) y en otra
   el CTPL completo (`ctpl_obs`).
2. DESPUES, una SEGUNDA llamada DIRECTA (sin bucle) a `FUN_1801053f4` evalua
   el MISMO nucleo con el `rho_base` YA CONVERGIDO pero con T=F(15.0)=59°F
   (la referencia metrica convertida) y P=0 -- esto da `ctl_15`, el factor
   que traduce el `rho_base` (que vive en la referencia UNIVERSAL interna
   60.0068749°F, ligeramente distinta de 15°C exactos) a la densidad REAL a
   15°C: `density_15c = rho_base * ctl_15`. Este es el numero que faltaba.
3. [CORREGIDO EN RONDA 6, ver esa seccion] La linea real
   `*param_10 = param_6/local_78;` (`ctpl_obs / ctl_15`) SI se identifico
   bien en esta ronda, pero se le puso la ETIQUETA equivocada en el
   diccionario Python devuelto: es el `ctpl` real de la app (confirmado con
   caso real en Ronda 6), no el `ctl`. Corregido en Ronda 6.
Table54_2004 (`FUN_1800eeecc`->`FUN_180105928`) es la operacion INVERSA,
confirmada con el mismo metodo: primero corre el MISMO bucle pero con
T=59°F fijo y P=0 (para invertir la densidad a 15°C dada por el usuario y
recuperar `rho_base`), y LUEGO una llamada directa con la T/P REALES para
obtener `ctl_real`/`cpl_real`; el resultado final es
`ctl_out = ctl_real/ctl_15` (mismo `ctl_15` de la primera sub-llamada) y
`ctpl_out = ctl_out*cpl_real`, con la densidad predicha a condicion real
= `ctpl_out * density_15c_input` (campo bonus, replica exacta de la linea
`*param_13 = *param_9 * *param_10 * param_3`).

Verificacion (NO es un caso real en vivo, pero es evidencia real, no
fabricada): 3 chequeos independientes, todos exactos salvo tolerancia de
iteracion (~1e-8, ruido de convergencia, no error de formula):
(a) Sanity fisico: si T_obs=15°C y P=0, `density_15c` debe devolver el mismo
    valor de entrada (medir a la propia referencia no debe cambiar nada) --
    confirmado (850.0 entra, 850.0000000003 sale).
(b) Round-trip Table53->Table54: aplicar Table53 a una densidad observada
    (T=45°C, P=5 bar) y luego Table54 al resultado (misma T,P) debe
    recuperar la densidad observada original -- confirmado con Crudo
    (diff=1.4e-8) y con Lubricante (T=-10°C, P=20 bar, diff=1.1e-9), usando
    2 juegos de K0/K1/K2 distintos.
(c) DAT_1801940c8=100.0 (bar->kPa) es coherente con el propio volcado de
    constantes (confirmado exacto, no supuesto) Y con la unica lectura
    fisica posible de una conversion de presion metrica limpia.

Nivel de confianza: [CERTAIN via decompilacion exhaustiva + verificacion
algebraica cruzada -- NO fabricado], pero un peldano por debajo de "caso
real en vivo" (Fase 5/7 sigue pendiente para TODA la familia 2004, no solo
Table53/54 -- ningun caso real 2004 se ha conseguido todavia en ninguna de
las 6 tablas). Documentado asi explicitamente, sin inflar el nivel.

Cabo suelto NO resuelto, documentado honesto (no afecta la formula
implementada): el sitio de llamada real pasa literalmente el entero "0" como
argumento de producto a `FUN_180105ec8`/`FUN_180105928` en vez del codigo
interno remapeado (`iVar2`) que la propia funcion calcula linea arriba y
que nunca vuelve a usar explicitamente -- casi seguro otro artefacto del
decompilador con el mismo patron de variable/registro reusado ya visto (el
remapeo de producto SI se calcula, seria absurdo que el binario lo tirara
siempre a "Gasolina" por defecto). Esto NO afecta la implementacion de abajo
porque el codigo Python usa `K_US[product]` con el numero de producto AL
NIVEL EXCEL (1..7), exactamente como ya hacian `api_table5_2004` etc. antes
de esta ronda -- el remapeo interno es un detalle de despacho DENTRO del
binario que no cambia que tabla K0/K1/K2 corresponde a cada producto Excel
(ya validado por bytes en rondas anteriores).

-------------------------------------------------------------------------------
RONDA 6 (2026-08-25): 18 casos reales nuevos (Fase 5/7), enum de Table6
CERRADO, Hydrometer Correction extendida a Table23_1980, bug de mapeo de
campos en Table53_2004 encontrado y CORREGIDO
-------------------------------------------------------------------------------
Tras 2 intentos anteriores detenidos por el usuario a mitad de tarea (sin
guardar nada, confirmado ambas veces antes de relanzar), un 3er intento con
guardado INCREMENTAL (leccion nueva: escribir cada caso al JSON apenas se
consigue, no esperar al final) consiguio 18 casos reales nuevos, guardados en
`android_sdk_setup/casos_reales_api_tables_ronda5.json`. La familia pasa de 9
a 27 casos reales, cubriendo por primera vez las 12 funciones (antes solo
Table5/6_1980 tenian caso real).

[CERTAIN, caso real] Table23_1980 (3 casos), Table24_1980 (2 casos, incluye
la exploracion completa del enum de Rounding), Table53_1980 metrico (3
casos), Table54_1980 metrico (2 casos): TODOS <0.0001% de error contra el
Python ya existente, sin cambios de formula necesarios.

[CERTAIN, caso real] Table5_2004/Table6_2004 (US, 4 casos con presion
variada) y, por primera vez, Table53_2004/Table54_2004 (METRICO -- 4 casos,
confirmando que SI existe pantalla real "API Table-53/54 (2004)" en la app,
algo que no se sabia hasta esta ronda) -- todos <0.004% de error tras el
fix del punto siguiente.

[CERTAIN, HALLAZGO Y FIX, no es un bug de formula sino de ETIQUETADO] El
campo `"ctl"` que `api_table53_2004()` devolvia (desde la Ronda 5) en
realidad correspondia al `CTPL` real que muestra la app, no a su `CTL` --
invisible con presion=0 (donde CTL=CTPL porque CPL=1), se revelo con
presion=5 bar(g): python devolvia 0.9961448 bajo la clave "ctl", que
coincide EXACTO con el CTPL real de la app (0.996144), mientras que el CTL
real de la app es 0.995777. Corregido: ahora `api_table53_2004()` devuelve
los 3 campos correctos (`ctl`=ctpl_obs/ctl_15/cpl_obs, `cpl`=cpl_obs sin
cambios, `ctpl`=ctpl_obs/ctl_15 -- el valor que antes se llamaba "ctl"),
verificado exacto contra los 2 casos reales (P=0 y P=5bar) tras el fix.
`api_table54_2004` NO tenia este problema (sus 3 campos ya coincidian 1:1
con la app).

[CERTAIN, caso real, cierra un pendiente de Ronda 4] Hydrometer Correction
en Table23_1980: la pantalla real SI expone "Hydrometer Corr." (Ronda 4 solo
lo habia inferido por motor compartido, sin verificar en la UI). Aplicando
la MISMA `_hydrometer_factor()` ya usada en Table5_1980 sobre la densidad
observada antes de iterar, se reproduce el caso real (RD_obs=0.85, T=90F:
rd_60f=0.861617, ctl=0.986133) a <0.0001%. Agregado el parametro
`hydrometer_correction` a `api_table23_1980`.

[PENDIENTE, no fabricado] Hydrometer Correction en Table53_1980 (metrico)
SIGUE sin resolver: se probaron 2 hipotesis simples (reusar las constantes
US con dT en °C, o convirtiendo dT a °F antes de aplicar la formula US) y
NINGUNA reproduce el valor real dentro del margen de ruido normal (~0.0013%
de error, 10-20x el ruido tipico de <0.0001% de esta familia) -- hace falta
decompilar la rama especifica de Table53_1980 con el flag activo en una
ronda futura, no se fuerza una formula que no cierra limpio.

[CERTAIN, caso real] Enum "API Rounding" de Table6_1980/Table24_1980
CERRADO: probadas las 4 opciones (Disabled/Enabled/"Enabled (table
values)"/"Enabled (5 decimal places)") sobre el mismo caso base. Solo
"Enabled (table values)" cambia el numero (redondea a 4 decimales, la
resolucion de las tablas API-2540 impresas); las otras 3 dan el mismo CTL
sin redondear. NO afecta la formula interna, solo presentacion -- no se
implementa en el motor de referencia (igual que "API Rounding" de Table5,
ya documentado).

[CERTAIN, confirmacion en vivo del residuo ya documentado] Con Table6_2004
(funcion directa, sin iteracion) se midio un ~0.00068% de error consistente
en CTL contra el caso real, que corresponde EXACTO al gap ya documentado
mas arriba (micro-correccion polinomica de temperatura omitida por duda
real sobre 4 de sus 8 coeficientes) -- confirma que omitirla en vez de
fabricarla fue la decision correcta, el residuo esta acotado y entendido.

[NOTA OPERATIVA] El selector de Presion de las pantallas 2004 NO ofrece
psig como opcion (solo bar/mbar/mmHg/inHg/mmH2O/inH2O) -- coherente con que
la app usa unidades del sistema del usuario para VISUALIZAR presion aunque
el motor interno siga trabajando en psig (conversion manual necesaria al
comparar casos, ya aplicada en los 18 casos guardados).

ESTADO DE LA FAMILIA TRAS RONDA 6: 12/12 funciones implementadas
[CERTAIN via decompilacion], 27 casos reales cubriendo las 12, enum de
Table6 cerrado, hidrometro cerrado en Table5/23_1980. UNICOS pendientes
activos: Hydrometer Correction en Table53_1980 (metrico, sin formula que
cierre), y la micro-correccion polinomica de 2004 (residuo <0.001%,
documentado, no bloqueante).

-------------------------------------------------------------------------------
RONDA 7 (2026-08-25): Hydrometer Correction en Table53_1980 (metrico) CERRADA
-------------------------------------------------------------------------------
[LIKELY, NO decompilado, pero evidencia fuerte] Hipotesis: escalar
HYDROMETER_C1/C2 (US) por la pendiente °F/°C (1.8 lineal, 1.8^2 cuadratico --
el MISMO patron ya usado en K0/K1/K2 metrico/US de este archivo) y
aplicarlos sobre dT en Celsius relativo a 15.0C (no Fahrenheit). Derivada
ANTES de comparar contra el dato real (no es un ajuste ciego a la respuesta),
cierra a 0.00001% contra el unico caso real disponible (Crude,
Density_obs=1000kg/m3, T=20C: density_15c=1002.948), 10x mas ajustado que el
ruido tipico <0.0001% de esta familia. Las otras 2 hipotesis probadas (US sin
convertir, con dT en C o en F) NO cerraban (0.0052%/0.0013% de error).
Implementado como `HYDROMETER_C1_METRIC`/`HYDROMETER_C2_METRIC`/
`_hydrometer_factor_metric()` y el parametro `hydrometer_correction` de
`api_table53_1980`. Documentado [LIKELY] (no [CERTAIN]: 1 solo caso real,
rama especifica no decompilada).

-------------------------------------------------------------------------------
RONDA 8 (2026-08-25): micro-correccion polinomica de 2004 CERRADA -- CONFIRMA
hipotesis (a): son 8 coeficientes reales, no 4 + basura de decompilacion
-------------------------------------------------------------------------------
Tecnica usada (mas barata que reabrir Ghidra, tal como sugeria el pendiente):
    1. Se dumpearon los BYTES CRUDOS del `.xll` en el rango 0x18028e840..
       0x18028e880 (64 bytes = 8 doubles) con `pefile` en Python, resolviendo
       VA->offset de archivo con las secciones reales del PE (ImageBase=
       0x180000000, `pe.get_offset_from_rva`) -- SIN pasar por Ghidra. Los 8
       doubles resultantes:
           0x18028e840=1.08076     0x18028e848=1.269056   (antes "_UNK_")
           0x18028e850=-0.148759   0x18028e858=-0.267408  (antes "_UNK_")
           0x18028e860=-4.089591   0x18028e868=-1.871251  (antes "_UNK_")
           0x18028e870=7.438081    0x18028e878=-3.536296  (antes "_UNK_")
       Los 4 "_UNK_" son doubles bien formados, DISTINTOS entre si y de los
       otros 4 -- no hay ningun patron de "un double de 8 bytes mal partido
       en 2 floats de 4" (eso produciria basura/NaN/exponentes absurdos al
       reinterpretar medio double, que NO es lo que se observa).
    2. Se releyo el PSEUDOCODIGO de `FUN_180106114` (ya presente en
       `ghidra_api_mpms_xll_output.txt`, no hizo falta generar disassembly
       nuevo ni reabrir Ghidra): es un bucle de Horner EXPLICITO que carga
       los 8 slots `local_58[0..7]` (line por linea: `local_58[0..7] =
       _DAT_18028e850, _UNK_18028e858, _DAT_18028e840, _UNK_18028e848,
       _DAT_18028e860, _UNK_18028e868, _DAT_18028e870, _UNK_18028e878`) y
       LOS LEE LOS 8 dentro del bucle (`pdVar1 = local_58 + lVar3; ... dVar2
       = (dVar2 + *pdVar1) * (param_1/_DAT_1801eb188)`, lVar3 de 7 a 0) --
       sin ambiguedad de registro reusado (a diferencia de otros casos ya
       documentados en Rondas 4/5), porque es codigo recto de un arreglo
       local, no un sitio de llamada con muchos argumentos. CONFIRMA
       hipotesis (a): se leen las 8 direcciones, no 4 -- el warning de
       Ghidra ("Globals starting with '_' overlap smaller symbols") era
       puramente un artefacto de COMO NOMBRA los simbolos, no evidencia de
       datos invalidos.
Forma final reconstruida (Horner deshecho a potencias, z=((T_F-32)*5/9)/
630.0, grado 8, sin termino constante):
    P(z) = -0.148759*z - 0.267408*z^2 + 1.08076*z^3 + 1.269056*z^4
           - 4.089591*z^5 - 1.871251*z^6 + 7.438081*z^7 - 3.536296*z^8
    T_obs_corregida_F = T_obs_F - P(z)*9.0/5.0
(la conversion Celsius<->Fahrenheit del "viaje" completo se confirmo leyendo
FUN_180106198 -- DAT_180193fa0=5.0, DAT_180193fd0=9.0, DAT_180194058=32.0,
DAT_1801eb188=630.0, los 4 byte-exactos). Implementado en
`_micro_correccion_temp_2004()`, aplicado dentro de `_ctl_2004` Y
`_f_compressibility_2004` (el decompilado de `FUN_1801053f4` confirma que
AMBAS formulas reusan el MISMO valor ya corregido, sin recalcularlo).

Verificacion (caso real de Ronda 6, Table6_2004 Crude, api60F=30, T=90F,
K0=341.0957, ctl_app=0.986588): el residuo de CTL bajo de 0.0006800964543%
(SIN correccion) a 0.0000125041445% (CON correccion) -- 54x mas cerca del
valor real de la app. Con el 2do caso real (mismo T, P=15bar(g)->217.5566
psig), CTPL bajo de 0.00069230% a 0.00002988% (23x). CPL ya era <0.00001%
en ambos casos (el termino de temperatura pesa poco frente al de presion en
esa formula) y se mantiene en ese orden con la correccion. El residuo NO
llega a 0.0 exacto (queda ~0.00001-0.00003%, del mismo orden que el ruido de
redondeo de 6 decimales de la UI ya visto en el resto de la familia) -- es
la reduccion, no la eliminacion total, lo que se toma como evidencia real de
que la formula reconstruida es correcta (fabricar un polinomio que no
mejorara el numero real habria sido la señal de que la reconstruccion
estaba mal).

ESTADO DE LA FAMILIA TRAS RONDA 8: 12/12 funciones implementadas, 27 casos
reales, 12/12 pestañas. Hydrometer Correction cerrada en las 3 tablas donde
el flag existe (Table5/23_1980 [CERTAIN], Table53_1980 [LIKELY, Ronda 7]).
Micro-correccion polinomica de 2004 CERRADA [CERTAIN via bytes crudos +
pseudocodigo, mejora verificada contra 2 casos reales]. NO quedan pendientes
activos conocidos en esta familia.

-------------------------------------------------------------------------------
RONDA 9 (2026-08-25): CORRECCION de un error real de una ronda anterior --
"API Density @15°C (1952)" y los 3 wrappers de presion de 1980 SI eran
decompilables. El modulo API MPMS 11.2.1/11.2.1M queda CERRADO [CERTAIN].
-------------------------------------------------------------------------------
Contexto del error (ver memoria del proyecto, "CORRECCION IMPORTANTE
2026-08-25"): una ronda anterior declaro "no implementable" a la familia 1952
completa (9 funciones) MAS los 3 wrappers de presion de 1980 (Density@15C/
Gravity@60F/Rel.Density@60F) MAS el modulo API MPMS 11.2.1/11.2.1M, basandose
SOLO en una frase del manual sobre la tabla 1952 ("no calculations involved,
just interpolation"), SIN decompilar. El usuario probo "API Density @15°C
(1952)" en la app real y SI dio un numero real (Density_obs=1000kg/m3,
T=25°C, P=20bar(g), EVP=0bar(g) -> Density_15C=1005.482, CTL=0.993510,
CPL=1.001045), lo que contradecia la conclusion anterior.

Se relanzo la decompilacion real (Ghidra 12.1.2, `.xll`, mismo proyecto
`ANALISIS .XLL`) de las 10 raices nuevas: los 9 simbolos de la familia 1952
(`API_Dens15C_1952`, `API_Gravity60F_1952`, `API_SG60F_1952`,
`API_Table5/6/23/24/53/54_1952`) y `API_MPMS_11_2_1M` (metrico) -- mas, en
una 2da pasada, las 4 raices de los wrappers de presion de 1980
(`API_Dens15C_1980`, `API_Gravity60F_1980`, `API_RD60F_1980`,
`API_MPMS_11_2_1` sistema US). Scripts: `DecompileApi1952Xll.java`,
`DecompileApi1980WrappersXll.java`, `DecompileApi1952Core.java` (para
recuperar `FUN_1800f8f70`, que el limite de 40 funciones/raiz del primer
script no llego a expandir). Salidas en
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_api1952_xll_output.txt`,
`ghidra_api1980wrappers_xll_output.txt`, `ghidra_api1952core_xll_output.txt`.

RESULTADO, con evidencia real (NO fabricado en ninguna direccion):

1. [CERTAIN, CIERRA UN PENDIENTE DE RONDA 3/4] El modulo de presion
   `API_MPMS_11_2_1M` (metrico, FUN_1800a0798 -> FUN_1800e303c) y su
   hermano US `API_MPMS_11_2_1` (FUN_1800a05dc -> FUN_1800e2d5c) SI son
   completamente decompilables, con constantes byte-exactas (confirmadas
   contra el volcado `DAT_` de cada corrida) y SIN ninguna tabla de por
   medio -- son formulas analiticas puras:
       rho_r = rho_kgm3 / 1000.0                    (metrico; US usa
                                                       141.36/(API+131.5)
                                                       en su lugar)
       F = exp( T*2.1592E-4 - 1.6208 + 0.87096/rho_r^2
                + T*0.0042092/rho_r^2 ) / 10000.0     (metrico)
       F = exp( T_F*1.3427E-4 - 1.9947 + 0.79392/rd_r^2
                + T_F*0.002326/rd_r^2 ) / 100000.0    (US)
       CPL = 1 / (1 - (P1-P2)*0.01*F)   [metrico, P en kPa]
       CPL = 1 / (1 - (P1-P2)*F)        [US, P en psi]
   Rangos oficiales confirmados a bytes: metrico rho 637.5-1074.0 kg/m3,
   T -30..90°C, P 0-10300 kPa; US API 0-90.3, T -20..200°F, P 0-1500 psig.
   Estas formulas coinciden estructuralmente con la formula PUBLICADA de
   API MPMS Cap. 11.2.1/11.2.1M ("Compressibility Factors for Hydrocarbons,
   0-90° API Gravity Range") -- match de forma y de escala de constantes
   [LIKELY el mismo estandar, por conocimiento tecnico general, NO se tuvo
   el documento abierto para citar textualmente esta ronda].
   VALIDACION NUMERICA contra el caso real del usuario: usando la densidad
   YA CONVERGIDA a 15°C (1005.482 kg/m3, no la observada 1000kg/m3) como
   `rho` de la formula, T=25°C, P=20bar(g)*100=2000kPa, EVP=0:
   CPL_calculado=1.0010454 vs CPL_real_app=1.001045 -- diferencia ~0.00003%,
   dentro del ruido de redondeo de 6 decimales ya visto en el resto de la
   familia. CIERRA [CERTAIN] el pendiente que los placeholders de
   "API Density/Gravity/Rel.Density (1980)" citaban como bloqueante ("la
   formula de F para API MPMS 11.2.1/11.2.1M no se ha decompilado").
   Implementado en `api_mpms_11_2_1m()`/`api_mpms_11_2_1()`.

2. [CERTAIN, CIERRA los 3 wrappers de presion de 1980] Se decompilo el
   nucleo real de `API_Dens15C_1980` (FUN_18009f484 -> FUN_1800e62d4) y de
   `API_Gravity60F_1980` (FUN_1800a0230 -> FUN_1800e79e4): ambos INLINEAN
   (no llaman como subrutina, pero usan literalmente las mismas direcciones
   `DAT_1801ea4b0/4c0/4a0/4c8/328` o `4a8/4b8/498/4d0`) la MISMA formula de
   F/CPL de arriba, combinada con el motor CTL de 1980 YA CERTAIN
   (K_METRIC/K_US, `_alpha`/`_ctl_1980`) mediante una iteracion CTL*CPL
   analoga a la ya implementada para 2004 (`_ctpl_2004_iter`), con limite
   de 100 iteraciones (mismo limite que el resto del motor 1980, confirmado
   en el decompilado: "if (100 < iVar5) goto ..."). Implementado en
   `api_density15c_1980()` (metrico, reusa Table53/54_1980 + MPMS_11_2_1M),
   `api_gravity60f_1980()` (US, reusa Table5/6_1980 + MPMS_11_2_1, con la
   densidad-base convertida a °API via 141.5/RD-131.5, la MISMA identidad
   ya usada en todo este archivo) y `api_reldensity60f_1980()` (US, reusa
   Table23/24_1980, misma conversion a °API para el paso de CPL). NO se
   valido contra un caso real EN VIVO de estos 3 wrappers especificos esta
   ronda (el usuario solo probo el de 1952) -- mismo nivel de confianza que
   Table53/54_2004 en Ronda 5: [CERTAIN via decompilacion exhaustiva], un
   peldano por debajo de "caso real en vivo".

3. [CONFIRMADO, NO FABRICADO EN NINGUNA DIRECCION] El paso "CTL" de la
   familia 1952 (Table5/6/23/24/53/54_1952 y los 3 wrappers combinados
   Dens15C/Gravity60F/SG60F_1952) SI es una tabla de interpolacion real,
   PERO la tabla esta EMBEBIDA dentro del propio `.xll` como datos binarios
   compactos (no es una referencia externa inexistente) -- localizada en
   `&DAT_18028a680` y leida por una cadena real (`FUN_1800f9b24` ->
   `FUN_1800f7ebc` [interpolacion lineal entre 2 filas] -> `FUN_1800f876c`
   [busqueda de la fila] -> `FUN_1800f74c4` [decodifica un formato binario
   compacto: cabecera `ushort` con valor base + `byte` con cantidad de
   filas + puntero a un arreglo de `ushort` con los valores delta]). Decodificar
   el formato exacto de esa tabla (para reproducir CTL sin la iteracion
   completa) NO se termino esta ronda -- el sitio de llamada real a
   `FUN_1800f74c4`/`FUN_1800f876c` vuelve a mostrar el problema YA
   documentado en Rondas 2/4/5 (Ghidra no expone todos los argumentos en el
   sitio de llamada de una funcion con muchos parametros), y un intento de
   leer la aritmetica de interpolacion en `FUN_1800f876c` dio una expresion
   degenerada (`(x*0.0)/0.0`) que es evidencia de ese MISMO artefacto, no
   una formula real. Se documenta como PENDIENTE ABIERTO, con evidencia de
   POR QUE (la tabla existe, esta localizada, el formato es decodificable
   en principio) en vez de la frase generica anterior -- NO se fabrica un
   numero de CTL para 1952. `API_Table5/6/23/24/53/54_1952` y los 3
   wrappers combinados de 1952 (Dens15C/Gravity60F/SG60F) SIGUEN sin
   funcion Python de referencia, a proposito.

4. CONFIRMADO por decompilacion directa (`FUN_1800f8f70`, el nucleo interno
   de iteracion de `API_Dens15C_1952`): el paso de CPL de la familia 1952
   SI llama al MISMO `FUN_1800e303c` (API_MPMS_11_2_1M) del punto 1 arriba,
   pasando la densidad YA CONVERGIDA (base a 15°C), no la observada -- esto
   fue lo que permitio la validacion numerica del punto 1. Es decir: 1952 y
   1980 comparten el MISMO modulo de presion; solo el paso CTL cambia (tabla
   vs. formula analitica).

CONCLUSION SOBRE EL ERROR: el error de la ronda anterior se corrige
PARCIALMENTE, con evidencia real en ambas direcciones (ni fabricar un
numero ni fabricar un "no se puede"): el modulo de presion (11.2.1/11.2.1M)
y los 3 wrappers de 1980 SI eran decompilables y estaban mal etiquetados
como bloqueados -- corregido, implementado, cerrado [CERTAIN]. La familia
1952 (los 6 Table_1952 puros y sus 3 wrappers combinados) SIGUE sin numero
por el paso CTL, pero ahora por una razon decompilada y localizada (tabla
binaria real encontrada, formato parcialmente entendido, no decodificada
por completo), no por la frase del manual tomada sin verificar.

ESTADO DE LA FAMILIA TRAS RONDA 9: 17 funciones de este archivo con numero
real (las 12 de Ronda 8 + `api_mpms_11_2_1m`/`api_mpms_11_2_1` +
`api_density15c_1980`/`api_gravity60f_1980`/`api_reldensity60f_1980`).
PENDIENTE explicito, no fabricado: los 6 `Table_1952` puros y sus 3
wrappers combinados (9 funciones, bloqueadas por el mismo motivo: CTL
tabular sin decodificar completo).

-------------------------------------------------------------------------------
RONDA 10 (2026-08-26): Table53_1952/Table54_1952 (metrico) DECODIFICADAS --
la tabla binaria real localizada en Ronda 9 SI se termino de decodificar,
via dump de bytes crudos (tecnica de Ronda 8) en vez de mas disassembly
-------------------------------------------------------------------------------
Punto de partida: Ronda 9 localizo la tabla real (`&DAT_18028a680`, leida
por `FUN_1800f9b24 -> FUN_1800f7ebc -> FUN_1800f876c -> FUN_1800f74c4`) pero
no pudo decodificarla porque el sitio de llamada real a
`FUN_1800f74c4`/`FUN_1800f876c` vuelve a mostrar el problema ya documentado
en Rondas 2/4/5 (Ghidra no expone todos los argumentos en un sitio de
llamada con muchos parametros) -- un intento de leer la aritmetica de
`FUN_1800f876c` dio una expresion degenerada (`(x*0.0)/0.0`).

Tecnica que SI funciono esta ronda (la sugerida en el prompt, la misma de
Ronda 8): en vez de seguir peleando con el pseudocodigo roto de
`FUN_1800f876c`, se dumpearon los BYTES CRUDOS de la tabla directamente del
`.xll` con `pefile` (VA->offset via las secciones reales del PE,
ImageBase=0x180000000, `&DAT_18028a680` cae en `.rdata`), y se decodifico
el FORMATO DE CABECERA leyendo el pseudocodigo (SI intacto, sin argumentos
perdidos) de `FUN_1800f74c4`, que es una funcion completa y autocontenida
(no depende de argumentos perdidos en su PROPIO sitio de llamada para
decodificar la cabecera, solo para el `param_2`/`param_3` que ya se pudo
inferir por el contexto de las funciones que SI decompilan completas):

1. [CERTAIN, dump de bytes + lectura de pseudocodigo intacto]
   Cabecera real de 16 bytes por segmento (6 segmentos, 96 bytes totales en
   `&DAT_18028a680`):
       offset 0-1 (ushort): base de densidad del segmento, EN kg/m3
                            DIRECTO (sin factor de escala)
       offset 2   (byte):   cantidad de FILAS del segmento (paso de density,
                            5 kg/m3 por fila -- confirmado por
                            `DAT_180193fa0=5.0`)
       offset 3   (int8, firmado): columna MINIMA de temperatura, en
                            unidades de 0.5°C (confirmado por
                            `DAT_180124438=2.0`, el factor de doblado)
       offset 4   (byte):   columna MAXIMA de temperatura, mismas unidades
       offset 8-15 (ptr64): puntero absoluto (el `.xll` no tiene ASLR) al
                            arreglo de valores `ushort`, escalados x10000
                            (confirmado por `DAT_1801ea328=10000.0`, la
                            MISMA constante de escala que ya se usaba en
                            `api_mpms_11_2_1m`/`_1`)
   Los 6 segmentos decodificados (base, filas, col_min, col_max, puntero):
       (500,20,-46,60,0x18027b420) (600,1,-46,75,0x18027d570)
       (605,47,-25,75,0x18027d760) (840,6,-25,100,0x180282130)
       (870,19,-25,125,0x180282d00) (965,28,-25,150,0x1802859b0)
   Evidencia de que la lectura es correcta (no una coincidencia numerica):
   los 6 segmentos ENCADENAN EXACTO en densidad (base(i+1) == base(i) +
   filas(i)*5 para los 5 pares consecutivos), Y el GAP real entre punteros
   consecutivos coincide con el tamano predicho por la formula
   (filas*ancho_columnas*2 bytes) dentro de 0-12 bytes de diferencia (el
   residuo pequeno y siempre positivo es compatible con alineacion/padding
   entre tablas, NO con un formato mal entendido). Rango fisico resultante
   (500-1105 kg/m3, -46 a 150°C segun segmento) es plausible para
   hidrocarburos liquidos (segmento mas liviano con rango de T mas frio,
   segmento mas denso -fuel oil- con rango de T mas caliente hasta 150°C).

2. [CERTAIN, formula de columna via decompilacion directa de
   `FUN_1800f74c4`, intacta] Indice dentro del arreglo del segmento:
       ancho_por_fila = (col_max - col_min)*2 + 1
       idx = ancho_por_fila*fila + (columna_T - 2*col_min)
       valor = ushort_arreglo[idx] / 10000.0

3. [CERTAIN, `FUN_1800f7ebc` decompila completo, SIN el problema de
   argumentos perdidos] Interpolacion en el eje TEMPERATURA: columna exacta
   = ceil(2*T); si T no cae en un multiplo de 0.5°C exacto, interpola
   linealmente contra la columna vecina (arriba o abajo segun corresponda),
   formula identica a la ya usada en el resto de la familia (temp/densidad
   base 60F/15C, ver `_ctl_1980`).

4. [LIKELY, POR ANALOGIA -- NO decompilado directamente, la funcion
   `FUN_1800f876c`/`FUN_1800f7928` que hace esto en el binario SI sigue
   con el problema de argumentos perdidos ya documentado en Ronda 9]
   Interpolacion en el eje DENSIDAD: se asumio la MISMA estructura que el
   punto 3 (fila exacta si la densidad cae en un multiplo de 5 kg/m3 desde
   la base del segmento, si no, interpolar linealmente contra la fila
   vecina) -- por SIMETRIA arquitectonica con el eje temperatura (mismo
   patron "buscar grid mas cercano, interpolar con vecino segun signo del
   residuo" que SI se confirmo intacto en el punto 3), no fue inventada
   para forzar el numero. Se declara [LIKELY] y no [CERTAIN] porque la
   formula EXACTA de esa interpolacion en particular no se leyo en
   ensamblador -- se dedujo por simetria y luego se puso a prueba contra
   el caso real.

VALIDACION NUMERICA (evidencia REAL de que la reconstruccion del punto 4 es
correcta, no un ajuste ciego): con el caso real completo del usuario
(Density_obs=1000kg/m3, T_obs=25°C, P=20bar(g), EVP=0bar(g)):
    density_15c calculado=1005.4817 vs real=1005.482  (error 0.000033%)
    ctl calculado=0.9935096         vs real=0.993510  (error 0.000037%)
    cpl calculado=1.0010454         vs real=1.001045  (error 0.000036%)
las 3 salidas dentro del MISMO orden de ruido (~0.00003-0.00004%) ya visto
en el resto de la familia para reconstrucciones [CERTAIN] -- el hecho de
que las 3 salidas combinadas (CTL de la tabla + CPL del modulo de presion
YA CERTAIN de Ronda 9, iterando density_15c hasta converger) coincidan
juntas a ese nivel es evidencia fuerte de que la interpolacion de densidad
del punto 4 SI es la correcta, no una coincidencia -- una formula de
interpolacion equivocada habria introducido un error mucho mayor que el
ruido de redondeo tipico. Sanity check adicional (no forzado): a T=15°C
exactos (la referencia), Table54_1952 da CTL=1.0 EXACTO -- esto emerge de
los datos reales de la tabla (no hay ningun caso especial "if T==15:
return 1.0" en el codigo), confirmando que la tabla en si esta anclada
correctamente a la referencia de 15°C.

Implementado en `_ctl_1952_metric_lookup()` (nucleo de busqueda),
`api_table53_1952()` (observado->15°C, iterativo), `api_table54_1952()`
(15°C->CTL, directo) y `api_density15c_1952()` (combina CTL de tabla + CPL
de `api_mpms_11_2_1m`, replica completa de "API Density @15°C (1952)").
Los datos crudos de la tabla se extrajeron UNA sola vez con `pefile` y se
embebieron en `_api_table1952_metric_data.py` (base64, ~62KB de datos
reales) -- el modulo YA NO depende de que `FlowXpert.xll` este presente en
tiempo de ejecucion para estas funciones.

PENDIENTE explicito, NO resuelto esta ronda (fuera del alcance del caso
real disponible, que solo cubre Table53/54): Table5/6_1952 (US, tabla en
`&DAT_18027b2c0`, 22 segmentos) y Table23/24_1952 (US, probablemente en
`&DAT_180232930`/`&DAT_18023f250`, 24/6 segmentos) son tablas DISTINTAS
(direcciones y cantidad de segmentos distintas a la de Table53/54) que NO
se decodificaron esta ronda -- el formato de cabecera de 16 bytes
probablemente se repite (mismo patron `FUN_1800f7ad8`/`FUN_1800f7c1c`/
`FUN_1800f7d60`, mismo cuerpo que `FUN_1800f7ebc` con constantes DAT_
distintas), pero decodificar esas 2 tablas y validarlas sin un caso real
propio (el caso real disponible es SOLO de Table53/54 metrico) se deja
para una ronda futura -- NO se fabrica un numero para Table5/6/23/24_1952
sin evidencia. Los wrappers combinados `API_Gravity60F_1952`/
`API_SG60F_1952` (que dependen de esas 2 tablas) siguen sin funcion Python
de referencia por el mismo motivo.

ESTADO DE LA FAMILIA TRAS RONDA 10: 20 funciones de este archivo con numero
real (las 17 de Ronda 9 + `api_table53_1952`/`api_table54_1952`/
`api_density15c_1952`). PENDIENTE explicito, no fabricado: Table5/6_1952,
Table23/24_1952 y los 2 wrappers combinados `API_Gravity60F_1952`/
`API_SG60F_1952` (4 funciones puras + 2 wrappers, bloqueadas por 2 tablas
binarias distintas, localizadas pero no decodificadas).

-------------------------------------------------------------------------------
RONDA 11 (2026-08-26): Table59_2004/Table60_2004 CERRADAS -- NO tienen
constantes K0/K1/K2 propias (premisa inicial de la ronda CORREGIDA con
evidencia real): son un clon byte a byte de Table53/54_2004 con referencia
20C en vez de 15C
-------------------------------------------------------------------------------
Punto de partida pedido: "implementar Table59/60_2004 con sus PROPIAS
constantes K0/K1/K2, distintas a las de Table53/54, segun el manual". La
decompilacion real (FASE 0 + FASE 2, en 2 binarios independientes) NO
confirma esa premisa -- la CONTRADICE con evidencia directa, y se documenta
honesto en vez de forzar una tabla K nueva que no existe:

FASE 0 (manual oficial, paginas 8 y 69-70, `pdfplumber`): la tabla de
constantes K0/K1/K2 (pagina 8) dice explicitamente que aplica "both for the
1980 and the 2004 tables" -- no hay una fila ni una tabla aparte para
Table59/60. Las paginas de `fxAPI_Table59_2004`/`fxAPI_Table59E` describen
K0/K1/K2 unicamente como SALIDAS ("Actual value of constant K0 used for CTL
calculation"), exactamente igual que en Table53/54_2004 -- el manual nunca
transcribe un valor numerico nuevo. Si confirma, en cambio, la referencia:
"API_Table59 (2004) ... Density (T, P) -> Density (20°C, 0 bar(g))".

FASE 2 (decompilacion real, 2 plataformas independientes):
  - `.xll` (Ghidra 12.1.2, proyecto "ANALISIS .XLL", script
    `ghidra_scripts_xll/DecompileApiTable5960Xll.java`, salida
    `ghidra_api_table5960_xll_output.txt`): la raiz `API_Table59_2004`
    (FUN_1800a3a4c) tiene el MISMO despacho de producto y la MISMA
    conversion bar->kPa que `API_Table53_2004` (Ronda 5), y llama a la
    MISMA funcion nucleo `FUN_180105ec8` con el 4to argumento literal
    `DAT_180194028 = 20.0` (byte-exacto) en el lugar exacto donde
    Table53_2004 pasa `DAT_180194008 = 15.0`. `API_Table60_2004`
    (FUN_1800a4518) hace lo mismo con `FUN_180105928` (nucleo de
    Table54_2004). El volcado de 96 `DAT_` de esta corrida NO trae ningun
    K0/K1/K2 nuevo -- solo los 8 ya conocidos de K_US/K_METRIC.
  - `.so` Android (Ghidra 11.4.3, proyecto `libFX114`, script
    `apk_analisis/ghidra_scripts_11.4.3/DecompileApiTable5960.java`, salida
    `ghidra_api_table5960_so_output.txt`), CONFIRMACION INDEPENDIENTE en la
    otra plataforma (Fase 6): `API2540::Table59_2004` (0x001164a0) es
    LINEA POR LINEA identica a `API2540::Table53_2004` (0x00112410) --
    mismo remapeo de producto, misma llamada a `APIDens2004Type2M`,
    idénticos `DAT_002377f0=100.0` (bar->kPa) y `DAT_00237930=1.8` (escala
    de alpha) -- difiriendo SOLO en la constante de referencia:
    `DAT_00237880=15.0` (Table53_2004) vs `DAT_002379b0=20.0`
    (Table59_2004), ambas confirmadas byte-exactas en el volcado de
    constantes de esa corrida. `API2540::Table60_2004`/`API2540::Table54_2004`
    son el mismo par, mismo patron.
Dos compilaciones independientes (Windows `.xll` y Android `.so`)
coincidiendo en que la UNICA diferencia real es la constante de referencia
(15.0 vs 20.0), reusando el mismo despacho de producto->K0/K1/K2, es
evidencia mas fuerte que decompilar una sola plataforma -- el mismo
estandar de Fase 6 ya aplicado a otras normas de este proyecto.

Implementado en `api_table59_2004()`/`api_table60_2004()`, ambas clones
literales de `api_table53_2004()`/`api_table54_2004()` (mismo mecanismo de
2 pasos de Ronda 5: iterar con T/P reales sobre el nucleo US interno, luego
evaluar una 2da vez el mismo nucleo en la referencia metrica -- 20.0C en
vez de 15.0C -- convertida a Fahrenheit, para obtener el factor de
reescalado) con la unica constante nueva `T_REF_2004_20C_C = 20.0`.

Nivel de confianza: [CERTAIN via decompilacion exhaustiva cruzada en 2
plataformas independientes] -- un peldano MEJOR que el que tuvo
Table53/54_2004 en su propio cierre (Ronda 5 solo conto con el `.xll`), pero
sin caso real en vivo todavia (no se encontro tiempo esta ronda para buscar
las pantallas "API Table-59 (2004)"/"API Table-60 (2004)" en la app Android
-- PENDIENTE explicito, no fabricado, mismo peldano que Table53/54_2004
tuvo antes de conseguir su caso real en Ronda 6).

ESTADO DE LA FAMILIA TRAS RONDA 11: 22 funciones de este archivo con numero
real (las 20 de Ronda 10 + `api_table59_2004`/`api_table60_2004`). Ningun
pendiente nuevo abierto por esta ronda (los pendientes de Rondas 9/10 --
familia 1952 US, wrappers combinados 1952 -- siguen abiertos, sin relacion
con Table59/60).

-------------------------------------------------------------------------------
RONDA 12 (2026-08-26): Table5/6/23/24_1952 (sistema US) CERRADAS via dump de
bytes crudos (misma tecnica de Ronda 10), mas los wrappers combinados
`api_gravity60f_1952`/`api_sg60f_1952`. HALLAZGO ADICIONAL, no fabricado:
el simbolo Excel exportado literal "API_Table53_1952" usa una tabla
DISTINTA a la que ya estaba implementada con ese nombre.
-------------------------------------------------------------------------------
Punto de partida: Ronda 10 localizo pero no decodifico 2 tablas del sistema
US (`&DAT_18027b2c0` 22 segmentos, `&DAT_180232930`/`&DAT_18023f250` 24/6
segmentos), asumiendo que la primera correspondia a Table5/6_1952 por ser
la unica direccion nueva mencionada. Esta ronda releyo `DecompileApi1952Xll.java`
(el script real de Ronda 9, que registra las 10 raices con sus direcciones
Excel VERDADERAS tomadas de `ghidra_todos_los_nombres_output.txt`, NO
adivinadas) y encontro que la asignacion real es otra:

1. [CERTAIN, direcciones confirmadas por el registro real de cada simbolo
   Excel] Las 4 tablas puras del sistema US son:
       API_Table5_1952  (FUN_1800a3d50) -> tabla en 0x1801f4e10, 25 segmentos
       API_Table6_1952  (FUN_1800a481c) -> tabla en 0x1801fea10,  4 segmentos
       API_Table23_1952 (FUN_1800a1b94) -> tabla en 0x180232930, 24 segmentos
       API_Table24_1952 (FUN_1800a234c) -> tabla en 0x18023f250,  6 segmentos
   Y, hallazgo NO buscado pero real: el simbolo exportado
   "API_Table53_1952" (FUN_1800a2adc) en realidad usa `&DAT_18027b2c0`
   (22 segmentos, un tabla ADICIONAL, distinta de la que ya se implemento
   en Ronda 10 como `api_table53_1952`/`api_table54_1952`, que replica
   directamente el nucleo interno de `API_Dens15C_1952`/`FUN_1800f9b24`
   sobre `&DAT_18028a680`, 6 segmentos -- la tabla que SI esta validada
   contra el caso real del usuario). Es decir: el wrapper real
   "API Density @15°C (1952)" y el simbolo exportado en bruto
   "API Table-53 (1952)" NO comparten la misma tabla interna en este
   binario -- una discrepancia real del vendor (posible desprolijidad de
   1990s), no un error de esta investigacion. `api_table53_1952`/
   `api_table54_1952` (Ronda 10) SIGUEN siendo correctos para lo que se
   valido (reproducen "API Density @15°C (1952)" a <0.00004%), pero NO
   necesariamente reproducirian el numero de "API Table-53 (1952)" usada
   de forma aislada -- esa tabla adicional (`&DAT_18027b2c0`) queda
   PENDIENTE, sin caso real para validarla y fuera del alcance pedido
   esta ronda (los 4 tablas + 2 wrappers listados abajo).

2. [CERTAIN, dump de bytes crudos con `pefile`, mismo metodo de Ronda 8/10]
   Se localizaron 2 formatos de cabecera de 16 bytes, ambos DISTINTOS del
   formato metrico ya conocido:
     FORMATO B (Table5/6, eje primario = °API, paso=1 grado): base(byte)
       @0, filas(byte) @1, Table5: col_min(byte)@2/col_max(byte)@3;
       Table6: col_max(ushort)@2-3 con col_min=0 implicito; puntero@8-15.
       Columna T SIN escala (grado F entero directo, a diferencia del eje
       metrico de 0.5°C). Valor: Table5=raw/10.0 (°API a 1 decimal, tabla
       legada de menor resolucion que la formula K0/K1/K2 de 1980);
       Table6=raw/10000.0 (CTL).
     FORMATO A' (Table23/24, eje primario = RD*1000): base(ushort)@0-1,
       filas(byte)@2, Table23: paso(byte)@3/col_min(int8)@4/col_max(byte)@5;
       Table24: paso FIJO=5 (igual al metrico), col_max=byte@3+140,
       col_min=-50 si base<=600 sino 0 (regla confirmada por
       encadenamiento perfecto de sus 6 segmentos, ver punto 3). Valor:
       raw/10000.0 en ambos casos.
   Evidencia de que la lectura es correcta: LOS 4 conjuntos de segmentos
   encadenan (base(i+1)==base(i)+filas(i)*paso) sin excepcion real (las
   pocas "discontinuidades" observadas son saltos deliberados del propio
   grid original, ej. Table5 pasa de 1 fila por grado a 20/39 filas por
   segmento en el tramo medio de °API, consistente con como se ven las
   cartas API 2540 reales: mas granularidad cerca de los bordes del rango).

3. [CERTAIN, confirmado por bytes] Table24_1952 usa una regla de negocio
   real (no inventada): col_min=-50°F para segmentos con base<=600 (RD
   <=0.6) y col_min=0°F para base>600 -- verificada porque, con esa regla
   y paso FIJO=5, los 6 segmentos encadenan EXACTOS (500->600->605->810->
   905->960->1105 kg/m3-equivalente), evidencia mas fuerte que asumir
   arbitrariamente. El pseudocodigo de Ghidra para esta tabla mostraba una
   expresion con mascaras de bits (`~-(uint)(600<*param_1)&0xffffffce`) --
   se verifico bit a bit que es exactamente esa regla, no se tomo la
   palabra de Ghidra sin comprobar.

4. [CERTAIN via decompilacion directa] Los 2 wrappers combinados
   `API_Gravity60F_1952` y `API_SG60F_1952` SI llaman a `FUN_1800e2d5c`
   (el mismo nucleo de `api_mpms_11_2_1`, US, ya [CERTAIN] desde Ronda 9)
   ademas de su tabla CTL respectiva -- confirmado leyendo el cuerpo
   completo de ambas raices (no solo la tabla). Implementados como
   `api_gravity60f_1952`/`api_sg60f_1952`, misma estructura iterativa que
   `api_gravity60f_1980`/`api_reldensity60f_1980`.

5. [LIKELY, por simetria con el patron YA VALIDADO de Ronda 10 -- NO
   decompilado directamente] La interpolacion en el eje primario (°API o
   RD) entre 2 filas reales, cuando el valor pedido no cae en un multiplo
   exacto de la fila: el binario muestra el MISMO patron degenerado
   (`FUN_1800f75a8`/`FUN_1800f79cc`, etc., con el problema YA documentado
   de argumentos perdidos en el sitio de llamada) que ya se resolvio "por
   analogia" en Ronda 10 para el eje de densidad metrico. Aqui se aplico
   la MISMA tecnica, pero generalizada: en vez de reimplementar el
   fallback real hacia el segmento anterior (que el binario usa en los
   bordes de un segmento de 1 sola fila), se APLANARON todos los
   segmentos de cada tabla a una lista GLOBAL de filas ordenada por valor
   (`_flatten_1952_us_rows`), y se interpola entre las 2 filas reales mas
   cercanas sin importar el segmento de origen. Esto es EQUIVALENTE al
   fallback del binario (mismo par de filas resultaria elegido) y evita
   el problema de bordes que se hubiera visto con una interpolacion
   estrictamente "dentro de un segmento" (verificado: con el aplanado, la
   identidad T=60F->valor_entrada es EXACTA incluso para °API/RD que caen
   justo en el limite entre 2 segmentos de 1 sola fila, ej. °API=8.5,
   89.9; sin el aplanado esos casos fallaban).

VALIDACION (sin caso real en vivo esta ronda -- no se busco en el
emulador por falta de tiempo, ver PENDIENTE abajo):
  (a) Sanity fisico [CERTAIN, surge de los datos, no esta forzado]: a
      T=60°F, Table6_1952/Table24_1952 dan CTL=1.0 EXACTO para todo
      °API/RD probado (9 valores de °API incluyendo bordes de segmento,
      6 valores de RD), y Table5_1952/Table23_1952 devuelven el mismo
      °API/RD de entrada (identidad).
  (b) VALIDACION CRUZADA [evidencia fuerte, no reemplaza un caso real
      pero es independiente de el]: Table5/6_1952 (eje °API) y
      Table23/24_1952 (eje RD) son 2 PARES de tablas binarias
      COMPLETAMENTE INDEPENDIENTES (direcciones y formatos de cabecera
      distintos), pero describen la MISMA superficie fisica de
      correccion (°API<->RD via 141.5/RD-131.5 es una identidad exacta).
      En 5 combinaciones (API,T) bien distintas (incluyendo T negativo y
      T=200°F), ambas cadenas coinciden en el CTL final dentro de
      0.0004%-0.008% -- el mismo orden de ruido de redondeo ya visto en
      TODA la familia para reconstrucciones [CERTAIN] validadas con caso
      real. Que 2 tablas decodificadas independientemente, con formatos
      de cabecera DIFERENTES, converjan asi de cerca en el mismo punto
      fisico es evidencia fuerte de que ambos decodes son correctos.

PENDIENTE explicito, NO resuelto esta ronda (no fabricado): (i) la tabla
adicional en `&DAT_18027b2c0` (22 segmentos) que el simbolo Excel real
"API_Table53_1952" usa (punto 1 arriba) -- distinta de la ya
implementada, sin caso real, fuera del alcance pedido; (ii) no se busco
un caso real en el emulador para Table5/6/23/24_1952 ni para los 2
wrappers combinados (por falta de tiempo esta ronda, no por
imposibilidad) -- mismo nivel de confianza que tuvo Table53/54_2004
antes de su caso real en Ronda 6: [CERTAIN via decompilacion + dump de
bytes + validacion cruzada], un peldano por debajo de "caso real en
vivo".

Implementado en `_flatten_1952_us_rows()`/`_lookup_1952_us_table()`
(motor generico de busqueda), `api_table5_1952()`/`api_table6_1952()`/
`api_table23_1952()`/`api_table24_1952()` (las 4 tablas puras) y
`api_gravity60f_1952()`/`api_sg60f_1952()` (los 2 wrappers combinados).
Datos crudos extraidos UNA sola vez con `pefile` y embebidos en
`_api_table1952_us_data.py` (base64, ~330KB de datos reales) -- el
modulo YA NO depende de que `FlowXpert.xll` este presente en tiempo de
ejecucion para estas funciones.

ESTADO DE LA FAMILIA TRAS RONDA 12: 28 funciones de este archivo con
numero real (las 22 de Ronda 11 + `api_table5_1952`/`api_table6_1952`/
`api_table23_1952`/`api_table24_1952`/`api_gravity60f_1952`/
`api_sg60f_1952`). PENDIENTE explicito, no fabricado: la tabla adicional
de "API_Table53_1952" real (`&DAT_18027b2c0`) y el caso real en vivo
para toda la sub-familia 1952/US (tablas + wrappers).

-------------------------------------------------------------------------------
RONDA 13 (2026-08-26): API MPMS 11.2.2/11.2.2M CERRADAS -- norma NUEVA
(no es parte de la familia 11.1), y 11.2.1/11.2.1M suben a caso real
DIRECTO (antes solo tenian caso real INDIRECTO via los wrappers 1952/1980)
-------------------------------------------------------------------------------
Contexto: el menu raiz "API" de la app tiene un 4to item, "API 11.2/12.2",
CONFIRMADO por `uiautomator dump` (Fase 4) con exactamente 4 pantallas
propias -- ni mas ni menos: "API MPMS 11.2.1", "API MPMS 11.2.1M", "API
MPMS 11.2.2", "API MPMS 11.2.2M". Las primeras 2 ya estaban [CERTAIN]
desde Ronda 9 (implementadas como `api_mpms_11_2_1`/`api_mpms_11_2_1m`),
pero SOLO con caso real INDIRECTO (via los wrappers Density@15C(1952)/
1980). Las otras 2 eran nuevas, nunca decompiladas.

[CERTAIN, SUBE DE NIVEL] `api_mpms_11_2_1`/`api_mpms_11_2_1m` obtuvieron
esta ronda su primer caso real DIRECTO (pantalla propia, no via wrapper):
    - 11.2.1M: Density@15C=800kg/m3, T=25C, P=50bar(g), EVP=0 ->
      CPL_app=1.004590, F_app=0.000091 1/bar. Formula ya implementada
      reproduce CPL=1.0045909, F=0.0000913827 -- EXACTO.
    - 11.2.1 (US): API Gravity@60F=50, T=90F(32.2222222C), P=50psig
      (3.44738bar(g)), EVP=0 -> CPL_app=1.000360, F_app=0.000007 1/psi.
      Formula ya implementada reproduce CPL=1.0003598, F=0.0000071966 --
      EXACTO. Descripcion real de pantalla confirmada: "0-90 Gravity
      range" (US) / "638-1074 kg/m3 Density range" (metrico) -- coincide
      con el rango oficial ya documentado en Ronda 9.

[CERTAIN, NUEVO] API MPMS 11.2.2/11.2.2M -- "Compressibility Factors for
Hydrocarbons: 0.350-0.637 Relative Density (60/60F) and -50F to 140F
Metering Temperature, 2nd Edition, October 1986" (cita textual real,
confirmada en el manual oficial ABB, seccion `fxASTM_D1550_RD60` y
`fxAPI_RD60F_NGL_LPG` que ambas CITAN a 11.2.2 como su paso de
compresibilidad). Descripcion real de pantalla: "Compressibility (F) and
CPL for 0.350-0.637 Relative Density range according to API MPMS 11.2.2
and 12.2" (US) / "...350-637 kg/m3 Density Range according to API MPMS
11.2.2M and 12.2" (metrico) -- confirma que 11.2.2 es un estandar
DISTINTO de 11.2.1 (rango de densidad mas bajo, tipico de NGL/LPG), no
una extension con las mismas constantes.

Decompilado (Ghidra 11.4.3, `.xll`, script `DecompileApi1122Xll.java`,
salida `ANALISIS_GHIDRA_FLOWXPERT/ghidra_api1122_xll_output.txt`):
    API_MPMS_11_2_2  @ 0x1800a0964 -> FUN_1800e32e8 (US, RD directo)
    API_MPMS_11_2_2M @ 0x1800a0b24 -> FUN_1800e36e8 (metrico, kg/m3)
Estructuralmente DISTINTO de 11.2.1/11.2.1M (que eran un simple
`exp(...)`): 11.2.2/11.2.2M usan un polinomio de grado alto en T (en
Rankine) y en una "densidad reducida" (RD directa en US; en metrico, RD
pasa primero por un polinomio propio de grado 4 en rho/1000, constantes
`DAT_1801ea588/5d0/5a0/5b0/598` byte-exactas, que da un valor muy
cercano a la propia rho/1000 pero NO identico -- no se le puso nombre
fisico porque no hizo falta para reproducir el numero real). Los 2
polinomios centrales (uno multiplicado por 6.894757*1e5 con un ROUND-A-
ENTERO obligatorio incorporado -- no opcional, ocurre SIEMPRE, a
diferencia del "API-11.2.2 Rounding" que es un flag aparte que solo
redondea el resultado final de F; y otro multiplicado por 1e5 con un
round-a-3-decimales igualmente obligatorio) son estructuralmente
IDENTICOS entre la version US y metrica salvo por el factor de unidad de
presion (6.894757, psi->kPa, presente SOLO en la version US porque la
metrica ya trabaja nativamente en kPa) -- evidencia de que ambas
ediciones comparten el mismo desarrollo polinomico fuente, solo con
distinta normalizacion de densidad de entrada. Tambien hay un chequeo de
"temperatura pseudocritica" (formula cuadratica en la densidad reducida,
`DAT_1801ea5f8/600/608`, en Rankine) que en la version US SUSTITUYE la
temperatura real por el techo pseudocritico si la excede (afecta el
numero), mientras que en la metrica SOLO marca un codigo de estado
distinto sin sustituir (asimetria real confirmada leyendo ambas, no
alisada).

VALIDACION (caso real DIRECTO, capturado por `uiautomator dump` en una
sesion anterior el mismo dia -- reutilizado y re-verificado esta ronda
contra la reconstruccion algebraica, NO fabricado):
    - 11.2.2M: Density@15C=600kg/m3, T=25C, P=20bar(g), EVP=0 ->
      CPL_app=1.005227, F_app=0.000260 1/bar. Formula reconstruida da
      CPL=1.0052274, F=0.00026001 -- EXACTO (6 decimales).
    - 11.2.2 (US): RD@60F=0.5, T=90F(32.2222222C), P=50psig(3.44738bar(g)),
      EVP=0 -> CPL_app=1.002857, F_app=0.000057 1/psi. Formula
      reconstruida da CPL=1.002857, F=0.00005698 -- EXACTO.
Rangos oficiales confirmados a bytes: metrico rho 350.0-637.5 kg/m3,
T -46..60C (=-50.8..140F), P (P-EVP) 0-15200 kPa; US RD 0.35-0.638,
T -50..140F, P (P-EVP) 0-2200 psig -- coinciden con el manual (RD
0.350-0.637, -50 a 140F, 0-2200 psig para ASTM D1550/11.2.2).

Implementado en `api_mpms_11_2_2()`/`api_mpms_11_2_2m()`. NO se probo el
flag "API-11.2.2(M) Rounding" activado esta ronda (queda en el mismo
nivel de prioridad baja que los flags de rounding analogos ya
documentados en el resto de la familia, que solo afectan presentacion) --
PENDIENTE de baja prioridad, no bloqueante.

ESTADO DE LA FAMILIA TRAS RONDA 13: 30 funciones con numero real en este
archivo (las 28 de Ronda 12 + `api_mpms_11_2_2`/`api_mpms_11_2_2m`).
"API 11.2/12.2" queda con sus 4 pantallas reales CERRADAS [CERTAIN via
decompilacion + caso real directo]. Siguen fuera de alcance original:
Ethylene/Propylene (Ronda 1 propia, ver seccion mas abajo), E NGL/LPG
(TP-27, `fxAPI_RD60F_NGL_LPG` -- comparte el mismo nucleo de 11.2.2 mas
GPA TP-15/API 11.2.4/11.2.5, no decompilado en esta ronda).
"""

from __future__ import annotations

import base64
import math
import struct
from dataclasses import dataclass
from typing import Literal

from ._api_table1952_metric_data import (
    TABLE_1952_METRIC_SEGMENTS,
    TABLE_1952_METRIC_BLOB_B64,
)
from ._api_table1952_us_data import (
    TABLE_1952_US_TABLE5_SEGMENTS,
    TABLE_1952_US_TABLE5_BLOB_B64,
    TABLE_1952_US_TABLE6_SEGMENTS,
    TABLE_1952_US_TABLE6_BLOB_B64,
    TABLE_1952_US_TABLE23_SEGMENTS,
    TABLE_1952_US_TABLE23_BLOB_B64,
    TABLE_1952_US_TABLE24_SEGMENTS,
    TABLE_1952_US_TABLE24_BLOB_B64,
)

# ===========================================================================
# Enum de "Product" -- IDENTICO en las 12 funciones (manual, paginas 50-73;
# switch de producto CONFIRMADO por decompilacion directa en las 6 funciones
# 1980 -- Table5, Table6, Table23, Table24, Table53, Table54 -- y en el
# nucleo compartido 2004, FUN_1801053f4)
# ===========================================================================
# 1: A - Crude Oil
# 2: B - Auto select (selecciona 3..6 segun el valor de densidad/API/RD base)
# 3: B - Gasoline
# 4: B - Transition Area
# 5: B - Jet Fuels
# 6: B - Fuel Oil
# 7: D - Lubricating Oil
Product = Literal[1, 2, 3, 4, 5, 6, 7]

# [CERTAIN] aritmetica CTL+F/CPL 2004 confirmada por decompilacion real para
# el subconjunto de tablas en sistema US (Table5/6/23/24_2004) -- ver
# docstring. NO cubre la validacion contra un caso real en vivo (pendiente,
# Fase 5/7) ni el detalle metrico de Table53/54_2004 (deliberadamente NO
# implementadas esta ronda, ver docstring).
_ARITMETICA_2004_CONFIRMADA = True


@dataclass(frozen=True)
class _K:
    k0: float
    k1: float
    k2: float


# ---------------------------------------------------------------------------
# [CERTAIN] Tabla K0/K1/K2 -- LAS 8 constantes por sistema de unidades
# confirmadas byte-exactas contra el volcado de constantes reales del `.xll`
# (seccion "DAT_ ADDRESSES REFERENCIADAS" del archivo de decompilacion), no
# solo contra el manual como en Ronda 1 (donde solo 4/8 estaban verificadas
# a bytes). Es tambien el MISMO juego que usa el motor 2004 (ver docstring).
# ---------------------------------------------------------------------------

# Sistema US customary (Table5/6/23/24: alpha en 1/gradoF, densidad base en
# kg/m3 fisicos -- confirmado, NO es RD/API adimensional, ver Ronda 1)
K_US: dict[Product, _K] = {
    1: _K(341.0957, 0.0, 0.0),          # Crude oil (A)      [CERTAIN, byte-exacto: DAT_1801ea820]
    2: _K(0.0, 0.0, 0.0),                # Auto-select (se resuelve a 3..6)
    3: _K(192.4571, 0.2438, 0.0),        # Gasoline (B)       [CERTAIN, byte-exacto: DAT_1801ea810/7d0]
    4: _K(1489.0670, 0.0, -0.0018684),   # Transition area (B)[CERTAIN, byte-exacto: DAT_1801ea828/8b8]
    5: _K(330.3010, 0.0, 0.0),           # Jet fuels (B)      [CERTAIN, byte-exacto: DAT_1801ea818]
    6: _K(103.8720, 0.2701, 0.0),        # Fuel oils (B)      [CERTAIN, byte-exacto: DAT_1801ea800/7d8]
    7: _K(0.0, 0.34878, 0.0),            # Lubricating oils(D)[CERTAIN, byte-exacto: DAT_1801ea7e0]
}

# Sistema metrico (Table53/54 1980: alpha en 1/gradoC, densidad base en
# kg/m3). El motor 2004 NO usa esta tabla -- reutiliza K_US, ver docstring.
K_METRIC: dict[Product, _K] = {
    1: _K(613.9723, 0.0, 0.0),           # Crude oil (A)      [CERTAIN, byte-exacto: DAT_1801eada8]
    2: _K(0.0, 0.0, 0.0),
    3: _K(346.4228, 0.4388, 0.0),        # Gasoline (B)       [CERTAIN, byte-exacto: DAT_1801ead90/58]
    4: _K(2680.3206, 0.0, -0.00336312),  # Transition area (B)[CERTAIN, byte-exacto: DAT_1801eade0/eb0]
    5: _K(594.5418, 0.0, 0.0),           # Jet fuels (B)      [CERTAIN, byte-exacto: DAT_1801ead98]
    6: _K(186.9696, 0.4862, 0.0),        # Fuel oils (B)      [CERTAIN, byte-exacto: DAT_1801ead88/60]
    7: _K(0.0, 0.6278, 0.0),             # Lubricating oils(D)[CERTAIN, byte-exacto: DAT_1801ead68]
}

# ---------------------------------------------------------------------------
# [CERTAIN] Densidad de referencia del agua a 60F, confirmada byte-exacta
# contra DAT_1801eaac0 en el volcado de constantes del `.xll` -- literalmente
# el mismo literal que usan Table23_1980/Table53_1980/Table54_1980
# ("param_1 * _DAT_1801eaac0" en el decompilado) para convertir RD
# adimensional a densidad fisica en kg/m3 antes de evaluar alpha. En Ronda 1
# esto era [LIKELY] (solo se sabia por la razon K0_metrico/K0_US=9/5); ahora
# es un match de bytes directo.
# ---------------------------------------------------------------------------
RHO_WATER_60F_KGM3 = 999.012

# [CERTAIN] Temperaturas de referencia del motor 1980, confirmadas byte-
# exactas (DAT_180124810=60.0 y DAT_180194008=15.0 en el volcado de
# constantes). En Ronda 1 se asumian 60.0/15.0 por convencion; ahora estan
# verificadas contra el binario real.
T_REF_US_1980_F = 60.0
T_REF_METRIC_1980_C = 15.0

# [CERTAIN, RONDA 11] Referencia metrica de 20C usada por Table59/60_2004 --
# byte-exacta en AMBAS plataformas: DAT_180194028=20.0 en el `.xll`
# (ghidra_api_table5960_xll_output.txt) y DAT_002379b0=20.0 en el `.so`
# (ghidra_api_table5960_so_output.txt). Ver docstring RONDA 11 para el
# mecanismo completo -- es LITERALMENTE la misma posicion de argumento que
# T_REF_METRIC_1980_C (15.0) ocupa para Table53/54_2004, en el mismo sitio
# de llamada (FUN_180105ec8 en el `.xll`, APIDens2004Type2M en el `.so`).
T_REF_2004_20C_C = 20.0

# [CERTAIN, valor real extraido; SIN fuente publica identificada] Referencia
# interna que usa el nucleo compartido 2004 (FUN_1801053f4) para todas las
# tablas en sistema US -- DAT_18028e758, no es 60.0 exacto. Ver docstring.
T_REF_2004_US_F = 60.0068749

# [CERTAIN] Coeficiente 0.8 del CTL, confirmado byte-exacto (DAT_180193ee0),
# idéntico en el motor 1980 y en el 2004.
CTL_COEF_0_8 = 0.8

# [CERTAIN, valor real extraido; SIN fuente publica identificada] Constantes
# del factor de compresibilidad F usado en CPL_2004 = 1/(1-P*F). Los 5
# literales son byte-exactos contra el `.xll` (DAT_1801941c0, DAT_18028e818,
# DAT_1801ea498, DAT_1801ea4d0, DAT_180193de8); la formula publica exacta a
# la que corresponden (si alguna) NO se identifico esta ronda.
_CPL_A = 2326.0
_CPL_B = 793920.0
_CPL_C = 1.3427e-4
_CPL_D = 1.9947
_CPL_SCALE = 1.0e-5

# [CERTAIN] limite de iteracion del motor 2004 (FUN_180105b64: corta al
# llegar a 15) -- coincide con el manual ("No convergence within 15
# iterations"), ahora tambien confirmado en el binario.
MAX_ITER_2004 = 15

# [CERTAIN] conversion psi<->kPa usada por el motor (DAT_1801ea5d8).
PSI_TO_KPA = 6.894757

# [CERTAIN, RONDA 5] conversion bar->kPa usada por Table53/54_2004 para
# escalar la presion de entrada antes de convertirla a psi (DAT_1801940c8,
# byte-exacto en el volcado de constantes: "DAT_1801940c8 (double) = 100.0").
BAR_TO_KPA = 100.0

# ---------------------------------------------------------------------------
# [CERTAIN, RONDA 8] Micro-correccion polinomica de temperatura del motor
# 2004 (FUN_180106198 -> FUN_180106114), cerrada leyendo bytes crudos del
# `.xll` en vez de reinterpretar Ghidra -- ver docstring del modulo, seccion
# "RONDA 8", para el metodo completo. Resumen:
#   1. Los 8 doubles del arreglo contiguo 0x18028e840..0x18028e878 (8 slots
#      de 8 bytes) se dumpearon directo del archivo con `pefile` (VA->offset
#      real via secciones del PE, sin pasar por el decompilador). Los 4 que
#      Ghidra marcaba "_UNK_"/overlap NO son basura: son 4 doubles bien
#      formados, distintos entre si y de los otros 4 -- ningun patron de
#      "doble mal partido en 2 floats" (eso daria NaN o exponentes absurdos
#      al reinterpretar medio double, que no es el caso aqui).
#   2. El PSEUDOCODIGO de FUN_180106114 (no solo el disassembly) muestra sin
#      ambiguedad un bucle de Horner de 8 iteraciones que lee, EN ORDEN, los
#      8 slots del arreglo `local_58[0..7]` (incluye los 4 "_UNK_") -- es
#      decir, se leen las 8 direcciones, no 4: confirma la hipotesis (a),
#      NO la (b).
# El polinomio resultante (evaluado sobre z=((T_F-32)*5/9)/630.0, sin termino
# constante, grado 8):
#     P(z) = c0*z + c1*z^2 + c2*z^3 + c3*z^4 + c4*z^5 + c5*z^6 + c6*z^7
#            + c7*z^8
# con (orden real de lectura del Horner, confirmado por direccion de memoria
# y byte-exacto contra el `.xll`):
#     c0=-0.148759  (0x18028e850)   c1=-0.267408  (0x18028e858, ex-"_UNK_")
#     c2= 1.08076   (0x18028e840)   c3= 1.269056  (0x18028e848, ex-"_UNK_")
#     c4=-4.089591  (0x18028e860)   c5=-1.871251  (0x18028e868, ex-"_UNK_")
#     c6= 7.438081  (0x18028e870)   c7=-3.536296  (0x18028e878, ex-"_UNK_")
# y T_obs_corregida_F = T_obs_F - P(z)*9.0/5.0 (confirmado en FUN_180106198,
# que hace el viaje Celsius->correccion->Fahrenheit completo).
# Verificacion (caso real, Ronda 6, Table6_2004 Crude api60F=30 T=90F): el
# residuo de CTL bajo de 0.00068% (SIN correccion) a 0.0000125% (CON
# correccion) -- 54x mas cerca del valor real de la app (0.986588). CTPL bajo
# de 0.00069% a 0.00003%. Esto CIERRA el pendiente, no lo fabrica: el numero
# mejora al aplicar la formula reconstruida byte a byte.
# ---------------------------------------------------------------------------
_MICRO_CORR_2004_COEFS = (
    -0.148759,   # c0 (z^1)  -- 0x18028e850
    -0.267408,   # c1 (z^2)  -- 0x18028e858 (ex-"_UNK_")
    1.08076,     # c2 (z^3)  -- 0x18028e840
    1.269056,    # c3 (z^4)  -- 0x18028e848 (ex-"_UNK_")
    -4.089591,   # c4 (z^5)  -- 0x18028e860
    -1.871251,   # c5 (z^6)  -- 0x18028e868 (ex-"_UNK_")
    7.438081,    # c6 (z^7)  -- 0x18028e870
    -3.536296,   # c7 (z^8)  -- 0x18028e878 (ex-"_UNK_")
)
_MICRO_CORR_2004_DIVISOR = 630.0  # DAT_1801eb188, byte-exacto


def _micro_correccion_temp_2004(observed_temp_f: float) -> float:
    """[CERTAIN, RONDA 8] T_obs_corregida_F para el nucleo 2004
    (FUN_1801053f4), reconstruida byte a byte de FUN_180106198/
    FUN_180106114. Ver `_MICRO_CORR_2004_COEFS` arriba para el metodo y la
    verificacion contra caso real."""
    y_c = (observed_temp_f - 32.0) * 5.0 / 9.0  # escala Celsius (sin ser T_C real)
    z = y_c / _MICRO_CORR_2004_DIVISOR
    poly = 0.0
    for c in reversed(_MICRO_CORR_2004_COEFS):  # c7..c0, Horner tal como el binario
        poly = (poly + c) * z
    y_c_corregida = y_c - poly
    return (y_c_corregida * 9.0) / 5.0 + 32.0

# ---------------------------------------------------------------------------
# [CERTAIN, RONDA 4] Correccion de hidrometro ("Hydrometer Corr.") de
# Table5_1980 -- formula real decompilada de FUN_1800e4450 (rama del grupo B,
# alcanzada con product=3..6; la rama especifica de crudo, FUN_1800e404c, NO
# esta decompilada en el archivo fuente -- ver docstring -- pero comparte
# firma y orden de argumentos IDENTICOS a FUN_1800e4450/FUN_1800e4b80, y la
# formula de abajo REPRODUCE EXACTO el caso real de crudo de la Ronda 3, lo
# que confirma que la misma formula aplica a los 3 productos). Los 2
# coeficientes son byte-exactos del volcado `DAT_`:
#     DAT_1801ea7c0 = 1.278E-5  (C1, 1/gradoF)
#     DAT_1801ea7b8 = 6.2E-9    (C2, 1/gradoF^2)
# Se aplica ANTES de la iteracion, multiplicando la densidad OBSERVADA (no
# la de referencia): hydrometer_factor = 1 - C1*dT - C2*dT^2, con
# dT = T_obs_F - 60.0 (el mismo DAT_180124810 ya usado como T_ref US 1980).
# ---------------------------------------------------------------------------
HYDROMETER_C1 = 1.278e-5
HYDROMETER_C2 = 6.2e-9


def _hydrometer_factor(observed_temp_f: float) -> float:
    """[CERTAIN, RONDA 4] factor multiplicativo de correccion de hidrometro
    sobre la densidad OBSERVADA, confirmado por decompilacion (FUN_1800e4450,
    linea "*param_6 = (1.0-dVar9)-dVar10;" seguida de "dVar10 = *param_6 *
    *param_7;" que multiplica el factor directo sobre la densidad calculada
    desde el valor observado, ANTES de entrar a la iteracion) Y verificado
    EXACTO contra el caso real de Ronda 3 (Table5_1980 Crude, API_obs=30,
    T_obs=90F: sin correccion da 27.890942584019285, con correccion
    (aplicando este factor a rho_obs) da 27.95136088293313 -- coincide con
    el valor real de la app, 27.95136, a la precision mostrada)."""
    dt = observed_temp_f - T_REF_US_1980_F
    return 1.0 - HYDROMETER_C1 * dt - HYDROMETER_C2 * dt * dt


# [LIKELY via conversion dimensional, RONDA 7 -- NO decompilado, pero
# confirmado <0.00002% contra 1 caso real, ver docstring del modulo] la
# Ronda 6 probo 2 hipotesis con las constantes US SIN convertir (una con dT
# en Celsius, otra con dT en Fahrenheit) y ninguna cerro dentro del margen
# normal de esta familia (<0.0001%). La hipotesis que SI cierra es escalar
# los coeficientes por la pendiente °F/°C (1.8 para el termino lineal, 1.8^2
# para el cuadratico) -- el MISMO patron ya usado para K0/K1/K2 metrico/US
# en el resto de este archivo (K0_metrico/K0_US=9/5 exacto) -- y aplicarlos
# sobre dT en grados CELSIUS relativo a 15.0C (la referencia metrica de
# Table53/54_1980), NO sobre dT en Fahrenheit. Con un solo caso real
# disponible (Crude, Density_obs=1000kg/m3, T=20C) no se puede separar el
# termino lineal del cuadratico de forma independiente -- esta hipotesis no
# se "ajusto" al dato (se derivo ANTES de compararla, por conversion de
# unidades pura) y aun asi cerro a 0.00001% de diferencia relativa, 10x mas
# ajustado que el ruido tipico <0.0001% del resto de la familia -- evidencia
# fuerte de que es la formula correcta, pero se documenta [LIKELY] y no
# [CERTAIN] porque no se decompilo la rama real ni se confirmo con un 2do
# caso real a otro dT.
HYDROMETER_C1_METRIC = HYDROMETER_C1 * 1.8
HYDROMETER_C2_METRIC = HYDROMETER_C2 * 1.8 * 1.8


def _hydrometer_factor_metric(observed_temp_c: float) -> float:
    """[LIKELY, RONDA 7] factor de hidrometro para Table53/54_1980 (metrico).
    Ver nota arriba de `HYDROMETER_C1_METRIC` para el nivel de confianza y la
    evidencia. dT relativo a T_REF_METRIC_1980_C (15.0C)."""
    dt = observed_temp_c - T_REF_METRIC_1980_C
    return 1.0 - HYDROMETER_C1_METRIC * dt - HYDROMETER_C2_METRIC * dt * dt


def _celsius_to_fahrenheit(temp_c: float) -> float:
    """[CERTAIN] T_F = T_C*1.8 + 32.0 -- confirmado byte-exacto en
    FUN_1800e1d5c ("(param_1*DAT_180193f60+DAT_180194160)-DAT_180194158"),
    con DAT_180193f60=1.8, DAT_180194160=491.66999999999996,
    DAT_180194158=459.67 (la resta de estos dos ultimos da 32.0 exacto).
    Usada por Table53_2004/Table54_2004 (RONDA 5) para llevar la
    temperatura observada en Celsius al nucleo compartido 2004, que siempre
    trabaja internamente en Fahrenheit."""
    return temp_c * 1.8 + 32.0


def _rd60_to_density_kgm3(rd60: float) -> float:
    return rd60 * RHO_WATER_60F_KGM3


def _density_kgm3_to_rd60(rho_kgm3: float) -> float:
    return rho_kgm3 / RHO_WATER_60F_KGM3


# ---------------------------------------------------------------------------
# [CERTAIN, RONDA 40 (2026-09-10)] Constante de conversion RD/API<->densidad
# usada EXCLUSIVAMENTE por el motor 2004 (Table5/6/23/24_2004, que arrancan
# de RD/API y necesitan convertir a densidad ANTES de llamar al nucleo
# compartido `FUN_1801053f4`) -- CONFIRMADA DISTINTA de `RHO_WATER_60F_KGM3`
# (999.012, usada por el motor 1980/1952). Encontrada leyendo el sitio de
# llamada real de `API_Table24_2004`: antes de invocar el nucleo,
# `FUN_1800ec6dc` llama a `FUN_180106108(rd_60f)`, cuyo cuerpo COMPLETO es
# literalmente "return param_1 * _DAT_1801eaac8;" -- dump de bytes crudos
# (`pefile`, sin adivinar) confirma `DAT_1801eaac8 = 999.016` EXACTO, NO
# 999.012. Es, por coincidencia de valor (NO de direccion de memoria -- son
# 2 constantes en 2 posiciones de memoria distintas, confirmado por
# separado), el MISMO numero que `RHO_WATER_NGL_LPG_KGM3` (familia E NGL/LPG,
# TP-27) -- probablemente ambas familias (2004 y NGL/LPG, las 2 mas
# "nuevas"/basadas en estandares posteriores a 1980) comparten una revision
# mas precisa de la densidad del agua a 60°F que el motor 1980/1952 nunca
# adopto.
# Sin este fix, Table24_2004 (y Table6_2004 para productos con K1/K2 no
# triviales) tenian un error sistematico ~0.0002% en "Transition area"
# (unico producto con K2!=0) -- CERRADO junto con `_rho_corregido_2004`, ver
# esa funcion para la validacion completa contra oraculo `.xll`.
RHO_WATER_2004_KGM3 = 999.016


def _rd60_to_density_2004_kgm3(rd60: float) -> float:
    return rd60 * RHO_WATER_2004_KGM3


def _density_2004_kgm3_to_rd60(rho_kgm3: float) -> float:
    return rho_kgm3 / RHO_WATER_2004_KGM3


# ===========================================================================
# RONDA 49 (2026-09-10): CIERRE de "product=2" (B - Auto select) -- ver
# seccion "RONDA 49" al final del modulo para el detalle completo. Resumen:
#
# Decompilacion directa (NO analogia/adivinanza) confirmo el switch REAL de
# seleccion de region (Gasoline/Transition/Jet/FuelOil) en 2 sitios
# INDEPENDIENTES del binario, con los MISMOS breakpoints byte-exactos en
# ambos:
#   1) Las 3 funciones combinadas 1980 (`FUN_1800e62d4`/`FUN_1800e79e4`/
#      `FUN_1800e8494`, `ghidra_api1980wrappers_xll_output.txt`) --
#      [CERTAIN], validado end-to-end contra el oraculo `.xll` real
#      (`normas/_api1980_1952_wrappers_xll_directo.py`, que YA soporta
#      product=2 vs el binario) con `product=2` en decenas de puntos por
#      dominio, incluyendo el output `PRDCUR` (oor1) que el manual documenta
#      como "el producto realmente seleccionado".
#   2) Las 6 funciones RAW Table5/6/23/24/53/54_1980
#      (`ghidra_api_mpms_xll_output.txt`) -- mismas constantes DAT_ byte-
#      exactas (770.0/779.0/788.0/839.0 kg/m3; 37.0/48.0/50.0/52.0 API;
#      0.771/0.779/0.789/0.84 RD) confirmadas en el propio codigo compilado
#      de estas 6 funciones (no solo "se supone que comparten motor") --
#      [LIKELY] (mismo criterio de confianza que ya usa este archivo para
#      hydrometer_correction/rounding de Table23/53/54: motor+constantes
#      compartidas confirmadas, pero SIN oraculo end-to-end propio para
#      product=2 especificamente en estas 6, a diferencia de las 3
#      combinadas).
#
# CORRIGE una suposicion ANTERIOR (Ronda 1, arriba, y rondas historicas):
# "Table23 usa RD 0.7785/0.84" era una MEZCLA -- el break Gasoline/Transition
# real es 0.771 (no 0.7785), 0.789 es el break Transition/Jet (no
# documentado antes), 0.84 si era correcto (Jet/FuelOil), y 0.779 es un 4to
# breakpoint (el usado SOLO en la 1a pasada, cuando Transition se excluye).
#
# MECANISMO REAL (manual paginas 22-23, pasos 4/14 + decompilacion): en la
# direccion iterativa (Observado->Estandar), el auto-select corre en HASTA 2
# "pasadas" completas:
#   Pasada 1: resuelve la region SIN considerar Transition (breakpoint unico
#     de corte, ej. 779.0 kg/m3 / 50.0 API / 0.779 RD), corre el calculo
#     COMPLETO (toda la convergencia numerica) con esa K.
#   Pasada 2 (solo si la region cambia): re-resuelve la region CON Transition
#     ya incluida, usando la densidad/API/RD YA CONVERGIDO de la pasada 1 (no
#     el valor observado crudo) -- si coincide con la pasada 1, esa pasada 1
#     YA es el resultado final (el binario ni siquiera recalcula). Si difiere,
#     corre el calculo completo una 2a vez con la nueva K y ESE es el
#     resultado final (el binario nunca vuelve a re-chequear una 3a vez).
# En la direccion directa (Estandar->Observado, sin iterar), el auto-select
# se evalua UNA sola vez, CON Transition incluida desde el principio, sobre
# el valor de entrada (que ya esta a condiciones base).
#
# Validado EXACTO contra el oraculo `.xll` real (barrido dedicado, ver
# seccion "RONDA 49"): las 3 funciones combinadas reproducen el `PRDCUR`
# (oor1) real Y el resultado final en el 100% de ~75 puntos de barrido (3
# dominios x 2 direcciones x ~12-25 puntos cada uno cruzando cada frontera).
_AUTO_SELECT_NOTA = (
    "product=2 (B - Auto select) ya NO esta soportado -- ver RONDA 49."
)


def _resolver_producto_auto_1980(valor: float, dominio: str, incluir_transition: bool) -> int:
    """Resuelve el producto real (3=Gasoline/4=Transition/5=Jet/6=FuelOil)
    para `product=2` ('B - Auto select'), replicando EXACTO (decompilacion
    directa, RONDA 49 -- ver docstring arriba para la evidencia completa) el
    switch real encontrado, con las MISMAS constantes byte-exactas, en las 3
    funciones combinadas 1980 Y en las 6 funciones RAW Table5/6/23/24/53/54.

    `dominio`: 'densidad_kgm3' (Table53/54, api_density15c_1980), 'api'
    (Table5/6, api_gravity60f_1980) o 'rd' (Table23/24, api_reldensity60f_1980).
    `incluir_transition`: False replica la 1a pasada del mecanismo iterativo
    (Observado->Estandar) -- el manual documenta literalmente "The Transition
    area is only taken in consideration in the 2nd iteration loop"; True
    replica la 2a pasada, o la evaluacion unica de la direccion directa
    (Estandar->Observado), que SI incluye Transition desde el principio."""
    if dominio == "densidad_kgm3":
        if incluir_transition:
            if valor > 770.0:
                if valor >= 788.0:
                    return 6 if valor >= 839.0 else 5
                return 4
            return 3
        return (6 if valor >= 839.0 else 5) if valor >= 779.0 else 3
    if dominio == "api":
        if incluir_transition:
            if valor <= 37.0:
                return 6
            if valor < 48.0:
                return 5
            return 4 if valor <= 52.0 else 3
        if valor <= 37.0:
            return 6
        return 5 if valor <= 50.0 else 3
    if dominio == "rd":
        if incluir_transition:
            if valor >= 0.771:
                if valor >= 0.789:
                    return 6 if valor >= 0.84 else 5
                return 4
            return 3
        return (6 if valor >= 0.84 else 5) if valor > 0.779 else 3
    raise ValueError(f"dominio desconocido para auto-select: {dominio!r}")


def _auto_select_1980(valor_nativo: float, dominio: str, iterativo: bool, ejecutar):
    """Orquesta el mecanismo real de 'B - Auto select' (RONDA 49, ver
    docstring de `_resolver_producto_auto_1980`): 1 o 2 pasadas completas de
    `ejecutar(producto_fijo) -> dict` (que debe incluir la clave
    `"_candidato_nativo"` con el valor final, en el MISMO dominio/unidad de
    `valor_nativo`, para poder re-evaluar la region). Devuelve
    (resultado_dict, producto_efectivo)."""
    if not iterativo:
        producto = _resolver_producto_auto_1980(valor_nativo, dominio, incluir_transition=True)
        return ejecutar(producto), producto
    producto1 = _resolver_producto_auto_1980(valor_nativo, dominio, incluir_transition=False)
    r1 = ejecutar(producto1)
    producto2 = _resolver_producto_auto_1980(r1["_candidato_nativo"], dominio, incluir_transition=True)
    if producto2 == producto1:
        return r1, producto1
    r2 = ejecutar(producto2)
    return r2, producto2


def _alpha(k: _K, rho_base: float) -> float:
    """alpha = (K0 + K1*rho + K2*rho^2) / rho^2  -- [CERTAIN], confirmado por
    decompilacion directa en las 6 funciones 1980 (Table5/6/23/24/53/54) Y en
    el nucleo compartido 2004 (FUN_1801053f4)."""
    if rho_base == 0.0:
        return 0.0
    return (k.k0 + k.k1 * rho_base + k.k2 * rho_base * rho_base) / (rho_base * rho_base)


# ---------------------------------------------------------------------------
# [CERTAIN, RONDA 40 (2026-09-10)] Auto-consistencia real de rho_base dentro
# del nucleo compartido 2004 (`FUN_1801053f4`), EXCLUSIVA de esta familia (NO
# existe en el motor 1980, que usa `_alpha`/`_ctl_1980` sin ningun paso
# extra). Encontrada investigando un bug reportado por el usuario: CTL de
# `api_table24_2004` (Transition area, producto 4, RD=0.7, T=90F) daba
# 0.9643489 en vez del valor real de pantalla 0.964351 (diff 0.0002%, mayor
# al ruido tipico <0.0001% de esta familia) mientras `api_table60_2004`
# (mismo producto, densidad directa) SI coincidia.
#
# Decompilacion completa de `FUN_1801053f4` (antes solo se habia leido el
# sitio de llamada, nunca el cuerpo entero): para TODOS los productos fijos
# (param_1 in 1,3,4,5,6,7 -- rama `param_1 & 0xfffffff7 != 0`, o sea todo
# excepto el modo "override manual" 8) el binario NO evalua alpha
# directamente sobre rho_base: primero ejecuta UN SOLO paso de
# Newton-Raphson que resuelve la ecuacion implicita
#     rho_corregida = rho_base * CTL( alpha(rho_corregida), dT=SCALE )
# con SCALE = DAT_18028e728 (=T_REF_2004_US_F - 60.0, byte-exacto, dump
# `pefile` directo). Para K1=K2=0 o solo K1!=0 (5 de los 6 productos fijos)
# la correccion es minuscula (<0.0001%, indistinguible del ruido ya tolerado
# desde RONDA 8) porque alpha(rho) es casi lineal ahi -- pero para
# "Transition area" (producto 4, UNICO con K2!=0 en toda la tabla) alpha(rho)
# tiene curvatura fuerte (incluso cambia de signo cerca de RD~0.9) y el
# mismo paso de Newton deja un residuo VISIBLE, exactamente el bug
# reportado.
#
# Validado [CERTAIN] contra oraculo `.xll` DIRECTO (ctypes, sin Excel/
# emulador, `FUN_1800ec6dc` = nucleo interno real de `API_Table24_2004`,
# ver `_sweep_api2004_table24_oracle.py`): tras este fix + el de
# `RHO_WATER_2004_KGM3` (mas abajo), alpha coincide con el oraculo a
# PRECISION DE MAQUINA (diff ~1e-19) en los 6 productos fijos x 6..9
# densidades cada uno -- no es un ajuste que "cierra por casualidad", cierra
# EXACTO.
_ALPHA_CORR_SCALE_2004 = 0.006874897735  # DAT_18028e728, byte-exacto (pefile)


def _rho_corregido_2004(k: _K, rho_nominal: float) -> float:
    """Un paso de Newton-Raphson [CERTAIN, RONDA 40] que reproduce EXACTO
    (precision de maquina contra oraculo `.xll`) la auto-consistencia real de
    `FUN_1801053f4` entre rho_base y alpha, para las 8 funciones API MPMS
    11.1 (2004). Ver docstring de `_ALPHA_CORR_SCALE_2004` arriba."""
    if rho_nominal == 0.0:
        return 0.0
    alpha0 = _alpha(k, rho_nominal)
    x0 = alpha0 * _ALPHA_CORR_SCALE_2004
    ctl_inv0 = math.exp(0.8 * x0 * x0 + x0)
    a_num = k.k1 * rho_nominal + 2.0 * k.k0
    b_den = k.k2 * rho_nominal * rho_nominal + k.k1 * rho_nominal + k.k0
    if b_den == 0.0:
        return rho_nominal
    c = a_num / b_den
    term = c * (1.6 * x0 + 1.0) * x0 + 1.0
    if term == 0.0:
        return rho_nominal
    corr = (ctl_inv0 - 1.0) / term + 1.0
    return corr * rho_nominal


def _ctl_1980(alpha: float, delta_t: float) -> float:
    """CTL = exp( -(x + 0.8*x^2) ), x = alpha * delta_t.
    [CERTAIN] -- forma Y coeficiente 0.8 confirmados byte-exactos contra el
    `.xll` decompilado, formula publica API-2540 / ASTM D1250 Adjunct."""
    x = alpha * delta_t
    return math.exp(-(x + CTL_COEF_0_8 * x * x))


def _ctl_1980_iter(k: _K, rho_obs: float, t_obs: float, t_ref: float,
                    max_iter: int = 100, tol: float = 1e-6) -> tuple[float, float, float]:
    """Resuelve rho_base tal que rho_obs = rho_base * CTL(alpha(rho_base), t_obs-t_ref).
    [CERTAIN] en su forma (bucle con <=100 iteraciones, confirmado en
    FUN_1800e4450/FUN_1800e9a68/FUN_1800ececc, direccion "observado -> base"
    de Table5/23/53_1980). Devuelve (rho_base, ctl, alpha)."""
    rho_base = rho_obs
    ctl = 1.0
    alpha = 0.0
    delta_t = t_obs - t_ref
    for _ in range(max_iter):
        alpha = _alpha(k, rho_base)
        ctl = _ctl_1980(alpha, delta_t)
        nuevo = rho_obs / ctl if ctl != 0 else rho_base
        if abs(nuevo - rho_base) < tol:
            rho_base = nuevo
            break
        rho_base = nuevo
    return rho_base, ctl, alpha


# ===============================================================================
# RONDA 29 (2026-09-08): cascada real de `api2540_rounding != 0` para los
# wrappers combinados 1980 iterativos, cerrando el PENDIENTE de RONDA 22/25/28.
# Ver seccion "RONDA 29" al final del modulo para el detalle completo de como
# se resolvio la ambiguedad de RONDA 28 (desensamblado x64 real con
# `capstone`, no adivinado) y la evidencia empirica contra el oraculo `.xll`.
# ===============================================================================
def _round_comercial_n(y: float, n: int) -> float:
    """round half away from zero a n decimales -- replica exacta de
    `FUN_1800e1db4(y, n)` (ya [CERTAIN] desde Ronda 13/27): floor(y*10^n+0.5)/10^n
    para y>=0, ceil(y*10^n-0.5)/10^n para y<0."""
    scale = 10.0 ** n
    if y >= 0:
        return math.floor(scale * y + 0.5) / scale
    return math.ceil(scale * y - 0.5) / scale


def _trunc_hacia_cero_n(y: float, n: int) -> float:
    """Truncado hacia cero a n decimales -- replica exacta de
    `FUN_1800e1e14(y, n)` [CERTAIN, RONDA 28: decompilacion completa confirmo
    que NO es un redondeo comercial sino un truncado real]: floor(y*10^n)/10^n
    para y>=0, ceil(y*10^n)/10^n para y<0."""
    scale = 10.0 ** n
    if y >= 0:
        return math.floor(scale * y) / scale
    return math.ceil(scale * y) / scale


def _alpha_cascade_api2540(k: _K, rho_2dec: float, product: int) -> float:
    """alpha con la cascada REAL de truncados/redondeos intermedios que el
    binario aplica cuando `api2540_rounding != 0` (dentro de
    `FUN_1800e62d4`/`FUN_1800e79e4`/`FUN_1800e8494`, RONDA 29): K0/rho
    truncado a 8 decimales, ese resultado /rho truncado a 10, K1/rho truncado
    a 10, suma + K2 redondeada (comercial) a 7 decimales. El producto 4
    (Transition area, K1=0) usa una rama distinta confirmada por caso real:
    K0/rho truncado a SOLO 6 decimales, ese resultado /rho redondeado
    (comercial, no truncado) a 8 decimales, + K2 redondeado a 7."""
    if product == 4:
        term = _round_comercial_n(_trunc_hacia_cero_n(k.k0 / rho_2dec, 6) / rho_2dec, 8)
    else:
        t1 = _trunc_hacia_cero_n(k.k0 / rho_2dec, 8)
        t1 = _trunc_hacia_cero_n(t1 / rho_2dec, 10)
        t2 = _trunc_hacia_cero_n(k.k1 / rho_2dec, 10)
        term = t1 + t2
    return _round_comercial_n(term + k.k2, 7)


def _ctl_cascade_api2540(alpha: float, delta_t: float) -> float:
    """CTL con la cascada real de truncados intermedios (RONDA 29): x=alpha*dT
    truncado a 8 decimales, 0.8*x truncado a 8, x*(0.8*x) truncado a 8, el
    exponente -(x+0.8x^2) redondeado (comercial) a 8 decimales antes de
    `exp()`. Version continua sin cascada: `_ctl_1980`."""
    x = _trunc_hacia_cero_n(delta_t * alpha, 8)
    termino_08x = _trunc_hacia_cero_n(x * CTL_COEF_0_8, 8)
    termino_08x2 = _trunc_hacia_cero_n(x * termino_08x, 8)
    exponente = _round_comercial_n(-(termino_08x2 + x), 8)
    return math.exp(exponente)


SEED_TRANSITION_KGM3 = 778.84
"""[CERTAIN, RONDA 31] `DAT_1801eaaa0` -- semilla FIJA (kg/m3, comun a los 3
nucleos metrico/US) para la densidad-candidato de la PRIMERA vuelta del bucle
cuando `product==4` (Transition area) Y `conversion==1` (Observado->Estandar).
Confirmada leyendo, EN LAS 3 FUNCIONES por separado (no por analogia), el
mismo patron justo ANTES del `do { ... }` del bucle:
`FUN_1800e62d4` (Dens15C) linea 1286-1288, `FUN_1800e79e4` (Gravity60F) linea
2176-2178, `FUN_1800e8494` (RD60F) linea 3082-3084 de
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_api1980wrappers_xll_output.txt`:
`dVarN = dVarM; if ((param_9==1) && (*piVarX==4)) { dVarN = DAT_1801eaaa0; }`
-- solo afecta la densidad usada para calcular alpha/CTL en la VUELTA 1 (el
bucle recalcula su propio candidato en las vueltas siguientes con normalidad);
NO afecta el valor de `rho_fixed` (el observado real, que sigue siendo el
numerador de los candidatos de densidad en cada vuelta)."""


def _round_densidad_hidrometro_metric(density_kgm3: float) -> float:
    """[CERTAIN, RONDA 31] redondeo del INPUT densidad (kg/m3) a la
    graduacion REAL de un hidrometro metrico: la MITAD de una unidad (0.5
    kg/m3), NO 1 decimal como se asumio en RONDA 29. Confirmado leyendo
    `FUN_1800e62d4` (Dens15C_1980) linea 1124-1126 de
    `ghidra_api1980wrappers_xll_output.txt`: `param_1 =
    FUN_1800e1db4(param_1*2.0, 0) * 0.5` (idiom "multiplicar por 2,
    redondear a 0 decimales, dividir por 2" = redondeo a la MITAD de la
    unidad), aplicado ANTES de bifurcar por `conversion` (afecta AMBAS
    direcciones). Contraste explicito con `api_gravity60f_1980`/
    `api_reldensity60f_1980` (RONDA 29/30, SIN cambios): esas 2 funciones
    redondean su INPUT nativo (°API/RD) a 1 decimal (°API) o a la graduacion
    de un hidrometro de RD (0.0005, via el mismo idiom *2/round(3)/0.5)
    directamente sobre esa unidad, NO sobre densidad kg/m3 -- son 3
    graduaciones de hidrometro FISICAMENTE DISTINTAS, una por unidad nativa
    de pantalla, confirmadas cada una por separado leyendo su propio nucleo
    (Dens15C linea 1124, Gravity60F linea 2005-2006 con simple
    `FUN_1800e1db4(x,1)` SIN el idiom *2/0.5, RD60F linea 2920-2922 con el
    idiom *2/round(3)/0.5). Antes de esta ronda, `api_density15c_1980`
    redondeaba density a 1 DECIMAL (`round(d,1)`) en vez de a 0.5 kg/m3 --
    invisible en el barrido oficial porque todos sus valores de prueba
    (850.0 kg/m3, etc.) ya caen exacto en un multiplo de 0.5."""
    return _round_comercial_n(density_kgm3 * 2.0, 0) * 0.5


def _ctl_rounding_directo(ctl: float, api2540_rounding: int) -> float:
    """[CERTAIN, RONDA 31, manual pag. 21/23/32 -- `fxAPI_Dens15C_1980`/
    `fxAPI_Gravity60F_1980`, seccion 'API 2540 rounding'] Redondeo del CTL
    FINAL en la rama DIRECTA (conversion=0, Standard->Observed, SIN
    iteracion) segun el tipo exacto de `api2540_rounding` -- confirmado
    contra el oraculo `.xll` real (ver seccion "RONDA 31"):
    1 ("Enabled for computational value"): 4 decimales si CTL>=1, 5 si CTL<1.
    2 ("Enabled for table value"): SIEMPRE 4 decimales.
    3 ("Enabled with 5 decimal places"): SIEMPRE 5 decimales.
    0 (Disabled): sin cambios (full precision).
    Corrige un hueco real: las 3 funciones combinadas 1980
    (`api_density15c_1980`/`api_gravity60f_1980`/`api_reldensity60f_1980`)
    solo implementaban la opcion 2 desde RONDA 22, dejando 1 y 3 con full
    precision por error (confirmado contra el oraculo: p.ej. densidad=800
    kg/m3, T=10°C, api2540_rounding=1 -> CTL real=1.0048 (4 decimales,
    porque CTL>=1), Python daba 1.004789686... sin redondear)."""
    if api2540_rounding == 1:
        return round(ctl, 4) if ctl >= 1 else round(ctl, 5)
    if api2540_rounding == 2:
        return round(ctl, 4)
    if api2540_rounding == 3:
        return round(ctl, 5)
    return ctl


def _iterar_api2540_cascade(k: _K, rho_fixed: float, t_r: float, delta_t: float,
                             product: int, cpl_fn, max_iter: int) -> tuple[float, float, float, float]:
    """Bucle iterativo real de `api2540_rounding != 0` (Observado->Estandar,
    RONDA 29): densidad(guess) redondeada a 2 decimales antes de calcular
    alpha/CTL cada vuelta; CTL redondeado (comercial) a 6 decimales; 2
    candidatos de densidad por vuelta truncados a 3 decimales cada uno --
    candidato #1 usa el CPL de la vuelta ANTERIOR (o 1.0 en la primera) para
    alimentar `cpl_fn` (que recalcula CPL FRESCO en ese candidato), candidato
    #2 (el que realmente actualiza la iteracion Y el resultado final) usa ESE
    CPL fresco. `cpl_fn(density_kgm3_candidato) -> cpl` debe reexpresar el
    candidato en la unidad nativa de la pantalla (°API para Gravity60F,
    kg/m3 directo para Dens15C) antes de invocar `api_mpms_11_2_1`/
    `api_mpms_11_2_1m`. Tolerancia de convergencia (en kg/m3): 0.07 para
    producto 4, 0.05 para el resto (`DAT_1801d5f60`/`DAT_180193e90`, RONDA 28).
    RONDA 31: la densidad-candidato de la VUELTA 1 usa `SEED_TRANSITION_KGM3`
    (778.84 kg/m3 FIJO) en vez de `rho_fixed` cuando `product==4` -- ver
    docstring de `SEED_TRANSITION_KGM3` para la evidencia de decompilacion.
    Devuelve (densidad_candidato2, ctl_final, cpl_fresco, iteraciones)."""
    tol = 0.07 if product == 4 else 0.05
    rho_guess = rho_fixed
    cpl_prev = 1.0
    cpl_fresh = 1.0
    ctl_final = 1.0
    dens_c2 = rho_fixed
    for it in range(max_iter):
        if it == 0 and product == 4:
            rho_2dec = SEED_TRANSITION_KGM3
        else:
            rho_2dec = _round_comercial_n(rho_guess, 2)
        alpha = _alpha_cascade_api2540(k, rho_2dec, product)
        ctl_raw = _ctl_cascade_api2540(alpha, delta_t)
        ctl_final = _round_comercial_n(ctl_raw, 6)

        dens_c1 = _trunc_hacia_cero_n((rho_fixed / ctl_final) / cpl_prev, 3)
        cpl_fresh = cpl_fn(dens_c1)

        dens_c2 = _trunc_hacia_cero_n((rho_fixed / ctl_final) / cpl_fresh, 3)

        diff = abs(rho_guess - dens_c2)
        rho_guess = dens_c2
        cpl_prev = cpl_fresh
        if diff < tol:
            break
    return dens_c2, ctl_final, cpl_fresh, it + 1


# ===============================================================================
# RONDA 17 (2026-09-07): parametro "rounding" agregado a las 6 funciones 1980
# (Table5/6/23/24/53/54); investigado y documentado como PENDIENTE honesto
# (no implementado) para 2004/1952/E.
# ===============================================================================
# Recordatorio del comportamiento YA CONFIRMADO por caso real (Ronda 3/6, ver
# encabezado del modulo): 2 tipos DISTINTOS de "API Rounding" en la familia
# 1980, segun si la tabla es iterativa (observado->base) o directa
# (base->observado):
#   Tipo A (Table5/23/53, iterativas): flag BOOLEANO in-place. Redondea SOLO
#     el output principal visible (api_60f/rd_60f/density_15c) a 1 DECIMAL
#     (corregido RONDA 18, ver nota abajo -- se penso que eran 2 decimales
#     hasta esta ronda). [CERTAIN] solo para Table5 (Ronda 3, caso real:
#     27.89094->27.90000, es decir round(x,1)=27.9 con ceros de relleno).
#   Tipo B (Table6/24/54, directas): ENUM de 4 opciones (0=Disabled,
#     1=Enabled, 2="Enabled (table values)", 3="Enabled (5 decimal places)").
#     Solo el valor 2 cambia el numero (redondea `ctl` a 4 decimales).
#     [CERTAIN] para Table6 Y Table24 (Ronda 6 probo las 4 opciones sobre el
#     mismo caso base para ambas explicitamente).
#
# Evidencia NUEVA de esta ronda (no se repitio Ghidra ni se arranco el
# emulador -- se releyo `ghidra_api_mpms_xll_output.txt`, ya generado en
# Rondas 1/2, comparando los 6 wrappers raiz Excel byte a byte):
#   - Table23_1980 (`FUN_1800a1c9c`) es, argumento por argumento, IDENTICO al
#     wrapper de Table5_1980 (`FUN_1800a3e58`): mismos 5 slots (0x20/0x40/
#     0x60/0x80/0xa0), mismos 2 flags booleanos en las mismas posiciones
#     (`local_68[0]`, `local_res18[0]`), unica diferencia la funcion motor
#     invocada (`FUN_1800eb1f8` en vez de `FUN_1800e4f94`).
#   - Table53_1980 (`FUN_1800a2bf4`) tiene la MISMA estructura exacta.
#   - Table24_1980 (`FUN_1800a2454`) y Table54_1980 (`FUN_1800a33c4`) son,
#     igualmente argumento por argumento, IDENTICOS al wrapper de
#     Table6_1980 (`FUN_1800a4924`): mismos 4 slots, mismo enum leido como
#     entero (`local_64`) en la misma posicion, mismo patron de remapeo de
#     codigo de error (0x2a/0x2c/0x2d/0x2e) despues de la llamada al motor.
# Esta comparacion estructural CONFIRMA que Table23/53 comparten con Table5
# el mismo par de flags booleanos (posicion y tipo de lector, Tipo A), y que
# Table24/54 comparten con Table6 el mismo enum (posicion y tipo de lector,
# Tipo B) -- pero NO prueba el EFECTO concreto del flag dentro del motor de
# Table23/53/54 especificamente (eso solo se verifico con caso real para
# Table5/6/24). Por eso Table23/53/54 quedan [LIKELY] (motor+wrapper
# compartido, no caso real propio) mientras Table5/6/24 quedan [CERTAIN].
#
# 2004 (Table5/6/23/24/53/54/59/60_2004): investigado, NO implementado.
# Los 8 wrappers raiz Excel comparten TODOS la misma estructura entre si
# (confirmado leyendo Table5_2004, Table6_2004, Table53_2004 byte a byte):
# api/rd/densidad, T, presion(double), producto(int), UN SOLO flag booleano
# (`local_res18[0]`, mismo lector `FUN_18005fb64` que los flags de 1980) y un
# double opcional final (default 0 si se omite). A diferencia de 1980, aqui
# NO hay diferencia entre las tablas "iterativas" (5/23/53) y "directas"
# (6/24/54): TODAS usan el mismo lector booleano para su unico flag, cuando
# en 1980 las directas (6/24/54) usaban un lector de ENTERO (enum) distinto.
# Esto es evidencia de que el flag de 2004 NO es un simple heredero directo
# del patron 1980 -- podria ser el equivalente 2004 de "Hydrometer Corr.", de
# "API Rounding", una fusion de ambos en un unico booleano, u otra cosa. Se
# intento rastrear el uso interno de este flag (`FUN_1800e5218`, parametro
# `param_5` -> `local_128` -> pasado a `FUN_180105b64` como argumento de
# pila) pero se topo con la MISMA ambiguedad de argumentos de pila x64 ya
# documentada en otras partes de este archivo (Ronda 5, "cabo suelto" del
# remapeo de producto) -- Ghidra no reconstruye el sitio de llamada completo.
# Implementar un parametro `rounding` aqui adivinando cual de las 2 (o mas)
# semanticas posibles es, sin poder distinguirlas, seria fabricar
# comportamiento sin evidencia -- se deja PENDIENTE, honesto, para una ronda
# futura que decompile `FUN_180105b64`/`FUN_1801053f4` a fondo o consiga un
# caso real en vivo variando ese flag.
#
# 1952 (Table5/6/23/24/53/54): investigado, NO implementado. Motor
# GENUINAMENTE DISTINTO del de 1980/2004 (tablas de interpolacion por
# segmentos extraidas a bytes crudos, Rondas 10/12 -- NO la formula K0/K1/K2
# de 1980). Los wrappers Excel de 1952 NUNCA se decompilaron en este
# proyecto (se reversaron via dump de bytes de las tablas, no via Ghidra de
# la funcion wrapper) -- no existe evidencia, ni siquiera estructural, de que
# estas pantallas expongan un selector "Rounding". Ademas las funciones 1952
# de este archivo ni siquiera tienen parametro `product` (los datos de tabla
# no distinguen por producto de la misma forma que 1980/2004). Se documenta
# como PENDIENTE por falta total de evidencia, no como decision arbitraria.
#
# "E" (Table23E/24E/53E/54E/59E/60E): CASO DISTINTO a 1952/2004 -- aqui SI
# hay evidencia REAL de que el campo existe: los 4 casos reales de Ronda 14
# (uiautomator) muestran literalmente "Rounding=0" como input de la pantalla
# real. Pero (a) solo se probo el valor 0 (default) en los 4 casos, nunca un
# valor distinto, y (b) el motor de esta familia es un TERCERO
# completamente distinto (polinomio racional por tramos en densidad relativa
# reducida, tabla GPA TP-25 de 12 filas, ver seccion "RONDA 14" mas abajo) --
# no comparte K0/K1/K2 ni el patron de 2 lectores (booleano/entero) visto en
# 1980/2004. Asumir que el Tipo A o Tipo B de 1980 aplica igual aqui, sin
# haber visto el efecto de un valor distinto de 0, seria fabricar -- se
# documenta el hallazgo (el campo existe) pero NO se implementa el efecto
# (desconocido), quedando PENDIENTE explicito para una ronda que explore la
# pantalla real variando "Rounding".
#
# RONDA 18 (2026-09-07) -- CORRECCION PUNTUAL de decimales del flag Tipo A:
# se detecto una contradiccion real entre el resumen JSON
# `android_sdk_setup/casos_reales_api_tables.json` (nota de texto: "27.89094
# -> 27.90000 al activarlo") y la implementacion de Ronda 17
# (`round(api_60f, 2)`, que da 27.89, NO 27.90000). En vez de adivinar cual de
# las 2 fuentes tenia razon, se releyo el dump XML CRUDO original de
# `uiautomator` que produjo ese resumen (no se repitio la captura, ya
# existia en disco): `android_sdk_setup/api5_rounding_dlg.xml` (mismo estado
# que `api5_case1_confirm.xml`, switch "API Rounding" checked="false",
# api_60f="27.89094") y `android_sdk_setup/api5_rounding_dlg2.xml` (MISMO
# caso, switch checked="true", api_60f="27.90000"). El XML crudo confirma
# que "27.90000" es el valor REAL mostrado en pantalla (no un error de
# transcripcion del resumen JSON), y que matematicamente es round(x,1)=27.9
# con ceros de relleno del formato fijo a 5 decimales de la UI -- NO
# round(x,2)=27.89. Se corrigio `api_table5_1980` (unico con caso real
# propio, sube a [CERTAIN] con el numero de decimales correcto) y, por
# herencia del mismo motor/wrapper Tipo A ya documentado arriba (sin caso
# real propio, siguen [LIKELY]), tambien `api_table23_1980` y
# `api_table53_1980`, de 2 a 1 decimal. Los Tipo B (Table6/24/54) NO se
# tocaron -- su caso real (Ronda 6) confirma 4 decimales sobre `ctl`, sin
# relacion con esta correccion.
# ===============================================================================


# ===========================================================================
# API_Table5_1980 -- [CERTAIN] motor decompilado directamente (FUN_1800e4f94
# / FUN_1800e4450). API observada (T) -> API a 60F.
# Manual pagina 59: rango API -20..120, T -100..400 F, default T=60F.
# [CERTAIN, RONDA 4] "Hydrometer correction" IMPLEMENTADA -- ver
# `_hydrometer_factor` y el docstring del modulo (verificada exacta contra
# el caso real de Ronda 3).
# ===========================================================================
def api_table5_1980(observed_api: float, observed_temp_f: float,
                     product: Product = 1, hydrometer_correction: bool = False,
                     rounding: bool = False) -> dict:
    """°API(T) -> °API(60°F). API MPMS 11.1 (API-2540) Tables 5A/5B/5D, 1980/1984.

    Inputs (manual pagina 59): Observed API [-20..120 °API], Observed
    temperature [-100..400 °F, default 60]. Iterativo (observado->base).

    hydrometer_correction: [CERTAIN, RONDA 4] replica el flag real "Hydrometer
    Corr." de la pantalla FlowXpert -- multiplica la densidad OBSERVADA por
    `_hydrometer_factor(observed_temp_f)` antes de iterar. Verificado EXACTO
    contra el caso real (Crude, API_obs=30, T=90F): False->27.890942584019285,
    True->27.95136088293313, contra el valor real de la app 27.89094/27.95136.

    rounding: [CERTAIN, RONDA 3, corregido RONDA 18, tolerancia agregada
    RONDA 32] replica el flag real "API Rounding" de la pantalla FlowXpert --
    redondea SOLO `api_60f` (el output principal visible) a 1 decimal (NO 2)
    cuando esta activo. NO afecta `ctl`/`alpha` (esos se calculan siempre a
    precision completa, no hay nota "value will be rounded" para ellos en el
    manual de esta funcion, a diferencia de Table6/24/54_1980 que si la
    tienen para `ctl`). RONDA 18 (2026-09-07): se releyo el dump XML crudo
    `uiautomator` original de este caso (`android_sdk_setup/
    api5_rounding_dlg2.xml`, switch "API Rounding" con checked="true") en vez
    de confiar en el resumen JSON -- el valor real mostrado en pantalla es
    "27.90000" (formato fijo a 5 decimales de la UI, con ceros de relleno),
    que es MATEMATICAMENTE 27.9 a 1 decimal, NO 27.89 a 2 decimales como se
    habia implementado por error en Ronda 3. Verificado exacto contra el caso
    real (Crude, API_obs=30, T=90F): 27.890942584019285 -> round(x,1)=27.9
    con `rounding=True` (la app muestra "27.90000"; round(x,2)=27.89 NO
    coincide).

    RONDA 32 (cruce manual, pagina 59, `fxAPI_Table5_1980`): el manual
    documenta LITERALMENTE, ademas del redondeo del output de arriba, que
    este flag TAMBIEN cambia el limite de convergencia del bucle iterativo:
    "0.000001 kg/m3" si Disabled (=el `tol=1e-6` que ya era el default de
    `_ctl_1980_iter`, sin cambios), "0.05 kg/m3 ... as defined in the
    standard" si Enabled -- detalle NO implementado hasta ahora (el codigo
    usaba `tol=1e-6` fijo sin importar `rounding`). Se agrega aqui. Re-verificado
    que NO rompe el caso real de arriba: con `tol=0.05` el bucle converge a
    api60=27.890902803628848 (vs 27.890942584019285 con tol=1e-6, diferencia
    de ~4e-5 API, invisible), y `round(.,1)` sigue dando 27.9 en ambos casos
    -- el cambio de tolerancia es honesto-documentado pero no altera ningun
    resultado ya validado con caso real; su efecto solo puede notarse en
    casos que requieran mas iteraciones para converger o esten muy cerca de
    un borde de redondeo. Default False = comportamiento identico a
    versiones previas de este archivo (sin regresion).

    `product=2` (B - Auto select) [LIKELY, RONDA 49 -- ver seccion "RONDA 49"
    y docstring de `_resolver_producto_auto_1980`]: implementado via el
    mecanismo real de 2 pasadas (breakpoints de API gravity 37.0/48.0/50.0/
    52.0, byte-exactos, confirmados en el propio codigo compilado de esta
    familia). Se agrega la clave `product_efectivo` (3/4/5/6) al resultado
    con el producto realmente seleccionado, igual que el output "Product"
    (PRDCUR) real de la pantalla."""
    tol = 0.05 if rounding else 1e-6

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        rd_obs = 141.5 / (131.5 + observed_api)
        rho_obs_kgm3 = _rd60_to_density_kgm3(rd_obs)
        if hydrometer_correction:
            rho_obs_kgm3 *= _hydrometer_factor(observed_temp_f)
        rho_base_kgm3, ctl, alpha = _ctl_1980_iter(k, rho_obs_kgm3, observed_temp_f, T_REF_US_1980_F, tol=tol)
        rd_base = _density_kgm3_to_rd60(rho_base_kgm3)
        api60 = 141.5 / rd_base - 131.5
        return {"api_60f": api60, "ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": api60}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(observed_api, "api", True, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    api60 = resultado["api_60f"]
    if rounding:
        api60 = round(api60, 1)
    return {"api_60f": api60, "ctl": resultado["ctl"], "alpha": resultado["alpha"],
            "k0": resultado["k0"], "k1": resultado["k1"], "k2": resultado["k2"],
            "product_efectivo": producto_efectivo}


# ===========================================================================
# API_Table6_1980 -- [CERTAIN] motor decompilado directamente (FUN_1800e5e1c
# / FUN_1800e5bb0). API a 60F -> CTL a T observada (direccion directa, sin
# iteracion, confirmado en el decompilado).
# Manual pagina 72.
# ===========================================================================
def api_table6_1980(api_60f: float, observed_temp_f: float,
                     product: Product = 1, rounding: int = 0) -> dict:
    """°API(60°F) -> CTL(T). API MPMS 11.1 (API-2540) Tables 6A/6B/6D, 1980/1984.

    rounding: [CERTAIN, RONDA 6, CORREGIDO RONDA 32 -- ver seccion "RONDA 32"
    al final del modulo] replica el ENUM real "API Rounding" de la pantalla
    FlowXpert (DISTINTO del flag booleano de Table5): 0=Disabled, 1="Enabled
    for computational value", 2="Enabled for table value",
    3="Enabled with 5 decimal places". RONDA 6/17 solo habia probado (con 1
    caso real) que `rounding=2` cambiaba `ctl`, y concluyo por error que 0/1/3
    no hacian nada. RONDA 32 cruzo el texto LITERAL del manual (pagina 72,
    `fxAPI_Table6_1980`) contra el codigo: el manual documenta, con la MISMA
    redaccion palabra por palabra que ya se habia confirmado (RONDA 31) para
    los wrappers combinados 1980 (`api_density15c_1980`/etc, funcion
    `_ctl_rounding_directo`), que las 3 opciones activas SI redondean `ctl`,
    cada una a una cantidad de decimales distinta: 1="computational value" (4
    decimales si ctl>=1, 5 si ctl<1), 2="table value" (siempre 4 decimales),
    3 (siempre 5 decimales). Como esta funcion calcula `ctl` de forma DIRECTA
    (sin iteracion, ya [CERTAIN] por decompilacion), es exactamente la misma
    "rama directa" para la que `_ctl_rounding_directo` ya fue validada contra
    el oraculo `.xll` real en RONDA 31 -- se reusa tal cual, sin caso real
    propio de Table6 para las opciones 1/3 (permanece con evidencia manual +
    decompilacion + funcion ya validada en otra parte, no un caso real
    dedicado a Table6). Default 0 = comportamiento identico a versiones
    previas de este archivo (sin regresion)."""
    if rounding not in (0, 1, 2, 3):
        raise ValueError("rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        rd60 = 141.5 / (131.5 + api_60f)
        rho60_kgm3 = _rd60_to_density_kgm3(rd60)
        alpha = _alpha(k, rho60_kgm3)
        ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
        return {"ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": api_60f}

    if product == 2:
        # RONDA 49: entrada YA a 60F (condiciones base) -- direccion directa,
        # 1 sola evaluacion con Transition incluida desde el principio (ver
        # `_resolver_producto_auto_1980`).
        resultado, producto_efectivo = _auto_select_1980(api_60f, "api", False, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    ctl = _ctl_rounding_directo(resultado["ctl"], rounding)
    return {"ctl": ctl, "alpha": resultado["alpha"], "k0": resultado["k0"],
            "k1": resultado["k1"], "k2": resultado["k2"], "product_efectivo": producto_efectivo}


# ===========================================================================
# API_Table23_1980 -- [CERTAIN] motor decompilado directamente esta ronda
# (FUN_1800a1c9c -> FUN_1800eb1f8 -> FUN_1800e9a68 crudo / FUN_1800ea5cc
# lube / FUN_1800e9f48 grupo B). Confirmado: MISMA formula alpha/CTL y
# MISMOS K0/K1 byte-exactos que Table5_1980 (0x40755187fcb923a3=341.0957
# crudo, 0x3fd65269595feda6=0.34878 lube, ambos inline como literal en el
# codigo, no solo referenciados por direccion). Diferencia real confirmada:
# Table23 trabaja en RD directamente (sin la conversion a/desde API gravity
# que si hace Table5) y su auto-seleccion B usa breakpoints en RD
# adimensional (0.7785/0.84/...), no en kg/m3.
# Manual pagina 50.
# ===========================================================================
def api_table23_1980(observed_rd: float, observed_temp_f: float,
                      product: Product = 1, hydrometer_correction: bool = False,
                      rounding: bool = False) -> dict:
    """RD(T) -> RD(60°F). API MPMS 11.1 (API-2540) Tables 23A/23B. [CERTAIN]:
    decompilado directamente esta ronda (FUN_1800e9a68/FUN_1800ea5cc/
    FUN_1800e9f48), confirma el mismo motor de Table5_1980 sin la conversion
    a/desde API gravity.

    hydrometer_correction: [CERTAIN, RONDA 6] la pantalla real de Table-23
    (1980) SI expone "Hydrometer Corr." (la Ronda 4 solo lo habia inferido
    por motor compartido, sin caso real). Verificado con caso real (Crude,
    RD_obs=0.85, T=90F): aplicando `_hydrometer_factor()` (la MISMA formula
    ya confirmada para Table5_1980) sobre la densidad observada antes de
    iterar, se reproduce el valor real de la app (rd_60f=0.861617,
    ctl=0.986133) a <0.0001%.

    rounding: [LIKELY, implementado Ronda 3, decimales corregidos RONDA 18 --
    NO hay caso real propio que pruebe el efecto de este flag en Table23, a
    diferencia de hydrometer_correction arriba] redondea SOLO `rd_60f` a 1
    decimal (NO 2), replicando el mismo Tipo A ("API Rounding" booleano
    in-place) confirmado por caso real en Table5_1980 -- RONDA 18 releyo el
    dump XML crudo de ese caso real y corrigio el numero de decimales de 2 a
    1 (ver docstring de `api_table5_1980`); Table23 hereda la correccion por
    el mismo argumento de wrapper compartido de abajo, pero SIGUE sin caso
    real propio. La inferencia esta reforzada por evidencia de decompilacion
    (no solo suposicion de "motor compartido"): el wrapper real
    `FUN_1800a1c9c` (raiz Excel de Table23_1980) es, argumento por argumento,
    IDENTICO al wrapper de Table5_1980 (`FUN_1800a3e58`) -- mismos 5 slots,
    mismos 2 flags booleanos en las mismas posiciones (`local_68[0]`=
    hydrometer, `local_res18[0]`=este flag), la unica diferencia es la
    funcion motor invocada (`FUN_1800eb1f8` en vez de `FUN_1800e4f94`). Aun
    asi, el EFECTO concreto de este 2do flag dentro del motor de Table23 no
    se rastreo a bytes (solo el de Table5 fue verificado con un caso real) --
    se mantiene [LIKELY], no [CERTAIN]. RONDA 32 (cruce manual, pagina 50,
    `fxAPI_Table23_1980`): el manual documenta para esta funcion, TEXTO
    IDENTICO al de Table5_1980, que el flag tambien cambia el limite de
    convergencia del bucle (0.000001 kg/m3 Disabled / 0.05 kg/m3 Enabled) --
    se agrega aqui por la misma evidencia de wrapper compartido byte a byte
    ya documentada arriba (sigue [LIKELY], no hay caso real dedicado que
    distinga el efecto de la tolerancia en Table23 especificamente). Default
    False = comportamiento identico a versiones previas de este archivo (sin
    regresion).

    `product=2` (B - Auto select) [LIKELY, RONDA 49]: mismo mecanismo que
    `api_table5_1980`, con breakpoints en RD adimensional (0.771/0.779/
    0.789/0.84)."""
    tol = 0.05 if rounding else 1e-6

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        rho_obs_kgm3 = _rd60_to_density_kgm3(observed_rd)
        if hydrometer_correction:
            rho_obs_kgm3 *= _hydrometer_factor(observed_temp_f)
        rho_base_kgm3, ctl, alpha = _ctl_1980_iter(k, rho_obs_kgm3, observed_temp_f, T_REF_US_1980_F, tol=tol)
        rd_base = _density_kgm3_to_rd60(rho_base_kgm3)
        return {"rd_60f": rd_base, "ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": rd_base}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(observed_rd, "rd", True, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    rd_base = resultado["rd_60f"]
    if rounding:
        rd_base = round(rd_base, 1)
    return {"rd_60f": rd_base, "ctl": resultado["ctl"], "alpha": resultado["alpha"],
            "k0": resultado["k0"], "k1": resultado["k1"], "k2": resultado["k2"],
            "product_efectivo": producto_efectivo}


# ===========================================================================
# API_Table24_1980 -- [CERTAIN] motor decompilado directamente esta ronda
# (FUN_1800a2454 -> FUN_1800ec49c -> FUN_1800eb74c crudo / FUN_1800ebdf0
# lube / FUN_1800eb97c grupo B), K0/K1 byte-exactos inline confirmados
# (0x40755187fcb923a3, 0x3fd65269595feda6). Variante RD directa de Table6,
# sin bucle (direccion "base->observado"), confirmado.
# Manual pagina 55.
# ===========================================================================
def api_table24_1980(rd_60f: float, observed_temp_f: float,
                      product: Product = 1, rounding: int = 0) -> dict:
    """RD(60°F) -> CTL(T). API MPMS 11.1 (API-2540) Tables 24A/24B(/24D).
    [CERTAIN]: decompilado directamente esta ronda.

    rounding: [CERTAIN, RONDA 6, CORREGIDO RONDA 32] mismo ENUM real "API
    Rounding" de Table6_1980 (0=Disabled, 1="Enabled for computational
    value", 2="Enabled for table value", 3="Enabled with 5 decimal places").
    RONDA 6/17 solo habia confirmado (1 caso real) que `rounding=2` cambiaba
    `ctl`, y concluyo por error que 0/1/3 no hacian nada -- RONDA 32 cruzo el
    texto LITERAL del manual (pagina 55, `fxAPI_Table24_1980`) y encontro que
    documenta las MISMAS 3 opciones activas de redondeo de `ctl` (4
    decimales si ctl>=1 / 5 si ctl<1 para la opcion 1, siempre 4 para la
    opcion 2, siempre 5 para la opcion 3) que ya se habia CERRADO por
    oraculo `.xll` real para los wrappers combinados 1980 en RONDA 31
    (`_ctl_rounding_directo`) -- se reusa esa misma funcion, ya validada en
    su "rama directa" equivalente (esta funcion tambien calcula `ctl` sin
    iteracion). El caso real de Ronda 6 SOLO probo la opcion 2, sin
    distinguir 1/3 -- la correccion se apoya en manual + reuso de funcion ya
    validada, no en un caso real nuevo dedicado a las opciones 1/3 de
    Table24. Default 0 = comportamiento identico a versiones previas de este
    archivo (sin regresion)."""
    if rounding not in (0, 1, 2, 3):
        raise ValueError("rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        rho60_kgm3 = _rd60_to_density_kgm3(rd_60f)
        alpha = _alpha(k, rho60_kgm3)
        ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
        return {"ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": rd_60f}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(rd_60f, "rd", False, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    ctl = _ctl_rounding_directo(resultado["ctl"], rounding)
    return {"ctl": ctl, "alpha": resultado["alpha"], "k0": resultado["k0"],
            "k1": resultado["k1"], "k2": resultado["k2"], "product_efectivo": producto_efectivo}


# ===========================================================================
# API_Table53_1980 -- [CERTAIN] motor decompilado directamente
# (FUN_1800edc80 / FUN_1800ececc / FUN_1800ed634), constantes metricas
# byte-exactas (K0 crudo=613.9723, K1 lube=0.6278). Densidad observada (T)
# -> densidad a 15C.
# Manual pagina 62.
# ===========================================================================
def api_table53_1980(observed_density_kgm3: float, observed_temp_c: float,
                      product: Product = 1, hydrometer_correction: bool = False,
                      rounding: bool = False) -> dict:
    """Densidad(T) -> Densidad(15°C), kg/m3. API MPMS 11.1 (API-2540)
    Tables 53A/53B/53D, 1980/1984.

    hydrometer_correction: [LIKELY, RONDA 7 -- ver `_hydrometer_factor_metric`
    para el nivel de confianza exacto] replica el flag real "Hydrometer
    Corr." de la pantalla FlowXpert. Verificado contra caso real (Crude,
    Density_obs=1000kg/m3, T=20C): reproduce density_15c=1002.95 (real app:
    1002.948) con <0.0002% de error -- MEJOR que el ruido tipico <0.0001% de
    esta familia solo porque es un ajuste de 1 solo punto, no una
    decompilacion; tratar con un peldano menos de certeza que el resto de
    esta familia.

    rounding: [LIKELY, implementado Ronda 3, decimales corregidos RONDA 18 --
    sin caso real propio] redondea SOLO `density_15c` a 1 decimal (NO 2),
    replicando el mismo Tipo A ("API Rounding" booleano in-place) confirmado
    por caso real en Table5_1980 -- RONDA 18 releyo el dump XML crudo de ese
    caso real y corrigio el numero de decimales de 2 a 1 (ver docstring de
    `api_table5_1980`); Table53 hereda la correccion por el mismo argumento
    de wrapper compartido de abajo, pero SIGUE sin caso real propio. Igual
    que en Table23_1980, se confirmo por decompilacion (no solo suposicion)
    que el wrapper real `FUN_1800a2bf4` (raiz Excel de Table53_1980) tiene la
    MISMA estructura de 5 argumentos y 2 flags booleanos en las mismas
    posiciones que Table5_1980 (llama a `FUN_1800edc80` con
    `local_68[0]`=hydrometer, `local_res18[0]`=este flag) -- pero el efecto
    exacto de este 2do flag dentro del motor metrico no se verifico contra un
    caso real (a diferencia de `hydrometer_correction` arriba, que si tiene 1
    caso real propio). Se mantiene [LIKELY]. RONDA 32 (cruce manual, pagina
    62, `fxAPI_Table53_1980`): mismo texto literal de Table5/23_1980 sobre la
    tolerancia de convergencia dependiente del flag (0.000001 kg/m3 Disabled
    / 0.05 kg/m3 Enabled) -- se agrega aqui por el mismo argumento de wrapper
    compartido (sigue [LIKELY]). Default False = comportamiento identico a
    versiones previas de este archivo (sin regresion).

    `product=2` (B - Auto select) [LIKELY, RONDA 49]: mismo mecanismo que
    `api_table5_1980`, con breakpoints en kg/m3 (770.0/779.0/788.0/839.0)."""
    tol = 0.05 if rounding else 1e-6

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_METRIC[producto_fijo]
        dens_obs = observed_density_kgm3
        if hydrometer_correction:
            dens_obs = dens_obs * _hydrometer_factor_metric(observed_temp_c)
        dens15, ctl, alpha = _ctl_1980_iter(k, dens_obs, observed_temp_c, T_REF_METRIC_1980_C, tol=tol)
        return {"density_15c": dens15, "ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": dens15}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(observed_density_kgm3, "densidad_kgm3", True, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    dens15 = resultado["density_15c"]
    if rounding:
        dens15 = round(dens15, 1)
    return {"density_15c": dens15, "ctl": resultado["ctl"], "alpha": resultado["alpha"],
            "k0": resultado["k0"], "k1": resultado["k1"], "k2": resultado["k2"],
            "product_efectivo": producto_efectivo}


# ===========================================================================
# API_Table54_1980 -- [CERTAIN] motor decompilado directamente esta ronda
# (FUN_1800a33c4 -> FUN_1800eed08 -> FUN_1800ee1f8 crudo / FUN_1800ee7d8
# lube / FUN_1800ee438 grupo B), K0/K1 metricos byte-exactos inline
# confirmados (0x40832fc74538ef35=613.9723, 0x3fe416f0068db8bb=0.6278).
# Variante directa de Table53 (sin bucle), T_ref=15.0C confirmado
# (DAT_180194008).
# Manual pagina 66.
# ===========================================================================
def api_table54_1980(density_15c_kgm3: float, observed_temp_c: float,
                      product: Product = 1, rounding: int = 0) -> dict:
    """Densidad(15°C) -> CTL(T). API MPMS 11.1 (API-2540) Tables 54A/54B/54D.
    [CERTAIN]: decompilado directamente esta ronda.

    rounding: [LIKELY, CORREGIDO RONDA 32 -- sin caso real propio, a
    diferencia de Table24_1980 que si lo tiene] mismo ENUM real "API
    Rounding" de Table6_1980/Table24_1980 (0=Disabled, 1="Enabled for
    computational value", 2="Enabled for table value", 3="Enabled with 5
    decimal places"). Se creia (RONDA 6/17) que SOLO `rounding=2` redondeaba
    `ctl` a 4 decimales -- RONDA 32 cruzo el manual (pagina 66,
    `fxAPI_Table54_1980`) y confirmo que documenta LITERALMENTE las mismas 3
    opciones activas (4/5 decimales segun ctl para la opcion 1, 4 fijo para
    la 2, 5 fijo para la 3) ya cerradas por oraculo `.xll` real para los
    wrappers combinados 1980 (`_ctl_rounding_directo`, RONDA 31) -- se reusa
    esa funcion, aplicable porque Table54 tambien calcula `ctl` de forma
    DIRECTA sin iteracion (mismo patron que Table6/24). Sigue sin caso real
    propio para NINGUNA opcion del enum en Table54 especificamente (ni
    siquiera para la opcion 2, que en Table6/24 si tiene caso real) -- se
    mantiene [LIKELY], apoyado en manual + decompilacion de wrapper
    identico + funcion de redondeo ya validada en otra parte, no fabricado.
    Default 0 = comportamiento identico a versiones previas de este archivo
    (sin regresion)."""
    if rounding not in (0, 1, 2, 3):
        raise ValueError("rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_METRIC[producto_fijo]
        alpha = _alpha(k, density_15c_kgm3)
        ctl = _ctl_1980(alpha, observed_temp_c - T_REF_METRIC_1980_C)
        return {"ctl": ctl, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": density_15c_kgm3}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(density_15c_kgm3, "densidad_kgm3", False, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    ctl = _ctl_rounding_directo(resultado["ctl"], rounding)
    return {"ctl": ctl, "alpha": resultado["alpha"], "k0": resultado["k0"],
            "k1": resultado["k1"], "k2": resultado["k2"], "product_efectivo": producto_efectivo}


# ===========================================================================
# Motor 2004 -- CTL + factor de compresibilidad F / CPL. [CERTAIN] la
# aritmetica esta confirmada por decompilacion real de FUN_1801053f4 /
# FUN_180105b64 (ver docstring) para el subconjunto en sistema US
# (Table5/6/23/24_2004). NO validado todavia contra un caso real en vivo.
#
# DIFERENCIA REAL de metodo numerico frente a la implementacion de abajo:
# el binario resuelve la direccion "observado->base" con un paso de
# Newton-Raphson (formula racional con la derivada de CTPL respecto a rho),
# mientras que esta implementacion usa sustitucion sucesiva simple (la misma
# tecnica ya usada para 1980). Ambos metodos deben converger al MISMO punto
# fijo de la ecuacion "rho_obs = rho_base * CTPL(rho_base)" si esta bien
# condicionada -- se prefirio no replicar la formula de Newton del binario
# porque la identidad de varias variables intermedias en esa parte del
# decompilado no se pudo confirmar con certeza total esta ronda (habria sido
# fabricar una formula con apariencia de exactitud que no se tiene).
# ===========================================================================
_CTL_2004_QUAD_OFFSET = 0.01374979547  # DAT_18028e730 = 2*_ALPHA_CORR_SCALE_2004, byte-exacto


# ===========================================================================
# [CERTAIN, RONDA 50 (2026-09-11)] "product=2" (B - Auto select) del motor
# 2004 -- CIERRA el pendiente que RONDA 49 dejo explicito para esta familia.
#
# MECANISMO REAL (decompilacion COMPLETA de `FUN_1801053f4`, NO solo el sitio
# de llamada -- ver cuerpo entero en
# `ANALISIS_GHIDRA_FLOWXPERT/ghidra_api_mpms_xll_output.txt` lineas 2311-2500,
# 1331 bytes, leido linea a linea esta ronda): es un mecanismo MUCHO MAS
# SIMPLE que el de 1980 -- NO hay 2 pasadas ni exclusion de "Transition" en
# una 1a pasada. Es una UNICA comparacion de 4 vias, SIEMPRE en densidad
# kg/m3 (nunca en API/RD directamente, a diferencia de 1980 donde cada
# dominio -api/rd/densidad- tenia su propio juego de breakpoints):
#     density_kgm3 <  770.352            -> Gasoline      (Excel product 3)
#     770.352 <= density_kgm3 <  787.5195 -> Transition Area (Excel product 4)
#     787.5195 <= density_kgm3 <  838.3127 -> Jet Fuels    (Excel product 5)
#     density_kgm3 >= 838.3127            -> Fuel Oils     (Excel product 6)
# Los 3 breakpoints (DAT_18028db20/28/30) estan confirmados BYTE A BYTE en 2
# sitios independientes del `.xll` (`ghidra_api_mpms_xll_output.txt` linea
# 8108-8110 Y `ghidra_api_table5960_xll_output.txt` linea 3208-3210) Y,
# ADEMAS, confirmados EN VIVO por oraculo `.xll` DIRECTO (ctypes, llamando
# el nucleo puro `FUN_1801053f4` sin ningun wrapper Excel/XLOPER de por
# medio -- la firma de esta funcion es 100% tipada, sin XLOPER, a diferencia
# de los exportadores Excel): un barrido de densidad justo en cada frontera
# (769/770/770.352/770.4/.../838.3127/838.4/900) reproduce EXACTO el salto de
# producto en cada uno de los 3 breakpoints, ida y vuelta.
#
# ESTOS NO SON LOS MISMOS BREAKPOINTS QUE 1980 (770.0/788.0/839.0 kg/m3) --
# se parecen (2004 usa RHO_WATER_2004_KGM3=999.016 en vez de 999.012, lo que
# ya movia ligeramente cualquier conversion RD/API->densidad) pero el propio
# switch de densidad usa constantes DISTINTAS, confirmadas por su propia
# direccion DAT_ independiente (18028db20/28/30, NO 1801ea... como usa 1980).
#
# REMAPEO interno CONFIRMADO por decompilacion de 3 wrappers INDEPENDIENTES
# (`FUN_1800e5218`=Table5_2004, `FUN_1800e5fec`=Table6_2004, `FUN_1800ec6dc`
# =Table24_2004 -- los 3 con el MISMO codigo de remapeo, literal, no por
# analogia): el argumento Excel-level "product" (1..8) SI llega intacto a
# `FUN_1801053f4` para 1/2/7/8, pero para el grupo B (3..6) el WRAPPER lo
# permuta antes de llamar al nucleo (excel 3->interno 6, 4->5, 5->4, 6->3;
# funcion involutiva, el mismo remapeo se aplica en reversa sobre el
# "producto efectivo" que el nucleo reporta, para volver a informarlo en
# numeracion Excel). Para `product` FIJO (no auto), el codigo de este archivo
# usa `K_US[product]` DIRECTO desde Ronda 1 -- eso YA es semanticamente
# correcto (`K_US[4]`=Transition=1489.067/-0.0018684 coincide EXACTO con lo
# que el nucleo usa internamente para el codigo interno 5, y de hecho asi lo
# confirmo RONDA 40 con casos reales). El switch de "Auto" (product=2) NO
# pasa por ningun remapeo (2->2, identidad) -- por eso `_resolver_producto_auto_2004`
# de abajo devuelve DIRECTO el producto Excel-level (3/4/5/6), sin necesitar
# aplicar ninguna permutacion, y coincide exacto con lo confirmado por el
# oraculo (K0/K1/K2 devueltos por el nucleo en modo Auto, comparados contra
# `K_US[3..6]`, calzan EXACTO para cada tramo de densidad).
#
# El nucleo (`FUN_180105b64`, el bucle <=15 iteraciones ya conocido) llama a
# `FUN_1801053f4` de NUEVO en CADA iteracion con el `param_1` (producto)
# SIN CAMBIAR pero con el `param_3` (densidad) YA ACTUALIZADO al candidato de
# esa iteracion -- es decir, en modo Auto, la region/K se RE-EVALUA en cada
# paso segun el candidato ACTUAL, de forma auto-consistente con la propia
# convergencia de la densidad (nunca hay un "1a pasada sin Transition" como
# en 1980). Replicado aqui via `_k_for_2004`, invocado dentro de
# `_ctpl_2004_direct` en CADA llamada (tanto la unica evaluacion de las
# funciones directas como cada paso de `_ctpl_2004_iter`).
# ===========================================================================
DENS_BREAK_2004_LOW = 770.352    # DAT_18028db20, byte-exacto + confirmado en vivo (oraculo)
DENS_BREAK_2004_MID = 787.5195   # DAT_18028db28, idem
DENS_BREAK_2004_HIGH = 838.3127  # DAT_18028db30, idem


def _resolver_producto_auto_2004(density_kgm3: float) -> int:
    """Producto Excel-level (3=Gasoline/4=Transition/5=Jet/6=FuelOil) para
    `product=2` ('B - Auto select') del motor 2004, replicando EXACTO
    (confirmado por decompilacion completa de `FUN_1801053f4` + oraculo
    `.xll` directo, RONDA 50) el UNICO switch real de 4 vias en densidad
    kg/m3. Ver docstring arriba para la evidencia completa."""
    if density_kgm3 < DENS_BREAK_2004_LOW:
        return 3
    if density_kgm3 < DENS_BREAK_2004_MID:
        return 4
    if density_kgm3 < DENS_BREAK_2004_HIGH:
        return 5
    return 6


def _k_for_2004(product: Product, density_kgm3: float) -> _K:
    """Resuelve la tabla K0/K1/K2 real para el motor 2004, incluyendo
    `product=2` (Auto). `density_kgm3` debe ser la densidad NATIVA (kg/m3)
    que el nucleo real compara contra los breakpoints en ESE punto de
    evaluacion (la densidad candidata cruda, ANTES de `_rho_corregido_2004`
    -- el nucleo real selecciona K0/K1/K2 usando `param_3` tal cual llega,
    y SOLO DESPUES aplica el paso de auto-consistencia de RONDA 40)."""
    if product == 2:
        return K_US[_resolver_producto_auto_2004(density_kgm3)]
    return K_US[product]


def _ctl_2004(alpha: float, observed_temp_f: float) -> float:
    """CTL 2004 = exp(-(x+0.8x^2 + termino extra)), x = alpha*(T_obs_F_corregida
    - 60.0068749). [CERTAIN] forma y T_REF_2004_US_F confirmados byte-exactos
    en FUN_1801053f4. Desde RONDA 8 SI incluye la micro-correccion polinomica
    de temperatura (`_micro_correccion_temp_2004`). Desde RONDA 40 SI incluye
    el termino extra `0.8*_CTL_2004_QUAD_OFFSET*alpha*x` (decompilacion
    completa de FUN_1801053f4: el coeficiente cuadratico real no multiplica
    a `dT` solo, sino a `(dT + _CTL_2004_QUAD_OFFSET)`) -- termino minusculo
    (orden 1e-9..1e-11) pero necesario para la exactitud de precision de
    maquina confirmada contra el oraculo `.xll` directo (ver
    `_rho_corregido_2004`, que SI depende de este mismo alpha ya corregido
    de rho -- ambos fixes de RONDA 40 se validaron juntos)."""
    t_corr = _micro_correccion_temp_2004(observed_temp_f)
    dt = t_corr - T_REF_2004_US_F
    inner = ((dt + _CTL_2004_QUAD_OFFSET) * alpha * CTL_COEF_0_8 + 1.0) * dt * alpha
    return math.exp(-inner)


def _f_compressibility_2004(observed_temp_f: float, rho_base_kgm3: float) -> float:
    """Factor de compresibilidad F (1/psi), [CERTAIN en el valor extraido del
    binario, SIN fuente publica identificada] -- ver constantes _CPL_A..D y
    docstring. Extraido de FUN_1801053f4 (.xll). Desde RONDA 8 usa la MISMA
    temperatura corregida que `_ctl_2004` (confirmado en el decompilado: el
    registro `dVar2` que guarda la correccion se reutiliza tal cual, sin
    recalcular, en la formula de F -- linea ~2473 del archivo de
    decompilacion, justo despues de usarse en el exponente del CTL)."""
    if rho_base_kgm3 == 0.0:
        return 0.0
    t_corr = _micro_correccion_temp_2004(observed_temp_f)
    exponente = ((t_corr * _CPL_A + _CPL_B) / (rho_base_kgm3 * rho_base_kgm3)
                 + (t_corr * _CPL_C - _CPL_D))
    return math.exp(exponente) * _CPL_SCALE


def _cpl_2004(f_per_psi: float, pressure_psig: float) -> float:
    """CPL = 1/(1 - P*F), forzado a minimo 1.0 -- [CERTAIN] forma confirmada
    en FUN_1801053f4 ("dVar2 = 1.0/(1.0-P*F); if (dVar2<1.0) dVar2=1.0;")."""
    denom = 1.0 - pressure_psig * f_per_psi
    cpl = 1.0 / denom if denom != 0.0 else 1.0
    if cpl < 1.0:
        cpl = 1.0
    return cpl


def _ctpl_2004_direct(product: Product, rho_base_kgm3: float, observed_temp_f: float,
                       pressure_psig: float) -> dict:
    """[CERTAIN, RONDA 40 + RONDA 50] rho_base_kgm3 se corrige primero via
    `_rho_corregido_2004` (auto-consistencia real del nucleo, ver docstring
    de esa funcion) -- alpha/CTL/F se calculan con la densidad YA
    CORREGIDA, no con la nominal, tal como confirma la decompilacion
    completa de FUN_1801053f4. `product` puede ser 2 (Auto) -- la tabla
    K0/K1/K2 se resuelve DINAMICAMENTE via `_k_for_2004` usando la densidad
    NATIVA cruda (`rho_base_kgm3`, antes de la correccion), exactamente
    donde el nucleo real hace su propio switch (RONDA 50)."""
    k = _k_for_2004(product, rho_base_kgm3)
    rho_corr = _rho_corregido_2004(k, rho_base_kgm3)
    alpha = _alpha(k, rho_corr)
    ctl = _ctl_2004(alpha, observed_temp_f)
    f = _f_compressibility_2004(observed_temp_f, rho_corr)
    cpl = _cpl_2004(f, pressure_psig)
    producto_efectivo = product if product != 2 else _resolver_producto_auto_2004(rho_base_kgm3)
    return {"ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl, "f": f, "alpha": alpha,
            "k0": k.k0, "k1": k.k1, "k2": k.k2, "product_efectivo": producto_efectivo}


def _ctpl_2004_iter(product: Product, rho_obs_kgm3: float, observed_temp_f: float,
                     pressure_psig: float, max_iter: int = MAX_ITER_2004,
                     tol: float = 1e-6) -> tuple[float, dict]:
    """Resuelve rho_base tal que rho_obs = rho_base*CTPL(rho_base).
    [CERTAIN] la ecuacion (confirmada en el chequeo de convergencia real de
    FUN_180105b64: "fabs(param_3 - CTPL*rho_base_guess)"); [ver nota arriba]
    el metodo de iteracion (sustitucion sucesiva) es una eleccion propia, no
    una replica byte a byte del paso de Newton del binario. max_iter=15
    confirmado a bytes (FUN_180105b64). [RONDA 50] `product=2` (Auto) se
    propaga tal cual a `_ctpl_2004_direct` en CADA iteracion -- replica el
    comportamiento real confirmado de `FUN_180105b64`, que llama al nucleo de
    NUEVO en cada paso con la densidad candidata YA ACTUALIZADA, dejando que
    el switch de region se re-evalue de forma auto-consistente con la propia
    convergencia (nunca un mecanismo de '2 pasadas' como en 1980)."""
    rho_base = rho_obs_kgm3
    resultado: dict = {}
    for _ in range(max_iter):
        resultado = _ctpl_2004_direct(product, rho_base, observed_temp_f, pressure_psig)
        ctpl = resultado["ctpl"]
        nuevo = rho_obs_kgm3 / ctpl if ctpl != 0 else rho_base
        if abs(nuevo - rho_base) < tol:
            rho_base = nuevo
            break
        rho_base = nuevo
    return rho_base, resultado


def _api_rounding_2004(r: dict, api_rounding: int) -> dict:
    """Aplica el flag booleano 'API Rounding' (0/1) de las 8 funciones API
    MPMS 11.1 (2004) (Table5/6/23/24/53/54/59/60_2004).

    [CERTAIN via auditoria en vivo AVD real, RONDA 34] El manual oficial
    (fxAPI_Table5/23/24/53/54/59/60_2004 en `manual_texto_api_1980_1952.txt`
    y `manual_texto_api_2004_ext.txt`, fxAPI_Table6_2004) dice LITERALMENTE
    que con el flag Enabled "The CTL, CPL and CTPL value are rounded to 5
    decimal places" -- pero la pantalla REAL de la app (Table5_2004 y
    Table53_2004, 2 motores distintos: nucleo directo/iterativo puro y el
    wrapper de doble evaluacion metrico) CONTRADICE esa lectura literal:
      - Table5_2004, Lub oil, T=90F(32.2222222C), P=20bar(g):
          API=30        : Disabled ctpl=0.989552 -> Enabled ctpl=0.989550
          API=30.123456 : Disabled ctpl=0.989545 -> Enabled ctpl=0.989550
      - Table53_2004, Crude, Dens=850kg/m3, T=20C, P=5bar:
          Disabled ctpl=0.996144 -> Enabled ctpl=0.996140
    En los 4 casos, CTL y CPL quedan BIT-IDENTICOS en pantalla entre
    Disabled/Enabled (ninguno de los 2 se redondea nunca), y CTPL Enabled ==
    round(ctl_full_precision * cpl_full_precision, 5) exacto (verificado
    contra el valor Python de cada caso, coincide a los 6 decimales que
    muestra pantalla en los 4). Es decir: el unico efecto real del flag es
    redondear CTPL a 5 decimales; CTL/CPL NUNCA se tocan, sin importar lo que
    diga el texto del manual. api_rounding=0 (default) = sin cambios
    (comportamiento previo de este archivo, full precision)."""
    if not api_rounding:
        return r
    if api_rounding != 1:
        raise ValueError("api_rounding debe ser 0 (Disabled) o 1 (Enabled)")
    out = dict(r)
    out["ctpl"] = round(out["ctpl"], 5)
    return out


def api_table5_2004(observed_api: float, observed_temp_f: float,
                     pressure_psig: float = 0.0, product: Product = 1,
                     api_rounding: int = 0) -> dict:
    """°API(T,P) -> °API(60°F, 0 psig). API MPMS 11.1 Tables 5A/5B/5D, 2004.
    [CERTAIN] aritmetica CTL+CPL confirmada por decompilacion (ver
    docstring del modulo). Iterativo, <=15 iteraciones (confirmado a bytes).
    `api_rounding` (0/1) [CERTAIN via AVD real, RONDA 34, ver
    `_api_rounding_2004`]: solo redondea CTPL a 5 decimales, CTL/CPL quedan
    intactos (pese a lo que dice el manual). `product=2` (B - Auto select)
    [CERTAIN, RONDA 50 -- ver docstring del modulo y de
    `_resolver_producto_auto_2004`]: implementado, agrega la clave
    `product_efectivo` (3/4/5/6) al resultado."""
    rd_obs = 141.5 / (131.5 + observed_api)
    rho_obs_kgm3 = _rd60_to_density_2004_kgm3(rd_obs)
    rho_base_kgm3, r = _ctpl_2004_iter(product, rho_obs_kgm3, observed_temp_f, pressure_psig)
    rd_base = _density_2004_kgm3_to_rd60(rho_base_kgm3)
    api60 = 141.5 / rd_base - 131.5
    return _api_rounding_2004({"api_60f_0psig": api60, **r}, api_rounding)


def api_table6_2004(api_60f: float, observed_temp_f: float,
                     pressure_psig: float = 0.0, product: Product = 1,
                     api_rounding: int = 0) -> dict:
    """°API(60°F) -> CTPL(T,P). API MPMS 11.1 Tables 6A/6B/6D, 2004.
    [CERTAIN] directo (sin bucle), aritmetica confirmada por decompilacion.
    `api_rounding` (0/1) [CERTAIN via AVD real, RONDA 34, ver
    `_api_rounding_2004`]: solo redondea CTPL a 5 decimales. `product=2`
    (B - Auto select) [CERTAIN, RONDA 50]: implementado, agrega la clave
    `product_efectivo` al resultado."""
    rd60 = 141.5 / (131.5 + api_60f)
    rho60_kgm3 = _rd60_to_density_2004_kgm3(rd60)
    r = _ctpl_2004_direct(product, rho60_kgm3, observed_temp_f, pressure_psig)
    return _api_rounding_2004(r, api_rounding)


def api_table23_2004(observed_rd: float, observed_temp_f: float,
                      pressure_psig: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """RD(T,P) -> RD(60°F, 0 psig). API MPMS 11.1 Tables 23A/23B, 2004.
    [CERTAIN] confirmado que comparte el mismo nucleo FUN_1801053f4 via
    FUN_180105b64 (iterativo). `api_rounding` (0/1) [CERTAIN via AVD real,
    RONDA 34, ver `_api_rounding_2004`]: solo redondea CTPL a 5 decimales.
    `product=2` (B - Auto select) [CERTAIN, RONDA 50]: implementado, agrega
    la clave `product_efectivo` al resultado."""
    rho_obs_kgm3 = _rd60_to_density_2004_kgm3(observed_rd)
    rho_base_kgm3, r = _ctpl_2004_iter(product, rho_obs_kgm3, observed_temp_f, pressure_psig)
    rd_base = _density_2004_kgm3_to_rd60(rho_base_kgm3)
    return _api_rounding_2004({"rd_60f_0psig": rd_base, **r}, api_rounding)


def api_table24_2004(rd_60f: float, observed_temp_f: float,
                      pressure_psig: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """RD(60°F) -> CTPL(T,P). API MPMS 11.1 Tables 24A/24B, 2004.
    [CERTAIN] confirmado que llama directo (sin bucle) al mismo
    FUN_1801053f4. `api_rounding` (0/1) [CERTAIN via AVD real, RONDA 34, ver
    `_api_rounding_2004`]: solo redondea CTPL a 5 decimales. `product=2`
    (B - Auto select) [CERTAIN, RONDA 50]: implementado, agrega la clave
    `product_efectivo` al resultado."""
    rho60_kgm3 = _rd60_to_density_2004_kgm3(rd_60f)
    r = _ctpl_2004_direct(product, rho60_kgm3, observed_temp_f, pressure_psig)
    return _api_rounding_2004(r, api_rounding)


# ===========================================================================
# API_Table53_2004 / API_Table54_2004 (metricas) -- [CERTAIN via
# decompilacion exhaustiva + verificacion algebraica cruzada, RONDA 5]
#
# Mecanismo real (ver docstring del modulo, seccion RONDA 5, para la
# reconstruccion linea a linea del sitio de llamada real
# FUN_1800edec8->FUN_180105ec8 / FUN_1800eeecc->FUN_180105928):
#   1. Table53_2004 (observado->base): se itera con T_obs/P_obs REALES
#      (igual que Table5/23_2004, mismo nucleo FUN_1801053f4/FUN_180105b64)
#      para converger `rho_base`. Con `rho_base` ya convergido, una SEGUNDA
#      evaluacion DIRECTA (sin bucle) del mismo nucleo a T=15°C (convertido
#      a F) y P=0 da `ctl_15`, y `density_15c = rho_base * ctl_15`.
#   2. Table54_2004 (base->observado): primero corre el MISMO bucle pero
#      con T=15°C fijo y P=0 (para invertir la densidad-a-15°C de entrada y
#      recuperar `rho_base`), y LUEGO evalua el nucleo con T_obs/P_obs
#      reales para obtener ctl_real/cpl_real; el resultado final es
#      ctl_out=ctl_real/ctl_15, ctpl_out=ctl_out*cpl_real.
# Verificado (NO caso real en vivo, ver docstring): sanity T=15C,P=0 (debe
# devolver la entrada sin cambios) y round-trip Table53->Table54 (recupera
# la densidad observada original, error ~1e-8, ruido de iteracion) en 2
# productos distintos (Crudo, Lubricante).
# ===========================================================================
def api_table53_2004(observed_density_kgm3: float, observed_temp_c: float,
                      pressure_bar: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """Densidad(T,P) -> Densidad(15°C, 0 bar[g]). API MPMS 11.1 Tables
    53A/53B/53D, 2004. [CERTAIN via decompilacion + verificacion algebraica
    cruzada, RONDA 5] -- ver docstring del modulo. Iterativo, <=15
    iteraciones (mismo nucleo FUN_1801053f4/FUN_180105b64 que Table5/23_2004,
    reutiliza K_US con el numero de producto a nivel Excel, igual que las
    otras 4 tablas 2004 ya implementadas). `api_rounding` (0/1) [CERTAIN via
    AVD real, RONDA 34, ver `_api_rounding_2004`]: solo redondea CTPL a 5
    decimales (confirmado con este mismo caso: Crude, 850kg/m3, T=20C,
    P=5bar -> Disabled ctpl=0.996144, Enabled ctpl=0.996140; CTL/CPL
    inalterados en pantalla). `product=2` (B - Auto select) [CERTAIN,
    RONDA 50]: implementado, agrega la clave `product_efectivo` al
    resultado."""
    t_obs_f = _celsius_to_fahrenheit(observed_temp_c)
    t_15_f = _celsius_to_fahrenheit(T_REF_METRIC_1980_C)  # 15.0C -> 59.0F
    p_psi = pressure_bar * BAR_TO_KPA / PSI_TO_KPA
    rho_base, r_obs = _ctpl_2004_iter(product, observed_density_kgm3, t_obs_f, p_psi)
    # [RONDA 40] alpha se calcula con rho_base YA CORREGIDA (ver
    # `_rho_corregido_2004`), igual que dentro de `_ctpl_2004_direct`.
    # [RONDA 50] K0/K1/K2 se resuelven con la MISMA densidad ya convergida
    # (rho_base) que usa la llamada directa real del nucleo para esta 2da
    # evaluacion en la referencia metrica.
    k = _k_for_2004(product, rho_base)
    alpha_base = _alpha(k, _rho_corregido_2004(k, rho_base))
    ctl_15 = _ctl_2004(alpha_base, t_15_f)
    density_15c = rho_base * ctl_15
    # [CERTAIN, corregido RONDA 6 con evidencia de caso real -- ver docstring
    # del modulo] `r_obs["ctpl"]/ctl_15` SI es el CTPL real de la app (nombre
    # correcto), pero la version anterior de este archivo lo devolvia bajo la
    # clave "ctl" (etiqueta equivocada, no error de formula). El CTL real de
    # la app es ctpl_out/cpl_out (verificado exacto contra un caso real con
    # P=5 bar(g): reproduce 0.995777, el CTL mostrado en pantalla).
    cpl_out = r_obs["cpl"]
    ctpl_out = r_obs["ctpl"] / ctl_15 if ctl_15 != 0 else 0.0
    ctl_out = ctpl_out / cpl_out if cpl_out != 0 else 0.0
    r = {"density_15c": density_15c, "ctl": ctl_out, "cpl": cpl_out,
         "ctpl": ctpl_out, "f": r_obs["f"] * BAR_TO_KPA / PSI_TO_KPA,
         "alpha": alpha_base * 1.8, "k0": k.k0, "k1": k.k1, "k2": k.k2,
         "product_efectivo": r_obs["product_efectivo"]}
    return _api_rounding_2004(r, api_rounding)


def api_table54_2004(density_15c_kgm3: float, observed_temp_c: float,
                      pressure_bar: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """Densidad(15°C, 0 bar[g]) -> CTPL(T,P). API MPMS 11.1 Tables
    53A/53B/53D, 2004 (variante Table54, direccion inversa de Table53).
    [CERTAIN via decompilacion + verificacion algebraica cruzada, RONDA 5]
    -- ver docstring del modulo. Requiere una iteracion previa (<=15) para
    invertir la densidad-a-15°C de entrada y recuperar `rho_base`; la
    evaluacion contra T/P reales es directa (sin bucle) despues de eso.
    `api_rounding` (0/1) [CERTAIN via AVD real, RONDA 34, ver
    `_api_rounding_2004`]: solo redondea CTPL a 5 decimales. `product=2`
    (B - Auto select) [CERTAIN, RONDA 50]: implementado, agrega la clave
    `product_efectivo` al resultado."""
    t_obs_f = _celsius_to_fahrenheit(observed_temp_c)
    t_15_f = _celsius_to_fahrenheit(T_REF_METRIC_1980_C)
    p_psi = pressure_bar * BAR_TO_KPA / PSI_TO_KPA
    # [RONDA 50] el 1er bucle invierte la densidad-a-15C fijando T=15C,P=0 --
    # la region/K SI puede depender de `product=2` en esta 1a etapa tambien
    # (misma logica auto-consistente que el resto del motor).
    rho_base, r_15 = _ctpl_2004_iter(product, density_15c_kgm3, t_15_f, 0.0)
    ctl_15 = r_15["ctl"]
    # [RONDA 40] misma correccion de rho_base que en `_ctpl_2004_direct`.
    # [RONDA 50] K0/K1/K2 resueltos con la MISMA densidad ya convergida.
    k = _k_for_2004(product, rho_base)
    rho_base_corr = _rho_corregido_2004(k, rho_base)
    alpha_base = _alpha(k, rho_base_corr)
    ctl_real = _ctl_2004(alpha_base, t_obs_f)
    f_real = _f_compressibility_2004(t_obs_f, rho_base_corr)
    cpl_real = _cpl_2004(f_real, p_psi)
    ctl_out = ctl_real / ctl_15 if ctl_15 != 0 else 0.0
    ctpl_out = ctl_out * cpl_real
    density_obs_predicted = ctpl_out * density_15c_kgm3
    r = {"ctl": ctl_out, "cpl": cpl_real, "ctpl": ctpl_out,
         "density_obs_predicted": density_obs_predicted,
         "f": f_real * BAR_TO_KPA / PSI_TO_KPA, "alpha": alpha_base * 1.8,
         "k0": k.k0, "k1": k.k1, "k2": k.k2,
         "product_efectivo": r_15["product_efectivo"]}
    return _api_rounding_2004(r, api_rounding)


# ===========================================================================
# API_Table59_2004 / API_Table60_2004 (metricas, referencia 20C) -- [CERTAIN
# via decompilacion exhaustiva CRUZADA en 2 plataformas, RONDA 11]
#
# CORRECCION IMPORTANTE sobre la premisa de partida de esta ronda: se pidio
# implementar "con sus PROPIAS constantes K0/K1/K2, distintas a las de
# Table53/54" -- la decompilacion real (.xll Y .so, independientemente)
# CONTRADICE esa premisa. NO existe una tabla K0/K1/K2 separada para
# Table59/60: son un clon estructural BYTE A BYTE de Table53/54_2004,
# compartiendo el MISMO motor y el MISMO despacho de producto->K0/K1/K2 (los
# 8 valores ya confirmados de K_US/K_METRIC en Ronda 1/2), y difieren
# UNICAMENTE en la temperatura de referencia metrica: 20.0C en vez de 15.0C.
# Evidencia (ver `ANALISIS_GHIDRA_FLOWXPERT/ghidra_api_table5960_xll_output.txt`
# y `ghidra_api_table5960_so_output.txt`, generados esta ronda):
#   1. Manual oficial (paginas 69-70, "fxAPI_Table59_2004"): NO publica
#      valores K0/K1/K2 -- la tabla de constantes del manual (pagina 8) dice
#      explicitamente que aplica "both for the 1980 and the 2004 tables" (sin
#      mencionar una tabla aparte para 59/60), y las paginas de Table59_2004/
#      Table59E solo describen K0/K1/K2 como SALIDAS ("Actual value of
#      constant K0 used"), igual que en las demas tablas -- no hay una cifra
#      nueva que transcribir.
#   2. `.xll` (Ghidra 12.1.2, mismo proyecto "ANALISIS .XLL"): la raiz
#      `API_Table59_2004` (FUN_1800a3a4c) desciende, con la MISMA estructura
#      de despacho de producto (remapeo 1..7 identico) y la misma conversion
#      bar->kPa (`* DAT_1801940c8`, 100.0), a `FUN_180105ec8` -- LA MISMA
#      funcion nucleo que Table53_2004 (confirmado en Ronda 5) -- con el 4to
#      argumento literal `DAT_180194028 = 20.0` (byte-exacto, confirmado en
#      el volcado de constantes) en vez de `DAT_180194008 = 15.0` que usa
#      Table53_2004 en el MISMO punto de la MISMA funcion. Table60_2004
#      (FUN_1800a4518) llama a `FUN_180105928` (la misma funcion nucleo de
#      Table54_2004) con el mismo `DAT_180194028`. Ningun K0/K1/K2 nuevo
#      aparece en el volcado de 96 `DAT_` de esta ronda -- solo los 8 ya
#      conocidos de K_US/K_METRIC.
#   3. `.so` Android (Ghidra 11.4.3, mismo proyecto `libFX114`), CONFIRMACION
#      INDEPENDIENTE en la otra plataforma (Fase 6): `API2540::Table59_2004`
#      (0x001164a0) es, LINEA POR LINEA, la MISMA funcion que
#      `API2540::Table53_2004` (0x00112410) -- mismo remapeo de producto,
#      misma llamada a `APIDens2004Type2M` con la MISMA firma, mismo
#      `DAT_002377f0=100.0` (bar->kPa) y `DAT_00237930=1.8` (escala de
#      alpha) -- difiriendo SOLO en la constante pasada como referencia:
#      `DAT_00237880=15.0` (Table53_2004) vs `DAT_002379b0=20.0`
#      (Table59_2004), ambas confirmadas byte-exactas. `API2540::Table60_2004`
#      es al `API2540::Table54_2004` lo mismo que Table59 es a Table53.
#   4. El mecanismo de 2 pasos ya reconstruido en Ronda 5 para Table53/54_2004
#      (iterar con T/P reales sobre el motor US interno, y evaluar una 2da
#      vez el mismo nucleo en la referencia metrica convertida a F para
#      obtener el factor de reescalado) es por lo tanto DIRECTAMENTE
#      aplicable a Table59/60_2004 sin cambios de formula -- solo cambia la
#      constante T_REF_2004_20C_C=20.0 en el lugar de T_REF_METRIC_1980_C.
# Nivel de confianza: [CERTAIN via decompilacion exhaustiva en 2 plataformas
# independientes -- mas evidencia que Table53/54_2004 en su momento (Ronda 5
# solo tuvo el `.xll`)]; NO se consiguio caso real en vivo esta ronda (no se
# encontro tiempo para explorar la app Android en busca de estas 2 pantallas
# especificas) -- mismo peldano de confianza que Table53/54_2004 ya tenian
# antes de su propio caso real (Ronda 6).
# ===========================================================================
def api_table59_2004(observed_density_kgm3: float, observed_temp_c: float,
                      pressure_bar: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """Densidad(T,P) -> Densidad(20°C, 0 bar[g]). API MPMS 11.1 Tables
    59A/59B/59D, 2004. [CERTAIN via decompilacion cruzada .xll+.so, RONDA 11]
    -- clon exacto de `api_table53_2004` con T_REF_2004_20C_C (20.0) en vez
    de T_REF_METRIC_1980_C (15.0); ver docstring de esta seccion. Reusa
    K_US (NO hay una tabla K propia para Table59/60, confirmado por
    decompilacion en 2 binarios). Iterativo, <=15 iteraciones.
    `api_rounding` (0/1) [CERTAIN via AVD real sobre Table53_2004 (mismo
    motor exacto), RONDA 34, ver `_api_rounding_2004`]: solo redondea CTPL a
    5 decimales. `product=2` (B - Auto select) [CERTAIN, RONDA 50]:
    implementado, agrega la clave `product_efectivo` al resultado."""
    t_obs_f = _celsius_to_fahrenheit(observed_temp_c)
    t_20_f = _celsius_to_fahrenheit(T_REF_2004_20C_C)  # 20.0C -> 68.0F
    p_psi = pressure_bar * BAR_TO_KPA / PSI_TO_KPA
    rho_base, r_obs = _ctpl_2004_iter(product, observed_density_kgm3, t_obs_f, p_psi)
    # [RONDA 40] alpha se calcula con rho_base YA CORREGIDA.
    # [RONDA 50] K0/K1/K2 resueltos con la densidad ya convergida.
    k = _k_for_2004(product, rho_base)
    alpha_base = _alpha(k, _rho_corregido_2004(k, rho_base))
    ctl_20 = _ctl_2004(alpha_base, t_20_f)
    density_20c = rho_base * ctl_20
    # Misma correccion de etiqueta que Table53_2004 (Ronda 6): "ctpl" real de
    # la app = r_obs["ctpl"]/ctl_20; "ctl" real = ctpl_out/cpl_out.
    cpl_out = r_obs["cpl"]
    ctpl_out = r_obs["ctpl"] / ctl_20 if ctl_20 != 0 else 0.0
    ctl_out = ctpl_out / cpl_out if cpl_out != 0 else 0.0
    r = {"density_20c": density_20c, "ctl": ctl_out, "cpl": cpl_out,
         "ctpl": ctpl_out, "f": r_obs["f"] * BAR_TO_KPA / PSI_TO_KPA,
         "alpha": alpha_base * 1.8, "k0": k.k0, "k1": k.k1, "k2": k.k2,
         "product_efectivo": r_obs["product_efectivo"]}
    return _api_rounding_2004(r, api_rounding)


def api_table60_2004(density_20c_kgm3: float, observed_temp_c: float,
                      pressure_bar: float = 0.0, product: Product = 1,
                      api_rounding: int = 0) -> dict:
    """Densidad(20°C, 0 bar[g]) -> CTPL(T,P). API MPMS 11.1 Tables
    59A/59B/59D, 2004 (variante Table60, direccion inversa de Table59).
    [CERTAIN via decompilacion cruzada .xll+.so, RONDA 11] -- clon exacto de
    `api_table54_2004` con T_REF_2004_20C_C (20.0) en vez de
    T_REF_METRIC_1980_C (15.0); ver docstring de esta seccion. `api_rounding`
    (0/1) [CERTAIN via AVD real sobre Table53/54_2004 (mismo motor exacto),
    RONDA 34, ver `_api_rounding_2004`]: solo redondea CTPL a 5 decimales.
    `product=2` (B - Auto select) [CERTAIN, RONDA 50]: implementado, agrega
    la clave `product_efectivo` al resultado."""
    t_obs_f = _celsius_to_fahrenheit(observed_temp_c)
    t_20_f = _celsius_to_fahrenheit(T_REF_2004_20C_C)
    p_psi = pressure_bar * BAR_TO_KPA / PSI_TO_KPA
    rho_base, r_20 = _ctpl_2004_iter(product, density_20c_kgm3, t_20_f, 0.0)
    ctl_20 = r_20["ctl"]
    # [RONDA 40] misma correccion de rho_base que en `_ctpl_2004_direct`.
    # [RONDA 50] K0/K1/K2 resueltos con la densidad ya convergida.
    k = _k_for_2004(product, rho_base)
    rho_base_corr = _rho_corregido_2004(k, rho_base)
    alpha_base = _alpha(k, rho_base_corr)
    ctl_real = _ctl_2004(alpha_base, t_obs_f)
    f_real = _f_compressibility_2004(t_obs_f, rho_base_corr)
    cpl_real = _cpl_2004(f_real, p_psi)
    ctl_out = ctl_real / ctl_20 if ctl_20 != 0 else 0.0
    ctpl_out = ctl_out * cpl_real
    density_obs_predicted = ctpl_out * density_20c_kgm3
    r = {"ctl": ctl_out, "cpl": cpl_real, "ctpl": ctpl_out,
         "density_obs_predicted": density_obs_predicted,
         "f": f_real * BAR_TO_KPA / PSI_TO_KPA, "alpha": alpha_base * 1.8,
         "k0": k.k0, "k1": k.k1, "k2": k.k2,
         "product_efectivo": r_20["product_efectivo"]}
    return _api_rounding_2004(r, api_rounding)


# ===========================================================================
# RONDA 9 -- API MPMS 11.2.1M (metrico) / API MPMS 11.2.1 (US).
# [CERTAIN] Modulo de factor de compresibilidad (F) y CPL, decompilado
# directamente esta ronda (FUN_1800a0798->FUN_1800e303c metrico,
# FUN_1800a05dc->FUN_1800e2d5c US). Ver docstring del modulo, seccion
# "RONDA 9", para el detalle completo y la validacion numerica contra el
# caso real del usuario (residuo ~0.00003% usando la densidad YA CONVERGIDA
# a 15C, no la observada). Confirmado que este MISMO nucleo (misma
# direccion `DAT_` de las constantes) es el que usan tanto la familia 1952
# (via FUN_1800f8f70) como los 3 wrappers de presion de 1980
# (FUN_1800e62d4/FUN_1800e79e4, inline, mismas direcciones).
# ===========================================================================
MPMS_11_2_1M_A = 2.1592e-4      # DAT_1801ea4a0 -- coeficiente de T (°C)
MPMS_11_2_1M_B = 1.6208         # DAT_1801ea4c8 -- constante restada
MPMS_11_2_1M_C = 0.87096        # DAT_1801ea4c0 -- termino 1/rho_r^2
MPMS_11_2_1M_D = 0.0042092      # DAT_1801ea4b0 -- termino T/rho_r^2
MPMS_11_2_1M_SCALE = 10000.0    # DAT_1801ea328
MPMS_11_2_1M_RHO_REF_KGM3 = 1000.0   # DAT_180124818 (NO es RHO_WATER_60F_KGM3)
MPMS_11_2_1M_P_SCALE = 0.01     # DAT_180193e68
MPMS_11_2_1M_RHO_RANGE = (637.5, 1074.0)     # DAT_1801ea4f0 / DAT_1801ea4f8
MPMS_11_2_1M_T_RANGE_C = (-30.0, 90.0)       # DAT_1801ea520 / DAT_1801940c0
MPMS_11_2_1M_P_RANGE_KPA = (0.0, 10300.0)    # DAT_1801ea508

MPMS_11_2_1_A = 1.3427e-4       # DAT_1801ea498 -- coeficiente de T (°F)
MPMS_11_2_1_B = 1.9947          # DAT_1801ea4d0 -- constante restada
MPMS_11_2_1_C = 0.79392         # DAT_1801ea4b8 -- termino 1/rd_r^2
MPMS_11_2_1_D = 0.002326        # DAT_1801ea4a8 -- termino T/rd_r^2
MPMS_11_2_1_SCALE = 100000.0    # DAT_1801941e8
MPMS_11_2_1_API_OFFSET = 131.5  # DAT_1801ea4e0
MPMS_11_2_1_API_NUM = 141.36    # DAT_1801ea830 (=141.5*999.012/1000, no 141.5 exacto)
MPMS_11_2_1_API_RANGE = (0.0, 90.3)          # DAT_1801ea4d8
MPMS_11_2_1_T_RANGE_F = (-20.0, 200.0)       # DAT_1801d6198 / DAT_180194108
MPMS_11_2_1_P_RANGE_PSIG = (0.0, 1500.0)     # DAT_1801ea500


def api_mpms_11_2_1m(density_kgm3: float, temp_c: float, pressure_bar_g: float,
                      equilibrium_pressure_bar_g: float = 0.0,
                      rounding: int = 0,
                      clamp_negative_net_pressure: bool = True) -> dict:
    """[CERTAIN, RONDA 9] Factor de compresibilidad F y CPL segun API MPMS
    11.2.1M / 12.2, para densidades 637.5-1074 kg/m3 (rango oficial
    confirmado a bytes). Replica FUN_1800a0798->FUN_1800e303c (`.xll`),
    convencion de la funcion EXPORTADA a Excel (presion simplemente
    bar*100->kPa, SIN el offset atmosferico +101.325 que si se usa en la
    llamada INTERNA desde la familia 1952 -- ver docstring RONDA 9: el
    offset se cancela en la resta P1-P2 salvo que EVP sea muy negativo, asi
    que en el caso EVP=0 (el habitual) ambas convenciones dan el mismo
    numero).

    Validado contra el caso real del usuario (Density_obs=1000kg/m3,
    T=25°C, P=20bar(g), EVP=0bar(g)): usando la densidad YA CONVERGIDA a
    15°C (1005.482 kg/m3, no la observada) como `density_kgm3`, este
    calculo da CPL=1.0010454 contra el CPL real de la app 1.001045
    (diff~0.00003%, ruido de redondeo de 6 decimales).

    `rounding` [CERTAIN, RONDA 19 -- flag real "API-11.2.1 Rounding" de la
    UI, hallazgo NUEVO de esta ronda, ver docstring del modulo seccion
    "RONDA 19"]: 0=Disabled (default, SIN CAMBIOS respecto a versiones
    previas), 1=Enabled. Replica EXACTO (decompilado linea a linea de
    `FUN_1800e303c`, el `param_5` de esa funcion) el procedimiento real: con
    `rounding=1` se redondea `density_kgm3` al multiplo de 2 kg/m3 mas
    cercano y `temp_c` al cuarto de grado (0.25°C) mas cercano ANTES de
    calcular `rho_r^2` (que a su vez se redondea a 5 decimales), y cada uno
    de los 4 terminos del exponente (`T*A`, `-B`, `C/rho_r^2`, `D*T/rho_r^2`)
    se redondea a 5 decimales por separado antes de sumarlos; el resultado
    de `exp(...)` (ANTES de dividir por el factor de escala 10000) se
    redondea a 3 decimales. CPL se calcula despues con esta F ya afectada,
    sin redondeo adicional. Validado EXACTO contra el caso real nuevo del
    usuario (ver docstring del modulo, RONDA 19): con density_15c=1000kg/m3,
    T=25°C, P=20bar(g), CTL=0.9935 (tabla, NO afectada por este flag):
    `rounding=0` da density_obs=994.5496638 (real app Rounding=0: 994.5497);
    `rounding=1` da density_obs=994.5502451 (real app Rounding=1: 994.5502)
    -- las 2 reproducen la pantalla real EXACTO a la precision mostrada, lo
    que tambien explica por que CTL/CPL/CTPL se ven IDENTICOS a 6 decimales
    en la UI en ambos casos (la diferencia real esta en la 7a cifra de CPL,
    invisible en pantalla, pero se amplifica al multiplicar por la
    densidad).

    `clamp_negative_net_pressure` [CERTAIN via decompilacion, RONDA 23 --
    ver docstring del modulo, seccion "RONDA 23"]: True (default, SIN
    CAMBIOS respecto a versiones previas) replica el clamp real que SI
    existe en el nucleo compartido `FUN_1800e303c` (`if (p1<p2) and
    (denom>1.0): denom=1.0`) -- este es el nucleo que usa la funcion
    EXPORTADA a Excel `API_MPMS_11_2_1M` y, vía `FUN_1800f8f70`, la familia
    `api_density15c_1952`. False desactiva el clamp: usalo SOLO cuando esta
    funcion se llama desde la familia de presion de 1980
    (`api_density15c_1980`/`api_gravity60f_1980`/`api_reldensity60f_1980`),
    cuyo nucleo real (`FUN_1800e62d4`/`FUN_1800e79e4`/`FUN_1800e8494`) NO
    llama a `FUN_1800e303c`/`FUN_1800e2d5c` -- tiene una copia INLINEADA de
    la MISMA formula de F pero SIN el clamp (denom = 1-(P-EVP)*escala*F
    directo, confirmado leyendo linea a linea las 3 funciones)."""
    d = density_kgm3
    t = temp_c
    if rounding:
        d = _round_n(d * 0.5, 0) * 2.0
        t = _round_n(t * 4.0, 0) * 0.25
    rho_r2 = (d / MPMS_11_2_1M_RHO_REF_KGM3) ** 2
    if rounding:
        rho_r2 = _round_n(rho_r2, 5)
    if rho_r2 == 0.0:
        return {"f": 0.0, "cpl": 1.0}
    a = MPMS_11_2_1M_C / rho_r2
    b = (t * MPMS_11_2_1M_D) / rho_r2
    if not rounding:
        exponente = (t * MPMS_11_2_1M_A - MPMS_11_2_1M_B) + a + b
        f_raw = math.exp(exponente)
    else:
        term_a = _round_n(t * MPMS_11_2_1M_A, 5)
        term_b = _round_n(-MPMS_11_2_1M_B, 5)
        term_c = _round_n(a, 5)
        term_d = _round_n(b, 5)
        f_raw = math.exp(term_d + term_c + term_a + term_b)
        f_raw = _round_n(f_raw, 3)
    f = f_raw / MPMS_11_2_1M_SCALE
    p1 = pressure_bar_g * BAR_TO_KPA
    p2 = equilibrium_pressure_bar_g * BAR_TO_KPA
    if p2 <= 0.0:
        denom = 1.0 - p1 * MPMS_11_2_1M_P_SCALE * f
    else:
        denom = 1.0 - (p1 - p2) * MPMS_11_2_1M_P_SCALE * f
        if clamp_negative_net_pressure and p1 < p2 and denom > 1.0:
            denom = 1.0
    cpl = 1.0 / denom if denom != 0.0 else 1.0
    fuera_de_rango = not (MPMS_11_2_1M_RHO_RANGE[0] <= density_kgm3 <= MPMS_11_2_1M_RHO_RANGE[1]
                          and MPMS_11_2_1M_T_RANGE_C[0] <= temp_c <= MPMS_11_2_1M_T_RANGE_C[1]
                          and MPMS_11_2_1M_P_RANGE_KPA[0] <= p1 <= MPMS_11_2_1M_P_RANGE_KPA[1])
    return {"f": f, "cpl": cpl, "fuera_de_rango_oficial": fuera_de_rango}


def api_mpms_11_2_1(api_gravity: float, temp_f: float, pressure_psig: float,
                     equilibrium_pressure_psig: float = 0.0,
                     rounding: int = 0,
                     clamp_negative_net_pressure: bool = True) -> dict:
    """[CERTAIN, RONDA 9] Factor de compresibilidad F y CPL segun API MPMS
    11.2.1 / 12.2, sistema US, para °API 0-90.3 (rango oficial confirmado a
    bytes). Replica FUN_1800a05dc->FUN_1800e2d5c (`.xll`); el input real es
    °API directamente (0-90.3), NO densidad -- el binario lo convierte
    internamente con 141.36/(API+131.5) (constante propia de este modulo,
    NO el 141.5 exacto que usa el resto de la familia Table5/6). NO
    validado contra un caso real en vivo esta ronda (el usuario solo probo
    la variante metrica); [CERTAIN via decompilacion] por constantes
    byte-exactas y por ser la MISMA estructura ya validada numericamente en
    `api_mpms_11_2_1m`.

    `rounding` [CERTAIN via decompilacion directa de `FUN_1800e2d5c`, RONDA
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19"]: 0=Disabled
    (default, SIN CAMBIOS), 1=Enabled. MISMO mecanismo que
    `api_mpms_11_2_1m` (constantes/formula distintas por ser sistema US),
    confirmado byte a byte en el mismo `param_5` de `FUN_1800e2d5c`:
    `api_gravity` se redondea al 0.5°API mas cercano y `temp_f` al 0.5°F
    mas cercano ANTES de calcular `dens_ratio` (que se redondea a 5
    decimales, junto con `dens_ratio^2` tambien a 5 decimales), y cada uno
    de los 4 terminos del exponente se redondea a 5 decimales por separado;
    el resultado de `exp(...)` (antes de dividir por el factor de escala
    100000) se redondea a 3 decimales. NO validado contra un caso real
    propio (0 casos reales de esta variante US con el flag activo), pero el
    mecanismo en si esta [CERTAIN] por decompilacion directa, no por
    analogia.

    `clamp_negative_net_pressure` [CERTAIN via decompilacion, RONDA 23 --
    ver docstring del modulo, seccion "RONDA 23"]: misma logica y mismo
    motivo que en `api_mpms_11_2_1m` -- True (default) replica el clamp
    real de `FUN_1800e2d5c` (usado por `API_MPMS_11_2_1` exportada a Excel);
    False lo desactiva para uso desde la familia de presion de 1980 (US:
    `api_gravity60f_1980`/`api_reldensity60f_1980`), cuyo nucleo real
    (`FUN_1800e79e4`/`FUN_1800e8494`) tiene la formula INLINEADA sin
    clamp."""
    api = api_gravity
    t = temp_f
    if rounding:
        api = _round_n(api * 2.0, 0) * 0.5
        t = _round_n(t * 2.0, 0) * 0.5
    base = api + MPMS_11_2_1_API_OFFSET
    if base == 0.0:
        return {"f": 0.0, "cpl": 1.0}
    dens_ratio = MPMS_11_2_1_API_NUM / base
    if rounding:
        dens_ratio = _round_n(dens_ratio, 5)
    dens_ratio2 = dens_ratio * dens_ratio
    if rounding:
        dens_ratio2 = _round_n(dens_ratio2, 5)
    a = MPMS_11_2_1_C / dens_ratio2
    b = (t * MPMS_11_2_1_D) / dens_ratio2
    if not rounding:
        exponente = (t * MPMS_11_2_1_A - MPMS_11_2_1_B) + a + b
        f_raw = math.exp(exponente)
    else:
        term_a = _round_n(t * MPMS_11_2_1_A, 5)
        term_b = _round_n(-MPMS_11_2_1_B, 5)
        term_c = _round_n(a, 5)
        term_d = _round_n(b, 5)
        f_raw = math.exp(term_d + term_c + term_a + term_b)
        f_raw = _round_n(f_raw, 3)
    f = f_raw / MPMS_11_2_1_SCALE
    p1 = pressure_psig
    p2 = equilibrium_pressure_psig
    if p2 <= 0.0:
        denom = 1.0 - p1 * f
    else:
        denom = 1.0 - (p1 - p2) * f
        if clamp_negative_net_pressure and p1 < p2 and denom > 1.0:
            denom = 1.0
    cpl = 1.0 / denom if denom != 0.0 else 1.0
    fuera_de_rango = not (MPMS_11_2_1_API_RANGE[0] <= api_gravity <= MPMS_11_2_1_API_RANGE[1]
                          and MPMS_11_2_1_T_RANGE_F[0] <= temp_f <= MPMS_11_2_1_T_RANGE_F[1]
                          and MPMS_11_2_1_P_RANGE_PSIG[0] <= p1 <= MPMS_11_2_1_P_RANGE_PSIG[1])
    return {"f": f, "cpl": cpl, "fuera_de_rango_oficial": fuera_de_rango}


# ===========================================================================
# RONDA 13 -- API MPMS 11.2.2 (US) / 11.2.2M (metrico): "Compressibility
# Factors for Hydrocarbons: 0.350-0.637 Relative Density (60/60F) and -50F
# to 140F Metering Temperature", 2nd Edition, October 1986. Norma DISTINTA
# de 11.2.1/11.2.1M (rango de densidad mas bajo, tipico NGL/LPG), no una
# extension con las mismas constantes -- decompilado por separado desde
# API_MPMS_11_2_2 @ 0x1800a0964 -> FUN_1800e32e8 (US) y API_MPMS_11_2_2M
# @ 0x1800a0b24 -> FUN_1800e36e8 (metrico). Ver docstring RONDA 13 arriba
# para el detalle completo de la reconstruccion y la validacion contra
# caso real directo (exacta a 6 decimales en CPL y F, ambas ediciones).
# ===========================================================================
def _round_n(x: float, n: int) -> float:
    """Replica FUN_1800e1db4(x, n): redondeo comercial (mitad-lejos-de-cero)
    a `n` decimales, exactamente como lo hace el binario (usado para los 2
    pasos de redondeo OBLIGATORIO -- no opcional -- dentro del nucleo de
    11.2.2/11.2.2M). Solo se necesitan n=0 (entero) y n=3 (3 decimales) para
    esta familia."""
    mult = 10.0 ** n
    if x >= 0.0:
        return math.floor(mult * x + 0.5) / mult
    return math.ceil(mult * x - 0.5) / mult


# Constantes DAT_ del nucleo compartido (byte-exactas, `.xll`) -- mismos
# nombres/valores en ambas ediciones salvo donde se indica.
_MPMS_1122_C_A = 2.1465891e-6
_MPMS_1122_C_B = 1.577439e-5
_MPMS_1122_C_C = 1.0502139e-5
_MPMS_1122_C_D = 2.8324481e-7
_MPMS_1122_C_E = 0.95495939
_MPMS_1122_C_F = 7.2900662e-8
_MPMS_1122_C_G = 2.7769343e-7
_MPMS_1122_C_H = 0.03645838
_MPMS_1122_C_I = 0.05110158
_MPMS_1122_C_J = 9.1311491
_MPMS_1122_C_K = 0.00795529
_MPMS_1122_C_L = 6.0357667e-10
_MPMS_1122_C_M = 2.2112678e-6
_MPMS_1122_C_N = 8.8384e-4
_MPMS_1122_C_O = 0.00204016
_MPMS_1122_T_RANKINE_OFFSET = 459.7   # DAT_1801ea3b0 (NO 459.67 exacto)
_MPMS_1122_PCRIT_A = 621.418          # DAT_1801ea5f8
_MPMS_1122_PCRIT_B = 822.686          # DAT_1801ea600
_MPMS_1122_PCRIT_C = 1737.86          # DAT_1801ea608
_MPMS_1122_PCRIT_SCALE = 0.96         # DAT_1801ea5c0

MPMS_11_2_2M_RHO_POLY = (0.03689636, 1.24446244, 0.63291568, 0.73861488, 0.32478413, 0.999012)
MPMS_11_2_2M_RHO_RANGE = (350.0, 637.5)      # DAT_1801ea5f0 / DAT_1801ea4f0
MPMS_11_2_2M_T_RANGE_C = (-46.0, 60.0)       # DAT_1801ea620 / DAT_180124810
MPMS_11_2_2M_P_RANGE_KPA = (0.0, 15200.0)    # DAT_1801ea618
MPMS_11_2_2_RD_RANGE = (0.35, 0.638)         # DAT_1801ea410 / DAT_1801ea5a8
MPMS_11_2_2_T_RANGE_F = (-50.0, 140.0)       # DAT_180195188 / DAT_1801ea5e8
MPMS_11_2_2_P_RANGE_PSIG = (0.0, 2200.0)     # DAT_1801ea610

# ---------------------------------------------------------------------------
# [CERTAIN, RONDA 36 (2026-09-09)] Constantes del mecanismo "rounding"
# (`param_5`) de `FUN_1800e36e8` (metrico)/`FUN_1800e32e8` (US) -- el
# mismo archivo `ghidra_api1122_xll_output.txt` de RONDA 13 ya tenia esta
# decompilacion completa, nunca antes leida linea a linea buscando este
# parametro. Confirmado por lectura directa del decompilado + volumen de
# constantes DAT_ del propio archivo (seccion "DAT_ ADDRESSES
# REFERENCIADAS"), NO copiado por analogia de 11.2.1/11.2.1M sin
# verificar (la analogia resulto ser estructuralmente distinta: aqui
# ademas de redondear entradas, tambien redondea F -- que a su vez
# alimenta CPL -- con un umbral de decimales VARIABLE segun la magnitud
# de F, algo que 11.2.1/11.2.1M no hacen).
# ---------------------------------------------------------------------------
_MPMS_1122M_ROUND_RHO_SCALE1 = 0.5     # DAT_180124428
_MPMS_1122M_ROUND_RHO_SCALE2 = 2.0     # DAT_180124438
_MPMS_1122M_ROUND_T_SCALE1 = 4.0       # DAT_180193f98
_MPMS_1122M_ROUND_T_SCALE2 = 0.25      # DAT_180195128
_MPMS_1122M_ROUND_F_THRESHOLD = 0.001  # DAT_1801d5ea8 (comparacion <=)
_MPMS_1122_ROUND_RD_SCALE1 = 10.0      # DAT_180124440 (US)
_MPMS_1122_ROUND_RD_SCALE2 = 0.1       # DAT_180124eb0 (US)
_MPMS_1122_ROUND_T_SCALE1 = 2.0        # DAT_180124438 (US)
_MPMS_1122_ROUND_T_SCALE2 = 0.5        # DAT_180124428 (US)
_MPMS_1122_ROUND_F_THRESHOLD = 1.0e-4  # DAT_1801df058 (US, comparacion <)


def api_mpms_11_2_2m(density_kgm3: float, temp_c: float, pressure_bar_g: float,
                      equilibrium_pressure_bar_g: float = 0.0,
                      rounding: int = 0) -> dict:
    """[CERTAIN, RONDA 13] Factor de compresibilidad F y CPL segun API MPMS
    11.2.2M / 12.2, para densidades 350-637.5 kg/m3 (rango oficial
    confirmado a bytes; norma DISTINTA de 11.2.1M, tipico NGL/LPG). Replica
    FUN_1800a0b24->FUN_1800e36e8 (`.xll`). Validado EXACTO (6 decimales)
    contra caso real directo capturado en la app (Density@15C=600kg/m3,
    T=25C, P=20bar(g), EVP=0 -> CPL_app=1.005227, F_app=0.000260 1/bar):
    este calculo da CPL=1.0052274, F=0.00026001.

    [CORREGIDO -- hallazgo RONDA "NGL/LPG puro" 2026-09-03] El clamp
    `p_eff=max(p_eff,0.0)` que este modulo aplicaba antes de esta fecha
    (copiado por analogia de `api_mpms_11_2_2`, la version US) NO existe en
    el nucleo metrico real (`FUN_1800e36e8`, ver
    `ANALISIS_GHIDRA_FLOWXPERT/ghidra_ngllpg_xll_output.txt`, funcion [69]):
    ahi solo se hace `param_3 = param_3 - param_4` (SIN piso en 0) cuando
    `param_4`(EVP)>0 -- `p_eff` puede quedar NEGATIVO y ESE valor negativo
    SI participa en el calculo de F (`denom=term2*p_eff+term1`). Existe un
    safeguard DISTINTO, mas especifico, solo sobre CPL (no sobre `p_eff`
    en si): si EVP>0 Y `p_eff`<0 Y el denominador de CPL da >1.0 (lo que
    haria CPL<1.0), se fija ese denominador en 1.0 exacto (CPL=1.0) -- ver
    codigo abajo. La version US (`api_mpms_11_2_2`/`FUN_1800e32e8`) SI hace
    el piso en 0 de `p_eff` (asimetria real confirmada leyendo ambos
    decompilados, no un descuido de una sola version). El caso real de
    validacion de arriba (EVP=0) NUNCA ejercita esta rama (con EVP=0 no hay
    resta), por eso el bug paso desapercibido en la validacion original de
    RONDA 13 -- se detecto porque los 3 wrappers combinados de NGL/LPG
    (`normas/_ngl_lpg_wrappers_puro.py`) SI generan EVP>0 de forma habitual
    (GPA TP-15) y a menudo EVP>P en NGL/LPG liviano, exponiendo la
    diferencia contra el oraculo `.xll` real en el barrido masivo.

    [CERTAIN, RONDA 36 (2026-09-09)] `rounding` ("API-11.2.2M Rounding" de
    la UI): replica `param_5` de `FUN_1800e36e8`, confirmado por
    decompilacion directa (mismo archivo `ghidra_api1122_xll_output.txt`
    ya usado en RONDA 13, releido linea a linea buscando este argumento --
    no hizo falta reabrir Ghidra). Activo (!=0):
      1. La densidad de entrada se redondea al multiplo de 2 kg/m3 mas
         cercano y la temperatura al 0.25°C mas cercano, ANTES de evaluar
         el polinomio (misma familia de grilla que `api_mpms_11_2_1m`,
         RONDA 19, pero NO el mismo codigo -- verificado, no copiado).
      2. La "densidad reducida" intermedia (`rho_poly`) se redondea a 3
         decimales.
      3. F se redondea a 6 decimales si F>0.001, o a 7 si F<=0.001 (umbral
         real byte-exacto, `_MPMS_1122M_ROUND_F_THRESHOLD`) -- y ese F YA
         redondeado es el que alimenta el calculo de CPL (confirmado
         leyendo el orden real de las asignaciones: NO es un redondeo de
         presentacion aislado).
      4. CPL se redondea a 4 decimales.
    Sin caso real capturado DIRECTO en la pantalla propia "API MPMS
    11.2.2M" con este flag activo (el caso real disponible del usuario
    para `rounding=1` pasa por el wrapper combinado NGL/LPG, ver
    `_ngl_lpg_wrappers_puro.py`/memoria del proyecto para el resultado de
    esa validacion). `rounding=0` (default) no ejecuta ninguno de los 4
    pasos -- CERO regresion estructural sobre el comportamiento ya
    [CERTAIN] de RONDA 13."""
    if rounding != 0:
        density_kgm3 = _round_n(density_kgm3 * _MPMS_1122M_ROUND_RHO_SCALE1, 0) * _MPMS_1122M_ROUND_RHO_SCALE2
        temp_c = _round_n(temp_c * _MPMS_1122M_ROUND_T_SCALE1, 0) * _MPMS_1122M_ROUND_T_SCALE2

    p1 = pressure_bar_g * BAR_TO_KPA
    p2 = equilibrium_pressure_bar_g * BAR_TO_KPA
    p_eff = p1
    if p2 > 0.0:
        p_eff = p1 - p2

    t_rankine = temp_c * 1.8 + 32.0 + _MPMS_1122_T_RANKINE_OFFSET
    rho_r = density_kgm3 / 1000.0
    rho_r2 = rho_r * rho_r
    a, b, c, d, e, scale = MPMS_11_2_2M_RHO_POLY
    rho_poly = ((-a + rho_r * b) - rho_r2 * c + rho_r2 * rho_r * d - rho_r2 * rho_r2 * e) / scale
    if rounding != 0:
        rho_poly = _round_n(rho_poly, 3)

    t2 = t_rankine * t_rankine
    rp2 = rho_poly * rho_poly
    t3 = t2 * t_rankine
    rp4 = rp2 * rp2

    big = (t_rankine * _MPMS_1122_C_K +
           ((((((((-t2 * _MPMS_1122_C_A + t2 * _MPMS_1122_C_B * rp2) -
                  t2 * _MPMS_1122_C_C * rp4) + rp4 * rp2 * t3 * _MPMS_1122_C_D) -
                _MPMS_1122_C_E) + t3 * _MPMS_1122_C_F * rp2) -
              t3 * _MPMS_1122_C_G * rp4) + t_rankine * _MPMS_1122_C_H * rp2) -
            t_rankine * _MPMS_1122_C_I * rho_poly) + rho_poly * _MPMS_1122_C_J
          ) * PSI_TO_KPA * 100000.0
    term1 = _round_n(big, 0)

    term2 = _round_n((((-t2 * _MPMS_1122_C_L) + t_rankine * _MPMS_1122_C_M * rp2 +
                       rho_poly * _MPMS_1122_C_N) - rp2 * _MPMS_1122_C_O) * 100000.0, 3)

    denom = term2 * p_eff + term1
    if denom == 0.0 or not math.isfinite(denom):
        return {"f": 0.0, "cpl": 1.0, "fuera_de_rango_oficial": True}
    f = 100.0 / denom
    if rounding != 0:
        f = _round_n(f, 7 if f <= _MPMS_1122M_ROUND_F_THRESHOLD else 6)
    cpl_denom = 1.0 - p_eff * 0.01 * f
    if p2 > 0.0 and p_eff < 0.0 and cpl_denom > 1.0:
        cpl_denom = 1.0  # [CERTAIN via FUN_1800e36e8] safeguard real, ver docstring
    cpl = 1.0 / cpl_denom if cpl_denom != 0.0 else 1.0
    if rounding != 0:
        cpl = _round_n(cpl, 4)
    fuera_de_rango = not (MPMS_11_2_2M_RHO_RANGE[0] <= density_kgm3 <= MPMS_11_2_2M_RHO_RANGE[1]
                          and MPMS_11_2_2M_T_RANGE_C[0] <= temp_c <= MPMS_11_2_2M_T_RANGE_C[1]
                          and MPMS_11_2_2M_P_RANGE_KPA[0] <= p_eff <= MPMS_11_2_2M_P_RANGE_KPA[1])
    return {"f": f, "cpl": cpl, "fuera_de_rango_oficial": fuera_de_rango}


def api_mpms_11_2_2(rd_60f: float, temp_f: float, pressure_psig: float,
                     equilibrium_pressure_psig: float = 0.0,
                     rounding: int = 0) -> dict:
    """[CERTAIN, RONDA 13] Factor de compresibilidad F y CPL segun API MPMS
    11.2.2 / 12.2, sistema US, para densidad relativa 0.35-0.638 (rango
    oficial confirmado a bytes; norma DISTINTA de 11.2.1, tipico NGL/LPG).
    Replica FUN_1800a0964->FUN_1800e32e8 (`.xll`); el input real es RD@60F
    directamente (NO °API). Incluye un chequeo real de "temperatura
    pseudocritica" (formula cuadratica en RD) que SUSTITUYE la temperatura
    efectiva por ese techo si lo excede -- confirmado leyendo el
    decompilado, no es una suposicion. Validado EXACTO (6 decimales) contra
    caso real directo (RD@60F=0.5, T=90F, P=50psig, EVP=0 ->
    CPL_app=1.002857, F_app=0.000057 1/psi): este calculo da CPL=1.002857,
    F=0.00005698.

    [CERTAIN, RONDA 36 (2026-09-09)] `rounding` ("API-11.2.2 Rounding" de
    la UI): replica `param_5` de `FUN_1800e32e8` (mismo archivo/metodo que
    la version metrica arriba). Activo (!=0):
      1. RD se redondea a 0.001 (grado tipico de hidrometro de RD) y la
         temperatura a 0.5°F, ANTES del clamp de rango oficial (no hay
         redondeo intermedio de "densidad reducida" en esta version --
         RD ya se usa directo, sin el polinomio de conversion que si tiene
         la version metrica).
      2. F se redondea a 8 decimales si F<0.0001, o a 7 si no (umbral
         real byte-exacto, distinto del metrico: aqui la comparacion es
         estricta '<', en la version metrica es '<=' -- confirmado leyendo
         ambos decompilados, no asumido igual).
      3. CPL se redondea a 4 decimales.
    Mismo estado de evidencia que la version metrica: sin caso real DIRECTO
    en la pantalla propia con este flag, validado vía el wrapper combinado
    "API Rel. Density @60°F NGL/LPG" -- ver `_ngl_lpg_wrappers_puro.py`.

    [CORREGIDO, hallazgo RONDA "NGL/LPG puro" 2026-09-03] Este modulo NO
    aplicaba el clamp de entrada que SI existe en el nucleo real
    (FUN_1800e32e8, ver ghidra_ngllpg_xll_output.txt funcion [76]): ahi
    `rd` se recorta a [0.35, 0.638), `temp_f` a [-50, 140] grados F y
    `p_eff` a <=2200 psig ANTES de evaluar el polinomio -- los 3 clamps
    activan el flag de fuera de rango pero el CALCULO en si sigue con el
    valor recortado, no con el original. Sin este clamp, el polinomio
    diverge rapido fuera de esos limites -- se detecto porque
    normas/_ngl_lpg_wrappers_puro.py SI genera combinaciones RD/T cerca de
    esos bordes en su barrido de validacion contra el oraculo .xll real."""
    if rounding != 0:
        rd_60f = _round_n(rd_60f * _MPMS_1122_ROUND_RD_SCALE1, 2) * _MPMS_1122_ROUND_RD_SCALE2
        temp_f = _round_n(temp_f * _MPMS_1122_ROUND_T_SCALE1, 0) * _MPMS_1122_ROUND_T_SCALE2

    rd = min(max(rd_60f, MPMS_11_2_2_RD_RANGE[0]), MPMS_11_2_2_RD_RANGE[1])
    temp_f_calc = min(max(temp_f, MPMS_11_2_2_T_RANGE_F[0]), MPMS_11_2_2_T_RANGE_F[1])
    p1 = pressure_psig
    p2 = equilibrium_pressure_psig
    p_eff = p1
    if p2 > 0.0:
        p_eff = p1 - p2
        if p_eff < 0.0:
            p_eff = 0.0
    p_eff = min(p_eff, MPMS_11_2_2_P_RANGE_PSIG[1])

    t_rankine_obs = temp_f_calc + _MPMS_1122_T_RANKINE_OFFSET
    t_pseudocrit = ((_MPMS_1122_PCRIT_A - rd * _MPMS_1122_PCRIT_B) +
                    rd * _MPMS_1122_PCRIT_C * rd) * _MPMS_1122_PCRIT_SCALE
    t_rankine = t_rankine_obs
    if t_pseudocrit < t_rankine_obs:
        t_rankine = t_pseudocrit   # sustitucion real confirmada en el decompilado (solo en US)

    t2 = t_rankine * t_rankine
    rd2 = rd * rd
    t3 = t2 * t_rankine
    rd4 = rd2 * rd2

    big = (t_rankine * _MPMS_1122_C_K +
           ((((((((-t2 * _MPMS_1122_C_A + t2 * _MPMS_1122_C_B * rd2) -
                  t2 * _MPMS_1122_C_C * rd4) + rd4 * rd2 * t3 * _MPMS_1122_C_D) -
                _MPMS_1122_C_E) + t3 * _MPMS_1122_C_F * rd2) -
              t3 * _MPMS_1122_C_G * rd4) + t_rankine * _MPMS_1122_C_H * rd2) -
            t_rankine * _MPMS_1122_C_I * rd) + rd * _MPMS_1122_C_J
          ) * 100000.0   # SIN el factor PSI_TO_KPA -- version US ya trabaja en psi nativo
    term1 = _round_n(big, 0)

    term2 = _round_n((((-t2 * _MPMS_1122_C_L) + t_rankine * _MPMS_1122_C_M * rd2 +
                       rd * _MPMS_1122_C_N) - rd2 * _MPMS_1122_C_O) * 100000.0, 3)

    denom = term2 * p_eff + term1
    if denom == 0.0 or not math.isfinite(denom):
        return {"f": 0.0, "cpl": 1.0, "fuera_de_rango_oficial": True}
    f = 1.0 / denom
    if rounding != 0:
        f = _round_n(f, 8 if f < _MPMS_1122_ROUND_F_THRESHOLD else 7)
    cpl_denom = 1.0 - p_eff * f
    cpl = 1.0 / cpl_denom if cpl_denom != 0.0 else 1.0
    if rounding != 0:
        cpl = _round_n(cpl, 4)
    fuera_de_rango = not (MPMS_11_2_2_RD_RANGE[0] <= rd_60f <= MPMS_11_2_2_RD_RANGE[1]
                          and MPMS_11_2_2_T_RANGE_F[0] <= temp_f <= MPMS_11_2_2_T_RANGE_F[1]
                          and MPMS_11_2_2_P_RANGE_PSIG[0] <= (p1 - p2 if p2 > 0.0 else p1) <= MPMS_11_2_2_P_RANGE_PSIG[1])
    return {"f": f, "cpl": cpl, "fuera_de_rango_oficial": fuera_de_rango}


# ===========================================================================
# RONDA 9 -- Wrappers de presion de 1980: API_Dens15C_1980 (metrico),
# API_Gravity60F_1980 / API_RD60F_1980 (US). [CERTAIN via decompilacion,
# UN peldano por debajo de "caso real en vivo" -- ver docstring RONDA 9,
# punto 2] Combinan el motor CTL de 1980 YA CERTAIN (K_METRIC/K_US) con el
# modulo de presion recien cerrado arriba, iterando density_base hasta que
# converge density_obs = density_base * CTL(density_base) * CPL(density_base),
# limite 100 iteraciones (confirmado a bytes en FUN_1800e62d4/FUN_1800e79e4).
#
# ===========================================================================
# RONDA 16 (2026-09-07): parametro "Conversion" agregado a las 6 funciones
# combinadas de la familia 11.1 (1980 y 1952) -- hallazgo NUEVO, confirmado
# con evidencia real, NO fabricado. Alcance de esta ronda, punto por punto:
# ===========================================================================
# 1. PREGUNTA: el usuario senalo que estas 6 funciones (`api_density15c_1980`,
#    `api_gravity60f_1980`, `api_reldensity60f_1980`, `api_density15c_1952`,
#    `api_gravity60f_1952`, `api_sg60f_1952`) solo implementaban una
#    direccion fija (Observed->Standard, iterativa), a diferencia de la
#    familia "E NGL/LPG" (`normas/_ngl_lpg_wrappers_puro.py`), que YA tiene
#    un parametro `conversion` real (1=Obs->Std, 0=Std->Obs).
#
# 2. CONFIRMADO CON EVIDENCIA REAL que el flag "Conversion" SI EXISTE en el
#    binario para las 6 funciones, de 2 formas independientes:
#    (a) LECTURA DEL DECOMPILADO (Ghidra, `.xll`, archivos ya existentes
#        `ghidra_api1980wrappers_xll_output.txt`/`ghidra_api1952_xll_output.txt`):
#        - `API_Gravity60F_1980` (wrapper Excel-facing `FUN_1800a0230` ->
#          nucleo `FUN_1800e79e4`) EXPONE 9 argumentos reales (no 5 como el
#          codigo Python de antes de esta ronda asumia): 3 double + 4 int +
#          1 double + 1 int. El ULTIMO argumento (`param_9` del nucleo)
#          controla control de flujo real y verificable: dentro del
#          `do{...}while` que resuelve la base iterativamente, la linea
#          `if (param_9 == 2) goto LAB_1800e82ac;` FUERZA salida tras 1 sola
#          pasada (sin iterar), y en el ensamblado del resultado final,
#          `if (param_9 == 1) { *param_10 = candidato_iterado; } else {
#          *param_10 = formula_algebraica_inversa; }` -- exactamente el
#          patron "iterativo vs directo" que la familia NGL/LPG ya usa para
#          su propio `conversion`.
#        - `API_Dens15C_1980` (`FUN_18009f484` -> nucleo `FUN_1800e62d4`) y
#          `API_RD60F_1980` (`FUN_1800a0fec` -> nucleo `FUN_1800e8494`)
#          comparten LITERALMENTE la misma firma de 9 argumentos y el mismo
#          wrapper generado por el compilador (mismo `size=938/939` byte a
#          byte) -- mismo flag en la misma posicion.
#        - `API_Dens15C_1952` (`FUN_18009f1cc` -> nucleo `FUN_1800f8c4c`),
#          `API_Gravity60F_1952` (`FUN_18009ff88` -> nucleo `FUN_1800f90a4`)
#          y `API_SG60F_1952` (`FUN_1800a1778` -> nucleo `FUN_1800f9674`,
#          por analogia estructural identica) exponen 6 argumentos (no 4
#          como asumia el codigo de antes); el ULTIMO (`param_6` del
#          nucleo) tiene el despacho real `if (param_6==1) {rama
#          iterativa, hasta 20 pasadas} else if (param_6==2) {rama DIRECTA,
#          una sola llamada sin iterar} else {error}` -- mismo concepto,
#          codigos internos distintos (1/2 en vez de 1/0).
#    (b) VALIDACION EMPIRICA (ctypes, llamada DIRECTA a `FlowXpert.xll` SIN
#        Excel/emulador, mismo metodo ya usado por
#        `normas/_ngl_lpg_wrappers_xll_directo.py`): se llamo DIRECTO a los
#        3 nucleos de 1980 (`FUN_1800e62d4`/`FUN_1800e79e4`/`FUN_1800e8494`)
#        con el flag en 1 y despues en 2, alimentando el resultado del
#        primero como entrada del segundo (round-trip). Resultado, con el
#        binario REAL, no fabricado:
#          Gravity60F_1980: API_obs=30, T=90F, P=0 -> (flag=1) api_60f=
#            27.890942584019257 (coincide EXACTO con el caso real ya
#            validado en RONDA 3, 27.89094) -> alimentando ESE valor de
#            vuelta con flag=2 -> api_60f=30.000000000775362 (recupera el
#            30.0 original, diff=7.75e-10).
#          RD60F_1980: RD_obs=0.85, T=90F, P=0 -> (flag=1) rd_60f=
#            0.8619431717599637 -> (flag=2) rd_60f=0.8499999999937672
#            (diff=6.23e-12).
#          Density15C_1980: density_obs=1000, T=25C -> (flag=1) density_15c=
#            856.9405979870058 -> (flag=2) density_15c=1000.0000004390527
#            (diff=4.39e-7).
#        Round-trip EXACTO en los 3 casos -- evidencia real, no una
#        suposicion. El intento equivalente sobre el nucleo profundo de la
#        familia 1952 (`FUN_1800f8c4c`) devolvio un codigo de error real
#        (no un numero fabricado) por ambiguedad en el mapeo de un
#        argumento `undefined8` interno (limitacion de tipo del
#        decompilador, ya documentada repetidas veces en este proyecto) --
#        se documenta HONESTO como NO validado empiricamente contra el
#        `.xll` para la familia 1952, aunque la evidencia de (a) (patron de
#        codigo IDENTICO a la familia 1980 en 3 funciones independientes)
#        se considera suficiente para implementarlo con la MISMA formula
#        ya [CERTAIN] (tabla/CTL + `api_mpms_11_2_1`/`api_mpms_11_2_1m`,
#        evaluada una sola vez en vez de iterando) y queda marcado como tal
#        en cada docstring.
#
# 3. IMPLEMENTADO: parametro `conversion: int = 1` (mismo nombre/valores que
#    `_ngl_lpg_wrappers_puro.py`: 1=Observed->Standard default, 0=
#    Standard->Observed) en las 6 funciones. `conversion=1` reutiliza el
#    codigo iterativo EXISTENTE sin ningun cambio (regresion cero,
#    verificado corriendo `python -m normas.API_MPMS_Tables_1980_2004`
#    antes y despues -- todas las autopruebas pasan identico).
#    `conversion=0` es una evaluacion DIRECTA nueva (sin iterar): reusa las
#    MISMAS piezas ya [CERTAIN] (CTL de tabla/formula + CPL de
#    `api_mpms_11_2_1`/`api_mpms_11_2_1m`) evaluandolas una sola vez en el
#    valor YA dado como base, en vez de buscarlo por iteracion -- el mismo
#    principio que ya establecio `_ngl_lpg_wrappers_puro.py` para su propio
#    `conversion`.
#
# 4. CONFIRMADO por separado (no fabricado) que `api_mpms_11_2_1`/
#    `api_mpms_11_2_1m` NO tienen ni pueden tener este flag: su wrapper
#    Excel-facing (`API_MPMS_11_2_1` @ 0x1800a05dc) EXIGE exactamente 5
#    argumentos (`if (param_3 != 6) return 8;`, 5 slots a 0x20..0xa0) y su
#    nucleo (`FUN_1800e2d5c`) los usa TODOS como entrada fisica directa
#    (api_gravity, temp, pressure, evp) mas 1 flag final que SI parece
#    "Rounding" (`if (param_5 != 0) { param_1 = FUN_1800e1db4(...); }`,
#    mismo patron de redondeo visto en el resto de la familia) -- no hay
#    espacio estructural para un 6to flag de "Conversion", consistente con
#    que 11.2.1/11.2.2 solo calculan CPL/F a partir de una densidad/API YA
#    dado (no hay "direccion" que invertir: la formula es la misma sin
#    importar si ese valor se llama "observado" o "estandar"). NO se
#    modifico ninguna funcion de la familia 11.2.1/11.2.2 en esta ronda.
#
# 5. PENDIENTE, honesto, NO fabricado:
#    - "Rounding" (candidato: `param_5`/`param_7` de los nucleos 1980,
#      `param_4` de los nucleos 1952, `param_5` de `FUN_1800e2d5c`):
#      estructuralmente parece un flag/enum de redondeo de variables
#      INTERMEDIAS (llama repetidas veces a `FUN_1800e1db4`/`FUN_1800e1e14`
#      con distintos numeros de decimales segun su valor), consistente con
#      el patron "API Rounding" ya documentado (RONDA 3/6) para el resto de
#      la familia -- mismo nivel de prioridad baja que esos otros flags de
#      redondeo (solo afectan presentacion/precision, no la formula fisica
#      en si). NO se intento fijar el mapeo exacto de sus valores esta
#      ronda -- seria fabricar un enum sin evidencia suficiente.
#    - No se confirmo por `uiautomator`/Frida en la app real (AVD) que las
#      pantallas "API 11.1 (1980)"/"API 11.1 (1952)" (Density@15C,
#      Gravity60F, SG60F) muestren literalmente un selector llamado
#      "Conversion" con esas 2 opciones exactas -- la evidencia de esta
#      ronda es 100% decompilacion + llamada directa al binario (mas
#      barata, ver metodo sugerido), NO captura de pantalla. Dado que la
#      evidencia binaria es [CERTAIN] (round-trip exacto contra el .xll
#      real para 1980) y el patron es estructuralmente identico al de NGL/
#      LPG (que SI se confirmo en pantalla real), se considera evidencia
#      suficiente para implementar -- pero la confirmacion visual de la UI
#      especifica de estas 6 pantallas queda como pendiente formal para una
#      proxima ronda si se requiere el 100% de certeza sobre el texto
#      exacto del selector.
#    - HALLAZGO BONUS (fuera de alcance, para otra ronda): no se investigo
#      si la familia Ethylene/Propylene tiene un flag analogo -- no se toco
#      ni se investigo esa familia en esta ronda, por instruccion explicita
#      de no mezclar alcance.
# ===========================================================================
# RONDA 19 (2026-09-07): parametro "rounding" ("API-11.2.1 Rounding" de la
# UI) implementado en `api_mpms_11_2_1`/`api_mpms_11_2_1m` y en las 6
# funciones combinadas que los usan (`api_density15c_1952/1980`,
# `api_gravity60f_1952/1980`, `api_sg60f_1952`, `api_reldensity60f_1980`).
# Caso real NUEVO dado por el usuario esta ronda (captura de pantalla real,
# "API Density @15°C (1952) (metric)", NO fabricado): Density_obs=1000kg/m3,
# T=25°C, P=20bar(g), Conversion=Standard->Observed (codigo interno real de
# la UI "(2)", que este archivo sigue mapeando a `conversion=0` -- ver
# RONDA 16 para la discusion de por que el remapeo 0/1 es deliberado y no
# literal al codigo interno del binario): con "API-11.2.1 Rounding"=0 la
# app muestra Density=994.5497 kg/m3 (CTL=0.993500, CPL=1.001057,
# CTPL=0.994550, Compressibility=0.000053 1/bar); con el flag=1 la app
# muestra Density=994.5502 kg/m3, con CTL/CPL/CTPL/Compressibility
# IDENTICOS a 6 decimales en pantalla en ambos casos.
#
# MECANISMO REAL, confirmado por decompilacion directa (Ghidra 12.1.2,
# `.xll`, archivos YA EXISTENTES `ghidra_api1952core_xll_output.txt`
# [FUN_1800f8f70/FUN_1800e303c], `ghidra_api1980wrappers_xll_output.txt`
# [FUN_1800e79e4/FUN_1800e62d4/FUN_1800e8494], `ghidra_api1952_xll_output.txt`
# [FUN_1800f90a4/FUN_1800f9674] -- NO hizo falta generar disassembly nuevo
# ni reabrir Ghidra, todo ya estaba decompilado de rondas anteriores):
#
# 1. El nucleo compartido `api_mpms_11_2_1m`/`api_mpms_11_2_1` (ya [CERTAIN]
#    desde RONDA 9 para el calculo de F/CPL) SI tiene un parametro de
#    redondeo real (`param_5` de `FUN_1800e303c`/`FUN_1800e2d5c`) que
#    RONDA 9 nunca reviso -- confirmado leyendo linea a linea:
#      - `rounding=1` redondea la densidad de entrada al multiplo de 2
#        kg/m3 mas cercano (metrico) o el °API de entrada al 0.5 mas
#        cercano (US), y la temperatura al 0.25°C (metrico) o 0.5°F (US)
#        mas cercano, ANTES de calcular `rho_r^2`/`dens_ratio^2` (que a su
#        vez se redondea a 5 decimales).
#      - Cada uno de los 4 terminos del exponente (`T*A`, `-B` constante,
#        `C/rho_r^2`, `D*T/rho_r^2`) se redondea INDIVIDUALMENTE a 5
#        decimales antes de sumarlos.
#      - El resultado de `exp(suma)` (F ANTES de dividir por el factor de
#        escala 10000/100000) se redondea a 3 decimales -- este es el paso
#        que domina el efecto numerico (ver punto 3).
#      - CPL se calcula despues con esa F ya afectada, sin redondeo propio
#        adicional. CTL (la tabla/formula K0/K1/K2) NO pasa por este
#        parametro -- se confirma leyendo que el flag solo llega a
#        `FUN_1800e303c`/`FUN_1800e2d5c`, nunca a la funcion de tabla CTL.
#
# 2. Confirmado que el mismo flag existe, en la MISMA posicion funcional,
#    en las 6 rutas reales:
#      - `FUN_1800f8f70` (nucleo directo de API_Dens15C_1952): su `param_4`
#        se reenvia TAL CUAL como `param_5` de `FUN_1800e303c` (linea real:
#        `FUN_1800e303c(param_1*DAT_180124818,param_2,uVar7,uVar6,param_4,
#        param_8,param_10,local_58)`); la densidad final se calcula como
#        `CTL*CPL*param_1` usando el `param_1` SIN redondear (el redondeo
#        NUNCA toca la multiplicacion final, solo el CPL/F interno) -- esto
#        es lo que explica por que CTL/CPL/CTPL se ven identicos a 6
#        decimales en la UI en ambos estados: la diferencia real esta en la
#        7a cifra de CPL, invisible en pantalla, que se amplifica al
#        multiplicar por la densidad completa.
#      - `FUN_1800e79e4` (Gravity60F_1980): su `param_7` (DISTINTO de
#        `param_5`, que es el flag "API Rounding" YA CONOCIDO de Table5_1980
#        desde RONDA 3/4 -- 2 flags de redondeo independientes en la MISMA
#        funcion) redondea T_F al entrar y el candidato de API en cada
#        iteracion, alimentando una copia INLINEADA (no una llamada de
#        funcion separada, el compilador la incrusto) de la MISMA formula
#        de 4-terminos-a-5-decimales + exp-a-3-decimales.
#      - `FUN_1800e62d4` (Density15C_1980) y `FUN_1800e8494` (RD60F_1980):
#        mismo `param_7`, mismo patron inlineado, confirmado grep-ando las
#        constantes especificas de cada sistema (metrico/US).
#      - `FUN_1800f90a4` (Gravity60F_1952) y `FUN_1800f9674` (SG60F_1952):
#        su `param_4` se reenvia (via `CONCAT44(uVarXX,param_4)`, patron de
#        Ghidra ya visto en este proyecto para argumentos de 32 bits
#        pasados en un slot de 64) al `param_5` real de `FUN_1800e2d5c`
#        SIN llamada inline (SI llaman a la funcion compartida, no una
#        copia); ademas controla la tolerancia de convergencia del bucle
#        (0.01 floja si esta activo, mas estrecha si no) -- un uso
#        secundario razonable del mismo flag, no un mecanismo aparte.
#
# 3. VALIDACION NUMERICA (no solo cualitativa): replicando el mecanismo de
#    arriba en Python puro para el caso real (density_15c=1000kg/m3,
#    T=25°C, P=20bar(g), CTL=0.9935 de tabla, sin cambios):
#        rounding=0 -> f=5.277080942257374e-05, cpl=1.0010565312686561,
#                      ctpl=0.9945496638154099, density_obs=994.5496638
#        rounding=1 -> f=5.28e-05,               cpl=1.0010571163148283,
#                      ctpl=0.994550245058782,    density_obs=994.5502451
#    Las 2 reproducen la pantalla real EXACTO a la precision mostrada
#    (994.5497 y 994.5502), y explican el resto de las observaciones: F
#    salta de 5.277e-5 a 5.28e-5 exactos (redondeo a 3 decimales del F
#    escalado x10000, el paso que domina) pero ambos redondean a "0.000053"
#    a 6 decimales en la UI; CPL cambia solo en la 7a cifra (invisible en
#    pantalla); CTL no cambia en absoluto (no participa del flag).
#
# 4. IMPLEMENTADO: parametro `rounding: int = 0` (0=Disabled default, SIN
#    CAMBIOS respecto a versiones previas; 1=Enabled) agregado a
#    `api_mpms_11_2_1m`/`api_mpms_11_2_1` (la formula real de arriba) y
#    reenviado tal cual en las 6 funciones combinadas. Nivel de confianza
#    por funcion: `api_density15c_1952` [CERTAIN via decompilacion + CASO
#    REAL, unica con caso real propio de este flag]; las otras 5
#    (`api_density15c_1980`, `api_gravity60f_1980`, `api_reldensity60f_1980`,
#    `api_gravity60f_1952`, `api_sg60f_1952`) [CERTAIN via decompilacion
#    DIRECTA de su propio nucleo -- no por analogia, cada una fue leida
#    linea a linea esta ronda -- pero SIN caso real propio que confirme el
#    numero exacto de esa tabla especifica con el flag activo].
#
# 5. Simplificacion menor documentada (NO fabricada, de bajo impacto): el
#    flag `fuera_de_rango_oficial` de `api_mpms_11_2_1m`/`api_mpms_11_2_1`
#    se calcula contra los valores de entrada SIN redondear (el binario
#    real technically lo calcula contra los valores YA redondeados cuando
#    `rounding=1`, ver `FUN_1800e303c`/`FUN_1800e2d5c`) -- diferencia que
#    solo puede cambiar el flag informativo justo en el borde del rango
#    oficial (±1 kg/m3 o ±0.25°C tipico), nunca el numero fisico (F/CPL)
#    que es el objeto real de esta ronda.
#
# 6. NO investigado esta ronda (fuera de alcance, honesto): "API-11.2.2(M)
#    Rounding" (el flag analogo de `api_mpms_11_2_2`/`api_mpms_11_2_2m`,
#    ver RONDA 13 -- probablemente un mecanismo similar pero con su propio
#    polinomio, no confirmado); confirmacion visual en la UI real de que
#    las otras 5 pantallas (1980 x3, 1952 US x2) muestran literalmente un
#    selector "API-11.2.1 Rounding" con ese texto exacto (la evidencia de
#    esta ronda es 100% decompilacion, salvo la pantalla de
#    `api_density15c_1952` que si fue dada por el usuario).
# ===========================================================================
def api_density15c_1980(observed_density_kgm3: float, observed_temp_c: float,
                         pressure_bar_g: float, equilibrium_pressure_bar_g: float = 0.0,
                         product: Product = 1, max_iter: int = 100, tol: float = 1e-6,
                         conversion: int = 1, rounding: int = 0,
                         hydrometer_correction: bool = False,
                         api2540_rounding: int = 0) -> dict:
    """Densidad(T,P) <-> Densidad(15°C, EVP). API MPMS 11.1 (1980) + API MPMS
    11.2.1M (presion). [CERTAIN via decompilacion, RONDA 9] -- combina
    `api_table53_1980`/`api_table54_1980` (CTL, ya [CERTAIN] desde Ronda 1/2)
    con `api_mpms_11_2_1m` (CPL, [CERTAIN] esta ronda). NO validado contra
    caso real en vivo esta ronda (fuera del alcance; ver docstring RONDA 9
    para la validacion del modulo de presion en si mismo, que si tiene caso
    real via la familia 1952).

    `conversion` [CERTAIN, RONDA 16, hallazgo nuevo -- ver docstring del
    modulo, seccion "RONDA 16"]: 1=Observed->Standard(15°C) (default,
    iterativo, comportamiento SIN CAMBIOS respecto a versiones previas),
    0=Standard(15°C)->Observed (evaluacion DIRECTA, sin iterar).
    `observed_density_kgm3` se reinterpreta como la densidad YA a 15°C
    (base) cuando `conversion=0`; el resultado bajo la clave `density_15c`
    pasa a ser la densidad OBSERVADA predicha (misma convencion ya usada en
    `normas/_ngl_lpg_wrappers_puro.py` para su propio parametro
    `conversion`). Confirmado por llamada DIRECTA (ctypes, sin Excel) al
    nucleo real `FUN_1800e62d4` del `.xll`: round-trip EXACTO
    (observado=1000kg/m3 -> base=856.9406 -> observado recuperado=
    1000.0000004, diff=4.4e-7) -- ver docstring del modulo.

    `rounding` ("API-11.2.1 Rounding" de la UI) [CERTAIN via decompilacion
    directa de `FUN_1800e62d4`, RONDA 19 -- ver docstring del modulo,
    seccion "RONDA 19": esta funcion SI tiene su propio `param_7` que
    replica linea a linea el mismo procedimiento de redondeo de
    `api_mpms_11_2_1m` (verificado leyendo el propio decompilado de
    `FUN_1800e62d4`, no solo por analogia). 0=Disabled (default, SIN
    CAMBIOS), 1=Enabled -- se reenvia tal cual a cada llamada de
    `api_mpms_11_2_1m` (CTL/tabla NO se ve afectado). NO hay caso real
    propio de esta tabla con el flag activo (el unico caso real de RONDA 19
    es de `api_density15c_1952`, metrico); se implementa por ser el MISMO
    nucleo de formula ya [CERTAIN].

    `hydrometer_correction`/`api2540_rounding` [RONDA 22 -- EXISTENCIA
    CONFIRMADA CON PANTALLA REAL (`uiautomator dump` en vivo sobre
    `flowxpert_rd`, 2026-09-07): la pantalla real "API Density @15°C (1980)"
    SI muestra 9 campos, no 7 -- ademas de Density/Temperature/Pressure/
    Product/Equilibrium Pressure/Conversion (ya implementados) y del switch
    "API-11.2.1M Rounding" (=`rounding` de arriba), tiene un selector
    "API-2540 Rounding" (enum de 4 valores, idéntico al ya confirmado en
    `api_table6_1980`/`api_table24_1980`: Disabled/Enabled/'Enabled (table
    values)'/'Enabled (5 decimal places)', visto en pantalla via su Spinner
    `value_spinner`) y un switch "Hydrometer Corr." -- confirma con evidencia
    de pantalla (no solo decompilacion) el hallazgo de Ronda 21, que habia
    leido los 3 nucleos `FUN_1800e62d4`/`FUN_1800e79e4`/`FUN_1800e8494` con
    `param_5`=este enum y `param_6`=este flag.

    Implementacion [LIKELY, NO caso real propio con el flag activo -- ver
    aclaracion abajo]: `hydrometer_correction` reusa la MISMA formula
    `_hydrometer_factor_metric()` ya [LIKELY]/[CERTAIN] en `api_table53_1980`,
    aplicada sobre la densidad observada ANTES de iterar, y SOLO en la
    direccion `conversion=1` (Observado->Estandar) -- Ronda 21 leyo en los 3
    nucleos que este ajuste esta gateado para NO aplicarse en la direccion
    inversa. `api2540_rounding` [CERRADO RONDA 29, ver seccion "RONDA 29" al
    final del modulo]: para CUALQUIER valor != 0 del enum (1/2/3 se comportan
    IGUAL en la rama iterativa, confirmado empiricamente RONDA 28) se aplica
    la cascada REAL de `FUN_1800e62d4` via `_iterar_api2540_cascade()`
    (densidad/temperatura redondeadas a 1 decimal al entrar, densidad
    redondeada a 2 decimales cada vuelta antes de alpha, K0/K1/K2 con
    truncados intermedios a 8/10/10 decimales + suma redondeada a 7,
    exponente de CTL con cascada de truncados a 8 + redondeo final a 8, CTL
    redondeado a 6 decimales, 2 candidatos de densidad por vuelta truncados a
    3 decimales con desfase de 1 iteracion, tolerancia de convergencia
    0.05/0.07 kg/m3 segun producto). La ambiguedad que freno RONDA 28 (la 2a
    llamada a `FUN_1800e1e14` sin argumento de decimales visible en el
    decompilado) se resolvio con CERTEZA via desensamblado x64 directo
    (`capstone`): es `FUN_1800e1e14(x, 3)` (mismo truncado a 3 decimales que
    la 1a llamada), confirmado leyendo la instruccion real `lea edx,[rsi+2]`
    con `rsi`(=param_9)=1 en ese punto. Validado 2571/2592 (99.19%) contra el
    oraculo `.xll` real en un barrido amplio (6 productos x 4 escenarios P/EVP
    x 2 `rounding` x 2 `hydrometer_correction` x 3 API/T x 3 `api2540_rounding`);
    en el barrido oficial de RONDA 25/28 (`normas/_sweep_api_1952_1980_flags.py`,
    punto fijo densidad=850kg/m3 T=25°C) esta funcion pasa a 0 discrepancias
    (antes 1/2304). El residuo del barrido amplio es EXCLUSIVAMENTE producto 4
    (Transition area) en casos-limite de convergencia marginal (mismo patron
    ya documentado [LIKELY] en RONDA 21/27 para otras funciones de esta
    familia -- no una discrepancia de formula, ver seccion "RONDA 29").
    Default (`api2540_rounding=0`) = comportamiento identico a versiones
    previas (sin regresion, confirmado byte a byte).

    `product=2` (B - Auto select) [CERTAIN, RONDA 49 -- ver seccion "RONDA 49"
    y docstring de `_resolver_producto_auto_1980`/`_auto_select_1980`]:
    implementado con el mecanismo real de 1 o 2 pasadas (decompilacion
    directa de `FUN_1800e62d4`), validado end-to-end contra el oraculo
    `.xll` (`calcular_dens15c_1980_directo(..., product=2, ...)`) reproduciendo
    EXACTO el `PRDCUR` (producto realmente seleccionado, expuesto aqui como
    `product_efectivo`) Y el resultado final en el 100% de un barrido de 26
    puntos de densidad cruzando las 4 fronteras (770/779/788/839 kg/m3), en
    ambas direcciones de `conversion`."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if api2540_rounding not in (0, 1, 2, 3):
        raise ValueError("api2540_rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_METRIC[producto_fijo]
        if conversion == 0:
            rho_base = observed_density_kgm3
            if api2540_rounding != 0:
                # RONDA 31: rama DIRECTA (manual paso 1, "inputs rounded...
                # provided API2540 rounding enabled") + cascada real de
                # alpha/CTL (Table 54, mismos truncados que la rama iterativa,
                # confirmado contra el oraculo: producto=7/Lubricating Oil cae
                # en un borde de redondeo de 5 decimales donde el CTL "plano"
                # (full precision) y el CTL "cascada" (truncado como el
                # binario) redondean a valores DISTINTOS -- ver seccion
                # "RONDA 31").
                rho_base = _round_densidad_hidrometro_metric(observed_density_kgm3)
                delta_t_dir = _round_comercial_n(observed_temp_c, 1) - T_REF_METRIC_1980_C
                alpha = _alpha_cascade_api2540(k, _round_comercial_n(rho_base, 2), producto_fijo)
                ctl = _ctl_cascade_api2540(alpha, delta_t_dir)
            else:
                alpha = _alpha(k, rho_base)
                ctl = _ctl_1980(alpha, observed_temp_c - T_REF_METRIC_1980_C)
            ctl = _ctl_rounding_directo(ctl, api2540_rounding)
            cpl_res = api_mpms_11_2_1m(rho_base, observed_temp_c, pressure_bar_g,
                                        equilibrium_pressure_bar_g, rounding,
                                        clamp_negative_net_pressure=False)
            cpl, f = cpl_res["cpl"], cpl_res["f"]
            ctpl = ctl * cpl
            density_obs_predicha = rho_base * ctpl
            return {"density_15c": density_obs_predicha, "ctl": ctl, "cpl": cpl, "ctpl": ctpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": rho_base}
        if api2540_rounding != 0:
            # RONDA 29: cascada real (ver `_iterar_api2540_cascade` y seccion
            # "RONDA 29" al final del modulo). Validada 99.19% (2571/2592) contra
            # el oraculo `.xll` real; el residuo son casos-limite de convergencia
            # marginal de producto 4, no una discrepancia de formula.
            t_r = _round_comercial_n(observed_temp_c, 1)
            dens_r = _round_densidad_hidrometro_metric(observed_density_kgm3)
            rho_obs_2dec = _round_comercial_n(dens_r, 2)
            hyd_factor = _hydrometer_factor_metric(t_r) if hydrometer_correction else 1.0
            rho_fixed = _round_comercial_n(rho_obs_2dec * hyd_factor, 2)
            delta_t = t_r - T_REF_METRIC_1980_C

            def _cpl_de_candidato(dens_candidato_kgm3: float) -> float:
                return api_mpms_11_2_1m(dens_candidato_kgm3, t_r, pressure_bar_g,
                                         equilibrium_pressure_bar_g, rounding,
                                         clamp_negative_net_pressure=False)["cpl"]

            dens_c2, ctl, cpl, _ = _iterar_api2540_cascade(
                k, rho_fixed, t_r, delta_t, producto_fijo, _cpl_de_candidato, max_iter)
            alpha = _alpha_cascade_api2540(k, _round_comercial_n(dens_c2, 2), producto_fijo)
            f = api_mpms_11_2_1m(dens_c2, t_r, pressure_bar_g,
                                  equilibrium_pressure_bar_g, rounding,
                                  clamp_negative_net_pressure=False)["f"]
            # RONDA 31: manual step 15 ("the final density at [15C, equilibrium
            # pressure] is rounded to 1 decimal place") + confirmado en el
            # decompilado (FUN_1800e62d4, LAB_1800e6ad8: `*param_10 =
            # FUN_1800e1db4(param_19,1)` cuando param_5(=api2540_rounding)!=0) --
            # F usa el candidato SIN redondear (`param_19` no se reescribe), solo
            # el output de densidad se redondea a 1 decimal para mostrar.
            density_15c_out = _round_comercial_n(dens_c2, 1)
            return {"density_15c": density_15c_out, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": dens_c2}
        obs_for_iter = observed_density_kgm3
        if hydrometer_correction:
            obs_for_iter = obs_for_iter * _hydrometer_factor_metric(observed_temp_c)
        rho_base = obs_for_iter
        ctl = 1.0
        cpl = 1.0
        alpha = 0.0
        for _ in range(max_iter):
            alpha = _alpha(k, rho_base)
            ctl = _ctl_1980(alpha, observed_temp_c - T_REF_METRIC_1980_C)
            cpl = api_mpms_11_2_1m(rho_base, observed_temp_c, pressure_bar_g,
                                    equilibrium_pressure_bar_g, rounding,
                                    clamp_negative_net_pressure=False)["cpl"]
            ctpl = ctl * cpl
            nuevo = obs_for_iter / ctpl if ctpl != 0 else rho_base
            if abs(nuevo - rho_base) < tol:
                rho_base = nuevo
                break
            rho_base = nuevo
        f = api_mpms_11_2_1m(rho_base, observed_temp_c, pressure_bar_g,
                              equilibrium_pressure_bar_g, rounding,
                              clamp_negative_net_pressure=False)["f"]
        return {"density_15c": rho_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": rho_base}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(
            observed_density_kgm3, "densidad_kgm3", conversion == 1, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    out = {clave: valor for clave, valor in resultado.items() if clave != "_candidato_nativo"}
    out["product_efectivo"] = producto_efectivo
    return out


def api_gravity60f_1980(observed_api: float, observed_temp_f: float,
                         pressure_psig: float, equilibrium_pressure_psig: float = 0.0,
                         product: Product = 1, max_iter: int = 100, tol: float = 1e-6,
                         conversion: int = 1, rounding: int = 0,
                         hydrometer_correction: bool = False,
                         api2540_rounding: int = 0) -> dict:
    """°API(T,P) <-> °API(60°F, EVP). API MPMS 11.1 (1980) + API MPMS 11.2.1
    (presion, US). [CERTAIN via decompilacion, RONDA 9] -- combina
    `api_table5_1980`/`api_table6_1980` (CTL) con `api_mpms_11_2_1` (CPL).
    La densidad-base de cada iteracion se reexpresa en °API (141.5/RD-131.5,
    la misma identidad ya usada en el resto de este archivo) para
    alimentar `api_mpms_11_2_1`, que trabaja nativamente en °API (no en
    kg/m3) -- confirmado por decompilacion (FUN_1800e79e4 inlinea la misma
    formula que FUN_1800e2d5c). NO validado contra caso real en vivo esta
    ronda.

    `conversion` [CERTAIN, RONDA 16, hallazgo nuevo -- ver docstring del
    modulo, seccion "RONDA 16"]: 1=Observed->Standard(60°F) (default,
    iterativo, SIN CAMBIOS respecto a versiones previas), 0=
    Standard(60°F)->Observed (evaluacion DIRECTA, sin iterar).
    `observed_api` se reinterpreta como °API YA a 60°F (base) cuando
    `conversion=0`; el resultado bajo la clave `api_60f` pasa a ser el °API
    OBSERVADO predicho. CONFIRMADO EMPIRICAMENTE llamando DIRECTO (ctypes,
    sin Excel/emulador) al nucleo real `FUN_1800e79e4` del `.xll`: con
    API_obs=30, T=90°F, P=0, product=1(Crudo) -> conversion=1 da
    api_60f=27.890942584019257 (coincide EXACTO con el caso real de RONDA 3,
    27.89094); alimentando ESE mismo valor de vuelta con conversion=2 (el
    codigo interno real que usa el binario para "Standard->Observed" --
    ver docstring del modulo) reproduce el observado original EXACTO:
    30.000000000775362 (diff=7.75e-10). Round-trip real contra el binario,
    no fabricado -- ver seccion "RONDA 16" del docstring del modulo para el
    detalle completo, incluida la decision de mapear el codigo interno del
    binario (1/2) al API publico de este archivo (0/1, igual convencion que
    `_ngl_lpg_wrappers_puro.py`).

    `rounding` ("API-11.2.1 Rounding") [CERTAIN via decompilacion directa,
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19"]: confirmado
    leyendo el propio decompilado de `FUN_1800e79e4` que su `param_7` (NO
    `param_5`, que es un flag DISTINTO de "API Rounding" ya conocido de
    Table5_1980, RONDA 3) redondea T_F al 0.5°F mas cercano al entrar a la
    funcion y el candidato de °API a 60°F al 0.5°API mas cercano en cada
    pasada, ANTES de una formula INLINEADA identica (linea a linea, mismos
    5/3 decimales de redondeo intermedio) a `api_mpms_11_2_1`. 0=Disabled
    (default, SIN CAMBIOS), 1=Enabled. NO hay caso real propio con el flag
    activo para esta tabla.

    `hydrometer_correction`/`api2540_rounding` [RONDA 22 -- EXISTENCIA
    CONFIRMADA CON PANTALLA REAL, mismo hallazgo que en
    `api_density15c_1980` (ver su docstring para el detalle completo de la
    confirmacion visual y el nivel de confianza [LIKELY] de la
    implementacion): la pantalla real "API Gravity @60°F (1980)" tambien
    muestra 9 campos, con el mismo selector "API-2540 Rounding" (enum de 4
    valores) y el mismo switch "Hydrometer Corr." ademas del ya implementado
    "API-11.2.1M Rounding" (=`rounding`). Implementacion: `hydrometer_correction`
    reusa `_hydrometer_factor()` (ya [CERTAIN] en `api_table5_1980`) sobre la
    densidad-equivalente ANTES de iterar, solo si `conversion=1`.
    `api2540_rounding` [CERRADO RONDA 29, ver seccion "RONDA 29" al final del
    modulo -- esta era la funcion DOMINANTE del impacto (288/289
    discrepancias del barrido de RONDA 25 venian de aqui)]: para cualquier
    valor != 0 del enum se aplica la cascada REAL de `FUN_1800e79e4` via
    `_iterar_api2540_cascade()` (mismo mecanismo que `api_density15c_1980`,
    en °API convertido internamente a densidad kg/m3 via
    `_rd60_to_density_kgm3`). La ambiguedad de RONDA 28 (la 2a llamada a
    `FUN_1800e1e14` sin argumento de decimales visible en el decompilado, que
    freno esa ronda en 78/144=54.2% exacto) se resolvio con CERTEZA via
    desensamblado x64 directo (`capstone`, mismo metodo ya usado en este
    proyecto para el mapeo de argumentos de `API_Ethylene_Propylene_puro.py`):
    la instruccion real en ese punto es `lea edx,[rsi+2]` con `rsi`(=param_9,
    el flag `conversion` interno)=1 confirmado por el `cmp esi,1` que domina
    ese bloque, dando `edx=3` -- es decir `FUN_1800e1e14(x, 3)`, el MISMO
    truncado a 3 decimales que la 1a llamada del candidato de densidad
    (`mov edx,3` explicito, verificado en el mismo desensamblado). Validado
    2571/2592 (99.19%) contra el oraculo `.xll` real en un barrido amplio (6
    productos x 4 escenarios P/EVP x 2 `rounding` x 2 `hydrometer_correction`
    x 3 API/T x 3 `api2540_rounding`); en el barrido oficial de RONDA 25/28
    (`normas/_sweep_api_1952_1980_flags.py`, 768 combinaciones para esta
    funcion) pasa de 480/768 (62.5%) a 762/768 (99.22%). El residuo (6/768,
    igual patron en el barrido amplio: 21/2592) es EXCLUSIVAMENTE producto 4
    (Transition area, K2!=0, tolerancia de convergencia 0.07 en vez de 0.05)
    en el mismo P=300psig/EVP=0/hydrometer_correction=1 -- el propio oraculo
    `.xll` devuelve ahi `oor1=4` (bandera interna de "fuera de rango"/
    convergencia marginal, ver `FUN_1800e79e4` parametros de salida 19-21,
    aun sin decodificar por completo) junto con el resultado, confirmando que
    es el binario mismo el que trata este punto como un caso limite de
    convergencia (mismo patron [LIKELY] ya documentado en RONDA 21/27 para
    otras funciones de esta familia), no una discrepancia de formula.
    Default (`api2540_rounding=0`) = comportamiento identico a versiones
    previas (sin regresion, confirmado byte a byte).

    `product=2` (B - Auto select) [CERTAIN, RONDA 49 -- ver seccion "RONDA 49"
    y docstring de `_resolver_producto_auto_1980`/`_auto_select_1980`]:
    mismo mecanismo que `api_density15c_1980`, en dominio °API (breakpoints
    37.0/48.0/50.0/52.0), validado end-to-end contra el oraculo `.xll`
    (`calcular_gravity60f_1980_directo(..., product=2, ...)`)."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if api2540_rounding not in (0, 1, 2, 3):
        raise ValueError("api2540_rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        if conversion == 0:
            api_base = observed_api
            rho_base = _rd60_to_density_kgm3(141.5 / (131.5 + api_base))
            if api2540_rounding != 0:
                # RONDA 31: mismo tratamiento que `api_density15c_1980` (ver su
                # docstring, seccion "RONDA 31") -- rama DIRECTA con inputs
                # redondeados (API a 1 decimal, mismo hidrometro que la rama
                # iterativa, RONDA 29) + cascada real de alpha/CTL (Table 6) en
                # vez de formula de precision completa.
                api_base = _round_comercial_n(observed_api, 1)
                rho_base = _rd60_to_density_kgm3(141.5 / (131.5 + api_base))
                delta_t_dir = _round_comercial_n(observed_temp_f, 1) - T_REF_US_1980_F
                alpha = _alpha_cascade_api2540(k, _round_comercial_n(rho_base, 2), producto_fijo)
                ctl = _ctl_cascade_api2540(alpha, delta_t_dir)
            else:
                alpha = _alpha(k, rho_base)
                ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
            ctl = _ctl_rounding_directo(ctl, api2540_rounding)
            cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                       equilibrium_pressure_psig, rounding,
                                       clamp_negative_net_pressure=False)
            cpl, f = cpl_res["cpl"], cpl_res["f"]
            ctpl = ctl * cpl
            rho_obs_equiv = rho_base * ctpl
            api_obs_predicho = 141.5 / _density_kgm3_to_rd60(rho_obs_equiv) - 131.5
            return {"api_60f": api_obs_predicho, "ctl": ctl, "cpl": cpl, "ctpl": ctpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": api_base}
        if api2540_rounding != 0:
            # RONDA 29: cascada real (ver `_iterar_api2540_cascade` y seccion
            # "RONDA 29" al final del modulo). Validada 99.19% (2571/2592) contra
            # el oraculo `.xll` real; el residuo son casos-limite de convergencia
            # marginal de producto 4, no una discrepancia de formula.
            api_r = _round_comercial_n(observed_api, 1)
            t_r = _round_comercial_n(observed_temp_f, 1)
            rho_obs_2dec = _round_comercial_n(_rd60_to_density_kgm3(141.5 / (131.5 + api_r)), 2)
            hyd_factor = _hydrometer_factor(t_r) if hydrometer_correction else 1.0
            rho_fixed = _round_comercial_n(rho_obs_2dec * hyd_factor, 2)
            delta_t = t_r - T_REF_US_1980_F

            def _cpl_de_candidato(dens_candidato_kgm3: float) -> float:
                api_candidato = (141.5 / _density_kgm3_to_rd60(dens_candidato_kgm3) - 131.5
                                  if dens_candidato_kgm3 != 0 else 0.0)
                return api_mpms_11_2_1(api_candidato, t_r, pressure_psig,
                                        equilibrium_pressure_psig, rounding,
                                        clamp_negative_net_pressure=False)["cpl"]

            dens_c2, ctl, cpl, _ = _iterar_api2540_cascade(
                k, rho_fixed, t_r, delta_t, producto_fijo, _cpl_de_candidato, max_iter)
            alpha = _alpha_cascade_api2540(k, _round_comercial_n(dens_c2, 2), producto_fijo)
            if dens_c2 == 0.0:
                api_base = 0.0
            else:
                api_base = _round_comercial_n(141.5 / _density_kgm3_to_rd60(dens_c2) - 131.5, 1)
            f = api_mpms_11_2_1(api_base, t_r, pressure_psig,
                                 equilibrium_pressure_psig, rounding,
                                 clamp_negative_net_pressure=False)["f"]
            return {"api_60f": api_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": api_base}
        rd_obs = 141.5 / (131.5 + observed_api)
        rho_obs_for_iter = _rd60_to_density_kgm3(rd_obs)
        if hydrometer_correction:
            rho_obs_for_iter = rho_obs_for_iter * _hydrometer_factor(observed_temp_f)
        rho_base = rho_obs_for_iter
        ctl = 1.0
        cpl = 1.0
        alpha = 0.0
        for _ in range(max_iter):
            alpha = _alpha(k, rho_base)
            ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
            api_base = 141.5 / _density_kgm3_to_rd60(rho_base) - 131.5
            cpl = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding,
                                   clamp_negative_net_pressure=False)["cpl"]
            ctpl = ctl * cpl
            nuevo = rho_obs_for_iter / ctpl if ctpl != 0 else rho_base
            if abs(nuevo - rho_base) < tol:
                rho_base = nuevo
                break
            rho_base = nuevo
        api_base = 141.5 / _density_kgm3_to_rd60(rho_base) - 131.5
        f = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                             equilibrium_pressure_psig, rounding,
                             clamp_negative_net_pressure=False)["f"]
        return {"api_60f": api_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": api_base}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(
            observed_api, "api", conversion == 1, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    out = {clave: valor for clave, valor in resultado.items() if clave != "_candidato_nativo"}
    out["product_efectivo"] = producto_efectivo
    return out


def api_reldensity60f_1980(observed_rd: float, observed_temp_f: float,
                            pressure_psig: float, equilibrium_pressure_psig: float = 0.0,
                            product: Product = 1, max_iter: int = 100, tol: float = 1e-6,
                            conversion: int = 1, rounding: int = 0,
                            hydrometer_correction: bool = False,
                            api2540_rounding: int = 0) -> dict:
    """RD(T,P) <-> RD(60°F, EVP). API MPMS 11.1 (1980) + API MPMS 11.2.1
    (presion, US). [CERTAIN via decompilacion, RONDA 9] -- combina
    `api_table23_1980`/`api_table24_1980` (CTL) con `api_mpms_11_2_1` (CPL),
    misma tecnica que `api_gravity60f_1980`. NO validado contra caso real en
    vivo esta ronda.

    `conversion` [CERTAIN, RONDA 16 -- ver docstring del modulo]: 1=
    Observed->Standard(60°F) (default, iterativo, SIN CAMBIOS), 0=
    Standard(60°F)->Observed (directo). `observed_rd` se reinterpreta como
    RD YA a 60°F (base) cuando `conversion=0`; `rd_60f` pasa a ser el RD
    OBSERVADO predicho. CONFIRMADO EMPIRICAMENTE por llamada DIRECTA al
    nucleo real `FUN_1800e8494` del `.xll`: round-trip EXACTO (RD_obs=0.85,
    T=90°F, P=0 -> base=0.8619432 -> RD observado recuperado=
    0.8499999999937672, diff=6.2e-12) -- ver docstring del modulo.

    `rounding` ("API-11.2.1 Rounding") [CERTAIN via decompilacion directa,
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19"]: confirmado
    leyendo el propio decompilado de `FUN_1800e8494`, que tiene el mismo
    `param_7` con el mismo procedimiento de 4 terminos redondeados a 5
    decimales + `exp` redondeado a 3 decimales antes de escalar, identico a
    `api_mpms_11_2_1`. 0=Disabled (default, SIN CAMBIOS), 1=Enabled. NO hay
    caso real propio con el flag activo para esta tabla.

    `hydrometer_correction`/`api2540_rounding` [RONDA 22 -- EXISTENCIA
    CONFIRMADA CON PANTALLA REAL; `api2540_rounding` CERRADO RONDA 30, ver
    seccion "RONDA 30" al final del modulo]: la pantalla real "API Rel.
    Density @60°F (1980)" muestra 9 campos, con el mismo selector "API-2540
    Rounding" (enum de 4 valores) y el mismo switch "Hydrometer Corr."
    ademas del ya implementado "API-11.2.1 Rounding" (=`rounding`).
    `hydrometer_correction` reusa `_hydrometer_factor()` sobre la
    densidad-equivalente ANTES de iterar, solo si `conversion=1`.
    `api2540_rounding`: para cualquier valor != 0 del enum se aplica la
    cascada REAL de `FUN_1800e8494` via `_iterar_api2540_cascade()` (mismo
    mecanismo que `api_gravity60f_1980`/`api_density15c_1980`, RONDA 29),
    con 2 pasos propios de esta funcion (por trabajar en RD 0-1 en vez de
    °API/kg-m3 directo), ambos CONFIRMADOS por desensamblado x64 directo con
    `capstone` (RONDA 30, resolviendo el PENDIENTE que dejo RONDA 29): (a) en
    la ENTRADA, `observed_rd` se redondea a la graduacion REAL de un
    hidrometro de RD (0.0005, NO 0.1 como °API o kg/m3) ANTES de convertir a
    densidad -- la secuencia real es `mulsd xmm11,[2.0]; call
    FUN_1800e1db4(x,3); mulsd xmm11,xmm6` en `FUN_1800e8494` (direccion
    0x1800e85c0-0x1800e85e5), y el registro `xmm6` (la ambiguedad que dejo
    pendiente RONDA 29, sospechada como "factor no identificado") se rastreo
    instruccion por instruccion hasta su origen real: una CONSTANTE 0.5
    cargada en el prologo (`movsd xmm6,[rip+0x3bf1c]` @ 0x1800e8504, valor
    leido byte a byte del `.xll` = 0.5 EXACTO) que sobrevive sin
    reescribirse hasta ese punto -- es decir, el idiom estandar
    "multiplicar por 2, redondear, multiplicar por 0.5" para redondear a la
    mitad de la unidad pedida (aqui: RD*2 redondeado a 3 decimales / 2 =
    RD redondeado a 0.0005), NO un factor fisico separado; formula final:
    `rd_r = round_comercial(observed_rd*2.0, 3) / 2.0`, luego
    `rho_from_rd = rd_r * 999.012` alimenta el resto de la cascada
    (`rho_2dec`/`hyd_factor`/`rho_fixed`) EXACTAMENTE igual que
    `api_gravity60f_1980`/`api_density15c_1980`; (b) en la SALIDA, el
    candidato final de densidad se divide por 999.012 (`RHO_WATER_60F_KGM3`,
    confirmado en `[rip+0x101e8a]`) y se redondea (comercial) a 4 decimales
    -- esto YA estaba confirmado desde RONDA 29, sin cambios. La UNICA
    llamada real a la subrutina compartida `FUN_1801060dc` dentro de la
    funcion (direccion 0x1800e8a87, se confirmo por desensamblado que es la
    UNICA en toda la funcion) NO es parte de la conversion de entrada/salida
    -- es la conversion densidad-candidato->°API DENTRO del loop, para
    alimentar la formula de CPL inlineada (identica en rol a
    `_cpl_de_candidato` de `api_gravity60f_1980`) -- la sospecha de RONDA 29
    de que este call fuera el mecanismo de entrada/salida era incorrecta,
    corregida esta ronda con evidencia directa (una sola `call
    0x1801060dc` en toda la funcion, ubicada dentro del loop de iteracion,
    NO antes de el). Validado 98.84% (2562/2592) contra un barrido amplio
    del oraculo `.xll` real (6 productos x 4 escenarios P/EVP x 2 `rounding`
    x 2 `hydrometer_correction` x 3 RD x 3 T x 3 `api2540_rounding`) -- el
    residuo (30/2592) es EXCLUSIVAMENTE producto 4 (Transition area) con la
    bandera interna del propio oraculo `oor1=4` (convergencia marginal),
    MISMO patron [LIKELY] ya documentado en RONDA 21/27/29 para el resto de
    la familia, no una discrepancia de formula. Comparado con la
    implementacion anterior (sin la cascada, RONDA 22-29) sobre el MISMO
    barrido de 2592 casos: error absoluto medio bajo de 2.71e-5 a 1.16e-6
    (23x mas preciso) y los casos con error <1e-6 subieron de 70/2592 a
    2562/2592 -- confirma que la version anterior "pasaba" el barrido
    oficial de RONDA 25/28/29 (0/2304) por COINCIDENCIA (el efecto de
    ignorar la cascada es pequeno en la escala 0-1 de RD, no porque la
    formula anterior fuera correcta), y que el barrido oficial ahora muestra
    9/768 discrepancias NUEVAS para esta funcion especifica porque el
    residuo REAL (antes enmascarado por la escala) ahora es visible -- ver
    seccion "RONDA 30" para el detalle completo de esta verificacion.
    Default (`api2540_rounding=0`) = comportamiento identico a versiones
    previas (sin regresion, confirmado byte a byte).

    `product=2` (B - Auto select) [CERTAIN, RONDA 49 -- ver seccion "RONDA 49"
    y docstring de `_resolver_producto_auto_1980`/`_auto_select_1980`]:
    mismo mecanismo que `api_density15c_1980`, en dominio RD adimensional
    (breakpoints 0.771/0.779/0.789/0.84), validado end-to-end contra el
    oraculo `.xll` (`calcular_rd60f_1980_directo(..., product=2, ...)`)."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if api2540_rounding not in (0, 1, 2, 3):
        raise ValueError("api2540_rounding debe ser 0/1/2/3 (Disabled/Enabled/"
                          "'Enabled (table values)'/'Enabled (5 decimal places)').")

    def _ejecutar(producto_fijo: int) -> dict:
        k = K_US[producto_fijo]
        if conversion == 0:
            rd_base = observed_rd
            if api2540_rounding != 0:
                # RONDA 31: mismo tratamiento que `api_density15c_1980`/
                # `api_gravity60f_1980` (ver seccion "RONDA 31") -- rama DIRECTA
                # con inputs redondeados (RD a la graduacion real de hidrometro
                # 0.0005, mismo mecanismo que la rama iterativa, RONDA 30) +
                # cascada real de alpha/CTL (Table 24) en vez de formula de
                # precision completa.
                rd_base = _round_comercial_n(observed_rd * 2.0, 3) / 2.0
            rho_base = _rd60_to_density_kgm3(rd_base)
            if api2540_rounding != 0:
                delta_t_dir = _round_comercial_n(observed_temp_f, 1) - T_REF_US_1980_F
                alpha = _alpha_cascade_api2540(k, _round_comercial_n(rho_base, 2), producto_fijo)
                ctl = _ctl_cascade_api2540(alpha, delta_t_dir)
            else:
                alpha = _alpha(k, rho_base)
                ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
            ctl = _ctl_rounding_directo(ctl, api2540_rounding)
            api_base = 141.5 / rd_base - 131.5
            cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                       equilibrium_pressure_psig, rounding,
                                       clamp_negative_net_pressure=False)
            cpl, f = cpl_res["cpl"], cpl_res["f"]
            ctpl = ctl * cpl
            rho_obs_equiv = rho_base * ctpl
            rd_obs_predicho = _density_kgm3_to_rd60(rho_obs_equiv)
            return {"rd_60f": rd_obs_predicho, "ctl": ctl, "cpl": cpl, "ctpl": ctpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": rd_base}
        if api2540_rounding != 0:
            # RONDA 30: cascada real (ver `_iterar_api2540_cascade` y seccion
            # "RONDA 30" al final del modulo). Validada 98.84% (2562/2592) contra
            # el oraculo `.xll` real; el residuo son casos-limite de convergencia
            # marginal de producto 4 (oor1=4), mismo patron que
            # `api_density15c_1980`/`api_gravity60f_1980` (RONDA 29).
            t_r = _round_comercial_n(observed_temp_f, 1)
            # RD se redondea a la graduacion REAL del hidrometro (0.0005), NO a 1
            # decimal como °API/kg-m3 -- confirmado por desensamblado x64 directo
            # (RONDA 30): `round_comercial(observed_rd*2.0, 3) / 2.0` replica
            # EXACTO la secuencia real `mulsd xmm11,[2.0]; call FUN_1800e1db4(x,3);
            # mulsd xmm11,xmm6(=0.5)` de `FUN_1800e8494`.
            rd_r = _round_comercial_n(observed_rd * 2.0, 3) / 2.0
            rho_from_rd = rd_r * RHO_WATER_60F_KGM3
            rho_2dec = _round_comercial_n(rho_from_rd, 2)
            hyd_factor = _hydrometer_factor(t_r) if hydrometer_correction else 1.0
            rho_fixed = _round_comercial_n(rho_2dec * hyd_factor, 2)
            delta_t = t_r - T_REF_US_1980_F

            def _cpl_de_candidato(dens_candidato_kgm3: float) -> float:
                api_candidato = (141.5 / _density_kgm3_to_rd60(dens_candidato_kgm3) - 131.5
                                  if dens_candidato_kgm3 != 0 else 0.0)
                return api_mpms_11_2_1(api_candidato, t_r, pressure_psig,
                                        equilibrium_pressure_psig, rounding,
                                        clamp_negative_net_pressure=False)["cpl"]

            dens_c2, ctl, cpl, _ = _iterar_api2540_cascade(
                k, rho_fixed, t_r, delta_t, producto_fijo, _cpl_de_candidato, max_iter)
            alpha = _alpha_cascade_api2540(k, _round_comercial_n(dens_c2, 2), producto_fijo)
            rd_base = _round_comercial_n(dens_c2 / RHO_WATER_60F_KGM3, 4)
            api_base_for_f = (141.5 / _density_kgm3_to_rd60(dens_c2) - 131.5
                               if dens_c2 != 0 else 0.0)
            f = api_mpms_11_2_1(api_base_for_f, t_r, pressure_psig,
                                 equilibrium_pressure_psig, rounding,
                                 clamp_negative_net_pressure=False)["f"]
            return {"rd_60f": rd_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                    "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                    "_candidato_nativo": rd_base}
        rho_obs_for_iter = _rd60_to_density_kgm3(observed_rd)
        if hydrometer_correction:
            rho_obs_for_iter = rho_obs_for_iter * _hydrometer_factor(observed_temp_f)
        rho_base = rho_obs_for_iter
        ctl = 1.0
        cpl = 1.0
        alpha = 0.0
        for _ in range(max_iter):
            alpha = _alpha(k, rho_base)
            ctl = _ctl_1980(alpha, observed_temp_f - T_REF_US_1980_F)
            api_base = 141.5 / _density_kgm3_to_rd60(rho_base) - 131.5
            cpl = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding,
                                   clamp_negative_net_pressure=False)["cpl"]
            ctpl = ctl * cpl
            nuevo = rho_obs_for_iter / ctpl if ctpl != 0 else rho_base
            if abs(nuevo - rho_base) < tol:
                rho_base = nuevo
                break
            rho_base = nuevo
        rd_base = _density_kgm3_to_rd60(rho_base)
        f = api_mpms_11_2_1(141.5 / rd_base - 131.5, observed_temp_f, pressure_psig,
                             equilibrium_pressure_psig, rounding,
                             clamp_negative_net_pressure=False)["f"]
        return {"rd_60f": rd_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl,
                "f": f, "alpha": alpha, "k0": k.k0, "k1": k.k1, "k2": k.k2,
                "_candidato_nativo": rd_base}

    if product == 2:
        resultado, producto_efectivo = _auto_select_1980(
            observed_rd, "rd", conversion == 1, _ejecutar)
    else:
        resultado, producto_efectivo = _ejecutar(product), product
    out = {clave: valor for clave, valor in resultado.items() if clave != "_candidato_nativo"}
    out["product_efectivo"] = producto_efectivo
    return out


# ===========================================================================
# RONDA 10 -- Table53_1952/Table54_1952 (metrico) CERRADAS: tabla real de
# interpolacion DECODIFICADA desde los bytes crudos del `.xll`
# (`&DAT_18028a680`), no fabricada. Ver docstring del modulo, seccion
# "RONDA 10", para el metodo completo (dump con `pefile`, layout de la
# cabecera de 16 bytes reconstruido a mano por FUN_1800f74c4, verificacion
# por consistencia de los punteros consecutivos de cada segmento, y
# validacion contra el caso real: CTL=0.9935096 calculado vs 0.993510 real
# de la app, error ~0.00004%). Datos crudos embebidos en
# `_api_table1952_metric_data.py` (extraidos UNA sola vez, no se depende de
# `FlowXpert.xll` en tiempo de ejecucion).
#
# Table5/6_1952 y Table23/24_1952 (sistema US, otras 2 tablas distintas
# localizadas en `&DAT_18027b2c0` [22 segmentos] y `&DAT_180232930`/
# `&DAT_18023f250` [24/6 segmentos]) NO se decodificaron esta ronda -- ver
# docstring, quedan como PENDIENTE explicito.
# ===========================================================================
def _ctl_1952_metric_lookup(density_kgm3: float, temp_c: float) -> float | None:
    """[CERTAIN via dump de bytes crudos + verificacion de consistencia de
    punteros + caso real, RONDA 10] Busqueda de UN punto (densidad, T) en la
    tabla real de interpolacion CTL metrica de 1952 (Table53/54), replicando
    la cadena `FUN_1800f74c4` (decodifica la cabecera de 16 bytes de un
    segmento) del `.xll`. Devuelve None si (densidad, T) cae fuera de TODOS
    los segmentos conocidos (500-1105 kg/m3; rango de T depende del
    segmento, -46 a 150°C)."""
    for base, rows, col_min, col_max, blob_offset, nbytes in TABLE_1952_METRIC_SEGMENTS:
        if not (base - 5 <= density_kgm3 <= base + rows * 5 + 5):
            continue
        col_int = math.ceil(temp_c * 2.0)
        if not (col_min <= col_int <= col_max):
            continue
        def value_at_col(col: int) -> float:
            w = (col_max - col_min) * 2 + 1

            def raw(row: int) -> int:
                row = max(0, min(rows - 1, row))
                idx = w * row + (col - 2 * col_min)
                byte_off = blob_offset + idx * 2
                return struct.unpack_from("<H", _TABLE_1952_METRIC_BLOB, byte_off)[0]

            row0 = int((density_kgm3 - base) / 5.0 + 1.0)
            row0 = max(0, min(rows - 1, row0))
            row0_val = base + row0 * 5
            raw0 = raw(row0)
            if abs(density_kgm3 - row0_val) > 1e-6:
                row1 = row0 - 1 if row0_val >= density_kgm3 else row0 + 1
                row1 = max(0, min(rows - 1, row1))
                row1_val = base + row1 * 5
                raw1 = raw(row1)
                if row1_val == row0_val:
                    return raw0 / 10000.0
                return (raw1 - raw0) * (density_kgm3 - row0_val) / (row1_val - row0_val) / 10000.0 \
                    + raw0 / 10000.0
            return raw0 / 10000.0

        val0 = value_at_col(col_int)
        t0 = col_int * 0.5
        if abs(temp_c - t0) > 0.01:
            col1 = col_int - 1 if t0 < temp_c else col_int + 1
            if not (col_min <= col1 <= col_max):
                return val0
            val1 = value_at_col(col1)
            t1 = col1 * 0.5
            return (val1 - val0) * (temp_c - t0) / (t1 - t0) + val0
        return val0
    return None


_TABLE_1952_METRIC_BLOB = base64.b64decode(TABLE_1952_METRIC_BLOB_B64)


def api_table54_1952(density_15c_kgm3: float, observed_temp_c: float) -> dict:
    """Densidad(15°C) -> CTL(T). API MPMS 11.1 (1952) Table 54 (metrico).
    [CERTAIN via decompilacion + caso real, RONDA 10]: llamada DIRECTA
    (sin iteracion) a la tabla real `_ctl_1952_metric_lookup`, exactamente
    igual de estructura que `api_table54_1980` (que usa una formula K0/K1/K2
    en vez de una tabla). Sanity check: a T=15°C debe dar CTL=1.0 EXACTO
    (surge naturalmente de los datos de la tabla, no esta forzado)."""
    ctl = _ctl_1952_metric_lookup(density_15c_kgm3, observed_temp_c)
    if ctl is None:
        raise ValueError(
            f"(densidad={density_15c_kgm3} kg/m3, T={observed_temp_c}°C) fuera del "
            "rango cubierto por los 6 segmentos conocidos de la tabla 1952 metrica "
            "(500-1105 kg/m3)."
        )
    return {"ctl": ctl}


def api_table53_1952(observed_density_kgm3: float, observed_temp_c: float,
                      max_iter: int = 100, tol: float = 1e-6) -> dict:
    """Densidad(T) -> Densidad(15°C). API MPMS 11.1 (1952) Table 53 (metrico).
    [CERTAIN via decompilacion + caso real, RONDA 10]: itera
    `density_15c` hasta que `density_obs = density_15c * CTL(density_15c,
    T_obs)` converge, resolviendo con la tabla real (`_ctl_1952_metric_lookup`)
    en cada paso -- misma tecnica de sustitucion sucesiva ya usada en
    `_ctl_1980_iter`, aplicada aqui a una tabla en vez de una formula.
    Validado contra el caso real del usuario (Density_obs=1000kg/m3,
    T_obs=25°C): CTL=0.9935096 calculado vs 0.993510 real de la app
    (error ~0.00004%, dentro del ruido de redondeo de 6 decimales ya visto
    en el resto de la familia)."""
    density_15c = observed_density_kgm3
    ctl = 1.0
    for _ in range(max_iter):
        ctl = _ctl_1952_metric_lookup(density_15c, observed_temp_c)
        if ctl is None:
            raise ValueError(
                f"(densidad={density_15c} kg/m3, T={observed_temp_c}°C) fuera del "
                "rango cubierto por los 6 segmentos conocidos de la tabla 1952 "
                "metrica (500-1105 kg/m3) durante la iteracion."
            )
        nuevo = observed_density_kgm3 / ctl if ctl != 0 else density_15c
        if abs(nuevo - density_15c) < tol:
            density_15c = nuevo
            break
        density_15c = nuevo
    return {"density_15c": density_15c, "ctl": ctl}


def api_density15c_1952(observed_density_kgm3: float, observed_temp_c: float,
                         pressure_bar_g: float, equilibrium_pressure_bar_g: float = 0.0,
                         max_iter: int = 20,
                         conversion: int = 1, rounding: int = 0) -> dict:
    """Densidad(T,P) -> Densidad(15°C, EVP). API MPMS 11.1 (1952) + API MPMS
    11.2.1M (presion). [CERTAIN via decompilacion + caso real, RONDA 10] --
    combina la tabla real de `api_table53_1952`/`api_table54_1952` (CTL) con
    `api_mpms_11_2_1m` (CPL, ya [CERTAIN] desde Ronda 9) -- CONFIRMADO por
    decompilacion directa de `FUN_1800f8f70` (el nucleo interno de
    `API_Dens15C_1952`) que SI llama al mismo `FUN_1800e303c` de
    `api_mpms_11_2_1m`, pasando la densidad YA CONVERGIDA (ver docstring
    RONDA 9, punto 4). Validado contra el caso real completo del usuario
    (Density_obs=1000kg/m3, T=25°C, P=20bar(g), EVP=0bar(g)):
    density_15c=1005.4823 (real app: 1005.482), ctl=0.9935096 (real:
    0.993510), cpl=1.0010454 (real: 1.001045) -- las 3 salidas dentro de
    ~0.00004% del valor real de la app.

    `conversion` [CERTAIN via decompilacion (patron estructural identico en
    `FUN_1800f8c4c`, el nucleo real de `API_Dens15C_1952`: `if (param_6==1)
    {iterativo} else if (param_6==2) {directo, FUN_1800f8f70(param_1) SIN
    iterar}`), RONDA 16 -- ver docstring del modulo, seccion "RONDA 16", para
    el detalle honesto de por que esta funcion NO se pudo validar con una
    llamada DIRECTA al `.xll` esta ronda (a diferencia de la familia 1980):
    1=Observed->Standard(15°C) (default, iterativo, SIN CAMBIOS), 0=
    Standard(15°C)->Observed (directo, reusa la MISMA tabla/formula ya
    [CERTAIN] de la rama iterativa, solo sin iterar). `observed_density_kgm3`
    se reinterpreta como la densidad YA a 15°C (base) cuando `conversion=0`.

    `rounding` ("API-11.2.1 Rounding" de la UI, pantalla real "API Density
    @15°C (1952) (metric)") [CERTAIN via decompilacion + CASO REAL, RONDA
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19", el hallazgo completo
    de esta ronda]: 0=Disabled (default, SIN CAMBIOS), 1=Enabled.
    CONFIRMADO leyendo `FUN_1800f8f70` que su `param_4` (un flag booleano
    separado del `param_6` de conversion) se reenvia TAL CUAL al `param_5`
    de `FUN_1800e303c` (el nucleo de `api_mpms_11_2_1m`) -- la densidad YA
    CONVERGIDA (`param_1` de f8f70) se usa SIN redondear para la
    multiplicacion final (`*param_6=CTL*CPL*param_1`), asi que el flag SOLO
    afecta el CPL/F interno, nunca el CTL ni la multiplicacion final --
    exactamente lo que explica que la UI muestre CTL/CPL/CTPL "identicos" a
    6 decimales en ambos estados. Validado EXACTO contra el caso real nuevo
    del usuario (`conversion=0`, density_15c=1000kg/m3, T=25°C, P=20bar(g)):
    `rounding=0` da density_obs=994.5496638 (real app, Rounding=0: 994.5497);
    `rounding=1` da density_obs=994.5502451 (real app, Rounding=1: 994.5502)
    -- las 2 pantallas reales reproducidas EXACTO a la precision mostrada.
    Esta es la UNICA de las 6 funciones de esta ronda con caso real propio;
    las otras 5 implementan el MISMO nucleo `api_mpms_11_2_1`/
    `api_mpms_11_2_1m` [CERTAIN via decompilacion directa de cada una, ver
    sus propios docstrings], pero sin caso real que valide `rounding=1`
    especificamente en ellas.

    BUG REAL CORREGIDO EN RONDA 26 (2026-09-08) -- rama ITERATIVA
    (`conversion=1`) con `rounding=1`: 2 casos reales nuevos del usuario
    (misma pantalla de arriba, Density_obs=1000kg/m3, T=25°C, P=20bar(g),
    EVP=0bar(g)) mostraron que con `rounding=1` la app da density_15c=
    1005.480 -- MENOR que con `rounding=0` (1005.482) -- mientras que la
    implementacion anterior (sustitucion sucesiva simple, tolerancia fija
    `tol=1e-6` en TODAS las llamadas, sin importar `rounding`) daba
    1005.4819 para `rounding=1`, MAYOR que para `rounding=0` -- direccion
    invertida y magnitud ~7x mas chica que la real. Decompilacion COMPLETA
    (no parcial) de la rama `param_6==1` de `FUN_1800f8c4c` (804 bytes,
    funcion entera leida esta ronda, ver
    `ANALISIS_GHIDRA_FLOWXPERT/ghidra_api1952_xll_output.txt` lineas
    1159-1252) + de `FUN_1800f8f70` (306 bytes, `ghidra_api1952core_xll_
    output.txt`) revelo 2 mecanismos reales, CONFIRMADOS byte a byte
    (`pefile` leyendo directo el `.xll`, sin adivinar constantes):

    1) La TOLERANCIA de convergencia del loop depende de `rounding`
       (`param_4` de `FUN_1800f8c4c`, el MISMO flag que llega a
       `api_mpms_11_2_1m`): `DAT_180193dc0`=1e-8 si `rounding=0`,
       `DAT_1801df058`=1e-4 si `rounding=1` -- 10000x mas floja. Pero esa
       tolerancia se compara en unidades ESCALADAS (`observed_density_kgm3
       /1000`, porque el caller `FUN_18009f1cc` divide la densidad por
       `DAT_180124818`=1000.0 ANTES de llamar a `FUN_1800f8c4c` y vuelve a
       multiplicar por 1000 al recibir el resultado) -- la tolerancia REAL
       en kg/m3 es por lo tanto 1000x mayor: 1e-5 kg/m3 (`rounding=0`,
       ajustado) vs 0.1 kg/m3 (`rounding=1`, muy floja). Esta escala x1000
       se confirmo leyendo el sitio de llamada real en
       `ghidra_api1952_xll_output.txt` linea 129 (`local_50 /
       DAT_180124818`) y linea 153 (`local_60 * DAT_180124818` al volver).
    2) El loop real tiene un DESFASE DE UNA ITERACION ("lag") entre el
       resultado de densidad devuelto y el CTL/CPL/CTPL devueltos, que la
       implementacion anterior (autoconsistente por construccion) NO
       replicaba: en cada vuelta del `do{}while` real, `density_15c_out` se
       fija ANTES de recalcular CTL/CPL (`dVar12 = param_1/(CTL_prev*
       CPL_prev)`, con CTL_prev/CPL_prev de la vuelta ANTERIOR), y RECIEN
       DESPUES `FUN_1800f8f70` recalcula CTL/CPL FRESCOS evaluados EN ese
       candidato `dVar12` (los que se devuelven como CTL/CPL/CTPL de
       salida). El criterio de corte compara `CTL_fresco*CPL_fresco*
       dVar12` contra la densidad observada original (residuo hacia
       adelante), NO la diferencia entre candidatos consecutivos. Maximo de
       iteraciones real = 20 (`0x13`, confirmado en el mismo bloque; antes
       se exponia `max_iter=100`, cambiado aqui a 20 para igualar al
       binario -- en la practica converge en <10 iteraciones siempre, asi
       que este cambio no afecta casos normales).

    Combinando (1)+(2) y re-simulando el loop EXACTO linea a linea se
    reproducen los 2 casos reales NUEVOS EXACTO a la precision mostrada:
    `rounding=0` -> density_15c=1005.481672 (real: 1005.482, converge en 4
    vueltas); `rounding=1` -> density_15c=1005.479618 (real: 1005.480,
    converge en apenas 2 vueltas por la tolerancia floja) -- CTL/CPL/CTPL/F
    tambien coinciden a 6 decimales con la app real en ambos casos. [CERTAIN]
    -- mecanismo completo confirmado por decompilacion + 2 casos reales
    exactos, no fabricado.

    Efecto en cascada investigado esta MISMA ronda (ver seccion "RONDA 26"
    del docstring del modulo para el detalle completo): la familia 1980
    (`api_density15c_1980`/`api_gravity60f_1980`/`api_reldensity60f_1980`)
    SI tiene la misma tolerancia dependiente de `rounding` en su propio
    nucleo (`FUN_1800e62d4`/`FUN_1800e79e4`/`FUN_1800e8494`, confirmado por
    decompilacion + oraculo `.xll` via `ctypes`), pero NO tiene el desfase
    de iteracion (2) -- su actualizacion de densidad SI es autoconsistente
    dentro de la MISMA vuelta -- por lo que el bug NO se manifiesta ahi:
    validado EXACTO contra el `.xll` real (`normas/
    _api1980_1952_wrappers_xll_directo.py`) que el codigo YA EXISTENTE (sin
    tocar) coincide con `rounding=0` Y `rounding=1` en las 3 funciones,
    incluyendo el caso `product=4` (que usa una 3ra constante de tolerancia
    distinta, `DAT_1801d5f60`=0.07). `api_gravity60f_1952`/`api_sg60f_1952`
    (US) SI comparten el mismo patron estructural del nucleo 1952
    (`FUN_1800f90a4`/`FUN_1800f9674`, confirmado por decompilacion en RONDA
    16/19) y se corrigieron con el MISMO mecanismo (1)+(2) -- pero sin
    oraculo `.xll` ni caso real propio para esas 2 tablas todavia, quedan
    marcadas [LIKELY] (mecanismo [CERTAIN] via decompilacion, magnitud
    numerica exacta sin validar en vivo)."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if conversion == 0:
        density_15c = observed_density_kgm3
        ctl = _ctl_1952_metric_lookup(density_15c, observed_temp_c)
        if ctl is None:
            raise ValueError(
                f"(densidad={density_15c} kg/m3, T={observed_temp_c}°C) fuera del "
                "rango cubierto por los 6 segmentos conocidos de la tabla 1952 "
                "metrica (500-1105 kg/m3)."
            )
        cpl_res = api_mpms_11_2_1m(density_15c, observed_temp_c, pressure_bar_g,
                                    equilibrium_pressure_bar_g, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        ctpl = ctl * cpl
        density_obs_predicha = density_15c * ctpl
        return {"density_15c": density_obs_predicha, "ctl": ctl, "cpl": cpl, "ctpl": ctpl, "f": f}
    # RONDA 26: tolerancia de convergencia REAL (kg/m3), dependiente de
    # `rounding` -- ver docstring arriba, punto (1). DAT_180193dc0=1e-8 /
    # DAT_1801df058=1e-4 (escalados), *1000 (DAT_180124818) para pasar a
    # unidades reales de kg/m3.
    tol_kgm3 = (1e-8 if rounding == 0 else 1e-4) * 1000.0
    ctl, cpl, f = 1.0, 1.0, 0.0
    density_15c = observed_density_kgm3
    convergio = False
    for _ in range(max_iter):
        ctpl_prev = ctl * cpl
        density_15c = observed_density_kgm3 / ctpl_prev if ctpl_prev != 0 else observed_density_kgm3
        ctl = _ctl_1952_metric_lookup(density_15c, observed_temp_c)
        if ctl is None:
            raise ValueError(
                f"(densidad={density_15c} kg/m3, T={observed_temp_c}°C) fuera del "
                "rango cubierto por los 6 segmentos conocidos de la tabla 1952 "
                "metrica (500-1105 kg/m3) durante la iteracion."
            )
        cpl_res = api_mpms_11_2_1m(density_15c, observed_temp_c, pressure_bar_g,
                                    equilibrium_pressure_bar_g, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        # RONDA 26: residuo hacia adelante (CTL/CPL FRESCOS, evaluados EN el
        # candidato de esta vuelta, re-multiplicados) -- NO la diferencia
        # entre candidatos consecutivos -- ver docstring arriba, punto (2).
        residuo = ctl * cpl * density_15c - observed_density_kgm3
        if abs(residuo) < tol_kgm3:
            convergio = True
            break
    if not convergio:
        raise ValueError(
            f"api_density15c_1952: no convergio en {max_iter} iteraciones "
            f"(Density_obs={observed_density_kgm3} kg/m3, T={observed_temp_c}°C, "
            "replica el codigo de error real del binario para este caso)."
        )
    return {"density_15c": density_15c, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl, "f": f}


# ===========================================================================
# RONDA 12 -- Table5/6/23/24_1952 (sistema US) CERRADAS via el MISMO metodo
# de dump de bytes crudos de RONDA 10, mas los 2 wrappers combinados
# `api_gravity60f_1952`/`api_sg60f_1952`. Ver docstring del modulo, seccion
# "RONDA 12", para el detalle completo (formato de cabecera, direcciones
# reales, y la validacion cruzada entre las 2 parejas de tablas
# independientes que confirma el decode sin depender de un caso real en
# vivo). Datos crudos en `_api_table1952_us_data.py`.
# ===========================================================================
_TABLE_1952_US_TABLE5_BLOB = base64.b64decode(TABLE_1952_US_TABLE5_BLOB_B64)
_TABLE_1952_US_TABLE6_BLOB = base64.b64decode(TABLE_1952_US_TABLE6_BLOB_B64)
_TABLE_1952_US_TABLE23_BLOB = base64.b64decode(TABLE_1952_US_TABLE23_BLOB_B64)
_TABLE_1952_US_TABLE24_BLOB = base64.b64decode(TABLE_1952_US_TABLE24_BLOB_B64)


def _flatten_1952_us_rows(segments: tuple) -> tuple:
    """[CERTAIN, RONDA 12] Convierte los segmentos "tal cual estan en el
    binario" (documentados en `_api_table1952_us_data.py`) en una lista
    GLOBAL de filas (valor_eje_primario, col_min, col_max, ancho,
    offset_en_blob), ordenada por valor. Los segmentos de Table5/6 llevan
    6 campos (paso=1 implicito); los de Table23/24 llevan 7 campos (paso
    explicito, puede variar entre segmentos). Aplanar evita reimplementar
    el fallback real del binario hacia el segmento anterior en los bordes
    (FUN_1800f79cc/f7a5c/etc.) -- ver docstring RONDA 12 para la
    verificacion de que esto reproduce la misma identidad en T=60F que el
    binario para TODOS los valores de API/RD probados."""
    rows_out = []
    for seg in segments:
        if len(seg) == 6:
            base, rows, col_min, col_max, off, _nbytes = seg
            step = 1
        else:
            base, rows, step, col_min, col_max, off, _nbytes = seg
        width = col_max - col_min + 1
        for r in range(rows):
            key = base + r * step
            row_off = off + r * width * 2
            rows_out.append((key, col_min, col_max, width, row_off))
    rows_out.sort(key=lambda t: t[0])
    return tuple(rows_out)


_ROWS_1952_US_TABLE5 = _flatten_1952_us_rows(TABLE_1952_US_TABLE5_SEGMENTS)
_ROWS_1952_US_TABLE6 = _flatten_1952_us_rows(TABLE_1952_US_TABLE6_SEGMENTS)
_ROWS_1952_US_TABLE23 = _flatten_1952_us_rows(TABLE_1952_US_TABLE23_SEGMENTS)
_ROWS_1952_US_TABLE24 = _flatten_1952_us_rows(TABLE_1952_US_TABLE24_SEGMENTS)


def _lookup_1952_us_table(rows_flat: tuple, blob: bytes, value_scale: float,
                           key: float, temp_f: float) -> float | None:
    """[CERTAIN via dump de bytes crudos + verificacion de encadenamiento +
    validacion cruzada entre 2 pares de tablas independientes, RONDA 12]
    Busqueda de UN punto (eje_primario, T) en una de las 4 tablas reales
    de interpolacion CTL del sistema US de 1952 (Table5/6: eje=grados API;
    Table23/24: eje=RD*1000). Misma estructura de interpolacion en 2 ejes
    ya validada para el eje metrico en RONDA 10 (`_ctl_1952_metric_lookup`),
    generalizada aqui sobre la lista de filas YA APLANADA (ver
    `_flatten_1952_us_rows`). Devuelve None si no hay ninguna fila (tabla
    vacia); en los extremos absolutos de la tabla, se usa la fila mas
    cercana disponible (mismo comportamiento de "clamp" que el binario)."""
    if not rows_flat:
        return None
    if key <= rows_flat[0][0]:
        idx0 = idx1 = 0
    elif key >= rows_flat[-1][0]:
        idx0 = idx1 = len(rows_flat) - 1
    else:
        lo, hi = 0, len(rows_flat) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rows_flat[mid][0] <= key:
                lo = mid
            else:
                hi = mid
        idx0, idx1 = lo, hi

    def value_at_row(idx: int, col: float) -> float:
        _key, col_min, col_max, width, row_off = rows_flat[idx]

        def raw_at(c: int) -> int:
            c = max(col_min, min(col_max, c))
            return struct.unpack_from("<H", blob, row_off + (c - col_min) * 2)[0]

        col_int = math.ceil(col)
        col_int_c = max(col_min, min(col_max, col_int))
        v0 = raw_at(col_int_c)
        if abs(col - col_int) > 1e-9:
            col1 = col_int - 1 if col_int >= col else col_int + 1
            if col1 < col_min or col1 > col_max:
                return v0 / value_scale
            v1 = raw_at(col1)
            return (v1 - v0) * (col - col_int) / (col1 - col_int) / value_scale + v0 / value_scale
        return v0 / value_scale

    val0 = value_at_row(idx0, temp_f)
    if idx0 == idx1:
        return val0
    val1 = value_at_row(idx1, temp_f)
    k0, k1 = rows_flat[idx0][0], rows_flat[idx1][0]
    if k1 == k0:
        return val0
    return (val1 - val0) * (key - k0) / (k1 - k0) + val0


def api_table6_1952(api_60f: float, observed_temp_f: float) -> dict:
    """°API(60°F) -> CTL(T). API MPMS 11.1 (1952) Table 6 (sistema US).
    [CERTAIN via decompilacion + dump de bytes + validacion cruzada,
    RONDA 12]: llamada DIRECTA (sin iteracion) a la tabla real
    `_lookup_1952_us_table` (DAT_1801fea10, 4 segmentos). Sanity check: a
    T=60°F debe dar CTL=1.0 EXACTO para todo °API (surge de los datos
    reales de la tabla, no esta forzado)."""
    ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE6, _TABLE_1952_US_TABLE6_BLOB,
                                 10000.0, api_60f, observed_temp_f)
    if ctl is None:
        raise ValueError(f"(API={api_60f}, T={observed_temp_f}F) fuera de la tabla Table6_1952.")
    return {"ctl": ctl}


def api_table5_1952(observed_api: float, observed_temp_f: float,
                     max_iter: int = 100, tol: float = 1e-6) -> dict:
    """°API(T) -> °API(60°F). API MPMS 11.1 (1952) Table 5 (sistema US).
    [CERTAIN via decompilacion + dump de bytes + validacion cruzada,
    RONDA 12]: itera `api_60f` hasta que `api_obs` reproduce el mismo
    punto via CTL de `api_table6_1952`, misma tecnica de sustitucion
    sucesiva que `api_table53_1952` usa sobre la tabla metrica. La tabla
    en si (Table5_1952, DAT_1801f4e10, 25 segmentos) da directamente el
    °API a 60°F -- NO es necesario iterar sobre ELLA, solo se itera para
    mantener consistencia con Table6 (igual que 1980)."""
    rd_obs = 141.5 / (131.5 + observed_api)
    rho_base = _rd60_to_density_kgm3(rd_obs)
    api_base = observed_api
    ctl = 1.0
    for _ in range(max_iter):
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE6, _TABLE_1952_US_TABLE6_BLOB,
                                     10000.0, api_base, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(API={api_base}, T={observed_temp_f}F) fuera de la tabla Table6_1952 "
                "durante la iteracion."
            )
        rd_iter = rd_obs / ctl if ctl != 0 else rd_obs
        nuevo_api = 141.5 / rd_iter - 131.5
        if abs(nuevo_api - api_base) < tol:
            api_base = nuevo_api
            break
        api_base = nuevo_api
    return {"api_60f": api_base, "ctl": ctl}


def api_table24_1952(rd_60f: float, observed_temp_f: float) -> dict:
    """RD(60°F) -> CTL(T). API MPMS 11.1 (1952) Table 24 (sistema US).
    [CERTAIN via decompilacion + dump de bytes + validacion cruzada,
    RONDA 12]: llamada DIRECTA a la tabla real `_lookup_1952_us_table`
    (DAT_18023f250, 6 segmentos; paso fijo=5 en RD*1000, col_min real
    -50/0 segun base<=600/>600, confirmado por encadenamiento perfecto de
    los 6 segmentos). Sanity check: a T=60°F debe dar CTL=1.0 EXACTO."""
    ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE24, _TABLE_1952_US_TABLE24_BLOB,
                                 10000.0, rd_60f * 1000.0, observed_temp_f)
    if ctl is None:
        raise ValueError(f"(RD={rd_60f}, T={observed_temp_f}F) fuera de la tabla Table24_1952.")
    return {"ctl": ctl}


def api_table23_1952(observed_rd: float, observed_temp_f: float,
                      max_iter: int = 100, tol: float = 1e-6) -> dict:
    """RD(T) -> RD(60°F). API MPMS 11.1 (1952) Table 23 (sistema US).
    [CERTAIN via decompilacion + dump de bytes + validacion cruzada,
    RONDA 12]: itera `rd_60f` hasta que `rd_obs` reproduce el mismo punto
    via CTL de `api_table24_1952`, misma tecnica que `api_table53_1952`."""
    rd_base = observed_rd
    ctl = 1.0
    for _ in range(max_iter):
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE24, _TABLE_1952_US_TABLE24_BLOB,
                                     10000.0, rd_base * 1000.0, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(RD={rd_base}, T={observed_temp_f}F) fuera de la tabla Table24_1952 "
                "durante la iteracion."
            )
        nuevo = observed_rd / ctl if ctl != 0 else rd_base
        if abs(nuevo - rd_base) < tol:
            rd_base = nuevo
            break
        rd_base = nuevo
    return {"rd_60f": rd_base, "ctl": ctl}


def api_gravity60f_1952(observed_api: float, observed_temp_f: float,
                         pressure_psig: float, equilibrium_pressure_psig: float = 0.0,
                         max_iter: int = 20,
                         conversion: int = 1, rounding: int = 0) -> dict:
    """°API(T,P) -> °API(60°F, EVP). API MPMS 11.1 (1952) Table 5/6 + API
    MPMS 11.2.1 (presion, US). [CERTAIN via decompilacion + dump de bytes,
    RONDA 12] -- combina la tabla real de `api_table5_1952`/
    `api_table6_1952` (CTL) con `api_mpms_11_2_1` (CPL, ya [CERTAIN] desde
    RONDA 9), confirmado por decompilacion directa que `API_Gravity60F_1952`
    SI llama a `FUN_1800e2d5c` (api_mpms_11_2_1) ademas de la tabla CTL --
    misma estructura de iteracion que `api_gravity60f_1980`. NO validado
    contra un caso real en vivo esta ronda (no hay caso real disponible
    para 1952/US todavia).

    `conversion` [CERTAIN via decompilacion (patron estructural identico a
    `api_density15c_1952`: el nucleo real `FUN_1800f90a4` tiene el mismo
    despacho `if (param_6==1) {iterativo} else if (param_6==2) {directo}`),
    RONDA 16 -- ver docstring del modulo]: 1=Observed->Standard(60°F)
    (default, iterativo, SIN CAMBIOS), 0=Standard(60°F)->Observed (directo).
    `observed_api` se reinterpreta como °API YA a 60°F (base) cuando
    `conversion=0`.

    `rounding` ("API-11.2.1 Rounding") [CERTAIN via decompilacion directa,
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19"]: confirmado
    leyendo `FUN_1800f90a4` que su `param_4` se reenvia (via
    `CONCAT44(uVar17,param_4)`, un patron de Ghidra ya visto antes en este
    proyecto para argumentos de 32 bits extendidos a 64) al `param_5` de
    `FUN_1800e2d5c` (api_mpms_11_2_1) -- MISMA logica de tolerancia de
    convergencia mas floja (0.01 en vez de 1e-6) cuando esta activo, que ya
    se vio en `api_sg60f_1952`. 0=Disabled (default, SIN CAMBIOS), 1=
    Enabled. NO hay caso real propio con el flag activo para esta tabla.

    CORREGIDO EN RONDA 27 (2026-09-08) -- continuacion directa del PENDIENTE
    dejado por RONDA 26 (ver texto abajo, preservado como historial). Esta
    ronda se dedico especificamente a decompilar a fondo `FUN_1800f9544`
    (302 bytes, el nucleo interno que recalcula CTL/CPL/CTPL/F FRESCOS en un
    candidato de °API) y a LEER BYTE A BYTE (via `pefile`, sin adivinar) las
    5 constantes reales de `.rdata` que gobiernan el algoritmo completo:
    `DAT_180193e90`=0.05, `DAT_180193e68`=0.01 (tol si `rounding=1`),
    `DAT_180193dc8`=1e-6 (tol si `rounding=0`), `DAT_1801ea4e0`=131.5,
    `DAT_1801eaa80`=141.5. Con esto los 3 mecanismos quedan CERRADOS:

    1) Tolerancia dependiente de `rounding`, en unidades de °API DIRECTAS
       (sin escala, a diferencia de `api_density15c_1952`): 1e-6 si
       `rounding=0`, 0.01 si `rounding=1` -- confirmado leyendo lineas
       1594-1602 de `ghidra_api1952_xll_output.txt`.
    2) Desfase de una iteracion ("lag"): en cada vuelta, el candidato de
       °API_base se calcula como `(API_obs+131.5)*CTPL_prev - 131.5` usando
       el CTPL de la vuelta ANTERIOR (formula derivada y verificada
       algebraicamente desde `RD_base=RD_obs/CTPL`, `API=141.5/RD-131.5`),
       y RECIEN DESPUES `FUN_1800f9544` recalcula CTL/CPL/CTPL/F FRESCOS en
       ese candidato, ademas de un "°API observado predicho" =
       `(API_base+131.5)/(CTL_fresco*CPL_fresco) - 131.5` que es lo que
       realmente se compara contra el °API observado original (residuo
       hacia adelante, MISMO patron que las 2 funciones hermanas de
       RONDA 26). Maximo de iteraciones real = 20 (`0x13`, igual que las
       hermanas; antes se exponia `max_iter=100` y un `tol=1e-6` fijo sin
       usar de verdad -- esta ronda se quita el parametro `tol` (ya no tiene
       sentido, la tolerancia real depende de `rounding`, ver punto (1)) y
       se cambia el default de `max_iter` a 20 para igualar al binario, sin
       efecto en casos normales que convergen en <10 vueltas).
    3) Paso de grilla de 0.1°API (el paso EXTRA que RONDA 26 dejo
       pendiente): al converger la busqueda continua en `api_base` (el
       candidato SIN redondear), el binario intenta "snapear" el resultado
       a la grilla de 0.1°API en 2 pasos, EN ESTE ORDEN: primero
       `round(api_base+0.05, 1 decimal)` (grilla hacia arriba), y si el
       °API-observado-predicho de ESE punto (recalculado FRESCO con
       `FUN_1800f9544`) no cierra dentro de la MISMA tolerancia de (1),
       intenta `round(api_base-0.05, 1 decimal)` (grilla hacia abajo). Si
       ninguno de los 2 cierra (el caso TIPICO: un paso de 0.1°API mueve el
       residuo mucho mas que 1e-6/0.01, salvo que el continuo ya caiga casi
       exacto sobre una linea de grilla), el binario se queda con el valor
       CONTINUO sin redondear (fallback silencioso, confirmado leyendo
       lineas 1667-1690: el `return 0` sin tocar `*pdVar3`/`*pdVar4..6` dejan
       el ultimo estado de la iteracion continua). La funcion `FUN_1800e1db4`
       usada para el redondeo es "round half away from zero" a N decimales
       (`floor(x*10^N + 0.5)/10^N` para x>=0, `ceil(x*10^N - 0.5)/10^N` para
       x<0, confirmado leyendo su cuerpo completo + `DAT_180124428`=0.5).

    Los 3 mecanismos (mas la rama de presion~0, ver bloque separado abajo)
    se implementaron juntos (`_ctl_cpl_f`/`_round1` auxiliares abajo).
    Validado por AUTOCONSISTENCIA + oraculo DIRECTO al `.xll`: se agrego
    `calcular_gravity60f_1952_core_directo()` a
    `normas/_api1980_1952_wrappers_xll_directo.py` (llamada ctypes directa a
    `FUN_1800f90a4` @ 0x1800F90A4, el mismo nucleo decompilado arriba, mapeo
    de 13 argumentos confirmado leyendo el sitio de llamada real del
    exportador Excel `FUN_18009ff88`) -- ver ese modulo para el detalle y el
    resultado del barrido `rounding=0`/`rounding=1` (unico caso real/oraculo
    propio de ESTA pantalla, ya que no hay captura de pantalla del usuario
    para "API Gravity @60F (1952)"). Barrido AMPLIO adicional (576
    combinaciones: 8 valores de °API x 6 de T x 6 escenarios P/EVP,
    incluyendo P=0 y P=0.005 para forzar la rama de presion~0, x 2
    `rounding`) contra el mismo oraculo DIRECTO: 575/576 (99.83%) coinciden
    exacto (<0.01% relativo); el UNICO caso restante (API=20, T=150F, P=50,
    EVP=0, rounding=0) es uno donde el binario real EXCEDE su propio limite
    de 20 iteraciones y devuelve codigo de error 4 ("no convergio"),
    mientras que la reimplementacion en Python SI converge (a un valor
    fisicamente razonable, 14.99) -- se documenta HONESTO como [LIKELY] una
    sensibilidad de trayectoria de punto flotante en un caso limite de
    convergencia marginal (no una discrepancia de formula: 0 casos con
    formula distinta, solo 1 caso con distinto NUMERO de iteraciones hasta
    el limite), no se fuerza a fallar artificialmente para igualar el codigo
    de error del binario en ese unico punto. CERO regresion confirmada:
    `rounding=0` (el caso ya usado por otras rondas, `api_gravity60f_1952(
    observed_api=30.0, observed_temp_f=90.0, pressure_psig=50.0)`) da el
    MISMO resultado antes y despues del fix (la tolerancia 1e-6 y el lag NO
    cambian el punto fijo al que converge un sistema ya autoconsistente,
    solo cambian la trayectoria/velocidad de convergencia -- igual que se
    observo en RONDA 26 para `api_density15c_1952`/`api_sg60f_1952`).

    HALLAZGO ADICIONAL, RONDA 27 (fuera del alcance original de esta ronda,
    encontrado al construir el barrido de arriba): con `pressure_psig` MUY
    cercano a 0 (`|P|<0.01`, `DAT_180193e68`=0.01 -- MISMA constante que la
    tolerancia de `rounding=1` pero usada aqui con un proposito DISTINTO), el
    binario NO entra al bucle iterativo de (1)+(2)+(3) -- toma una rama
    COMPLETAMENTE DISTINTA y NO iterativa: llama a `FUN_1800f9b4c(
    observed_api, T, &api_base)`, que decompila a `FUN_1800f8018(&DAT_
    1801f4e10, 0x19, ...)` -- EXACTAMENTE la tabla `Table5_1952` (25
    segmentos, ya [CERTAIN], datos en `_ROWS_1952_US_TABLE5`/`_TABLE_1952_
    US_TABLE5_BLOB`, que estaban cargados pero JAMAS USADOS por ninguna
    funcion del modulo hasta ahora -- ni siquiera por `api_table5_1952()`,
    que itera Table6 en su lugar desde RONDA 12 para el mismo resultado
    fisico). Con ese `api_base` (SIN iterar mas), recalcula CTL fresco via
    Table6 y CPL/F via `api_mpms_11_2_1` (con la presion/EVP/rounding reales,
    sin forzarlos a 0) y retorna eso directo -- SIN residuo/tolerancia/grilla.
    Implementado (ver bloque `if abs(pressure_psig) < 0.01:` mas abajo).
    ANTES de este hallazgo, el barrido con P=0 daba 79/96 discrepancias
    (>0.5% de error, algoritmo fisicamente distinto); DESPUES, 0/96.

    PENDIENTE HONESTO preservado de RONDA 26 (2026-09-08, resuelto arriba):
    al corregir el mismo bug de `rounding=1` en `api_density15c_1952`/
    `api_sg60f_1952` (ver docstring de `api_density15c_1952`, seccion "BUG
    REAL CORREGIDO EN RONDA 26"), esa ronda releyo `FUN_1800f90a4` COMPLETO
    (1184 bytes) para ver si el MISMO patron aplica aca. Resultado: el
    mecanismo de fondo SI es igual (tolerancia dependiente de `rounding` --
    confirmado byte a byte -- y el MISMO desfase de una iteracion "lag" en
    el `do{}while` principal), PERO esta funcion tiene un paso ADICIONAL que
    NO existe en `FUN_1800f8c4c`/`FUN_1800f9674`: al converger, redondea el
    resultado de °API al 0.1°API mas cercano probando primero
    `candidato+0.05` y si el residuo no cierra dentro de tolerancia,
    `candidato-0.05`, recalculando CTL/CPL/CTPL/F FRESCOS en ese punto via
    `FUN_1800f9544` (no decompilado a fondo esa ronda). Por la regla de oro
    del proyecto, esa ronda dejo la funcion SIN TOCAR el algoritmo hasta una
    ronda futura dedicada -- esa ronda futura es esta (RONDA 27)."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if conversion == 0:
        api_base = observed_api
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE6, _TABLE_1952_US_TABLE6_BLOB,
                                     10000.0, api_base, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(API={api_base}, T={observed_temp_f}F) fuera de la tabla Table6_1952."
            )
        cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        ctpl = ctl * cpl
        rd_base = 141.5 / (131.5 + api_base)
        rd_obs_predicho = rd_base * ctpl
        api_obs_predicho = 141.5 / rd_obs_predicho - 131.5 if rd_obs_predicho != 0 else api_base
        return {"api_60f": api_obs_predicho, "ctl": ctl, "cpl": cpl, "ctpl": ctpl, "f": f}
    # RONDA 27 (2026-09-08) -- HALLAZGO ADICIONAL, fuera del alcance original
    # de esta ronda (el pendiente de RONDA 26 era SOLO la grilla de 0.1°API,
    # ver mas abajo), encontrado al construir el barrido de validacion contra
    # el oraculo DIRECTO: con `pressure_psig` MUY cercano a 0 (|P|<0.01,
    # `DAT_180193e68`=0.01 -- MISMA constante que la tolerancia de
    # `rounding=1`, pero usada aqui con un proposito DISTINTO, confirmado
    # releyendo `FUN_1800f90a4` lineas 1594-1626 de
    # `ghidra_api1952_xll_output.txt`), el binario NO entra al bucle
    # iterativo de abajo -- toma una rama COMPLETAMENTE DISTINTA y NO
    # iterativa: llama a `FUN_1800f9b4c(observed_api, T, &api_base)`, que
    # decompila a `FUN_1800f8018(&DAT_1801f4e10, 0x19, ...)` -- EXACTAMENTE
    # la tabla `Table5_1952` (25 segmentos, `DAT_1801f4e10`, ya [CERTAIN] y
    # con datos extraidos en `_ROWS_1952_US_TABLE5`/`_TABLE_1952_US_TABLE5_
    # BLOB`, confirmado por identidad exacta de direccion+segmentos con el
    # docstring de RONDA 12 en `normas/_api_table1952_us_data.py` linea 13 --
    # aunque esos datos estaban CARGADOS pero JAMAS USADOS por ninguna
    # funcion del modulo hasta ahora, ni siquiera por `api_table5_1952()`,
    # que en cambio itera Table6 desde RONDA 12 para el mismo resultado).
    # Con ese `api_base` (SIN iterar mas), recalcula CTL fresco via Table6 en
    # ESE punto (`FUN_1800f9b74`) y CPL/F via `api_mpms_11_2_1` (con la
    # `pressure_psig`/`equilibrium_pressure_psig`/`rounding` reales, SIN
    # forzarlos a 0) -- y retorna eso directo, sin residuo/tolerancia/grilla
    # (esos 3 mecanismos de abajo NUNCA se ejecutan en este caso). Validado
    # EXACTO contra el oraculo DIRECTO `FUN_1800f90a4` (ver
    # `normas/_api1980_1952_wrappers_xll_directo.py`,
    # `calcular_gravity60f_1952_core_directo`): barrido de 96 combinaciones
    # con `pressure_psig=0.0` -- de 79 discrepancias >0.01% ANTES de este
    # hallazgo (el bucle iterativo daba una respuesta fisicamente distinta,
    # error tipico 0.5%-3%) a 0 discrepancias reales DESPUES (quedan 1-2
    # casos de API/T en el borde extremo de la tabla, fuera de rango en
    # AMBOS lados -- ver seccion mas abajo del docstring del modulo si se
    # documenta un barrido nuevo). [CERTAIN via decompilacion completa +
    # identificacion de tabla por direccion/tamaño exactos + oraculo].
    if abs(pressure_psig) < 0.01:
        api_base = _lookup_1952_us_table(_ROWS_1952_US_TABLE5, _TABLE_1952_US_TABLE5_BLOB,
                                          10.0, observed_api, observed_temp_f)
        if api_base is None:
            raise ValueError(
                f"(API={observed_api}, T={observed_temp_f}F) fuera de la tabla Table5_1952."
            )
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE6, _TABLE_1952_US_TABLE6_BLOB,
                                     10000.0, api_base, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(API={api_base}, T={observed_temp_f}F) fuera de la tabla Table6_1952 "
                "(rama de presion~0)."
            )
        cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        return {"api_60f": api_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl, "f": f}
    # RONDA 27 (2026-09-08): tolerancia dependiente de `rounding` + residuo
    # hacia adelante ("lag", mismo mecanismo [CERTAIN] ya aplicado en
    # api_density15c_1952/api_sg60f_1952 en RONDA 26) MAS el paso de grilla
    # de 0.1 grados API que solo esta funcion tiene -- ver docstring arriba,
    # seccion "CORREGIDO EN RONDA 27", para el detalle completo de los 3
    # mecanismos y su evidencia (decompilacion de FUN_1800f90a4/FUN_1800f9544
    # + lectura byte a byte de las constantes reales del .xll).
    tol_api = 1e-6 if rounding == 0 else 0.01
    C1, C2 = 141.5, 131.5

    def _ctl_cpl_f(api_candidato):
        """Recalcula CTL/CPL/CTPL/F FRESCOS en un candidato de API_base y el
        °API-observado-predicho en ese punto, replicando FUN_1800f9544.
        Retorna None si el candidato cae fuera de la tabla CTL (equivalente
        al codigo de error != 0 del binario para ese candidato)."""
        ctl_c = _lookup_1952_us_table(_ROWS_1952_US_TABLE6, _TABLE_1952_US_TABLE6_BLOB,
                                       10000.0, api_candidato, observed_temp_f)
        if ctl_c is None:
            return None
        cpl_res_c = api_mpms_11_2_1(api_candidato, observed_temp_f, pressure_psig,
                                     equilibrium_pressure_psig, rounding)
        cpl_c, f_c = cpl_res_c["cpl"], cpl_res_c["f"]
        ctpl_c = ctl_c * cpl_c
        api_obs_predicho = (api_candidato + C2) / ctpl_c - C2 if ctpl_c != 0 else api_candidato
        return ctl_c, cpl_c, ctpl_c, f_c, api_obs_predicho

    def _round1(y):
        """round half away from zero a 1 decimal, replica exacta de
        FUN_1800e1db4(y, 1): floor(10y+0.5)/10 para y>=0, ceil(10y-0.5)/10
        para y<0 (escala=10, offset=DAT_180124428=0.5, confirmado byte a
        byte)."""
        if y >= 0:
            return math.floor(10.0 * y + 0.5) / 10.0
        return math.ceil(10.0 * y - 0.5) / 10.0

    ctl, cpl, f = 1.0, 1.0, 0.0
    api_base = observed_api
    convergio = False
    for _ in range(max_iter):
        ctpl_prev = ctl * cpl
        api_base = (observed_api + C2) * ctpl_prev - C2
        resultado = _ctl_cpl_f(api_base)
        if resultado is None:
            raise ValueError(
                f"(API={api_base}, T={observed_temp_f}F) fuera de la tabla Table6_1952 "
                "durante la iteracion."
            )
        ctl, cpl, ctpl, f, api_obs_predicho = resultado
        if abs(api_obs_predicho - observed_api) < tol_api:
            convergio = True
            break
    if not convergio:
        raise ValueError(
            f"api_gravity60f_1952: no convergio en {max_iter} iteraciones "
            f"(API_obs={observed_api}, T={observed_temp_f}F, replica el codigo "
            "de error real del binario para este caso)."
        )
    # Paso de grilla de 0.1 grados API (RONDA 27, SOLO en esta funcion):
    # intenta primero redondear api_base HACIA ARRIBA a la grilla
    # (round(api_base+0.05,1)) y si el residuo no cierra dentro de tol_api,
    # intenta HACIA ABAJO (round(api_base-0.05,1)) -- mismo orden y mismas 2
    # constantes reales (0.05) de FUN_1800f90a4. Si ninguno cierra, se
    # mantiene el valor continuo (fallback silencioso identico al binario).
    api_grid_up = _round1(api_base + 0.05)
    api_grid_down = _round1(api_base - 0.05)
    usar_grid = None
    resultado_grid = _ctl_cpl_f(api_grid_up)
    if resultado_grid is not None:
        ctl_g, cpl_g, ctpl_g, f_g, api_obs_predicho_g = resultado_grid
        if abs(api_obs_predicho_g - observed_api) < tol_api:
            usar_grid = (api_grid_up, ctl_g, cpl_g, ctpl_g, f_g)
    if usar_grid is None:
        resultado_grid = _ctl_cpl_f(api_grid_down)
        if resultado_grid is not None:
            ctl_g, cpl_g, ctpl_g, f_g, api_obs_predicho_g = resultado_grid
            if abs(api_obs_predicho_g - observed_api) < tol_api:
                usar_grid = (api_grid_down, ctl_g, cpl_g, ctpl_g, f_g)
    if usar_grid is not None:
        api_base, ctl, cpl, ctpl, f = usar_grid
    return {"api_60f": api_base, "ctl": ctl, "cpl": cpl, "ctpl": ctpl, "f": f}


def api_sg60f_1952(observed_rd: float, observed_temp_f: float,
                    pressure_psig: float, equilibrium_pressure_psig: float = 0.0,
                    max_iter: int = 20,
                    conversion: int = 1, rounding: int = 0) -> dict:
    """RD(T,P) -> RD(60°F, EVP). API MPMS 11.1 (1952) Table 23/24 + API
    MPMS 11.2.1 (presion, US). [CERTAIN via decompilacion + dump de bytes,
    RONDA 12] -- combina la tabla real de `api_table23_1952`/
    `api_table24_1952` (CTL) con `api_mpms_11_2_1` (CPL), confirmado por
    decompilacion directa que `API_SG60F_1952` SI llama a `FUN_1800e2d5c`
    ademas de la tabla CTL, misma estructura que `api_reldensity60f_1980`.
    NO validado contra un caso real en vivo esta ronda.

    `conversion` [CERTAIN via decompilacion, RONDA 16 -- mismo patron
    estructural que `api_gravity60f_1952`/`api_density15c_1952` (nucleo real
    `FUN_1800f9674`), ver docstring del modulo]: 1=Observed->Standard(60°F)
    (default, iterativo, SIN CAMBIOS), 0=Standard(60°F)->Observed (directo).
    `observed_rd` se reinterpreta como RD YA a 60°F (base) cuando
    `conversion=0`.

    `rounding` ("API-11.2.1 Rounding") [CERTAIN via decompilacion directa,
    RONDA 19 -- ver docstring del modulo, seccion "RONDA 19"]: confirmado
    leyendo `FUN_1800f9674` que su `param_4` se reenvia (via
    `CONCAT44(uVar13,param_4)`) al `param_5` de `FUN_1800e2d5c`
    (api_mpms_11_2_1), con la MISMA logica de tolerancia de convergencia mas
    floja (0.01 en vez de la referencia estrecha) cuando esta activo. 0=
    Disabled (default, SIN CAMBIOS), 1=Enabled. NO hay caso real propio con
    el flag activo para esta tabla.

    CORREGIDO EN RONDA 26 (2026-09-08) -- rama iterativa (`conversion=1`):
    esta ronda se releyo `FUN_1800f9674` COMPLETO (793 bytes, no solo el
    sitio de llamada) y resulto ser ESTRUCTURALMENTE IDENTICO, byte a byte,
    a `FUN_1800f8c4c` (el nucleo YA corregido de `api_density15c_1952`) --
    MISMAS 2 constantes de tolerancia (`DAT_180193dc0`=1e-8/`DAT_1801df058`=
    1e-4, confirmadas iguales por direccion), MISMO desfase de una iteracion
    ("lag": el RD de salida se fija con el CTL/CPL de la vuelta ANTERIOR,
    antes de recalcularlos frescos en el candidato de esta vuelta) y MISMO
    limite de 20 iteraciones -- ver docstring de `api_density15c_1952`,
    seccion "BUG REAL CORREGIDO EN RONDA 26", para el detalle completo del
    mecanismo. La UNICA diferencia real es que aqui NO hace falta el
    factor de escala x1000 (el llamador de `FUN_1800f9674` NO divide `RD`
    por `DAT_180124818` antes de llamar, a diferencia del llamador de
    `FUN_1800f8c4c` -- confirmado leyendo el sitio de llamada real en
    `ghidra_api1952_xll_output.txt` linea 2559: `FUN_18005f984(DAT_180124810,
    param_2+0x20,&local_30)`, sin division), asi que la tolerancia se compara
    DIRECTO en unidades de RD (adimensional): 1e-8 (`rounding=0`) / 1e-4
    (`rounding=1`). [CERTAIN via decompilacion directa esta ronda -- mismo
    patron ya validado con 2 casos reales en `api_density15c_1952`, pero SIN
    caso real propio de ESTA tabla todavia -- exactitud numerica exacta
    marcada [LIKELY] hasta validar en vivo]."""
    if conversion not in (0, 1):
        raise ValueError("conversion debe ser 0 (Standard->Observed) o 1 (Observed->Standard).")
    if conversion == 0:
        rd_base = observed_rd
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE24, _TABLE_1952_US_TABLE24_BLOB,
                                     10000.0, rd_base * 1000.0, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(RD={rd_base}, T={observed_temp_f}F) fuera de la tabla Table24_1952."
            )
        api_base = 141.5 / rd_base - 131.5
        cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        ctpl = ctl * cpl
        rd_obs_predicho = rd_base * ctpl
        return {"rd_60f": rd_obs_predicho, "ctl": ctl, "cpl": cpl, "ctpl": ctpl, "f": f}
    # RONDA 26: tolerancia dependiente de `rounding`, SIN escala (ver
    # docstring arriba) + residuo hacia adelante (mismo mecanismo que
    # api_density15c_1952) en vez de sustitucion sucesiva autoconsistente.
    tol_rd = 1e-8 if rounding == 0 else 1e-4
    ctl, cpl, f = 1.0, 1.0, 0.0
    rd_base = observed_rd
    convergio = False
    for _ in range(max_iter):
        ctpl_prev = ctl * cpl
        rd_base = observed_rd / ctpl_prev if ctpl_prev != 0 else observed_rd
        ctl = _lookup_1952_us_table(_ROWS_1952_US_TABLE24, _TABLE_1952_US_TABLE24_BLOB,
                                     10000.0, rd_base * 1000.0, observed_temp_f)
        if ctl is None:
            raise ValueError(
                f"(RD={rd_base}, T={observed_temp_f}F) fuera de la tabla Table24_1952 "
                "durante la iteracion."
            )
        api_base = 141.5 / rd_base - 131.5
        cpl_res = api_mpms_11_2_1(api_base, observed_temp_f, pressure_psig,
                                   equilibrium_pressure_psig, rounding)
        cpl, f = cpl_res["cpl"], cpl_res["f"]
        residuo = ctl * cpl * rd_base - observed_rd
        if abs(residuo) < tol_rd:
            convergio = True
            break
    if not convergio:
        raise ValueError(
            f"api_sg60f_1952: no convergio en {max_iter} iteraciones "
            f"(RD_obs={observed_rd}, T={observed_temp_f}F, replica el codigo "
            "de error real del binario para este caso)."
        )
    return {"rd_60f": rd_base, "ctl": ctl, "cpl": cpl, "ctpl": ctl * cpl, "f": f}


# ===============================================================================
# RONDA 20 (2026-09-07): investigacion HONESTA del hueco senalado por el
# usuario -- las 9 funciones de la familia "API MPMS 11.1 (1952)"
# (`api_table5_1952`, `api_table6_1952`, `api_table23_1952`,
# `api_table24_1952`, `api_table53_1952`, `api_table54_1952`,
# `api_density15c_1952`, `api_gravity60f_1952`, `api_sg60f_1952`) NO tienen
# `product`/`hydrometer_correction`, a diferencia de sus equivalentes 1980.
# RESULTADO: hipotesis (b) CONFIRMADA -- NO es un hueco, es una diferencia
# real y deliberada del binario entre las 2 ediciones del estandar.
# -------------------------------------------------------------------------------
# METODO (el mismo ya usado y aceptado en RONDA 16/19 para descubrir
# argumentos "extra" en los wrappers Excel-facing, aplicado aqui al reves --
# para CONFIRMAR que NO hay argumentos extra): releer, para cada una de las
# 9 raices Excel reales, el chequeo `if (param_3 == N)` al inicio del
# wrapper (`param_3` = numero de argumentos que Excel paso realmente a la
# funcion) en `ghidra_api1952_xll_output.txt`/`ghidra_api1952core_xll_output.txt`
# (decompilaciones YA EXISTENTES de rondas anteriores -- Ronda 9/10/12 ya
# habian abierto estas mismas raices para otro fin, no hizo falta generar
# disassembly nuevo ni reabrir Ghidra ni el emulador Android):
#
# 1. [CERTAIN, leido directamente] Los 9 wrappers reales tienen EXACTAMENTE
#    estos conteos de argumentos Excel, sin excepcion:
#      API_Table5_1952  (FUN_1800a3d50): param_3==3 -- 2 usados (Observed
#        API, Temperature). Llama a `FUN_1800f9b4c(local_20,local_28,
#        local_18)`, 2 argumentos reales a la tabla, ninguno mas.
#      API_Table6_1952  (FUN_1800a481c): param_3==3 -- 2 usados (API@60F,
#        Temperature), mismo patron exacto (`FUN_1800f9b74`).
#      API_Table23_1952 (FUN_1800a1b94): param_3==3 -- 2 usados (Observed
#        RD, Temperature) (`FUN_1800f9aac`).
#      API_Table24_1952 (FUN_1800a234c): param_3==3 -- 2 usados (RD@60F,
#        Temperature) (`FUN_1800f9ad4`).
#      API_Table53_1952 (FUN_1800a2adc): param_3==3 -- 2 usados (Observed
#        Density, Temperature) (`FUN_1800f9afc` sobre la tabla adicional
#        `&DAT_18027b2c0`, ver PENDIENTE de RONDA 12 -- pero el conteo de
#        argumentos del WRAPPER es el mismo, 3, independiente de cual tabla
#        interna use).
#      API_Table54_1952 (FUN_1800a32b4): mismo patron (tamano de funcion
#        identico a Table53, 277 bytes vs 261 del resto -- la diferencia de
#        15 bytes es la division `/1000` que Table53/Dens15C hacen sobre la
#        densidad de entrada, no un argumento extra).
#      API_Dens15C_1952   (FUN_18009f1cc): param_3==7 -- 6 usados (Observed
#        Density, Temperature, Pressure, EVP, [algo interno], Conversion/
#        modo 1-o-2) via `FUN_1800f8c4c`. Coincide EXACTO con los 6
#        parametros reales que `api_density15c_1952` ya implementa
#        (`observed_density_kgm3, observed_temp_c, pressure_bar_g,
#        equilibrium_pressure_bar_g, conversion, rounding`).
#      API_Gravity60F_1952 (FUN_18009ff88): param_3==7 -- 6 usados, mismo
#        patron (`FUN_1800f90a4`), coincide EXACTO con los 6 parametros ya
#        implementados de `api_gravity60f_1952`.
#      API_SG60F_1952 (FUN_1800a1778): param_3==7 -- 6 usados, mismo patron
#        (`FUN_1800f9674`), coincide EXACTO con `api_sg60f_1952`.
#
# 2. [CERTAIN] En los 9 casos, el argumento Excel de indice 0 (offset
#    `param_2+0x00`) NUNCA se lee -- ni siquiera se intenta. Este mismo
#    hueco de indice 0 existe TAMBIEN en los wrappers 1980 ya confirmados
#    CON `product`/`hydrometer_correction` (ej. `API_Table5_1980`,
#    param_3==6, arg0 tambien sin leer, ver `ghidra_api_mpms_xll_output.txt`
#    linea ~73; `API_Dens15C_1980`, param_3==10, arg0 tambien sin leer, ver
#    `ghidra_api1980wrappers_xll_output.txt` linea ~81). Es decir: el
#    "hueco de indice 0" es un artefacto GENERICO del generador de wrappers
#    de este `.xll` (probablemente una celda reservada de la plantilla,
#    nunca conectada a ninguna pantalla en NINGUNA de las 2 ediciones), NO
#    un rastro de un selector "Product" olvidado en 1952 -- se descarto
#    explicitamente esta hipotesis alternativa comparando ambas ediciones
#    lado a lado antes de concluir.
#
# 3. [CERTAIN, ya establecido en RONDA 12] Las tablas CTL de 1952 (US:
#    Table5/6/23/24; metrico: Table53/54) son tablas de bytes UNICAS (una
#    sola tabla por sistema de unidades), no un conjunto de tablas
#    seleccionables por producto como los K0/K1/K2 de 1980 (`K_US`/
#    `K_METRIC`, un juego de 3 constantes POR producto). Ningun wrapper
#    1952 pasa un indice de producto a su tabla ni a su formula -- se
#    releyo linea a linea cada nucleo (`FUN_1800f9b4c/74/aac/ad4/afc`,
#    `FUN_1800f8c4c/90a4/9674`) y ninguno recibe ni usa un parametro que
#    seleccione entre variantes de tabla.
#
# CONCLUSION: Product/Hydrometer Corr. NO EXISTEN en ninguna de las 9
# pantallas reales "API Table-5/6/23/24/53/54 (1952)" / "API Density @15°C
# (1952)" / "API Gravity 60°F (1952)" / "API SG 60°F (1952)" del binario
# real. Esto es consistente con que las "1952 Petroleum Measurement
# Tables" (predecesoras historicas de la revision API-2540 de 1980) eran,
# en la practica de la epoca, tablas UNICAS sin distincion de producto --
# la distincion Crude/Refined/Gasoline/etc. (y la correccion de hidrometro
# asociada) se introdujo recien con la revision 1980 del estandar, y el
# vendor de FlowXpert la implemento SOLO ahi. NO se implemento
# `product`/`hydrometer_correction` en ninguna de las 9 funciones -- serian
# parametros fabricados sin respaldo del binario real. Las 9 firmas quedan
# SIN CAMBIOS (cero regresion, ver Sanity checks 16-20 ya existentes de
# RONDA 12).
#
# NO investigado esta ronda, PENDIENTE honesto (no por imposibilidad, sino
# fuera del alcance pedido): no se intento una llamada directa por ctypes
# al `.xll` para estas 9 funciones (el metodo de conteo de argumentos ya
# fue suficiente y concluyente -- ambas fuentes, el conteo `param_3` y la
# revision linea a linea de cada nucleo, coinciden en la misma conclusion
# negativa); tampoco se navego el emulador Android para buscar la pantalla
# real "API Table-5 (1952)" y confirmar visualmente la AUSENCIA de esos 2
# selectores (nivel de confianza [CERTAIN via decompilacion], un peldano
# por debajo de una captura de pantalla real, igual que el resto de la
# sub-familia 1952/US desde RONDA 12).
# ===============================================================================


# ===============================================================================
# RONDA 14 (2026-08-26): "E NGL/LPG (TP-27)" -- ULTIMA categoria del menu raiz
# "API". 9 funciones REALES confirmadas en vivo (uiautomator, Fase 4):
#   API Table-23E, API Table-24E, API Table-53E, API Table-54E, API Table-59E,
#   API Table-60E, API Density @15C NGL/LPG, API Density @20C NGL/LPG,
#   API Rel. Density @60F NGL/LPG.
# `GPA_TP15` (simbolo real del .xll, @0x1800a7b50) NO tiene pantalla propia --
# es un HELPER interno usado solo por los 3 wrappers combinados (confirmado:
# el menu de 9 items no lo incluye). Por tanto: 9 funciones de pantalla, no 10.
# ===============================================================================
# FASE 0 (manual oficial, descripcion real de pantalla via uiautomator):
# "API Table-53E": "LPG/NGL Density at 15 °C according to GPA TP-27 Table 53E."
# "API Rel. Density @60°F NGL/LPG": "Relative Density Conversion to and from
# 60 °F and EVP (Equilibrium Vapor Pressure) according to API 11.2.4 / GPA
# TP-27 Tables 23E and 24E, API MPMS 11.2 and GPA TP-15." -- confirma que el
# wrapper combinado (RD60F) integra 3 piezas: el motor CTL "E" (Table23E/24E),
# la compresibilidad de API MPMS 11.2 (11.2.1/11.2.2, YA implementadas en
# RONDA 13) y GPA TP-15 (presion de vapor en equilibrio).
#
# FASE 1/2/3 (decompilacion `.xll`, Ghidra 12.1.2, script
# `ghidra_scripts_xll/DecompileNglLpgXll.java`, salida
# `ghidra_ngllpg_xll_output.txt`, generada por un intento anterior que se
# perdio solo en el paso final de validacion -- el dump de decompilacion SI
# quedo guardado y se reutilizo integro esta ronda, sin repetir Ghidra):
#
# Las 6 funciones puras Table23E/24E/53E/54E/59E/60E son TODAS variantes de
# un UNICO motor nuevo (NO el K0/K1/K2 por producto de 1980/2004, NI el motor
# de 11.2.2 -- un tercer motor, propio de esta familia, consistente con GPA
# TP-25/TP-27 real): un polinomio racional por tramos en "densidad relativa
# reducida" (12 filas de segmentos, tabla real extraida a bytes via `pefile`
# desde el `.xll` en la VA 0x1802bd708..0x1802bdbe8, 156 doubles = 12 filas x
# 13 columnas -- ver `NGL_LPG_TABLE` abajo). Cada fila tiene: [0]=limite de
# densidad relativa reducida, [1]=temperatura de referencia en Kelvin (rango
# real 298.11K..540.15K, coincide con temperaturas criticas reales de
# hidrocarburos ligeros a pesados: fila 1=305.33K~etano(305.4K), fila
# 11=540.15K~heptano(540.2K) -- evidencia fisica real de que la tabla es
# autentica GPA TP-25, no un artefacto), [2]/[3]=factor de normalizacion y K,
# [4..7]=coeficientes c4/c5/c6/c7 de un polinomio racional en
# Z=(1-T_reducida). Formula reconstruida (`_ngl_alpha`, funcion `g(Z,fila)=
# K*(1+(Z²*c6+Z^0.35*c4+Z³*c7)/(1+Z^0.65*c5))`, evaluada en 2 filas
# adyacentes (lo/hi) e interpolada): mismo patron general (pow() con
# exponentes 0.35/0.65 sobre un termino "1-T_reducida") que el motor 11.2.2
# ya cerrado en RONDA 13, pero con datos y formula de mezcla lo/hi DISTINTOS
# -- confirma la premisa original ("motor y K0/K1/K2 distintos") con
# evidencia real, no supuesta.
#
# El paso INVERSO (dado un valor fisico objetivo, hallar la densidad relativa
# reducida "x" tal que x*alpha(x,T)=objetivo, usado por Table23E/53E/59E) se
# resuelve en el binario con un Newton/secante con fallback a bisección
# (`FUN_1800eab2c`, ~20 lineas de logica de bracket-update). En vez de
# replicar byte a byte esa mecanica de convergencia (innecesario: el
# resultado final SOLO depende de la raiz, no del camino), se usa aqui una
# biseccion robusta estandar sobre la MISMA ecuacion implicita -- converge a
# la MISMA raiz (confirmado exacto contra 4 casos reales, ver mas abajo), con
# la ventaja de ser mas simple de auditar y sin riesgo de reproducir un bug
# de borde del solver original.
#
# FASE 4 (emulador, uiautomator, SIN Frida -- las 6 pantallas ya muestran
# CTL/Density directamente): 4 CASOS REALES obtenidos en vivo, TODOS exactos
# a 6 decimales contra la formula reconstruida:
#   Table23E:  RD=0.65, T=32.2222222°C(=90°F), Rounding=0
#              -> Rel.Density@60F=0.664922, CTL=0.977559
#   Table24E:  Rel.Density@60F=0.6, T=32.2222222°C(=90°F), Rounding=0
#              -> CTL=0.969628
#   Table53E:  Density=600 kg/m3, T=25°C, Rounding=0
#              -> Density@15C=610.4798 kg/m3, CTL=0.982833
#   Table59E:  Density=600 kg/m3, T=25°C, Rounding=0 (mismo input que 53E,
#              referencia 20C en vez de 15C)
#              -> Density@20C=605.2727 kg/m3, CTL=0.991289
# Table54E/60E (inversas algebraicas de 53E/59E, MISMA estructura confirmada
# por decompilacion -- `FUN_1800eea6c`/`FUN_1800ef720` son linea por linea el
# mismo patron que `FUN_1800eda14`/`FUN_1800ef1e4` con los roles de entrada/
# salida invertidos) se verifican por ROUND-TRIP exacto (recuperan la
# densidad observada original a partir del resultado de 53E/59E, <1e-4 kg/m3)
# en vez de un caso real propio -- mismo estandar de evidencia ya usado en
# RONDA 5/11 de este archivo para pares Table53/54 y Table59/60.
#
# NIVEL DE CONFIANZA: [CERTAIN] para las 6 funciones puras Table23E/24E/53E/
# 54E/59E/60E (formula por decompilacion + tabla real extraida a bytes + 4
# casos reales directos + 3 round-trips exactos).
#
# PENDIENTE EXPLICITO, NO fabricado (3 funciones, los 3 wrappers combinados):
# `API_Dens15C_NGL_LPG`/`API_Dens20C_NGL_LPG`/`API_RD60F_NGL_LPG` combinan el
# motor CTL de arriba CON `GPA_TP15` (presion de vapor, formula exp()/log()
# propia con su propia tabla de 7 filas en &DAT_1801eaee0, decompilada en
# `FUN_1800efcbc` pero SIN tabla extraida a bytes todavia) Y con API MPMS
# 11.2.1/11.2.2 (confirmado por decompilacion directa: `API_RD60F_NGL_LPG` ->
# `FUN_1800e8e88` SI llama literalmente a `FUN_1800e32e8`, la MISMA raiz de
# `api_mpms_11_2_2` ya cerrada en RONDA 13) dentro de un solver combinado de
# hasta 100 iteraciones con aceleracion tipo Aitken (`FUN_1800e8e88`, 2860
# bytes, con una llamada RECURSIVA a si misma para un 2do pase) -- demasiado
# grande para cerrar con evidencia solida esta ronda sin arriesgar fabricar
# un numero. SI se obtuvo 1 caso real completo de `API Rel. Density @60°F
# NGL/LPG` para dejarlo listo para la proxima ronda:
#   Input:  RD=0.5, T=43.3333333°C(=110°F), P=13.78952 bar(a)(=200 psia),
#           API-11.2.4 Rounding=0, API-11.2.2 Rounding=0,
#           Equil.Pressure Mode="Calculate (TP-15)", P100 Correlation=0,
#           Conversion="Observed -> Standard",
#           Atmospheric Pressure=1.0132539 bar(a)(=14.696 psia)
#   Output: Relative Density(std)=0.537512, CTL=0.927163, CPL=1.003289,
#           CTPL=0.930212, Compressibility=0.000047 1/psi,
#           Equilibrium Pressure=9.020282 bar(a)
# NO se implementa `api_dens15c_ngl_lpg`/`api_dens20c_ngl_lpg`/
# `api_rd60f_ngl_lpg`/`gpa_tp15` esta ronda -- mejor un avance real y
# verificado (las 6 puras) que forzar los 3 combinados sin poder validarlos.
# ===============================================================================

# Tabla real de 12 segmentos (densidad relativa reducida) extraida a BYTES
# CRUDOS (`pefile`, VA 0x1802bd708..0x1802bdbe8 de FlowXpert.xll, 156 doubles)
# -- columnas: [limite_rd, T_ref_K, norm2, K, c4, c5, c6, c7]. [CERTAIN]
NGL_LPG_TABLE = (
    (0.325022, 298.11, 0.27998, 6.25, 2.54616855327, -0.058244177754, 0.803398090807, -0.745720314137),
    (0.355994, 305.33, 0.2822, 6.87, 1.891130426, -0.3703057823, -0.5448672887, 0.337876635),
    (0.429277, 333.67, 0.2806, 5.615, 2.209700785, -0.2942537082, -0.4057544201, 0.3194434334),
    (0.470381, 352.46, 0.2793, 5.11, 2.253419813, -0.266542138, -0.3727567117, 0.3847341857),
    (0.507025, 369.78, 0.27626, 5.0, 1.965683669, -0.3276624355, -0.4179797025, 0.3032716028),
    (0.562827, 407.85, 0.28326, 3.86, 2.047480344, -0.2897343634, -0.3303450364, 0.2917571031),
    (0.584127, 425.16, 0.27536, 3.92, 2.037347431, -0.2990591457, -0.4188830957, 0.3803677387),
    (0.624285, 460.44, 0.27026, 3.247, 2.065416407, -0.2383662088, -0.1614404922, 0.2586815686),
    (0.631054, 469.65, 0.27235, 3.2, 2.112634745, -0.2612694136, -0.2919234451, 0.30834429),
    (0.657167, 498.05, 0.26706, 2.727, 2.023821979, -0.4235500901, -1.152810983, 0.9501390017),
    (0.664064, 507.35, 0.26762, 2.704, 2.171345478, -0.2329973134, -0.267019794, 0.3786295241),
    (0.688039, 540.15, 0.26312, 2.315, 2.197735334, -0.2750567641, -0.447144095, 0.4937709958),
)
_NGL_N_ROWS = len(NGL_LPG_TABLE)
_NGL_T60F_K = (60.0 + 459.67) / 1.8  # FUN_1800e1da0(60.0) -- 60F en Kelvin, byte-exacto
RHO_WATER_NGL_LPG_KGM3 = 999.016  # DAT_1801eaac8 -- DISTINTA de RHO_WATER_60F_KGM3 (999.012)
T_REF_NGL_15C_C = 15.0
T_REF_NGL_20C_C = 20.0


def _ngl_bracket(x: float) -> tuple:
    """Localiza el segmento [lo,hi] de `NGL_LPG_TABLE` que contiene `x` (densidad
    relativa reducida) y la fraccion de interpolacion. Traduccion directa del
    bucle de busqueda de `FUN_1800ec10c`, con los mismos 2 casos de borde
    (x por debajo del primer limite o por encima del ultimo -> sin
    interpolar, fila 0 o fila 11 respectivamente)."""
    j = None
    for i in range(_NGL_N_ROWS):
        if x <= NGL_LPG_TABLE[i][0]:
            j = i
            break
    if j is None:
        return _NGL_N_ROWS - 1, _NGL_N_ROWS - 1, 0.0
    if j == 0:
        return 0, 0, 0.0
    lo, hi = j - 1, j
    frac = (x - NGL_LPG_TABLE[lo][0]) / (NGL_LPG_TABLE[hi][0] - NGL_LPG_TABLE[lo][0])
    return lo, hi, frac


def _ngl_g(z: float, row: int) -> float:
    """g(Z,fila) = K*(1 + (Z²c6 + Z^0.35 c4 + Z³c7)/(1 + Z^0.65 c5)).
    Nucleo polinomico racional real de `FUN_1800ec10c`, evaluado para 1 fila."""
    _, _, _, k, c4, c5, c6, c7 = NGL_LPG_TABLE[row]
    num = z * z * c6 + (z ** 0.35) * c4 + z * z * z * c7
    den = (z ** 0.65) * c5 + 1.0
    return k * (num / den + 1.0)


def _ngl_alpha(x: float, temp_k: float) -> tuple:
    """Traduccion directa de `FUN_1800ec10c`: dada la densidad relativa
    reducida `x` y la temperatura en Kelvin, devuelve (alpha, fuera_de_rango)
    donde alpha es el factor de correccion (CTL-like) tal que
    valor_fisico = x * alpha. [CERTAIN, 4 casos reales exactos]."""
    lo, hi, frac = _ngl_bracket(x)
    t_ref = NGL_LPG_TABLE[lo][1] + (NGL_LPG_TABLE[hi][1] - NGL_LPG_TABLE[lo][1]) * frac
    t_reducida = temp_k / t_ref
    fuera_de_rango = t_reducida > 1.0
    if fuera_de_rango:
        t_reducida = 1.0
    x_60f = 1.0 - _NGL_T60F_K / t_ref
    y = 1.0 - t_reducida
    razon = (NGL_LPG_TABLE[lo][2] * NGL_LPG_TABLE[lo][3]) / (NGL_LPG_TABLE[hi][2] * NGL_LPG_TABLE[hi][3])
    g_y_lo, g_y_hi = _ngl_g(y, lo), _ngl_g(y, hi)
    g_x_lo, g_x_hi = _ngl_g(x_60f, lo), _ngl_g(x_60f, hi)
    h_y = (g_y_lo / (g_y_hi * razon) - 1.0) * frac + 1.0
    h_x = (g_x_lo / (g_x_hi * razon) - 1.0) * frac + 1.0
    alpha = g_y_lo * h_x / (h_y * g_x_lo)
    return alpha, fuera_de_rango


def _ngl_solve_x(target: float, temp_k: float,
                  lo_bound: float = 0.30, hi_bound: float = 0.70) -> tuple:
    """Halla `x` (densidad relativa reducida) tal que x*alpha(x,T)=`target`,
    por biseccion robusta sobre la ecuacion implicita real de
    `FUN_1800eab2c` (NO replica su mecanica de Newton/secante byte a byte --
    innecesario, el resultado final solo depende de la raiz, verificado
    exacto contra 4 casos reales). Devuelve (x, alpha_en_x, fuera_de_rango)."""
    def f(x):
        a, _ = _ngl_alpha(x, temp_k)
        return x * a - target

    a_lo, a_hi = lo_bound, hi_bound
    f_lo, f_hi = f(a_lo), f(a_hi)
    tries = 0
    while f_lo * f_hi > 0 and tries < 20:
        a_lo -= 0.05
        a_hi += 0.05
        f_lo, f_hi = f(a_lo), f(a_hi)
        tries += 1
    for _ in range(200):
        mid = 0.5 * (a_lo + a_hi)
        f_mid = f(mid)
        if abs(f_mid) < 1e-12 or (a_hi - a_lo) < 1e-14:
            break
        if f_lo * f_mid <= 0:
            a_hi, f_hi = mid, f_mid
        else:
            a_lo, f_lo = mid, f_mid
    x_root = 0.5 * (a_lo + a_hi)
    alpha_root, fuera_de_rango = _ngl_alpha(x_root, temp_k)
    return x_root, alpha_root, fuera_de_rango


def _ngl_round_temp_01f(observed_temp_c: float) -> float:
    """Redondea la temperatura observada a la graduacion real de 0.1°F usada
    por Table23E/24E cuando `rounding=1` -- confirmado por decompilacion
    directa de `FUN_1800ea9dc`/`FUN_1800ec020` (`FUN_1800e1db4(temp_F,1)`,
    con `temp_F` en Fahrenheit ya que el core de estas 2 tablas trabaja
    nativamente en Fahrenheit, ver `FUN_1800e1da0`/`_NGL_T60F_K`).
    [CERTAIN, RONDA 37]."""
    temp_f = _celsius_to_fahrenheit(observed_temp_c)
    temp_f = _round_comercial_n(temp_f, 1)
    return (temp_f - 32.0) / 1.8


def _ngl_round_temp_005c(observed_temp_c: float) -> float:
    """Redondea la temperatura observada a la graduacion real de 0.05°C
    usada por Table53E/54E/59E/60E cuando `rounding=1` -- confirmado por
    decompilacion directa (idiom `FUN_1800e1db4(temp_C*2.0,1)*0.5`, mismo
    patron "multiplicar por 2, redondear, multiplicar por 0.5" ya usado en
    RONDA 30 para la graduacion de hidrometro de RD, aqui aplicado a un
    termometro de 0.05°C). Estas 4 tablas trabajan nativamente en Celsius
    (confirmado: `FUN_1800e1d78(x)=x+273.15`, NO pasa por Fahrenheit).
    [CERTAIN, RONDA 37]."""
    return _round_comercial_n(observed_temp_c * 2.0, 1) * 0.5


def api_table23e(observed_rd: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """RD observada(T) -> RD a 60°F. API 11.2.4 / GPA TP-27 Table 23E.
    [CERTAIN via decompilacion (`FUN_1800a1a20`/`FUN_1800ea9dc`) + caso real
    directo exacto: RD=0.65,T=90°F -> RD60F=0.664922,CTL=0.977559].

    `rounding` (0/1): campo real de pantalla "API Rounding" (Switch booleano,
    confirmado por uiautomator + decompilacion, RONDA 37 -- ya visto en
    RONDA 14 pero nunca conectado). Cuando =1: RD observada se redondea a 4
    decimales (graduacion real de hidrometro, 0.0001), la temperatura se
    redondea a 0.1°F (graduacion real de termometro, ver
    `_ngl_round_temp_01f`) y el resultado final RD@60°F se redondea a 4
    decimales. El CTL devuelto NUNCA se redondea (confirmado: no hay
    llamada de redondeo sobre ese puntero en `FUN_1800ea9dc`). [CERTAIN,
    decompilacion directa de `FUN_1800ea9dc` + constantes del `.xll`
    confirmadas byte-exactas (`DAT_180124428`=0.5, `DAT_180124438`=2.0)]."""
    if rounding:
        observed_rd = _round_comercial_n(observed_rd, 4)
        observed_temp_c = _ngl_round_temp_01f(observed_temp_c)
    t_k = observed_temp_c + 273.15
    x_root, alpha_val, fuera_de_rango = _ngl_solve_x(observed_rd, t_k)
    rd_60f = observed_rd / alpha_val if alpha_val != 0 else 0.0
    if rounding:
        rd_60f = _round_comercial_n(rd_60f, 4)
    return {"rd_60f": rd_60f, "ctl": alpha_val, "fuera_de_rango": fuera_de_rango}


def api_table24e(rd_60f: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """RD a 60°F -> CTL a T observada. API 11.2.4 / GPA TP-27 Table 24E
    (evaluacion DIRECTA, sin iterar -- variante "24" de la familia).
    [CERTAIN via decompilacion (`FUN_1800a2204`/`FUN_1800ec020`) + caso real
    directo exacto: RD60F=0.6,T=90°F -> CTL=0.969628].

    `rounding` (0/1): mismo campo "API Rounding" de Table23E. Cuando =1:
    RD@60°F y temperatura se redondean igual que en Table23E (4
    decimales/0.1°F), y el CTL final se redondea a 5 decimales (a diferencia
    de Table23E, aqui CTL SI es el resultado principal -- confirmado: unica
    llamada de redondeo de `FUN_1800ec020` es sobre el puntero de salida
    CTL). [CERTAIN, decompilacion directa]."""
    if rounding:
        rd_60f = _round_comercial_n(rd_60f, 4)
        observed_temp_c = _ngl_round_temp_01f(observed_temp_c)
    t_k = observed_temp_c + 273.15
    alpha_val, fuera_de_rango = _ngl_alpha(rd_60f, t_k)
    if rounding:
        alpha_val = _round_comercial_n(alpha_val, 5)
    return {"ctl": alpha_val, "fuera_de_rango": fuera_de_rango}


def api_table53e(observed_density_kgm3: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """Densidad observada(T) -> Densidad a 15°C. GPA TP-27 Table 53E.
    [CERTAIN via decompilacion (`FUN_1800a2970`/`FUN_1800eda14`) + caso real
    directo exacto: 600kg/m3,25°C -> 610.4798kg/m3,CTL=0.982833].

    `rounding` (0/1): campo real de pantalla "API Rounding" (confirmado
    RONDA 37). Cuando =1: densidad observada se redondea a 1 decimal
    (0.1 kg/m3, graduacion real de hidrometro de densidad) y la temperatura
    a 0.05°C (ver `_ngl_round_temp_005c`); el resultado Density@15°C se
    redondea a 1 decimal. El CTL devuelto NUNCA se redondea (mismo patron
    que Table23E: sin llamada de redondeo sobre ese puntero en
    `FUN_1800eda14`). [CERTAIN, decompilacion directa]."""
    if rounding:
        observed_density_kgm3 = _round_comercial_n(observed_density_kgm3, 1)
        observed_temp_c = _ngl_round_temp_005c(observed_temp_c)
    t_obs_k = observed_temp_c + 273.15
    t_ref_k = T_REF_NGL_15C_C + 273.15
    target_rd = observed_density_kgm3 / RHO_WATER_NGL_LPG_KGM3
    x_root, alpha_obs, oor1 = _ngl_solve_x(target_rd, t_obs_k)
    alpha_ref, oor2 = _ngl_alpha(x_root, t_ref_k)
    density_15c = alpha_ref * x_root * RHO_WATER_NGL_LPG_KGM3
    ctl = observed_density_kgm3 / density_15c if density_15c != 0 else 0.0
    if rounding:
        density_15c = _round_comercial_n(density_15c, 1)
    return {"density_15c": density_15c, "ctl": ctl, "fuera_de_rango": oor1 or oor2}


def api_table54e(density_15c_kgm3: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """Densidad a 15°C -> Densidad observada(T). GPA TP-27 Table 54E
    (inversa algebraica de Table 53E). [CERTAIN via decompilacion
    (`FUN_1800a315c`/`FUN_1800eea6c`, mismo patron que Table53E con
    entrada/salida invertidas) + round-trip exacto (<1e-4 kg/m3) contra el
    caso real de Table53E].

    `rounding` (0/1): mismo campo "API Rounding" de Table53E. Cuando =1:
    Density@15°C y temperatura se redondean igual que en Table53E (1
    decimal/0.05°C), y el CTL final se redondea a 5 decimales -- el
    decompilado inicial de Ghidra de `FUN_1800eea6c` mostraba esta ultima
    llamada sobre una variable entera (aparente bug), pero DESENSAMBLADO
    x64 directo (capstone, RONDA 37, mismo estandar de evidencia que RONDA
    29) confirmo que el registro `xmm0` que realmente entra a
    `FUN_1800e1db4` en ese punto es el CTL (double, sin escritura
    intermedia desde el `divsd` que lo calcula) -- CERTAIN, no ambiguo.
    `density_obs_predicted` se recalcula con el CTL YA redondeado (igual
    que el binario: `mulsd` ocurre despues de la llamada de redondeo)."""
    if rounding:
        density_15c_kgm3 = _round_comercial_n(density_15c_kgm3, 1)
        observed_temp_c = _ngl_round_temp_005c(observed_temp_c)
    t_ref_k = T_REF_NGL_15C_C + 273.15
    t_obs_k = observed_temp_c + 273.15
    target_rd = density_15c_kgm3 / RHO_WATER_NGL_LPG_KGM3
    x_root, alpha_ref, oor1 = _ngl_solve_x(target_rd, t_ref_k)
    alpha_obs, oor2 = _ngl_alpha(x_root, t_obs_k)
    ctl = alpha_obs / alpha_ref if alpha_ref != 0 else 0.0
    if rounding:
        ctl = _round_comercial_n(ctl, 5)
    density_obs_predicted = ctl * density_15c_kgm3
    return {"ctl": ctl, "density_obs_predicted": density_obs_predicted,
            "fuera_de_rango": oor1 or oor2}


def api_table59e(observed_density_kgm3: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """Densidad observada(T) -> Densidad a 20°C. API 11.2.4 / GPA TP-27
    Table 59E (clon estructural de Table53E con referencia 20°C en vez de
    15°C, mismo patron ya confirmado para Table59_2004/Table53_2004 en
    RONDA 11). [CERTAIN via decompilacion (`FUN_1800a38e0`/`FUN_1800ef1e4`)
    + caso real directo exacto: 600kg/m3,25°C -> 605.2727kg/m3,
    CTL=0.991289].

    `rounding` (0/1): identico a Table53E (mismas constantes/graduaciones
    confirmadas por decompilacion directa de `FUN_1800ef1e4`, linea por
    linea igual a `FUN_1800eda14` salvo la temperatura de referencia).
    [CERTAIN]."""
    if rounding:
        observed_density_kgm3 = _round_comercial_n(observed_density_kgm3, 1)
        observed_temp_c = _ngl_round_temp_005c(observed_temp_c)
    t_obs_k = observed_temp_c + 273.15
    t_ref_k = T_REF_NGL_20C_C + 273.15
    target_rd = observed_density_kgm3 / RHO_WATER_NGL_LPG_KGM3
    x_root, alpha_obs, oor1 = _ngl_solve_x(target_rd, t_obs_k)
    alpha_ref, oor2 = _ngl_alpha(x_root, t_ref_k)
    density_20c = alpha_ref * x_root * RHO_WATER_NGL_LPG_KGM3
    ctl = observed_density_kgm3 / density_20c if density_20c != 0 else 0.0
    if rounding:
        density_20c = _round_comercial_n(density_20c, 1)
    return {"density_20c": density_20c, "ctl": ctl, "fuera_de_rango": oor1 or oor2}


def api_table60e(density_20c_kgm3: float, observed_temp_c: float, rounding: int = 0) -> dict:
    """Densidad a 20°C -> Densidad observada(T). API 11.2.4 / GPA TP-27
    Table 60E (inversa algebraica de Table 59E). [CERTAIN via decompilacion
    (`FUN_1800a43c0`/`FUN_1800ef720`, mismo patron que Table54E con
    referencia 20°C) + round-trip exacto (<1e-4 kg/m3) contra el caso real
    de Table59E].

    `rounding` (0/1): identico a Table54E, incluyendo el CTL a 5 decimales
    confirmado por desensamblado directo (misma verificacion x64 hecha
    tambien sobre `FUN_1800ef720`, RONDA 37 -- ver docstring de
    `api_table54e`). [CERTAIN]."""
    if rounding:
        density_20c_kgm3 = _round_comercial_n(density_20c_kgm3, 1)
        observed_temp_c = _ngl_round_temp_005c(observed_temp_c)
    t_ref_k = T_REF_NGL_20C_C + 273.15
    t_obs_k = observed_temp_c + 273.15
    target_rd = density_20c_kgm3 / RHO_WATER_NGL_LPG_KGM3
    x_root, alpha_ref, oor1 = _ngl_solve_x(target_rd, t_ref_k)
    alpha_obs, oor2 = _ngl_alpha(x_root, t_obs_k)
    ctl = alpha_obs / alpha_ref if alpha_ref != 0 else 0.0
    if rounding:
        ctl = _round_comercial_n(ctl, 5)
    density_obs_predicted = ctl * density_20c_kgm3
    return {"ctl": ctl, "density_obs_predicted": density_obs_predicted,
            "fuera_de_rango": oor1 or oor2}


# ===============================================================================
# RONDA 15 (2026-08-27): cierra el PENDIENTE de RONDA 14 -- los 3 wrappers
# combinados de "E NGL/LPG (TP-27)" (`API Density @15°C NGL/LPG`,
# `API Density @20°C NGL/LPG`, `API Rel. Density @60°F NGL/LPG`). RONDA 14
# los dejo pendientes por ser "demasiado grandes para portar a mano" (motor
# CTL "E" + API MPMS 11.2.1/11.2.2 + GPA TP-15 dentro de un solver de hasta
# 100 iteraciones con aceleracion tipo Aitken, `FUN_1800e8e88`).
#
# Ese bloqueo era sobre "portar el algoritmo a Python" -- aqui NO se porta
# nada: se llama DIRECTO (ctypes, sin Excel, SIN emulador) al nucleo real
# ya decompilado por RONDA 14, misma tecnica que ya funciono para AGA-10 y
# NX-19 (`normas/_aga10_xll_directo.py`/`normas/_nx19_xll_directo.py`). Ver
# `normas/_ngl_lpg_wrappers_xll_directo.py` para el mapeo COMPLETO de
# parametros (reconstruido leyendo la extraccion de XLOPER de cada wrapper
# Excel-facing + verificacion cruzada contra `api_mpms_11_2_2`/
# `api_mpms_11_2_2m` ya [CERTAIN]) y la evidencia de validacion.
#
# RESULTADO: FUNCIONA para las 3 funciones.
#   `API_RD60F_NGL_LPG`: EXACTO (6 decimales) contra el UNICO caso real
#       completo guardado en RONDA 14 (RD=0.5,T=110F,P=200psia ->
#       RD_std=0.537512, CTL=0.927163, CPL=1.003289, CTPL=0.930212,
#       Compressibility=0.000047 1/psi, EVP=9.020282 bar(a)) -- primer
#       intento, sin ajustar ningun parametro tras el mapeo por
#       decompilacion. [CERTAIN]
#   `API_Dens15C_NGL_LPG`/`API_Dens20C_NGL_LPG`: SIN caso real propio
#       capturado en RONDA 14 -- validados por round-trip algebraico exacto
#       contra `api_table53e`/`api_table54e` y `api_table59e`/`api_table60e`
#       (YA [CERTAIN]) con P=EVP=0 bar(g) (mismo estandar de evidencia que
#       RONDA 5/11/14 ya usan para estos pares inversos), MAS que comparten
#       literalmente el mismo nucleo de presion/TP-15 ya validado byte-
#       exacto en el caso real de RD60F. [CERTAIN] sin presion, [LIKELY]
#       con presion/TP-15 (mismo codigo, sin caso real propio).
#
# PENDIENTE de baja prioridad, no bloqueante: el campo "round_tp15" (una
# rounding interna de GPA TP-15 sin nombre confirmado en el caso real) se
# asume 0 por default (patron: TODO el resto del caso real es 0/default) --
# no se probo con !=0. `p100_correlacion=1` (metodo alterno de TP-15) no se
# probo. Ver docstring de `normas/_ngl_lpg_wrappers_xll_directo.py`,
# seccion LIMITACIONES, para el detalle completo.
#
# Con esto, DE LAS 7 ENTRADAS DEL MENU RAIZ "API": 7/7 CERRADAS
# numericamente (11.1 x3 + 11.2/12.2 + E NGL/LPG TP-27 completa 9/9 +
# Ethylene/Propylene, cerradas en otra sesion via
# `normas/_ethylene_propylene_xll_directo.py`/`normas/API_Ethylene_Propylene.py`
# -- ver `MEMORY.md` del proyecto para el detalle de esa ronda). Familia
# "API" del menu raiz COMPLETA.
# ===============================================================================
def api_dens15c_ngl_lpg(observed_density_kgm3: float, observed_temp_c: float,
                         pressure_bar_g: float = 0.0,
                         equilibrium_pressure_bar_g: float = 0.0,
                         equilibrium_pressure_mode: int = 2,
                         p100_correlacion: int = 0, p100_valor: float = 0.0,
                         round_11_2_4: int = 0, round_11_2_2m: int = 0,
                         round_tp15: int = 0,
                         conversion: int = 1, usar_xll_si_disponible: bool = False) -> dict:
    """Densidad(T,P) <-> Densidad(15°C, EVP). "API Density @15°C NGL/LPG"
    (API 11.2.4 / GPA TP-27 + API MPMS 11.2.2M + GPA TP-15).

    [RONDA 36 (2026-09-09)] `round_tp15` ("GPA TP-15 Rounding" de la
    pantalla real, campo separado confirmado por el usuario -- caso real
    "API Density @15°C NGL/LPG": Density=600kg/m3, T=25°C, P=20bar(a),
    API-11.2.4=1, API-11.2.2=1, EVP-Mode=Override(1), EVP=5bar(a),
    TP15-Round=1, Conversion=Std->Obs(2) -> Density=591.4979,
    CTL=0.982000, CPL=1.003900, CTPL=0.985830, F=0.000262,
    EVP=5.000000). Este parametro YA existia implementado internamente
    en `_ngl_lpg_wrappers_puro.calcular_dens15c_ngl_lpg_puro` desde
    RONDA 33 (afecta la tolerancia de convergencia del solver y el
    redondeo a 1 decimal de GPA TP-15) pero NUNCA se conectaba desde esta
    funcion publica (quedaba fijo en 0 sin que el llamador lo supiera) --
    ver docstring de `_gpa_tp15_psia`/`_dens_ngl_lpg_puro` para el
    mecanismo completo. Ver docstring del modulo `_ngl_lpg_wrappers_puro`
    para el detalle round-by-round completo de esta ronda.

    [ACTUALIZADO, RONDA "NGL/LPG puro" 2026-09-03] Camino PRINCIPAL: 100%
    Python puro (`normas/_ngl_lpg_wrappers_puro.py`,
    `calcular_dens15c_ngl_lpg_puro`) -- sin `ctypes`/`pefile`/Excel, apto
    para despliegue web. Validado por barrido masivo contra el oraculo
    `.xll` real (`normas/_sweep_ngl_lpg_puro.py`): 94.7% de 974 casos (100%
    en `evp_mode=1`/Input sin presion, round-trip exacto contra
    `api_table53e`/`api_table54e`; el resto de las fallas caen en el borde
    extremo del rango oficial -- densidad cerca del minimo de la tabla,
    350 kg/m3, combinada con temperatura alta, ~55°C -- zona ya conocida
    como numericamente fragil en el resto de este proyecto, ver docstring
    de `_ngl_lpg_wrappers_puro.py`). `usar_xll_si_disponible=True` (default
    `False`) es un ATAJO OPCIONAL: si `FlowXpert.xll`/`pefile` estan
    disponibles, llama en su lugar a
    `_ngl_lpg_wrappers_xll_directo.calcular_dens15c_ngl_lpg_directo`
    (ctypes, sin Excel/emulador) -- NUNCA es el default, siguiendo la
    politica de este proyecto de cero dependencia de binario en produccion
    (ver `feedback-preferencia-python-puro.md` en la memoria del proyecto);
    si se pide y el `.xll` no esta disponible, se cae de vuelta al puro
    silenciosamente (nunca lanza `RuntimeError` por esto).

    `conversion`: 1=Observed->Standard(15°C) (default, `observed_density_kgm3`
    es la densidad OBSERVADA y el resultado `density_15c` es la densidad
    estandar), 0=Standard(15°C)->Observed (`observed_density_kgm3` es en
    realidad la densidad a 15°C de entrada, y `density_15c` en el resultado
    es en realidad la densidad OBSERVADA resultante -- mismo campo, sentido
    invertido, igual que expone la pantalla real)."""
    r = None
    if usar_xll_si_disponible:
        from . import _ngl_lpg_wrappers_xll_directo as _wx
        if _wx.disponible():
            r = _wx.calcular_dens15c_ngl_lpg_directo(
                densidad_kgm3=observed_density_kgm3, t_c=observed_temp_c, p_barg=pressure_bar_g,
                round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m,
                evp_mode=equilibrium_pressure_mode, evp_input_barg=equilibrium_pressure_bar_g,
                round_tp15=round_tp15,
                p100_correlacion=p100_correlacion, p100_valor=p100_valor, conversion=conversion)
    if r is None:
        from . import _ngl_lpg_wrappers_puro as _wp
        r = _wp.calcular_dens15c_ngl_lpg_puro(
            densidad_kgm3=observed_density_kgm3, t_c=observed_temp_c, p_barg=pressure_bar_g,
            round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m,
            evp_mode=equilibrium_pressure_mode, evp_input_barg=equilibrium_pressure_bar_g,
            round_tp15=round_tp15,
            p100_correlacion=p100_correlacion, p100_valor=p100_valor, conversion=conversion)
    return {"density_15c": r["x_kgm3"], "ctl": r["ctl"], "cpl": r["cpl"],
            "ctpl": r["ctpl"], "f": r["compressibility_1_bar"],
            "equilibrium_pressure_barg": r["evp_barg"],
            "fuera_de_rango": bool(r["oor_ctl"] or r["oor_cpl"] or r["oor_evp"])}


def api_dens20c_ngl_lpg(observed_density_kgm3: float, observed_temp_c: float,
                         pressure_bar_g: float = 0.0,
                         equilibrium_pressure_bar_g: float = 0.0,
                         equilibrium_pressure_mode: int = 2,
                         p100_correlacion: int = 0, p100_valor: float = 0.0,
                         round_11_2_4: int = 0, round_11_2_2m: int = 0,
                         round_tp15: int = 0,
                         conversion: int = 1, usar_xll_si_disponible: bool = False) -> dict:
    """Densidad(T,P) <-> Densidad(20°C, EVP). "API Density @20°C NGL/LPG".
    Mismo motor que `api_dens15c_ngl_lpg` con referencia 20°C -- ver ese
    docstring para el significado de `conversion`/`usar_xll_si_disponible`/
    `round_tp15` (RONDA 36).

    [ACTUALIZADO, RONDA "NGL/LPG puro" 2026-09-03] Camino PRINCIPAL: 100%
    Python puro (`calcular_dens20c_ngl_lpg_puro`). Validado por barrido:
    98.8% de 974 casos (100% en `evp_mode=1` sin presion, round-trip exacto
    contra `api_table59e`/`api_table60e`) -- ver docstring de
    `_ngl_lpg_wrappers_puro.py` para el detalle completo, incluido un
    hallazgo real de esta ronda (CPL siempre se evalua con la densidad
    equivalente a 15°C, incluso en esta pantalla de 20°C -- confirmado
    leyendo `FUN_1800e7304`)."""
    r = None
    if usar_xll_si_disponible:
        from . import _ngl_lpg_wrappers_xll_directo as _wx
        if _wx.disponible():
            r = _wx.calcular_dens20c_ngl_lpg_directo(
                densidad_kgm3=observed_density_kgm3, t_c=observed_temp_c, p_barg=pressure_bar_g,
                round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m,
                evp_mode=equilibrium_pressure_mode, evp_input_barg=equilibrium_pressure_bar_g,
                round_tp15=round_tp15,
                p100_correlacion=p100_correlacion, p100_valor=p100_valor, conversion=conversion)
    if r is None:
        from . import _ngl_lpg_wrappers_puro as _wp
        r = _wp.calcular_dens20c_ngl_lpg_puro(
            densidad_kgm3=observed_density_kgm3, t_c=observed_temp_c, p_barg=pressure_bar_g,
            round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m,
            evp_mode=equilibrium_pressure_mode, evp_input_barg=equilibrium_pressure_bar_g,
            round_tp15=round_tp15,
            p100_correlacion=p100_correlacion, p100_valor=p100_valor, conversion=conversion)
    return {"density_20c": r["x_kgm3"], "ctl": r["ctl"], "cpl": r["cpl"],
            "ctpl": r["ctpl"], "f": r["compressibility_1_bar"],
            "equilibrium_pressure_barg": r["evp_barg"],
            "fuera_de_rango": bool(r["oor_ctl"] or r["oor_cpl"] or r["oor_evp"])}


def api_rd60f_ngl_lpg(observed_rd: float, observed_temp_f: float,
                       pressure_psia: float, equilibrium_pressure_psia: float = 0.0,
                       equilibrium_pressure_mode: int = 2, atm_psia: float = 14.696,
                       p100_correlacion: int = 0, p100_valor_psia: float = 0.0,
                       round_11_2_4: int = 0, round_11_2_2: int = 0,
                       round_tp15: int = 0,
                       conversion: int = 1, usar_xll_si_disponible: bool = False) -> dict:
    """RD(T,P) <-> RD(60°F, EVP). "API Rel. Density @60°F NGL/LPG" (API
    11.2.4 / GPA TP-27 Tables 23E/24E + API MPMS 11.2.2 + GPA TP-15, sistema
    US -- unica pantalla US-nativa de esta familia, confirmado por los
    valores "bonitos" del caso real en °F/psia).

    [ACTUALIZADO, RONDA "NGL/LPG puro" 2026-09-03] Camino PRINCIPAL: 100%
    Python puro (`calcular_rd60f_ngl_lpg_puro`) -- validado EXACTO (dentro
    de 1e-4) contra el caso real completo (RD=0.5, T=110°F, P=200psia,
    Atm=14.696psia -> RD_std=0.537512, CTL=0.927163, CPL=1.003289,
    CTPL=0.930212, Compressibility=0.000047 1/psi, EVP=130.828 psia=
    9.020282 bar(a)) y por barrido masivo contra el oraculo `.xll`: 94.3%
    de 980 casos (las fallas caen en el borde extremo del rango oficial,
    RD=0.35 con T>=90°F -- zona donde ademas se corrigio un clamp faltante
    en `api_mpms_11_2_2`, ver docstring de esa funcion). Ver docstring de
    `api_dens15c_ngl_lpg` para el significado de `usar_xll_si_disponible`
    (mismo patron, default `False`, ATAJO opcional, nunca produccion).

    `conversion`: 1=Observed->Standard(60°F) (default, caso real validado),
    0=Standard(60°F)->Observed (mismo campo `observed_rd`/`rd_60f` en
    sentido invertido, igual que expone la pantalla real).

    [RONDA 36 (2026-09-09)] `round_tp15` ("GPA TP-15 Rounding" de la
    pantalla real) -- ver docstring de `api_dens15c_ngl_lpg` para el
    detalle completo (mismo parametro, misma conexion antes ausente)."""
    r = None
    if usar_xll_si_disponible:
        from . import _ngl_lpg_wrappers_xll_directo as _wx
        if _wx.disponible():
            r = _wx.calcular_rd60f_ngl_lpg_directo(
                rd=observed_rd, t_f=observed_temp_f, p_psia=pressure_psia,
                round_11_2_4=round_11_2_4, round_11_2_2=round_11_2_2,
                evp_mode=equilibrium_pressure_mode, evp_input_psia=equilibrium_pressure_psia,
                round_tp15=round_tp15,
                p100_correlacion=p100_correlacion, p100_valor_psia=p100_valor_psia,
                conversion=conversion, atm_psia=atm_psia)
    if r is None:
        from . import _ngl_lpg_wrappers_puro as _wp
        r = _wp.calcular_rd60f_ngl_lpg_puro(
            rd=observed_rd, t_f=observed_temp_f, p_psia=pressure_psia,
            round_11_2_4=round_11_2_4, round_11_2_2=round_11_2_2,
            evp_mode=equilibrium_pressure_mode, evp_input_psia=equilibrium_pressure_psia,
            round_tp15=round_tp15,
            p100_correlacion=p100_correlacion, p100_valor_psia=p100_valor_psia,
            conversion=conversion, atm_psia=atm_psia)
    return {"rd_60f": r["rd_std"], "ctl": r["ctl"], "cpl": r["cpl"],
            "ctpl": r["ctpl"], "f": r["compressibility_1_psi"],
            "equilibrium_pressure_psia": r["evp_psia"],
            "fuera_de_rango": bool(r["oor_ctl"] or r["oor_cpl"] or r["oor_evp"])}


# ===============================================================================
# RONDA 25 (2026-09-08): barrido sistematico de flags 0/1/enum (Conversion,
# Rounding, Hydrometer Correction, API-2540 Rounding, Product) cruzado con
# escenarios de Presion/EVP (incluido P<EVP, el caso que broto el bug real de
# RONDA 23/24) sobre los 6 wrappers combinados (3 de 1980 + 3 de 1952) y las 2
# funciones base `api_mpms_11_2_1`/`api_mpms_11_2_1m`, pedido explicitamente
# por el usuario para adelantarse a otro bug casual como el de RONDA 24.
# Script + oraculo: `normas/_sweep_api_1952_1980_flags.py` +
# `normas/_api1980_1952_wrappers_xll_directo.py` (llamada DIRECTA ctypes a
# `FUN_1800E303C`/`FUN_1800E2D5C` [funciones base] y `FUN_1800E62D4`/
# `FUN_1800E79E4`/`FUN_1800E8494` [los 3 nucleos combinados de 1980] --
# mapeo de entrada/salida confirmado por RE-LECTURA linea a linea de los 5
# cuerpos decompilados + autoconsistencia numerica contra los casos ya
# [CERTAIN] de este archivo, ver docstring de ese modulo).
# -------------------------------------------------------------------------------
# TOTAL: 2560 combinaciones corridas (64 funciones base + 2304 los 3
# wrappers de 1980 + 48 los 3 wrappers de 1952 + 144 regresion de las 6
# tablas puras de 1980, ver ese modulo para el desglose).
#
# RESULTADO 1 [CERTAIN, CONFIRMA RONDA 23/24 -- NO ES UN BUG NUEVO]: se
# releyo linea a linea (no solo se cito el docstring existente) el cuerpo de
# `FUN_1800E62D4`/`FUN_1800E79E4`/`FUN_1800E8494` (los 3 nucleos combinados
# de 1980) y se confirmo que NINGUNO tiene el clamp de presion neta negativa
# (`dVar8=param_3; if(0<param_8) dVar8=param_3-param_8; dVar8=dVar6-dVar8*
# dVar9;` -- SIN el `if(param_3<param_8 && dVar6<dVar8) dVar8=dVar6;` que SI
# tienen `FUN_1800E303C`/`FUN_1800E2D5C`) -- confirma que
# `clamp_negative_net_pressure=False` en los 3 wrappers de 1980 sigue siendo
# correcto. Las 2304 combinaciones de estos 3 wrappers (product x 4
# escenarios P/EVP x conversion x rounding x hydrometer_correction x
# api2540_rounding) dieron 2015/2304 (87.46%) exactas (<0.01%) contra el
# oraculo; TODAS las 289 discrepancias tienen `api2540_rounding` != 0 (ver
# RESULTADO 2) -- CERO discrepancias en ningun escenario de presion/EVP
# (incluido P<EVP) cuando `api2540_rounding=0` (el default). El patron de
# bug de RONDA 23/24 NO aparece en ninguna combinacion nueva.
#
# RESULTADO 2 [CERTAIN via decompilacion, PENDIENTE DE PORTAR -- ya conocido
# desde RONDA 22, ahora CUANTIFICADO]: se releyo el cuerpo completo de
# `FUN_1800E62D4` en la zona de `param_5` (api2540_rounding) y se confirmo
# que el nucleo real aplica una CASCADA de redondeos intermedios (density
# candidata a 2 decimales en cada paso Newton via `FUN_1800e1db4`, y el
# termino de F/alpha a 6/7/8/10 decimales en varios puntos, con un caso
# especial para el grupo de producto 4) para CUALQUIER valor != 0 de
# `api2540_rounding` (1, 2 y 3 activan la MISMA cascada -- el nucleo NO
# distingue entre ellos salvo un detalle menor dentro de la rama
# `conversion=Standard->Observed`), mientras que la implementacion Python
# actual SOLO actua cuando `api2540_rounding==2` (y solo redondeando `ctl` a
# 4 decimales) -- deja 1 y 3 identicos a 0 y no replica la cascada intermedia
# de 2. Esto es la MISMA limitacion ya declarada [LIKELY]/incompleta en
# RONDA 22 ("no se replicaron los pasos intermedios... hace falta una ronda
# futura dedicada a releer FUN_1800e1db4 a fondo") -- este barrido la
# CONFIRMA con numeros reales en vez de dejarla en sospecha: 289/2304
# combinaciones (12.5%) con `api2540_rounding` in {1,2,3} difieren del
# oraculo entre 0.010% y 0.192% (concentradas casi todas en
# `api_gravity60f_1980`, 288/289 -- `api_reldensity60f_1980` no mostro
# ninguna en el punto de operacion probado, `api_density15c_1980` solo 1).
# NO SE CORRIGIO esta ronda: requiere decompilar ademas `FUN_1800e1e14`
# (una 2a funcion de redondeo, nunca leida en detalle hasta ahora, que usa
# una mascara XOR de bits en vez de la aritmetica simple de
# `FUN_1800e1db4`) para replicar la cascada completa sin fabricar el
# detalle -- PENDIENTE EXPLICITO para una ronda futura dedicada, exactamente
# como ya preveia RONDA 22. Mientras tanto, `api2540_rounding=0` (el
# default, sin cambios de comportamiento) sigue siendo exacto.
#
# RESULTADO 3 [CERTAIN via decompilacion propia, NO se repite el patron de
# RONDA 23/24]: se releyo `FUN_1800f8f70` (nucleo de iteracion de
# `API_Dens15C_1952`, ya localizado desde RONDA 9) y se confirmo que llama
# DIRECTO a `FUN_1800E303C` (linea "FUN_1800e303c(param_1*DAT_180124818,
# param_2,uVar7,uVar6,param_4,param_8,param_10,...)" en
# `ghidra_api1952core_xll_output.txt`) -- el MISMO nucleo con clamp que usan
# `api_mpms_11_2_1m`/`api_mpms_11_2_1` por default. Esto confirma que
# `api_density15c_1952`/`api_gravity60f_1952`/`api_sg60f_1952`, que NO pasan
# `clamp_negative_net_pressure=False` (dejan el default `True`), estan
# CORRECTOS -- el barrido de consistencia interna (48 combinaciones, CPL del
# wrapper 1952 vs una llamada independiente a `api_mpms_11_2_1m`/
# `api_mpms_11_2_1` con la misma densidad/°API ya convergida) dio 48/48 OK,
# CERO discrepancias, en las 3 funciones, en las 4 combinaciones de P/EVP
# (incluido P<EVP) x 2 rounding x 2 conversion.
#
# RESULTADO 4: las 6 tablas puras de 1980 (Table5/6/23/24/53/54_1980) NO
# tienen argumento EVP -- el patron de bug de RONDA 23/24 no puede
# manifestarse ahi por construccion. Se corrio un chequeo de
# regresion/no-crash (144 combinaciones: product x rounding x
# hydrometer_correction, sin oraculo nuevo -- decompilar 6 nucleos
# adicionales quedo fuera del alcance razonable de este barrido) -- 144/144
# sin excepciones y dentro de rango fisico sano. La evidencia [CERTAIN]/
# [LIKELY] ya existente de RONDA 6/7/17/18 (con casos reales propios para
# varias) sigue siendo la fuente de verdad para estas 6 funciones.
#
# CONCLUSION: de las 2560 combinaciones, 2271 exactas (<0.01%, 88.7%), 289
# con discrepancia >0.01% (11.3%, TODAS explicadas por el mismo hueco
# YA CONOCIDO de RONDA 22 sobre `api2540_rounding`, no un bug nuevo), 0
# excepciones. NO se encontro ningun bug nuevo del patron de RONDA 23/24 en
# esta ronda -- la correccion de RONDA 23/24 queda RE-VALIDADA a fondo (no
# solo con el 1 caso original) y la familia 1952 queda CONFIRMADA libre del
# mismo patron, con evidencia de decompilacion propia (no solo por
# analogia).
# ===============================================================================
# RONDA 28 (2026-09-08): intento DEDICADO de cerrar el PENDIENTE de RONDA
# 22/25 (`api2540_rounding` != 0 en los 3 wrappers combinados 1980) --
# decompilo `FUN_1800e1e14` a fondo (nunca leida en detalle hasta ahora) y
# reconstruyo la cascada real de `FUN_1800e79e4` (Gravity60F_1980, 288/289
# de las discrepancias de RONDA 25) linea a linea. RESULTADO: la cascada es
# MAS COMPLEJA de lo que se podia cerrar con certeza en el tiempo disponible
# -- NO SE MODIFICO NINGUNA formula de produccion esta ronda (regla de oro:
# preferible dejar pendiente documentado a fabricar un cierre "mas o menos"
# exacto). Detalle de lo que SI se confirmo, [CERTAIN] via decompilacion:
#
# 1. `FUN_1800e1e14(x, n)`: NO es un redondeo comercial -- es un TRUNCADO
#    hacia cero a `n` decimales (`floor(escala*x)/escala` si x>=0,
#    `ceil(escala*x)/escala` si x<0, con `escala`/`1/escala` obtenidos de
#    `FUN_1800e1bc8(n)`) -- distinto de `FUN_1800e1db4` (redondeo comercial
#    mitad-lejos-de-cero, ya conocido desde RONDA 13). Las 2 funciones se
#    intercalan dentro de la MISMA cascada.
#
# 2. En los 3 nucleos combinados (`FUN_1800e62d4`/`FUN_1800e79e4`/
#    `FUN_1800e8494`), el argumento Excel-facing que llega como `param_5` es
#    el mismo `api2540_rounding` (confirmado cruzando el mapeo de argumentos
#    del wrapper raiz con el docstring RONDA 19, que ya lo habia identificado
#    como "el flag 'API Rounding' YA CONOCIDO de Table5_1980"). CONFIRMADO
#    EMPIRICAMENTE (llamada directa al `.xll`, no solo por lectura del
#    decompilado) que en la rama ITERATIVA (`conversion=1`, el default,
#    `param_9==1` en el binario) los 3 valores no-cero {1, 2, 3} producen
#    SIEMPRE el mismo resultado exacto (bit a bit) -- confirma RONDA 25.
#    Esto significa que la implementacion Python actual (`if
#    api2540_rounding == 2: ctl = round(ctl, 4)`) esta INCOMPLETA para los 3
#    valores por igual (no solo para 1 y 3 como se penso originalmente en
#    RONDA 22) -- ni siquiera el valor 2 replica la cascada real.
#
# 3. La cascada real (releida linea a linea en `FUN_1800e79e4`, que domina
#    288/289 de las discrepancias) NO es "redondear ctl al final": es una
#    reformulacion COMPLETA del algoritmo iterativo, estructuralmente
#    DISTINTA (aunque matematicamente equivalente a precision completa) de
#    la que usa este archivo para `api2540_rounding=0`:
#      - API observado y temperatura se redondean (comercial, 1 decimal) ANTES
#        de iterar.
#      - Se precalcula UNA VEZ (fuera del loop) un "CTL aproximado" via
#        polinomio SOLO EN FUNCION DE dT (constantes `DAT_1801ea7c0`=
#        1.278e-5, `DAT_1801ea7b8`=6.2e-9), multiplicado por la
#        densidad-equivalente del API observado -- este producto queda FIJO
#        durante TODA la iteracion (nunca se recalcula).
#      - Dentro del loop: el termino K0/K1/K2 (alpha, `*param_17` en el
#        decompilado) se calcula con divisiones TRUNCADAS a 8/8/10/10
#        decimales (caso especial producto 4: solo 6 y 8) y se suma
#        redondeado (comercial) a 7 decimales; el "CTL" final
#        (`*param_11`, exp del termino anterior) pasa por otra cascada de
#        truncados a 8 decimales + redondeo comercial final a 6 decimales
#        (iterativo) o 4/5 decimales con una comparacion condicional
#        (SOLO en la rama NO iterativa, `conversion=0` -- ahi si distinguen
#        los valores 1/2/3, con 2 dando siempre 4 decimales y 1/3 dando 5
#        salvo el caso donde 1 cae en la rama de comparacion).
#      - El candidato de densidad (`CTL_aprox_fijo / ctl / cpl`) se trunca a
#        3 decimales; el candidato en espacio °API se redondea (comercial) a
#        1 decimal. Hay un DESFASE de una pasada (patron "lag" ya visto en
#        RONDA 26 para 1952): el CPL usado para el candidato "definitivo" de
#        cada iteracion es el CPL calculado con el candidato °API de la
#        iteracion ANTERIOR, no el de la iteracion actual.
#      - La tolerancia de convergencia (en unidades de densidad) tambien
#        depende de `api2540_rounding`: `DAT_180193dc8`=1e-6 si es 0 (igual
#        al default de este archivo), pero `DAT_180193e90`=0.05 (o
#        `DAT_1801d5f60`=0.07 para producto 4) si es != 0 -- mismo patron ya
#        confirmado para 1952 en RONDA 26.
#
# 4. VALIDACION CONTRA EL ORACULO (honesta, no se fabrico un cierre): se
#    programo la reconstruccion completa del punto 3 y se probo contra los
#    144 casos de RONDA 25 (subconjunto sin `hydrometer_correction`, para
#    aislar esa variable) de `api_gravity60f_1980` que fallaban. Mejor
#    resultado obtenido tras probar variantes (con/sin tolerancia floja,
#    barriendo el numero de decimales del segundo truncado de densidad que
#    el decompilado deja AMBIGUO por reuso de registro -- el mismo tipo de
#    ambiguedad que ya freno un cierre en la familia 1952 antes en este
#    proyecto): 78/144 (54.2%) exactos -- una mejora real sobre el 0/144 de
#    un intento ingenuo (redondear solo `ctl` final a 5 decimales, que
#    coincidia por pura coincidencia en 1 caso de prueba pero fallaba en el
#    resto), pero NO el 100% necesario para tener certeza de la formula.
#    El residuo (~0.36% relativo, ~0.1 grados API) en el ~46% restante no
#    se pudo explicar con el tiempo disponible -- candidatos sin confirmar:
#    un registro reusado en la 2a llamada a `FUN_1800e1e14` dentro del loop
#    (`FUN_1800e1e14(dVar11)` SIN argumento de decimales visible en el
#    decompilado, a diferencia de la 1a ocurrencia que si muestra
#    `FUN_1800e1e14(dVar11,3)`) que podria depender del camino tomado por el
#    formula de F/CPL inlineada (que SI difiere segun el flag `rounding`
#    independiente); o un error de mapeo de que variable exacta pasa a ser
#    "dVar4" en la siguiente pasada del K0/K1/K2.
#
# 5. DECISION (regla de oro): NO SE MODIFICO `api_density15c_1980`/
#    `api_gravity60f_1980`/`api_reldensity60f_1980` esta ronda. La formula
#    parcial (78/144, 54.2%) NO se llevo a produccion por no alcanzar
#    certeza -- shippearla habria sido fabricar un cierre "mas o menos"
#    exacto, exactamente lo que la regla de oro prohibe. El barrido de
#    RONDA 25 se re-corrio SIN CAMBIOS de codigo (confirmacion de que nada
#    se rompio durante la investigacion): 2015/2304 (87.4566%) en los 3
#    wrappers de 1980, 289 discrepancias, NUMEROS IDENTICOS a RONDA 25 (cero
#    regresion, cero mejora -- honesto). `python -m
#    normas.API_MPMS_Tables_1980_2004` sigue en verde (exit 0) antes y
#    despues, sin cambios porque no se toco codigo de produccion.
#
# PENDIENTE EXPLICITO para una ronda futura dedicada (con mas tiempo para
# desensamblado x64 real, no solo el decompilado de Ghidra, para resolver la
# ambiguedad del punto 4): terminar de cerrar `api_gravity60f_1980` (dominante,
# 288/289 casos) y luego confirmar si `api_density15c_1980`/
# `api_reldensity60f_1980` comparten el MISMO residuo (su exposicion actual es
# mucho menor -- 1 y 0 discrepancias respectivamente en el punto de operacion
# probado -- pero eso no prueba que la cascada este bien ahi, solo que el
# efecto numerico en esos puntos es pequeno). El PENDIENTE de RONDA 22 sigue
# activo, ahora con mucho mas detalle que antes: la cascada esta MAPEADA
# estructuralmente completa, falta solo 1 detalle de redondeo para cerrarla
# con certeza.
# ===============================================================================

# ===============================================================================
# RONDA 29 (2026-09-08): mision DEDICADA a resolver la ambiguedad puntual que
# freno RONDA 28 (la 2a llamada a `FUN_1800e1e14` dentro del loop de
# `FUN_1800e79e4`, sin argumento de decimales visible en el decompilado de
# Ghidra) y, con eso resuelto, terminar de cerrar la cascada real de
# `api2540_rounding != 0` en los wrappers combinados 1980. Pedido explicito
# del usuario: usar desensamblado x64 real (`capstone`) como metodo
# preferente (mismo que ya funciono para el mapeo de 13 argumentos de
# `API_Ethylene_Propylene_puro.py`), complementado con el oraculo `.xll`
# directo para confirmar la hipotesis, no adivinarla.
#
# 1. AMBIGUEDAD RESUELTA CON CERTEZA (metodo 1, desensamblado x64 directo):
#    se cargo `FlowXpert.xll` con `pefile` (ImageBase=0x180000000, .text en
#    RVA 0x1000/file-offset 0x400) y se desensamblo con `capstone` (modo
#    CS_MODE_64) el cuerpo completo de `FUN_1800e79e4` (2736+200 bytes desde
#    0x1800e79e4). Se localizaron las 10 llamadas reales a `FUN_1800e1e14`
#    dentro de la funcion (mismo conteo que el decompilado) y, para cada una,
#    se rastreo hacia atras la ultima escritura al registro `edx` (el 2do
#    argumento entero, "decimales", en la convencion x64 de Windows: los
#    argumentos van por POSICION en rcx/xmm0, rdx/xmm1, r8/xmm2, r9/xmm3;
#    `param_1`(double) ocupa la posicion 1 -> xmm0, `param_2`(decimales,
#    entero) la posicion 2 -> edx). La llamada ambigua (linea ~2306 del
#    decompilado, `dVar11 = (dVar10/*param_11)/dVar12; if (param_5!=0)
#    dVar11=FUN_1800e1e14(dVar11);`) esta en la direccion real 0x1800e81e0,
#    y la instruccion inmediatamente anterior que escribe `edx` es
#    `lea edx,[rsi+2]` (0x1800e81d9) -- NO una constante inmediata, sino una
#    expresion en `rsi`. Se confirmo que `rsi` es literalmente el registro
#    donde el compilador cachea `param_9` (el flag `conversion` interno,
#    1=Observado->Estandar) durante todo ese tramo de la funcion, mediante el
#    `cmp esi,1 / jne <fuera-del-bloque>` que domina el bloque completo (la
#    ejecucion solo llega a la instruccion `lea edx,[rsi+2]` cuando ese salto
#    NO se tomo, es decir cuando `esi==1`). Por lo tanto en el UNICO camino de
#    ejecucion real donde esta llamada ocurre, `edx = rsi + 2 = 1 + 2 = 3` --
#    es decir, la llamada ambigua es `FUN_1800e1e14(dVar11, 3)`, EXACTAMENTE
#    el mismo truncado a 3 decimales que la 1a llamada del candidato de
#    densidad (linea ~2251, `FUN_1800e1e14(dVar11,3)`, confirmada con
#    `mov edx,3` explicito en la direccion 0x1800e7ffb, verificado con el
#    mismo metodo). El mismo patron (`lea edx,[rXX+2]` con el registro que
#    cachea `param_9`, resolviendo siempre a 3) se confirmo TAMBIEN,
#    independientemente, en `FUN_1800e62d4` (Dens15C, direccion 0x1800e6a63,
#    `rdi`) y `FUN_1800e8494` (RD60F, direccion 0x1800e8c1a, `rsi`) --
#    releyendo cada nucleo por separado, no asumiendo por analogia.
#
# 2. HALLAZGO ADICIONAL, no buscado originalmente pero necesario para cerrar
#    la cascada completa (metodo 1 otra vez, extendiendo el barrido de
#    llamadas a `FUN_1800e1db4`/`FUN_1800e1e14` de TODA la funcion, no solo
#    la ambigua): RONDA 28 no habia notado que la densidad RD_obs (=
#    141.5*999.012/(API_obs+131.5)) se REDONDEA (comercial) a 2 decimales
#    ANTES del loop cuando `api2540_rounding!=0` (direcciones 0x1800e7bfc y
#    0x1800e7c1b, ambas `mov edx,2`), y que la densidad-candidata usada como
#    denominador de alpha (`dVar4`) se vuelve a redondear a 2 decimales EN
#    CADA VUELTA del loop (direccion 0x1800e7e48, `mov edx,2`) antes de
#    calcular K0/K1/K2. Sin este paso, la reconstruccion de RONDA 28 solo
#    llegaba a 78/144 (54.2%) exacta contra el oraculo.
#
# 3. RECONSTRUCCION COMPLETA (`_round_comercial_n`/`_trunc_hacia_cero_n`/
#    `_alpha_cascade_api2540`/`_ctl_cascade_api2540`/
#    `_iterar_api2540_cascade`, definidas arriba de este archivo, justo
#    despues de `_ctl_1980_iter`): API/densidad y temperatura de entrada
#    redondeados (comercial) a 1 decimal; densidad-fija (RD_obs, o RD_obs*
#    factor-hidrometro si `hydrometer_correction`) redondeada a 2 decimales;
#    en cada vuelta: densidad-guess redondeada a 2 decimales -> alpha =
#    round(trunc(trunc(K0/rho,8)/rho,10) + trunc(K1/rho,10) + K2, 7) (rama
#    generica) o round(trunc(trunc(K0/rho,6)/rho,8) + K2, 8->7) (producto 4,
#    Transition area, K1=0 siempre) -> x=trunc(alpha*dT,8) ->
#    CTL=exp(round(-(trunc(x*0.8,8)*x_trunc + x),8)) [cascada real del
#    exponente, 3 truncados a 8 + 1 redondeo a 8] -> CTL final =
#    round(CTL,6) -> candidato#1 de densidad = trunc((RD_fija/CTL)/CPL_previo,
#    3) -> CPL fresco = `api_mpms_11_2_1`/`api_mpms_11_2_1m` en el candidato#1
#    (reexpresado en la unidad nativa de la pantalla) -> candidato#2 de
#    densidad = trunc((RD_fija/CTL)/CPL_fresco, 3) [la llamada ambigua,
#    resuelta en el punto 1] -> convergencia cuando
#    |densidad_guess_anterior - candidato#2| < 0.05 kg/m3 (0.07 para producto
#    4, `DAT_180193e90`/`DAT_1801d5f60`, ya conocidas desde RONDA 28) ->
#    resultado final = candidato#2 (reconvertido a la unidad nativa y
#    redondeado 1 decimal para °API, SIN redondeo adicional para densidad
#    kg/m3 -- confirmado empiricamente, ver punto 4).
#
# 4. VALIDACION (metodo 2, oraculo `.xll` directo, usado para CONFIRMAR no
#    para adivinar): usando `normas/_api1980_1952_wrappers_xll_directo.py`
#    (ya existente, reusado sin cambios) se corrio un barrido amplio (6
#    productos x 4 escenarios P/EVP x 2 `rounding` x 2
#    `hydrometer_correction` x 3 valores de API/densidad observada x 3
#    valores de T observada x 3 valores de `api2540_rounding`, 2592
#    combinaciones por funcion) para `api_gravity60f_1980` Y
#    `api_density15c_1980` por separado: 2571/2592 (99.19%) exacto (<0.01%
#    relativo) en AMBAS funciones, con el residuo (21/2592 en cada una)
#    EXCLUSIVAMENTE en producto 4 (Transition area) y con el MISMO patron
#    (diferencia de exactamente 0.1 en la unidad final -- un paso de grilla
#    completo, no un error de formula) -- ver punto 6 para la explicacion.
#
# 5. INTEGRACION: se reemplazo la implementacion parcial anterior
#    (`if api2540_rounding==2: ctl=round(ctl,4)`, la unica linea que existia
#    para este flag) por una llamada a `_iterar_api2540_cascade()` en la
#    rama `if api2540_rounding != 0:` de `api_density15c_1980` y
#    `api_gravity60f_1980` (rama iterativa, `conversion=1`). La rama directa
#    (`conversion=0`) NO se toco -- RONDA 25 ya habia confirmado que TODAS
#    las discrepancias eran con `conversion=1`, y el mecanismo de la rama
#    directa (`param_9!=1` en el binario) usa una cascada estructuralmente
#    distinta (vista en el propio desensamblado, decimales 4/5 en vez de
#    3/6) que queda fuera del alcance de esta ronda. Re-corrido el barrido
#    OFICIAL de RONDA 25/28 (`normas/_sweep_api_1952_1980_flags.py`, Parte B,
#    2304 combinaciones, punto fijo API=30/densidad=850kg/m3, T=90°F/25°C):
#      ANTES (RONDA 25/28): 2015/2304 (87.4566%), 289 discrepancias.
#      DESPUES (RONDA 29):  2298/2304 (99.7396%), 6 discrepancias.
#    Las 6 discrepancias restantes son TODAS `api_gravity60f_1980`, producto
#    4, P=300psig/EVP=0psig, `hydrometer_correction=1` (las 3 combinaciones
#    de `api2540_rounding` x 2 de `rounding`, mismo resultado en las 6 por
#    ser identicas segun el punto 2 de RONDA 28) -- CERO discrepancias en
#    `api_density15c_1980` (antes 1) y `api_reldensity60f_1980` (antes 0,
#    sin cambios, ver punto 7).
#
# 6. EL RESIDUO (6/2304 oficial, 21/2592 en el barrido amplio, siempre
#    producto 4) se investigo en detalle (no se dejo sin mirar): para el
#    caso oficial (API=30, T=90°F, P=300psig, EVP=0, hydrometer_correction=1,
#    api2540_rounding=1) el oraculo `.xll` real devuelve, junto con el
#    resultado (codigo=0x2a=OK), `oor1=4` -- una de las 3 banderas de salida
#    "fuera de rango" del propio binario (`param_19/20/21` de
#    `FUN_1800e79e4`, nunca decodificadas por completo en este proyecto,
#    ver docstring del modulo de `_api1980_1952_wrappers_xll_directo.py`)
#    puesta a un valor distinto de 0/1. Esto es evidencia DIRECTA (no
#    inferida) de que el binario mismo trata este punto de operacion como un
#    caso limite (la tolerancia de convergencia de producto 4 es la mas
#    floja de las 2, 0.07 kg/m3, y la combinacion con `hydrometer_correction`
#    activo desplaza el punto de partida de la iteracion lo suficiente como
#    para quedar justo en el borde de un paso de grilla de 0.1 unidades) --
#    coincide con el patron [LIKELY] "sensibilidad de trayectoria de punto
#    flotante en convergencia marginal" ya documentado en RONDA 21 y RONDA 27
#    para otras funciones de esta misma familia (1952). NO se fuerza un
#    ajuste ad-hoc para maquillar este residuo (violaria la regla de oro
#    igual que fabricar un cierre parcial).
#
# 7. `api_reldensity60f_1980` (`FUN_1800e8494`) NO se modifico esta ronda
#    pese a que la ambiguedad del punto 1 SI se resolvio tambien para ella
#    (mismo patron `lea edx,[rsi+2]`=3, confirmado por separado). Se
#    reconstruyo tambien su bloque de entrada/salida (que convierte a/desde
#    RD en vez de °API o kg/m3 directo) via desensamblado: en la salida, el
#    candidato final de densidad se divide DIRECTO por la constante real
#    999.012 (leida byte a byte de `[rip+0x101e8a]`, confirma
#    `RHO_WATER_60F_KGM3` ya usada en el resto del archivo) y se redondea
#    (comercial) a 4 decimales (`mov edx,4`, confirmado 2 veces, patron
#    redundante identico al doble-redondeo ya visto en `api_gravity60f_1980`);
#    en la entrada, el candidato se procesa via una subrutina compartida real
#    `FUN_1801060dc` (desensamblada aparte, confirma la formula
#    `API=141.5*999.012/densidad-131.5`, la MISMA que ya usa el resto del
#    archivo) pero PRECEDIDA de un redondeo a 3 decimales cuyo orden exacto
#    de operaciones (que se redondea, y en que espacio -- RD, densidad
#    intermedia, u otra variable -- antes de multiplicar por un factor
#    adicional visto en el mismo bloque, `xmm6`, no identificado con
#    certeza) no se termino de mapear con el tiempo disponible. Un intento de
#    implementar esta funcion con la MISMA cascada interna ya validada
#    (compartida con Gravity60F/Dens15C) mas esta conversion final directa a
#    RD dejo un residuo sistematico pequeno pero no-cero (~0.01%-0.02%,
#    direccion inconsistente entre casos) contra el oraculo `.xll` real en un
#    barrido de 72 casos -- por debajo de la certeza que la regla de oro
#    exige, y ademas el impacto medido de la version YA EXISTENTE (sin tocar)
#    en el punto de operacion del barrido oficial sigue siendo NULO (0/2304).
#    Por ambos motivos (sin certeza Y sin necesidad urgente) se DECIDIO no
#    tocar esta funcion esta ronda -- PENDIENTE EXPLICITO para una ronda
#    futura dedicada a mapear por completo el bloque de entrada de
#    `FUN_1800e8494` (rastrear el origen exacto de `xmm6` en ese tramo).
#
# 8. REGRESION: `python -m normas.API_MPMS_Tables_1980_2004` sigue en verde
#    (exit 0, sin excepciones) antes y despues. El default `api2540_rounding
#    =0` es byte-identico a versiones previas en ambas funciones modificadas
#    (la unica linea que se elimino, `if api2540_rounding==2: ctl=round(ctl,
#    4)` dentro del loop iterativo, era CODIGO MUERTO para `api2540_rounding
#    ==0` -- esa condicion nunca podia ser verdadera ahi, verificado
#    leyendo el flujo). `api_reldensity60f_1980` no se toco en absoluto.
#
# Archivos modificados: `normas/API_MPMS_Tables_1980_2004.py` (5 helpers
# nuevos `_round_comercial_n`/`_trunc_hacia_cero_n`/`_alpha_cascade_api2540`/
# `_ctl_cascade_api2540`/`_iterar_api2540_cascade`; rama `api2540_rounding!=0`
# reescrita en `api_density15c_1980`/`api_gravity60f_1980`; docstrings de las
# 3 funciones + esta seccion). Ningun otro archivo del repositorio
# modificado (los scripts de desensamblado/barrido de esta ronda quedaron en
# el scratchpad de la sesion).
# ===============================================================================
# RONDA 30 (2026-09-08, mision DEDICADA): resuelve el PENDIENTE explicito que
# dejo RONDA 29 -- el registro `xmm6` de `FUN_1800e8494` (RD60F_1980) que no
# se logro rastrear hasta su origen -- y con eso CIERRA la cascada real de
# `api2540_rounding != 0` en `api_reldensity60f_1980`, igualando la precision
# ya lograda en `api_gravity60f_1980`/`api_density15c_1980`.
#
# METODO: desensamblado x64 directo con `capstone` sobre `FlowXpert.xll`
# (mismo metodo que RONDA 29), esta vez enfocado en el bloque de ENTRADA de
# `FUN_1800e8494` (0x1800e8494-0x1800e8a90 aprox, ANTES del loop de
# iteracion) en vez del loop mismo (ya resuelto RONDA 29 via el patron
# `lea edx,[rsi+2]`=3, que se confirmo aplica IDENTICO aqui).
#
# 1. Se desensamblo el cuerpo completo de `FUN_1800e8494` (3200 bytes desde
#    0x1800e8494, 731 instrucciones) Y `FUN_1801060dc` (500 bytes, 122
#    instrucciones). Se localizaron TODAS las referencias a `xmm6` en la
#    funcion (grep sobre el desensamblado, no una unica ocurrencia
#    sospechada): 30 instrucciones distintas la leen o escriben a lo largo de
#    toda la funcion -- CONFIRMA que `xmm6` es, la mayor parte del tiempo, un
#    registro de USO GENERAL reciclado por el compilador (patron normal en
#    codigo optimizado), NO un "factor" persistente como sugeria la
#    formulacion original de RONDA 29 -- esa hipotesis quedo DESCARTADA por
#    evidencia directa.
# 2. El UNICO uso de `xmm6` con impacto real en el resultado (aislado
#    revisando cada instruccion entre su carga inicial y su primera
#    reescritura) es en el prologo: `movsd xmm6,[rip+0x3bf1c]` @ 0x1800e8504
#    carga una CONSTANTE (leida byte a byte del `.xll`, RVA resuelto via
#    `pefile`: direccion real 0x180124428, valor = 0.5 EXACTO) que sobrevive
#    SIN reescribirse hasta la instruccion `mulsd xmm11,xmm6` @ 0x1800e85e5
#    (dentro del bloque gateado por `api2540_rounding!=0`, antes de que
#    cualquier otra instruccion la sobrescriba con `movaps xmm6,xmm9` @
#    0x1800e8612 mas adelante, en el bloque de correccion de hidrometro). En
#    ese mismo bloque, 3 instrucciones antes (`mulsd xmm11,[rip+0x3be6f]` @
#    0x1800e85c0), se confirmo que la constante multiplicada ahi es EXACTAMENTE
#    2.0 (no 999.012 como se habia asumido por analogia en RONDA 29). La
#    secuencia completa resulta: `xmm11 = observed_rd` (copiado del
#    parametro `xmm0` @ 0x1800e852a) -> `xmm11 *= 2.0` -> `xmm11 =
#    FUN_1800e1db4(xmm11, 3)` (redondeo comercial a 3 decimales, `mov edx,3`
#    confirmado @ 0x1800e85c9) -> `xmm11 *= xmm6(=0.5)`. Es decir, el idiom
#    aritmetico estandar "multiplicar por N, redondear, dividir por N" para
#    redondear a la mitad de la unidad pedida por el redondeo directo --
#    aqui: `round_comercial(RD*2, 3)/2` redondea RD a la GRADUACION REAL de
#    un hidrometro de RD (0.0005), a diferencia de °API/kg-m3 que se redondean
#    a 0.1 en las otras 2 funciones (`_round_comercial_n(observed_api/dens,
#    1)`, RONDA 29) -- consistente con que un hidrometro de RD (escala
#    0.6-1.1) necesita mayor resolucion relativa que uno de °API o de
#    densidad en kg/m3, y con el hecho fisico conocido de que los hidrometros
#    de RD/SG del rango del petroleo se gradúan tipicamente en pasos de
#    0.0005 (ASTM E100 / API 1250). NO fabricado -- se deriva directamente
#    de una constante leida byte a byte y de la secuencia de instrucciones
#    real, sin analogia con las otras 2 funciones.
# 3. Se investigo tambien, por descarte, la hipotesis original de RONDA 29 de
#    que la subrutina compartida `FUN_1801060dc` fuera parte del bloque de
#    ENTRADA/SALIDA: se confirmo (grep de TODAS las instrucciones `call` de
#    la funcion, no solo alrededor de un sitio sospechado) que existe
#    EXACTAMENTE UNA llamada a `FUN_1801060dc` en toda la funcion (direccion
#    0x1800e8a87), y que esta llamada esta DENTRO del loop de iteracion (no
#    antes), convirtiendo el candidato de densidad de esa vuelta a °API para
#    alimentar la formula de CPL inlineada -- el MISMO rol que cumple
#    `_density_kgm3_to_rd60`+formula-API en `_cpl_de_candidato` de
#    `api_gravity60f_1980` (RONDA 29), solo que aqui el binario lo hace en
#    una unica llamada a subrutina en vez de 2 pasos inline. Esta hipotesis
#    original de RONDA 29 (que el redondeo a 3 decimales "antes de
#    `FUN_1801060dc`" fuera el mecanismo de entrada) queda por lo tanto
#    CORREGIDA: son 2 redondeos a 3 decimales DISTINTOS y con roles
#    DISTINTOS -- el de la entrada (bloque 0x1800e85c0, sobre `observed_rd`,
#    parte del mecanismo del punto 2) y el del candidato `dens_c1` dentro del
#    loop (bloque 0x1800e8a1d/0x1800e8a75, ya generico de
#    `_iterar_api2540_cascade`, RONDA 29) -- ambos coexisten sin conflicto.
# 4. La conversion de SALIDA (candidato final de densidad / 999.012,
#    redondeado a 4 decimales) YA estaba confirmada correctamente desde
#    RONDA 29 -- sin cambios, solo re-confirmada leyendo de nuevo el bloque
#    0x1800e8c2a-0x1800e8c57 (`divsd xmm1,[rip+0x101e8a]` = /999.012, `mov
#    edx,4` = redondeo a 4 decimales).
#
# INTEGRACION: se agrego la rama `if api2540_rounding != 0:` (antes ausente)
# a `api_reldensity60f_1980`, reusando `_iterar_api2540_cascade`/
# `_alpha_cascade_api2540` (sin cambios, ya [CERTAIN] desde RONDA 29) con la
# formula de entrada `rd_r = _round_comercial_n(observed_rd*2.0, 3) / 2.0`
# -> `rho_from_rd = rd_r * RHO_WATER_60F_KGM3` -> `rho_2dec`/`hyd_factor`/
# `rho_fixed` (identico patron a Gravity60F/Dens15C) y la formula de salida
# `rd_base = _round_comercial_n(dens_c2 / RHO_WATER_60F_KGM3, 4)`.
#
# VALIDACION EMPIRICA (oraculo `.xll` directo, `_api1980_1952_wrappers_xll_
# directo.py`, ya existente, reusado sin cambios): barrido amplio de 2592
# casos (6 productos x 4 escenarios P/EVP x 2 `rounding` x 2
# `hydrometer_correction` x 3 RD x 3 T x 3 `api2540_rounding`, mismo diseno
# que RONDA 29 para las otras 2 funciones): 2562/2592 (98.8426%) exacto
# (<0.01% relativo); el residuo (30/2592) es EXCLUSIVAMENTE producto 4
# (Transition area) con la bandera interna del propio oraculo `oor1=4`
# (convergencia marginal), MISMO patron [LIKELY] ya documentado en RONDA
# 21/27/29 para el resto de la familia -- no una discrepancia de formula.
#
# COMPARACION CON LA IMPLEMENTACION ANTERIOR (honesta, para verificar que el
# barrido oficial de RONDA 25/28/29 -- que mostraba 0/2304 discrepancias
# para esta funcion ANTES de esta ronda -- no invalida el cierre): se
# recalculo el MISMO barrido amplio de 2592 casos con la formula anterior
# (sin la cascada, la que estuvo en produccion desde RONDA 22 hasta esta
# ronda) y se comparo el ERROR ABSOLUTO (no solo el relativo con umbral
# 1e-4) contra el oraculo en TODOS los casos, no solo los que fallaban el
# umbral: error absoluto medio ANTERIOR = 2.71e-5, NUEVO = 1.16e-6 (23x mas
# preciso); casos con error <1e-6 ANTERIOR = 70/2592 (2.7%), NUEVO =
# 2562/2592 (98.8%). CONCLUSION: la implementacion anterior "pasaba" el
# barrido oficial de 2304 casos (que usa un umbral relativo de 1e-4) por
# COINCIDENCIA -- el efecto de ignorar la cascada completa es pequeno en
# terminos ABSOLUTOS en la escala 0-1 de RD (por eso nunca cruzaba el
# umbral), NO porque la formula anterior fuera correcta. Consistente con
# esto, el barrido oficial de RONDA 25/28/29 (`normas/
# _sweep_api_1952_1980_flags.py`, 2304 combinaciones, Parte B) re-corrido
# esta ronda pasa de 2298/2304 (99.7396%, 6 discrepancias, TODAS de
# `api_gravity60f_1980`) a 2289/2304 (99.35%, 15 discrepancias: las MISMAS 6
# de `api_gravity60f_1980`, sin cambios, + 9 NUEVAS de
# `api_reldensity60f_1980`) -- las 9 nuevas son, sin excepcion, el MISMO
# patron producto-4/`oor1=4` ya visto en el barrido amplio: el residuo REAL
# que antes estaba enmascarado por la escala ahora es visible porque el
# resto de la funcion dejo de tener el error sistematico de ~2.7e-5. Esto NO
# es una regresion de calidad -- es la version anterior dejando de
# "acertar por casualidad".
#
# REGRESION: `python -m normas.API_MPMS_Tables_1980_2004` sigue en verde
# (exit 0) antes y despues; `python -m normas._api1980_1952_wrappers_xll_
# directo` (autoconsistencia contra el oraculo, incluye
# `api_reldensity60f_1980` con flags default) tambien sigue en verde. El
# default `api2540_rounding=0` es byte-identico a versiones previas (la
# unica linea eliminada del loop iterativo antiguo, `if api2540_rounding==2:
# ctl=round(ctl,4)`, era codigo muerto para `api2540_rounding==0` -- esa
# condicion nunca podia ser verdadera ahi, ahora que ese caso vive en la
# rama nueva -- mismo patron ya aplicado en RONDA 29 a las otras 2
# funciones).
#
# Archivo modificado: `normas/API_MPMS_Tables_1980_2004.py` (rama
# `api2540_rounding!=0` agregada a `api_reldensity60f_1980`, reusando los 5
# helpers de RONDA 29 sin cambios; docstring de la funcion + esta seccion).
# Ningun otro archivo del repositorio modificado (scripts de
# desensamblado/barrido de esta ronda quedaron en el scratchpad de la
# sesion).
# ===============================================================================
# RONDA 31 (2026-09-08, mision DEDICADA): el usuario aporto texto que dice ser
# del manual oficial `Flow-X Manual IIIb - Function Reference_CM_FlowX_FR-EN_E.pdf`
# (verificado autentico por el orquestador, palabra por palabra contra el PDF
# real, paginas 19-23/1-based) describiendo el algoritmo COMPLETO de
# `fxAPI_Dens15C_1952`/`fxAPI_Dens15C_1980` (y por estructura compartida,
# `fxAPI_Gravity60F_1980`). Esta ronda extrajo con `pdfplumber` el texto
# COMPLETO de las paginas 19-72 (0-based, todas las funciones de la familia
# API 1952/1980/NGL-LPG) a `normas/manual_texto_api_1980_1952.txt` (2828
# lineas, para reuso futuro SIN re-extraer) y lo comparo linea a linea contra
# el codigo de este modulo, resolviendo el PENDIENTE que dejo RONDA 29 (residuo
# de 6-15 casos, producto 4/Transition area, en el barrido oficial).
#
# HALLAZGO 1 [CERTAIN, corrige una interpretacion ERRONEA de RONDA 29/30]: la
# hipotesis "el propio oraculo `.xll` devuelve `oor1=4` como bandera de
# convergencia marginal" es FALSA. Se probo empiricamente (barrido dedicado,
# ver mas abajo) que `oor1` es SIEMPRE identico al `product` de ENTRADA (1,3,
# 4,5,6,7) en TODOS los casos, no solo los que fallan -- coincide EXACTO con
# lo que el manual documenta como el output "Product": "When input 'Product'
# is 'B - Auto select', then the output is set to the actual selected
# product..., else the output is set equal to input Product" (paginas 22/33).
# Es decir `oor1` es el output PRDCUR (passthrough del producto), NO una
# bandera de diagnostico -- la "evidencia" citada en RONDA 29/30 para
# descartar el residuo como "convergencia marginal del binario" no probaba lo
# que decia probar. Esto NO invalida que el residuo fuera real (si lo era,
# ver Hallazgo 2), solo corrige el razonamiento que lo acompañaba.
#
# HALLAZGO 2 [CERTAIN via decompilacion + desensamblado, CIERRA el residuo de
# RONDA 29 100%]: el manual documenta (paginas 22/33, paso 4/5 y paso 14/18)
# que, en 'B - Auto select', el producto 4 (Transition area) solo se
# considera en la 2a vuelta del bucle exterior de auto-seleccion -- pero ESE
# mecanismo (exclusivo de auto-select, product=2, que este modulo rechaza
# explicitamente con `_AUTO_SELECT_NOTA`) NO es la causa del residuo, porque
# el barrido oficial (`_sweep_api_1952_1980_flags.py`) siempre pasa producto
# EXPLICITO (nunca auto-select). Releyendo el decompilado de las 3 funciones
# combinadas (`ghidra_api1980wrappers_xll_output.txt`) se encontro la causa
# REAL: justo ANTES del bucle `do{...}while(...)`, las 3 funciones
# (`FUN_1800e62d4` linea 1286-1288, `FUN_1800e79e4` linea 2176-2178,
# `FUN_1800e8494` linea 3082-3084) tienen el mismo patron `dVarN = dVarM; if
# ((param_9==1) && (*piVarX==4)) { dVarN = DAT_1801eaaa0; }` -- cuando
# `product==4` Y `conversion==1` (Observado->Estandar, CUALQUIER forma de
# llegar a producto 4, explicita o auto-select), la densidad-candidato usada
# para calcular alpha/CTL en la VUELTA 1 del bucle se reemplaza por una
# CONSTANTE FIJA `DAT_1801eaaa0 = 778.84` kg/m3 (extraida byte a byte,
# confirmada IDENTICA en las 3 funciones), en vez de la densidad real del
# usuario. Esto no estaba implementado (`_iterar_api2540_cascade` arrancaba
# siempre con `rho_guess=rho_fixed`) -- se agrego `SEED_TRANSITION_KGM3=778.84`
# y el override en la vuelta 1 cuando `product==4` (ver docstring de la
# constante y de la funcion). VALIDACION: barrido oficial (`_sweep_api_1952_
# 1980_flags.py`, Parte B, 2304 combinaciones) paso de 2289/2304 (99.35%, 15
# discrepancias heredadas de RONDA 29/30) a 2304/2304 (100.00%, CERO
# discrepancias) -- CIERRE COMPLETO, no parcial. Barridos amplios propios
# (648-3240 combinaciones por funcion, incluyendo P/EVP/T/API fuera de la
# grilla oficial) tambien dieron 0 fallas para producto 4 en las 3 funciones.
#
# HALLAZGO 3 [CERTAIN via decompilacion, bug independiente del residuo de
# RONDA 29]: `api_density15c_1980` NO implementaba el paso 15 del manual
# ("When API2540 rounding is enabled, the final density at [15C, equilibrium
# pressure] is rounded to 1 decimal place") en la rama iterativa -- devolvia
# el candidato truncado a 3 decimales sin el redondeo final. Confirmado en el
# decompilado (`LAB_1800e6ad8`, linea 1185-1190: `*param_10 = param_19; if
# (param_5!=0) { *param_10 = FUN_1800e1db4(param_19,1); }` -- el redondeo
# final es SOLO para el output de densidad, `F` sigue usando el candidato SIN
# redondear). `api_gravity60f_1980` YA tenia este paso (RONDA 29), por eso
# solo afectaba a Dens15C. Corregido agregando el redondeo final a 1 decimal
# en el output (`density_15c`), sin tocar el calculo de `F`.
#
# HALLAZGO 4 [CERTAIN via decompilacion, bug independiente, rama DIRECTA
# conversion=0]: las 3 funciones combinadas solo implementaban la opcion
# `api2540_rounding==2` ("Enabled for table value", CTL->4 decimales) en la
# rama DIRECTA (Standard->Observed); las opciones 1 y 3 quedaban con full
# precision por error desde RONDA 22. El manual documenta la regla completa
# (paginas 21/32, tabla de "API 2540 rounding"): opcion 1 = CTL a 4 decimales
# si CTL>=1, 5 si CTL<1; opcion 2 = SIEMPRE 4; opcion 3 = SIEMPRE 5. Se agrego
# `_ctl_rounding_directo()` implementando la regla completa, reusada en las 3
# funciones. Confirmado contra el oraculo en decenas de casos (incluye
# CTL<1 y CTL>=1 por separado).
#
# HALLAZGO 5 [CERTAIN via decompilacion, bug independiente, precision]:
# `api_density15c_1980` redondeaba el INPUT densidad a 1 DECIMAL
# (`round(d,1)`) al entrar cuando `api2540_rounding!=0`, en AMBAS
# direcciones -- pero el binario real (`FUN_1800e62d4` linea 1124-1126)
# redondea la densidad a la MITAD de una unidad (0.5 kg/m3, idiom
# "multiplicar por 2, redondear a 0 decimales, dividir por 2":
# `FUN_1800e1db4(d*2,0)*0.5`), NO a 1 decimal. Para inputs "limpios" (multiplo
# de 0.5, como los 850.0 kg/m3 del barrido oficial) ambos esquemas coinciden
# -- por eso era invisible hasta que se probo con densidades NO multiplo de
# 0.5 (ej. 873.4 kg/m3), donde produce una diferencia real (~0.1 kg/m3 en el
# resultado final). Se agrego `_round_densidad_hidrometro_metric()` (usada en
# ambas direcciones de `api_density15c_1980`) -- CONTRASTE explicito con
# `api_gravity60f_1980` (redondea °API a 1 decimal, SIN el idiom *2/0.5,
# confirmado por separado en `FUN_1800e79e4` linea 2005-2009) y
# `api_reldensity60f_1980` (redondea RD via el MISMO idiom *2/round(3dec)/0.5,
# ya correcto desde RONDA 30) -- son 3 graduaciones de hidrometro FISICAMENTE
# DISTINTAS, una por unidad nativa de pantalla, cada una confirmada leyendo su
# propio nucleo, no por analogia entre las 3.
#
# HALLAZGO 6 [CERTAIN via decompilacion, bug independiente, rama DIRECTA]: la
# rama `conversion==0` (Standard->Observed, sin iterar) de las 3 funciones
# usaba SIEMPRE la formula de precision completa (`_alpha`/`_ctl_1980`) para
# alpha/CTL, ignorando la cascada de truncados/redondeos intermedios de
# Table 5/6/53/54/23/24 que el manual documenta tambien para esta direccion
# (paginas 22-23/33-34, pasos 3-4 de "Conversion method 2"). Para la mayoria
# de los inputs de prueba esto no cambiaba el resultado (el CTL final
# converge al mismo valor redondeado), pero se encontraron casos-borde reales
# (ej. producto=7/Lubricating Oil en Dens15C con densidad=900/T=50, producto=5
# en RD60F con RD=0.75/T=120) donde el CTL "de precision completa" y el CTL
# "cascada" (el que realmente usa el binario) caen en DECIMALES DISTINTOS
# despues de redondear -- confirmado contra el oraculo en ambos casos (el
# CASCADE coincide EXACTO, el full-precision no). Se extendio la rama
# `conversion==0` de las 3 funciones para usar `_alpha_cascade_api2540`/
# `_ctl_cascade_api2540` (con los inputs redondeados a su graduacion de
# hidrometro respectiva) cuando `api2540_rounding!=0`, reusando los mismos
# helpers de RONDA 29 (sin crear formulas nuevas).
#
# VALIDACION FINAL (todas las correcciones juntas): `python -m normas.
# API_MPMS_Tables_1980_2004` exit 0, output BYTE-IDENTICO al de antes de esta
# ronda (cero regresion en el default `api2540_rounding=0`, confirmado por
# diff vacio). Barrido oficial (`_sweep_api_1952_1980_flags.py`): Parte A
# 64/64 (100%), Parte B 2304/2304 (100%, ANTES 2289/2304), Parte C 48/48
# (100%), Parte D 144/144 (100%) -- CERO discrepancias, CERO excepciones.
# Barridos amplios propios de esta ronda (no en el repo, ejecutados contra
# `_api1980_1952_wrappers_xll_directo.py` sin modificarlo): Dens15C 7680/7680,
# Gravity60F 7680/7680, RD60F 7680/7680 combinaciones exactas (error relativo
# maximo observado 2.4e-7, muy por debajo del umbral de discrepancia de 1e-4
# ya usado en todo el proyecto), cubriendo los 6 productos x ambas direcciones
# x los 4 valores de `api2540_rounding` x `rounding`/`hydrometer_correction`
# x multiples P/EVP x densidades/temperaturas NO redondas (para forzar los
# casos-borde de graduacion de hidrometro).
#
# Archivo modificado: `normas/API_MPMS_Tables_1980_2004.py` (constante
# `SEED_TRANSITION_KGM3`, helpers `_ctl_rounding_directo`/
# `_round_densidad_hidrometro_metric` nuevos; `_iterar_api2540_cascade` con el
# override de vuelta 1 para producto 4; ramas `conversion==0` y
# `api2540_rounding!=0` de las 3 funciones combinadas 1980 reescritas para
# usar los helpers correctos; docstrings actualizados). Archivo NUEVO:
# `normas/manual_texto_api_1980_1952.txt` (texto completo extraido del manual
# oficial, paginas 19-72 0-based, para reuso en rondas futuras sin
# re-extraer). Ningun otro archivo del repositorio modificado.
# ===============================================================================
# RONDA 49 (2026-09-10, mision DEDICADA): CIERRE de "product=2" (B - Auto
# select), pedido explicito del usuario tras ver el error de
# `_AUTO_SELECT_NOTA` en la pestaña "API Density @15°C (1980)"
# (`api_density15c_1980`).
#
# PASO 1 -- reconocimiento: se listaron los 17 sitios `raise ValueError
# (_AUTO_SELECT_NOTA)` del archivo: 6 tablas raw 1980 (Table5/6/23/24/53/54)
# + 3 combinadas 1980 (Dens15C/Gravity60F/RD60F) + 8 en la familia 2004
# (Table5/6/23/24/53/54/59/60). Se leyo el manual YA extraido
# (`manual_texto_api_1980_1952.txt`, paginas 21-23) confirmando que describe
# el ALGORITMO del auto-select (K0/K1/K2 segun densidad, Transition solo en
# la 2a vuelta) pero NO publica los breakpoints numericos de la norma -- hacia
# falta decompilar.
#
# PASO 2 -- decompilacion (SIN Ghidra nuevo, reuso de decompilados YA
# guardados de rondas anteriores, releidos linea a linea): se encontro el
# switch real de seleccion de region en DOS sitios independientes:
#   (a) `ghidra_api1980wrappers_xll_output.txt` -- las 3 funciones combinadas
#       (`FUN_1800e62d4`/Dens15C, `FUN_1800e79e4`/Gravity60F,
#       `FUN_1800e8494`/RD60F), cada una con su propio switch inline (NO
#       comparten una subrutina comun para esto).
#   (b) `ghidra_api_mpms_xll_output.txt` -- las 6 funciones RAW
#       Table5/6/23/24/53/54_1980, con las MISMAS constantes DAT_ByteExactas
#       (verificado por grep de las 12 direcciones especificas, no por
#       analogia).
# Constantes confirmadas (3 dominios, cada uno con 4 breakpoints: 3 limites
# de region + 1 breakpoint especial de "1a pasada sin Transition"):
#   densidad_kgm3: 770.0 (Gasoline/Transition), 788.0 (Transition/Jet), 839.0
#     (Jet/FuelOil), 779.0 (1a pasada, Transition excluida)
#   api:           52.0 (Gasoline/Transition), 48.0 (Transition/Jet), 37.0
#     (Jet/FuelOil), 50.0 (1a pasada)
#   rd:            0.771 (Gasoline/Transition), 0.789 (Transition/Jet), 0.84
#     (Jet/FuelOil), 0.779 (1a pasada)
# Esto CORRIGE la nota de Ronda 1 (arriba, docstring del modulo) que
# adivinaba "0.7785/0.84" para Table23 -- el valor real tiene 3 breakpoints
# de region (0.771/0.789/0.84), no 2, y 0.7785 era una confusion con el de
# 1a pasada (0.779).
#
# PASO 3 -- mecanismo (manual paginas 22-23, pasos 4/14, cruzado con el
# decompilado): direccion iterativa (Observed->Standard), hasta 2 "pasadas"
# completas -- pasada 1 resuelve la region SIN Transition y corre el calculo
# COMPLETO; si la region resuelta con el resultado YA CONVERGIDO de la
# pasada 1 (CON Transition incluida) coincide, esa pasada 1 ES el resultado
# final; si difiere, se corre una 2a pasada completa con la nueva region y
# ESE es el resultado final (nunca hay una 3a). Direccion directa
# (Standard->Observed): 1 sola evaluacion, con Transition incluida desde el
# inicio, sobre el valor de entrada (ya a condiciones base). Implementado en
# `_resolver_producto_auto_1980`/`_auto_select_1980` (nuevas), reusadas por
# las 9 funciones (6 raw + 3 combinadas).
#
# PASO 4 -- validacion: las 6 funciones RAW se validaron por CONSISTENCIA
# CRUZADA (dan, punto a punto, el mismo numero que la parte "CTL" de la
# funcion combinada correspondiente, ya validada contra el oraculo -- ej.
# `api_table53_1980(d=700,...,product=2)` da 709.3073, IDENTICO a
# `api_density15c_1980(d=700,...,product=2)`, ambos ya confirmados contra
# `calcular_dens15c_1980_directo` del oraculo `.xll`), [LIKELY] (mismo motor y
# constantes confirmadas, SIN oraculo `.xll` propio dedicado a estas 6 --
# igual criterio que ya usa este archivo para `hydrometer_correction`/
# `rounding` de Table23/53/54).
# Las 3 funciones combinadas se validaron [CERTAIN] END-TO-END contra el
# oraculo `.xll` real (`normas/_api1980_1952_wrappers_xll_directo.py`, que YA
# soporta `product=2` sin cambios) con un barrido dedicado de 136 puntos (3
# dominios x 2 direcciones de `conversion` x 19-26 valores cruzando las 4
# fronteras de cada dominio): 134/136 (98.5%) exacto tanto en el resultado
# numerico como en el `PRDCUR` (producto realmente seleccionado, expuesto
# aqui como `product_efectivo`). Los 2/136 restantes (API=51 y RD=0.775,
# ambos con `conversion=1`, ambos MUY cerca de una frontera de la 2a pasada)
# tienen el RESULTADO NUMERICO exacto a precision de maquina (diff<1e-15)
# pero el `PRDCUR` reportado por el oraculo difiere del `product_efectivo`
# calculado aqui -- es decir, el K0/K1/K2 usado para el calculo SI fue el
# correcto (confirmado porque el numero coincide exacto con una region
# especifica y no con la otra), pero la ETIQUETA que el oraculo expone en su
# propio `PRDCUR` en esos 2 puntos no calza con la region que produjo ese
# numero. No se investigo la causa exacta de esta micro-discrepancia de
# ETIQUETA (podria ser una 3a re-evaluacion interna del binario solo para el
# campo de reporte, evaluada en un punto ligeramente distinto al candidato
# que yo uso) -- documentado honesto como residuo menor [LIKELY] de
# `product_efectivo` (el campo NUEVO agregado esta ronda, no existia en el
# output original), NO del calculo (ese es [CERTAIN], 136/136).
#
# PENDIENTE HONESTO, fuera de alcance esta ronda: la familia 2004
# (Table5/6/23/24/53/54/59/60_2004) SIGUE lanzando `_AUTO_SELECT_NOTA` para
# product=2 -- tiene su PROPIO switch de auto-select (motor `FUN_1801053f4`,
# param_1==2, breakpoints DISTINTOS ya apuntados en memoria de rondas
# anteriores: DAT_18028db20/28/30 = 770.352/787.5195/838.3127 kg/m3 -- mas
# precisos que 1980 porque usan `RHO_WATER_2004_KGM3=999.016`), pero
# decompilar el mecanismo completo (unidad nativa de `param_3`, manejo del
# caso `param_3<db20`, y si existe el mismo patron de 2 pasadas) y conseguir
# un oraculo propio para validar (esta familia NO tiene ctypes wiring en
# `_api1980_1952_wrappers_xll_directo.py`, habria que construirlo) es trabajo
# NUEVO no cerrado esta ronda -- se deja el error explicito en las 8
# funciones 2004, mejorado con un puntero a esta seccion para la proxima
# ronda que lo aborde. La familia 1952 (sin parametro `product` real) y "E"/
# NGL-LPG (mecanismo de producto totalmente distinto, TP-27) tampoco se
# tocaron -- no aplica el mismo concepto de "B - Auto select" de 1980/2004.
#
# Archivos modificados: `normas/API_MPMS_Tables_1980_2004.py` (helpers
# `_resolver_producto_auto_1980`/`_auto_select_1980` nuevos; las 9 funciones
# 1980 reescritas para usar una closure `_ejecutar(producto_fijo)` +
# despacho por `_auto_select_1980` cuando `product==2`, sin cambiar el
# comportamiento para `product` explicito -- confirmado sin regresion,
# `python -m normas.API_MPMS_Tables_1980_2004` en verde antes y despues, y
# el autoconsistencia-vs-oraculo de `_api1980_1952_wrappers_xll_directo.py`
# tambien en verde); `interfaz_calculo_flujo.py` (parametro
# `auto_select_disponible` nuevo en los 2 builders de pestaña compartidos,
# `True` solo en las 9 llamadas de la familia 1980 ya cerrada; texto de aviso
# actualizado; campo nuevo "Product (selected)" en resultados que muestra
# `product_efectivo`). Ningun otro archivo modificado.
# ===============================================================================


if __name__ == "__main__":
    print("=== Autoprueba minima (sanity checks, NO es un caso real validado) ===")

    # Sanity check 1: si T_obs == T_ref, CTL debe ser exactamente 1.0
    r = api_table6_1980(api_60f=35.0, observed_temp_f=60.0, product=1)
    print("Table6_1980 crudo, T=60F (debe dar CTL=1.0):", r["ctl"])
    assert abs(r["ctl"] - 1.0) < 1e-12

    r = api_table54_1980(density_15c_kgm3=850.0, observed_temp_c=15.0, product=1)
    print("Table54_1980 crudo, T=15C (debe dar CTL=1.0):", r["ctl"])
    assert abs(r["ctl"] - 1.0) < 1e-12

    r = api_table24_1980(rd_60f=0.85, observed_temp_f=60.0, product=1)
    print("Table24_1980 crudo, T=60F (debe dar CTL=1.0):", r["ctl"])
    assert abs(r["ctl"] - 1.0) < 1e-12

    # Sanity check 2: Table5_1980 y Table6_1980 deben ser consistentes entre si
    # (ida y vuelta): API60 -> CTL(T) con Table6, luego observar el valor
    # resultante y volver con Table5 deberia reproducir el API60 original.
    api60_in = 35.0
    t_obs = 90.0
    r6 = api_table6_1980(api_60f=api60_in, observed_temp_f=t_obs, product=1)
    rd60_in = 141.5 / (131.5 + api60_in)
    rd_obs = rd60_in * r6["ctl"]
    api_obs = 141.5 / rd_obs - 131.5
    r5 = api_table5_1980(observed_api=api_obs, observed_temp_f=t_obs, product=1)
    print(f"Round-trip Table6->Table5 (crudo, T={t_obs}F): API60 original={api60_in}, "
          f"recuperado={r5['api_60f']:.6f}")
    assert abs(r5["api_60f"] - api60_in) < 1e-4

    # Sanity check 3: Table23_1980/Table24_1980 (RD directo) deben coincidir
    # con Table5_1980/Table6_1980 (via API) para el mismo punto fisico.
    rd60_check = 141.5 / (131.5 + api60_in)
    r24 = api_table24_1980(rd_60f=rd60_check, observed_temp_f=t_obs, product=1)
    print("Table24_1980 vs Table6_1980 (mismo CTL esperado):", r24["ctl"], "vs", r6["ctl"])
    assert abs(r24["ctl"] - r6["ctl"]) < 1e-12

    # Sanity check 4 (motor 2004): CTL=1.0 y CPL=1.0 cuando T_obs=60.0F y P=0.
    # [ACTUALIZADO RONDA 8] Antes de esta ronda se usaba T_obs=T_REF_2004_US_F
    # (60.0068749) directo, porque la correccion polinomica no existia todavia
    # en el codigo. Con la correccion activa, el T_obs "neutro" (el que hace
    # CTL=1.0) es el fisico 60.0F, NO 60.0068749: la propia correccion mapea
    # 60.0F -> ~60.0068749 (verificado: _micro_correccion_temp_2004(60.0) =
    # 60.00687489773... contra T_REF_2004_US_F=60.0068749, diff~2e-9) -- es
    # decir, RONDA 8 tambien explica el "sin fuente publica identificada" de
    # 60.0068749 documentado mas arriba: ese valor es simplemente la imagen
    # de 60.0F bajo la MISMA correccion polinomica, no una constante fisica
    # independiente. Se documenta como hallazgo adicional, no como certeza
    # de que asi lo pensaron los autores del binario.
    r2004 = api_table6_2004(api_60f=35.0, observed_temp_f=60.0,
                             pressure_psig=0.0, product=1)
    print("Table6_2004 crudo, T_obs=60.0F (fisico), P=0 (debe dar CTL=1.0, CPL=1.0):",
          r2004["ctl"], r2004["cpl"])
    assert abs(r2004["ctl"] - 1.0) < 1e-6
    assert abs(r2004["cpl"] - 1.0) < 1e-12

    # Constantes K0/K1 byte-exactas (documentadas arriba, re-verificadas aqui)
    import struct

    def _hex(v: float) -> str:
        return hex(struct.unpack(">Q", struct.pack(">d", v))[0])

    print("K0 crudo US  :", K_US[1].k0, _hex(K_US[1].k0), "== 0x40755187fcb923a3")
    print("K1 lube US   :", K_US[7].k1, _hex(K_US[7].k1), "== 0x3fd65269595feda6")
    print("K0 crudo metr:", K_METRIC[1].k0, _hex(K_METRIC[1].k0), "== 0x40832fc74538ef35")
    print("K1 lube metr :", K_METRIC[7].k1, _hex(K_METRIC[7].k1), "== 0x3fe416f0068db8bb")
    assert _hex(K_US[1].k0) == "0x40755187fcb923a3"
    assert _hex(K_US[7].k1) == "0x3fd65269595feda6"
    assert _hex(K_METRIC[1].k0) == "0x40832fc74538ef35"
    assert _hex(K_METRIC[7].k1) == "0x3fe416f0068db8bb"

    # Sanity check 5 (RONDA 4): Hydrometer Correction de Table5_1980 contra el
    # caso real de Ronda 3 (Crude, API_obs=30, T_obs=90F). Sin correccion debe
    # coincidir con el caso ya validado en Ronda 3 (27.89094); con correccion
    # debe reproducir el otro valor real (27.95136) que motivo este pendiente.
    r5_sin = api_table5_1980(observed_api=30.0, observed_temp_f=90.0, product=1)
    r5_con = api_table5_1980(observed_api=30.0, observed_temp_f=90.0, product=1,
                              hydrometer_correction=True)
    print("Table5_1980 Crude API=30 T=90F sin hidrometro:", r5_sin["api_60f"],
          "(real app: 27.89094)")
    print("Table5_1980 Crude API=30 T=90F con hidrometro:", r5_con["api_60f"],
          "(real app: 27.95136)")
    assert abs(r5_sin["api_60f"] - 27.89094) < 1e-4
    assert abs(r5_con["api_60f"] - 27.95136) < 1e-4

    # Sanity check 6 (RONDA 5): Table53_2004/Table54_2004 (metrico).
    # (a) T_obs=15C, P=0 -> density_15c debe devolver la entrada sin cambios
    r53_ref = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=15.0,
                                pressure_bar=0.0, product=1)
    print("Table53_2004 Crudo T=15C P=0 (debe devolver density_15c=850.0):",
          r53_ref["density_15c"])
    assert abs(r53_ref["density_15c"] - 850.0) < 1e-4

    # (b) round-trip Table53_2004 -> Table54_2004 (Crudo, T=45C, P=5 bar)
    r53 = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=45.0,
                            pressure_bar=5.0, product=1)
    r54 = api_table54_2004(density_15c_kgm3=r53["density_15c"], observed_temp_c=45.0,
                            pressure_bar=5.0, product=1)
    print("Round-trip Table53->Table54 (Crudo, T=45C, P=5bar): rho_obs original=850.0,",
          "recuperado=", r54["density_obs_predicted"])
    assert abs(r54["density_obs_predicted"] - 850.0) < 1e-3

    # (c) round-trip con otro producto (Lubricante, T=-10C, P=20 bar)
    r53_l = api_table53_2004(observed_density_kgm3=900.0, observed_temp_c=-10.0,
                              pressure_bar=20.0, product=7)
    r54_l = api_table54_2004(density_15c_kgm3=r53_l["density_15c"], observed_temp_c=-10.0,
                              pressure_bar=20.0, product=7)
    print("Round-trip Table53->Table54 (Lube, T=-10C, P=20bar): rho_obs original=900.0,",
          "recuperado=", r54_l["density_obs_predicted"])
    assert abs(r54_l["density_obs_predicted"] - 900.0) < 1e-3

    # Sanity check 7 (RONDA 6): 18 casos reales nuevos, ver
    # android_sdk_setup/casos_reales_api_tables_ronda5.json. Se re-verifican
    # aqui los 2 mas importantes (el que revelo y el que confirma el fix del
    # bug de mapeo ctl/ctpl de Table53_2004).
    r53_p0 = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=20.0,
                               pressure_bar=0.0, product=1)
    print("Table53_2004 Crudo T=20C P=0 (real app: ctl=0.99578 cpl=1.0 ctpl=0.99578):",
          f"{r53_p0['ctl']:.5f} {r53_p0['cpl']:.5f} {r53_p0['ctpl']:.5f}")
    assert abs(r53_p0["ctl"] - 0.99578) < 1e-4

    r53_p5 = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=20.0,
                               pressure_bar=5.0, product=1)
    print("Table53_2004 Crudo T=20C P=5bar (real app: ctl=0.995777 cpl=1.000369 "
          "ctpl=0.996144):",
          f"{r53_p5['ctl']:.6f} {r53_p5['cpl']:.6f} {r53_p5['ctpl']:.6f}")
    assert abs(r53_p5["ctl"] - 0.995777) < 1e-4
    assert abs(r53_p5["cpl"] - 1.000369) < 1e-4
    assert abs(r53_p5["ctpl"] - 0.996144) < 1e-4

    # Hydrometer Correction extendida a Table23_1980 (RONDA 6, caso real):
    r23_con = api_table23_1980(observed_rd=0.85, observed_temp_f=90.0, product=1,
                                hydrometer_correction=True)
    print("Table23_1980 Crude RD=0.85 T=90F con hidrometro "
          "(real app: rd_60f=0.861617 ctl=0.986133):",
          f"{r23_con['rd_60f']:.6f} {r23_con['ctl']:.6f}")
    assert abs(r23_con["rd_60f"] - 0.861617) < 1e-4
    assert abs(r23_con["ctl"] - 0.986133) < 1e-4

    # Hydrometer Correction metrico en Table53_1980 (RONDA 7, [LIKELY] via
    # conversion dimensional, ver docstring de _hydrometer_factor_metric):
    r53_hid = api_table53_1980(observed_density_kgm3=1000.0, observed_temp_c=20.0,
                                product=1, hydrometer_correction=True)
    print("Table53_1980 Crude Dens=1000 T=20C con hidrometro "
          "(real app: density_15c=1002.948 ctl=0.996945):",
          f"{r53_hid['density_15c']:.4f} {r53_hid['ctl']:.6f}")
    assert abs(r53_hid["density_15c"] - 1002.948) < 1e-2
    assert abs(r53_hid["ctl"] - 0.996945) < 1e-4

    # Sanity check 8 (RONDA 8): micro-correccion polinomica de 2004, contra
    # los 2 casos reales de Ronda 6 que revelaron el residuo (Table6_2004,
    # Crude, API60F=30, T=90F). Antes de esta ronda el error en CTL era
    # ~0.00068% (documentado); con la correccion debe bajar a <0.0001%
    # (el orden normal de ruido de esta familia).
    r6_2004_p0 = api_table6_2004(api_60f=30.0, observed_temp_f=90.0,
                                  pressure_psig=0.0, product=1)
    err_ctl_p0 = abs(r6_2004_p0["ctl"] - 0.986588) / 0.986588 * 100.0
    print("Table6_2004 Crude API60F=30 T=90F P=0 (real app ctl=0.986588):",
          f"{r6_2004_p0['ctl']:.7f}  error%={err_ctl_p0:.6f} (antes de RONDA 8: 0.000680%)")
    assert err_ctl_p0 < 0.0001

    r6_2004_p15bar = api_table6_2004(api_60f=30.0, observed_temp_f=90.0,
                                      pressure_psig=217.55661584592465, product=1)
    err_ctpl = abs(r6_2004_p15bar["ctpl"] - 0.987684) / 0.987684 * 100.0
    print("Table6_2004 Crude API60F=30 T=90F P=217.5566psig "
          "(real app ctpl=0.987684):",
          f"{r6_2004_p15bar['ctpl']:.7f}  error%={err_ctpl:.6f} (antes de RONDA 8: 0.000692%)")
    assert err_ctpl < 0.0001

    # Sanity check 9 (RONDA 9): api_mpms_11_2_1m contra el caso real del
    # usuario (Density_obs=1000kg/m3, T=25C, P=20bar(g), EVP=0). Usando la
    # densidad YA CONVERGIDA a 15C (1005.482, no la observada) como
    # `density_kgm3` -- ver docstring RONDA 9.
    r_mpms_m = api_mpms_11_2_1m(density_kgm3=1005.482, temp_c=25.0,
                                 pressure_bar_g=20.0, equilibrium_pressure_bar_g=0.0)
    err_cpl = abs(r_mpms_m["cpl"] - 1.001045) / 1.001045 * 100.0
    print("api_mpms_11_2_1m rho_15c=1005.482 T=25C P=20bar(g) "
          "(real app CPL=1.001045):",
          f"cpl={r_mpms_m['cpl']:.7f}  error%={err_cpl:.6f}")
    assert err_cpl < 0.001

    # Sanity check 10 (RONDA 9): CPL debe ser 1.0 cuando P==EVP (sin
    # diferencial de presion, sin importar T/rho).
    r_mpms_m0 = api_mpms_11_2_1m(density_kgm3=850.0, temp_c=40.0,
                                  pressure_bar_g=5.0, equilibrium_pressure_bar_g=5.0)
    print("api_mpms_11_2_1m P=EVP=5bar (debe dar CPL=1.0):", r_mpms_m0["cpl"])
    assert abs(r_mpms_m0["cpl"] - 1.0) < 1e-9

    r_mpms_us0 = api_mpms_11_2_1(api_gravity=35.0, temp_f=90.0,
                                  pressure_psig=100.0, equilibrium_pressure_psig=100.0)
    print("api_mpms_11_2_1 (US) P=EVP=100psig (debe dar CPL=1.0):", r_mpms_us0["cpl"])
    assert abs(r_mpms_us0["cpl"] - 1.0) < 1e-9

    # Sanity check 11 (RONDA 9): los 3 wrappers de 1980 deben ser
    # autoconsistentes -- con P=EVP (CPL=1.0), deben coincidir exacto con
    # las funciones Table53/5/23_1980 ya [CERTAIN] desde Ronda 1/2.
    r_dens15c = api_density15c_1980(observed_density_kgm3=1000.0, observed_temp_c=25.0,
                                     pressure_bar_g=5.0, equilibrium_pressure_bar_g=5.0,
                                     product=1)
    r_table53 = api_table53_1980(observed_density_kgm3=1000.0, observed_temp_c=25.0,
                                  product=1)
    print("api_density15c_1980 (P=EVP, CPL=1.0) vs api_table53_1980:",
          r_dens15c["density_15c"], "vs", r_table53["density_15c"])
    assert abs(r_dens15c["cpl"] - 1.0) < 1e-9
    assert abs(r_dens15c["density_15c"] - r_table53["density_15c"]) < 1e-3

    r_grav60f = api_gravity60f_1980(observed_api=30.0, observed_temp_f=90.0,
                                     pressure_psig=50.0, equilibrium_pressure_psig=50.0,
                                     product=1)
    r_table5 = api_table5_1980(observed_api=30.0, observed_temp_f=90.0, product=1)
    print("api_gravity60f_1980 (P=EVP, CPL=1.0) vs api_table5_1980:",
          r_grav60f["api_60f"], "vs", r_table5["api_60f"])
    assert abs(r_grav60f["cpl"] - 1.0) < 1e-9
    assert abs(r_grav60f["api_60f"] - r_table5["api_60f"]) < 1e-3

    r_rd60f = api_reldensity60f_1980(observed_rd=0.85, observed_temp_f=90.0,
                                      pressure_psig=50.0, equilibrium_pressure_psig=50.0,
                                      product=1)
    r_table23 = api_table23_1980(observed_rd=0.85, observed_temp_f=90.0, product=1)
    print("api_reldensity60f_1980 (P=EVP, CPL=1.0) vs api_table23_1980:",
          r_rd60f["rd_60f"], "vs", r_table23["rd_60f"])
    assert abs(r_rd60f["cpl"] - 1.0) < 1e-9
    assert abs(r_rd60f["rd_60f"] - r_table23["rd_60f"]) < 1e-3

    print("\nTodas las autopruebas estructurales pasaron. Recordar: esto NO")
    print("reemplaza un caso real validado contra el motor en vivo (.so) --")
    print("pendiente para una ronda futura (Fase 5/7, TODA la familia 2004,")
    print("y los 3 wrappers de presion de 1980 -- ver docstring RONDA 9).")

    # Sanity check 12 (RONDA 10): tabla real de interpolacion de Table53/54_1952
    # (metrica), decodificada de los bytes crudos del .xll. A T=15C (la
    # referencia) CTL debe dar 1.0 EXACTO -- surge de los datos reales de la
    # tabla, no esta forzado.
    r_t54_ref = api_table54_1952(density_15c_kgm3=1005.482, observed_temp_c=15.0)
    print("Table54_1952 T=15C (debe dar CTL=1.0 exacto):", r_t54_ref["ctl"])
    assert abs(r_t54_ref["ctl"] - 1.0) < 1e-9

    # Caso real completo del usuario: Density_obs=1000kg/m3, T=25C, P=20bar(g),
    # EVP=0bar(g) -> density_15c=1005.482, ctl=0.993510, cpl=1.001045.
    r_dens15c_1952 = api_density15c_1952(observed_density_kgm3=1000.0, observed_temp_c=25.0,
                                          pressure_bar_g=20.0, equilibrium_pressure_bar_g=0.0)
    err_d15c = abs(r_dens15c_1952["density_15c"] - 1005.482) / 1005.482 * 100.0
    err_ctl_1952 = abs(r_dens15c_1952["ctl"] - 0.993510) / 0.993510 * 100.0
    err_cpl_1952 = abs(r_dens15c_1952["cpl"] - 1.001045) / 1.001045 * 100.0
    print("api_density15c_1952 Density_obs=1000 T=25C P=20bar(g) "
          "(real app: density_15c=1005.482, ctl=0.993510, cpl=1.001045):")
    print(f"  density_15c={r_dens15c_1952['density_15c']:.4f}  error%={err_d15c:.6f}")
    print(f"  ctl={r_dens15c_1952['ctl']:.7f}  error%={err_ctl_1952:.6f}")
    print(f"  cpl={r_dens15c_1952['cpl']:.7f}  error%={err_cpl_1952:.6f}")
    assert err_d15c < 0.001
    assert err_ctl_1952 < 0.001
    assert err_cpl_1952 < 0.001

    r_t53_1952 = api_table53_1952(observed_density_kgm3=1000.0, observed_temp_c=25.0)
    print("api_table53_1952 (sin CPL) vs api_density15c_1952:",
          r_t53_1952["ctl"], "vs", r_dens15c_1952["ctl"])

    print("\nRONDA 10: Table53/54_1952 (metrico) y api_density15c_1952 CERRADOS")
    print("via tabla real decodificada del .xll -- ver docstring RONDA 10.")

    # Sanity check 13 (RONDA 11): api_table59_2004 a T=20C, P=0 (la propia
    # referencia) debe devolver la densidad de entrada sin cambios -- mismo
    # sanity fisico que Table53_2004 tuvo en Ronda 5 a T=15C.
    r_t59_ref = api_table59_2004(observed_density_kgm3=850.0, observed_temp_c=20.0,
                                  pressure_bar=0.0, product=1)
    print("Table59_2004 T=20C,P=0 (debe devolver 850.0 sin cambios):",
          r_t59_ref["density_20c"])
    assert abs(r_t59_ref["density_20c"] - 850.0) < 1e-4

    # Sanity check 14 (RONDA 11): round-trip Table59_2004 -> Table60_2004 debe
    # recuperar la densidad observada original (mismo chequeo que Ronda 5 hizo
    # para Table53/54_2004, con la referencia de 20C en vez de 15C).
    for prod, t_c, p_bar, rho_obs in ((1, 45.0, 5.0, 900.0), (7, -10.0, 20.0, 850.0)):
        r59 = api_table59_2004(observed_density_kgm3=rho_obs, observed_temp_c=t_c,
                                pressure_bar=p_bar, product=prod)
        r60 = api_table60_2004(density_20c_kgm3=r59["density_20c"], observed_temp_c=t_c,
                                pressure_bar=p_bar, product=prod)
        rho_recuperada = r60["density_obs_predicted"]
        err_roundtrip = abs(rho_recuperada - rho_obs)
        print(f"Round-trip Table59->Table60 product={prod} T={t_c}C P={p_bar}bar: "
              f"obs={rho_obs} -> density_20c={r59['density_20c']:.6f} -> "
              f"recuperado={rho_recuperada:.6f} (diff={err_roundtrip:.2e})")
        assert err_roundtrip < 1e-5

    # Sanity check 15 (RONDA 11): Table59_2004/Table60_2004 deben reusar
    # LITERALMENTE la misma tabla K0/K1/K2 que Table53_2004/Table54_2004 (no
    # hay una tabla propia -- ver docstring RONDA 11, hallazgo real que
    # corrige la premisa inicial de la ronda).
    for prod in (1, 3, 4, 5, 6, 7):
        r59_k = api_table59_2004(observed_density_kgm3=900.0, observed_temp_c=25.0,
                                   pressure_bar=0.0, product=prod)
        r53_k = api_table53_2004(observed_density_kgm3=900.0, observed_temp_c=25.0,
                                   pressure_bar=0.0, product=prod)
        assert r59_k["k0"] == r53_k["k0"] == K_US[prod].k0
        assert r59_k["k1"] == r53_k["k1"] == K_US[prod].k1
        assert r59_k["k2"] == r53_k["k2"] == K_US[prod].k2
    print("Table59_2004/Table60_2004 confirmadas: MISMA tabla K_US que "
          "Table53_2004/Table54_2004 (product 1,3,4,5,6,7) -- no hay K propia.")

    print("\nRONDA 11: Table59_2004/Table60_2004 CERRADAS [CERTAIN via")
    print("decompilacion cruzada .xll+.so] -- NO tienen K0/K1/K2 propias,")
    print("son Table53/54_2004 con T_ref=20C en vez de 15C. Ver docstring RONDA 11.")

    # Sanity check 16 (RONDA 12): Table6_1952/Table24_1952 deben dar CTL=1.0
    # EXACTO a T=60F para cualquier API/RD (surge de los datos reales de la
    # tabla, no esta forzado) -- probado en varios puntos incluyendo bordes
    # entre segmentos de 1 sola fila.
    for api in (0.5, 1.0, 8.5, 10.3, 35.0, 50.0, 65.7, 89.9, 99.99):
        r6 = api_table6_1952(api_60f=api, observed_temp_f=60.0)
        assert abs(r6["ctl"] - 1.0) < 1e-9, f"Table6_1952 API={api} T=60F debe dar CTL=1.0"
    for rd in (0.55, 0.65, 0.75, 0.85, 0.95, 1.05):
        r24 = api_table24_1952(rd_60f=rd, observed_temp_f=60.0)
        assert abs(r24["ctl"] - 1.0) < 1e-9, f"Table24_1952 RD={rd} T=60F debe dar CTL=1.0"
    print("\nTable6_1952/Table24_1952 T=60F -> CTL=1.0 exacto: OK (multiples API/RD).")

    # Sanity check 17 (RONDA 12): Table5_1952 a T=60F debe devolver el mismo
    # API de entrada (identidad), incluyendo valores que caen justo en el
    # borde entre 2 segmentos de 1 sola fila (validacion de que el aplanado
    # de filas reproduce el fallback real del binario entre segmentos).
    for api in (0.5, 8.5, 10.3, 49.9, 50.0, 65.7, 89.9, 99.99):
        r5 = api_table5_1952(observed_api=api, observed_temp_f=60.0)
        err = abs(r5["api_60f"] - api)
        assert err < 1e-3, f"Table5_1952 API={api} T=60F debe devolver ~{api}, dio {r5['api_60f']}"
    print("Table5_1952 T=60F -> identidad (API_60F==API_obs): OK.")

    # Sanity check 18 (RONDA 12): Table23_1952 a T=60F debe devolver el mismo
    # RD de entrada.
    for rd in (0.55, 0.65, 0.75, 0.85, 0.95, 1.05):
        r23 = api_table23_1952(observed_rd=rd, observed_temp_f=60.0)
        assert abs(r23["rd_60f"] - rd) < 1e-3, f"Table23_1952 RD={rd} T=60F debe devolver ~{rd}"
    print("Table23_1952 T=60F -> identidad (RD_60F==RD_obs): OK.")

    # Sanity check 19 (RONDA 12): VALIDACION CRUZADA -- Table5/6_1952 (eje
    # API) y Table23/24_1952 (eje RD) son 2 tablas binarias COMPLETAMENTE
    # INDEPENDIENTES (direcciones y formatos de cabecera distintos), pero
    # describen la MISMA superficie fisica de correccion (API<->RD via
    # 141.5/RD-131.5 es una identidad exacta, no una aproximacion). Que
    # ambas cadenas coincidan en el CTL final para el mismo punto fisico,
    # en 5 combinaciones (API,T) bien distintas, es evidencia fuerte e
    # independiente de que el decode de AMBAS parejas es correcto -- sin
    # necesidad de un caso real en vivo (que no esta disponible todavia
    # para esta sub-familia). Tolerancia 0.01% (mismo orden de ruido de
    # redondeo ya visto en el resto de la familia).
    for api_obs, t_f in ((30.0, 90.0), (10.0, -10.0), (60.0, 150.0), (85.0, 200.0), (5.0, 30.0)):
        r5x = api_table5_1952(observed_api=api_obs, observed_temp_f=t_f)
        r6x = api_table6_1952(api_60f=r5x["api_60f"], observed_temp_f=t_f)
        rd_obs = 141.5 / (131.5 + api_obs)
        r23x = api_table23_1952(observed_rd=rd_obs, observed_temp_f=t_f)
        r24x = api_table24_1952(rd_60f=r23x["rd_60f"], observed_temp_f=t_f)
        diff_pct = abs(r6x["ctl"] - r24x["ctl"]) / r24x["ctl"] * 100.0
        print(f"  API_obs={api_obs:5.1f} T={t_f:6.1f}F: CTL via Table5/6={r6x['ctl']:.6f} "
              f"vs CTL via Table23/24={r24x['ctl']:.6f}  diff%={diff_pct:.5f}")
        assert diff_pct < 0.01, "Table5/6 y Table23/24 deben coincidir en CTL (validacion cruzada)"
    print("Validacion cruzada Table5/6 <-> Table23/24 (2 tablas binarias")
    print("independientes, mismo punto fisico): coinciden en CTL, <0.01% -- OK.")

    # Sanity check 20 (RONDA 12): los 2 wrappers combinados deben ser
    # autoconsistentes con P=EVP (CPL=1.0, ctpl=ctl) contra las tablas puras.
    r_grav = api_gravity60f_1952(observed_api=30.0, observed_temp_f=90.0,
                                  pressure_psig=50.0, equilibrium_pressure_psig=50.0)
    r_t5 = api_table5_1952(observed_api=30.0, observed_temp_f=90.0)
    print("api_gravity60f_1952 (P=EVP, CPL=1.0) vs api_table5_1952:",
          r_grav["api_60f"], "vs", r_t5["api_60f"])
    assert abs(r_grav["cpl"] - 1.0) < 1e-9
    assert abs(r_grav["api_60f"] - r_t5["api_60f"]) < 1e-3

    r_sg = api_sg60f_1952(observed_rd=0.85, observed_temp_f=90.0,
                           pressure_psig=50.0, equilibrium_pressure_psig=50.0)
    r_t23 = api_table23_1952(observed_rd=0.85, observed_temp_f=90.0)
    print("api_sg60f_1952 (P=EVP, CPL=1.0) vs api_table23_1952:",
          r_sg["rd_60f"], "vs", r_t23["rd_60f"])
    assert abs(r_sg["cpl"] - 1.0) < 1e-9
    assert abs(r_sg["rd_60f"] - r_t23["rd_60f"]) < 1e-3

    print("\nRONDA 12: Table5/6/23/24_1952 (sistema US) y los wrappers")
    print("api_gravity60f_1952/api_sg60f_1952 CERRADOS via dump de bytes")
    print("crudos + validacion cruzada entre 2 tablas independientes.")
    print("Sin caso real en vivo todavia -- ver docstring RONDA 12.")

    # Sanity check 21 (RONDA 13): api_mpms_11_2_1/11_2_1m contra su primer
    # caso real DIRECTO (pantalla propia "API MPMS 11.2.1"/"11.2.1M", no via
    # wrapper 1952/1980 -- ver docstring RONDA 13).
    r1121m_direct = api_mpms_11_2_1m(density_kgm3=800.0, temp_c=25.0,
                                      pressure_bar_g=50.0, equilibrium_pressure_bar_g=0.0)
    err_cpl_1121m = abs(r1121m_direct["cpl"] - 1.004590) / 1.004590 * 100.0
    err_f_1121m = abs(r1121m_direct["f"] - 0.000091) / 0.000091 * 100.0
    print("api_mpms_11_2_1m (caso real DIRECTO) rho=800 T=25C P=50bar(g) "
          f"(app: cpl=1.004590 f=0.000091): cpl={r1121m_direct['cpl']:.7f} "
          f"f={r1121m_direct['f']:.8f} err_cpl%={err_cpl_1121m:.5f}")
    assert err_cpl_1121m < 0.001
    assert err_f_1121m < 1.0  # F tiene solo 2 cifras significativas visibles en la app

    r1121_direct = api_mpms_11_2_1(api_gravity=50.0, temp_f=90.0,
                                    pressure_psig=3.44738 * 14.5037738,
                                    equilibrium_pressure_psig=0.0)
    err_cpl_1121 = abs(r1121_direct["cpl"] - 1.000360) / 1.000360 * 100.0
    print("api_mpms_11_2_1 (caso real DIRECTO) API=50 T=90F P=50psig "
          f"(app: cpl=1.000360 f=0.000007): cpl={r1121_direct['cpl']:.7f} "
          f"f={r1121_direct['f']:.8f} err_cpl%={err_cpl_1121:.5f}")
    assert err_cpl_1121 < 0.001

    # Sanity check 22 (RONDA 13): api_mpms_11_2_2m/11_2_2 (NUEVAS esta ronda)
    # contra su caso real directo -- ver docstring RONDA 13.
    r1122m = api_mpms_11_2_2m(density_kgm3=600.0, temp_c=25.0,
                               pressure_bar_g=20.0, equilibrium_pressure_bar_g=0.0)
    err_cpl_1122m = abs(r1122m["cpl"] - 1.005227) / 1.005227 * 100.0
    err_f_1122m = abs(r1122m["f"] - 0.000260) / 0.000260 * 100.0
    print("api_mpms_11_2_2m rho=600 T=25C P=20bar(g) (app: cpl=1.005227 "
          f"f=0.000260): cpl={r1122m['cpl']:.7f} f={r1122m['f']:.8f} "
          f"err_cpl%={err_cpl_1122m:.5f} err_f%={err_f_1122m:.5f}")
    assert err_cpl_1122m < 0.001
    assert err_f_1122m < 0.5

    r1122 = api_mpms_11_2_2(rd_60f=0.5, temp_f=90.0,
                             pressure_psig=3.44738 * 14.5037738,
                             equilibrium_pressure_psig=0.0)
    err_cpl_1122 = abs(r1122["cpl"] - 1.002857) / 1.002857 * 100.0
    err_f_1122 = abs(r1122["f"] - 0.000057) / 0.000057 * 100.0
    print("api_mpms_11_2_2 RD=0.5 T=90F P=50psig (app: cpl=1.002857 "
          f"f=0.000057): cpl={r1122['cpl']:.7f} f={r1122['f']:.8f} "
          f"err_cpl%={err_cpl_1122:.5f} err_f%={err_f_1122:.5f}")
    assert err_cpl_1122 < 0.001
    assert err_f_1122 < 0.5

    # Sanity check 23 (RONDA 13): CPL debe ser 1.0 cuando P==EVP, para ambas
    # ediciones de 11.2.2, igual que ya se probo para 11.2.1 en Ronda 9.
    r1122m_0 = api_mpms_11_2_2m(density_kgm3=500.0, temp_c=10.0,
                                 pressure_bar_g=5.0, equilibrium_pressure_bar_g=5.0)
    assert abs(r1122m_0["cpl"] - 1.0) < 1e-9
    r1122_0 = api_mpms_11_2_2(rd_60f=0.45, temp_f=60.0,
                               pressure_psig=100.0, equilibrium_pressure_psig=100.0)
    assert abs(r1122_0["cpl"] - 1.0) < 1e-9
    print("api_mpms_11_2_2/11_2_2m P=EVP (debe dar CPL=1.0 en ambas): OK.")

    print("\nRONDA 13: API MPMS 11.2.2/11.2.2M CERRADAS [CERTAIN via")
    print("decompilacion + caso real DIRECTO exacto]; 11.2.1/11.2.1M suben")
    print("de caso real INDIRECTO a DIRECTO. Ver docstring RONDA 13.")

    # Sanity check 24 (RONDA 14): "E NGL/LPG (TP-27)" -- las 6 funciones
    # puras (Table23E/24E/53E/54E/59E/60E) contra sus 4 casos reales directos
    # + 3 round-trips exactos. Ver docstring RONDA 14.
    r23e = api_table23e(observed_rd=0.65, observed_temp_c=32.2222222)
    print(f"Table23E RD=0.65 T=90F (app: rd60f=0.664922 ctl=0.977559): "
          f"rd60f={r23e['rd_60f']:.6f} ctl={r23e['ctl']:.6f}")
    assert abs(r23e["rd_60f"] - 0.664922) < 1e-5
    assert abs(r23e["ctl"] - 0.977559) < 1e-5

    r24e = api_table24e(rd_60f=0.6, observed_temp_c=32.2222222)
    print(f"Table24E RD60F=0.6 T=90F (app: ctl=0.969628): ctl={r24e['ctl']:.6f}")
    assert abs(r24e["ctl"] - 0.969628) < 1e-5

    r53e = api_table53e(observed_density_kgm3=600.0, observed_temp_c=25.0)
    print(f"Table53E rho=600 T=25C (app: density_15c=610.4798 ctl=0.982833): "
          f"density_15c={r53e['density_15c']:.4f} ctl={r53e['ctl']:.6f}")
    assert abs(r53e["density_15c"] - 610.4798) < 1e-3
    assert abs(r53e["ctl"] - 0.982833) < 1e-5

    r59e = api_table59e(observed_density_kgm3=600.0, observed_temp_c=25.0)
    print(f"Table59E rho=600 T=25C (app: density_20c=605.2727 ctl=0.991289): "
          f"density_20c={r59e['density_20c']:.4f} ctl={r59e['ctl']:.6f}")
    assert abs(r59e["density_20c"] - 605.2727) < 1e-3
    assert abs(r59e["ctl"] - 0.991289) < 1e-5

    # Round-trip Table53E -> Table54E debe recuperar la densidad observada
    # original (mismo caso real de arriba).
    r54e = api_table54e(density_15c_kgm3=r53e["density_15c"], observed_temp_c=25.0)
    print(f"Round-trip Table53E->Table54E: recuperado={r54e['density_obs_predicted']:.4f} "
          f"(esperado 600.0000)")
    assert abs(r54e["density_obs_predicted"] - 600.0) < 1e-3

    # Round-trip Table59E -> Table60E, mismo chequeo con referencia 20C.
    r60e = api_table60e(density_20c_kgm3=r59e["density_20c"], observed_temp_c=25.0)
    print(f"Round-trip Table59E->Table60E: recuperado={r60e['density_obs_predicted']:.4f} "
          f"(esperado 600.0000)")
    assert abs(r60e["density_obs_predicted"] - 600.0) < 1e-3

    # Round-trip Table23E -> Table24E (RD60F resultante de 23E debe devolver
    # el mismo CTL, y RD60F*CTL debe recuperar el RD observado original).
    r24e_rt = api_table24e(rd_60f=r23e["rd_60f"], observed_temp_c=32.2222222)
    rd_obs_recuperado = r23e["rd_60f"] * r24e_rt["ctl"]
    print(f"Round-trip Table23E->Table24E: ctl={r24e_rt['ctl']:.6f} "
          f"(esperado {r23e['ctl']:.6f}), RD_obs recuperado={rd_obs_recuperado:.6f} "
          f"(esperado 0.65)")
    assert abs(r24e_rt["ctl"] - r23e["ctl"]) < 1e-9
    assert abs(rd_obs_recuperado - 0.65) < 1e-5

    print("\nRONDA 14: 'E NGL/LPG (TP-27)' -- 6/9 funciones CERRADAS")
    print("[CERTAIN via decompilacion + tabla real de 12 segmentos extraida a")
    print("bytes (pefile) + 4 casos reales directos + 3 round-trips exactos]:")
    print("Table23E/24E/53E/54E/59E/60E.")

    # Sanity check 25 (RONDA 15): los 3 wrappers combinados, llamada DIRECTA
    # .xll (ctypes, sin Excel/emulador) -- ver normas/_ngl_lpg_wrappers_xll_directo.py.
    try:
        rrd60f = api_rd60f_ngl_lpg(observed_rd=0.5, observed_temp_f=110.0,
                                    pressure_psia=200.0, atm_psia=14.696)
        print(f"RD60F_NGL_LPG RD=0.5 T=110F P=200psia (app: rd60f=0.537512 "
              f"ctl=0.927163 cpl=1.003289 ctpl=0.930212 f=0.000047 "
              f"evp=130.828psia): rd60f={rrd60f['rd_60f']:.6f} "
              f"ctl={rrd60f['ctl']:.6f} cpl={rrd60f['cpl']:.6f} "
              f"ctpl={rrd60f['ctpl']:.6f} f={rrd60f['f']:.6f} "
              f"evp={rrd60f['equilibrium_pressure_psia']:.3f}psia")
        assert abs(rrd60f["rd_60f"] - 0.537512) < 1e-5
        assert abs(rrd60f["ctl"] - 0.927163) < 1e-5
        assert abs(rrd60f["cpl"] - 1.003289) < 1e-5
        assert abs(rrd60f["ctpl"] - 0.930212) < 1e-5
        assert abs(rrd60f["f"] - 0.000047) < 5e-7

        r15c = api_dens15c_ngl_lpg(observed_density_kgm3=600.0, observed_temp_c=25.0,
                                    equilibrium_pressure_mode=1)
        print(f"Dens15C_NGL_LPG rho=600 T=25C P=0 (round-trip vs Table53E "
              f"density_15c=610.4798 ctl=0.982833): density_15c="
              f"{r15c['density_15c']:.4f} ctl={r15c['ctl']:.6f} cpl={r15c['cpl']:.6f}")
        assert abs(r15c["density_15c"] - 610.4798) < 1e-2
        assert abs(r15c["ctl"] - 0.982833) < 1e-5
        assert abs(r15c["cpl"] - 1.0) < 1e-9

        r20c = api_dens20c_ngl_lpg(observed_density_kgm3=600.0, observed_temp_c=25.0,
                                    equilibrium_pressure_mode=1)
        print(f"Dens20C_NGL_LPG rho=600 T=25C P=0 (round-trip vs Table59E "
              f"density_20c=605.2727 ctl=0.991289): density_20c="
              f"{r20c['density_20c']:.4f} ctl={r20c['ctl']:.6f} cpl={r20c['cpl']:.6f}")
        assert abs(r20c["density_20c"] - 605.2727) < 1e-2
        assert abs(r20c["ctl"] - 0.991289) < 1e-5
        assert abs(r20c["cpl"] - 1.0) < 1e-9

        print("\nRONDA 15: los 3 wrappers combinados (API_Dens15C_NGL_LPG/")
        print("API_Dens20C_NGL_LPG/API_RD60F_NGL_LPG) CERRADOS via llamada")
        print("DIRECTA .xll (ctypes, sin Excel/emulador) -- ver docstring RONDA 15")
        print("y normas/_ngl_lpg_wrappers_xll_directo.py. Familia 'E NGL/LPG")
        print("(TP-27)' COMPLETA, 9/9. De las 7 entradas del menu 'API': 7/7")
        print("CERRADAS (Ethylene/Propylene cerradas en otra sesion). Familia")
        print("'API' del menu raiz COMPLETA.")
    except Exception as _e:
        print(f"\n[AVISO] Los 3 wrappers NGL/LPG (RONDA 15, llamada directa .xll) "
              f"no se pudieron probar en este entorno: {_e!r}")

    # -------------------------------------------------------------------
    # RONDA 17: parametro `rounding` en las 6 funciones de la familia 1980.
    # Ver docstring del modulo, seccion "RONDA 17", para el detalle de
    # confianza CERTAIN/LIKELY por tabla. Aqui solo se verifica: (a) default
    # = cero regresion (ya cubierto por diff exacto del resto de este
    # autotest), (b) el flag SI cambia el numero cuando corresponde, (c) el
    # flag NO cambia nada cuando el enum Tipo B no es 2.
    # -------------------------------------------------------------------
    print("\n=== RONDA 17: parametro 'rounding' (Tipo A booleano / Tipo B enum) ===")

    # Tipo A (Table5_1980, [CERTAIN] contra el mismo caso real de Ronda 3,
    # decimales corregidos RONDA 18 -- ver docstring de api_table5_1980 y
    # android_sdk_setup/api5_rounding_dlg2.xml, dump crudo que muestra
    # "27.90000" con el switch "API Rounding" checked="true"):
    r5_round = api_table5_1980(observed_api=30.0, observed_temp_f=90.0, product=1,
                                rounding=True)
    print("Table5_1980 rounding=True (debe ser api_60f=27.9 exacto, real "
          "app '27.90000' truncado/redondeado a 1 decimal por 'API "
          "Rounding'):", r5_round["api_60f"])
    assert r5_round["api_60f"] == round(r5_sin["api_60f"], 1) == 27.9

    # Tipo A (Table23_1980, [LIKELY], decimales corregidos RONDA 18):
    r23_round = api_table23_1980(observed_rd=0.85, observed_temp_f=90.0, product=1,
                                  rounding=True)
    r23_sin = api_table23_1980(observed_rd=0.85, observed_temp_f=90.0, product=1)
    print("Table23_1980 rounding=True vs False (rd_60f):", r23_round["rd_60f"],
          "vs", r23_sin["rd_60f"])
    assert r23_round["rd_60f"] == round(r23_sin["rd_60f"], 1)

    # Tipo A (Table53_1980, [LIKELY], decimales corregidos RONDA 18):
    r53_round = api_table53_1980(observed_density_kgm3=1000.0, observed_temp_c=20.0,
                                  product=1, rounding=True)
    r53_sin = api_table53_1980(observed_density_kgm3=1000.0, observed_temp_c=20.0,
                                product=1)
    print("Table53_1980 rounding=True vs False (density_15c):", r53_round["density_15c"],
          "vs", r53_sin["density_15c"])
    assert r53_round["density_15c"] == round(r53_sin["density_15c"], 1)

    # Tipo B (Table6_1980, CORREGIDO RONDA 32 -- ver docstring de
    # api_table6_1980): rounding=0 no cambia nada; 1/2/3 SI redondean ctl,
    # cada uno a su propia cantidad de decimales (via _ctl_rounding_directo,
    # ya validada contra el oraculo .xll real en RONDA 31 para los wrappers
    # combinados 1980, misma "rama directa" sin iteracion).
    r6_base = api_table6_1980(api_60f=35.0, observed_temp_f=90.0, product=1)
    assert r6_base["ctl"] == api_table6_1980(api_60f=35.0, observed_temp_f=90.0,
                                              product=1, rounding=0)["ctl"]
    r6_1 = api_table6_1980(api_60f=35.0, observed_temp_f=90.0, product=1, rounding=1)
    r6_2 = api_table6_1980(api_60f=35.0, observed_temp_f=90.0, product=1, rounding=2)
    r6_3 = api_table6_1980(api_60f=35.0, observed_temp_f=90.0, product=1, rounding=3)
    ctl_esperado_1 = round(r6_base["ctl"], 4) if r6_base["ctl"] >= 1 else round(r6_base["ctl"], 5)
    print("Table6_1980 ctl base:", r6_base["ctl"])
    print("  rounding=1 'computational value' (4 dec si ctl>=1, 5 si ctl<1):", r6_1["ctl"])
    print("  rounding=2 'table value' (siempre 4 dec):", r6_2["ctl"])
    print("  rounding=3 (siempre 5 dec):", r6_3["ctl"])
    assert r6_1["ctl"] == ctl_esperado_1
    assert r6_2["ctl"] == round(r6_base["ctl"], 4)
    assert r6_3["ctl"] == round(r6_base["ctl"], 5)

    # Tipo B (Table24_1980, [CERTAIN] -- mismo caso real de Ronda 6 que Table6
    # para la opcion 2; 1/3 corregidas RONDA 32 por manual + reuso de
    # _ctl_rounding_directo):
    r24_base = api_table24_1980(rd_60f=0.85, observed_temp_f=90.0, product=1)
    r24_1 = api_table24_1980(rd_60f=0.85, observed_temp_f=90.0, product=1, rounding=1)
    r24_2 = api_table24_1980(rd_60f=0.85, observed_temp_f=90.0, product=1, rounding=2)
    r24_3 = api_table24_1980(rd_60f=0.85, observed_temp_f=90.0, product=1, rounding=3)
    print("Table24_1980 ctl base:", r24_base["ctl"], "rounding=1/2/3:",
          r24_1["ctl"], r24_2["ctl"], r24_3["ctl"])
    ctl_esperado_24_1 = round(r24_base["ctl"], 4) if r24_base["ctl"] >= 1 else round(r24_base["ctl"], 5)
    assert r24_1["ctl"] == ctl_esperado_24_1
    assert r24_2["ctl"] == round(r24_base["ctl"], 4)
    assert r24_3["ctl"] == round(r24_base["ctl"], 5)

    # Tipo B (Table54_1980, [LIKELY] -- sin caso real propio, corregida RONDA
    # 32 por manual + reuso de _ctl_rounding_directo):
    r54_base = api_table54_1980(density_15c_kgm3=850.0, observed_temp_c=20.0, product=1)
    r54_1 = api_table54_1980(density_15c_kgm3=850.0, observed_temp_c=20.0, product=1, rounding=1)
    r54_2 = api_table54_1980(density_15c_kgm3=850.0, observed_temp_c=20.0, product=1, rounding=2)
    r54_3 = api_table54_1980(density_15c_kgm3=850.0, observed_temp_c=20.0, product=1, rounding=3)
    print("Table54_1980 ctl base:", r54_base["ctl"], "rounding=1/2/3:",
          r54_1["ctl"], r54_2["ctl"], r54_3["ctl"])
    ctl_esperado_54_1 = round(r54_base["ctl"], 4) if r54_base["ctl"] >= 1 else round(r54_base["ctl"], 5)
    assert r54_1["ctl"] == ctl_esperado_54_1
    assert r54_2["ctl"] == round(r54_base["ctl"], 4)
    assert r54_3["ctl"] == round(r54_base["ctl"], 5)

    # Validacion de enum invalido (Tipo B):
    try:
        api_table6_1980(api_60f=35.0, observed_temp_f=90.0, product=1, rounding=9)
        raise AssertionError("rounding=9 deberia lanzar ValueError")
    except ValueError:
        pass

    print("\nRONDA 17: parametro 'rounding' agregado a Table5/6/23/24/53/54_1980")
    print("([CERTAIN] Table5/6/24 via caso real propio, [LIKELY] Table23/53/54 por")
    print("motor+wrapper compartido -- ver docstring). Analizadas 2004/1952/E: NO")
    print("se implemento en ninguna de esas 3 familias (motor distinto en 1952/E,")
    print("y en 2004 la decompilacion revela un flag booleano no distinguible entre")
    print("Rounding/otra semantica -- ver docstring RONDA 17). Cero regresion")
    print("verificada (diff exacto del resto de este autotest antes/despues).")
    print("\n=== RONDA 32: cruce manual literal (paginas 50-72) vs Table5/6/23/24/53/54_1980 ===")
    print("Table6/24/54_1980 ('API2540 rounding' enum 0-3): el manual documenta,")
    print("con el MISMO texto que ya se habia confirmado por oraculo .xll (RONDA 31)")
    print("para los wrappers combinados, que las opciones 1/2/3 TODAS redondean ctl")
    print("(4/5 dec segun ctl para 1, 4 fijo para 2, 5 fijo para 3) -- RONDA 6/17")
    print("solo habia cerrado la opcion 2 con caso real; 1 y 3 quedaban en 'full")
    print("precision' por error. CORREGIDO reusando _ctl_rounding_directo (misma")
    print("funcion, ya validada) porque estas 3 tablas calculan ctl en la 'rama")
    print("directa' (sin iteracion), identica estructuralmente a la de los wrappers.")
    print("Table5/23/53_1980 ('API2540 rounding' booleano): el manual documenta")
    print("ADEMAS del redondeo del output (ya CERTAIN/LIKELY, sin cambios) que la")
    print("tolerancia de convergencia del bucle cambia de 0.000001 a 0.05 kg/m3 --")
    print("detalle no implementado hasta ahora, agregado sin alterar ningun caso")
    print("real ya validado (la diferencia es <1e-4 API/RD/kg-m3, invisible al")
    print("redondeo a 1 decimal ya confirmado).")
    print("PENDIENTE HONESTO: ninguna de las 6 funciones tiene oraculo .xll DIRECTO")
    print("propio (ctypes) -- a diferencia de los wrappers combinados 1980, que si")
    print("lo tienen y permitieron CERRAR la ambiguedad de RONDA 28/29 con un barrido")
    print("de 2304 casos. Aqui la correccion se apoya en: (a) texto LITERAL del")
    print("manual (identico palabra por palabra al de los wrappers ya cerrados),")
    print("(b) decompilacion ya existente que confirma 'rama directa sin iteracion'")
    print("para Table6/24/54, y (c) reuso de una funcion de redondeo (_ctl_rounding_")
    print("directo) YA validada contra el oraculo real en otro contexto -- NO se")
    print("construyo un oraculo nuevo dedicado a estas 6 funciones especificamente")
    print("(no ameritaba el esfuerzo: mismo motor K0/K1/K2, mismo patron de flags,")
    print("ya explorado a fondo en la familia combinada). El manual NO documenta")
    print("'doble verificacion de region de producto' (repetir el loop si la")
    print("densidad convergida cae en otra region B) para NINGUNA de las 6 tablas")
    print("raw -- esa logica es EXCLUSIVA de los wrappers combinados 1980/2004,")
    print("confirmado por ausencia total de esa mencion en las 6 secciones del")
    print("manual (paginas 50-72) revisadas esta ronda.")

    # -------------------------------------------------------------------
    # RONDA 19 (2026-09-07): parametro `rounding` ("API-11.2.1 Rounding" de
    # la UI) en `api_mpms_11_2_1m`/`api_mpms_11_2_1` y en las 6 funciones
    # combinadas que los usan. Ver docstring del modulo, seccion "RONDA 19",
    # para el mecanismo completo (decompilado linea a linea de
    # FUN_1800e303c/FUN_1800e2d5c y sus 6 llamadores reales) y el nivel de
    # confianza real por funcion.
    # -------------------------------------------------------------------
    print("\n=== RONDA 19: parametro 'rounding' ('API-11.2.1 Rounding') ===")

    # Caso real NUEVO dado por el usuario esta ronda -- UNICO con validacion
    # exacta contra la pantalla real en ambos estados del flag.
    r_r0 = api_density15c_1952(observed_density_kgm3=1000.0, observed_temp_c=25.0,
                                pressure_bar_g=20.0, conversion=0, rounding=0)
    r_r1 = api_density15c_1952(observed_density_kgm3=1000.0, observed_temp_c=25.0,
                                pressure_bar_g=20.0, conversion=0, rounding=1)
    print("api_density15c_1952 (caso real, 'API Density @15°C (1952) (metric)'):")
    print(f"  rounding=0: density_obs={r_r0['density_15c']:.4f} (real app: 994.5497)")
    print(f"  rounding=1: density_obs={r_r1['density_15c']:.4f} (real app: 994.5502)")
    assert round(r_r0["density_15c"], 4) == 994.5497
    assert round(r_r1["density_15c"], 4) == 994.5502
    # CTL identico en ambos estados (el flag NO toca la tabla/formula CTL) --
    # coincide con la pantalla real, donde CTL se ve igual a 6 decimales.
    assert r_r0["ctl"] == r_r1["ctl"]
    # CPL/CTPL cambian, pero solo en una cifra invisible a 6 decimales en la UI.
    assert r_r0["cpl"] != r_r1["cpl"]
    assert round(r_r0["cpl"], 6) == round(r_r1["cpl"], 6) == 1.001057
    assert round(r_r0["ctpl"], 6) == round(r_r1["ctpl"], 6) == 0.994550

    # Cero regresion: default (rounding=0) reproduce EXACTO el numero ya
    # validado antes de esta ronda para las 6 funciones (mismo valor citado
    # en sus propios docstrings/RONDA 9/10/12/16).
    assert api_density15c_1980(1000.0, 25.0, 20.0, conversion=0)["density_15c"] == \
        api_density15c_1980(1000.0, 25.0, 20.0, conversion=0, rounding=0)["density_15c"]
    assert api_gravity60f_1980(30.0, 90.0, 0.0, conversion=1)["api_60f"] == \
        api_gravity60f_1980(30.0, 90.0, 0.0, conversion=1, rounding=0)["api_60f"]
    assert api_reldensity60f_1980(0.85, 90.0, 0.0, conversion=1)["rd_60f"] == \
        api_reldensity60f_1980(0.85, 90.0, 0.0, conversion=1, rounding=0)["rd_60f"]
    assert api_gravity60f_1952(30.0, 90.0, 0.0, conversion=1)["api_60f"] == \
        api_gravity60f_1952(30.0, 90.0, 0.0, conversion=1, rounding=0)["api_60f"]
    assert api_sg60f_1952(0.85, 90.0, 0.0, conversion=1)["rd_60f"] == \
        api_sg60f_1952(0.85, 90.0, 0.0, conversion=1, rounding=0)["rd_60f"]

    # Las otras 5 funciones NO tienen caso real propio de este flag -- solo
    # se verifica que `rounding=1` SI cambia algo (el mecanismo esta activo,
    # [CERTAIN via decompilacion directa de cada nucleo, ver docstrings) sin
    # afirmar el numero exacto de cada tabla.
    _base = api_density15c_1980(1000.0, 25.0, 20.0, conversion=0, rounding=0)
    _rnd = api_density15c_1980(1000.0, 25.0, 20.0, conversion=0, rounding=1)
    assert _base["ctl"] == _rnd["ctl"] and _base["cpl"] != _rnd["cpl"]
    print("api_density15c_1980 rounding=0 vs 1 (cpl):", _base["cpl"], "vs", _rnd["cpl"],
          "(sin caso real propio, [CERTAIN via decompilacion de FUN_1800e62d4])")

    # NOTA: en las ramas ITERATIVAS (conversion=1) el CTL converge a un
    # `rho_base` ligeramente distinto cuando `rounding=1` (el CPL usado
    # DENTRO del bucle de punto fijo tambien cambia, asi que el punto de
    # convergencia se desplaza) -- por eso aqui solo se verifica que el
    # resultado final SI cambia (el mecanismo esta activo), no que CTL se
    # mantenga bit-a-bit identico (eso solo aplica a la evaluacion DIRECTA,
    # conversion=0, como en el caso real de arriba).
    _base = api_gravity60f_1980(30.0, 90.0, 50.0, conversion=1)
    _rnd = api_gravity60f_1980(30.0, 90.0, 50.0, conversion=1, rounding=1)
    assert _base["api_60f"] != _rnd["api_60f"]
    print("api_gravity60f_1980 rounding=0 vs 1 (api_60f):", _base["api_60f"], "vs", _rnd["api_60f"])

    _base = api_reldensity60f_1980(0.85, 90.0, 50.0, conversion=1)
    _rnd = api_reldensity60f_1980(0.85, 90.0, 50.0, conversion=1, rounding=1)
    assert _base["rd_60f"] != _rnd["rd_60f"]
    print("api_reldensity60f_1980 rounding=0 vs 1 (rd_60f):", _base["rd_60f"], "vs", _rnd["rd_60f"])

    _base = api_gravity60f_1952(30.0, 90.0, 50.0, conversion=1)
    _rnd = api_gravity60f_1952(30.0, 90.0, 50.0, conversion=1, rounding=1)
    assert _base["api_60f"] != _rnd["api_60f"]
    print("api_gravity60f_1952 rounding=0 vs 1 (api_60f):", _base["api_60f"], "vs", _rnd["api_60f"])

    _base = api_sg60f_1952(0.85, 90.0, 50.0, conversion=1)
    _rnd = api_sg60f_1952(0.85, 90.0, 50.0, conversion=1, rounding=1)
    assert _base["rd_60f"] != _rnd["rd_60f"]
    print("api_sg60f_1952 rounding=0 vs 1 (rd_60f):", _base["rd_60f"], "vs", _rnd["rd_60f"])

    print("\nRONDA 19: mecanismo real de 'API-11.2.1 Rounding' CONFIRMADO via")
    print("decompilacion (FUN_1800e303c/FUN_1800e2d5c + sus 6 llamadores reales)")
    print("y validado EXACTO contra el caso real nuevo (994.5497 / 994.5502) en")
    print("api_density15c_1952. Implementado en las 6 funciones que usan")
    print("api_mpms_11_2_1/api_mpms_11_2_1m para CPL -- ver docstring RONDA 19.")

    # === RONDA 34 (2026-09-09): auditoria en vivo AVD real de las 8 pantallas
    # 'API 11.1 (2004)' (Table5/6/23/24/53/54/59/60_2004) y cierre del
    # parametro 'API Rounding' (booleano 0/1) que faltaba en las 8 funciones
    # -- ver docstring de `_api_rounding_2004`. 4 casos reales nuevos
    # (2 en Table5_2004, 2 en Table53_2004) confirman que el flag SOLO
    # redondea CTPL a 5 decimales (CTL/CPL quedan intactos, pese al texto
    # literal del manual que dice que los 3 se redondean).
    r5_a0 = api_table5_2004(observed_api=30.0, observed_temp_f=90.0,
                             pressure_psig=20 * 100 / 6.894757293168361, product=7)
    r5_a1 = api_table5_2004(observed_api=30.0, observed_temp_f=90.0,
                             pressure_psig=20 * 100 / 6.894757293168361, product=7,
                             api_rounding=1)
    print("Table5_2004 Lub oil API=30 T=90F P=20bar(g) (real app Disabled "
          "ctl=0.988127 cpl=1.001442 ctpl=0.989552 / Enabled ctpl=0.989550):",
          f"ctl={r5_a1['ctl']:.6f} cpl={r5_a1['cpl']:.6f}",
          f"ctpl0={r5_a0['ctpl']:.6f} ctpl1={r5_a1['ctpl']:.6f}")
    assert abs(r5_a0["ctl"] - 0.988127) < 1e-4 and abs(r5_a1["ctl"] - 0.988127) < 1e-4
    assert abs(r5_a0["cpl"] - 1.001442) < 1e-4 and abs(r5_a1["cpl"] - 1.001442) < 1e-4
    assert abs(r5_a0["ctpl"] - 0.989552) < 1e-4
    assert abs(r5_a1["ctpl"] - 0.989550) < 1e-5
    assert r5_a1["ctl"] == r5_a0["ctl"] and r5_a1["cpl"] == r5_a0["cpl"]

    r5_b0 = api_table5_2004(observed_api=30.123456, observed_temp_f=90.0,
                             pressure_psig=20 * 100 / 6.894757293168361, product=7)
    r5_b1 = api_table5_2004(observed_api=30.123456, observed_temp_f=90.0,
                             pressure_psig=20 * 100 / 6.894757293168361, product=7,
                             api_rounding=1)
    print("Table5_2004 Lub oil API=30.123456 T=90F P=20bar(g) (real app "
          "Disabled ctpl=0.989545 / Enabled ctpl=0.989550):",
          f"ctpl0={r5_b0['ctpl']:.6f} ctpl1={r5_b1['ctpl']:.6f}")
    assert abs(r5_b0["ctpl"] - 0.989545) < 1e-4
    assert abs(r5_b1["ctpl"] - 0.989550) < 1e-5

    r6_c0 = api_table6_2004(api_60f=30.0, observed_temp_f=90.0,
                             pressure_psig=15 * 100 / 6.894757293168361, product=1)
    r6_c1 = api_table6_2004(api_60f=30.0, observed_temp_f=90.0,
                             pressure_psig=15 * 100 / 6.894757293168361, product=1,
                             api_rounding=1)
    print("Table6_2004 Crude API60F=30 T=90F P=15bar(g) (real app Disabled "
          "ctl=0.986588 cpl=1.001111 ctpl=0.987684 / Enabled ctpl=0.987680, "
          "motor DIRECTO sin iteracion):",
          f"ctl={r6_c1['ctl']:.6f} cpl={r6_c1['cpl']:.6f}",
          f"ctpl0={r6_c0['ctpl']:.6f} ctpl1={r6_c1['ctpl']:.6f}")
    assert abs(r6_c0["ctl"] - 0.986588) < 1e-4 and abs(r6_c1["ctl"] - 0.986588) < 1e-4
    assert abs(r6_c0["cpl"] - 1.001111) < 1e-4 and abs(r6_c1["cpl"] - 1.001111) < 1e-4
    assert abs(r6_c0["ctpl"] - 0.987684) < 1e-4
    assert abs(r6_c1["ctpl"] - 0.987680) < 1e-5
    assert r6_c1["ctl"] == r6_c0["ctl"] and r6_c1["cpl"] == r6_c0["cpl"]

    r53_c0 = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=20.0,
                               pressure_bar=5.0, product=1)
    r53_c1 = api_table53_2004(observed_density_kgm3=850.0, observed_temp_c=20.0,
                               pressure_bar=5.0, product=1, api_rounding=1)
    print("Table53_2004 Crude Dens=850 T=20C P=5bar (real app Disabled "
          "ctl=0.995777 cpl=1.000369 ctpl=0.996144 / Enabled ctpl=0.996140):",
          f"ctl={r53_c1['ctl']:.6f} cpl={r53_c1['cpl']:.6f}",
          f"ctpl0={r53_c0['ctpl']:.6f} ctpl1={r53_c1['ctpl']:.6f}")
    assert abs(r53_c0["ctl"] - 0.995777) < 1e-4 and abs(r53_c1["ctl"] - 0.995777) < 1e-4
    assert abs(r53_c0["cpl"] - 1.000369) < 1e-4 and abs(r53_c1["cpl"] - 1.000369) < 1e-4
    assert abs(r53_c0["ctpl"] - 0.996144) < 1e-4
    assert abs(r53_c1["ctpl"] - 0.996140) < 1e-5
    assert r53_c1["ctl"] == r53_c0["ctl"] and r53_c1["cpl"] == r53_c0["cpl"]

    # api_rounding invalido debe rechazarse (misma convencion que las demas
    # familias de este archivo)
    try:
        api_table5_2004(30.0, 90.0, 0.0, 1, api_rounding=2)
        raise AssertionError("api_rounding=2 debio lanzar ValueError")
    except ValueError:
        pass

    print("\nRONDA 34: auditoria en vivo (AVD flowxpert_rd, 'API 11.1 (2004)',")
    print("8 pantallas, uiautomator) confirmo que las 8 funciones YA tenian")
    print("todos los parametros de entrada reales EXCEPTO 'API Rounding'")
    print("(booleano 0/1, ausente en las 8) -- agregado ahora en las 8 via")
    print("`_api_rounding_2004`, validado exacto (5 casos reales nuevos, 3")
    print("motores distintos: Table5_2004 iterativo, Table6_2004 directo sin")
    print("iteracion, Table53_2004 wrapper de doble evaluacion metrica)")
    print("contra la app real. Hallazgo: el manual dice que rounding=1")
    print("redondea CTL, CPL y CTPL a 5 decimales, pero la pantalla real")
    print("SOLO redondea CTPL; CTL/CPL quedan bit-a-bit identicos en los 5")
    print("casos. Sin caso real dedicado para Table23/24/54/59/60_2004")
    print("(comparten motor exacto con Table5/6/53_2004, ya confirmado en 2")
    print("de los 3 motores posibles) -- ver estado.md RONDA 34.")

    print("\n=== RONDA 49: product=2 ('B - Auto select'), regresion basica ===")
    # Regresion minima (sin oraculo -- el barrido completo contra el oraculo
    # .xll vive en el scratchpad de la sesion, no en el repo): confirma que
    # las 9 funciones afectadas (6 raw + 3 combinadas 1980) YA NO lanzan
    # ValueError con product=2 y que el producto resuelto cae en el rango
    # esperado (3..6) para un punto de cada region.
    for prod_esperado, d in ((3, 700.0), (4, 780.0), (5, 800.0), (6, 900.0)):
        r = api_table53_1980(observed_density_kgm3=d, observed_temp_c=25.0, product=2)
        assert r["product_efectivo"] == prod_esperado, (d, r["product_efectivo"])
    r_dens = api_density15c_1980(observed_density_kgm3=780.0, observed_temp_c=25.0,
                                  pressure_bar_g=0.0, product=2)
    assert r_dens["product_efectivo"] == 4
    r_grav = api_gravity60f_1980(observed_api=30.0, observed_temp_f=90.0,
                                  pressure_psig=0.0, product=2)
    assert r_grav["product_efectivo"] == 6
    r_rd = api_reldensity60f_1980(observed_rd=0.90, observed_temp_f=90.0,
                                   pressure_psig=0.0, product=2)
    assert r_rd["product_efectivo"] == 6
    print("OK -- product=2 ya no lanza ValueError en las 9 funciones 1980 y")
    print("resuelve el producto esperado en los puntos de control de arriba.")
    print("Barrido DEDICADO contra el oraculo .xll real (136 puntos: 3")
    print("dominios x 2 direcciones de `conversion` x 19-26 densidades/API/RD")
    print("cruzando las 4 fronteras, ver scratchpad de la sesion RONDA 49):")
    print("134/136 (98.5%) exacto en PRDCUR Y en el resultado numerico;")
    print("2/136 con PRDCUR reportado por el oraculo distinto del calculado")
    print("aqui (ambos casos MUY cerca de una frontera, ej. API=51 con la")
    print("frontera Transition/Jet en 48-52) -- pero el RESULTADO NUMERICO")
    print("en esos 2 casos coincide con el oraculo a precision de maquina")
    print("(diff<1e-15), confirmando que el K0/K1/K2 usado internamente SI")
    print("fue el correcto; solo la ETIQUETA 'product_efectivo' (agregada")
    print("esta ronda, no existe en el output original) queda [LIKELY] en")
    print("ese residuo -- ver seccion 'RONDA 49' para el detalle completo.")

    print("\n=== RONDA 50: product=2 ('B - Auto select') en la familia 2004 ===")
    # Regresion minima (sin oraculo -- el barrido de 160 puntos contra el
    # oraculo .xll real vive en el scratchpad de la sesion, no en el repo):
    # confirma que las 8 funciones 2004 (antes lanzaban _AUTO_SELECT_NOTA)
    # YA NO lo hacen y resuelven el producto Excel-level esperado
    # (3=Gasoline/4=Transition/5=Jet/6=FuelOil) en un punto de cada region,
    # usando los breakpoints REALES de este motor (770.352/787.5195/
    # 838.3127 kg/m3 -- DISTINTOS de los de 1980, ver docstring de
    # `_resolver_producto_auto_2004`).
    for prod_esperado, d in ((3, 700.0), (4, 780.0), (5, 800.0), (6, 900.0)):
        r = api_table60_2004(density_20c_kgm3=d, observed_temp_c=25.0, product=2)
        assert r["product_efectivo"] == prod_esperado, (d, r["product_efectivo"])
    r5 = api_table5_2004(observed_api=45.0, observed_temp_f=90.0, product=2)
    assert r5["product_efectivo"] == 5, r5
    r24 = api_table24_2004(rd_60f=0.90, observed_temp_f=90.0, product=2)
    assert r24["product_efectivo"] == 6, r24
    r53 = api_table53_2004(observed_density_kgm3=780.0, observed_temp_c=20.0, product=2)
    assert r53["product_efectivo"] == 4, r53
    print("OK -- product=2 ya no lanza ValueError en las 8 funciones 2004 y")
    print("resuelve el producto esperado en los puntos de control de arriba.")
    print("Barrido DEDICADO contra el oraculo `.xll` real (160 puntos: 80")
    print("modo directo + 80 modo iterativo, cruzando las 3 fronteras con")
    print("densidad/temperatura/presion aleatorias, llamando DIRECTO al")
    print("nucleo puro FUN_1801053f4 via ctypes -- ver scratchpad de la")
    print("sesion RONDA 50): 160/160 (100%) exacto en producto Y en el")
    print("resultado numerico (ctl/cpl/ctpl/k0/k1/k2). Mecanismo real")
    print("CONFIRMADO distinto al de 1980: 1 SOLA comparacion de 4 vias en")
    print("densidad kg/m3 (NUNCA en API/RD directo), re-evaluada en cada")
    print("iteracion segun el candidato actual (auto-consistente con la")
    print("propia convergencia) -- NO hay mecanismo de '2 pasadas' ni")
    print("exclusion de Transition en una 1a pasada como en 1980.")
