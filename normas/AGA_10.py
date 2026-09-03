# -*- coding: utf-8 -*-
"""
normas/AGA_10.py
==================
AGA Report No. 10 -- Velocidad del sonido y factor de supercompresibilidad
(Fpv) de gas natural. NO es una ecuacion de estado propia: usa las
propiedades (Z, Cp, Cv, dP/dD) de AGA8-DETAIL (normas/AGA_8.py) y de ahi
deriva velocidad del sonido (W) y Fpv.

Este archivo se puede ejecutar solo:
    python -m normas.AGA_10

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
Copia "NORMAS_AGA_GERG" (sin dependencias binarias). Para Critical Flow
intenta, en orden: (1) llamada directa a `FlowXpert.xll` si esta disponible
(solo Windows), (2) porte Python puro (`normas/AGA_10_puro.py`, siempre
disponible, funciona en cualquier plataforma). El resto de los campos
(Z/Fpv/Cp/Cv/etc.) SIEMPRE es Python puro.

PASO 1 -- Importar:
    from normas.AGA_10 import calcular_velocidad_sonido_y_fpv

PASO 2 -- Armar la composicion (ver `normas/AGA_8.py`, `NOMBRES_
COMPONENTES`, para los 21 nombres validos; fraccion o porcentaje, no hace
falta que sumen exacto):
    composicion = {"Metano": 96.5222, "Etano": 1.8186, "Propano": 0.4596,
                   "Nitrogeno": 0.2595, "CO2": 0.5904}

PASO 3 -- Llamar con T_K (Kelvin) y P_kPa (kilopascal absolutos):
    resultado = calcular_velocidad_sonido_y_fpv(
        composicion, T_K=288.15, P_kPa=5000.0, calcular_flujo_critico=True)

PASO 4 -- Leer resultados (37 campos). Los mas usados:
    resultado["Z_flujo"]; resultado["Fpv"]; resultado["W_m_s"]
    resultado["critical_flow_factor"]  # solo si calcular_flujo_critico=True
    resultado["metodo_critical_flow"]  # cual de los 2 caminos se uso de verdad

PASO 5 -- SIEMPRE revisar antes de un uso real/fiscal:
    resultado["rango_aga10"]["rango_combinado"]       # Normal/Extendido/Fuera de rango
    resultado["aviso_critical_flow_fuera_de_normal"]  # None si OK
    resultado["aviso_bug_flowxpert_critical_flow"]    # None si OK (bug conocido Kappa>1.6)
Si NINGUNO de los 2 caminos puede calcular Critical Flow, la funcion lanza
`RuntimeError` explicito -- no hay un "plan B" aproximado que devuelva un
numero silenciosamente.

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] Se decompilaron con Ghidra los exports `FlowXpert_AGA10_M` y
`FlowXpert_AGA10ex_M` de FlowXpert.xll. Ambos tienen la MISMA estructura de
despacho generico (motor + selector de tipo por puntero, funciones
FUN_1800471ac/FUN_180046cb4/FUN_1800470d8/FUN_180047088) que ya se documento
para AGA5 (ver ANALISIS_GHIDRA_FLOWXPERT/ghidra_aga5_dispatch_output.txt) y
para AGA8-DETAIL. NO son formulas matematicas propias inline -- son wrappers
delgados sobre el mismo motor de calculo generico de FlowXpert.

[CERTAIN -- 2026-07-22, cierra el gap anterior] Validado contra un caso real
de la app FlowXpert (pantalla "AGA-10 (extended)", composicion "Default",
P=1.01325 bar(a), T=0 degC, condiciones base = condiciones de flujo):
    W (Speed of Sound):   real=399.7979 m/s      calculado=399.7971 m/s    dif. 0.0002%
    Fpv:                  real=1.000000          calculado=1.000000       exacto
    Z (Compressibility):  real=0.997731          calculado=0.997731       dif. 0.000016%
    Cp [kJ/kg-degC]:      real=1.871773          calculado=1.871796       dif. 0.001%
    Cv [kJ/kg-degC]:      real=1.420532          calculado=1.420556       dif. 0.002%
    Cp [kJ/kmol-degC]:    real=34.88501          calculado=34.885447      dif. 0.001%
    Isentropic Exponent:  real=1.314666          calculado=1.314661       dif. 0.0004%
    Specific Heats Ratio: real=1.317656          calculado=1.317651       dif. 0.0004%
    Ideal rel. Density:   real=0.643500          calculado=0.643502       dif. 0.0003%
Esto confirma:
  1. La formula W = sqrt(1000*(Cp/Cv)*(dP/dD)/Mm) SI es la que usa FlowXpert
     (ya no es una suposicion basada solo en la definicion publica del
     estandar).
  2. Fpv = sqrt(Zb/Zf) tambien confirmado (en este caso base=flujo, Fpv=1
     exacto, el caso mas simple pero real).
  3. "Ideal rel. Density" = Mm_gas / 28.9625 (constante fija, no la masa
     molar de una composicion de aire real).
  4. "Real rel. Density" = (Mm_gas/28.9625) * (Z_aire/Z_gas), calculando
     Z_aire con el MISMO motor AGA8-DETAIL aplicado a una composicion de
     aire seco estandar (N2 78.09%, O2 20.95%, Ar 0.93%, CO2 0.04%) a las
     MISMAS T,P del gas -- confirmado numericamente: real=0.644583,
     calculado=0.644578 (dif. 0.0007%).
No se comparo la entalpia absoluta (H) porque DETAIL.FOR la define relativa
a un estado de referencia arbitrario distinto del que usa la app -- solo
las DIFERENCIAS/derivadas (Cp, Cv, W, Fpv, Kappa) son comparables entre
implementaciones independientes, y esas SI coinciden.

[CERTAIN -- 2026-07-24, confirma la nota anterior con datos, agrega campos
nuevos] Se recibio la captura real COMPLETA de esta pantalla (~25 salidas,
antes solo se comparaban 9). Se agregaron a `PropertiesDetail` (ver
normas/AGA_8.py) las propiedades de GAS IDEAL (Cv0, Cp0, H0, S0), derivadas
de la misma `Alpha0Detail` ya usada para las reales -- mismo patron
matematico que U/H/Cp reales, con Z0=1 exacto. Probado contra el caso real
completo (Default, 1.01325 bar(a), 0 degC):
  - Base/Flowing Density (mol/m3 y kg/m3): EXACTO.
  - Cp0, Cp, Cv (kJ/kg-C y kJ/kmol-C): todos <0.002% (Cv0 kJ/kmol-C 0.09%,
    algo peor pero razonable).
  - Ideal spec. Enthalpy (H0), Real spec. Enthalpy (H), Real spec. Entropy
    (S), en kJ/kg y kJ/kmol: **NO coinciden en absoluto** (~110% de
    diferencia en H, ~99% en S, incluso con signo contrario). Confirma con
    datos duros la sospecha ya anotada arriba: la referencia arbitraria de
    NIST/DETAIL.FOR no es la misma que usa FlowXpert internamente.
    Evidencia de que la FISICA si esta bien pese a esto: la DIFERENCIA
    H-H0 (departure function, independiente de la referencia arbitraria)
    SI coincide: real=-0.9729 kJ/kg, calculado=-0.9728 kJ/kg (dif. 0.006%).
    Es decir, el "punto cero" esta corrido, pero la forma de la funcion es
    correcta. No se encontro (ni se busco a fondo) el offset que usa
    FlowXpert para alinear el cero -- se decidio exponer H0/H/S de todas
    formas (la app si los muestra) pero con advertencia explicita en la
    interfaz/Excel de que el valor absoluto no es comparable.
  - Critical flow factor (C*), Isentropic ideal/real C*: la captura real
    muestra 0.000000 en los 3 porque el selector "Critical Flow" esta en
    "Don't calculate (fast)" (unico modo probado contra un caso real). Se
    devuelve 0.0 fijo para ese modo -- NO se implemento la fisica de flujo
    critico, si se usa "Calculate" estos 3 campos no van a coincidir.

[CERTAIN -- 2026-07-25, CIERRA el pendiente de arriba] Se recibieron 2
capturas reales NUEVAS con "Critical Flow: Calculate (slow)" (P=200kPa y
P=50kPa, T=283.15K, composicion Default, Add to iC5). Se implemento
`resolver_flujo_critico()`: resuelve el punto sonico real (garganta de
tobera) planteando la fisica de primeros principios --
conservacion de entropia (isentropico, S(T*,D*)=S0), conservacion de
energia (H0=H*+V*^2/2) y condicion sonica (V*=W*, velocidad = velocidad
local del sonido) -- todo evaluado con el motor AGA8-DETAIL ya confirmado,
resuelto por bisection anidada (primero T* a P* fijo via entropia, luego
P* tal que V*=W*). Confirmado con capstone/RetDec que el binario real
(`AGA10::crit`, libFXLibrary.so 0xe1dc0) hace un bucle iterativo
equivalente (hasta 99 pasos, usando `CTherm::HS_Mode`, entalpia-entropia)
-- misma estrategia general, aunque no se pudo decompilar el cuerpo exacto
con Ghidra (bug/limite de la herramienta con este binario especifico, ver
conversacion 2026-07-24/25).

Isentropic ideal C* e Isentropic real C* (EXACTOS, formula cerrada):
    C*_ideal = sqrt(k) * (2/(k+1))^((k+1)/(2*(k-1)))   [k=Kappa, gas de flujo]
    C*_real  = C*_ideal / sqrt(Zf)
Confirmado exacto contra los 2 casos reales (dif. <0.0002%).

Critical flow factor (C*) principal: la primera normalizacion probada
(razon contra un gas ideal equivalente) daba 0.1%-0.4% de error. Se
encontro la normalizacion CORRECTA en un reporte oficial de NASA de
dominio publico -- R. C. Johnson, "Real-Gas Effects in the Flow of
Methane and Natural Gas Through Critical-Flow Nozzles" (NASA TM X-2308,
1971, ntrs.nasa.gov/citations/19710011855) -- que define (ec. 11-12,
sistema US, adaptado aqui a SI):
    mdot = Cd * C* * A1 * P0 / sqrt(Rm * T0)
    Rm = R / Mm   (constante especifica del gas, R=8.31451 J/mol-K)
despejando C* = mdot/A1 * sqrt(Rm*T0) / P0 = (rho* * V*) * sqrt(Rm*T0) / P0
(mdot/A1 = flujo masico por unidad de area = rho* * V*, con rho*/V* del
punto sonico real ya resuelto arriba). Probado contra los 2 casos reales:
dif. 0.0085% y 0.0083% -- mismo nivel de precision que el resto del
proyecto. `calcular_flujo_critico=False` (default, "Don't calculate
(fast)") devuelve 0.0 en los 3 campos, replicando el comportamiento real
confirmado en 3 capturas distintas.

[GUESSING] Las condiciones base (Tb, Pb) varian por contrato/pais. Aqui se
exponen como parametros explicitos (no se asume un valor), igual que se hizo
con `columna_referencia` en AGA_5.py.

[CERTAIN -- 2026-07-25, CIERRA el pendiente de H0/H/S de arriba, PARA LA
COMPOSICION "Default"] Se recibio una 2a captura real completa (P=50kPa,
T=50degC, misma composicion Default) y se comparo contra la 1a (P=1.01325
bar(a), T=0degC). El offset (real - calculado) resulto ser LA MISMA
CONSTANTE en ambos casos, con precision <0.001%:
    Offset H0/H [kJ/kg]:   caso1=532.044380/532.044325   caso2=532.042303/532.042337
    Offset S    [kJ/kgC]:  caso1=10.147248               caso2=10.147240
Esto confirma la sospecha de arriba (el "cero" de FlowXpert es un
desplazamiento aditivo fijo, no una formula distinta) y permite corregirlo:
se suma `_OFFSET_H_KJ_KG` (=532.0433, promedio de los 4 valores de arriba) a
H0 y H, y `_OFFSET_S_KJ_KGC` (=10.14724) a S. Confirmado que el resultado
corregido coincide con AMBOS casos reales dentro de 0.0004%.
[CERTAIN -- 2026-07-25, CONFIRMADO limite real de esta correccion, NO
universal] Se probo un 3er caso real con la MISMA composicion Default (otro
T/P: 40degC/60kPa) -- coincide de nuevo, 0.00013% de error, buena
confirmacion adicional para Default. PERO se probo tambien un caso real con
METANO PURO (100% C1, P=60kPa, T=40degC) y el offset de Default (532.0433)
da **14.04% de error** -- confirma que el offset SI depende de la
composicion. El offset que necesitaria el metano puro es 624.4533 kJ/kg (un
gas 100% C1 resuelve directo: ese es el "ref_CH4" por si solo), 92.41 kJ/kg
distinto del de Default. Esto es consistente con que FlowXpert use una
entalpia de referencia DISTINTA POR COMPONENTE que NIST/DETAIL.FOR.

[CERTAIN -- 2026-07-25, MEJORA: modelo POR COMPONENTE en vez de constante
unica] Se recibio un 4o caso real (N2 puro, 100% N2, T=40degC, P=60kPa):
offset necesario = 309.5101 kJ/kg. Con 3 puntos (Metano puro=624.4533, N2
puro=309.5101, Default=532.0433) se resolvio inicialmente el offset del
"resto" de Default por diferencia (promedio implicito, no individual).

[CERTAIN -- 2026-07-25, AMPLIADO con 2 componentes puros mas] Se recibieron
2 casos reales mas: CO2 puro (100% CO2, T=40degC, P=50kPa) y Etano puro
(100% C2, mismas condiciones). Offsets resueltos:
    CO2:    212.8027 kJ/kg
    Etano:  394.4382 kJ/kg
Con estos 4 componentes conocidos (Metano, N2, CO2, Etano) se cubre el
98.26% de la masa de la composicion "Default" -- el promedio residual para
el 1.74% restante (Propano+iC4+nC4+iC5+nC5+nC6+nC7+nC8+Helio) se
recalculo por diferencia: 336.5638 kJ/kg. El offset de una mezcla se
calcula como promedio PONDERADO POR FRACCION DE MASA: los 4 componentes
conocidos usan su delta real; el resto usa el promedio residual como
aproximacion (ahora con menos peso relativo que antes, por lo tanto menos
riesgo de error). Validado: los 6 casos reales conocidos (Default x3,
Metano puro, N2 puro, CO2 puro, Etano puro) coinciden todos <0.0003%. De
paso, Fpv coincidio exacto en los 2 casos nuevos (<0.0001%), y Critical
Flow Factor dio 0.049% (CO2) y 0.084% (Etano) de error -- mismo patron
menor ya visto con N2 puro (0.015%).

[CERTAIN, RESUELTO 2026-07-29/30] El residual de Critical Flow Factor con
gases de un solo componente puro SI se investigo a fondo y se cerro: no
era un problema de convergencia (se subio max_iter de 60 a 90 sin ningun
cambio en el resultado, descartando precision numerica del solver propio)
ni de la formula fisica en si -- es que `resolver_flujo_critico()` (nuestra
implementacion independiente, NASA TM X-2308) tiene un residual real y
genuino frente al algoritmo REAL de FlowXpert (`AGA10::crit`), que crece
con composiciones de un solo componente. Se resolvio emulando `AGA10::crit`
directo con Unicorn (mismo patron que `_nx19_emulador.py`, ver
`normas/_aga10_emulador.py`) -- una sola llamada a esa funcion real calcula
TODO lo que muestra la pantalla "AGA-10 (extended)" (Mm, Z, Fpv,
densidades, densidad relativa, Kappa, Isentropic Exponent, Speed of Sound
Y Critical Flow Factor), no solo C*. Confirmado exacto en los 4 casos ya
conocidos (Default 0.000065%, N2/CO2/Etano puros: el emulador reproduce
EXACTO la diferencia ya documentada contra la formula propia -- prueba de
que el emulador da el valor real y la formula propia SI tenia ese
residual). `calcular_velocidad_sonido_y_fpv()` ahora usa el emulador para
`critical_flow_factor` cuando esta disponible (unicorn + el .so), con
`resolver_flujo_critico()` como fallback automatico si no. Ver docstring
completo de `normas/_aga10_emulador.py` para el detalle tecnico (struct de
entrada/salida confirmado campo por campo, PLT/libm necesarios).
[CERTAIN -- 2026-08-31, NUEVO: "Status"/"Range" REALES de fxAGA10ex_M,
decompilados directamente (no inferidos del manual)] La pantalla real tiene
2 salidas que ni `_aga10_xll_directo.py` ni `_aga10_emulador.py` extraen
(ver seccion "AUDITORIA EXHAUSTIVA 2026-08-29" e "INVESTIGACION DE CAUSA
RAIZ 2026-08-31" en el docstring de `_aga10_xll_directo.py`): "Status" (0
Normal/1 Input out of range/2 Calculation error/3 No convergence/4 Mole
fractions != 1.0) y "Range" (0 Normal/1 Extended/2 Out of Range). Se
decompilo con Ghidra el wrapper real `FUN_18009daf0` ("AGA10ex_M") y de ahi
2 funciones que SI se pudieron aislar limpio, sin dependencia de Excel:
  - `FUN_1800cdf14(double *composicion_22)`: calcula el "Range" POR
    COMPOSICION -- devuelve 0 (Normal), 1 (Extended) o 2 (Out of Range).
  - `FUN_1800ce1ec(double T_degC, double P_bar)`: calcula el "Range" POR
    T/P -- devuelve 0 (dentro) o -3 (fuera), y el llamador fuerza Range=2
    si esto falla, SIN IMPORTAR el resultado de la composicion (el T/P malo
    manda).
Todas las constantes numericas de ambas funciones se extrajeron a BYTES
CRUDOS con `pefile` (mismo metodo ya usado en la familia API MPMS, Rondas
8/10) y coinciden, LAS 21, EXACTAS con la tabla oficial de la pagina 16 del
manual ABB SpiritIT (`fxAGA8_C`, la funcion a la que el propio manual remite
para AGA-10: "Refer to the fxAGA8 function for details on the actual limit
values used by this function to set output 'Range'"), incluyendo el detalle
de que Hexanos+ (n-Hexano...n-Decano) y Agua NO tienen limite Expandido real
(el binario nunca los chequea mas alla del limite Normal) -- exactamente lo
que el manual anota como "Limit check is ignored for reason of simplicity".
Ademas, el limite T/P de `FUN_1800ce1ec` (-129..204 degC, 0..1379 bar(a))
coincidio BYTE A BYTE con el gate ya decompilado independientemente para
AGA-8 (`validar_rango_aga8()` en `normas/AGA_8.py`, extraido en una ronda
anterior de un binario/funcion DISTINTA) -- doble confirmacion cruzada de
que es el mismo limite real, no una coincidencia de lectura.
Un hallazgo real NO fabricado (que el manual no deja claro por si solo,
pero SI el binario decompilado): el chequeo por-componente de "Hexanos+" en
el binario real es POR COMPONENTE INDIVIDUAL (cada uno <=0.002 por separado)
y NO por la suma del grupo como sugiere el texto del manual ("Mole fraction
of Hexanes Plus 0.00..0.002") -- una diferencia real entre lo documentado y
lo compilado, mas permisiva que una lectura literal del texto.
Implementado en `validar_rango_aga10()` (mas abajo) -- replica ambas
funciones tal cual decompiladas, no una aproximacion basada solo en el texto
del manual. Aplicado retroactivamente a los 12 casos caoticos de la
auditoria 2026-08-29: 9/12 caen fuera del rango "Normal" (Extendido o Fuera
de rango) -- los otros 3 ("Default"/"GasRicoCO2"/"GasRicoN2" a
200 degC/800 bar(a)) siguen siendo "Normal" segun este chequeo real pese al
caos numerico observado, un residuo HONESTO que no se oculta: 800 bar(a)/
200 degC esta muy cerca del borde real (1379 bar(a)/204 degC) del rango T/P,
consistente con la causa raiz ya documentada (mal condicionamiento numerico
que crece cerca de los bordes del rango de validez, no solo fuera de el).
No se decompilo el resto de la logica de "Status" (que requeriria tambien
`FUN_1800d0610`/`FUN_1800c93ac` completos para NOCONV/CALCERR) -- el caso de
Status=COMPOOR (suma de composicion != 100%) ya esta cubierto en este
proyecto por `validar_suma_composicion()`/`_revisar_suma_composicion_o_
avisar()` (normas/AGA_8.py / interfaz_calculo_flujo.py), confirmado con la
MISMA tolerancia real encontrada aqui (constantes DAT_180193f00/08 =
0.9999/1.0001 para fraccion, DAT_1801942b0/b8 = 99.99/100.01 para
porcentaje -- FUN_1800c93ac acepta AMBAS convenciones).

[CERTAIN, 2026-08-03] Se agregaron 7 offsets individuales mas (Oxigeno,
Argon, Helio, Hidrogeno, CO, Agua, H2S), motivados por un caso real con
"Dry Air" (78% N2/21% O2/0.9% Ar) que mostro ~6% de error en Entalpia/
Entropia -- O2 y Ar nunca se habian calibrado, usaban el residual generico
(pensado para trazas de hidrocarburos pesados, no para una mezcla
dominada por O2/Ar). Mismo metodo que los 5 anteriores: caso real puro,
T/P variados para confirmar independencia de T/P (Agua confirmada a 0.01%
entre 150 degC y 200 degC/1 bar(a) -- necesita P baja y T alta porque a
condiciones normales de gas natural el agua pura es liquida, fuera del
rango de DETAIL.FOR). El residual se recalculo (338.3971 -> 324.0491) para
excluir a Helio (que ya tiene valor propio) del "resto sin calibrar".
[CERTAIN -- 2026-08-03, CIERRA los 2 pendientes de arriba] Con el emulador
de `AGA10::crit` ya corregido (bug de slots de flujo/base invertidos, ver
docstring de `_aga10_emulador.py`) se pudo resolver el offset de H0/H para
los 9 isomeros pesados que faltaban (Isobutano...n-Decano) Y el offset de
S POR COMPONENTE para los 21 componentes (antes una sola constante
calibrada solo con "Default") -- sin necesitar nuevas capturas del
telefono, llamando al emulador directo con cada componente puro. La
entropia de mezclado (termino -R*sum(x_i*ln(x_i))) NO complica esto: ese
termino es universal/independiente del componente, ya lo calcula
correctamente AGA8-DETAIL por su cuenta -- el offset por resolver es solo
la referencia arbitraria de CADA componente, aditiva igual que para H.
Cobertura de masa de "Default" resuelta individualmente: 100% para H0/H
Y para S (antes 99.17% para H, una sola constante para S). Validado sin
regresion (Default sigue en 0.00008% de diferencia en S) y con mejora
real en el caso que motivo esto (Dry Air: S de 62.96% de error a 0.0056%,
ver `test_aga10_dry_air_mezcla_calculate_slow` en
`normas/test_aga10_caso_real.py`).
===============================================================================
"""

