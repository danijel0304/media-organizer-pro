#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Napredni pronalazač duplikata - Moderni GUI
"""

import os
import hashlib
import cv2
import numpy as np
from collections import defaultdict
from pathlib import Path
import time
from PIL import Image
import imagehash
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from queue import Queue
import json
from datetime import datetime

class ModernDuplicateFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Napredni Pronalazač Duplikata")
        self.root.geometry("1200x800")
        
        # Postavi theme
        self.setup_style()
        
        # Varijable
        self.selected_folder = tk.StringVar()
        self.is_scanning = False
        self.current_language = "hr"
        
        # Postavke
        self.similarity_threshold_images = tk.DoubleVar(value=85.0)
        self.similarity_threshold_videos = tk.DoubleVar(value=85.0)
        self.delete_after_scan = tk.BooleanVar(value=False)
        self.create_backup = tk.BooleanVar(value=True)
        
        # Rezultati
        self.similar_images = []
        self.similar_videos = []
        self.scan_results = []
        self.total_found = tk.IntVar(value=0)
        self.scan_time = tk.StringVar(value="00:00:00")
        
        # Ekstenzije
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg'}
        
        # Setup UI
        self.setup_ui()
        
    def setup_style(self):
        """Konfigurira moderne stile"""
        style = ttk.Style()
        
        # Modernni teme
        style.theme_use('clam')
        
        # Custom boje
        bg_color = '#f8f9fa'
        accent_color = '#007bff'
        danger_color = '#dc3545'
        success_color = '#28a745'
        warning_color = '#ffc107'
        
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'))
        style.configure('TNotebook.Tab', font=('Segoe UI', 10))
        
        self.root.configure(bg=bg_color)
        
    def setup_ui(self):
        """Postavi korisničko sučelje"""
        # Glavni container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.setup_header(main_container)
        
        # Body - Notebook (tabovi)
        self.setup_notebook(main_container)
        
        # Status bar
        self.setup_status_bar(main_container)
        
    def setup_header(self, parent):
        """Postavi header sa folder odabirom"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Naslov
        title_label = ttk.Label(header_frame, text="🔍 Napredni Pronalazač Duplikata", 
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Folder selektor
        folder_frame = ttk.Frame(header_frame)
        folder_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(50, 0))
        
        ttk.Label(folder_frame, text="📁 Odaberi mapu:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.selected_folder, width=40)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(folder_frame, text="Pregledaj...", 
                              command=self.browse_folder, style='Accent.TButton')
        browse_btn.pack(side=tk.LEFT)
        
        scan_btn = ttk.Button(header_frame, text="🔍 Pokreni skeniranje", 
                            command=self.start_scan, style='Accent.TButton')
        scan_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
    def setup_notebook(self, parent):
        """Postavi tabove"""
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Skeniranje i rezultati
        self.setup_scan_tab(notebook)
        
        # Tab 2: Postavke
        self.setup_settings_tab(notebook)
        
        # Tab 3: Usporedba
        self.setup_compare_tab(notebook)
        
    def setup_scan_tab(self, notebook):
        """Tab za skeniranje i pregled rezultata"""
        scan_frame = ttk.Frame(notebook)
        notebook.add(scan_frame, text="📊 Skeniranje")
        
        # Gornji panel - statistika
        stats_frame = ttk.LabelFrame(scan_frame, text="📈 Statistika", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.setup_stats_panel(stats_frame)
        
        # Donji panel - rezultati
        results_frame = ttk.LabelFrame(scan_frame, text="📋 Rezultati", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        self.setup_results_panel(results_frame)
        
    def setup_stats_panel(self, parent):
        """Panel sa statistikom"""
        # Grid za statističke podatke
        stats_grid = ttk.Frame(parent)
        stats_grid.pack(fill=tk.X)
        
        # Red 1
        ttk.Label(stats_grid, text="Pronađeno duplikata:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.total_label = ttk.Label(stats_grid, text="0", font=('Segoe UI', 12, 'bold'))
        self.total_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(stats_grid, text="Sličnih slika:").grid(row=0, column=2, sticky=tk.W, padx=20, pady=5)
        self.images_label = ttk.Label(stats_grid, text="0 grupa", font=('Segoe UI', 10))
        self.images_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(stats_grid, text="Sličnih videa:").grid(row=0, column=4, sticky=tk.W, padx=20, pady=5)
        self.videos_label = ttk.Label(stats_grid, text="0 grupa", font=('Segoe UI', 10))
        self.videos_label.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        # Red 2
        ttk.Label(stats_grid, text="Vrijeme skeniranja:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.time_label = ttk.Label(stats_grid, text="00:00:00", font=('Segoe UI', 10))
        self.time_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(stats_grid, text="Prosječna sličnost:").grid(row=1, column=2, sticky=tk.W, padx=20, pady=5)
        self.avg_similarity_label = ttk.Label(stats_grid, text="0%", font=('Segoe UI', 10))
        self.avg_similarity_label.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Dugmad za akcije
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(action_frame, text="🗑️  Upravljaj duplikatima", 
                  command=self.show_duplicate_manager).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="📊 Detaljni izvještaj", 
                  command=self.show_detailed_report).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(action_frame, text="💾 Izvezi rezultate", 
                  command=self.export_results).pack(side=tk.LEFT)
        
    def setup_results_panel(self, parent):
        """Panel sa prikazom rezultata"""
        # Treeview za prikaz grupa
        columns = ('Broj', 'Tip', 'Broj datoteka', 'Prosječna sličnost', 'Ušteda prostora')
        self.results_tree = ttk.Treeview(parent, columns=columns, show='headings', height=15)
        
        # Kolone
        self.results_tree.heading('Broj', text='#')
        self.results_tree.heading('Tip', text='Tip')
        self.results_tree.heading('Broj datoteka', text='Broj datoteka')
        self.results_tree.heading('Prosječna sličnost', text='Sličnost')
        self.results_tree.heading('Ušteda prostora', text='Ušteda')
        
        self.results_tree.column('Broj', width=50)
        self.results_tree.column('Tip', width=100)
        self.results_tree.column('Broj datoteka', width=100)
        self.results_tree.column('Prosječna sličnost', width=100)
        self.results_tree.column('Ušteda prostora', width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click
        self.results_tree.bind('<Double-1>', self.on_result_double_click)
        
    def setup_settings_tab(self, notebook):
        """Tab sa postavkama"""
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="⚙️ Postavke")
        
        # Postavke sličnosti
        similarity_frame = ttk.LabelFrame(settings_frame, text="📐 Postavke sličnosti", padding=15)
        similarity_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Slider za slike
        img_frame = ttk.Frame(similarity_frame)
        img_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(img_frame, text="Prag sličnosti za slike:").pack(side=tk.LEFT)
        self.img_slider = ttk.Scale(img_frame, from_=0, to=100, 
                                   variable=self.similarity_threshold_images,
                                   orient=tk.HORIZONTAL)
        self.img_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.img_value_label = ttk.Label(img_frame, text="85%")
        self.img_value_label.pack(side=tk.LEFT)
        
        # Slider za videe
        vid_frame = ttk.Frame(similarity_frame)
        vid_frame.pack(fill=tk.X)
        
        ttk.Label(vid_frame, text="Prag sličnosti za videe:").pack(side=tk.LEFT)
        self.vid_slider = ttk.Scale(vid_frame, from_=0, to=100,
                                   variable=self.similarity_threshold_videos,
                                   orient=tk.HORIZONTAL)
        self.vid_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 10))
        self.vid_value_label = ttk.Label(vid_frame, text="85%")
        self.vid_value_label.pack(side=tk.LEFT)
        
        # Bind slider promjene
        self.img_slider.bind('<Motion>', lambda e: self.update_slider_labels())
        self.vid_slider.bind('<Motion>', lambda e: self.update_slider_labels())
        
        # Ostale postavke
        options_frame = ttk.LabelFrame(settings_frame, text="⚡ Opcije skeniranja", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(options_frame, text="Napravi backup prije brisanja", 
                       variable=self.create_backup).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(options_frame, text="Pitaj za brisanje nakon skeniranja", 
                       variable=self.delete_after_scan).pack(anchor=tk.W, pady=2)
        
        # Reset dugme
        reset_frame = ttk.Frame(settings_frame)
        reset_frame.pack(fill=tk.X)
        
        ttk.Button(reset_frame, text="🔄 Resetiraj postavke", 
                  command=self.reset_settings).pack(side=tk.LEFT)
        
    def setup_compare_tab(self, notebook):
        """Tab za vizualnu usporedbu"""
        compare_frame = ttk.Frame(notebook)
        notebook.add(compare_frame, text="👁️ Usporedba")
        
        # Panel za prikaz sličnih datoteka
        self.compare_text = scrolledtext.ScrolledText(compare_frame, height=20, 
                                                     font=('Consolas', 10))
        self.compare_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.compare_text.insert(tk.END, "Odaberite grupu za usporedbu...")
        self.compare_text.configure(state='disabled')
        
    def setup_status_bar(self, parent):
        """Postavi status bar"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Spreman", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress = ttk.Progressbar(status_frame, mode='indeterminate', length=200)
        self.progress.pack(side=tk.RIGHT, padx=(10, 0))
        
    def browse_folder(self):
        """Odaberi mapu za skeniranje"""
        folder = filedialog.askdirectory(title="Odaberite mapu za skeniranje")
        if folder:
            self.selected_folder.set(folder)
            
    def start_scan(self):
        """Pokreni skeniranje"""
        folder = self.selected_folder.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Greška", "Molimo odaberite ispravnu mapu!")
            return
        
        # Očisti prethodne rezultate
        self.clear_results()
        
        # Prikaži progress
        self.is_scanning = True
        self.status_label.config(text="🔍 Skeniranje u tijeku...")
        self.progress.start()
        
        # Pokreni u threadu
        scan_thread = threading.Thread(target=self.perform_scan, args=(folder,))
        scan_thread.daemon = True
        scan_thread.start()
        
    def perform_scan(self, folder):
        """Izvrši skeniranje u pozadini"""
        try:
            start_time = time.time()
            
            # Pronađi sve medijske datoteke
            all_files = []
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = Path(root) / file
                    if self.is_image_file(file_path) or self.is_video_file(file_path):
                        all_files.append(file_path)
            
            # Računanje hash-ova i grupiranje
            similar_images, similar_videos = self.find_duplicates(all_files, folder)
            
            # Spremi rezultate
            self.similar_images = similar_images
            self.similar_videos = similar_videos
            
            # Ažuriraj UI na glavnom threadu
            self.root.after(0, self.update_results_ui, start_time)
            
        except Exception as e:
            self.root.after(0, self.scan_error, str(e))
            
    def find_duplicates(self, files, base_folder):
        """Pronađi duplikate"""
        # Grupiranje po veličini (brza provjera)
        size_groups = defaultdict(list)
        for file in files:
            try:
                size = file.stat().st_size
                size_groups[size].append(file)
            except:
                pass
        
        # Daljnja analiza unutar grupa s istom veličinom
        similar_images = []
        similar_videos = []
        
        for size, file_group in size_groups.items():
            if len(file_group) > 1:
                # Provjeri sličnost unutar grupe
                for i in range(len(file_group)):
                    for j in range(i + 1, len(file_group)):
                        file1 = file_group[i]
                        file2 = file_group[j]
                        
                        if self.is_image_file(file1) and self.is_image_file(file2):
                            similarity = self.compare_images(file1, file2)
                            if similarity >= self.similarity_threshold_images.get():
                                self.add_to_groups(similar_images, file1, file2, similarity)
                                
                        elif self.is_video_file(file1) and self.is_video_file(file2):
                            similarity = self.compare_videos(file1, file2)
                            if similarity >= self.similarity_threshold_videos.get():
                                self.add_to_groups(similar_videos, file1, file2, similarity)
        
        return similar_images, similar_videos
    
    def add_to_groups(self, groups, file1, file2, similarity):
        """Dodaj datoteke u grupe sličnosti"""
        found_group = None
        for group in groups:
            if file1 in group['files'] or file2 in group['files']:
                found_group = group
                break
        
        if found_group:
            found_group['files'].update([file1, file2])
            found_group['similarities'].append(similarity)
        else:
            groups.append({
                'files': {file1, file2},
                'similarities': [similarity],
                'type': 'image' if self.is_image_file(file1) else 'video'
            })
    
    def compare_images(self, img1, img2):
        """Usporedi dvije slike"""
        try:
            # Perceptual hash metoda
            with Image.open(img1) as im1, Image.open(img2) as im2:
                # Resize za bržu obradu
                im1 = im1.resize((32, 32)).convert('L')
                im2 = im2.resize((32, 32)).convert('L')
                
                # Average hash
                hash1 = imagehash.average_hash(im1)
                hash2 = imagehash.average_hash(im2)
                
                # Izračunaj sličnost
                similarity = 100 - (hash1 - hash2) * 100 / 64
                return max(0, min(100, similarity))
        except:
            return 0
    
    def compare_videos(self, vid1, vid2):
        """Usporedi dva videa (pojednostavljeno)"""
        try:
            # Uzmi samo prvi frame za usporedbu
            cap1 = cv2.VideoCapture(str(vid1))
            cap2 = cv2.VideoCapture(str(vid2))
            
            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()
            
            cap1.release()
            cap2.release()
            
            if ret1 and ret2:
                # Resize i convert to grayscale
                frame1 = cv2.resize(frame1, (32, 32))
                frame2 = cv2.resize(frame2, (32, 32))
                
                gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
                
                # MSE (Mean Squared Error)
                mse = np.mean((gray1 - gray2) ** 2)
                if mse == 0:
                    return 100
                
                # PSNR (Peak Signal to Noise Ratio)
                psnr = 20 * np.log10(255 / np.sqrt(mse))
                similarity = min(100, psnr * 2)  # Normalizacija
                return similarity
        except:
            pass
        
        return 0
    
    def update_results_ui(self, start_time):
        """Ažuriraj UI nakon skeniranja"""
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Stopiraj progress
        self.progress.stop()
        self.is_scanning = False
        
        # Ažuriraj statuse
        total_duplicates = len(self.similar_images) + len(self.similar_videos)
        self.total_label.config(text=str(total_duplicates))
        self.images_label.config(text=f"{len(self.similar_images)} grupa")
        self.videos_label.config(text=f"{len(self.similar_videos)} grupa")
        
        # Formatiraj vrijeme
        hours, remainder = divmod(int(elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Popuni treeview
        self.populate_results_tree()
        
        # Ažuriraj status
        self.status_label.config(text=f"Skeniranje završeno. Pronađeno {total_duplicates} grupa duplikata.")
        
        # Pitaj za brisanje ako je opcija uključena
        if self.delete_after_scan.get() and total_duplicates > 0:
            self.root.after(100, self.prompt_for_deletion)
    
    def populate_results_tree(self):
        """Popuni treeview sa rezultatima"""
        # Očisti postojeće
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        group_number = 1
        
        # Dodaj slike
        for group in self.similar_images:
            file_count = len(group['files'])
            avg_similarity = np.mean(group['similarities']) if group['similarities'] else 0
            space_saved = self.calculate_space_saving(group['files'])
            
            self.results_tree.insert('', 'end', 
                values=(group_number, '🖼️ Slike', file_count, 
                       f"{avg_similarity:.1f}%", space_saved),
                tags=('image_group',))
            group_number += 1
        
        # Dodaj videe
        for group in self.similar_videos:
            file_count = len(group['files'])
            avg_similarity = np.mean(group['similarities']) if group['similarities'] else 0
            space_saved = self.calculate_space_saving(group['files'])
            
            self.results_tree.insert('', 'end',
                values=(group_number, '🎬 Video', file_count,
                       f"{avg_similarity:.1f}%", space_saved),
                tags=('video_group',))
            group_number += 1
        
        # Postavi tagove za bojenje
        self.results_tree.tag_configure('image_group', background='#e8f4f8')
        self.results_tree.tag_configure('video_group', background='#f8e8f4')
    
    def calculate_space_saving(self, files):
        """Izračunaj potencijalnu uštedu prostora"""
        sizes = []
        for file in files:
            try:
                sizes.append(file.stat().st_size)
            except:
                pass
        
        if not sizes:
            return "0 B"
        
        # Pretpostavka: zadržavamo 1 datoteku, brišemo ostale
        max_size = max(sizes)
        total_size = sum(sizes)
        saved = total_size - max_size
        
        return self.format_size(saved)
    
    def format_size(self, size_bytes):
        """Formatiraj veličinu"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {units[i]}"
    
    def clear_results(self):
        """Očisti sve rezultate"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        self.similar_images = []
        self.similar_videos = []
        self.total_label.config(text="0")
        self.images_label.config(text="0 grupa")
        self.videos_label.config(text="0 grupa")
        self.time_label.config(text="00:00:00")
        self.avg_similarity_label.config(text="0%")
        
        self.compare_text.configure(state='normal')
        self.compare_text.delete(1.0, tk.END)
        self.compare_text.insert(tk.END, "Odaberite grupu za usporedbu...")
        self.compare_text.configure(state='disabled')
    
    def update_slider_labels(self):
        """Ažuriraj labele za slidere"""
        self.img_value_label.config(text=f"{self.similarity_threshold_images.get():.0f}%")
        self.vid_value_label.config(text=f"{self.similarity_threshold_videos.get():.0f}%")
    
    def is_image_file(self, file_path):
        """Provjeri je li datoteka slika"""
        return file_path.suffix.lower() in self.image_extensions
    
    def is_video_file(self, file_path):
        """Provjeri je li datoteka video"""
        return file_path.suffix.lower() in self.video_extensions
    
    def on_result_double_click(self, event):
        """Klik na rezultat u treeview"""
        selection = self.results_tree.selection()
        if not selection:
            return
        
        item = self.results_tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 2:
            group_index = values[0] - 1
            group_type = values[1]
            
            if '🖼️' in group_type and group_index < len(self.similar_images):
                self.show_group_details(self.similar_images[group_index], 'image')
            elif '🎬' in group_type and (group_index - len(self.similar_images)) < len(self.similar_videos):
                adjusted_index = group_index - len(self.similar_images)
                self.show_group_details(self.similar_videos[adjusted_index], 'video')
    
    def show_group_details(self, group, group_type):
        """Prikaži detalje grupe"""
        self.compare_text.configure(state='normal')
        self.compare_text.delete(1.0, tk.END)
        
        # Header
        icon = "🖼️" if group_type == 'image' else "🎬"
        self.compare_text.insert(tk.END, f"{icon} Detalji grupe\n")
        self.compare_text.insert(tk.END, "=" * 50 + "\n\n")
        
        # Datoteke
        self.compare_text.insert(tk.END, "📁 Datoteke u grupi:\n")
        for i, file in enumerate(group['files'], 1):
            try:
                size = self.format_size(file.stat().st_size)
                self.compare_text.insert(tk.END, f"{i}. {file.name} ({size})\n")
                self.compare_text.insert(tk.END, f"   📍 {file}\n\n")
            except:
                self.compare_text.insert(tk.END, f"{i}. {file.name} (nepoznata veličina)\n\n")
        
        # Sličnosti
        if group.get('similarities'):
            avg = np.mean(group['similarities'])
            self.compare_text.insert(tk.END, f"\n📊 Prosječna sličnost: {avg:.1f}%\n")
        
        self.compare_text.configure(state='disabled')
    
    def show_duplicate_manager(self):
        """Prikaži upravljač duplikatima"""
        if not self.similar_images and not self.similar_videos:
            messagebox.showinfo("Info", "Nema duplikata za upravljanje.")
            return
        
        manager = DuplicateManager(self.root, self.similar_images + self.similar_videos)
        self.root.wait_window(manager.window)
    
    def show_detailed_report(self):
        """Prikaži detaljan izvještaj"""
        if not self.similar_images and not self.similar_videos:
            messagebox.showinfo("Info", "Nema rezultata za izvještaj.")
            return
        
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 Detaljan izvještaj")
        report_window.geometry("800x600")
        
        report_text = scrolledtext.ScrolledText(report_window, font=('Consolas', 10))
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Generiraj izvještaj
        report = self.generate_report()
        report_text.insert(tk.END, report)
        report_text.configure(state='disabled')
        
        # Dugmad
        button_frame = ttk.Frame(report_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="💾 Spremi izvještaj", 
                  command=lambda: self.save_report(report)).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="📋 Kopiraj", 
                  command=lambda: self.copy_to_clipboard(report)).pack(side=tk.LEFT, padx=(10, 0))
    
    def generate_report(self):
        """Generiraj detaljan izvještaj"""
        report = "=" * 60 + "\n"
        report += "NAPRAVNJENI IZVJEŠTAJ O DUPLIKATIMA\n"
        report += "=" * 60 + "\n\n"
        
        report += f"Datum: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Mapa: {self.selected_folder.get()}\n"
        report += f"Prag slika: {self.similarity_threshold_images.get():.0f}%\n"
        report += f"Prag video: {self.similarity_threshold_videos.get():.0f}%\n"
        report += "\n" + "=" * 60 + "\n\n"
        
        # Ukupno
        total_groups = len(self.similar_images) + len(self.similar_videos)
        total_files = sum(len(g['files']) for g in self.similar_images + self.similar_videos)
        report += f"UKUPNO: {total_groups} grupa, {total_files} datoteka\n\n"
        
        # Slike
        if self.similar_images:
            report += "🖼️ SLIČNE SLIKE\n"
            report += "-" * 40 + "\n"
            
            for i, group in enumerate(self.similar_images, 1):
                file_count = len(group['files'])
                avg_sim = np.mean(group['similarities']) if group['similarities'] else 0
                
                report += f"\nGrupa {i}: {file_count} slika, {avg_sim:.1f}% sličnost\n"
                
                for j, file in enumerate(group['files'], 1):
                    try:
                        size = self.format_size(file.stat().st_size)
                        report += f"  {j}. {file.name} ({size})\n"
                    except:
                        report += f"  {j}. {file.name}\n"
            
            report += "\n"
        
        # Videi
        if self.similar_videos:
            report += "🎬 SLIČNI VIDEOZAPISI\n"
            report += "-" * 40 + "\n"
            
            for i, group in enumerate(self.similar_videos, 1):
                file_count = len(group['files'])
                avg_sim = np.mean(group['similarities']) if group['similarities'] else 0
                
                report += f"\nGrupa {i}: {file_count} videa, {avg_sim:.1f}% sličnost\n"
                
                for j, file in enumerate(group['files'], 1):
                    try:
                        size = self.format_size(file.stat().st_size)
                        report += f"  {j}. {file.name} ({size})\n"
                    except:
                        report += f"  {j}. {file.name}\n"
        
        # Potencijalna ušteda
        report += "\n" + "=" * 60 + "\n"
        report += "POTENCIJALNA UŠTEDA PROSTORA\n"
        report += "-" * 40 + "\n"
        
        total_saving = 0
        for group in self.similar_images + self.similar_videos:
            sizes = []
            for file in group['files']:
                try:
                    sizes.append(file.stat().st_size)
                except:
                    pass
            
            if sizes:
                max_size = max(sizes)
                total_size = sum(sizes)
                total_saving += total_size - max_size
        
        report += f"Ukupna ušteda: {self.format_size(total_saving)}\n"
        report += "=" * 60 + "\n"
        
        return report
    
    def save_report(self, report):
        """Spremi izvještaj u datoteku"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Tekst datoteke", "*.txt"), ("Sve datoteke", "*.*")],
            initialfile=f"izvjestaj_duplikati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                messagebox.showinfo("Uspjeh", "Izvještaj je spremljen!")
            except Exception as e:
                messagebox.showerror("Greška", f"Ne mogu spremiti datoteku: {e}")
    
    def copy_to_clipboard(self, text):
        """Kopiraj tekst u clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Info", "Tekst kopiran u clipboard!")
    
    def export_results(self):
        """Izvezi rezultate u JSON format"""
        if not self.similar_images and not self.similar_videos:
            messagebox.showinfo("Info", "Nema rezultata za izvoz.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON datoteke", "*.json"), ("Sve datoteke", "*.*")],
            initialfile=f"duplikati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                # Pripremi podatke za JSON
                export_data = {
                    'scan_date': datetime.now().isoformat(),
                    'folder': self.selected_folder.get(),
                    'settings': {
                        'image_threshold': self.similarity_threshold_images.get(),
                        'video_threshold': self.similarity_threshold_videos.get()
                    },
                    'results': {
                        'similar_images': [
                            {
                                'files': [str(f) for f in group['files']],
                                'similarities': group['similarities']
                            }
                            for group in self.similar_images
                        ],
                        'similar_videos': [
                            {
                                'files': [str(f) for f in group['files']],
                                'similarities': group['similarities']
                            }
                            for group in self.similar_videos
                        ]
                    }
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Uspjeh", "Rezultati su izvezeni u JSON format!")
            except Exception as e:
                messagebox.showerror("Greška", f"Ne mogu spremiti datoteku: {e}")
    
    def prompt_for_deletion(self):
        """Pitaj korisnika želi li obrisati duplikate"""
        response = messagebox.askyesno(
            "Upravljanje duplikatima",
            "Želite li upravljati pronađenim duplikatima?\n\n"
            "Možete birati koje datoteke zadržati, a koje obrisati."
        )
        
        if response:
            self.show_duplicate_manager()
    
    def reset_settings(self):
        """Resetiraj postavke na default"""
        self.similarity_threshold_images.set(85.0)
        self.similarity_threshold_videos.set(85.0)
        self.delete_after_scan.set(False)
        self.create_backup.set(True)
        self.update_slider_labels()
        messagebox.showinfo("Info", "Postavke su resetirane!")
    
    def scan_error(self, error_msg):
        """Prikaži grešku skeniranja"""
        self.progress.stop()
        self.is_scanning = False
        self.status_label.config(text="Greška pri skeniranju")
        messagebox.showerror("Greška skeniranja", f"Došlo je do greške:\n\n{error_msg}")


class DuplicateManager:
    """Prozor za upravljanje duplikatima"""
    
    def __init__(self, parent, duplicate_groups):
        self.parent = parent
        self.duplicate_groups = duplicate_groups
        
        self.window = tk.Toplevel(parent)
        self.window.title("🗑️ Upravljanje duplikatima")
        self.window.geometry("900x700")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Postavi UI upravljača"""
        # Naslov
        title_frame = ttk.Frame(self.window)
        title_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        ttk.Label(title_frame, text="🗑️ Upravljanje duplikatima", 
                 font=('Segoe UI', 14, 'bold')).pack()
        
        ttk.Label(title_frame, text="Odaberite datoteke koje želite zadržati:", 
                 font=('Segoe UI', 10)).pack(pady=(5, 0))
        
        # Notebook za grupe
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Kreiraj tabove za svaku grupu
        self.group_pages = []
        self.selection_vars = []
        
        for i, group in enumerate(self.duplicate_groups, 1):
            self.create_group_tab(group, i)
        
        # Kontrolni panel
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        ttk.Button(control_frame, text="✅ Potvrdi odabir", 
                  command=self.confirm_selection, style='Accent.TButton').pack(side=tk.LEFT)
        
        ttk.Button(control_frame, text="📋 Kopiraj u folder", 
                  command=self.copy_to_folder).pack(side=tk.LEFT, padx=(10, 0))
        
        ttk.Button(control_frame, text="❌ Odustani", 
                  command=self.window.destroy).pack(side=tk.RIGHT)
    
    def create_group_tab(self, group, group_number):
        """Kreiraj tab za jednu grupu"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=f"Grupa {group_number}")
        
        # Header
        header_frame = ttk.Frame(tab_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        icon = "🖼️" if self.is_image_group(group) else "🎬"
        ttk.Label(header_frame, text=f"{icon} Grupa {group_number}: {len(group['files'])} datoteka", 
                 font=('Segoe UI', 11, 'bold')).pack(anchor=tk.W)
        
        if group.get('similarities'):
            avg = np.mean(group['similarities'])
            ttk.Label(header_frame, text=f"Prosječna sličnost: {avg:.1f}%").pack(anchor=tk.W)
        
        # Frame za datoteke
        files_frame = ttk.LabelFrame(tab_frame, text="Datoteke u grupi")
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista datoteka
        listbox_frame = ttk.Frame(files_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.group_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE,
                                       yscrollcommand=scrollbar.set,
                                       font=('Consolas', 9))
        self.group_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.group_listbox.yview)
        
        # Popuni listbox
        group_vars = []
        files = list(group['files'])
        for i, file in enumerate(files):
            try:
                size = self.format_size(file.stat().st_size)
                display_text = f"{i+1}. {file.name} ({size})"
            except:
                display_text = f"{i+1}. {file.name}"
            
            self.group_listbox.insert(tk.END, display_text)
            group_vars.append(file)
        
        self.group_pages.append(files)
        
        # Selekcija
        selection_frame = ttk.Frame(tab_frame)
        selection_frame.pack(fill=tk.X, pady=(10, 0))
        
        var = tk.IntVar(value=0)  # Default prva datoteka
        self.selection_vars.append(var)
        
        ttk.Radiobutton(selection_frame, text="Zadržaj ovu datoteku:", 
                       variable=var, value=0).pack(side=tk.LEFT)
        
        ttk.Label(selection_frame, text="(Prva je najveća)").pack(side=tk.LEFT, padx=(5, 0))
    
    def is_image_group(self, group):
        """Provjeri je li grupa slika"""
        files = list(group['files'])
        if not files:
            return False
        
        # Provjeri ekstenziju prve datoteke
        ext = files[0].suffix.lower()
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        return ext in image_exts
    
    def format_size(self, size_bytes):
        """Formatiraj veličinu"""
        if size_bytes == 0:
            return "0 B"
        
        units = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(units) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {units[i]}"
    
    def confirm_selection(self):
        """Potvrdi odabir i izvrši brisanje"""
        files_to_keep = []
        files_to_delete = []
        
        for i, (group, var) in enumerate(zip(self.group_pages, self.selection_vars)):
            selection = var.get()
            if 0 <= selection < len(group):
                keep_file = group[selection]
                files_to_keep.append(keep_file)
                
                # Dodaj ostale za brisanje
                for j, file in enumerate(group):
                    if j != selection:
                        files_to_delete.append(file)
        
        if not files_to_delete:
            messagebox.showinfo("Info", "Nema datoteka za brisanje.")
            return
        
        # Prikaži potvrdu
        delete_count = len(files_to_delete)
        total_saved = sum(f.stat().st_size for f in files_to_delete if f.exists())
        
        confirm = messagebox.askyesno(
            "Potvrda brisanja",
            f"Želite li obrisati {delete_count} datoteka?\n\n"
            f"Ušteda prostora: {self.format_size(total_saved)}\n\n"
            "⚠️ Ova akcija se ne može poništiti!"
        )
        
        if confirm:
            self.delete_files(files_to_delete)
            self.window.destroy()
            messagebox.showinfo("Uspjeh", f"Obrisano {delete_count} datoteka!")
    
    def delete_files(self, files):
        """Obriši datoteke"""
        for file in files:
            try:
                if file.exists():
                    file.unlink()
            except Exception as e:
                print(f"Greška pri brisanju {file}: {e}")
    
    def copy_to_folder(self):
        """Kopiraj duplikate u folder za usporedbu"""
        folder = filedialog.askdirectory(title="Odaberite folder za kopiranje")
        if not folder:
            return
        
        folder_path = Path(folder)
        
        try:
            # Kreiraj podfldere
            images_folder = folder_path / "Slike"
            videos_folder = folder_path / "Video"
            images_folder.mkdir(exist_ok=True)
            videos_folder.mkdir(exist_ok=True)
            
            copied_count = 0
            
            for group in self.duplicate_groups:
                files = list(group['files'])
                if not files:
                    continue
                
                # Odredi tip
                is_image = self.is_image_group({'files': files})
                target_folder = images_folder if is_image else videos_folder
                
                # Kopiraj s prefiksima
                for i, file in enumerate(files):
                    if file.exists():
                        prefix = chr(65 + i % 26)  # A, B, C, ...
                        new_name = f"{prefix}_{file.name}"
                        target_path = target_folder / new_name
                        
                        try:
                            shutil.copy2(file, target_path)
                            copied_count += 1
                        except Exception as e:
                            print(f"Greška pri kopiranju {file}: {e}")
            
            messagebox.showinfo("Uspjeh", f"Kopirano {copied_count} datoteka u folder!")
            
        except Exception as e:
            messagebox.showerror("Greška", f"Ne mogu kopirati datoteke: {e}")


def main():
    """Pokreni aplikaciju"""
    root = tk.Tk()
    app = ModernDuplicateFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()