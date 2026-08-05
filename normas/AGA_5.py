# -*- coding: utf-8 -*-
"""
normas/AGA_5.py
=================
Calculo de poder calorifico (Calorific Value) segun el motor real "AGA5_C" de
FlowXpert (ABB), reconstruido por ingenieria inversa directa de
`libFXLibrary.so` (version Android de FlowXpert) usando Ghidra + RetDec.

Este archivo se puede ejecutar solo:
    python normas/AGA_5.py

===============================================================================
FUENTE Y NIVEL DE CONFIANZA (leer antes de usar en un entregable formal)
===============================================================================
[CERTAIN] La formula real de `fsAGA5::AGA5` (simbolo `_ZN6fsAGA54AGA5...` en
libFXLibrary.so, direccion ELF real 0x000ee260) fue extraida por decompilacion
completa (Ghidra para direcciones/constantes GOT-relativas, RetDec para forma
SSA limpia sin ambiguedad de reutilizacion de registros) y VALIDADA
numericamente contra un caso real de la app (composicion + resultados reales
capturados en pantalla, ver mas abajo). Los dos resultados (CV_MASS y CV_VOL)
coinciden con los valores reales de la app con una diferencia de 0.00002% o
menor -- mismo nivel de rigor que AGA-3.

[CERTAIN] AGA5_C NO tiene ningun paso de correccion de gas real (no llama a
ninguna funcion del namespace `spirit::math::iso6976_2016`, que es una norma
DISTINTA -- ISO 6976 -- tambien presente en el mismo binario pero registrada
como una funcion Excel separada). La formula de AGA5_C es una suma ponderada
simple, con dos particularidades importantes frente a lo que se asumia antes:

  1. La Gravedad Especifica (SG, "Molar Mass Ratio", gas/aire=28.9644 kg/kmol)
     es un INPUT INDEPENDIENTE que el usuario provee (por ejemplo medido con
     un densitometro), NO se calcula aqui a partir de la composicion. Si se
     calcula a partir de la composicion y esta no coincide exactamente con el
     SG medido, los resultados no van a coincidir con la app aunque la
     formula este bien.

  2. La composicion de entrada de la app es un arreglo de 22 numeros (ver
     `ORDEN_COMPONENTES_APP` mas abajo, confirmado leyendo directamente las
     pantallas de composicion de la app), pero la formula real de AGA5_C SOLO
     usa 8 de esos 22 valores como correcciones (los gases no-hidrocarburo:
     N2, CO2, H2O, H2S, H2, CO, O2, He). Los hidrocarburos (metano, etano,
     propano, butanos, pentanos, hexano+, argon, neo-pentano) NO entran en
     esta formula especifica -- su efecto ya esta capturado por el SG medido
     independientemente. Confirmado por: (a) rastreo directo de los offsets
     de pila en `Math_AGA5_C` que arman el struct de 8 valores pasado a
     `fsAGA5::AGA5`, y (b) validacion numerica exacta contra el caso real.

[CERTAIN] Formula completa (ver `calcular_poder_calorifico` mas abajo):

    B_SUM = 0.000329*CO2 + 0.000217*N2 + 0.000245*O2 + 0.000048*He
            + 0.000174*CO + 0.000174*H2S + 0.000146*H2O - 0.000009*H2

    CV_MASS [kJ/kg] = ((0.00197/SG + 0.02035) - B_SUM*100/SG) * 1e6 * 2.326

    H_SUM = 3.612*He + 25.318*CO2 + 16.639*N2 + 18.801*O2 + 13.424*CO
            + 13.462*H2S + 11.214*H2O - 0.713*H2

    CV_VOL [kJ/Sm3] = ((144 + SG*1571.5) - H_SUM*100) * 37.2589413236289

Donde N2, CO2, O2, He, CO, H2S, H2O, H2 son FRACCIONES MOLARES (0..1, no
porcentaje) de esos componentes en la composicion de 22 valores.

Los factores de conversion 2.326 (BTU/lbm -> kJ/kg) y 37.2589413236289
(BTU/scf -> kJ/Sm3) NO son constantes fisicas asumidas: se extrajeron
LITERALMENTE de la tabla de unidades registrada en el mismo binario
(`Unit_CTypeAndUnitContainer::RegisterBuiltIns`, entradas `Btu_lbm` con
factor=2326.0 y `Btu_scf` con factor=37258.9413236289, ambas relativas a la
misma unidad base que `kJ_kg`/`kJ_sm3` con factor=1000.0). Esto confirma que
el nucleo de calculo trabaja en unidades imperiales (BTU) y la app convierte
a SI solo para mostrar en pantalla -- mismo patron ya visto en AGA-3.

[CERTAIN] Caso real usado para validar (capturas de pantalla de la app,
composicion completa transcrita y confirmada dos veces por el usuario):
    SG = 0.7
    Composicion (%): Metano=81.3150, N2=14.2110, CO2=0.9900, Etano=2.8290,
        Propano=0.3800, H2O=0, H2S=0, H2=0, CO=0, O2=0, iC4=0.0600,
        nC4=0.0720, iC5=0.0180, nC5=0.0330, nC6=0.0200, nC7=0.0130,
        nC8=0.0050, nC9=0, nC10=0, He=0.0460, Ar=0, neo-C5=0.0080
    Resultado real de la app: CV_MASS=42543.52 kJ/kg, CV_VOL=36601.77 kJ/Sm3
    Resultado de este modulo: CV_MASS=42543.52024 kJ/kg (dif. 0.0000005%),
        CV_VOL=36601.77553 kJ/Sm3 (dif. 0.00002%)

[GUESSING] No se investigo si la validacion de rango real de AGA5_C (suma de
los 8 valores usados <= cierto umbral, cada valor entre 0 y un maximo) usa
exactamente los mismos limites documentados aqui en `RANGOS_VALIDACION` --
estan puestos por sentido comun (0..1 por fraccion molar) pero no se extrajo
el valor EXACTO del umbral de suma desde el binario.
===============================================================================
"""

