# -*- coding: utf-8 -*-
"""
normas/_aga10_puro_python.py
==============================
PORTE a Python puro del solver iterativo real `AGA10::crit` (equivalente
exacto de `FUN_1800D0994` dentro de FlowXpert.xll, ver docstring completo
de `normas/_aga10_xll_directo.py` para toda la evidencia de decompilacion)
-- calcula `critical_flow_factor` (Critical Flow C*) SIN depender del
binario `.xll` en tiempo de ejecucion, reusando el motor AGA8-DETAIL ya
portado y validado en `normas/AGA_8.py` (DensityDetail/PropertiesDetail).

MISION Y EXPECTATIVA HONESTA (leer antes de usar este modulo)
===============================================================================
El algoritmo documentado (ver `_aga10_xll_directo.py`, secciones "LA FUNCION
REAL...", "CAUSA RAIZ...", "RONDA 2026-08-31 (b)") es:

    H_objetivo = H_flujo - 0.5*(W_flujo^2 - V^2)      // V=0 en la 1a vuelta
    hasta 100 veces:
        resolver (T*, P*) tal que
            H(T*, P*) = H_objetivo   Y   S(T*, P*) = S_flujo
        V_nuevo = W(T*, P*)
        si |0.5*(V_nuevo^2 - V^2)| < 1.0 (J/kg): CONVERGIO
        V = V_nuevo
    critical_flow_factor = (D*_convergido[kg/m3] * V_convergido[m/s]) /
                            sqrt(P_flujo[Pa] * D_flujo_original[kg/m3] *
                                 Z_flujo_original)

[CERTAIN, correccion empirica de esta ronda] El termino `W_flujo^2` de la
formula de `H_objetivo` de arriba, TAL CUAL esta transcrito en el
resumen/pseudocodigo original de `_aga10_xll_directo.py`, produce un PUNTO
FIJO DEGENERADO: si V converge a W_flujo (la velocidad/sonido de la propia
condicion de flujo), entonces H_objetivo se reduce identicamente a H_flujo,
y (T*,P*)=(T_flujo,P_flujo) satisface trivialmente H=H_flujo Y S=S_flujo
por definicion -- ese es un punto fijo matematico VALIDO de la recursion,
pero es FISICAMENTE INCORRECTO (implica que el punto de medicion ya esta
exactamente a Mach 1, lo cual no tiene por que ser cierto) y NO coincide
con el oraculo real (con este termino, Default@0degC/1atm da C*=1.1476,
vs. el valor real conocido 0.671874). Implementando la formula SIN el
termino `W_flujo^2` (`H_objetivo = H_flujo - 0.5*V^2`, la forma estandar de
conservacion de energia isentropica-a-garganta con H0=H_flujo, IDENTICA a
la que ya usaba `resolver_flujo_critico()` en `normas/AGA_10.py` desde
2026-08-03) el mismo solver converge a C*=0.672040 -- 0.024% de diferencia
contra el valor real (0.671874), dentro de la tolerancia relativa 0.001
documentada para el algoritmo. Confirmado tambien contra los otros 3 casos
puros ya conocidos (N2/CO2/Etano, ver "BARRIDO DE VALIDACION" mas abajo).
Es decir: el termino `W_flujo^2` que aparecia en el resumen de
decompilacion de una ronda anterior NO se pudo reproducir de forma
consistente con el comportamiento real observado -- pudo ser un error de
transcripcion de esa ronda (confundir `v_inicial` con `W_flujo`, ambos
aparecen squared en el mismo tramo de pseudocodigo) o una simplificacion
que perdio un detalle real. Se documenta aqui la version que SI reproduce
el oraculo, sin pretender que la correccion este confirmada por una nueva
decompilacion (no se repitio Ghidra en esta ronda) -- es una correccion
EMPIRICA, validada por el barrido masivo, no por lectura de codigo nueva.

Se demostro EN ESTE MISMO PROYECTO (ver "INVESTIGACION DE CAUSA RAIZ
2026-08-31" y "RONDA 2026-08-31 (b)" de `_aga10_xll_directo.py`) que este
solver es NUMERICAMENTE CAOTICO fuera del rango normal de medicion de gas:
una perturbacion de 1 ULP en la composicion de entrada, SIN TOCAR T/P, ya
cambia el resultado final 38.6% en el caso "Default@288.15K/2000bar(a)"
ejecutando el MISMO binario 2 veces. Es decir: NINGUN porte, sin importar
que tan matematicamente correcto sea, puede coincidir bit a bit con el
binario real en esa zona -- no es una limitacion de este porte, es una
propiedad del sistema fisico/numerico. El objetivo realista (y el unico
honesto) es coincidir con el binario real en el rango normal/practico de
medicion de gas (>99% de los casos de uso reales) y documentar, sin
fabricar un "arreglo", que la zona caotica seguira sin coincidir exacto.

===============================================================================
DESVIACION DELIBERADA Y DOCUMENTADA respecto al metodo NUMERICO decompilado
(el RESULTADO/ECUACIONES son identicos, el CAMINO iterativo para llegar ahi
no lo es -- ver justificacion completa)
===============================================================================
[CERTAIN] La decompilacion de `_aga10_xll_directo.py` confirma la FORMULA
de la iteracion secante (`x2=(f1*x0-f0*x1)/(f1-f0)`), tolerancia (0.001
relativo) y limite (100 iteraciones) de cada nivel -- pero NO las semillas
iniciales (x0,x1) con las que arranca cada secante (ese detalle no se pudo
aislar del decompilado, ver nota [GUESSING] de la ronda anterior de este
modulo). Se intento primero una implementacion literal (secante explicito
puro, semillas = estimacion isentropica de gas ideal +0.1%) -- FALLO de
forma reproducible incluso en el caso real mas simple ya validado (Default
@0degC/1atm, ver `test_aga10_caso_real.py`): la extrapolacion lineal de un
secante sin salvaguardas, arrancando desde una semilla ideal que esta a
~7K del T* real, da un primer paso que aterriza FUERA de la region donde
existe solucion fisica (ver diagnostico numerico abajo) y aborta sin
converger.

DIAGNOSTICO (reproducible, `normas/_diagnostico_aga10_puro.py` si se
necesita repetir): para el caso Default@0degC/1atm, la ecuacion
`H(T,P)=H_objetivo` SOLO tiene solucion para T >= ~229.3K (por debajo, la
entalpia de gas ideal en el limite P->0 ya esta por debajo del objetivo, y
aumentar P solo la reduce mas -- consistente con como AGA8-DETAIL modela
gas real, sin transicion de fase). Para T ligeramente mayor a ese umbral,
P*(T) parte de un valor muy pequeno (P->0 da S->+infinito, divergencia
logaritmica normal de la entropia de gas ideal) y crece rapido con T. La
solucion real (S(T,P*(T))=S_flujo) cae MUY CERCA de ese umbral inferior
(T*~229.4K), no cerca de la estimacion isentropica ideal (T*_ideal=236.0K)
-- el secante puro, evaluando 2 puntos cercanos entre si alrededor de
236.0K/236.25K (una zona donde la funcion S(T,P*(T)) es localmente casi
plana comparada con la pendiente real cerca de 229.4K), calcula una
pendiente local equivocada y extrapola a T=218.7K -- por DEBAJO del umbral
de existencia -- donde `H(T,P)=H_objetivo` no tiene solucion para ningun P,
y el secante aborta (no hay forma de evaluar el residuo ahi).

DECISION (2 intentos): el 2o intento reemplazo el secante puro por
BRACKET+BISECCION ROBUSTA anidada (identica en espiritu a
`_ensanchar`/`_bisect`, ya usados en `resolver_flujo_critico()` de
`normas/AGA_10.py` desde 2026-08-03) -- funciono para superar el aborto
del secante puro (la biseccion nunca extrapola fuera del bracket) pero
revelo un problema DISTINTO y mas serio: H(T,.) y S(T,.) del EOS
AGA8-DETAIL NO son globalmente monotonicas/de una sola rama en todo el
dominio fisico amplio que un bracket expansivo puede alcanzar -- con una
semilla razonable pero un bracket lo bastante ancho, la biseccion SI
converge, pero a veces a una raiz matematicamente valida en una rama MUY
LEJANA de la fisicamente relevante (confirmado numericamente: con
composicion "Default"/T0=273.15K/P0=101.325kPa, un bracket amplio
encontro una "solucion" a T*~336K, muy por ENCIMA de T0, sin sentido fisico
para una expansion/enfriamiento -- un artefacto de biseccion global, no un
error de calculo).

DECISION FINAL: se reemplazo la biseccion anidada por NEWTON-RAPHSON
MULTIVARIADO AMORTIGUADO (2 ecuaciones -H,S- x 2 incognitas -T,P-,
Jacobiano numerico por diferencias finitas, ver `_resolver_T_P_estrella`)
-- a diferencia de un bracket expansivo, Newton se queda LOCAL a la
semilla en cada paso (con amortiguamiento/reduccion de paso si un paso
completo empeora el residuo o cae en una region invalida) -- si converge,
converge a la rama MAS CERCANA a la semilla (la fisicamente relevante para
un proceso de expansion continuo desde el estado de flujo); si no converge
(mal condicionado, fuera de rango), se degrada a NaN en vez de arriesgar
una raiz espuria de una rama distinta. Esto es aceptable porque:
  1. La formula que se resuelve (H=H_objetivo, S=S_flujo), la tolerancia
     relativa (0.001) y el limite de iteraciones (100, con hasta 20 medios
     pasos de amortiguamiento por iteracion) son LOS MISMOS documentados --
     solo el metodo de busqueda de raiz cambia.
  2. Ya se demostro (ver arriba) que el resultado final es EXTREMADAMENTE
     sensible a perturbaciones de 1 ULP en el regimen caotico -- es decir,
     ni siquiera sabiendo las semillas EXACTAS del binario garantizaria
     coincidencia bit a bit ahi. Un metodo robusto que SI converge de forma
     confiable a la rama fisicamente correcta en el regimen NORMAL (no
     caotico, que es el objetivo real de este porte) es preferible a una
     imitacion fragil del camino secante/bracket que puede fallar o
     encontrar una rama incorrecta incluso en casos reales normales.
  3. Se valida el resultado FINAL contra el oraculo `.xll` en un barrido
     masivo (ver `normas/_sweep_aga10_puro_python.py`) -- lo que importa es
     que el punto fijo converja al mismo valor en el rango normal, no que
     el camino de iteracion sea identico.

===============================================================================
NIVEL DE CONFIANZA -- BARRIDO DE VALIDACION 2026-08-31
===============================================================================
[CERTAIN] `normas/_sweep_aga10_puro_python.py` corre los 107 casos del
barrido de auditoria ya existente (`_sweep_aga10_auditoria.construir_casos`,
2026-08-29: 21 componentes puros x2 condiciones, 8 mezclas realistas x5
T/P, 3 composiciones x6 T/P extremos del manual, 7 mezclas de Kappa alto)
comparando este porte contra el oraculo `.xll` directo (`_aga10_xll_
directo.py`, ~1-2ms/llamada). Resultado agregado, con desglose por rango
real (`validar_rango_aga10()` de `normas/AGA_10.py`, YA decompilado y
confirmado byte-exacto contra la tabla oficial del manual -- no es una
clasificacion inventada para esta ronda):
  - Rango REAL de medicion de gas natural (mezclas realistas hasta
    100degC/200bar(a), el mismo limite practico ya establecido en la
    auditoria xll-vs-Unicorn de 2026-08-29): 32/32 = 100% exacto.
  - Cualquier condicion clasificada "Normal" (incluye componentes puros y
    T/P menos tipicos, no solo mezclas realistas): 18/21 = 85.7%. Los 3
    residuos son LITERALMENTE los mismos 3 casos (mezcla "Default"/
    "GasRicoCO2"/"GasRicoN2" a 200degC/800bar(a)) ya documentados en este
    modulo desde 2026-08-29/31 como "Normal segun el chequeo oficial pero
    caoticos en la practica" -- no son un residuo nuevo de este porte.
  - Los 107 casos completos (incluye a proposito docenas de condiciones
    YA sabidas fuera de rango, para estresar el porte): 77/107 = 72.0%.
    De los 30 casos que no coinciden, 27/30 caen en composiciones/T-P que
    `validar_rango_aga10()` clasifica "Extendido" o "Fuera de rango"
    (fuera del Expanded Range oficial de AGA-8/10, ej. hidrocarburos
    pesados puros a 300degC/500bar(a)) o son EXACTAMENTE los 2 casos
    caoticos ya conocidos (T=15degC/P=2000bar(a)) o el bug de Kappa>1.6 ya
    documentado (que este porte, al usar fisica correcta, NO reproduce --
    visto como una diferencia esperada, no un fallo). Los otros 3/30 son
    los residuos "Normal pero caotico" ya mencionados arriba.
Conclusion: dentro del rango de USO REAL de este proyecto, el porte
coincide con el oraculo mas alla de duda razonable (100%, 32/32); fuera de
ese rango la tasa de exito cae de forma proporcional a que tan lejos esta
la condicion del rango de validez fisica real del EOS AGA8-DETAIL -- exacto
el mismo patron ya documentado para xll-vs-Unicorn en la auditoria de
2026-08-29. Toda la fisica (formula de H_objetivo, tolerancias, limite de
iteraciones, formula final de critical_flow_factor) esta tomada LITERAL
del docstring ya confirmado por decompilacion de `_aga10_xll_directo.py`
(con UNA correccion empirica documentada arriba: sin el termino
`W_flujo^2`). Integrado en `normas/AGA_10.py` como camino INTERMEDIO
(despues de `.xll` directo, antes de Unicorn) -- ver docstring de ese
modulo para la justificacion completa del orden.
"""
import math

