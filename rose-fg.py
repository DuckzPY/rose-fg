import socket
import threading
import urllib.request, urllib.parse
import subprocess
import json
import os
import sys
import platform
import hashlib
import base64
import random
import string
import re
import time
import datetime
import ssl
import uuid
import difflib
import qrcode
from io import BytesIO
from PIL import ExifTags, Image, ImageTk
import customtkinter as ctk
from tkinter import colorchooser, ttk, filedialog
import tkinter as tk

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".rose-fg_settings.json")
NOTES_FILE    = os.path.join(os.path.expanduser("~"), ".rose-fg_notes.txt")

def load_settings():
    defaults = {"theme": "dark", "accent": "blue", "opacity": 1.0, "font_size": 12, "default_tab": "OSINT"}
    try:
        with open(SETTINGS_FILE) as f:
            data = json.load(f)
            defaults.update(data)
    except:
        pass
    return defaults

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f)

settings = load_settings()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

stop_flag = False

SERVICES = {
    21:"FTP", 22:"SSH", 23:"Telnet", 25:"SMTP", 53:"DNS", 80:"HTTP", 110:"POP3",
    135:"RPC", 139:"NetBIOS", 143:"IMAP", 443:"HTTPS", 445:"SMB", 993:"IMAPS",
    995:"POP3S", 1433:"MSSQL", 3306:"MySQL", 3389:"RDP", 5432:"PostgreSQL",
    5900:"VNC", 6379:"Redis", 8080:"HTTP-Alt", 8443:"HTTPS-Alt", 27017:"MongoDB", 631:"IPP",
}

C = {
    "bg":        "#080008",
    "sidebar":   "#060006",
    "card":      "#0f000a",
    "card2":     "#1a0010",
    "border":    "#2a0015",
    "green":     "#FF0054",
    "green_dim": "#cc0040",
    "green_dark":"#1a0010",
    "blue":      "#cc3366",
    "red":       "#E24B4A",
    "yellow":    "#EF9F27",
    "cyan":      "#ff6688",
    "text":      "#ffffff",
    "text_dim":  "#888888",
    "text_muted":"#444444",
    "accent":    "#FF0054",
    "Ready":     "#00FF54",
    "term_bg":   "#1a1a1a",
    "term_text": "#ffffff",
    "term_red":  "#ff4444",
    "term_green":"#44ff88",
    "term_yellow":"#ffcc00",
}
FONT_MONO   = "JetBrains Mono"
FONT_UI     = "Inter"
FONT_HEADER = "Inter"

app = ctk.CTk()
app.title("rose-fg  v7.0")
app.geometry("1080x720")
app.resizable(True, True)
app.configure(fg_color=C["bg"])

style = ttk.Style()
style.theme_use("default")

sidebar_outer = ctk.CTkFrame(app, width=230, corner_radius=0, fg_color=C["sidebar"], border_width=0)
sidebar_outer.pack(side="left", fill="y")
sidebar_outer.pack_propagate(False)

sidebar = ctk.CTkScrollableFrame(sidebar_outer, fg_color="transparent",
                                  scrollbar_button_color=C["text_muted"],
                                  scrollbar_button_hover_color=C["green_dim"])
sidebar.pack(fill="both", expand=True, padx=0, pady=0)

logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
logo_frame.pack(fill="x", pady=(20, 8), padx=16)

_logo_img_ref = [None]
try:
    _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rose_logo.png")
    _logo_pil  = Image.open(_logo_path).resize((42, 42), Image.LANCZOS)
    _logo_ctk  = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(42, 42))
    _logo_img_ref[0] = _logo_ctk
    logo_img_label = ctk.CTkLabel(logo_frame, image=_logo_ctk, text="")
    logo_img_label.pack(side="left", padx=(0, 10), pady=4)
except Exception:
    dot_canvas = tk.Canvas(logo_frame, width=10, height=10, bg=C["sidebar"], highlightthickness=0)
    dot_canvas.pack(side="left", padx=(0, 8), pady=6)
    dot = dot_canvas.create_oval(1, 1, 9, 9, fill=C["green"], outline="")
    def pulse_dot(alpha=255, direction=-1):
        colors = [int(255*(alpha/255)), int(30*(alpha/255)), int(70*(alpha/255))]
        hex_col = "#{:02x}{:02x}{:02x}".format(*colors)
        try:
            dot_canvas.itemconfig(dot, fill=hex_col)
            new_alpha = alpha + direction * 8
            if new_alpha <= 60: direction = 1
            if new_alpha >= 255: direction = -1
            app.after(40, lambda: pulse_dot(new_alpha, direction))
        except Exception: pass
    pulse_dot()

logo_text = ctk.CTkFrame(logo_frame, fg_color="transparent")
logo_text.pack(side="left")
ctk.CTkLabel(logo_text, text="rose-fg",
             font=ctk.CTkFont(family=FONT_HEADER, size=16, weight="bold"),
             text_color=C["green"]).pack(anchor="w")
ctk.CTkLabel(logo_text, text="v7.0",
             font=ctk.CTkFont(family=FONT_HEADER, size=10),
             text_color=C["text_dim"]).pack(anchor="w")

def _divider(parent, color=C["border"], pady=6):
    ctk.CTkFrame(parent, height=1, fg_color=color).pack(fill="x", padx=12, pady=pady)

_divider(sidebar, C["green_dark"], 4)

current_frame = [None]
active_btn    = [None]

def show(frame, btn=None):
    if current_frame[0]:
        current_frame[0].pack_forget()
    if active_btn[0] and active_btn[0] != btn:
        active_btn[0].configure(fg_color="transparent", text_color=C["text_dim"])
    frame.pack(fill="both", expand=True)
    current_frame[0] = frame
    if btn:
        btn.configure(fg_color=C["green_dark"], text_color=C["green"])
        active_btn[0] = btn

def make_section(label, submenus, frames):
    visible = [False]
    emoji_fallback = {
        "OSINT":"⬡","Port Scanner":"◈","Network":"◎","Discord":"◆",
        "Passwords":"◈","Encoding":"▣","System Info":"◉","Web Tools":"◎",
        "File Tools":"▤","Crypto":"◆","Social Media":"◈","Text Tools":"▦",
        "QR Code":"▣","Notes":"▦","Settings":"◎",
        "Generators":"◈","Dev Tools":"◈","Converters":"▣",
    }
    icon = emoji_fallback.get(label, "•")
    sub_frame = ctk.CTkFrame(sidebar, fg_color="transparent")

    section_btn = ctk.CTkButton(
        sidebar, text=f"  {icon}  {label}", anchor="w",
        fg_color="transparent", text_color=C["text_dim"],
        hover_color=C["card2"],
        font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"), height=32,
        corner_radius=6,
    )

    def toggle():
        visible[0] = not visible[0]
        if visible[0]:
            sub_frame.pack(fill="x", after=section_btn, pady=(0,2))
            section_btn.configure(text_color=C["text"])
        else:
            sub_frame.pack_forget()
            section_btn.configure(text_color=C["text_dim"])

    section_btn.configure(command=toggle)
    section_btn.pack(fill="x", padx=8, pady=1)

    for name, frame in zip(submenus, frames):
        b = ctk.CTkButton(
            sub_frame, text=f"    ╴  {name}", anchor="w",
            fg_color="transparent", text_color=C["text_muted"],
            hover_color=C["card"],
            font=ctk.CTkFont(family=FONT_UI, size=11), height=26,
            corner_radius=4,
        )
        b.configure(command=lambda f=frame, btn=b: show(f, btn))
        b.pack(fill="x", padx=10, pady=1)

content_outer = ctk.CTkFrame(app, fg_color=C["bg"])
content_outer.pack(side="left", fill="both", expand=True)

statusbar = ctk.CTkFrame(content_outer, height=28, fg_color=C["sidebar"], corner_radius=0)
statusbar.pack(fill="x")
statusbar.pack_propagate(False)

def update_clock():
    now = datetime.datetime.now().strftime("%H:%M:%S  ·  %d %b %Y")
    clock_label.configure(text=now)
    app.after(1000, update_clock)

clock_label = ctk.CTkLabel(statusbar, text="", font=ctk.CTkFont(family=FONT_MONO, size=10),
                            text_color=C["text_dim"])
clock_label.pack(side="right", padx=16, pady=4)
update_clock()

status_dot2 = ctk.CTkLabel(statusbar, text="● READY", font=ctk.CTkFont(family=FONT_MONO, size=10),
                             text_color=C["Ready"])
status_dot2.pack(side="left", padx=16, pady=4)

content = ctk.CTkFrame(content_outer, fg_color="transparent")
content.pack(fill="both", expand=True, padx=24, pady=20)

# ─── TERMINAL OUTPUT ──────────────────────────────────────────────────────────
def outbox(parent, height=320):
    fs = settings["font_size"]
    outer = ctk.CTkFrame(parent, fg_color=C["term_bg"], corner_radius=8,
                          border_width=1, border_color="#333333")
    outer.pack(fill="both", expand=True, pady=(8, 0))
    bar = ctk.CTkFrame(outer, height=24, fg_color="#111111", corner_radius=0)
    bar.pack(fill="x")
    ctk.CTkLabel(bar, text="  OUTPUT", font=ctk.CTkFont(family=FONT_MONO, size=9),
                 text_color="#555555").pack(side="left", padx=8, pady=3)
    for col in ["#ff4444", "#ffcc00", "#44ff88"]:
        ctk.CTkFrame(bar, width=8, height=8, corner_radius=4, fg_color=col).pack(
            side="right", padx=3, pady=8)
    box = ctk.CTkTextbox(outer, height=height,
                          font=ctk.CTkFont(family=FONT_MONO, size=fs),
                          fg_color=C["term_bg"], text_color=C["term_text"],
                          scrollbar_button_color="#333333",
                          wrap="word")
    box.pack(fill="both", expand=True, padx=4, pady=4)
    box.configure(state="disabled")
    box.tag_config("green",  foreground=C["term_green"])
    box.tag_config("red",    foreground=C["term_red"])
    box.tag_config("blue",   foreground="#88aaff")
    box.tag_config("yellow", foreground=C["term_yellow"])
    box.tag_config("cyan",   foreground="#88ddff")
    box.tag_config("dim",    foreground="#888888")
    return box

def write(box, msg, tag=None):
    box.configure(state="normal")
    box.insert("end", msg + "\n", tag or "")
    box.see("end")
    box.configure(state="disabled")
    app.update_idletasks()

def clear(box):
    box.configure(state="normal")
    box.delete("1.0", "end")
    box.configure(state="disabled")

def title(parent, text, subtitle=None):
    hdr = ctk.CTkFrame(parent, fg_color="transparent")
    hdr.pack(fill="x", pady=(0, 16))
    accent = ctk.CTkFrame(hdr, width=3, height=38, fg_color=C["green"], corner_radius=2)
    accent.pack(side="left", padx=(0, 12))
    accent.pack_propagate(False)
    txt_frame = ctk.CTkFrame(hdr, fg_color="transparent")
    txt_frame.pack(side="left")
    ctk.CTkLabel(txt_frame, text=text,
                 font=ctk.CTkFont(family=FONT_HEADER, size=20, weight="bold"),
                 text_color=C["text"]).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(txt_frame, text=subtitle,
                     font=ctk.CTkFont(family=FONT_UI, size=11),
                     text_color=C["text_dim"]).pack(anchor="w")

def card(parent, **kwargs):
    return ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=10,
                         border_width=1, border_color=C["border"], **kwargs)

def irow(parent):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    f.pack(fill="x", pady=(0, 8))
    return f

def lentry(parent, label, placeholder, show_char=""):
    ctk.CTkLabel(parent, text=label, anchor="w",
                 font=ctk.CTkFont(family=FONT_UI, size=11),
                 text_color=C["text_dim"]).pack(fill="x")
    e = ctk.CTkEntry(parent, placeholder_text=placeholder, show=show_char,
                     fg_color=C["card2"], border_color=C["border"],
                     text_color=C["text"], placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     corner_radius=6, border_width=1)
    e.pack(fill="x", pady=(2, 8))
    return e

def mk_btn(parent, text, command=None, width=120, danger=False, muted=False, **kw):
    fg    = C["red"]      if danger else (C["card2"]     if muted else C["green_dark"])
    hover = "#991111"     if danger else (C["card"]       if muted else "#550018")
    txt   = "#ffffff"     if danger else (C["text_dim"]   if muted else C["green"])
    b = ctk.CTkButton(parent, text=text, command=command, width=width,
                      fg_color=fg, hover_color=hover, text_color=txt,
                      border_width=1,
                      border_color=C["red"] if danger else (C["border"] if muted else C["green_dark"]),
                      font=ctk.CTkFont(family=FONT_UI, size=12),
                      corner_radius=6, **kw)
    return b

def make_drag_drop_entry(parent, label, placeholder):
    ctk.CTkLabel(parent, text=label, anchor="w",
                 font=ctk.CTkFont(family=FONT_UI, size=11),
                 text_color=C["text_dim"]).pack(fill="x")
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", pady=(2, 8))
    e = ctk.CTkEntry(row, placeholder_text=placeholder,
                     fg_color=C["card2"], border_color=C["border"],
                     text_color=C["text"], placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11),
                     corner_radius=6, border_width=1)
    e.pack(side="left", expand=True, fill="x")
    def browse():
        path = filedialog.askopenfilename()
        if path:
            e.delete(0, "end")
            e.insert(0, path)
    mk_btn(row, "Browse", width=80, muted=True, command=browse).pack(side="left", padx=(8, 0))
    drop_zone = ctk.CTkFrame(parent, height=36, fg_color=C["card2"],
                              corner_radius=6, border_width=1, border_color=C["border"])
    drop_zone.pack(fill="x", pady=(0, 8))
    drop_zone.pack_propagate(False)
    drop_label = ctk.CTkLabel(drop_zone, text="  ↓  Drag & drop file here",
                               font=ctk.CTkFont(family=FONT_UI, size=10),
                               text_color=C["text_muted"])
    drop_label.pack(expand=True)
    def on_drag_enter(event):
        drop_zone.configure(border_color=C["green"])
        drop_label.configure(text="  ↓  Release to load file", text_color=C["green"])
    def on_drag_leave(event):
        drop_zone.configure(border_color=C["border"])
        drop_label.configure(text="  ↓  Drag & drop file here", text_color=C["text_muted"])
    def on_drop(event):
        path = event.data if hasattr(event, "data") else ""
        if not path:
            raw = event.widget.tk.call("event", "info")
            path = str(raw).strip()
        path = path.strip("{}")
        if path and os.path.exists(path):
            e.delete(0, "end")
            e.insert(0, path)
        drop_zone.configure(border_color=C["border"])
        drop_label.configure(text="  ↓  Drag & drop file here", text_color=C["text_muted"])
    try:
        drop_zone.drop_target_register("DND_Files")
        drop_zone.dnd_bind("<<DropEnter>>", on_drag_enter)
        drop_zone.dnd_bind("<<DropLeave>>", on_drag_leave)
        drop_zone.dnd_bind("<<Drop>>", on_drop)
        drop_label.drop_target_register("DND_Files")
        drop_label.dnd_bind("<<DropEnter>>", on_drag_enter)
        drop_label.dnd_bind("<<DropLeave>>", on_drag_leave)
        drop_label.dnd_bind("<<Drop>>", on_drop)
    except Exception:
        pass
    return e

# ════════════════════════════════════════════════════════════
#  OSINT
# ════════════════════════════════════════════════════════════

f_ip = ctk.CTkFrame(content, fg_color="transparent")
title(f_ip, "IP / Domain Lookup", "Geolocation, ISP, ASN and threat intelligence")
c = card(f_ip); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_ip = ctk.CTkEntry(r, placeholder_text="IP address or domain  —  e.g.  8.8.8.8 / google.com",
                     fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                     placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_ip.pack(side="left", expand=True, fill="x")
btn_ip = mk_btn(r, "  Lookup", width=110); btn_ip.pack(side="left", padx=(10, 0))
out_ip = outbox(f_ip)

def do_ip():
    t = e_ip.get().strip(); clear(out_ip)
    write(out_ip, f"  Resolving {t}...\n", "dim")
    try:
        ip = socket.gethostbyname(t)
        d = json.loads(urllib.request.urlopen(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,zip,isp,org,as,query,reverse,mobile,proxy,hosting",
            timeout=5).read())
        if d["status"] == "success":
            write(out_ip, f"  IP Address   :  {d['query']}")
            write(out_ip, f"  Hostname     :  {d.get('reverse', 'N/A')}")
            write(out_ip, f"  Country      :  {d['country']}")
            write(out_ip, f"  Region       :  {d['regionName']}")
            write(out_ip, f"  City         :  {d['city']}")
            write(out_ip, f"  Postcode     :  {d['zip']}")
            write(out_ip, f"  ISP          :  {d['isp']}")
            write(out_ip, f"  Organisation :  {d['org']}")
            write(out_ip, f"  ASN          :  {d['as']}")
            write(out_ip, f"  Mobile       :  {'Yes' if d['mobile'] else 'No'}", "green" if d["mobile"] else "dim")
            write(out_ip, f"  Proxy/VPN    :  {'Yes' if d['proxy'] else 'No'}", "yellow" if d["proxy"] else "dim")
            write(out_ip, f"  Hosting      :  {'Yes' if d['hosting'] else 'No'}", "blue" if d["hosting"] else "dim")
        else:
            write(out_ip, "  Lookup failed.", "red")
    except Exception as e:
        write(out_ip, f"  Error: {e}", "red")

btn_ip.configure(command=lambda: threading.Thread(target=do_ip, daemon=True).start())

# ── Email Header Analyser ──────────────────────────────────
f_email = ctk.CTkFrame(content, fg_color="transparent")
title(f_email, "Email Header Analyser", "Extract IPs, sender info and routing from raw headers")
ctk.CTkLabel(f_email, text="Paste raw email headers below:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
email_in = ctk.CTkTextbox(f_email, height=130, fg_color=C["card"], border_width=1,
                           border_color=C["border"], text_color=C["text"],
                           font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
email_in.pack(fill="x", pady=(4, 8))
mk_btn(f_email, "  Analyse Headers", width=160, command=lambda: do_email()).pack(anchor="w")
out_email = outbox(f_email, height=200)

def do_email():
    text = email_in.get("1.0", "end"); clear(out_email)
    ips = list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))
    for label, pattern in [("Subject", "Subject:.*"), ("From", "From:.*"),
                            ("Reply-To", "Reply-To:.*"), ("Date", "Date:.*"),
                            ("To", "To:.*"), ("Message-ID", "Message-ID:.*"),
                            ("X-Mailer", "X-Mailer:.*"), ("MIME-Version", "MIME-Version:.*")]:
        match = re.findall(pattern, text)
        write(out_email, f"  {label:<14} :  {match[0].strip() if match else 'Not found'}")
    write(out_email, f"\n  IPs extracted:", "cyan")
    if ips:
        for ip in ips: write(out_email, f"    {ip}", "green")
    else:
        write(out_email, "    None found.", "dim")
    spf  = re.findall(r'(spf=\S+)',  text, re.IGNORECASE)
    dkim = re.findall(r'(dkim=\S+)', text, re.IGNORECASE)
    dmarc= re.findall(r'(dmarc=\S+)',text, re.IGNORECASE)
    write(out_email, f"\n  Auth Results:", "dim")
    write(out_email, f"  SPF   :  {spf[0] if spf else 'not found'}",   "green" if spf  and "pass" in spf[0].lower()  else "yellow")
    write(out_email, f"  DKIM  :  {dkim[0] if dkim else 'not found'}", "green" if dkim and "pass" in dkim[0].lower() else "yellow")
    write(out_email, f"  DMARC :  {dmarc[0] if dmarc else 'not found'}","green" if dmarc and "pass" in dmarc[0].lower() else "yellow")

# ── WHOIS ─────────────────────────────────────────────────
f_whois = ctk.CTkFrame(content, fg_color="transparent")
title(f_whois, "WHOIS Lookup", "Domain registration and ownership info")
c = card(f_whois); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_whois = ctk.CTkEntry(r, placeholder_text="e.g. google.com",
                        fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                        placeholder_text_color=C["text_muted"],
                        font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_whois.pack(side="left", expand=True, fill="x")
btn_w = mk_btn(r, "  Lookup", width=110); btn_w.pack(side="left", padx=(10, 0))
out_whois = outbox(f_whois)

def do_whois():
    t = e_whois.get().strip(); clear(out_whois)
    write(out_whois, f"  Running WHOIS for {t}...\n", "dim")
    try:
        subprocess.run(["whois", "--version"], capture_output=True, timeout=3)
        whois_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        whois_available = False
    if whois_available:
        try:
            r2 = subprocess.run(["whois", t], capture_output=True, text=True, timeout=10)
            write(out_whois, r2.stdout or "No output.")
            return
        except Exception as e:
            write(out_whois, f"  whois command failed: {e}\n  Falling back...\n", "yellow")
    try:
        import whois as pywhois
        data = pywhois.whois(t)
        write(out_whois, f"  Domain      :  {data.domain_name}", "green")
        write(out_whois, f"  Registrar   :  {data.registrar}")
        write(out_whois, f"  Created     :  {data.creation_date}")
        write(out_whois, f"  Expires     :  {data.expiration_date}")
        write(out_whois, f"  Updated     :  {data.updated_date}")
        write(out_whois, f"  Name Servers:  {data.name_servers}")
        write(out_whois, f"  Status      :  {data.status}")
        write(out_whois, f"  Emails      :  {data.emails}")
        return
    except ImportError:
        pass
    except Exception as e:
        write(out_whois, f"  python-whois error: {e}\n", "red")
    write(out_whois, "  python-whois not installed. Attempting pip install...", "yellow")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "python-whois", "--quiet"], timeout=30, check=True)
        import whois as pywhois
        data = pywhois.whois(t)
        write(out_whois, f"  Installed successfully!\n", "green")
        write(out_whois, f"  Domain      :  {data.domain_name}", "green")
        write(out_whois, f"  Registrar   :  {data.registrar}")
        write(out_whois, f"  Created     :  {data.creation_date}")
        write(out_whois, f"  Expires     :  {data.expiration_date}")
    except Exception as e:
        write(out_whois, f"  Auto-install failed: {e}", "red")

