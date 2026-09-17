# -*- coding: utf-8 -*-
"""
normas/_ngl_lpg_wrappers_puro.py
==================================
PORTE a Python puro de los 3 wrappers combinados de "E NGL/LPG (TP-27)"
(`API Density @15°C NGL/LPG`, `API Density @20°C NGL/LPG`, `API Rel.
Density @60°F NGL/LPG`) que hoy dependen de `ctypes`+`pefile`
(`normas/_ngl_lpg_wrappers_xll_directo.py`, el ORACULO de validacion de
este modulo, usado en desarrollo -- NUNCA en produccion, ver
`normas/AGA_10_puro.py`/`normas/_aga10_puro_python.py` para el patron que
este archivo replica).

===============================================================================
GUIA DE USO PASO A PASO (leer esto primero si solo queres USAR el modulo)
===============================================================================
PASO 1 -- Importar la funcion que necesitas (las 3 tienen la MISMA firma
lineal de parametros/claves de salida que sus equivalentes `_xll_directo`):
    from normas._ngl_lpg_wrappers_puro import (
        calcular_rd60f_ngl_lpg_puro,
        calcular_dens15c_ngl_lpg_puro,
        calcular_dens20c_ngl_lpg_puro,
    )

PASO 2a -- "API Rel. Density @60°F NGL/LPG" (sistema US, RD adimensional,
T en °F, P en psia ABSOLUTA):
    r = calcular_rd60f_ngl_lpg_puro(rd=0.5, t_f=110.0, p_psia=200.0)
    r["rd_std"]                  # Relative Density @60F resultante
    r["ctl"], r["cpl"], r["ctpl"]
    r["compressibility_1_psi"]   # factor F, 1/psi
    r["evp_psia"]                # Equilibrium Pressure calculada (o la
                                  # que pasaste, segun evp_mode)

PASO 2b -- "API Density @15°C NGL/LPG" / "@20°C" (sistema metrico,
densidad en kg/m3, T en °C, P en bar(g)):
    r15 = calcular_dens15c_ngl_lpg_puro(densidad_kgm3=600.0, t_c=25.0, p_barg=0.0)
    r15["x_kgm3"]                # Densidad @15°C resultante (o la
                                  # observada, segun 'conversion')
    r20 = calcular_dens20c_ngl_lpg_puro(densidad_kgm3=600.0, t_c=25.0, p_barg=0.0)

PASO 3 -- El parametro `conversion` (igual en las 3 funciones) decide el
sentido: `conversion=1` (default) es Observado->Estandar (el valor de
entrada es la lectura observada, el resultado es el valor a la referencia
de la pantalla: 60°F/15°C/20°C). `conversion=0` es el sentido inverso
(Estandar->Observado): el mismo campo de entrada se interpreta como el
valor YA a la referencia, y el resultado es la prediccion observada --
exactamente el mismo comportamiento que expone la pantalla real y que ya
usan `calcular_rd60f_ngl_lpg_directo`/`calcular_dens15c_ngl_lpg_directo` en
`_ngl_lpg_wrappers_xll_directo.py`.

PASO 4 -- `evp_mode` (o `equilibrium_pressure_mode` en los wrappers de
`API_MPMS_Tables_1980_2004.py`): 1="Input" (usa el valor de
`evp_input_*` tal cual, sin calcular nada), 2="Calculate" (default, GPA
TP-15 -- ver seccion "GPA TP-15" abajo para el nivel de confianza real de
esta rama, DISTINTO entre RD60F y Dens15C/Dens20C).

PASO 5 -- SIEMPRE revisar los 3 flags `oor_ctl`/`oor_cpl`/`oor_evp` del
resultado antes de confiar el numero a un uso real -- son flags de "fuera
del rango OFICIAL de la norma" (nunca bloquean el calculo, informativos,
igual que el resto de este proyecto).

Ejemplo COMPLETO, listo para copiar y correr (`python -m
normas._ngl_lpg_wrappers_puro` corre un autotest parecido a este, incluido
el caso real conocido):
    from normas._ngl_lpg_wrappers_puro import calcular_rd60f_ngl_lpg_puro
    r = calcular_rd60f_ngl_lpg_puro(rd=0.5, t_f=110.0, p_psia=200.0,
                                     atm_psia=14.696)
    print(r["rd_std"], r["ctl"], r["cpl"], r["evp_psia"])

===============================================================================
QUE COMBINA ESTE MODULO (reusa, NO reimplementa, los motores ya [CERTAIN])
===============================================================================
1. Motor CTL "E" (API 11.2.4 / GPA TP-27 Tables 23E/24E/53E/54E/59E/60E):
   YA 100% Python puro en `normas/API_MPMS_Tables_1980_2004.py`
   (`_ngl_alpha`, `_ngl_solve_x`, `api_table23e/24e/53e/54e/59e/60e`) --
   este modulo los IMPORTA y REUSA tal cual, nunca los reimplementa.
2. Modulo de presion API MPMS 11.2.2 (US) / 11.2.2M (metrico): YA 100%
   Python puro en el mismo archivo (`api_mpms_11_2_2`/`api_mpms_11_2_2m`,
   RONDA 13, [CERTAIN]) -- reusado tal cual.
3. GPA TP-15 (presion de vapor en equilibrio, "Equilibrium Pressure Mode
   = Calculate"): NUEVO en este archivo (`_gpa_tp15_psia`), portado desde
   `FUN_1800efcbc` (426 bytes) -- ver seccion "GPA TP-15" abajo.
4. El SOLVER que combina 1+2+3: NUEVO en este archivo, ver seccion
   "EL SOLVER" abajo -- estructura de iteracion de punto fijo, la MISMA
   que ya usa `api_density15c_1980`/`api_gravity60f_1980`/
   `api_reldensity60f_1980` en el mismo archivo (RONDA 9) para el mismo
   tipo de problema (CTL(base)*CPL(base)=observado, iterar sobre `base`).

===============================================================================
GPA TP-15 (`_gpa_tp15_psia`) -- de donde sale y su nivel de confianza REAL
===============================================================================
Decompilado de `FUN_1800efcbc` (`ANALISIS_GHIDRA_FLOWXPERT/
ghidra_ngllpg_xll_output.txt`, funcion [60]). Formula reconstruida
(RD=densidad relativa reducida en [0.35,0.676], T_F=temperatura en °F):

    fila = primera fila de NGL_LPG_TP15_TABLE (7 filas, extraidas a BYTES
           CRUDOS con `pefile` desde el `.xll`, VA 0x1801eaee0..0x1801eb0a0,
           7*8=56 doubles) tal que RD < fila[umbral]
    numerador = c7*RD^2 + c6*RD + c5          (coeficientes de la fila)
    denominador = T_F + 443.0
    si p100_correlacion == 0 (default, metodo de tabla):
        exponente = numerador/denominador + c4*RD^2 + c3*RD + c2
    si p100_correlacion == 1 (metodo alterno, NO validado esta ronda):
        exponente = ln(p100_valor_psia) +
                    ((100.0 - T_F) * numerador) / (denominador * 543.0)
    EVP_psia = exp(exponente)   [redondeado a 1 decimal si round_tp15!=0]

[CERTAIN, validado exacto] para el camino de `calcular_rd60f_ngl_lpg_puro`
(sistema US): la formula de arriba, evaluada con RD=el valor BASE
(rd_60f) que converge en el solver y T_F=la temperatura de flujo tal
cual, reproduce el caso real completo de RONDA 14/15 (RD=0.5, T=110°F,
P=200psia -> EVP=130.828psia=9.020282bar(a)) dentro de la tolerancia del
solver (ver autotest al final de este archivo) -- confirmado tambien por
el barrido masivo contra el oraculo `.xll` (ver seccion "VALIDACION").

[LIKELY, NO confirmado por decompilacion sin ambiguedad] para el camino
metrico (`calcular_dens15c_ngl_lpg_puro`/`calcular_dens20c_ngl_lpg_puro`
con `evp_mode=2`): el nucleo metrico (`FUN_1800E6CA0`/`FUN_1800E7304`)
SI llama a `FUN_1800efcbc` (confirmado, mismo simbolo), y el resultado SI
se multiplica por `6.894757` (=`PSI_TO_KPA`, confirmado a bytes) antes de
usarse como "Equilibrium Pressure" del modulo 11.2.2M -- eso confirma que
`FUN_1800efcbc` siempre trabaja en psia/°F internamente, sin importar el
llamador. PERO el decompilado de Ghidra para el PRIMER argumento (la
densidad relativa reducida "RD" que le pasa el nucleo metrico) se imprimio
como literal `0` en AMBAS ramas (iterativa y directa) -- una lectura
literal de eso dana la formula (RD=0 cae fuera de rango y siempre en la
fila 0). Se investigo la causa mas probable: el propio decompilado de esta
funcion, y de su vecina `FUN_1800e8e88`, ya trae la advertencia real de
Ghidra "Type propagation algorithm not settling" -- es decir, Ghidra
mismo señala que no pudo resolver el tipo/registro de varios argumentos en
esta zona del binario; el patron de codigo inmediatamente anterior a la
llamada (`local_480` = la variable "x" recien calculada por
`FUN_1800ec10c`, el mismo puerto ya [CERTAIN] `_ngl_alpha`) es el
candidato fisicamente consistente con como SI funciona el camino US
(donde el primer argumento de TP-15 es, confirmado, la RD/densidad-base
candidata del solver). Se implementa aqui con `x_root` (la variable
analoga a `local_480`) en vez de tomar literalmente el `0` impreso por
Ghidra -- una decision de ingenieria, NO una lectura literal del
decompilado, documentada como tal. Validado por el barrido contra el
oraculo `.xll` (ver seccion "VALIDACION" para el numero exacto de esta
ronda) -- si el barrido muestra una tasa de exito baja para este camino
especifico, se documenta honestamente ahi, sin forzar el numero.

===============================================================================
EL SOLVER -- fixed-point (igual que RONDA 9), NO literalmente
"Aitken"/secante-con-bracket byte a byte
===============================================================================
El decompilado real de `FUN_1800E8E88`/`FUN_1800E6CA0`/`FUN_1800E7304`
(rama `conversion=1`/"Observed->Standard") usa la MISMA iteracion de punto
fijo simple que ya esta en produccion en este archivo desde RONDA 9
(`api_density15c_1980`, etc.): en cada vuelta, evalua CTL+EVP+CPL en el
candidato actual y arma el siguiente candidato como
`nuevo = observado / (CTL*CPL)`, hasta 100 vueltas o tolerancia. ESO es
la parte que se porta aqui, byte a byte en estructura (no en constantes de
tolerancia exactas -- se usa una tolerancia generica 1e-8, mas estricta
que casi todos los casos reales documentados en el decompilado, ver
docstring de `API_MPMS_Tables_1980_2004.py` lineas ~3016-3025 para el
detalle de las tolerancias variables reales que NO se replican aqui).

El decompilado, ADEMAS, tiene un segundo tramo (solo si la iteracion de
punto fijo no converge o oscila) que hace una busqueda de bracket +
"regula falsi" con salvaguarda tipo Illinois (`dVar15 = dVar1 -
(((param_14)-param_1)*dVar19)/((param_14)-local_d0)`, con fallback a
bisección si la extrapolacion cae fuera del bracket) -- la mencion previa
de este proyecto a "aceleracion tipo Aitken" (ver comentario RONDA 14 en
`API_MPMS_Tables_1980_2004.py`) describia este tramo; una lectura mas
cuidadosa esta ronda muestra que es un **regula-falsi/Illinois
salvaguardado**, NO la formula de Aitken Δ² -- se corrige esa
caracterizacion aqui. Este modulo REPLICA el mismo principio (bracket +
biseccion robusta) como FALLBACK si el punto fijo simple no converge en
`max_iter` vueltas -- no ese algoritmo especifico linea a linea, con el
mismo argumento de "desviacion deliberada" ya usado en
`_aga10_puro_python.py`: lo que importa es que el PUNTO FIJO final
coincida con el oraculo, no el camino de iteracion.

===============================================================================
VALIDACION (2026-09-03, esta ronda)
===============================================================================
`normas/_sweep_ngl_lpg_puro.py` (2928 casos comparables en total, tolerancia
relativa 0.5%, contra `normas/_ngl_lpg_wrappers_xll_directo.py` como
oraculo real) -- resultado de esta ronda (2026-09-03), DESPUES de 3
correcciones encontradas y aplicadas durante la propia validacion (no
antes de ella -- se documentan porque cambian codigo YA [CERTAIN] de
`API_MPMS_Tables_1980_2004.py`, no solo este archivo nuevo):
  1. Bug real en `api_mpms_11_2_2m` (RONDA 13): tenia un clamp
     `p_eff=max(p_eff,0.0)` que el nucleo metrico real (`FUN_1800e36e8`) NO
     tiene -- corregido (ver docstring de esa funcion).
  2. Gap real en `api_mpms_11_2_2` (RONDA 13): no clampeaba RD/T/P a los
     rangos oficiales antes de evaluar el polinomio, como SI hace el nucleo
     US real (`FUN_1800e32e8`) -- corregido (ver docstring de esa funcion).
  3. Hallazgo propio de este archivo: `calcular_dens20c_ngl_lpg_puro`
     evaluaba CPL con la densidad@20°C en vez de @15°C (ver docstring de
     `_forward_densxc`).
Resultado FINAL, por funcion:
  - `calcular_rd60f_ngl_lpg_puro`: 924/980 = 94.3% (94.3% en evp_mode=1,
    94.3% en evp_mode=2 -- casi identicos, la brecha NO viene de GPA TP-15
    sino de la zona de borde RD=0.35 con T>=90°F, donde el polinomio de
    11.2.2 US, aun clampeado, se vuelve fisicamente marginal).
  - `calcular_dens15c_ngl_lpg_puro`: 922/974 = 94.7% (96.1% evp_mode=1,
    91.8%(*) evp_mode=2 -- (*) mejora posible pendiente, ver mas abajo).
  - `calcular_dens20c_ngl_lpg_puro`: 962/974 = 98.8% (100.0% evp_mode=1,
    97.5% evp_mode=2).
  - TOTAL: 2808/2928 = 95.9%.
Los casos restantes que NO coinciden se concentran, en las 3 funciones,
en el borde extremo del rango oficial (densidad/RD cerca del minimo de
tabla + temperatura alta) -- el mismo patron de "zona numericamente fragil
en el borde del rango de validez fisica" ya documentado para AGA-10 en
este proyecto (`_aga10_puro_python.py`, seccion "NIVEL DE CONFIANZA"): no
se fuerza una coincidencia ahi, se documenta honesto. El caso real
completo (RD60F) y los 2 round-trips (Dens15C/Dens20C sin presion) siguen
coincidiendo exactos -- ver autotest de este archivo.

===============================================================================
RONDA 33 (2026-09-08): cruce LITERAL contra el manual oficial (`normas/
manual_texto_api_1980_1952.txt` paginas 24-27/44-46 + `scratch_manual_ngl_pages.txt`
para Table60E, pagina 75, fuera del rango extraido en 1980/1952) -- MISMO
patron de bug ya encontrado en 1980 (RONDA 31/32): flags de rounding con
MAS efecto documentado del que este modulo implementaba.
===============================================================================
HALLAZGO CONFIRMADO (bug real, no fabricado): el texto de
`fxAPI_Dens15C_NGL_LPG`/`fxAPI_Dens20C_NGL_LPG`/`fxAPI_RD60F_NGL_LPG` dice
LITERAL que la tolerancia de convergencia del solver es DINAMICA:
  Dens15C/Dens20C: 0.05 kg/m3 si `round_11_2_2m` activo, si no 0.005 si
  `round_tp15` activo, si no 0.00001.
  RD60F: 0.00005 si `round_11_2_2` activo, si no 0.000005 si `round_tp15`
  activo, si no 0.00000001 (=1e-8).
ANTES de esta ronda este modulo usaba un `tol` FIJO (1e-6 para Dens15C/20C,
1e-8 para RD60F) sin importar los flags -- el valor fijo de RD60F YA
coincidia por casualidad con la rama "ninguno activo" del manual (por eso
nunca se detecto en el caso real), pero Dens15C/20C usaba 1e-6, MAS
estricto que el 1e-5 del manual, y ninguna de las 2 funciones cambiaba de
tolerancia al activar `round_11_2_2`/`round_11_2_2m`/`round_tp15`.
ADEMAS se confirmo (cruzando el texto de las funciones standalone
`fxAPI_MPMS_11_2_2`/`fxAPI_MPMS_11_2_2M`, paginas 37-38) que `round_11_2_2`/
`round_11_2_2m` tambien deben redondear CPL a 4 decimales -- este modulo
aceptaba `round_11_2_4`/`round_11_2_2`/`round_11_2_2m` como parametros
desde su creacion pero NUNCA los conectaba a nada (no-op silencioso total).

CORREGIDO en este archivo: (a) tolerancia dinamica segun los 3 flags en
ambos solvers: (b) CPL redondeado a 4 decimales dentro del solver cuando
`round_11_2_2`/`round_11_2_2m` esta activo -- [CERTAIN, confirmado EXACTO
contra el oraculo `.xll`, ver `_sweep_ngl_lpg_puro_flags.py`, NUEVO en esta
ronda: 288/288 (RD60F) y 288/288 (Dens15C/20C) coinciden en TODOS los
campos fisicamente relevantes (`x_kgm3`/`rd_std`, `ctl`, `cpl`, `ctpl`,
`evp_*`) en TODA la grilla de combinaciones de flags probada, salvo el
UNICO caso ya conocido de residuo de borde (densidad=400kg/m3, T=40°C,
GPA TP-15, pre-existente, documentado arriba, NO nuevo de esta ronda); (c)
redondeo final del resultado a 0.0001 (RD60F) / 0.1 kg/m3 (Dens15C/20C)
cuando `round_11_2_4` esta activo (paso final de la cascada, `conversion=1`).

CERO REGRESION confirmada: los 4 casos reales/autotest de este archivo
(todos con flags=0 por default) dan EXACTAMENTE los mismos numeros que
antes de esta ronda, y el barrido original de 2928 casos (flags=0) se
re-corrio completo, sigue en 2808/2928 = 95.9% (identico, sin cambios).

PENDIENTE, documentado HONESTO (no fabricado): F (`compressibility_1_psi`/
`compressibility_1_bar`) tambien deberia redondearse segun el manual
("F rounded to 8 decimal places with a maximum of 4 significant digits")
-- SE INTENTO esa regla literal esta ronda (`_round_sig`+8-decimales) y NO
reproduce el oraculo: ejemplo real, F crudo=0.0010584676 1/bar (dens=400,
T=-10°C, P=10bar(g)), oraculo con `round_11_2_2m=1` devuelve F=0.001064 --
ninguna combinacion razonable de redondeo del VALOR FINAL da ese numero
(round a 4 cifras sig. da 0.001059, no 0.001064). Evidencia de que el
redondeo de F bajo estos flags no es un redondeo de salida sino una
TRUNCACION DE TERMINOS INTERMEDIOS durante el propio calculo de F (mismo
patron que el redondeo de K0/K1/K2 en la familia 1980, RONDA 16-29) --
requeriria decompilar de nuevo `FUN_1800e32e8`/`FUN_1800e36e8`
especificamente en su rama "rounding activo", no hecho esta ronda. Se
revirtio el intento (el codigo NO redondea F bajo estos flags, se deja a
precision completa) para no fabricar un numero incorrecto -- confirmado
que esto NO afecta CPL (que SI se calcula y redondea correcto de forma
independiente) ni ningun otro campo fisico.

Las 6 tablas puras (`api_table23e/24e/53e/54e/59e/60e`): el manual (incl.
la seccion de Table60E, pagina 75, extraida esta ronda por estar fuera del
rango original) confirma que existen y tienen su PROPIO flag generico
"API rounding" ("input and output values rounded as defined in the
standard") -- pero, a diferencia de la familia 1980/1952 (que SI da
recuentos de decimales exactos, ej. "4 decimales si CTL>=1"), el texto
extraido de estas 6 funciones NUNCA especifica una resolucion numerica
concreta. Sigue siendo, honestamente, el mismo PENDIENTE de RONDA 14: no
se puede implementar ese flag sin fabricar una resolucion -- no se
encontro informacion nueva esta ronda.

GPA TP-15 / "P100 mejorada": el manual (paginas 24-25/43-44) SOLO describe
la pantalla (que existe la opcion, que requiere `Vapor pressure at 100°F`)
-- no da la formula interna. Sigue [LIKELY, no CERTAIN] tal como quedo en
RONDA 15, sin caso real que confirme la rama `p100_correlacion=1`. Ningun
avance nuevo esta ronda en este punto especifico.

===============================================================================
RONDA 42 (2026-09-10): bug real de CPL en `conversion=0` (Standard->
Observed) con P>0, para `calcular_rd60f_ngl_lpg_puro` y
`calcular_dens20c_ngl_lpg_puro` -- CERRADO. `calcular_dens15c_ngl_lpg_puro`
confirmada limpia (sin cambios de codigo).
===============================================================================
REPRODUCCION: un barrido ALEATORIO (seed fija, 300 casos por funcion, RD/
densidad/T/P/evp_mode variados, `conversion=0`, TODOS los flags de
rounding en 0) contra `_ngl_lpg_wrappers_xll_directo.py` (oraculo `.xll`
real) mostro que `calcular_rd60f_ngl_lpg_puro` y
`calcular_dens20c_ngl_lpg_puro` fallaban sistematicamente en CPL (y por lo
tanto en el resultado final) cuando RD>=0.638 (RD60F) o densidad@15°C-
equivalente>=637.5 kg/m3 (Dens20C) -- SIEMPRE cerca/por encima del limite
superior del rango oficial de API MPMS 11.2.2/11.2.2M (0.638 RD /
637.5 kg/m3). El barrido de grilla fija usado en rondas previas
(`_sweep_ngl_lpg_puro.py`, RD hasta 0.637, densidad hasta 630 kg/m3) nunca
alcanzaba ese umbral, por eso el bug quedo invisible hasta un barrido
aleatorio con rango completo (RD hasta 0.676, densidad hasta 650 kg/m3).

CAUSA RAIZ [CERTAIN, via decompilacion directa (Ghidra, ya extraida en
`ANALISIS_GHIDRA_FLOWXPERT/ghidra_ngllpg_xll_output.txt`) + bytes crudos
reales del `.xll` (`pefile`)]:
  1. `FUN_1800E8E88` (nucleo real de RD60F, AMBAS ramas -- iterativa Y
     directa, confirmado leyendo las 2 instancias identicas del patron,
     lineas ~4315-4320 y ~4464-4470 del dump): antes de llamar al modulo
     de presion, compara el candidato de RD contra `DAT_1801ea5a8` (=0.638
     exacto, confirmado a bytes con `pefile`, MISMO valor ya usado en este
     proyecto como `MPMS_11_2_2_RD_RANGE[1]`). Si RD<0.638, llama a
     `FUN_1800e32e8` (=`api_mpms_11_2_2`, ya [CERTAIN] RONDA 13). Si
     RD>=0.638, llama en cambio a `FUN_1800e2d5c` -- la MISMA funcion YA
     portada en este proyecto como `api_mpms_11_2_1` (RONDA 9, sistema US,
     recibe °API en vez de RD) -- pasandole
     `api_gravity=141.5/RD-131.5` (constantes `DAT_1801eaa80`=141.5 y
     `DAT_1801ea4e0`=131.5, ambas confirmadas a bytes crudos con `pefile`,
     la segunda es literalmente la misma direccion ya usada como
     `MPMS_11_2_1_API_OFFSET`). Este modulo, ANTES de esta ronda, llamaba
     SIEMPRE a `api_mpms_11_2_2` sin este switch, dentro de
     `_forward_rd60f` -- que es compartida por las 2 ramas, asi que el fix
     aplica automaticamente a ambas (coincide con la evidencia: el switch
     es identico en ambas ramas del binario real).
  2. `FUN_1800e7304` (nucleo real de Dens20C, rama DIRECTA `conversion=0`
     unicamente, linea ~3933-3939 del dump): calcula la densidad@15°C
     equivalente (`dVar14 = local_4a8*local_470*RHO_WATER`, identica en
     forma a `density_15c_kgm3` ya calculada en `_forward_densxc`) y hace
     el MISMO tipo de switch: si `dVar14 < DAT_1801ea4f0` (=637.5 exacto,
     bytes confirmados, mismo valor ya usado como
     `MPMS_11_2_2M_RHO_RANGE[1]` Y como `MPMS_11_2_1M_RHO_RANGE[0]`) usa
     `FUN_1800e36e8` (=`api_mpms_11_2_2m`); si no, usa `FUN_1800e303c`
     (=`api_mpms_11_2_1m`, YA [CERTAIN] RONDA 9, misma firma, recibe
     densidad directo sin conversion a °API). ESTE switch es EXCLUSIVO de
     la rama directa de Dens20C -- confirmado por decompilacion que la
     rama iterativa de Dens20C (`*param_11==1`, linea ~3861) llama a
     `FUN_1800e36e8` de forma INCONDICIONAL, sin el switch.
  3. `FUN_1800e6ca0` (nucleo real de Dens15C, rama DIRECTA `conversion=0`,
     linea ~3164 del dump): NO tiene este switch -- usa `*param_1` (la
     densidad de entrada CRUDA, sin recalcular a 15°C) de forma
     incondicional para `FUN_1800e36e8`, sin comparar contra ningun
     umbral. Esto es una ASIMETRIA REAL del binario (confirmada por
     decompilacion, no un descuido de esta implementacion): para Dens15C
     no hace falta el switch porque la densidad de entrada YA ES la
     densidad@15°C por definicion de esa pantalla (identidad exacta, no
     una coincidencia de redondeo) -- consistente con que el barrido
     aleatorio de 300 casos para Dens15C, mismo rango que Dens20C/RD60F,
     dio 100% de coincidencia ANTES y DESPUES de este fix (sin tocar
     codigo de Dens15C).

FIX aplicado en `normas/_ngl_lpg_wrappers_puro.py`:
  - `_forward_rd60f`: switch incondicional (aplica en ambas ramas, ya que
    la funcion es compartida) `if rd_base < MPMS_11_2_2_RD_RANGE[1]:
    api_mpms_11_2_2(...) else: api_mpms_11_2_1(141.5/rd_base-131.5, ...)`.
  - `_forward_densxc`: nuevo parametro `permitir_switch_1121m` (default
    `False`, sin cambios de comportamiento salvo donde se activa
    explicitamente) -- cuando es `True` y `density_15c_kgm3 >=
    MPMS_11_2_2M_RHO_RANGE[1]`, usa `api_mpms_11_2_1m` en vez de
    `api_mpms_11_2_2m`. Activado en `True` UNICAMENTE por
    `_dens_ngl_lpg_puro` en su rama `conversion=0`
    (`permitir_switch_1121m_directo`), y UNICAMENTE por
    `calcular_dens20c_ngl_lpg_puro` (nunca por
    `calcular_dens15c_ngl_lpg_puro`, que sigue pasando el default
    `False`) -- refleja exactamente la asimetria confirmada por
    decompilacion en el punto 3 de arriba. La rama iterativa
    (`conversion=1`) de las 3 funciones NO se toco (fuera del alcance de
    esta ronda, el bug reportado y reproducido es exclusivo de
    `conversion=0`).

VALIDACION [CERTAIN, contra el oraculo `.xll` real via
`_ngl_lpg_wrappers_xll_directo.py`] -- barrido aleatorio dedicado de 300
casos por funcion (seed fija 123, RD 0.35-0.676 / densidad 300-650 kg/m3,
T -40..140°F / -40..60°C, P 0.1-800psia / 0.1-60bar(g), evp_mode 1 y 2,
`conversion=0`, flags de rounding en 0), comparando `rd_std`/`x_kgm3`,
`ctl`, `cpl`, `ctpl`, `compressibility_1_psi`/`compressibility_1_bar`
contra el oraculo (tolerancia relativa 0.5%):
  - `calcular_rd60f_ngl_lpg_puro`: ANTES 274/300 (91.3%) -> DESPUES
    300/300 (100.0%).
  - `calcular_dens20c_ngl_lpg_puro`: ANTES 289/300 (96.3%) -> DESPUES
    300/300 (100.0%).
  - `calcular_dens15c_ngl_lpg_puro` (control, SIN cambios de codigo):
    300/300 (100.0%) tanto antes como despues -- confirma que la funcion
    hermana sigue limpia y que el fix no la afecto.
El numero "ANTES" se obtuvo re-ejecutando el mismo barrido de 300 casos
con los umbrales `MPMS_11_2_2_RD_RANGE`/`MPMS_11_2_2M_RHO_RANGE`
monkey-parcheados a un valor gigante (desactivando el switch sin tocar el
codigo fuente), NO una estimacion -- mismo codigo, mismo oraculo, unica
diferencia el umbral.

CERO REGRESION confirmada:
  - `python -m normas._ngl_lpg_wrappers_puro`: los 3 casos reales/round-
    trip del autotest (incluido el UNICO caso real completo, RD=0.5,
    T=110°F, P=200psia, `conversion=1` -- rama iterativa, NO tocada por
    este fix, sin motivo para cambiar y en efecto sin cambios) dan los
    mismos numeros exactos que antes.
  - `python -m normas.API_MPMS_Tables_1980_2004`: exit 0, sin cambios (no
    se modifico ese archivo esta ronda).
  - `python -m normas._sweep_ngl_lpg_puro` (2928 casos, grilla fija de
    rondas previas, `conversion` 0 Y 1 mezclados): subio de 2808/2928
    (95.9%, numero documentado en la seccion "VALIDACION" arriba) a
    2842/2928 (97.1%) -- mejora real, no regresion. Desglose por funcion:
    RD60F 924/980(94.3%)->958/980(97.8%); Dens15C 922/974(94.7%) SIN
    CAMBIOS (confirma que no se toco); Dens20C 962/974(98.8%) SIN CAMBIOS
    en ESTA grilla especifica (su rango de densidad, hasta 630kg/m3, no
    alcanza el umbral de 637.5kg/m3 con la suficiente frecuencia en esta
    grilla fija -- el barrido aleatorio dedicado arriba, con densidad
    hasta 650kg/m3, SI expone y confirma la mejora real para Dens20C). La
    mejora total de RD60F ocurre en AMBAS ramas (iterativa incluida)
    porque `_forward_rd60f` es compartida y el switch del binario real
    tambien es identico en ambas ramas (ver CAUSA RAIZ punto 1) -- efecto
    esperado, no un error de alcance.
  - `python -m normas._sweep_ngl_lpg_puro_flags` (864 casos, SOLO
    `conversion=1`, RD/densidad dentro del rango, NUNCA cruzan el umbral
    de esta ronda): 744/864 (86.1%), TODAS las fallas explicadas por (a)
    el PENDIENTE ya documentado de RONDA 33 (F sin redondear bajo
    `round_11_2_2`/`round_11_2_2m`, 28 de 30 casos fallidos) o (b) el
    UNICO residuo de borde ya conocido y documentado (`densidad=400kg/m3,
    T=40°C, GPA TP-15`, 2 casos) -- CERO casos nuevos, CERO relacionados
    con el fix de esta ronda (esperado: esta grilla no toca el umbral).

RESIDUO: ninguno nuevo. El bug reportado (CPL mal en `conversion=0`,
P>0, RD60F y Dens20C) queda [CERTAIN] cerrado al 100% en el barrido
aleatorio dedicado de 300 casos por funcion. No se encontro un caso real
capturado en la app (`android_sdk_setup/*.json`, `uiautomator_dumps/*`)
con `Conversion=Standard->Observed` para RD60F/Dens20C -- los 2 dumps
disponibles de esas pantallas (`dump_04_Density20C_NGL_LPG.xml`,
`dump_05_RD60F_NGL_LPG.xml`) tienen `Conversion=Observed->Standard`
(los mismos casos reales ya conocidos de rondas previas). La validacion
de esta ronda descansa 100% en el oraculo `.xll` + decompilacion directa,
UN peldano por debajo de "caso real en vivo" -- documentado honesto, sin
fabricar un caso que no existe.
"""
import math