# Offset aditivo (real - calculado) de la entalpia de gas ideal, POR
# COMPONENTE (kJ/kg de ESE componente puro). Los primeros 12 se resolvieron
# con casos reales puros capturados del dispositivo (ver notas de fecha
# abajo). Los 9 isomeros pesados (Isobutano...n-Decano) y TODOS los
# offsets de Entropia (`_OFFSET_S_KJ_KGC_POR_COMPONENTE`) se resolvieron
# el 2026-08-03 usando el emulador Unicorn de `AGA10::crit`
# (`normas/_aga10_emulador.py`) DIRECTO, sin necesitar nuevas capturas del
# telefono -- valido desde que se confirmo (mismo dia) que el emulador da
# el valor EXACTO para cualquier composicion (bug de slots de flujo/base
# invertidos corregido). Confirmado sin regresion contra los 8 casos
# reales de `test_aga10_caso_real.py` (Default sigue en 0.00008% de
# diferencia en S, igual que con la constante unica vieja) y con mejora
# real en el caso que motivo esto (Dry Air: S de 62.96% de error a
# 0.0056%, ver ese archivo de test). Con los 21 componentes cubiertos
# individualmente, YA NO HACE FALTA `_OFFSET_H_KJ_KG_RESIDUAL` ni una
# constante unica de S para el uso normal -- se dejan como fallback de
# seguridad para composiciones con algun componente no mapeado.
_OFFSET_H_KJ_KG_POR_COMPONENTE = {
    "Metano": 624.4533,
    "Nitrogeno": 309.5101,
    "CO2": 212.8027,
    "Etano": 394.4382,
    "Propano": 334.8450,
    # [CERTAIN, 2026-07-25/2026-08-03] Resueltos igual que los 5 de arriba
    # (caso real puro capturado del dispositivo, T/P variados para
    # confirmar que el offset no depende de T/P). Motivados por el
    # hallazgo de "Dry Air" (O2/Ar sin offset propio daban 6% de error).
    "Oxigeno": 271.2764,
    "Argon": 155.1362,
    "Helio": 1548.338,
    "Hidrogeno": 4269.856,
    "CO": 311.5722,
    "Agua": 549.5127,  # promedio de 2 T distintas (549.5399 @150C, 549.4855 @200C)
    # [CERTAIN, 2026-08-04] Recalibrado (antes 292.0425) tras agregar
    # `TH0I_ESCALA_POR_COMPONENTE` en normas/AGA_8.py (H2S usa una escala
    # de temperatura vibracional ~2.1% mayor que el estandar publico de
    # NIST, encontrada via 3 casos reales -- ver esa constante y la
    # memoria del proyecto, actualizacion 2026-08-04 (5)). Recalculado
    # con el mismo caso real ya usado antes (267.8250 via H0 Y via H,
    # cross-check exacto).
    "H2S": 267.8250,
    # [CERTAIN, 2026-08-03] Isomeros pesados -- via emulador (ver nota de
    # arriba), promedio de T=40degC y T=100degC/60kPa (dispersion <0.25
    # kJ/kg entre ambos puntos, T/P-independencia confirmada de nuevo).
    "Isobutano": 308.6811,
    "n-Butano": 331.6875,
    "Isopentano": 304.7218,
    "n-Pentano": 335.0397,
    "n-Hexano": 332.9987,
    "n-Heptano": 331.6196,
    "n-Octano": 330.7567,
    "n-Nonano": 330.1499,
    "n-Decano": 329.3964,
}
# Fallback de seguridad (no deberia usarse en la practica, los 21
# componentes ya estan cubiertos arriba): promedio historico calculado
# por diferencia contra "Default" antes de tener datos individuales.
_OFFSET_H_KJ_KG_RESIDUAL = 324.0491