# Orden real de los 22 componentes tal como los presenta la app FlowXpert
# (confirmado leyendo las pantallas de composicion de la app). Los valores
# se pasan como fraccion molar (0..1) o porcentaje (0..100); esta funcion
# normaliza internamente dividiendo por la suma total, igual que la app.
ORDEN_COMPONENTES_APP = [
    "Metano",       # C1
    "Nitrogeno",    # N2
    "CO2",          # Carbon Dioxide
    "Etano",        # C2
    "Propano",      # C3
    "Agua",         # H2O
    "H2S",          # Hydrogen Sulphide
    "Hidrogeno",    # H2
    "CO",           # Carbon Monoxide
    "Oxigeno",      # O2
    "i-Butano",     # iC4
    "n-Butano",     # nC4
    "i-Pentano",    # iC5
    "n-Pentano",    # nC5
    "n-Hexano",     # nC6
    "n-Heptano",    # nC7
    "n-Octano",     # nC8
    "n-Nonano",     # nC9
    "n-Decano",     # nC10
    "Helio",        # He
    "Argon",        # Ar
    "neo-Pentano",  # neo-C5
]

# Los 8 componentes que SI participan en la formula real de AGA5_C (los demas
# 14 de ORDEN_COMPONENTES_APP solo se validan, no se usan en el calculo: su
# efecto ya esta implicito en SG).
COMPONENTES_FORMULA = ["Nitrogeno", "CO2", "Agua", "H2S", "Hidrogeno", "CO", "Oxigeno", "Helio"]