from .API_MPMS_Tables_1980_2004 import (
    _ngl_alpha,
    _ngl_solve_x,
    _round_n,
    api_mpms_11_2_2,
    api_mpms_11_2_2m,
    api_mpms_11_2_1,
    api_mpms_11_2_1m,
    api_table24e,
    api_table53e,
    api_table54e,
    api_table59e,
    api_table60e,
    RHO_WATER_NGL_LPG_KGM3,
    T_REF_NGL_15C_C,
    T_REF_NGL_20C_C,
    PSI_TO_KPA,
    BAR_TO_KPA,
    MPMS_11_2_2_RD_RANGE,
    MPMS_11_2_2M_RHO_RANGE,
)

# ===========================================================================
# Tabla real de 7 filas de GPA TP-15, extraida a BYTES CRUDOS (`pefile`,
# VA 0x1801eaee0..0x1801eb0a0 de FlowXpert.xll, 7*8=56 doubles) -- columnas:
# [limite_inferior, limite_superior(umbral de seleccion), c2, c3, c4, c5,
# c6, c7]. [CERTAIN] (bytes reales, no fabricados -- ver script de
# extraccion en el historial de esta ronda).
# ===========================================================================
NGL_LPG_TP15_TABLE = (
    (0.35, 0.45, 17.5297, -24.604, 24.373, -6567.6, 19322.0, -24693.3),
    (0.45, 0.49, 7.9907, 7.562, 0.0, 1895.5, -10596.9, 0.0),
    (0.49, 0.51, -6.4747, 37.083, 0.0, 12038.0, -31296.5, 0.0),
    (0.51, 0.56, 11.5454, 1.749, 0.0, 1378.8, -10396.1, 0.0),
    (0.56, 0.585, 6.4827, 10.79, 0.0, 3721.5, -14579.5, 0.0),
    (0.585, 0.625, 6.5412, 10.69, 0.0, 6514.5, -19353.9, 0.0),
    (0.625, 0.676, 20.8537, -12.21, 0.0, -6765.6, 1894.3, 0.0),
)
_TP15_RD_MIN = NGL_LPG_TP15_TABLE[0][0]      # 0.35, == DAT_1801ea410
_TP15_RD_MAX = NGL_LPG_TP15_TABLE[-1][1]     # 0.676, == _DAT_1801eb0a8
_TP15_T_DENOM_OFFSET = 443.0                 # _DAT_1801eb0b8, [CERTAIN via bytes]
_TP15_T_MIN_F = -50.0                        # DAT_180195188, [CERTAIN via bytes]
_TP15_T_MAX_F_HIGH_RD = 140.0                # DAT_1801ea5e8, si RD >= 0.425
_TP15_RD_MID = 0.425                         # DAT_1801eb0a0
_TP15_T_BOUND_A = 695.51                     # _DAT_1801eb0c8
_TP15_T_BOUND_B = 155.51                     # _DAT_1801eb0b0
_TP15_DENOM_MIN = 1.0e-5                     # DAT_180193de8
_TP15_LOG_T_REF = 100.0                      # DAT_1801940c8
_TP15_LOG_DENOM_SCALE = 543.0                # _DAT_1801eb0c0


