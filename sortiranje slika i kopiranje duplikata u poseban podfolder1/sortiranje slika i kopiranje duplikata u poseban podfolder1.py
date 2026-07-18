import os
import shutil
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import threading
from datetime import datetime


class ImageSorterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizator Slika Pro")
        self.root.geometry("1500x950")
        self.root.minsize(1300, 800)
        
        # Moderne boje - vibrantne i savremene
        self.colors = {
            'bg_dark': '#0f1419',
            'bg_medium': '#1a1f2e',
            'bg_light': '#252d3d',
            'bg_lighter': '#2d3748',
            'accent_primary': '#00d4ff',
            'accent_secondary': '#7c3aed',
            'accent_hover': '#06b6d4',
            'text_white': '#ffffff',
            'text_gray': '#cbd5e1',
            'text_light_gray': '#94a3b8',
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Varijable
        self.source_dir = tk.StringVar()
        self.dest_dir = tk.StringVar()
        self.copy_mode = tk.BooleanVar(value=False)
        self.check_subdirs = tk.BooleanVar(value=False)
        self.delete_originals = tk.BooleanVar(value=False)
        self.create_backup = tk.BooleanVar(value=True)
        self.rename_files = tk.BooleanVar(value=False)
        self.preserve_structure = tk.BooleanVar(value=False)
        self.skip_small = tk.BooleanVar(value=False)
        self.create_log = tk.BooleanVar(value=True)
        self.sort_by = tk.StringVar(value="godina")
        self.image_format = tk.StringVar(value="svi")
        self.min_size = tk.StringVar(value="0")
        self.max_size = tk.StringVar(value="0")
        self.date_format = tk.StringVar(value="%Y")
        self.rename_pattern = tk.StringVar(value="IMG_{YYYY}{MM}{DD}_{HH}{mm}{ss}_{index}")
        self.remove_duplicates = tk.BooleanVar(value=True)
        self.keep_original_names = tk.BooleanVar(value=False)
        self.compress_images = tk.BooleanVar(value=False)
        self.watermark = tk.BooleanVar(value=False)
        self.processing = False
        
        self.rename_templates = [
            "IMG_{YYYY}{MM}{DD}_{HH}{mm}{ss}_{index}",
            "PHOTO_{YYYY}-{MM}-{DD}_{HH}h{mm}m{ss}s",
            "DSC_{YYYY}{MM}{DD}_{kamera}_{index}",
            "{YYYY}/{MM}/{DD}_Slika_{index}",
            "{lokacija}_{YYYY}{MM}{DD}_{HH}{mm}",
            "Archive_{YYYY}-{MM}_{HH}{mm}{ss}",
            "{YYYY}_IMG_{sequenceid}",
            "IMG_{HH}{mm}{ss}_{randomid}",
            "{dan}_vrijedna_slika_{index}",
            "Backup_{YYYY}{MM}{DD}_{HH}{mm}"
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Header sa gradijentom
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief=tk.FLAT, bd=0)
        header_frame.pack(fill=tk.X, pady=(0, 15), padx=0)
        
        title_label = tk.Label(
            header_frame,
            text="🖼️  Organizator Slika Pro",
            font=("Segoe UI", 28, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_primary']
        )
        title_label.pack(pady=(12, 0), padx=15)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Napredni alat za sortiranje, organizaciju i upravljanje fotografijama",
            font=("Segoe UI", 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light_gray']
        )
        subtitle_label.pack(pady=(3, 12), padx=15)
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        content_frame.grid_columnconfigure(0, weight=2, minsize=450)
        content_frame.grid_columnconfigure(1, weight=1, minsize=350)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        left_panel.grid_rowconfigure(0, weight=0)
        left_panel.grid_rowconfigure(1, weight=0)
        left_panel.grid_rowconfigure(2, weight=0)
        left_panel.grid_rowconfigure(3, weight=0)
        left_panel.grid_rowconfigure(4, weight=1)
        left_panel.grid_rowconfigure(5, weight=0)
        left_panel.grid_columnconfigure(0, weight=1)
        
        self.create_card("📁 Direktoriji", self.create_directory_section, left_panel, 0)
        self.create_card("⚙️ Osnovne opcije", self.create_basic_options, left_panel, 1)
        self.create_card("🎨 Filtri i formati", self.create_filters_section, left_panel, 2)
        self.create_card("✏️ Preimenovanje", self.create_rename_section, left_panel, 3)
        
        advanced_frame = tk.Frame(left_panel, bg=self.colors['bg_dark'])
        advanced_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 10))
        advanced_frame.grid_columnconfigure(0, weight=1)
        advanced_frame.grid_columnconfigure(1, weight=1)
        
        self.create_card("🔧 Napredne opcije", self.create_advanced_options, advanced_frame, 0, column=0, padx=(0, 5))
        self.create_card("🌟 Dodatne funkcije", self.create_extra_features, advanced_frame, 0, column=1, padx=(5, 0))
        
        self.create_action_button(left_panel)
        
        # Right panel
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        right_panel.grid_rowconfigure(0, weight=2)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_rowconfigure(2, weight=0)
        right_panel.grid_columnconfigure(0, weight=1)
        
        self.status_card = self.create_card("📊 Status", None, right_panel, 0)
        self.status_text = tk.Text(
            self.status_card,
            bg=self.colors['bg_light'],
            fg=self.colors['accent_primary'],
            font=("Consolas", 8),
            relief=tk.FLAT,
            padx=10,
            pady=10,
            wrap=tk.WORD
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        self.status_text.insert(tk.END, "✓ Spremno za rad...\n")
        self.status_text.config(state=tk.DISABLED)
        
        info_card = self.create_card("ℹ️ Informacije", None, right_panel, 1)
        info_text = tk.Label(
            info_card,
            text="• Sortira po EXIF metapodacima\n"
                 "• MD5 detekcija duplikata\n"
                 "• Formati: JPG, PNG, HEIC, RAW, GIF\n"
                 "• Dinamički formati preimenovanja\n"
                 "• Automatski backup i detaljan log\n"
                 "• Zaštita od gubitka podataka",
            bg=self.colors['bg_light'],
            fg=self.colors['text_gray'],
            font=("Segoe UI", 8),
            justify=tk.LEFT,
            padx=12,
            pady=10
        )
        info_text.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        
        self.stats_card = self.create_card("⚡ Statistike", None, right_panel, 2)
        self.stats_label = tk.Label(
            self.stats_card,
            text="Direktorij: -\nDatoteke: -\nVeličina: -\nSlobodno: -",
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 8),
            justify=tk.LEFT,
            padx=12,
            pady=10
        )
        self.stats_label.pack(fill=tk.BOTH, padx=12, pady=(0, 12))
    
    def create_card(self, title, content_func, parent, row, column=0, padx=0, pady=(0, 10)):
        card = tk.Frame(parent, bg=self.colors['bg_medium'], relief=tk.FLAT, bd=1)
        card.grid(row=row, column=column, sticky="nsew", padx=padx, pady=pady)
        
        title_frame = tk.Frame(card, bg=self.colors['bg_lighter'])
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            title_frame,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_lighter'],
            fg=self.colors['accent_primary'],
            pady=10,
            padx=12
        )
        title_label.pack(anchor=tk.W)
        
        if content_func:
            content_frame = tk.Frame(card, bg=self.colors['bg_medium'])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))
            content_func(content_frame)
        
        return card
    
    def create_directory_section(self, parent):
        source_label = tk.Label(
            parent,
            text="IZVORNI DIREKTORIJ",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        source_label.pack(anchor=tk.W, pady=(0, 5))
        
        source_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        source_frame.pack(fill=tk.X, pady=(0, 12))
        
        source_entry = tk.Entry(
            source_frame,
            textvariable=self.source_dir,
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            insertbackground=self.colors['accent_primary'],
            bd=1
        )
        source_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6)
        
        source_btn = tk.Button(
            source_frame,
            text="Odaberi",
            command=lambda: self.browse_directory(self.source_dir),
            bg=self.colors['accent_primary'],
            fg=self.colors['bg_dark'],
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        source_btn.pack(side=tk.RIGHT, padx=(6, 0))
        source_btn.bind("<Enter>", lambda e: source_btn.config(bg=self.colors['accent_hover']))
        source_btn.bind("<Leave>", lambda e: source_btn.config(bg=self.colors['accent_primary']))
        
        dest_label = tk.Label(
            parent,
            text="ODREDIŠNI DIREKTORIJ",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        dest_label.pack(anchor=tk.W, pady=(0, 5))
        
        dest_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        dest_frame.pack(fill=tk.X)
        
        dest_entry = tk.Entry(
            dest_frame,
            textvariable=self.dest_dir,
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            insertbackground=self.colors['accent_primary'],
            bd=1
        )
        dest_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6)
        
        dest_btn = tk.Button(
            dest_frame,
            text="Odaberi",
            command=lambda: self.browse_directory(self.dest_dir),
            bg=self.colors['accent_primary'],
            fg=self.colors['bg_dark'],
            font=("Segoe UI", 8, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=6
        )
        dest_btn.pack(side=tk.RIGHT, padx=(6, 0))
        dest_btn.bind("<Enter>", lambda e: dest_btn.config(bg=self.colors['accent_hover']))
        dest_btn.bind("<Leave>", lambda e: dest_btn.config(bg=self.colors['accent_primary']))
    
    def create_basic_options(self, parent):
        options = [
            ("📋 Kopiraj", "Zadrži originale", self.copy_mode),
            ("📂 Podmape", "Uključi sve", self.check_subdirs),
            ("🗑️ Obriši originale", "Ukloni izvorne", self.delete_originals),
            ("💾 Backup", "Sigurnosna kopija", self.create_backup)
        ]
        
        for i, (title, subtitle, var) in enumerate(options):
            row = i // 2
            col = i % 2
            
            option_frame = tk.Frame(parent, bg=self.colors['bg_light'], relief=tk.FLAT)
            option_frame.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            parent.grid_columnconfigure(col, weight=1)
            
            cb = tk.Checkbutton(
                option_frame,
                text="",
                variable=var,
                bg=self.colors['bg_light'],
                activebackground=self.colors['bg_light'],
                selectcolor=self.colors['accent_primary'],
                cursor="hand2",
                bd=0
            )
            cb.pack(side=tk.LEFT, padx=(8, 5), pady=8)
            
            text_frame = tk.Frame(option_frame, bg=self.colors['bg_light'])
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=8, padx=(0, 8))
            
            title_lbl = tk.Label(
                text_frame,
                text=title,
                font=("Segoe UI", 9, "bold"),
                bg=self.colors['bg_light'],
                fg=self.colors['text_white'],
                anchor=tk.W
            )
            title_lbl.pack(anchor=tk.W)
            
            subtitle_lbl = tk.Label(
                text_frame,
                text=subtitle,
                font=("Segoe UI", 7),
                bg=self.colors['bg_light'],
                fg=self.colors['text_light_gray'],
                anchor=tk.W
            )
            subtitle_lbl.pack(anchor=tk.W)
    
    def create_filters_section(self, parent):
        sort_label = tk.Label(
            parent,
            text="📅 SORTIRAJ PO",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        sort_label.pack(anchor=tk.W, pady=(0, 4))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Custom.TCombobox',
                       fieldbackground=self.colors['bg_light'],
                       background=self.colors['accent_primary'],
                       foreground=self.colors['bg_dark'],
                       arrowcolor=self.colors['accent_primary'])
        
        sort_combo = ttk.Combobox(
            parent,
            textvariable=self.sort_by,
            values=["godina", "mjesec", "datum", "kamera", "lokacija", "rezolucija", "veličina"],
            state="readonly",
            font=("Segoe UI", 9),
            style='Custom.TCombobox',
            height=6
        )
        sort_combo.pack(fill=tk.X, pady=(0, 10), ipady=4)
        
        format_label = tk.Label(
            parent,
            text="🖼️ FORMAT SLIKA",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        format_label.pack(anchor=tk.W, pady=(0, 4))
        
        format_combo = ttk.Combobox(
            parent,
            textvariable=self.image_format,
            values=["svi", "JPG/JPEG", "PNG", "RAW", "HEIC", "GIF", "TIFF", "WebP"],
            state="readonly",
            font=("Segoe UI", 9),
            style='Custom.TCombobox',
            height=6
        )
        format_combo.pack(fill=tk.X, pady=(0, 10), ipady=4)
        
        size_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        min_frame = tk.Frame(size_frame, bg=self.colors['bg_medium'])
        min_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        
        min_label = tk.Label(
            min_frame,
            text="MIN (MB)",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        min_label.pack(anchor=tk.W, pady=(0, 3))
        
        min_entry = tk.Entry(
            min_frame,
            textvariable=self.min_size,
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            insertbackground=self.colors['accent_primary'],
            bd=1
        )
        min_entry.pack(fill=tk.X, ipady=5)
        
        max_frame = tk.Frame(size_frame, bg=self.colors['bg_medium'])
        max_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(4, 0))
        
        max_label = tk.Label(
            max_frame,
            text="MAX (MB)",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        max_label.pack(anchor=tk.W, pady=(0, 3))
        
        max_entry = tk.Entry(
            max_frame,
            textvariable=self.max_size,
            font=("Segoe UI", 9),
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            insertbackground=self.colors['accent_primary'],
            bd=1
        )
        max_entry.pack(fill=tk.X, ipady=5)
    
    def create_rename_section(self, parent):
        template_label = tk.Label(
            parent,
            text="ODABERI ŠABLON ZA PREIMENOVANJE",
            font=("Segoe UI", 8, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        template_label.pack(anchor=tk.W, pady=(0, 5))
        
        template_combo = ttk.Combobox(
            parent,
            textvariable=self.rename_pattern,
            values=self.rename_templates,
            font=("Segoe UI", 8),
            style='Custom.TCombobox',
            height=8
        )
        template_combo.pack(fill=tk.X, pady=(0, 10), ipady=4)
        
        pattern_label = tk.Label(
            parent,
            text="PRIJEDLOZI ŠABLONA",
            font=("Segoe UI", 7, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_secondary']
        )
        pattern_label.pack(anchor=tk.W, pady=(0, 5))
        
        patterns_text = tk.Label(
            parent,
            text="{YYYY}=godina {MM}=mjesec {DD}=dan\n"
                 "{HH}=sata {mm}=minute {ss}=sekunde\n"
                 "{index}=redni br {randomid}=random ID\n"
                 "{kamera}=model {lokacija}=lokacija",
            bg=self.colors['bg_light'],
            fg=self.colors['text_light_gray'],
            font=("Segoe UI", 7),
            justify=tk.LEFT,
            padx=8,
            pady=6
        )
        patterns_text.pack(fill=tk.X)
    
    def create_advanced_options(self, parent):
        options = [
            ("✔️ Preimenuj", self.rename_files),
            ("📂 Zadrži strukturu", self.preserve_structure),
            ("🚫 Preskoči male", self.skip_small),
            ("📋 Generiraj log", self.create_log),
            ("🔄 Ukloni duplikate", self.remove_duplicates),
            ("📝 Originalna imena", self.keep_original_names)
        ]
        
        for i, (title, var) in enumerate(options):
            option_frame = tk.Frame(parent, bg=self.colors['bg_light'], relief=tk.FLAT)
            option_frame.pack(fill=tk.X, pady=2)
            
            cb = tk.Checkbutton(
                option_frame,
                text="",
                variable=var,
                bg=self.colors['bg_light'],
                activebackground=self.colors['bg_light'],
                selectcolor=self.colors['accent_primary'],
                cursor="hand2",
                bd=0
            )
            cb.pack(side=tk.LEFT, padx=(8, 6), pady=7)
            
            title_lbl = tk.Label(
                option_frame,
                text=title,
                font=("Segoe UI", 8, "bold"),
                bg=self.colors['bg_light'],
                fg=self.colors['text_white'],
                anchor=tk.W
            )
            title_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=7, padx=(0, 8))
    
    def create_extra_features(self, parent):
        options = [
            ("🎨 Kompresija", self.compress_images),
            ("🖌️ Vodotisak", self.watermark),
        ]
        
        for i, (title, var) in enumerate(options):
            option_frame = tk.Frame(parent, bg=self.colors['bg_light'], relief=tk.FLAT)
            option_frame.pack(fill=tk.X, pady=2)
            
            cb = tk.Checkbutton(
                option_frame,
                text="",
                variable=var,
                bg=self.colors['bg_light'],
                activebackground=self.colors['bg_light'],
                selectcolor=self.colors['accent_primary'],
                cursor="hand2",
                bd=0
            )
            cb.pack(side=tk.LEFT, padx=(8, 6), pady=7)
            
            title_lbl = tk.Label(
                option_frame,
                text=title,
                font=("Segoe UI", 8, "bold"),
                bg=self.colors['bg_light'],
                fg=self.colors['text_white'],
                anchor=tk.W
            )
            title_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=7, padx=(0, 8))
        
        info_label = tk.Label(
            parent,
            text="💡 Napomene:\n• Kompresija smanjuje veličinu\n• Vodotisak štiti vlasništvo",
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light_gray'],
            font=("Segoe UI", 7),
            justify=tk.LEFT,
            padx=8,
            pady=6
        )
        info_label.pack(fill=tk.X, pady=(10, 0))
    
    def create_action_button(self, parent):
        btn_frame = tk.Frame(parent, bg=self.colors['bg_dark'])
        btn_frame.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        
        self.action_btn = tk.Button(
            btn_frame,
            text="⚡ POKRENI ORGANIZACIJU SLIKA",
            command=self.start_processing,
            bg=self.colors['accent_primary'],
            fg=self.colors['bg_dark'],
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=12,
            activebackground=self.colors['accent_hover'],
            activeforeground=self.colors['bg_dark'],
            bd=0
        )
        self.action_btn.pack(fill=tk.X)
    
    def browse_directory(self, var):
        directory = filedialog.askdirectory(title="Odaberite direktorij")
        if directory:
            var.set(directory)
            self.update_stats()
    
    def update_stats(self):
        if self.source_dir.get():
            try:
                total_files = sum([len(files) for _, _, files in os.walk(self.source_dir.get())])
                total_size = sum([os.path.getsize(os.path.join(root, file)) 
                                for root, _, files in os.walk(self.source_dir.get()) 
                                for file in files]) / (1024**3)
                
                free_space = shutil.disk_usage(self.source_dir.get()).free / (1024**3)
                
                self.stats_label.config(
                    text=f"Direktorij: {os.path.basename(self.source_dir.get())}\n"
                         f"Datoteke: {total_files}\n"
                         f"Veličina: {total_size:.2f} GB\n"
                         f"Slobodno: {free_space:.2f} GB"
                )
            except:
                pass
    
    def update_status(self, message, append=True, color=None):
        self.status_text.config(state=tk.NORMAL)
        if not append:
            self.status_text.delete(1.0, tk.END)
        
        if color:
            self.status_text.tag_config(color, foreground=color)
            self.status_text.insert(tk.END, f"{message}\n", color)
        else:
            self.status_text.insert(tk.END, f"{message}\n")
        
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update()
    
    def format_filename(self, pattern, exif_data, index, file_name):
        """Formatira naziv datoteke prema šablonu"""
        try:
            if exif_data and 36867 in exif_data:
                date_str = exif_data[36867]
                year = date_str[:4]
                month = date_str[5:7]
                day = date_str[8:10]
                time_str = date_str[11:19]
                hour = time_str[:2]
                minute = time_str[3:5]
                second = time_str[6:8]
            else:
                now = datetime.now()
                year = now.strftime("%Y")
                month = now.strftime("%m")
                day = now.strftime("%d")
                hour = now.strftime("%H")
                minute = now.strftime("%M")
                second = now.strftime("%S")
            
            result = pattern.replace("{YYYY}", year)
            result = result.replace("{MM}", month)
            result = result.replace("{DD}", day)
            result = result.replace("{HH}", hour)
            result = result.replace("{mm}", minute)
            result = result.replace("{ss}", second)
            
            # Dodaj ostale zamjene
            result = result.replace("{index}", str(index).zfill(4))
            result = result.replace("{randomid}", str(hashlib.md5(file_name.encode()).hexdigest()[:8]))
            result = result.replace("{kamera}", exif_data.get(271, "Nepoznato") if exif_data else "Nepoznato")
            
            # Za lokaciju, možda ćeš trebati izvući iz GPS EXIF podataka
            result = result.replace("{lokacija}", "Nepoznato")
            
            # Obradi naziv dana ako je potrebno
            if "{dan}" in result:
                dani = ["Ponedjeljak", "Utorak", "Srijeda", "Četvrtak", "Petak", "Subota", "Nedjelja"]
                try:
                    datum_obj = datetime(int(year), int(month), int(day))
                    ime_dana = dani[datum_obj.weekday()]
                except:
                    ime_dana = "Nepoznato"
                result = result.replace("{dan}", ime_dana)
            
            if "{sequenceid}" in result:
                result = result.replace("{sequenceid}", str(index).zfill(6))
            
            return result
        except Exception as e:
            self.update_status(f"Greška u formatiranju naziva: {e}", color=self.colors['error'])
            return file_name  # Vrati originalno ime datoteke u slučaju greške
    
    def start_processing(self):
        if not self.source_dir.get() or not self.dest_dir.get():
            messagebox.showerror("Greška", "Odaberite izvorni i odredišni direktorij!")
            return
        
        if self.processing:
            return
        
        self.processing = True
        self.action_btn.config(state=tk.DISABLED, text="⏳ OBRADA U TOKU...")
        
        # Pokreni obradu u zasebnoj niti
        thread = threading.Thread(target=self.process_images)
        thread.daemon = True
        thread.start()
    
    def process_images(self):
        """Glavna metoda za obradu slika"""
        try:
            self.update_status("🚀 Počinje obrada slika...", append=False)
            self.update_status(f"Izvor: {self.source_dir.get()}")
            self.update_status(f"Odredište: {self.dest_dir.get()}")
            
            # Stvori odredišni direktorij ako ne postoji
            if not os.path.exists(self.dest_dir.get()):
                os.makedirs(self.dest_dir.get())
                self.update_status(f"✓ Stvoren odredišni direktorij: {self.dest_dir.get()}")
            
            # Prikupi sve slike
            image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.heic', '.raw', '.webp'}
            
            images = []
            self.update_status("🔍 Skeniram direktorij za slike...")
            
            if self.check_subdirs.get():
                # Skeniraj sve podmape
                for root, dirs, files in os.walk(self.source_dir.get()):
                    for file in files:
                        if os.path.splitext(file.lower())[1] in image_extensions:
                            images.append(os.path.join(root, file))
            else:
                # Skeniraj samo glavni direktorij
                for file in os.listdir(self.source_dir.get()):
                    if os.path.splitext(file.lower())[1] in image_extensions:
                        images.append(os.path.join(self.source_dir.get(), file))
            
            self.update_status(f"✓ Pronađeno {len(images)} slika")
            
            if len(images) == 0:
                self.update_status("❌ Nema slika za obradu", color=self.colors['warning'])
                return
            
            # Filtriraj po formatu
            if self.image_format.get() != "svi":
                format_filter = self.image_format.get().lower().split('/')[0]
                images = [img for img in images if img.lower().endswith(f'.{format_filter}')]
                self.update_status(f"✓ Filtrirano na {len(images)} {format_filter} slika")
            
            # Filtriraj po veličini
            min_size_mb = float(self.min_size.get()) if self.min_size.get() else 0
            max_size_mb = float(self.max_size.get()) if self.max_size.get() else 0
            
            if min_size_mb > 0 or max_size_mb > 0:
                filtered_images = []
                for img in images:
                    size_mb = os.path.getsize(img) / (1024 * 1024)
                    if (min_size_mb == 0 or size_mb >= min_size_mb) and (max_size_mb == 0 or size_mb <= max_size_mb):
                        filtered_images.append(img)
                
                removed = len(images) - len(filtered_images)
                images = filtered_images
                if removed > 0:
                    self.update_status(f"✓ Uklonjeno {removed} slika prema filteru veličine")
            
            self.update_status(f"🎯 Konačno {len(images)} slika za obradu")
            
            # Inicijaliziraj varijable za statistiku
            processed_count = 0
            duplicate_count = 0
            error_count = 0
            file_hashes = set()
            duplicate_folder = os.path.join(self.dest_dir.get(), "DUPLIKATI")
            
            # Stvori folder za duplikate ako je potrebno
            if self.remove_duplicates.get():
                if not os.path.exists(duplicate_folder):
                    os.makedirs(duplicate_folder)
                    self.update_status(f"✓ Stvoren folder za duplikate: {duplicate_folder}")
            
            # Procesiraj svaku sliku
            for i, image_path in enumerate(images, 1):
                try:
                    file_name = os.path.basename(image_path)
                    file_ext = os.path.splitext(file_name)[1].lower()
                    
                    # Izračunaj MD5 hash za detekciju duplikata
                    with open(image_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    # Provjeri duplikate
                    if self.remove_duplicates.get() and file_hash in file_hashes:
                        if self.copy_mode.get():
                            duplicate_dest = os.path.join(duplicate_folder, file_name)
                            shutil.copy2(image_path, duplicate_dest)
                        duplicate_count += 1
                        self.update_status(f"⚠️  Duplikat: {file_name}")
                        continue
                    
                    file_hashes.add(file_hash)
                    
                    # Pročitaj EXIF podatke
                    try:
                        with Image.open(image_path) as img:
                            exif_data = img._getexif() if hasattr(img, '_getexif') else None
                    except:
                        exif_data = None
                    
                    # Odredi novi naziv datoteke
                    if self.rename_files.get():
                        new_name = self.format_filename(self.rename_pattern.get(), exif_data, i, file_name)
                        # Dodaj ekstenziju ako nema
                        if not new_name.lower().endswith(file_ext):
                            new_name += file_ext
                    else:
                        new_name = file_name
                    
                    # Odredi odredišnu putanju
                    dest_path = os.path.join(self.dest_dir.get(), new_name)
                    
                    # Kopiraj ili premjesti datoteku
                    if self.copy_mode.get():
                        shutil.copy2(image_path, dest_path)
                        action = "Kopirano"
                    else:
                        shutil.move(image_path, dest_path)
                        action = "Premješteno"
                    
                    processed_count += 1
                    self.update_status(f"✓ {action}: {file_name} → {new_name}")
                    
                    # Ažuriraj progres
                    if i % 10 == 0 or i == len(images):
                        self.update_status(f"📊 Progres: {i}/{len(images)} ({i/len(images)*100:.1f}%)")
                
                except Exception as e:
                    error_count += 1
                    self.update_status(f"❌ Greška prilikom obrade {file_name}: {str(e)}", color=self.colors['error'])
            
            # Generiraj izvještaj
            self.update_status("=" * 50)
            self.update_status("📋 REZIME OBRADE:")
            self.update_status(f"✓ Ukupno obrađeno: {processed_count}")
            self.update_status(f"✓ Duplikata pronađeno: {duplicate_count}")
            self.update_status(f"✓ Grešaka: {error_count}")
            
            # Ako se brišu originali nakon kopiranja
            if not self.copy_mode.get() and self.delete_originals.get():
                self.update_status("🗑️  Brišem izvorne datoteke...")
                for img in images:
                    try:
                        os.remove(img)
                    except:
                        pass
            
            # Stvori log datoteku ako je označeno
            if self.create_log.get():
                log_path = os.path.join(self.dest_dir.get(), "obrada_log.txt")
                with open(log_path, 'w', encoding='utf-8') as log_file:
                    log_file.write(f"LOG ORGANIZACIJE SLIKA\n")
                    log_file.write(f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    log_file.write(f"Izvor: {self.source_dir.get()}\n")
                    log_file.write(f"Odredište: {self.dest_dir.get()}\n")
                    log_file.write(f"Ukupno slika: {len(images)}\n")
                    log_file.write(f"Uspješno obrađeno: {processed_count}\n")
                    log_file.write(f"Duplikata: {duplicate_count}\n")
                    log_file.write(f"Grešaka: {error_count}\n")
                
                self.update_status(f"✓ Log datoteka kreirana: {log_path}")
            
            self.update_status("✅ OBRADA ZAVRŠENA!", color=self.colors['success'])
            
        except Exception as e:
            self.update_status(f"❌ Kritisna greška: {str(e)}", color=self.colors['error'])
        
        finally:
            self.processing = False
            self.root.after(0, lambda: self.action_btn.config(state=tk.NORMAL, text="⚡ POKRENI ORGANIZACIJU SLIKA"))
    
    def run(self):
        self.root.mainloop()


# Pokreni aplikaciju
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSorterGUI(root)
    app.run()