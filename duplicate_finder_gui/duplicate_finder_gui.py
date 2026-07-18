import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import tkinter as tk
from PIL import Image, ImageTk
import os
import threading
import queue
import time
from pathlib import Path
import shutil

# Uvoz klase iz originalnog fajla
from duplicate_finder import NapredniTrazilicaDuplikata

ctk.set_appearance_mode("dark")  # Modes: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue", "green", "dark-blue"

class ModernDuplikatGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🎯 Moderni Finder Duplikata - Slike i Video")
        self.root.geometry("1400x900")
        
        # Varijable
        self.izabrana_putanja = ""
        self.slicne_slike = []
        self.slicni_videi = []
        self.trazilica = None
        self.izabrane_datoteke = {}  # {grupa_index: {putanja: True/False}}
        self.progress_queue = queue.Queue()
        self.previews_cache = {}
        
        # Setup GUI
        self.setup_styles()
        self.create_widgets()
        self.setup_bindings()
        
        # Start progress checker
        self.check_progress_queue()
    
    def setup_styles(self):
        """Postavlja stilove za aplikaciju"""
        self.font_title = ("Segoe UI", 20, "bold")
        self.font_subtitle = ("Segoe UI", 14, "bold")
        self.font_normal = ("Segoe UI", 11)
        self.font_small = ("Segoe UI", 10)
        
        # Boje
        self.color_primary = "#2563eb"
        self.color_success = "#10b981"
        self.color_warning = "#f59e0b"
        self.color_danger = "#ef4444"
        self.color_gray = "#6b7280"
        self.color_dark = "#1f2937"
        self.color_light = "#f9fafb"
    
    def create_widgets(self):
        """Kreira sve widget-e aplikacije"""
        # Glavni kontejner
        self.main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        self.create_header()
        
        # Tabovi
        self.create_tabs()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Kreira header dio aplikacije"""
        header_frame = ctk.CTkFrame(self.main_frame, height=80, corner_radius=10)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        # Logo i naslov
        logo_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_frame.pack(side="left", fill="y", padx=20)
        
        ctk.CTkLabel(
            logo_frame, 
            text="🎯", 
            font=("Segoe UI", 32)
        ).pack(side="left", padx=(0, 15))
        
        title_frame = ctk.CTkFrame(logo_frame, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        ctk.CTkLabel(
            title_frame, 
            text="Moderni Finder Duplikata", 
            font=self.font_title
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame, 
            text="Pronalazi vizualno slične slike i videozapise", 
            font=self.font_small,
            text_color=self.color_gray
        ).pack(anchor="w")
        
        # Dugmad u headeru
        button_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        button_frame.pack(side="right", fill="y", padx=20)
        
        self.btn_settings = ctk.CTkButton(
            button_frame,
            text="⚙️ Postavke",
            width=100,
            command=self.open_settings,
            font=self.font_normal
        )
        self.btn_settings.pack(side="left", padx=5)
        
        self.btn_help = ctk.CTkButton(
            button_frame,
            text="❔ Pomoć",
            width=100,
            command=self.show_help,
            font=self.font_normal
        )
        self.btn_help.pack(side="left", padx=5)
    
    def create_tabs(self):
        """Kreira tabove aplikacije"""
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Kreiraj tabove
        self.tab_pretraga = self.tabview.add("🔍 Pretraga")
        self.tab_rezultati = self.tabview.add("📊 Rezultati")
        self.tab_upravljanje = self.tabview.add("🛠️ Upravljanje")
        self.tab_pregled = self.tabview.add("👁️ Pregled")
        
        # Popuni tabove
        self.setup_pretraga_tab()
        self.setup_rezultati_tab()
        self.setup_upravljanje_tab()
        self.setup_pregled_tab()
        
        # Onemogući rezultate tab dok se ne završi pretraga
        self.tabview.set("🔍 Pretraga")
    
    def setup_pretraga_tab(self):
        """Postavlja Pretraga tab"""
        # Glavni frame
        main_content = ctk.CTkFrame(self.tab_pretraga, fg_color="transparent")
        main_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Lijevi panel - postavke
        left_panel = ctk.CTkFrame(main_content, width=400, corner_radius=10)
        left_panel.pack(side="left", fill="y", padx=(0, 20))
        left_panel.pack_propagate(False)
        
        # Desni panel - informacije
        right_panel = ctk.CTkFrame(main_content, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Postavke pretrage
        settings_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Odabir mape
        ctk.CTkLabel(
            settings_frame,
            text="📁 Odabir mape za pretragu:",
            font=self.font_subtitle
        ).pack(anchor="w", pady=(0, 10))
        
        path_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 20))
        
        self.path_entry = ctk.CTkEntry(
            path_frame,
            placeholder_text="Kliknite 'Odaberi mapu' ili povucite datoteke ovdje...",
            font=self.font_normal
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.btn_browse = ctk.CTkButton(
            path_frame,
            text="Odaberi mapu",
            width=120,
            command=self.browse_folder,
            font=self.font_normal
        )
        self.btn_browse.pack(side="right")
        
        # Tipovi datoteka
        ctk.CTkLabel(
            settings_frame,
            text="📄 Tipovi datoteka:",
            font=self.font_subtitle
        ).pack(anchor="w", pady=(0, 10))
        
        filetype_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        filetype_frame.pack(fill="x", pady=(0, 20))
        
        self.var_slike = ctk.BooleanVar(value=True)
        self.var_videi = ctk.BooleanVar(value=True)
        
        ctk.CTkCheckBox(
            filetype_frame,
            text="🖼️ Slike (JPG, PNG, GIF, BMP...)",
            variable=self.var_slike,
            font=self.font_normal
        ).pack(anchor="w", pady=5)
        
        ctk.CTkCheckBox(
            filetype_frame,
            text="🎬 Videozapisi (MP4, AVI, MKV, MOV...)",
            variable=self.var_videi,
            font=self.font_normal
        ).pack(anchor="w", pady=5)
        
        # Pragovi sličnosti
        ctk.CTkLabel(
            settings_frame,
            text="🎯 Pragovi sličnosti:",
            font=self.font_subtitle
        ).pack(anchor="w", pady=(0, 10))
        
        # Slider za slike
        slider_frame1 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        slider_frame1.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            slider_frame1,
            text="Slike:",
            font=self.font_normal
        ).pack(side="left")
        
        self.slider_slike_value = ctk.CTkLabel(
            slider_frame1,
            text="85%",
            font=self.font_normal,
            width=50
        )
        self.slider_slike_value.pack(side="right")
        
        self.slider_slike = ctk.CTkSlider(
            slider_frame1,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_slider_slike
        )
        self.slider_slike.pack(fill="x", expand=True, padx=10)
        self.slider_slike.set(85)
        
        # Slider za video
        slider_frame2 = ctk.CTkFrame(settings_frame, fg_color="transparent")
        slider_frame2.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            slider_frame2,
            text="Video:",
            font=self.font_normal
        ).pack(side="left")
        
        self.slider_video_value = ctk.CTkLabel(
            slider_frame2,
            text="85%",
            font=self.font_normal,
            width=50
        )
        self.slider_video_value.pack(side="right")
        
        self.slider_video = ctk.CTkSlider(
            slider_frame2,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_slider_video
        )
        self.slider_video.pack(fill="x", expand=True, padx=10)
        self.slider_video.set(85)
        
        # Napredne opcije
        self.var_subfolders = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            settings_frame,
            text="🔍 Pretraži podmape",
            variable=self.var_subfolders,
            font=self.font_normal
        ).pack(anchor="w", pady=(0, 20))
        
        # Dugme za pokretanje
        self.btn_start = ctk.CTkButton(
            settings_frame,
            text="🚀 Pokreni pretragu",
            height=50,
            font=("Segoe UI", 14, "bold"),
            command=self.start_search,
            state="normal"
        )
        self.btn_start.pack(fill="x", pady=(10, 0))
        
        # Desni panel - informacije
        info_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Informacije o pretrazi",
            font=self.font_subtitle
        ).pack(anchor="w", pady=(0, 20))
        
        info_text = """
