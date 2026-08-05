# -*- coding: utf-8 -*-
"""
tema_focqus.py
==============
Paleta de marca FocQus aplicada a ttk (sin dependencia nueva, solo
ttk.Style nativo de Tkinter) + widget de ayuda colapsable reutilizado
por las pestanas de interfaz_calculo_flujo.py que tienen bloques largos
de texto explicativo (ej. AGA-3 FlowXpert).

Paleta FocQus (subconjunto de los 12 colores aprobados, usado en esta
interfaz interna -- no es un documento .docx de cliente):
    navy_primario   #345A8A
    navy_secundario #1F497D
    naranja_acento  #D46A1A
"""

import tkinter as tk
from tkinter import ttk

NAVY_PRIMARIO = "#345A8A"
NAVY_SECUNDARIO = "#1F497D"
NARANJA_ACENTO = "#D46A1A"
FONDO_CLARO = "#F4F6F9"
FONDO_TARJETA = "#FFFFFF"
TEXTO_OSCURO = "#1B2733"
TEXTO_CLARO = "#FFFFFF"
BORDE = "#C9D4E0"


def aplicar_tema(root):
    root.configure(bg=FONDO_CLARO)
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=FONDO_CLARO)
    style.configure("Tarjeta.TFrame", background=FONDO_TARJETA)

    style.configure("TLabel", background=FONDO_CLARO, foreground=TEXTO_OSCURO,
                    font=("Segoe UI", 10))
    style.configure("Tarjeta.TLabel", background=FONDO_TARJETA, foreground=TEXTO_OSCURO,
                    font=("Segoe UI", 10))
    style.configure("Subtitulo.TLabel", background=FONDO_CLARO, foreground=NAVY_PRIMARIO,
                    font=("Segoe UI Semibold", 10))

    style.configure("TLabelframe", background=FONDO_TARJETA, bordercolor=BORDE,
                    relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=FONDO_TARJETA, foreground=NAVY_SECUNDARIO,
                    font=("Segoe UI Semibold", 10))

    style.configure("TEntry", fieldbackground="#FFFFFF", bordercolor=BORDE)
    style.configure("TCombobox", fieldbackground="#FFFFFF")

    style.configure("TNotebook", background=FONDO_CLARO, borderwidth=0)
    style.configure("TNotebook.Tab", background=NAVY_PRIMARIO, foreground=TEXTO_CLARO,
                    padding=(12, 6), font=("Segoe UI", 9))
    style.map("TNotebook.Tab",
              background=[("selected", NARANJA_ACENTO)],
              foreground=[("selected", TEXTO_CLARO)])

    style.configure("Accento.TButton", background=NARANJA_ACENTO, foreground=TEXTO_CLARO,
                    font=("Segoe UI Semibold", 10), padding=(14, 8))
    style.map("Accento.TButton", background=[("active", NAVY_SECUNDARIO)])

    style.configure("Toggle.TButton", background=FONDO_TARJETA, foreground=NAVY_PRIMARIO,
                    font=("Segoe UI", 9), padding=(6, 3), relief="flat")
    style.map("Toggle.TButton", background=[("active", FONDO_CLARO)])

    style.configure("Treeview", background=FONDO_TARJETA, fieldbackground=FONDO_TARJETA,
                    foreground=TEXTO_OSCURO, font=("Segoe UI", 10), rowheight=24,
                    borderwidth=0)
    style.configure("Treeview.Heading", background=NAVY_PRIMARIO, foreground=TEXTO_CLARO)
    style.map("Treeview", background=[("selected", NARANJA_ACENTO)],
              foreground=[("selected", TEXTO_CLARO)])

    return style


class PanelAyudaColapsable(ttk.Frame):
    """Boton toggle + panel de texto que arranca colapsado. Usado para
    sacar bloques largos de texto explicativo (notas de campos/selectores)
    del flujo visual principal sin perder la informacion."""

    def __init__(self, parent, titulo, lineas=None, wraplength=640, constructor_contenido=None):
        """lineas: lista de strings (modo texto, el uso original). Para
        contenido distinto de texto plano (ej. una imagen de diagrama), pasar
        constructor_contenido=fn(frame_contenido) en vez de lineas -- fn
        arma lo que necesite adentro del frame que se le pasa."""
        super().__init__(parent)
        self._abierto = False
        self._boton = ttk.Button(self, style="Toggle.TButton",
                                  text=f"▸  {titulo}", command=self._alternar)
        self._boton.pack(anchor="w", fill="x")

        self._titulo = titulo
        self._contenido = ttk.Frame(self)
        if constructor_contenido is not None:
            constructor_contenido(self._contenido)
        else:
            for texto in (lineas or []):
                ttk.Label(self._contenido, text=texto, foreground="gray",
                          wraplength=wraplength, justify="left",
                          font=("Segoe UI", 8)).pack(anchor="w", padx=(18, 6), pady=(3, 0))

    def _alternar(self):
        self._abierto = not self._abierto
        if self._abierto:
            self._boton.configure(text=f"▾  {self._titulo}")
            self._contenido.pack(fill="x", pady=(4, 0))
        else:
            self._boton.configure(text=f"▸  {self._titulo}")
            self._contenido.pack_forget()
