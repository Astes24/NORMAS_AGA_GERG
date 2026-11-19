# -*- coding: utf-8 -*-
"""
normas/_aga10_fx.py
===================
[C-48, 2026-11-18] Port bit a bit (Python puro) del camino de Critical Flow de AGA-10 de FlowXpert.xll:
AGA10::crit, CTherm (run, HS_Mode, H, S, CprCvrHS, H0, S0, CpiMolar) y CDetail (Run, paramdl, chardl, bvir,
temp, zdetail, pdetail, braket, ddetail, dZdT, d2ZdT2, dZdD, relativedensity) del AGA Report No. 8 (1994) y
No. 10, tal como estan compilados en el .xll. Cada operacion de punto flotante sigue el orden exacto del
codigo maquina (SSE2 escalar, sin FMA): las rutinas aritmeticas largas son transliteraciones instruccion por
instruccion del desensamblado (registros xmmN -> variables xN); los bucles y ramas se reescribieron a mano
con la misma semantica de comparacion (incluido el tratamiento de NaN). Direcciones FUN_18xxxxxxx entre
corchetes.

La memoria del binario se emula con listas de doubles indexadas por offset/8:
  s = tagAGA10STRUCT (0x08.. fracciones de los 21 componentes, 0xb0 Pb [Pa], 0xb8 Tb [K], 0xc0 P [Pa],
      0xc8 T [K], 0xd8 Mm, 0xe0 Zb, 0xe8 Z, 0xf0 Fpv, 0xf8 Db, 0x100 D, 0x108 rho_b, 0x110 rho, 0x118 rd_i,
      0x120 rd_r, 0x128 H0, 0x130 H, 0x138 S, 0x140 Cp0, 0x148 Cp, 0x150 Cv, 0x158 Cp/Cv, 0x160 kappa,
      0x168 W, 0x170 C*)
  c = CDetail::DetailCache (0x8100 bytes)
Los enteros del cache (cantidad de componentes presentes y sus indices) van aparte (self.n, self.idx).

Funciones matematicas: exp() es una replica exacta de la de MSVCR110.dll (la de Python difiere en ~0.4 % de
los argumentos por 1 ulp, lo que basta para cambiar C* en la zona caotica). log, sqrt, sinh, cosh y tanh de
Python coinciden con las de MSVCR110 (verificado en 2e5 argumentos cada una). pow solo se usa en chardl
(parametros de la mezcla).
"""
import math
import struct

from . import _aga10_fx_datos as _D

_IDEAL = _D.IDEAL
_GX = _D.GAUSS_X
_GW = _D.GAUSS_W
_EXP_LEAD = _D.EXP_LEAD
_EXP_TRAIL = _D.EXP_TRAIL
_EXP_FULL = _D.EXP_FULL
_pk_d = struct.Struct("<d")
_pk_q = struct.Struct("<Q")


def _d_de_bits(q):
    return _pk_d.unpack(_pk_q.pack(q))[0]


def exp_ms(x):
    """exp() bit a bit igual a MSVCR110.dll (x64, camino SSE2): reduccion con tabla de 64 entradas y
    polinomio de grado 5."""
    bits = _pk_q.unpack(_pk_d.pack(x))[0]
    if bits & 0x7ff0000000000000 == 0x7ff0000000000000:
        if x != x:
            return x
        return 0.0 if x < 0 else math.inf
    if (bits & 0x7fffffffffffffff) < 0x3c00000000000000:
        return 1.0
    t = 92.33248261689366 * x
    if t > 65536.0:
        return math.inf
    if not t > -68800.0:
        return 0.0
    n = int(round(t))
    dn = float(n)
    x0 = x - 0.010830424696223417 * dn
    r = x0 + dn * -2.5728046223276688e-14
    j = n & 63
    m = (n - j) >> 6
    r2 = r * r
    a = 0.5 * r
    b = 0.041666666666666664 * r
    cc = 0.001388888888888889 * r
    r3 = r2 * r
    a = a + 1.0
    b = b + 0.16666666666666666
    cc = cc + 0.008333333333333333
    r5 = r2 * r3
    a = a * r
    b = b * r3
    cc = cc * r5
    b = b + cc
    p = a + b
    res = p * _EXP_FULL[j]
    res = res + _EXP_TRAIL[j]
    res = res + _EXP_LEAD[j]
    if m == 1024:
        return math.inf
    if m <= -1022:
        if res >= 1.0 and m == -1022:
            return res * _d_de_bits((m + 1023) << 52)
        if x < -744.0346068132731:
            return 5e-324
        sh = m + 0x432
        if sh < 0:
            sh = 0
        return res * _d_de_bits(1 << sh)
    return res * _d_de_bits((m + 1023) << 52)


_exp = exp_ms
_log = math.log
_sqrt = math.sqrt
_pow = math.pow
_tanh = math.tanh


_NAN_HW = -math.nan  # NaN "indefinido" que produce el hardware / MSVCR110 (bit de signo activo)


def _div(a, b):
    """Division IEEE (x/0 -> +-inf, 0/0 -> NaN) como el binario."""
    try:
        return a / b
    except ZeroDivisionError:
        if a != a:
            return a
        if a == 0.0:
            return _NAN_HW
        return math.copysign(math.inf, a) * math.copysign(1.0, b)


def _logm(x):
    """log de MSVCR110 con su semantica para x <= 0 (-inf / NaN)."""
    if x > 0.0:
        return _log(x)
    if x == 0.0:
        return -math.inf
    if x != x:
        return x
    return _NAN_HW


def _sqrtm(x):
    if x >= 0.0:
        return _sqrt(x)
    if x != x:
        return x
    return _NAN_HW


def _sinh_m(x):
    try:
        return math.sinh(x)
    except OverflowError:
        return math.copysign(math.inf, x)


def _cosh_m(x):
    try:
        return math.cosh(x)
    except OverflowError:
        return math.inf


def _coth(x):
    """FUN_1801052d4: cosh(x)/sinh(x)."""
    return _div(_cosh_m(x), _sinh_m(x))


_NC = 0x8100 >> 3
_NS = 0x200 >> 3


