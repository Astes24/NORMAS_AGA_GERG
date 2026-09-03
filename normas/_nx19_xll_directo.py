# -*- coding: utf-8 -*-
"""
normas/_nx19_xll_directo.py
==============================
Camino EXACTO alternativo para la pantalla "NX-19 SG+GHV+PTB G9": llama
DIRECTO (ctypes, sin Excel, SIN emulador de CPU) al despachador real
`Nx19_Calc` equivalente que vive dentro de `FlowXpert.xll` (Windows), en
vez de emular con Unicorn el binario de Android (`_nx19_emulador.py`).
Misma tecnica que `herramientas/llamada_directa_xll_sin_emulador.py` y
`normas/_aga10_xll_directo.py` (RVA + LoadLibraryW + ctypes.CFUNCTYPE).

===============================================================================
RESULTADO (2026-08-26): FUNCIONA, confirmado exacto contra `nx19_fpv_ghv()`
(camino Unicorn YA VALIDADO, `_nx19_emulador.py` -- 21+100 casos reales
capturados del dispositivo, ver docstring de `normas/NX_19.py`) en 6 casos
que cubren las 3 ramas reales del despacho (`Z_AGA_nx19`/`_mod`/`_3H`) MAS
un caso extremo de borde (donde el metodo NX-19 clasico da un Z sin
sentido fisico, 14.695 -- limite REAL y ya documentado del metodo, no un
bug de esta implementacion): TODOS coinciden EXACTOS (diferencia de punto
flotante, 0.000000%), incluyendo el flag "fuera de rango". Y es
~800-1000x MAS RAPIDO (~0-1 ms por llamada vs los ~0.87 segundos medidos
para el camino Unicorn en esta misma maquina).
===============================================================================

LA FUNCION REAL
---------------------------------------------------------------------------
`FUN_1800AE150` ("NX19_M", el callback Excel real registrado para
L"NX19_M"/"NX-19" -- ver `ANALISIS_GHIDRA_FLOWXPERT/
ghidra_todos_los_nombres_output.txt`) es, igual que `FUN_18009daf0` de
AGA-10, un wrapper que SI depende de Excel (extrae los 7 argumentos
XLOPER reales via `FUN_18005f984`/`FUN_18005f840`) -- NO es callable
directo.

Pero, a diferencia de AGA-10 (donde hacia falta un struct de 376 bytes),
aqui el wrapper extrae los 7 valores primitivos y los pasa TAL CUAL,
SIN construir ningun struct compuesto, a:

    FUN_1800C9500(double P_bar, double T_degC, double SG, double GHV_MJ_m3,
                  double N2_frac, double CO2_frac, bool ptb_g9,
                  double* outZ, int* outStatus) -> int (codigo de error)

-- confirmado por decompilacion completa (Ghidra, tipos double reales,
ver el log completo generado por `DecompileNx19Xll.java` en esta sesion).
`FUN_1800C9500` es el equivalente EXACTO de `Nx19_Calc` (el despachador ya
documentado para el .so en `_nx19_emulador.py`): internamente aplica el
MISMO chequeo de rango de GHV (constante compartida `DAT_180124430`/etc,
mismos nombres de DAT_ que ya aparecen en AGA-10, confirmando datos
compartidos entre normas dentro del mismo binario) y despacha a
`FUN_1800C979C` (la rama "alta"/3H, formula polinomica pow/exp) o
`FUN_1800C95B8`/`FUN_1800C9DB4` segun el valor de GHV -- misma logica de
3 ramas ya conocida (`Z_AGA_nx19`/`_mod`/`_3H`). NO tiene NINGUNA
dependencia de Excel (solo pow/exp/fabs y aritmetica pura) -- confirmado
leyendo su cuerpo completo, sin ninguna llamada a las funciones de
marshaling XLOPER (`FUN_18005fxxx`) que si aparecen en el wrapper.

ORDEN DE ARGUMENTOS: confirmado por la extraccion de XLOPER en
`FUN_1800AE150` (offsets +0x20,+0x40,+0x60,+0x80,+0xa0,+0xc0,+0xe0 = 7
slots de 0x20 bytes cada uno, mismo patron que AGA-10) Y por CUAL de esos
7 valores el codigo interno usa para el chequeo/dispatch de GHV (el 4to
extraido) -- coincide con el orden ya usado en la interfaz de Excel real
(Pressure, Temperature, SG, Gross Heating Val., Nitrogen Frac., CO2 Frac.,
PTB G9): P, T, SG, GHV, N2, CO2, ptb_g9. Confirmado ADEMAS empiricamente:
el caso ya validado de `normas/NX_19.py` (P=50bar/T=25degC/SG=0.6/GHV=40/
N2=1%/CO2=2%/ptb_g9=True -> Z=0.909911) reproduce EXACTO con este orden a
la primera prueba.

SEMANTICA DE SALIDA: `outStatus` (int*) es el flag "fuera de rango" --
confirmado 1:1 contra `fuera_de_rango` del camino Unicorn en los 6 casos
de prueba (0/1 coincide exacto con False/True en todos). El valor de
RETORNO de la funcion (distinto de `outStatus`) es un codigo de error
generico (0=OK en los 6 casos probados, incluido el caso extremo) -- no
se probo un caso que dispare un valor distinto de 0 en el retorno (los
chequeos de rango ya existentes en `normas/NX_19.py`, P>0/T>-273.15,
cubren los casos obvios de entrada invalida antes de llegar aqui).

===============================================================================
LIMITACIONES
===============================================================================
- Igual que `_aga10_xll_directo.py`: un ctypes.CFUNCTYPE mal armado o una
  entrada realmente extrema podria crashear el proceso Python -- probado
  contra 6 casos que cubren las 3 ramas + 1 caso extremo antes de
  integrarse a produccion, pero sin la red de seguridad de una excepcion
  Python normal para un caso verdaderamente inedito.
- No se probo el codigo de retorno != 0 (posible codigo de error generico
  de `FUN_1800C9500` para entradas invalidas mas alla de las ya validadas
  por `normas/NX_19.py` antes de llegar aqui) -- se trata como error
  generico (RuntimeError) si aparece, no se le asume un significado
  especifico.
"""
import ctypes