📋 **Kako radi pretraga:**
1. **Perceptual hashing** - pronalazi vizualno slične slike
2. **Frame analiza** - analizira ključne kadrove videozapisa
3. **Multi-algoritamski** - koristi 3 različita algoritma za slike
4. **Pametno poređenje** - ne osjetljivo na male promjene

🎯 **Što se može pronaći:**
• Slike različitih veličina
• Slike različitih formata (JPG ↔ PNG)
• Slike s različitom kvalitetom
• Blago izmijenjene slike
• Slični videozapisi

⏱️ **Procijenjeno vrijeme:**
• 100 slika: ~30 sekundi
• 500 slika: ~2-3 minute
• 50 videozapisa: ~1-2 minute

💡 **Savjet:** Start pretragu navečer ako imate puno datoteka!
        """
        
        self.info_textbox = ctk.CTkTextbox(
            info_frame,
            font=self.font_normal,
            wrap="word",
            height=400
        )
        self.info_textbox.pack(fill="both", expand=True)
        self.info_textbox.insert("1.0", info_text)
        self.info_textbox.configure(state="disabled")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(right_panel)
        self.progress_bar.pack(fill="x", padx=30, pady=(0, 20))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            right_panel,
            text="Spremno za pretragu...",
            font=self.font_small,
            text_color=self.color_gray
        )
        self.progress_label.pack()
    
    def setup_rezultati_tab(self):
        """Postavlja Rezultati tab"""
        main_frame = ctk.CTkFrame(self.tab_rezultati, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header rezultata
        header_frame = ctk.CTkFrame(main_frame, height=60, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        self.result_title = ctk.CTkLabel(
            header_frame,
            text="📊 Rezultati pretrage",
            font=self.font_subtitle
        )
        self.result_title.pack(side="left", padx=20)
        
        self.result_stats = ctk.CTkLabel(
            header_frame,
            text="Nema rezultata",
            font=self.font_small,
            text_color=self.color_gray
        )
        self.result_stats.pack(side="right", padx=20)
        
        # Tabovi za slike i video
        self.result_tabview = ctk.CTkTabview(main_frame, corner_radius=10)
        self.result_tabview.pack(fill="both", expand=True)
        
        self.tab_slike = self.result_tabview.add("🖼️ Slike")
        self.tab_videi = self.result_tabview.add("🎬 Video")
        
        # Setup za slike tab
        self.setup_slike_results()
        self.setup_video_results()
    
    def setup_slike_results(self):
        """Postavlja prikaz rezultata za slike"""
        # Glavni frame
        main_frame = ctk.CTkFrame(self.tab_slike, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollable frame
        self.canvas_slike = tk.Canvas(main_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(main_frame, command=self.canvas_slike.yview)
        scrollable_frame = ctk.CTkFrame(self.canvas_slike, fg_color="transparent")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_slike.configure(scrollregion=self.canvas_slike.bbox("all"))
        )
        
        self.canvas_slike.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas_slike.configure(yscrollcommand=scrollbar.set)
        
        self.canvas_slike.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame za thumbnails
        self.slike_container = scrollable_frame
    
    def setup_video_results(self):
        """Postavlja prikaz rezultata za video"""
        # Glavni frame
        main_frame = ctk.CTkFrame(self.tab_videi, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollable frame
        self.canvas_video = tk.Canvas(main_frame, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(main_frame, command=self.canvas_video.yview)
        scrollable_frame = ctk.CTkFrame(self.canvas_video, fg_color="transparent")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_video.configure(scrollregion=self.canvas_video.bbox("all"))
        )
        
        self.canvas_video.create_window((0, 0), window=scrollable_frame, anchor="nw")
        self.canvas_video.configure(yscrollcommand=scrollbar.set)
        
        self.canvas_video.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Frame za thumbnails
        self.video_container = scrollable_frame
    
    def setup_upravljanje_tab(self):
        """Postavlja Upravljanje tab"""
        main_frame = ctk.CTkFrame(self.tab_upravljanje, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Lijevi panel - izbor datoteka
        left_panel = ctk.CTkFrame(main_frame, width=500, corner_radius=10)
        left_panel.pack(side="left", fill="both", padx=(0, 20))
        
        # Desni panel - akcije
        right_panel = ctk.CTkFrame(main_frame, corner_radius=10)
        right_panel.pack(side="right", fill="both", expand=True)
        
        # Lista grupa
        ctk.CTkLabel(
            left_panel,
            text="📋 Grupe duplikata",
            font=self.font_subtitle
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # TreeView za grupe
        columns = ("grupa", "tip", "broj", "sličnost")
        self.tree_grupe = ttk.Treeview(
            left_panel,
            columns=columns,
            show="headings",
            height=15
        )
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b",
                       rowheight=35)
        style.configure("Treeview.Heading",
                       background="#3b3b3b",
                       foreground="white",
                       relief="flat")
        
        self.tree_grupe.heading("grupa", text="Grupa")
        self.tree_grupe.heading("tip", text="Tip")
        self.tree_grupe.heading("broj", text="Broj")
        self.tree_grupe.heading("sličnost", text="Sličnost")
        
        self.tree_grupe.column("grupa", width=100)
        self.tree_grupe.column("tip", width=80)
        self.tree_grupe.column("broj", width=80)
        self.tree_grupe.column("sličnost", width=100)
        
        self.tree_grupe.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Bind selection
        self.tree_grupe.bind("<<TreeviewSelect>>", self.on_grupa_select)
        
        # Panel za akcije
        ctk.CTkLabel(
            right_panel,
            text="⚡ Akcije",
            font=self.font_subtitle
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        action_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_keep_selected = ctk.CTkButton(
            action_frame,
            text="💾 Zadrži označeno",
            height=45,
            font=self.font_normal,
            command=self.keep_selected,
            state="disabled"
        )
        self.btn_keep_selected.pack(fill="x", pady=5)
        
        self.btn_delete_all = ctk.CTkButton(
            action_frame,
            text="🗑️ Obriši sve duplikate",
            height=45,
            font=self.font_normal,
            fg_color=self.color_danger,
            hover_color="#dc2626",
            command=self.delete_all_duplicates,
            state="disabled"
        )
        self.btn_delete_all.pack(fill="x", pady=5)
        
        self.btn_copy_compare = ctk.CTkButton(
            action_frame,
            text="📁 Kopiraj za usporedbu",
            height=45,
            font=self.font_normal,
            command=self.copy_for_comparison,
            state="disabled"
        )
        self.btn_copy_compare.pack(fill="x", pady=5)
        
        self.btn_select_all = ctk.CTkButton(
            action_frame,
            text="✅ Označi sve",
            height=35,
            font=self.font_small,
            command=self.select_all_files
        )
        self.btn_select_all.pack(fill="x", pady=5)
        
        self.btn_deselect_all = ctk.CTkButton(
            action_frame,
            text="❌ Odznači sve",
            height=35,
            font=self.font_small,
            command=self.deselect_all_files
        )
        self.btn_deselect_all.pack(fill="x", pady=5)
        
        # Info panel
        info_frame = ctk.CTkFrame(right_panel, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(
            info_frame,
            text="ℹ️ Informacije o odabranoj grupi",
            font=self.font_normal
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.grupa_info_text = ctk.CTkTextbox(
            info_frame,
            height=150,
            font=self.font_small,
            wrap="word"
        )
        self.grupa_info_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.grupa_info_text.insert("1.0", "Odaberite grupu za detalje...")
        self.grupa_info_text.configure(state="disabled")
        
        # Lista datoteka u grupi (scrollable)
        ctk.CTkLabel(
            left_panel,
            text="📄 Datoteke u grupi",
            font=self.font_subtitle
        ).pack(anchor="w", padx=20, pady=(10, 10))
        
        # Scrollable frame za liste datoteka
        self.file_list_frame = tk.Canvas(left_panel, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(left_panel, command=self.file_list_frame.yview)
        self.file_list_container = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        
        self.file_list_container.bind(
            "<Configure>",
            lambda e: self.file_list_frame.configure(scrollregion=self.file_list_frame.bbox("all"))
        )
        
        self.file_list_frame.create_window((0, 0), window=self.file_list_container, anchor="nw")
        self.file_list_frame.configure(yscrollcommand=scrollbar.set)
        
        self.file_list_frame.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=(0, 20))
        scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=(0, 20))
    
    def setup_pregled_tab(self):
        """Postavlja Pregled tab za vizualnu usporedbu"""
        main_frame = ctk.CTkFrame(self.tab_pregled, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, height=60, corner_radius=10)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        
        ctk.CTkLabel(
            header_frame,
            text="👁️ Vizualni pregled duplikata",
            font=self.font_subtitle
        ).pack(side="left", padx=20)
        
        # Kontrole za pregled
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.pack(side="right", padx=20)
        
        ctk.CTkLabel(
            controls_frame,
            text="Grupa:",
            font=self.font_normal
        ).pack(side="left", padx=(0, 10))
        
        self.combo_grupe = ctk.CTkComboBox(
            controls_frame,
            values=[],
            width=150,
            state="disabled",
            command=self.load_preview_group
        )
        self.combo_grupe.pack(side="left")
        
        # Glavni prikaz
        self.preview_container = ctk.CTkFrame(main_frame, corner_radius=10)
        self.preview_container.pack(fill="both", expand=True)
        
        # Default poruka
        self.preview_label = ctk.CTkLabel(
            self.preview_container,
            text="Odaberite grupu za vizualni pregled...",
            font=("Segoe UI", 16),
            text_color=self.color_gray
        )
        self.preview_label.pack(expand=True)
    
    def create_status_bar(self):
        """Kreira status bar na dnu"""
        status_frame = ctk.CTkFrame(self.main_frame, height=40, corner_radius=10)
        status_frame.pack(fill="x", padx=10, pady=(5, 10))
        status_frame.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="👋 Dobrodošli! Odaberite mapu za pretragu.",
            font=self.font_small
        )
        self.status_label.pack(side="left", padx=20)
        
        # Memory usage indicator
        self.memory_label = ctk.CTkLabel(
            status_frame,
            text="Memorija: --",
            font=self.font_small,
            text_color=self.color_gray
        )
        self.memory_label.pack(side="right", padx=20)
    
    def setup_bindings(self):
        """Postavlja event bindings"""
        # Drag and drop za path entry
        self.path_entry.bind("<Button-1>", lambda e: self.browse_folder())
        
        # Bind za zatvaranje prozora
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def update_slider_slike(self, value):
        """Update-uje vrijednost slidera za slike"""
        self.slider_slike_value.configure(text=f"{float(value):.0f}%")
    
    def update_slider_video(self, value):
        """Update-uje vrijednost slidera za video"""
        self.slider_video_value.configure(text=f"{float(value):.0f}%")
    
    def browse_folder(self):
        """Otvara dijalog za odabir mape"""
        folder = filedialog.askdirectory(title="Odaberite mapu za pretragu")
        if folder:
            self.izabrana_putanja = folder
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)
            self.update_status(f"Odabrana mapa: {folder}")
    
    def update_status(self, message):
        """Update-uje status bar"""
        self.status_label.configure(text=message)
    
    def open_settings(self):
        """Otvara prozor s postavkama"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("⚙️ Postavke")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center window
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - settings_window.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - settings_window.winfo_height()) // 2
        settings_window.geometry(f"+{x}+{y}")
        
        # Sadržaj postavki
        content = ctk.CTkFrame(settings_window, corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            content,
            text="Postavke aplikacije",
            font=self.font_subtitle
        ).pack(anchor="w", pady=(0, 20))
        
        # Tema
        ctk.CTkLabel(
            content,
            text="Tema:",
            font=self.font_normal
        ).pack(anchor="w", pady=(0, 5))
        
        theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_combo = ctk.CTkComboBox(
            content,
            values=["System", "Dark", "Light"],
            variable=theme_var,
            command=lambda v: ctk.set_appearance_mode(v)
        )
        theme_combo.pack(fill="x", pady=(0, 20))
        
        # Ostale postavke
        ctk.CTkLabel(
            content,
            text="Ostale postavke:",
            font=self.font_normal
        ).pack(anchor="w", pady=(0, 5))
        
        # Checkboxovi
        self.var_auto_open = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            content,
            text="Automatski otvori folder nakon kopiranja",
            variable=self.var_auto_open,
            font=self.font_normal
        ).pack(anchor="w", pady=5)
        
        self.var_confirm_delete = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            content,
            text="Potvrda prije brisanja",
            variable=self.var_confirm_delete,
            font=self.font_normal
        ).pack(anchor="w", pady=5)
        
        self.var_keep_largest = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            content,
            text="Preporuči najveću datoteku za zadržavanje",
            variable=self.var_keep_largest,
            font=self.font_normal
        ).pack(anchor="w", pady=5)
        
        # Dugmad
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(
            button_frame,
            text="💾 Spremi",
            command=settings_window.destroy
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Odustani",
            command=settings_window.destroy
        ).pack(side="right", padx=5)
    
    def show_help(self):
        """Prikazuje help dijalog"""
        messagebox.showinfo(
            "Pomoć - Moderni Finder Duplikata",
            """🎯 **Kako koristiti aplikaciju:**

1. **Odaberite mapu** koju želite pretražiti
2. **Postavite pragove sličnosti** (preporučeno 85-95%)
3. **Odaberite tipove datoteka** (slike, video, ili oboje)
4. **Kliknite 'Pokreni pretragu'** i sačekajte rezultate
5. **Pregledajte rezultate** u tabovima
6. **Upravljajte duplikatima** - zadržite željene, obrišite ostale

💡 **Savjeti:**
• Veći prag = strožija pretraga
• Za video treba više vremena
• Uvijek backup-ujte prije brisanja

🛠️ **Podrška:** Ako imate problema, provjerite da li imate instalirane:
• OpenCV: pip install opencv-python
• Pillow: pip install pillow
• imagehash: pip install imagehash
            """
        )
    
    def start_search(self):
        """Pokreće pretragu u zasebnoj niti"""
        if not self.izabrana_putanja or not os.path.exists(self.izabrana_putanja):
            messagebox.showerror("Greška", "Molim odaberite validnu mapu!")
            return
        
        # Onemogući dugme tokom pretrage
        self.btn_start.configure(state="disabled", text="🔍 Pretraga u toku...")
        
        # Resetuj rezultate
        self.slicne_slike = []
        self.slicni_videi = []
        
        # Kreiraj instancu tražilice s postavkama
        self.trazilica = NapredniTrazilicaDuplikata(self.izabrana_putanja)
        self.trazilica.prag_slicnosti_slike = self.slider_slike.get()
        self.trazilica.prag_slicnosti_videa = self.slider_video.get()
        
        # Pokreni pretragu u zasebnoj niti
        search_thread = threading.Thread(target=self.run_search, daemon=True)
        search_thread.start()
    
    def run_search(self):
        """Pokreće pretragu - poziva se u threadu"""
        try:
            # Pronađi slične slike
            if self.var_slike.get():
                self.progress_queue.put(("progress", 10, "Tražim slične slike..."))
                self.slicne_slike = self.trazilica.pronadi_slicne_slike()
            
            # Pronađi slične videe
            if self.var_videi.get():
                self.progress_queue.put(("progress", 60, "Tražim slične videozapise..."))
                self.slicni_videi = self.trazilica.pronadi_slicne_videe()
            
            # Završeno
            self.progress_queue.put(("complete", 100, "Pretraga završena!"))
            
        except Exception as e:
            self.progress_queue.put(("error", 0, f"Greška pri pretrazi: {str(e)}"))
    
    def check_progress_queue(self):
        """Provjerava progress queue i update-uje GUI"""
        try:
            while True:
                msg_type, value, message = self.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    self.progress_bar.set(value / 100)
                    self.progress_label.configure(text=message)
                    
                elif msg_type == "complete":
                    self.progress_bar.set(1.0)
                    self.progress_label.configure(text=message)
                    self.btn_start.configure(state="normal", text="🚀 Pokreni pretragu")
                    
                    # Prikaži rezultate
                    self.display_results()
                    self.tabview.set("📊 Rezultati")
                    
                elif msg_type == "error":
                    self.progress_bar.set(0)
                    self.progress_label.configure(text=message)
                    self.btn_start.configure(state="normal", text="🚀 Pokreni pretragu")
                    messagebox.showerror("Greška", message)
                    
        except queue.Empty:
            pass
        
        # Ponovi za 100ms
        self.root.after(100, self.check_progress_queue)
    
    def display_results(self):
        """Prikazuje rezultate pretrage"""
        # Update statistike
        total_slike = sum(len(g['datoteke']) for g in self.slicne_slike)
        total_video = sum(len(g['datoteke']) for g in self.slicni_videi)
        
        self.result_stats.configure(
            text=f"Slike: {total_slike} u {len(self.slicne_slike)} grupa | Video: {total_video} u {len(self.slicni_videi)} grupa"
        )
        
        # Clear previous results
        for widget in self.slike_container.winfo_children():
            widget.destroy()
        
        for widget in self.video_container.winfo_children():
            widget.destroy()
        
        # Display image groups
        self.display_image_groups()
        
        # Display video groups
        self.display_video_groups()
        
        # Popuni treeview za upravljanje
        self.populate_grupe_treeview()
        
        # Popuni combo za pregled
        self.populate_preview_combo()
        
        # Enable management buttons
        if total_slike + total_video > 0:
            self.btn_keep_selected.configure(state="normal")
            self.btn_delete_all.configure(state="normal")
            self.btn_copy_compare.configure(state="normal")
    
    def display_image_groups(self):
        """Prikazuje grupe slika"""
        for i, grupa in enumerate(self.slicne_slike):
            group_frame = ctk.CTkFrame(self.slike_container, corner_radius=8)
            group_frame.pack(fill="x", pady=10, padx=10)
            
            # Header grupe
            header = ctk.CTkFrame(group_frame, height=40, corner_radius=8)
            header.pack(fill="x", padx=5, pady=5)
            header.pack_propagate(False)
            
            ctk.CTkLabel(
                header,
                text=f"Grupa {i+1}: {len(grupa['datoteke'])} slika",
                font=self.font_normal
            ).pack(side="left", padx=15)
            
            # Izračunaj prosječnu sličnost
            slicnosti = list(grupa['slicnosti'].values())
            avg_slicnost = sum(slicnosti) / len(slicnosti) if slicnosti else 0
            
            ctk.CTkLabel(
                header,
                text=f"Sličnost: {avg_slicnost:.1f}%",
                font=self.font_normal,
                text_color=self.color_success if avg_slicnost > 90 else self.color_warning
            ).pack(side="right", padx=15)
            
            # Thumbnails
            thumb_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
            thumb_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            # Prikaži prvih 4 slike kao thumbnail
            for j, putanja in enumerate(list(grupa['datoteke'])[:4]):
                try:
                    img = Image.open(putanja)
                    img.thumbnail((150, 150))
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Label za thumbnail
                    thumb_label = ctk.CTkLabel(
                        thumb_frame,
                        text="",  # No text, just image
                        image=photo
                    )
                    thumb_label.image = photo  # Keep reference
                    thumb_label.pack(side="left", padx=5)
                    
                except Exception as e:
                    # Ako ne možemo učitati sliku, prikaži placeholder
                    placeholder = ctk.CTkLabel(
                        thumb_frame,
                        text=f"🖼️\n{putanja.name[:15]}...",
                        width=150,
                        height=150,
                        corner_radius=8,
                        font=self.font_small
                    )
                    placeholder.pack(side="left", padx=5)
    
    def display_video_groups(self):
        """Prikazuje grupe videa"""
        for i, grupa in enumerate(self.slicni_videi):
            group_frame = ctk.CTkFrame(self.video_container, corner_radius=8)
            group_frame.pack(fill="x", pady=10, padx=10)
            
            # Header grupe
            header = ctk.CTkFrame(group_frame, height=40, corner_radius=8)
            header.pack(fill="x", padx=5, pady=5)
            header.pack_propagate(False)
            
            ctk.CTkLabel(
                header,
                text=f"Grupa {i+1}: {len(grupa['datoteke'])} videozapisa",
                font=self.font_normal
            ).pack(side="left", padx=15)
            
            # Izračunaj prosječnu sličnost
            slicnosti = list(grupa['slicnosti'].values())
            avg_slicnost = sum(slicnosti) / len(slicnosti) if slicnosti else 0
            
            ctk.CTkLabel(
                header,
                text=f"Sličnost: {avg_slicnost:.1f}%",
                font=self.font_normal,
                text_color=self.color_success if avg_slicnost > 90 else self.color_warning
            ).pack(side="right", padx=15)
            
            # Lista videa
            list_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
            list_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            for j, putanja in enumerate(grupa['datoteke']):
                try:
                    velicina = self.trazilica.formatiraj_velicinu_datoteke(putanja.stat().st_size)
                    
                    video_item = ctk.CTkFrame(list_frame, height=30)
                    video_item.pack(fill="x", pady=2)
                    video_item.pack_propagate(False)
                    
                    ctk.CTkLabel(
                        video_item,
                        text="🎬",
                        width=30
                    ).pack(side="left")
                    
                    ctk.CTkLabel(
                        video_item,
                        text=f"{putanja.name[:40]}...",
                        font=self.font_small
                    ).pack(side="left", padx=10)
                    
                    ctk.CTkLabel(
                        video_item,
                        text=velicina,
                        font=self.font_small,
                        text_color=self.color_gray,
                        width=80
                    ).pack(side="right", padx=10)
                    
                except Exception:
                    pass
    
    def populate_grupe_treeview(self):
        """Popunjava treeview s grupama"""
        # Clear existing items
        for item in self.tree_grupe.get_children():
            self.tree_grupe.delete(item)
        
        # Dodaj grupe slika
        for i, grupa in enumerate(self.slicne_slike):
            slicnosti = list(grupa['slicnosti'].values())
            avg_slicnost = sum(slicnosti) / len(slicnosti) if slicnosti else 0
            
            self.tree_grupe.insert(
                "", "end",
                values=(
                    f"Grupa {i+1}",
                    "🖼️ Slike",
                    len(grupa['datoteke']),
                    f"{avg_slicnost:.1f}%"
                ),
                tags=("slike",)
            )
        
        # Dodaj grupe videa
        for i, grupa in enumerate(self.slicni_videi):
            slicnosti = list(grupa['slicnosti'].values())
            avg_slicnost = sum(slicnosti) / len(slicnosti) if slicnosti else 0
            
            self.tree_grupe.insert(
                "", "end",
                values=(
                    f"Grupa {len(self.slicne_slike) + i + 1}",
                    "🎬 Video",
                    len(grupa['datoteke']),
                    f"{avg_slicnost:.1f}%"
                ),
                tags=("video",)
            )
    
    def populate_preview_combo(self):
        """Popunjava combo box za pregled grupa"""
        groups = []
        
        # Dodaj grupe slika
        for i in range(len(self.slicne_slike)):
            groups.append(f"Grupa {i+1} - 🖼️ Slike")
        
        # Dodaj grupe videa
        for i in range(len(self.slicni_videi)):
            groups.append(f"Grupa {len(self.slicne_slike) + i + 1} - 🎬 Video")
        
        self.combo_grupe.configure(values=groups)
        if groups:
            self.combo_grupe.set(groups[0])
            self.combo_grupe.configure(state="normal")
    
    def on_grupa_select(self, event):
        """Handla odabir grupe iz treeview-a"""
        selection = self.tree_grupe.selection()
        if not selection:
            return
        
        item = self.tree_grupe.item(selection[0])
        values = item['values']
        
        # Dobavi index grupe (Grupa X -> index X-1)
        grupa_index = int(values[0].split()[1]) - 1
        tip = "slike" if "🖼️" in values[1] else "video"
        
        # Clear file list
        for widget in self.file_list_container.winfo_children():
            widget.destroy()
        
        # Dohvati grupu
        if tip == "slike":
            grupa = self.slicne_slike[grupa_index] if grupa_index < len(self.slicne_slike) else None
        else:
            grupa = self.slicni_videi[grupa_index - len(self.slicne_slike)] if grupa_index >= len(self.slicne_slike) else None
        
        if not grupa:
            return
        
        # Prikaži informacije o grupi
        self.show_grupa_info(grupa, tip)
        
        # Prikaži datoteke u grupi
        self.show_files_in_group(grupa, tip, grupa_index)
    
    def show_grupa_info(self, grupa, tip):
        """Prikazuje informacije o odabranoj grupi"""
        self.grupa_info_text.configure(state="normal")
        self.grupa_info_text.delete("1.0", "end")
        
        info_text = f"📋 Informacije o grupi:\n"
        info_text += f"• Tip: {'Slike' if tip == 'slike' else 'Videozapisi'}\n"
        info_text += f"• Broj datoteka: {len(grupa['datoteke'])}\n"
        
        if grupa['slicnosti']:
            slicnosti = list(grupa['slicnosti'].values())
            avg_slicnost = sum(slicnosti) / len(slicnosti)
            min_slicnost = min(slicnosti)
            max_slicnost = max(slicnosti)
            
            info_text += f"• Prosječna sličnost: {avg_slicnost:.1f}%\n"
            info_text += f"• Min sličnost: {min_slicnost:.1f}%\n"
            info_text += f"• Max sličnost: {max_slicnost:.1f}%\n"
        
        info_text += f"\n📁 Datoteke u grupi:\n"
        
        # Sortiraj po veličini
        sorted_files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size, reverse=True)
        
        for i, putanja in enumerate(sorted_files):
            try:
                velicina = putanja.stat().st_size
                formatted = self.trazilica.formatiraj_velicinu_datoteke(velicina)
                info_text += f"{i+1}. {putanja.name} ({formatted})\n"
            except:
                info_text += f"{i+1}. {putanja.name}\n"
        
        self.grupa_info_text.insert("1.0", info_text)
        self.grupa_info_text.configure(state="disabled")
    
    def show_files_in_group(self, grupa, tip, grupa_index):
        """Prikazuje datoteke u grupi sa checkboxovima"""
        # Inicijaliziraj izbore za ovu grupu
        if grupa_index not in self.izabrane_datoteke:
            self.izabrane_datoteke[grupa_index] = {}
        
        # Sortiraj po veličini (najveća prva)
        sorted_files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
        
        for i, putanja in enumerate(sorted_files):
            file_frame = ctk.CTkFrame(self.file_list_container, height=50)
            file_frame.pack(fill="x", pady=2)
            file_frame.pack_propagate(False)
            
            # Checkbox
            var = ctk.BooleanVar(value=(i == 0))  # Po defaultu označi prvu (najveću)
            self.izabrane_datoteke[grupa_index][putanja] = var
            
            checkbox = ctk.CTkCheckBox(
                file_frame,
                text="",
                variable=var,
                width=30
            )
            checkbox.pack(side="left", padx=10)
            
            # Ikonica
            icon = "🖼️" if tip == "slike" else "🎬"
            ctk.CTkLabel(
                file_frame,
                text=icon,
                width=30
            ).pack(side="left")
            
            # Ime datoteke
            name_label = ctk.CTkLabel(
                file_frame,
                text=putanja.name[:40] + ("..." if len(putanja.name) > 40 else ""),
                font=self.font_small,
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True, padx=10)
            
            # Veličina
            try:
                velicina = putanja.stat().st_size
                formatted = self.trazilica.formatiraj_velicinu_datoteke(velicina)
                size_label = ctk.CTkLabel(
                    file_frame,
                    text=formatted,
                    font=self.font_small,
                    text_color=self.color_gray,
                    width=80
                )
                size_label.pack(side="right", padx=10)
            except:
                pass
            
            # Info za slike
            if tip == "slike" and putanja.exists():
                try:
                    with Image.open(putanja) as img:
                        dims = f"{img.width}×{img.height}"
                        dim_label = ctk.CTkLabel(
                            file_frame,
                            text=dims,
                            font=self.font_small,
                            text_color=self.color_gray,
                            width=80
                        )
                        dim_label.pack(side="right", padx=10)
                except:
                    pass
    
    def select_all_files(self):
        """Označi sve datoteke u svim grupama"""
        for grupa_index, files in self.izabrane_datoteke.items():
            for var in files.values():
                var.set(True)
    
    def deselect_all_files(self):
        """Odznači sve datoteke u svim grupama"""
        for grupa_index, files in self.izabrane_datoteke.items():
            for var in files.values():
                var.set(False)
    
    def keep_selected(self):
        """Zadrži samo označene datoteke, obriši ostale"""
        if not self.izabrane_datoteke:
            messagebox.showwarning("Upozorenje", "Nema datoteka za obradu!")
            return
        
        # Potvrda
        if self.var_confirm_delete.get():
            confirm = messagebox.askyesno(
                "Potvrda brisanja",
                "Želite li zaista obrisati sve neoznačene duplikate?\n\n"
                "Ova akcija se ne može poništiti!"
            )
            if not confirm:
                return
        
        total_deleted = 0
        errors = 0
        
        # Prođi kroz sve grupe
        for grupa_index, files in self.izabrane_datoteke.items():
            # Odredi koje su označene
            to_keep = [path for path, var in files.items() if var.get()]
            to_delete = [path for path, var in files.items() if not var.get()]
            
            # Obriši neoznačene
            for path in to_delete:
                try:
                    path.unlink()
                    total_deleted += 1
                except Exception as e:
                    errors += 1
        
        # Prikaži rezultat
        message = f"✅ Uspješno obrisano: {total_deleted} datoteka"
        if errors > 0:
            message += f"\n❌ Greške: {errors} datoteka"
        
        messagebox.showinfo("Rezultat brisanja", message)
        
        # Osvježi prikaz
        self.start_search()
    
    def delete_all_duplicates(self):
        """Obriši sve duplikate (zadrži po jedan u svakoj grupi)"""
        if not self.slicne_slike and not self.slicni_videi:
            messagebox.showwarning("Upozorenje", "Nema duplikata za brisanje!")
            return
        
        # Potvrda
        if self.var_confirm_delete.get():
            confirm = messagebox.askyesno(
                "Potvrda brisanja",
                "Želite li zaista obrisati sve duplikate?\n\n"
                "Samo jedna datoteka po grupi će biti zadržana.\n"
                "Ova akcija se ne može poništiti!"
            )
            if not confirm:
                return
        
        total_deleted = 0
        errors = 0
        
        # Obradi grupe slika
        for grupa in self.slicne_slike:
            files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size, reverse=True)
            to_keep = files[0] if files else None
            to_delete = files[1:] if len(files) > 1 else []
            
            for path in to_delete:
                try:
                    path.unlink()
                    total_deleted += 1
                except Exception as e:
                    errors += 1
        
        # Obradi grupe videa
        for grupa in self.slicni_videi:
            files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size, reverse=True)
            to_keep = files[0] if files else None
            to_delete = files[1:] if len(files) > 1 else []
            
            for path in to_delete:
                try:
                    path.unlink()
                    total_deleted += 1
                except Exception as e:
                    errors += 1
        
        # Prikaži rezultat
        message = f"✅ Uspješno obrisano: {total_deleted} duplikata"
        if errors > 0:
            message += f"\n❌ Greške: {errors} datoteka"
        
        messagebox.showinfo("Rezultat brisanja", message)
        
        # Osvježi prikaz
        self.start_search()
    
    def copy_for_comparison(self):
        """Kopira duplikate u folder za usporedbu"""
        if not self.slicne_slike and not self.slicni_videi:
            messagebox.showwarning("Upozorenje", "Nema duplikata za kopiranje!")
            return
        
        # Odaberi odredišni folder
        dest_folder = filedialog.askdirectory(
            title="Odaberite folder za kopiranje duplikata",
            mustexist=False
        )
        
        if not dest_folder:
            return
        
        dest_path = Path(dest_folder)
        
        try:
            # Kreiraj folder ako ne postoji
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Kopiraj slike
            if self.slicne_slike:
                self.trazilica.kopiraj_slicne_grupe(self.slicne_slike, dest_path, "slike")
            
            # Kopiraj videe
            if self.slicni_videi:
                self.trazilica.kopiraj_slicne_grupe(self.slicni_videi, dest_path, "videi")
            
            # Prikaži poruku
            messagebox.showinfo(
                "Kopiranje završeno",
                f"Svi duplikati su kopirani u:\n{dest_folder}\n\n"
                f"Pogledajte README.txt za upute o uklanjanju prefiksa."
            )
            
        except Exception as e:
            messagebox.showerror("Greška", f"Greška pri kopiranju: {str(e)}")
    
    def load_preview_group(self, choice):
        """Učitava grupu za vizualni pregled"""
        # Parse choice
        if not choice:
            return
        
        parts = choice.split(" - ")
        if len(parts) < 2:
            return
        
        group_num = int(parts[0].split()[1]) - 1
        tip = "slike" if "🖼️" in parts[1] else "video"
        
        # Dobavi grupu
        if tip == "slike":
            grupa = self.slicne_slike[group_num] if group_num < len(self.slicne_slike) else None
        else:
            grupa = self.slicni_videi[group_num - len(self.slicne_slike)] if group_num >= len(self.slicne_slike) else None
        
        if not grupa:
            return
        
        # Clear preview
        for widget in self.preview_container.winfo_children():
            widget.destroy()
        
        # Za slike: prikaži thumbnail grid
        if tip == "slike":
            self.show_image_preview(grupa)
        else:
            self.show_video_preview(grupa)
    
    def show_image_preview(self, grupa):
        """Prikazuje slike u grupi za vizualnu usporedbu"""
        # Sortiraj po veličini
        files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size, reverse=True)
        
        # Kreiraj grid
        rows = 2
        cols = min(3, len(files))
        
        for i, putanja in enumerate(files[:rows*cols]):
            try:
                # Učitaj sliku
                img = Image.open(putanja)
                img.thumbnail((250, 250))
                photo = ImageTk.PhotoImage(img)
                
                # Kreiraj frame za sliku
                img_frame = ctk.CTkFrame(self.preview_container)
                img_frame.grid(row=i//cols, column=i%cols, padx=10, pady=10, sticky="nsew")
                
                # Konfiguriši grid
                self.preview_container.grid_rowconfigure(i//cols, weight=1)
                self.preview_container.grid_columnconfigure(i%cols, weight=1)
                
                # Label za sliku
                label = ctk.CTkLabel(img_frame, text="", image=photo)
                label.image = photo
                label.pack(padx=5, pady=5)
                
                # Ime i veličina
                velicina = self.trazilica.formatiraj_velicinu_datoteke(putanja.stat().st_size)
                try:
                    with Image.open(putanja) as img_full:
                        dims = f"{img_full.width}×{img_full.height}"
                    info_text = f"{putanja.name[:20]}...\n{velicina} | {dims}"
                except:
                    info_text = f"{putanja.name[:20]}...\n{velicina}"
                
                ctk.CTkLabel(
                    img_frame,
                    text=info_text,
                    font=self.font_small,
                    text_color=self.color_gray
                ).pack(pady=(0, 5))
                
            except Exception as e:
                # Placeholder ako ne možemo učitati sliku
                placeholder = ctk.CTkLabel(
                    self.preview_container,
                    text=f"🖼️\n{putanja.name[:15]}...\n(Ne mogu učitati)",
                    width=250,
                    height=250,
                    corner_radius=8,
                    font=self.font_small
                )
                placeholder.grid(row=i//cols, column=i%cols, padx=10, pady=10)
    
    def show_video_preview(self, grupa):
        """Prikazuje informacije o videima u grupi"""
        # Sortiraj po veličini
        files = sorted(grupa['datoteke'], key=lambda p: p.stat().st_size, reverse=True)
        
        # Kreiraj listu
        for i, putanja in enumerate(files):
            try:
                velicina = self.trazilica.formatiraj_velicinu_datoteke(putanja.stat().st_size)
                
                video_frame = ctk.CTkFrame(self.preview_container, height=60)
                video_frame.pack(fill="x", pady=5, padx=20)
                video_frame.pack_propagate(False)
                
                # Ikonica
                ctk.CTkLabel(
                    video_frame,
                    text="🎬",
                    width=40
                ).pack(side="left", padx=10)
                
                # Informacije
                info_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
                info_frame.pack(side="left", fill="both", expand=True, padx=10)
                
                ctk.CTkLabel(
                    info_frame,
                    text=putanja.name,
                    font=self.font_normal,
                    anchor="w"
                ).pack(anchor="w")
                
                ctk.CTkLabel(
                    info_frame,
                    text=f"Veličina: {velicina} | Putanja: {putanja.parent}",
                    font=self.font_small,
                    text_color=self.color_gray,
                    anchor="w"
                ).pack(anchor="w")
                
                # Dugme za pregled
                if i == 0:  # Samo za prvi video
                    btn_frame = ctk.CTkFrame(video_frame, fg_color="transparent")
                    btn_frame.pack(side="right", padx=10)
                    
                    ctk.CTkButton(
                        btn_frame,
                        text="📂 Otvori folder",
                        width=120,
                        font=self.font_small,
                        command=lambda p=putanja: os.startfile(p.parent)
                    ).pack(side="right", padx=5)
                    
            except Exception as e:
                pass
    
    def on_closing(self):
        """Handla zatvaranje aplikacije"""
        if messagebox.askokcancel("Izlaz", "Želite li zaista izaći iz aplikacije?"):
            self.root.destroy()
    
    def run(self):
        """Pokreće GUI aplikaciju"""
        self.root.mainloop()


if __name__ == "__main__":
    # Provjeri da li su potrebne biblioteke instalirane
    try:
        import cv2
        import PIL
        import imagehash
    except ImportError as e:
        print("❌ Greška: Nedostaju potrebne biblioteke!")
        print("📦 Molim instalirajte:")
        print("   pip install opencv-python pillow imagehash customtkinter")
        print(f"   Nedostaje: {e}")
        exit(1)
    
    # Pokreni aplikaciju
    app = ModernDuplikatGUI()
    app.run()