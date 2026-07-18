import os
import shutil
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
from datetime import datetime
import cv2
import numpy as np


class VideoDuplicateRemoverGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Duplikat Remover Pro")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)
        
        # Moderna tamna tema
        self.colors = {
            'bg_dark': '#0f172a',
            'bg_medium': '#1e293b',
            'bg_light': '#334155',
            'bg_lighter': '#475569',
            'accent_primary': '#3b82f6',
            'accent_secondary': '#8b5cf6',
            'accent_hover': '#2563eb',
            'accent_danger': '#ef4444',
            'accent_success': '#10b981',
            'accent_warning': '#f59e0b',
            'text_white': '#ffffff',
            'text_gray': '#cbd5e1',
            'text_light_gray': '#94a3b8',
            'border': '#475569'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        # Varijable
        self.nas_paths = []
        self.check_folder = tk.StringVar()
        self.move_folder = tk.StringVar()
        self.processing = False
        self.video_files = []
        self.duplicates = []
        self.selected_duplicates = set()
        
        # Opcije
        self.deep_check = tk.BooleanVar(value=False)
        self.delete_original = tk.BooleanVar(value=True)
        self.create_log = tk.BooleanVar(value=True)
        self.show_preview = tk.BooleanVar(value=True)
        self.check_subfolders = tk.BooleanVar(value=True)
        
        # Video ekstenzije
        self.video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
            '.3gp', '.3g2', '.f4v', '.asf', '.rm', '.rmvb', '.vob', '.ogv',
            '.mts', '.m2ts', '.ts', '.mxf', '.dv', '.divx', '.xvid', '.mpg', '.mpeg'
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_medium'], relief=tk.FLAT)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="🎬 VIDEO DUPLIKAT REMOVER PRO",
            font=("Segoe UI", 24, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_primary'],
            pady=15
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header_frame,
            text="Napredni alat za pronalaženje i uklanjanje duplikata video datoteka",
            font=("Segoe UI", 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light_gray']
        )
        subtitle_label.pack(pady=(0, 15))
        
        # Content area
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Left panel - File management
        left_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Right panel - Preview and controls
        right_panel = tk.Frame(content_frame, bg=self.colors['bg_dark'])
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Setup panels
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
        
    def setup_left_panel(self, parent):
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Notebook za više tabova
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Stiliziraj notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg_dark'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.colors['bg_medium'],
                       foreground=self.colors['text_white'],
                       padding=[15, 5],
                       font=('Segoe UI', 10))
        style.map('TNotebook.Tab', 
                 background=[('selected', self.colors['accent_primary'])],
                 foreground=[('selected', self.colors['text_white'])])
        
        # Tab 1: NAS Folders
        nas_tab = tk.Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(nas_tab, text="📁 NAS Folders")
        self.setup_nas_tab(nas_tab)
        
        # Tab 2: Check Folder
        check_tab = tk.Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(check_tab, text="🔍 Check Folder")
        self.setup_check_tab(check_tab)
        
        # Tab 3: Duplicates
        dup_tab = tk.Frame(notebook, bg=self.colors['bg_medium'])
        notebook.add(dup_tab, text="🔄 Duplicates")
        self.setup_duplicates_tab(dup_tab)
        
    def setup_nas_tab(self, parent):
        # NAS paths list
        list_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header_label = tk.Label(
            list_frame,
            text="NAS Folders (Reference Folders)",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            anchor=tk.W
        )
        header_label.pack(fill=tk.X, pady=(0, 10))
        
        # Listbox sa scrollbarom
        list_container = tk.Frame(list_frame, bg=self.colors['bg_light'])
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_container, bg=self.colors['bg_light'])
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.nas_listbox = tk.Listbox(
            list_container,
            bg=self.colors['bg_lighter'],
            fg=self.colors['text_white'],
            selectbackground=self.colors['accent_primary'],
            selectforeground=self.colors['text_white'],
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            yscrollcommand=scrollbar.set,
            height=8
        )
        self.nas_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.nas_listbox.yview)
        
        # Button frame
        button_frame = tk.Frame(list_frame, bg=self.colors['bg_medium'])
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Buttons
        add_btn = tk.Button(
            button_frame,
            text="+ Add NAS Folder",
            command=self.add_nas_folder,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        remove_btn = tk.Button(
            button_frame,
            text="− Remove Selected",
            command=self.remove_nas_folder,
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        remove_btn.pack(side=tk.LEFT)
        
        # Info
        info_label = tk.Label(
            list_frame,
            text="Add folders that contain your original video files.\nFiles found here will be used as reference for duplicate detection.",
            font=("Segoe UI", 8),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light_gray'],
            justify=tk.LEFT
        )
        info_label.pack(fill=tk.X, pady=(15, 0))
        
    def setup_check_tab(self, parent):
        # Check folder selection
        folder_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        folder_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Check folder
        check_label = tk.Label(
            folder_frame,
            text="Folder to Check for Duplicates",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_white'],
            anchor=tk.W
        )
        check_label.pack(fill=tk.X, pady=(0, 10))
        
        check_entry_frame = tk.Frame(folder_frame, bg=self.colors['bg_medium'])
        check_entry_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.check_entry = tk.Entry(
            check_entry_frame,
            textvariable=self.check_folder,
            font=("Segoe UI", 10),
            bg=self.colors['bg_lighter'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            insertbackground=self.colors['accent_primary']
        )
        self.check_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        browse_check_btn = tk.Button(
            check_entry_frame,
            text="Browse",
            command=self.browse_check_folder,
            bg=self.colors['accent_primary'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8
        )
        browse_check_btn.pack(side=tk.RIGHT)
        
        # Options
        options_frame = tk.Frame(folder_frame, bg=self.colors['bg_medium'])
        options_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Options grid
        for i, (text, var) in enumerate([
            ("Deep Check (MD5 Hash)", self.deep_check),
            ("Include Subfolders", self.check_subfolders),
            ("Show Video Preview", self.show_preview),
            ("Create Log File", self.create_log)
        ]):
            cb = tk.Checkbutton(
                options_frame,
                text=text,
                variable=var,
                bg=self.colors['bg_medium'],
                fg=self.colors['text_gray'],
                activebackground=self.colors['bg_medium'],
                activeforeground=self.colors['text_gray'],
                selectcolor=self.colors['accent_primary'],
                font=("Segoe UI", 9),
                cursor="hand2",
                anchor=tk.W
            )
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=(0, 20), pady=5)
        
        # Scan button
        scan_btn = tk.Button(
            folder_frame,
            text="🔍 SCAN FOR DUPLICATES",
            command=self.start_scan,
            bg=self.colors['accent_secondary'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 12, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            pady=12
        )
        scan_btn.pack(fill=tk.X, pady=(10, 0))
        
    def setup_duplicates_tab(self, parent):
        # Duplicates list
        dup_frame = tk.Frame(parent, bg=self.colors['bg_medium'])
        dup_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header with count
        self.dup_header = tk.Label(
            dup_frame,
            text="Duplicates Found: 0",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_medium'],
            fg=self.colors['accent_primary'],
            anchor=tk.W
        )
        self.dup_header.pack(fill=tk.X, pady=(0, 10))
        
        # Listbox with checkboxes simulation
        list_container = tk.Frame(dup_frame, bg=self.colors['bg_light'])
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbars
        y_scrollbar = tk.Scrollbar(list_container, bg=self.colors['bg_light'])
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = tk.Scrollbar(list_container, orient=tk.HORIZONTAL, bg=self.colors['bg_light'])
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview for better display
        columns = ('Select', 'Filename', 'Size', 'Path')
        self.dup_tree = ttk.Treeview(
            list_container,
            columns=columns,
            show='headings',
            height=12,
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview",
                       background=self.colors['bg_lighter'],
                       foreground=self.colors['text_white'],
                       fieldbackground=self.colors['bg_lighter'],
                       rowheight=25)
        style.configure("Treeview.Heading",
                       background=self.colors['bg_light'],
                       foreground=self.colors['text_white'],
                       relief=tk.FLAT,
                       font=('Segoe UI', 9, 'bold'))
        style.map('Treeview', background=[('selected', self.colors['accent_primary'])])
        
        # Configure columns
        self.dup_tree.heading('Select', text='✓', command=self.toggle_all_selection)
        self.dup_tree.heading('Filename', text='Filename')
        self.dup_tree.heading('Size', text='Size')
        self.dup_tree.heading('Path', text='Path')
        
        self.dup_tree.column('Select', width=40, anchor=tk.CENTER)
        self.dup_tree.column('Filename', width=200)
        self.dup_tree.column('Size', width=80, anchor=tk.E)
        self.dup_tree.column('Path', width=300)
        
        self.dup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scrollbar.config(command=self.dup_tree.yview)
        x_scrollbar.config(command=self.dup_tree.xview)
        
        # Action buttons
        action_frame = tk.Frame(dup_frame, bg=self.colors['bg_medium'])
        action_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Move folder selection
        move_frame = tk.Frame(action_frame, bg=self.colors['bg_medium'])
        move_frame.pack(fill=tk.X, pady=(0, 10))
        
        move_label = tk.Label(
            move_frame,
            text="Move to folder:",
            font=("Segoe UI", 9),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_gray'],
            anchor=tk.W
        )
        move_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.move_entry = tk.Entry(
            move_frame,
            textvariable=self.move_folder,
            font=("Segoe UI", 9),
            bg=self.colors['bg_lighter'],
            fg=self.colors['text_white'],
            relief=tk.FLAT,
            width=40
        )
        self.move_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        
        browse_move_btn = tk.Button(
            move_frame,
            text="Browse",
            command=self.browse_move_folder,
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=4
        )
        browse_move_btn.pack(side=tk.RIGHT)
        
        # Action buttons
        btn_frame = tk.Frame(action_frame, bg=self.colors['bg_medium'])
        btn_frame.pack(fill=tk.X)
        
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️ DELETE SELECTED",
            command=self.delete_selected,
            bg=self.colors['accent_danger'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        delete_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        move_btn = tk.Button(
            btn_frame,
            text="📁 MOVE SELECTED",
            command=self.move_selected,
            bg=self.colors['accent_warning'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10
        )
        move_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        select_all_btn = tk.Button(
            btn_frame,
            text="✓ SELECT ALL",
            command=self.select_all_duplicates,
            bg=self.colors['bg_light'],
            fg=self.colors['text_white'],
            font=("Segoe UI", 9),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=8
        )
        select_all_btn.pack(side=tk.LEFT)
        
    def setup_right_panel(self, parent):
        parent.grid_rowconfigure(0, weight=2)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Preview panel
        preview_card = self.create_card("🎥 Video Preview", parent, 0)
        self.setup_preview_panel(preview_card)
        
        # Stats panel
        stats_card = self.create_card("📊 Statistics", parent, 1)
        self.setup_stats_panel(stats_card)
        
    def create_card(self, title, parent, row):
        card = tk.Frame(parent, bg=self.colors['bg_medium'], relief=tk.FLAT)
        card.grid(row=row, column=0, sticky="nsew", pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        
        title_label = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg_lighter'],
            fg=self.colors['accent_primary'],
            anchor=tk.W,
            pady=10,
            padx=15
        )
        title_label.grid(row=0, column=0, sticky="ew")
        
        content_frame = tk.Frame(card, bg=self.colors['bg_medium'])
        content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        return content_frame
        
    def setup_preview_panel(self, parent):
        self.preview_label = tk.Label(
            parent,
            text="No video selected\n\nSelect a duplicate from the list\nto see preview",
            font=("Segoe UI", 10),
            bg=self.colors['bg_medium'],
            fg=self.colors['text_light_gray'],
            justify=tk.CENTER,
            padx=20,
            pady=40
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # Bind selection event
        self.dup_tree.bind('<<TreeviewSelect>>', self.on_video_select)
        
    def setup_stats_panel(self, parent):
        self.stats_text = tk.Text(
            parent,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_gray'],
            font=("Consolas", 9),
            relief=tk.FLAT,
            height=8,
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.insert(tk.END, "Statistics will appear here after scan.")
        self.stats_text.config(state=tk.DISABLED)
        
        # Update stats initially
        self.update_stats()
        
    def add_nas_folder(self):
        folder = filedialog.askdirectory(title="Select NAS Folder")
        if folder and folder not in self.nas_paths:
            self.nas_paths.append(folder)
            self.nas_listbox.insert(tk.END, folder)
            self.update_stats()
            
    def remove_nas_folder(self):
        selection = self.nas_listbox.curselection()
        if selection:
            index = selection[0]
            self.nas_paths.pop(index)
            self.nas_listbox.delete(index)
            self.update_stats()
            
    def browse_check_folder(self):
        folder = filedialog.askdirectory(title="Select Folder to Check")
        if folder:
            self.check_folder.set(folder)
            
    def browse_move_folder(self):
        folder = filedialog.askdirectory(title="Select Move Destination")
        if folder:
            self.move_folder.set(folder)
            
    def start_scan(self):
        if not self.nas_paths:
            messagebox.showwarning("Warning", "Please add at least one NAS folder first.")
            return
            
        if not self.check_folder.get():
            messagebox.showwarning("Warning", "Please select a folder to check.")
            return
            
        # Disable scan button during processing
        self.processing = True
        
        # Start scan in separate thread
        thread = threading.Thread(target=self.scan_duplicates)
        thread.daemon = True
        thread.start()
        
    def scan_duplicates(self):
        try:
            self.update_status("🔍 Starting scan for duplicates...")
            
            # Get NAS files
            nas_files = {}
            self.update_status("Scanning NAS folders...")
            
            for nas_path in self.nas_paths:
                nas_videos = self.get_video_files(nas_path, self.check_subfolders.get())
                for video in nas_videos:
                    filename = self.get_filename_without_extension(video)
                    if self.deep_check.get():
                        # Use hash for deep check
                        file_hash = self.calculate_file_hash(video)
                        key = f"{filename}_{file_hash}"
                    else:
                        key = filename
                    
                    if key not in nas_files:
                        nas_files[key] = []
                    nas_files[key].append(video)
            
            self.update_status(f"Found {len(nas_files)} unique files in NAS folders")
            
            # Get check folder files
            self.update_status("Scanning check folder...")
            check_files = self.get_video_files(self.check_folder.get(), self.check_subfolders.get())
            
            self.update_status(f"Found {len(check_files)} files in check folder")
            
            # Find duplicates
            self.duplicates = []
            self.selected_duplicates.clear()
            
            for check_file in check_files:
                filename = self.get_filename_without_extension(check_file)
                if self.deep_check.get():
                    file_hash = self.calculate_file_hash(check_file)
                    key = f"{filename}_{file_hash}"
                else:
                    key = filename
                
                if key in nas_files:
                    file_size = os.path.getsize(check_file)
                    self.duplicates.append({
                        'path': check_file,
                        'filename': os.path.basename(check_file),
                        'size': file_size,
                        'nas_matches': nas_files[key]
                    })
            
            # Update UI with results
            self.root.after(0, self.update_duplicates_list)
            self.update_status(f"✅ Scan complete! Found {len(self.duplicates)} duplicates")
            
        except Exception as e:
            self.update_status(f"❌ Error during scan: {str(e)}", error=True)
        finally:
            self.processing = False
            
    def get_video_files(self, folder_path, recursive=True):
        video_files = []
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if Path(file).suffix.lower() in self.video_extensions:
                        full_path = os.path.join(root, file)
                        video_files.append(full_path)
        else:
            for file in os.listdir(folder_path):
                if os.path.isfile(os.path.join(folder_path, file)):
                    if Path(file).suffix.lower() in self.video_extensions:
                        full_path = os.path.join(folder_path, file)
                        video_files.append(full_path)
        
        return video_files
        
    def get_filename_without_extension(self, file_path):
        return Path(file_path).stem
        
    def calculate_file_hash(self, file_path, chunk_size=8192):
        """Calculate MD5 hash of file"""
        md5_hash = hashlib.md5()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except:
            return "error_hash"
            
    def update_duplicates_list(self):
        # Clear current list
        for item in self.dup_tree.get_children():
            self.dup_tree.delete(item)
        
        # Add new items
        for i, dup in enumerate(self.duplicates):
            size_mb = dup['size'] / (1024 * 1024)
            display_size = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{dup['size'] / 1024:.1f} KB"
            
            # Truncate path for display
            display_path = dup['path']
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]
            
            # Insert with checkbox emoji
            item_id = self.dup_tree.insert('', tk.END, values=(
                '☐',  # Checkbox emoji
                dup['filename'],
                display_size,
                display_path
            ))
            
            # Store original path in item
            self.dup_tree.set(item_id, 'full_path', dup['path'])
            
        # Update header
        self.dup_header.config(text=f"Duplicates Found: {len(self.duplicates)}")
        
        # Update stats
        self.update_stats()
        
    def toggle_all_selection(self):
        all_selected = all(self.dup_tree.item(item)['values'][0] == '☑' 
                          for item in self.dup_tree.get_children())
        
        new_state = '☐' if all_selected else '☑'
        
        for item in self.dup_tree.get_children():
            values = list(self.dup_tree.item(item)['values'])
            values[0] = new_state
            self.dup_tree.item(item, values=values)
            
            # Update selection set
            full_path = self.dup_tree.set(item, 'full_path')
            if new_state == '☑':
                self.selected_duplicates.add(full_path)
            else:
                self.selected_duplicates.discard(full_path)
                
        self.update_stats()
        
    def on_video_select(self, event):
        selection = self.dup_tree.selection()
        if selection and self.show_preview.get():
            item = selection[0]
            full_path = self.dup_tree.set(item, 'full_path')
            self.show_video_preview(full_path)
            
    def show_video_preview(self, video_path):
        try:
            # Get video thumbnail using OpenCV
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Resize frame for preview
                    frame = cv2.resize(frame, (320, 180))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    img = Image.fromarray(frame)
                    photo = ImageTk.PhotoImage(img)
                    
                    # Update label
                    self.preview_label.config(
                        image=photo,
                        text=""
                    )
                    self.preview_label.image = photo  # Keep reference
                else:
                    self.preview_label.config(
                        image="",
                        text="Unable to load preview\n\nVideo file may be corrupted"
                    )
                cap.release()
        except Exception as e:
            self.preview_label.config(
                image="",
                text=f"Preview error:\n{str(e)}"
            )
            
    def select_all_duplicates(self):
        for item in self.dup_tree.get_children():
            values = list(self.dup_tree.item(item)['values'])
            values[0] = '☑'
            self.dup_tree.item(item, values=values)
            
            full_path = self.dup_tree.set(item, 'full_path')
            self.selected_duplicates.add(full_path)
            
        self.update_stats()
        
    def delete_selected(self):
        if not self.selected_duplicates:
            messagebox.showwarning("Warning", "No duplicates selected for deletion.")
            return
            
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {len(self.selected_duplicates)} selected files?\n\nThis action cannot be undone!"
        )
        
        if confirm:
            deleted = 0
            failed = 0
            
            for file_path in list(self.selected_duplicates):
                try:
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    os.remove(file_path)
                    self.update_status(f"🗑️ Deleted: {os.path.basename(file_path)} ({file_size:.1f} MB)")
                    deleted += 1
                    
                    # Remove from list
                    self.selected_duplicates.remove(file_path)
                    
                except Exception as e:
                    self.update_status(f"❌ Failed to delete {file_path}: {str(e)}", error=True)
                    failed += 1
            
            # Refresh list
            self.duplicates = [d for d in self.duplicates if d['path'] not in self.selected_duplicates]
            self.root.after(0, self.update_duplicates_list)
            
            messagebox.showinfo(
                "Deletion Complete",
                f"Successfully deleted: {deleted} files\nFailed: {failed} files"
            )
            
    def move_selected(self):
        if not self.selected_duplicates:
            messagebox.showwarning("Warning", "No duplicates selected for moving.")
            return
            
        move_folder = self.move_folder.get()
        if not move_folder:
            move_folder = filedialog.askdirectory(title="Select Destination Folder")
            if not move_folder:
                return
            self.move_folder.set(move_folder)
        
        # Create folder if it doesn't exist
        if not os.path.exists(move_folder):
            try:
                os.makedirs(move_folder)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create folder: {str(e)}")
                return
        
        moved = 0
        failed = 0
        total_size = 0
        
        for file_path in list(self.selected_duplicates):
            try:
                filename = os.path.basename(file_path)
                destination = os.path.join(move_folder, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(destination):
                    new_filename = f"{base_name}_{counter}{ext}"
                    destination = os.path.join(move_folder, new_filename)
                    counter += 1
                
                file_size = os.path.getsize(file_path) / (1024 * 1024)
                shutil.move(file_path, destination)
                
                self.update_status(f"📁 Moved: {filename} ({file_size:.1f} MB)")
                moved += 1
                total_size += file_size
                
                # Remove from list
                self.selected_duplicates.remove(file_path)
                
            except Exception as e:
                self.update_status(f"❌ Failed to move {file_path}: {str(e)}", error=True)
                failed += 1
        
        # Refresh list
        self.duplicates = [d for d in self.duplicates if d['path'] not in self.selected_duplicates]
        self.root.after(0, self.update_duplicates_list)
        
        messagebox.showinfo(
            "Move Complete",
            f"Successfully moved: {moved} files ({total_size:.1f} MB)\nFailed: {failed} files"
        )
        
    def update_stats(self):
        total_size = sum(d['size'] for d in self.duplicates) / (1024 * 1024 * 1024)  # GB
        selected_size = sum(d['size'] for d in self.duplicates 
                          if d['path'] in self.selected_duplicates) / (1024 * 1024 * 1024)
        
        stats_text = f"""
┌────────────── STATISTICS ──────────────┐
│                                         │
│  📁 NAS Folders: {len(self.nas_paths):<10}          │
│  🔍 Files to Check: {len(self.video_files):<7}          │
│  🔄 Duplicates Found: {len(self.duplicates):<6}          │
│  ✓ Selected: {len(self.selected_duplicates):<10}          │
│                                         │
│  📊 Total Duplicate Size: {total_size:.2f} GB      │
│  📊 Selected Size: {selected_size:.2f} GB          │
│                                         │
└─────────────────────────────────────────┘
"""
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats_text)
        self.stats_text.config(state=tk.DISABLED)
        
    def update_status(self, message, error=False):
        # This would update a status bar if we had one
        print(f"[STATUS] {message}")
        # For now, just update the stats
        self.update_stats()


def main():
    root = tk.Tk()
    app = VideoDuplicateRemoverGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()