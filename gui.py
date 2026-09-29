import customtkinter as ctk
import subprocess
import threading
import os
import sys
import json
import webbrowser
from datetime import datetime
from tkinter import PhotoImage, filedialog, messagebox
from PIL import Image

# ── Constants ──────────────────────────────────────────────────────────────────
APP_TITLE      = "Refat's Android Full Backup"
APP_VERSION    = "1.0.3"
APP_SUBTITLE   = "Multi-Device  •  MTKClient Engine"
APP_DEVELOPER  = "Robiul Islam Refat"
APP_WEBSITE    = "www.refatishere.free.nf/android-backup.html"
APP_EMAIL      = "rbl.islam.refat2@gmail.com"
APP_REPOSITORY = "https://github.com/refatwashere/AndroidBackup"
APP_DESCRIPTION = "Back up and restore MediaTek Android partitions, and generate scatter files."
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR     = os.path.join(BASE_DIR, "assets")
CONFIG_FILE    = os.path.join(BASE_DIR, "gui_config.json")
DEFAULT_BACKUP = r"C:\OppoA1kBackup"
ENGINE         = os.path.join(BASE_DIR, "refat_backup_engine.py")

ACCENT       = "#1f6feb"
ACCENT_HOVER = "#388bfd"
DANGER       = "#da3633"
DANGER_HOVER = "#f85149"
SUCCESS      = "#3fb950"
WARNING      = "#d29922"
SURFACE      = "#161b22"
SURFACE2     = "#21262d"
BORDER       = "#30363d"
TEXT_MUTED   = "#8b949e"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Helpers ────────────────────────────────────────────────────────────────────
def asset(name):
    return os.path.join(ASSETS_DIR, name)

def load_image(name, size):
    try:
        return ctk.CTkImage(Image.open(asset(name)), size=size)
    except Exception:
        return None

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"backup_dir": DEFAULT_BACKUP, "skip_partitions": "userdata",
            "theme": "dark", "timestamps": True, "device_class": "A"}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ── Widget helpers ─────────────────────────────────────────────────────────────
def card(parent, **kw):
    return ctk.CTkFrame(parent, corner_radius=10, fg_color=SURFACE2,
                        border_width=1, border_color=BORDER, **kw)

def page_title(parent, text):
    ctk.CTkLabel(parent, text=text,
                 font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=32, pady=(28, 2))

def section_label(parent, text):
    ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13, weight="bold"),
                 text_color=TEXT_MUTED).pack(anchor="w", pady=(14, 3))

def hint(parent, text):
    ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11),
                 text_color=TEXT_MUTED, wraplength=580, justify="left").pack(anchor="w", pady=(0, 6))

def divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(fill="x", pady=10)

def primary_btn(parent, text, cmd, color=ACCENT, hover=ACCENT_HOVER, width=160):
    return ctk.CTkButton(parent, text=text, command=cmd, height=38, width=width,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         fg_color=color, hover_color=hover, corner_radius=8)

def ghost_btn(parent, text, cmd, width=100):
    return ctk.CTkButton(parent, text=text, command=cmd, height=34, width=width,
                         font=ctk.CTkFont(size=12), fg_color=SURFACE,
                         hover_color=SURFACE2, border_width=1, border_color=BORDER,
                         corner_radius=8)

def status_pill(parent):
    lbl = ctk.CTkLabel(parent, text="  \u25cf  Idle  ",
                       font=ctk.CTkFont(size=11, weight="bold"),
                       fg_color=SURFACE, corner_radius=20, text_color=TEXT_MUTED)
    lbl.pack(anchor="w", pady=(8, 0))
    return lbl

def set_pill(pill, state):
    s = {
        "idle":    ("  \u25cf  Idle  ",    TEXT_MUTED, SURFACE),
        "running": ("  \u25cf  Running\u2026", WARNING,    "#2d2200"),
        "ok":      ("  \u25cf  Done  ",    SUCCESS,    "#0d2b1a"),
        "error":   ("  \u25cf  Failed  ",  DANGER,     "#2d0d0d"),
    }
    t, fg, bg = s[state]
    pill.configure(text=t, text_color=fg, fg_color=bg)

# ── BROM steps widget (device-class aware) ─────────────────────────────────────
BROM_CLASSES = {
    "A": {
        "label": "Class A — Legacy MT67xx  (Oppo A1k, A5s, Realme C2/C11, Redmi 9A)",
        "steps": [
            "\u2460  Power OFF completely — wait 10 seconds",
            "\u2461  Hold  Vol \u2191  +  Vol \u2193  simultaneously",
            "\u2462  While holding, plug in the USB cable",
            "\u2463  Release keys once the log shows  Hardware Signature Extracted",
        ],
    },
    "B": {
        "label": "Class B — Dimensity / Helio  (Oppo Reno, OnePlus Nord CE MTK, Vivo V-Series)",
        "steps": [
            "\u2460  Power OFF completely",
            "\u2461  Hold  Vol \u2193  only  (some variants: Vol \u2191)",
            "\u2462  Plug in USB cable",
            "\u2463  If device boots to charging screen, retry with  --preloader-crash",
        ],
    },
    "C": {
        "label": "Class C — Samsung MTK  (Galaxy A10s, A12, M01s)",
        "steps": [
            "\u2460  Power OFF completely",
            "\u2461  Hold  Vol \u2191  only — or plug in with no keys held",
            "\u2462  Script intercepts at the exact moment power flows through USB",
        ],
    },
}

def brom_steps(parent, class_var):
    box = card(parent)
    box.pack(fill="x", pady=(0, 8))

    def _refresh(val=None):
        for w in box.winfo_children():
            w.destroy()
        cls = class_var.get()
        info = BROM_CLASSES.get(cls, BROM_CLASSES["A"])
        ctk.CTkLabel(box, text="BROM Connection  —  " + info["label"],
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=WARNING).pack(anchor="w", padx=14, pady=(10, 4))
        for s in info["steps"]:
            ctk.CTkLabel(box, text=s, font=ctk.CTkFont(size=12),
                         text_color="#cccccc").pack(anchor="w", padx=14, pady=1)
        ctk.CTkFrame(box, height=8, fg_color="transparent").pack()

    class_var.trace_add("write", lambda *_: _refresh())
    _refresh()

