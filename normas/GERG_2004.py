# -*- coding: utf-8 -*-
"""
normas/GERG_2004.py
======================
GERG-2004 (Kunz, Klimeck, Wagner, Jaeschke -- GERG Technical Monograph 15,
2007). Mismo codigo de calculo que `normas/GERG_2008.py`, pero con los DATOS
propios de la ruta GERG-2004 de FlowXpert (`normas/_gerg2004_data_generado.py`).

===============================================================================
ACTUALIZACION 2026-10-05 [CERTAIN] -- SUPERA la conclusion "misma tabla" de abajo
===============================================================================
El binario tiene DOS juegos de tablas GERG. La ruta GERG-2004 de FlowXpert
difiere de GERG-2008 en:
  1. CO e isopentano: coeficientes y constantes criticas de la NORMA GERG-2004
     (TM15, Tablas A3.2 y A3.5; CO Tc 132.800 K, iC5 Dc 3.271018581 mol/l).
     GERG-2008 los modifico.
  2. n-nonano, n-decano y H2S: la TM15 no los incluye; FlowXpert los acepta con
     coeficientes, constantes criticas y pares binarios propios (sin fuente
     publica). Gas ideal del H2S solo con el termino constante.
  3. Pares binarios derivados de lo anterior.
La busqueda de julio concluyo "una sola copia" porque busco el bloque CONTIGUO
de 24 coeficientes del metano (la tabla de GERG-2008 esta intercalada) y cotejo
la TM15 solo en metano, N2 y etano. Decision del usuario 2026-10-05: replicar
FlowXpert. Validado con 5 capturas reales (H2S en mezcla y puro, metano con
n-nonano, metano con n-decano, CO puro): error <= 0.00007 % en Z, densidad,
velocidad del sonido y exponente isentropico. Con los 16 componentes restantes
GERG-2004 y GERG-2008 dan lo mismo (libro 01). El texto historico de abajo se
conserva como registro.
===============================================================================

Este archivo se puede ejecutar solo:
    python -m normas.GERG_2004

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] Se decompilo con Ghidra el export `FlowXpert_GERG2004_Gas` de
FlowXpert.xll. Es una ruta de codigo GENUINAMENTE DISTINTA de
`FlowXpert_GERG2008_Gas` (selector de tipo diferente: DAT_1802f24f0 vs
DAT_1802c7340; 5 salidas contra 8). No es un simple alias a nivel de
exportacion de la DLL.

[CERTAIN] Sin embargo, se busco en TODO el archivo FlowXpert.xll el bloque
COMPLETO y CONTIGUO de los 24 coeficientes del metano de GERG-2008
(`noik(1,1..24)`) y aparece UNA SOLA VEZ en el binario. Si GERG2004 tuviera
su propia copia separada de esta tabla (con los mismos o distintos valores),
apareceria una segunda vez. Esto indica que la ruta de codigo de GERG2004
REUTILIZA la misma tabla de coeficientes de fluido puro en memoria que
GERG2008, no una copia propia.

[CERTAIN] Se confirmo ademas contra la fuente publicada
(`documentos_normativos/GERG-2004_TM15.pdf`, Tabla A3.3 pag. 476 y Tabla
A3.8 pag. 482) que los coeficientes de fluido puro (metano, nitrogeno,
etano) Y los parametros de reduccion binaria (Metano-Nitrogeno, Metano-CO2,
etc.) publicados para GERG-2004/TM15 son IDENTICOS digito por digito a los
que ya se extrajeron de GERG2008.FOR. La propia Tabla A3.3 de TM15 dice
explicitamente "Los valores... tambien son validos para la Ec. (4.27)"
(la ecuacion de GERG-2004), confirmando que el estandar publicado NO
diferencia estos coeficientes entre ambas versiones.

[GUESSING -- no verificado, limite tecnico] NO se pudo confirmar si
FlowXpert restringe GERG2004_Gas a un subconjunto de los 21 componentes
(por ejemplo, excluyendo Helio/Argon, que en el estandar original de 2004
no estaban --aunque la Tabla A3.8 de esta edicion de TM15 SI los incluye,
lo cual sugiere que TM15 (2007) ya es una revision posterior al articulo
original de 2004). El selector de tipo de GERG2004 (DAT_1802f24f0) no se
pudo rastrear mas alla (mismo despacho virtual sin ancla, igual que la
columna de AGA5). Si se necesita reproducir EXACTAMENTE que componentes
acepta FlowXpert_GERG2004_Gas (y no solo la formula), habria que retomar
la investigacion con Ghidra en esa estructura.

DECISION: en vez de duplicar codigo, este archivo es un alias fino sobre
`normas/GERG_2008.py`. Si en el futuro se encuentra evidencia de que
FlowXpert aplica una diferencia real (ej. una funcion de "departure"
adicional que solo exista en la ruta 2008, o una restriccion de
componentes), corregir aqui sin tocar GERG_2008.py.

===============================================================================
GAS vs FLASH -- son DOS pantallas distintas en la app, expuestas por separado
===============================================================================
[CERTAIN] Confirmado con capturas reales (carpeta `GERG 2004/`) que
"GERG-2004 Gas" (propiedades en una sola fase) y "GERG-2004 Flash"
(equilibrio liquido-vapor) son pantallas DIFERENTES en FlowXpert, con
resultados diferentes (Vapour/Liquid/Total Compr., Vapour/Liquid/Total
Density vs. las 8 propiedades de "Gas"). Por eso este archivo expone
`calcular_propiedades_gas()` y `calcular_flash()` como funciones separadas,
en vez de una sola.

[CERTAIN -- 2026-07-22, cierra el gap de "GERG-2004 Gas no confirmado"] El
usuario aporto una captura adicional despues de que este archivo ya estaba
validado solo para "Flash": `GERG 2004/GERG GAS 11.jpeg`, titulo real
"GERG-2004 Gas", descripcion real "Thermodynamic properties of gas
according to GERG-2004 (not split).", MISMO P=100 bar(a)/T=25 degC/
composicion Default. Resultados (solo 4 campos, sin separar densidad
masica/molar como "GERG-2008 Gas"):
    Compressibility: real=0.865194     calculado=0.865194     dif. 0.00004%
    Density (kg/m3, correcta aqui, no como en "GERG-2004 Flash"):
        real=86.89434   calculado=86.89433   dif. 0.00001%
    Speed of Sound: real=415.4652   calculado=415.4652   dif. 0.000006%
    Isentropic Exponent: real=1.499894   calculado=1.499894   dif. 0.00003%
Esto confirma que "GERG-2004 Gas" SI existe como pantalla real separada
(con su propio titulo/descripcion), cerrando la duda planteada antes de
esta captura (no habia titulo ni resultados propios, solo la pantalla
generica de composicion).

[CERTAIN] Validado tambien contra la captura real de "GERG-2004 Flash"
(titulo real "GERG-2004 Flash", descripcion real "Flash calculation
according to GERG-2004."), MISMO P/T/composicion:
    Vapour Fraction: real=1.000000   calculado=1.000000
    Total Compr. (Z): real=0.865194   calculado=0.865194   dif. 0.00005%
    Total Density: real=4.662483 (etiqueta "kg/m3" de la app)
                   calculado=4.662482 (mol/l = kmol/m3)   dif. 0.00002%
[Certain, discrepancia de la app, no mia] Ese resultado real es MONOFASICO
(VF=1), asi que en la practica solo valida el motor GERG-2008 de una fase.
Ademas, el numero que la app etiqueta "kg/m3" en esta pantalla NO es
densidad masica real (esa seria ~86.9 kg/m3 con Mm=18.64 g/mol): coincide
digito a digito con la densidad MOLAR (mol/l = kmol/m3). Es decir, la propia
pantalla "GERG-2004 Flash" de FlowXpert parece tener la etiqueta de unidad
mal puesta. Se replica el numero que muestra la app (para comparacion 1 a 1),
mientras que `calcular_flash()` tambien expone la densidad masica CORRECTA
por separado (`D_*_kg_m3` real, no confundir con lo que se muestra en la
interfaz bajo la etiqueta de la app).

[CERTAIN -- 2026-07-22, cierra el punto anterior con evidencia dura, ya NO es
un [GUESSING]] Se rastreo el call graph real de `GergMath_GERG2004_Flash` en
libFXLibrary.so (Android, disassembly con capstone): llama a
`GERG::GERG_Calculate` (calculo de UNA fase), NUNCA a
`GERG::CEquation::CalculateFlash` (la funcion grande que si tiene un
algoritmo real de equilibrio de fases, existe en el binario pero no esta
conectada a esta pantalla). Confirmado ademas empiricamente: una composicion
deliberadamente pesada (65% metano + 35% repartido en etano a n-octano, a
100 bar(a)/25 degC) que segun el motor GERG-2008 SI deberia dar un resultado
bifasico (VF~0.46) sigue dando Vapour Fraction=1.000000 en la app real.
CONCLUSION: la pantalla "GERG-2004 Flash" NUNCA calcula equilibrio de fases
de verdad, siempre reporta VF=1.000000 sin importar la composicion. Ver
docstring de `calcular_flash` en GERG_2008.py para el detalle completo.

[Decision de alcance, 2026-08-01, pedido explicito del usuario] Por lo
anterior, la rama de 2 fases de `calcular_flash()` (metodo estandar, Wilson
+ Rachford-Rice + sustitucion sucesiva) se ELIMINO por completo: la funcion
ahora siempre devuelve un resultado monofasico, igual que la app real.

===============================================================================
"neo-Pentane Mode" -- IMPORTANTE: "Neglect" NO se comporta igual que en
GERG-2008 (unica diferencia real encontrada entre ambas pantallas)
===============================================================================
[CERTAIN -- RONDA 56, 2026-09-16] Se confirmo en vivo (AVD `flowxpert_rd`,
composicion "Default", neo-Pentano=0.008, P=100 bar(a)/T=25 degC) que "Add
to iC5" y "Add to nC5" dan resultados IDENTICOS entre "GERG-2004 Gas"/
"GERG-2004 Flash" y "GERG-2008 Gas"/"GERG-2008 Flash" (coincide con que
comparten el mismo motor real, ver docstring de GERG_2008.py). SIN EMBARGO
"Neglect" especificamente NO coincide:
    GERG-2004 Gas:   real Z=0.865392, Density=86.84751 kg/m3,
                      Speed of Sound=415.5746 m/s, Isentropic Exp.=1.499876.
    GERG-2008 Gas (MISMA composicion/T/P, MISMO caso):
                      real Z=0.865283, Density=86.86535 kg/m3,
                      Speed of Sound=415.5392 m/s, Isentropic Exp.=1.499929.
La diferencia es real y reproducible (confirmado tambien en las pantallas
"Flash" de ambas, mismos valores que sus "Gas" respectivos). GERG-2004
"Neglect" deja intencionalmente un hueco en la suma de fracciones molares
(no renormaliza sobre el total restante), mientras GERG-2008 "Neglect" SI
renormaliza sobre el total restante (igual que AGA8-DETAIL/AGA-10, ver
`normas/AGA_8.py`). Por eso `calcular_propiedades_gas`/`calcular_flash` de
este archivo (que son alias directos de GERG_2008.py, sin logica propia)
DEBEN recibir la composicion ya plegada con
`GERG_2008.aplicar_modo_neo_pentano_gerg()` (NO con
`AGA_8.aplicar_modo_neo_pentano()`, que es la que usan GERG-2008 Gas/Flash y
AGA8 GERG) -- `interfaz_calculo_flujo.py` ya llama a la funcion correcta por
pantalla. Esta es la UNICA diferencia de comportamiento real encontrada
entre "GERG-2004" y "GERG-2008" en toda la investigacion de este proyecto
(la relacion de "alias fino"/mismo motor sigue siendo correcta para todo lo
demas: Gas vs Flash, Add to iC5, Add to nC5, formulas, coeficientes).
===============================================================================
"""