btn_w.configure(command=lambda: threading.Thread(target=do_whois, daemon=True).start())

# ── Reverse DNS ────────────────────────────────────────────
f_rdns = ctk.CTkFrame(content, fg_color="transparent")
title(f_rdns, "Reverse DNS", "Resolve an IP address back to its hostname")
c = card(f_rdns); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_rdns = ctk.CTkEntry(r, placeholder_text="IP address  e.g.  8.8.8.8",
                       fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                       placeholder_text_color=C["text_muted"],
                       font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_rdns.pack(side="left", expand=True, fill="x")
btn_rdns = mk_btn(r, "  Resolve", width=110); btn_rdns.pack(side="left", padx=(10, 0))
out_rdns = outbox(f_rdns)

def do_rdns():
    ip = e_rdns.get().strip(); clear(out_rdns)
    try:
        h = socket.gethostbyaddr(ip)
        write(out_rdns, f"  IP        :  {ip}", "cyan")
        write(out_rdns, f"  Hostname  :  {h[0]}", "green")
        write(out_rdns, f"  Aliases   :  {', '.join(h[1]) or 'None'}")
    except Exception as e:
        write(out_rdns, f"  Error: {e}", "red")

btn_rdns.configure(command=lambda: threading.Thread(target=do_rdns, daemon=True).start())

# ── SSL Checker ────────────────────────────────────────────
f_ssl = ctk.CTkFrame(content, fg_color="transparent")
title(f_ssl, "SSL/TLS Certificate Checker", "Inspect SSL certificates, expiry, and chain info")
c = card(f_ssl); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_ssl = ctk.CTkEntry(r, placeholder_text="Domain  e.g.  google.com",
                      fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                      placeholder_text_color=C["text_muted"],
                      font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_ssl.pack(side="left", expand=True, fill="x")
btn_ssl = mk_btn(r, "  Check SSL", width=120); btn_ssl.pack(side="left", padx=(10, 0))
out_ssl = outbox(f_ssl)

def do_ssl():
    domain = e_ssl.get().strip().replace("https://","").replace("http://","").split("/")[0]
    clear(out_ssl)
    write(out_ssl, f"  Connecting to {domain}:443...\n", "dim")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(8)
            s.connect((domain, 443))
            cert     = s.getpeercert()
            protocol = s.version()
        subject    = dict(x[0] for x in cert.get("subject", []))
        issuer     = dict(x[0] for x in cert.get("issuer", []))
        not_before = cert.get("notBefore", "N/A")
        not_after  = cert.get("notAfter",  "N/A")
        try:
            exp_dt    = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_left = (exp_dt - datetime.datetime.utcnow()).days
            expiry_tag = "green" if days_left > 30 else ("yellow" if days_left > 7 else "red")
            expiry_str = f"{not_after}  ({days_left} days remaining)"
        except:
            days_left = -1; expiry_tag = "dim"; expiry_str = not_after
        sans = [v for t2, v in cert.get("subjectAltName", []) if t2 == "DNS"]
        write(out_ssl, f"  Common Name   :  {subject.get('commonName', 'N/A')}")
        write(out_ssl, f"  Organisation  :  {subject.get('organizationName', 'N/A')}")
        write(out_ssl, f"  Issued By     :  {issuer.get('organizationName', 'N/A')}", "blue")
        write(out_ssl, f"  Valid From    :  {not_before}", "dim")
        write(out_ssl, f"  Expires       :  {expiry_str}", expiry_tag)
        write(out_ssl, f"  Protocol      :  {protocol}", "cyan")
        write(out_ssl, f"  Serial No.    :  {cert.get('serialNumber', 'N/A')}", "dim")
        write(out_ssl, f"\n  Subject Alt Names ({len(sans)}):", "dim")
        if sans:
            for san in sans[:12]: write(out_ssl, f"    {san}", "green")
            if len(sans) > 12: write(out_ssl, f"    ... and {len(sans)-12} more", "dim")
        else:
            write(out_ssl, "    None", "dim")
        if days_left < 0:
            write(out_ssl, "\n  Certificate has EXPIRED!", "red")
        elif days_left <= 7:
            write(out_ssl, f"\n  WARNING: Expires in {days_left} day(s)!", "red")
        elif days_left <= 30:
            write(out_ssl, f"\n  Certificate expiring soon ({days_left} days).", "yellow")
        else:
            write(out_ssl, f"\n  Certificate valid — {days_left} days remaining.", "green")
    except ssl.SSLCertVerificationError as e:
        write(out_ssl, f"  SSL Verification Failed: {e}", "red")
    except Exception as e:
        write(out_ssl, f"  Error: {e}", "red")

btn_ssl.configure(command=lambda: threading.Thread(target=do_ssl, daemon=True).start())

# ── Subnet Calculator ──────────────────────────────────────
f_subnet = ctk.CTkFrame(content, fg_color="transparent")
title(f_subnet, "Subnet Calculator", "Calculate network address, broadcast, host range and more")
c = card(f_subnet); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_subnet = ctk.CTkEntry(r, placeholder_text="e.g.  192.168.1.0/24  or  10.0.0.1/255.255.255.0",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_subnet.pack(side="left", expand=True, fill="x")
btn_subnet = mk_btn(r, "  Calculate", width=120); btn_subnet.pack(side="left", padx=(10, 0))
out_subnet = outbox(f_subnet)

def do_subnet():
    raw = e_subnet.get().strip(); clear(out_subnet)
    try:
        import ipaddress
        net   = ipaddress.ip_network(raw, strict=False)
        hosts = list(net.hosts())
        write(out_subnet, f"  Network       :  {net.network_address}", "cyan")
        write(out_subnet, f"  Broadcast     :  {net.broadcast_address}", "yellow")
        write(out_subnet, f"  Subnet Mask   :  {net.netmask}")
        write(out_subnet, f"  Wildcard      :  {net.hostmask}", "dim")
        write(out_subnet, f"  CIDR Prefix   :  /{net.prefixlen}")
        write(out_subnet, f"  Total IPs     :  {net.num_addresses:,}")
        write(out_subnet, f"  Usable Hosts  :  {len(hosts):,}", "green")
        if hosts:
            write(out_subnet, f"  First Host    :  {hosts[0]}", "green")
            write(out_subnet, f"  Last Host     :  {hosts[-1]}", "green")
        write(out_subnet, f"  IP Version    :  IPv{net.version}")
        write(out_subnet, f"  Is Private    :  {'Yes' if net.is_private else 'No'}", "blue" if net.is_private else "")
        write(out_subnet, f"\n  First 4 usable subnets (/28 each):", "dim")
        try:
            for i, sub in enumerate(net.subnets(new_prefix=min(net.prefixlen+4, 30))):
                if i >= 4: break
                write(out_subnet, f"    {sub}", "green")
        except: pass
    except Exception as e:
        write(out_subnet, f"  Error: {e}", "red")

btn_subnet.configure(command=lambda: threading.Thread(target=do_subnet, daemon=True).start())

# ── DNS Records ────────────────────────────────────────────
f_dnsrec = ctk.CTkFrame(content, fg_color="transparent")
title(f_dnsrec, "DNS Records", "Query A, MX, TXT, NS and CNAME records")
c = card(f_dnsrec); c.pack(fill="x", pady=(0, 12))
r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=14, pady=14)
e_dnsrec = ctk.CTkEntry(r, placeholder_text="Domain  e.g.  google.com",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_dnsrec.pack(side="left", expand=True, fill="x")
btn_dnsrec = mk_btn(r, "  Query", width=110); btn_dnsrec.pack(side="left", padx=(10, 0))
out_dnsrec = outbox(f_dnsrec)

def do_dnsrec():
    domain = e_dnsrec.get().strip(); clear(out_dnsrec)
    write(out_dnsrec, f"  Querying DNS records for {domain}...\n", "dim")
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]:
            try:
                answers = resolver.resolve(domain, rtype)
                write(out_dnsrec, f"  {rtype} Records:", "cyan")
                for rdata in answers:
                    write(out_dnsrec, f"    {rdata}", "green")
            except Exception:
                write(out_dnsrec, f"  {rtype} Records:  none", "dim")
    except ImportError:
        write(out_dnsrec, "  dnspython not found. Falling back to basic resolution...", "yellow")
        try:
            ips = socket.getaddrinfo(domain, None)
            unique_ips = list(dict.fromkeys(r2[4][0] for r2 in ips))
            write(out_dnsrec, f"  A Records:", "cyan")
            for ip in unique_ips:
                write(out_dnsrec, f"    {ip}", "green")
        except Exception as e:
            write(out_dnsrec, f"  Error: {e}", "red")
        write(out_dnsrec, "\n  For full DNS queries: pip install dnspython", "yellow")
    except Exception as e:
        write(out_dnsrec, f"  Error: {e}", "red")

btn_dnsrec.configure(command=lambda: threading.Thread(target=do_dnsrec, daemon=True).start())

# ════════════════════════════════════════════════════════════
#  PORT SCANNER
# ════════════════════════════════════════════════════════════
f_ps = ctk.CTkFrame(content, fg_color="transparent")
title(f_ps, "Port Scanner", "Scan any host for open TCP ports")
ps_card = card(f_ps); ps_card.pack(fill="x")
inner = ctk.CTkFrame(ps_card, fg_color="transparent"); inner.pack(fill="x", padx=14, pady=14)
ctk.CTkLabel(inner, text="Target IP", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
ps_ip = ctk.CTkEntry(inner, placeholder_text="e.g.  192.168.1.1",
                      fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                      placeholder_text_color=C["text_muted"],
                      font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
ps_ip.pack(fill="x", pady=(2, 10))
pr = ctk.CTkFrame(inner, fg_color="transparent"); pr.pack(fill="x")
ctk.CTkLabel(pr, text="Port Range", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
pr2 = ctk.CTkFrame(pr, fg_color="transparent"); pr2.pack(fill="x", pady=(2, 4))
ps_s = ctk.CTkEntry(pr2, placeholder_text="Start  e.g. 1", fg_color=C["card2"], border_color=C["border"],
                     text_color=C["text"], font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
ps_s.pack(side="left", expand=True, fill="x")
ctk.CTkLabel(pr2, text="  →  ", text_color=C["text_dim"]).pack(side="left")
ps_e = ctk.CTkEntry(pr2, placeholder_text="End  e.g. 1024", fg_color=C["card2"], border_color=C["border"],
                     text_color=C["text"], font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
ps_e.pack(side="left", expand=True, fill="x")
ctk.CTkLabel(inner, text="Quick presets:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=10), text_color=C["text_muted"]).pack(fill="x", pady=(4,2))
preset_row = ctk.CTkFrame(inner, fg_color="transparent")
preset_row.pack(fill="x", pady=(0, 8))

def set_preset(s, e):
    ps_s.delete(0, "end"); ps_s.insert(0, str(s))
    ps_e.delete(0, "end"); ps_e.insert(0, str(e))

for lbl, s, e in [("Top 20", 1, 1024), ("Web", 80, 443), ("Common", 1, 10000), ("Full", 1, 65535)]:
    mk_btn(preset_row, lbl, width=72, muted=True,
           command=lambda _s=s, _e=e: set_preset(_s, _e)).pack(side="left", padx=2)

ctk.CTkLabel(inner, text="Scan Speed", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
sr = ctk.CTkFrame(inner, fg_color="transparent"); sr.pack(fill="x", pady=(2, 4))
ctk.CTkLabel(sr, text="Careful", font=ctk.CTkFont(size=10), text_color=C["text_muted"]).pack(side="left")
ps_slider = ctk.CTkSlider(sr, from_=0.05, to=1.0, number_of_steps=19,
                           button_color=C["green"], button_hover_color=C["green_dim"],
                           progress_color=C["green_dark"])
ps_slider.set(0.5); ps_slider.pack(side="left", expand=True, fill="x", padx=8)
ctk.CTkLabel(sr, text="Fast", font=ctk.CTkFont(size=10), text_color=C["text_muted"]).pack(side="left")
ps_prog = ctk.CTkProgressBar(f_ps, progress_color=C["green"], fg_color=C["card"])
ps_prog.pack(fill="x", pady=(10, 2)); ps_prog.set(0)
ps_status = ctk.CTkLabel(f_ps, text="Ready to scan", text_color=C["text_dim"],
                          font=ctk.CTkFont(family=FONT_MONO, size=10)); ps_status.pack()
out_ps = ctk.CTkTextbox(f_ps, height=180,
                          font=ctk.CTkFont(family=FONT_MONO, size=settings["font_size"]),
                          fg_color=C["term_bg"], text_color=C["term_text"], corner_radius=8,
                          border_width=1, border_color="#333333", wrap="word")
out_ps.pack(fill="x", pady=(8, 8)); out_ps.configure(state="disabled")
out_ps.tag_config("green", foreground=C["term_green"])
out_ps.tag_config("red",   foreground=C["term_red"])
out_ps.tag_config("blue",  foreground="#88aaff")
out_ps.tag_config("dim",   foreground="#888888")
ps_br = ctk.CTkFrame(f_ps, fg_color="transparent"); ps_br.pack()
ps_scan_btn = mk_btn(ps_br, "▶  Start Scan", width=140); ps_scan_btn.pack(side="left", padx=4)
ps_stop_btn = mk_btn(ps_br, "■  Stop", width=90, danger=True); ps_stop_btn.pack(side="left", padx=4)
ps_copy_btn = mk_btn(ps_br, "Copy", width=80, muted=True); ps_copy_btn.pack(side="left", padx=4)
ps_stop_btn.configure(state="disabled")

def do_ps():
    global stop_flag; stop_flag = False
    ip = ps_ip.get().strip()
    try:
        start = int(ps_s.get() or 1); end = int(ps_e.get() or 1024)
    except: start, end = 1, 1024
    timeout = round(1.05 - ps_slider.get(), 2); found = 0
    out_ps.configure(state="normal"); out_ps.delete("1.0", "end"); out_ps.configure(state="disabled")
    write(out_ps, f"  Scanning {ip}  [{start}-{end}]  timeout={timeout}s\n", "dim")
    for port in range(start, end + 1):
        if stop_flag:
            write(out_ps, f"\n  Scan stopped at port {port}.", "red"); break
        ps_status.configure(text=f"Port {port} / {end}   ·   {found} open")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout); res = s.connect_ex((ip, port)); s.close()
        if res == 0:
            svc = SERVICES.get(port, "unknown")
            write(out_ps, f"  {port:<6} OPEN   {svc}", "green"); found += 1
        ps_prog.set(port / end)
    else:
        write(out_ps, f"\n  Complete — {found} open port(s) found.", "blue")
        ps_status.configure(text=f"Done  ·  {found} open")
    ps_scan_btn.configure(state="normal", text="▶  Start Scan")
    ps_stop_btn.configure(state="disabled")

ps_scan_btn.configure(command=lambda: [
    ps_scan_btn.configure(state="disabled", text="Scanning..."),
    ps_stop_btn.configure(state="normal"),
    threading.Thread(target=do_ps, daemon=True).start()
])
ps_stop_btn.configure(command=lambda: globals().update(stop_flag=True))
ps_copy_btn.configure(command=lambda: [app.clipboard_clear(), app.clipboard_append(out_ps.get("1.0", "end"))])

# ── Banner Grabber ─────────────────────────────────────────
f_banner = ctk.CTkFrame(content, fg_color="transparent")
title(f_banner, "Banner Grabber", "Grab service banners from open ports")
c = card(f_banner); c.pack(fill="x", pady=(0,12))
inner_bg = ctk.CTkFrame(c, fg_color="transparent"); inner_bg.pack(fill="x", padx=14, pady=14)
bg_ip   = lentry(inner_bg, "Target IP / Host", "e.g. 192.168.1.1")
bg_port = lentry(inner_bg, "Port", "80")
mk_btn(f_banner, "  Grab Banner", width=150,
       command=lambda: threading.Thread(target=do_banner, daemon=True).start()).pack(anchor="w")
out_banner = outbox(f_banner)

def do_banner():
    host = bg_ip.get().strip(); clear(out_banner)
    try:
        port = int(bg_port.get().strip())
    except:
        write(out_banner, "  Invalid port.", "red"); return
    write(out_banner, f"  Connecting to {host}:{port}...\n", "dim")
    try:
        s = socket.socket()
        s.settimeout(5)
        s.connect((host, port))
        if port in (80, 8080, 8443):
            s.send(b"HEAD / HTTP/1.0\r\nHost: " + host.encode() + b"\r\n\r\n")
        else:
            s.send(b"\r\n")
        banner = s.recv(1024).decode(errors="replace")
        s.close()
        write(out_banner, f"  Banner from {host}:{port}:", "cyan")
        for line in banner.splitlines():
            write(out_banner, f"  {line}")
        write(out_banner, "\n  Done.", "green")
    except Exception as e:
        write(out_banner, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  NETWORK
# ════════════════════════════════════════════════════════════
def make_net_tool(ttl, sub, ph, btn_lbl, func):
    f = ctk.CTkFrame(content, fg_color="transparent")
    title(f, ttl, sub)
    c2 = card(f); c2.pack(fill="x", pady=(0, 12))
    r2 = ctk.CTkFrame(c2, fg_color="transparent"); r2.pack(fill="x", padx=14, pady=14)
    e = ctk.CTkEntry(r2, placeholder_text=ph,
                     fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                     placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
    e.pack(side="left", expand=True, fill="x")
    o = [outbox(f)]
    mk_btn(r2, f"  {btn_lbl}", width=110,
           command=lambda: threading.Thread(target=lambda: func(e.get().strip(), o[0]), daemon=True).start()
           ).pack(side="left", padx=(10, 0))
    return f

def do_ping(t, o):
    clear(o); write(o, f"  Pinging {t}...\n", "dim")
    try:
        cmd = ["ping", "-n", "4", t] if sys.platform == "win32" else ["ping", "-c", "4", t]
        r2 = subprocess.run(cmd, capture_output=True, text=True)
        write(o, r2.stdout)
    except Exception as e: write(o, f"  Error: {e}", "red")

def do_trace(t, o):
    clear(o); write(o, f"  Tracing route to {t}...\n", "dim")
    try:
        if sys.platform == "win32":
            cmd = ["tracert", "-d", "-h", "30", t]
        else:
            for candidate in ["traceroute", "tracepath", "mtr"]:
                try:
                    subprocess.run([candidate, "--version"], capture_output=True, timeout=2)
                    cmd = [candidate, "-n", "-m", "30", t] if candidate == "traceroute" else [candidate, t]
                    break
                except FileNotFoundError:
                    continue
            else:
                write(o, "  No traceroute tool found.", "red"); return
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = result.stdout or result.stderr
        if output.strip(): write(o, output)
        else: write(o, "  No output returned.", "yellow")
    except subprocess.TimeoutExpired:
        write(o, "  Traceroute timed out.", "yellow")
    except Exception as e:
        write(o, f"  Error: {e}", "red")

def do_dns(t, o):
    clear(o)
    if not t: write(o, "  Enter a domain name.", "yellow"); return
    try:
        results = socket.getaddrinfo(t, None)
        ips = list(dict.fromkeys(r2[4][0] for r2 in results))
        write(o, f"  Domain  :  {t}", "cyan")
        for ip in ips: write(o, f"  IP      :  {ip}", "green")
        try:
            hostname = socket.gethostbyaddr(ips[0])[0]
            write(o, f"  Reverse :  {hostname}", "dim")
        except: pass
    except socket.gaierror as e:
        write(o, f"  DNS resolution failed: {e}", "red")
    except Exception as e:
        write(o, f"  Error: {e}", "red")

f_ping  = make_net_tool("Ping",       "Send ICMP packets to test connectivity",  "IP or domain", "Ping",   do_ping)
f_trace = make_net_tool("Traceroute", "Trace the route packets take to a host",  "IP or domain", "Trace",  do_trace)
f_dns   = make_net_tool("DNS Lookup", "Resolve a domain to its IP address",      "Domain",       "Lookup", do_dns)

f_myip = ctk.CTkFrame(content, fg_color="transparent")
title(f_myip, "My Public IP", "Fetch your external IP and geolocation")
mk_btn(f_myip, "  Get My IP", width=140,
       command=lambda: threading.Thread(target=do_myip, daemon=True).start()).pack(anchor="w")
out_myip = outbox(f_myip)

def do_myip():
    clear(out_myip)
    try:
        ip = urllib.request.urlopen("https://api.ipify.org", timeout=5).read().decode()
        d  = json.loads(urllib.request.urlopen(f"http://ip-api.com/json/{ip}?fields=country,regionName,city,isp", timeout=5).read())
        write(out_myip, f"  Public IP  :  {ip}", "green")
        write(out_myip, f"  Location   :  {d['city']}, {d['regionName']}, {d['country']}")
        write(out_myip, f"  ISP        :  {d['isp']}")
    except Exception as e: write(out_myip, f"  Error: {e}", "red")

f_netstat = ctk.CTkFrame(content, fg_color="transparent")
title(f_netstat, "Netstat", "List all active network connections")
mk_btn(f_netstat, "  Run Netstat", width=140,
       command=lambda: threading.Thread(target=do_netstat, daemon=True).start()).pack(anchor="w")
out_netstat = outbox(f_netstat)

def do_netstat():
    clear(out_netstat)
    try:
        if sys.platform == "win32":
            r2 = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        else:
            r2 = subprocess.run(["netstat", "-tunap"], capture_output=True, text=True)
            if r2.returncode != 0:
                r2 = subprocess.run(["ss", "-tunap"], capture_output=True, text=True)
        write(out_netstat, r2.stdout or r2.stderr)
    except Exception as e: write(out_netstat, f"  Error: {e}", "red")

f_arp = ctk.CTkFrame(content, fg_color="transparent")
title(f_arp, "ARP Scanner", "Discover devices on your local network")
mk_btn(f_arp, "  Scan LAN", width=140,
       command=lambda: threading.Thread(target=do_arp, daemon=True).start()).pack(anchor="w")
out_arp = outbox(f_arp)

def do_arp():
    clear(out_arp)
    write(out_arp, "  Scanning local network (ARP)...\n", "dim")
    try:
        if sys.platform == "win32":
            r2 = subprocess.run(["arp", "-a"], capture_output=True, text=True)
        else:
            r2 = subprocess.run(["arp", "-n"], capture_output=True, text=True)
            if r2.returncode != 0:
                r2 = subprocess.run(["ip", "neigh"], capture_output=True, text=True)
        lines = [l for l in r2.stdout.splitlines() if l.strip()]
        write(out_arp, f"  Found {len(lines)} ARP entries:\n", "dim")
        for line in lines:
            write(out_arp, f"  {line}")
        write(out_arp, "\n  Done.", "green")
    except Exception as e:
        write(out_arp, f"  Error: {e}", "red")

f_speed = ctk.CTkFrame(content, fg_color="transparent")
title(f_speed, "Speed Test", "Measure your download speed from a public endpoint")
mk_btn(f_speed, "  Run Speed Test", width=160,
       command=lambda: threading.Thread(target=do_speed, daemon=True).start()).pack(anchor="w")
out_speed = outbox(f_speed)

def do_speed():
    clear(out_speed)
    write(out_speed, "  Running download speed test...\n", "dim")
    url = "https://httpbin.org/bytes/5000000"
    try:
        start = time.time()
        data  = urllib.request.urlopen(url, timeout=30).read()
        elapsed   = time.time() - start
        size_mb   = len(data) / (1024 * 1024)
        speed_mbps= (size_mb * 8) / elapsed
        write(out_speed, f"  Downloaded   :  {size_mb:.2f} MB", "green")
        write(out_speed, f"  Time         :  {elapsed:.2f} seconds")
        write(out_speed, f"  Speed        :  {speed_mbps:.2f} Mbps", "yellow")
        if speed_mbps > 50:   write(out_speed, "  Rating       :  Excellent", "green")
        elif speed_mbps > 20: write(out_speed, "  Rating       :  Good",      "green")
        elif speed_mbps > 5:  write(out_speed, "  Rating       :  Fair",      "yellow")
        else:                 write(out_speed, "  Rating       :  Slow",      "red")
    except Exception as e:
        write(out_speed, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  DISCORD  — single api_discord definition + all UI frames
# ════════════════════════════════════════════════════════════

def api_discord(path, token, method="GET", body=None):
    import urllib.error
    headers = {
        "Content-Type":  "application/json",
        "Authorization": f"Bot {token}",
        "User-Agent":    "DiscordBot (rose-fg, 7.0)"
    }
    req = urllib.request.Request(
        f"https://discord.com/api/v10{path}",
        data=body, headers=headers, method=method
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        raw  = resp.read()
        return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors="replace")
        try:
            ej  = json.loads(error_body)
            msg = ej.get("message", error_body)
            code= ej.get("code", "")
            raise Exception(f"HTTP {e.code} — {msg} (Discord code: {code})")
        except json.JSONDecodeError:
            raise Exception(f"HTTP {e.code} — {error_body}")
    except urllib.error.URLError as e:
        raise Exception(f"Network error: {e.reason}")

# ── Send Message ───────────────────────────────────────────
f_disc_send = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_send, "Send Message", "Send a message to a Discord channel via bot token")
c = card(f_disc_send); c.pack(fill="x", pady=(0, 12))
inner_ds = ctk.CTkFrame(c, fg_color="transparent"); inner_ds.pack(fill="x", padx=14, pady=14)
dt1 = lentry(inner_ds, "Bot Token", "Bot token from Discord Developer Portal", "*")
dc1 = lentry(inner_ds, "Channel ID", "e.g. 1234567890123456789")
dm1 = lentry(inner_ds, "Message", "Hello from rose-fg!")
mk_btn(f_disc_send, "  Send Message", width=150,
       command=lambda: threading.Thread(target=do_disc_send, daemon=True).start()).pack(anchor="w")
out_ds = outbox(f_disc_send, height=160)

def do_disc_send():
    token = dt1.get().strip()
    ch    = dc1.get().strip()
    msg   = dm1.get().strip()
    clear(out_ds)
    if not token: write(out_ds, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_ds, "  Missing: Channel ID", "red"); return
    if not msg:   write(out_ds, "  Missing: Message",    "red"); return
    write(out_ds, f"  Sending to channel {ch}...", "dim")
    try:
        result = api_discord(f"/channels/{ch}/messages", token, "POST",
                             json.dumps({"content": msg}).encode())
        write(out_ds, f"  Sent! Message ID: {result.get('id', 'N/A')}", "green")
    except Exception as e:
        write(out_ds, f"  Failed: {e}", "red")
        write(out_ds, "\n  Common fixes:", "yellow")
        write(out_ds, "  - Bot not in server? Re-invite via OAuth2 URL Generator", "dim")
        write(out_ds, "  - Wrong channel ID? Right-click channel → Copy Channel ID", "dim")
        write(out_ds, "  - Missing permissions? Give bot Send Messages + View Channel", "dim")

# ── Embed Sender ───────────────────────────────────────────
f_disc_embed = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_embed, "Embed Sender", "Send a rich embed message to a Discord channel")
c = card(f_disc_embed); c.pack(fill="x", pady=(0, 12))
inner_de = ctk.CTkFrame(c, fg_color="transparent"); inner_de.pack(fill="x", padx=14, pady=14)
dt2      = lentry(inner_de, "Bot Token",  "Bot token", "*")
dc2      = lentry(inner_de, "Channel ID", "e.g. 1234567890123456789")
de_title = lentry(inner_de, "Embed Title", "My Embed Title")
de_desc  = lentry(inner_de, "Description", "Embed description text")
de_color = lentry(inner_de, "Colour (hex)", "5865f2")
de_footer= lentry(inner_de, "Footer text (optional)", "rose-fg v7.0")
mk_btn(f_disc_embed, "  Send Embed", width=140,
       command=lambda: threading.Thread(target=do_embed, daemon=True).start()).pack(anchor="w")
out_embed = outbox(f_disc_embed, height=140)

def do_embed():
    token = dt2.get().strip()
    ch    = dc2.get().strip()
    clear(out_embed)
    if not token: write(out_embed, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_embed, "  Missing: Channel ID", "red"); return
    write(out_embed, f"  Sending embed to channel {ch}...", "dim")
    try:
        color_int = int((de_color.get().strip().replace("#", "") or "5865f2"), 16)
        embed = {
            "title":       de_title.get().strip(),
            "description": de_desc.get().strip(),
            "color":       color_int,
        }
        footer = de_footer.get().strip()
        if footer:
            embed["footer"] = {"text": footer}
        result = api_discord(f"/channels/{ch}/messages", token, "POST",
                             json.dumps({"embeds": [embed]}).encode())
        write(out_embed, f"  Embed sent! Message ID: {result.get('id', 'N/A')}", "green")
    except Exception as e:
        write(out_embed, f"  Failed: {e}", "red")

# ── Webhook Sender ─────────────────────────────────────────
f_disc_webhook = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_webhook, "Webhook Sender", "Send a message via a Discord webhook URL")
c = card(f_disc_webhook); c.pack(fill="x", pady=(0, 12))
inner_dw = ctk.CTkFrame(c, fg_color="transparent"); inner_dw.pack(fill="x", padx=14, pady=14)
dw_url  = lentry(inner_dw, "Webhook URL", "https://discord.com/api/webhooks/...")
dw_name = lentry(inner_dw, "Username override (optional)", "rose-fg")
dw_msg  = lentry(inner_dw, "Message", "Hello from webhook!")
mk_btn(f_disc_webhook, "  Send Webhook", width=150,
       command=lambda: threading.Thread(target=do_webhook, daemon=True).start()).pack(anchor="w")
out_wh = outbox(f_disc_webhook, height=140)

def do_webhook():
    url = dw_url.get().strip()
    msg = dw_msg.get().strip()
    clear(out_wh)
    if not url: write(out_wh, "  Missing: Webhook URL", "red"); return
    if not msg: write(out_wh, "  Missing: Message",     "red"); return
    if not url.startswith("https://discord.com/api/webhooks/"):
        write(out_wh, "  Invalid webhook URL format.", "red")
        write(out_wh, "  Should start with: https://discord.com/api/webhooks/", "dim")
        return
    write(out_wh, "  Sending webhook...", "dim")
    try:
        payload = {"content": msg}
        name = dw_name.get().strip()
        if name:
            payload["username"] = name
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=8)
        write(out_wh, "  Webhook sent successfully.", "green")
    except urllib.error.HTTPError as e:
        write(out_wh, f"  Failed: HTTP {e.code} — {e.read().decode(errors='replace')}", "red")
    except Exception as e:
        write(out_wh, f"  Failed: {e}", "red")

# ── DM Sender ──────────────────────────────────────────────
f_disc_dm = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_dm, "DM Sender", "Send a direct message to a user via bot token")
c = card(f_disc_dm); c.pack(fill="x", pady=(0, 12))
inner_ddm = ctk.CTkFrame(c, fg_color="transparent"); inner_ddm.pack(fill="x", padx=14, pady=14)
dt3 = lentry(inner_ddm, "Bot Token",  "Bot token", "*")
du3 = lentry(inner_ddm, "User ID",    "e.g. 1234567890123456789")
dm3 = lentry(inner_ddm, "Message",    "Hello!")
mk_btn(f_disc_dm, "  Send DM", width=130,
       command=lambda: threading.Thread(target=do_dm, daemon=True).start()).pack(anchor="w")
out_dm = outbox(f_disc_dm, height=140)

def do_dm():
    token = dt3.get().strip()
    user  = du3.get().strip()
    msg   = dm3.get().strip()
    clear(out_dm)
    if not token: write(out_dm, "  Missing: Bot Token", "red"); return
    if not user:  write(out_dm, "  Missing: User ID",   "red"); return
    if not msg:   write(out_dm, "  Missing: Message",   "red"); return
    write(out_dm, f"  Opening DM channel with user {user}...", "dim")
    try:
        ch = api_discord("/users/@me/channels", token, "POST",
                         json.dumps({"recipient_id": user}).encode())
        write(out_dm, f"  DM channel opened: {ch.get('id')}", "dim")
        result = api_discord(f"/channels/{ch['id']}/messages", token, "POST",
                             json.dumps({"content": msg}).encode())
        write(out_dm, f"  DM sent! Message ID: {result.get('id', 'N/A')}", "green")
    except Exception as e:
        write(out_dm, f"  Failed: {e}", "red")
        write(out_dm, "\n  Note: Bot must share a server with the user to DM them.", "yellow")

# ── Bot Info ───────────────────────────────────────────────
f_disc_info = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_info, "Bot Info", "Fetch information about your bot and its servers")
c = card(f_disc_info); c.pack(fill="x", pady=(0, 12))
inner_bi = ctk.CTkFrame(c, fg_color="transparent"); inner_bi.pack(fill="x", padx=14, pady=14)
dt4 = lentry(inner_bi, "Bot Token", "Bot token", "*")
mk_btn(f_disc_info, "  Fetch Bot Info", width=160,
       command=lambda: threading.Thread(target=do_bot_info, daemon=True).start()).pack(anchor="w")
out_bi = outbox(f_disc_info, height=220)

def do_bot_info():
    token = dt4.get().strip(); clear(out_bi)
    if not token: write(out_bi, "  Missing: Bot Token", "red"); return
    write(out_bi, "  Fetching bot info...", "dim")
    try:
        d = api_discord("/users/@me", token)
        write(out_bi, f"  Username  :  {d.get('username', 'N/A')}", "green")
        write(out_bi, f"  ID        :  {d.get('id', 'N/A')}")
        write(out_bi, f"  Bot       :  {'Yes' if d.get('bot') else 'No — may be a user token!'}", "green" if d.get("bot") else "red")
        write(out_bi, f"  Verified  :  {d.get('verified', 'N/A')}")
        write(out_bi, "\n  Fetching server list...", "dim")
        guilds = api_discord("/users/@me/guilds", token)
        write(out_bi, f"  Servers   :  {len(guilds)}\n")
        for g in guilds:
            write(out_bi, f"    {g.get('name','N/A')}  ({g.get('id','N/A')})", "dim")
    except Exception as e:
        write(out_bi, f"  Failed: {e}", "red")
        write(out_bi, "\n  HTTP 401 means the token is invalid or expired.", "yellow")

# ── Channel Info ───────────────────────────────────────────
f_disc_channel = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_channel, "Channel Info", "Fetch details about a Discord channel")
c = card(f_disc_channel); c.pack(fill="x", pady=(0, 12))
inner_ci = ctk.CTkFrame(c, fg_color="transparent"); inner_ci.pack(fill="x", padx=14, pady=14)
dt5 = lentry(inner_ci, "Bot Token",  "Bot token", "*")
dc5 = lentry(inner_ci, "Channel ID", "e.g. 1234567890123456789")
mk_btn(f_disc_channel, "  Get Channel Info", width=170,
       command=lambda: threading.Thread(target=do_channel_info, daemon=True).start()).pack(anchor="w")
out_ci = outbox(f_disc_channel, height=200)

def do_channel_info():
    token = dt5.get().strip()
    ch    = dc5.get().strip()
    clear(out_ci)
    if not token: write(out_ci, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_ci, "  Missing: Channel ID", "red"); return
    write(out_ci, f"  Fetching channel {ch}...", "dim")
    try:
        d = api_discord(f"/channels/{ch}", token)
        TYPE_MAP = {
            0:"Text", 1:"DM", 2:"Voice", 3:"Group DM", 4:"Category",
            5:"Announcement", 10:"Thread", 11:"Thread", 12:"Thread",
            13:"Stage", 15:"Forum"
        }
        write(out_ci, f"  Name      :  {d.get('name', 'N/A')}", "green")
        write(out_ci, f"  ID        :  {d.get('id')}")
        write(out_ci, f"  Type      :  {TYPE_MAP.get(d.get('type', 0), d.get('type'))}")
        write(out_ci, f"  Topic     :  {d.get('topic') or 'None'}")
        write(out_ci, f"  Guild ID  :  {d.get('guild_id', 'N/A')}")
        write(out_ci, f"  NSFW      :  {d.get('nsfw', False)}", "red" if d.get("nsfw") else "dim")
        write(out_ci, f"  Position  :  {d.get('position', 'N/A')}")
        write(out_ci, f"  Slowmode  :  {d.get('rate_limit_per_user', 0)}s")
    except Exception as e:
        write(out_ci, f"  Failed: {e}", "red")

# ── Delete Message ─────────────────────────────────────────
f_disc_delete = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_delete, "Delete Message", "Delete a specific message by ID")
c = card(f_disc_delete); c.pack(fill="x", pady=(0, 12))
inner_del = ctk.CTkFrame(c, fg_color="transparent"); inner_del.pack(fill="x", padx=14, pady=14)
dt7 = lentry(inner_del, "Bot Token",  "Bot token", "*")
dc7 = lentry(inner_del, "Channel ID", "e.g. 1234567890123456789")
dm7 = lentry(inner_del, "Message ID", "e.g. 9876543210987654321")
mk_btn(f_disc_delete, "  Delete Message", width=160, danger=True,
       command=lambda: threading.Thread(target=do_delete, daemon=True).start()).pack(anchor="w")
out_del = outbox(f_disc_delete, height=140)

def do_delete():
    token = dt7.get().strip()
    ch    = dc7.get().strip()
    mid   = dm7.get().strip()
    clear(out_del)
    if not token: write(out_del, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_del, "  Missing: Channel ID", "red"); return
    if not mid:   write(out_del, "  Missing: Message ID", "red"); return
    write(out_del, f"  Deleting message {mid}...", "dim")
    try:
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{ch}/messages/{mid}",
            headers={"Authorization": f"Bot {token}", "User-Agent": "DiscordBot (rose-fg, 7.0)"},
            method="DELETE")
        urllib.request.urlopen(req, timeout=8)
        write(out_del, "  Message deleted successfully.", "green")
    except urllib.error.HTTPError as e:
        write(out_del, f"  Failed: HTTP {e.code} — {e.read().decode(errors='replace')}", "red")
    except Exception as e:
        write(out_del, f"  Failed: {e}", "red")

# ── Server Info ────────────────────────────────────────────
f_disc_server = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_server, "Server Info", "Fetch details about a Discord guild/server")
c = card(f_disc_server); c.pack(fill="x", pady=(0, 12))
inner_sv = ctk.CTkFrame(c, fg_color="transparent"); inner_sv.pack(fill="x", padx=14, pady=14)
dt_sv = lentry(inner_sv, "Bot Token", "Bot token", "*")
dc_sv = lentry(inner_sv, "Server ID", "e.g. 1234567890123456789")
mk_btn(f_disc_server, "  Get Server Info", width=170,
       command=lambda: threading.Thread(target=do_server_info, daemon=True).start()).pack(anchor="w")
out_sv = outbox(f_disc_server, height=260)

def do_server_info():
    token = dt_sv.get().strip()
    gid   = dc_sv.get().strip()
    clear(out_sv)
    if not token: write(out_sv, "  Missing: Bot Token", "red"); return
    if not gid:   write(out_sv, "  Missing: Server ID", "red"); return
    write(out_sv, f"  Fetching server {gid}...", "dim")
    try:
        d = api_discord(f"/guilds/{gid}?with_counts=true", token)
        write(out_sv, f"  Name            :  {d.get('name', 'N/A')}", "green")
        write(out_sv, f"  ID              :  {d.get('id')}")
        write(out_sv, f"  Owner ID        :  {d.get('owner_id', 'N/A')}", "cyan")
        mc = d.get("approximate_member_count", "N/A")
        write(out_sv, f"  Members         :  {mc:,}" if isinstance(mc, int) else f"  Members  :  {mc}")
        write(out_sv, f"  Online          :  {d.get('approximate_presence_count', 'N/A')}", "green")
        write(out_sv, f"  Boost Level     :  {d.get('premium_tier', 0)}", "yellow")
        write(out_sv, f"  Boosts          :  {d.get('premium_subscription_count', 0)}")
        write(out_sv, f"  Verification    :  {d.get('verification_level', 0)}")
        write(out_sv, f"  Explicit Filter :  {d.get('explicit_content_filter', 0)}")
        write(out_sv, f"  Locale          :  {d.get('preferred_locale', 'N/A')}")
        write(out_sv, f"  Description     :  {d.get('description') or 'None'}", "dim")
        features = d.get("features", [])
        if features:
            write(out_sv, f"\n  Features ({len(features)}):", "dim")
            for feat in features:
                write(out_sv, f"    {feat}", "blue")
    except Exception as e:
        write(out_sv, f"  Failed: {e}", "red")

# ── Role Lister ────────────────────────────────────────────
f_disc_roles = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_roles, "Role Lister", "List all roles in a server")
c = card(f_disc_roles); c.pack(fill="x", pady=(0, 12))
inner_rl = ctk.CTkFrame(c, fg_color="transparent"); inner_rl.pack(fill="x", padx=14, pady=14)
dt_rl = lentry(inner_rl, "Bot Token", "Bot token", "*")
dc_rl = lentry(inner_rl, "Server ID", "e.g. 1234567890123456789")
mk_btn(f_disc_roles, "  List Roles", width=140,
       command=lambda: threading.Thread(target=do_role_list, daemon=True).start()).pack(anchor="w")