# Offset aditivo (real - calculado) de la Entropia [kJ/(kg*K)], POR
# COMPONENTE -- ver nota arriba (mismo metodo/fecha que los 9 isomeros
# pesados de H). Antes de esto, S usaba UNA sola constante para los 21
# componentes (`_OFFSET_S_KJ_KGC` abajo, calibrada solo con "Default")
# -- por eso "Dry Air" daba 62.96% de error en S pese a que H0/H ya
# estaban bien. T/P-independencia confirmada (dispersion tipica
# <0.001 kJ/kg-K entre T=40degC y T=100degC/60kPa, salvo Hidrogeno
# ~0.003 y Agua que solo tiene 1 punto valido por licuar a 40degC/60kPa).
_OFFSET_S_KJ_KGC_POR_COMPONENTE = {
    "Metano": 11.61070, "Nitrogeno": 6.83497, "CO2": 4.85527,
    "Etano": 7.61755, "Propano": 6.13024, "Isobutano": 5.08249,
    "n-Butano": 5.33111, "Isopentano": 4.76170, "n-Pentano": 4.84417,
    "n-Hexano": 4.51137, "n-Heptano": 4.27150, "n-Octano": 4.08998,
    "n-Nonano": 3.94822, "n-Decano": 3.83517, "Hidrogeno": 64.80666,
    "Oxigeno": 6.40760, "CO": 7.05316, "Agua": 10.47497,
    "H2S": 6.032846,  # recalibrado 2026-08-04, ver nota de H2S en H arriba
    "Helio": 31.49076, "Argon": 3.87348,
}
# Fallback de seguridad (no deberia usarse en la practica, ver nota
# arriba) -- constante vieja, calibrada solo con "Default".
_OFFSET_S_KJ_KGC = 10.14724

