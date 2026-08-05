# -*- coding: utf-8 -*-
"""
Emulador x86 de las funciones reales `sgerg0`..`sgerg4` (SGERG-88) dentro de
`apk_analisis/libFXLibrary.so` (libreria nativa de FlowXpert for Android),
usado para calcular "PTB G9 Correction" con el algoritmo REAL de ABB en vez
de una aproximacion en Python.

CONTEXTO (ver seccion "SGERG-88"/"PTB G9" del docstring de normas/NX_19.py
para el detalle completo de la investigacion, 2026-07-25):
  - La pantalla NX-19 SG+GHV de FlowXpert usa SGERG-88, con un interruptor
    "PTB G9 Correction" (0/1) cuyo significado NUNCA se encontro documentado
    en fuente publica (se investigaron TR-G9/DVGW G685-6 de la PTB alemana,
    ninguno contiene una formula que coincida).
  - Se encontraron en el binario 5 variantes reales `sgerg0`..`sgerg4`
    (funcion `Z_Sgerg_88` las despacha segun un campo "modo" 0-4 del struct
    de entrada `Z_SGERG_DATA_T`). Probando las 5 contra datos reales de la
    app (no adivinando), se determino empiricamente:
        PTB G9=0  <->  sgerg3 (modo 3)
        PTB G9=1  <->  sgerg2 (modo 2)
    Error medido contra 13 casos reales: 0.0001%-0.53% (mejor cerca de la
    composicion de referencia SG=0.6/N2=1%/CO2=2%/GHV=40, peor a presion
    alta o composicion lejana -- ver docstring de NX_19.py para la tabla
    completa). Se agotaron las hipotesis de por que no es exacto (ver abajo
    "LIMITE DE PRECISION").

METODO: en vez de reimplementar el algoritmo en Python (se intento -- el
puerto basado en pygerg/SGERG-88 clasico NO coincide exactamente con lo que
hace el binario real, converge a un H distinto en el lazo de Newton), se
ejecuta el CODIGO REAL con un emulador de CPU (unicorn) sobre los segmentos
PT_LOAD del .so, con:
  - Un area TLS minima para que el canario de pila (%gs:0x14) no falle.
  - Hooks manuales de las 3 unicas funciones externas reales que este
    algoritmo necesita (sqrt/pow/exp de libm, resueltas via PLT/GOT que no
    podemos religar sin un linker dinamico real).

LIMITE DE PRECISION (no resuelto, agotado 2026-07-25): el error de 0.02%-
0.5% remanente NO se debe (confirmado empiricamente):
  - a que el despachador Z_Sgerg_88 haga algo mas alla de llamar a sgergN
    (se probo llamando Z_Sgerg_88 completo vs sgergN directo -- resultado
    identico);
  - a un uso oculto del campo N2 de entrada (se confirmo que sgerg2/sgerg3
    lo leen una sola vez, en un chequeo, y no en el resto de la funcion);
  - a la constante de conversion degC->K (se probo 273.15/273.16/273.0,
    273.15 ya es la mejor).
Se concluyo que es una limitacion real y no resuelta del propio algoritmo
de ABB (consistente con lo que advierte el reporte DVGW sobre la perdida de
precision de SGERG-88 fuera de su rango de calibracion), no un error de
esta implementacion.

DEPENDENCIA: requiere el paquete `unicorn` (pip install unicorn) y el
archivo `apk_analisis/libFXLibrary.so` presente junto al proyecto. Si
cualquiera de los dos falta, `disponible()` devuelve False y el llamador
debe usar el fallback en Python puro (`calcular_sgerg88` en NX_19.py, que
solo es exacto para "PTB G9=0" clasico, no para "PTB G9=1").

INTENTO DE MEJORA 2026-07-27 (no aplicado -- empeoro el resultado, ver
abajo): se reabrio la investigacion del limite de precision. Hallazgos
reales, confirmados, que vale la pena dejar registrados aunque el intento
de arreglo no funciono:

  1. TRAMPA DE ESPACIOS DE DIRECCION: el proyecto Ghidra de
     apk_analisis/ghidra_project/libFX usa un "Image Base" de 0x00010000
     (confirmado via currentProgram.getImageBase()). Cualquier direccion
     que se lea de Ghidra (decompilador, disassembler, symbol table) esta
     desplazada +0x10000 respecto a la direccion real dentro del archivo
     .so (la que usan _vaddr_a_offset() y unicorn en este modulo). Ejemplo
     verificado: el simbolo real "Z_Sgerg_88" aparece en Ghidra como
     0x00144BF0, pero en el espacio de direcciones de ESTE modulo (el que
     importa para _Z_SGERG_88 de arriba) es 0x134BF0 -- exactamente la
     constante que ya estaba puesta. Es decir: la direccion actual YA
     apuntaba a la funcion real; una sesion de RE con Ghidra que no reste
     0x10000 antes de comparar con este modulo llega a la conclusion falsa
     de que se esta llamando a otra funcion. Si se retoma el analisis con
     Ghidra headless, restar siempre 0x10000 antes de usar una direccion
     aqui.

  2. FORMULA REAL DEL WRAPPER (Math_SGERG_C, direccion Ghidra 0x836a0 =
     real 0x826a0, no llamado directamente por este modulo -- este modulo
     llama a Z_Sgerg_88 saltandose el wrapper): antes de llamar a
     Z_Sgerg_88, Math_SGERG_C llena Z_SGERG_DATA_T con VALORES DERIVADOS,
     no los valores crudos de entrada:
       offset 0x00 (T): grados Celsius directos (NO Kelvin -- el chequeo
         de rango de CheckSgerg88InputRange en este campo es [-8, 62], o
         sea Celsius, no Kelvin).
       offset 0x08 (P): bar (constante real 0.0689476 = psi->bar, pero si
         la entrada ya esta en bar no hace falta aplicarla).
       offset 0x10 (SG): SG_crudo * 1.0002 (factor de correccion pequeno,
         constante real leida del binario).
       offset 0x18 (N2): fraccion molar cruda, sin transformar.
       offset 0x20 (CO2): fraccion molar cruda, sin transformar.
       offset 0x28 (H2): fraccion molar cruda, sin transformar.
       offset 0x30 (GHV): GHV_crudo * K, con K in
         {0.03926629422718808, 0.03925167535368578} segun un selector
         adicional del wrapper (no confirmado si es el mismo switch que
         "PTB G9" o algo distinto -- ver punto 4).
       offset 0x38: CONSTANTE FIJA -273.15 (no depende de ningun input;
         se presume que Z_Sgerg_88 la usa internamente para pasar de
         Celsius a Kelvin: T_K = T_C - campo[0x38]).
     Estas formulas se confirmaron leyendo los valores reales de las
     constantes desde el .so (no adivinando), en el espacio de
     direcciones correcto (GOT base real = 0x3acde8).

  3. SE PROBARON estas formulas corregidas contra los 12 casos reales
     (P=30-110bar, T=40-50degC, SG=0.6/0.7, con/sin N2/CO2, PTB G9=0/1,
     GHV=37.96) y el error EMPEORO a 0.07%-1.2% (peor que el 0.0001%-0.53%
     documentado antes). Ademas, con estas correcciones, SOLO el modo 3
     del campo [0x40] devuelve un resultado no-nulo -- los modos 0, 1, 2 y
     4 devuelven Z=0.0 (silencioso, sin excepcion) para las mismas
     entradas, sin causa identificada (probablemente falta un hook de
     libm/PLT adicional que esos modos necesitan y el modo 3 no). Esto
     bloquea aislar el mecanismo real de "PTB G9": con el modo fijo en 3,
     cambiar la constante GHV (0.039266 vs 0.039252) entre los casos
     PTB=0/1 dio un resultado IDENTICO en ambos casos -- el campo GHV
     derivado no parece influir en el resultado del modo 3 en absoluto,
     lo que sugiere que el switch real de "PTB G9" pasa por uno de los
     modos rotos (0/1/2/4), no por el campo GHV ni por el modo 3.

  4. Por lo anterior, EL CODIGO ACTUAL DE ESTE MODULO NO SE MODIFICO --
     sigue exactamente como estaba (direccion 0x134BF0 sin cambios, struct
     con T en Kelvin y GHV/SG crudos, tal como funcionaba antes de esta
     investigacion). Las formulas del punto 2 son un punto de partida
     verificado para una futura sesion, pero aplicarlas tal cual, sin
     ademas resolver por que los modos 0/1/2/4 fallan, empeora el
     resultado. Pistas para seguir: identificar que hook falta (probar
     hooks adicionales de libm como log/log10/fabs/floor, o revisar si
     alguno de esos modos llama a una funcion interna del .so aun no
     mapeada/hookeada) usando UC_HOOK_MEM_INVALID para capturar la
     direccion exacta de fallo en modo 0, 1, 2 y 4 (a diferencia del
     intento con Z_Sgerg_88 en la direccion Ghidra 0x144bf0 -- que en este
     espacio de direcciones es una zona sin mapear, no confundir con este
     punto), antes de volver a tocar las formulas de campos.
"""
import os
import struct
import math

