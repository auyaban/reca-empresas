import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from supabase import create_client, Client

# ============================================
# CONFIGURACIÓN
# ============================================

# Importar credenciales de configuración
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    messagebox.showerror("Error", "No se encontró el archivo config.py")
    SUPABASE_URL = None
    SUPABASE_KEY = None


def conectar_supabase():
    """
    Establece conexión con Supabase

    Returns:
        Client: Cliente de Supabase o None si hay error
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        messagebox.showerror("Error", "Credenciales no configuradas")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        messagebox.showerror("Error", f"Error conectando: {e}")
        return None


# ============================================
# VENTANA DE FORMULARIO
# ============================================

class FormularioEmpresa(tk.Toplevel):
    """Ventana modal para crear o editar empresas"""

    # Configuración de campos del formulario
    CAMPOS_CONFIG = [
        ("nombre_empresa", "Nombre Empresa *", True),
        ("nit", "NIT", False),
        ("direccion", "Dirección", False),
        ("ciudad", "Ciudad", False),
        ("correo_1", "Email(s)", False),
        ("contacto", "Contacto(s)", False),
        ("cargo", "Cargo", False),
        ("telefono", "Teléfono(s)", False),
        ("sede", "Sede", False),
        ("zona", "Zona", False),
        ("responsable_visita", "Responsable Visita", False),
        ("asesor", "Asesor", False),
        ("correo_asesor", "Email Asesor", False),
        ("profesional_asignado", "Profesional Asignado", False),
        ("correo_profesional", "Email Profesional", False),
        ("caja_compensacion", "Caja Compensación", False),
        ("estado", "Estado *", True),
        ("observaciones", "Observaciones", False),
    ]

    ESTADOS_DISPONIBLES = ["Activa", "En Proceso", "Pausada", "Cerrada", "Inactiva"]

    def __init__(self, parent, supabase, empresa=None):
        """
        Inicializa el formulario

        Args:
            parent: Ventana padre
            supabase: Cliente de Supabase
            empresa: Datos de empresa a editar (None para crear nueva)
        """
        super().__init__(parent)
        self.parent = parent
        self.supabase = supabase
        self.empresa = empresa
        self.resultado = None
        self.campos = {}

        # Configurar ventana
        titulo = "Editar Empresa" if empresa else "Nueva Empresa"
        self.title(titulo)
        self.geometry("900x700")
        self.resizable(False, False)

        # Crear interfaz
        self.crear_formulario()

        # Convertir en modal
        self.transient(parent)
        self.grab_set()

    def crear_formulario(self):
        """Construye la interfaz del formulario con scroll"""

        # Canvas con scrollbar para manejar muchos campos
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        # Actualizar región de scroll cuando cambia el tamaño
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Título del formulario
        titulo_text = "Editar Empresa" if self.empresa else "Nueva Empresa"
        titulo_label = tk.Label(
            scrollable_frame,
            text=titulo_text,
            font=("Arial", 18, "bold")
        )
        titulo_label.grid(row=0, column=0, columnspan=4, pady=20)

        # Crear campos dinámicamente
        self._crear_campos(scrollable_frame)

        # Crear botones de acción
        self._crear_botones(scrollable_frame, len(self.CAMPOS_CONFIG) + 1)

        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _crear_campos(self, parent):
        """
        Crea todos los campos del formulario

        Args:
            parent: Frame contenedor
        """
        for row, (campo, label, required) in enumerate(self.CAMPOS_CONFIG, start=1):
            # Label del campo
            tk.Label(
                parent,
                text=label,
                font=("Arial", 10, "bold")
            ).grid(row=row, column=0, sticky="w", padx=10, pady=5)

            # Widget según tipo de campo
            if campo == "estado":
                widget = self._crear_campo_estado(parent)
            elif campo == "observaciones":
                widget = self._crear_campo_observaciones(parent)
            else:
                widget = self._crear_campo_texto(parent, campo)

            self.campos[campo] = widget
            widget.grid(row=row, column=1, columnspan=3, sticky="w", padx=10, pady=5)

    def _crear_campo_estado(self, parent):
        """Crea combobox para el campo estado"""
        widget = ttk.Combobox(
            parent,
            values=self.ESTADOS_DISPONIBLES,
            state="readonly",
            width=40,
            font=("Arial", 10)
        )

        # Establecer valor inicial
        if self.empresa:
            valor = self.empresa.get("estado", "En Proceso") or "En Proceso"
            widget.set(valor)
        else:
            widget.set("En Proceso")

        return widget

    def _crear_campo_observaciones(self, parent):
        """Crea área de texto para observaciones"""
        widget = scrolledtext.ScrolledText(
            parent,
            width=50,
            height=5,
            font=("Arial", 10)
        )

        # Cargar valor si existe
        if self.empresa:
            valor = self.empresa.get("observaciones", "") or ""
            widget.insert("1.0", valor)

        return widget

    def _crear_campo_texto(self, parent, campo):
        """Crea campo de entrada de texto simple"""
        widget = tk.Entry(parent, width=60, font=("Arial", 10))

        # Cargar valor si existe
        if self.empresa:
            valor = self.empresa.get(campo, "") or ""
            widget.insert(0, valor)

        return widget

    def _crear_botones(self, parent, row):
        """
        Crea los botones de acción del formulario

        Args:
            parent: Frame contenedor
            row: Fila donde colocar los botones
        """
        btn_frame = tk.Frame(parent)
        btn_frame.grid(row=row, column=0, columnspan=4, pady=20)

        if self.empresa:
            # Modo edición: Guardar y Eliminar
            tk.Button(
                btn_frame,
                text="Guardar Cambios",
                command=self.guardar,
                bg="#28a745",
                fg="white",
                font=("Arial", 12, "bold"),
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                btn_frame,
                text="Eliminar",
                command=self.eliminar,
                bg="#dc3545",
                fg="white",
                font=("Arial", 12),
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)
        else:
            # Modo crear
            tk.Button(
                btn_frame,
                text="Crear Empresa",
                command=self.guardar,
                bg="#28a745",
                fg="white",
                font=("Arial", 12, "bold"),
                padx=20,
                pady=10
            ).pack(side=tk.LEFT, padx=5)

        # Botón cancelar (siempre presente)
        tk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy,
            font=("Arial", 12),
            padx=20,
            pady=10
        ).pack(side=tk.LEFT, padx=5)

    def guardar(self):
        """Guarda o actualiza la empresa en la base de datos"""

        # Recoger datos de todos los campos
        datos = {}
        for campo, widget in self.campos.items():
            if campo == "observaciones":
                datos[campo] = widget.get("1.0", tk.END).strip()
            elif isinstance(widget, ttk.Combobox):
                datos[campo] = widget.get()
            else:
                datos[campo] = widget.get().strip()

        # Validar campo obligatorio
        if not datos["nombre_empresa"]:
            messagebox.showerror("Error", "El nombre de la empresa es obligatorio")
            return

        try:
            if self.empresa:
                # Actualizar empresa existente
                self.supabase.table("empresas").update(datos).eq("id", self.empresa["id"]).execute()
                messagebox.showinfo("Éxito", "Empresa actualizada correctamente")
            else:
                # Crear nueva empresa
                self.supabase.table("empresas").insert(datos).execute()
                messagebox.showinfo("Éxito", "Empresa creada correctamente")

            self.resultado = "guardado"
            self.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Error guardando empresa: {e}")

    def eliminar(self):
        """Elimina la empresa de la base de datos"""

        if not self.empresa:
            return

        # Confirmar eliminación
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de eliminar la empresa '{self.empresa['nombre_empresa']}'?\n\n"
            "Esta acción no se puede deshacer."
        )

        if not confirmar:
            return

        try:
            self.supabase.table("empresas").delete().eq("id", self.empresa["id"]).execute()
            messagebox.showinfo("Éxito", "Empresa eliminada correctamente")
            self.resultado = "eliminado"
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error eliminando empresa: {e}")


# ============================================
# APLICACIÓN PRINCIPAL
# ============================================

class AppRECA:
    """Aplicación principal de gestión de empresas"""

    # Configuración de columnas de la tabla
    COLUMNAS = (
        "nombre_empresa", "nit", "ciudad", "estado", "zona",
        "profesional_asignado", "asesor", "contacto", "telefono", "sede"
    )

    ANCHOS_COLUMNAS = {
        "nombre_empresa": 250,
        "nit": 100,
        "ciudad": 100,
        "estado": 100,
        "zona": 120,
        "profesional_asignado": 150,
        "asesor": 130,
        "contacto": 150,
        "telefono": 100,
        "sede": 100
    }

    # Tamaño del lote para paginación (máximo de Supabase es 1000)
    BATCH_SIZE = 1000

    def __init__(self, root):
        """
        Inicializa la aplicación

        Args:
            root: Ventana raíz de tkinter
        """
        self.root = root
        self.root.title("RECA - Gestión de Empresas")
        self.root.geometry("1400x750")

        # Inicializar variables
        self.supabase = conectar_supabase()
        self.empresas_actuales = []
        self.empresa_seleccionada = None

        # Crear interfaz y cargar datos
        self.crear_interfaz()
        self.cargar_todas_empresas()

    def crear_interfaz(self):
        """Construye la interfaz principal de la aplicación"""

        # Header
        self._crear_header()

        # Barra de búsqueda
        self._crear_barra_busqueda()

        # Tabla de resultados
        self._crear_tabla()

        # Botones de acción
        self._crear_botones_accion()

    def _crear_header(self):
        """Crea el encabezado de la aplicación"""
        header = tk.Frame(self.root, bg="#0066cc", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="RECA - Gestión de Empresas",
            font=("Arial", 24, "bold"),
            bg="#0066cc",
            fg="white"
        ).pack(pady=20)

    def _crear_barra_busqueda(self):
        """Crea la barra de búsqueda"""
        search_frame = tk.Frame(self.root, bg="#f0f0f0", height=70)
        search_frame.pack(fill=tk.X, pady=10, padx=20)

        # Campo de búsqueda
        tk.Label(
            search_frame,
            text="Buscar:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=5)

        self.search_entry = tk.Entry(search_frame, font=("Arial", 12), width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.buscar_empresas())

        # Selector de campo
        tk.Label(
            search_frame,
            text="En:",
            font=("Arial", 12),
            bg="#f0f0f0"
        ).pack(side=tk.LEFT, padx=5)

        self.campo_busqueda = ttk.Combobox(
            search_frame,
            values=["Todos", "Nombre", "NIT", "Ciudad"],
            state="readonly",
            width=12
        )
        self.campo_busqueda.set("Todos")
        self.campo_busqueda.pack(side=tk.LEFT, padx=5)

        # Botones de búsqueda
        tk.Button(
            search_frame,
            text="Buscar",
            command=self.buscar_empresas,
            font=("Arial", 11, "bold"),
            bg="#0066cc",
            fg="white",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            search_frame,
            text="Limpiar",
            command=self.limpiar_busqueda,
            font=("Arial", 11),
            padx=10,
            pady=5
        ).pack(side=tk.LEFT, padx=5)

    def _crear_tabla(self):
        """Crea la tabla de empresas con scrollbars"""
        tabla_frame = tk.Frame(self.root)
        tabla_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Contador de resultados
        self.contador_label = tk.Label(
            tabla_frame,
            text="Resultados: 0 empresas",
            font=("Arial", 11, "bold")
        )
        self.contador_label.grid(row=0, column=0, sticky="w", pady=5)

        # Treeview
        self.tree = ttk.Treeview(
            tabla_frame,
            columns=self.COLUMNAS,
            show="headings",
            height=18
        )

        # Configurar columnas
        for col in self.COLUMNAS:
            # Encabezado con función de ordenamiento
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda c=col: self.ordenar_columna(c)
            )
            # Ancho de columna
            self.tree.column(col, width=self.ANCHOS_COLUMNAS.get(col, 100))

        # Scrollbars
        scroll_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tabla_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scroll_y.set, xscroll=scroll_x.set)

        # Grid layout
        self.tree.grid(row=1, column=0, sticky="nsew")
        scroll_y.grid(row=1, column=1, sticky="ns")
        scroll_x.grid(row=2, column=0, sticky="ew")

        tabla_frame.grid_rowconfigure(1, weight=1)
        tabla_frame.grid_columnconfigure(0, weight=1)

        # Eventos
        self.tree.bind("<ButtonRelease-1>", self.seleccionar)
        self.tree.bind("<Double-1>", self.abrir_editar)

    def _crear_botones_accion(self):
        """Crea los botones de acción principales"""
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Button(
            btn_frame,
            text="Nueva Empresa",
            command=self.nueva_empresa,
            font=("Arial", 12, "bold"),
            bg="#28a745",
            fg="white",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Editar",
            command=self.editar_empresa,
            font=("Arial", 12),
            bg="#ffc107",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Eliminar",
            command=self.eliminar_empresa,
            font=("Arial", 12),
            bg="#dc3545",
            fg="white",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            btn_frame,
            text="Refrescar",
            command=self.cargar_todas_empresas,
            font=("Arial", 12),
            bg="#17a2b8",
            fg="white",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)

    def cargar_todas_empresas(self):
        """
        Carga todas las empresas de la base de datos.
        Usa paginación para superar el límite de 1000 registros de Supabase.
        """
        if not self.supabase:
            return

        # Limpiar tabla
        self._limpiar_tabla()

        try:
            todas_empresas = []
            offset = 0

            # Obtener total de registros
            count_response = self.supabase.table("empresas").select("*", count="exact").limit(1).execute()
            total_registros = count_response.count if hasattr(count_response, 'count') else 0

            # Cargar en lotes para superar el límite de 1000
            while offset < total_registros or offset == 0:
                response = self.supabase.table("empresas")\
                    .select("*")\
                    .range(offset, offset + self.BATCH_SIZE - 1)\
                    .execute()

                if not response.data:
                    break

                todas_empresas.extend(response.data)
                offset += self.BATCH_SIZE

                # Si obtuvimos menos registros que el tamaño del lote, ya terminamos
                if len(response.data) < self.BATCH_SIZE:
                    break

            if not todas_empresas:
                messagebox.showinfo("Info", "No hay empresas en la base de datos")
                return

            # Guardar y mostrar empresas
            self.empresas_actuales = todas_empresas
            self._mostrar_empresas(todas_empresas)

        except Exception as e:
            messagebox.showerror("Error", f"Error cargando empresas: {e}")

    def buscar_empresas(self):
        """Busca empresas según el término y campo seleccionado"""
        if not self.supabase:
            return

        termino = self.search_entry.get().strip()
        if not termino:
            self.cargar_todas_empresas()
            return

        self._limpiar_tabla()

        try:
            campo = self.campo_busqueda.get()

            # Mapear campo de búsqueda a nombre de columna
            campo_columna = {
                "Nombre": "nombre_empresa",
                "NIT": "nit",
                "Ciudad": "ciudad",
                "Todos": "nombre_empresa"
            }.get(campo, "nombre_empresa")

            # Realizar búsqueda
            response = self.supabase.table("empresas")\
                .select("*")\
                .ilike(campo_columna, f"%{termino}%")\
                .execute()

            self.empresas_actuales = response.data
            self._mostrar_empresas(response.data)

        except Exception as e:
            messagebox.showerror("Error", f"Error buscando empresas: {e}")

    def limpiar_busqueda(self):
        """Limpia el campo de búsqueda y recarga todas las empresas"""
        self.search_entry.delete(0, tk.END)
        self.campo_busqueda.set("Todos")
        self.cargar_todas_empresas()

    def ordenar_columna(self, col):
        """
        Ordena la tabla por la columna seleccionada

        Args:
            col: Nombre de la columna a ordenar
        """
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        items.sort(reverse=False)

        for index, (val, k) in enumerate(items):
            self.tree.move(k, '', index)

    def seleccionar(self, event):
        """
        Maneja la selección de una empresa con un click

        Args:
            event: Evento de tkinter
        """
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            empresa_id = item["tags"][0] if item["tags"] else None
            self.empresa_seleccionada = next(
                (e for e in self.empresas_actuales if e.get("id") == empresa_id),
                None
            )

    def abrir_editar(self, event=None):
        """
        Abre el formulario de edición (doble click)

        Args:
            event: Evento de tkinter (opcional)
        """
        if not self.empresa_seleccionada:
            messagebox.showwarning("Aviso", "Selecciona una empresa primero")
            return

        ventana = FormularioEmpresa(self.root, self.supabase, self.empresa_seleccionada)
        self.root.wait_window(ventana)

        # Recargar si hubo cambios
        if ventana.resultado:
            self.cargar_todas_empresas()

    def nueva_empresa(self):
        """Abre el formulario para crear una nueva empresa"""
        if not self.supabase:
            return

        ventana = FormularioEmpresa(self.root, self.supabase)
        self.root.wait_window(ventana)

        # Recargar si se creó
        if ventana.resultado:
            self.cargar_todas_empresas()

    def editar_empresa(self):
        """Edita la empresa seleccionada (botón editar)"""
        if not self.empresa_seleccionada:
            messagebox.showwarning("Aviso", "Selecciona una empresa primero")
            return

        self.abrir_editar()

    def eliminar_empresa(self):
        """Elimina la empresa seleccionada (botón eliminar)"""
        if not self.empresa_seleccionada:
            messagebox.showwarning("Aviso", "Selecciona una empresa primero")
            return

        confirmar = messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar '{self.empresa_seleccionada['nombre_empresa']}'?"
        )

        if confirmar:
            try:
                self.supabase.table("empresas")\
                    .delete()\
                    .eq("id", self.empresa_seleccionada["id"])\
                    .execute()
                messagebox.showinfo("Éxito", "Empresa eliminada")
                self.cargar_todas_empresas()
            except Exception as e:
                messagebox.showerror("Error", f"Error eliminando: {e}")

    def _limpiar_tabla(self):
        """Limpia todos los elementos de la tabla"""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _mostrar_empresas(self, empresas):
        """
        Muestra empresas en la tabla

        Args:
            empresas: Lista de empresas a mostrar
        """
        for empresa in empresas:
            self.tree.insert("", tk.END, values=(
                empresa.get("nombre_empresa", ""),
                empresa.get("nit", ""),
                empresa.get("ciudad", ""),
                empresa.get("estado", ""),
                empresa.get("zona", ""),
                empresa.get("profesional_asignado", ""),
                empresa.get("asesor", ""),
                empresa.get("contacto", ""),
                empresa.get("telefono", ""),
                empresa.get("sede", "")
            ), tags=(empresa.get("id"),))

        # Actualizar contador
        self.contador_label.config(text=f"Resultados: {len(empresas)} empresas")


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    root = tk.Tk()
    app = AppRECA(root)
    root.mainloop()