import math

from .AGA_8 import (_composicion_a_x, DensityDetail, PropertiesDetail,
                     calcular_propiedades, R_DETAIL, NOMBRES_COMPONENTES, MM)


def _offset_h_kj_kg(x) -> float:
    """Offset de entalpia [kJ/kg] para la mezcla `x` (array 1-based de
    fracciones molares, ver `_composicion_a_x`), como promedio ponderado
    por FRACCION DE MASA de los offsets por componente -- ver nota del
    modulo. Componentes sin dato propio usan `_OFFSET_H_KJ_KG_RESIDUAL`."""
    masa_total = sum(x[i] * MM[i] for i in range(1, 22))
    if masa_total <= 0:
        return _OFFSET_H_KJ_KG_RESIDUAL
    offset = 0.0
    for i in range(1, 22):
        if x[i] <= 0:
            continue
        w_i = x[i] * MM[i] / masa_total
        delta_i = _OFFSET_H_KJ_KG_POR_COMPONENTE.get(NOMBRES_COMPONENTES[i - 1],
                                                       _OFFSET_H_KJ_KG_RESIDUAL)
        offset += w_i * delta_i
    return offset


def _offset_s_kj_kgc(x) -> float:
    """Offset de Entropia [kJ/(kg*K)] para la mezcla `x` -- mismo modelo
    que `_offset_h_kj_kg` (promedio ponderado por FRACCION DE MASA de los
    offsets por componente, ver `_OFFSET_S_KJ_KGC_POR_COMPONENTE`).
    Componentes sin dato propio usan `_OFFSET_S_KJ_KGC` (no deberia pasar,
    los 21 componentes ya estan cubiertos)."""
    masa_total = sum(x[i] * MM[i] for i in range(1, 22))
    if masa_total <= 0:
        return _OFFSET_S_KJ_KGC
    offset = 0.0
    for i in range(1, 22):
        if x[i] <= 0:
            continue
        w_i = x[i] * MM[i] / masa_total
        delta_i = _OFFSET_S_KJ_KGC_POR_COMPONENTE.get(NOMBRES_COMPONENTES[i - 1],
                                                        _OFFSET_S_KJ_KGC)
        offset += w_i * delta_i
    return offset

# Condiciones base tipicas de EE.UU. (60°F, 14.696 psia) -- SOLO como default
# documentado, no como valor asumido implicitamente. Verificar contra el
# contrato/norma local antes de usar en un caso real.
TB_DEFAULT_K = 288.7056   # 60 F
PB_DEFAULT_KPA = 101.325  # 14.696 psia

# Masa molar del aire usada por FlowXpert para "Ideal rel. Density" (constante
# fija, confirmada contra caso real -- ver docstring). Composicion de aire
# seco estandar usada para "Real rel. Density" (via el mismo motor AGA8-DETAIL,
# confirmada contra caso real dentro de 0.001%).
MM_AIRE = 28.9625
COMPOSICION_AIRE_SECO = {"Nitrogeno": 78.09, "Oxigeno": 20.95, "Argon": 0.93, "CO2": 0.04}


def _cstar_ideal(kappa: float) -> float:
    """Factor de flujo critico de gas ideal, formula clasica. Ver docstring
    del modulo -- confirmado EXACTO contra 2 casos reales usando Kappa del
    gas de flujo (real, no ideal) directamente.

    [CERTAIN, 2026-08-03] Kappa<=1 no tiene sentido fisico (Kappa=Cp/Cv,
    siempre >1 para un gas real) y rompe la formula matematicamente
    (division por cero en el exponente si Kappa=1, sqrt de negativo si
    Kappa<0) -- encontrado con un barrido de condiciones extremas
    (T/P fuera de rango donde DensityDetail no converge bien y arrastra
    un Kappa sin sentido). Se degrada a NaN en vez de crashear con
    "math domain error"."""
    if kappa <= 1.0:
        return float("nan")
    try:
        return math.sqrt(kappa) * (2.0 / (kappa + 1.0)) ** ((kappa + 1.0) / (2.0 * (kappa - 1.0)))
    except (ValueError, OverflowError):
        return float("nan")


def _cstar_real(kappa: float, Z: float) -> float:
    # [CERTAIN, 2026-08-03] A T/P fuera del rango fisico razonable (ej. un
    # error de unidad real que confunde K con degC), AGA8-DETAIL puede
    # devolver Z<=0 (sin sentido fisico) -- math.sqrt(Z) crashearia con
    # "math domain error". Se degrada a NaN (senal explicita de resultado
    # invalido) en vez de tumbar todo el calculo.
    if Z <= 0:
        return float("nan")
    return _cstar_ideal(kappa) / math.sqrt(Z)