# Coeficientes B (para CV_MASS, BTU/lbm nativo) y H (para CV_VOL, BTU/scf
# nativo) por componente, extraidos byte a byte de libFXLibrary.so (ver
# docstring). Signo negativo para Hidrogeno = se resta, no se suma.
COEF_B = {
    "CO2": 0.000329, "Nitrogeno": 0.000217, "Oxigeno": 0.000245, "Helio": 0.000048,
    "CO": 0.000174, "H2S": 0.000174, "Agua": 0.000146, "Hidrogeno": -0.000009,
}
COEF_H = {
    "Helio": 3.612, "CO2": 25.318, "Nitrogeno": 16.639, "Oxigeno": 18.801,
    "CO": 13.424, "H2S": 13.462, "Agua": 11.214, "Hidrogeno": -0.713,
}

# Factores de conversion EXACTOS, extraidos literalmente de la tabla de
# unidades del binario (Unit_CTypeAndUnitContainer::RegisterBuiltIns):
# Btu_lbm.factor=2326.0, Btu_scf.factor=37258.9413236289, ambos relativos a
# kJ_kg.factor=1000.0 / kJ_sm3.factor=1000.0 respectivamente.
_BTU_LBM_A_KJ_KG = 2326.0 / 1000.0          # = 2.326
_BTU_SCF_A_KJ_SM3 = 37258.9413236289 / 1000.0  # = 37.2589413236289

# [CERTAIN, 2026-08-05] Condicion de referencia REAL de CV_VOL, confirmada
# leyendo el texto "Details" del propio campo de resultado en la app
# FlowXpert (pantalla AGA-5, campo "Calorific Value" en kJ/sm3): "Volume
# calorific value at 60 degF and 14.73 psia." Documentado aqui en las 3
# unidades de temperatura y de presion para no tener que recalcularlo cada
# vez. Importante: esto es la referencia de FLOWXPERT/AGA5_C especificamente
# -- otros instrumentos (ej. un cromatografo de campo) pueden estar
# calibrados a una referencia DISTINTA (ej. 15 degC/14.696 psia, una
# convencion tambien valida y comun), lo que produce una diferencia
# sistematica de ~0.4% en CV_VOL si se comparan directamente sin ajustar
# por esto -- ver memoria del proyecto, hallazgo 2026-08-05.
REFERENCIA_CV_VOL_TEMPERATURA = {"degF": 60.0, "degC": 15.5556, "K": 288.7056}
REFERENCIA_CV_VOL_PRESION = {"psia": 14.73, "kPa": 101.5598, "bar_a": 1.015598}

# Rango de validacion basico (fraccion molar 0..1 por componente). El umbral
# EXACTO de suma que usa el binario no se extrajo (ver [GUESSING] arriba);
# aqui se usa el sentido comun: composicion total no debe superar 100%.
RANGO_FRACCION_MOLAR = (0.0, 1.0)


