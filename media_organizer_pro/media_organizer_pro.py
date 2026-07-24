#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Media Organizer Pro

Objedinjeni GUI alat za organizaciju fotografija i videa te za pronalazak
duplikata. Program je napravljen kao samostalna zamjena za odvojene skripte
koje su ranije bile u ovom workspaceu.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from PIL import Image
    from PIL.ExifTags import TAGS

    PIL_AVAILABLE = True
except Exception:
    Image = None
    TAGS = {}
    PIL_AVAILABLE = False

try:
    import imagehash

    IMAGEHASH_AVAILABLE = True
except Exception:
    imagehash = None
    IMAGEHASH_AVAILABLE = False

try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except Exception:
    cv2 = None
    np = None
    OPENCV_AVAILABLE = False


APP_NAME = "Media Organizer Pro"
APP_VERSION = "1.0.1"
GITHUB_REPO = "danijel0304/media-organizer-pro"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
PAYPAL_DONATE_URL = "https://paypal.me/danijel0304"
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".heic",
    ".raw",
    ".cr2",
    ".nef",
}
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".3gp",
    ".3g2",
    ".f4v",
    ".asf",
    ".rm",
    ".rmvb",
    ".vob",
    ".ogv",
    ".mts",
    ".m2ts",
    ".ts",
    ".mxf",
    ".dv",
    ".divx",
    ".xvid",
    ".mpg",
    ".mpeg",
}

TRANSLATIONS = {
    "en": {
        "language_label": "Language",
        "language_name": "English",
        "app_subtitle": "Organize photos and videos, detect duplicates, and check NAS/reference folders in one focused tool.",
        "ready": "Ready",
        "busy": "Working...",
        "wait_title": "Work in progress",
        "wait_message": "Please wait for the current operation to finish.",
        "choose": "Choose",
        "donate": "Support via PayPal",
        "donate_title": "PayPal Donate",
        "version_label": "Version {version}",
        "check_updates": "Update",
        "checking_updates": "Checking updates...",
        "update_available_title": "Update available",
        "update_available_msg": "A new Media Organizer Pro version is available.\n\nCurrent version: {current}\nNew version: {latest}\n\nOpen the download page?",
        "update_current_title": "Up to date",
        "update_current_msg": "You are using the latest version ({current}).",
        "update_failed_title": "Update check failed",
        "update_failed_msg": "I could not check for a new version. Check the internet connection and try again.",
        "update_in_progress_title": "Check in progress",
        "update_in_progress_msg": "The update check is already running.",
        "tab_dashboard": "Overview",
        "tab_photos": "Photos by date",
        "tab_videos": "Videos by date",
        "tab_duplicates": "Media duplicates",
        "tab_nas": "NAS/video check",
        "tab_report": "Report",
        "dashboard_desc": "Quick health check for optional dependencies and a summary of what this unified app improves.",
        "photos_desc": "Analyze photo dates from EXIF metadata or file dates, then copy or move files into dated folders.",
        "videos_desc": "Analyze video creation dates with FFprobe when available, then organize videos into dated folders.",
        "duplicates_desc": "Find exact and visually similar media groups, review them, copy comparison sets, move extras, or delete extras.",
        "nas_desc": "Compare a folder of videos against one or more reference/NAS folders by name or SHA-256 hash.",
        "report_desc": "Review, clear, or export the activity log from this session.",
        "available": "Available",
        "missing": "Missing",
        "dep_pillow": "photo dates and image hashes",
        "dep_imagehash": "more accurate similar-photo matching",
        "dep_opencv": "video frame preview/hash support",
        "dep_ffprobe": "video creation dates",
        "review_title": "What was unified and improved",
        "review_notes": [
            "One tabbed GUI instead of several separate scripts.",
            "File hashes are read in chunks, so large videos do not need to fit into memory.",
            "Visual photo matching no longer depends on files having the same size.",
            "The default organization action is copy, not move, for safer first use.",
            "Move/delete actions clean processed rows from result tables.",
            "Video dates use FFprobe when available, with file mtime as fallback.",
        ],
        "photos_title": "Photo organization",
        "videos_title": "Video organization",
        "source_folder": "Source folder",
        "destination_folder": "Destination folder",
        "choose_source": "Choose source folder",
        "choose_destination": "Choose destination folder",
        "include_subfolders": "Include subfolders",
        "copy_instead_move": "Copy instead of move",
        "isolate_duplicates": "Put exact duplicates into _duplicates",
        "output_structure": "Output structure",
        "group_year": "Year",
        "group_year_month": "Year/Month",
        "group_year_month_day": "Year/Month/Day",
        "analyze": "Analyze",
        "organize": "Organize",
        "group_preview": "Group preview",
        "folder_col": "Folder",
        "count_col": "Count",
        "size_col": "Size",
        "example_col": "Example file",
        "fallback_col": "File-date fallback",
        "duplicates_title": "Photo and video duplicates",
        "scan_folder": "Folder to scan",
        "choose_scan_folder": "Choose folder to scan",
        "scan_images": "Scan images",
        "scan_videos": "Scan videos",
        "exact_duplicates": "Exact duplicates (SHA-256)",
        "visual_images": "Visually similar images",
        "visual_videos": "Visually similar videos (slower)",
        "image_threshold": "Image similarity threshold (%)",
        "video_threshold": "Video similarity threshold (%)",
        "scan_duplicates": "Scan duplicates",
        "copy_groups": "Copy groups",
        "move_duplicates": "Move duplicates",
        "delete_duplicates": "Delete duplicates",
        "found_groups": "Found groups",
        "group_col": "Group",
        "type_col": "Type",
        "method_col": "Method",
        "similarity_col": "Similarity",
        "savings_col": "Potential savings",
        "keep_col": "Keep",
        "selected_group_details": "Selected group details",
        "file_col": "File",
        "path_col": "Path",
        "nas_title": "Check videos against reference folders",
        "reference_folders": "Reference/NAS folders",
        "add": "Add",
        "remove": "Remove",
        "check_folder": "Folder to check",
        "choose_check_folder": "Choose folder to check",
        "deep_sha": "Deep SHA-256 check",
        "scan_video_duplicates": "Scan video duplicates",
        "move_selected": "Move selected",
        "delete_selected": "Delete selected",
        "nas_results_title": "Videos already present in references",
        "matches_col": "Matches",
        "report_title": "Activity report",
        "clear": "Clear",
        "save_report": "Save report",
        "app_started": "Application started.",
    },
    "hr": {
        "language_label": "Jezik",
        "language_name": "Hrvatski",
        "app_subtitle": "Organizacija fotografija i videa, detekcija duplikata i NAS provjera u jednom alatu.",
        "ready": "Spremno",
        "busy": "Obrada u tijeku...",
        "wait_title": "Rad u tijeku",
        "wait_message": "Pricekajte da se trenutna operacija zavrsi.",
        "choose": "Odaberi",
        "donate": "Podrzi putem PayPala",
        "donate_title": "PayPal donacija",
        "version_label": "Verzija {version}",
        "check_updates": "Update",
        "checking_updates": "Provjeravam update...",
        "update_available_title": "Dostupna je nova verzija",
        "update_available_msg": "Dostupna je nova verzija programa Media Organizer Pro.\n\nTrenutna verzija: {current}\nNova verzija: {latest}\n\nOtvoriti stranicu za preuzimanje?",
        "update_current_title": "Program je azuran",
        "update_current_msg": "Koristite najnoviju verziju programa ({current}).",
        "update_failed_title": "Provjera nije uspjela",
        "update_failed_msg": "Nisam uspio provjeriti novu verziju. Provjerite internet vezu i pokusajte ponovno.",
        "update_in_progress_title": "Provjera je u tijeku",
        "update_in_progress_msg": "Provjera nove verzije vec je pokrenuta.",
        "tab_dashboard": "Pregled",
        "tab_photos": "Slike po datumu",
        "tab_videos": "Video po datumu",
        "tab_duplicates": "Duplikati medija",
        "tab_nas": "NAS/video provjera",
        "tab_report": "Izvjestaj",
        "dashboard_desc": "Brzi pregled dostupnih dodatnih biblioteka i sazetak poboljsanja u objedinjenoj aplikaciji.",
        "photos_desc": "Analizira datume fotografija iz EXIF podataka ili datuma datoteke te kopira ili premjesta slike u foldere po datumu.",
        "videos_desc": "Analizira datume videa pomocu FFprobe kad je dostupan te organizira video datoteke u foldere po datumu.",
        "duplicates_desc": "Pronalazi identicne i vizualno slicne medije, omogucuje pregled grupa, kopiranje za usporedbu, premjestanje ili brisanje viska.",
        "nas_desc": "Usporedjuje folder s video datotekama prema jednom ili vise referentnih/NAS foldera po nazivu ili SHA-256 hashu.",
        "report_desc": "Pregled, ciscenje i izvoz izvjestaja rada iz trenutne sesije.",
        "available": "Dostupno",
        "missing": "Nije dostupno",
        "dep_pillow": "datumi fotografija i hash slika",
        "dep_imagehash": "preciznije trazenje slicnih slika",
        "dep_opencv": "preview/hash video frameova",
        "dep_ffprobe": "datumi snimanja videa",
        "review_title": "Sto je objedinjeno i popravljeno",
        "review_notes": [
            "Jedan GUI s tabovima umjesto vise odvojenih skripti.",
            "Hashiranje se radi u chunkovima, pa velike video datoteke ne moraju cijele stati u memoriju.",
            "Vizualno trazenje slicnih slika vise nije ograniceno samo na datoteke iste velicine.",
            "Default za organizaciju je kopiranje, a ne premjestanje, radi sigurnijeg prvog koristenja.",
            "Move/delete akcije nakon obrade ciste rezultate iz tablica.",
            "Video datumi koriste FFprobe kad je dostupan, a fallback je mtime datoteke.",
        ],
        "photos_title": "Organizacija slika",
        "videos_title": "Organizacija videa",
        "source_folder": "Izvorni folder",
        "destination_folder": "Odredisni folder",
        "choose_source": "Odaberite izvorni folder",
        "choose_destination": "Odaberite odredisni folder",
        "include_subfolders": "Ukljuci podfoldere",
        "copy_instead_move": "Kopiraj umjesto premjesti",
        "isolate_duplicates": "Identicne duplikate izdvoji u _duplikati",
        "output_structure": "Struktura izlaza",
        "group_year": "Godina",
        "group_year_month": "Godina/Mjesec",
        "group_year_month_day": "Godina/Mjesec/Dan",
        "analyze": "Analiziraj",
        "organize": "Organiziraj",
        "group_preview": "Pregled po grupama",
        "folder_col": "Folder",
        "count_col": "Broj",
        "size_col": "Velicina",
        "example_col": "Primjer datoteke",
        "fallback_col": "Datum iz datoteke",
        "duplicates_title": "Duplikati slika i videa",
        "scan_folder": "Folder za skeniranje",
        "choose_scan_folder": "Odaberite folder za skeniranje",
        "scan_images": "Skeniraj slike",
        "scan_videos": "Skeniraj video",
        "exact_duplicates": "Identicni duplikati (SHA-256)",
        "visual_images": "Vizualno slicne slike",
        "visual_videos": "Vizualno slicni videi (sporije)",
        "image_threshold": "Prag slicnosti slika (%)",
        "video_threshold": "Prag slicnosti videa (%)",
        "scan_duplicates": "Skeniraj duplikate",
        "copy_groups": "Kopiraj grupe",
        "move_duplicates": "Premjesti duplikate",
        "delete_duplicates": "Obrisi duplikate",
        "found_groups": "Pronadjene grupe",
        "group_col": "Grupa",
        "type_col": "Tip",
        "method_col": "Metoda",
        "similarity_col": "Slicnost",
        "savings_col": "Moguca usteda",
        "keep_col": "Zadrzi",
        "selected_group_details": "Detalji odabrane grupe",
        "file_col": "Datoteka",
        "path_col": "Putanja",
        "nas_title": "Provjera videa prema referentnim folderima",
        "reference_folders": "Referentni/NAS folderi",
        "add": "Dodaj",
        "remove": "Ukloni",
        "check_folder": "Folder za provjeru",
        "choose_check_folder": "Odaberite folder za provjeru",
        "deep_sha": "Dubinska provjera po SHA-256 hashu",
        "scan_video_duplicates": "Skeniraj video duplikate",
        "move_selected": "Premjesti odabrane",
        "delete_selected": "Obrisi odabrane",
        "nas_results_title": "Video datoteke koje vec postoje u referencama",
        "matches_col": "Match",
        "report_title": "Izvjestaj rada",
        "clear": "Ocisti",
        "save_report": "Spremi izvjestaj",
        "app_started": "Aplikacija pokrenuta.",
    },
}