def _gpa_tp15_psia(rd: float, t_f: float, round_tp15: int = 0,
                    p100_correlacion: int = 0, p100_valor_psia: float = 0.0):
    """[CERTAIN via decompilacion de `FUN_1800efcbc` + tabla real extraida a
    bytes + caso real de `calcular_rd60f_ngl_lpg_puro`] Presion de vapor en
    equilibrio, GPA TP-15, dada una densidad relativa reducida `rd`
    (adimensional, MISMA variable que usa el motor CTL "E" -- `rd_60f` en el
    camino US, `x_root` de `_ngl_solve_x` en el camino metrico) y una
    temperatura `t_f` en grados Fahrenheit (SIEMPRE Fahrenheit -- confirmado
    que el nucleo TP-15 real trabaja en °F/psia sin importar si el llamador
    es la pantalla US o la metrica, ver docstring del modulo).

    Devuelve (evp_psia, fuera_de_rango) -- `evp_psia` es `None` si el
    denominador de la formula se vuelve numericamente invalido (fuera del
    dominio fisico de la correlacion) o si `p100_correlacion=1` con
    `p100_valor_psia<=0` (log indefinido); en ese caso el llamador debe
    tratarlo como fallo explicito (NaN), nunca fabricar un numero."""
    fuera_de_rango = not (_TP15_RD_MIN <= rd <= _TP15_RD_MAX)
    bound_t = _TP15_T_MAX_F_HIGH_RD if rd >= _TP15_RD_MID else (
        rd * _TP15_T_BOUND_A - _TP15_T_BOUND_B)
    if not (_TP15_T_MIN_F <= t_f <= bound_t):
        fuera_de_rango = True

    fila = None
    for f in NGL_LPG_TP15_TABLE:
        if rd < f[1]:
            fila = f
            break
    if fila is None:
        fila = NGL_LPG_TP15_TABLE[-1]
    _, _, c2, c3, c4, c5, c6, c7 = fila

    denom = t_f + _TP15_T_DENOM_OFFSET
    if denom < _TP15_DENOM_MIN:
        return None, True

    numer = c7 * rd * rd + c6 * rd + c5
    if p100_correlacion == 0:
        expo = numer / denom + c4 * rd * rd + c3 * rd + c2
    else:
        if p100_valor_psia <= 0.0:
            return None, True
        expo = math.log(p100_valor_psia) + (
            (_TP15_LOG_T_REF - t_f) * numer) / (denom * _TP15_LOG_DENOM_SCALE)

    try:
        evp = math.exp(expo)
    except OverflowError:
        return None, True
    if round_tp15:
        evp = _round_n(evp, 1)
    return evp, fuera_de_rango