out_rl = outbox(f_disc_roles, height=260)

def do_role_list():
    token = dt_rl.get().strip()
    gid   = dc_rl.get().strip()
    clear(out_rl)
    if not token: write(out_rl, "  Missing: Bot Token", "red"); return
    if not gid:   write(out_rl, "  Missing: Server ID", "red"); return
    write(out_rl, f"  Fetching roles for server {gid}...", "dim")
    try:
        roles = api_discord(f"/guilds/{gid}/roles", token)
        roles = sorted(roles, key=lambda r: -r.get("position", 0))
        write(out_rl, f"  Found {len(roles)} roles:\n", "dim")
        for i, role in enumerate(roles, 1):
            name    = role.get("name", "N/A")
            rid     = role.get("id",   "N/A")
            color   = f"#{role.get('color', 0):06x}" if role.get("color") else "none"
            managed = "  [bot]"     if role.get("managed") else ""
            hoisted = "  [hoisted]" if role.get("hoist")   else ""
            write(out_rl, f"  {i:<4}  {name:<28}  {rid:<20}  {color}{managed}{hoisted}",
                  "green" if role.get("color") else "")
    except Exception as e:
        write(out_rl, f"  Failed: {e}", "red")

# ── Message Fetcher ────────────────────────────────────────
f_disc_fetch = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_fetch, "Message Fetcher", "Fetch recent messages from a channel")
c = card(f_disc_fetch); c.pack(fill="x", pady=(0, 12))
inner_mf = ctk.CTkFrame(c, fg_color="transparent"); inner_mf.pack(fill="x", padx=14, pady=14)
dt_mf = lentry(inner_mf, "Bot Token",         "Bot token", "*")
dc_mf = lentry(inner_mf, "Channel ID",        "e.g. 1234567890123456789")
dl_mf = lentry(inner_mf, "Number of messages (max 100)", "20")
mk_btn(f_disc_fetch, "  Fetch Messages", width=160,
       command=lambda: threading.Thread(target=do_fetch_msgs, daemon=True).start()).pack(anchor="w")