@dataclass
class MediaRecord:
    path: Path
    kind: str
    taken_at: datetime | None
    used_fallback_date: bool
    size: int


@dataclass
class DuplicateGroup:
    group_id: str
    kind: str
    method: str
    files: list[Path]
    score: float


@dataclass
class NasDuplicate:
    path: Path
    size: int
    method: str
    matches: list[Path]


class UnionFind:
    def __init__(self, items: Iterable[Path]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: Path) -> Path:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: Path, right: Path) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left != root_right:
            self.parent[root_right] = root_left


def format_size(size_bytes: int) -> str:
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    return f"{value:.1f} {units[unit_index]}"


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def iter_files(folder: Path, extensions: set[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    if recursive:
        for root, _, names in os.walk(folder):
            for name in names:
                path = Path(root) / name
                if path.suffix.lower() in extensions:
                    files.append(path)
    else:
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() in extensions:
                files.append(path)
    return sorted(files, key=lambda item: str(item).lower())


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_path(folder: Path, filename: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    candidate = folder / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    counter = 1
    while True:
        candidate = folder / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def copy_or_move(source: Path, destination: Path, copy_mode: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if copy_mode:
        shutil.copy2(source, destination)
    else:
        shutil.move(str(source), str(destination))


def fallback_file_datetime(path: Path) -> datetime | None:
    try:
        # mtime is usually more stable than ctime on Linux after copies/moves.
        return datetime.fromtimestamp(path.stat().st_mtime)
    except OSError:
        return None


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    text = str(value).strip()
    if not text:
        return None

    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass

    # Strip timezone and fractional seconds for common camera formats.
    normalized = text.replace("T", " ").split("+")[0].split(".")[0].replace("Z", "")
    formats = [
        "%Y:%m:%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%Y:%m:%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def image_datetime(path: Path) -> datetime | None:
    if not PIL_AVAILABLE:
        return None
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            if not exif:
                return None
            wanted = {"DateTimeOriginal", "DateTimeDigitized", "DateTime"}
            for tag_id, raw_value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in wanted:
                    parsed = parse_datetime(raw_value)
                    if parsed:
                        return parsed
    except Exception:
        return None
    return None


def ffprobe_executable() -> str | None:
    return shutil.which("ffprobe")


def video_datetime(path: Path) -> datetime | None:
    executable = ffprobe_executable()
    if not executable:
        return None

    command = [
        executable,
        "-v",
        "quiet",
        "-show_entries",
        "format_tags=creation_time:stream_tags=creation_time",
        "-of",
        "json",
        str(path),
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=creation_flags,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout or "{}")
    except Exception:
        return None

    candidates: list[Any] = []
    format_tags = data.get("format", {}).get("tags", {})
    if isinstance(format_tags, dict):
        candidates.append(format_tags.get("creation_time"))
    for stream in data.get("streams", []):
        if isinstance(stream, dict):
            tags = stream.get("tags", {})
            if isinstance(tags, dict):
                candidates.append(tags.get("creation_time"))

    for candidate in candidates:
        parsed = parse_datetime(candidate)
        if parsed:
            return parsed
    return None


def group_label(taken_at: datetime | None, mode: str) -> str:
    if not taken_at:
        return "_bez_datuma" if mode.startswith("Godina") else "_undated"
    if mode in {"Godina/Mjesec/Dan", "Year/Month/Day"}:
        return f"{taken_at.year:04d}/{taken_at.month:02d}/{taken_at.day:02d}"
    if mode in {"Godina/Mjesec", "Year/Month"}:
        return f"{taken_at.year:04d}/{taken_at.month:02d}"
    return f"{taken_at.year:04d}"


def average_hash_from_pil(image: Any, hash_size: int = 8) -> int:
    gray = image.resize((hash_size, hash_size)).convert("L")
    pixels = list(gray.getdata())
    average = sum(pixels) / len(pixels)
    value = 0
    for pixel in pixels:
        value = (value << 1) | int(pixel >= average)
    return value


def image_fingerprint(path: Path) -> tuple[str, Any, int] | None:
    if not PIL_AVAILABLE:
        return None
    try:
        with Image.open(path) as image:
            if IMAGEHASH_AVAILABLE:
                fingerprint = imagehash.phash(image)
                return ("imagehash", fingerprint, fingerprint.hash.size)
            return ("int", average_hash_from_pil(image), 64)
    except Exception:
        return None


def video_fingerprint(path: Path) -> tuple[str, int, int] | None:
    if not OPENCV_AVAILABLE:
        return None
    try:
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            return None
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if frame_count > 20:
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_count // 10))
        ok, frame = cap.read()
        cap.release()
        if not ok:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (8, 8))
        average = float(np.mean(resized))
        value = 0
        for pixel in resized.flatten():
            value = (value << 1) | int(pixel >= average)
        return ("int", value, 64)
    except Exception:
        return None


def fingerprint_similarity(left: tuple[str, Any, int], right: tuple[str, Any, int]) -> float:
    left_type, left_value, left_bits = left
    right_type, right_value, right_bits = right
    bits = max(left_bits, right_bits, 1)
    if left_type == "imagehash" and right_type == "imagehash":
        distance = left_value - right_value
    else:
        distance = int(left_value ^ right_value).bit_count()
    return max(0.0, min(100.0, 100.0 - (distance * 100.0 / bits)))


class MediaOrganizerPro(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1360x860")
        self.minsize(1180, 760)

        self.colors = {
            "bg": "#0b1020",
            "panel": "#111827",
            "panel_alt": "#172033",
            "border": "#263247",
            "text": "#e5e7eb",
            "muted": "#94a3b8",
            "accent": "#38bdf8",
            "accent_dark": "#0ea5e9",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "entry": "#0f172a",
        }

        self.log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.log_lines: list[str] = []
        self.photo_groups: dict[str, list[MediaRecord]] = {}
        self.video_groups: dict[str, list[MediaRecord]] = {}
        self.duplicate_groups: list[DuplicateGroup] = []
        self.nas_duplicates: list[NasDuplicate] = []
        self.busy = False
        self.lang = "en"
        self.update_check_running = False

        self.configure(bg=self.colors["bg"])
        self.setup_style()
        self.setup_tk_options()
        self.setup_variables()
        self.setup_shell()
        self.after(100, self.flush_log_queue)

    def setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        style.map("TLabel", background=[("active", self.colors["bg"])], foreground=[("active", self.colors["text"])])
        style.configure("Muted.TLabel", background=self.colors["panel"], foreground=self.colors["muted"])
        style.configure("Title.TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 10))
        style.configure("Metric.TLabel", background=self.colors["panel"], foreground=self.colors["accent"], font=("Segoe UI", 18, "bold"))
        style.configure("TNotebook", background=self.colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["panel"], foreground=self.colors["muted"], padding=(16, 10), borderwidth=0)
        style.map(
            "TNotebook.Tab",
            background=[("selected", self.colors["panel_alt"]), ("active", self.colors["panel_alt"]), ("!selected", self.colors["panel"])],
            foreground=[("selected", self.colors["text"]), ("active", self.colors["text"]), ("!selected", self.colors["muted"])],
        )
        style.configure("Treeview", background=self.colors["entry"], fieldbackground=self.colors["entry"], foreground=self.colors["text"], rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background=self.colors["panel_alt"], foreground=self.colors["text"], relief="flat", font=("Segoe UI", 10, "bold"))
        style.map(
            "Treeview",
            background=[("selected", self.colors["accent_dark"]), ("!selected", self.colors["entry"])],
            foreground=[("selected", "#ffffff"), ("!selected", self.colors["text"])],
            fieldbackground=[("!selected", self.colors["entry"])],
        )
        style.map("Treeview.Heading", background=[("active", self.colors["panel_alt"])], foreground=[("active", self.colors["text"])])
        style.configure(
            "TEntry",
            fieldbackground=self.colors["entry"],
            foreground=self.colors["text"],
            insertcolor=self.colors["text"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
        )
        style.map(
            "TEntry",
            fieldbackground=[("disabled", self.colors["panel_alt"]), ("readonly", self.colors["entry"]), ("!disabled", self.colors["entry"])],
            foreground=[("disabled", self.colors["muted"]), ("readonly", self.colors["text"]), ("!disabled", self.colors["text"])],
        )
        style.configure(
            "TCombobox",
            fieldbackground=self.colors["entry"],
            background=self.colors["entry"],
            foreground=self.colors["text"],
            arrowcolor=self.colors["text"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["border"],
            darkcolor=self.colors["border"],
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.colors["entry"]), ("!disabled", self.colors["entry"])],
            foreground=[("readonly", self.colors["text"]), ("!disabled", self.colors["text"])],
            selectbackground=[("readonly", self.colors["entry"])],
            selectforeground=[("readonly", self.colors["text"])],
            background=[("active", self.colors["panel_alt"]), ("readonly", self.colors["entry"])],
        )
        style.configure("TCheckbutton", background=self.colors["panel"], foreground=self.colors["text"])
        style.map(
            "TCheckbutton",
            background=[("active", self.colors["panel"]), ("!active", self.colors["panel"])],
            foreground=[("active", self.colors["text"]), ("selected", self.colors["text"]), ("!selected", self.colors["text"])],
            indicatorcolor=[("selected", self.colors["accent_dark"]), ("!selected", self.colors["entry"])],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=self.colors["panel_alt"],
            troughcolor=self.colors["entry"],
            bordercolor=self.colors["border"],
            arrowcolor=self.colors["text"],
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=self.colors["panel_alt"],
            troughcolor=self.colors["entry"],
            bordercolor=self.colors["border"],
            arrowcolor=self.colors["text"],
        )
        style.configure("Horizontal.TProgressbar", troughcolor=self.colors["entry"], background=self.colors["accent"], bordercolor=self.colors["border"], lightcolor=self.colors["accent"], darkcolor=self.colors["accent"])

    def setup_tk_options(self) -> None:
        self.option_add("*Background", self.colors["bg"])
        self.option_add("*Foreground", self.colors["text"])
        self.option_add("*Entry.Background", self.colors["entry"])
        self.option_add("*Entry.Foreground", self.colors["text"])
        self.option_add("*Entry.insertBackground", self.colors["text"])
        self.option_add("*Listbox.Background", self.colors["entry"])
        self.option_add("*Listbox.Foreground", self.colors["text"])
        self.option_add("*Listbox.selectBackground", self.colors["accent_dark"])
        self.option_add("*Listbox.selectForeground", "#ffffff")
        self.option_add("*Menu.Background", self.colors["entry"])
        self.option_add("*Menu.Foreground", self.colors["text"])
        self.option_add("*Menu.activeBackground", self.colors["accent_dark"])
        self.option_add("*Menu.activeForeground", "#ffffff")
        self.option_add("*Text.Background", self.colors["entry"])
        self.option_add("*Text.Foreground", self.colors["text"])
        self.option_add("*Text.insertBackground", self.colors["text"])

    def setup_variables(self) -> None:
        self.photo_source = tk.StringVar()
        self.photo_dest = tk.StringVar()
        self.photo_recursive = tk.BooleanVar(value=True)
        self.photo_copy = tk.BooleanVar(value=True)
        self.photo_isolate_duplicates = tk.BooleanVar(value=True)
        self.photo_group_mode = tk.StringVar(value="Year/Month")
        self.photo_status = tk.StringVar(value="Ready")
        self.photo_progress = tk.DoubleVar(value=0)

        self.video_source = tk.StringVar()
        self.video_dest = tk.StringVar()
        self.video_recursive = tk.BooleanVar(value=True)
        self.video_copy = tk.BooleanVar(value=True)
        self.video_isolate_duplicates = tk.BooleanVar(value=True)
        self.video_group_mode = tk.StringVar(value="Year/Month")
        self.video_status = tk.StringVar(value="Ready")
        self.video_progress = tk.DoubleVar(value=0)

        self.dup_source = tk.StringVar()
        self.dup_recursive = tk.BooleanVar(value=True)
        self.dup_include_images = tk.BooleanVar(value=True)
        self.dup_include_videos = tk.BooleanVar(value=True)
        self.dup_exact = tk.BooleanVar(value=True)
        self.dup_visual_images = tk.BooleanVar(value=True)
        self.dup_visual_videos = tk.BooleanVar(value=False)
        self.dup_image_threshold = tk.DoubleVar(value=88.0)
        self.dup_video_threshold = tk.DoubleVar(value=90.0)
        self.dup_status = tk.StringVar(value="Ready")
        self.dup_progress = tk.DoubleVar(value=0)

        self.nas_check_folder = tk.StringVar()
        self.nas_recursive = tk.BooleanVar(value=True)
        self.nas_deep_hash = tk.BooleanVar(value=False)
        self.nas_status = tk.StringVar(value="Ready")
        self.nas_progress = tk.DoubleVar(value=0)
        self.language_var = tk.StringVar(value="English")

    def t(self, key: str) -> Any:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))

    def localized_group_values(self) -> list[str]:
        return [self.t("group_year"), self.t("group_year_month"), self.t("group_year_month_day")]

    def switch_language(self, _event: tk.Event | str | None = None) -> None:
        if self.busy:
            messagebox.showinfo(self.t("wait_title"), self.t("wait_message"))
            self.language_var.set(self.t("language_name"))
            return
        selected = self.language_var.get()
        new_lang = "hr" if selected == "Hrvatski" else "en"
        if new_lang == self.lang:
            return
        old_photo_group = self.photo_group_mode.get()
        old_video_group = self.video_group_mode.get()
        self.lang = new_lang
        self.language_var.set(self.t("language_name"))
        self.photo_group_mode.set(self.localized_group_value_for(old_photo_group))
        self.video_group_mode.set(self.localized_group_value_for(old_video_group))
        for status_var in (self.photo_status, self.video_status, self.dup_status, self.nas_status):
            if status_var.get() in {"Ready", "Spremno"}:
                status_var.set(self.t("ready"))
        self.rebuild_shell()

    def localized_group_value_for(self, value: str) -> str:
        if value in {"Godina", "Year"}:
            return self.t("group_year")
        if value in {"Godina/Mjesec/Dan", "Year/Month/Day"}:
            return self.t("group_year_month_day")
        return self.t("group_year_month")

    def display_kind(self, kind: str) -> str:
        if self.lang == "hr":
            return kind
        return {"slike": "images", "video": "video", "mijesano": "mixed"}.get(kind, kind)

    def display_method(self, method: str) -> str:
        if self.lang == "hr":
            return method
        return {
            "vizualni hash": "visual hash",
            "video frame hash": "video frame hash",
            "naziv": "name",
        }.get(method, method)

    def rebuild_shell(self) -> None:
        for child in self.winfo_children():
            child.destroy()
        self.setup_style()
        self.setup_shell()
        if self.photo_groups:
            self.render_date_tree(self.photo_tree, self.photo_groups)
        if self.video_groups:
            self.render_date_tree(self.video_tree, self.video_groups)
        if self.duplicate_groups:
            self.render_duplicate_groups()
        if self.nas_duplicates:
            self.render_nas_results()
        for line in self.log_lines:
            if hasattr(self, "log_text"):
                self.log_text.insert(tk.END, line + "\n")
        if hasattr(self, "log_text"):
            self.log_text.see(tk.END)

    def setup_shell(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root)
        header.pack(fill=tk.X, pady=(0, 16))
        title_area = ttk.Frame(header)
        title_area.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(title_area, text=f"{APP_NAME} v{APP_VERSION}", style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(
            title_area,
            text=f"{self.t('version_label').format(version=APP_VERSION)} | {self.t('app_subtitle')}",
            style="Subtitle.TLabel",
        ).pack(anchor=tk.W, pady=(4, 0))

        header_tools = ttk.Frame(header)
        header_tools.pack(side=tk.RIGHT)

        ttk.Label(header_tools, text=self.t("language_label"), style="Subtitle.TLabel").pack(side=tk.LEFT, padx=(0, 8))
        language_menu = self.dark_option_menu(
            header_tools,
            self.language_var,
            ["English", "Hrvatski"],
            command=self.switch_language,
            width=11,
        )
        language_menu.pack(side=tk.LEFT, padx=(0, 10))

        self.update_button = self.header_button(header_tools, self.t("check_updates"), self.check_for_updates)
        self.update_button.pack(side=tk.LEFT, padx=(0, 10))
        self.paypal_button(header_tools).pack(side=tk.LEFT, padx=(0, 12))

        self.header_status = ttk.Label(header_tools, text=self.t("ready"), style="Subtitle.TLabel")
        self.header_status.pack(side=tk.LEFT)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.dashboard_tab = ttk.Frame(self.notebook)
        self.photo_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)
        self.duplicates_tab = ttk.Frame(self.notebook)
        self.nas_tab = ttk.Frame(self.notebook)
        self.log_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text=self.t("tab_dashboard"))
        self.notebook.add(self.photo_tab, text=self.t("tab_photos"))
        self.notebook.add(self.video_tab, text=self.t("tab_videos"))
        self.notebook.add(self.duplicates_tab, text=self.t("tab_duplicates"))
        self.notebook.add(self.nas_tab, text=self.t("tab_nas"))
        self.notebook.add(self.log_tab, text=self.t("tab_report"))

        self.build_dashboard_tab()
        self.build_photo_tab()
        self.build_video_tab()
        self.build_duplicates_tab()
        self.build_nas_tab()
        self.build_log_tab()

    def paypal_button(self, parent: tk.Widget) -> tk.Button:
        return tk.Button(
            parent,
            text=self.t("donate"),
            command=self.open_paypal_donate,
            bg="#003087",
            fg="#ffffff",
            activebackground="#0070ba",
            activeforeground="#ffffff",
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )

    def open_paypal_donate(self) -> None:
        webbrowser.open(PAYPAL_DONATE_URL)

    def header_button(self, parent: tk.Widget, text: str, command: Callable[[], None]) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.colors["panel_alt"],
            fg=self.colors["text"],
            activebackground=self.colors["border"],
            activeforeground=self.colors["text"],
            bd=0,
            padx=12,
            pady=7,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )

    def version_tuple(self, value: str) -> tuple[int, int, int]:
        parts = [int(part) for part in re.findall(r"\d+", str(value).lstrip("v"))[:3]]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)

    def is_newer_version(self, latest: str, current: str) -> bool:
        return self.version_tuple(latest) > self.version_tuple(current)

    def check_for_updates(self) -> None:
        if self.update_check_running:
            messagebox.showinfo(self.t("update_in_progress_title"), self.t("update_in_progress_msg"))
            return
        self.update_check_running = True
        if hasattr(self, "update_button"):
            self.update_button.config(state=tk.DISABLED)
        if hasattr(self, "header_status"):
            self.header_status.config(text=self.t("checking_updates"))
        threading.Thread(target=self.update_worker, daemon=True).start()

    def update_worker(self) -> None:
        release = None
        error = None
        try:
            request = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": f"MediaOrganizerPro/{APP_VERSION}",
                },
            )
            with urllib.request.urlopen(request, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not data.get("draft") and not data.get("prerelease"):
                release = {
                    "tag": str(data.get("tag_name", "")).strip(),
                    "url": data.get("html_url") or GITHUB_RELEASES_URL,
                }
        except (OSError, TimeoutError, urllib.error.URLError, ValueError) as exc:
            error = exc

        try:
            self.after(0, lambda: self.handle_update_result(release, error))
        except tk.TclError:
            pass

    def handle_update_result(self, release: dict[str, str] | None, error: Exception | None) -> None:
        self.update_check_running = False
        if hasattr(self, "update_button"):
            self.update_button.config(state=tk.NORMAL)
        if hasattr(self, "header_status"):
            self.header_status.config(text=self.t("ready"))

        if error is not None or not release or not release.get("tag"):
            messagebox.showwarning(self.t("update_failed_title"), self.t("update_failed_msg"))
            return

        latest = release["tag"]
        if not self.is_newer_version(latest, APP_VERSION):
            messagebox.showinfo(self.t("update_current_title"), self.t("update_current_msg").format(current=APP_VERSION))
            return

        message = self.t("update_available_msg").format(current=APP_VERSION, latest=latest)
        if messagebox.askyesno(self.t("update_available_title"), message):
            webbrowser.open(release["url"], new=2)

    def dark_option_menu(
        self,
        parent: tk.Widget,
        variable: tk.StringVar,
        values: list[str],
        *,
        command: Callable[[str], None] | None = None,
        width: int = 16,
    ) -> tk.OptionMenu:
        menu = tk.OptionMenu(parent, variable, *values, command=command)
        menu.configure(
            bg=self.colors["entry"],
            fg=self.colors["text"],
            activebackground=self.colors["panel_alt"],
            activeforeground=self.colors["text"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
            width=width,
            font=("Segoe UI", 10, "bold"),
        )
        menu["menu"].configure(
            bg=self.colors["entry"],
            fg=self.colors["text"],
            activebackground=self.colors["accent_dark"],
            activeforeground="#ffffff",
            font=("Segoe UI", 10),
        )
        return menu

    def tab_intro(self, parent: tk.Widget, description_key: str) -> None:
        tk.Label(
            parent,
            text=self.t(description_key),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10),
            anchor=tk.W,
            justify=tk.LEFT,
            wraplength=1000,
        ).pack(fill=tk.X, pady=(0, 12))

    def panel(self, parent: tk.Widget, padding: int = 14) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=self.colors["panel"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        inner = tk.Frame(frame, bg=self.colors["panel"])
        inner.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)
        frame.inner = inner  # type: ignore[attr-defined]
        return frame

    def label(self, parent: tk.Widget, text: str, *, muted: bool = False, font: tuple[str, int, str] | tuple[str, int] | None = None) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=self.colors["panel"],
            fg=self.colors["muted"] if muted else self.colors["text"],
            font=font or ("Segoe UI", 10),
            anchor=tk.W,
        )

    def button(self, parent: tk.Widget, text: str, command: Callable[[], None], *, danger: bool = False) -> tk.Button:
        bg = self.colors["danger"] if danger else self.colors["accent_dark"]
        active = "#dc2626" if danger else "#0284c7"
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="#ffffff",
            activebackground=active,
            activeforeground="#ffffff",
            bd=0,
            padx=14,
            pady=8,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
        )

    def path_row(self, parent: tk.Widget, label: str, variable: tk.StringVar, title: str) -> None:
        row = tk.Frame(parent, bg=self.colors["panel"])
        row.pack(fill=tk.X, pady=(0, 10))
        self.label(row, label).pack(anchor=tk.W, pady=(0, 4))
        entry_row = tk.Frame(row, bg=self.colors["panel"])
        entry_row.pack(fill=tk.X)
        entry = ttk.Entry(entry_row, textvariable=variable)
        entry.configure(style="TEntry")
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button(entry_row, self.t("choose"), lambda: self.choose_directory(variable, title)).pack(side=tk.LEFT, padx=(8, 0))

    def choose_directory(self, variable: tk.StringVar, title: str) -> None:
        folder = filedialog.askdirectory(title=title)
        if folder:
            variable.set(folder)

    def set_busy(self, busy: bool, status: str | None = None) -> bool:
        if busy and self.busy:
            messagebox.showinfo(self.t("wait_title"), self.t("wait_message"))
            return False
        self.busy = busy
        self.header_status.config(text=status or (self.t("busy") if busy else self.t("ready")))
        return True

    def log(self, message: str) -> None:
        if threading.current_thread() is threading.main_thread():
            self.append_log(message)
        else:
            self.log_queue.put(("log", message))

    def append_log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.log_lines.append(line)
        if hasattr(self, "log_text"):
            self.log_text.insert(tk.END, line + "\n")
            self.log_text.see(tk.END)

    def flush_log_queue(self) -> None:
        try:
            while True:
                kind, message = self.log_queue.get_nowait()
                if kind == "log":
                    self.append_log(message)
        except queue.Empty:
            pass
        self.after(100, self.flush_log_queue)

    def build_dashboard_tab(self) -> None:
        wrapper = ttk.Frame(self.dashboard_tab, padding=16)
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.tab_intro(wrapper, "dashboard_desc")

        top = ttk.Frame(wrapper)
        top.pack(fill=tk.X)

        dependencies = [
            ("Pillow / EXIF", PIL_AVAILABLE, self.t("dep_pillow")),
            ("ImageHash", IMAGEHASH_AVAILABLE, self.t("dep_imagehash")),
            ("OpenCV", OPENCV_AVAILABLE, self.t("dep_opencv")),
            ("FFprobe", bool(ffprobe_executable()), self.t("dep_ffprobe")),
        ]
        for name, available, note in dependencies:
            card = self.panel(top)
            card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            inner = card.inner  # type: ignore[attr-defined]
            self.label(inner, name, font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
            status = self.t("available") if available else self.t("missing")
            color = self.colors["success"] if available else self.colors["warning"]
            tk.Label(inner, text=status, bg=self.colors["panel"], fg=color, font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(8, 2))
            self.label(inner, note, muted=True).pack(anchor=tk.W)

        review = self.panel(wrapper)
        review.pack(fill=tk.BOTH, expand=True, pady=(16, 0))
        inner = review.inner  # type: ignore[attr-defined]
        self.label(inner, self.t("review_title"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))
        for note in self.t("review_notes"):
            self.label(inner, f"- {note}", muted=False).pack(anchor=tk.W, pady=2)

    def build_photo_tab(self) -> None:
        self.build_organizer_tab(
            self.photo_tab,
            kind="image",
            source_var=self.photo_source,
            dest_var=self.photo_dest,
            recursive_var=self.photo_recursive,
            copy_var=self.photo_copy,
            isolate_var=self.photo_isolate_duplicates,
            group_mode_var=self.photo_group_mode,
            status_var=self.photo_status,
            progress_var=self.photo_progress,
        )

    def build_video_tab(self) -> None:
        self.build_organizer_tab(
            self.video_tab,
            kind="video",
            source_var=self.video_source,
            dest_var=self.video_dest,
            recursive_var=self.video_recursive,
            copy_var=self.video_copy,
            isolate_var=self.video_isolate_duplicates,
            group_mode_var=self.video_group_mode,
            status_var=self.video_status,
            progress_var=self.video_progress,
        )

    def build_organizer_tab(
        self,
        tab: ttk.Frame,
        *,
        kind: str,
        source_var: tk.StringVar,
        dest_var: tk.StringVar,
        recursive_var: tk.BooleanVar,
        copy_var: tk.BooleanVar,
        isolate_var: tk.BooleanVar,
        group_mode_var: tk.StringVar,
        status_var: tk.StringVar,
        progress_var: tk.DoubleVar,
    ) -> None:
        wrapper = ttk.Frame(tab, padding=16)
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.tab_intro(wrapper, "photos_desc" if kind == "image" else "videos_desc")

        left = self.panel(wrapper)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        left.configure(width=380)
        inner = left.inner  # type: ignore[attr-defined]

        title = self.t("photos_title") if kind == "image" else self.t("videos_title")
        self.label(inner, title, font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 12))
        self.path_row(inner, self.t("source_folder"), source_var, self.t("choose_source"))
        self.path_row(inner, self.t("destination_folder"), dest_var, self.t("choose_destination"))

        options = tk.Frame(inner, bg=self.colors["panel"])
        options.pack(fill=tk.X, pady=(4, 12))
        ttk.Checkbutton(options, text=self.t("include_subfolders"), variable=recursive_var).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(options, text=self.t("copy_instead_move"), variable=copy_var).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(options, text=self.t("isolate_duplicates"), variable=isolate_var).pack(anchor=tk.W, pady=3)

        self.label(inner, self.t("output_structure")).pack(anchor=tk.W, pady=(6, 4))
        group_menu = self.dark_option_menu(inner, group_mode_var, self.localized_group_values(), width=20)
        group_menu.pack(fill=tk.X)

        buttons = tk.Frame(inner, bg=self.colors["panel"])
        buttons.pack(fill=tk.X, pady=(16, 10))
        analyze_cmd = lambda: self.start_date_analysis(kind)
        organize_cmd = lambda: self.start_date_organize(kind)
        self.button(buttons, self.t("analyze"), analyze_cmd).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button(buttons, self.t("organize"), organize_cmd).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        ttk.Progressbar(inner, variable=progress_var, maximum=100).pack(fill=tk.X, pady=(8, 4))
        ttk.Label(inner, textvariable=status_var, style="Muted.TLabel").pack(anchor=tk.W)

        right = self.panel(wrapper)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_inner = right.inner  # type: ignore[attr-defined]
        self.label(right_inner, self.t("group_preview"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))

        tree = self.create_tree(right_inner, columns=("group", "count", "size", "example", "fallback"), show="headings")
        headings = {
            "group": self.t("folder_col"),
            "count": self.t("count_col"),
            "size": self.t("size_col"),
            "example": self.t("example_col"),
            "fallback": self.t("fallback_col"),
        }
        widths = {"group": 160, "count": 80, "size": 110, "example": 360, "fallback": 130}
        self.setup_tree_columns(tree, headings, widths)
        tree.container.pack(fill=tk.BOTH, expand=True)  # type: ignore[attr-defined]

        if kind == "image":
            self.photo_tree = tree
        else:
            self.video_tree = tree

    def create_tree(self, parent: tk.Widget, *, columns: tuple[str, ...], show: str = "headings") -> ttk.Treeview:
        frame = ttk.Frame(parent)
        tree = ttk.Treeview(frame, columns=columns, show=show, selectmode="extended")
        y_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        x_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree.container = frame  # type: ignore[attr-defined]
        return tree

    def setup_tree_columns(self, tree: ttk.Treeview, headings: dict[str, str], widths: dict[str, int]) -> None:
        for column, heading in headings.items():
            tree.heading(column, text=heading)
            tree.column(column, width=widths.get(column, 120), minwidth=60, stretch=True)

    def validate_folder(self, value: str, name: str, must_exist: bool = True) -> Path | None:
        if not value.strip():
            messagebox.showwarning("Nedostaje folder", f"Odaberite {name}.")
            return None
        path = Path(value).expanduser()
        if must_exist and not path.exists():
            messagebox.showerror("Neispravan folder", f"Folder ne postoji:\n{path}")
            return None
        return path

    def start_date_analysis(self, kind: str) -> None:
        if not self.set_busy(True, "Analiza u tijeku..."):
            return
        if kind == "image":
            source = self.validate_folder(self.photo_source.get(), "izvorni folder")
            recursive = self.photo_recursive.get()
            group_mode = self.photo_group_mode.get()
            status_var = self.photo_status
            progress_var = self.photo_progress
        else:
            source = self.validate_folder(self.video_source.get(), "izvorni folder")
            recursive = self.video_recursive.get()
            group_mode = self.video_group_mode.get()
            status_var = self.video_status
            progress_var = self.video_progress

        if not source:
            self.set_busy(False)
            return

        progress_var.set(0)
        status_var.set("Analiza pokrenuta")
        thread = threading.Thread(
            target=self.analyze_by_date_worker,
            args=(kind, source, recursive, group_mode),
            daemon=True,
        )
        thread.start()

    def analyze_by_date_worker(self, kind: str, source: Path, recursive: bool, group_mode: str) -> None:
        try:
            extensions = IMAGE_EXTENSIONS if kind == "image" else VIDEO_EXTENSIONS
            label = "slika" if kind == "image" else "video datoteka"
            self.log(f"Skeniram {source} ({label})")
            files = iter_files(source, extensions, recursive)
            total = len(files)
            groups: dict[str, list[MediaRecord]] = defaultdict(list)
            total_size = 0

            for index, path in enumerate(files, 1):
                taken_at = image_datetime(path) if kind == "image" else video_datetime(path)
                used_fallback = False
                if taken_at is None:
                    taken_at = fallback_file_datetime(path)
                    used_fallback = taken_at is not None
                try:
                    size = path.stat().st_size
                except OSError:
                    size = 0
                total_size += size
                record = MediaRecord(path=path, kind=kind, taken_at=taken_at, used_fallback_date=used_fallback, size=size)
                groups[group_label(taken_at, group_mode)].append(record)
                if total:
                    self.after(0, self.update_date_progress, kind, index, total)

            self.after(0, self.finish_date_analysis, kind, dict(groups), total, total_size)
        except Exception as exc:
            self.after(0, self.operation_failed, f"Analiza nije uspjela: {exc}")

    def update_date_progress(self, kind: str, index: int, total: int) -> None:
        percent = index * 100 / total
        if kind == "image":
            self.photo_progress.set(percent)
            self.photo_status.set(f"Obradjeno {index}/{total} slika")
        else:
            self.video_progress.set(percent)
            self.video_status.set(f"Obradjeno {index}/{total} video datoteka")

    def finish_date_analysis(self, kind: str, groups: dict[str, list[MediaRecord]], total: int, total_size: int) -> None:
        if kind == "image":
            self.photo_groups = groups
            self.render_date_tree(self.photo_tree, groups)
            self.photo_status.set(f"Pronadjeno {total} slika u {len(groups)} grupa ({format_size(total_size)})")
        else:
            self.video_groups = groups
            self.render_date_tree(self.video_tree, groups)
            self.video_status.set(f"Pronadjeno {total} video datoteka u {len(groups)} grupa ({format_size(total_size)})")
        self.log(f"Analiza zavrsena: {total} datoteka, {len(groups)} grupa, {format_size(total_size)}")
        self.set_busy(False)

    def render_date_tree(self, tree: ttk.Treeview, groups: dict[str, list[MediaRecord]]) -> None:
        tree.delete(*tree.get_children())
        for key in sorted(groups):
            records = groups[key]
            size = sum(record.size for record in records)
            fallback_count = sum(1 for record in records if record.used_fallback_date)
            example = records[0].path.name if records else ""
            tree.insert("", tk.END, values=(key, len(records), format_size(size), example, fallback_count))

    def start_date_organize(self, kind: str) -> None:
        if kind == "image":
            groups = self.photo_groups
            dest = self.validate_folder(self.photo_dest.get(), "odredisni folder", must_exist=False)
            copy_mode = self.photo_copy.get()
            isolate = self.photo_isolate_duplicates.get()
            status_var = self.photo_status
            progress_var = self.photo_progress
        else:
            groups = self.video_groups
            dest = self.validate_folder(self.video_dest.get(), "odredisni folder", must_exist=False)
            copy_mode = self.video_copy.get()
            isolate = self.video_isolate_duplicates.get()
            status_var = self.video_status
            progress_var = self.video_progress

        if not dest:
            return
        if not groups:
            messagebox.showinfo("Nema analize", "Prvo pokrenite analizu.")
            return
        count = sum(len(records) for records in groups.values())
        action = "kopirati" if copy_mode else "premjestiti"
        if not messagebox.askyesno("Potvrda", f"Zelite li {action} {count} datoteka u:\n{dest}"):
            return
        if not self.set_busy(True, "Organizacija u tijeku..."):
            return

        status_var.set("Organizacija pokrenuta")
        progress_var.set(0)
        thread = threading.Thread(
            target=self.organize_by_date_worker,
            args=(kind, groups, dest, copy_mode, isolate),
            daemon=True,
        )
        thread.start()

    def organize_by_date_worker(
        self,
        kind: str,
        groups: dict[str, list[MediaRecord]],
        dest: Path,
        copy_mode: bool,
        isolate_duplicates: bool,
    ) -> None:
        processed = 0
        duplicated = 0
        failed = 0
        seen_hashes: dict[str, Path] = {}
        total = sum(len(records) for records in groups.values())
        duplicate_root = dest / "_duplikati" / ("slike" if kind == "image" else "video")
        started = time.time()

        for group, records in sorted(groups.items()):
            target_folder = dest.joinpath(*group.split("/"))
            for record in records:
                try:
                    target_folder.mkdir(parents=True, exist_ok=True)
                    target = unique_path(target_folder, record.path.name)
                    if isolate_duplicates:
                        digest = sha256_file(record.path)
                        if digest in seen_hashes:
                            target = unique_path(duplicate_root, record.path.name)
                            duplicated += 1
                        else:
                            seen_hashes[digest] = record.path
                    copy_or_move(record.path, target, copy_mode)
                    processed += 1
                    self.log(f"{'Kopirano' if copy_mode else 'Premjesteno'}: {record.path.name} -> {target}")
                except Exception as exc:
                    failed += 1
                    self.log(f"Greska za {record.path}: {exc}")
                finally:
                    if total:
                        self.after(0, self.update_organize_progress, kind, processed + failed, total)

        elapsed = time.time() - started
        self.after(0, self.finish_organize, kind, processed, duplicated, failed, elapsed)

    def update_organize_progress(self, kind: str, done: int, total: int) -> None:
        percent = done * 100 / total
        if kind == "image":
            self.photo_progress.set(percent)
            self.photo_status.set(f"Organizirano {done}/{total}")
        else:
            self.video_progress.set(percent)
            self.video_status.set(f"Organizirano {done}/{total}")

    def finish_organize(self, kind: str, processed: int, duplicated: int, failed: int, elapsed: float) -> None:
        status = f"Gotovo: {processed} obradjeno, {duplicated} duplikata, {failed} gresaka ({elapsed:.1f}s)"
        if kind == "image":
            self.photo_status.set(status)
            self.photo_progress.set(0)
        else:
            self.video_status.set(status)
            self.video_progress.set(0)
        self.log(status)
        self.set_busy(False)
        if failed:
            messagebox.showwarning("Zavrseno s greskama", status)
        else:
            messagebox.showinfo("Zavrseno", status)

    def operation_failed(self, message: str) -> None:
        self.log(message)
        self.set_busy(False)
        messagebox.showerror("Greska", message)

    def build_duplicates_tab(self) -> None:
        wrapper = ttk.Frame(self.duplicates_tab, padding=16)
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.tab_intro(wrapper, "duplicates_desc")

        left = self.panel(wrapper)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        left.configure(width=390)
        inner = left.inner  # type: ignore[attr-defined]
        self.label(inner, self.t("duplicates_title"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 12))
        self.path_row(inner, self.t("scan_folder"), self.dup_source, self.t("choose_scan_folder"))

        ttk.Checkbutton(inner, text=self.t("include_subfolders"), variable=self.dup_recursive).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("scan_images"), variable=self.dup_include_images).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("scan_videos"), variable=self.dup_include_videos).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("exact_duplicates"), variable=self.dup_exact).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("visual_images"), variable=self.dup_visual_images).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("visual_videos"), variable=self.dup_visual_videos).pack(anchor=tk.W, pady=3)

        self.label(inner, self.t("image_threshold")).pack(anchor=tk.W, pady=(10, 2))
        ttk.Scale(inner, from_=50, to=100, variable=self.dup_image_threshold, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(inner, textvariable=self.dup_image_threshold, style="Muted.TLabel").pack(anchor=tk.W)

        self.label(inner, self.t("video_threshold")).pack(anchor=tk.W, pady=(10, 2))
        ttk.Scale(inner, from_=50, to=100, variable=self.dup_video_threshold, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(inner, textvariable=self.dup_video_threshold, style="Muted.TLabel").pack(anchor=tk.W)

        self.button(inner, self.t("scan_duplicates"), self.start_duplicate_scan).pack(fill=tk.X, pady=(16, 8))
        action_row = tk.Frame(inner, bg=self.colors["panel"])
        action_row.pack(fill=tk.X)
        self.button(action_row, self.t("copy_groups"), self.copy_duplicate_groups).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button(action_row, self.t("move_duplicates"), self.move_duplicate_groups).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        self.button(inner, self.t("delete_duplicates"), self.delete_duplicate_groups, danger=True).pack(fill=tk.X, pady=(8, 8))
        ttk.Progressbar(inner, variable=self.dup_progress, maximum=100).pack(fill=tk.X, pady=(6, 4))
        ttk.Label(inner, textvariable=self.dup_status, style="Muted.TLabel").pack(anchor=tk.W)

        right = ttk.Frame(wrapper)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        result_panel = self.panel(right)
        result_panel.pack(fill=tk.BOTH, expand=True)
        result_inner = result_panel.inner  # type: ignore[attr-defined]
        self.label(result_inner, self.t("found_groups"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))
        self.dup_tree = self.create_tree(result_inner, columns=("id", "kind", "method", "count", "score", "savings", "keep"), show="headings")
        self.setup_tree_columns(
            self.dup_tree,
            {
                "id": self.t("group_col"),
                "kind": self.t("type_col"),
                "method": self.t("method_col"),
                "count": self.t("count_col"),
                "score": self.t("similarity_col"),
                "savings": self.t("savings_col"),
                "keep": self.t("keep_col"),
            },
            {"id": 80, "kind": 100, "method": 130, "count": 70, "score": 90, "savings": 130, "keep": 260},
        )
        self.dup_tree.container.pack(fill=tk.BOTH, expand=True)  # type: ignore[attr-defined]
        self.dup_tree.bind("<<TreeviewSelect>>", self.render_duplicate_details)

        detail_panel = self.panel(right)
        detail_panel.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        detail_inner = detail_panel.inner  # type: ignore[attr-defined]
        self.label(detail_inner, self.t("selected_group_details"), font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, pady=(0, 8))
        self.dup_detail_tree = self.create_tree(detail_inner, columns=("file", "size", "path"), show="headings")
        self.setup_tree_columns(
            self.dup_detail_tree,
            {"file": self.t("file_col"), "size": self.t("size_col"), "path": self.t("path_col")},
            {"file": 240, "size": 100, "path": 520},
        )
        self.dup_detail_tree.container.pack(fill=tk.BOTH, expand=True)  # type: ignore[attr-defined]

    def start_duplicate_scan(self) -> None:
        source = self.validate_folder(self.dup_source.get(), "folder za skeniranje")
        if not source:
            return
        options = {
            "include_images": self.dup_include_images.get(),
            "include_videos": self.dup_include_videos.get(),
            "recursive": self.dup_recursive.get(),
            "exact": self.dup_exact.get(),
            "visual_images": self.dup_visual_images.get(),
            "visual_videos": self.dup_visual_videos.get(),
            "image_threshold": self.dup_image_threshold.get(),
            "video_threshold": self.dup_video_threshold.get(),
        }
        if not (options["include_images"] or options["include_videos"]):
            messagebox.showwarning("Nema tipova", "Odaberite slike, video ili oboje.")
            return
        if not (options["exact"] or options["visual_images"] or options["visual_videos"]):
            messagebox.showwarning("Nema metode", "Odaberite barem jednu metodu detekcije.")
            return
        if not self.set_busy(True, "Skeniranje duplikata..."):
            return
        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_detail_tree.delete(*self.dup_detail_tree.get_children())
        self.dup_progress.set(0)
        self.dup_status.set("Skeniranje pokrenuto")
        thread = threading.Thread(target=self.duplicate_scan_worker, args=(source, options), daemon=True)
        thread.start()

    def duplicate_scan_worker(self, source: Path, options: dict[str, Any]) -> None:
        try:
            extensions: set[str] = set()
            if options["include_images"]:
                extensions.update(IMAGE_EXTENSIONS)
            if options["include_videos"]:
                extensions.update(VIDEO_EXTENSIONS)
            files = iter_files(source, extensions, bool(options["recursive"]))
            self.log(f"Duplikati: pronadjeno {len(files)} medijskih datoteka")
            groups: list[DuplicateGroup] = []

            if options["exact"]:
                groups.extend(self.find_exact_duplicate_groups(files))

            if options["visual_images"]:
                image_files = [path for path in files if is_image(path)]
                groups.extend(
                    self.find_visual_groups(
                        image_files,
                        float(options["image_threshold"]),
                        "slike",
                        "vizualni hash",
                        image_fingerprint,
                    )
                )

            if options["visual_videos"]:
                video_files = [path for path in files if is_video(path)]
                groups.extend(
                    self.find_visual_groups(
                        video_files,
                        float(options["video_threshold"]),
                        "video",
                        "video frame hash",
                        video_fingerprint,
                    )
                )

            for index, group in enumerate(groups, 1):
                group.group_id = f"G{index:03d}"
            self.after(0, self.finish_duplicate_scan, groups)
        except Exception as exc:
            self.after(0, self.operation_failed, f"Skeniranje duplikata nije uspjelo: {exc}")

    def find_exact_duplicate_groups(self, files: list[Path]) -> list[DuplicateGroup]:
        buckets: dict[str, list[Path]] = defaultdict(list)
        total = len(files)
        for index, path in enumerate(files, 1):
            try:
                buckets[sha256_file(path)].append(path)
            except Exception as exc:
                self.log(f"Ne mogu hashirati {path}: {exc}")
            if total:
                self.after(0, self.set_duplicate_progress, index * 100 / max(total, 1) * 0.35, "SHA-256 analiza")

        groups: list[DuplicateGroup] = []
        for paths in buckets.values():
            if len(paths) > 1:
                kind = "slike" if all(is_image(path) for path in paths) else "video" if all(is_video(path) for path in paths) else "mijesano"
                groups.append(DuplicateGroup("", kind, "SHA-256", sorted(paths), 100.0))
        self.log(f"SHA-256 grupe: {len(groups)}")
        return groups

    def find_visual_groups(
        self,
        files: list[Path],
        threshold: float,
        kind: str,
        method: str,
        fingerprint_func: Callable[[Path], tuple[str, Any, int] | None],
    ) -> list[DuplicateGroup]:
        if not files:
            return []
        if kind == "slike" and not PIL_AVAILABLE:
            self.log("Pillow nije dostupan, preskacem vizualnu analizu slika.")
            return []
        if kind == "video" and not OPENCV_AVAILABLE:
            self.log("OpenCV nije dostupan, preskacem vizualnu analizu videa.")
            return []

        fingerprints: dict[Path, tuple[str, Any, int]] = {}
        for index, path in enumerate(files, 1):
            fingerprint = fingerprint_func(path)
            if fingerprint:
                fingerprints[path] = fingerprint
            self.after(0, self.set_duplicate_progress, 35 + index * 25 / max(len(files), 1), f"Fingerprint: {kind}")

        paths = list(fingerprints)
        if len(paths) < 2:
            return []

        uf = UnionFind(paths)
        matched_scores: list[tuple[Path, Path, float]] = []
        pair_count = len(paths) * (len(paths) - 1) // 2
        checked = 0
        for i, left in enumerate(paths):
            for right in paths[i + 1 :]:
                similarity = fingerprint_similarity(fingerprints[left], fingerprints[right])
                if similarity >= threshold:
                    uf.union(left, right)
                    matched_scores.append((left, right, similarity))
                checked += 1
                if checked % 100 == 0 or checked == pair_count:
                    self.after(0, self.set_duplicate_progress, 60 + checked * 35 / max(pair_count, 1), f"Usporedba: {kind}")

        components: dict[Path, list[Path]] = defaultdict(list)
        for path in paths:
            components[uf.find(path)].append(path)

        groups: list[DuplicateGroup] = []
        for component in components.values():
            if len(component) < 2:
                continue
            scores = [
                score
                for left, right, score in matched_scores
                if left in component and right in component
            ]
            average_score = sum(scores) / len(scores) if scores else threshold
            groups.append(DuplicateGroup("", kind, method, sorted(component), average_score))

        self.log(f"Vizualne grupe ({kind}): {len(groups)}")
        return groups

    def set_duplicate_progress(self, value: float, status: str) -> None:
        self.dup_progress.set(max(0, min(100, value)))
        self.dup_status.set(status)

    def finish_duplicate_scan(self, groups: list[DuplicateGroup]) -> None:
        self.duplicate_groups = groups
        self.render_duplicate_groups()
        self.dup_progress.set(0)
        self.dup_status.set(f"Pronadjeno {len(groups)} grupa duplikata")
        self.log(f"Skeniranje duplikata zavrseno: {len(groups)} grupa")
        self.set_busy(False)

    def render_duplicate_groups(self) -> None:
        self.dup_tree.delete(*self.dup_tree.get_children())
        self.dup_detail_tree.delete(*self.dup_detail_tree.get_children())
        for index, group in enumerate(self.duplicate_groups):
            existing_files = [path for path in group.files if path.exists()]
            if not existing_files:
                continue
            keep = max(existing_files, key=lambda path: path.stat().st_size if path.exists() else 0)
            savings = sum(path.stat().st_size for path in existing_files if path != keep and path.exists())
            self.dup_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    group.group_id,
                    self.display_kind(group.kind),
                    self.display_method(group.method),
                    len(existing_files),
                    f"{group.score:.1f}%",
                    format_size(savings),
                    keep.name,
                ),
            )

    def render_duplicate_details(self, _event: tk.Event | None = None) -> None:
        self.dup_detail_tree.delete(*self.dup_detail_tree.get_children())
        selected = self.dup_tree.selection()
        if not selected:
            return
        group = self.duplicate_groups[int(selected[0])]
        keep = max(group.files, key=lambda path: path.stat().st_size if path.exists() else 0)
        for path in sorted(group.files):
            marker = "[ZADRZI] " if path == keep else ""
            size = path.stat().st_size if path.exists() else 0
            self.dup_detail_tree.insert("", tk.END, values=(marker + path.name, format_size(size), str(path)))

    def selected_duplicate_groups(self) -> list[DuplicateGroup]:
        selected = self.dup_tree.selection()
        groups = [self.duplicate_groups[int(item)] for item in selected if item.isdigit()]
        if not groups:
            messagebox.showwarning("Nema odabira", "Odaberite jednu ili vise grupa u tablici.")
        return groups

    def duplicate_action_files(self, groups: list[DuplicateGroup]) -> tuple[set[Path], set[Path]]:
        keep_files: set[Path] = set()
        all_files: set[Path] = set()
        for group in groups:
            existing = [path for path in group.files if path.exists()]
            if not existing:
                continue
            keep_files.add(max(existing, key=lambda path: path.stat().st_size))
            all_files.update(existing)
        delete_or_move = all_files - keep_files
        return keep_files, delete_or_move

    def copy_duplicate_groups(self) -> None:
        groups = self.selected_duplicate_groups()
        if not groups:
            return
        folder = filedialog.askdirectory(title="Odaberite folder za kopiranje grupa")
        if not folder:
            return
        if not self.set_busy(True, "Kopiranje grupa..."):
            return
        thread = threading.Thread(target=self.copy_duplicate_groups_worker, args=(groups, Path(folder)), daemon=True)
        thread.start()

    def copy_duplicate_groups_worker(self, groups: list[DuplicateGroup], destination: Path) -> None:
        copied = 0
        failed = 0
        for group in groups:
            group_folder = destination / f"{group.group_id}_{group.method.replace(' ', '_')}"
            group_folder.mkdir(parents=True, exist_ok=True)
            info_lines = [
                f"Grupa: {group.group_id}",
                f"Tip: {group.kind}",
                f"Metoda: {group.method}",
                f"Slicnost: {group.score:.1f}%",
                "",
            ]
            for index, path in enumerate(group.files):
                prefix = chr(65 + (index % 26))
                target = unique_path(group_folder, f"{prefix}_{path.name}")
                try:
                    shutil.copy2(path, target)
                    copied += 1
                    info_lines.append(f"{prefix}: {path}")
                except Exception as exc:
                    failed += 1
                    self.log(f"Kopiranje nije uspjelo za {path}: {exc}")
            try:
                (group_folder / "INFO.txt").write_text("\n".join(info_lines), encoding="utf-8")
            except Exception as exc:
                self.log(f"Ne mogu napisati INFO za {group.group_id}: {exc}")
        self.after(0, self.finish_file_action, f"Kopirano {copied} datoteka, gresaka {failed}")

    def move_duplicate_groups(self) -> None:
        groups = self.selected_duplicate_groups()
        if not groups:
            return
        _, files_to_move = self.duplicate_action_files(groups)
        if not files_to_move:
            messagebox.showinfo("Nema akcije", "Nema duplikata za premjestanje.")
            return
        folder = filedialog.askdirectory(title="Odaberite quarantine folder za duplikate")
        if not folder:
            return
        if not messagebox.askyesno("Potvrda", f"Premjestiti {len(files_to_move)} datoteka u:\n{folder}"):
            return
        if not self.set_busy(True, "Premjestanje duplikata..."):
            return
        thread = threading.Thread(target=self.move_files_worker, args=(files_to_move, Path(folder), groups), daemon=True)
        thread.start()

    def move_files_worker(self, files: set[Path], destination: Path, handled_groups: list[DuplicateGroup]) -> None:
        moved = 0
        failed = 0
        for path in files:
            try:
                target = unique_path(destination, path.name)
                shutil.move(str(path), str(target))
                moved += 1
            except Exception as exc:
                failed += 1
                self.log(f"Premjestanje nije uspjelo za {path}: {exc}")
        self.after(0, self.remove_handled_duplicate_groups, handled_groups, f"Premjesteno {moved} datoteka, gresaka {failed}")

    def delete_duplicate_groups(self) -> None:
        groups = self.selected_duplicate_groups()
        if not groups:
            return
        _, files_to_delete = self.duplicate_action_files(groups)
        if not files_to_delete:
            messagebox.showinfo("Nema akcije", "Nema duplikata za brisanje.")
            return
        total_size = sum(path.stat().st_size for path in files_to_delete if path.exists())
        if not messagebox.askyesno(
            "Potvrda brisanja",
            f"Obrisati {len(files_to_delete)} datoteka?\nMoguca usteda: {format_size(total_size)}\n\nOva akcija se ne moze ponistiti.",
        ):
            return
        if not self.set_busy(True, "Brisanje duplikata..."):
            return
        thread = threading.Thread(target=self.delete_files_worker, args=(files_to_delete, groups), daemon=True)
        thread.start()

    def delete_files_worker(self, files: set[Path], handled_groups: list[DuplicateGroup]) -> None:
        deleted = 0
        failed = 0
        for path in files:
            try:
                if path.exists():
                    path.unlink()
                    deleted += 1
            except Exception as exc:
                failed += 1
                self.log(f"Brisanje nije uspjelo za {path}: {exc}")
        self.after(0, self.remove_handled_duplicate_groups, handled_groups, f"Obrisano {deleted} datoteka, gresaka {failed}")

    def remove_handled_duplicate_groups(self, handled_groups: list[DuplicateGroup], message: str) -> None:
        handled_ids = {id(group) for group in handled_groups}
        self.duplicate_groups = [group for group in self.duplicate_groups if id(group) not in handled_ids]
        for index, group in enumerate(self.duplicate_groups, 1):
            group.group_id = f"G{index:03d}"
        self.render_duplicate_groups()
        self.finish_file_action(message)

    def finish_file_action(self, message: str) -> None:
        self.log(message)
        self.set_busy(False)
        messagebox.showinfo("Gotovo", message)

    def build_nas_tab(self) -> None:
        wrapper = ttk.Frame(self.nas_tab, padding=16)
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.tab_intro(wrapper, "nas_desc")

        left = self.panel(wrapper)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        left.configure(width=410)
        inner = left.inner  # type: ignore[attr-defined]
        self.label(inner, self.t("nas_title"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 12))

        self.label(inner, self.t("reference_folders")).pack(anchor=tk.W, pady=(0, 4))
        self.nas_list = tk.Listbox(
            inner,
            height=7,
            bg=self.colors["entry"],
            fg=self.colors["text"],
            selectbackground=self.colors["accent_dark"],
            highlightbackground=self.colors["border"],
            bd=0,
        )
        self.nas_list.pack(fill=tk.X, pady=(0, 8))
        nas_buttons = tk.Frame(inner, bg=self.colors["panel"])
        nas_buttons.pack(fill=tk.X, pady=(0, 12))
        self.button(nas_buttons, self.t("add"), self.add_nas_folder).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button(nas_buttons, self.t("remove"), self.remove_nas_folder).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        self.path_row(inner, self.t("check_folder"), self.nas_check_folder, self.t("choose_check_folder"))
        ttk.Checkbutton(inner, text=self.t("include_subfolders"), variable=self.nas_recursive).pack(anchor=tk.W, pady=3)
        ttk.Checkbutton(inner, text=self.t("deep_sha"), variable=self.nas_deep_hash).pack(anchor=tk.W, pady=3)

        self.button(inner, self.t("scan_video_duplicates"), self.start_nas_scan).pack(fill=tk.X, pady=(16, 8))
        action_row = tk.Frame(inner, bg=self.colors["panel"])
        action_row.pack(fill=tk.X)
        self.button(action_row, self.t("move_selected"), self.move_nas_selected).pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.button(action_row, self.t("delete_selected"), self.delete_nas_selected, danger=True).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        ttk.Progressbar(inner, variable=self.nas_progress, maximum=100).pack(fill=tk.X, pady=(12, 4))
        ttk.Label(inner, textvariable=self.nas_status, style="Muted.TLabel").pack(anchor=tk.W)

        right = self.panel(wrapper)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_inner = right.inner  # type: ignore[attr-defined]
        self.label(right_inner, self.t("nas_results_title"), font=("Segoe UI", 13, "bold")).pack(anchor=tk.W, pady=(0, 10))
        self.nas_tree = self.create_tree(right_inner, columns=("file", "size", "method", "matches", "path"), show="headings")
        self.setup_tree_columns(
            self.nas_tree,
            {
                "file": self.t("file_col"),
                "size": self.t("size_col"),
                "method": self.t("method_col"),
                "matches": self.t("matches_col"),
                "path": self.t("path_col"),
            },
            {"file": 240, "size": 100, "method": 120, "matches": 70, "path": 520},
        )
        self.nas_tree.container.pack(fill=tk.BOTH, expand=True)  # type: ignore[attr-defined]

    def add_nas_folder(self) -> None:
        folder = filedialog.askdirectory(title="Dodajte referentni/NAS folder")
        if folder:
            existing = set(self.nas_list.get(0, tk.END))
            if folder not in existing:
                self.nas_list.insert(tk.END, folder)

    def remove_nas_folder(self) -> None:
        selected = list(self.nas_list.curselection())
        for index in reversed(selected):
            self.nas_list.delete(index)

    def start_nas_scan(self) -> None:
        refs = [Path(item) for item in self.nas_list.get(0, tk.END)]
        refs = [path for path in refs if path.exists()]
        check_folder = self.validate_folder(self.nas_check_folder.get(), "folder za provjeru")
        if not check_folder:
            return
        if not refs:
            messagebox.showwarning("Nema referenci", "Dodajte barem jedan referentni/NAS folder.")
            return
        if not self.set_busy(True, "NAS provjera u tijeku..."):
            return
        self.nas_tree.delete(*self.nas_tree.get_children())
        self.nas_duplicates = []
        self.nas_progress.set(0)
        self.nas_status.set("Skeniranje pokrenuto")
        recursive = self.nas_recursive.get()
        deep = self.nas_deep_hash.get()
        thread = threading.Thread(target=self.nas_scan_worker, args=(refs, check_folder, recursive, deep), daemon=True)
        thread.start()

    def nas_scan_worker(self, refs: list[Path], check_folder: Path, recursive: bool, deep: bool) -> None:
        try:
            reference_map: dict[str, list[Path]] = defaultdict(list)
            reference_paths: set[Path] = set()

            ref_files: list[Path] = []
            for ref in refs:
                ref_files.extend(iter_files(ref, VIDEO_EXTENSIONS, recursive))
            for index, path in enumerate(ref_files, 1):
                try:
                    reference_paths.add(path.resolve())
                except OSError:
                    pass
                key = sha256_file(path) if deep else path.stem.lower()
                reference_map[key].append(path)
                self.after(0, self.update_nas_progress, index, max(len(ref_files), 1), "Citam reference")

            check_files = iter_files(check_folder, VIDEO_EXTENSIONS, recursive)
            duplicates: list[NasDuplicate] = []
            for index, path in enumerate(check_files, 1):
                try:
                    if path.resolve() in reference_paths:
                        continue
                except OSError:
                    pass
                key = sha256_file(path) if deep else path.stem.lower()
                matches = reference_map.get(key, [])
                if matches:
                    size = path.stat().st_size if path.exists() else 0
                    duplicates.append(NasDuplicate(path=path, size=size, method="SHA-256" if deep else "naziv", matches=matches))
                self.after(0, self.update_nas_progress, index, max(len(check_files), 1), "Provjeravam folder")

            self.after(0, self.finish_nas_scan, duplicates)
        except Exception as exc:
            self.after(0, self.operation_failed, f"NAS provjera nije uspjela: {exc}")

    def update_nas_progress(self, index: int, total: int, status: str) -> None:
        self.nas_progress.set(index * 100 / total)
        self.nas_status.set(f"{status}: {index}/{total}")

    def finish_nas_scan(self, duplicates: list[NasDuplicate]) -> None:
        self.nas_duplicates = duplicates
        self.render_nas_results()
        self.nas_progress.set(0)
        self.nas_status.set(f"Pronadjeno {len(duplicates)} video duplikata")
        self.log(f"NAS provjera zavrsena: {len(duplicates)} rezultata")
        self.set_busy(False)

    def render_nas_results(self) -> None:
        self.nas_tree.delete(*self.nas_tree.get_children())
        for index, duplicate in enumerate(self.nas_duplicates):
            self.nas_tree.insert(
                "",
                tk.END,
                iid=str(index),
                values=(
                    duplicate.path.name,
                    format_size(duplicate.size),
                    self.display_method(duplicate.method),
                    len(duplicate.matches),
                    str(duplicate.path),
                ),
            )

    def selected_nas_duplicates(self) -> list[NasDuplicate]:
        selected = self.nas_tree.selection()
        rows = [self.nas_duplicates[int(item)] for item in selected if item.isdigit()]
        if not rows:
            messagebox.showwarning("Nema odabira", "Odaberite jednu ili vise video datoteka.")
        return rows

    def move_nas_selected(self) -> None:
        rows = self.selected_nas_duplicates()
        if not rows:
            return
        folder = filedialog.askdirectory(title="Odaberite folder za premjestanje")
        if not folder:
            return
        if not messagebox.askyesno("Potvrda", f"Premjestiti {len(rows)} odabranih video datoteka?"):
            return
        if not self.set_busy(True, "Premjestanje videa..."):
            return
        files = {row.path for row in rows}
        thread = threading.Thread(target=self.move_nas_worker, args=(files, Path(folder)), daemon=True)
        thread.start()

    def move_nas_worker(self, files: set[Path], destination: Path) -> None:
        moved = 0
        failed = 0
        handled: set[Path] = set()
        for path in files:
            try:
                target = unique_path(destination, path.name)
                shutil.move(str(path), str(target))
                handled.add(path)
                moved += 1
            except Exception as exc:
                failed += 1
                self.log(f"Premjestanje nije uspjelo za {path}: {exc}")
        self.after(0, self.finish_nas_file_action, handled, f"Premjesteno {moved} videa, gresaka {failed}")

    def delete_nas_selected(self) -> None:
        rows = self.selected_nas_duplicates()
        if not rows:
            return
        total_size = sum(row.size for row in rows)
        if not messagebox.askyesno(
            "Potvrda brisanja",
            f"Obrisati {len(rows)} video datoteka?\nMoguca usteda: {format_size(total_size)}\n\nOva akcija se ne moze ponistiti.",
        ):
            return
        if not self.set_busy(True, "Brisanje videa..."):
            return
        files = {row.path for row in rows}
        thread = threading.Thread(target=self.delete_nas_worker, args=(files,), daemon=True)
        thread.start()

    def delete_nas_worker(self, files: set[Path]) -> None:
        deleted = 0
        failed = 0
        handled: set[Path] = set()
        for path in files:
            try:
                if path.exists():
                    path.unlink()
                    handled.add(path)
                    deleted += 1
            except Exception as exc:
                failed += 1
                self.log(f"Brisanje nije uspjelo za {path}: {exc}")
        self.after(0, self.finish_nas_file_action, handled, f"Obrisano {deleted} videa, gresaka {failed}")

    def finish_nas_file_action(self, handled: set[Path], message: str) -> None:
        self.nas_duplicates = [item for item in self.nas_duplicates if item.path not in handled]
        self.render_nas_results()
        self.finish_file_action(message)

    def build_log_tab(self) -> None:
        wrapper = ttk.Frame(self.log_tab, padding=16)
        wrapper.pack(fill=tk.BOTH, expand=True)
        self.tab_intro(wrapper, "report_desc")
        panel = self.panel(wrapper)
        panel.pack(fill=tk.BOTH, expand=True)
        inner = panel.inner  # type: ignore[attr-defined]
        top = tk.Frame(inner, bg=self.colors["panel"])
        top.pack(fill=tk.X, pady=(0, 10))
        self.label(top, self.t("report_title"), font=("Segoe UI", 13, "bold")).pack(side=tk.LEFT)
        self.button(top, self.t("clear"), self.clear_log).pack(side=tk.RIGHT, padx=(8, 0))
        self.button(top, self.t("save_report"), self.export_log).pack(side=tk.RIGHT)
        self.log_text = ScrolledText(
            inner,
            bg=self.colors["entry"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief=tk.FLAT,
            wrap=tk.WORD,
            font=("Consolas", 10),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        if not self.log_lines:
            self.log(self.t("app_started"))

    def clear_log(self) -> None:
        self.log_lines.clear()
        self.log_text.delete("1.0", tk.END)

    def export_log(self) -> None:
        path = filedialog.asksaveasfilename(
            title=self.t("save_report"),
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("All files", "*.*")],
            initialfile=f"media_organizer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not path:
            return
        try:
            Path(path).write_text("\n".join(self.log_lines), encoding="utf-8")
            messagebox.showinfo("Spremljeno", f"Izvjestaj je spremljen u:\n{path}")
        except Exception as exc:
            messagebox.showerror("Greska", f"Ne mogu spremiti izvjestaj:\n{exc}")


def main() -> None:
    app = MediaOrganizerPro()
    app.mainloop()


if __name__ == "__main__":
    main()
