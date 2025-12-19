import hashlib
import logging

import logging.handlers

import os

import subprocess

import sys

import tempfile



import tkinter as tk

from tkinter import ttk, messagebox, scrolledtext



import requests

from dotenv import load_dotenv

from supabase import create_client, Client



# ============================================

# CONFIGURACION

# ============================================



APP_NAME = "RECA Empresas"

APP_VERSION = "1.0.2"

GITHUB_OWNER = "auyaban"

GITHUB_REPO = "reca-empresas"

UPDATE_ASSET_NAME = "RECA_Setup.exe"
UPDATE_HASH_NAME = "RECA_Setup.exe.sha256"



def _resource_path(relative_path):
    base_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base_dir, relative_path)

LOGO_PATH = _resource_path(os.path.join("logo", "logo_reca.png"))


class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("RECA")
        self.resizable(False, False)
        self.configure(bg="white")
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.logo_image = None

        container = tk.Frame(self, bg="white")
        container.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        if os.path.exists(LOGO_PATH):
            try:
                logo = tk.PhotoImage(file=LOGO_PATH)
                max_w, max_h = 240, 240
                scale = max(1, logo.width() // max_w, logo.height() // max_h)
                if scale > 1:
                    logo = logo.subsample(scale, scale)
                self.logo_image = logo
                tk.Label(container, image=self.logo_image, bg="white").pack(pady=(0, 12))
            except Exception:
                self.logo_image = None

        tk.Label(
            container,
            text="Bienvenido al sistema de gestion de empresas de RECA",
            font=("Arial", 12, "bold"),
            bg="white",
            fg="#003366",
            wraplength=420,
            justify="center",
        ).pack(pady=(0, 12))

        self.status_label = tk.Label(
            container,
            text="Iniciando...",
            font=("Arial", 10),
            bg="white",
            fg="#333333",
        )
        self.status_label.pack(pady=(0, 8))

        self.progress = ttk.Progressbar(container, length=360, mode="determinate", maximum=100)
        self.progress.pack(pady=(0, 12))

        self.log_box = tk.Text(container, height=6, width=52, bg="#f5f5f5", bd=0)
        self.log_box.configure(state="disabled")
        self.log_box.pack(fill=tk.BOTH, expand=False)

        self._center_window(520, 420)

    def _center_window(self, width, height):
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = int((screen_w - width) / 2)
        y = int((screen_h - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def set_status(self, message, progress=None):
        if message:
            self.status_label.config(text=message)
            self._append_log(message)
        if progress is not None:
            self.progress["value"] = max(0, min(100, progress))
        self.update_idletasks()

    def _append_log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert(tk.END, "- " + message + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state="disabled")

    def close(self):
        self.destroy()


def _get_appdata_dir():

    appdata = os.getenv("APPDATA")

    if appdata:

        return os.path.join(appdata, APP_NAME)

    return os.path.join(os.getcwd(), APP_NAME)



def _setup_logging():

    log_dir = os.path.join(_get_appdata_dir(), "logs")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("reca")

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    app_log = logging.handlers.RotatingFileHandler(

        os.path.join(log_dir, "app.log"), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"

    )

    app_log.setLevel(logging.INFO)

    app_log.setFormatter(formatter)

    error_log = logging.handlers.RotatingFileHandler(

        os.path.join(log_dir, "error.log"), maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"

    )

    error_log.setLevel(logging.ERROR)

    error_log.setFormatter(formatter)

    logger.handlers = []

    logger.addHandler(app_log)

    logger.addHandler(error_log)

    logger.propagate = False

    return logger



LOG = _setup_logging()



def _get_env_path():

    env_override = os.getenv("RECA_ENV_PATH")

    if env_override:

        return env_override

    return os.path.join(_get_appdata_dir(), ".env")



def _load_credentials():

    env_path = _get_env_path()

    if os.path.exists(env_path):

        load_dotenv(dotenv_path=env_path, override=True)

    else:

        load_dotenv()



_load_credentials()

SUPABASE_URL = os.getenv("SUPABASE_URL")

SUPABASE_KEY = os.getenv("SUPABASE_KEY")



if not SUPABASE_URL or not SUPABASE_KEY:

    LOG.error("Missing Supabase credentials")

    messagebox.showerror("Error", "Credenciales no configuradas (.env)")



def _parse_version(value):

    value = (value or "").strip().lstrip("v")

    parts = value.split(".")

    try:

        return tuple(int(part) for part in parts)

    except ValueError:

        return ()



def _is_newer_version(latest):

    current = _parse_version(APP_VERSION)

    latest_version = _parse_version(latest)

    if not current or not latest_version:

        return False

    return latest_version > current



def _get_latest_release():

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

    response = requests.get(url, timeout=10)

    if response.status_code != 200:

        LOG.error("Update check failed: %s", response.status_code)

        return None

    return response.json()

def _get_asset_url(release, asset_name):
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset.get("browser_download_url")
    return None




def _download_asset(release):
    download_url = _get_asset_url(release, UPDATE_ASSET_NAME)
    if not download_url:
        return None
    target = os.path.join(tempfile.gettempdir(), UPDATE_ASSET_NAME)
    with requests.get(download_url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(target, "wb") as handler:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handler.write(chunk)
    return target


def _download_hash(release):
    download_url = _get_asset_url(release, UPDATE_HASH_NAME)
    if not download_url:
        return None
    response = requests.get(download_url, timeout=10)
    response.raise_for_status()
    return response.text.strip()


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handler:
        for chunk in iter(lambda: handler.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()




def _run_installer(installer_path):

    args = [installer_path, "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]

    kwargs = {}

    if os.name == "nt":

        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    subprocess.Popen(args, **kwargs)



def check_for_updates():

    try:

        release = _get_latest_release()

        if not release:

            return False

        latest_tag = release.get("tag_name", "")

        if not _is_newer_version(latest_tag):

            return False

        installer_path = _download_asset(release)
        if not installer_path:
            LOG.error("Update asset not found in release %s", latest_tag)
            return False
        expected_hash = _download_hash(release)
        if not expected_hash:
            LOG.error("Update hash not found in release %s", latest_tag)
            return False
        expected_value = expected_hash.split()[0].lower()
        actual_value = _sha256_file(installer_path).lower()
        if expected_value != actual_value:
            LOG.error("Update hash mismatch for %s", latest_tag)
            return False
        LOG.info("Update verified for version %s", latest_tag)
        _run_installer(installer_path)
        return True

    except Exception:

        LOG.exception("Auto-update failed")

        return False





def conectar_supabase():
    """
    Establece conexion con Supabase

    Returns:
        Client: Cliente de Supabase o None si hay error
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        messagebox.showerror("Error", "Credenciales no configuradas")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        LOG.exception("Error conectando a Supabase")
        messagebox.showerror("Error", f"Error conectando: {e}")
        return None

# ============================================

# VENTANA DE FORMULARIO

# ============================================



class FormularioEmpresa(tk.Toplevel):
    """Ventana modal para crear o editar empresas"""

    # Configuracion de campos del formulario
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
                LOG.info("Empresa actualizada: %s", datos.get("nombre_empresa"))

                messagebox.showinfo("Éxito", "Empresa actualizada correctamente")

            else:

                # Crear nueva empresa

                self.supabase.table("empresas").insert(datos).execute()
                LOG.info("Empresa creada: %s", datos.get("nombre_empresa"))

                messagebox.showinfo("Éxito", "Empresa creada correctamente")



            self.resultado = "guardado"

            self.destroy()



        except Exception as e:
            LOG.exception("Error en formulario de empresa")

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
            LOG.info("Empresa eliminada: %s", self.empresa.get("nombre_empresa"))

            messagebox.showinfo("Éxito", "Empresa eliminada correctamente")

            self.resultado = "eliminado"

            self.destroy()

        except Exception as e:
            LOG.exception("Error en formulario de empresa")

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



    def __init__(self, root, progress_callback=None, on_ready=None):
        """
        Inicializa la aplicacion

        Args:
            root: Ventana raiz de tkinter
            progress_callback: Funcion para reportar avance
            on_ready: Callback cuando la app termina de iniciar
        """
        self.root = root
        self.root.title("RECA - Gestion de Empresas")
        self.root.geometry("1400x750")

        self._progress_callback = progress_callback
        self._on_ready = on_ready
        self._progress_value = 0
        self._report_progress("Iniciando interfaz...", 5)

        # Inicializar variables
        self._report_progress("Conectando a Supabase...", 15)
        self.supabase = conectar_supabase()
        self.empresas_actuales = []
        self._empresa_por_id = {}
        self.empresa_seleccionada = None
        self._offset = 0
        self._all_loaded = False
        self._is_loading = False
        self._search_term = ""
        self._search_field = "Todos"
        self._sort_state = {}

        # Crear interfaz y cargar datos
        self._report_progress("Construyendo interfaz...", 35)
        self.crear_interfaz()
        self._report_progress("Cargando empresas...", 55)
        self.cargar_todas_empresas()

    def _report_progress(self, message, value=None):
        if value is not None:
            self._progress_value = value
        if self._progress_callback:
            self._progress_callback(message, self._progress_value)

    def _finish_ready(self):
        if self._on_ready:
            self._report_progress("Listo", 100)
            callback = self._on_ready
            self._on_ready = None
            callback()

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
            # Encabezado con funcion de ordenamiento
            self.tree.heading(
                col,
                text=col.replace("_", " ").title(),
                command=lambda c=col: self.ordenar_columna(c)
            )
            # Ancho de columna
            self.tree.column(col, width=self.ANCHOS_COLUMNAS.get(col, 100))

        def on_scrollbar(*args):
            self.tree.yview(*args)
            self._maybe_load_next()

        # Scrollbars
        scroll_y = ttk.Scrollbar(tabla_frame, orient=tk.VERTICAL, command=on_scrollbar)
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
        self.tree.bind("<MouseWheel>", lambda e: self._maybe_load_next())
        self.tree.bind("<Button-4>", lambda e: self._maybe_load_next())
        self.tree.bind("<Button-5>", lambda e: self._maybe_load_next())
        self.tree.bind("<KeyRelease-Next>", lambda e: self._maybe_load_next())
        self.tree.bind("<Configure>", lambda e: self._maybe_load_next())

    def _reset_paginacion(self):
        self._offset = 0
        self._all_loaded = False
        self._is_loading = False
        self.empresas_actuales = []
        self._empresa_por_id = {}
        self.empresa_seleccionada = None
        self._limpiar_tabla()
        self._update_contador()

    def _build_or_filter(self, term):
        safe_term = term.replace(",", " ")
        columnas = [
            "nombre_empresa",
            "nit",
            "ciudad",
            "estado",
            "zona",
            "profesional_asignado",
            "asesor",
            "contacto",
            "telefono",
            "sede",
        ]
        return ",".join([f"{col}.ilike.%{safe_term}%" for col in columnas])

    def _load_next_page(self):
        if not self.supabase or self._all_loaded or self._is_loading:
            return
        self._is_loading = True
        try:
            query = self.supabase.table("empresas").select("*")
            if self._search_term:
                if self._search_field == "Todos":
                    query = query.or_(self._build_or_filter(self._search_term))
                else:
                    campo_columna = {
                        "Nombre": "nombre_empresa",
                        "NIT": "nit",
                        "Ciudad": "ciudad",
                    }.get(self._search_field, "nombre_empresa")
                    query = query.ilike(campo_columna, f"%{self._search_term}%")
            query = query.range(self._offset, self._offset + self.BATCH_SIZE - 1)
            response = query.execute()
            data = response.data or []
            if not data:
                self._all_loaded = True
                return
            self._offset += len(data)
            self.empresas_actuales.extend(data)
            self._mostrar_empresas(data)
            next_value = min(90, max(self._progress_value, 60) + 10)
            self._report_progress(f"Cargando empresas... ({len(self.empresas_actuales)})", next_value)
            if len(data) < self.BATCH_SIZE:
                self._all_loaded = True
            self._update_contador()
            if not self._all_loaded:
                self.root.after(0, self._maybe_load_next)
        except Exception as e:
            LOG.exception("Error cargando empresas")
            messagebox.showerror("Error", f"Error cargando empresas: {e}")
            self._all_loaded = True
        finally:
            self._is_loading = False

    def _maybe_load_next(self):
        if self._all_loaded or self._is_loading:
            return
        first, last = self.tree.yview()
        if last >= 0.98:
            self._load_next_page()

    def _update_contador(self):
        self.contador_label.config(text=f"Resultados: {len(self.empresas_actuales)} empresas")

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
        Carga empresas con paginacion por lotes.
        """
        if not self.supabase:
            self._finish_ready()
            return

        self._search_term = ""
        self._search_field = "Todos"
        self._reset_paginacion()
        self._load_next_page()

        if self._all_loaded and not self.empresas_actuales:
            messagebox.showinfo("Info", "No hay empresas en la base de datos")
        self._finish_ready()


    def buscar_empresas(self):
        """Busca empresas segun el termino y campo seleccionado"""
        if not self.supabase:
            return

        termino = self.search_entry.get().strip()
        if not termino:
            self.cargar_todas_empresas()
            return

        self._search_term = termino
        self._search_field = self.campo_busqueda.get()
        self._reset_paginacion()
        self._load_next_page()

        if self._all_loaded and not self.empresas_actuales:
            messagebox.showinfo("Info", "No hay resultados")

    def limpiar_busqueda(self):
        """Limpia el campo de busqueda y recarga todas las empresas"""
        self.search_entry.delete(0, tk.END)
        self.campo_busqueda.set("Todos")
        self.cargar_todas_empresas()

    def _sort_key(self, value):
        if value is None:
            return ""
        value = str(value).strip()
        if not value:
            return ""
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return value.lower()

    def ordenar_columna(self, col):
        """Ordena la tabla por la columna seleccionada (toggle asc/desc)"""
        ascending = self._sort_state.get(col, True)
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        items.sort(key=lambda item: self._sort_key(item[0]), reverse=not ascending)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
        self._sort_state[col] = not ascending

    def seleccionar(self, event):
        """Maneja la seleccion de una empresa con un click"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            empresa_id = item["tags"][0] if item["tags"] else None
            if empresa_id is not None:
                empresa_id = str(empresa_id)
            self.empresa_seleccionada = self._empresa_por_id.get(empresa_id)

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
                (self.supabase.table("empresas")
                    .delete()
                    .eq("id", self.empresa_seleccionada["id"])
                    .execute())
                LOG.info("Empresa eliminada (principal): %s", self.empresa_seleccionada.get("nombre_empresa"))
                messagebox.showinfo("?xito", "Empresa eliminada")
                self.cargar_todas_empresas()
            except Exception as e:
                LOG.exception("Error eliminando empresa (principal)")
                messagebox.showerror("Error", f"Error eliminando: {e}")



    def _limpiar_tabla(self):

        """Limpia todos los elementos de la tabla"""

        for item in self.tree.get_children():

            self.tree.delete(item)



    def _mostrar_empresas(self, empresas):
        """Muestra empresas en la tabla"""
        for empresa in empresas:
            empresa_id = empresa.get("id")
            empresa_id_str = str(empresa_id) if empresa_id is not None else ""
            if empresa_id_str:
                self._empresa_por_id[empresa_id_str] = empresa
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
                empresa.get("sede", ""),
            ), tags=(empresa_id_str,) if empresa_id_str else ())

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    LOG.info("App start version %s", APP_VERSION)
    root = tk.Tk()
    root.withdraw()
    splash = SplashScreen(root)
    splash.set_status("Buscando actualizaciones...", 5)
    if check_for_updates():
        splash.close()
        root.destroy()
        sys.exit(0)

    def on_ready():
        splash.close()
        root.deiconify()

    splash.set_status("Iniciando aplicacion...", 10)
    app = AppRECA(root, progress_callback=splash.set_status, on_ready=on_ready)
    root.mainloop()
