# -*- coding: utf-8 -*-
"""
normas/_aga10_emulador.py
==========================
Emulador x86 (Unicorn) de `AGA10::crit` (direccion raw 0x131DC0... en
realidad 0xe1dc0 -- ver mas abajo) dentro de `libFXLibrary.so`, para el
"Critical Flow Factor (C*)" real de la pantalla "AGA-10 (extended)" de
FlowXpert. Mismo patron que `_nx19_emulador.py`: se ejecuta el binario REAL
compilado, no una reimplementacion, para reproducir el numero exacto.

CONTEXTO (2026-07-29): `normas/AGA_10.py` ya tenia una implementacion
propia de Critical Flow Factor (`resolver_flujo_critico()`, formula fisica
independiente basada en NASA TM X-2308: conservacion de entropia+energia+
condicion sonica), validada <0.01% contra 2 casos reales de MEZCLA, pero
con un residual real de 0.015%-0.084% documentado y sin explicar contra
gases de UN SOLO componente puro (N2/CO2/Etano). Se encontro la causa real
emulando `AGA10::crit` directo: el residual es una limitacion genuina de
la formula fisica propia (probablemente una sutileza del estado de
referencia de entropia/entalpia en la integracion, no identificada en
detalle), NO un error de transcripcion ni de convergencia numerica
(confirmado subiendo max_iter de 60 a 90 sin cambio en el resultado).

`AGA10::crit(tagAGA10STRUCT*, double)` resulto ser una funcion MUCHO mas
completa de lo que su nombre sugiere: en una sola llamada calcula TODO lo
que muestra la pantalla "AGA-10 (extended)" (Molar Mass, Z base/flujo,
Fpv, densidades molares/masicas base/flujo, densidad relativa ideal/real,
Kappa, Isentropic Exponent, Speed of Sound, Y Critical Flow Factor) -- no
es una funcion aislada solo para C*.

STRUCT DE ENTRADA (confirmado via Frida, comparando bytes reales contra
la composicion/P/T conocidas de un caso real, `android_sdk_setup/
test_aga10_crit.py` en el historial de la sesion): array de doubles de 8
bytes cada uno (offsets = indice*8):
    [0]        no usado
    [1..5]     Metano, Nitrogeno, CO2, Etano, Propano
    [6..10]    Agua, H2S, Hidrogeno, CO, Oxigeno -- CONFIRMADO probando
               cada slot con 100% de un solo componente y comparando la
               Masa Molar resultante contra los valores publicados
               (H2O=18.0153, H2S=34.08, H2=2.0159, CO=28.01, O2=31.9988,
               todos coinciden exacto).
    [11..21]   Isobutano, n-Butano, Isopentano(+neo-Pentano si "Add to
               iC5"), n-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano,
               n-Decano, Helio, Argon
    [22]       Presion BASE, Pa   [CORREGIDO 2026-08-03, ver nota abajo]
    [23]       Temperatura BASE, K
    [24]       Presion de flujo, Pa
    [25]       Temperatura de flujo, K
El segundo argumento (double, por la pila) se probo en 0.0 (mismo valor
que se leyo de una llamada real capturada) y funciono para los casos
probados -- no se identifico su rol exacto (podria ser un termino
opcional sin usar en este camino de codigo).

STRUCT DE SALIDA (mismo array, escrito por la funcion), offsets de interes:
    [27] Molar Mass (g/mol)          [28] Z base        [29] Z flujo
    [30] Fpv                         [31] D molar base (mol/L)
    [32] D molar flujo (mol/L)       [33] D masica base (kg/m3)
    [34] D masica flujo (kg/m3)      [35] Densidad relativa ideal
    [36] Densidad relativa real
    [37] Ideal spec. Enthalpy (H0, kJ/kg)   [38] Real spec. Enthalpy (H, kJ/kg)
    [39] Real spec. Entropy (S, kJ/kg-degC) [40] Ideal isobaric Heat cap. (Cp0, kJ/kg-degC)
    [41] Real isobaric Heat cap. (Cp, kJ/kg-degC) [42] Real isochoric Heat cap. (Cv, kJ/kg-degC)
    [43] Cp/Cv ratio (Specific Heats Ratio)
    [44] Isentropic Exponent         [45] Speed of Sound (m/s)
    [46] Critical Flow Factor (C*)

[CERTAIN, 2026-08-03] Offsets 37-42 (Entalpia/Entropia/Cp/Cv) encontrados
DESPUES de construir todo un sistema de "offset empirico por componente"
(ver docstring de normas/AGA_10.py) para aproximar estos mismos valores --
resulta que `AGA10::crit` YA LOS CALCULA, exactos, con el estado de
referencia real de FlowXpert ya incorporado (no hace falta ningun offset
manual). Confirmado EXACTO contra el caso real "Default" (los 6 valores,
<0.001% de diferencia cada uno) tras corregir un bug de escala: el struct
espera la composicion de entrada SUMANDO A LA MISMA UNIDAD que se use
consistentemente (1.0 si son fracciones, 100 si son porcentajes) -- **los
offsets 37-42 escalan con esa suma** (son quasi-extensivos internamente,
no exactamente intensivos), asi que el factor de conversion correcto es
`valor_kJ_kg = raw / (1000.0 * suma_de_x_i_de_entrada)`, NO simplemente
`raw/1000`. Si se usa `_composicion_a_slots()` (que siempre normaliza a
fraccion, suma=1.0) esto se simplifica a `raw/1000` sin ambiguedad -- por
eso `calcular_aga10_extended_real()` exige que quien lo llame ya haya
normalizado la composicion a fraccion (ver ese docstring).
Con esto, TODO lo que muestra la pantalla "AGA-10 (extended)" (excepto el
bug de Critical Flow con kappa alto, documentado arriba, que se replica
tal cual) se puede obtener de una sola llamada a `AGA10::crit`, sin
ninguna formula propia aproximada ni offset calibrado a mano.

[CERTAIN, 2026-08-03 -- BUG REAL DE ESTE MODULO ENCONTRADO Y CORREGIDO,
NO ERA UN BUG DE FLOWXPERT] Los slots de entrada [22-23] y [24-25]
estaban INVERTIDOS en `calcular_aga10_extended_real()` desde que se
integro el modulo (2026-07-30): se escribia la condicion de FLUJO en el
slot [22-23] y la de BASE en el [24-25], pero el binario real espera lo
CONTRARIO (BASE en [22-23], FLUJO en [24-25]). Nunca se detecto antes
porque: (a) todos los casos reales validados hasta ahora con
`calcular_flujo_critico=True` para composiciones DISTINTAS de gas puro
usaban base=flujo (caso "Default" a 0degC) donde el orden no se puede
distinguir, y (b) los 3 casos de gas puro (N2/CO2/Etano, base=273.15K
fijo != flujo) que SI podian detectar el error nunca se corrieron con el
test completo de aserciones despues de integrar el emulador -- la nota
"cerrado 2026-07-30" en la memoria del proyecto se basaba en una prueba
informal que (sin saberlo) tambien dejaba base=flujo por defecto,
repitiendo el mismo punto ciego. Confirmado el bug y la correccion con N2
puro (T=40degC/60kPa, base=273.15K/101.325kPa, el mismo caso real que
`test_aga10_caso_real.py` ya tenia): con el orden VIEJO,
critical_flow_factor daba 0.685140 (real=0.684896, 0.036% de error, peor
que el fallback de formula fisica propia) y H0 daba 283.52 (real=325.11,
12.8% de error); con el orden CORREGIDO, critical_flow_factor da
0.684896 (0.0000411%) y H0 da 325.1068 (0.0000043%). El fix quedo en
`calcular_aga10_extended_real()`: los NOMBRES de parametros (p_pa/t_k=
flujo, pb_pa/tb_k=base, lo que ya esperan todos los callers) no cambiaron,
solo a que slot del struct escribe cada uno.
**Consecuencia importante**: esto tambien invalida la conclusion previa
(ver docstring de `normas/AGA_10.py`, actualizacion revertida el mismo
dia) de que los offsets 37-42 "estan evaluados en condicion base, no de
flujo, y no sirven para reemplazar el offset empirico de Enthalpy/
Entropy/Cp/Cv" -- esa conclusion se obtuvo probando con el mismo bug de
slots invertidos activo. Con el fix, offset 37 (H0) SI sigue el flujo
correctamente (confirmado arriba, 0.0000043% contra N2 puro). Pendiente
re-evaluar si conviene reactivar el uso de estos offsets en
`normas/AGA_10.py` (ver seccion correspondiente de la memoria del
proyecto para el estado actual de esa decision).

VALIDADO: caso real Default/1 atm/0degC (Cstar=0.671874 real) reproduce
EXACTO (0.000065%, redondeo de punto flotante); caso N2 puro/40degC/60kPa
reproduce el MISMO 0.6848957184271273 que produce la diferencia de
0.01486% ya documentada contra `resolver_flujo_critico()` -- confirma que
el emulador da el valor REAL, y que la formula propia (NASA TM X-2308)
efectivamente tiene ese residual real para gases puros.

[CERTAIN, 2026-07-30 -- BUG REAL ENCONTRADO EN FLOWXPERT, NO EN ESTE
PROYECTO] Al probar un barrido mas amplio de composiciones (pedido
explicito del usuario, "has probado distintas composiciones") se encontro
que Helio puro y Argon puro dan Critical Flow Factor = 87.58/87.61 --
un numero SIN SENTIDO FISICO (C* real siempre esta entre ~0.5 y ~0.8 para
cualquier gas real). Se sospecho primero un bug de la emulacion, pero se
confirmo llamando `AGA10::crit` DIRECTO en el dispositivo Android real
(no el emulador) con la misma composicion: el dispositivo real da
EXACTAMENTE el mismo 87.5819567960988 -- **es un bug real del binario de
FlowXpert, no de este proyecto ni de la emulacion**. Se caracterizo el
patron con un barrido adicional (kappa, no la composicion exacta, es la
variable que dispara el bug):
    Argon puro (kappa=1.6677):        Cstar=87.61  (roto)
    99% He + 1% N2 (kappa=1.6626):    Cstar=89.23  (roto)
    90% He + 10% Ar (kappa=1.6671):   Cstar=87.54  (roto)
    99.9% He + 0.1% N2 (kappa=1.6666): Cstar=87.79  (roto)
    50% He + 50% N2 (kappa=1.5002):   Cstar=0.701  (normal)
El bug aparece especificamente cuando kappa (Cp/Cv) se acerca al valor
ideal de gas monoatomico (5/3=1.6667, el maximo fisico posible para un
gas ideal) -- NO requiere composicion 100% pura de un solo componente,
cualquier mezcla con kappa suficientemente alto (>~1.66) lo dispara. Esto
es consistente con un bug real de rango/branch en el solver iterativo
interno de `crit()` que no maneja bien el caso de alto kappa (posiblemente
una division por (kappa-1) o similar que se vuelve numericamente inestable
cerca de ese extremo).
**Decision de diseño**: como el proposito de este proyecto es CONFIRMAR lo
que FlowXpert realmente calcula (no corregirlo), `calcular_
aga10_extended_real()` reproduce este comportamiento TAL CUAL, bugs
incluidos -- es lo correcto para un modulo de confirmacion. No se agrego
ningun "arreglo" que oculte el bug. Sigue pendiente (no bloqueante, fuera
del alcance de "confirmar", seria "mejorar"): decidir si vale la pena
agregar una advertencia visible en la GUI cuando kappa>~1.6 y se pida
Critical Flow, para que el usuario sepa que el numero mostrado replica un
bug conocido de FlowXpert, no un calculo confiable.

PLT/libm necesarios (descubiertos incrementalmente con
UC_HOOK_MEM_INVALID, direcciones RAW confirmadas via .rel.plt +
.dynsym): sqrt, pow, exp, sinh, cosh, log, acos, cos, fmax, __isfinite,
ceil, log10, fmin, sqrtf, malloc, free, floorf, floor, ceilf, tanh -- una
lista bastante mas larga que la de NX-19 (que solo necesitaba sqrt/pow/
exp/isfinite/ceil/log10/fmin), porque `crit()` llama internamente al
motor completo de AGA8-DETAIL (mezclas, mixing rules) en vez de una
formula simple. `malloc`/`free` se resuelven con un bump allocator simple
sobre una region de memoria separada (no hace falta liberar de verdad
para una sola llamada).

DEPENDENCIA: igual que `_nx19_emulador.py` -- requiere `unicorn` instalado
y `apk_analisis/libFXLibrary.so` presente.
"""
import struct