out_mf = outbox(f_disc_fetch, height=240)

def do_fetch_msgs():
    token = dt_mf.get().strip()
    ch    = dc_mf.get().strip()
    clear(out_mf)
    if not token: write(out_mf, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_mf, "  Missing: Channel ID", "red"); return
    try:
        limit = min(int(dl_mf.get().strip() or "20"), 100)
    except:
        limit = 20
    write(out_mf, f"  Fetching {limit} messages from channel {ch}...", "dim")
    try:
        msgs = api_discord(f"/channels/{ch}/messages?limit={limit}", token)
        write(out_mf, f"  Fetched {len(msgs)} message(s):\n", "dim")
        for m in reversed(msgs):
            author       = m.get("author", {}).get("username", "Unknown")
            ts           = m.get("timestamp", "")[:19].replace("T", " ")
            content_text = m.get("content", "") or "[embed/attachment]"
            write(out_mf, f"  [{ts}]  {author}:", "cyan")
            write(out_mf, f"    {content_text}\n")
    except Exception as e:
        write(out_mf, f"  Failed: {e}", "red")

# ── User Lookup ────────────────────────────────────────────
f_disc_user = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_user, "User Lookup", "Look up a Discord user by ID")
c = card(f_disc_user); c.pack(fill="x", pady=(0, 12))
inner_ul = ctk.CTkFrame(c, fg_color="transparent"); inner_ul.pack(fill="x", padx=14, pady=14)
dt_ul = lentry(inner_ul, "Bot Token", "Bot token", "*")
du_ul = lentry(inner_ul, "User ID",   "e.g. 1234567890123456789")
mk_btn(f_disc_user, "  Lookup User", width=150,
       command=lambda: threading.Thread(target=do_user_lookup, daemon=True).start()).pack(anchor="w")
out_ul = outbox(f_disc_user, height=200)

def do_user_lookup():
    token = dt_ul.get().strip()
    uid   = du_ul.get().strip()
    clear(out_ul)
    if not token: write(out_ul, "  Missing: Bot Token", "red"); return
    if not uid:   write(out_ul, "  Missing: User ID",   "red"); return
    write(out_ul, f"  Looking up user {uid}...", "dim")
    try:
        d = api_discord(f"/users/{uid}", token)
        write(out_ul, f"  Username    :  {d.get('username', 'N/A')}", "green")
        write(out_ul, f"  ID          :  {d.get('id')}")
        write(out_ul, f"  Display     :  {d.get('global_name') or 'N/A'}")
        write(out_ul, f"  Bot         :  {'Yes' if d.get('bot') else 'No'}")
        avatar = d.get("avatar")
        if avatar:
            write(out_ul, f"  Avatar URL  :  https://cdn.discordapp.com/avatars/{uid}/{avatar}.png", "cyan")
        try:
            ts_ms   = (int(uid) >> 22) + 1420070400000
            created = datetime.datetime.utcfromtimestamp(ts_ms / 1000)
            write(out_ul, f"  Created     :  {created.strftime('%Y-%m-%d %H:%M UTC')}")
        except: pass
    except Exception as e:
        write(out_ul, f"  Failed: {e}", "red")

# ── Bulk Delete ────────────────────────────────────────────
f_disc_bulkdel = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_bulkdel, "Bulk Delete", "Bulk-delete recent messages from a channel")
c = card(f_disc_bulkdel); c.pack(fill="x", pady=(0, 12))
inner_bd = ctk.CTkFrame(c, fg_color="transparent"); inner_bd.pack(fill="x", padx=14, pady=14)
dt_bd = lentry(inner_bd, "Bot Token",  "Bot token", "*")
dc_bd = lentry(inner_bd, "Channel ID", "e.g. 1234567890123456789")
dn_bd = lentry(inner_bd, "Number of messages to delete (2–100)", "10")
mk_btn(f_disc_bulkdel, "  Bulk Delete", width=150, danger=True,
       command=lambda: threading.Thread(target=do_bulk_delete, daemon=True).start()).pack(anchor="w")
out_bd = outbox(f_disc_bulkdel, height=160)

def do_bulk_delete():
    token = dt_bd.get().strip()
    ch    = dc_bd.get().strip()
    clear(out_bd)
    if not token: write(out_bd, "  Missing: Bot Token",  "red"); return
    if not ch:    write(out_bd, "  Missing: Channel ID", "red"); return
    try:
        count = max(2, min(100, int(dn_bd.get().strip() or "10")))
    except:
        count = 10
    write(out_bd, f"  Fetching {count} messages to delete...", "dim")
    try:
        msgs = api_discord(f"/channels/{ch}/messages?limit={count}", token)
        ids  = [m["id"] for m in msgs]
        if len(ids) < 2:
            write(out_bd, "  Need at least 2 messages to bulk delete.", "yellow"); return
        write(out_bd, f"  Deleting {len(ids)} messages...", "dim")
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{ch}/messages/bulk-delete",
            data=json.dumps({"messages": ids}).encode(),
            headers={"Content-Type":"application/json","Authorization":f"Bot {token}","User-Agent":"DiscordBot (rose-fg, 7.0)"},
            method="POST")
        urllib.request.urlopen(req, timeout=10)
        write(out_bd, f"  Deleted {len(ids)} messages successfully.", "green")
        write(out_bd, "\n  Note: Messages older than 14 days cannot be bulk deleted.", "dim")
    except urllib.error.HTTPError as e:
        write(out_bd, f"  Failed: HTTP {e.code} — {e.read().decode(errors='replace')}", "red")
    except Exception as e:
        write(out_bd, f"  Failed: {e}", "red")

# ── Bot Builder ────────────────────────────────────────────
f_disc_builder = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_builder, "Bot Builder", "Generate a starter Discord bot script")
c = card(f_disc_builder); c.pack(fill="x", pady=(0, 12))
inner_bb = ctk.CTkFrame(c, fg_color="transparent"); inner_bb.pack(fill="x", padx=14, pady=14)
db_name   = lentry(inner_bb, "Bot Name",      "MyBot")
db_prefix = lentry(inner_bb, "Command Prefix","!")
r_bb = irow(f_disc_builder)
mk_btn(r_bb, "  Generate Code", width=160, command=lambda: do_builder()).pack(side="left")
mk_btn(r_bb, "Copy", width=80, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_builder.get("1.0","end"))]).pack(side="left", padx=(8,0))
out_builder = outbox(f_disc_builder, height=320)

def do_builder():
    name   = db_name.get().strip()   or "MyBot"
    prefix = db_prefix.get().strip() or "!"
    code = f'''import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="{prefix}", intents=intents)

@bot.event
async def on_ready():
    print(f"{name} is online as {{bot.user}}")
    await bot.change_presence(activity=discord.Game(name="Type {prefix}help"))

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {{ctx.author.mention}}!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {{round(bot.latency * 1000)}}ms")

@bot.command()
async def say(ctx, *, message):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
async def info(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=str(member), color=discord.Color.blurple())
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"))
    await ctx.send(embed=embed)

@bot.command()
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Cleared {{amount}} messages.", delete_after=3)

bot.run("YOUR_TOKEN_HERE")
'''
    clear(out_builder)
    write(out_builder, code)

# ════════════════════════════════════════════════════════════
#  PASSWORDS
# ════════════════════════════════════════════════════════════
f_passgen = ctk.CTkFrame(content, fg_color="transparent")
title(f_passgen, "Password Generator", "Generate strong cryptographically random passwords")
c_pg2 = card(f_passgen); c_pg2.pack(fill="x", pady=(0,12))
inner_pg2 = ctk.CTkFrame(c_pg2, fg_color="transparent"); inner_pg2.pack(fill="x", padx=14, pady=14)
pg_len2 = lentry(inner_pg2, "Length", "16")
pg_sym2 = ctk.CTkCheckBox(inner_pg2, text="Include symbols  (!@#$...)",
                            text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
pg_sym2.pack(anchor="w", pady=2); pg_sym2.select()
pg_num2 = ctk.CTkCheckBox(inner_pg2, text="Include numbers",
                            text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
pg_num2.pack(anchor="w", pady=2); pg_num2.select()
pg_up2  = ctk.CTkCheckBox(inner_pg2, text="Include uppercase",
                           text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
pg_up2.pack(anchor="w", pady=2); pg_up2.select()
pg_ambig= ctk.CTkCheckBox(inner_pg2, text="Exclude ambiguous  (0 O l 1 I)",
                            text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
pg_ambig.pack(anchor="w", pady=2)
r_pg2 = irow(f_passgen)
mk_btn(r_pg2, "  Generate × 5", width=150, command=lambda: do_passgen2()).pack(side="left")
mk_btn(r_pg2, "Copy First", width=100, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_pg2.get("2.0","3.0").strip())]).pack(side="left", padx=(8,0))
out_pg2 = outbox(f_passgen, height=200)

def do_passgen2():
    try: length = int(pg_len2.get().strip() or 16)
    except: length = 16
    chars = string.ascii_lowercase
    if pg_up2.get():   chars += string.ascii_uppercase
    if pg_num2.get():  chars += string.digits
    if pg_sym2.get():  chars += string.punctuation
    if pg_ambig.get():
        for ch in "0Ol1I": chars = chars.replace(ch, "")
    clear(out_pg2)
    write(out_pg2, "  Generated passwords:\n", "dim")
    for _ in range(5):
        pw = "".join(random.choice(chars) for _ in range(length))
        write(out_pg2, f"  {pw}", "green")

f_hasher = ctk.CTkFrame(content, fg_color="transparent")
title(f_hasher, "Hash Generator", "MD5 · SHA1 · SHA256 · SHA512 · BLAKE2")
hash_in = lentry(f_hasher, "Text to hash", "Enter text here")
mk_btn(f_hasher, "  Generate Hashes", width=170, command=lambda: do_hash()).pack(anchor="w")
out_hash = outbox(f_hasher, height=240)

def do_hash():
    t = hash_in.get().strip().encode(); clear(out_hash)
    write(out_hash, "  MD5",    "dim"); write(out_hash, f"  {hashlib.md5(t).hexdigest()}\n",    "yellow")
    write(out_hash, "  SHA1",   "dim"); write(out_hash, f"  {hashlib.sha1(t).hexdigest()}\n",   "blue")
    write(out_hash, "  SHA256", "dim"); write(out_hash, f"  {hashlib.sha256(t).hexdigest()}\n", "green")
    write(out_hash, "  SHA512", "dim"); write(out_hash, f"  {hashlib.sha512(t).hexdigest()}\n", "")
    write(out_hash, "  BLAKE2b","dim"); write(out_hash, f"  {hashlib.blake2b(t).hexdigest()}",  "cyan")

f_passcheck = ctk.CTkFrame(content, fg_color="transparent")
title(f_passcheck, "Password Strength", "Analyse and score your password")
pc_e = lentry(f_passcheck, "Password", "Enter password to analyse", "*")
mk_btn(f_passcheck, "  Analyse", width=130, command=lambda: do_passcheck()).pack(anchor="w")
out_pc = outbox(f_passcheck)

def do_passcheck():
    p = pc_e.get(); clear(out_pc); score = 0; tips = []
    if len(p) >= 8:  score += 1
    else: tips.append("Use at least 8 characters")
    if len(p) >= 12: score += 1
    if re.search(r'[A-Z]', p): score += 1
    else: tips.append("Add uppercase letters")
    if re.search(r'[a-z]', p): score += 1
    else: tips.append("Add lowercase letters")
    if re.search(r'\d', p): score += 1
    else: tips.append("Add numbers")
    if re.search(r'[!@#$%^&*(),.?:{}|<>]', p): score += 1
    else: tips.append("Add special symbols")
    labels = ["Very Weak","Weak","Weak","Fair","Good","Strong","Very Strong"]
    colors = ["red","red","red","yellow","yellow","green","green"]
    bar = "█" * score + "░" * (6 - score)
    write(out_pc, f"  [{bar}]  {labels[score]}  ({score}/6)", colors[score])
    write(out_pc, f"\n  Length  :  {len(p)} characters")
    charset = 0
    if re.search(r'[a-z]', p): charset += 26
    if re.search(r'[A-Z]', p): charset += 26
    if re.search(r'\d', p): charset += 10
    if re.search(r'[^a-zA-Z0-9]', p): charset += 32
    if charset > 0:
        import math
        entropy = len(p) * math.log2(charset)
        write(out_pc, f"  Entropy :  ~{entropy:.0f} bits", "cyan")
    if tips:
        write(out_pc, "\n  Suggestions:", "yellow")
        for t2 in tips: write(out_pc, f"    {t2}", "dim")

f_passphrase = ctk.CTkFrame(content, fg_color="transparent")
title(f_passphrase, "Passphrase Generator", "Generate memorable multi-word passphrases")
c_pp = card(f_passphrase); c_pp.pack(fill="x", pady=(0,12))
inner_pp = ctk.CTkFrame(c_pp, fg_color="transparent"); inner_pp.pack(fill="x", padx=14, pady=14)
pp_words = lentry(inner_pp, "Number of words (3–8)", "4")
pp_sep   = lentry(inner_pp, "Separator", "-")
mk_btn(f_passphrase, "  Generate × 5", width=150, command=lambda: do_passphrase()).pack(anchor="w")
mk_btn(f_passphrase, "Copy First", width=110, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_pp.get("2.0","3.0").strip())]).pack(anchor="w", pady=(4,0))
out_pp = outbox(f_passphrase, height=200)

WORD_LIST = (
    "apple banana cherry dragon eagle falcon galaxy harbor island jungle karma lemon mango"
    " noble ocean palace quartz river silver tiger ultra violet walnut xenon yellow zebra"
    " castle bridge forest meadow garden rocket planet thunder coffee engine bright"
    " amber blaze coast desert flame grove haven ivory jade knight lance maple orbit"
).split()

def do_passphrase():
    try: nw = max(3, min(8, int(pp_words.get().strip() or "4")))
    except: nw = 4
    sep = pp_sep.get() or "-"
    clear(out_pp)
    write(out_pp, "  Passphrases:\n", "dim")
    for _ in range(5):
        words = [random.choice(WORD_LIST) for _ in range(nw)]
        write(out_pp, f"  {sep.join(words)}", "green")