import pefile

XLL_PATH = r"D:\PROYECTOS FOQUS\CONFIRMACION DE CALCULOS\FlowXpert.xll"
_FUN_1800C9500 = 0x1800C9500

_func_addr = None
_func = None
_FuncType = ctypes.CFUNCTYPE(
    ctypes.c_int32,
    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.c_double, ctypes.c_double, ctypes.c_byte,
    ctypes.c_void_p, ctypes.c_void_p,
)


def disponible() -> bool:
    """True si FlowXpert.xll existe en la ruta esperada y pefile esta
    instalado -- no garantiza que la llamada vaya a funcionar (eso solo se
    sabe intentando)."""
    import os
    try:
        import pefile  # noqa: F401
    except ImportError:
        return False
    return os.path.isfile(XLL_PATH)


def _cargar_y_resolver(xll_path: str, va_ghidra: int) -> int:
    """RVA + LoadLibraryW + base real -- misma tecnica exacta que
    `herramientas/llamada_directa_xll_sin_emulador.py` y
    `normas/_aga10_xll_directo.py`."""
    pe = pefile.PE(xll_path, fast_load=True)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    rva = va_ghidra - image_base

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.LoadLibraryW.restype = ctypes.c_void_p
    kernel32.LoadLibraryW.argtypes = [ctypes.c_wchar_p]
    hmod = kernel32.LoadLibraryW(xll_path)
    if not hmod:
        raise OSError(
            f"LoadLibraryW devolvio NULL cargando {xll_path!r}, "
            f"GetLastError={ctypes.get_last_error()}"
        )
    return hmod + rva


def _get_func():
    global _func_addr, _func
    if _func is None:
        _func_addr = _cargar_y_resolver(XLL_PATH, _FUN_1800C9500)
        _func = _FuncType(_func_addr)
    return _func


def calcular_nx19_directo(p_bar: float, t_degc: float, sg: float, ghv_mj_m3: float,
                           n2_frac: float, co2_frac: float, ptb_g9: bool) -> dict:
    """Llama DIRECTO (ctypes, sin Excel, sin emulador de CPU) a
    `FUN_1800C9500` dentro de FlowXpert.xll -- equivalente exacto de
    `Nx19_Calc`, ver docstring del modulo para la evidencia de validacion.

    Devuelve dict con `z` (compresibilidad) y `fuera_de_rango` (bool) --
    mismas claves relevantes que `_nx19_emulador.calcular_nx19_dispatch_real`.
    Lanza RuntimeError si el codigo de retorno de la funcion real es
    distinto de 0 (fallo generico, no confundir con `fuera_de_rango`, que
    es un flag separado que puede ser True con retorno 0)."""
    func = _get_func()
    out_z = ctypes.c_double(-999.0)
    out_status = ctypes.c_int32(0)
    codigo = func(
        ctypes.c_double(p_bar), ctypes.c_double(t_degc), ctypes.c_double(sg),
        ctypes.c_double(ghv_mj_m3), ctypes.c_double(n2_frac), ctypes.c_double(co2_frac),
        ctypes.c_byte(1 if ptb_g9 else 0),
        ctypes.byref(out_z), ctypes.byref(out_status),
    )
    if codigo != 0:
        raise RuntimeError(
            f"FUN_1800C9500 (Nx19_Calc real, llamada directa .xll) devolvio "
            f"codigo de error {codigo} para P={p_bar} T={t_degc} SG={sg} "
            f"GHV={ghv_mj_m3} N2={n2_frac} CO2={co2_frac} ptb_g9={ptb_g9}."
        )
    return {"z": out_z.value, "fuera_de_rango": out_status.value != 0}