class MaquinaFX:
    """Struct AGA10 + DetailCache de FlowXpert y las rutinas que operan sobre ellos."""

    def __init__(self):
        self.s = [0.0] * _NS
        self.status = 0
        self.flag = 0
        self.c = [0.0] * _NC
        self.n = 0
        self.idx = []
        self.init_cache()

    # ---------------------------------------------------------------- CDetail::InitDetailCache [1801004a0]
    def init_cache(self):
        c = self.c
        for i in range(_NC):
            c[i] = 0.0
        for off, v in _D.INIT.items():
            c[off >> 3] = v
        self.n = 0
        self.idx = []

    # ---------------------------------------------------------------- CompositionChange [1800ff4d0]
    def _composition_change(self):
        s, c = self.s, self.c
        d = 0.0
        for k in range(21):
            d = d + float(k + 2) * s[1 + k]
        if d != c[0x58 >> 3]:
            c[0x58 >> 3] = d
            return True
        return False

    # ---------------------------------------------------------------- CDetail::paramdl [1801030f0]
    def _paramdl(self):
        c = self.c
        for k in range(21):
            c[(0x77a0 >> 3) + k] = 0.0
            c[(0x7848 >> 3) + k] = 0.0
            c[(0x78f0 >> 3) + k] = 0.0
            c[(0x7998 >> 3) + k] = 0.0
        c[0x77b0 >> 3] = _d_de_bits(0x3fe6147ae147ae14)
        c[0x7880 >> 3] = 1.0
        c[0x77c8 >> 3] = _d_de_bits(0x3ff115810624dd2f)
        c[0x79c0 >> 3] = 1.0
        c[0x77d0 >> 3] = _d_de_bits(0x3fe443cc07aaef2c)
        c[0x7918 >> 3] = _d_de_bits(0x3ff950b0f27bb2ff)
        c[0x7920 >> 3] = _d_de_bits(0x3fd8f5c28f5c28f6)
        n, idx = self.n, self.idx
        for k in range(n - 1, -1, -1):
            c[(0x420 >> 3) + k] = _D.A1[idx[k]]
            c[(0x570 >> 3) + k] = _D.A3[idx[k]]
        for k in range(n):
            c[(0x618 >> 3) + k] = _D.A4[idx[k]]
            c[(0x4c8 >> 3) + k] = _D.A2[idx[k]]
        for k in range(n):
            ii = idx[k]
            u = c[(0x77a0 >> 3) + ii]
            c[(0x768 >> 3) + k] = 0.0
            c[(0x6c0 >> 3) + k] = u
            if ii == 7:
                c[(0x768 >> 3) + k] = c[0x7880 >> 3]
            c[(0x810 >> 3) + k] = c[(0x78f0 >> 3) + ii]
            c[(0x8b8 >> 3) + k] = c[(0x7998 >> 3) + ii]
        for i in range(n):
            base = (0x24f0 >> 3) + 22 * i
            for j in range(i, n):
                q = 21 * idx[i] + idx[j]
                p = base + (j - i)
                c[p - (0xdc8 >> 3)] = c[(0x4e48 >> 3) + q]
                c[p] = c[(0x5c10 >> 3) + q]
                c[p - (0x1b90 >> 3)] = c[(0x4080 >> 3) + q]
                c[p + (0xdc8 >> 3)] = c[(0x69d8 >> 3) + q]

    # ---------------------------------------------------------------- CDetail::bvir [180100a48]
    def _bvir(self):
        c = self.c
        c[0x7fb8 >> 3] = 0.0
        c[0x7fb0 >> 3] = 0.0
        c[0x7b08 >> 3] = 0.0
        b = [0.0] * 18
        x0 = _sqrtm(c[0x7af0 >> 3])
        x10 = c[0x7af0 >> 3]
        x1 = c[0x7b18 >> 3]
        x7 = x0
        x11 = x10
        x8 = x10
        x1 = _div(x1, x7)
        x11 = x11 * x10
        x4 = x10
        x9 = x10
        b[1] = x1
        x1 = c[0x7b28 >> 3]
        x8 = x8 * x11
        x6 = x8
        x2 = x8
        x2 = x2 * x0
        x6 = x6 * x8
        x1 = _div(x1, x2)
        x4 = x4 * x6
        x9 = x9 * x2
        b[3] = x1
        x1 = c[0x7b38 >> 3]
        x4 = x4 * x0
        x1 = _div(x1, x9)
        x9 = x9 * x9
        x3 = x4
        b[5] = x1
        x1 = c[0x7b48 >> 3]
        x1 = _div(x1, x4)
        x3 = x3 * x11
        x9 = x9 * x11
        x5 = x3
        b[7] = x1
        x1 = c[0x7b58 >> 3]
        x5 = x5 * x0
        x1 = _div(x1, x6)
        x6 = x6 * c[0x7b70 >> 3]
        b[0] = c[0x7b10 >> 3]
        x0 = c[0x7b20 >> 3]
        b[12] = x6
        b[9] = x1
        x1 = c[0x7b80 >> 3]
        x0 = _div(x0, x10)
        x5 = x5 * x11
        x1 = _div(x1, x8)
        b[2] = x0
        x0 = x7
        b[14] = x1
        x1 = c[0x7b90 >> 3]
        x0 = x0 * c[0x7b30 >> 3]
        x1 = _div(x1, x11)
        b[4] = x0
        x0 = c[0x7b40 >> 3]
        b[16] = x1
        x0 = _div(x0, x7)
        b[6] = x0
        x0 = c[0x7b50 >> 3]
        x0 = _div(x0, x3)
        b[8] = x0
        x0 = c[0x7b60 >> 3]
        x0 = _div(x0, x5)
        x5 = x5 * x7
        b[10] = x0
        x0 = c[0x7b68 >> 3]
        x0 = _div(x0, x5)
        b[11] = x0
        x0 = c[0x7b78 >> 3]
        x0 = _div(x0, x11)
        b[13] = x0
        x0 = c[0x7b88 >> 3]
        x0 = _div(x0, x11)
        b[15] = x0
        x0 = c[0x7b98 >> 3]
        x1 = c[0x7b08 >> 3]
        x0 = _div(x0, x9)
        b[17] = x0
        for k in range(18):
            x1 = x1 + b[k]
        c[0x7b08 >> 3] = x1
        un = 0x250 >> 3
        for k in range(18):
            x0 = c[un + k]
            if x0 != 0.0:
                b[k] = x0 * b[k]
        for k in range(18):
            if c[un + k] != 0.0:
                c[0x7fb0 >> 3] = _div(b[k], x10) + c[0x7fb0 >> 3]
        c[0x7fb0 >> 3] = -c[0x7fb0 >> 3]
        for k in range(18):
            x0 = c[un + k]
            if x0 != 0.0 and x0 != -1.0:
                b[k] = (x0 + 1.0) * b[k]
        for k in range(18):
            x0 = c[un + k]
            if x0 != 0.0 and x0 != -1.0:
                c[0x7fb8 >> 3] = _div(b[k], x11) + c[0x7fb8 >> 3]

    # ---------------------------------------------------------------- CDetail::chardl [180100db4]
    def _chardl(self):
        s, c, n = self.s, self.c, self.n
        X = 0x7a40 >> 3
        tot = 0.0
        for k in range(n):
            tot = tot + c[X + k]
        for k in range(n):
            c[X + k] = _div(c[X + k], tot)
        B = 0x7b10 >> 3
        for k in range(18):
            c[B + k] = 0.0
        c[0x7f50 >> 3] = 0.0
        c[0x7f60 >> 3] = 0.0
        x8 = 0.0      # correccion de K (xmm8)
        x9 = 0.0      # suma de K (xmm9)
        x10 = 0.0     # suma de U (xmm10)
        s[0xd8 >> 3] = 0.0
        x6 = 0.0      # correccion de U ([rsp+0x150])
        x11 = 0.0     # suma de Q (xmm11)
        if n > 0:
            x1 = 0.0
            for k in range(n):
                x0 = c[X + k]
                x0 = x0 * c[(0x420 >> 3) + k]
                x1 = x1 + x0
                s[0xd8 >> 3] = x1
            E, Kk, G, Q, F, S, W = (0x4c8 >> 3, 0x570 >> 3, 0x618 >> 3, 0x6c0 >> 3, 0x768 >> 3,
                                    0x810 >> 3, 0x8b8 >> 3)
            corrU = 0.0
            for i in range(n):
                Ki = c[Kk + i]
                x0 = _sqrtm(Ki)
                x7 = c[X + i]
                x1 = x0
                x0 = Ki
                x0 = x0 * c[X + i]
                x0 = x0 * Ki
                Ei = c[E + i]
                x1 = x1 * x0
                x9 = x9 + x1
                sumK = x9
                x0 = _sqrtm(Ei)
                x1 = x0
                x0 = x7
                x7 = x7 * c[G + i]
                x0 = x0 * Ei
                x7 = x7 + c[0x7f50 >> 3]
                x0 = x0 * Ei
                c[0x7f50 >> 3] = x7
                x1 = x1 * x0
                x10 = x10 + x1
                x1 = c[X + i]
                x0 = x1
                x1 = x1 * x1
                x1 = x1 * c[F + i]
                x0 = x0 * c[Q + i]
                x1 = x1 + c[0x7f60 >> 3]
                x11 = x11 + x0
                c[0x7f60 >> 3] = x1
                x9 = corrU
                base = (0x24f0 >> 3) + 22 * i
                for j in range(i, n):
                    p = base + (j - i)
                    if i != j:
                        w = c[X + i]
                        w = w * 2.0
                        w = w * c[X + j]
                    else:
                        w = c[X + j]
                        w = w * c[X + i]
                    if c[p] != 1.0:
                        a = _pow(c[Kk + j], 5.0)
                        a = a * _pow(c[Kk + i], 5.0)
                        a = _pow(a, 0.5)
                        t = _pow(c[p], 5.0)
                        t = t - 1.0
                        t = t * w
                        a = a * t
                        x8 = x8 + a
                    if c[p - (0xdc8 >> 3)] != 1.0:
                        a = _pow(c[E + j], 5.0)
                        a = a * _pow(c[E + i], 5.0)
                        a = _pow(a, 0.5)
                        t = _pow(c[p - (0xdc8 >> 3)], 5.0)
                        t = t - 1.0
                        t = t * w
                        a = a * t
                        x9 = x9 + a
                    v1 = c[p + (0xdc8 >> 3)]
                    if v1 != 1.0:
                        a = c[G + j]
                        v1 = v1 - 1.0
                        a = a + c[G + i]
                        v1 = v1 * w
                        a = a * 0.5
                        a = a * v1
                        a = a + c[0x7f50 >> 3]
                        c[0x7f50 >> 3] = a
                    a = c[E + j]
                    a = a * c[E + i]
                    a = _sqrtm(a)
                    x15 = c[G + j]
                    x15 = x15 + c[G + i]
                    e = a
                    x15 = x15 * c[p + (0xdc8 >> 3)]
                    e = e * c[p - (0x1b90 >> 3)]
                    x15 = x15 * 0.5
                    e05 = _sqrtm(e)
                    e2 = e * e
                    e3 = e2 * e
                    e6 = e3 * e3
                    e35 = e3 * e05
                    e45 = e35 * e
                    e9 = e45 * e45
                    e55 = e45 * e
                    e11 = e9 * e2
                    e75 = e55 * e2
                    e12 = e11 * e
                    e95 = e75 * e2
                    e125 = e12 * e05
                    kj = c[Kk + j]
                    kj3 = 1.0 * kj
                    kj = kj * kj
                    kj3 = kj3 * kj
                    b = _pow(c[Kk + i], 3.0)
                    b = b * kj3
                    b = _pow(b, 0.5)
                    b = b * w
                    bg = b * x15
                    c[B] = b + c[B]
                    c[B + 1] = b * e05 + c[B + 1]
                    c[B + 2] = b * e + c[B + 2]
                    c[B + 3] = b * e35 + c[B + 3]
                    t = bg
                    bg = bg * e45
                    t = _div(t, e05)
                    c[B + 5] = bg + c[B + 5]
                    c[B + 4] = t + c[B + 4]
                    b2 = b * e2
                    c[B + 6] = b * c[Q + i] * c[Q + j] * e05 + c[B + 6]
                    c[B + 7] = b * c[S + i] * c[S + j] * e75 + c[B + 7]
                    c[B + 8] = b * c[S + i] * c[S + j] * e95 + c[B + 8]
                    c[B + 9] = b * c[W + i] * c[W + j] * e6 + c[B + 9]
                    c[B + 10] = b * c[W + i] * c[W + j] * e12 + c[B + 10]
                    c[B + 11] = b * c[W + i] * c[W + j] * e125 + c[B + 11]
                    c[B + 12] = _div(b * c[F + i] * c[F + j], e6) + c[B + 12]
                    c[B + 13] = b2 + c[B + 13]
                    c[B + 16] = b2 + c[B + 16]
                    c[B + 17] = b * e11 + c[B + 17]
                    c[B + 14] = b * e3 + c[B + 14]
                    c[B + 15] = b * c[Q + i] * c[Q + j] * e2 + c[B + 15]
                corrU = x9
                x9 = sumK
            x6 = corrU
        for k in range(18):
            c[B + k] = c[(0x80 >> 3) + k] * c[B + k]
        x9 = x9 * x9
        x9 = x9 + x8
        c[0x7f48 >> 3] = _pow(x9, 0.6)
        x10 = x10 * x10
        x10 = x10 + x6
        c[0x7f40 >> 3] = _pow(x10, 0.2)
        x11 = x11 * x11
        c[0x7f58 >> 3] = x11

    # ---------------------------------------------------------------- CDetail::relativedensity [180103644]
    def _relativedensity(self):
        s, c = self.s, self.c
        x1 = s[0xb8 >> 3]
        x0 = x1
        x2 = x1
        x2 = x2 * 0.000591
        x0 = x0 * 6.62e-07
        x2 = x2 - 0.12527
        x0 = x0 * x1
        x1 = x1 * 0.00831451
        x2 = x2 - x0
        x0 = s[0xd8 >> 3]
        x2 = x2 * c[0x7af8 >> 3]
        x0 = _div(x0, 28.96256)
        s[0x118 >> 3] = x0
        x2 = _div(x2, x1)
        x2 = x2 + 1.0
        x2 = _div(x2, s[0xe0 >> 3])
        x2 = x2 * x0
        s[0x120 >> 3] = x2

    # ---------------------------------------------------------------- CTherm::CpiMolar [1801041cc]
    def _cpi(self):
        s = self.s
        x12 = s[0xc8 >> 3]
        x10 = 0.0
        for k in range(21):
            xk = s[1 + k]
            if 0.0 >= xk:
                continue
            f = _IDEAL[k]
            x6 = _div(f[3], x12)
            x7 = _div(f[5], x12)
            x8 = _div(f[7], x12)
            x9 = _div(f[9], x12)
            x6 = _div(x6, _sinh_m(x6))
            x7 = _div(x7, _cosh_m(x7))
            x8 = _div(x8, _sinh_m(x8))
            x9 = _div(x9, _cosh_m(x9))
            x2 = x6 * f[2]
            x1 = x7 * f[4]
            x0 = f[1] + 0.0
            x2 = x2 * x6
            x1 = x1 * x7
            x2 = x2 + x0
            x0 = x8 * f[6]
            x2 = x2 + x1
            x1 = x9 * f[8]
            x0 = x0 * x8
            x2 = x2 + x0
            x1 = x1 * x9
            x2 = x2 + x1
            x2 = x2 * xk
            x10 = x10 + x2
        return x10 * 4.184

    # ---------------------------------------------------------------- CTherm::H0 [180104728]
    def _h0(self):
        s = self.s
        x12 = s[0xc8 >> 3]
        x10 = 0.0
        for k in range(21):
            xk = s[1 + k]
            if 0.0 >= xk:
                continue
            f = _IDEAL[k]
            x9 = _coth(_div(f[3], x12))
            x8 = _tanh(_div(f[5], x12))
            x7 = _coth(_div(f[7], x12))
            x2 = _tanh(_div(f[9], x12))
            x1 = f[2] * f[3]
            x3 = x12 * f[1]
            x0 = f[0] + 0.0
            x1 = x1 * x9
            x3 = x3 + x0
            x0 = f[4] * f[5]
            x3 = x3 + x1
            x1 = f[6] * f[7]
            x0 = x0 * x8
            x1 = x1 * x7
            x3 = x3 - x0
            x0 = f[8] * f[9]
            x3 = x3 + x1
            x0 = x0 * x2
            x3 = x3 - x0
            x3 = x3 * xk
            x10 = x10 + x3
        x10 = x10 * 4.184
        x10 = _div(x10, s[0xd8 >> 3])
        return x10 * 1000.0

    # ---------------------------------------------------------------- CTherm::S0 [180104de4]
    def _s0(self):
        s = self.s
        x1 = s[0xc8 >> 3]
        acc = 0.0
        x6 = 0.0
        for k in range(21):
            xk = s[1 + k]
            if 0.0 >= xk:
                continue
            f = _IDEAL[k]
            x11 = _div(f[3], x1)
            x8 = _div(f[7], x1)
            x10 = _div(f[9], x1)
            x14 = _div(f[5], x1)
            x9 = _coth(x11)
            x12 = _tanh(x14)
            x15 = _coth(x8)
            t4 = _tanh(x10)
            sh1 = _sinh_m(x11)
            ch2 = _cosh_m(x14)
            sh3 = _sinh_m(x8)
            ch4 = _cosh_m(x10)
            x13 = f[10] + 0.0
            x0 = _logm(x1)
            x9 = x9 * x11
            x0 = x0 * f[1]
            x13 = x13 + x0
            x0 = _logm(sh1)
            x12 = x12 * x14
            x9 = x9 - x0
            x9 = x9 * f[2]
            x13 = x13 + x9
            x0 = _logm(ch2)
            x15 = x15 * x8
            x12 = x12 - x0
            x12 = x12 * f[4]
            x13 = x13 - x12
            x0 = _logm(sh3)
            x6 = t4 * x10
            x15 = x15 - x0
            x15 = x15 * f[6]
            x13 = x13 + x15
            x0 = _logm(ch4)
            x6 = x6 - x0
            x6 = x6 * f[8]
            x13 = x13 - x6
            x13 = x13 * xk
            acc = acc + x13
            x6 = acc
        x6 = x6 * 4.184
        mez = 0.0
        for k in range(21):
            xk = s[1 + k]
            if xk == 0.0:
                continue
            x0 = _logm(xk)
            x0 = x0 * xk
            mez = mez + x0
        x1 = mez * -8.31451
        x1 = x1 + x6
        x1 = _div(x1, s[0xd8 >> 3])
        return x1 * 1000.0

    def _tres(self, D):
        self._zdetail(D)
        self._dzdt(D)
        self._d2zdt2(D)

    # ---------------------------------------------------------------- CTherm::CprCvrHS [180104330]
    def _cprcvrhs(self):
        s, c = self.s, self.c
        x7 = 0.0
        x10 = 0.0
        x13 = 0.0
        x8 = self._cpi()
        s[0x128 >> 3] = self._h0()
        x15 = self._s0()
        x1 = x8 * 1000.0
        x1 = _div(x1, s[0xd8 >> 3])
        s[0x140 >> 3] = x1
        for k in range(5):
            gx = _GX[k]
            x6 = gx + 1.0
            x6 = x6 * s[0x100 >> 3]
            x6 = x6 * 0.5
            self._tres(x6)
            x4 = _GW[k]
            x2 = c[0x7f98 >> 3]
            x3 = s[0xc8 >> 3]
            x1 = x3
            x0 = x4
            x3 = x3 * x2
            x1 = x1 * c[0x7fa0 >> 3]
            x0 = x0 * x2
            x3 = x3 + c[0x7f90 >> 3]
            x3 = x3 - 1.0
            x0 = _div(x0, x6)
            x3 = x3 * x4
            x13 = x13 + x0
            x0 = x2
            x0 = x0 * 2.0
            x3 = _div(x3, x6)
            x1 = x1 + x0
            x10 = x10 + x3
            x1 = x1 * x4
            x1 = _div(x1, x6)
            x6 = 1.0 - gx
            x6 = x6 * s[0x100 >> 3]
            x7 = x7 + x1
            x6 = x6 * 0.5
            self._tres(x6)
            x3 = _GW[k]
            x4 = c[0x7f98 >> 3]
            x2 = s[0xc8 >> 3]
            x0 = x3
            x1 = x2
            x1 = x1 * c[0x7fa0 >> 3]
            x0 = x0 * x4
            x0 = _div(x0, x6)
            x13 = x13 + x0
            x0 = x4
            x4 = x4 * x2
            x0 = x0 * 2.0
            x4 = x4 + c[0x7f90 >> 3]
            x4 = x4 - 1.0
            x1 = x1 + x0
            x4 = x4 * x3
            x1 = x1 * x3
            x4 = _div(x4, x6)
            x1 = _div(x1, x6)
            x10 = x10 + x4
            x7 = x7 + x1
        self._tres(s[0x100 >> 3])
        x1 = s[0x100 >> 3]
        x5 = s[0xc8 >> 3]
        x0 = x5
        x2 = x1
        x5 = x5 * c[0x7f98 >> 3]
        x2 = x2 * c[0x7fa8 >> 3]
        x0 = x0 * x7
        x0 = x0 * 0.5
        x0 = x0 * x1
        x0 = x0 + 1.0
        x0 = x0 * 8.31451
        x8 = x8 - x0
        x0 = s[0xe8 >> 3]
        x5 = x5 + x0
        x2 = x2 + x0
        x5 = x5 * x5
        x1 = x8
        x5 = _div(x5, x2)
        x5 = x5 * 8.31451
        x3 = s[0xd8 >> 3]
        x2 = s[0xe8 >> 3]
        x1 = _div(x1, x3)
        x2 = x2 - 1.0
        x5 = x5 + x8
        x1 = x1 * 1000.0
        x5 = _div(x5, x3)
        s[0x150 >> 3] = x1
        x1 = s[0xc8 >> 3]
        x0 = x1
        x1 = x1 * 8314.51
        x5 = x5 * 1000.0
        x0 = x0 * x13
        s[0x148 >> 3] = x5
        x0 = x0 * 0.5
        x0 = x0 * s[0x100 >> 3]
        x2 = x2 - x0
        x0 = _div(s[0xc0 >> 3], 101325.0)
        x2 = x2 * x1
        x2 = _div(x2, x3)
        x2 = x2 + s[0x128 >> 3]
        s[0x130 >> 3] = x2
        x6 = _logm(x0)
        x0 = _logm(s[0xe8 >> 3])
        x10 = x10 * 0.5
        x10 = x10 * s[0x100 >> 3]
        x6 = x6 - x0
        x6 = x6 + x10
        x6 = x6 * 8314.51
        x6 = _div(x6, s[0xd8 >> 3])
        x15 = x15 - x6
        s[0x138 >> 3] = x15

    # ---------------------------------------------------------------- CTherm::H [1801048b4]
    def _H(self):
        s, c = self.s, self.c
        x7 = 0.0
        s[0x128 >> 3] = self._h0()
        for k in range(5):
            x6 = _GX[k] + 1.0
            x6 = x6 * s[0x100 >> 3]
            x6 = x6 * 0.5
            self._tres(x6)
            x0 = _GW[k]
            x0 = x0 * c[0x7f98 >> 3]
            x0 = _div(x0, x6)
            x6 = 1.0 - _GX[k]
            x6 = x6 * s[0x100 >> 3]
            x7 = x7 + x0
            x6 = x6 * 0.5
            self._tres(x6)
            x0 = _GW[k]
            x0 = x0 * c[0x7f98 >> 3]
            x0 = _div(x0, x6)
            x7 = x7 + x0
        self._tres(s[0x100 >> 3])
        x2 = s[0xc8 >> 3]
        x0 = s[0xe8 >> 3]
        x0 = x0 - 1.0
        x1 = x2
        x2 = x2 * 8314.51
        x1 = x1 * x7
        x1 = x1 * 0.5
        x1 = x1 * s[0x100 >> 3]
        x0 = x0 - x1
        x0 = x0 * x2
        x0 = _div(x0, s[0xd8 >> 3])
        x0 = x0 + s[0x128 >> 3]
        s[0x130 >> 3] = x0
        return x0

    # ---------------------------------------------------------------- CTherm::S [1801050ac]
    def _S(self):
        s, c = self.s, self.c
        x7 = 0.0
        for k in range(5):
            x6 = _GX[k] + 1.0
            x6 = x6 * s[0x100 >> 3]
            x6 = x6 * 0.5
            self._tres(x6)
            x0 = s[0xc8 >> 3]
            x0 = x0 * c[0x7f98 >> 3]
            x0 = x0 + c[0x7f90 >> 3]
            x0 = x0 - 1.0
            x0 = x0 * _GW[k]
            x0 = _div(x0, x6)
            x6 = 1.0 - _GX[k]
            x6 = x6 * s[0x100 >> 3]
            x7 = x7 + x0
            x6 = x6 * 0.5
            self._tres(x6)
            x0 = s[0xc8 >> 3]
            x0 = x0 * c[0x7f98 >> 3]
            x0 = x0 + c[0x7f90 >> 3]
            x0 = x0 - 1.0
            x0 = x0 * _GW[k]
            x0 = _div(x0, x6)
            x7 = x7 + x0
        self._tres(s[0x100 >> 3])
        s0 = self._s0()
        x0 = _div(s[0xc0 >> 3], 101325.0)
        x6 = _logm(x0)
        x0 = _logm(s[0xe8 >> 3])
        x7 = x7 * 0.5
        x7 = x7 * s[0x100 >> 3]
        x6 = x6 - x0
        x6 = x6 + x7
        x6 = x6 * 8314.51
        x6 = _div(x6, s[0xd8 >> 3])
        x0 = s0 - x6
        s[0x138 >> 3] = x0
        return x0

    def _zdetail(self, x0):
        c = self.c
        x6 = -0.0
        x1 = x0
        x7 = x0
        x1 = x1 * c[0x7f48 >> 3]
        x8 = x1
        stk_108 = x1
        x8 = x8 * x1
        x12 = x8
        x12 = x12 * x1
        x14 = x12
        x14 = x14 * x1
        x0 = x14
        x0 = x0 * x1
        stk_28 = x0
        x0 = x0 * x1
        stk_30 = x0
        x0 = x0 * x1
        stk_38 = x0
        x0 = x0 * x1
        stk_40 = x0
        x0 = x1
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_20 = x0
        x0 = x8
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_100 = x0
        x0 = x12
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        x9 = x0
        x0 = x14
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        x3 = 1.0
        x4 = 2.0
        x7 = x7 * c[0x7b08 >> 3]
        x1 = stk_100
        x2 = c[0x7c10 >> 3]
        x10 = 3.0
        x2 = x2 + c[0x7c08 >> 3]
        x11 = 4.0
        x15 = x0
        x2 = x2 + c[0x7c18 >> 3]
        x1 = x1 - x3
        x0 = x8
        x0 = x0 * x4
        x2 = x2 * stk_108
        stk_110 = x0
        x0 = x0 * stk_100
        x6 = x12
        x13 = x14
        x5 = x4
        x7 = x7 + x3
        x6 = x6 * x10
        x13 = x13 * x11
        x1 = x1 - x0
        x0 = x6
        x5 = x5 - x13
        x0 = x0 * x9
        x2 = x2 * x1
        stk_118 = x2
        x2 = x9
        x2 = x2 - x3
        x2 = x2 - x0
        x0 = stk_108
        x1 = x0
        x1 = x1 * c[0x7c00 >> 3]
        x2 = x2 * x1
        x2 = x2 + x7
        x7 = stk_118
        x1 = x15
        x7 = x7 + x2
        x2 = c[0x7c28 >> 3]
        x1 = x1 - x3
        x2 = x2 + c[0x7c20 >> 3]
        x2 = x2 * x0
        x0 = x13
        x0 = x0 * x15
        x1 = x1 - x0
        x0 = c[0x7c38 >> 3]
        x0 = x0 + c[0x7c30 >> 3]
        x2 = x2 * x1
        x1 = c[0x7c48 >> 3]
        x1 = x1 + c[0x7c40 >> 3]
        x0 = x0 * x8
        x7 = x7 + x2
        x0 = x0 * x4
        x1 = x1 + c[0x7c50 >> 3]
        x7 = x7 + x0
        x0 = c[0x7c60 >> 3]
        x1 = x1 * x8
        x0 = x0 + c[0x7c58 >> 3]
        x4 = x4 - stk_110
        x2 = c[0x7c98 >> 3]
        x1 = x1 * x4
        x1 = x1 * stk_100
        x0 = x0 + c[0x7c68 >> 3]
        x2 = x2 + c[0x7c90 >> 3]
        x0 = x0 * x8
        x8 = x8 * c[0x7c70 >> 3]
        x2 = x2 * x12
        x7 = x7 + x1
        x1 = c[0x7c88 >> 3]
        x1 = x1 + c[0x7c80 >> 3]
        x0 = x0 * x5
        x8 = x8 * x5
        x5 = stk_110
        x0 = x0 * x15
        x1 = x1 * x12
        x8 = x8 * x15
        x7 = x7 + x0
        x0 = x12
        x7 = x7 + x8
        x8 = stk_100
        x0 = x0 * c[0x7c78 >> 3]
        x0 = x0 * x10
        x7 = x7 + x0
        x0 = x10
        x0 = x0 - stk_108
        x1 = x1 * x0
        x0 = x10
        x1 = x1 * stk_20
        x0 = x0 - x5
        x2 = x2 * x0
        x7 = x7 + x1
        x1 = c[0x7ca8 >> 3]
        x0 = x10
        x2 = x2 * x8
        x1 = x1 + c[0x7ca0 >> 3]
        x0 = x0 - x6
        x10 = x10 - x13
        x1 = x1 * x12
        x1 = x1 * x0
        x0 = c[0x7cb8 >> 3]
        x7 = x7 + x2
        x1 = x1 * x9
        x0 = x0 + c[0x7cb0 >> 3]
        x7 = x7 + x1
        x1 = c[0x7ce0 >> 3]
        x0 = x0 + c[0x7cc0 >> 3]
        x0 = x0 * x12
        x0 = x0 * x10
        x0 = x0 * x15
        x7 = x7 + x0
        x0 = c[0x7cd0 >> 3]
        x0 = x0 + c[0x7cc8 >> 3]
        x0 = x0 * x14
        x0 = x0 * x11
        x7 = x7 + x0
        x1 = x1 + c[0x7cd8 >> 3]
        x3 = stk_28
        x2 = 5.0
        x0 = x11
        x1 = x1 + c[0x7ce8 >> 3]
        x0 = x0 - x5
        x11 = x11 - x13
        x1 = x1 * x14
        x1 = x1 * x0
        x0 = c[0x7cf8 >> 3]
        x1 = x1 * x8
        x0 = x0 + c[0x7cf0 >> 3]
        x7 = x7 + x1
        x1 = c[0x7d10 >> 3]
        x0 = x0 * x14
        x0 = x0 * x11
        x1 = x1 + c[0x7d08 >> 3]
        x0 = x0 * x15
        x7 = x7 + x0
        x1 = x1 * x3
        x0 = x3
        x0 = x0 * c[0x7d00 >> 3]
        x0 = x0 * x2
        x7 = x7 + x0
        x0 = x2
        x2 = x2 - x13
        x0 = x0 - x5
        x1 = x1 * x0
        x0 = c[0x7d20 >> 3]
        x0 = x0 + c[0x7d18 >> 3]
        x1 = x1 * x8
        x7 = x7 + x1
        x1 = 6.0
        x0 = x0 * x3
        x0 = x0 * x2
        x2 = stk_30
        x3 = stk_40
        x0 = x0 * x15
        x7 = x7 + x0
        x0 = x2
        x2 = x2 * c[0x7d30 >> 3]
        x0 = x0 * c[0x7d28 >> 3]
        x0 = x0 * x1
        x1 = x1 - x5
        x2 = x2 * x1
        x1 = 7.0
        x7 = x7 + x0
        x2 = x2 * x8
        x7 = x7 + x2
        x2 = stk_38
        x0 = x2
        x2 = x2 * c[0x7d40 >> 3]
        x0 = x0 * c[0x7d38 >> 3]
        x0 = x0 * x1
        x1 = x1 - x5
        x2 = x2 * x1
        x7 = x7 + x0
        x1 = x3
        x1 = x1 * c[0x7d48 >> 3]
        x2 = x2 * x8
        x7 = x7 + x2
        x2 = 8.0
        x0 = x2
        x0 = x0 - stk_108
        x2 = x2 - x5
        x1 = x1 * x0
        x1 = x1 * stk_20
        x0 = c[0x7d58 >> 3]
        x0 = x0 + c[0x7d50 >> 3]
        x7 = x7 + x1
        x1 = 9.0
        x0 = x0 * x3
        x3 = x3 * stk_108
        x1 = x1 - x5
        x0 = x0 * x2
        x2 = c[0x7d68 >> 3]
        x0 = x0 * x8
        x2 = x2 + c[0x7d60 >> 3]
        x7 = x7 + x0
        x2 = x2 * x3
        x2 = x2 * x1
        x2 = x2 * x8
        x7 = x7 + x2
        c[0x7f90 >> 3] = x7
        x0 = x7
        return x0

    def _dzdt(self, x0):
        c = self.c
        x6 = -0.0
        x7 = x0
        x9 = x0
        x9 = x9 * c[0x7f48 >> 3]
        x11 = x9
        x11 = x11 * x9
        x10 = x11
        x10 = x10 * x9
        x12 = x10
        x12 = x12 * x9
        x13 = x12
        x13 = x13 * x9
        x14 = x13
        x14 = x14 * x9
        x15 = x14
        x15 = x15 * x9
        x0 = x15
        x0 = x0 * x9
        stk_20 = x0
        x0 = x9
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_f0 = x0
        x0 = x11
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_e8 = x0
        x0 = x10
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_f8 = x0
        x8 = x0
        x0 = x12
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        x2 = 0.0
        stk_e0 = x0
        x2 = 0.0
        for k in range(46):
            x1 = c[(0x2b0 >> 3) + k]
            if x1 == 0.0:
                c[(0x7dd0 >> 3) + k] = 0.0
                continue
            x0 = c[(0x7c00 >> 3) + k]
            if x0 == 0.0:
                c[(0x7dd0 >> 3) + k] = 0.0
                continue
            x1 = x1 * x0
            x1 = x1 * x9
            x1 = _div(x1, c[0x7af0 >> 3])
            c[(0x7dd0 >> 3) + k] = x1
        x7 = x7 * c[0x7fb0 >> 3]
        x0 = c[0x7f60 >> 3]
        x4 = 1.0
        c[0x7f98 >> 3] = x7
        if x0 != 0.0:
            x2 = c[0x7dd0 >> 3]
            x0 = x10
            x1 = x4
            x0 = x0 * 3.0
            x1 = x1 - x0
            x1 = x1 * x2
            x1 = x1 * x8
            x2 = x2 - x1
            x2 = x2 + x7
            c[0x7f98 >> 3] = x2
        x1 = c[0x7dd8 >> 3]
        x5 = 2.0
        x8 = x11
        x0 = x1
        x8 = x8 * x5
        x4 = x4 - x8
        x6 = x12
        x4 = x4 * stk_e8
        x0 = x0 * x4
        x1 = x1 - x0
        x1 = x1 + c[0x7f98 >> 3]
        c[0x7f98 >> 3] = x1
        x2 = c[0x7de0 >> 3]
        x0 = x2
        x0 = x0 * x4
        x2 = x2 - x0
        x2 = x2 + x1
        c[0x7f98 >> 3] = x2
        x3 = c[0x7de8 >> 3]
        x0 = x3
        x0 = x0 * x4
        x4 = 4.0
        x6 = x6 * x4
        x3 = x3 - x0
        x3 = x3 + x2
        x2 = 1.0
        c[0x7f98 >> 3] = x3
        x1 = c[0x7df0 >> 3]
        x2 = x2 - x6
        x0 = x1
        x2 = x2 * stk_e0
        x0 = x0 * x2
        x1 = x1 - x0
        x1 = x1 + x3
        c[0x7f98 >> 3] = x1
        x7 = c[0x7df8 >> 3]
        x0 = x7
        x0 = x0 * x2
        x2 = x5
        x2 = x2 - x6
        x7 = x7 - x0
        x7 = x7 + x1
        c[0x7f98 >> 3] = x7
        x0 = c[0x7e08 >> 3]
        x1 = c[0x7e20 >> 3]
        x0 = x0 + c[0x7e00 >> 3]
        x1 = x1 + c[0x7e18 >> 3]
        x0 = x0 * x9
        x1 = x1 * x9
        x0 = x0 * x5
        x5 = x5 - x8
        x7 = x7 - x0
        x0 = c[0x7e30 >> 3]
        x1 = x1 * x5
        x1 = x1 * stk_e8
        x0 = x0 + c[0x7e28 >> 3]
        x5 = 3.0
        x0 = x0 + c[0x7e38 >> 3]
        x7 = x7 - x1
        x1 = c[0x7e58 >> 3]
        x0 = x0 * x9
        x0 = x0 * x2
        x1 = x1 + c[0x7e50 >> 3]
        x0 = x0 * stk_e0
        x1 = x1 * x11
        x7 = x7 - x0
        x0 = x9
        x0 = x0 * c[0x7e40 >> 3]
        x0 = x0 * x2
        x2 = c[0x7e68 >> 3]
        x0 = x0 * stk_e0
        x7 = x7 - x0
        x0 = x11
        x0 = x0 * c[0x7e48 >> 3]
        x0 = x0 * x5
        x7 = x7 - x0
        x0 = x5
        x0 = x0 - x9
        x1 = x1 * x0
        x1 = x1 * stk_f0
        x7 = x7 - x1
        x2 = x2 + c[0x7e60 >> 3]
        x3 = c[0x7e78 >> 3]
        x0 = x5
        x1 = x5
        x3 = x3 + c[0x7e70 >> 3]
        x0 = x0 - x8
        x2 = x2 * x11
        x2 = x2 * x0
        x2 = x2 * stk_e8
        x3 = x3 * x11
        x0 = x10
        x7 = x7 - x2
        x2 = 5.0
        x0 = x0 * x5
        x5 = x5 - x6
        x1 = x1 - x0
        x0 = c[0x7e88 >> 3]
        x0 = x0 + c[0x7e80 >> 3]
        x3 = x3 * x1
        x1 = c[0x7eb0 >> 3]
        x3 = x3 * stk_f8
        x0 = x0 + c[0x7e90 >> 3]
        x1 = x1 + c[0x7ea8 >> 3]
        x7 = x7 - x3
        x0 = x0 * x11
        x0 = x0 * x5
        x1 = x1 + c[0x7eb8 >> 3]
        x5 = stk_e0
        x3 = stk_e8
        x0 = x0 * x5
        x1 = x1 * x10
        x7 = x7 - x0
        x0 = x10
        x0 = x0 * c[0x7e98 >> 3]
        x0 = x0 * x4
        x7 = x7 - x0
        x0 = x4
        x4 = x4 - x6
        x0 = x0 - x8
        x1 = x1 * x0
        x0 = c[0x7ec8 >> 3]
        x0 = x0 + c[0x7ec0 >> 3]
        x1 = x1 * x3
        x7 = x7 - x1
        x1 = c[0x7ee0 >> 3]
        x0 = x0 * x10
        x0 = x0 * x4
        x1 = x1 + c[0x7ed8 >> 3]
        x0 = x0 * x5
        x7 = x7 - x0
        x0 = x12
        x1 = x1 * x12
        x0 = x0 * c[0x7ed0 >> 3]
        x0 = x0 * x2
        x7 = x7 - x0
        x0 = x2
        x2 = x2 - x6
        x0 = x0 - x8
        x1 = x1 * x0
        x0 = c[0x7ef0 >> 3]
        x0 = x0 + c[0x7ee8 >> 3]
        x1 = x1 * x3
        x7 = x7 - x1
        x1 = 6.0
        x0 = x0 * x12
        x0 = x0 * x2
        x0 = x0 * x5
        x7 = x7 - x0
        x0 = x13
        x13 = x13 * c[0x7f00 >> 3]
        x0 = x0 * c[0x7ef8 >> 3]
        x0 = x0 * x1
        x1 = x1 - x8
        x7 = x7 - x0
        x13 = x13 * x1
        x1 = 7.0
        x13 = x13 * x3
        x0 = x14
        x7 = x7 - x13
        x0 = x0 * c[0x7f08 >> 3]
        x0 = x0 * x1
        x14 = x14 * c[0x7f10 >> 3]
        x2 = 8.0
        x7 = x7 - x0
        x0 = x2
        x1 = x1 - x8
        x0 = x0 - x9
        x2 = x2 - x8
        x14 = x14 * x1
        x14 = x14 * x3
        x1 = x15
        x15 = x15 * c[0x7f20 >> 3]
        x7 = x7 - x14
        x1 = x1 * c[0x7f18 >> 3]
        x15 = x15 * x2
        x1 = x1 * x0
        x15 = x15 * x3
        x0 = stk_20
        x0 = x0 * c[0x7f30 >> 3]
        x1 = x1 * stk_f0
        x7 = x7 - x1
        x1 = 9.0
        x7 = x7 - x15
        x1 = x1 - x8
        x0 = x0 * x1
        x0 = x0 * x3
        x7 = x7 - x0
        c[0x7f98 >> 3] = x7
        x0 = x7
        return x0

    def _d2zdt2(self, x0):
        c = self.c
        x6 = -0.0
        x7 = x0
        x9 = x0
        x9 = x9 * c[0x7f48 >> 3]
        x11 = x9
        x11 = x11 * x9
        x10 = x11
        x10 = x10 * x9
        x12 = x10
        x12 = x12 * x9
        x13 = x12
        x13 = x13 * x9
        x14 = x13
        x14 = x14 * x9
        x15 = x14
        x15 = x15 * x9
        x0 = x15
        x0 = x0 * x9
        stk_20 = x0
        x0 = x9
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_f0 = x0
        x0 = x11
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_e0 = x0
        x0 = x10
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        stk_f8 = x0
        x8 = x0
        x0 = x12
        x0 = -x0  # xor x6
        x0 = _exp(x0)
        x4 = 1.0
        x3 = 0.0
        stk_e8 = x0
        x3 = 0.0
        for k in range(46):
            x2 = c[(0x2b0 >> 3) + k]
            if x2 == 0.0:
                c[(0x7dd0 >> 3) + k] = 0.0
                continue
            x1 = c[(0x7c00 >> 3) + k]
            if x1 == 0.0:
                c[(0x7dd0 >> 3) + k] = 0.0
                continue
            x0 = c[0x7af0 >> 3]
            x1 = x1 * x9
            x1 = x1 * x2
            x0 = x0 * x0
            x2 = x2 + x4
            x1 = x1 * x2
            x1 = _div(x1, x0)
            c[(0x7dd0 >> 3) + k] = x1
        x7 = x7 * c[0x7fb8 >> 3]
        x0 = c[0x7f60 >> 3]
        c[0x7fa0 >> 3] = x7
        if x0 != 0.0:
            x2 = c[0x7dd0 >> 3]
            x0 = x10
            x1 = x4
            x0 = x0 * 3.0
            x1 = x1 - x0
            x1 = x1 * x2
            x1 = x1 * x8
            x2 = x2 - x1
            x2 = x2 + x7
            c[0x7fa0 >> 3] = x2
        x0 = c[0x7dd8 >> 3]
        x5 = 2.0
        x7 = 1.0
        x1 = x0
        x4 = x7
        x8 = x11
        x8 = x8 * x5
        x4 = x4 - x8
        x6 = x12
        x4 = x4 * stk_e0
        x1 = x1 * x4
        x1 = x1 - x0
        x1 = x1 + c[0x7fa0 >> 3]
        c[0x7fa0 >> 3] = x1
        x0 = c[0x7de0 >> 3]
        x2 = x0
        x2 = x2 * x4
        x2 = x2 - x0
        x2 = x2 + x1
        c[0x7fa0 >> 3] = x2
        x0 = c[0x7de8 >> 3]
        x3 = x0
        x3 = x3 * x4
        x4 = 4.0
        x6 = x6 * x4
        x3 = x3 - x0
        x7 = x7 - x6
        x3 = x3 + x2
        x7 = x7 * stk_e8
        c[0x7fa0 >> 3] = x3
        x0 = c[0x7df0 >> 3]
        x1 = x0
        x1 = x1 * x7
        x1 = x1 - x0
        x1 = x1 + x3
        x3 = x5
        c[0x7fa0 >> 3] = x1
        x0 = c[0x7df8 >> 3]
        x3 = x3 - x6
        x2 = x0
        x2 = x2 * x7
        x2 = x2 - x0
        x0 = x5
        x0 = x0 - x8
        x2 = x2 + x1
        c[0x7fa0 >> 3] = x2
        x1 = c[0x7e30 >> 3]
        x7 = c[0x7e20 >> 3]
        x1 = x1 + c[0x7e28 >> 3]
        x7 = x7 + c[0x7e18 >> 3]
        x7 = x7 * x9
        x7 = x7 * x0
        x1 = x1 + c[0x7e38 >> 3]
        x0 = c[0x7e08 >> 3]
        x7 = x7 * stk_e0
        x1 = x1 * x9
        x0 = x0 + c[0x7e00 >> 3]
        x1 = x1 * x3
        x1 = x1 * stk_e8
        x0 = x0 * x9
        x0 = x0 * x5
        x5 = 3.0
        x0 = x0 + x2
        x7 = x7 + x0
        x0 = x9
        x0 = x0 * c[0x7e40 >> 3]
        x7 = x7 + x1
        x1 = c[0x7e58 >> 3]
        x0 = x0 * x3
        x0 = x0 * stk_e8
        x1 = x1 + c[0x7e50 >> 3]
        x7 = x7 + x0
        x0 = x11
        x1 = x1 * x11
        x0 = x0 * c[0x7e48 >> 3]
        x0 = x0 * x5
        x7 = x7 + x0
        x0 = x5
        x0 = x0 - x9
        x1 = x1 * x0
        x1 = x1 * stk_f0
        x2 = c[0x7e68 >> 3]
        x3 = c[0x7e78 >> 3]
        x7 = x7 + x1
        x0 = x5
        x1 = x5
        x2 = x2 + c[0x7e60 >> 3]
        x3 = x3 + c[0x7e70 >> 3]
        x0 = x0 - x8
        x2 = x2 * x11
        x3 = x3 * x11
        x2 = x2 * x0
        x0 = x10
        x2 = x2 * stk_e0
        x0 = x0 * x5
        x5 = x5 - x6
        x1 = x1 - x0
        x0 = c[0x7e88 >> 3]
        x3 = x3 * x1
        x0 = x0 + c[0x7e80 >> 3]
        x1 = c[0x7eb0 >> 3]
        x7 = x7 + x2
        x3 = x3 * stk_f8
        x0 = x0 + c[0x7e90 >> 3]
        x1 = x1 + c[0x7ea8 >> 3]
        x2 = 5.0
        x0 = x0 * x11
        x0 = x0 * x5
        x1 = x1 + c[0x7eb8 >> 3]
        x5 = stk_e8
        x7 = x7 + x3
        x0 = x0 * x5
        x1 = x1 * x10
        x3 = stk_e0
        x7 = x7 + x0
        x0 = x10
        x0 = x0 * c[0x7e98 >> 3]
        x0 = x0 * x4
        x7 = x7 + x0
        x0 = x4
        x4 = x4 - x6
        x0 = x0 - x8
        x1 = x1 * x0
        x0 = c[0x7ec8 >> 3]
        x0 = x0 + c[0x7ec0 >> 3]
        x1 = x1 * x3
        x7 = x7 + x1
        x1 = c[0x7ee0 >> 3]
        x0 = x0 * x10
        x0 = x0 * x4
        x1 = x1 + c[0x7ed8 >> 3]
        x0 = x0 * x5
        x7 = x7 + x0
        x0 = x12
        x1 = x1 * x12
        x0 = x0 * c[0x7ed0 >> 3]
        x0 = x0 * x2
        x7 = x7 + x0
        x0 = x2
        x2 = x2 - x6
        x0 = x0 - x8
        x1 = x1 * x0
        x0 = c[0x7ef0 >> 3]
        x0 = x0 + c[0x7ee8 >> 3]
        x1 = x1 * x3
        x7 = x7 + x1
        x1 = 6.0
        x0 = x0 * x12
        x0 = x0 * x2
        x0 = x0 * x5
        x7 = x7 + x0
        x0 = x13
        x13 = x13 * c[0x7f00 >> 3]
        x0 = x0 * c[0x7ef8 >> 3]
        x0 = x0 * x1
        x1 = x1 - x8
        x7 = x7 + x0
        x13 = x13 * x1
        x0 = x14
        x0 = x0 * c[0x7f08 >> 3]
        x13 = x13 * x3
        x7 = x7 + x13
        x14 = x14 * c[0x7f10 >> 3]
        x1 = 7.0
        x2 = 8.0
        x0 = x0 * x1
        x1 = x1 - x8
        x7 = x7 + x0
        x14 = x14 * x1
        x1 = x15
        x15 = x15 * c[0x7f20 >> 3]
        x14 = x14 * x3
        x0 = x2
        x2 = x2 - x8
        x0 = x0 - x9
        x7 = x7 + x14
        x1 = x1 * c[0x7f18 >> 3]
        x15 = x15 * x2
        x1 = x1 * x0
        x15 = x15 * x3
        x0 = stk_20
        x0 = x0 * c[0x7f30 >> 3]
        x1 = x1 * stk_f0
        x7 = x7 + x1
        x1 = 9.0
        x7 = x7 + x15
        x1 = x1 - x8
        x0 = x0 * x1
        x0 = x0 * x3
        x7 = x7 + x0
        c[0x7fa0 >> 3] = x7
        x0 = x7
        return x0

    def _dzdd(self, x0):
        c = self.c
        x7 = -0.0
        x14 = x0
        x14 = x14 * c[0x7f48 >> 3]
        x9 = x14
        x9 = x9 * x14
        x15 = x9
        stk_120 = x9
        x15 = x15 * x14
        x10 = x15
        x10 = x10 * x14
        x0 = x10
        stk_28 = x10
        x0 = x0 * x14
        x6 = x0
        stk_128 = x0
        x6 = x6 * x14
        x0 = x6
        stk_38 = x6
        x0 = x0 * x14
        stk_40 = x0
        x0 = x0 * x14
        stk_48 = x0
        x0 = x14
        x0 = -x0  # xor x7
        x0 = _exp(x0)
        stk_30 = x0
        x0 = x9
        x0 = -x0  # xor x7
        x0 = _exp(x0)
        stk_110 = x0
        x11 = x0
        x0 = x15
        x0 = -x0  # xor x7
        x0 = _exp(x0)
        stk_20 = x0
        x8 = x0
        x0 = x10
        x0 = -x0  # xor x7
        x0 = _exp(x0)
        x3 = 1.0
        stk_118 = x0
        x5 = x0
        for k in range(46):
            c[(0x7dd0 >> 3) + k] = c[(0x7c00 >> 3) + k]
        x2 = c[0x7b08 >> 3]
        x1 = c[0x7f60 >> 3]
        x2 = _div(x2, c[0x7f48 >> 3])
        c[0x7fa8 >> 3] = x2
        if x1 != 0.0:
            x0 = x15
            x1 = x3
            x0 = x0 * 3.0
            x1 = x1 - x0
            x0 = x15
            x0 = x0 * -9.0
            x0 = x0 * x8
            x1 = x1 * x8
            x0 = x0 + x1
            x1 = x1 * -3.0
            x1 = x1 * x6
            x0 = x0 + x1
            x0 = x0 * c[0x7dd0 >> 3]
            x0 = x0 - c[0x7dd0 >> 3]
            x0 = x0 + x2
            c[0x7fa8 >> 3] = x0
        x13 = 2.0
        x7 = -4.0
        x6 = -2.0
        x0 = x3
        x3 = x9
        x12 = x9
        x3 = x3 * x7
        x12 = x12 * x13
        x0 = x0 - x12
        x8 = x10
        x3 = x3 * x11
        x0 = x0 * x11
        x11 = 4.0
        x8 = x8 * x11
        x3 = x3 + x0
        x0 = x0 * x6
        x0 = x0 * x9
        x3 = x3 + x0
        x0 = c[0x7dd8 >> 3]
        x1 = x0
        x1 = x1 * x3
        x1 = x1 - x0
        x1 = x1 + c[0x7fa8 >> 3]
        c[0x7fa8 >> 3] = x1
        x0 = c[0x7de0 >> 3]
        x2 = x0
        x2 = x2 * x3
        x2 = x2 - x0
        x2 = x2 + x1
        c[0x7fa8 >> 3] = x2
        x0 = c[0x7de8 >> 3]
        x4 = x0
        x4 = x4 * x3
        x3 = x10
        x4 = x4 - x0
        x0 = 1.0
        x4 = x4 + x2
        x0 = x0 - x8
        x0 = x0 * x5
        x5 = -16.0
        c[0x7fa8 >> 3] = x4
        x3 = x3 * x5
        x3 = x3 * stk_118
        x3 = x3 + x0
        x0 = x0 * x7
        x0 = x0 * x10
        x10 = x14
        x10 = x10 * x11
        x3 = x3 + x0
        x0 = c[0x7df0 >> 3]
        x1 = x3
        x1 = x1 * x0
        x1 = x1 - x0
        x1 = x1 + x4
        x4 = x15
        x4 = x4 * x7
        x4 = x4 * stk_110
        c[0x7fa8 >> 3] = x1
        x0 = c[0x7df8 >> 3]
        x2 = x0
        x2 = x2 * x3
        x2 = x2 - x0
        x0 = x10
        x2 = x2 + x1
        x1 = x13
        c[0x7fa8 >> 3] = x2
        x1 = x1 - x12
        x0 = x0 * c[0x7e00 >> 3]
        x1 = x1 * x13
        x0 = x0 + x2
        x2 = x10
        x1 = x1 * x14
        c[0x7fa8 >> 3] = x0
        x1 = x1 * stk_110
        x2 = x2 * c[0x7e08 >> 3]
        x4 = x4 + x1
        x2 = x2 + x0
        x1 = x1 * x9
        c[0x7fa8 >> 3] = x2
        x1 = -x1  # xor xword ptr [rip + 0x1f371]
        x4 = x4 + x1
        x3 = stk_128
        x0 = x4
        x1 = x4
        x0 = x0 * c[0x7e10 >> 3]
        x0 = x0 + x2
        x3 = x3 * x5
        x2 = x9
        x3 = x3 * stk_118
        c[0x7fa8 >> 3] = x0
        x9 = 9.0
        x1 = x1 * c[0x7e18 >> 3]
        x2 = x2 * x9
        x1 = x1 + x0
        x0 = x13
        c[0x7fa8 >> 3] = x1
        x4 = x4 * c[0x7e20 >> 3]
        x0 = x0 - x8
        x0 = x0 * x13
        x4 = x4 + x1
        x0 = x0 * x14
        c[0x7fa8 >> 3] = x4
        x0 = x0 * stk_118
        x3 = x3 + x0
        x0 = x0 * x6
        x0 = x0 * stk_28
        x3 = x3 + x0
        x0 = x3
        x1 = x3
        x0 = x0 * c[0x7e28 >> 3]
        x0 = x0 + x4
        x4 = 3.0
        c[0x7fa8 >> 3] = x0
        x1 = x1 * c[0x7e30 >> 3]
        x1 = x1 + x0
        x0 = x3
        c[0x7fa8 >> 3] = x1
        x0 = x0 * c[0x7e38 >> 3]
        x0 = x0 + x1
        x1 = x4
        c[0x7fa8 >> 3] = x0
        x1 = x1 - x14
        x3 = x3 * c[0x7e40 >> 3]
        x3 = x3 + x0
        x0 = stk_30
        c[0x7fa8 >> 3] = x3
        x2 = x2 * c[0x7e48 >> 3]
        x2 = x2 + x3
        x3 = x1
        x1 = x1 * x15
        x1 = x1 * stk_30
        x3 = x3 * x4
        c[0x7fa8 >> 3] = x2
        x3 = x3 * stk_120
        x3 = x3 * x0
        x0 = x0 * x15
        x3 = x3 - x0
        x3 = x3 - x1
        x1 = x4
        x1 = x1 - x12
        x0 = x3
        x0 = x0 * c[0x7e50 >> 3]
        x4 = x1
        x4 = x4 * 3.0
        x1 = x1 * x6
        x0 = x0 + x2
        x2 = stk_28
        c[0x7fa8 >> 3] = x0
        x4 = x4 * stk_120
        x3 = x3 * c[0x7e58 >> 3]
        x1 = x1 * x2
        x3 = x3 + x0
        x0 = x2
        c[0x7fa8 >> 3] = x3
        x4 = x4 * stk_110
        x1 = x1 * stk_110
        x0 = x0 * x7
        x0 = x0 * stk_110
        x4 = x4 + x0
        x4 = x4 + x1
        x0 = x4
        x0 = x0 * c[0x7e60 >> 3]
        x0 = x0 + x3
        x3 = 3.0
        x1 = x3
        c[0x7fa8 >> 3] = x0
        x4 = x4 * c[0x7e68 >> 3]
        x4 = x4 + x0
        x0 = x15
        x0 = x0 * x3
        x1 = x1 - x0
        c[0x7fa8 >> 3] = x4
        x2 = x1
        x1 = x1 * -3.0
        x2 = x2 * x3
        x3 = stk_128
        x2 = x2 * stk_120
        x1 = x1 * x3
        x0 = x3
        x0 = x0 * -9.0
        x1 = x1 * stk_20
        x2 = x2 * stk_20
        x0 = x0 * stk_20
        x2 = x2 + x0
        x2 = x2 + x1
        x0 = x2
        x0 = x0 * c[0x7e70 >> 3]
        x0 = x0 + x4
        x4 = stk_38
        c[0x7fa8 >> 3] = x0
        x2 = x2 * c[0x7e78 >> 3]
        x2 = x2 + x0
        x0 = 3.0
        x1 = x0
        x1 = x1 - x8
        c[0x7fa8 >> 3] = x2
        x3 = x1
        x1 = x1 * x4
        x3 = x3 * x0
        x1 = x1 * x7
        x0 = x4
        x4 = stk_128
        x3 = x3 * stk_120
        x1 = x1 * stk_118
        x0 = x0 * x5
        x5 = 16.0
        x3 = x3 * stk_118
        x0 = x0 * stk_118
        x3 = x3 + x0
        x3 = x3 + x1
        x0 = x3
        x1 = x3
        x0 = x0 * c[0x7e80 >> 3]
        x0 = x0 + x2
        x2 = x15
        x2 = x2 * x5
        c[0x7fa8 >> 3] = x0
        x1 = x1 * c[0x7e88 >> 3]
        x1 = x1 + x0
        x0 = x2
        c[0x7fa8 >> 3] = x1
        x3 = x3 * c[0x7e90 >> 3]
        x3 = x3 + x1
        x1 = x11
        c[0x7fa8 >> 3] = x3
        x1 = x1 - x12
        x0 = x0 * c[0x7e98 >> 3]
        x0 = x0 + x3
        x3 = x1
        x1 = x1 * x6
        c[0x7fa8 >> 3] = x0
        x2 = x2 * c[0x7ea0 >> 3]
        x3 = x3 * x11
        x2 = x2 + x0
        x0 = x4
        x3 = x3 * x15
        x0 = x0 * x7
        x1 = x1 * x4
        c[0x7fa8 >> 3] = x2
        x0 = x0 * stk_110
        x3 = x3 * stk_110
        x1 = x1 * stk_110
        x3 = x3 + x0
        x4 = stk_118
        x7 = stk_28
        x6 = stk_38
        x3 = x3 + x1
        x0 = x3
        x1 = x3
        x0 = x0 * c[0x7ea8 >> 3]
        x0 = x0 + x2
        x2 = x11
        c[0x7fa8 >> 3] = x0
        x2 = x2 - x8
        x1 = x1 * c[0x7eb0 >> 3]
        x1 = x1 + x0
        c[0x7fa8 >> 3] = x1
        x3 = x3 * c[0x7eb8 >> 3]
        x3 = x3 + x1
        x1 = x2
        c[0x7fa8 >> 3] = x3
        x1 = x1 * x11
        x1 = x1 * x15
        x15 = stk_40
        x1 = x1 * x4
        x2 = x2 * x15
        x0 = x15
        x0 = x0 * x5
        x2 = x2 * x11
        x0 = x0 * x4
        x2 = x2 * x4
        x1 = x1 - x0
        x1 = x1 - x2
        x2 = x7
        x2 = x2 * 25.0
        x0 = x1
        x0 = x0 * c[0x7ec0 >> 3]
        x0 = x0 + x3
        x3 = 5.0
        c[0x7fa8 >> 3] = x0
        x1 = x1 * c[0x7ec8 >> 3]
        x1 = x1 + x0
        x0 = x6
        c[0x7fa8 >> 3] = x1
        x0 = x0 * x11
        x2 = x2 * c[0x7ed0 >> 3]
        x0 = x0 * stk_110
        x2 = x2 + x1
        x1 = x3
        x1 = x1 - x12
        c[0x7fa8 >> 3] = x2
        x4 = x1
        x1 = x1 * x6
        x4 = x4 * x3
        x1 = x1 * x13
        x1 = x1 * stk_110
        x4 = x4 * x7
        x4 = x4 * stk_110
        x4 = x4 - x0
        x4 = x4 - x1
        x1 = x3
        x1 = x1 - x8
        x0 = x4
        x0 = x0 * c[0x7ed8 >> 3]
        x0 = x0 + x2
        x2 = x1
        c[0x7fa8 >> 3] = x0
        x2 = x2 * x3
        x3 = stk_118
        x4 = x4 * c[0x7ee0 >> 3]
        x2 = x2 * x7
        x7 = stk_48
        x4 = x4 + x0
        x2 = x2 * x3
        x0 = x7
        x1 = x1 * x7
        c[0x7fa8 >> 3] = x4
        x0 = x0 * x5
        x1 = x1 * x11
        x0 = x0 * x3
        x1 = x1 * x3
        x2 = x2 - x0
        x2 = x2 - x1
        x0 = x2
        x0 = x0 * c[0x7ee8 >> 3]
        x5 = stk_110
        x10 = x10 * x7
        x0 = x0 + x4
        x4 = stk_128
        x10 = x10 * x5
        x3 = x4
        c[0x7fa8 >> 3] = x0
        x2 = x2 * c[0x7ef0 >> 3]
        x3 = x3 * 36.0
        x2 = x2 + x0
        x0 = 6.0
        x1 = x0
        c[0x7fa8 >> 3] = x2
        x1 = x1 - x12
        x3 = x3 * c[0x7ef8 >> 3]
        x3 = x3 + x2
        x2 = x1
        x1 = x1 * x15
        x2 = x2 * x0
        c[0x7fa8 >> 3] = x3
        x1 = x1 * x13
        x0 = x15
        x2 = x2 * x4
        x0 = x0 * x11
        x1 = x1 * x5
        x0 = x0 * x5
        x2 = x2 * x5
        x2 = x2 - x0
        x0 = 7.0
        x2 = x2 - x1
        x1 = x0
        x1 = x1 - x12
        x2 = x2 * c[0x7f00 >> 3]
        x4 = x1
        x1 = x1 * x7
        x2 = x2 + x3
        x3 = x6
        x3 = x3 * 49.0
        x4 = x4 * x0
        c[0x7fa8 >> 3] = x2
        x0 = x7
        x3 = x3 * c[0x7f08 >> 3]
        x4 = x4 * x6
        x0 = x0 * x11
        x6 = stk_30
        x3 = x3 + x2
        x2 = 8.0
        c[0x7fa8 >> 3] = x3
        x4 = x4 * x5
        x0 = x0 * x5
        x1 = x1 * x13
        x4 = x4 - x0
        x0 = x6
        x1 = x1 * x5
        x0 = x0 * x7
        x4 = x4 - x1
        x1 = x2
        x4 = x4 * c[0x7f10 >> 3]
        x1 = x1 - x14
        x4 = x4 + x3
        x3 = x1
        x1 = x1 * x7
        c[0x7fa8 >> 3] = x4
        x3 = x3 * x2
        x1 = x1 * x6
        x3 = x3 * x15
        x3 = x3 * x6
        x3 = x3 - x0
        x0 = x2
        x3 = x3 - x1
        x0 = x0 - x12
        x3 = x3 * c[0x7f18 >> 3]
        x3 = x3 + x4
        x4 = x0
        x0 = x0 * x7
        x4 = x4 * x2
        c[0x7fa8 >> 3] = x3
        x4 = x4 * x15
        x4 = x4 * x5
        x4 = x4 - x10
        x0 = x0 * x13
        x0 = x0 * x14
        x0 = x0 * x5
        x4 = x4 - x0
        x0 = x4
        x1 = x9
        x0 = x0 * c[0x7f20 >> 3]
        x1 = x1 - x12
        x2 = x1
        x0 = x0 + x3
        x3 = stk_120
        x2 = x2 * x9
        x1 = x1 * x3
        c[0x7fa8 >> 3] = x0
        x4 = x4 * c[0x7f28 >> 3]
        x2 = x2 * x7
        x1 = x1 * x7
        x4 = x4 + x0
        x0 = x3
        c[0x7fa8 >> 3] = x4
        x2 = x2 * x5
        x1 = x1 * x13
        x0 = x0 * x11
        x1 = x1 * x5
        x0 = x0 * x7
        x0 = x0 * x5
        x2 = x2 - x0
        x2 = x2 - x1
        x1 = x2
        x1 = x1 * c[0x7f30 >> 3]
        x1 = x1 + x4
        c[0x7fa8 >> 3] = x1
        x2 = x2 * c[0x7f38 >> 3]
        x2 = x2 + x1
        x2 = x2 * c[0x7f48 >> 3]
        c[0x7fa8 >> 3] = x2
        x0 = x2
        return x0

    def _temp(self):
        c = self.c
        self._bvir()
        c[0x7c40 >> 3] = c[0x120 >> 3]
        c[0x7cd0 >> 3] = c[0x1b0 >> 3]
        x15 = c[0x7af0 >> 3]
        x15 = _div(x15, c[0x7f40 >> 3])
        x0 = x15
        x0 = _sqrtm(x0)
        x1 = c[0xf0 >> 3]
        x7 = x15
        x13 = x0
        x0 = c[0xe0 >> 3]
        x7 = x7 * x15
        x0 = x0 * c[0x7f60 >> 3]
        x14 = x7
        x14 = x14 * x15
        x1 = _div(x1, x14)
        x12 = x14
        x12 = x12 * x15
        c[0x7c10 >> 3] = x1
        x10 = x12
        x10 = x10 * x15
        x4 = x10
        x4 = x4 * x15
        x0 = x0 * x4
        x1 = x4
        x11 = x4
        x1 = x1 * x10
        x11 = x11 * x15
        c[0x7c00 >> 3] = x0
        x0 = c[0xe8 >> 3]
        x9 = x11
        x0 = _div(x0, x7)
        x9 = x9 * x15
        c[0x7c08 >> 3] = x0
        x0 = c[0xf8 >> 3]
        x0 = x0 * c[0x7f58 >> 3]
        x6 = x9
        x0 = _div(x0, x7)
        x6 = x6 * x15
        x3 = x6
        c[0x7c18 >> 3] = x0
        x0 = c[0x100 >> 3]
        x0 = _div(x0, x7)
        x3 = x3 * x6
        c[0x7c20 >> 3] = x0
        x0 = c[0x108 >> 3]
        x0 = _div(x0, x1)
        x3 = x3 * x14
        x1 = x13
        x5 = x3
        c[0x7c28 >> 3] = x0
        x0 = c[0x118 >> 3]
        x1 = x1 * c[0x110 >> 3]
        x0 = _div(x0, x13)
        x5 = x5 * x15
        x8 = x5
        c[0x7c30 >> 3] = x1
        x1 = c[0x130 >> 3]
        c[0x7c38 >> 3] = x0
        x0 = c[0x128 >> 3]
        x0 = _div(x0, x12)
        x1 = _div(x1, x4)
        x8 = x8 * x15
        c[0x7c48 >> 3] = x0
        x0 = c[0x138 >> 3]
        c[0x7c50 >> 3] = x1
        x1 = c[0x140 >> 3]
        x0 = _div(x0, x3)
        c[0x7c58 >> 3] = x0
        x1 = x1 * c[0x7f50 >> 3]
        x0 = c[0x148 >> 3]
        x2 = c[0x190 >> 3]
        x1 = _div(x1, x8)
        c[0x7c60 >> 3] = x1
        x0 = x0 * c[0x7f58 >> 3]
        x1 = c[0x150 >> 3]
        x0 = _div(x0, x5)
        c[0x7c68 >> 3] = x0
        x1 = x1 * c[0x7f60 >> 3]
        x0 = c[0x158 >> 3]
        x1 = x1 * x15
        c[0x7c70 >> 3] = x1
        x0 = x0 * c[0x7f58 >> 3]
        x1 = c[0x160 >> 3]
        x0 = x0 * x13
        c[0x7c78 >> 3] = x0
        x1 = x1 * c[0x7f50 >> 3]
        x0 = c[0x168 >> 3]
        x1 = _div(x1, x11)
        c[0x7c80 >> 3] = x1
        x0 = x0 * c[0x7f60 >> 3]
        x1 = c[0x178 >> 3]
        x0 = x0 * x15
        c[0x7c88 >> 3] = x0
        x0 = c[0x170 >> 3]
        x0 = _div(x0, x4)
        c[0x7c90 >> 3] = x0
        x1 = x1 * c[0x7f50 >> 3]
        x0 = c[0x180 >> 3]
        x1 = _div(x1, x12)
        c[0x7c98 >> 3] = x1
        x0 = x0 * c[0x7f50 >> 3]
        x1 = c[0x188 >> 3]
        x0 = _div(x0, x15)
        c[0x7ca0 >> 3] = x0
        x1 = x1 * c[0x7f50 >> 3]
        x0 = x11
        x0 = x0 * x4
        x1 = _div(x1, x6)
        c[0x7ca8 >> 3] = x1
        x1 = c[0x1a0 >> 3]
        x2 = x2 * c[0x7f60 >> 3]
        x2 = x2 * x0
        x0 = c[0x198 >> 3]
        x0 = _div(x0, x3)
        c[0x7cb0 >> 3] = x2
        c[0x7cb8 >> 3] = x0
        x1 = x1 * c[0x7f58 >> 3]
        x0 = x13
        x0 = x0 * c[0x1a8 >> 3]
        x1 = _div(x1, x9)
        c[0x7cc8 >> 3] = x0
        x0 = c[0x1b8 >> 3]
        c[0x7cc0 >> 3] = x1
        x1 = c[0x1c0 >> 3]
        x0 = _div(x0, x7)
        x1 = _div(x1, x11)
        c[0x7cd8 >> 3] = x0
        x0 = c[0x1c8 >> 3]
        c[0x7ce0 >> 3] = x1
        x1 = c[0x1d8 >> 3]
        x0 = x0 * c[0x7f58 >> 3]
        x1 = _div(x1, x8)
        c[0x7cf8 >> 3] = x1
        x1 = c[0x1e8 >> 3]
        x0 = _div(x0, x6)
        x1 = _div(x1, x6)
        c[0x7ce8 >> 3] = x0
        x0 = c[0x1d0 >> 3]
        c[0x7d08 >> 3] = x1
        x0 = _div(x0, x5)
        c[0x7cf0 >> 3] = x0
        x0 = c[0x1e0 >> 3]
        x0 = _div(x0, x15)
        c[0x7d00 >> 3] = x0
        x0 = c[0x1f0 >> 3]
        x0 = x0 * c[0x7f58 >> 3]
        x0 = _div(x0, x14)
        c[0x7d10 >> 3] = x0
        x0 = c[0x1f8 >> 3]
        x1 = c[0x200 >> 3]
        x2 = c[0x210 >> 3]
        x0 = _div(x0, x9)
        c[0x7d18 >> 3] = x0
        x1 = x1 * c[0x7f58 >> 3]
        x0 = c[0x208 >> 3]
        x1 = _div(x1, x8)
        c[0x7d20 >> 3] = x1
        x1 = x13
        x1 = x1 * x15
        x0 = _div(x0, x1)
        x1 = c[0x228 >> 3]
        c[0x7d28 >> 3] = x0
        x2 = x2 * c[0x7f50 >> 3]
        x0 = c[0x218 >> 3]
        x2 = _div(x2, x10)
        c[0x7d30 >> 3] = x2
        x0 = x0 * c[0x7f58 >> 3]
        x0 = x0 * x13
        c[0x7d38 >> 3] = x0
        x0 = c[0x220 >> 3]
        x0 = _div(x0, x12)
        c[0x7d40 >> 3] = x0
        x1 = x1 * c[0x7f50 >> 3]
        x0 = c[0x230 >> 3]
        x1 = _div(x1, x11)
        x0 = _div(x0, x14)
        c[0x7d50 >> 3] = x0
        x0 = c[0x240 >> 3]
        c[0x7d48 >> 3] = x1
        x1 = c[0x238 >> 3]
        x1 = x1 * c[0x7f50 >> 3]
        x0 = _div(x0, x15)
        c[0x7d58 >> 3] = x1
        x1 = c[0x248 >> 3]
        c[0x7d60 >> 3] = x0
        x1 = x1 * c[0x7f58 >> 3]
        c[0x7d68 >> 3] = x1


    # ---------------------------------------------------------------- CDetail::pdetail [180103604]
    def _pdetail(self, D):
        c = self.c
        p = self._zdetail(D) * D * 0.00831451 * c[0x7af0 >> 3]
        c[0x7ae8 >> 3] = p
        return p

    # ---------------------------------------------------------------- CDetail::braket [180100864]
    def _braket(self):
        c = self.c
        T = c[0x7af0 >> 3]
        rhomax = _div(1.0, c[0x7f48 >> 3])
        if T > c[0x7f40 >> 3] * 1.2593:
            rhomax = rhomax * 20.0
        videal = _div(T * 0.00831451, c[0x7af8 >> 3])
        if videal * 0.167 > abs(c[0x7b08 >> 3]):
            rho2 = _div(0.95, videal + c[0x7b08 >> 3])
        else:
            rho2 = _div(1.15, videal)
        dl = rho2 / 20.0
        rho1 = 0.0
        p1 = 0.0
        for _ in range(200):
            if rho2 > rhomax and self.status != 0x232e:
                self.status = 0x232e
                dl = _div(c[0x7af8 >> 3], c[0x7af0 >> 3] * 0.00831451) / 20.0 + (rhomax - rho1) * 0.01
                rho2 = dl + rho1
                continue
            p2 = self._pdetail(rho2)
            if p2 > c[0x7af8 >> 3]:
                c[0x7f70 >> 3] = rho1
                c[0x7f80 >> 3] = p1
                c[0x7f78 >> 3] = rho2
                c[0x7f88 >> 3] = p2
                self.status = 0x2328
                return
            if not p2 > p1:
                self.status = 0x232d
                c[0x7f68 >> 3] = rho1
                return
            if self.status == 0x232e:
                dl = dl * 2.0
            rho1 = rho2
            p1 = p2
            rho2 = rho2 + dl
        self.status = 0x232c
        c[0x7f68 >> 3] = rho2

    # ---------------------------------------------------------------- CDetail::ddetail [180102d30]
    def _ddetail(self):
        c = self.c
        c[0x7f68 >> 3] = 0.0
        self._braket()
        if self.status in (0x232c, 0x232d):
            return
        x1 = c[0x7f70 >> 3]
        P = c[0x7af8 >> 3]
        x2 = c[0x7f78 >> 3]
        y1 = c[0x7f80 >> 3] - P
        y2 = c[0x7f88 >> 3] - P
        delx = x1 - x2
        delprv = delx
        x3 = x1
        y3 = y1
        for _ in range(150):
            if y3 * y2 > 0.0:
                delx = x1 - x2
                x3 = x1
                y3 = y1
                delprv = delx
            if abs(y2) > abs(y3):
                x1, y1, x2, y2, x3, y3 = x2, y2, x3, y3, x2, y2
            delbis = (x3 - x2) * 0.5
            delmin = abs(x2) * 1e-07
            interp = False
            if not (delmin > abs(delprv)) and not (abs(y2) > abs(y1)):
                if x3 == x1:
                    xden = y1 - y2
                    xnum = (x2 - x1) * y2
                else:
                    a_ = y3 - y1
                    b_ = y1 - y2
                    c_ = y2 - y3
                    xden = -((b_ * c_) * a_)
                    xnum = (((((y2 * x1) * y3) * c_) + (((y3 * x2) * y1) * a_))
                            + (((x3 * y1) * y2) * b_)) - xden * x2
                if abs(xden * delprv) > abs(xnum) * 2.0:
                    delprv = delx
                    delx = _div(xnum, xden)
                    interp = True
            if not interp:
                delprv = delbis
                delx = delbis
            if c[0x7af8 >> 3] * 1e-06 > abs(y2) and abs(x2) * 1e-06 > abs(delx):
                c[0x7f68 >> 3] = delx + x2
                return
            if delmin > abs(delx):
                delx = _div(delbis, abs(delbis)) * 1.0000009 * delmin
                delprv = delx
            if ((delx + x2) - x3) * delx > 0.0:
                delx = delbis
                delprv = delbis
            x1 = x2
            x2 = x2 + delx
            y1 = y2
            y2 = self._pdetail(x2) - c[0x7af8 >> 3]
        self.status = 0x232c
        c[0x7f68 >> 3] = x2

    # ---------------------------------------------------------------- CDetail::Run [180100590]
    def detail_run(self):
        s, c = self.s, self.c
        if self.flag == 0:
            ch = self._composition_change()
        else:
            ch = True
        self.flag = 1 if ch else 0
        if ch:
            self.n = 0
            self.idx = []
            for k in range(21):
                if s[1 + k] > 0.0:
                    c[(0x7a40 >> 3) + self.n] = s[1 + k]
                    self.idx.append(k)
                    self.n += 1
            self._paramdl()
            self._chardl()
        if (abs(s[0xb0 >> 3] - c[0x60 >> 3]) > 0.001 or abs(s[0xb8 >> 3] - c[0x68 >> 3]) > 0.001
                or self.flag != 0):
            c[0x7af8 >> 3] = s[0xb0 >> 3] * 1e-06
            c[0x7af0 >> 3] = s[0xb8 >> 3]
            self._temp()
            self._ddetail()
            s[0xf8 >> 3] = c[0x7f68 >> 3]
            zb = self._zdetail(c[0x7f68 >> 3])
            s[0xe0 >> 3] = zb
            c[0x7b00 >> 3] = _div(s[0xd8 >> 3] * c[0x7af8 >> 3], (zb * 0.00831451) * c[0x7af0 >> 3])
            self._relativedensity()
            s[0x108 >> 3] = c[0x7b00 >> 3]
            c[0x68 >> 3] = s[0xb8 >> 3]
            c[0x60 >> 3] = s[0xb0 >> 3]
            self.flag = 1
        c[0x7af8 >> 3] = s[0xc0 >> 3] * 1e-06
        c[0x7af0 >> 3] = s[0xc8 >> 3]
        if abs(s[0xc8 >> 3] - c[0x78 >> 3]) > 0.001 or self.flag != 0:
            self._temp()
            self.flag = 1
        if abs(s[0xc0 >> 3] - c[0x70 >> 3]) > 0.001 or self.flag != 0:
            self._ddetail()
            s[0x100 >> 3] = c[0x7f68 >> 3]
            z = self._zdetail(c[0x7f68 >> 3])
            s[0xe8 >> 3] = z
            v = _div(s[0xd8 >> 3] * c[0x7af8 >> 3], (z * 0.00831451) * c[0x7af0 >> 3])
            c[0x7b00 >> 3] = v
            s[0x110 >> 3] = v
            c[0x78 >> 3] = s[0xc8 >> 3]
            c[0x70 >> 3] = s[0xc0 >> 3]
        if s[0xe0 >> 3] > 0.0 and s[0xe8 >> 3] > 0.0:
            s[0xf0 >> 3] = _sqrtm(_div(s[0xe0 >> 3], s[0xe8 >> 3]))
        else:
            s[0xe8 >> 3] = 0.0
            s[0xe0 >> 3] = 0.0
            s[0xf0 >> 3] = 0.0
            self.status = 0x232b
        self.flag = 0

    # ---------------------------------------------------------------- CTherm::run [18010530c]
    def therm_run(self):
        s, c = self.s, self.c
        self.detail_run()
        if not s[0x100 >> 3] > 0.0:
            return 1
        self._dzdd(s[0x100 >> 3])
        self._cprcvrhs()
        x6 = _div(s[0x148 >> 3], s[0x150 >> 3])
        s[0x158 >> 3] = x6
        x6 = x6 * 8.31451
        x0 = c[0x7fa8 >> 3]
        x6 = x6 * 1000.0
        x0 = x0 * s[0x100 >> 3]
        x0 = x0 + s[0xe8 >> 3]
        x6 = x6 * s[0xc8 >> 3]
        x6 = _div(x6, s[0xd8 >> 3])
        x6 = x6 * x0
        x0 = _sqrtm(x6)
        x6 = x6 * s[0x110 >> 3]
        x6 = _div(x6, s[0xc0 >> 3])
        s[0x168 >> 3] = x0
        s[0x160 >> 3] = x6
        return 0

    # ---------------------------------------------------------------- CTherm::HS_Mode [180104a5c]
    def hs_mode(self, H_obj, S_obj):
        s = self.s
        T0 = s[0xc8 >> 3]
        P0 = s[0xc0 >> 3]
        p_max = P0 * 2.0
        t_max = T0 * 1.5
        p_min = P0 * 0.1
        t_min = T0 * 0.67
        t_prev = T0
        t_act = T0 + 10.0
        self.detail_run()
        rH_prev = self._H() - H_obj
        for k in range(100):
            s[0xc8 >> 3] = t_act
            s[0xc0 >> 3] = P0
            p_ant = P0
            p_sig = P0 * 0.1
            self.detail_run()
            f0 = self._S() - S_obj
            j = 0
            while j < 100:
                p_act = p_sig
                s[0xc0 >> 3] = p_act
                self.detail_run()
                f1 = self._S() - S_obj
                if 0.001 > _div(abs(f0 - f1), S_obj):
                    break
                p_n = _div(f1 * p_ant - f0 * p_act, f1 - f0)
                if p_min >= p_n:
                    p_n = p_min
                if p_n >= p_max:
                    p_n = p_max
                p_sig = p_n
                j += 1
                p_ant = p_act
                f0 = f1
            if j >= 100:
                self.status = 0x232c
            rH = self._H() - H_obj
            if 0.001 > _div(abs(rH_prev - rH), H_obj) and k > 0:
                return
            t_n = _div(rH * t_prev - rH_prev * t_act, rH - rH_prev)
            if t_n >= t_max:
                t_n = t_max
            if t_min >= t_n:
                t_n = t_act + 10.0
                s[0xc8 >> 3] = t_n
                self.detail_run()
                rH = self._H() - H_obj
            t_prev = t_act
            rH_prev = rH
            t_act = t_n
        self.status = 0x232c