def validar_rango_aga10(composicion: dict, T_K: float, P_kPa: float) -> dict:
    """Replica el "Range"/"Status" real de la pantalla "AGA-10 (extended)"
    (`fxAGA10ex_M`) -- ver seccion "[CERTAIN -- 2026-08-31, NUEVO...]" del
    docstring del modulo para la evidencia completa de decompilacion
    (Ghidra, `FUN_1800cdf14`/`FUN_1800ce1ec` de FlowXpert.xll, constantes
    confirmadas byte a byte con pefile). NO es una aproximacion basada solo
    en el texto del manual -- es la logica real decompilada, que ademas
    coincide 21/21 constantes con la tabla de la pagina 16 del manual ABB
    SpiritIT (`fxAGA8_C`) a la que el propio manual de AGA-10 remite.

    Mismo patron que `validar_rango_aga8()` (normas/AGA_8.py): informativo,
    NO bloqueante -- la app real tampoco bloquea el calculo por "Range" malo
    (solo lo marca), asi que esta funcion nunca levanta excepcion por rango,
    solo informa. Devuelve dict con:
      valido_entrada: True si T/P caen dentro del CAMPO DE ENTRADA propio de
          AGA-10 (0..2000 bar(a), -200..+400 degC -- paginas 9/10 del
          manual, MAS AMPLIO que el rango T/P de abajo). Informativo.
      rango_composicion: "Normal" / "Extendido" / "Fuera de rango (Expandido)"
          -- por fraccion molar de cada componente (o grupo), igual que
          `FUN_1800cdf14`.
      rango_pt: "Dentro de rango" / "Fuera de rango (T/P)" -- T en
          [-129,204] degC Y P en [0,1379] bar(a) (igual que `FUN_1800ce1ec`,
          BYTE-EXACTO con el gate ya usado en `validar_rango_aga8()`).
      rango_combinado: peor de los 2 anteriores ("Normal"/"Extendido"/
          "Fuera de rango") -- replica que un T/P malo FUERZA "Fuera de
          rango" sin importar la composicion, tal cual hace el binario real.
      mensaje: resumen legible.
    """
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion no puede sumar cero.")
    f = {nombre: composicion.get(nombre, 0.0) / total for nombre in NOMBRES_COMPONENTES}

    T_C = T_K - 273.15
    P_bar = P_kPa / 100.0

    # --- Campo de entrada propio de AGA-10 (paginas 9/10 del manual) --
    # MAS AMPLIO que el rango T/P de "Range" de abajo. Solo informativo
    # (no se decompilo el chequeo exacto que produce Status=1/FIOOR).
    valido_entrada = (-200.0 <= T_C <= 400.0) and (0.0 <= P_bar <= 2000.0)

    # --- Rango T/P para "Range" (FUN_1800ce1ec, decompilado) ---
    pt_normal = (-129.0 <= T_C <= 204.0) and (0.0 <= P_bar <= 1379.0)

    # --- Rango por composicion (FUN_1800cdf14, decompilado) ---
    butanos = f["Isobutano"] + f["n-Butano"]
    pentanos = f["Isopentano"] + f["n-Pentano"]

    fuera_de_normal = (
        not (0.45 <= f["Metano"] <= 1.0)
        or f["Etano"] > 0.10
        or f["Propano"] > 0.04
        or butanos > 0.01
        or pentanos > 0.003
        # [CERTAIN, decompilado] Hexanos+ se chequea POR COMPONENTE
        # INDIVIDUAL (no la suma del grupo, pese a como lo redacta el
        # manual) -- ver nota del docstring del modulo.
        or f["n-Hexano"] > 0.002 or f["n-Heptano"] > 0.002 or f["n-Octano"] > 0.002
        or f["n-Nonano"] > 0.002 or f["n-Decano"] > 0.002
        or f["CO"] > 0.03
        or f["CO2"] > 0.30
        or f["Nitrogeno"] > 0.50
        or f["Helio"] > 0.002
        or f["Argon"] > 0.0    # Normal exige Argon EXACTAMENTE 0
        or f["Oxigeno"] > 0.0  # Normal exige Oxigeno EXACTAMENTE 0
        or f["H2S"] > 0.0002
        or f["Hidrogeno"] > 0.10
        or f["Agua"] > 0.0005
    )

    dentro_de_expandido = (
        f["Metano"] <= 1.0 and f["Nitrogeno"] <= 1.0 and f["CO2"] <= 1.0
        and f["Etano"] <= 1.0 and f["Propano"] <= 0.12
        and butanos <= 0.06 and pentanos <= 0.04
        and f["Helio"] <= 0.03 and f["Hidrogeno"] <= 1.0 and f["CO"] <= 0.03
        and f["Argon"] <= 0.01
        and f["Oxigeno"] <= 0.21
        and f["H2S"] <= 1.0
        # [CERTAIN, decompilado] Hexanos+ y Agua NO tienen limite Expandido
        # real en el binario -- "Limit check is ignored for reason of
        # simplicity" (manual, pagina 16), confirmado en `FUN_1800cdf14`:
        # nunca se leen mas alla del chequeo Normal de arriba.
    )

    if not dentro_de_expandido:
        clas_composicion = "Fuera de rango (Expandido)"
    elif fuera_de_normal:
        clas_composicion = "Extendido"
    else:
        clas_composicion = "Normal"

    clas_pt = "Dentro de rango" if pt_normal else "Fuera de rango (T/P)"

    # --- Combinado: un T/P fuera de rango FUERZA "Fuera de rango" sin
    # importar la composicion (igual que el binario real). ---
    if clas_composicion == "Fuera de rango (Expandido)" or not pt_normal:
        rango_combinado = "Fuera de rango"
    elif clas_composicion == "Extendido":
        rango_combinado = "Extendido"
    else:
        rango_combinado = "Normal"

    mensaje = f"Composicion: {clas_composicion}. T/P: {clas_pt}. Range combinado: {rango_combinado}."
    if not valido_entrada:
        mensaje += (" ADEMAS, T/P esta fuera del campo de entrada propio de AGA-10 "
                    "(0..2000 bar(a), -200..+400 degC) -- la app real probablemente "
                    "ni siquiera aceptaria esta entrada (Status='Input argument out of range').")

    return {
        "valido_entrada": valido_entrada,
        "rango_composicion": clas_composicion,
        "rango_pt": clas_pt,
        "rango_combinado": rango_combinado,
        "mensaje": mensaje,
    }


def resolver_flujo_critico(T0_K: float, P0_kPa: float, x: list, max_iter: int = 60,
                            calcular_main: bool = True):
    """Resuelve el punto sonico real (garganta de tobera) para el gas de
    flujo (T0, P0), y devuelve el 'Critical flow factor (C*)' segun la
    definicion de NASA TM X-2308 (R.C. Johnson, 1971) -- ver docstring del
    modulo. Fisica: conservacion de entropia (isentropico) + conservacion
    de energia + condicion sonica (V*=W*), resuelta con AGA8-DETAIL.
    Confirmado <0.01% contra 2 casos reales.

    [CERTAIN, 2026-08-03] `Cstar_ideal`/`Cstar_real` son formulas cerradas
    (una sola evaluacion de AGA8-DETAIL en T0/P0) -- rapidas. `Cstar_main`
    en cambio necesita una busqueda de raiz ANIDADA (bisector de P* que
    llama, por cada evaluacion, a un bisector de T* que llama a
    DensityDetail/PropertiesDetail decenas de veces) -- perfilado: >55
    segundos de los ~74s totales que puede tomar
    `calcular_velocidad_sonido_y_fpv(calcular_flujo_critico=True)`, mas que
    el propio emulador Unicorn (~15s). Como `Cstar_main` solo se usa como
    FALLBACK cuando el emulador (que da el `critical_flow_factor` real,
    exacto) no esta disponible o falla, `calcular_main=False` permite
    saltarse toda esa busqueda cara y devolver solo lo que realmente hace
    falta en el camino rapido/normal (Cstar_ideal/Cstar_real, siempre
    necesarios para "Isentropic ideal/real C*", ademas de mostrarse
    aunque el emulador si funcione)."""
    D0, _, _ = DensityDetail(T0_K, P0_kPa, x)
    prop0 = PropertiesDetail(T0_K, D0, x)
    S0 = prop0["S_J_molK"]
    H0 = prop0["H_J_mol"]
    Mm = prop0["Mm_g_mol"]
    kappa0 = prop0["Kappa"]

    if not calcular_main:
        return {
            "Cstar_ideal": _cstar_ideal(kappa0),
            "Cstar_real": _cstar_real(kappa0, prop0["Z"]),
            "Cstar_main": None,
            "T_star": None, "P_star": None, "V_star": None, "W_star": None,
        }

    T_estrella_ideal = T0_K * 2.0 / (kappa0 + 1.0)
    P_estrella_ideal = P0_kPa * (2.0 / (kappa0 + 1.0)) ** (kappa0 / (kappa0 - 1.0))

    def _f_seguro(f, valor):
        # [CERTAIN, 2026-08-03] A T/P extremos (ej. T=400K/P=500bar con la
        # composicion "Default"), la busqueda de raiz de abajo puede
        # necesitar evaluar `f` en un T/P lejos del rango fisico razonable
        # antes de converger -- eso hace que AGA8-DETAIL (Alpha0Detail)
        # desborde `math.exp` (OverflowError: math range error), un crash
        # real encontrado por el usuario probando distintas combinaciones
        # de entrada. Se trata como "punto invalido" (NaN) en vez de dejar
        # que la excepcion se propague (o que un `None` legitimo de `f`
        # -- ej. cuando la busqueda INTERNA de T* ya fallo -- se compare
        # directo con `> 0`, que tambien crashearia): NaN nunca es > 0,
        # asi que el bisector/ensanchador simplemente descarta esa
        # direccion y sigue buscando (o falla de forma controlada
        # devolviendo None), en vez de tumbar todo el calculo.
        try:
            r = f(valor)
        except Exception:
            return float("nan")
        return float("nan") if r is None else r

    def _bisect(f, lo, hi):
        flo, fhi = _f_seguro(f, lo), _f_seguro(f, hi)
        if (flo > 0) == (fhi > 0):
            return None
        for _ in range(max_iter):
            m = 0.5 * (lo + hi)
            fm = _f_seguro(f, m)
            if (fm > 0) == (flo > 0):
                lo, flo = m, fm
            else:
                hi, fhi = m, fm
        return 0.5 * (lo + hi)

    def _ensanchar(f, centro, factor_inicial=0.05, pasos=25):
        delta = centro * factor_inicial
        for _ in range(pasos):
            lo, hi = max(centro - delta, centro * 0.01), centro + delta
            if (_f_seguro(f, lo) > 0) != (_f_seguro(f, hi) > 0):
                return lo, hi
            delta *= 1.6
        return None, None

    def _T_estrella_en_P(P_star):
        def f(T):
            D, _, _ = DensityDetail(T, P_star, x)
            prop = PropertiesDetail(T, D, x)
            return prop["S_J_molK"] - S0
        lo, hi = _ensanchar(f, T_estrella_ideal)
        if lo is None:
            return None
        return _bisect(f, lo, hi)

    def _estado_en_P(P_star):
        T_star = _T_estrella_en_P(P_star)
        if T_star is None:
            return None
        D_star, _, _ = DensityDetail(T_star, P_star, x)
        prop_star = PropertiesDetail(T_star, D_star, x)
        delta_H = (H0 - prop_star["H_J_mol"]) / Mm * 1000.0  # J/kg
        V_star = math.sqrt(delta_H) * math.sqrt(2.0) if delta_H > 0 else 0.0
        return T_star, D_star, prop_star, V_star, prop_star["W_m_s"]

    def g(P_star):
        r = _estado_en_P(P_star)
        if r is None:
            return None
        return r[3] - r[4]  # V_star - W_star

    lo, hi = _ensanchar(g, P_estrella_ideal)
    P_star = _bisect(g, lo, hi) if lo is not None else None
    resultado_estado = _estado_en_P(P_star) if P_star is not None else None

    if resultado_estado is None:
        # [CERTAIN, 2026-08-03] A T0/P0 extremos la busqueda puede no
        # converger (ver nota de `_f_seguro` arriba) -- se degrada a NaN
        # en vez de crashear con `TypeError` al desempacar `None`.
        T_star = P_star = V_star = W_star = None
        Cstar_main = float("nan")
    else:
        T_star, D_star, prop_star, V_star, W_star = resultado_estado
        rho_star = D_star * Mm  # kg/m3
        Rm = R_DETAIL * 1000.0 / Mm  # J/(kg K), constante especifica del gas
        G_star = rho_star * V_star  # kg/(m2 s), flujo masico por unidad de area
        Cstar_main = G_star * math.sqrt(Rm * T0_K) / (P0_kPa * 1000.0)

    return {
        "Cstar_ideal": _cstar_ideal(kappa0),
        "Cstar_real": _cstar_real(kappa0, prop0["Z"]),
        "Cstar_main": Cstar_main,
        "T_star": T_star, "P_star": P_star, "V_star": V_star, "W_star": W_star,
    }