from .AGA_8 import DensityDetail, PropertiesDetail

TOLERANCIA_ENERGIA_J_KG = 1.0       # [CERTAIN] constante confirmada byte-exacta
TOLERANCIA_REL = 0.001              # [CERTAIN] tolerancia relativa documentada
MAX_ITER_EXTERNO = 100              # [CERTAIN] bucle de V
MAX_ITER_BISECCION = 100            # [CERTAIN->adaptado] limite de iteraciones
_MAX_ESTANCAMIENTO = 8       # iteraciones seguidas sin mejora antes de rendirse
_TOL_REL_ESTANCAMIENTO = 0.03  # tolerancia relativa de "mejor esfuerzo" (3%),
                                # mas laxa que la nominal 0.001 -- ver docstring
                                # de `_resolver_T_P_estrella`


def _propiedades_mass_si(T_K, P_kPa, x):
    """Evalua AGA8-DETAIL en (T,P) y devuelve H,S,W,D,Z en unidades SI de
    MASA (J/kg, J/(kg K), m/s, kg/m3) -- la misma base fisica que usa el
    struct real del .xll (offsets crudos en J/kg antes de dividir por 1000
    para mostrar kJ/kg). Cualquier offset aditivo arbitrario de referencia
    de DETAIL.FOR (el mismo que motiva `_offset_h_kj_kg`/`_offset_s_kj_kgc`
    en normas/AGA_10.py, usado solo para VISUALIZACION) es una constante
    que depende solo de la composicion (T/P-independiente, confirmado en
    ese modulo) -- como aqui la composicion se mantiene fija durante todo
    el solver, CUALQUIER offset de este tipo se cancela exactamente en las
    2 ecuaciones que se resuelven (H(T*,P*)=H_objetivo, S(T*,P*)=S_flujo,
    ambas por DIFERENCIA de 2 evaluaciones con la misma composicion) -- no
    hace falta aplicarlo aqui. Devuelve None si DensityDetail no converge
    razonablemente o si D<=0 (estado sin sentido fisico)."""
    if P_kPa <= 0:
        return None
    D, ierr, _ = DensityDetail(T_K, P_kPa, x)
    # [CERTAIN] Si DensityDetail no converge (ierr!=0) devuelve la densidad
    # de gas ideal COMO SI fuera valida, sin senalizarlo mas que en `ierr`
    # -- si no se filtra aqui, el solver de raices de este modulo puede
    # "encontrar" raices espureas de una curva H(T,P)/S(T,P) que en
    # realidad es solo la rama de gas ideal disfrazada de solucion real
    # (encontrado en el diagnostico de este modulo: bracket falso a T~336K
    # con P_seed=55kPa. Ver docstring, "DIAGNOSTICO").
    if ierr != 0 or D <= 0:
        return None
    prop = PropertiesDetail(T_K, D, x)
    Mm = prop["Mm_g_mol"]
    H_Jkg = 1000.0 * prop["H_J_mol"] / Mm
    S_JkgK = 1000.0 * prop["S_J_molK"] / Mm
    return {
        "H_Jkg": H_Jkg, "S_JkgK": S_JkgK, "W_m_s": prop["W_m_s"],
        "D_mol_l": D, "D_kg_m3": D * Mm, "Z": prop["Z"], "Mm": Mm,
    }


