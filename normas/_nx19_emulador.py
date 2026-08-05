# -*- coding: utf-8 -*-
"""
Emulador x86 de las funciones REALES `Z_AGA_nx19`, `Z_AGA_nx19_3H` y
`Z_AGA_nx19_mod` dentro de `apk_analisis/libFXLibrary.so` (misma libreria
nativa de FlowXpert for Android que usa `_sgerg_emulador.py`), para la
pantalla NX-19 SG+GHV.

CONTEXTO (2026-07-28): se establecio con instrumentacion dinamica REAL
(Frida sobre la app corriendo en un emulador Android x86 rooteado, ver
`android_sdk_setup/` en la raiz del proyecto) que la pantalla NX-19 SG+GHV
NO llama a `Z_Sgerg_88`/SGERG-88 en absoluto -- esa era una conclusion
equivocada de sesiones anteriores (ver addendum 2026-07-27 en
`_sgerg_emulador.py`). La funcion real que se llama es `Nx19_Calc`, que
despacha asi (confirmado por 5 casos reales capturados con Frida Y por
desensamblado del despachador, direccion real Ghidra 0x142780 = raw
0x132780):

    si ptb_g9 == False: siempre `Z_AGA_nx19` (el GHV NUNCA se lee en esta
        rama -- confirmado con 4 valores de GHV distintos dando el mismo
        resultado exacto)
    si ptb_g9 == True:
        K_HIGH = 39.79999923706055 (constante real leida del binario)
        si GHV < K_HIGH: `Z_AGA_nx19_mod`
        si GHV >= K_HIGH: `Z_AGA_nx19_3H`

Las 3 funciones comparten firma real `(Z_NX19IN_T*, double*)` -- reciben
un puntero a un struct de entrada y escriben el resultado (Z,
compresibilidad) en un solo double de salida. El struct (offsets
confirmados por volcado de memoria real via Frida, en unidades SI
directas, SIN conversion): GHV_MJ_m3@0x00, CO2_frac@0x08, N2_frac@0x10,
SG@0x18, P_bar@0x20, T_degC@0x28.

METODO: igual que `_sgerg_emulador.py` -- se ejecuta el CODIGO REAL
compilado con `unicorn`, no una traduccion manual a Python (la funcion
`Z_AGA_nx19` result0 ser una ecuacion de estado completa, con multiples
llamadas a pow/exp anidadas -- del mismo orden de tamano que portar
AGA-8 DETAIL a mano -- por lo que se opto por emular el binario en vez de
transcribir cientos de instrucciones). Los PLT de `pow`/`exp` usados por
estas funciones son LOS MISMOS que ya hookea `_sgerg_emulador.py`
(0x523E0/0x523F0, confirmado byte a byte), asi que se reutiliza toda su
infraestructura de mapeo de segmentos y hooks de libm.

DEPENDENCIA: igual que `_sgerg_emulador.py` -- requiere `unicorn` instalado
y `apk_analisis/libFXLibrary.so` presente.
"""
import math
import struct

from . import _sgerg_emulador as _sg

_Z_AGA_NX19 = 0x131860
_Z_AGA_NX19_MOD = 0x132240
_Z_AGA_NX19_3H = 0x132540
_NX19_CALC = 0x132780

_GHV_UMBRAL_3H = 39.79999923706055

_RET_SENTINEL = _sg._RET_SENTINEL

# PLT adicionales que Z_AGA_nx19/_mod/_3H usan y que _sgerg_emulador.py NO
# hookea (ese modulo solo necesita sqrt/pow/exp). Direcciones RAW
# confirmadas leyendo .rel.plt + .dynsym del propio archivo (mismo
# GOT_BASE_RAW=0x3acde8 usado en toda la investigacion de esta sesion).
_PLT_ISFINITE = 0x52460
_PLT_CEIL = 0x52470
_PLT_LOG10 = 0x52480
_PLT_FMIN = 0x52490