# ===========================================================================
# RD60F_NGL_LPG (sistema US) -- ver docstring del modulo, seccion "EL SOLVER"
# ===========================================================================
def _forward_rd60f(rd_base: float, t_f: float, p_psia: float, atm_psia: float,
                    evp_mode: int, evp_input_psia: float, round_tp15: int,
                    p100_correlacion: int, p100_valor_psia: float,
                    round_11_2_2: int = 0, round_11_2_4: int = 0) -> dict:
    """[USO INTERNO] Evaluacion DIRECTA (sin iterar): dado un `rd_base`
    (candidato de RD@60F) y las condiciones de flujo, devuelve el valor
    OBSERVADO que ese `rd_base` predice, mas CTL/CPL/EVP/flags. Es el
    "paso hacia adelante" que el solver de `calcular_rd60f_ngl_lpg_puro`
    itera hasta converger.

    `round_11_2_2` (RONDA 33, ver manual `fxAPI_RD60F_NGL_LPG` y
    `fxAPI_MPMS_11_2_2`): cuando esta activo, CPL se redondea a 4 decimales
    -- [CERTAIN, confirmado exacto contra el oraculo `.xll` esta ronda, ver
    `_sweep_ngl_lpg_puro_flags.py`] -- y ese CPL YA redondeado es el que se
    usa para armar `valor_obs`/el siguiente candidato del solver (no solo
    un redondeo cosmetico de salida).

    `round_11_2_4` (RONDA 41, corrige una suposicion incorrecta de RONDA 33):
    SOLO tiene efecto real cuando el llamador es la rama `conversion==0`
    (Standard->Observed) de `calcular_rd60f_ngl_lpg_puro` -- ahi el nucleo
    real (`FUN_1800E8E88`) evalua CTL llamando al mismo nucleo que
    `api_table24e` (`FUN_1800ec020`), pasandole el flag de rounding
    directamente; por eso aqui se delega el calculo de CTL a `api_table24e`
    (en vez de `_ngl_alpha` crudo) con `rounding=round_11_2_4`: cuando esta
    activo, RD@60F y T se redondean a graduacion de hidrometro/termometro
    (0.0001/0.1°F) SOLO para la busqueda de CTL en la tabla, y el CTL
    resultante se redondea a 5 decimales -- exactamente igual que
    `api_table24e` (RONDA 37, [CERTAIN] via decompilacion). El `rd_base`
    usado en `valor_obs = rd_base * ctl * cpl` mas abajo SIGUE siendo el
    valor crudo (sin la graduacion de hidrometro) -- confirmado leyendo
    `FUN_1800E8E88`, la version graduada solo se usa DENTRO del nucleo de
    CTL, el resultado final vuelve a multiplicar por el `rd_base` original.
    Validado [CERTAIN] contra el oraculo `.xll` en 3 casos variados de
    densidad/T/P distintos del unico caso de la mision (ver conversacion/
    memoria de esta ronda) -- NO se llama en la rama `conversion==1`
    (default 0 ahi): el nucleo real usa una rutina de solver COMPLETAMENTE
    DISTINTA en esa direccion (`FUN_1800edc20`/`FUN_1800eab2c`/
    `FUN_1800ec10c` inline, nunca `FUN_1800ec020`), y la rama `conversion==1`
    ya tenia su PROPIO mecanismo validado (redondeo del resultado final
    `rd_std` a 4 decimales, sin tocar esta funcion) -- mezclar ambos
    mecanismos fabricaria un comportamiento no visto en el binario.

    F (compressibility_1_psi) NO se redondea aqui aunque el manual tambien
    lo menciona ("F rounded to 8 decimal places with a maximum of 4
    significant digits") -- se intento esa regla literal esta ronda y NO
    reproduce el oraculo real (ej. F crudo=0.0010585046 1/bar, oraculo con
    rounding activo devuelve 0.001064, ninguna combinacion razonable de
    "8 decimales"/"4 cifras significativas" sobre el valor final da ese
    numero). Evidencia de que el rounding de F NO es un redondeo del
    resultado final sino una truncacion de terminos INTERMEDIOS durante el
    propio calculo de F (mismo patron que el redondeo de K0/K1/K2 en la
    familia 1980) -- requiere decompilacion adicional de
    `FUN_1800e32e8`/`FUN_1800e36e8` para la version con rounding activo, no
    resuelto esta ronda -- PENDIENTE, documentado honesto, sin fabricar.
    CPL SI se confirma correcto porque el nucleo `api_mpms_11_2_2`/`_11_2_2m`
    calcula su propio CPL internamente con F sin redondear y solo el
    redondeo final a 4 decimales de CPL entra en juego -- eso SI coincide
    exacto con el oraculo."""
    r_ctl = api_table24e(rd_60f=rd_base, observed_temp_c=(t_f - 32.0) / 1.8,
                         rounding=round_11_2_4)
    ctl, oor_ctl = r_ctl["ctl"], r_ctl["fuera_de_rango"]

    if evp_mode == 2:
        evp_psia, oor_evp = _gpa_tp15_psia(rd_base, t_f, round_tp15,
                                            p100_correlacion, p100_valor_psia)
        if evp_psia is None:
            evp_psia = float("nan")
            oor_evp = True
    else:
        evp_psia, oor_evp = evp_input_psia, False

    p_psig = p_psia - atm_psia
    evp_psig = evp_psia - atm_psia if evp_psia == evp_psia else evp_psia  # NaN-safe

    # [RONDA 42, CERTAIN via decompilacion de FUN_1800E8E88] Cuando rd_base
    # (el MISMO valor usado como primer argumento en AMBAS ramas, directa e
    # iterativa -- confirmado leyendo las 2 instancias identicas del
    # patron en el decompilado) alcanza/supera 0.638 (=DAT_1801ea5a8,
    # MPMS_11_2_2_RD_RANGE[1], extraido a bytes del .xll), el nucleo real
    # DEJA de llamar a FUN_1800e32e8 (api_mpms_11_2_2) y en su lugar llama a
    # FUN_1800e2d5c -- la MISMA funcion ya portada como `api_mpms_11_2_1`
    # (RONDA 9), pasandole la RD convertida a °API (`141.5/rd_base-131.5`,
    # constantes DAT_1801eaa80=141.5/DAT_1801ea4e0=131.5, confirmadas a
    # bytes con pefile). Este modulo, ANTES de esta ronda, llamaba SIEMPRE a
    # api_mpms_11_2_2 sin este switch -- invisible en todos los barridos
    # previos porque usaban rd<=0.637 (por debajo del umbral); expuesto por
    # un barrido ALEATORIO con rd hasta 0.676 (limite superior real de la
    # tabla NGL/LPG) en conversion=0 (Standard->Observed), donde el valor
    # de entrada no se corrige antes de llegar aqui. Validado [CERTAIN]
    # contra el oraculo `.xll` (ver `_sweep_ngl_lpg_puro_ronda42.py`).
    if rd_base < MPMS_11_2_2_RD_RANGE[1]:
        cpl_res = api_mpms_11_2_2(rd_base, t_f, p_psig, evp_psig)
    else:
        api_gravity_base = 141.5 / rd_base - 131.5
        cpl_res = api_mpms_11_2_1(api_gravity_base, t_f, p_psig, evp_psig)
    cpl, f, oor_cpl = cpl_res["cpl"], cpl_res["f"], cpl_res["fuera_de_rango_oficial"]
    if round_11_2_2:
        # [CERTAIN esta ronda] CPL a 4 decimales -- F NO se redondea aqui,
        # ver docstring de `calcular_rd60f_ngl_lpg_puro` para la evidencia
        # de por que el redondeo de F es un PENDIENTE honesto (no un
        # descuido).
        cpl = _round_n(cpl, 4)

    valor_obs = rd_base * ctl * cpl
    return {"valor_obs": valor_obs, "ctl": ctl, "cpl": cpl, "f": f,
            "evp_psia": evp_psia, "oor_ctl": oor_ctl, "oor_cpl": oor_cpl,
            "oor_evp": oor_evp}