from . import _sgerg_emulador as _sg

_AGA10_CRIT = 0xE1DC0

_PLT = {
    "sqrt": 0x523D0, "pow": 0x523E0, "exp": 0x523F0, "sinh": 0x52400,
    "cosh": 0x52410, "log": 0x52420, "acos": 0x52430, "cos": 0x52440,
    "fmax": 0x52450, "isfinite": 0x52460, "ceil": 0x52470, "log10": 0x52480,
    "fmin": 0x52490, "sqrtf": 0x524A0, "malloc": 0x524B0, "free": 0x524C0,
    "floorf": 0x524D0, "floor": 0x524E0, "ceilf": 0x524F0, "tanh": 0x52500,
}

_HEAP_BASE = 0x51000000
_HEAP_SIZE = 0x400000
_STRUCT_ADDR = 0x50000000
_STRUCT_SIZE = 0x10000

# Offsets (indice * 8 bytes) del struct de entrada/salida -- ver docstring.
_OFFSETS_SALIDA = {
    "Mm_g_mol": 27, "Z_base": 28, "Z_flujo": 29, "Fpv": 30,
    "D_base_mol_l": 31, "D_flujo_mol_l": 32, "D_base_kg_m3": 33, "D_flujo_kg_m3": 34,
    "rel_density_ideal": 35, "rel_density_real": 36, "Cp_Cv_ratio": 43,
    "Kappa": 44, "W_m_s": 45, "critical_flow_factor": 46,
}
# Offsets 37-42: Entalpia/Entropia/Cp/Cv REALES, calculados por el binario
# (ver docstring del modulo) -- se leen aparte (no en _OFFSETS_SALIDA) porque
# necesitan dividirse por 1000*suma(composicion_1indexed.values()), no por
# una constante fija, y `calcular_aga10_extended_real()` no siempre recibe
# composicion ya normalizada a fraccion=1.0.
_OFFSETS_ENTALPIA = {
    "H0_kJ_kg": 37, "H_kJ_kg": 38, "S_kJ_kgC": 39,
    "Cp0_kJ_kgC": 40, "Cp_kJ_kgC": 41, "Cv_kJ_kgC": 42,
}