_RUTA_SO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "apk_analisis",
    "libFXLibrary.so",
)

# Direcciones reales (confirmadas por desensamblado + ejecucion) dentro de
# libFXLibrary.so v1.6.0:
_Z_SGERG_88 = 0x134BF0
_PLT_SQRT = 0x523D0
_PLT_POW = 0x523E0
_PLT_EXP = 0x523F0

_RET_SENTINEL = 0x7F000000

_MODO_PTB_G9 = {False: 3, True: 2}  # sgerg3=PTB G9:0 ; sgerg2=PTB G9:1

_elf_bytes = None
_segmentos = None


def disponible():
    """True si se puede usar el emulador (unicorn instalado y el .so
    presente). No lanza excepcion si falta algo."""
    try:
        import unicorn  # noqa: F401
    except ImportError:
        return False
    return os.path.isfile(_RUTA_SO)


def _cargar_elf():
    global _elf_bytes, _segmentos
    if _elf_bytes is not None:
        return
    with open(_RUTA_SO, "rb") as f:
        _elf_bytes = f.read()
    e_phoff = struct.unpack_from("<I", _elf_bytes, 28)[0]
    e_phentsize = struct.unpack_from("<H", _elf_bytes, 42)[0]
    e_phnum = struct.unpack_from("<H", _elf_bytes, 44)[0]
    segs = []
    for i in range(e_phnum):
        b = e_phoff + i * e_phentsize
        p_type, p_offset, p_vaddr, _paddr, p_filesz, p_memsz, _flags, _align = struct.unpack_from(
            "<IIIIIIII", _elf_bytes, b
        )
        if p_type == 1:  # PT_LOAD
            segs.append((p_vaddr, p_offset, p_filesz, p_memsz))
    _segmentos = segs