def _instalar_hooks_extra(uc):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX

    def leer_double(uc, esp, off):
        return struct.unpack("<d", uc.mem_read(esp + off, 8))[0]

    def volver_int(uc, valor):
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_EAX, valor & 0xFFFFFFFF)
        uc.reg_write(UC_X86_REG_ESP, esp + 4)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def volver_double(uc, valor):
        # mismo bug/fix que _sgerg_emulador._instalar_hooks_libm (ver esa
        # funcion para la explicacion completa, encontrada 2026-07-29):
        # el retorno x87 real es un PUSH -- hay que decrementar TOP
        # (campo de FPSW) y escribir en el FP(TOP) resultante, no siempre
        # en FP0.
        from unicorn.x86_const import (
            UC_X86_REG_FPSW, UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2,
            UC_X86_REG_FP3, UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6,
            UC_X86_REG_FP7,
        )
        fp_regs = [UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2, UC_X86_REG_FP3,
                   UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6, UC_X86_REG_FP7]
        ext80 = _sg._doble_a_extendido80(valor)
        mantisa = ext80 & ((1 << 64) - 1)
        exponente = (ext80 >> 64) & 0xFFFF
        fpsw = uc.reg_read(UC_X86_REG_FPSW)
        top = (fpsw >> 11) & 0x7
        nuevo_top = (top - 1) & 0x7
        nuevo_fpsw = (fpsw & ~(0x7 << 11)) | (nuevo_top << 11)
        uc.reg_write(fp_regs[nuevo_top], (mantisa, exponente))
        uc.reg_write(UC_X86_REG_FPSW, nuevo_fpsw)
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def h_isfinite(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        volver_int(uc, 1 if math.isfinite(x) else 0)

    def h_ceil(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        volver_double(uc, math.ceil(x))

    def h_log10(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        volver_double(uc, math.log10(x) if x > 0 else float("-inf") if x == 0 else float("nan"))

    def h_fmin(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        y = leer_double(uc, esp, 0xC)
        volver_double(uc, min(x, y))

    uc.hook_add(UC_HOOK_CODE, h_isfinite, begin=_PLT_ISFINITE, end=_PLT_ISFINITE + 1)
    uc.hook_add(UC_HOOK_CODE, h_ceil, begin=_PLT_CEIL, end=_PLT_CEIL + 1)
    uc.hook_add(UC_HOOK_CODE, h_log10, begin=_PLT_LOG10, end=_PLT_LOG10 + 1)
    uc.hook_add(UC_HOOK_CODE, h_fmin, begin=_PLT_FMIN, end=_PLT_FMIN + 1)


def disponible():
    """True si se puede usar el emulador (mismo criterio que _sgerg_emulador)."""
    return _sg.disponible()


def _elegir_funcion(ptb_g9, ghv_mj_m3):
    if not ptb_g9:
        return _Z_AGA_NX19, "Z_AGA_nx19"
    if ghv_mj_m3 < _GHV_UMBRAL_3H:
        return _Z_AGA_NX19_MOD, "Z_AGA_nx19_mod"
    return _Z_AGA_NX19_3H, "Z_AGA_nx19_3H"


def calcular_nx19_real(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9):
    """Ejecuta la funcion NX-19 SG+GHV REAL de FlowXpert (via emulacion del
    binario real, no una reimplementacion) para los inputs dados.

    Devuelve dict con: z (compresibilidad), funcion (nombre de la variante
    real usada: Z_AGA_nx19 / Z_AGA_nx19_mod / Z_AGA_nx19_3H).

    Lanza RuntimeError si `disponible()` es False o si la emulacion no
    completa limpiamente."""
    if not disponible():
        raise RuntimeError(
            "Emulador NX-19 no disponible (falta 'unicorn' o "
            "apk_analisis/libFXLibrary.so)."
        )
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EAX
    from unicorn.unicorn import UcError

    direccion, nombre_funcion = _elegir_funcion(ptb_g9, ghv_mj_m3)

    uc, stack_base, stack_size = _sg._nueva_maquina()
    _sg._instalar_hooks_libm(uc)
    _instalar_hooks_extra(uc)

    data_struct = stack_base + stack_size - 0x3000
    out_z = stack_base + stack_size - 0x4000
    # puntero a flag "fuera de rango" (int32*, offset 0x30 del struct real,
    # confirmado desensamblando Z_AGA_nx19_3H 2026-07-29): si este puntero
    # es NULL y algun chequeo de rango (GHV/P/T/SG) falla, la funcion
    # aborta devolviendo un codigo de error en EAX (-1/-2/-3/-4) SIN
    # escribir Z. Pasando un puntero valido, la funcion marca el flag=1 y
    # SIGUE calculando con el valor dado (igual que hace el Nx19_Calc real).
    flag_ptr = stack_base + stack_size - 0x4200

    buf = bytearray(64)
    struct.pack_into("<d", buf, 0x00, ghv_mj_m3)
    struct.pack_into("<d", buf, 0x08, co2_frac)
    struct.pack_into("<d", buf, 0x10, n2_frac)
    struct.pack_into("<d", buf, 0x18, sg)
    struct.pack_into("<d", buf, 0x20, p_bar)
    struct.pack_into("<d", buf, 0x28, t_degc)
    struct.pack_into("<I", buf, 0x30, flag_ptr)
    uc.mem_write(data_struct, bytes(buf))
    uc.mem_write(out_z, bytes(8))
    uc.mem_write(flag_ptr, struct.pack("<i", 0))

    esp = stack_base + stack_size - 0x1000
    uc.mem_write(esp, struct.pack("<I", _RET_SENTINEL))
    uc.mem_write(esp + 4, struct.pack("<I", data_struct))
    uc.mem_write(esp + 8, struct.pack("<I", out_z))
    uc.reg_write(UC_X86_REG_ESP, esp)

    try:
        uc.emu_start(direccion, _RET_SENTINEL, timeout=0, count=5_000_000)
    except UcError as e:
        raise RuntimeError(f"Fallo emulando {nombre_funcion} real: {e}") from e

    eax = uc.reg_read(UC_X86_REG_EAX)
    if eax & 0x80000000:
        raise RuntimeError(
            f"{nombre_funcion} real devolvio codigo de error {eax - 0x100000000} "
            "(entrada invalida, ver desensamblado de los chequeos de rango)."
        )

    z = struct.unpack("<d", uc.mem_read(out_z, 8))[0]
    fuera_de_rango = struct.unpack("<i", uc.mem_read(flag_ptr, 4))[0] != 0
    return {"z": z, "funcion": nombre_funcion, "fuera_de_rango": fuera_de_rango}


def calcular_nx19_dispatch_real(p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac, ptb_g9):
    """Ejecuta `Nx19_Calc` REAL completo (el despachador, direccion raw
    0x132780), no las 3 subfunciones por separado como `calcular_nx19_real`.

    [CERTAIN, 2026-07-29] Necesario porque `Nx19_Calc` tiene SU PROPIO
    chequeo de rango de GHV (contra 2 constantes de .rodata, confirmado
    desensamblando 0x132780-0x132850) que escribe al MISMO puntero de
    status que luego se pasa hacia adentro de `Z_AGA_nx19_mod`/`_3H` --
    llamar a la subfuncion directo con un puntero propio (como hace
    `calcular_nx19_real`) SOLO captura el chequeo interno de la subfuncion,
    no el chequeo adicional que hace `Nx19_Calc` antes de llamarla.
    Confirmado con Frida (llamada directa a `Nx19_Calc` en el dispositivo
    real, sin pasar por la UI): con ptb_g9=True y GHV=20 o 31 MJ/m3
    (SG=0.6/P=50/T=25/N2=1%/CO2=2%), el status real es 1 ("fuera de
    rango") pero `calcular_nx19_real` con la subfuncion _mod sola daba
    fuera_de_rango=False -- discrepancia real, cerrada usando esta funcion.
    El valor de Z coincide EXACTO entre ambas formas de llamar (confirmado
    en 100 casos reales via Frida, P=1-118bar/T=-8..63degC/SG=0.56-0.90/
    N2=0-13%/CO2=0-13%/GHV=20.5-55, error 0.0% en todos) -- el status es
    lo unico que requiere el despachador completo, no el valor de Z.

    Firma real (mangled `_Z9Nx19_CalcddddddbPdPi`): Nx19_Calc(double P_bar,
    double T_degC, double SG, double GHV_MJ_m3, double N2_frac,
    double CO2_frac, bool ptb_g9, double* outZ, int* outStatus) -- 6
    doubles + bool + 2 punteros, todo por la pila (cdecl x86), confirmado
    por Frida hookeando la llamada real desde `Math_NX19_M`.

    Devuelve dict con: z, fuera_de_rango (bool, True si outStatus!=0),
    status (int crudo, por si se necesita el valor exacto)."""
    if not disponible():
        raise RuntimeError(
            "Emulador NX-19 no disponible (falta 'unicorn' o "
            "apk_analisis/libFXLibrary.so)."
        )
    from unicorn.x86_const import UC_X86_REG_ESP
    from unicorn.unicorn import UcError

    uc, stack_base, stack_size = _sg._nueva_maquina()
    _sg._instalar_hooks_libm(uc)
    _instalar_hooks_extra(uc)

    out_z = stack_base + stack_size - 0x4000
    out_status = stack_base + stack_size - 0x4100
    uc.mem_write(out_z, bytes(8))
    uc.mem_write(out_status, bytes(4))

    esp = stack_base + stack_size - 0x1000
    dobles = [p_bar, t_degc, sg, ghv_mj_m3, n2_frac, co2_frac]
    uc.mem_write(esp, struct.pack("<I", _RET_SENTINEL))
    for i, v in enumerate(dobles):
        uc.mem_write(esp + 4 + i * 8, struct.pack("<d", v))
    uc.mem_write(esp + 4 + 48, struct.pack("<I", 1 if ptb_g9 else 0))
    uc.mem_write(esp + 4 + 52, struct.pack("<I", out_z))
    uc.mem_write(esp + 4 + 56, struct.pack("<I", out_status))
    uc.reg_write(UC_X86_REG_ESP, esp)

    try:
        uc.emu_start(_NX19_CALC, _RET_SENTINEL, timeout=0, count=5_000_000)
    except UcError as e:
        raise RuntimeError(f"Fallo emulando Nx19_Calc real: {e}") from e

    z = struct.unpack("<d", uc.mem_read(out_z, 8))[0]
    status = struct.unpack("<i", uc.mem_read(out_status, 4))[0]
    return {"z": z, "fuera_de_rango": status != 0, "status": status}