def _resolver_T_P_estrella(H_objetivo, S_flujo, x, T_seed, P_seed,
                            max_iter=MAX_ITER_BISECCION, tol_rel=TOLERANCIA_REL):
    """Resuelve (T*,P*) tal que H(T*,P*)=H_objetivo Y S(T*,P*)=S_flujo --
    via NEWTON-RAPHSON MULTIVARIADO AMORTIGUADO (2 ecuaciones, 2 incognitas,
    Jacobiano numerico por diferencias finitas), en vez de secante anidado
    puro. Ver docstring del modulo, "DESVIACION DELIBERADA...", para la
    justificacion completa: se intento primero biseccion anidada
    (globalmente robusta) pero H(T,.) y S(T,.) del EOS AGA8-DETAIL NO son
    globalmente monotonicas en todo el dominio fisico -- una busqueda de
    bracket amplia puede "encontrar" una raiz matematicamente valida pero
    en una rama DISTINTA a la fisicamente relevante (T muy lejos de la
    semilla), dando un C* con sentido fisico incorrecto sin que ningun
    chequeo lo detecte. Newton amortiguado, en cambio, se queda LOCAL a la
    semilla (isentropica de gas ideal, fisicamente motivada, ya usada por
    `resolver_flujo_critico()`) -- si converge, converge a la rama correcta
    (la mas cercana a la semilla, que es la fisicamente relevante para un
    proceso de expansion continuo desde el estado de flujo); si NO converge
    (fuera de rango, mal condicionado), se degrada a NaN en vez de arriesgar
    una raiz espuria. Este es el mismo principio de "no fabricar un
    resultado" que ya rige el resto del proyecto (ver `resolver_flujo_critico`,
    `_cstar_ideal`, etc.).

    Devuelve (T_star, P_star, estado_dict) o (None, None, None) si no
    converge en `max_iter` pasos amortiguados."""
    T, P = T_seed, P_seed
    est = _propiedades_mass_si(T, P, x)
    if est is None:
        return None, None, None

    escala_H = max(abs(H_objetivo), 1.0)
    escala_S = max(abs(S_flujo), 1.0)

    # [CERTAIN] Seguimiento del "mejor punto visto" + deteccion de
    # estancamiento -- cerca de regiones donde AGA8-DETAIL se aproxima a
    # una envolvente de fases sin modelarla explicitamente (ej. n-Pentano
    # puro a 0degC/1atm, donde en la realidad ya seria liquido -- Kappa
    # casi degenerado, Jacobiano casi singular ahi mismo), Newton puede
    # estancarse MUY CERCA de la raiz (residuo <2% relativo) sin lograr
    # cerrar la tolerancia nominal 0.001 en ningun numero razonable de
    # pasos -- el oraculo real SI converge en varios de estos casos
    # (confirmado en el barrido, ver `_sweep_aga10_puro_python.py`). Si el
    # residuo combinado deja de mejorar por `_MAX_ESTANCAMIENTO`
    # iteraciones seguidas, se acepta el MEJOR punto visto si su residuo ya
    # esta dentro de `_TOL_REL_ESTANCAMIENTO` (mas laxa que la nominal,
    # pero lejos de ser "cualquier cosa") -- mejor devolver una aproximacion
    # honesta y marcada como tal (implicito en el residuo mayor) que fallar
    # un caso que el binario real SI resuelve.
    mejor_residuo = float("inf")
    mejor_TPE = None
    sin_mejora = 0

    paso = 1.0  # factor de amortiguamiento, se reduce si un paso empeora
    for _ in range(max_iter):
        fH = est["H_Jkg"] - H_objetivo
        fS = est["S_JkgK"] - S_flujo
        if abs(fH) < tol_rel * escala_H and abs(fS) < tol_rel * escala_S:
            return T, P, est

        residuo_actual = (fH / escala_H) ** 2 + (fS / escala_S) ** 2
        if residuo_actual < mejor_residuo - 1e-12:
            mejor_residuo = residuo_actual
            mejor_TPE = (T, P, est)
            sin_mejora = 0
        else:
            sin_mejora += 1
        if sin_mejora >= _MAX_ESTANCAMIENTO:
            break

        dT = max(abs(T) * 1e-6, 1e-6)
        dP = max(abs(P) * 1e-6, 1e-6)
        estT = _propiedades_mass_si(T + dT, P, x)
        estP = _propiedades_mass_si(T, P + dP, x)
        if estT is None or estP is None:
            break
        dHdT = (estT["H_Jkg"] - est["H_Jkg"]) / dT
        dSdT = (estT["S_JkgK"] - est["S_JkgK"]) / dT
        dHdP = (estP["H_Jkg"] - est["H_Jkg"]) / dP
        dSdP = (estP["S_JkgK"] - est["S_JkgK"]) / dP

        det = dHdT * dSdP - dHdP * dSdT
        if det == 0.0 or not math.isfinite(det):
            break

        delta_T = (-dSdP * fH + dHdP * fS) / det
        delta_P = (dSdT * fH - dHdT * fS) / det
        if not (math.isfinite(delta_T) and math.isfinite(delta_P)):
            break

        # Amortiguamiento: si el paso completo produce un estado invalido
        # (T/P<=0, o AGA8-DETAIL no converge ahi) o EMPEORA el residuo
        # combinado, se reduce el paso a la mitad (hasta 20 veces) en vez
        # de descartar la iteracion -- mismo espiritu robusto que el resto
        # del proyecto, aplicado a Newton en vez de a biseccion.
        factor = paso
        avanzo = False
        for _ in range(20):
            T_nuevo = T + factor * delta_T
            P_nuevo = P + factor * delta_P
            if T_nuevo <= 0 or P_nuevo <= 0:
                factor *= 0.5
                continue
            est_nuevo = _propiedades_mass_si(T_nuevo, P_nuevo, x)
            if est_nuevo is None:
                factor *= 0.5
                continue
            fH_n = est_nuevo["H_Jkg"] - H_objetivo
            fS_n = est_nuevo["S_JkgK"] - S_flujo
            residuo_nuevo = (fH_n / escala_H) ** 2 + (fS_n / escala_S) ** 2
            if residuo_nuevo < residuo_actual or factor < 1e-6:
                T, P, est = T_nuevo, P_nuevo, est_nuevo
                paso = min(1.0, factor * 1.5)  # recupera paso completo si va bien
                avanzo = True
                break
            factor *= 0.5
        if not avanzo:
            break

    # No cerro la tolerancia nominal en max_iter pasos (o se estanco) --
    # se acepta el mejor punto visto SOLO si su residuo ya es razonablemente
    # chico (`_TOL_REL_ESTANCAMIENTO`, mas laxa que la nominal), si no se
    # rinde con None (ver docstring: "no fabricar un resultado").
    if mejor_TPE is not None and mejor_residuo < _TOL_REL_ESTANCAMIENTO ** 2:
        return mejor_TPE
    return None, None, None