def _vaddr_a_offset(vaddr):
    for pv, po, pf, _pm in _segmentos:
        if pv <= vaddr < pv + pf:
            return po + (vaddr - pv)
    return None


def _doble_a_extendido80(valor):
    """Convierte un double de Python al entero de 80 bits que unicorn espera
    para escribir un registro ST(n) del x87 (usado por el valor de retorno
    de sqrt/pow/exp segun el ABI cdecl de 32 bits)."""
    bits = struct.unpack("<Q", struct.pack("<d", valor))[0]
    signo = (bits >> 63) & 1
    exp = (bits >> 52) & 0x7FF
    mant = bits & ((1 << 52) - 1)
    if exp == 0 and mant == 0:
        return signo << 79
    if exp == 0x7FF:
        ext_mant = (1 << 63) if mant == 0 else (1 << 63) | (mant << 11)
        return (signo << 79) | (0x7FFF << 64) | ext_mant
    exp_ext = exp - 1023 + 16383
    mant_ext = (1 << 63) | (mant << 11)
    return (signo << 79) | (exp_ext << 64) | mant_ext


def _nueva_maquina():
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import (
        UC_X86_REG_GDTR, UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES,
        UC_X86_REG_SS, UC_X86_REG_GS,
    )

    _cargar_elf()
    uc = Uc(UC_ARCH_X86, UC_MODE_32)

    def alinear_abajo(x, a=0x1000):
        return x & ~(a - 1)

    def alinear_arriba(x, a=0x1000):
        return (x + a - 1) & ~(a - 1)

    for vaddr, offset, filesz, memsz in _segmentos:
        lo = alinear_abajo(vaddr)
        hi = alinear_arriba(vaddr + max(filesz, memsz))
        uc.mem_map(lo, hi - lo)
        uc.mem_write(vaddr, _elf_bytes[offset : offset + filesz])

    stack_base = 0x60000000
    stack_size = 0x100000
    uc.mem_map(stack_base, stack_size)

    tls_base = 0x70000000
    uc.mem_map(tls_base, 0x1000)
    uc.mem_write(tls_base + 0x14, struct.pack("<I", 0xDEADBEEF))

    gdt_base = 0x71000000
    uc.mem_map(gdt_base, 0x1000)

    def entrada_gdt(base, limite, acceso, flags):
        e = bytearray(8)
        e[0] = limite & 0xFF
        e[1] = (limite >> 8) & 0xFF
        e[6] = (limite >> 16) & 0xF
        e[2] = base & 0xFF
        e[3] = (base >> 8) & 0xFF
        e[4] = (base >> 16) & 0xFF
        e[7] = (base >> 24) & 0xFF
        e[5] = acceso
        e[6] |= flags << 4
        return bytes(e)

    gdt = (
        bytes(8)
        + entrada_gdt(0, 0xFFFFF, 0x9A, 0xC)
        + entrada_gdt(0, 0xFFFFF, 0x92, 0xC)
        + entrada_gdt(tls_base, 0xFFFFF, 0x92, 0xC)
    )
    uc.mem_write(gdt_base, gdt)
    uc.reg_write(UC_X86_REG_GDTR, (0, gdt_base, len(gdt) - 1, 0))
    uc.reg_write(UC_X86_REG_CS, (1 << 3) | 0)
    uc.reg_write(UC_X86_REG_DS, (2 << 3) | 0)
    uc.reg_write(UC_X86_REG_ES, (2 << 3) | 0)
    uc.reg_write(UC_X86_REG_SS, (2 << 3) | 0)
    uc.reg_write(UC_X86_REG_GS, (3 << 3) | 0)

    return uc, stack_base, stack_size


