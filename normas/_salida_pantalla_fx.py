# -*- coding: utf-8 -*-
"""Redondeo de SALIDA del factor de compresibilidad F igual que la pantalla de FlowXpert.

[2026-11-16, C-35] FlowXpert calcula F a precision completa, pero lo MUESTRA en una unidad fija por
pantalla con su regla de formato (C-30, FXNumberFormatter.stringFromNumber(v, 7): decimales =
max(3, 7 - digitos de la parte entera), redondeo HALF_EVEN sobre el valor binario). Para F (< 1)
eso da 6 decimales en la unidad de la pantalla:

    pantalla                                   unidad de F en FlowXpert
    API 11.1 2004 (todas), 11.2.1/1M/2/2M,     1/MPa
    ASTM D1550 RD @60F, NGL/LPG 15/20 C y RD
    API Density @15C 1952 y 1980               1/bar
    API Gravity/SG/RD @60F 1952 y 1980         1/psi

Este modulo redondea F SOLO en lo que devuelve la funcion publica llamada desde afuera (app local o
web). Las llamadas internas del motor (por ejemplo, el F de api_mpms_11_2_1 que alimenta CPL dentro
de las tablas) siguen usando F a precision completa: un contador de profundidad hace que solo la
llamada mas externa redondee. CPL, CTPL y los demas resultados NO cambian.

El valor se devuelve en la misma unidad que antes (1/psi o 1/bar), ya redondeado.
"""
import contextvars
import functools
import math
from decimal import ROUND_HALF_EVEN, Context, Decimal

# 1 MPa = 145.03773773 psi = 10 bar (mismo factor que recuento_digitos.py)
_POR_MPA = {"1/psi": 145.03773773, "1/bar": 10.0}

_profundidad = contextvars.ContextVar("profundidad_salida_fx", default=0)


def redondear_como_pantalla_fx(valor, unidad_motor: str, unidad_pantalla: str):
    """Redondea `valor` (en `unidad_motor`) a lo que mostraria FlowXpert en `unidad_pantalla`
    y lo devuelve otra vez en `unidad_motor`."""
    if not isinstance(valor, (int, float)) or isinstance(valor, bool) or valor == 0:
        return valor
    if math.isnan(valor) or math.isinf(valor):
        return valor
    # factor motor -> pantalla
    if unidad_pantalla == unidad_motor:
        k = 1.0
    elif unidad_pantalla == "1/MPa":
        k = _POR_MPA[unidad_motor]
    else:
        k = _POR_MPA[unidad_motor] / _POR_MPA[unidad_pantalla]
    v = valor * k
    decimales = max(3, 7 - len(str(int(v))))  # regla C-30
    # Contexto con precision amplia: con F enorme (entradas sin sentido fisico) el contexto por
    # defecto (28 digitos) lanzaba InvalidOperation al cuantizar (C-41, 2026-11-18).
    q = Decimal(v).quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_EVEN,
                            context=Context(prec=800))
    return float(q) / k


def salida_f_como_flowxpert(claves: dict):
    """Decorador. `claves` = {clave_del_dict: (unidad_motor, unidad_pantalla)}.
    Solo redondea si es la llamada mas externa (no anidada dentro de otra funcion decorada)."""
    def deco(fn):
        if getattr(fn, "_salida_fx", False):
            return fn

        @functools.wraps(fn)
        def envoltura(*args, **kwargs):
            token = _profundidad.set(_profundidad.get() + 1)
            try:
                res = fn(*args, **kwargs)
            finally:
                _profundidad.reset(token)
            if _profundidad.get() == 0 and isinstance(res, dict):
                res = dict(res)
                for clave, (u_motor, u_pantalla) in claves.items():
                    if clave in res:
                        res[clave] = redondear_como_pantalla_fx(res[clave], u_motor, u_pantalla)
            return res

        @functools.wraps(fn)
        def sin_redondeo(*args, **kwargs):
            # valor completo: se marca como anidada para que tampoco redondeen las llamadas internas
            token = _profundidad.set(_profundidad.get() + 1)
            try:
                return fn(*args, **kwargs)
            finally:
                _profundidad.reset(token)

        envoltura._salida_fx = True
        envoltura.sin_redondeo_fx = sin_redondeo  # acceso al F completo si se necesita
        return envoltura
    return deco


def aplicar(modulo, tabla: dict):
    """Reemplaza en `modulo` cada funcion de `tabla` {nombre: claves} por su version decorada.
    Las llamadas internas del modulo (que buscan el nombre global) quedan anidadas y no redondean."""
    for nombre, claves in tabla.items():
        setattr(modulo, nombre, salida_f_como_flowxpert(claves)(getattr(modulo, nombre)))