# ── Splash ─────────────────────────────────────────────────────────────────────
class SplashScreen(ctk.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        w, h = 520, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.configure(fg_color=SURFACE)
        self.lift()
        self.attributes("-topmost", True)

        img = load_image("splash.jpg", (520, 220))
        if img:
            ctk.CTkLabel(self, image=img, text="").pack()
        else:
            ctk.CTkLabel(self, text=APP_TITLE,
                         font=ctk.CTkFont(size=28, weight="bold"),
                         text_color=ACCENT).pack(pady=40)

        ctk.CTkLabel(self, text=APP_TITLE,
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(6, 2))
        ctk.CTkLabel(self, text=f"V{APP_VERSION}  \u2022  Loading\u2026",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack()

        self.bar = ctk.CTkProgressBar(self, width=460, height=4,
                                       fg_color=SURFACE2, progress_color=ACCENT)
        self.bar.pack(pady=(10, 0))
        self.bar.set(0)
        self._animate(0)

    def _animate(self, val):
        if val <= 1.0:
            self.bar.set(val)
            self.after(18, self._animate, val + 0.02)

# ── Main App ───────────────────────────────────────────────────────────────────
class MTKApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.cfg     = load_config()
        self.process = None

        self.title(APP_TITLE)
        self.geometry("1020x700")
        self.minsize(880, 620)
        self.configure(fg_color=SURFACE)

        try:
            self._icon_image = PhotoImage(file=os.path.join(ASSETS_DIR, "Icon_32x32.png"))
            self.wm_iconphoto(True, self._icon_image)
        except Exception:
            pass

        ctk.CTkFrame(self, height=3, fg_color=ACCENT, corner_radius=0).pack(fill="x", side="top")
        self._build_layout()
        self._show("home")

    def _build_layout(self):
        root = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        root.pack(fill="both", expand=True)
        self._build_sidebar(root)

        self.content = ctk.CTkFrame(root, fg_color="transparent", corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

        self.frames = {
            "home":     HomeFrame(self.content, self),
            "setup":    SetupFrame(self.content, self),
            "backup":   BackupFrame(self.content, self),
            "scatter":  ScatterFrame(self.content, self),
            "restore":  RestoreFrame(self.content, self),
            "logs":     LogsFrame(self.content, self),
            "settings": SettingsFrame(self.content, self),
            "about":    AboutFrame(self.content, self),
        }
        for fr in self.frames.values():
            fr.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _build_sidebar(self, root):
        sb = ctk.CTkFrame(root, width=220, corner_radius=0,
                          fg_color=SURFACE2, border_width=0)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        logo_frame = ctk.CTkFrame(sb, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 0))
        logo_img = load_image("Icon_64x64.png", (36, 36))
        if logo_img:
            ctk.CTkLabel(logo_frame, image=logo_img, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(logo_frame, text="Refat's Backup",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        ctk.CTkLabel(sb, text=APP_SUBTITLE,
                     font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(pady=(2, 16))
        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(fill="x", padx=16)

        self.nav_btns = {}
        nav = [
            ("\U0001f3e0  Home",     "home"),
            ("\u2699\ufe0f  Setup",      "setup"),
            ("\U0001f4be  Backup",   "backup"),
            ("\U0001f4c4  Scatter",  "scatter"),
            ("\U0001f504  Restore",  "restore"),
            ("\U0001f4cb  Logs",     "logs"),
            ("\U0001f3a8  Settings", "settings"),
            ("\u2139\ufe0f  About",     "about"),
        ]
        ctk.CTkFrame(sb, height=8, fg_color="transparent").pack()
        for label, key in nav:
            btn = ctk.CTkButton(
                sb, text=label, anchor="w", height=42,
                fg_color="transparent", hover_color=BORDER,
                font=ctk.CTkFont(size=13), corner_radius=8,
                command=lambda k=key: self._show(k)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_btns[key] = btn

        ctk.CTkFrame(sb, fg_color="transparent").pack(expand=True)
        ctk.CTkFrame(sb, height=1, fg_color=BORDER).pack(fill="x", padx=16)
        ctk.CTkLabel(sb, text=f"V{APP_VERSION}",
                     font=ctk.CTkFont(size=10), text_color=TEXT_MUTED).pack(pady=(8, 14))

    def _show(self, key):
        self.frames[key].lift()
        for k, b in self.nav_btns.items():
            b.configure(fg_color=ACCENT if k == key else "transparent",
                        text_color="white" if k == key else "#e6edf3")

    def log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S") if self.cfg.get("timestamps", True) else ""
        prefix = f"[{ts}] " if ts else ""
        color_map = {"info": "white", "ok": SUCCESS, "warn": WARNING,
                     "error": DANGER, "cmd": "#79c0ff"}
        self.frames["logs"].append(prefix + msg, color_map.get(tag, "white"))

    def _handle_command_line(self, line, on_progress=None):
        if line.startswith("REFAT_PROGRESS|"):
            try:
                _, percent, label = line.split("|", 2)
                if on_progress:
                    self.after(0, on_progress, float(percent), label)
            except (ValueError, TypeError):
                pass
            return

        if not line:
            return
        lowered = line.lower()
        tag = ("ok" if any(word in lowered for word in ["success", "done", "complete", "finish", "saved"]) else
               "error" if any(word in lowered for word in ["error", "fail", "exception", "traceback", "critical", "blocked"]) else
               "warn" if any(word in lowered for word in ["warning", "warn", "skip", "missing", "mismatch"]) else "info")
        self.after(0, self.log, line, tag)

    def run_command(self, cmd, on_done=None, on_progress=None, show_logs=True):
        self.log("$ " + " ".join(str(c) for c in cmd), "cmd")

        def _worker():
            try:
                process_cmd = cmd
                if getattr(sys, "frozen", False) and len(cmd) > 2 and cmd[1] == ENGINE:
                    process_cmd = [sys.executable, "--refat-engine-worker", *cmd[2:]]
                process = subprocess.Popen(
                    process_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, cwd=BASE_DIR,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                self.process = process
                if process.stdout is not None:
                    for line in process.stdout:
                        self._handle_command_line(line.rstrip(), on_progress)
                process.wait()
                rc = process.returncode if process.returncode is not None else -1
                self.after(0, self.log, f"Exited with code {rc}", "ok" if rc == 0 else "error")
                if on_done:
                    self.after(0, on_done, rc)
            except Exception as e:
                self.after(0, self.log, f"Command error: {e}", "error")
                if on_done:
                    self.after(0, on_done, -1)
            finally:
                self.process = None

        threading.Thread(target=_worker, daemon=True).start()
        if show_logs:
            self._show("logs")

    def stop_command(self):
        if self.process:
            self.process.terminate()
            self.log("Process terminated by user.", "warn")


# ── Home Frame ─────────────────────────────────────────────────────────────────
class HomeFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app
        self._info_labels = {}

        title_row = ctk.CTkFrame(self, fg_color="transparent")
        title_row.pack(fill="x", padx=32, pady=(24, 0))
        ctk.CTkLabel(title_row, text=APP_TITLE,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkLabel(title_row, text=f"V{APP_VERSION}",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left", padx=(10, 0), pady=(6, 0))
        ctk.CTkLabel(self, text=APP_SUBTITLE,
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", padx=32, pady=(2, 12))

        # ── Device Info Panel ──────────────────────────────────────────────────
        dev_card = card(self)
        dev_card.pack(fill="x", padx=32, pady=(0, 12))

        dev_header = ctk.CTkFrame(dev_card, fg_color="transparent")
        dev_header.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(dev_header, text="\U0001f4f1  Connected Device",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        self._status_dot = ctk.CTkLabel(dev_header, text="  \u25cf  No device",
                                        font=ctk.CTkFont(size=11, weight="bold"),
                                        text_color=TEXT_MUTED, fg_color=SURFACE,
                                        corner_radius=20)
        self._status_dot.pack(side="left", padx=(12, 0))
        ghost_btn(dev_header, "\U0001f504  Refresh", self._fetch_device_info, width=100).pack(side="right")

        ctk.CTkFrame(dev_card, height=1, fg_color=BORDER).pack(fill="x", padx=16)

        info_grid = ctk.CTkFrame(dev_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=16, pady=(10, 14))
        info_grid.columnconfigure((0, 1), weight=1, uniform="col")

        fields = [
            ("\U0001f4f1", "Model",            "model"),
            ("\U0001f50b", "Battery",          "battery"),
            ("\U0001f4be", "Internal Storage", "storage"),
            ("\U0001f4c0", "SD Card",          "sdcard"),
            ("\U0001f310", "Network / SIM",    "network"),
            ("\U0001f3f7\ufe0f", "Android Version", "android"),
            ("\U0001f527", "Build / ROM",      "build"),
            ("\U0001f464", "Owner / Account",  "owner"),
        ]
        for i, (icon, label, key) in enumerate(fields):
            row_f = ctk.CTkFrame(info_grid, fg_color="transparent")
            row_f.grid(row=i // 2, column=i % 2, sticky="ew", padx=(0, 8), pady=3)
            ctk.CTkLabel(row_f, text=f"{icon}  {label}",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TEXT_MUTED, width=140, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row_f, text="\u2014",
                               font=ctk.CTkFont(size=11), anchor="w")
            lbl.pack(side="left", fill="x", expand=True)
            self._info_labels[key] = lbl

        self.after(500, self._fetch_device_info)

        grid2 = ctk.CTkFrame(self, fg_color="transparent")
        grid2.pack(fill="x", padx=32, pady=(0, 16))
        grid2.columnconfigure((0, 1, 2, 3), weight=1, uniform="col")

        quick = [
            ("\u2699\ufe0f", "Setup",   "Verify Python\n& install deps",  "setup",   ACCENT),
            ("\U0001f4be", "Backup",  "Dump full ROM\nto PC",           "backup",  "#1a6b3c"),
            ("\U0001f4c4", "Scatter", "Export GPT\nscatter file",       "scatter", "#5a3e9e"),
            ("\U0001f504", "Restore", "Flash backup\nto device",        "restore", "#7b2d00"),
        ]
        for col, (icon, label, desc, key, color) in enumerate(quick):
            c = ctk.CTkFrame(grid2, corner_radius=10, fg_color=SURFACE2,
                             border_width=1, border_color=BORDER)
            c.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")
            ctk.CTkLabel(c, text=icon, font=ctk.CTkFont(size=28)).pack(pady=(16, 4))
            ctk.CTkLabel(c, text=label, font=ctk.CTkFont(size=13, weight="bold")).pack()
            ctk.CTkLabel(c, text=desc, font=ctk.CTkFont(size=11),
                         text_color=TEXT_MUTED, justify="center").pack(pady=(2, 10))
            ctk.CTkButton(c, text="Open \u2192", height=32, corner_radius=8,
                          fg_color=color, hover_color=ACCENT_HOVER,
                          font=ctk.CTkFont(size=12),
                          command=lambda k=key: app._show(k)).pack(pady=(0, 14))

        info = card(self)
        info.pack(fill="x", padx=32, pady=(0, 24))
        ctk.CTkLabel(info, text="\u2139\ufe0f  Getting Started",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        for s in [
            "1.  Run Setup to install all dependencies",
            "2.  Select your device class in Settings (A / B / C)",
            "3.  Open Backup, set destination folder, connect phone in BROM mode",
            "4.  After backup, open Scatter to export the partition layout",
            "5.  Use Restore to flash the backup back if the device is bricked",
        ]:
            ctk.CTkLabel(info, text=s, font=ctk.CTkFont(size=12),
                         text_color=TEXT_MUTED).pack(anchor="w", padx=16, pady=1)
        ctk.CTkFrame(info, height=10, fg_color="transparent").pack()

    def _adb(self, *args):
        try:
            r = subprocess.run(["adb"] + list(args), capture_output=True, text=True, timeout=5,
                               creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            return r.stdout.strip()
        except Exception:
            return ""

    def _fetch_device_info(self):
        self._status_dot.configure(text="  \u25cf  Fetching\u2026", text_color=WARNING, fg_color="#2d2200")
        for lbl in self._info_labels.values():
            lbl.configure(text="\u2026")

        def _worker():
            devices = self._adb("devices")
            connected = any(
                line.endswith("device") and not line.startswith("List")
                for line in devices.splitlines()
            )
            if not connected:
                try:
                    from refat_backup_engine import detect_usb_devices

                    usb_devices = detect_usb_devices()
                except Exception as exc:
                    self.after(0, self._set_usb_scan_error)
                    self.app.after(0, self.app.log, f"Home USB scan failed: {exc}", "warn")
                    return

                usb_modes = {
                    (0x0E8D, 0x0003): ("MediaTek BROM", "BROM"),
                    (0x0E8D, 0x6000): ("MediaTek Preloader", "Preloader"),
                    (0x0E8D, 0x2000): ("MediaTek Preloader", "Preloader"),
                    (0x0E8D, 0x2001): ("MediaTek Preloader", "Preloader"),
                    (0x0E8D, 0x20FF): ("MediaTek Preloader", "Preloader"),
                    (0x0E8D, 0x3000): ("MediaTek Preloader", "Preloader"),
                    (0x22D9, 0x0006): ("OPPO Preloader", "Preloader"),
                }
                mtk_device = next(
                    ((vid, pid, *usb_modes[(vid, pid)])
                     for vid, pid in usb_devices if (vid, pid) in usb_modes),
                    None
                )
                if mtk_device:
                    self.after(0, self._set_usb_device, *mtk_device)
                else:
                    self.after(0, self._set_disconnected)
                return

            def prop(key):
                return self._adb("shell", "getprop", key)

            model   = prop("ro.product.model") or prop("ro.product.name")
            android = prop("ro.build.version.release")
            build   = prop("ro.build.display.id")
            owner   = self._adb("shell", "settings", "get", "global", "device_name") or "\u2014"

            bat_raw  = self._adb("shell", "dumpsys", "battery")
            bat_lvl  = next((l.split(":")[1].strip() for l in bat_raw.splitlines() if "level" in l), "?")
            bat_stat = next((l.split(":")[1].strip() for l in bat_raw.splitlines() if "status" in l), "?")
            bat_stat_map = {"1": "Unknown", "2": "Charging", "3": "Discharging", "4": "Not charging", "5": "Full"}
            battery  = f"{bat_lvl}%  ({bat_stat_map.get(bat_stat, bat_stat)})"

            stor_raw   = self._adb("shell", "df", "/data")
            stor_lines = [l for l in stor_raw.splitlines() if "/data" in l]
            if stor_lines:
                parts = stor_lines[0].split()
                try:
                    total   = round(int(parts[1]) / 1024 / 1024, 1)
                    used    = round(int(parts[2]) / 1024 / 1024, 1)
                    free    = round(int(parts[3]) / 1024 / 1024, 1)
                    storage = f"{used} GB used / {total} GB total  ({free} GB free)"
                except Exception:
                    storage = stor_lines[0]
            else:
                storage = "\u2014"

            sd_raw   = self._adb("shell", "df", "/storage/sdcard1")
            sd_lines = [l for l in sd_raw.splitlines() if "sdcard" in l or "/storage/" in l]
            if sd_lines:
                parts = sd_lines[0].split()
                try:
                    total  = round(int(parts[1]) / 1024 / 1024, 1)
                    free   = round(int(parts[3]) / 1024 / 1024, 1)
                    sdcard = f"{total} GB total  ({free} GB free)"
                except Exception:
                    sdcard = sd_lines[0]
            else:
                sdcard = "Not inserted"

            sim_op    = self._adb("shell", "getprop", "gsm.sim.operator.alpha")
            wifi_raw  = self._adb("shell", "dumpsys", "wifi")
            ssid      = next((l.split("SSID:")[1].split(",")[0].strip()
                              for l in wifi_raw.splitlines() if "SSID:" in l and "BSSID" not in l), "")
            network   = ", ".join(filter(None, [sim_op, f"Wi-Fi: {ssid}" if ssid else ""])) or "\u2014"

            data = {
                "model":   model   or "\u2014",
                "battery": battery,
                "storage": storage,
                "sdcard":  sdcard,
                "network": network,
                "android": f"Android {android}" if android else "\u2014",
                "build":   build   or "\u2014",
                "owner":   owner,
            }
            self.after(0, self._set_info, data)

        threading.Thread(target=_worker, daemon=True).start()

    def _set_usb_device(self, vid, pid, device_name, mode):
        self._status_dot.configure(
            text=f"  \u25cf  Connected ({mode})", text_color=SUCCESS, fg_color="#0d2b1a"
        )
        unavailable = f"N/A in {mode} mode"
        values = {
            "model": f"{device_name}  ({vid:04X}:{pid:04X})",
            "battery": unavailable,
            "storage": unavailable,
            "sdcard": unavailable,
            "network": unavailable,
            "android": unavailable,
            "build": unavailable,
            "owner": unavailable,
        }
        for key, value in values.items():
            self._info_labels[key].configure(text=value)

    def _set_usb_scan_error(self):
        self._status_dot.configure(text="  \u25cf  USB scan failed", text_color=WARNING,
                                   fg_color="#2d2200")
        for lbl in self._info_labels.values():
            lbl.configure(text="\u2014")
        self._info_labels["model"].configure(text="See Logs for USB scan error")

    def _set_disconnected(self):
        self._status_dot.configure(text="  \u25cf  No device", text_color=TEXT_MUTED, fg_color=SURFACE)
        for lbl in self._info_labels.values():
            lbl.configure(text="\u2014")

    def _set_info(self, data):
        self._status_dot.configure(text="  \u25cf  Connected", text_color=SUCCESS, fg_color="#0d2b1a")
        for key, val in data.items():
            if key in self._info_labels:
                self._info_labels[key].configure(text=val)


# ── Setup Frame ────────────────────────────────────────────────────────────────
class SetupFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\u2699\ufe0f  Environment Setup")
        hint(self, "  Run once before using any other feature. Verifies Python, upgrades pip, and installs all MTKClient dependencies.")

        c = card(self)
        c.pack(fill="x", padx=32, pady=(8, 0))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        section_label(inner, "PYTHON RUNTIME")
        self.py_lbl = ctk.CTkLabel(inner, text="Not checked yet",
                                   font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        self.py_lbl.pack(anchor="w", pady=(0, 8))
        primary_btn(inner, "\u25b6  Check Python", self._check_python, width=160).pack(anchor="w")

        divider(inner)

        section_label(inner, "PLATFORM")
        self.platform_lbl = ctk.CTkLabel(
            inner,
            text=f"Detected: {'Windows' if sys.platform == 'win32' else 'Linux / macOS'}",
            font=ctk.CTkFont(size=12), text_color=TEXT_MUTED
        )
        self.platform_lbl.pack(anchor="w", pady=(0, 4))

        if sys.platform != "win32":
            hint(inner, "Linux: udev rule will be written to /etc/udev/rules.d/80-mtk.rules")
            primary_btn(inner, "\u25b6  Write Udev Rule", self._write_udev, width=180).pack(anchor="w")
            divider(inner)

        section_label(inner, "DEPENDENCIES")
        hint(inner, "Installs all packages from requirements.txt into the active Python environment.")
        self.badge = status_pill(inner)
        self.prog = ctk.CTkProgressBar(inner, height=6, fg_color=SURFACE, progress_color=ACCENT)
        self.prog.pack(fill="x", pady=(8, 0))
        self.prog.set(0)
        primary_btn(inner, "\u25b6  Run Setup", self._run_setup, width=160).pack(anchor="w", pady=(12, 0))

    def _check_python(self):
        try:
            r = subprocess.run(["python", "--version"], capture_output=True, text=True)
            ver = (r.stdout + r.stderr).strip()
            self.py_lbl.configure(text=f"\u2714  {ver}", text_color=SUCCESS)
            self.app.log(f"Python found: {ver}", "ok")
        except FileNotFoundError:
            self.py_lbl.configure(text="\u2718  Python not found on PATH", text_color=DANGER)
            self.app.log("Python not found on PATH.", "error")

    def _write_udev(self):
        rule = 'SUBSYSTEM=="usb", ATTRS{idVendor}=="0e8d", MODE="0666"'
        path = "/etc/udev/rules.d/80-mtk.rules"
        try:
            subprocess.run(
                ["sudo", "bash", "-c", f'echo \'{rule}\' > {path} && udevadm control --reload-rules && udevadm trigger'],
                check=True
            )
            self.app.log(f"Udev rule written to {path}", "ok")
        except Exception as e:
            self.app.log(f"Udev write failed: {e}", "error")

    def _run_setup(self):
        if getattr(sys, "frozen", False):
            base = os.path.dirname(sys.executable)
        else:
            base = BASE_DIR
        req = os.path.join(base, "requirements.txt")
        if not os.path.exists(req):
            req = os.path.join(base, "_internal", "requirements.txt")
        if not os.path.exists(req):
            messagebox.showerror("Missing File",
                f"requirements.txt not found.\nLooked in:\n  {os.path.dirname(req)}")
            return
        set_pill(self.badge, "running")
        self.prog.configure(mode="indeterminate")
        self.prog.start()

        def _done(rc):
            self.prog.stop()
            self.prog.configure(mode="determinate")
            self.prog.set(1 if rc == 0 else 0)
            set_pill(self.badge, "ok" if rc == 0 else "error")

        self.app.run_command(
            ["python", "-m", "pip", "install", "--upgrade", "pip"],
            on_done=lambda rc: self.app.run_command(["pip", "install", "-r", req], on_done=_done)
        )


# ── Backup Frame ───────────────────────────────────────────────────────────────
class BackupFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\U0001f4be  Full ROM Backup")
        hint(self, "  Dumps all partitions (except userdata) via refat_backup_engine — preloader, boot, system, nvram, nvdata and more.")

        c = card(self)
        c.pack(fill="x", padx=32, pady=(8, 0))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        section_label(inner, "BACKUP DESTINATION")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        self.dir_var = ctk.StringVar(value=self.app.cfg.get("backup_dir", DEFAULT_BACKUP))
        ctk.CTkEntry(row, textvariable=self.dir_var, height=36,
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_btn(row, "Browse", self._browse, width=80).pack(side="left")

        divider(inner)

        section_label(inner, "SKIP PARTITIONS")
        self.skip_var = ctk.StringVar(value=self.app.cfg.get("skip_partitions", "userdata"))
        ctk.CTkEntry(inner, textvariable=self.skip_var, height=36,
                     placeholder_text="e.g. userdata,cache  (comma-separated)",
                     font=ctk.CTkFont(size=12), width=340).pack(anchor="w")
        hint(inner, "userdata is skipped by default — encrypted and can be hundreds of GB.")

        divider(inner)
        brom_steps(inner, ctk.StringVar(value=self.app.cfg.get("device_class", "A")))

        self.badge = status_pill(inner)
        self.prog = ctk.CTkProgressBar(inner, height=10, fg_color=SURFACE, progress_color=ACCENT)
        self.prog.pack(fill="x", pady=(8, 0))
        self.prog.set(0)
        self.progress_lbl = ctk.CTkLabel(inner, text="Waiting to start",
                         font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.progress_lbl.pack(anchor="w", pady=(4, 0))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(14, 0))
        primary_btn(btn_row, "\u25b6  Start Backup", self._run, width=150).pack(side="left", padx=(0, 10))
        primary_btn(btn_row, "\u23f9  Stop", self.app.stop_command,
                    color=DANGER, hover=DANGER_HOVER, width=100).pack(side="left")

    def _browse(self):
        d = filedialog.askdirectory(title="Select Backup Folder")
        if d:
            self.dir_var.set(d)

    def _update_progress(self, percent, label):
        self.prog.set(max(0.0, min(1.0, percent / 100.0)))
        self.progress_lbl.configure(text=f"{percent:.1f}%  |  {label}")

    def _run(self):
        d = self.dir_var.get().strip()
        if not d:
            messagebox.showerror("Error", "Please set a backup destination folder.")
            return
        os.makedirs(d, exist_ok=True)
        self.app.cfg.update({"backup_dir": d, "skip_partitions": self.skip_var.get().strip()})
        save_config(self.app.cfg)

        cmd = ["python", ENGINE, "backup", d, "--skip", self.skip_var.get().strip() or "userdata"]

        set_pill(self.badge, "running")
        self.prog.configure(mode="determinate")
        self.prog.set(0)
        self.progress_lbl.configure(text="Preparing backup...")

        def _done(rc):
            self.prog.set(1 if rc == 0 else 0)
            self.progress_lbl.configure(text="100.0%  |  Backup complete" if rc == 0 else "Backup failed")
            set_pill(self.badge, "ok" if rc == 0 else "error")

        self.app.run_command(cmd, on_done=_done, on_progress=self._update_progress,
                     show_logs=False)


# ── Scatter Frame ──────────────────────────────────────────────────────────────
class ScatterFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\U0001f4c4  Scatter File Generator")
        hint(self, "  Reads the device GPT partition table and exports a flashable scatter file for SP Flash Tool and UnlockTool.")

        c = card(self)
        c.pack(fill="x", padx=32, pady=(8, 0))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        section_label(inner, "OUTPUT FILE PATH")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        self.out_var = ctk.StringVar(value=os.path.join(
            self.app.cfg.get("backup_dir", DEFAULT_BACKUP), "MT6765_Android_scatter.txt"
        ))
        ctk.CTkEntry(row, textvariable=self.out_var, height=36,
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_btn(row, "Browse", self._browse, width=80).pack(side="left")

        divider(inner)

        prereq = card(inner)
        prereq.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(prereq, text="Prerequisites",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=WARNING).pack(anchor="w", padx=14, pady=(10, 4))
        for note in [
            "\u2714  Device must still be connected in BROM mode",
            "\u2714  Complete the Backup phase before generating scatter",
        ]:
            ctk.CTkLabel(prereq, text=note, font=ctk.CTkFont(size=12),
                         text_color="#cccccc").pack(anchor="w", padx=14, pady=1)
        ctk.CTkFrame(prereq, height=8, fg_color="transparent").pack()

        self.badge = status_pill(inner)

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(12, 0))
        primary_btn(btn_row, "\u25b6  Print GPT Table", self._print_gpt, width=160).pack(side="left", padx=(0, 10))
        primary_btn(btn_row, "\u25b6  Export Scatter", self._export,
                    color="#5a3e9e", hover="#7c5cbf", width=160).pack(side="left")

    def _browse(self):
        p = filedialog.asksaveasfilename(title="Save Scatter File As",
                                         defaultextension=".txt",
                                         filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if p:
            self.out_var.set(p)

    def _print_gpt(self):
        set_pill(self.badge, "running")
        self.app.run_command(
            ["python", ENGINE, "printgpt"],
            on_done=lambda rc: set_pill(self.badge, "ok" if rc == 0 else "error")
        )

    def _export(self):
        out = self.out_var.get().strip()
        if not out:
            messagebox.showerror("Error", "Please set an output file path.")
            return
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        set_pill(self.badge, "running")
        self.app.run_command(
            ["python", ENGINE, "scatter", "--output", out],
            on_done=lambda rc: set_pill(self.badge, "ok" if rc == 0 else "error")
        )


# ── Restore Frame ──────────────────────────────────────────────────────────────
class RestoreFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\U0001f504  Restore Backup")
        hint(self, "  Flashes all backed-up partition files back to the device. Hardware mismatch guard reads refat_manifest.json and blocks cross-flash.")

        warn_box = ctk.CTkFrame(self, corner_radius=10, fg_color="#2d1a00",
                                border_width=1, border_color=WARNING)
        warn_box.pack(fill="x", padx=32, pady=(0, 8))
        ctk.CTkLabel(warn_box,
                     text="\u26a0\ufe0f  This will OVERWRITE all partitions on the device. Ensure the backup is complete and valid before proceeding.",
                     font=ctk.CTkFont(size=12), text_color=WARNING,
                     wraplength=660, justify="left").pack(padx=16, pady=12)

        c = card(self)
        c.pack(fill="x", padx=32)
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        section_label(inner, "BACKUP SOURCE FOLDER")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        self.dir_var = ctk.StringVar(value=self.app.cfg.get("backup_dir", DEFAULT_BACKUP))
        ctk.CTkEntry(row, textvariable=self.dir_var, height=36,
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_btn(row, "Browse", self._browse, width=80).pack(side="left")

        self.file_count_lbl = ctk.CTkLabel(inner, text="",
                                            font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.file_count_lbl.pack(anchor="w", pady=(4, 0))

        # Manifest status
        self.manifest_lbl = ctk.CTkLabel(inner, text="",
                                          font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.manifest_lbl.pack(anchor="w", pady=(2, 0))

        ghost_btn(inner, "\U0001f50d  Scan Folder", self._scan, width=130).pack(anchor="w", pady=(6, 0))

        divider(inner)
        brom_steps(inner, ctk.StringVar(value=self.app.cfg.get("device_class", "A")))

        self.badge = status_pill(inner)
        self.prog = ctk.CTkProgressBar(inner, height=10, fg_color=SURFACE, progress_color=DANGER)
        self.prog.pack(fill="x", pady=(8, 0))
        self.prog.set(0)
        self.progress_lbl = ctk.CTkLabel(inner, text="Waiting to start",
                         font=ctk.CTkFont(size=11), text_color=TEXT_MUTED)
        self.progress_lbl.pack(anchor="w", pady=(4, 0))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(anchor="w", pady=(14, 0))
        primary_btn(btn_row, "\u25b6  Start Restore", self._run,
                    color="#7b2d00", hover="#a03a00", width=150).pack(side="left", padx=(0, 10))
        primary_btn(btn_row, "\u23f9  Stop", self.app.stop_command,
                    color=DANGER, hover=DANGER_HOVER, width=100).pack(side="left")

    def _browse(self):
        d = filedialog.askdirectory(title="Select Backup Folder")
        if d:
            self.dir_var.set(d)
            self._scan()

    def _update_progress(self, percent, label):
        self.prog.set(max(0.0, min(1.0, percent / 100.0)))
        self.progress_lbl.configure(text=f"{percent:.1f}%  |  {label}")

    def _scan(self):
        d = self.dir_var.get().strip()
        if os.path.isdir(d):
            bins = [f for f in os.listdir(d) if f.endswith(".bin")]
            self.file_count_lbl.configure(
                text=f"\u2714  {len(bins)} partition file(s) found" if bins else "\u2718  No .bin files found",
                text_color=SUCCESS if bins else DANGER
            )
            manifest_path = os.path.join(d, "refat_manifest.json")
            if os.path.exists(manifest_path):
                try:
                    with open(manifest_path) as f:
                        m = json.load(f)
                    self.manifest_lbl.configure(
                        text=f"\U0001f4cb  Manifest found — HW: {m.get('hw_code','?')}  |  Created: {m.get('created','?')[:10]}",
                        text_color=SUCCESS
                    )
                except Exception:
                    self.manifest_lbl.configure(text="\u26a0\ufe0f  Manifest unreadable", text_color=WARNING)
            else:
                self.manifest_lbl.configure(text="\u26a0\ufe0f  No manifest — mismatch guard disabled", text_color=WARNING)
        else:
            self.file_count_lbl.configure(text="\u2718  Folder not found", text_color=DANGER)
            self.manifest_lbl.configure(text="")

    def _run(self):
        d = self.dir_var.get().strip()
        if not os.path.isdir(d):
            messagebox.showerror("Error", f"Backup folder not found:\n{d}")
            return
        bins = [f for f in os.listdir(d) if f.endswith(".bin")]
        if not bins:
            messagebox.showerror("Error", "No .bin partition files found.\nRun a backup first.")
            return
        if not messagebox.askyesno("Confirm Restore",
                f"Flash {len(bins)} partition(s) from:\n{d}\n\nThis cannot be undone. Continue?"):
            return

        set_pill(self.badge, "running")
        self.prog.configure(mode="determinate")
        self.prog.set(0)
        self.progress_lbl.configure(text="Preparing restore...")

        def _done(rc):
            self.prog.set(1 if rc == 0 else 0)
            self.progress_lbl.configure(text="100.0%  |  Restore complete" if rc == 0 else "Restore failed")
            set_pill(self.badge, "ok" if rc == 0 else "error")

        self.app.run_command(["python", ENGINE, "--restore", d], on_done=_done,
                             on_progress=self._update_progress, show_logs=False)


# ── Logs Frame ─────────────────────────────────────────────────────────────────
class LogsFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(24, 8))
        ctk.CTkLabel(header, text="\U0001f4cb  Live Logs",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        ghost_btn(btn_frame, "\U0001f4be  Save", self._save, width=90).pack(side="left", padx=(0, 8))
        ghost_btn(btn_frame, "\U0001f5d1  Clear", self._clear, width=90).pack(side="left")

        filter_row = ctk.CTkFrame(self, fg_color="transparent")
        filter_row.pack(fill="x", padx=32, pady=(0, 6))
        ctk.CTkLabel(filter_row, text="Filter:",
                     font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkSegmentedButton(filter_row, values=["All", "OK", "Warn", "Error"],
                               variable=self.filter_var, width=260, height=28,
                               font=ctk.CTkFont(size=11),
                               command=self._apply_filter).pack(side="left")

        self.box = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12),
                                  wrap="word", state="disabled",
                                  fg_color=SURFACE2, border_width=1, border_color=BORDER)
        self.box.pack(fill="both", expand=True, padx=32, pady=(0, 20))

        for tag, color in [("white", "white"), ("ok", SUCCESS), ("warn", WARNING),
                            ("error", DANGER), ("cmd", "#79c0ff")]:
            self.box.tag_config(tag, foreground=color)

        self._all_lines = []

    def append(self, text, color="white"):
        tag_name = {SUCCESS: "ok", WARNING: "warn", DANGER: "error", "#79c0ff": "cmd"}.get(color, "white")
        self._all_lines.append((text, tag_name))
        self._write(text, tag_name)

    def _write(self, text, tag_name):
        self.box.configure(state="normal")
        self.box.insert("end", text + "\n", tag_name)
        self.box.see("end")
        self.box.configure(state="disabled")

    def _apply_filter(self, val):
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        self.box.configure(state="disabled")
        fmap = {"All": None, "OK": "ok", "Warn": "warn", "Error": "error"}
        f = fmap.get(val)
        for text, tag in self._all_lines:
            if f is None or tag == f:
                self._write(text, tag)

    def _clear(self):
        self._all_lines.clear()
        self.box.configure(state="normal")
        self.box.delete("1.0", "end")
        self.box.configure(state="disabled")

    def _save(self):
        path = filedialog.asksaveasfilename(title="Save Log", defaultextension=".txt",
                                             filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            with open(path, "w") as f:
                f.write(self.box.get("1.0", "end"))
            self.app.log(f"Log saved \u2192 {path}", "ok")


# ── Settings Frame ─────────────────────────────────────────────────────────────
class SettingsFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\U0001f3a8  Settings")

        # ── Disclaimer & Warnings ──────────────────────────────────────────────
        disc = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a0a00",
                            border_width=1, border_color=DANGER)
        disc.pack(fill="x", padx=32, pady=(0, 12))
        ctk.CTkLabel(disc, text="\u26a0\ufe0f  IMPORTANT \u2014 Read Before Use",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=DANGER).pack(anchor="w", padx=16, pady=(12, 6))
        warnings = [
            ("\U0001f50b", "Keep battery above 50% before any read or write operation. A disconnect mid-flash WILL brick the device."),
            ("\U0001f50c", "Never unplug the USB cable while a backup or restore is in progress. Wait for 'Done' in the Logs tab."),
            ("\U0001f4be", "Restore overwrites ALL selected partitions permanently. There is no undo. Verify your backup is complete first."),
            ("\U0001f512", "Flashing system or security partitions (e.g. persist, nvram, nvdata) can permanently damage IMEI, Wi-Fi MAC, and DRM keys."),
            ("\U0001f6ab", "Do NOT flash a backup from a different device or firmware version \u2014 it will cause a bootloop or hard brick."),
            ("\U0001f6e1\ufe0f", "This tool uses MTKClient which bypasses BROM security. Use only on devices you own. Misuse may void warranty."),
            ("\u26a1", "Use a good-quality USB cable directly into a PC port \u2014 avoid hubs. A bad cable causes incomplete transfers."),
            ("\U0001f4cb", "Always verify the scatter file matches your exact device model before flashing with SP Flash Tool."),
        ]
        for icon, text in warnings:
            row_f = ctk.CTkFrame(disc, fg_color="transparent")
            row_f.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row_f, text=icon, font=ctk.CTkFont(size=13), width=24).pack(side="left", anchor="n", pady=1)
            ctk.CTkLabel(row_f, text=text, font=ctk.CTkFont(size=11),
                         text_color="#e6c07b", wraplength=680, justify="left",
                         anchor="w").pack(side="left", padx=(8, 0), fill="x", expand=True)
        ctk.CTkFrame(disc, height=10, fg_color="transparent").pack()

        c = card(self)
        c.pack(fill="x", padx=32, pady=(8, 0))
        inner = ctk.CTkFrame(c, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        section_label(inner, "APPEARANCE")
        self.theme_var = ctk.StringVar(value=self.app.cfg.get("theme", "dark").capitalize())
        ctk.CTkLabel(inner, text="Color Theme", font=ctk.CTkFont(size=12),
                     text_color=TEXT_MUTED).pack(anchor="w")
        ctk.CTkSegmentedButton(inner, values=["Dark", "Light", "System"],
                               variable=self.theme_var, height=34,
                               command=lambda v: ctk.set_appearance_mode(v.lower())
                               ).pack(anchor="w", pady=(4, 0))

        divider(inner)

        section_label(inner, "DEVICE CLASS")
        hint(inner, "Selects the BROM connection method shown in Backup and Restore tabs.")
        self.class_var = ctk.StringVar(value=self.app.cfg.get("device_class", "A"))
        class_frame = ctk.CTkFrame(inner, fg_color="transparent")
        class_frame.pack(anchor="w", pady=(4, 0))
        for cls, label in [("A", "Class A — Legacy MT67xx"), ("B", "Class B — Dimensity/Helio"), ("C", "Class C — Samsung MTK")]:
            ctk.CTkRadioButton(class_frame, text=label, variable=self.class_var, value=cls,
                               font=ctk.CTkFont(size=12)).pack(anchor="w", pady=2)

        divider(inner)

        section_label(inner, "DEFAULT BACKUP DIRECTORY")
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=(0, 4))
        self.dir_var = ctk.StringVar(value=self.app.cfg.get("backup_dir", DEFAULT_BACKUP))
        ctk.CTkEntry(row, textvariable=self.dir_var, height=36,
                     font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ghost_btn(row, "Browse", self._browse_dir, width=80).pack(side="left")

        divider(inner)

        section_label(inner, "DEFAULT SKIP PARTITIONS")
        self.skip_var = ctk.StringVar(value=self.app.cfg.get("skip_partitions", "userdata"))
        ctk.CTkEntry(inner, textvariable=self.skip_var, height=36,
                     font=ctk.CTkFont(size=12), width=320).pack(anchor="w")

        divider(inner)

        section_label(inner, "LOG OPTIONS")
        self.ts_var = ctk.BooleanVar(value=self.app.cfg.get("timestamps", True))
        ctk.CTkCheckBox(inner, text="Show timestamps in logs",
                        variable=self.ts_var, font=ctk.CTkFont(size=12)).pack(anchor="w")

        divider(inner)

        save_row = ctk.CTkFrame(inner, fg_color="transparent")
        save_row.pack(anchor="w", pady=(4, 0))
        primary_btn(save_row, "\U0001f4be  Save Settings", self._save, width=160).pack(side="left")
        self.saved_lbl = ctk.CTkLabel(save_row, text="",
                                       font=ctk.CTkFont(size=12), text_color=SUCCESS)
        self.saved_lbl.pack(side="left", padx=(14, 0))

    def _browse_dir(self):
        d = filedialog.askdirectory(title="Select Default Backup Folder")
        if d:
            self.dir_var.set(d)

    def _save(self):
        self.app.cfg.update({
            "theme":           self.theme_var.get().lower(),
            "backup_dir":      self.dir_var.get().strip(),
            "skip_partitions": self.skip_var.get().strip(),
            "timestamps":      self.ts_var.get(),
            "device_class":    self.class_var.get(),
        })
        save_config(self.app.cfg)
        self.app.frames["backup"].dir_var.set(self.app.cfg["backup_dir"])
        self.app.frames["restore"].dir_var.set(self.app.cfg["backup_dir"])
        self.saved_lbl.configure(text="\u2714  Saved")
        self.after(3000, lambda: self.saved_lbl.configure(text=""))


# ── About Frame ────────────────────────────────────────────────────────────────
class AboutFrame(ctk.CTkScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, corner_radius=0, fg_color="transparent")
        self.app = app

        page_title(self, "\u2139\ufe0f  About")

        app_card = card(self)
        app_card.pack(fill="x", padx=32, pady=(8, 12))
        app_inner = ctk.CTkFrame(app_card, fg_color="transparent")
        app_inner.pack(fill="x", padx=20, pady=18)
        section_label(app_inner, "APPLICATION")
        ctk.CTkLabel(app_inner, text=APP_TITLE,
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(app_inner, text=f"Version V{APP_VERSION}  \u2022  {APP_SUBTITLE}",
                     font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(anchor="w", pady=(3, 8))
        ctk.CTkLabel(app_inner, text=APP_DESCRIPTION,
                     font=ctk.CTkFont(size=12), text_color="#cccccc",
                     wraplength=680, justify="left", anchor="w").pack(anchor="w", fill="x")

        developer_card = card(self)
        developer_card.pack(fill="x", padx=32, pady=(0, 20))
        developer_inner = ctk.CTkFrame(developer_card, fg_color="transparent")
        developer_inner.pack(fill="x", padx=20, pady=18)
        section_label(developer_inner, "DEVELOPER & CONTACT")

        details = [
            ("Developer", APP_DEVELOPER, None),
            ("Email", APP_EMAIL, f"mailto:{APP_EMAIL}"),
            ("Website", APP_WEBSITE, f"https://{APP_WEBSITE}"),
            ("GitHub", APP_REPOSITORY, APP_REPOSITORY),
        ]
        for label, value, url in details:
            row = ctk.CTkFrame(developer_inner, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=label, width=100, anchor="w",
                         font=ctk.CTkFont(size=12), text_color=TEXT_MUTED).pack(side="left")
            if url:
                ctk.CTkButton(row, text=value, command=lambda link=url: webbrowser.open(link),
                              anchor="w", height=30, fg_color="transparent",
                              hover_color=SURFACE2, text_color=ACCENT_HOVER,
                              font=ctk.CTkFont(size=12), corner_radius=6).pack(side="left", fill="x", expand=True)
            else:
                ctk.CTkLabel(row, text=value, anchor="w",
                             font=ctk.CTkFont(size=12)).pack(side="left", fill="x", expand=True)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if getattr(sys, "frozen", False) and len(sys.argv) > 1 and sys.argv[1] == "--refat-engine-worker":
        for stream_name, stream_fd in (("stdout", 1), ("stderr", 2)):
            if getattr(sys, stream_name) is None:
                try:
                    setattr(sys, stream_name, os.fdopen(
                        stream_fd, "w", encoding="utf-8", buffering=1, closefd=False
                    ))
                except OSError:
                    pass
        import refat_backup_engine
        raise SystemExit(refat_backup_engine.main(sys.argv[2:]))

    splash_root = ctk.CTk()
    splash_root.withdraw()
    splash = SplashScreen()
    splash.update()

    def _launch():
        splash.destroy()
        splash_root.destroy()
        app = MTKApp()
        app.mainloop()

    splash_root.after(2200, _launch)
    splash_root.mainloop()