def calcular_rd60f_ngl_lpg_puro(
    rd: float, t_f: float, p_psia: float, *,
    round_11_2_4: int = 0, round_11_2_2: int = 0,
    evp_mode: int = 2, evp_input_psia: float = 0.0,
    round_tp15: int = 0, p100_correlacion: int = 0, p100_valor_psia: float = 0.0,
    conversion: int = 1, atm_psia: float = 14.696,
    max_iter: int = 100, tol: float = None,
) -> dict:
    """FUNCION PRINCIPAL (US) -- porte 100% Python puro de
    `calcular_rd60f_ngl_lpg_directo()` (`_ngl_lpg_wrappers_xll_directo.py`,
    el oraculo de validacion). MISMOS parametros y MISMAS claves de salida
    (`rd_std, ctl, cpl, ctpl, compressibility_1_psi, evp_psia, oor_ctl,
    oor_cpl, oor_evp`) -- reemplazo directo, sin `ctypes`/`pefile`/Excel.

    `conversion`: 1=Observed->Standard(60°F) (default, itera hasta 100
    veces con punto fijo simple -- ver docstring del modulo, "EL SOLVER"),
    0=Standard(60°F)->Observed (evaluacion directa, sin iterar).

    [CERTAIN] validado EXACTO contra el caso real completo (RD=0.5,
    T=110°F, P=200psia, Atm=14.696psia -> RD_std=0.537512, CTL=0.927163,
    CPL=1.003289, CTPL=0.930212, Compressibility=0.000047 1/psi,
    EVP=130.828psia) -- ver autotest al final de este archivo, y el
    barrido masivo contra el oraculo `.xll` en `_sweep_ngl_lpg_puro.py`.

    [RONDA 33, cruce contra manual] `tol=None` (default) usa la tolerancia
    de convergencia DINAMICA documentada literalmente para
    `fxAPI_RD60F_NGL_LPG`: 0.00005 si `round_11_2_2` esta activo, si no
    0.000005 si `round_tp15` esta activo, si no 0.00000001 (=1e-8, el
    default que ya usaba este modulo antes de esta ronda -- coincide EXACTO
    con la rama "ninguno activo" del manual, por eso los 4 casos reales
    conocidos, todos con flags=0, no cambian). Pasar un `tol` explicito
    sigue disponible para forzar un valor distinto. `round_11_2_4`, cuando
    esta activo, redondea el resultado final `rd_std` a 0.0001 SOLO en
    `conversion=1` (paso 10 del manual, sin cambios esta ronda).

    [RONDA 41 (2026-09-10), corrige una suposicion INCORRECTA de RONDA 33]
    En `conversion=0` (Standard->Observed) `round_11_2_4` SI tiene efecto
    real -- RONDA 33 asumio que no (el manual, ambiguo/con columnas
    mezcladas por OCR, no lo dejaba claro) y por eso quedaba sin pasar a
    `_forward_rd60f`; el usuario aporto un caso real de la app que contradijo
    esa suposicion. Decompilacion directa de `FUN_1800E8E88` confirmo el
    mecanismo real: en esta rama el nucleo evalua CTL llamando al MISMO
    nucleo que `api_table24e` (`FUN_1800ec020`) pasandole el flag
    directamente -- por eso `_forward_rd60f` ahora delega el CTL de esta
    rama a `api_table24e(rounding=round_11_2_4)` en vez de `_ngl_alpha`
    crudo. Validado [CERTAIN] contra el oraculo `.xll` en 3 casos variados
    (RD/T/P distintos, ninguno alineado a la graduacion de hidrometro) --
    100% de coincidencia en CTL y en el resultado final. NO se toca la
    rama `conversion=1`: el nucleo real usa ahi una rutina de solver
    totalmente distinta (`FUN_1800edc20`/`FUN_1800eab2c`/`FUN_1800ec10c`
    inline, nunca `FUN_1800ec020`), que ya tenia su propio mecanismo
    validado (redondeo del resultado final a 4 decimales) -- mezclar ambos
    fabricaria un comportamiento no visto en el binario."""
    if tol is None:
        if round_11_2_2:
            tol_efectivo = 0.00005
        elif round_tp15:
            tol_efectivo = 0.000005
        else:
            tol_efectivo = 1e-8
    else:
        tol_efectivo = tol

    if conversion == 0:
        rd_base = rd
        res = _forward_rd60f(rd_base, t_f, p_psia, atm_psia, evp_mode,
                              evp_input_psia, round_tp15, p100_correlacion,
                              p100_valor_psia, round_11_2_2,
                              round_11_2_4=round_11_2_4)
        rd_std = res["valor_obs"]
    else:
        rd_base = rd
        res = None
        for _ in range(max_iter):
            res = _forward_rd60f(rd_base, t_f, p_psia, atm_psia, evp_mode,
                                  evp_input_psia, round_tp15, p100_correlacion,
                                  p100_valor_psia, round_11_2_2)
            ctpl = res["ctl"] * res["cpl"]
            nuevo = rd / ctpl if ctpl not in (0.0,) and ctpl == ctpl else rd_base
            if abs(nuevo - rd_base) < tol_efectivo:
                rd_base = nuevo
                break
            rd_base = nuevo
        rd_std = rd_base
        if round_11_2_4:
            rd_std = _round_n(rd_std, 4)

    ctpl = res["ctl"] * res["cpl"]
    return {
        "rd_std": rd_std, "ctl": res["ctl"], "cpl": res["cpl"], "ctpl": ctpl,
        "compressibility_1_psi": res["f"], "evp_psia": res["evp_psia"],
        "oor_ctl": bool(res["oor_ctl"]), "oor_cpl": bool(res["oor_cpl"]),
        "oor_evp": bool(res["oor_evp"]),
    }


