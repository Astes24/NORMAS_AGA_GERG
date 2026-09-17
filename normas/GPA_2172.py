# -*- coding: utf-8 -*-
"""
normas/GPA_2172.py
====================
GPA 2172 -- "Calculation of Gross Heating Value, Relative Density,
Compressibility and Theoretical Hydrocarbon Liquid Content for Natural Gas
Mixtures for Custody Transfer". Porte a PYTHON PURO (sin .xll/emulador en
produccion, ver memoria `feedback-preferencia-python-puro`) del motor real
`FUN_1800deb44` de FlowXpert.xll, compartido por las 4 variantes Excel
(`GPA2172_C`, `GPA2172_M`, y sus 2 alias de compatibilidad `GPA2172_96_C`/
`GPA2172_96_M`, confirmado que estos ultimos NO tienen logica propia: su
cuerpo real es literalmente 6 lineas que solo registran el nombre legado y
llaman a `GPA2172_C`/`GPA2172_M` tal cual, sin ninguna diferencia de
calculo -- ver `normas/_gpa2172_xll_directo.py` para el detalle completo de
evidencia).

ALCANCE DE ESTA IMPLEMENTACION: Theoretical Hydrocarbon Liquid Content (la
3ra parte del nombre del estandar) NO esta incluida -- no se encontro
ninguna salida relacionada ni en el manual (paginas 96-100) ni en los 21
punteros de salida reales de `FUN_1800deb44` (los 21 son exactamente Gross/
Net Heating Value, Molar Mass, Molar Mass Ratio, Relative Density y
Compressibility, x3 bases Wet/Dry/Saturated) -- la funcion real de FlowXpert
NO calcula liquid content pese al nombre del estandar, esto se documenta
honesto, no se fabrica esa salida.

METODOLOGIA Y NIVEL DE CERTEZA
-------------------------------
[CERTAIN] Estructura completa y TODAS las formulas de este archivo fueron
derivadas por 2 tecnicas cruzadas, no una sola:
1. Decompilacion real (Ghidra 12.1.2) de las 4 raices Excel + su motor
   compartido `FUN_1800deb44` (ver `ANALISIS_GHIDRA_FLOWXPERT/
   ghidra_gpa2172_xll_output.txt`, generado por
   `ghidra_scripts_xll/DecompileGpa2172Xll.java`).
2. Llamada DIRECTA por ctypes al motor real aislado (sin Excel, sin
   marshalling XLOPER -- `FUN_1800deb44` es una funcion "pura" de
   doubles/ints, un nivel mas arriba en la cadena que los wrappers
   `GPA2172_C`/`_M` que SI dependen del host, mismo patron que
   `_gost30319_xll_directo.py`) usada como ORACULO para AJUSTAR y CONFIRMAR
   cada formula con precision numerica de ~1e-10 (ver
   `normas/_gpa2172_xll_directo.py` para el script; los tests que fijaron
   cada formula estan documentados linea por linea en ese archivo y no se
   repiten aqui).

TABLAS DE PROPIEDADES POR COMPONENTE (9 variantes: 5 ediciones customary +
4 metricas -- NO hay edicion 1989 metrica, confirmado por decompilacion Y
por el manual explicito "1: 15C...GPA2145-00" como PRIMERA opcion metrica):
extraidas de los bytes CRUDOS de `.rdata` en `FlowXpert.xll` (`pefile`,
sin Ghidra), estructura de 21 filas x 17 doubles/fila, columnas reales
usadas: [0]=Molar Mass, [1]=SG ideal (Molar Mass Ratio), [2]=b (factor de
sumacion de compresibilidad), [4]=GHV masico, [5]=GHV volumetrico bruto,
[6]=GHV volumetrico neto (columna [3] no se usa en customary ed.2+, valor
centinela -1, ver docstring de `_gpa2172_xll_directo.py`). Cada fila fue
identificada por comparacion 1:1 contra valores FISICOS PUBLICOS conocidos
(Metano M=16.043/GHV=1010 Btu/scf exacto, Etano/Propano/... todos
coincidentes a 4-5 cifras significativas con GPA 2145 publicado) -- el
orden de 21 filas es PROPIO de esta tabla (alcanos primero, luego inertes),
DISTINTO del orden AGA8/GERG/ISO6976 usado en el resto del proyecto.
CONFIRMADO ademas que las ediciones GPA2145-2000/2003 (customary Y metric)
tienen Hidrogeno/CO/Argon con TODAS las propiedades en 0 -- coincide
EXACTO con el texto literal del manual ("GPA-2145 standard editions 2000
and 2003 do not specify properties for hydrogen, argon and carbon
monoxide... processed... with all property values set to 0").

FORMULAS (confirmadas por ajuste numerico exacto contra el oraculo, no
adivinadas -- ver detalle de cada test en `_gpa2172_xll_directo.py`):
    M   = sum(xi * Mi)
    ISG = sum(xi * SGi)                         (SG ideal tabulada, NO M/Maire)
    b   = sum(xi * bi)
    Z   = 1 - Pbase * b^2
    Zaire = 1 - Pbase * baire^2                 (baire = constante por edicion)
    RRD = ISG * Zaire / Z
    GHV_vol = sum(xi * GHVvol_i) / Z
    NHV_vol = sum(xi * NHVvol_i) / Z
    GHV_mass = sum(xi * Mi * GHVmass_i) / M      (promedio ponderado por masa)

3 BASES DE COMPOSICION (a partir del array de 21 componentes YA fusionado
con neo-Pentano, ver mas abajo):
    WET: composicion tal cual, renormalizada a suma=1.
    DRY: fraccion de Agua forzada a 0, resto renormalizado a suma=1.
    SATURATED: fraccion de Agua forzada al valor de saturacion FIJO de la
        edicion (no depende del valor de Agua de entrada), resto
        renormalizado proporcionalmente para sumar 1.
Confirmado por 2 tests reales: (a) con Agua=0 de entrada, WET y DRY dan
resultados IDENTICOS (esperado, ambos terminan en la misma composicion) y
SATURATED difiere (usa su fraccion fija); (b) con Agua=1% de entrada, WET
usa el 1% real, DRY lo fuerza a 0 (recupera exactamente la composicion pura
sin agua) y SATURATED sigue dando el MISMO resultado que con Agua=0 (no
depende del valor de entrada, solo de si el usuario puso agua>=0).

NEO-PENTANO (confirmado exacto contra el oraculo, incluyendo el caso
"Neglect" que reproduce EXACTO el resultado de no tener neo-Pentano en
absoluto):
    modo 0 ("Add to i-Pentane"): x[i-Pentano] += x[neo-Pentano]
    modo 1 ("Add to n-Pentane"): x[n-Pentano] += x[neo-Pentano]
    modo 2 ("Neglect"): x[neo-Pentano] se excluye de la suma de
        normalizacion (equivalente a borrarlo de la composicion).
La verificacion de que la composicion de 22 valores (21 + neo-Pentano) suma
100% +-0.01% (tolerancia 1.0e-4, confirmada por bytes) se hace ANTES de
esta fusion, sobre los 22 valores crudos de entrada.

RONDA 54 (2026-09-16): pantalla real de FlowXpert Android CONFIRMADA EN
VIVO (uiautomator, AVD flowxpert_rd) -- sube de [LIKELY] a [CERTAIN]. Menu
"GPA" -> "GPA-2172" junto a "GPA-TP15" tal como esperaba el manual.
Composicion, "Edition" (etiqueta real "GPA-2145 Edition", 4 opciones reales
2000/2003/2009/2016 con 2003 preseleccionado, coincide exacto con
_EDICIONES_M claves 1-4) y los 7 campos x 3 bases (Wet/Dry/Saturated, la
app real los lista en vertical Wet->Dry->Saturated en vez de una tabla de
3 columnas -- misma info, presentacion distinta) confirmados campo a campo
contra `interfaz_calculo_flujo.py`. Unica diferencia real encontrada:
"neo-Pentane Mode" default de pantalla es "Add to nC5" (el codigo
compartia el default "Add to iC5" del resto de la app) -- corregido solo
en la pestaña GPA-2172 de la GUI, sin tocar el default compartido de otras
normas. ADEMAS: 2 casos reales de pantalla capturados (composicion
"Default" del proyecto, y un gas humedo con Agua 15%, ambos edicion 2003)
validados 1 a 1 contra este motor: 16/16 valores coinciden a la precision
mostrada en pantalla (6 cifras) -- el motor sube de [CERTAIN via oraculo
.xll] a [CERTAIN via oraculo + 2 casos reales de pantalla].
- Theoretical Hydrocarbon Liquid Content: NO implementado, ver "ALCANCE"
  arriba -- la funcion real de FlowXpert no lo calcula.

RONDA 55 (2026-09-16) -- CORRECCION de RONDA 54, "neo-Pentane Mode" default:
[CERTAIN, metodologia mas rigurosa] RONDA 54 leyo el default de "neo-Pentane
Mode" ("Add to nC5") sobre dumps `gpa2172_*.xml` de una sesion anterior
(2026-09-10) que asumia "fresh" por el nombre de archivo, pero el AVD/app
NO habian sido reseteados (`pm clear`) antes de esa captura -- FlowXpert
PERSISTE el ultimo valor usado POR PANTALLA/FUNCION entre sesiones (igual
que un configurador real de instrumento), asi que ese dump reflejaba un
valor de prueba anterior, no el default de fabrica. Esta ronda repitio la
confirmacion con `pm clear com.spiritit.flowxpert` (reset completo, primera
apertura real de la pantalla) Y ademas abriendo el dropdown real hasta ver
el atributo `checked="true"` del item seleccionado (no solo el texto de
resumen) -- doble rigor. Resultado, confirmado 2 veces independientes
(Customary y Metric, ambas primera apertura tras el reset): "neo-Pentane
Mode" = **"Neglect"**, NO "Add to nC5" (RONDA 54) ni "Add to iC5" (default
compartido del resto de la app). Interesante ademas: esto tampoco coincide
con el "Default: 1 (Add to i-Pentane)" que documenta el manual oficial
(`Flow-X Manual IIIb - Function Reference`, fxGPA2172_C/_M, pag. 98/100) --
a diferencia de AGA-8/AGA8 GERG/GERG-2008 Gas/GERG-2008 Flash/GERG-2004
Gas/GERG-2004 Flash/AGA-10, donde el default real de pantalla SI coincide
con el manual ("Add to i-Pentane"), GPA-2172 es la UNICA de las 8
normas/pantallas auditadas donde el preset de la app movil difiere del
default documentado para la funcion de flow-computer -- se prioriza el
comportamiento real de la app (fuente de verdad de este proyecto en las
demas 53 rondas) sobre el manual de referencia de funciones. Corregido en
`interfaz_calculo_flujo.py` (`_build_tab_gpa2172`).
BONUS/PENDIENTE (no corregido esta ronda, fuera de alcance de la mision de
neo-Pentano): con el mismo reset se encontro que "GPA-2145 Edition" tambien
muestra "2000" seleccionado de fabrica (no "2003" como decia RONDA 54) en
AMBOS sistemas Customary y Metric -- para Customary coincide con el default
ya codificado (clave 2) y con el manual (default=2 -> "2000" en su lista de
5 ediciones incluyendo 1989), pero para Metric el manual y el codigo actual
default en clave 2 ("2003" en la lista de 4 ediciones del manual, sin
1989), mientras la app real mostro "2000" incluso ya en modo Metric -- Y
ademas el dropdown de Edition en modo Metric seguia listando "1989" como
opcion (que el manual dice que NO existe para fxGPA2172_M). Esto sugiere
que la app movil no separa Customary/Metric en 2 funciones distintas como
el manual (fxGPA2172_C vs _M), sino que usa una sola lista de ediciones y
solo cambia las unidades de despliegue -- necesita una ronda dedicada para
confirmar bien antes de tocar el codigo de Edition, no fabricar el fix aqui.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# -----------------------------------------------------------------------
# Orden de la tabla GPA2145 (21 filas reales + neo-Pentano como 22a entrada
# que se fusiona antes de calcular, ver docstring).
# -----------------------------------------------------------------------
ORDEN_TABLA_GPA2145 = [
    "Metano", "Etano", "Propano", "i-Butano", "n-Butano", "i-Pentano",
    "n-Pentano", "n-Hexano", "n-Heptano", "n-Octano", "n-Nonano", "n-Decano",
    "Hidrogeno", "Helio", "Agua", "CO", "Nitrogeno", "Oxigeno", "H2S",
    "Argon", "CO2",
]
IDX_I_PENTANO = ORDEN_TABLA_GPA2145.index("i-Pentano")
IDX_N_PENTANO = ORDEN_TABLA_GPA2145.index("n-Pentano")
IDX_AGUA = ORDEN_TABLA_GPA2145.index("Agua")

# columnas: (M, SG_ideal, b, GHV_masico, GHV_vol_bruto, GHV_vol_neto)
# (se omite la columna cruda [3]=Hv_molar SI/-1, no usada en el calculo)
_T = {
    "ed0_1989_C": [
        (16.043, 0.55392, 0.0116, 23891.0, 1010.0, 909.4),
        (30.07, 1.0382, 0.0239, 22333.0, 1769.7, 1618.7),
        (44.097, 1.5226, 0.0344, 21653.0, 2516.1, 2314.9),
        (58.123, 2.0068, 0.0458, 21232.0, 3251.9, 3000.4),
        (58.123, 2.0068, 0.0478, 21300.0, 3262.3, 3010.8),
        (72.15, 2.4912, 0.0581, 21043.0, 4000.9, 3699.0),
        (72.15, 2.4912, 0.0631, 21085.0, 4008.9, 3703.9),
        (86.177, 2.9755, 0.0802, 20943.0, 4755.9, 4403.9),
        (100.204, 3.4598, 0.0944, 20839.0, 5502.5, 5100.3),
        (114.231, 3.9441, 0.1137, 20759.0, 6248.9, 5796.2),
        (128.258, 4.4284, 0.1331, 20701.0, 6996.5, 6493.6),
        (142.285, 4.9127, 0.1538, 20651.0, 7742.9, 7189.9),
        (2.0159, 0.0696, 0.0, 61022.0, 324.2, 273.93),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.0623, 1059.8, 50.312, 0.0),
        (28.01, 0.96711, 0.0053, 4342.0, 320.5, 320.5),
        (28.0134, 0.96723, 0.0044, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.0073, 0.0, 0.0, 0.0),
        (34.08, 1.1767, 0.0253, 7094.2, 637.1, 586.8),
        (39.948, 1.3793, 0.0071, 0.0, 0.0, 0.0),
        (44.01, 1.5196, 0.0197, 0.0, 0.0, 0.0),
    ],
    "ed1_2000_C": [
        (16.043, 0.55392, 0.0116, 23891.0, 1010.0, 909.0),
        (30.07, 1.0382, 0.0239, 22333.0, 1769.7, 1619.0),
        (44.097, 1.5226, 0.035, 21653.0, 2516.2, 2315.0),
        (58.123, 2.0068, 0.0444, 21232.0, 3251.9, 3000.0),
        (58.123, 2.0068, 0.0477, 21300.0, 3262.4, 3011.0),
        (72.15, 2.4912, 0.0591, 21043.0, 4000.9, 3699.0),
        (72.15, 2.4912, 0.0606, 21085.0, 4008.7, 3707.0),
        (86.177, 2.9755, 0.0782, 20943.0, 4756.0, 4404.0),
        (100.204, 3.4598, 0.108, 20839.0, 5502.6, 5100.0),
        (114.231, 3.9441, 0.122, 20759.0, 6248.8, 5796.0),
        (128.258, 4.4284, 0.141, 20700.0, 6996.2, 6493.0),
        (142.285, 4.9127, 0.169, 20651.0, 7742.9, 7190.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.002602, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.0603, 1060.1, 50.328, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.0134, 0.96723, 0.0045, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.0147, 0.0, 0.0, 0.0),
        (34.08, 1.1767, 0.0245, 7094.5, 637.13, 586.82),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.01, 1.5196, 0.0195, 0.0, 0.0, 0.0),
    ],
    "ed2_2003_C": [
        (16.042, 0.55397, 0.0116, 23892.0, 1010.0, 909.0),
        (30.069, 1.0383, 0.0238, 22334.0, 1769.7, 1619.0),
        (44.096, 1.5227, 0.0349, 21654.0, 2516.2, 2315.0),
        (58.122, 2.0071, 0.0444, 21232.0, 3252.0, 3000.0),
        (58.122, 2.0071, 0.0471, 21300.0, 3262.4, 3011.0),
        (72.149, 2.4914, 0.0572, 21044.0, 4000.9, 3699.0),
        (72.149, 2.4914, 0.0603, 21085.0, 4008.7, 3707.0),
        (86.175, 2.9758, 0.0792, 20944.0, 4756.0, 4404.0),
        (100.202, 3.4601, 0.0953, 20839.0, 5502.5, 5100.0),
        (114.229, 3.9445, 0.1214, 20760.0, 6248.9, 5796.0),
        (128.255, 4.4289, 0.135, 20701.0, 6996.4, 6493.0),
        (142.282, 4.9132, 0.1516, 20652.0, 7743.0, 7190.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.6221, 0.05557, 1059.8, 50.312, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.013, 0.9673, 0.00442, 0.0, 0.0, 0.0),
        (31.999, 1.105, 0.0072, 0.0, 0.0, 0.0),
        (34.082, 1.1769, 0.0242, 7093.8, 637.11, 586.8),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.01, 1.5197, 0.0195, 0.0, 0.0, 0.0),
    ],
    "ed3_2009_C": [
        (16.0425, 0.5539, 0.0116, 23892.0, 1010.0, 909.4),
        (30.069, 1.0382, 0.0238, 22334.0, 1769.7, 1619.0),
        (44.0956, 1.5225, 0.0347, 21654.0, 2516.1, 2315.0),
        (58.1222, 2.0068, 0.0441, 21232.0, 3251.9, 3000.0),
        (58.1222, 2.0068, 0.047, 21300.0, 3262.3, 3011.0),
        (72.1488, 2.4911, 0.0576, 21044.0, 4000.9, 3699.0),
        (72.1488, 2.4911, 0.0606, 21085.0, 4008.7, 3707.0),
        (86.1754, 2.9754, 0.0776, 20943.0, 4755.9, 4404.0),
        (100.2019, 3.4597, 0.0951, 20839.0, 5502.6, 5100.0),
        (114.2285, 3.944, 0.1128, 20760.0, 6249.0, 5796.0),
        (128.2551, 4.4283, 0.1307, 20701.0, 6996.3, 6493.0),
        (142.2817, 4.9126, 0.1556, 20651.0, 7742.9, 7190.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.0651, 1059.8, 50.31, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.0134, 0.9672, 0.00442, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.0072, 0.0, 0.0, 0.0),
        (34.0809, 1.1767, 0.0239, 7094.0, 637.1, 586.79),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.0095, 1.5195, 0.0195, 0.0, 0.0, 0.0),
    ],
    "ed4_2016_C": [
        (16.0425, 0.5539, 0.0116, 23892.0, 1010.0, 909.4),
        (30.069, 1.0382, 0.0238, 22334.0, 1769.7, 1619.0),
        (44.0956, 1.5225, 0.0347, 21654.0, 2516.1, 2315.0),
        (58.1222, 2.0068, 0.0441, 21232.0, 3251.9, 3000.0),
        (58.1222, 2.0068, 0.047, 21300.0, 3262.3, 3011.0),
        (72.1488, 2.4911, 0.0576, 21044.0, 4000.9, 3699.0),
        (72.1488, 2.4911, 0.0606, 21085.0, 4008.7, 3707.0),
        (86.1754, 2.9754, 0.0776, 20943.0, 4755.9, 4404.0),
        (100.2019, 3.4597, 0.0951, 20839.0, 5502.6, 5100.0),
        (114.2285, 3.944, 0.1128, 20760.0, 6249.0, 5796.0),
        (128.2551, 4.4283, 0.1307, 20701.0, 6996.3, 6493.0),
        (142.2817, 4.9126, 0.1556, 20651.0, 7742.9, 7190.0),
        (2.0159, 0.0696, 0.0, 61022.0, 324.2, 273.9),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.0651, 1059.8, 50.31, 0.0),
        (28.0101, 0.9671, 0.0056, 4342.0, 320.5, 320.5),
        (28.0134, 0.9672, 0.00442, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.0072, 0.0, 0.0, 0.0),
        (34.0809, 1.1767, 0.0239, 7094.0, 637.1, 586.79),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.0095, 1.5195, 0.0195, 0.0, 0.0, 0.0),
    ],
    "ed10_2000_M": [
        (16.043, 0.55392, 0.00442, 55.575, 37.707, 33.949),
        (30.07, 1.0382, 0.0091, 51.95, 66.067, 60.429),
        (44.097, 1.5226, 0.0133, 50.368, 93.935, 86.418),
        (58.123, 2.0068, 0.0169, 49.388, 121.4, 112.01),
        (58.123, 2.0068, 0.0182, 49.546, 121.79, 112.4),
        (72.15, 2.4912, 0.0225, 48.949, 149.36, 138.09),
        (72.15, 2.4912, 0.0231, 49.045, 149.66, 138.38),
        (86.177, 2.9755, 0.0298, 48.716, 177.55, 164.4),
        (100.204, 3.4598, 0.0412, 48.474, 205.43, 190.39),
        (114.231, 3.9441, 0.0464, 48.287, 233.28, 216.37),
        (128.258, 4.4284, 0.0539, 48.15, 261.18, 242.39),
        (142.285, 4.9127, 0.0643, 48.036, 289.06, 268.39),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.002602, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.023, 2.4659, 1.8788, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.0134, 0.96723, 0.00171, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.00562, 0.0, 0.0, 0.0),
        (34.08, 1.1767, 0.00934, 16.502, 23.785, 21.906),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.01, 1.5196, 0.0074, 0.0, 0.0, 0.0),
    ],
    "ed11_2003_M": [
        (16.042, 0.55397, 0.00442, 55.576, 37.707, 33.949),
        (30.069, 1.0383, 0.0091, 51.952, 66.067, 60.429),
        (44.096, 1.5227, 0.0133, 50.37, 93.936, 86.419),
        (58.122, 2.0071, 0.0169, 49.389, 121.4, 112.01),
        (58.122, 2.0071, 0.018, 49.547, 121.79, 112.4),
        (72.149, 2.4914, 0.0219, 48.95, 149.36, 138.09),
        (72.149, 2.4914, 0.023, 49.046, 149.66, 138.38),
        (86.175, 2.9758, 0.0303, 48.717, 177.55, 164.4),
        (100.202, 3.4601, 0.0364, 48.474, 205.42, 190.39),
        (114.229, 3.9445, 0.0464, 48.289, 233.29, 216.37),
        (128.255, 4.4289, 0.0516, 48.153, 261.19, 242.4),
        (142.282, 4.9132, 0.058, 48.038, 289.06, 268.39),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.6221, 0.02496, 2.4664, 1.8792, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.013, 0.9673, 0.0017, 0.0, 0.0, 0.0),
        (31.999, 1.105, 0.00275, 0.0, 0.0, 0.0),
        (34.082, 1.1769, 0.00926, 16.501, 23.785, 21.91),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.01, 1.5197, 0.00745, 0.0, 0.0, 0.0),
    ],
    "ed12_2009_M": [
        (16.0425, 0.5539, 0.00442, 55.575, 37.706, 33.95),
        (30.069, 1.0382, 0.0091, 51.951, 66.066, 60.43),
        (44.0956, 1.5225, 0.0132, 50.369, 93.934, 86.42),
        (58.1222, 2.0068, 0.0168, 49.388, 121.4, 112.0),
        (58.1222, 2.0068, 0.0179, 49.546, 121.79, 112.4),
        (72.1488, 2.4911, 0.022, 48.95, 149.36, 138.1),
        (72.1488, 2.4911, 0.0232, 49.045, 149.65, 138.4),
        (86.1754, 2.9754, 0.02961, 48.715, 177.55, 164.39),
        (100.2019, 3.4597, 0.0364, 48.474, 205.42, 190.39),
        (114.2285, 3.944, 0.04311, 48.29, 233.29, 216.38),
        (128.2551, 4.4283, 0.05001, 48.152, 261.19, 242.4),
        (142.2817, 4.9126, 0.05951, 48.037, 289.06, 268.39),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.02495, 2.4662, 1.879, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (28.0134, 0.9672, 0.0017, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.00275, 0.0, 0.0, 0.0),
        (34.0809, 1.1767, 0.00913, 16.501, 23.784, 21.905),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.0095, 1.5195, 0.00745, 0.0, 0.0, 0.0),
    ],
    "ed13_2016_M": [
        (16.0425, 0.5539, 0.00442, 55.575, 37.706, 33.95),
        (30.069, 1.0382, 0.0091, 51.951, 66.066, 60.43),
        (44.0956, 1.5225, 0.0132, 50.369, 93.934, 86.42),
        (58.1222, 2.0068, 0.0168, 49.388, 121.4, 112.0),
        (58.1222, 2.0068, 0.0179, 49.546, 121.79, 112.4),
        (72.1488, 2.4911, 0.022, 48.95, 149.36, 138.1),
        (72.1488, 2.4911, 0.0232, 49.045, 149.65, 138.4),
        (86.1754, 2.9754, 0.0296, 48.715, 177.55, 164.39),
        (100.2019, 3.4597, 0.0364, 48.474, 205.42, 190.39),
        (114.2285, 3.944, 0.0431, 48.29, 233.29, 216.38),
        (128.2551, 4.4283, 0.05, 48.152, 261.19, 242.4),
        (142.2817, 4.9126, 0.0595, 48.037, 289.06, 268.39),
        (2.0159, 0.0696, 0.0, 141.95, 12.102, 10.223),
        (4.0026, 0.1382, 0.0, 0.0, 0.0, 0.0),
        (18.0153, 0.62202, 0.02495, 2.4662, 1.879, 0.0),
        (28.0101, 0.9671, 0.00216, 10.1, 11.965, 11.965),
        (28.0134, 0.9672, 0.0017, 0.0, 0.0, 0.0),
        (31.9988, 1.1048, 0.00275, 0.0, 0.0, 0.0),
        (34.0809, 1.1767, 0.00913, 16.501, 23.784, 21.905),
        (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        (44.0095, 1.5195, 0.00745, 0.0, 0.0, 0.0),
    ],
}

# metadatos por edicion: (tabla, Pbase, b_aire, x_agua_saturacion, etiqueta)
_EDICIONES_C = {
    1: ("ed0_1989_C", 14.696, 0.005, 0.017444202504082743, "GPA2145-89 (1989)"),
    2: ("ed1_2000_C", 14.696, 0.00678, 0.017444202504082743, "GPA2145-00 (2000)"),
    3: ("ed2_2003_C", 14.696, 0.00523, 0.017444202504082743, "GPA2145-03 (2003)"),
    4: ("ed3_2009_C", 14.696, 0.00537, 0.01744692433315188, "GPA2145-09 (2009)"),
    5: ("ed4_2016_C", 14.696, 0.00537, 0.01744692433315188, "GPA2145-16 (2016)"),
}
_EDICIONES_M = {
    1: ("ed10_2000_M", 101.325, 0.00259, 0.016834937083641748, "GPA2145-00 (2000)"),
    2: ("ed11_2003_M", 101.325, 0.00201, 0.016834937083641748, "GPA2145-03 (2003)"),
    3: ("ed12_2009_M", 101.325, 0.00201, 0.016834937083641748, "GPA2145-09 (2009)"),
    4: ("ed13_2016_M", 101.325, 0.00201, 0.016834937083641748, "GPA2145-16 (2016)"),
}

TOLERANCIA_COMPOSICION = 1.0e-4  # +-0.01%, confirmado por bytes (DAT_1801df058)


@dataclass
class ResultadoBase:
    ghv_vol: float
    molar_mass: float
    molar_mass_ratio: float
    rel_density: float
    compresibilidad: float
    ghv_mass: float
    nhv_vol: float


@dataclass
class ResultadoGPA2172:
    status: int  # 0 OK, 1 fuera de rango, 3 composicion no suma 100%
    wet: "ResultadoBase | None" = None
    dry: "ResultadoBase | None" = None
    sat: "ResultadoBase | None" = None
    mensaje: str = ""


def _normalizar_y_calcular(x21, tabla, pbase, b_aire):
    # [CERTAIN, ajustado por oraculo] El manual dice literalmente que cada
    # Relative Density esta "Based on the compressibility of wet/dry/
    # saturated air" -- NO es una sola Zaire fija por edicion, es la
    # compresibilidad de una mezcla ficticia "aire seco + agua" usando LA
    # MISMA fraccion de agua que tiene la base de gas actual (wet/dry/sat),
    # con b_aire(seco, constante de edicion) y b_agua (columna de tabla,
    # ej. 0.0623 para Metano-ed.1989). Confirmado por ajuste numerico exacto
    # contra el oraculo para WET (agua>0) y SAT (agua=fraccion fija) -- ver
    # `_gpa2172_xll_directo.py` para el detalle de los 2 casos usados.
    x_agua = x21[IDX_AGUA]
    b_agua_tabla = tabla[IDX_AGUA][2]
    b_aire_mix = b_aire * (1.0 - x_agua) + b_agua_tabla * x_agua
    zaire = 1.0 - pbase * (b_aire_mix ** 2)
    m = sum(x21[i] * tabla[i][0] for i in range(21))
    isg = sum(x21[i] * tabla[i][1] for i in range(21))
    b = sum(x21[i] * tabla[i][2] for i in range(21))
    z = 1.0 - pbase * (b ** 2)
    rrd = isg * zaire / z if z else float("nan")
    # [CERTAIN, ajustado por oraculo] El Agua se EXCLUYE de la suma ideal de
    # poder calorifico (volumetrico Y masico), pese a que la tabla SI trae
    # un valor de Agua nominal distinto de cero para GHV (ej. 50.312 Btu/scf,
    # 1059.8 Btu/lbm en ed.1989) -- confirmado por ajuste numerico exacto: la
    # composicion SAT (unica que fuerza Agua>0 con una fraccion conocida
    # incluso para una entrada 100% Metano) solo cierra contra el oraculo
    # si el termino de Agua se omite de estas 2 sumas (Z/M/ISG/NHV SI la
    # incluyen sin cambios, NHV de Agua ya es 0 en la tabla asi que no
    # distinguia esto por si solo). El poder calorifico masico y volumetrico
    # de "Wet"/"Saturated" gas se reporta entonces como el aporte puro de
    # los hidrocarburos e inertes, no de la fraccion de agua.
    ghv_vol_ideal = sum(x21[i] * tabla[i][4] for i in range(21) if i != IDX_AGUA)
    nhv_vol_ideal = sum(x21[i] * tabla[i][5] for i in range(21) if i != IDX_AGUA)
    ghv_vol = ghv_vol_ideal / z if z else float("nan")
    nhv_vol = nhv_vol_ideal / z if z else float("nan")
    ghv_mass = (sum(x21[i] * tabla[i][0] * tabla[i][3] for i in range(21) if i != IDX_AGUA) / m) if m else 0.0
    return ResultadoBase(
        ghv_vol=ghv_vol, molar_mass=m, molar_mass_ratio=isg, rel_density=rrd,
        compresibilidad=z, ghv_mass=ghv_mass, nhv_vol=nhv_vol,
    )


def calcular_gpa2172(composicion22: list[float], edicion: int, neo_pentano_modo: int,
                      sistema: str = "C") -> ResultadoGPA2172:
    """composicion22: 22 fracciones molares [0..1] en ORDEN_TABLA_GPA2145 + neo-Pentano
    (indice 21) como ULTIMA entrada.
    edicion: 1..5 (customary, sistema='C') o 1..4 (metric, sistema='M') --
    MISMA numeracion 1-based que expone la pantalla real (ver manual).
    neo_pentano_modo: 1 (Add to i-Pentane), 2 (Add to n-Pentane), 3 (Neglect)
    -- MISMA numeracion 1-based del manual/Excel.
    sistema: 'C' (customary, Btu/lbm, Btu/ft3, psia) o 'M' (metric, MJ/kg,
    MJ/m3, kPa/bar(a))."""
    if len(composicion22) != 22:
        raise ValueError("composicion22 debe tener 22 valores (21 componentes + neo-Pentano)")

    ediciones = _EDICIONES_C if sistema.upper() == "C" else _EDICIONES_M
    if edicion not in ediciones:
        return ResultadoGPA2172(status=1, mensaje=f"Edicion {edicion} invalida para sistema {sistema}")
    if neo_pentano_modo not in (1, 2, 3):
        return ResultadoGPA2172(status=1, mensaje="Modo neo-Pentano invalido (1/2/3)")

    tabla_nombre, pbase, b_aire, x_agua_sat, _etq = ediciones[edicion]
    tabla = _T[tabla_nombre]

    suma_total = sum(composicion22)
    if abs(suma_total - 1.0) >= TOLERANCIA_COMPOSICION:
        return ResultadoGPA2172(status=3, mensaje="Composicion no suma 100% +-0.01%")

    x = list(composicion22[:21])
    neo = composicion22[21]
    if neo_pentano_modo == 1:
        x[IDX_I_PENTANO] += neo
        suma_norm = suma_total
    elif neo_pentano_modo == 2:
        x[IDX_N_PENTANO] += neo
        suma_norm = suma_total
    else:  # 3: Neglect
        suma_norm = suma_total - neo

    # WET: composicion tal cual (post neo-Pentano), renormalizada a 1.
    x_wet = [xi / suma_norm for xi in x]
    wet = _normalizar_y_calcular(x_wet, tabla, pbase, b_aire)

    # DRY: agua -> 0, resto renormalizado.
    agua_wet = x_wet[IDX_AGUA]
    resto = 1.0 - agua_wet
    if resto > 0:
        x_dry = [(0.0 if i == IDX_AGUA else x_wet[i] / resto) for i in range(21)]
    else:
        x_dry = list(x_wet)
    dry = _normalizar_y_calcular(x_dry, tabla, pbase, b_aire)

    # SATURATED: agua -> fraccion fija de saturacion, resto renormalizado
    # proporcionalmente (excluyendo la fraccion de agua original).
    resto_sat = 1.0 - x_agua_sat
    if resto > 0:
        x_sat = [(x_agua_sat if i == IDX_AGUA else (x_wet[i] / resto) * resto_sat) for i in range(21)]
    else:
        x_sat = [(x_agua_sat if i == IDX_AGUA else 0.0) for i in range(21)]
    sat = _normalizar_y_calcular(x_sat, tabla, pbase, b_aire)

    return ResultadoGPA2172(status=0, wet=wet, dry=dry, sat=sat)


if __name__ == "__main__":
    # Autotest minimo: 100% Metano, edicion 1 (1989), neo-Pentano Neglect.
    comp = [0.0] * 22
    comp[ORDEN_TABLA_GPA2145.index("Metano")] = 1.0
    r = calcular_gpa2172(comp, edicion=1, neo_pentano_modo=3, sistema="C")
    print("status", r.status)
    print("WET", r.wet)
    print("DRY", r.dry)
    print("SAT", r.sat)
    assert r.status == 0
    assert abs(r.dry.ghv_vol - 1012.0012261097444) < 1e-6
    assert abs(r.sat.molar_mass - 16.0774052005988) < 1e-9
    assert abs(r.sat.ghv_vol - 994.6596531135998) < 1e-6
    assert abs(r.sat.ghv_mass - 23424.006335149526) < 1e-6
    assert abs(r.sat.rel_density - 0.5560880470555661) < 1e-9
    print("OK autotest basico")