def _instalar_hooks_libm(uc):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import (
        UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_FPSW,
        UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2, UC_X86_REG_FP3,
        UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6, UC_X86_REG_FP7,
    )

    _FP_REGS = [UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2, UC_X86_REG_FP3,
                UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6, UC_X86_REG_FP7]

    def leer_double(uc, esp, off):
        return struct.unpack("<d", uc.mem_read(esp + off, 8))[0]

    def volver(uc, valor):
        # BUG REAL encontrado 2026-07-29 (dos capas, la segunda es la causa
        # de fondo): (1) escribir UC_X86_REG_ST0 con un entero plano de 80
        # bits pierde el exponente/signo -- corregido usando UC_X86_REG_FP0
        # con tupla (mantisa,exponente). Pero (2) FP0 es el registro FISICO
        # 0, no "ST0 logico" -- la convencion real de retorno x87 (usada
        # por pow/sqrt/exp compilados) es un PUSH: el TOP-of-stack (campo
        # de 3 bits en FPSW, bits 11-13) se decrementa y el valor se
        # guarda en el NUEVO FP(TOP). Escribir siempre FP0 sin tocar TOP
        # solo era correcto por casualidad cuando TOP ya estaba en 1 antes
        # del push; en llamadas posteriores dentro de la misma funcion
        # (TOP ya modificado por llamadas previas) el valor quedaba en el
        # registro fisico equivocado, y la siguiente FSTP/FLD leia un
        # registro no inicializado (0.0) en vez del resultado real.
        # Confirmado instrumentando Z_AGA_nx19_fpv_and_z: FPSW/TOP valia
        # 0, 2 y 3 en 3 llamadas sucesivas a pow() dentro de la MISMA
        # ejecucion. Con el push correcto, la emulacion de
        # Z_AGA_nx19_fpv_and_z reproduce el Z real exacto (0.9005676048370888
        # vs 0.9005676048370887 real, diferencia de 1 ULP por precision de
        # 64 vs 80 bits en el propio pow de Python). Este bug explica el
        # residual "cerca pero no exacto" de TODAS las funciones que
        # dependen de sqrt/pow/exp via estos hooks (SGERG-88 y NX-19 por
        # igual) -- no era un limite del algoritmo real ni del .init_array,
        # era este bug de emulacion.
        ext80 = _doble_a_extendido80(valor)
        mantisa = ext80 & ((1 << 64) - 1)
        exponente = (ext80 >> 64) & 0xFFFF
        fpsw = uc.reg_read(UC_X86_REG_FPSW)
        top = (fpsw >> 11) & 0x7
        nuevo_top = (top - 1) & 0x7
        nuevo_fpsw = (fpsw & ~(0x7 << 11)) | (nuevo_top << 11)
        uc.reg_write(_FP_REGS[nuevo_top], (mantisa, exponente))
        uc.reg_write(UC_X86_REG_FPSW, nuevo_fpsw)
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def h_sqrt(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        volver(uc, math.sqrt(x) if x >= 0 else float("nan"))

    def h_pow(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        y = leer_double(uc, esp, 0xC)
        try:
            r = math.pow(x, y)
        except ValueError:
            r = float("nan")
        volver(uc, r)

    def h_exp(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_double(uc, esp, 4)
        volver(uc, math.exp(x))

    uc.hook_add(UC_HOOK_CODE, h_sqrt, begin=_PLT_SQRT, end=_PLT_SQRT + 1)
    uc.hook_add(UC_HOOK_CODE, h_pow, begin=_PLT_POW, end=_PLT_POW + 1)
    uc.hook_add(UC_HOOK_CODE, h_exp, begin=_PLT_EXP, end=_PLT_EXP + 1)


def calcular_sgerg_real(t_degc, p_bar, sg, n2_frac, co2_frac, h2_frac, ghv_mj_m3, ptb_g9):
    """Ejecuta el algoritmo SGERG-88 REAL de FlowXpert (via emulacion del
    binario, no una reimplementacion) para los inputs dados.

    ptb_g9: bool, selecciona `sgerg3` (False, "PTB G9 Correction: 0") o
    `sgerg2` (True, "PTB G9 Correction: 1"), via el despachador real
    `Z_Sgerg_88`.

    Devuelve dict con: z (compresibilidad), mm_g_mol (masa molar),
    rango_status (1=en rango, 2=fuera de rango, tal como lo calcula el
    binario real, no una heuristica).

    Lanza RuntimeError si `disponible()` es False o si la emulacion no
    completa limpiamente (p.ej. entrada que hace que el algoritmo real
    tome una rama no cubierta por los hooks instalados)."""
    if not disponible():
        raise RuntimeError(
            "Emulador SGERG no disponible (falta 'unicorn' o "
            "apk_analisis/libFXLibrary.so). Instalar con 'pip install "
            "unicorn' y verificar que el .so este presente."
        )
    from unicorn.x86_const import UC_X86_REG_ESP
    from unicorn.unicorn import UcError

    uc, stack_base, stack_size = _nueva_maquina()
    _instalar_hooks_libm(uc)

    data_struct = stack_base + stack_size - 0x3000
    out_z = stack_base + stack_size - 0x4000
    out_mm = stack_base + stack_size - 0x4100
    out_rango = stack_base + stack_size - 0x4200

    buf = bytearray(128)
    struct.pack_into("<d", buf, 0, t_degc + 273.15)
    struct.pack_into("<d", buf, 8, p_bar)
    struct.pack_into("<d", buf, 16, sg)
    struct.pack_into("<d", buf, 24, n2_frac)
    struct.pack_into("<d", buf, 32, co2_frac)
    struct.pack_into("<d", buf, 40, h2_frac)
    struct.pack_into("<d", buf, 48, ghv_mj_m3)
    struct.pack_into("<i", buf, 64, _MODO_PTB_G9[bool(ptb_g9)])
    uc.mem_write(data_struct, bytes(buf))
    uc.mem_write(out_z, bytes(8))
    uc.mem_write(out_mm, bytes(8))
    uc.mem_write(out_rango, bytes(4))

    esp = stack_base + stack_size - 0x1000
    uc.mem_write(esp, struct.pack("<I", _RET_SENTINEL))
    uc.mem_write(esp + 4, struct.pack("<I", data_struct))
    uc.mem_write(esp + 8, struct.pack("<I", out_z))
    uc.mem_write(esp + 0xC, struct.pack("<I", out_mm))
    uc.mem_write(esp + 0x10, struct.pack("<I", out_rango))
    uc.reg_write(UC_X86_REG_ESP, esp)

    try:
        uc.emu_start(_Z_SGERG_88, _RET_SENTINEL, timeout=0, count=5_000_000)
    except UcError as e:
        raise RuntimeError(f"Fallo emulando SGERG-88 real: {e}") from e

    z = struct.unpack("<d", uc.mem_read(out_z, 8))[0]
    mm = struct.unpack("<d", uc.mem_read(out_mm, 8))[0]
    rango = struct.unpack("<i", uc.mem_read(out_rango, 4))[0]
    return {"z": z, "mm_g_mol": mm, "rango_status": rango}