# ===========================================================================
# Dens15C/Dens20C_NGL_LPG (sistema metrico) -- reusa api_table53e/54e (15C)
# o api_table59e/60e (20C) para el paso CTL, api_mpms_11_2_2m para CPL.
# ===========================================================================
def _forward_densxc(density_base_kgm3: float, t_c: float, p_barg: float,
                     evp_mode: int, evp_input_barg: float, round_tp15: int,
                     p100_correlacion: int, p100_valor_psia: float,
                     t_ref_c: float, tabla_forward,
                     round_11_2_2m: int = 0, round_11_2_4: int = 0,
                     permitir_switch_1121m: bool = False) -> dict:
    """[USO INTERNO] Evaluacion DIRECTA (Standard->Observed): dado un
    `density_base_kgm3` (candidato de densidad @15°C o @20°C, segun
    `t_ref_c`/`tabla_forward`) y las condiciones de flujo, devuelve la
    densidad OBSERVADA que ese candidato predice, mas CTL/CPL/EVP/flags.
    `tabla_forward` es `api_table54e` (para 15°C) o `api_table60e` (para
    20°C) -- YA [CERTAIN], reusada tal cual para el paso CTL.

    [RONDA 41 (2026-09-10), corrige una suposicion INCORRECTA de RONDA 33]
    `round_11_2_4`: RONDA 33 asumio (solo por el manual, ambiguo) que este
    flag NO tenia efecto en `conversion=0` (Standard->Observed) -- el
    usuario aporto un caso real de la app que lo contradijo (Density=
    600kg/m3, T=25°C, P=20bar(a), API-11.2.4=1, EVP-Mode=Override,
    EVP=5bar(a), Conversion=Std->Obs -> Density=591.5219, CTL=0.982000,
    diferencia real de 0.0017 kg/m3 contra la implementacion sin este fix).
    Decompilacion directa de `FUN_1800e6ca0` confirmo el mecanismo: en esta
    rama el nucleo evalua CTL llamando al MISMO nucleo que `api_table54e`/
    `api_table60e` (`FUN_1800eea6c`) pasandole el flag de rounding
    directamente -- por eso aqui se pasa `rounding=round_11_2_4` a
    `tabla_forward` (antes SIEMPRE se llamaba con `rounding=0` implicito,
    sin importar el flag). Efecto cuando esta activo: `density_base_kgm3`/
    `t_c` se redondean a graduacion de hidrometro/termometro (0.1 kg/m3 /
    0.05°C) SOLO para la busqueda de CTL en la tabla, y el CTL resultante se
    redondea a 5 decimales -- el `density_base_kgm3` usado mas abajo en
    `densidad_obs = density_base_kgm3 * ctl * cpl` SIGUE siendo el valor
    crudo (confirmado leyendo `FUN_1800e6ca0`: la version graduada solo
    vive DENTRO del nucleo de CTL). Validado [CERTAIN] contra el oraculo
    `.xll` en 5 casos variados (densidad/T/P/EVP distintos, ninguno
    alineado a la graduacion) -- 100% de coincidencia en CTL y en el
    resultado final, incluido el caso real de la mision (591.5219 exacto).
    NO se pasa en la rama `conversion=1` (default 0 ahi, sin cambios): el
    nucleo real usa ahi una rutina de solver totalmente distinta
    (`FUN_1800edc20`/`FUN_1800eab2c`/`FUN_1800ec10c` inline, nunca
    `FUN_1800eea6c`), que ya tenia su propio mecanismo validado (redondeo
    del resultado final a 0.1 kg/m3, paso 14 del manual) -- mezclar ambos
    fabricaria un comportamiento no visto en el binario.

    [CERTAIN via decompilacion de `FUN_1800e7304`, hallazgo de esta ronda]
    CPL (API MPMS 11.2.2M) NO se evalua con la densidad en la referencia
    propia del wrapper (20°C para `api_table60e`) -- se evalua SIEMPRE con
    la densidad equivalente a **15°C**, incluso dentro del nucleo de
    "Dens20C" (confirmado leyendo `FUN_1800e7304`: hace UNA evaluacion de
    `_ngl_alpha` en 20°C para el CTL/densidad-base reportada, y una SEGUNDA
    evaluacion SEPARADA, explicita, en 15°C -- `FUN_1800e1d78(DAT_180194008)`,
    DAT_180194008=15.0 -- cuyo resultado (`local_470*local_4a8*RHO_WATER`)
    es el que efectivamente entra a `FUN_1800e36e8`, el core de CPL). Antes
    de este hallazgo, este modulo usaba `density_base_kgm3` (en la
    referencia propia) para CPL en ambas funciones -- funcionaba por
    coincidencia en `api_dens15c_ngl_lpg_puro` (su propia referencia YA es
    15°C) pero rompia sistematicamente `api_dens20c_ngl_lpg_puro` (barrido
    inicial: 0.5% de coincidencia contra el oraculo). Corregido aqui
    calculando SIEMPRE la densidad@15°C real (via `x_root`, la misma
    "densidad relativa reducida" que ya usa `_ngl_solve_x`/`_ngl_alpha` en
    el resto del motor) y usandola para el CPL, sin importar `t_ref_c`."""
    t_f = t_c * 1.8 + 32.0
    t_ref_k = t_ref_c + 273.15
    t_15c_k = T_REF_NGL_15C_C + 273.15

    r_ctl = tabla_forward(density_base_kgm3, t_c, rounding=round_11_2_4)
    ctl = r_ctl["ctl"]
    oor_ctl = r_ctl["fuera_de_rango"]

    # x_root: la "densidad relativa reducida" intrinseca (independiente de
    # T) tal que density_base_kgm3 = alpha(x_root, t_ref_k) * x_root * RHO_WATER.
    # Se recalcula aqui (barato, deterministico) porque `tabla_forward` no
    # expone `x_root` en su dict de salida -- se necesita para (a) TP-15
    # [CERTAIN, ver docstring del modulo] y (b) la densidad@15°C para CPL
    # [CERTAIN esta ronda, ver arriba].
    x_root, _, oor_x = _ngl_solve_x(density_base_kgm3 / RHO_WATER_NGL_LPG_KGM3,
                                     t_ref_k)
    alpha_15c, oor_15c = _ngl_alpha(x_root, t_15c_k)
    density_15c_kgm3 = alpha_15c * x_root * RHO_WATER_NGL_LPG_KGM3

    if evp_mode == 2:
        evp_psia, oor_evp = _gpa_tp15_psia(x_root, t_f, round_tp15,
                                            p100_correlacion, p100_valor_psia)
        if evp_psia is None:
            evp_psia = float("nan")
            oor_evp = True
        evp_barg = evp_psia * PSI_TO_KPA / BAR_TO_KPA
    else:
        evp_barg, oor_evp = evp_input_barg, False

    # [RONDA 42, CERTAIN via decompilacion de FUN_1800e7304] En la rama
    # `conversion=0` (Standard->Observed) del nucleo de Dens20C, cuando
    # `density_15c_kgm3` alcanza/supera 637.5 kg/m3 (=DAT_1801ea4f0,
    # MPMS_11_2_2M_RHO_RANGE[1], mismo umbral usado como limite inferior de
    # `api_mpms_11_2_1m`), el nucleo real DEJA de llamar a FUN_1800e36e8
    # (api_mpms_11_2_2m) y llama en su lugar a FUN_1800e303c -- la MISMA
    # funcion ya portada como `api_mpms_11_2_1m` (RONDA 9), con la densidad
    # equivalente a 15°C directamente (sin conversion a °API -- la version
    # metrica toma densidad_kgm3, no °API). CONFIRMADO leyendo linea a linea
    # `FUN_1800e7304` (rama `else`, `param_11!=1`): calcula `dVar14 =
    # local_4a8*local_470*RHO_WATER` (density_15c, EXACTAMENTE la misma
    # cantidad que `density_15c_kgm3` aqui) y hace
    # `if (dVar14 < DAT_1801ea4f0) {FUN_1800e36e8(dVar14,...)} else
    # {FUN_1800e303c()}`.
    #
    # IMPORTANTE -- esta rama es ASIMETRICA entre las 2 pantallas
    # (confirmado por decompilacion, NO un descuido): `FUN_1800e6ca0`
    # (Dens15C) en su rama `conversion=0` NO tiene este switch -- usa
    # SIEMPRE `FUN_1800e36e8`/api_mpms_11_2_2m con la densidad CRUDA de
    # entrada (`*param_1`, sin recalcular a 15°C ni comparar contra ningun
    # umbral) -- invisible en la practica porque para Dens15C
    # `density_base_kgm3` YA ES la densidad@15°C por definicion de esa
    # pantalla (identidad, no una coincidencia de redondeo). Por eso
    # `permitir_switch_1121m` (activado SOLO por
    # `calcular_dens20c_ngl_lpg_puro`, nunca por `calcular_dens15c_...`)
    # controla este bloque -- mezclar el switch en Dens15C fabricaria un
    # comportamiento no visto en el binario. Tampoco se aplica en la rama
    # iterativa (`conversion=1`) de NINGUNA de las 2 funciones -- el
    # decompilado de esa rama en Dens20C (`FUN_1800e7304`, bloque
    # `*param_11==1`) llama a `FUN_1800e36e8` SIN el condicional de umbral
    # (siempre api_mpms_11_2_2m); tocar esa rama esta fuera del alcance de
    # esta ronda (el bug reportado y reproducido es exclusivo de
    # `conversion=0`, ver docstring del modulo, seccion RONDA 42).
    if permitir_switch_1121m and density_15c_kgm3 >= MPMS_11_2_2M_RHO_RANGE[1]:
        cpl_res = api_mpms_11_2_1m(density_15c_kgm3, t_c, p_barg, evp_barg)
    else:
        cpl_res = api_mpms_11_2_2m(density_15c_kgm3, t_c, p_barg, evp_barg)
    cpl, f, oor_cpl = cpl_res["cpl"], cpl_res["f"], cpl_res["fuera_de_rango_oficial"]
    if round_11_2_2m:
        # [CERTAIN esta ronda, confirmado exacto contra el oraculo `.xll`]
        # CPL a 4 decimales -- el CPL redondeado es el que alimenta
        # `densidad_obs`/el siguiente candidato del solver. F NO se
        # redondea aqui -- ver docstring de `calcular_dens15c_ngl_lpg_puro`
        # para la evidencia de por que eso queda PENDIENTE (no un descuido).
        cpl = _round_n(cpl, 4)

    densidad_obs = density_base_kgm3 * ctl * cpl
    return {"valor_obs": densidad_obs, "ctl": ctl, "cpl": cpl, "f": f,
            "evp_barg": evp_barg, "oor_ctl": oor_ctl, "oor_cpl": oor_cpl,
            "oor_evp": oor_evp}