import os as _os
import sys as _sys
import types as _types


def _cargar_motor_gerg2004():
    """Ejecuta el codigo de GERG_2008.py como un modulo aparte que importa los datos de GERG-2004
    (`_gerg2004_data_generado`). GERG-2008 no se modifica: cada norma tiene su propio estado."""
    nombre = __name__.rpartition(".")[0] + "._gerg2004_motor"
    if nombre in _sys.modules:
        return _sys.modules[nombre]
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "GERG_2008.py")
    with open(ruta, encoding="utf-8") as fh:
        src = fh.read()
    marca = "from ._gerg2008_data_generado import ("
    assert src.count(marca) == 1, "GERG_2008.py cambio: revisar la carga del motor GERG-2004"
    src = src.replace(marca, "from ._gerg2004_data_generado import (")
    mod = _types.ModuleType(nombre)
    mod.__file__ = ruta
    mod.__package__ = __name__.rpartition(".")[0]
    _sys.modules[nombre] = mod
    exec(compile(src, ruta, "exec"), mod.__dict__)
    # Gas ideal del H2S (indice 19): la ruta GERG-2004 de FlowXpert usa solo el termino constante.
    # Confirmado con H2S puro 298.15 K / 1000 kPa: W 297.1264 m/s y kappa 1.319038 exactos.
    mod.n0i[19][4] = 0.0
    mod.n0i[19][5] = 0.0

    # [CERTAIN, 2026-10-06, rutina real emulada (Unicorn) + capturas Nordic/Sleen/Default del libro 01] La ruta
    # GERG-2004 de FlowXpert NO normaliza la composicion: usa cada porcentaje / 100 (Nordic suma 99.9995 % y da
    # Z 0.772881 solo sin normalizar). Si la suma se aleja mas de 0.01 % de 100 % se normaliza [Guessing: la app
    # real probablemente rechaza la composicion].
    def _composicion_a_x(composicion: dict):
        total = sum(composicion.values())
        if total <= 0:
            raise ValueError("La composicion no puede sumar cero.")
        escala = 100.0 if total > 1.5 else 1.0
        if abs(total / escala - 1.0) > 1e-4:
            escala = total
        return [None] + [composicion.get(nombre, 0.0) / escala for nombre in mod.NOMBRES_COMPONENTES]
    mod._composicion_a_x = _composicion_a_x
    return mod


