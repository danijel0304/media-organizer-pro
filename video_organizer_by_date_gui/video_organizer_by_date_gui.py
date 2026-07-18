import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import json
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

class VideoOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Organizer Pro")
        self.root.geometry("900x700")
        
        # Stilizacija
        self.style = ttkb.Style("darkly")
        
        # Varijable
        self.source_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Spreman za početak")
        self.video_count_var = tk.StringVar(value="Pronađeno video datoteka: 0")
        self.ffprobe_status_var = tk.StringVar(value="Provjeravam FFprobe...")
        self.organize_in_progress = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Glavni okvir
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Naslov
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(
            title_frame,
            text="🎬 Video Organizer Pro",
            font=("Helvetica", 24, "bold"),
            foreground="#FF6B6B"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Organizirajte video datoteke po godini snimanja",
            font=("Helvetica", 12),
            foreground="#aaa"
        )
        subtitle_label.pack()
        
        # Status FFprobe
        ffprobe_frame = ttk.Frame(main_frame)
        ffprobe_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.ffprobe_label = ttk.Label(
            ffprobe_frame,
            textvariable=self.ffprobe_status_var,
            font=("Helvetica", 10),
            foreground="#4ECDC4"
        )
        self.ffprobe_label.pack()
        
        # Okvir za unos putanja
        input_frame = ttk.LabelFrame(main_frame, text="📁 Izvori i odredišta", padding=15)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Izvor
        ttk.Label(input_frame, text="Izvor video datoteka:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        source_entry = ttk.Entry(input_frame, textvariable=self.source_folder, width=50, font=("Helvetica", 10))
        source_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        source_btn = ttk.Button(
            input_frame,
            text="Odaberi folder",
            command=self.browse_source,
            bootstyle=SECONDARY
        )
        source_btn.grid(row=0, column=2, padx=5)
        
        # Odredište
        ttk.Label(input_frame, text="Odredišni folder:", font=("Helvetica", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        dest_entry = ttk.Entry(input_frame, textvariable=self.dest_folder, width=50, font=("Helvetica", 10))
        dest_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        dest_btn = ttk.Button(
            input_frame,
            text="Odaberi folder",
            command=self.browse_dest,
            bootstyle=SECONDARY
        )
        dest_btn.grid(row=1, column=2, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Status i statistika
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Levo: broj video datoteka
        count_label = ttk.Label(
            stats_frame,
            textvariable=self.video_count_var,
            font=("Helvetica", 10, "bold"),
            foreground="#4CAF50"
        )
        count_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Desno: status
        status_label = ttk.Label(
            stats_frame,
            textvariable=self.status_var,
            font=("Helvetica", 10),
            foreground="#FF9800"
        )
        status_label.pack(side=tk.RIGHT)
        
        # Okvir za gumbe
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.analyze_btn = ttk.Button(
            button_frame,
            text="🔍 Analiziraj video datoteke",
            command=self.analyze_videos,
            bootstyle=INFO,
            width=20
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.organize_btn = ttk.Button(
            button_frame,
            text="📁 Organiziraj video datoteke",
            command=self.organize_videos,
            bootstyle=SUCCESS,
            width=20,
            state=tk.DISABLED
        )
        self.organize_btn.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            bootstyle=STRIPED
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 20))
        
        # Tabovi za prikaz podataka
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Pregled po godinama
        self.year_frame = ttk.Frame(notebook)
        notebook.add(self.year_frame, text="📊 Pregled po godinama")
        
        # Stablo za prikaz godina i video datoteka
        self.tree = ttk.Treeview(
            self.year_frame,
            columns=("count", "first_video"),
            show="tree headings",
            height=15
        )
        
        self.tree.heading("#0", text="Godina", anchor=tk.W)
        self.tree.heading("count", text="Broj video datoteka", anchor=tk.W)
        self.tree.heading("first_video", text="Prvi video", anchor=tk.W)
        
        self.tree.column("#0", width=200)
        self.tree.column("count", width=150)
        self.tree.column("first_video", width=300)
        
        scrollbar = ttk.Scrollbar(self.year_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: Detaljni log
        log_frame = ttk.Frame(notebook)
        notebook.add(log_frame, text="📝 Detaljni log")
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tab 3: Video datoteke bez datuma
        self.no_date_frame = ttk.Frame(notebook)
        notebook.add(self.no_date_frame, text="⚠️ Bez datuma")
        
        self.no_date_listbox = tk.Listbox(
            self.no_date_frame,
            font=("Helvetica", 10)
        )
        scrollbar2 = ttk.Scrollbar(self.no_date_frame, orient=tk.VERTICAL, command=self.no_date_listbox.yview)
        self.no_date_listbox.configure(yscrollcommand=scrollbar2.set)
        
        self.no_date_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Podaci
        self.video_files = []
        self.videos_by_year = {}
        self.videos_without_date = []
        self.ffprobe_available = False
        
        # Provjeri FFprobe
        self.check_ffprobe()
        
    def check_ffprobe(self):
        """Provjerava je li ffprobe dostupan"""
        def check():
            try:
                subprocess.run(['ffprobe', '-version'], capture_output=True, timeout=5, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.ffprobe_available = True
                self.ffprobe_status_var.set("✓ FFprobe je dostupan - mogu čitati video meta podatke")
            except (subprocess.SubprocessError, FileNotFoundError):
                self.ffprobe_available = False
                self.ffprobe_status_var.set("⚠ FFprobe nije dostupan - koristit ću samo datum datoteke")
        
        threading.Thread(target=check, daemon=True).start()
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="Odaberite folder s video datotekama")
        if folder:
            self.source_folder.set(folder)
            
    def browse_dest(self):
        folder = filedialog.askdirectory(title="Odaberite odredišni folder")
        if folder:
            self.dest_folder.set(folder)
    
    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_status(self, message):
        self.status_var.set(message)
        self.log_message(message)
        
    def clear_data(self):
        self.tree.delete(*self.tree.get_children())
        self.no_date_listbox.delete(0, tk.END)
        self.log_text.delete(1.0, tk.END)
        self.videos_by_year = {}
        self.videos_without_date = []
        self.video_files = []
        
    def get_video_creation_date_ffprobe(self, video_path):
        """Izvlači datum snimanja iz video meta podataka koristeći ffprobe"""
        try:
            cmd = [
                'ffprobe', 
                '-v', 'quiet',
                '-show_entries', 'format_tags=creation_time:stream_tags=creation_time',
                '-of', 'json',
                video_path
            ]
            
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=creation_flags)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Traži creation_time u format tags
                if 'format' in data and 'tags' in data['format']:
                    creation_time = data['format']['tags'].get('creation_time')
                    if creation_time:
                        return self.parse_creation_time(creation_time)
                
                # Traži creation_time u stream tags
                if 'streams' in data:
                    for stream in data['streams']:
                        if 'tags' in stream and 'creation_time' in stream['tags']:
                            creation_time = stream['tags']['creation_time']
                            if creation_time:
                                return self.parse_creation_time(creation_time)
            
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            return None
    
    def parse_creation_time(self, time_str):
        """Parsira različite formate creation_time"""
        try:
            # Ukloni 'Z' ili '+00:00' na kraju ako postoji
            time_str = time_str.replace('Z', '').split('+')[0].split('.')[0]
            
            # Pokušaj različite formate
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y:%m:%d %H:%M:%S',
                '%Y-%m-%d',
                '%Y:%m:%d'
            ]
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(time_str, fmt)
                    return date_obj.year
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def get_file_creation_date(self, file_path):
        """Vraća godinu kreiranja datoteke ako meta podaci nisu dostupni"""
        try:
            if os.name == 'nt':
                creation_time = os.path.getctime(file_path)
            else:
                stat = os.stat(file_path)
                creation_time = min(stat.st_mtime, stat.st_ctime)
            
            return datetime.fromtimestamp(creation_time).year
        except Exception as e:
            self.log_message(f"Greška pri čitanju datuma datoteke {os.path.basename(file_path)}: {str(e)}")
            return None
    
    def get_video_files(self, folder_path):
        """Pronalazi sve video datoteke u folderu i podfolderima"""
        video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
            '.3gp', '.3g2', '.f4v', '.asf', '.rm', '.rmvb', '.vob', '.ogv',
            '.mts', '.m2ts', '.ts', '.mxf', '.dv', '.divx', '.xvid'
        }
        video_files = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if Path(file).suffix.lower() in video_extensions:
                        full_path = os.path.join(root, file)
                        video_files.append(full_path)
        except Exception as e:
            self.log_message(f"Greška pri čitanju foldera {folder_path}: {str(e)}")
        
        return video_files
    
    def analyze_videos_thread(self):
        self.organize_in_progress = True
        self.analyze_btn.configure(state=tk.DISABLED)
        
        try:
            self.clear_data()
            source = self.source_folder.get()
            dest = self.dest_folder.get()
            
            if not source or not os.path.exists(source):
                messagebox.showerror("Greška", "Molimo odaberite valjan izvorni folder!")
                return
                
            if not dest:
                messagebox.showerror("Greška", "Molimo odaberite odredišni folder!")
                return
            
            self.update_status("Tražim video datoteke...")
            self.video_files = self.get_video_files(source)
            
            self.video_count_var.set(f"Pronađeno video datoteka: {len(self.video_files)}")
            
            if not self.video_files:
                self.update_status("Nema video datoteka za obradu!")
                return
            
            self.update_status("Analiziram datume snimanja...")
            self.videos_by_year = {}
            self.videos_without_date = []
            
            for i, video_path in enumerate(self.video_files, 1):
                if not self.organize_in_progress:
                    break
                    
                # Update progress
                progress = (i / len(self.video_files)) * 100
                self.progress_var.set(progress)
                
                # Get year
                year = None
                
                # Prvo pokušaj iz video meta podataka ako je ffprobe dostupan
                if self.ffprobe_available:
                    year = self.get_video_creation_date_ffprobe(video_path)
                
                # Ako nema meta podataka, koristi datum datoteke
                if year is None:
                    year = self.get_file_creation_date(video_path)
                
                if year:
                    if year not in self.videos_by_year:
                        self.videos_by_year[year] = []
                    self.videos_by_year[year].append(video_path)
                else:
                    self.videos_without_date.append(video_path)
                
                if i % 10 == 0:
                    self.update_status(f"Obrađeno {i}/{len(self.video_files)} video datoteka")
            
            # Update treeview
            total_videos = 0
            for year in sorted(self.videos_by_year.keys()):
                count = len(self.videos_by_year[year])
                total_videos += count
                
                # Get first video name for display
                first_video = os.path.basename(self.videos_by_year[year][0]) if self.videos_by_year[year] else ""
                if len(first_video) > 30:
                    first_video = first_video[:27] + "..."
                
                self.tree.insert("", tk.END, text=str(year), values=(count, first_video))
            
            # Update no date list
            for video in self.videos_without_date:
                self.no_date_listbox.insert(tk.END, os.path.basename(video))
            
            self.update_status(f"Analiza završena. Pronađeno {total_videos} video datoteka u {len(self.videos_by_year)} godina.")
            
            if total_videos > 0:
                self.organize_btn.configure(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {str(e)}")
            self.update_status(f"Greška: {str(e)}")
        finally:
            self.progress_var.set(0)
            self.organize_in_progress = False
            self.analyze_btn.configure(state=tk.NORMAL)
    
    def analyze_videos(self):
        if not self.source_folder.get():
            messagebox.showwarning("Upozorenje", "Molimo odaberite izvorni folder!")
            return
            
        thread = threading.Thread(target=self.analyze_videos_thread, daemon=True)
        thread.start()
    
    def organize_videos_thread(self):
        self.organize_in_progress = True
        self.analyze_btn.configure(state=tk.DISABLED)
        self.organize_btn.configure(state=tk.DISABLED)
        
        try:
            dest = self.dest_folder.get()
            
            if not self.videos_by_year:
                messagebox.showinfo("Informacija", "Nema video datoteka za organizaciju!")
                return
            
            total_videos = sum(len(videos) for videos in self.videos_by_year.values())
            
            response = messagebox.askyesno(
                "Potvrda",
                f"Želite li organizirati {total_videos} video datoteka u {len(self.videos_by_year)} godina?\n\nOdredište: {dest}"
            )
            
            if not response:
                self.update_status("Operacija otkazana od strane korisnika.")
                return
            
            self.update_status("Počinjem organizaciju video datoteka...")
            
            moved_count = 0
            failed_count = 0
            
            for year_idx, (year, video_list) in enumerate(sorted(self.videos_by_year.items())):
                if not self.organize_in_progress:
                    break
                
                self.update_status(f"Obrađujem godinu {year} ({len(video_list)} video datoteka)...")
                
                # Create year folder
                year_folder = os.path.join(dest, str(year))
                if not os.path.exists(year_folder):
                    try:
                        os.makedirs(year_folder)
                        self.log_message(f"Kreirana mapa: {year_folder}")
                    except Exception as e:
                        self.log_message(f"Greška pri kreiranju mape {year_folder}: {str(e)}")
                        failed_count += len(video_list)
                        continue
                
                # Move videos
                for video_idx, video_path in enumerate(video_list):
                    if not self.organize_in_progress:
                        break
                    
                    try:
                        filename = os.path.basename(video_path)
                        
                        # Get unique filename
                        base_name, ext = os.path.splitext(filename)
                        counter = 1
                        new_filename = filename
                        
                        while os.path.exists(os.path.join(year_folder, new_filename)):
                            new_filename = f"{base_name}_{counter}{ext}"
                            counter += 1
                        
                        destination = os.path.join(year_folder, new_filename)
                        shutil.move(video_path, destination)
                        
                        self.log_message(f"Premješteno: {filename} -> {year}/{new_filename}")
                        moved_count += 1
                        
                        # Update progress
                        total_processed = sum(len(lst) for lst in list(self.videos_by_year.values())[:year_idx]) + video_idx + 1
                        progress = (total_processed / total_videos) * 100
                        self.progress_var.set(progress)
                        
                    except Exception as e:
                        self.log_message(f"Greška pri premještanju {os.path.basename(video_path)}: {str(e)}")
                        failed_count += 1
            
            self.update_status(f"Organizacija završena!")
            
            if failed_count == 0:
                messagebox.showinfo(
                    "Uspjeh",
                    f"Uspješno organizirano {moved_count} video datoteka!"
                )
            else:
                messagebox.showwarning(
                    "Upozorenje",
                    f"Organizacija završena s greškama.\n\nUspješno: {moved_count}\nNeuspješno: {failed_count}"
                )
            
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {str(e)}")
            self.update_status(f"Greška: {str(e)}")
        finally:
            self.progress_var.set(0)
            self.organize_in_progress = False
            self.analyze_btn.configure(state=tk.NORMAL)
            self.organize_btn.configure(state=tk.DISABLED if not self.videos_by_year else tk.NORMAL)
    
    def organize_videos(self):
        if not self.dest_folder.get():
            messagebox.showwarning("Upozorenje", "Molimo odaberite odredišni folder!")
            return
            
        thread = threading.Thread(target=self.organize_videos_thread, daemon=True)
        thread.start()
    
    def on_closing(self):
        if self.organize_in_progress:
            if messagebox.askyesno("Potvrda", "Organizacija je u tijeku. Da li sigurno želite zatvoriti program?"):
                self.organize_in_progress = False
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    try:
        # Try to import ttkbootstrap, fall back to standard tkinter if not available
        import ttkbootstrap
    except ImportError:
        # Create basic tkinter window without ttkbootstrap
        root = tk.Tk()
        app = VideoOrganizerGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    else:
        # Use ttkbootstrap for better styling
        root = ttkb.Window(themename="darkly")
        app = VideoOrganizerGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()

if __name__ == "__main__":
    main()