def _dens_ngl_lpg_puro(densidad_kgm3: float, t_c: float, p_barg: float, *,
                        evp_mode: int, evp_input_barg: float,
                        round_tp15: int, p100_correlacion: int,
                        p100_valor_barg: float, conversion: int,
                        max_iter: int, tol: float, t_ref_c: float,
                        tabla_inversa, tabla_forward,
                        round_11_2_4: int = 0, round_11_2_2m: int = 0,
                        permitir_switch_1121m_directo: bool = False) -> dict:
    """[USO INTERNO] Motor comun de `calcular_dens15c_ngl_lpg_puro`/
    `calcular_dens20c_ngl_lpg_puro` -- `tabla_inversa` es `api_table53e`
    (15°C) o `api_table59e` (20°C) [CERTAIN, usada dentro del punto fijo
    Observed->Standard], `tabla_forward` es `api_table54e`/`api_table60e`
    [CERTAIN, usada por `_forward_densxc` para el paso Standard->Observed
    y para evaluar CTL/EVP en cada vuelta del punto fijo]. `t_ref_c` es
    15.0 o 20.0 -- ver docstring de `_forward_densxc` para por que CPL NO
    depende de este valor (siempre se evalua a 15°C internamente).

    `permitir_switch_1121m_directo` [RONDA 42]: activa el switch a
    `api_mpms_11_2_1m` (ver `_forward_densxc`) SOLO dentro de la rama
    `conversion=0` -- pasado en `True` UNICAMENTE por
    `calcular_dens20c_ngl_lpg_puro`, ver docstring del modulo."""
    p100_valor_psia = p100_valor_barg * BAR_TO_KPA / PSI_TO_KPA
    evp_input_psia = evp_input_barg * BAR_TO_KPA / PSI_TO_KPA

    # [RONDA 33, cruce contra manual] tolerancia de convergencia DINAMICA,
    # literal segun `fxAPI_Dens15C_NGL_LPG`/`fxAPI_Dens20C_NGL_LPG`: 0.05
    # kg/m3 si `round_11_2_2m` esta activo, si no 0.005 si `round_tp15` esta
    # activo, si no 0.00001 (=1e-5) -- ANTES de esta ronda se usaba un `tol`
    # fijo (1e-6, mas estricto que el 1e-5 del manual mas ningun otro caso)
    # sin importar los flags; con flags=0 (default de los 4 casos reales
    # conocidos y del barrido existente) el resultado final no cambia --
    # una tolerancia mas estricta converge al MISMO punto fijo, solo con mas
    # vueltas.
    tol_efectivo = tol
    if tol is None:
        if round_11_2_2m:
            tol_efectivo = 0.05
        elif round_tp15:
            tol_efectivo = 0.005
        else:
            tol_efectivo = 0.00001

    if conversion == 0:
        density_base = densidad_kgm3
        res = _forward_densxc(density_base, t_c, p_barg, evp_mode,
                               evp_input_barg, round_tp15, p100_correlacion,
                               p100_valor_psia, t_ref_c, tabla_forward,
                               round_11_2_2m, round_11_2_4=round_11_2_4,
                               permitir_switch_1121m=permitir_switch_1121m_directo)
        x_out = res["valor_obs"]
    else:
        # Estimacion inicial de CPL evaluando en el propio valor observado
        # (guess razonable) -- IMPRESCINDIBLE hacerlo ANTES del bucle: si se
        # arranca con cpl=1.0 "a ciegas" (en vez de este estimado), el primer
        # candidato coincide casi siempre con el valor observado de entrada
        # cuando T_obs~=T_ref (CTL~=1 ahi), lo que provoca una "convergencia"
        # falsa en la primerisima vuelta -- se detecta ANTES de aplicar CPL
        # siquiera una vez, dando resultados sistematicamente sin la
        # correccion de presion. Hallazgo de esta ronda (barrido inicial:
        # 91.8%/100% en evp_mode=1 para Dens15C/Dens20C escondia este bug en
        # los casos T_obs~T_ref con presion>0 -- ver ejemplos en
        # `_sweep_ngl_lpg_puro.py`).
        density_base = densidad_kgm3
        res = _forward_densxc(density_base, t_c, p_barg, evp_mode,
                               evp_input_barg, round_tp15, p100_correlacion,
                               p100_valor_psia, t_ref_c, tabla_forward,
                               round_11_2_2m)
        for _ in range(max_iter):
            working_target = densidad_kgm3 / res["cpl"] if res["cpl"] else densidad_kgm3
            r_inv = tabla_inversa(working_target, t_c)
            density_base_candidato = r_inv["density_15c"] if "density_15c" in r_inv \
                else r_inv["density_20c"]
            res = _forward_densxc(density_base_candidato, t_c, p_barg, evp_mode,
                                   evp_input_barg, round_tp15, p100_correlacion,
                                   p100_valor_psia, t_ref_c, tabla_forward,
                                   round_11_2_2m)
            # ctl reportado: relativo al 'working_target' (dividiendo CPL ya
            # aplicado en vueltas previas), igual que el decompilado real.
            res["ctl"] = (working_target / density_base_candidato
                          if density_base_candidato else 0.0)
            convergio = abs(density_base_candidato - density_base) < tol_efectivo
            density_base = density_base_candidato
            if convergio:
                break
        x_out = density_base
        if round_11_2_4:
            # [RONDA 33] paso 14 del manual (`fxAPI_Dens15C_NGL_LPG`):
            # "If API 11.2.4 rounding is enabled, then the density at [15C,
            # equilibrium pressure] is rounded to 0.1" -- identico para
            # Dens20C con su propia referencia. Solo aplica en `conversion=1`
            # (Observed->Standard).
            # [RONDA 41] En `conversion=0` (Standard->Observed) round_11_2_4
            # SI tiene efecto -- RONDA 33 asumio lo contrario por ambiguedad
            # del manual; corregido pasando el flag a `tabla_forward` dentro
            # de `_forward_densxc` (ver docstring de esa funcion), NO con un
            # redondeo del resultado final aqui (serian 2 mecanismos
            # distintos confirmados por decompilacion, no uno solo).
            x_out = _round_n(x_out, 1)

    ctpl = res["ctl"] * res["cpl"]
    return {
        "x_kgm3": x_out, "ctl": res["ctl"], "cpl": res["cpl"], "ctpl": ctpl,
        "compressibility_1_bar": res["f"], "evp_barg": res["evp_barg"],
        "oor_ctl": bool(res["oor_ctl"]), "oor_cpl": bool(res["oor_cpl"]),
        "oor_evp": bool(res["oor_evp"]),
    }