_motor = _cargar_motor_gerg2004()
calcular_propiedades = _motor.calcular_propiedades
calcular_flash = _motor.calcular_flash
DensityGERG = _motor.DensityGERG
PropertiesGERG = _motor.PropertiesGERG
PressureGERG = _motor.PressureGERG
MolarMassGERG = _motor.MolarMassGERG
NOMBRES_COMPONENTES = _motor.NOMBRES_COMPONENTES

calcular_propiedades_gas = calcular_propiedades  # alias explicito: pantalla "GERG-2004 Gas"

if __name__ == "__main__":
    composicion_ejemplo = {
        "Metano": 0.77824, "Nitrogeno": 0.02, "CO2": 0.06, "Etano": 0.08,
        "Propano": 0.03, "Isobutano": 0.0015, "n-Butano": 0.003,
        "Isopentano": 0.0005, "n-Pentano": 0.00165, "n-Hexano": 0.00215,
        "n-Heptano": 0.00088, "n-Octano": 0.00024, "n-Nonano": 0.00015,
        "n-Decano": 0.00009, "Hidrogeno": 0.004, "Oxigeno": 0.005,
        "CO": 0.002, "Agua": 0.0001, "H2S": 0.0025, "Helio": 0.007,
        "Argon": 0.001,
    }
    print("=== normas/GERG_2004.py -- autotest (Gas, datos GERG-2004 de FlowXpert) ===")
    r = calcular_propiedades_gas(composicion_ejemplo, 400.0, 50000.0)
    for k in ["Mm_g_mol", "D_mol_l", "Z", "Cv_J_molK", "Cp_J_molK", "W_m_s"]:
        print(f"  {k} = {r[k]:.6f}")

    print()
    print("=== normas/GERG_2004.py -- autotest (Flash, caso real Default P=100 bar(a) T=25 degC) ===")
    composicion_default = {
        "Metano": 81.315, "Nitrogeno": 14.211, "CO2": 0.99, "Etano": 2.829,
        "Propano": 0.38, "Isobutano": 0.06, "n-Butano": 0.072,
        "Isopentano": 0.018 + 0.008,  # neo-Pentano sumado a iC5
        "n-Pentano": 0.033, "n-Hexano": 0.02, "n-Heptano": 0.013, "n-Octano": 0.005,
        "Helio": 0.046,
    }
    rf = calcular_flash(composicion_default, 25.0 + 273.15, 100.0 * 100.0)
    for k, v in rf.items():
        print(f"  {k} = {v}")
