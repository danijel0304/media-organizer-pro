import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image
from PIL.ExifTags import TAGS
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *

class PhotoOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Organizer Pro")
        self.root.geometry("900x700")
        
        # Stilizacija
        self.style = ttkb.Style("darkly")
        
        # Varijable
        self.source_folder = tk.StringVar()
        self.dest_folder = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Spreman za početak")
        self.photo_count_var = tk.StringVar(value="Pronađeno slika: 0")
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
            text="📸 Photo Organizer Pro",
            font=("Helvetica", 24, "bold"),
            foreground="#4a9eff"
        )
        title_label.pack()
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Organizujte fotografije po godini snimanja",
            font=("Helvetica", 12),
            foreground="#aaa"
        )
        subtitle_label.pack()
        
        # Okvir za unos putanja
        input_frame = ttk.LabelFrame(main_frame, text="🔍 Izvori i odredišta", padding=15)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Izvor
        ttk.Label(input_frame, text="Izvor fotografija:", font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        
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
        
        # Levo: broj slika
        count_label = ttk.Label(
            stats_frame,
            textvariable=self.photo_count_var,
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
        
        # Okvir za dugmad
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.analyze_btn = ttk.Button(
            button_frame,
            text="🔍 Analiziraj fotografije",
            command=self.analyze_photos,
            bootstyle=INFO,
            width=20
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.organize_btn = ttk.Button(
            button_frame,
            text="📁 Organizuj fotografije",
            command=self.organize_photos,
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
        
        # Stablo za prikaz godina i slika
        self.tree = ttk.Treeview(
            self.year_frame,
            columns=("count", "size"),
            show="tree headings",
            height=15
        )
        
        self.tree.heading("#0", text="Godina", anchor=tk.W)
        self.tree.heading("count", text="Broj slika", anchor=tk.W)
        self.tree.heading("size", text="Prva slika", anchor=tk.W)
        
        self.tree.column("#0", width=200)
        self.tree.column("count", width=150)
        self.tree.column("size", width=300)
        
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
        
        # Tab 3: Slike bez datuma
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
        self.image_files = []
        self.photos_by_year = {}
        self.photos_without_date = []
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="Odaberite folder sa fotografijama")
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
        self.photos_by_year = {}
        self.photos_without_date = []
        self.image_files = []
        
    def get_date_taken(self, image_path):
        try:
            with Image.open(image_path) as image:
                exifdata = image.getexif()
                
                date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
                
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in date_tags:
                        date_str = exifdata.get(tag_id)
                        if date_str:
                            try:
                                date_obj = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                                return date_obj.year
                            except ValueError:
                                continue
                
                return None
        except Exception as e:
            self.log_message(f"Greška pri čitanju EXIF podataka za {os.path.basename(image_path)}: {str(e)}")
            return None
    
    def get_file_creation_date(self, file_path):
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
    
    def get_image_files(self, folder_path):
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.raw', '.cr2', '.nef'}
        image_files = []
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if Path(file).suffix.lower() in image_extensions:
                        full_path = os.path.join(root, file)
                        image_files.append(full_path)
        except Exception as e:
            self.log_message(f"Greška pri čitanju foldera {folder_path}: {str(e)}")
        
        return image_files
    
    def analyze_photos_thread(self):
        self.organize_in_progress = True
        self.analyze_btn.configure(state=tk.DISABLED)
        
        try:
            self.clear_data()
            source = self.source_folder.get()
            dest = self.dest_folder.get()
            
            if not source or not os.path.exists(source):
                messagebox.showerror("Greška", "Molimo odaberite validan izvorni folder!")
                return
                
            if not dest:
                messagebox.showerror("Greška", "Molimo odaberite odredišni folder!")
                return
            
            self.update_status("Tražim slike...")
            self.image_files = self.get_image_files(source)
            
            self.photo_count_var.set(f"Pronađeno slika: {len(self.image_files)}")
            
            if not self.image_files:
                self.update_status("Nema slika za obradu!")
                return
            
            self.update_status("Analiziram datume snimanja...")
            self.photos_by_year = {}
            self.photos_without_date = []
            
            for i, img_path in enumerate(self.image_files, 1):
                if not self.organize_in_progress:
                    break
                    
                # Update progress
                progress = (i / len(self.image_files)) * 100
                self.progress_var.set(progress)
                
                # Get year
                year = self.get_date_taken(img_path)
                
                if year is None:
                    year = self.get_file_creation_date(img_path)
                
                if year:
                    if year not in self.photos_by_year:
                        self.photos_by_year[year] = []
                    self.photos_by_year[year].append(img_path)
                else:
                    self.photos_without_date.append(img_path)
                
                if i % 10 == 0:
                    self.update_status(f"Obrađeno {i}/{len(self.image_files)} slika")
            
            # Update treeview
            total_photos = 0
            for year in sorted(self.photos_by_year.keys()):
                count = len(self.photos_by_year[year])
                total_photos += count
                
                # Get first image name for display
                first_image = os.path.basename(self.photos_by_year[year][0]) if self.photos_by_year[year] else ""
                if len(first_image) > 30:
                    first_image = first_image[:27] + "..."
                
                self.tree.insert("", tk.END, text=str(year), values=(count, first_image))
            
            # Update no date list
            for img in self.photos_without_date:
                self.no_date_listbox.insert(tk.END, os.path.basename(img))
            
            self.update_status(f"Analiza završena. Pronađeno {total_photos} slika u {len(self.photos_by_year)} godina.")
            
            if total_photos > 0:
                self.organize_btn.configure(state=tk.NORMAL)
            
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {str(e)}")
            self.update_status(f"Greška: {str(e)}")
        finally:
            self.progress_var.set(0)
            self.organize_in_progress = False
            self.analyze_btn.configure(state=tk.NORMAL)
    
    def analyze_photos(self):
        if not self.source_folder.get():
            messagebox.showwarning("Upozorenje", "Molimo odaberite izvorni folder!")
            return
            
        thread = threading.Thread(target=self.analyze_photos_thread, daemon=True)
        thread.start()
    
    def organize_photos_thread(self):
        self.organize_in_progress = True
        self.analyze_btn.configure(state=tk.DISABLED)
        self.organize_btn.configure(state=tk.DISABLED)
        
        try:
            dest = self.dest_folder.get()
            
            if not self.photos_by_year:
                messagebox.showinfo("Informacija", "Nema slika za organizaciju!")
                return
            
            total_photos = sum(len(photos) for photos in self.photos_by_year.values())
            
            response = messagebox.askyesno(
                "Potvrda",
                f"Želite li organizovati {total_photos} slika u {len(self.photos_by_year)} godina?\n\nOdredište: {dest}"
            )
            
            if not response:
                self.update_status("Operacija otkazana od strane korisnika.")
                return
            
            self.update_status("Počinjem organizaciju fotografija...")
            
            moved_count = 0
            failed_count = 0
            
            for year_idx, (year, photo_list) in enumerate(sorted(self.photos_by_year.items())):
                if not self.organize_in_progress:
                    break
                
                self.update_status(f"Obrađujem godinu {year} ({len(photo_list)} slika)...")
                
                # Create year folder
                year_folder = os.path.join(dest, str(year))
                if not os.path.exists(year_folder):
                    try:
                        os.makedirs(year_folder)
                        self.log_message(f"Kreiran folder: {year_folder}")
                    except Exception as e:
                        self.log_message(f"Greška pri kreiranju foldera {year_folder}: {str(e)}")
                        failed_count += len(photo_list)
                        continue
                
                # Move photos
                for photo_idx, photo_path in enumerate(photo_list):
                    if not self.organize_in_progress:
                        break
                    
                    try:
                        filename = os.path.basename(photo_path)
                        
                        # Get unique filename
                        base_name, ext = os.path.splitext(filename)
                        counter = 1
                        new_filename = filename
                        
                        while os.path.exists(os.path.join(year_folder, new_filename)):
                            new_filename = f"{base_name}_{counter}{ext}"
                            counter += 1
                        
                        destination = os.path.join(year_folder, new_filename)
                        shutil.move(photo_path, destination)
                        
                        self.log_message(f"Premješteno: {filename} -> {year}/{new_filename}")
                        moved_count += 1
                        
                        # Update progress
                        total_processed = sum(len(list) for list in list(self.photos_by_year.values())[:year_idx]) + photo_idx + 1
                        progress = (total_processed / total_photos) * 100
                        self.progress_var.set(progress)
                        
                    except Exception as e:
                        self.log_message(f"Greška pri premještanju {os.path.basename(photo_path)}: {str(e)}")
                        failed_count += 1
            
            self.update_status(f"Organizacija završena!")
            
            if failed_count == 0:
                messagebox.showinfo(
                    "Uspeh",
                    f"Uspješno organizovano {moved_count} fotografija!"
                )
            else:
                messagebox.showwarning(
                    "Upozorenje",
                    f"Organizacija završena sa greškama.\n\nUspješno: {moved_count}\nNeuspješno: {failed_count}"
                )
            
        except Exception as e:
            messagebox.showerror("Greška", f"Došlo je do greške: {str(e)}")
            self.update_status(f"Greška: {str(e)}")
        finally:
            self.progress_var.set(0)
            self.organize_in_progress = False
            self.analyze_btn.configure(state=tk.NORMAL)
            self.organize_btn.configure(state=tk.DISABLED if not self.photos_by_year else tk.NORMAL)
    
    def organize_photos(self):
        if not self.dest_folder.get():
            messagebox.showwarning("Upozorenje", "Molimo odaberite odredišni folder!")
            return
            
        thread = threading.Thread(target=self.organize_photos_thread, daemon=True)
        thread.start()
    
    def on_closing(self):
        if self.organize_in_progress:
            if messagebox.askyesno("Potvrda", "Organizacija je u toku. Da li sigurno želite da zatvorite program?"):
                self.organize_in_progress = False
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    try:
        # Check for required packages
        import PIL
    except ImportError:
        messagebox.showerror(
            "Greška",
            "Potrebna je Pillow biblioteka!\n\nInstalirajte je sa:\npip install Pillow"
        )
        return
    
    try:
        # Try to import ttkbootstrap, fall back to standard tkinter if not available
        import ttkbootstrap
    except ImportError:
        messagebox.showwarning(
            "Upozorenje",
            "ttkbootstrap nije instaliran. Koristiće se standardni Tkinter stil.\n\nZa bolji izgled instalirajte:\npip install ttkbootstrap"
        )
        # Create basic tkinter window without ttkbootstrap
        root = tk.Tk()
        app = PhotoOrganizerGUI(root)
    else:
        # Use ttkbootstrap for better styling
        root = ttkb.Window(themename="darkly")
        app = PhotoOrganizerGUI(root)
    
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()