def calcular_velocidad_sonido_y_fpv(composicion: dict, T_K: float, P_kPa: float,
                                      Tb_K: float = TB_DEFAULT_K, Pb_kPa: float = PB_DEFAULT_KPA,
                                      calcular_flujo_critico: bool = False):
    """FUNCION PRINCIPAL -- ver "GUIA DE USO PASO A PASO" al inicio del
    archivo para un ejemplo completo.

    Parametros:
        composicion: dict {nombre_componente: fraccion_o_porcentaje}, los
            21 nombres de `NOMBRES_COMPONENTES` en `normas/AGA_8.py`.
        T_K / P_kPa: temperatura (Kelvin) y presion (kPa absolutos) de
            FLUJO.
        Tb_K / Pb_kPa: temperatura/presion BASE/referencia (defaults:
            288.7056 K / 101.325 kPa) -- solo importan para `Fpv`.
        calcular_flujo_critico: bool, default False. En True activa el
            solver de `critical_flow_factor` (mas lento, intenta 2 caminos
            en cascada -- ver GUIA DE USO).

    Devuelve W (velocidad del sonido, m/s), Fpv = sqrt(Zb/Zf), densidades
    relativas (ideal y real) y propiedades termicas (Cp, Cv, Kappa) usando
    el motor AGA8-DETAIL ya confirmado. Validado contra caso real -- ver
    docstring del modulo."""
    x = _composicion_a_x(composicion)

    # [CERTAIN, 2026-08-31] "Range" real de fxAGA10ex_M -- ver
    # validar_rango_aga10() y la seccion nueva del docstring del modulo.
    # Informativo, NO bloqueante (viaja siempre con el resultado, igual que
    # aviso_bug_flowxpert_critical_flow).
    rango_aga10 = validar_rango_aga10(composicion, T_K, P_kPa)

    Df, ierr_f, _ = DensityDetail(T_K, P_kPa, x)
    prop_flujo = PropertiesDetail(T_K, Df, x)

    Db, ierr_b, _ = DensityDetail(Tb_K, Pb_kPa, x)
    prop_base = PropertiesDetail(Tb_K, Db, x)

    Zf = prop_flujo["Z"]
    Zb = prop_base["Z"]
    Fpv = (Zb / Zf) ** 0.5

    Mm = prop_flujo["Mm_g_mol"]
    rd_ideal = Mm / MM_AIRE
    prop_aire = calcular_propiedades(COMPOSICION_AIRE_SECO, T_K, P_kPa)
    Z_aire = prop_aire["Z"]
    rd_real = rd_ideal * (Z_aire / Zf)

    Cp_kJ_kgC = prop_flujo["Cp_J_molK"] / Mm
    Cv_kJ_kgC = prop_flujo["Cv_J_molK"] / Mm
    H0_kJ_kg = prop_flujo["H0_J_mol"] / Mm + _offset_h_kj_kg(x)
    H_kJ_kg = prop_flujo["H_J_mol"] / Mm + _offset_h_kj_kg(x)
    S_kJ_kgC = prop_flujo["S_J_molK"] / Mm + _offset_s_kj_kgc(x)
    Cp0_kJ_kgC = prop_flujo["Cp0_J_molK"] / Mm
    Cv0_kJ_kgC = prop_flujo["Cv0_J_molK"] / Mm

    # Campos adicionales de la pantalla real "AGA-10 (extended)" -- ver
    # capturas AGA 10 1-6.jpeg. [CERTAIN, 2026-07-24] Base/Flowing Density
    # en mol/m3 y kg/m3 son conversion directa de unidades (Db/Df ya
    # calculados arriba).
    #
    # [CERTAIN, 2026-08-03] Entalpia/Entropia/Cp/Cv arriba usan el offset
    # empirico por componente (rapido, fast path) como valor por defecto.
    # Cuando `calcular_flujo_critico=True` se sobreescriben con los offsets
    # 37-42 del struct de `AGA10::crit` (mismo emulador de Critical Flow),
    # que son EXACTOS (confirmados <0.0001% contra 7 casos reales, ver
    # `normas/_aga10_emulador.py`). Se habia descartado este camino antes
    # (misma fecha) por un falso negativo: `_aga10_emulador.py` tenia los
    # slots de entrada de flujo/base INVERTIDOS (bug real de este modulo,
    # no de FlowXpert, encontrado y corregido el mismo dia) -- con el bug
    # activo, offset 37 parecia seguir la base en vez del flujo. Corregido
    # el bug, offsets 37-42 SI siguen el flujo correctamente. Se reusa la
    # MISMA llamada que ya se hacia solo para Critical Flow (selector real
    # "Calculate (slow)") para ADEMAS sobreescribir H0/H/S/Cp0/Cp/Cv. Con
    # "Don't calculate (fast)" se mantienen los valores empiricos.
    #
    # Critical flow factor (C*) e Isentropic ideal/real C*: replica el
    # selector real "Critical Flow" (Don't calculate/fast vs Calculate/slow
    # -- el nombre real explica por que es opcional, el solver iterativo es
    # mas lento que el resto del calculo). Confirmado <0.01% contra 2 casos
    # reales con "Calculate" y 0.0 exacto contra 3 casos reales con
    # "Don't calculate". Ver resolver_flujo_critico() y docstring del modulo.
    Base_Density_mol_m3 = Db * 1000.0
    Flowing_Density_mol_m3 = Df * 1000.0
    Base_Density_kg_m3 = Db * Mm
    Flowing_Density_kg_m3 = Df * Mm

    if calcular_flujo_critico:
        # [CERTAIN, 2026-08-03] Cstar_main (formula fisica propia, solo se
        # usa como fallback si el emulador falla) es la parte CARA de
        # `resolver_flujo_critico()` (>55s de los ~74s totales medidos,
        # perfilado -- ver docstring de esa funcion). Se pide con
        # `calcular_main=False` (rapido, solo Cstar_ideal/Cstar_real) y
        # solo se recalcula completo (caro) dentro del `except` si
        # realmente hace falta -- asi el camino normal (emulador
        # disponible) queda acotado por el emulador (~15s), no por esta
        # formula descartada.
        _cf = resolver_flujo_critico(T_K, P_kPa, x, calcular_main=False)
        isentropic_ideal_Cstar = _cf["Cstar_ideal"]
        isentropic_real_Cstar = _cf["Cstar_real"]
        # [CERTAIN, 2026-08-26, AMPLIADO 2026-08-29] Camino PRIMARIO:
        # llamada DIRECTA (ctypes, sin Excel, SIN emulador de CPU) al
        # nucleo real dentro de FlowXpert.xll (ver
        # normas/_aga10_xll_directo.py) -- MISMO algoritmo/binario logico
        # que el emulador Unicorn del .so de Android, confirmado exacto
        # contra los 4 casos reales de test_aga10_caso_real.py, y desde
        # 2026-08-29 tambien confirmado en un BARRIDO AUTOMATIZADO de 109
        # combinaciones independientes de composicion/T/P contra el propio
        # emulador Unicorn (97/109 exactas, <1e-12% tipico) -- ver la
        # seccion "AUDITORIA EXHAUSTIVA 2026-08-29" en el docstring de
        # `_aga10_xll_directo.py` para el detalle completo. Este ya NO es
        # solo "el camino rapido con un respaldo por si acaso": dentro de
        # cualquier condicion real de medicion de gas (aprox. hasta
        # 100degC/200bar(a) para mezclas, y todo el rango normal para
        # componentes puros) la equivalencia con Unicorn quedo confirmada
        # mas alla de duda razonable, ademas de ~500-1000x mas rapido
        # (1-2 ms vs ~11-15 segundos por llamada). Las UNICAS discrepancias
        # reales encontradas (12/109, ver la auditoria) caen en
        # composiciones/T/P muy por fuera de cualquier operacion real
        # (componentes puros muy fuera del 'Expanded Range' de AGA-8, o
        # P/T en el borde literal 2000bar(a)/-200/+400degC del campo de
        # entrada) -- el emulador Unicorn se mantiene intacto, ya NO como
        # simple red de seguridad "por si la llamada directa falla en
        # alguna maquina", sino tambien como herramienta de auditoria/
        # segunda opinion para cualquier caso futuro que un usuario
        # reporte cerca de esos bordes. La decision de eliminarlo por
        # completo del proyecto sigue siendo del usuario, no se asume
        # aqui -- pero la evidencia para hacerlo con confianza, dentro del
        # rango real de uso, ya existe.
        _real = None
        _errores = []
        try:
            from . import _aga10_xll_directo as _a10x
            if _a10x.disponible():
                _slots0 = _a10x._composicion_a_slots0(composicion)
                _real = _a10x.calcular_aga10_crit_directo(_slots0, P_kPa * 1000.0, T_K)
                metodo_critical_flow = "xll_directo_exacto"
        except Exception as _err_xll:
            _errores.append(f"xll_directo: {_err_xll!r}")
            _real = None

        # [CERTAIN, 2026-08-31, NUEVO] Camino intermedio: porte a Python
        # PURO del solver `AGA10::crit` (`normas/_aga10_puro_python.py`),
        # sin depender de ningun binario/emulador -- solo usa AGA8-DETAIL
        # ya portado (este mismo modulo/`normas/AGA_8.py`). Se intenta
        # DESPUES de `.xll` directo y ANTES de Unicorn, NO primero, por
        # decision EXPLICITA basada en el barrido de validacion (ver
        # docstring de `_aga10_puro_python.py` y
        # `normas/_sweep_aga10_puro_python.py`): dentro del rango REAL de
        # medicion de gas (mezclas tipicas hasta ~100degC/200bar(a)) el
        # porte coincide 32/32 (100%) contra el oraculo `.xll directo`;
        # ampliando a cualquier condicion "Normal" segun `validar_rango_
        # aga10()` (incluye componentes puros y T/P menos tipicos) baja a
        # 18/21 (85.7%) -- los 3 residuos son EXACTAMENTE los mismos 3
        # casos (Default/GasRicoCO2/GasRicoN2 a 200degC/800bar(a)) que ya
        # se documentaron como "Normal segun el chequeo pero caoticos en la
        # practica" en la seccion "[CERTAIN -- 2026-08-31, NUEVO...]" de
        # arriba. Fuera de "Normal" (ej. componentes puros pesados a
        # 300degC/500bar, ya fuera del 'Expanded Range' oficial) el porte
        # puede no converger (NaN explicito, nunca un numero fabricado) --
        # tasa de exito mucho menor ahi (`.xll` directo, que ejecuta el
        # binario real, es estrictamente mas confiable en esa zona porque
        # no tiene una capa adicional de metodo numerico propio). Por eso
        # NO se pone primero pese a no necesitar el `.xll` -- el propio
        # criterio pedido ("no ponerlo primero si tiene mas fallos que el
        # camino directo") ya decide el orden.
        _cff_puro = None
        if _real is None:
            try:
                from . import _aga10_puro_python as _a10p
                _res_puro = _a10p.calcular_critical_flow_factor_puro(x, T_K, P_kPa)
                if _res_puro["convergio"]:
                    _cff = _res_puro["critical_flow_factor"]
                    if _cff == _cff:  # descarta NaN explicito sin importar 'convergio'
                        _cff_puro = _cff
                        metodo_critical_flow = "puro_python_newton"
                if _cff_puro is None:
                    _errores.append(f"puro_python: no convergio (rango_aga10={rango_aga10['rango_combinado']!r})")
            except Exception as _err_puro:
                _errores.append(f"puro_python: {_err_puro!r}")
                _cff_puro = None

        if _real is None and _cff_puro is None:
            # [CERTAIN, 2026-09-02 -- copia "NORMAS_AGA_GERG" (GitHub),
            # pedido explicito del usuario: "elimina las emulaciones"] Esta
            # copia del proyecto, pensada para despliegue sin dependencias
            # (web/Linux), NO incluye el respaldo via emulador Unicorn
            # (`_aga10_emulador.py`, requiere `pip install unicorn` + el
            # binario `.so` de Android) -- ese archivo fue retirado de este
            # repositorio a proposito. Solo quedan los 2 caminos que no
            # dependen de esa libreria: llamada directa a `FlowXpert.xll`
            # (opcional, solo funciona en Windows con el archivo presente) y
            # el porte Python puro (`_aga10_puro_python.py`, sin ninguna
            # dependencia binaria, funciona en cualquier plataforma). Si
            # ninguno de los 2 funciona para una entrada dada, se falla de
            # forma explicita en vez de devolver un numero que podria estar
            # mal sin que se note (misma filosofia de diseño que el proyecto
            # ya tenia antes de este cambio, ver commit_no_preguntar en la
            # memoria del proyecto principal).
            raise RuntimeError(
                "No se pudo ejecutar el algoritmo real de Critical Flow por "
                "ninguno de los 2 caminos disponibles en esta copia sin "
                "dependencias (llamada directa a FlowXpert.xll, o porte "
                "Python puro validado). El emulador Unicorn fue retirado "
                "deliberadamente de este repositorio. Por diseño, este "
                "sistema NO usa una formula aproximada de respaldo para "
                "este campo. Detalle: " + " | ".join(_errores)
            )

        if _real is not None:
            critical_flow_factor = _real["critical_flow_factor"]
            # Exactos (ver nota arriba) -- sobreescriben el offset empirico.
            H0_kJ_kg = _real["H0_kJ_kg"]
            H_kJ_kg = _real["H_kJ_kg"]
            S_kJ_kgC = _real["S_kJ_kgC"]
            Cp0_kJ_kgC = _real["Cp0_kJ_kgC"]
            Cp_kJ_kgC = _real["Cp_kJ_kgC"]
            Cv_kJ_kgC = _real["Cv_kJ_kgC"]
        else:
            # Camino puro_python: SOLO calcula critical_flow_factor (reusa
            # AGA8-DETAIL, no un struct completo del motor real) -- H0/H/S/
            # Cp0/Cp/Cv se DEJAN con el valor del offset empirico ya
            # calculado arriba (fast path, <0.006% de error ya validado),
            # no hay nada mejor que sobreescribirlos aqui.
            critical_flow_factor = _cff_puro
    else:
        critical_flow_factor = 0.0
        isentropic_ideal_Cstar = 0.0
        isentropic_real_Cstar = 0.0
        metodo_critical_flow = "no_solicitado"

    # Bug REAL confirmado en FlowXpert (2026-07-30, contra el dispositivo
    # real, ver normas/_aga10_emulador.py): Critical Flow Factor da un
    # numero sin sentido fisico (~87-89 en vez de ~0.5-0.8) cuando el gas
    # es casi puramente monoatomico (Kappa cercano a 5/3=1.6667). Este
    # campo viaja SIEMPRE con el resultado (no solo en la GUI) para que
    # cualquier consumidor de esta funcion (script, otra GUI, export a
    # Excel) se entere del problema sin depender de que alguien lea un
    # aviso visual. El umbral 1.6 es aproximado (confirmado roto desde
    # kappa=1.6626, confirmado normal en kappa=1.50 -- no se determino el
    # limite exacto entre esos dos puntos).
    aviso_bug_flowxpert_critical_flow = (
        "Kappa > 1.6 (gas casi monoatomico, ej. Helio/Argon): FlowXpert tiene un bug real "
        "confirmado que da un Critical Flow Factor sin sentido fisico (~87-89) en este rango. "
        "critical_flow_factor replica ese bug tal cual (no es un valor confiable)."
        if calcular_flujo_critico and prop_flujo["Kappa"] > 1.6 else None
    )

    # [CERTAIN, 2026-08-31] Aviso de "solver caotico" para critical_flow_factor
    # fuera de "Normal" -- ver seccion "VALIDACION CONTRA APP REAL 2026-08-31"
    # en el docstring de _aga10_xll_directo.py. Se probaron los 12 casos
    # exactos donde el camino directo .xll y el emulador Unicorn discrepaban
    # entre si, DIRECTO contra el proceso real de FlowXpert (Frida, sin tocar
    # la UI). Resultado: en TODOS los campos de estado (Z_flujo, Kappa, Mm, W,
    # H/S/Cp/Cv) el camino directo .xll coincidio con la app real casi bit a
    # bit en los 12/12 casos -- confirmando que .xll_directo (ya el camino
    # PRIMARIO, ver mas arriba) es el que hay que preferir, nunca Unicorn (que
    # dio critical_flow_factor=0.0 en 11/12 casos frente a un numero real no
    # nulo de la app, y Z_flujo/Kappa muy distintos incluso en el caso restante).
    # PERO especificamente critical_flow_factor (el ultimo campo que calcula
    # el solver iterativo, tras ~100 iteraciones de secante anidado) SI
    # diverge de forma real entre .xll y la app en 2 de esos 12 casos (hasta
    # ~35% de diferencia relativa: extremo:Default@15C/2000bar(a) y
    # extremo:Metano puro@15C/2000bar(a)) pese a que Z_flujo/Kappa coincidian
    # casi exactos -- el mismo mal condicionamiento numerico ya documentado
    # (perturbaciones del orden del ULP se amplifican tras el solver) afecta
    # tambien a xll-vs-app-real, no solo a xll-vs-Unicorn. [CORREGIDO,
    # 2026-08-31, misma fecha: una 3ra ronda de verificacion encontro que un
    # 4to caso que parecia divergir igual de fuerte (DryAir@200C/800bar(a),
    # ~80%) en realidad era un artefacto de la prueba, NO una divergencia
    # real -- la composicion usada en el hook de Frida sumaba 1.0001 en vez
    # de 1.0 exacto (sin renormalizar, a diferencia de esta funcion que
    # siempre renormaliza via `_composicion_a_slots0`); repitiendo la llamada
    # con la MISMA composicion sin normalizar, el camino directo SI reproduce
    # la app real a 7e-6% (ruido puro). Ver seccion "CORRECCION 2026-08-31"
    # en el docstring de `normas/_aga10_xll_directo.py` para el detalle
    # completo y reproducible.] Este aviso es honesto sobre la limitacion
    # real que SI queda (2 casos, no se puede "arreglar" sin recompilar):
    # fuera de "Normal", critical_flow_factor especificamente puede no ser
    # literalmente exacto a la app aun usando el camino preferido, aunque
    # siga siendo la mejor aproximacion disponible (mucho mejor que Unicorn,
    # que en el mismo barrido NUNCA coincidio con la app en estos 12 casos).
    aviso_critical_flow_fuera_de_normal = (
        f"Composicion/T/P fuera de 'Normal' (rango_aga10.rango_combinado="
        f"{rango_aga10['rango_combinado']!r}). Z_flujo/Kappa/W/H/S/Cp/Cv "
        "siguen siendo confiables (validado <0.0001% contra la app real vía "
        "Frida en 12 casos extremos, 2026-08-31), pero critical_flow_factor "
        "(Critical Flow C*) puede diverger de la app real hasta ~35% en esta "
        "zona (2 de los 12 casos probados) por mal condicionamiento numerico "
        "real del solver iterativo -- no es un bug de este software, es el "
        "mismo comportamiento caotico que tiene FlowXpert mismo aqui. Ver "
        "'VALIDACION CONTRA APP REAL 2026-08-31' y su 'CORRECCION 2026-08-31' "
        "en normas/_aga10_xll_directo.py."
        if calcular_flujo_critico and rango_aga10["rango_combinado"] != "Normal" else None
    )

    return {
        "W_m_s": prop_flujo["W_m_s"],
        "Z_flujo": Zf,
        "Z_base": Zb,
        "Fpv": Fpv,
        "Mm_g_mol": Mm,
        "D_flujo_mol_l": Df,
        "D_base_mol_l": Db,
        "D_base_mol_m3": Base_Density_mol_m3,
        "D_flujo_mol_m3": Flowing_Density_mol_m3,
        "D_base_kg_m3": Base_Density_kg_m3,
        "D_flujo_kg_m3": Flowing_Density_kg_m3,
        "rel_density_ideal": rd_ideal,
        "rel_density_real": rd_real,
        "Cp_kJ_kgC": Cp_kJ_kgC,
        "Cv_kJ_kgC": Cv_kJ_kgC,
        "Cp_kJ_kmolC": Cp_kJ_kgC * Mm,
        "Cv_kJ_kmolC": Cv_kJ_kgC * Mm,
        "Cp0_kJ_kgC": Cp0_kJ_kgC,
        "Cv0_kJ_kgC": Cv0_kJ_kgC,
        "Cp0_kJ_kmolC": Cp0_kJ_kgC * Mm,
        "Cv0_kJ_kmolC": Cv0_kJ_kgC * Mm,
        "H0_kJ_kg": H0_kJ_kg,
        "H_kJ_kg": H_kJ_kg,
        "S_kJ_kgC": S_kJ_kgC,
        "H0_kJ_kmol": H0_kJ_kg * Mm,
        "H_kJ_kmol": H_kJ_kg * Mm,
        "Kappa": prop_flujo["Kappa"],
        "Cp_Cv_ratio": prop_flujo["Cp_J_molK"] / prop_flujo["Cv_J_molK"],
        "critical_flow_factor": critical_flow_factor,
        "isentropic_ideal_Cstar": isentropic_ideal_Cstar,
        "isentropic_real_Cstar": isentropic_real_Cstar,
        "aviso_bug_flowxpert_critical_flow": aviso_bug_flowxpert_critical_flow,
        "aviso_critical_flow_fuera_de_normal": aviso_critical_flow_fuera_de_normal,
        "metodo_critical_flow": metodo_critical_flow,
        "ierr_flujo": ierr_f,
        "ierr_base": ierr_b,
        "rango_aga10": rango_aga10,
    }


if __name__ == "__main__":
    composicion = {
        "Metano": 0.77824, "Nitrogeno": 0.02, "CO2": 0.06, "Etano": 0.08,
        "Propano": 0.03, "Isobutano": 0.0015, "n-Butano": 0.003,
        "Isopentano": 0.0005, "n-Pentano": 0.00165, "n-Hexano": 0.00215,
        "n-Heptano": 0.00088, "n-Octano": 0.00024, "n-Nonano": 0.00015,
        "n-Decano": 0.00009, "Hidrogeno": 0.004, "Oxigeno": 0.005,
        "CO": 0.002, "Agua": 0.0001, "H2S": 0.0025, "Helio": 0.007,
        "Argon": 0.001,
    }
    print("=== normas/AGA_10.py -- autotest ===")
    r = calcular_velocidad_sonido_y_fpv(composicion, 400.0, 50000.0)
    for k, v in r.items():
        print(f"  {k} = {v}")