# ════════════════════════════════════════════════════════════
#  ENCODING
# ════════════════════════════════════════════════════════════
f_b64 = ctk.CTkFrame(content, fg_color="transparent")
title(f_b64, "Base64", "Encode or decode Base64 strings")
ctk.CTkLabel(f_b64, text="Input:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
b64_in = ctk.CTkTextbox(f_b64, height=100, fg_color=C["card"], border_width=1,
                          border_color=C["border"], text_color=C["text"],
                          font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
b64_in.pack(fill="x", pady=(2, 8))
r_b64 = irow(f_b64)
mk_btn(r_b64, "  Encode",          width=110, command=lambda: do_b64(True)).pack(side="left")
mk_btn(r_b64, "  Decode",          width=110, command=lambda: do_b64(False)).pack(side="left", padx=(8,0))
mk_btn(r_b64, "  URL-safe Encode", width=150, command=lambda: do_b64_url(True)).pack(side="left", padx=(8,0))
out_b64 = outbox(f_b64, height=200)

def do_b64(enc):
    t = b64_in.get("1.0", "end").strip(); clear(out_b64)
    try:
        result = base64.b64encode(t.encode()).decode() if enc else base64.b64decode(t.encode()).decode()
        write(out_b64, result, "green")
    except Exception as e: write(out_b64, f"  Error: {e}", "red")

def do_b64_url(enc):
    t = b64_in.get("1.0","end").strip(); clear(out_b64)
    try:
        result = base64.urlsafe_b64encode(t.encode()).decode() if enc else base64.urlsafe_b64decode(t.encode()).decode()
        write(out_b64, result, "green")
    except Exception as e: write(out_b64, f"  Error: {e}", "red")

f_url_enc = ctk.CTkFrame(content, fg_color="transparent")
title(f_url_enc, "URL Encode / Decode", "Encode or decode URL-safe strings")
url_in = lentry(f_url_enc, "Input", "Text or URL string")
r_url = irow(f_url_enc)
mk_btn(r_url, "  Encode", width=110, command=lambda: do_url(True)).pack(side="left")
mk_btn(r_url, "  Decode", width=110, command=lambda: do_url(False)).pack(side="left", padx=(8,0))
out_url = outbox(f_url_enc, height=220)

def do_url(enc):
    import urllib.parse; t = url_in.get().strip(); clear(out_url)
    try:
        write(out_url, urllib.parse.quote(t) if enc else urllib.parse.unquote(t), "green")
    except Exception as e: write(out_url, f"  Error: {e}", "red")

f_hex_enc = ctk.CTkFrame(content, fg_color="transparent")
title(f_hex_enc, "Hex Converter", "Convert text to hexadecimal and back")
hex_in = lentry(f_hex_enc, "Input", "Text or hex string")
r_hex = irow(f_hex_enc)
mk_btn(r_hex, "  → Hex",    width=110, command=lambda: do_hex(True)).pack(side="left")
mk_btn(r_hex, "  From Hex", width=110, command=lambda: do_hex(False)).pack(side="left", padx=(8,0))
out_hex = outbox(f_hex_enc, height=220)

def do_hex(to_hex):
    t = hex_in.get().strip(); clear(out_hex)
    try:
        write(out_hex, t.encode().hex() if to_hex else bytes.fromhex(t).decode(), "green")
    except Exception as e: write(out_hex, f"  Error: {e}", "red")

f_caesar = ctk.CTkFrame(content, fg_color="transparent")
title(f_caesar, "Caesar / ROT13 Cipher", "Shift characters by a given amount or apply ROT13")
ctk.CTkLabel(f_caesar, text="Input text:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
caesar_in = ctk.CTkTextbox(f_caesar, height=90, fg_color=C["card"], border_width=1,
                             border_color=C["border"], text_color=C["text"],
                             font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
caesar_in.pack(fill="x", pady=(2, 8))
caesar_shift = lentry(f_caesar, "Shift amount (1–25, ignored for ROT13)", "13")
r_caesar = irow(f_caesar)
mk_btn(r_caesar, "  Encode",      width=110, command=lambda: do_caesar(1)).pack(side="left")
mk_btn(r_caesar, "  Decode",      width=110, command=lambda: do_caesar(-1)).pack(side="left", padx=(8,0))
mk_btn(r_caesar, "  ROT13",       width=100, command=lambda: do_rot13()).pack(side="left", padx=(8,0))
mk_btn(r_caesar, "  Brute Force", width=120, command=lambda: do_caesar_brute()).pack(side="left", padx=(8,0))
out_caesar = outbox(f_caesar, height=180)

def do_caesar(direction):
    text = caesar_in.get("1.0","end").strip(); clear(out_caesar)
    try:
        shift = (int(caesar_shift.get().strip() or 13) * direction) % 26
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                result.append(ch)
        write(out_caesar, "".join(result), "green")
    except Exception as e: write(out_caesar, f"  Error: {e}", "red")

def do_rot13():
    text = caesar_in.get("1.0","end").strip(); clear(out_caesar)
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + 13) % 26 + base))
        else:
            result.append(ch)
    write(out_caesar, "".join(result), "green")

def do_caesar_brute():
    text = caesar_in.get("1.0","end").strip(); clear(out_caesar)
    write(out_caesar, "  Brute force (all 25 shifts):\n", "dim")
    for shift in range(1, 26):
        result = []
        for ch in text:
            if ch.isalpha():
                base = ord('A') if ch.isupper() else ord('a')
                result.append(chr((ord(ch) - base + shift) % 26 + base))
            else:
                result.append(ch)
        write(out_caesar, f"  [{shift:>2}]  {''.join(result)}", "green")

f_jwt = ctk.CTkFrame(content, fg_color="transparent")
title(f_jwt, "JWT Decoder", "Decode and inspect JSON Web Tokens without verification")
ctk.CTkLabel(f_jwt, text="Paste JWT token:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
jwt_in = ctk.CTkTextbox(f_jwt, height=80, fg_color=C["card"], border_width=1,
                          border_color=C["border"], text_color=C["text"],
                          font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
jwt_in.pack(fill="x", pady=(2, 8))
mk_btn(f_jwt, "  Decode JWT", width=140, command=lambda: do_jwt()).pack(anchor="w")
out_jwt = outbox(f_jwt)

def do_jwt():
    token = jwt_in.get("1.0","end").strip(); clear(out_jwt)
    parts = token.split(".")
    if len(parts) != 3:
        write(out_jwt, "  Invalid JWT — expected 3 parts.", "red"); return
    try:
        def b64_decode_part(p):
            p += "=" * (-len(p) % 4)
            return json.loads(base64.urlsafe_b64decode(p).decode())
        header  = b64_decode_part(parts[0])
        payload = b64_decode_part(parts[1])
        write(out_jwt, "  HEADER", "dim")
        for k, v in header.items():
            write(out_jwt, f"  {k:<16} :  {v}", "cyan")
        write(out_jwt, "\n  PAYLOAD", "dim")
        for k, v in payload.items():
            tag = ""
            if k in ("exp", "iat", "nbf"):
                try:
                    dt = datetime.datetime.utcfromtimestamp(int(v))
                    v  = f"{v}  ({dt.strftime('%Y-%m-%d %H:%M:%S UTC')})"
                    if k == "exp":
                        tag = "red" if dt < datetime.datetime.utcnow() else "green"
                except: pass
            write(out_jwt, f"  {k:<16} :  {v}", tag or "")
        write(out_jwt, "\n  SIGNATURE  (not verified — decode only)", "yellow")
        if "exp" in payload:
            exp_dt = datetime.datetime.utcfromtimestamp(int(payload["exp"]))
            if exp_dt < datetime.datetime.utcnow():
                write(out_jwt, "\n  Token has EXPIRED.", "red")
            else:
                diff = exp_dt - datetime.datetime.utcnow()
                write(out_jwt, f"\n  Token valid for ~{diff.seconds // 60} minutes.", "green")
    except Exception as e: write(out_jwt, f"  Error: {e}", "red")

MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
    'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-',
    'R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...',
    '8':'---..','9':'----.','.':'.-.-.-',',':'--..--','?':'..--..','!':'-.-.--','/':'-..-.','=':'-...-'
}
MORSE_REV = {v:k for k,v in MORSE.items()}

f_morse = ctk.CTkFrame(content, fg_color="transparent")
title(f_morse, "Morse Code", "Convert text to Morse code and back")
ctk.CTkLabel(f_morse, text="Input:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
morse_in = ctk.CTkTextbox(f_morse, height=80, fg_color=C["card"], border_width=1,
                            border_color=C["border"], text_color=C["text"],
                            font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
morse_in.pack(fill="x", pady=(2,8))
r_morse = irow(f_morse)
mk_btn(r_morse, "  Text → Morse", width=140, command=lambda: do_morse(True)).pack(side="left")
mk_btn(r_morse, "  Morse → Text", width=140, command=lambda: do_morse(False)).pack(side="left", padx=(8,0))
out_morse = outbox(f_morse, height=200)

def do_morse(to_morse):
    text = morse_in.get("1.0","end").strip(); clear(out_morse)
    try:
        if to_morse:
            result = "  ".join(MORSE.get(c.upper(), "?") if c != " " else "/" for c in text)
        else:
            result = "".join(MORSE_REV.get(code, "?") if code != "/" else " " for code in text.split("  "))
        write(out_morse, result, "green")
    except Exception as e: write(out_morse, f"  Error: {e}", "red")

f_binascii = ctk.CTkFrame(content, fg_color="transparent")
title(f_binascii, "Binary ↔ Text", "Convert text to binary and back")
ba_in = lentry(f_binascii, "Input", "Text  or  01001000 01101001")
r_ba = irow(f_binascii)
mk_btn(r_ba, "  Text → Binary", width=150, command=lambda: do_ba(True)).pack(side="left")
mk_btn(r_ba, "  Binary → Text", width=150, command=lambda: do_ba(False)).pack(side="left", padx=(8,0))
out_ba = outbox(f_binascii, height=220)

def do_ba(to_bin):
    t = ba_in.get().strip(); clear(out_ba)
    try:
        if to_bin:
            result = " ".join(f"{ord(c):08b}" for c in t)
        else:
            chunks = t.split()
            result = "".join(chr(int(b, 2)) for b in chunks)
        write(out_ba, result, "green")
    except Exception as e:
        write(out_ba, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  SYSTEM INFO
# ════════════════════════════════════════════════════════════
f_sysinfo = ctk.CTkFrame(content, fg_color="transparent")
title(f_sysinfo, "System Info", "OS, hardware, and network overview")
mk_btn(f_sysinfo, "  Collect Info", width=150,
       command=lambda: threading.Thread(target=do_sysinfo, daemon=True).start()).pack(anchor="w")
out_sys = outbox(f_sysinfo)

def do_sysinfo():
    clear(out_sys)
    write(out_sys, "  SYSTEM", "dim")
    write(out_sys, f"  OS            :  {platform.system()} {platform.release()}")
    write(out_sys, f"  Version       :  {platform.version()}")
    write(out_sys, f"  Machine       :  {platform.machine()}")
    write(out_sys, f"  Processor     :  {platform.processor()}")
    write(out_sys, f"  Architecture  :  {' / '.join(platform.architecture())}")
    write(out_sys, f"  Node Name     :  {platform.node()}")
    write(out_sys, "\n  NETWORK", "dim")
    hostname = socket.gethostname()
    write(out_sys, f"  Hostname      :  {hostname}")
    try:
        local_ip = socket.gethostbyname(hostname)
        write(out_sys, f"  Local IP      :  {local_ip}")
    except:
        write(out_sys, f"  Local IP      :  unavailable", "dim")
    write(out_sys, "\n  RUNTIME", "dim")
    write(out_sys, f"  Python        :  {sys.version.split()[0]}")
    write(out_sys, f"  Executable    :  {sys.executable}")
    write(out_sys, f"  Platform Tag  :  {sys.platform}")
    write(out_sys, "\n  ENVIRONMENT", "dim")
    write(out_sys, f"  User          :  {os.environ.get('USERNAME') or os.environ.get('USER', 'N/A')}")
    write(out_sys, f"  Home Dir      :  {os.path.expanduser('~')}")
    write(out_sys, f"  CWD           :  {os.getcwd()}")
    write(out_sys, f"  PID           :  {os.getpid()}")
    try:
        import psutil
        write(out_sys, "\n  HARDWARE  (psutil)", "dim")
        write(out_sys, f"  CPU Cores     :  {psutil.cpu_count(logical=False)} physical / {psutil.cpu_count()} logical")
        write(out_sys, f"  CPU Usage     :  {psutil.cpu_percent(interval=1)}%")
        mem = psutil.virtual_memory()
        write(out_sys, f"  RAM Total     :  {mem.total // (1024**3)} GB")
        write(out_sys, f"  RAM Used      :  {mem.used // (1024**3)} GB  ({mem.percent}%)", "yellow" if mem.percent > 80 else "")
        write(out_sys, f"  RAM Free      :  {mem.available // (1024**3)} GB")
        bt = datetime.datetime.fromtimestamp(psutil.boot_time())
        write(out_sys, f"  Boot Time     :  {bt.strftime('%Y-%m-%d %H:%M:%S')}")
    except ImportError:
        write(out_sys, "\n  Install psutil for CPU/RAM info:  pip install psutil", "dim")

f_procs = ctk.CTkFrame(content, fg_color="transparent")
title(f_procs, "Running Processes", "List all active system processes")
mk_btn(f_procs, "  List Processes", width=160,
       command=lambda: threading.Thread(target=do_procs, daemon=True).start()).pack(anchor="w")
out_procs = outbox(f_procs)

def do_procs():
    clear(out_procs)
    try:
        cmd = ["tasklist"] if sys.platform == "win32" else ["ps", "aux"]
        r2 = subprocess.run(cmd, capture_output=True, text=True)
        write(out_procs, r2.stdout)
    except Exception as e: write(out_procs, f"  Error: {e}", "red")

f_disk = ctk.CTkFrame(content, fg_color="transparent")
title(f_disk, "Disk Info", "View disk space and drive usage")
mk_btn(f_disk, "  Get Disk Info", width=160,
       command=lambda: threading.Thread(target=do_disk, daemon=True).start()).pack(anchor="w")
out_disk = outbox(f_disk)

def do_disk():
    clear(out_disk)
    try:
        import shutil
        if sys.platform == "win32":
            import ctypes
            drives = []
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1: drives.append(f"{letter}:\\")
                bitmask >>= 1
            write(out_disk, f"  {'Drive':<8}  {'Total':>10}  {'Used':>10}  {'Free':>10}  {'Use%':>6}", "dim")
            write(out_disk, "  " + "─" * 50, "dim")
            for drive in drives:
                try:
                    total, used, free = shutil.disk_usage(drive)
                    pct = round(used / total * 100)
                    tag = "red" if pct > 90 else ("yellow" if pct > 75 else "green")
                    write(out_disk, f"  {drive:<8}  {total//1073741824:>8} GB  {used//1073741824:>8} GB  {free//1073741824:>8} GB  {pct:>5}%", tag)
                except PermissionError:
                    write(out_disk, f"  {drive:<8}  (no access)", "dim")
        else:
            write(out_disk, f"  {'Mount':<20}  {'Total':>10}  {'Used':>10}  {'Free':>10}  {'Use%':>6}", "dim")
            write(out_disk, "  " + "─" * 64, "dim")
            for path in ["/"]:
                try:
                    total, used, free = shutil.disk_usage(path)
                    if total == 0: continue
                    pct = round(used / total * 100)
                    tag = "red" if pct > 90 else ("yellow" if pct > 75 else "green")
                    write(out_disk, f"  {path:<20}  {total//1073741824:>8} GB  {used//1073741824:>8} GB  {free//1073741824:>8} GB  {pct:>5}%", tag)
                except Exception: pass
    except Exception as e:
        write(out_disk, f"  Error: {e}", "red")

f_envvars = ctk.CTkFrame(content, fg_color="transparent")
title(f_envvars, "Environment Variables", "View all system environment variables")
ev_search = lentry(f_envvars, "Filter (leave blank for all)", "e.g. PATH")
mk_btn(f_envvars, "  List Vars", width=140, command=lambda: do_envvars()).pack(anchor="w")
out_ev = outbox(f_envvars)

def do_envvars():
    clear(out_ev)
    query = ev_search.get().strip().lower()
    items = [(k, v) for k, v in sorted(os.environ.items()) if not query or query in k.lower() or query in v.lower()]
    write(out_ev, f"  {len(items)} variable(s) found:\n", "dim")
    for k, v in items:
        write(out_ev, f"  {k:<30} =  {v[:80]}", "green" if k.upper() in ("PATH","HOME","USERNAME","USER","APPDATA","TEMP") else "")

# ════════════════════════════════════════════════════════════
#  WEB TOOLS
# ════════════════════════════════════════════════════════════
f_http = ctk.CTkFrame(content, fg_color="transparent")
title(f_http, "HTTP Headers", "Inspect the response headers of any URL")
c_h = card(f_http); c_h.pack(fill="x", pady=(0,12))
r_h = ctk.CTkFrame(c_h, fg_color="transparent"); r_h.pack(fill="x", padx=14, pady=14)
e_http = ctk.CTkEntry(r_h, placeholder_text="https://example.com",
                       fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                       placeholder_text_color=C["text_muted"],
                       font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_http.pack(side="left", expand=True, fill="x")
btn_h = mk_btn(r_h, "  Fetch", width=100); btn_h.pack(side="left", padx=(10,0))
out_http = outbox(f_http)

def do_http():
    url = e_http.get().strip(); clear(out_http)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        res = urllib.request.urlopen(req, timeout=8)
        write(out_http, f"  Status  :  {res.status}  OK\n", "green")
        for k, v in res.headers.items():
            tag = "yellow" if k.lower() in ("server","x-powered-by","x-aspnet-version") else ""
            write(out_http, f"  {k:<30} :  {v}", tag)
    except Exception as e: write(out_http, f"  Error: {e}", "red")

btn_h.configure(command=lambda: threading.Thread(target=do_http, daemon=True).start())

f_sitestatus = ctk.CTkFrame(content, fg_color="transparent")
title(f_sitestatus, "Site Status", "Check whether a website is online or down")
c_ss = card(f_sitestatus); c_ss.pack(fill="x", pady=(0,12))
r_ss = ctk.CTkFrame(c_ss, fg_color="transparent"); r_ss.pack(fill="x", padx=14, pady=14)
e_site = ctk.CTkEntry(r_ss, placeholder_text="https://example.com",
                       fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                       placeholder_text_color=C["text_muted"],
                       font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_site.pack(side="left", expand=True, fill="x")
btn_ss = mk_btn(r_ss, "  Check", width=100); btn_ss.pack(side="left", padx=(10,0))
out_site = outbox(f_sitestatus)

def do_sitestatus():
    url = e_site.get().strip(); clear(out_site)
    write(out_site, f"  Checking {url}...", "dim")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        start = time.time()
        res = urllib.request.urlopen(req, timeout=8)
        elapsed = round((time.time() - start) * 1000)
        write(out_site, f"  ONLINE  —  Status {res.status}  ({elapsed}ms)", "green")
        write(out_site, f"  Final URL  :  {res.url}")
    except urllib.error.HTTPError as e:
        write(out_site, f"  HTTP {e.code}  —  {e.reason}", "yellow")
    except Exception as e:
        write(out_site, f"  OFFLINE  —  {e}", "red")

btn_ss.configure(command=lambda: threading.Thread(target=do_sitestatus, daemon=True).start())

f_bulkip = ctk.CTkFrame(content, fg_color="transparent")
title(f_bulkip, "Bulk IP Lookup", "Geolocate multiple IPs at once")
ctk.CTkLabel(f_bulkip, text="One IP per line:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
bulkip_in = ctk.CTkTextbox(f_bulkip, height=120, fg_color=C["card"], border_width=1,
                             border_color=C["border"], text_color=C["text"],
                             font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
bulkip_in.pack(fill="x", pady=(4, 8))
mk_btn(f_bulkip, "  Lookup All", width=140,
       command=lambda: threading.Thread(target=do_bulkip, daemon=True).start()).pack(anchor="w")
out_bulkip = outbox(f_bulkip, height=200)

def do_bulkip():
    ips = [l.strip() for l in bulkip_in.get("1.0","end").strip().splitlines() if l.strip()]
    clear(out_bulkip)
    write(out_bulkip, f"  Processing {len(ips)} IP(s)...\n", "dim")
    for ip in ips:
        try:
            d = json.loads(urllib.request.urlopen(
                f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,query", timeout=5).read())
            if d["status"] == "success":
                write(out_bulkip, f"  {ip:<18}  {d['city']}, {d['country']}  —  {d['isp']}", "green")
            else:
                write(out_bulkip, f"  {ip:<18}  Failed", "red")
        except Exception as e:
            write(out_bulkip, f"  {ip:<18}  {e}", "red")

f_robots = ctk.CTkFrame(content, fg_color="transparent")
title(f_robots, "Robots.txt Reader", "Fetch and display a site's robots.txt file")
c_rb = card(f_robots); c_rb.pack(fill="x", pady=(0,12))
r_rb = ctk.CTkFrame(c_rb, fg_color="transparent"); r_rb.pack(fill="x", padx=14, pady=14)
e_robots = ctk.CTkEntry(r_rb, placeholder_text="https://example.com",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_robots.pack(side="left", expand=True, fill="x")
mk_btn(r_rb, "  Fetch", width=100,
       command=lambda: threading.Thread(target=do_robots, daemon=True).start()).pack(side="left", padx=(10,0))
out_robots = outbox(f_robots)

def do_robots():
    url = e_robots.get().strip().rstrip("/")
    if not url.startswith("http"): url = "https://" + url
    target = url + "/robots.txt"
    clear(out_robots)
    write(out_robots, f"  Fetching {target}...\n", "dim")
    try:
        req = urllib.request.Request(target, headers={"User-Agent":"Mozilla/5.0"})
        content2 = urllib.request.urlopen(req, timeout=8).read().decode(errors="replace")
        disallowed = [l for l in content2.splitlines() if l.lower().startswith("disallow")]
        allowed    = [l for l in content2.splitlines() if l.lower().startswith("allow")]
        for line in content2.splitlines():
            tag = "red" if line.lower().startswith("disallow") else ("green" if line.lower().startswith("allow") else "dim")
            write(out_robots, f"  {line}", tag)
        write(out_robots, f"\n  Summary: {len(disallowed)} Disallow, {len(allowed)} Allow rules", "yellow")
    except Exception as e:
        write(out_robots, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  FILE TOOLS
# ════════════════════════════════════════════════════════════
f_filehash = ctk.CTkFrame(content, fg_color="transparent")
title(f_filehash, "File Hash", "Compute MD5 / SHA hashes of any file")
fh_path = make_drag_drop_entry(f_filehash, "File path", "C:\\path\\to\\file.exe  or  /path/to/file")
mk_btn(f_filehash, "  Hash File", width=130, command=lambda: do_filehash()).pack(anchor="w")
out_fh = outbox(f_filehash)

def do_filehash():
    path = fh_path.get().strip().strip('"').strip("'")
    clear(out_fh)
    if not path: write(out_fh, "  Enter or browse to a file path.", "yellow"); return
    if not os.path.exists(path): write(out_fh, f"  File not found: {path}", "red"); return
    if os.path.isdir(path): write(out_fh, "  Path is a directory.", "yellow"); return
    try:
        with open(path, "rb") as f2: data = f2.read()
        write(out_fh, f"  File    :  {os.path.basename(path)}")
        write(out_fh, f"  Size    :  {os.path.getsize(path):,} bytes\n")
        write(out_fh, f"  MD5     :  {hashlib.md5(data).hexdigest()}",    "yellow")
        write(out_fh, f"  SHA1    :  {hashlib.sha1(data).hexdigest()}",   "blue")
        write(out_fh, f"  SHA256  :  {hashlib.sha256(data).hexdigest()}", "green")
        write(out_fh, f"  SHA512  :  {hashlib.sha512(data).hexdigest()}", "dim")
    except Exception as e: write(out_fh, f"  Error: {e}", "red")

f_fileinfo = ctk.CTkFrame(content, fg_color="transparent")
title(f_fileinfo, "File Info", "View metadata and details for any file")
fi_path = make_drag_drop_entry(f_fileinfo, "File path", "C:\\path\\to\\file  or  /path/to/file")
mk_btn(f_fileinfo, "  Get Info", width=130, command=lambda: do_fileinfo()).pack(anchor="w")
out_fi = outbox(f_fileinfo)

def do_fileinfo():
    path = fi_path.get().strip().strip('"').strip("'")
    clear(out_fi)
    if not path: write(out_fi, "  Enter or browse to a file path.", "yellow"); return
    if not os.path.exists(path): write(out_fi, f"  Path not found: {path}", "red"); return
    try:
        stat = os.stat(path)
        write(out_fi, f"  Name       :  {os.path.basename(path)}", "green")
        write(out_fi, f"  Full Path  :  {os.path.abspath(path)}", "dim")
        write(out_fi, f"  Size       :  {stat.st_size:,} bytes  ({stat.st_size / 1024:.2f} KB)")
        write(out_fi, f"  Extension  :  {os.path.splitext(path)[1] or 'None'}")
        write(out_fi, f"  Is Dir     :  {os.path.isdir(path)}")
        write(out_fi, f"  Readable   :  {os.access(path, os.R_OK)}")
        write(out_fi, f"  Writable   :  {os.access(path, os.W_OK)}")
        write(out_fi, f"  Created    :  {datetime.datetime.fromtimestamp(stat.st_ctime)}")
        write(out_fi, f"  Modified   :  {datetime.datetime.fromtimestamp(stat.st_mtime)}")
        write(out_fi, f"  Accessed   :  {datetime.datetime.fromtimestamp(stat.st_atime)}")
        if os.path.isdir(path):
            items = os.listdir(path)
            write(out_fi, f"\n  Contents   :  {len(items)} items", "cyan")
            for item in items[:10]:
                write(out_fi, f"    {item}", "dim")
            if len(items) > 10:
                write(out_fi, f"    ... and {len(items)-10} more", "dim")
    except Exception as e: write(out_fi, f"  Error: {e}", "red")

f_filecmp = ctk.CTkFrame(content, fg_color="transparent")
title(f_filecmp, "File Comparator", "Compare two files byte-by-byte")
fc_a = make_drag_drop_entry(f_filecmp, "File A", "/path/to/file_a")
fc_b = make_drag_drop_entry(f_filecmp, "File B", "/path/to/file_b")
mk_btn(f_filecmp, "  Compare Files", width=160, command=lambda: do_filecmp()).pack(anchor="w")
out_fc = outbox(f_filecmp)

def do_filecmp():
    a = fc_a.get().strip().strip('"')
    b = fc_b.get().strip().strip('"')
    clear(out_fc)
    if not a or not b: write(out_fc, "  Select both files.", "yellow"); return
    if not os.path.exists(a): write(out_fc, f"  File A not found: {a}", "red"); return
    if not os.path.exists(b): write(out_fc, f"  File B not found: {b}", "red"); return
    try:
        sa, sb = os.path.getsize(a), os.path.getsize(b)
        ha = hashlib.sha256(open(a,"rb").read()).hexdigest()
        hb = hashlib.sha256(open(b,"rb").read()).hexdigest()
        write(out_fc, f"  File A  :  {os.path.basename(a)}  ({sa:,} bytes)", "cyan")
        write(out_fc, f"  File B  :  {os.path.basename(b)}  ({sb:,} bytes)", "cyan")
        write(out_fc, f"\n  SHA256 A:  {ha}", "dim")
        write(out_fc, f"  SHA256 B:  {hb}", "dim")
        if ha == hb:
            write(out_fc, "\n  Files are IDENTICAL.", "green")
        else:
            write(out_fc, "\n  Files are DIFFERENT.", "red")
            write(out_fc, f"  Size diff  :  {abs(sa-sb):,} bytes", "yellow")
    except Exception as e:
        write(out_fc, f"  Error: {e}", "red")

f_subdomains = ctk.CTkFrame(content, fg_color="transparent")
title(f_subdomains, "Subdomain Finder", "Discover subdomains from certificate transparency logs")
r_sd = ctk.CTkFrame(f_subdomains, fg_color="transparent"); r_sd.pack(fill="x", padx=14, pady=14)
e_subdomains = ctk.CTkEntry(r_sd, placeholder_text="Domain  e.g.  example.com",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_subdomains.pack(side="left", expand=True, fill="x")
mk_btn(r_sd, "  Find Subdomains", width=170,
       command=lambda: threading.Thread(target=do_subdomains, daemon=True).start()).pack(side="left", padx=(10,0))
out_subdomains = outbox(f_subdomains, height=260)

def do_subdomains():
    domain = e_subdomains.get().strip().lstrip("*.")
    clear(out_subdomains)
    if not domain:
        write(out_subdomains, "  Enter a domain.", "yellow"); return
    write(out_subdomains, f"  Querying crt.sh for {domain}...\n", "dim")
    try:
        url = f"https://crt.sh/?q=%25.{urllib.parse.quote(domain)}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        text = urllib.request.urlopen(req, timeout=15).read().decode(errors="replace")
        data = json.loads(text)
        names = []
        seen = set()
        for entry in data:
            name_value = entry.get("name_value", "")
            for n in name_value.splitlines():
                n = n.strip().lower()
                if n and n not in seen:
                    seen.add(n)
                    if n.endswith(domain):
                        names.append(n)
        if not names:
            write(out_subdomains, "  No subdomains found.", "yellow")
            return
        write(out_subdomains, f"  Found {len(names)} unique subdomains:\n", "green")
        for n in names[:100]:
            write(out_subdomains, f"  {n}")
        if len(names) > 100:
            write(out_subdomains, f"  ...and {len(names)-100} more", "dim")
    except Exception as e:
        write(out_subdomains, f"  Error: {e}", "red")

f_spf = ctk.CTkFrame(content, fg_color="transparent")
title(f_spf, "SPF / DMARC Checker", "Fetch SPF and DMARC TXT records for a domain")
r_spf = ctk.CTkFrame(f_spf, fg_color="transparent"); r_spf.pack(fill="x", padx=14, pady=14)
e_spf = ctk.CTkEntry(r_spf, placeholder_text="Domain  e.g.  example.com",
                     fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                     placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
e_spf.pack(side="left", expand=True, fill="x")
mk_btn(r_spf, "  Check Records", width=150,
       command=lambda: threading.Thread(target=do_spf_dmarc, daemon=True).start()).pack(side="left", padx=(10,0))
out_spf = outbox(f_spf, height=220)

def fetch_dns_txt_records(name):
    url = f"https://dns.google/resolve?name={urllib.parse.quote(name)}&type=16"
    req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
    data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode(errors="replace"))
    answers = data.get("Answer", []) or []
    records = []
    for item in answers:
        text = item.get("data", "")
        if text:
            records.append(text.strip().strip('"'))
    return records

def do_spf_dmarc():
    domain = e_spf.get().strip().lstrip("*.")
    clear(out_spf)
    if not domain:
        write(out_spf, "  Enter a domain.", "yellow"); return
    write(out_spf, f"  Checking SPF and DMARC for {domain}...\n", "dim")
    try:
        spf_records = [r for r in fetch_dns_txt_records(domain) if r.lower().startswith("v=spf1")]
        dmarc_records = [r for r in fetch_dns_txt_records(f"_dmarc.{domain}") if r.lower().startswith("v=dmarc1")]
        if spf_records:
            write(out_spf, "  SPF records:", "cyan")
            for r in spf_records: write(out_spf, f"  {r}")
        else:
            write(out_spf, "  No SPF record found.", "yellow")
        if dmarc_records:
            write(out_spf, "\n  DMARC records:", "cyan")
            for r in dmarc_records: write(out_spf, f"  {r}")
        else:
            write(out_spf, "\n  No DMARC record found.", "yellow")
    except Exception as e:
        write(out_spf, f"  Error: {e}", "red")

f_pwned = ctk.CTkFrame(content, fg_color="transparent")
title(f_pwned, "Password Leak Check", "Check whether a password appears in public breach data")
r_pwned = ctk.CTkFrame(f_pwned, fg_color="transparent"); r_pwned.pack(fill="x", padx=14, pady=14)
e_pwned = ctk.CTkEntry(r_pwned, placeholder_text="Enter password to check",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1, show="*")
e_pwned.pack(side="left", expand=True, fill="x")
mk_btn(r_pwned, "  Check Password", width=150,
       command=lambda: threading.Thread(target=do_pwned_password, daemon=True).start()).pack(side="left", padx=(10,0))
out_pwned = outbox(f_pwned, height=200)

def do_pwned_password():
    pwd = e_pwned.get().strip()
    clear(out_pwned)
    if not pwd:
        write(out_pwned, "  Enter a password.", "yellow"); return
    write(out_pwned, "  Checking password leak database...\n", "dim")
    try:
        digest = hashlib.sha1(pwd.encode("utf-8")).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        req = urllib.request.Request(f"https://api.pwnedpasswords.com/range/{prefix}", headers={"User-Agent":"Mozilla/5.0"})
        body = urllib.request.urlopen(req, timeout=10).read().decode(errors="replace")
        count = 0
        for line in body.splitlines():
            if not line: continue
            h, c = line.split(":")
            if h == suffix:
                count = int(c.strip())
                break
        if count:
            write(out_pwned, f"  This password was seen {count:,} times in breaches.", "red")
        else:
            write(out_pwned, "  Nice — this password was not found in the Pwned Passwords list.", "green")
    except Exception as e:
        write(out_pwned, f"  Error: {e}", "red")

f_portmap = ctk.CTkFrame(content, fg_color="transparent")
title(f_portmap, "Port Process Map", "List local ports and the owning process")
r_portmap = ctk.CTkFrame(f_portmap, fg_color="transparent"); r_portmap.pack(fill="x", padx=14, pady=14)
pp_filter = ctk.CTkEntry(r_portmap, placeholder_text="Optional port number",
                         fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                         placeholder_text_color=C["text_muted"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
pp_filter.pack(side="left", expand=True, fill="x")
mk_btn(r_portmap, "  Refresh", width=120,
       command=lambda: threading.Thread(target=do_portmap, daemon=True).start()).pack(side="left", padx=(10,0))
out_portmap = outbox(f_portmap, height=260)

def do_portmap():
    clear(out_portmap)
    filter_text = pp_filter.get().strip()
    filt = None
    if filter_text:
        try:
            filt = int(filter_text)
        except:
            write(out_portmap, "  Invalid port number.", "yellow"); return
    write(out_portmap, "  Gathering local port mappings...\n", "dim")
    try:
        conns = psutil.net_connections(kind='inet')
        entries = []
        for conn in conns:
            if not conn.laddr: continue
            port = conn.laddr.port
            if filt and port != filt: continue
            proto = 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP'
            pid = conn.pid or 0
            name = 'N/A'
            if pid:
                try:
                    name = psutil.Process(pid).name()
                except Exception:
                    name = str(pid)
            status = conn.status
            entries.append((port, proto, name, status))
        entries.sort(key=lambda x: (x[0], x[1], x[2]))
        if not entries:
            write(out_portmap, "  No local port connections found.", "yellow")
            return
        for port, proto, name, status in entries[:200]:
            write(out_portmap, f"  {port:<5} {proto:<4} {name:<25} {status}")
        if len(entries) > 200:
            write(out_portmap, f"  ...and {len(entries)-200} more", "dim")
        write(out_portmap, f"\n  Total entries: {len(entries)}", "green")
    except Exception as e:
        write(out_portmap, f"  Error: {e}", "red")

f_filemeta = ctk.CTkFrame(content, fg_color="transparent")
title(f_filemeta, "File Metadata", "View image metadata and file attributes")
fm_path = make_drag_drop_entry(f_filemeta, "File path", "C:\\path\\to\\file")
mk_btn(f_filemeta, "  Read Metadata", width=150, command=lambda: do_filemetadata()).pack(anchor="w")
out_fmeta = outbox(f_filemeta, height=260)

def do_filemetadata():
    path = fm_path.get().strip().strip('"').strip("'")
    clear(out_fmeta)
    if not path:
        write(out_fmeta, "  Enter a file path.", "yellow"); return
    if not os.path.exists(path):
        write(out_fmeta, f"  File not found: {path}", "red"); return
    try:
        stat = os.stat(path)
        write(out_fmeta, f"  Name        :  {os.path.basename(path)}", "green")
        write(out_fmeta, f"  Full Path   :  {os.path.abspath(path)}")
        write(out_fmeta, f"  Size        :  {stat.st_size:,} bytes")
        write(out_fmeta, f"  Modified    :  {datetime.datetime.fromtimestamp(stat.st_mtime)}")
        write(out_fmeta, f"  Created     :  {datetime.datetime.fromtimestamp(stat.st_ctime)}")
        write(out_fmeta, f"  Readable    :  {os.access(path, os.R_OK)}")
        write(out_fmeta, f"  Writable    :  {os.access(path, os.W_OK)}")
        try:
            img = Image.open(path)
            write(out_fmeta, "\n  Image metadata:", "cyan")
            write(out_fmeta, f"  Format      :  {img.format}")
            write(out_fmeta, f"  Size        :  {img.size[0]} x {img.size[1]}")
            write(out_fmeta, f"  Mode        :  {img.mode}")
            if img.info:
                for key, value in img.info.items():
                    write(out_fmeta, f"  {key:<12}:  {value}")
            exif = getattr(img, '_getexif', None)
            if exif:
                exif_data = exif() or {}
                if exif_data:
                    write(out_fmeta, "\n  EXIF data:", "yellow")
                    count = 0
                    for tag_id, value in exif_data.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        write(out_fmeta, f"  {tag:<22}:  {value}")
                        count += 1
                        if count >= 20:
                            write(out_fmeta, f"  ...and {len(exif_data)-20} more", "dim")
                            break
        except Exception:
            write(out_fmeta, "\n  No image metadata available.", "dim")
    except Exception as e:
        write(out_fmeta, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  CRYPTO
# ════════════════════════════════════════════════════════════
f_crypto = ctk.CTkFrame(content, fg_color="transparent")
title(f_crypto, "Crypto Prices", "Live cryptocurrency prices via CoinGecko")
crypto_top_row  = ctk.CTkFrame(f_crypto, fg_color="transparent")
crypto_top_row.pack(fill="x", pady=(0, 8))
crypto_search_var = ctk.StringVar()
crypto_search = ctk.CTkEntry(crypto_top_row, placeholder_text="Search coin  e.g. bitcoin, solana...",
                              textvariable=crypto_search_var,
                              fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                              placeholder_text_color=C["text_muted"],
                              font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
crypto_search.pack(side="left", expand=True, fill="x")
mk_btn(crypto_top_row, "  Search",   width=100,
       command=lambda: threading.Thread(target=do_crypto_search, daemon=True).start()).pack(side="left", padx=(8,0))
mk_btn(crypto_top_row, "  Fetch All",width=110,
       command=lambda: threading.Thread(target=do_crypto, daemon=True).start()).pack(side="left", padx=(8,0))
out_crypto = outbox(f_crypto)
DEFAULT_COINS = ["bitcoin","ethereum","solana","dogecoin","cardano","ripple","litecoin","polkadot","monero","chainlink"]

def do_crypto():
    clear(out_crypto); write(out_crypto, "  Fetching live prices...\n", "dim")
    try:
        ids  = ",".join(DEFAULT_COINS)
        data = json.loads(urllib.request.urlopen(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd,gbp&include_24hr_change=true", timeout=8).read())
        clear(out_crypto)
        write(out_crypto, f"  {'Coin':<16}  {'USD':>12}  {'GBP':>12}  {'24h%':>8}", "dim")
        write(out_crypto, "  " + "─" * 56, "dim")
        for coin in DEFAULT_COINS:
            if coin in data:
                usd = f"${data[coin].get('usd', 0):,.2f}"
                gbp = f"£{data[coin].get('gbp', 0):,.2f}"
                chg = data[coin].get('usd_24h_change', 0)
                chg_str = f"{chg:+.2f}%"
                tag = "green" if chg >= 0 else "red"
                write(out_crypto, f"  {coin.capitalize():<16}  {usd:>12}  {gbp:>12}  {chg_str:>8}", tag)
    except Exception as e: write(out_crypto, f"  Error: {e}", "red")

def do_crypto_search():
    query = crypto_search_var.get().strip().lower().replace(" ", "-")
    if not query: return
    clear(out_crypto)
    write(out_crypto, f"  Searching for '{query}'...\n", "dim")
    try:
        search_data = json.loads(urllib.request.urlopen(
            f"https://api.coingecko.com/api/v3/search?query={query}", timeout=8).read())
        coins_found = search_data.get("coins", [])
        if not coins_found: write(out_crypto, "  No coins found.", "red"); return
        coin_ids = [c["id"] for c in coins_found[:6]]
        data = json.loads(urllib.request.urlopen(
            f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd,gbp", timeout=8).read())
        write(out_crypto, f"  {'Coin':<28}  {'USD':>12}  {'GBP':>12}", "dim")
        write(out_crypto, "  " + "─" * 58, "dim")
        for c in coins_found[:6]:
            cid = c["id"]
            if cid in data:
                usd   = f"${data[cid].get('usd', 0):,.4f}"
                gbp   = f"£{data[cid].get('gbp', 0):,.4f}"
                label = f"{c['name']} ({c['symbol'].upper()})"
                write(out_crypto, f"  {label:<28}  {usd:>12}  {gbp:>12}", "green")
    except Exception as e: write(out_crypto, f"  Error: {e}", "red")

f_convert = ctk.CTkFrame(content, fg_color="transparent")
title(f_convert, "Currency Converter", "Real-time exchange rates")
conv_amount = lentry(f_convert, "Amount",          "100")
conv_from   = lentry(f_convert, "From (e.g. USD)", "USD")
conv_to     = lentry(f_convert, "To (e.g. GBP)",   "GBP")
mk_btn(f_convert, "  Convert", width=130,
       command=lambda: threading.Thread(target=do_convert, daemon=True).start()).pack(anchor="w")
out_conv = outbox(f_convert, height=200)

def do_convert():
    amount = conv_amount.get().strip()
    frm    = conv_from.get().strip().upper()
    to     = conv_to.get().strip().upper()
    clear(out_conv)
    try:
        data = json.loads(urllib.request.urlopen(
            f"https://api.exchangerate-api.com/v4/latest/{frm}", timeout=8).read())
        rate = data["rates"].get(to)
        if rate:
            result = float(amount) * rate
            write(out_conv, f"  {amount} {frm}  =  {result:,.2f} {to}", "green")
            write(out_conv, f"\n  Rate    :  1 {frm} = {rate} {to}", "dim")
            write(out_conv, f"  Updated :  {data.get('date','N/A')}", "dim")
        else:
            write(out_conv, f"  Currency not found: {to}", "red")
    except Exception as e: write(out_conv, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  TEXT TOOLS
# ════════════════════════════════════════════════════════════
f_texttools = ctk.CTkFrame(content, fg_color="transparent")
title(f_texttools, "Text Tools", "Transform, analyse, and manipulate text")
ctk.CTkLabel(f_texttools, text="Input:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
text_in = ctk.CTkTextbox(f_texttools, height=100, fg_color=C["card"], border_width=1,
                           border_color=C["border"], text_color=C["text"],
                           font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
text_in.pack(fill="x", pady=(2, 8))
btn_row  = irow(f_texttools)
for lbl, fn in [("UPPER", str.upper), ("lower", str.lower), ("Title", str.title),
                ("Reverse", lambda t: t[::-1])]:
    mk_btn(btn_row, lbl, width=90, command=lambda f=fn: do_text(f)).pack(side="left", padx=2)
btn_row2 = irow(f_texttools)
mk_btn(btn_row2, "Word Count",   width=110, command=lambda: do_wordcount()).pack(side="left", padx=2)
mk_btn(btn_row2, "No Spaces",    width=100, command=lambda: do_text(lambda t: t.replace(" ",""))).pack(side="left", padx=2)
mk_btn(btn_row2, "Strip Lines",  width=100, command=lambda: do_text(lambda t: "\n".join(l.strip() for l in t.splitlines()))).pack(side="left", padx=2)
mk_btn(btn_row2, "Remove Dupes", width=120, command=lambda: do_remove_dupes()).pack(side="left", padx=2)
btn_row3 = irow(f_texttools)
mk_btn(btn_row3, "Sort Lines",  width=100, command=lambda: do_text(lambda t: "\n".join(sorted(t.splitlines())))).pack(side="left", padx=2)
mk_btn(btn_row3, "Trim Blank",  width=100, command=lambda: do_text(lambda t: "\n".join(l for l in t.splitlines() if l.strip()))).pack(side="left", padx=2)
mk_btn(btn_row3, "Camel→Snake", width=120, command=lambda: do_camel_snake()).pack(side="left", padx=2)
out_text = outbox(f_texttools, height=180)

def do_text(fn):
    t = text_in.get("1.0","end").strip(); clear(out_text); write(out_text, fn(t), "green")

def do_wordcount():
    t = text_in.get("1.0","end").strip(); clear(out_text)
    write(out_text, f"  Characters  :  {len(t)}")
    write(out_text, f"  No spaces   :  {len(t.replace(' ',''))}")
    write(out_text, f"  Words       :  {len(t.split())}")
    write(out_text, f"  Lines       :  {len(t.splitlines())}")
    write(out_text, f"  Sentences   :  {len(re.split(r'[.!?]+', t))}")

def do_remove_dupes():
    t = text_in.get("1.0","end").strip()
    lines = t.splitlines()
    seen = set(); result = []
    for l in lines:
        if l not in seen:
            seen.add(l); result.append(l)
    removed = len(lines) - len(result)
    clear(out_text)
    write(out_text, "\n".join(result), "green")
    write(out_text, f"\n  Removed {removed} duplicate line(s).", "yellow")

def do_camel_snake():
    t = text_in.get("1.0","end").strip()
    result = re.sub(r'([A-Z])', r'_\1', t).lower().lstrip('_')
    clear(out_text)
    write(out_text, result, "green")

# ════════════════════════════════════════════════════════════
#  QR CODE
# ════════════════════════════════════════════════════════════
f_qr = ctk.CTkFrame(content, fg_color="transparent")
title(f_qr, "QR Code Generator", "Generate a QR code for any text or URL")
qr_in = lentry(f_qr, "Text or URL", "https://example.com")
qr_display_frame = ctk.CTkFrame(f_qr, fg_color=C["card"], corner_radius=8,
                                  border_width=1, border_color=C["border"])
qr_display_frame.pack(fill="x", pady=(0, 8))
qr_image_label = ctk.CTkLabel(qr_display_frame, text="QR code will appear here",
                                text_color=C["text_muted"],
                                font=ctk.CTkFont(family=FONT_UI, size=11))
qr_image_label.pack(pady=12)
qr_img_ref = [None]

def do_qr():
    import urllib.parse
    t = qr_in.get().strip()
    if not t: return
    clear(out_qr)
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=3)
        qr.add_data(t)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        pil_img = Image.open(buf).resize((220, 220), Image.NEAREST)
        ctk_img = ImageTk.PhotoImage(pil_img)
        qr_img_ref[0] = ctk_img
        qr_image_label.configure(image=ctk_img, text="")
        write(out_qr, "  QR code generated above.", "green")
    except Exception as gen_err:
        write(out_qr, f"  Inline QR failed ({gen_err}) — falling back to URL.\n", "dim")
    encoded = urllib.parse.quote(t)
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded}"
    write(out_qr, f"  Link: {url}", "cyan")
    app.clipboard_clear(); app.clipboard_append(url)
    write(out_qr, "  URL copied to clipboard.", "dim")

r_qr = irow(f_qr)
mk_btn(r_qr, "  Generate QR", width=150, command=lambda: do_qr()).pack(side="left")
mk_btn(r_qr, "Copy URL", width=100, muted=True, command=lambda: do_qr()).pack(side="left", padx=(8,0))
out_qr = outbox(f_qr, height=100)

# ════════════════════════════════════════════════════════════
#  SOCIAL MEDIA
# ════════════════════════════════════════════════════════════
f_social_ip = ctk.CTkFrame(content, fg_color="transparent")
title(f_social_ip, "Platform IP Lookup", "Resolve the IP of a social media platform")
c_soc = card(f_social_ip); c_soc.pack(fill="x", pady=(0,12))
r_soc = ctk.CTkFrame(c_soc, fg_color="transparent"); r_soc.pack(fill="x", padx=14, pady=14)
soc_entry = ctk.CTkEntry(r_soc, placeholder_text="e.g. twitter.com  /  instagram.com",
                           fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                           placeholder_text_color=C["text_muted"],
                           font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
soc_entry.pack(side="left", expand=True, fill="x")
btn_soc = mk_btn(r_soc, "  Lookup", width=110); btn_soc.pack(side="left", padx=(10,0))
out_soc = outbox(f_social_ip)

def do_social_ip():
    raw = soc_entry.get().strip()
    t   = raw.replace("https://","").replace("http://","").split("/")[0].strip()
    if not t: write(out_soc, "  Enter a domain.", "yellow"); return
    clear(out_soc)
    write(out_soc, f"  Resolving {t}...\n", "dim")
    try:
        results = socket.getaddrinfo(t, None)
        ips = list(dict.fromkeys(r2[4][0] for r2 in results))
        write(out_soc, f"  Domain   :  {t}", "cyan")
        for ip in ips:
            write(out_soc, f"  IP       :  {ip}", "green")
            try:
                d = json.loads(urllib.request.urlopen(
                    f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,query", timeout=5).read())
                if d["status"] == "success":
                    write(out_soc, f"  Country  :  {d['country']}")
                    write(out_soc, f"  City     :  {d['city']}")
                    write(out_soc, f"  ISP      :  {d['isp']}")
                    write(out_soc, f"  Org      :  {d['org']}\n")
            except: pass
    except socket.gaierror as e:
        write(out_soc, f"  DNS resolution failed: {e}", "red")
    except Exception as e:
        write(out_soc, f"  Error: {e}", "red")

btn_soc.configure(command=lambda: threading.Thread(target=do_social_ip, daemon=True).start())

f_username = ctk.CTkFrame(content, fg_color="transparent")
title(f_username, "Username Checker", "Search for a username across popular platforms")
c_un = card(f_username); c_un.pack(fill="x", pady=(0,12))
r_un = ctk.CTkFrame(c_un, fg_color="transparent"); r_un.pack(fill="x", padx=14, pady=14)
uname_entry = ctk.CTkEntry(r_un, placeholder_text="Username to check",
                            fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                            placeholder_text_color=C["text_muted"],
                            font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
uname_entry.pack(side="left", expand=True, fill="x")
btn_un = mk_btn(r_un, "  Search", width=110); btn_un.pack(side="left", padx=(10,0))
out_uname = outbox(f_username)

def do_username():
    username = uname_entry.get().strip(); clear(out_uname)
    write(out_uname, f"  Searching for '{username}'...\n", "dim")
    platforms = {
        "GitHub":      f"https://github.com/{username}",
        "Twitter / X": f"https://twitter.com/{username}",
        "Instagram":   f"https://instagram.com/{username}",
        "TikTok":      f"https://tiktok.com/@{username}",
        "Reddit":      f"https://reddit.com/user/{username}",
        "YouTube":     f"https://youtube.com/@{username}",
        "Twitch":      f"https://twitch.tv/{username}",
        "Pinterest":   f"https://pinterest.com/{username}",
    }
    for platform, url in platforms.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=5)
            write(out_uname, f"  {platform:<16}  FOUND    {url}", "green")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                write(out_uname, f"  {platform:<16}  Not found", "red")
            else:
                write(out_uname, f"  {platform:<16}  HTTP {e.code}", "yellow")
        except Exception as e:
            write(out_uname, f"  {platform:<16}  {e}", "dim")

btn_un.configure(command=lambda: threading.Thread(target=do_username, daemon=True).start())

f_emailval = ctk.CTkFrame(content, fg_color="transparent")
title(f_emailval, "Email Validator", "Validate email format and check MX records")
ev_email = lentry(f_emailval, "Email address", "user@example.com")
mk_btn(f_emailval, "  Validate", width=130,
       command=lambda: threading.Thread(target=do_emailval, daemon=True).start()).pack(anchor="w")
out_emailval = outbox(f_emailval)

def do_emailval():
    email = ev_email.get().strip(); clear(out_emailval)
    write(out_emailval, f"  Validating {email}...\n", "dim")
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        write(out_emailval, "  Format    :  Valid", "green")
        domain = email.split("@")[1]
        try:
            results = socket.getaddrinfo(domain, None)
            write(out_emailval, f"  Domain    :  {domain} resolves", "green")
            ips = list(dict.fromkeys(r2[4][0] for r2 in results))
            for ip in ips:
                write(out_emailval, f"    {ip}", "dim")
        except:
            write(out_emailval, f"  Domain    :  {domain} — DOES NOT RESOLVE", "red")
        write(out_emailval, f"  Local     :  {email.split('@')[0]}")
        write(out_emailval, f"  Domain    :  {domain}")
    else:
        write(out_emailval, "  Format    :  INVALID", "red")
        write(out_emailval, "  Check for correct format: user@domain.com", "yellow")

# ════════════════════════════════════════════════════════════
#  DEV TOOLS
# ════════════════════════════════════════════════════════════
f_json_fmt = ctk.CTkFrame(content, fg_color="transparent")
title(f_json_fmt, "JSON Formatter", "Beautify or minify JSON data")
ctk.CTkLabel(f_json_fmt, text="Input JSON:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
json_in = ctk.CTkTextbox(f_json_fmt, height=140, fg_color=C["card"], border_width=1,
                          border_color=C["border"], text_color=C["text"],
                          font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
json_in.pack(fill="x", pady=(2, 8))
r_json = irow(f_json_fmt)
mk_btn(r_json, "  Beautify", width=120, command=lambda: do_json(True)).pack(side="left")
mk_btn(r_json, "  Minify",   width=110, command=lambda: do_json(False)).pack(side="left", padx=(8,0))
mk_btn(r_json, "  Validate", width=110, command=lambda: do_json_validate()).pack(side="left", padx=(8,0))
mk_btn(r_json, "Copy", width=80, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_json.get("1.0","end"))]).pack(side="left", padx=(8,0))
out_json = outbox(f_json_fmt, height=200)

def do_json(pretty):
    raw = json_in.get("1.0","end").strip(); clear(out_json)
    try:
        parsed = json.loads(raw)
        result = json.dumps(parsed, indent=4, ensure_ascii=False) if pretty else json.dumps(parsed, separators=(',',':'), ensure_ascii=False)
        write(out_json, result, "green")
        write(out_json, f"\n  Valid JSON  —  {len(result)} chars", "dim")
    except json.JSONDecodeError as e:
        write(out_json, f"  JSON Error: {e}", "red")

def do_json_validate():
    raw = json_in.get("1.0","end").strip(); clear(out_json)
    try:
        parsed = json.loads(raw)
        write(out_json, "  Valid JSON", "green")
        if isinstance(parsed, dict):
            write(out_json, f"  Type   :  Object  ({len(parsed)} keys)", "dim")
            for k in list(parsed.keys())[:10]:
                write(out_json, f"    {k}  :  {type(parsed[k]).__name__}", "dim")
        elif isinstance(parsed, list):
            write(out_json, f"  Type   :  Array  ({len(parsed)} items)", "dim")
    except json.JSONDecodeError as e:
        write(out_json, f"  INVALID: {e}", "red")
        if hasattr(e, 'lineno'):
            write(out_json, f"  Line {e.lineno}, Column {e.colno}", "yellow")

f_regex = ctk.CTkFrame(content, fg_color="transparent")
title(f_regex, "Regex Tester", "Test regular expressions against any text")
regex_pattern = lentry(f_regex, "Pattern", r"e.g.  \d+  or  [a-z]+@\w+\.\w+")
ctk.CTkLabel(f_regex, text="Test text:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
regex_text = ctk.CTkTextbox(f_regex, height=100, fg_color=C["card"], border_width=1,
                              border_color=C["border"], text_color=C["text"],
                              font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
regex_text.pack(fill="x", pady=(2, 8))
r_regex = irow(f_regex)
mk_btn(r_regex, "  Test / Find All", width=160, command=lambda: do_regex()).pack(side="left")
regex_flags = ctk.CTkCheckBox(r_regex, text="Case insensitive", text_color=C["text"],
                               font=ctk.CTkFont(family=FONT_UI, size=11))
regex_flags.pack(side="left", padx=(16, 0))
out_regex = outbox(f_regex, height=180)

def do_regex():
    pattern = regex_pattern.get().strip()
    text    = regex_text.get("1.0","end")
    clear(out_regex)
    try:
        flags   = re.IGNORECASE if regex_flags.get() else 0
        matches = list(re.finditer(pattern, text, flags))
        if matches:
            write(out_regex, f"  {len(matches)} match(es) found:\n", "green")
            for i, m in enumerate(matches, 1):
                groups = m.groups()
                write(out_regex, f"  [{i:02d}]  '{m.group()}'  @ pos {m.start()}–{m.end()}", "green")
                if groups:
                    for j, g in enumerate(groups, 1):
                        write(out_regex, f"       Group {j}: {g}", "cyan")
        else:
            write(out_regex, "  No matches found.", "red")
    except re.error as e:
        write(out_regex, f"  Regex error: {e}", "red")

f_diff = ctk.CTkFrame(content, fg_color="transparent")
title(f_diff, "Diff Checker", "Compare two texts and highlight differences")
diff_frames = ctk.CTkFrame(f_diff, fg_color="transparent")
diff_frames.pack(fill="x", pady=(0,8))
diff_left_f  = ctk.CTkFrame(diff_frames, fg_color="transparent")
diff_left_f.pack(side="left", expand=True, fill="both", padx=(0,4))
diff_right_f = ctk.CTkFrame(diff_frames, fg_color="transparent")
diff_right_f.pack(side="left", expand=True, fill="both", padx=(4,0))
ctk.CTkLabel(diff_left_f, text="Text A:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
diff_a = ctk.CTkTextbox(diff_left_f, height=140, fg_color=C["card"], border_width=1,
                         border_color=C["border"], text_color=C["text"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
diff_a.pack(fill="both", expand=True, pady=(2,0))
ctk.CTkLabel(diff_right_f, text="Text B:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
diff_b = ctk.CTkTextbox(diff_right_f, height=140, fg_color=C["card"], border_width=1,
                         border_color=C["border"], text_color=C["text"],
                         font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
diff_b.pack(fill="both", expand=True, pady=(2,0))
mk_btn(f_diff, "  Compare", width=130, command=lambda: do_diff()).pack(anchor="w", pady=(8,0))
out_diff = outbox(f_diff, height=180)

def do_diff():
    a = diff_a.get("1.0","end").splitlines(keepends=True)
    b = diff_b.get("1.0","end").splitlines(keepends=True)
    clear(out_diff)
    diff = list(difflib.unified_diff(a, b, fromfile="Text A", tofile="Text B", lineterm=""))
    if not diff:
        write(out_diff, "  Texts are identical.", "green"); return
    added   = sum(1 for l in diff if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff if l.startswith("-") and not l.startswith("---"))
    write(out_diff, f"  +{added} lines added  /  -{removed} lines removed\n", "yellow")
    for line in diff:
        if line.startswith("---") or line.startswith("+++"): write(out_diff, line.rstrip(), "cyan")
        elif line.startswith("+"): write(out_diff, line.rstrip(), "green")
        elif line.startswith("-"): write(out_diff, line.rstrip(), "red")
        elif line.startswith("@@"): write(out_diff, line.rstrip(), "yellow")
        else: write(out_diff, line.rstrip(), "dim")

f_timestamp = ctk.CTkFrame(content, fg_color="transparent")
title(f_timestamp, "Timestamp Converter", "Convert between Unix timestamps and human-readable dates")
ts_in = lentry(f_timestamp, "Unix timestamp  or  date  (e.g. 2024-01-15 12:00:00)", "")
r_ts = irow(f_timestamp)
mk_btn(r_ts, "  → Human Date", width=150, command=lambda: do_ts_to_human()).pack(side="left")
mk_btn(r_ts, "  → Unix",       width=130, command=lambda: do_ts_to_unix()).pack(side="left", padx=(8,0))
mk_btn(r_ts, "  Now",          width=80,  muted=True, command=lambda: do_ts_now()).pack(side="left", padx=(8,0))
out_ts = outbox(f_timestamp, height=220)

def do_ts_to_human():
    raw = ts_in.get().strip(); clear(out_ts)
    try:
        ts       = int(raw)
        dt_utc   = datetime.datetime.utcfromtimestamp(ts)
        dt_local = datetime.datetime.fromtimestamp(ts)
        write(out_ts, f"  Unix Timestamp  :  {ts}", "dim")
        write(out_ts, f"  UTC             :  {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC", "green")
        write(out_ts, f"  Local           :  {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
        write(out_ts, f"  ISO 8601        :  {dt_utc.isoformat()}Z", "cyan")
        write(out_ts, f"  Readable        :  {dt_utc.strftime('%A, %d %B %Y at %H:%M UTC')}")
        diff = datetime.datetime.utcnow() - dt_utc
        if diff.total_seconds() > 0:
            write(out_ts, f"  Relative        :  {int(diff.total_seconds() // 3600)}h ago", "yellow")
        else:
            write(out_ts, f"  Relative        :  in {int(abs(diff.total_seconds()) // 3600)}h", "yellow")
    except Exception as e: write(out_ts, f"  Error: {e}", "red")

def do_ts_to_unix():
    raw = ts_in.get().strip(); clear(out_ts)
    try:
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
            try:
                dt = datetime.datetime.strptime(raw, fmt)
                ts = int(dt.timestamp())
                write(out_ts, f"  Date Input      :  {raw}", "dim")
                write(out_ts, f"  Unix Timestamp  :  {ts}", "green")
                write(out_ts, f"  Milliseconds    :  {ts * 1000}", "cyan")
                return
            except: pass
        write(out_ts, "  Unrecognised date format.\n  Try: YYYY-MM-DD HH:MM:SS", "red")
    except Exception as e: write(out_ts, f"  Error: {e}", "red")

def do_ts_now():
    clear(out_ts)
    now = datetime.datetime.utcnow()
    ts  = int(now.timestamp())
    write(out_ts, f"  Current UTC     :  {now.strftime('%Y-%m-%d %H:%M:%S')} UTC", "green")
    write(out_ts, f"  Unix Timestamp  :  {ts}", "cyan")
    write(out_ts, f"  Milliseconds    :  {ts * 1000}", "dim")
    write(out_ts, f"  Week Number     :  {now.isocalendar()[1]}", "dim")

f_httpreq = ctk.CTkFrame(content, fg_color="transparent")
title(f_httpreq, "HTTP Request Builder", "Send custom GET / POST requests with headers")
hreq_url        = lentry(f_httpreq, "URL", "https://httpbin.org/get")
hreq_method_var = ctk.StringVar(value="GET")
ctk.CTkLabel(f_httpreq, text="Method:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
hreq_method = ctk.CTkOptionMenu(f_httpreq, variable=hreq_method_var,
                                 values=["GET","POST","PUT","DELETE","PATCH","HEAD"],
                                 fg_color=C["card2"], button_color=C["green_dark"],
                                 button_hover_color=C["green"],
                                 text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
hreq_method.pack(anchor="w", pady=(2,8))
hreq_headers = lentry(f_httpreq, "Headers (JSON, optional)", '{"Authorization": "Bearer token"}')
ctk.CTkLabel(f_httpreq, text="Body (for POST/PUT):", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
hreq_body = ctk.CTkTextbox(f_httpreq, height=70, fg_color=C["card"], border_width=1,
                             border_color=C["border"], text_color=C["text"],
                             font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
hreq_body.pack(fill="x", pady=(2,8))
mk_btn(f_httpreq, "  Send Request", width=150,
       command=lambda: threading.Thread(target=do_httpreq, daemon=True).start()).pack(anchor="w")
out_httpreq = outbox(f_httpreq)

def do_httpreq():
    url    = hreq_url.get().strip()
    method = hreq_method_var.get()
    clear(out_httpreq)
    write(out_httpreq, f"  {method} {url}\n", "dim")
    try:
        headers  = {"User-Agent": "rose-fg/7.0", "Content-Type": "application/json"}
        hdr_raw  = hreq_headers.get().strip()
        if hdr_raw:
            try: headers.update(json.loads(hdr_raw))
            except: write(out_httpreq, "  Warning: invalid header JSON, using defaults.\n", "yellow")
        body_raw  = hreq_body.get("1.0","end").strip()
        body_data = body_raw.encode() if body_raw else None
        req = urllib.request.Request(url, data=body_data, headers=headers, method=method)
        start = time.time()
        res   = urllib.request.urlopen(req, timeout=10)
        elapsed = round((time.time() - start)*1000)
        write(out_httpreq, f"  Status   :  {res.status}  ({elapsed}ms)", "green")
        write(out_httpreq, f"\n  Headers:", "dim")
        for k, v in res.headers.items():
            write(out_httpreq, f"    {k}: {v}", "dim")
        resp_body = res.read().decode(errors="replace")
        write(out_httpreq, f"\n  Body ({len(resp_body)} chars):", "cyan")
        write(out_httpreq, resp_body[:2000])
        if len(resp_body) > 2000:
            write(out_httpreq, f"  ... truncated ({len(resp_body)} total)", "dim")
    except urllib.error.HTTPError as e:
        write(out_httpreq, f"  HTTP {e.code}  {e.reason}", "red")
        write(out_httpreq, e.read().decode(errors="replace")[:500])
    except Exception as e:
        write(out_httpreq, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  GENERATORS
# ════════════════════════════════════════════════════════════
f_uuid = ctk.CTkFrame(content, fg_color="transparent")
title(f_uuid, "UUID Generator", "Generate UUIDs v1, v4, and bulk batches")
uuid_count = lentry(f_uuid, "How many to generate", "10")
r_uuid2 = irow(f_uuid)
mk_btn(r_uuid2, "  UUID v4 ×N", width=140, command=lambda: do_uuid(4)).pack(side="left")
mk_btn(r_uuid2, "  UUID v1",    width=120, command=lambda: do_uuid(1)).pack(side="left", padx=(8,0))
mk_btn(r_uuid2, "Copy All", width=90, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_uuid.get("1.0","end"))]).pack(side="left", padx=(8,0))
out_uuid = outbox(f_uuid, height=260)

def do_uuid(version):
    clear(out_uuid)
    try: count = min(int(uuid_count.get().strip() or 10), 100)
    except: count = 10
    write(out_uuid, f"  Generated {count} UUID v{version}(s):\n", "dim")
    for _ in range(count):
        u = uuid.uuid1() if version == 1 else uuid.uuid4()
        write(out_uuid, f"  {u}", "green")

f_lorem = ctk.CTkFrame(content, fg_color="transparent")
title(f_lorem, "Lorem Ipsum Generator", "Generate placeholder text for design and testing")
lorem_count = lentry(f_lorem, "Number of paragraphs (1–10)", "3")
r_lorem = irow(f_lorem)
mk_btn(r_lorem, "  Generate", width=130, command=lambda: do_lorem()).pack(side="left")
mk_btn(r_lorem, "Copy", width=80, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_lorem.get("1.0","end"))]).pack(side="left", padx=(8,0))
out_lorem = outbox(f_lorem, height=280)

LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt "
    "ut labore et dolore magna aliqua enim ad minim veniam quis nostrud exercitation ullamco "
    "laboris nisi aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit "
    "voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat "
    "cupidatat non proident sunt culpa qui officia deserunt mollit anim id est laborum"
).split()

def do_lorem():
    clear(out_lorem)
    try: count = min(int(lorem_count.get().strip() or 3), 10)
    except: count = 3
    for _ in range(count):
        sentence_count = random.randint(4, 8)
        para_sentences = []
        for _ in range(sentence_count):
            word_count = random.randint(8, 18)
            words = [random.choice(LOREM_WORDS) for _ in range(word_count)]
            words[0] = words[0].capitalize()
            para_sentences.append(" ".join(words) + ".")
        write(out_lorem, "  " + " ".join(para_sentences) + "\n", "")

f_color = ctk.CTkFrame(content, fg_color="transparent")
title(f_color, "Colour Converter", "Convert between HEX, RGB, and HSL colour formats")
color_hex = lentry(f_color, "HEX colour (with or without #)", "#1a8cff")
r_color = irow(f_color)
mk_btn(r_color, "  Convert",     width=120, command=lambda: do_color_convert()).pack(side="left")
mk_btn(r_color, "  Pick Colour", width=130, muted=True, command=lambda: do_color_pick()).pack(side="left", padx=(8,0))
color_preview = ctk.CTkFrame(f_color, height=40, corner_radius=8, fg_color=C["card"])
color_preview.pack(fill="x", pady=(0,4))
out_color = outbox(f_color, height=200)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r2, g, b):
    r2, g, b = r2/255, g/255, b/255
    mx, mn = max(r2,g,b), min(r2,g,b)
    l = (mx+mn)/2
    if mx == mn: h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r2:  h = (g - b) / d + (6 if g < b else 0)
        elif mx == g: h = (b - r2) / d + 2
        else:         h = (r2 - g) / d + 4
        h /= 6
    return round(h*360), round(s*100), round(l*100)

def do_color_convert():
    raw = color_hex.get().strip(); clear(out_color)
    try:
        r2, g, b = hex_to_rgb(raw)
        h, s, l  = rgb_to_hsl(r2, g, b)
        hex_clean = raw if raw.startswith("#") else f"#{raw}"
        color_preview.configure(fg_color=hex_clean)
        write(out_color, f"  HEX   :  {hex_clean.upper()}", "cyan")
        write(out_color, f"  RGB   :  rgb({r2}, {g}, {b})", "green")
        write(out_color, f"  HSL   :  hsl({h}, {s}%, {l}%)", "yellow")
        write(out_color, f"\n  Red   :  {r2}  ({r2/255*100:.1f}%)", "red")
        write(out_color, f"  Green :  {g}  ({g/255*100:.1f}%)", "green")
        write(out_color, f"  Blue  :  {b}  ({b/255*100:.1f}%)", "blue")
        comp_r, comp_g, comp_b = 255-r2, 255-g, 255-b
        comp_hex = f"#{comp_r:02x}{comp_g:02x}{comp_b:02x}"
        write(out_color, f"\n  Complementary :  {comp_hex.upper()}", "dim")
    except Exception as e:
        write(out_color, f"  Error: {e}", "red")

def do_color_pick():
    chosen = colorchooser.askcolor(title="Pick a colour")
    if chosen and chosen[1]:
        hex_val = chosen[1]
        color_hex.delete(0, "end")
        color_hex.insert(0, hex_val)
        do_color_convert()

# ════════════════════════════════════════════════════════════
#  CONVERTERS
# ════════════════════════════════════════════════════════════
f_units = ctk.CTkFrame(content, fg_color="transparent")
title(f_units, "Unit Converter", "Convert length, weight, temperature, and data size")
unit_val = lentry(f_units, "Value", "100")
ctk.CTkLabel(f_units, text="Category:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
unit_cat_var = ctk.StringVar(value="Length")
unit_cat = ctk.CTkOptionMenu(f_units, variable=unit_cat_var,
                              values=["Length","Weight","Temperature","Data Size","Speed","Area","Pressure"],
                              fg_color=C["card2"], button_color=C["green_dark"],
                              button_hover_color=C["green"], text_color=C["text"],
                              font=ctk.CTkFont(family=FONT_UI, size=11))
unit_cat.pack(anchor="w", pady=(2,8))
mk_btn(f_units, "  Convert All", width=140, command=lambda: do_units()).pack(anchor="w")
out_units = outbox(f_units, height=260)

UNIT_TABLES = {
    "Length": {"metres":1.0,"kilometres":0.001,"centimetres":100.0,"millimetres":1000.0,
               "miles":0.000621371,"yards":1.09361,"feet":3.28084,"inches":39.3701,"nautical mi":0.000539957},
    "Weight": {"kilograms":1.0,"grams":1000.0,"milligrams":1000000.0,"tonnes":0.001,
               "pounds":2.20462,"ounces":35.274,"stones":0.157473},
    "Data Size": {"bytes":1.0,"kilobytes":1/1024,"megabytes":1/1048576,"gigabytes":1/1073741824,
                  "terabytes":1/1099511627776,"bits":8.0},
    "Speed": {"m/s":1.0,"km/h":3.6,"mph":2.23694,"knots":1.94384,"ft/s":3.28084},
    "Area":  {"m²":1.0,"km²":1e-6,"cm²":10000,"mm²":1e6,"hectares":1e-4,"acres":0.000247105,"ft²":10.7639,"in²":1550.0},
    "Pressure": {"pascal":1.0,"bar":1e-5,"psi":0.000145038,"atm":9.86923e-6,"mmHg":0.00750062},
}

def do_units():
    clear(out_units)
    try: val = float(unit_val.get().strip())
    except: write(out_units, "  Enter a valid number.", "red"); return
    cat = unit_cat_var.get()
    if cat == "Temperature":
        c = val
        write(out_units, f"  Input (as Celsius)  :  {val}°C\n", "dim")
        write(out_units, f"  Celsius       :  {c:.4f} °C", "green")
        write(out_units, f"  Fahrenheit    :  {c * 9/5 + 32:.4f} °F", "yellow")
        write(out_units, f"  Kelvin        :  {c + 273.15:.4f} K", "cyan")
        write(out_units, f"  Rankine       :  {(c + 273.15) * 9/5:.4f} °R", "dim")
        return
    table    = UNIT_TABLES.get(cat, {})
    base_key = list(table.keys())[0]
    write(out_units, f"  Input  :  {val} {base_key}\n", "dim")
    for unit, rate in table.items():
        write(out_units, f"  {unit:<16}  :  {val * rate:.6g}", "green" if unit == base_key else "")

f_numtools = ctk.CTkFrame(content, fg_color="transparent")
title(f_numtools, "Number Tools", "Convert numbers between bases")
num_in = lentry(f_numtools, "Decimal number", "255")
r_num  = irow(f_numtools)
for lbl, fn in [("→ Binary", lambda n: bin(int(n))),
                ("→ Hex",    lambda n: hex(int(n))),
                ("→ Octal",  lambda n: oct(int(n)))]:
    mk_btn(r_num, lbl, width=110, command=lambda f=fn: do_num(f)).pack(side="left", padx=2)
mk_btn(r_num, "→ Roman", width=110, command=lambda: do_roman()).pack(side="left", padx=2)
out_num = outbox(f_numtools, height=200)

def do_num(fn):
    t = num_in.get().strip(); clear(out_num)
    try: write(out_num, f"  {fn(t)}", "green")
    except Exception as e: write(out_num, f"  Error: {e}", "red")

def do_roman():
    t = num_in.get().strip(); clear(out_num)
    try:
        n = int(t)
        if n <= 0 or n > 3999:
            write(out_num, "  Roman numerals: 1–3999 only.", "yellow"); return
        val_syms = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
                    (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
        result = ""
        for val, sym in val_syms:
            while n >= val:
                result += sym; n -= val
        write(out_num, f"  {result}", "green")
    except Exception as e:
        write(out_num, f"  Error: {e}", "red")

# ════════════════════════════════════════════════════════════
#  NOTES
# ════════════════════════════════════════════════════════════
f_notes = ctk.CTkFrame(content, fg_color="transparent")
title(f_notes, "Notes", "Scratch pad — auto-saves every 30 seconds")
notes_box = ctk.CTkTextbox(f_notes, fg_color=C["card"], border_width=1, border_color=C["border"],
                             text_color=C["text"], font=ctk.CTkFont(family=FONT_MONO, size=12), corner_radius=8)
notes_box.pack(fill="both", expand=True)
try:
    with open(NOTES_FILE) as nf: notes_box.insert("1.0", nf.read())
except: pass

def save_notes():
    with open(NOTES_FILE, "w") as nf: nf.write(notes_box.get("1.0","end"))
    app.after(30000, save_notes)

app.after(30000, save_notes)
r_notes = irow(f_notes)
mk_btn(r_notes, "  Save Notes", width=130,
       command=lambda: open(NOTES_FILE,"w").write(notes_box.get("1.0","end"))).pack(side="left")
mk_btn(r_notes, "Clear", width=80, muted=True,
       command=lambda: notes_box.delete("1.0","end")).pack(side="left", padx=(8,0))

# ════════════════════════════════════════════════════════════
#  SETTINGS
# ════════════════════════════════════════════════════════════
f_settings = ctk.CTkFrame(content, fg_color="transparent")
title(f_settings, "Settings", "Customise appearance and preferences")

def settings_section(parent, label):
    ctk.CTkLabel(parent, text=label, anchor="w",
                 font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
                 text_color=C["text"]).pack(fill="x", pady=(12,4))

settings_section(f_settings, "Appearance")
c_s = card(f_settings); c_s.pack(fill="x", pady=(0,8))
inner_s = ctk.CTkFrame(c_s, fg_color="transparent"); inner_s.pack(fill="x", padx=14, pady=14)
ctk.CTkLabel(inner_s, text="Theme", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
theme_var = ctk.StringVar(value=settings["theme"])
tr = ctk.CTkFrame(inner_s, fg_color="transparent"); tr.pack(fill="x", pady=(2,10))
for t2 in ["dark","light","system"]:
    ctk.CTkRadioButton(tr, text=t2.capitalize(), variable=theme_var, value=t2,
                        text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11)
                        ).pack(side="left", padx=12)
ctk.CTkLabel(inner_s, text="Window Opacity", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
opacity_slider = ctk.CTkSlider(inner_s, from_=0.3, to=1.0, number_of_steps=14,
                                button_color=C["green"], button_hover_color=C["green_dim"],
                                progress_color=C["green_dark"])
opacity_slider.set(settings.get("opacity", 1.0))
opacity_slider.pack(fill="x", pady=(2,4))
opacity_val_label = ctk.CTkLabel(inner_s, text="100%",
                                  font=ctk.CTkFont(family=FONT_MONO, size=10),
                                  text_color=C["text_dim"])
opacity_val_label.pack(anchor="w", pady=(0,8))

def _apply_opacity(val):
    val = float(val)
    pct = round(val * 100)
    opacity_val_label.configure(text=f"{pct}%")
    app.attributes("-alpha", val)

opacity_slider.configure(command=_apply_opacity)
ctk.CTkLabel(inner_s, text="Font Size", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
font_slider = ctk.CTkSlider(inner_s, from_=9, to=16, number_of_steps=7,
                             button_color=C["green"], button_hover_color=C["green_dim"],
                             progress_color=C["green_dark"])
font_slider.set(settings["font_size"])
font_slider.pack(fill="x", pady=(2,4))
settings_section(f_settings, "Default Tab")
tab_var = ctk.StringVar(value=settings["default_tab"])
tab_opt = ctk.CTkOptionMenu(f_settings, variable=tab_var,
                              values=["OSINT","Port Scanner","Network","Discord","Passwords","Settings"],
                              fg_color=C["card2"], button_color=C["green_dark"],
                              button_hover_color=C["green"],
                              text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
tab_opt.pack(anchor="w", pady=(0,16))

def _show_restart_dialog():
    dialog = tk.Toplevel(app)
    dialog.title("Restart Required")
    dialog.geometry("360x160")
    dialog.configure(bg=C["card"])
    dialog.resizable(False, False)
    dialog.grab_set()
    app.update_idletasks()
    x = app.winfo_x() + (app.winfo_width()  // 2) - 180
    y = app.winfo_y() + (app.winfo_height() // 2) - 80
    dialog.geometry(f"+{x}+{y}")
    tk.Label(dialog, text="Settings Saved", bg=C["card"], fg=C["green"],
             font=(FONT_UI, 13, "bold")).pack(pady=(20, 4))
    tk.Label(dialog, text="Some changes need a restart to take full effect.",
             bg=C["card"], fg=C["text_dim"], font=(FONT_UI, 10)).pack()
    btn_frame = tk.Frame(dialog, bg=C["card"])
    btn_frame.pack(pady=20)
    def restart_now():
        dialog.destroy(); app.destroy()
        os.execv(sys.executable, [sys.executable] + sys.argv)
    def restart_later():
        dialog.destroy()
    tk.Button(btn_frame, text="  Restart Now  ", command=restart_now,
              bg=C["green_dark"], fg=C["green"], relief="flat",
              font=(FONT_UI, 11), cursor="hand2",
              activebackground=C["green"], activeforeground=C["bg"],
              padx=8, pady=4).pack(side="left", padx=8)
    tk.Button(btn_frame, text="  Later  ", command=restart_later,
              bg=C["card2"], fg=C["text_dim"], relief="flat",
              font=(FONT_UI, 11), cursor="hand2",
              activebackground=C["border"], activeforeground=C["text"],
              padx=8, pady=4).pack(side="left", padx=8)

def save_and_apply():
    settings["theme"]       = theme_var.get()
    settings["opacity"]     = opacity_slider.get()
    settings["font_size"]   = int(font_slider.get())
    settings["default_tab"] = tab_var.get()
    save_settings(settings)
    ctk.set_appearance_mode(settings["theme"])
    _apply_opacity(settings.get("opacity", 1.0))
    _show_restart_dialog()

mk_btn(f_settings, "  Save Settings", width=160, command=save_and_apply).pack(anchor="w")
out_saved = ctk.CTkLabel(f_settings, text="", text_color=C["green"],
                           font=ctk.CTkFont(family=FONT_MONO, size=11))
out_saved.pack(anchor="w", pady=8)

# ════════════════════════════════════════════════════════════
#  SIDEBAR MENUS  — all frames now defined above
# ════════════════════════════════════════════════════════════
make_section("OSINT",
    ["IP Lookup","Email Headers","WHOIS","Reverse DNS","SSL Checker","Subnet Calc","DNS Records","Subdomain Finder","SPF/DMARC"],
    [f_ip, f_email, f_whois, f_rdns, f_ssl, f_subnet, f_dnsrec, f_subdomains, f_spf])

make_section("Port Scanner",
    ["Scan Ports","Banner Grabber"],
    [f_ps, f_banner])

make_section("Network",
    ["Ping","Traceroute","DNS Lookup","My IP","Netstat","ARP Scanner","Speed Test","Port Map"],
    [f_ping, f_trace, f_dns, f_myip, f_netstat, f_arp, f_speed, f_portmap])

make_section("Discord",
    ["Send Message","Embed Sender","Webhook","DM Sender",
     "Bot Info","Channel Info","Delete Message",
     "Server Info","Role Lister","Message Fetcher",
     "User Lookup","Bulk Delete","Bot Builder"],
    [f_disc_send, f_disc_embed, f_disc_webhook, f_disc_dm,
     f_disc_info, f_disc_channel, f_disc_delete,
     f_disc_server, f_disc_roles, f_disc_fetch,
     f_disc_user, f_disc_bulkdel, f_disc_builder])

make_section("Passwords",
    ["Generator","Passphrase","Hash Generator","Strength Checker","Pwned Password"],
    [f_passgen, f_passphrase, f_hasher, f_passcheck, f_pwned])

make_section("Encoding",
    ["Base64","URL Encode","Hex Converter","Caesar / ROT13","JWT Decoder","Morse Code","Binary ↔ Text"],
    [f_b64, f_url_enc, f_hex_enc, f_caesar, f_jwt, f_morse, f_binascii])

make_section("System Info",
    ["System Info","Processes","Disk Info","Env Variables"],
    [f_sysinfo, f_procs, f_disk, f_envvars])

make_section("Web Tools",
    ["HTTP Headers","Site Status","Bulk IP Lookup","Robots.txt"],
    [f_http, f_sitestatus, f_bulkip, f_robots])

make_section("File Tools",
    ["File Hash","File Info","File Metadata","File Comparator"],
    [f_filehash, f_fileinfo, f_filemeta, f_filecmp])

make_section("Crypto",
    ["Crypto Prices","Currency Converter"],
    [f_crypto, f_convert])

make_section("Text Tools",
    ["Text Transformer"],
    [f_texttools])

make_section("QR Code",
    ["QR Generator"],
    [f_qr])

make_section("Social Media",
    ["Platform IP Lookup","Username Checker","Email Validator"],
    [f_social_ip, f_username, f_emailval])

make_section("Dev Tools",
    ["JSON Formatter","Regex Tester","Diff Checker","Timestamp Converter","HTTP Request Builder"],
    [f_json_fmt, f_regex, f_diff, f_timestamp, f_httpreq])

make_section("Generators",
    ["UUID Generator","Colour Converter","Lorem Ipsum"],
    [f_uuid, f_color, f_lorem])

make_section("Converters",
    ["Unit Converter","Number Converter"],
    [f_units, f_numtools])

_divider(sidebar, C["green_dark"], 4)

notes_btn = ctk.CTkButton(
    sidebar, text="  ▦  Notes", anchor="w",
    fg_color="transparent", text_color=C["text_dim"],
    hover_color=C["card2"], font=ctk.CTkFont(family=FONT_UI, size=12), height=32, corner_radius=6)
notes_btn.configure(command=lambda: show(f_notes, notes_btn))
notes_btn.pack(fill="x", padx=8, pady=1)

settings_btn = ctk.CTkButton(
    sidebar, text="  ◎  Settings", anchor="w",
    fg_color="transparent", text_color=C["text_dim"],
    hover_color=C["card2"], font=ctk.CTkFont(family=FONT_UI, size=12), height=32, corner_radius=6)
settings_btn.configure(command=lambda: show(f_settings, settings_btn))
settings_btn.pack(fill="x", padx=8, pady=(0, 16))

show(f_ip)
app.mainloop()