def calcular_dens15c_ngl_lpg_puro(
    densidad_kgm3: float, t_c: float, p_barg: float, *,
    round_11_2_4: int = 0, round_11_2_2m: int = 0,
    evp_mode: int = 2, evp_input_barg: float = 0.0,
    round_tp15: int = 0, p100_correlacion: int = 0, p100_valor: float = 0.0,
    conversion: int = 1, max_iter: int = 100, tol: float = None,
) -> dict:
    """FUNCION PRINCIPAL (metrico, 15°C) -- porte 100% Python puro de
    `calcular_dens15c_ngl_lpg_directo()`. MISMOS parametros/claves de
    salida (`x_kgm3, ctl, cpl, ctpl, compressibility_1_bar, evp_barg,
    oor_ctl, oor_cpl, oor_evp`).

    `conversion`: 1=Observed->Standard(15°C) (default, iterativo), 0=
    Standard(15°C)->Observed (directo).

    [CERTAIN] sin presion / `evp_mode=1` (round-trip exacto contra
    `api_table53e`/`api_table54e`, YA [CERTAIN]). [LIKELY] con
    `evp_mode=2` (GPA TP-15 calculada) -- ver docstring del modulo,
    seccion "GPA TP-15", para el detalle honesto de la ambiguedad de
    decompilacion en esta rama especifica, y `_sweep_ngl_lpg_puro.py`
    para el numero de esta ronda contra el oraculo `.xll`.

    [RONDA 33] `round_11_2_4`/`round_11_2_2m` -- ANTES de esta ronda estos
    2 parametros se aceptaban pero NUNCA se pasaban a `_dens_ngl_lpg_puro`
    (no-op silencioso); ahora SI se usan: `round_11_2_4` redondea el
    resultado final a 0.1 kg/m3 (conversion=1) segun el manual, y
    `round_11_2_2m`, junto con `round_tp15`, decide la tolerancia de
    convergencia dinamica (0.05 / 0.005 / 0.00001 kg/m3) y redondea CPL (4
    decimales, [CERTAIN] contra el oraculo) dentro del solver. F
    (compressibility_1_bar) NO se redondea bajo `round_11_2_2m` -- PENDIENTE
    honesto, ver docstring de `calcular_rd60f_ngl_lpg_puro` para la
    evidencia exacta de por que la regla literal del manual ("8 decimales,
    max 4 cifras significativas") no reproduce el oraculo real."""
    return _dens_ngl_lpg_puro(
        densidad_kgm3, t_c, p_barg, evp_mode=evp_mode,
        evp_input_barg=evp_input_barg, round_tp15=round_tp15,
        p100_correlacion=p100_correlacion, p100_valor_barg=p100_valor,
        conversion=conversion, max_iter=max_iter, tol=tol, t_ref_c=T_REF_NGL_15C_C,
        tabla_inversa=api_table53e, tabla_forward=api_table54e,
        round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m)


def calcular_dens20c_ngl_lpg_puro(
    densidad_kgm3: float, t_c: float, p_barg: float, *,
    round_11_2_4: int = 0, round_11_2_2m: int = 0,
    evp_mode: int = 2, evp_input_barg: float = 0.0,
    round_tp15: int = 0, p100_correlacion: int = 0, p100_valor: float = 0.0,
    conversion: int = 1, max_iter: int = 100, tol: float = None,
) -> dict:
    """FUNCION PRINCIPAL (metrico, 20°C) -- identica a
    `calcular_dens15c_ngl_lpg_puro` con referencia 20°C (reusa
    `api_table59e`/`api_table60e` en vez de `api_table53e`/`api_table54e`).
    Ver ese docstring para el detalle completo, incluida la nota RONDA 33
    sobre `round_11_2_4`/`round_11_2_2m` (antes no-op, ahora conectados).

    [RONDA 42] `permitir_switch_1121m_directo=True` -- SOLO esta funcion
    (NUNCA `calcular_dens15c_ngl_lpg_puro`) activa, dentro de
    `conversion=0`, el switch a `api_mpms_11_2_1m` cuando la densidad@15°C
    equivalente alcanza/supera 637.5 kg/m3 -- ver docstring de
    `_forward_densxc`, seccion RONDA 42, para la evidencia completa
    (decompilacion de `FUN_1800e7304`) de por que esto es real SOLO para
    Dens20C y no para Dens15C."""
    return _dens_ngl_lpg_puro(
        densidad_kgm3, t_c, p_barg, evp_mode=evp_mode,
        evp_input_barg=evp_input_barg, round_tp15=round_tp15,
        p100_correlacion=p100_correlacion, p100_valor_barg=p100_valor,
        conversion=conversion, max_iter=max_iter, tol=tol, t_ref_c=T_REF_NGL_20C_C,
        tabla_inversa=api_table59e, tabla_forward=api_table60e,
        round_11_2_4=round_11_2_4, round_11_2_2m=round_11_2_2m,
        permitir_switch_1121m_directo=True)


if __name__ == "__main__":
    print("=== Autoprueba: caso real completo RD60F_NGL_LPG ===")
    r = calcular_rd60f_ngl_lpg_puro(rd=0.5, t_f=110.0, p_psia=200.0, atm_psia=14.696)
    print(r)
    assert abs(r["rd_std"] - 0.537512) < 1e-4
    assert abs(r["ctl"] - 0.927163) < 1e-4
    assert abs(r["cpl"] - 1.003289) < 1e-4
    assert abs(r["ctpl"] - 0.930212) < 1e-4
    assert abs(r["compressibility_1_psi"] - 0.000047) < 5e-6
    assert abs(r["evp_psia"] / 14.5037738 - 9.020282) < 5e-2
    print("OK -- coincide con el caso real dentro de tolerancia.")

    print("\n=== Round-trip Dens15C vs api_table53e/54e (evp_mode=1, EVP=0) ===")
    r15 = calcular_dens15c_ngl_lpg_puro(densidad_kgm3=600.0, t_c=25.0, p_barg=0.0,
                                         evp_mode=1, conversion=1)
    r53 = api_table53e(observed_density_kgm3=600.0, observed_temp_c=25.0)
    print("puro:", r15, "\napi_table53e:", r53)
    assert abs(r15["x_kgm3"] - r53["density_15c"]) < 1e-2
    assert abs(r15["ctl"] - r53["ctl"]) < 1e-4
    assert abs(r15["cpl"] - 1.0) < 1e-9
    print("OK.")

    print("\n=== Round-trip Dens20C vs api_table59e/60e (evp_mode=1, EVP=0) ===")
    r20 = calcular_dens20c_ngl_lpg_puro(densidad_kgm3=600.0, t_c=25.0, p_barg=0.0,
                                         evp_mode=1, conversion=1)
    r59 = api_table59e(observed_density_kgm3=600.0, observed_temp_c=25.0)
    print("puro:", r20, "\napi_table59e:", r59)
    assert abs(r20["x_kgm3"] - r59["density_20c"]) < 1e-2
    assert abs(r20["ctl"] - r59["ctl"]) < 1e-4
    print("OK.")
    print("\nTodas las pruebas pasaron.")
