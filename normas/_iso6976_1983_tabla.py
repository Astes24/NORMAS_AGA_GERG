# -*- coding: utf-8 -*-
"""Tabla de ISO 6976:1983 tal como la usa FlowXpert (pantalla "ISO-6976 (1983)").

[CERTAIN, 2026-10-05] Valores leidos de la tabla de datos de libFXLibrary.so (offset 0x3ae780, 31 filas de 11
doubles: M, densidad relativa ideal, densidad ideal a 0 y 15 degC [kg/m3], poder calorifico superior volumetrico
ideal [kJ/m3] en las 5 referencias del selector "Cal. Val. ref. Temp." (25/0, 0/0, 15/0, 15/15, 60/60 degF) y
sqrt(b) a 0 y 15 degC). Con esta tabla el calculo reproduce a la app
FlowXpert real al 0.0000 % en Z, masa molar, densidad y poder calorifico en los 16 casos del libro 02.
Son los valores publicados de la norma; aqui solo se guardan los componentes que usa la app (la tabla de la norma
trae ademas isomeros, ciclicos y aromaticos). n-Nonano y n-Decano NO estan en ISO 6976:1983.
"""

TABLA_ISO6976_1983 = {
    "Metano": {"M": 16.0426, "d_ideal": 0.5539, "rho_ideal": [0.7157, 0.6785],
        "Hs_ideal_kJ_m3": [39724.0, 39829.0, 39766.0, 37696.0, 37620.0], "sqrt_b": [0.049, 0.0447]},
    "Etano": {"M": 30.0694, "d_ideal": 1.0382, "rho_ideal": [1.3416, 1.2717],
        "Hs_ideal_kJ_m3": [69595.0, 69759.0, 69661.0, 66035.0, 65902.0], "sqrt_b": [0.1015, 0.0927]},
    "Propano": {"M": 44.0962, "d_ideal": 1.5224, "rho_ideal": [1.9674, 1.865],
        "Hs_ideal_kJ_m3": [99048.0, 99264.0, 99135.0, 93975.0, 93788.0], "sqrt_b": [0.153, 0.1393]},
    "n-Butano": {"M": 58.123, "d_ideal": 2.0067, "rho_ideal": [2.5932, 2.4582],
        "Hs_ideal_kJ_m3": [128363.0, 128629.0, 128469.0, 121782.0, 121539.0], "sqrt_b": [0.2112, 0.1913]},
    "i-Butano": {"M": 58.123, "d_ideal": 2.0067, "rho_ideal": [2.5932, 2.4582],
        "Hs_ideal_kJ_m3": [127990.0, 128257.0, 128096.0, 121428.0, 121186.0], "sqrt_b": [0.2042, 0.1847]},
    "n-Pentano": {"M": 72.1498, "d_ideal": 2.491, "rho_ideal": [3.219, 3.0514],
        "Hs_ideal_kJ_m3": [157768.0, 158087.0, 157895.0, 149676.0, 149378.0], "sqrt_b": [0.261, 0.2366]},
    "i-Pentano": {"M": 72.1498, "d_ideal": 2.491, "rho_ideal": [3.219, 3.0514],
        "Hs_ideal_kJ_m3": [157410.0, 157730.0, 157537.0, 149336.0, 149040.0], "sqrt_b": [0.2462, 0.2238]},
    "neo-Pentano": {"M": 72.1498, "d_ideal": 2.491, "rho_ideal": [3.219, 3.0514],
        "Hs_ideal_kJ_m3": [156896.0, 157215.0, 157023.0, 148850.0, 148553.0], "sqrt_b": [0.2245, 0.2052]},
    "n-Hexano": {"M": 86.1766, "d_ideal": 2.9753, "rho_ideal": [3.8448, 3.6477],
        "Hs_ideal_kJ_m3": [187160.0, 187528.0, 187306.0, 177556.0, 177203.0], "sqrt_b": [0.3317, 0.2975]},
    "n-Heptano": {"M": 100.2034, "d_ideal": 3.4596, "rho_ideal": [4.4706, 4.2379],
        "Hs_ideal_kJ_m3": [216546.0, 216966.0, 216713.0, 205432.0, 205024.0], "sqrt_b": [0.4141, 0.367]},
    "n-Octano": {"M": 114.2302, "d_ideal": 3.9439, "rho_ideal": [5.0965, 4.8312],
        "Hs_ideal_kJ_m3": [245909.0, 246381.0, 246098.0, 233287.0, 232823.0], "sqrt_b": [0.5126, 0.4488]},
    "Hidrogeno": {"M": 2.0158, "d_ideal": 0.0696, "rho_ideal": [0.0899, 0.0852],
        "Hs_ideal_kJ_m3": [12753.0, 12789.0, 12767.0, 12102.0, 12079.0], "sqrt_b": [0.0, 0.0]},
    "CO": {"M": 28.0104, "d_ideal": 0.9671, "rho_ideal": [1.2497, 1.1846],
        "Hs_ideal_kJ_m3": [12626.0, 12618.0, 12623.0, 11966.0, 11942.0], "sqrt_b": [0.0265, 0.0224]},
    "H2S": {"M": 34.076, "d_ideal": 1.1765, "rho_ideal": [1.5203, 1.4412],
        "Hs_ideal_kJ_m3": [25098.0, 25141.0, 25114.0, 23807.0, 23760.0], "sqrt_b": [0.1077, 0.098]},
    "Helio": {"M": 4.0026, "d_ideal": 0.1382, "rho_ideal": [0.1786, 0.1693],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [-0.016, -0.016]},
    "Argon": {"M": 39.948, "d_ideal": 1.3792, "rho_ideal": [1.7823, 1.6895],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [0.0316, 0.0283]},
    "Nitrogeno": {"M": 28.0134, "d_ideal": 0.9672, "rho_ideal": [1.2498, 1.1848],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [0.0224, 0.0173]},
    "Oxigeno": {"M": 31.9988, "d_ideal": 1.1048, "rho_ideal": [1.4276, 1.3533],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [0.0316, 0.0265]},
    "CO2": {"M": 44.0098, "d_ideal": 1.5195, "rho_ideal": [1.9635, 1.8613],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [0.067, 0.0614]},
    "Agua": {"M": 18.0152, "d_ideal": 0.622, "rho_ideal": [0.8038, 0.7619],
        "Hs_ideal_kJ_m3": [0.0, 0.0, 0.0, 0.0, 0.0], "sqrt_b": [0.179, 0.17]},
}

# Z del aire de ISO 6976:1983 por temperatura de medicion [degC] (recuperado de la app real: d * Z / d_ideal).
Z_AIRE_1983 = {0: 0.99941, 15: 0.99958}