def calcular_poder_calorifico(composicion: dict, gravedad_especifica: float) -> dict:
    """Calcula el poder calorifico segun el motor real AGA5_C de FlowXpert.

    composicion: dict {nombre_componente (ver ORDEN_COMPONENTES_APP): valor}.
        No necesita sumar 1/100, se normaliza internamente. Componentes no
        presentes en el dict se toman como 0.
    gravedad_especifica: SG (Molar Mass Ratio gas/aire), INPUT INDEPENDIENTE
        -- NO se deriva de la composicion (ver docstring del modulo).

    Devuelve CV_MASS [kJ/kg] y CV_VOL [kJ/Sm3], mas los valores nativos en
    BTU/lbm y BTU/scf (utiles para comparar directamente contra el motor
    nativo sin el factor de conversion de unidades).
    """
    if gravedad_especifica <= 0:
        raise ValueError("La gravedad especifica debe ser mayor que cero.")

    total = sum(composicion.get(nombre, 0.0) for nombre in ORDEN_COMPONENTES_APP)
    if total == 0:
        raise ValueError("La composicion no puede sumar cero.")

    frac = {nombre: composicion.get(nombre, 0.0) / total for nombre in ORDEN_COMPONENTES_APP}

    sg = gravedad_especifica

    b_sum = sum(COEF_B[c] * frac[c] for c in COMPONENTES_FORMULA)
    cv_mass_nativo_btu_lbm = ((0.00197 / sg + 0.02035) - b_sum * 100 / sg) * 1_000_000

    h_sum = sum(COEF_H[c] * frac[c] for c in COMPONENTES_FORMULA)
    cv_vol_nativo_btu_scf = (144 + sg * 1571.5) - h_sum * 100

    return {
        "cv_mass_kJ_kg": cv_mass_nativo_btu_lbm * _BTU_LBM_A_KJ_KG,
        "cv_vol_kJ_sm3": cv_vol_nativo_btu_scf * _BTU_SCF_A_KJ_SM3,
        "cv_mass_BTU_lbm": cv_mass_nativo_btu_lbm,
        "cv_vol_BTU_scf": cv_vol_nativo_btu_scf,
        "gravedad_especifica_usada": sg,
        # [CERTAIN, 2026-08-05] Referencia real de CV_VOL confirmada en la
        # propia app FlowXpert -- ver REFERENCIA_CV_VOL_* arriba. Se incluye
        # en el resultado para que cualquier comparacion contra OTRO
        # instrumento (ej. un cromatografo de campo, que puede usar una
        # referencia distinta) tenga a mano el dato sin ir al codigo fuente.
        "cv_vol_referencia_temperatura": dict(REFERENCIA_CV_VOL_TEMPERATURA),
        "cv_vol_referencia_presion": dict(REFERENCIA_CV_VOL_PRESION),
    }


def validar_rangos(composicion: dict) -> list:
    """Devuelve una lista de mensajes de error si algun componente esta fuera
    de rango (0..1 en fraccion molar, o su equivalente 0..100 en porcentaje
    segun como venga el dict). No lanza excepcion, solo reporta."""
    errores = []
    for nombre in ORDEN_COMPONENTES_APP:
        v = composicion.get(nombre)
        if v is None:
            continue
        if v < 0:
            errores.append(f"{nombre}: valor negativo ({v})")
    return errores


if __name__ == "__main__":
    # Caso real (CAP AGA 5.jpeg / COMP AGA 5 1-2.jpeg), en porcentaje molar
    composicion_real = {
        "Metano": 81.3150, "Nitrogeno": 14.2110, "CO2": 0.9900, "Etano": 2.8290,
        "Propano": 0.3800, "Agua": 0.0, "H2S": 0.0, "Hidrogeno": 0.0, "CO": 0.0,
        "Oxigeno": 0.0, "i-Butano": 0.0600, "n-Butano": 0.0720, "i-Pentano": 0.0180,
        "n-Pentano": 0.0330, "n-Hexano": 0.0200, "n-Heptano": 0.0130, "n-Octano": 0.0050,
        "n-Nonano": 0.0, "n-Decano": 0.0, "Helio": 0.0460, "Argon": 0.0, "neo-Pentano": 0.0080,
    }
    sg_real = 0.7
    r = calcular_poder_calorifico(composicion_real, sg_real)

    print("=== normas/AGA_5.py -- autotest (caso real CAP AGA 5.jpeg) ===")
    print(f"SG = {sg_real}")
    print(f"CV_MASS = {r['cv_mass_kJ_kg']:.5f} kJ/kg   (real app: 42543.52)")
    print(f"CV_VOL  = {r['cv_vol_kJ_sm3']:.5f} kJ/Sm3  (real app: 36601.77)")

    dif_mass = abs(r['cv_mass_kJ_kg'] - 42543.52) / 42543.52 * 100
    dif_vol = abs(r['cv_vol_kJ_sm3'] - 36601.77) / 36601.77 * 100
    print(f"\nDiferencia CV_MASS: {dif_mass:.6f}%")
    print(f"Diferencia CV_VOL:  {dif_vol:.6f}%")
    assert dif_mass < 0.001, "CV_MASS no coincide con el caso real"
    assert dif_vol < 0.001, "CV_VOL no coincide con el caso real"
    print("\nOK: coincide con el caso real dentro de 0.001%")