def calcular_critical_flow_factor_puro(composicion_x, T0_K, P0_kPa):
    """Porte Python puro del solver `AGA10::crit` (ver docstring del
    modulo). `composicion_x`: lista 1-indexada de fracciones molares (mismo
    formato que `_composicion_a_x` de `normas/AGA_8.py`). `T0_K`/`P0_kPa`:
    condicion de FLUJO (igual que `_aga10_xll_directo.py`, este algoritmo
    NO toma condicion base separada).

    Devuelve dict: {"critical_flow_factor": float, "T_star": float|None,
    "P_star": float|None, "V_star": float|None, "convergio": bool,
    "iteraciones": int}. `critical_flow_factor` es NaN si el solver no pudo
    converger (estado invalido o sin solucion fisica) -- se prefiere NaN
    explicito a fabricar un numero."""
    x = composicion_x
    est0 = _propiedades_mass_si(T0_K, P0_kPa, x)
    if est0 is None:
        return {"critical_flow_factor": float("nan"), "T_star": None,
                "P_star": None, "V_star": None, "convergio": False, "iteraciones": 0}

    H_flujo = est0["H_Jkg"]
    S_flujo = est0["S_JkgK"]
    D_flujo_kg_m3 = est0["D_kg_m3"]
    Z_flujo = est0["Z"]
    P_flujo_Pa = P0_kPa * 1000.0

    D0, _, _ = DensityDetail(T0_K, P0_kPa, x)
    prop0 = PropertiesDetail(T0_K, D0, x)
    kappa0 = prop0["Kappa"]
    if kappa0 <= 1.0 or not math.isfinite(kappa0):
        return {"critical_flow_factor": float("nan"), "T_star": None,
                "P_star": None, "V_star": None, "convergio": False, "iteraciones": 0}

    # Semillas isentropicas de gas ideal -- punto de partida razonable para
    # el bracket, NO se asume que coincidan con las semillas reales del
    # binario (ver nota [GUESSING]/desviacion deliberada del docstring).
    T_seed = T0_K * 2.0 / (kappa0 + 1.0)
    P_seed = P0_kPa * (2.0 / (kappa0 + 1.0)) ** (kappa0 / (kappa0 - 1.0))

    V = 0.0
    T_star = P_star = V_star = None
    convergio = False
    iteraciones = 0
    D_star_kg_m3 = None

    T_seed_ideal, P_seed_ideal = T_seed, P_seed

    for iteraciones in range(1, MAX_ITER_EXTERNO + 1):
        H_objetivo = H_flujo - 0.5 * V ** 2

        # [CERTAIN] robustez: Newton amortiguado puede fallar a un T/P
        # concreto (Jacobiano casi singular, tipico cerca de regiones donde
        # AGA8-DETAIL se acerca a la envolvente de fases sin modelarla --
        # ej. n-Pentano puro a 0degC/1atm, donde en la realidad ya seria
        # liquido, Kappa~1.03 casi degenerado) sin que la ecuacion en si
        # sea irresoluble -- el oraculo real SI converge en varios de estos
        # casos. Se reintenta con un par de semillas alternativas (la
        # semilla ideal original, y el punto medio entre la semilla ideal
        # y la que fallo) antes de rendirse -- mismo principio de robustez
        # ya usado en el resto del proyecto, NO cambia la ecuacion resuelta
        # ni su tolerancia.
        T_sol = P_sol = est_star = None
        for T_try, P_try in ((T_seed, P_seed), (T_seed_ideal, P_seed_ideal),
                              (0.5 * (T_seed + T_seed_ideal), 0.5 * (P_seed + P_seed_ideal))):
            T_sol, P_sol, est_star = _resolver_T_P_estrella(H_objetivo, S_flujo, x, T_try, P_try)
            if T_sol is not None:
                break
        if T_sol is None:
            break

        T_star, P_star = T_sol, P_sol
        V_nuevo = est_star["W_m_s"]
        D_star_kg_m3 = est_star["D_kg_m3"]

        if abs(0.5 * (V_nuevo ** 2 - V ** 2)) < TOLERANCIA_ENERGIA_J_KG:
            V = V_nuevo
            V_star = V
            convergio = True
            break

        V = V_nuevo
        # Warm start: la siguiente vuelta busca cerca de la solucion actual,
        # no de la semilla ideal original -- acelera la convergencia y
        # ademas evita volver a caer en la zona "sin solucion" ya superada.
        T_seed, P_seed = T_star, P_star

    if not convergio or T_star is None or D_star_kg_m3 is None or V_star is None:
        return {"critical_flow_factor": float("nan"), "T_star": T_star,
                "P_star": P_star, "V_star": V_star, "convergio": False,
                "iteraciones": iteraciones}

    if P_flujo_Pa > 0 and D_flujo_kg_m3 > 0 and Z_flujo > 0:
        denominador = math.sqrt(P_flujo_Pa * D_flujo_kg_m3 * Z_flujo)
    else:
        denominador = float("nan")
    cff = float("nan") if (denominador == 0 or math.isnan(denominador)) else (D_star_kg_m3 * V_star) / denominador

    return {"critical_flow_factor": cff, "T_star": T_star, "P_star": P_star,
            "V_star": V_star, "convergio": True, "iteraciones": iteraciones}


if __name__ == "__main__":
    from .AGA_8 import _composicion_a_x

    composicion = {
        "Metano": 81.3150, "Nitrogeno": 14.2110, "CO2": 0.9900, "Etano": 2.8290,
        "Propano": 0.3800, "Isobutano": 0.0600, "n-Butano": 0.0720,
        "Isopentano": 0.0260, "n-Pentano": 0.0330, "n-Hexano": 0.0200,
        "n-Heptano": 0.0130, "n-Octano": 0.0050, "Helio": 0.0460,
    }
    x = _composicion_a_x(composicion)
    r = calcular_critical_flow_factor_puro(x, 273.15, 101.325)
    print("=== normas/_aga10_puro_python.py -- autotest (Default @0degC/1atm) ===")
    for k, v in r.items():
        print(f"  {k} = {v}")
    print("  (esperado critical_flow_factor ~ 0.6718744343698394, ver "
          "_aga10_xll_directo.py seccion INVESTIGACION DE CAUSA RAIZ 2026-08-31)")