def _instalar_hooks_aga10(uc):
    import math
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import (
        UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX, UC_X86_REG_FPSW,
        UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2, UC_X86_REG_FP3,
        UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6, UC_X86_REG_FP7,
    )

    fp_regs = [UC_X86_REG_FP0, UC_X86_REG_FP1, UC_X86_REG_FP2, UC_X86_REG_FP3,
               UC_X86_REG_FP4, UC_X86_REG_FP5, UC_X86_REG_FP6, UC_X86_REG_FP7]

    heap_siguiente = [_HEAP_BASE + 0x10]

    def leer_d(uc, esp, off=4):
        return struct.unpack("<d", uc.mem_read(esp + off, 8))[0]

    def volver_double(uc, valor):
        # Convencion de retorno x87 real = PUSH (ver normas/_sgerg_emulador.py
        # para la explicacion completa del bug/fix encontrado 2026-07-29).
        ext80 = _sg._doble_a_extendido80(valor)
        mant = ext80 & ((1 << 64) - 1)
        exp = (ext80 >> 64) & 0xFFFF
        fpsw = uc.reg_read(UC_X86_REG_FPSW)
        top = (fpsw >> 11) & 0x7
        nuevo_top = (top - 1) & 0x7
        nuevo_fpsw = (fpsw & ~(0x7 << 11)) | (nuevo_top << 11)
        uc.reg_write(fp_regs[nuevo_top], (mant, exp))
        uc.reg_write(UC_X86_REG_FPSW, nuevo_fpsw)
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def volver_int(uc, valor, nbytes_args):
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_EAX, valor & 0xFFFFFFFF)
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + nbytes_args)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def h_double1(fn):
        def hook(uc, address, size, ud):
            x = leer_d(uc, uc.reg_read(UC_X86_REG_ESP))
            volver_double(uc, fn(x))
        return hook

    def h_pow(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = leer_d(uc, esp, 4)
        y = leer_d(uc, esp, 0xC)
        try:
            r = math.pow(x, y)
        except (ValueError, OverflowError):
            r = float("nan")
        volver_double(uc, r)

    def h_fmax(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        volver_double(uc, max(leer_d(uc, esp, 4), leer_d(uc, esp, 0xC)))

    def h_fmin(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        volver_double(uc, min(leer_d(uc, esp, 4), leer_d(uc, esp, 0xC)))

    def h_isfinite(uc, address, size, ud):
        x = leer_d(uc, uc.reg_read(UC_X86_REG_ESP))
        volver_int(uc, 1 if math.isfinite(x) else 0, 8)

    def h_sqrtf(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
        volver_double(uc, math.sqrt(x) if x >= 0 else float("nan"))

    def h_floorf(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
        volver_double(uc, math.floor(x))

    def h_ceilf(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        x = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
        volver_double(uc, math.ceil(x))

    def h_malloc(uc, address, size, ud):
        esp = uc.reg_read(UC_X86_REG_ESP)
        n = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
        n = (n + 15) & ~15
        ptr = heap_siguiente[0]
        heap_siguiente[0] += max(n, 16)
        volver_int(uc, ptr, 4)

    def h_free(uc, address, size, ud):
        volver_int(uc, 0, 4)

    tabla_simple = {
        "sqrt": lambda x: math.sqrt(x) if x >= 0 else float("nan"),
        "exp": math.exp, "sinh": math.sinh, "cosh": math.cosh,
        "tanh": math.tanh, "log": lambda x: math.log(x) if x > 0 else float("nan"),
        "acos": lambda x: math.acos(x) if -1.0 <= x <= 1.0 else float("nan"),
        "cos": math.cos, "ceil": math.ceil,
        "log10": lambda x: math.log10(x) if x > 0 else float("nan"),
        "floor": math.floor,
    }
    for nombre, fn in tabla_simple.items():
        addr = _PLT[nombre]
        uc.hook_add(UC_HOOK_CODE, h_double1(fn), begin=addr, end=addr + 1)
    uc.hook_add(UC_HOOK_CODE, h_pow, begin=_PLT["pow"], end=_PLT["pow"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_fmax, begin=_PLT["fmax"], end=_PLT["fmax"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_fmin, begin=_PLT["fmin"], end=_PLT["fmin"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_isfinite, begin=_PLT["isfinite"], end=_PLT["isfinite"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_sqrtf, begin=_PLT["sqrtf"], end=_PLT["sqrtf"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_floorf, begin=_PLT["floorf"], end=_PLT["floorf"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_ceilf, begin=_PLT["ceilf"], end=_PLT["ceilf"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_malloc, begin=_PLT["malloc"], end=_PLT["malloc"] + 1)
    uc.hook_add(UC_HOOK_CODE, h_free, begin=_PLT["free"], end=_PLT["free"] + 1)


def disponible():
    return _sg.disponible()


# Mapeo nombre de componente (mismas claves que normas/AGA_8.py
# NOMBRES_COMPONENTES) -> indice 1-based del struct real de AGA10::crit
# (confirmado, ver docstring del modulo).
_NOMBRE_A_SLOT = {
    "Metano": 1, "Nitrogeno": 2, "CO2": 3, "Etano": 4, "Propano": 5,
    "Agua": 6, "H2S": 7, "Hidrogeno": 8, "CO": 9, "Oxigeno": 10,
    "Isobutano": 11, "n-Butano": 12, "Isopentano": 13, "n-Pentano": 14,
    "n-Hexano": 15, "n-Heptano": 16, "n-Octano": 17, "n-Nonano": 18,
    "n-Decano": 19, "Helio": 20, "Argon": 21,
}


def _composicion_a_slots(composicion: dict) -> dict:
    """Convierte un dict {nombre_componente: fraccion o porcentaje} (mismas
    claves que normas/AGA_8.py) al dict {indice_1based: fraccion_molar_0_1}
    que espera calcular_aga10_extended_real(). Normaliza automaticamente
    (no necesita sumar 1 o 100)."""
    total = sum(composicion.values())
    if total <= 0:
        raise ValueError("La composicion debe sumar mas que cero.")
    return {
        _NOMBRE_A_SLOT[nombre]: valor / total
        for nombre, valor in composicion.items()
        if nombre in _NOMBRE_A_SLOT and valor
    }


def calcular_aga10_extended_real(composicion_1indexed: dict, p_pa: float, t_k: float,
                                  pb_pa: float = None, tb_k: float = None,
                                  arg2: float = 0.0) -> dict:
    """Ejecuta `AGA10::crit` REAL (emulacion Unicorn del binario, no una
    reimplementacion) para una composicion dada como dict {indice_1based:
    fraccion_molar} en el orden confirmado (ver docstring del modulo:
    1=Metano,2=N2,3=CO2,4=Etano,5=Propano,11=iC4,12=nC4,13=iC5,14=nC5,
    15=nC6,16=nC7,17=nC8,18=nC9,19=nC10,20=He,21=Ar), presion de flujo en
    Pa, temperatura de flujo en K (presion/temperatura base opcionales,
    por defecto iguales a las de flujo).

    Devuelve dict con Mm_g_mol, Z_base, Z_flujo, Fpv, D_base_mol_l,
    D_flujo_mol_l, D_base_kg_m3, D_flujo_kg_m3, rel_density_ideal,
    rel_density_real, Cp_Cv_ratio, Kappa, W_m_s, critical_flow_factor.

    Lanza RuntimeError si `disponible()` es False o si la emulacion no
    completa limpiamente."""
    if not disponible():
        raise RuntimeError(
            "Emulador AGA-10 no disponible (falta 'unicorn' o "
            "apk_analisis/libFXLibrary.so)."
        )
    from unicorn.x86_const import UC_X86_REG_ESP
    from unicorn.unicorn import UcError

    uc, stack_base, stack_size = _sg._nueva_maquina()
    uc.mem_map(_HEAP_BASE, _HEAP_SIZE)
    _instalar_hooks_aga10(uc)

    buf = bytearray(_STRUCT_SIZE if _STRUCT_SIZE < 960 else 960)
    buf = bytearray(120 * 8)

    def set_d(idx, val):
        struct.pack_into("<d", buf, idx * 8, val)

    for idx, val in composicion_1indexed.items():
        set_d(idx, val)
    # [CERTAIN, 2026-08-03] Los slots 22/23 y 24/25 del struct real estan
    # INVERTIDOS respecto a lo que este modulo documentaba: el slot 22/23
    # es el que el binario trata internamente como "base", y el 24/25 es
    # el que trata como "flujo" (confirmado escribiendo cada combinacion
    # por separado y comparando W_m_s/critical_flow_factor/H0 resultantes
    # contra un caso real de N2 puro con base!=flujo -- con la asignacion
    # de abajo, critical_flow_factor da 0.0000411% de diferencia contra el
    # real 0.684896, y H0 da 0.0000043% contra el real 325.1068; con la
    # asignacion vieja (22/23=flujo,24/25=base) daban 0.0357% y 12.8%
    # respectivamente). Los NOMBRES de los parametros de esta funcion
    # (p_pa/t_k=flujo, pb_pa/tb_k=base) NO cambian -- solo a que slot del
    # struct se escribe cada uno.
    set_d(24, p_pa)
    set_d(25, t_k)
    set_d(22, pb_pa if pb_pa is not None else p_pa)
    set_d(23, tb_k if tb_k is not None else t_k)

    uc.mem_map(_STRUCT_ADDR, _STRUCT_SIZE)
    uc.mem_write(_STRUCT_ADDR, bytes(buf))

    esp = stack_base + stack_size - 0x2000
    ret_sentinel = _sg._RET_SENTINEL
    uc.mem_write(esp, struct.pack("<I", ret_sentinel))
    uc.mem_write(esp + 4, struct.pack("<I", _STRUCT_ADDR))
    uc.mem_write(esp + 8, struct.pack("<d", arg2))
    uc.reg_write(UC_X86_REG_ESP, esp)

    try:
        uc.emu_start(_AGA10_CRIT, ret_sentinel, timeout=0, count=50_000_000)
    except UcError as e:
        raise RuntimeError(f"Fallo emulando AGA10::crit real: {e}") from e

    resultado = {}
    for nombre, idx in _OFFSETS_SALIDA.items():
        resultado[nombre] = struct.unpack_from(
            "<d", uc.mem_read(_STRUCT_ADDR + idx * 8, 8))[0]

    # Entalpia/Entropia/Cp/Cv reales -- ver docstring del modulo, escalan
    # con la suma de composicion_1indexed.values(), no con una constante
    # fija (por eso NO estan en _OFFSETS_SALIDA de arriba).
    suma_composicion = sum(composicion_1indexed.values())
    if suma_composicion > 0:
        escala = 1000.0 * suma_composicion
        for nombre, idx in _OFFSETS_ENTALPIA.items():
            resultado[nombre] = struct.unpack_from(
                "<d", uc.mem_read(_STRUCT_ADDR + idx * 8, 8))[0] / escala
    return resultado