def crit(fracciones21, T_K, P_Pa, Tb_K=273.15, Pb_Pa=0.0, v0=0.0):
    """AGA10::crit [1800d0994] sobre una maquina nueva. fracciones21: 21 fracciones molares en el orden del
    struct de FlowXpert (Metano, Nitrogeno, CO2, Etano, Propano, Agua, H2S, Hidrogeno, CO, Oxigeno,
    Isobutano, n-Butano, Isopentano, n-Pentano, n-Hexano, n-Heptano, n-Octano, n-Nonano, n-Decano, Helio,
    Argon). Devuelve (codigo, maquina): codigo 0 = OK (C* en maquina.s[0x170 >> 3]), != 0 = Calculation
    error (CTherm::run fallo: densidad <= 0)."""
    m = MaquinaFX()
    s = m.s
    for k in range(21):
        s[1 + k] = fracciones21[k]
    s[0xb0 >> 3] = Pb_Pa
    s[0xb8 >> 3] = Tb_K
    s[0xc0 >> 3] = P_Pa
    s[0xc8 >> 3] = T_K
    m.init_cache()
    if m.therm_run() != 0:
        return 1, m
    W = s[0x168 >> 3]
    S_f = s[0x138 >> 3]
    H_f = s[0x130 >> 3]
    rho_f = s[0x110 >> 3]
    P_f = s[0xc0 >> 3]
    Z_f = s[0xe8 >> 3]
    T_f = s[0xc8 >> 3]
    vv = v0 * v0
    dE = (W * W - vv) * 0.5
    for _ in range(99):
        m.hs_mode(H_f - dE, S_f)
        if m.therm_run() != 0:
            return 1, m
        W = s[0x168 >> 3]
        dN = (W * W - vv) * 0.5
        if 1.0 > abs(dE - dN):
            break
        dE = dN
    m.T_star, m.P_star_Pa, m.W_star = s[0xc8 >> 3], s[0xc0 >> 3], s[0x168 >> 3]
    rho = s[0x110 >> 3]
    arg = P_f * rho_f * Z_f
    cst = _div(rho * s[0x168 >> 3], _sqrtm(arg))
    s[0xc0 >> 3] = P_f
    s[0xc8 >> 3] = T_f
    s[0x170 >> 3] = cst
    return m.therm_run(), m
