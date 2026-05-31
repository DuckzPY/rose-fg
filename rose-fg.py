import socket
import threading
import urllib.request
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
from PIL import Image, ImageTk
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
    'Ready':     "#00FF54",
}
FONT_MONO   = "JetBrains Mono"
FONT_UI     = "Inter"
FONT_HEADER = "Inter"

app = ctk.CTk()
app.title("rose-fg  v6.0")
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

# Rose logo image
_logo_img_ref = [None]
try:
    _logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rose_logo.png")
    _logo_pil  = Image.open(_logo_path).resize((42, 42), Image.LANCZOS)
    _logo_ctk  = ctk.CTkImage(light_image=_logo_pil, dark_image=_logo_pil, size=(42, 42))
    _logo_img_ref[0] = _logo_ctk
    logo_img_label = ctk.CTkLabel(logo_frame, image=_logo_ctk, text="")
    logo_img_label.pack(side="left", padx=(0, 10), pady=4)
except Exception:
    # Fallback pulsing dot if image not found
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
ctk.CTkLabel(logo_text, text="v6.0",
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

def outbox(parent, height=320):
    fs = settings["font_size"]
    outer = ctk.CTkFrame(parent, fg_color=C["card"], corner_radius=8,
                          border_width=1, border_color=C["border"])
    outer.pack(fill="both", expand=True, pady=(8, 0))
    bar = ctk.CTkFrame(outer, height=24, fg_color=C["card2"], corner_radius=0)
    bar.pack(fill="x")
    ctk.CTkLabel(bar, text="  OUTPUT", font=ctk.CTkFont(family=FONT_MONO, size=9),
                 text_color=C["text_muted"]).pack(side="left", padx=8, pady=3)
    for col in [C["red"], C["yellow"], C["green"]]:
        ctk.CTkFrame(bar, width=8, height=8, corner_radius=4, fg_color=col).pack(
            side="right", padx=3, pady=8)
    box = ctk.CTkTextbox(outer, height=height,
                          font=ctk.CTkFont(family=FONT_MONO, size=fs),
                          fg_color="transparent", text_color=C["text"],
                          scrollbar_button_color=C["border"],
                          wrap="word")
    box.pack(fill="both", expand=True, padx=4, pady=4)
    box.configure(state="disabled")
    box.tag_config("green",  foreground=C["green"])
    box.tag_config("red",    foreground=C["red"])
    box.tag_config("blue",   foreground=C["blue"])
    box.tag_config("yellow", foreground=C["yellow"])
    box.tag_config("cyan",   foreground=C["cyan"])
    box.tag_config("dim",    foreground=C["text_dim"])
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
    fg = C["red"] if danger else (C["card2"] if muted else C["green_dark"])
    hover = "#991111" if danger else (C["card"] if muted else "#550018")
    txt = "#ffffff" if danger else (C["text_dim"] if muted else C["green"])
    b = ctk.CTkButton(parent, text=text, command=command, width=width,
                      fg_color=fg, hover_color=hover, text_color=txt,
                      border_width=1,
                      border_color=C["red"] if danger else (C["border"] if muted else C["green_dark"]),
                      font=ctk.CTkFont(family=FONT_UI, size=12),
                      corner_radius=6, **kw)
    return b

def api_discord(path, token, method="GET", body=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bot {token}"}
    req = urllib.request.Request(
        f"https://discord.com/api/v10{path}", data=body,
        headers=headers, method=method)
    return json.loads(urllib.request.urlopen(req, timeout=8).read())

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
                            ("Reply-To", "Reply-To:.*"), ("Date", "Date:.*")]:
        match = re.findall(pattern, text)
        write(out_email, f"  {label:<10} :  {match[0].strip() if match else 'Not found'}")
    write(out_email, f"\n  IPs extracted:", "cyan")
    if ips:
        for ip in ips: write(out_email, f"    {ip}", "green")
    else:
        write(out_email, "    None found.", "dim")

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
    whois_available = False
    try:
        result = subprocess.run(["whois", "--version"], capture_output=True, timeout=3)
        whois_available = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        whois_available = False
    if whois_available:
        try:
            r = subprocess.run(["whois", t], capture_output=True, text=True, timeout=10)
            write(out_whois, r.stdout or "No output.")
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
        write(out_whois, f"  Updated     :  {data.updated_date}")
        write(out_whois, f"  Name Servers:  {data.name_servers}")
        write(out_whois, f"  Status      :  {data.status}")
    except Exception as e:
        write(out_whois, f"  Auto-install failed: {e}", "red")
        write(out_whois, "  pip install python-whois", "yellow")

btn_w.configure(command=lambda: threading.Thread(target=do_whois, daemon=True).start())

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
            cert = s.getpeercert()
            protocol = s.version()
        subject  = dict(x[0] for x in cert.get("subject", []))
        issuer   = dict(x[0] for x in cert.get("issuer", []))
        not_before = cert.get("notBefore", "N/A")
        not_after  = cert.get("notAfter",  "N/A")
        try:
            exp_dt = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
            days_left = (exp_dt - datetime.datetime.utcnow()).days
            expiry_tag = "green" if days_left > 30 else ("yellow" if days_left > 7 else "red")
            expiry_str = f"{not_after}  ({days_left} days remaining)"
        except:
            days_left = -1; expiry_tag = "dim"; expiry_str = not_after
        sans = [v for t, v in cert.get("subjectAltName", []) if t == "DNS"]
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
        net = ipaddress.ip_network(raw, strict=False)
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
    except Exception as e:
        write(out_subnet, f"  Error: {e}", "red")

btn_subnet.configure(command=lambda: threading.Thread(target=do_subnet, daemon=True).start())

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
ctk.CTkLabel(pr, text="Port Range  —  tip: keep ranges small (e.g. 1–1024) for speed", anchor="w",
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
                          fg_color=C["card"], text_color=C["text"], corner_radius=8,
                          border_width=1, border_color=C["border"], wrap="word")
out_ps.pack(fill="x", pady=(8, 8)); out_ps.configure(state="disabled")
out_ps.tag_config("green", foreground=C["green"])
out_ps.tag_config("red",   foreground=C["red"])
out_ps.tag_config("blue",  foreground=C["blue"])
out_ps.tag_config("dim",   foreground=C["text_dim"])
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
    if end - start > 9999:
        write(out_ps, f"  Range {start}-{end} is {end-start+1} ports — this may take a while.", "yellow")
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
        r = subprocess.run(cmd, capture_output=True, text=True)
        write(o, r.stdout)
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
        ips = list(dict.fromkeys(r[4][0] for r in results))
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

f_ping  = make_net_tool("Ping",       "Send ICMP packets to test connectivity",  "IP or domain", "Ping",  do_ping)
f_trace = make_net_tool("Traceroute", "Trace the route packets take to a host",  "IP or domain", "Trace", do_trace)
f_dns   = make_net_tool("DNS Lookup", "Resolve a domain to its IP address",       "Domain",       "Lookup",do_dns)

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
            r = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        else:
            r = subprocess.run(["netstat", "-tunap"], capture_output=True, text=True)
            if r.returncode != 0:
                r = subprocess.run(["ss", "-tunap"], capture_output=True, text=True)
        write(out_netstat, r.stdout or r.stderr)
    except Exception as e: write(out_netstat, f"  Error: {e}", "red")

def disc_field(parent, label, ph, hide=False):
    ctk.CTkLabel(parent, text=label, anchor="w",
                 font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
    e = ctk.CTkEntry(parent, placeholder_text=ph, show="*" if hide else "",
                     fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                     placeholder_text_color=C["text_muted"],
                     font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
    e.pack(fill="x", pady=(2, 8))
    return e

f_disc_send = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_send, "Send Message", "Send a message to any channel your bot is in")
dt1 = disc_field(f_disc_send, "Bot Token", "Bot token", True)
dc1 = disc_field(f_disc_send, "Channel ID", "Channel ID")
dm1 = disc_field(f_disc_send, "Message", "Your message")
mk_btn(f_disc_send, "  Send Message", width=150,
       command=lambda: threading.Thread(target=do_disc_send, daemon=True).start()).pack(anchor="w")
out_ds = outbox(f_disc_send, height=160)

def do_disc_send():
    token, ch, msg = dt1.get().strip(), dc1.get().strip(), dm1.get().strip()
    if not all([token, ch, msg]): write(out_ds, "  Fill in all fields.", "yellow"); return
    clear(out_ds)
    try:
        api_discord(f"/channels/{ch}/messages", token, "POST", json.dumps({"content": msg}).encode())
        write(out_ds, "  Message sent successfully.", "green")
    except Exception as e: write(out_ds, f"  Error: {e}", "red")

f_disc_embed = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_embed, "Embed Sender", "Send a rich embed message via your bot")
dt2 = disc_field(f_disc_embed, "Bot Token", "Bot token", True)
dc2 = disc_field(f_disc_embed, "Channel ID", "Channel ID")
de_title  = disc_field(f_disc_embed, "Embed Title", "Title")
de_desc   = disc_field(f_disc_embed, "Description", "Description")
de_color  = disc_field(f_disc_embed, "Colour (hex)", "5865f2")
de_footer = disc_field(f_disc_embed, "Footer text (optional)", "Footer")
mk_btn(f_disc_embed, "  Send Embed", width=140,
       command=lambda: threading.Thread(target=do_embed, daemon=True).start()).pack(anchor="w")
out_embed = outbox(f_disc_embed, height=100)

def do_embed():
    token, ch = dt2.get().strip(), dc2.get().strip()
    if not token or not ch: write(out_embed, "  Fill in token and channel.", "yellow"); return
    clear(out_embed)
    try:
        color_int = int((de_color.get().strip().replace("#", "") or "5865f2"), 16)
        embed = {"title": de_title.get().strip(), "description": de_desc.get().strip(), "color": color_int}
        footer = de_footer.get().strip()
        if footer: embed["footer"] = {"text": footer}
        api_discord(f"/channels/{ch}/messages", token, "POST", json.dumps({"embeds": [embed]}).encode())
        write(out_embed, "  Embed sent.", "green")
    except Exception as e: write(out_embed, f"  Error: {e}", "red")

f_disc_webhook = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_webhook, "Webhook Sender", "Send messages via a webhook URL")
dw_url  = disc_field(f_disc_webhook, "Webhook URL",             "https://discord.com/api/webhooks/...")
dw_name = disc_field(f_disc_webhook, "Display Name (optional)", "Custom name")
dw_msg  = disc_field(f_disc_webhook, "Message",                  "Your message")
mk_btn(f_disc_webhook, "  Send Webhook", width=150,
       command=lambda: threading.Thread(target=do_webhook, daemon=True).start()).pack(anchor="w")
out_wh = outbox(f_disc_webhook, height=140)

def do_webhook():
    url, msg = dw_url.get().strip(), dw_msg.get().strip()
    if not url or not msg: write(out_wh, "  Fill in URL and message.", "yellow"); return
    clear(out_wh)
    try:
        payload = {"content": msg}
        name = dw_name.get().strip()
        if name: payload["username"] = name
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req, timeout=5)
        write(out_wh, "  Webhook sent.", "green")
    except Exception as e: write(out_wh, f"  Error: {e}", "red")

f_disc_dm = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_dm, "DM Sender", "Send a direct message to any user by ID")
dt3 = disc_field(f_disc_dm, "Bot Token", "Bot token", True)
du3 = disc_field(f_disc_dm, "User ID",   "User ID")
dm3 = disc_field(f_disc_dm, "Message",   "Your message")
mk_btn(f_disc_dm, "  Send DM", width=130,
       command=lambda: threading.Thread(target=do_dm, daemon=True).start()).pack(anchor="w")
out_dm = outbox(f_disc_dm, height=160)

def do_dm():
    token, user, msg = dt3.get().strip(), du3.get().strip(), dm3.get().strip()
    if not all([token, user, msg]): write(out_dm, "  Fill in all fields.", "yellow"); return
    clear(out_dm)
    try:
        ch = api_discord("/users/@me/channels", token, "POST", json.dumps({"recipient_id": user}).encode())
        api_discord(f"/channels/{ch['id']}/messages", token, "POST", json.dumps({"content": msg}).encode())
        write(out_dm, "  DM sent.", "green")
    except Exception as e: write(out_dm, f"  Error: {e}", "red")

f_disc_info = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_info, "Bot Info", "Retrieve info and server list for your bot")
dt4 = disc_field(f_disc_info, "Bot Token", "Bot token", True)
mk_btn(f_disc_info, "  Get Info", width=130,
       command=lambda: threading.Thread(target=do_bot_info, daemon=True).start()).pack(anchor="w")
out_bi = outbox(f_disc_info)

def do_bot_info():
    token = dt4.get().strip()
    if not token: write(out_bi, "  Enter a bot token.", "yellow"); return
    clear(out_bi)
    try:
        d = api_discord("/users/@me", token)
        guilds = api_discord("/users/@me/guilds", token)
        write(out_bi, f"  Username  :  {d['username']}", "green")
        write(out_bi, f"  ID        :  {d['id']}")
        write(out_bi, f"  Servers   :  {len(guilds)}\n")
        for g in guilds:
            write(out_bi, f"    {g['name']}  ({g['id']})", "dim")
    except Exception as e: write(out_bi, f"  Error: {e}", "red")

f_disc_channel = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_channel, "Channel Info", "Get details about a Discord channel")
dt5 = disc_field(f_disc_channel, "Bot Token",  "Bot token", True)
dc5 = disc_field(f_disc_channel, "Channel ID", "Channel ID")
mk_btn(f_disc_channel, "  Get Info", width=130,
       command=lambda: threading.Thread(target=do_channel_info, daemon=True).start()).pack(anchor="w")
out_ci = outbox(f_disc_channel)

def do_channel_info():
    token, ch = dt5.get().strip(), dc5.get().strip()
    if not token or not ch: write(out_ci, "  Fill in all fields.", "yellow"); return
    clear(out_ci)
    try:
        d = api_discord(f"/channels/{ch}", token)
        write(out_ci, f"  Name      :  {d.get('name','N/A')}")
        write(out_ci, f"  ID        :  {d.get('id')}")
        write(out_ci, f"  Type      :  {d.get('type')}")
        write(out_ci, f"  Topic     :  {d.get('topic') or 'None'}")
        write(out_ci, f"  Guild ID  :  {d.get('guild_id','N/A')}")
        write(out_ci, f"  NSFW      :  {d.get('nsfw', False)}")
    except Exception as e: write(out_ci, f"  Error: {e}", "red")

f_disc_delete = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_delete, "Delete Message", "Delete a specific message by ID")
dt7 = disc_field(f_disc_delete, "Bot Token",  "Bot token", True)
dc7 = disc_field(f_disc_delete, "Channel ID", "Channel ID")
dm7 = disc_field(f_disc_delete, "Message ID", "Message ID")
mk_btn(f_disc_delete, "  Delete", width=120, danger=True,
       command=lambda: threading.Thread(target=do_delete, daemon=True).start()).pack(anchor="w")
out_del = outbox(f_disc_delete, height=140)

def do_delete():
    token, ch, mid = dt7.get().strip(), dc7.get().strip(), dm7.get().strip()
    if not all([token, ch, mid]): write(out_del, "  Fill in all fields.", "yellow"); return
    clear(out_del)
    try:
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{ch}/messages/{mid}",
            headers={"Authorization": f"Bot {token}"}, method="DELETE")
        urllib.request.urlopen(req, timeout=5)
        write(out_del, "  Message deleted.", "green")
    except Exception as e: write(out_del, f"  Error: {e}", "red")

f_disc_server = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_server, "Server Info", "Get detailed information about a Discord server")
dt_sv = disc_field(f_disc_server, "Bot Token",         "Bot token", True)
dc_sv = disc_field(f_disc_server, "Server (Guild) ID", "Server ID")
mk_btn(f_disc_server, "  Get Server Info", width=160,
       command=lambda: threading.Thread(target=do_server_info, daemon=True).start()).pack(anchor="w")
out_sv = outbox(f_disc_server)

def do_server_info():
    token, gid = dt_sv.get().strip(), dc_sv.get().strip()
    if not token or not gid: write(out_sv, "  Fill in all fields.", "yellow"); return
    clear(out_sv)
    try:
        d = api_discord(f"/guilds/{gid}?with_counts=true", token)
        write(out_sv, f"  Name            :  {d.get('name','N/A')}", "green")
        write(out_sv, f"  ID              :  {d.get('id')}")
        write(out_sv, f"  Owner ID        :  {d.get('owner_id','N/A')}", "cyan")
        mc = d.get('approximate_member_count','N/A')
        write(out_sv, f"  Members         :  {mc:,}" if isinstance(mc, int) else f"  Members         :  {mc}")
        write(out_sv, f"  Online          :  {d.get('approximate_presence_count','N/A')}", "green")
        write(out_sv, f"  Boost Level     :  {d.get('premium_tier', 0)}", "yellow")
        write(out_sv, f"  Boosts          :  {d.get('premium_subscription_count', 0)}")
        write(out_sv, f"  Verification    :  {d.get('verification_level', 0)}")
        write(out_sv, f"  Explicit Filter :  {d.get('explicit_content_filter', 0)}")
        write(out_sv, f"  Locale          :  {d.get('preferred_locale','N/A')}")
        write(out_sv, f"  Description     :  {d.get('description') or 'None'}", "dim")
        features = d.get('features', [])
        if features:
            write(out_sv, f"\n  Features:", "dim")
            for feat in features: write(out_sv, f"    {feat}", "blue")
    except Exception as e: write(out_sv, f"  Error: {e}", "red")

f_disc_roles = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_roles, "Role Lister", "List all roles in a Discord server with permissions")
dt_rl = disc_field(f_disc_roles, "Bot Token",         "Bot token", True)
dc_rl = disc_field(f_disc_roles, "Server (Guild) ID", "Server ID")
mk_btn(f_disc_roles, "  List Roles", width=140,
       command=lambda: threading.Thread(target=do_role_list, daemon=True).start()).pack(anchor="w")
out_rl = outbox(f_disc_roles)

def do_role_list():
    token, gid = dt_rl.get().strip(), dc_rl.get().strip()
    if not token or not gid: write(out_rl, "  Fill in all fields.", "yellow"); return
    clear(out_rl)
    try:
        roles = api_discord(f"/guilds/{gid}/roles", token)
        roles = sorted(roles, key=lambda r: -r.get("position", 0))
        write(out_rl, f"  Found {len(roles)} roles:\n", "dim")
        for i, role in enumerate(roles, 1):
            name    = role.get("name", "N/A")
            rid     = role.get("id", "N/A")
            color   = f"#{role.get('color', 0):06x}" if role.get("color") else "none"
            managed = "  [bot]" if role.get("managed") else ""
            write(out_rl, f"  {i:<4}  {name:<28}  {rid:<20}  {color}{managed}", "green" if role.get("color") else "")
    except Exception as e: write(out_rl, f"  Error: {e}", "red")

f_disc_fetch = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_fetch, "Message Fetcher", "Fetch recent messages from a channel")
dt_mf = disc_field(f_disc_fetch, "Bot Token",       "Bot token", True)
dc_mf = disc_field(f_disc_fetch, "Channel ID",      "Channel ID")
dl_mf = disc_field(f_disc_fetch, "Limit (max 100)", "20")
mk_btn(f_disc_fetch, "  Fetch Messages", width=160,
       command=lambda: threading.Thread(target=do_fetch_msgs, daemon=True).start()).pack(anchor="w")
out_mf = outbox(f_disc_fetch)

def do_fetch_msgs():
    token, ch = dt_mf.get().strip(), dc_mf.get().strip()
    limit = min(int(dl_mf.get().strip() or "20"), 100)
    if not token or not ch: write(out_mf, "  Fill in all fields.", "yellow"); return
    clear(out_mf)
    try:
        msgs = api_discord(f"/channels/{ch}/messages?limit={limit}", token)
        write(out_mf, f"  Fetched {len(msgs)} message(s):\n", "dim")
        for m in reversed(msgs):
            author = m.get("author", {}).get("username", "Unknown")
            ts     = m.get("timestamp", "")[:19].replace("T", " ")
            content_text = m.get("content", "") or "[embed/attachment]"
            write(out_mf, f"  [{ts}]  {author}:", "cyan")
            write(out_mf, f"    {content_text}\n")
    except Exception as e: write(out_mf, f"  Error: {e}", "red")

f_disc_builder = ctk.CTkFrame(content, fg_color="transparent")
title(f_disc_builder, "Bot Builder", "Generate a ready-to-run Discord bot script")
db_name   = disc_field(f_disc_builder, "Bot Name",       "MyBot")
db_prefix = disc_field(f_disc_builder, "Command Prefix", "!")
r_db = irow(f_disc_builder)
mk_btn(r_db, "  Generate Code", width=150, command=lambda: do_builder()).pack(side="left")
mk_btn(r_db, "Copy", width=90, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_builder.get("1.0","end"))]).pack(side="left", padx=(8,0))
out_builder = outbox(f_disc_builder, height=320)

def do_builder():
    name   = db_name.get().strip()   or "MyBot"
    prefix = db_prefix.get().strip() or "!"
    code = f'''import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="{prefix}", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"{name} is online as {{bot.user}}")

@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {{ctx.author.mention}}!")

@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {{round(bot.latency * 1000)}}ms")

@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

bot.run("YOUR_TOKEN_HERE")
'''
    clear(out_builder); write(out_builder, code)

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
pg_up2 = ctk.CTkCheckBox(inner_pg2, text="Include uppercase",
                           text_color=C["text"], font=ctk.CTkFont(family=FONT_UI, size=11))
pg_up2.pack(anchor="w", pady=2); pg_up2.select()
r_pg2 = irow(f_passgen)
mk_btn(r_pg2, "  Generate × 5", width=150, command=lambda: do_passgen2()).pack(side="left")
mk_btn(r_pg2, "Copy First", width=100, muted=True,
       command=lambda: [app.clipboard_clear(), app.clipboard_append(out_pg2.get("2.0","3.0").strip())]).pack(side="left", padx=(8,0))
out_pg2 = outbox(f_passgen, height=200)

def do_passgen2():
    try: length = int(pg_len2.get().strip() or 16)
    except: length = 16
    chars = string.ascii_lowercase
    if pg_up2.get():  chars += string.ascii_uppercase
    if pg_num2.get(): chars += string.digits
    if pg_sym2.get(): chars += string.punctuation
    clear(out_pg2)
    write(out_pg2, "  Generated passwords:\n", "dim")
    for _ in range(5):
        pw = "".join(random.choice(chars) for _ in range(length))
        write(out_pg2, f"  {pw}", "green")

f_hasher = ctk.CTkFrame(content, fg_color="transparent")
title(f_hasher, "Hash Generator", "MD5 · SHA1 · SHA256 · SHA512")
hash_in = lentry(f_hasher, "Text to hash", "Enter text here")
mk_btn(f_hasher, "  Generate Hashes", width=170, command=lambda: do_hash()).pack(anchor="w")
out_hash = outbox(f_hasher, height=200)

def do_hash():
    t = hash_in.get().strip().encode(); clear(out_hash)
    write(out_hash, f"  MD5", "dim")
    write(out_hash, f"  {hashlib.md5(t).hexdigest()}\n", "yellow")
    write(out_hash, f"  SHA1", "dim")
    write(out_hash, f"  {hashlib.sha1(t).hexdigest()}\n", "blue")
    write(out_hash, f"  SHA256", "dim")
    write(out_hash, f"  {hashlib.sha256(t).hexdigest()}\n", "green")
    write(out_hash, f"  SHA512", "dim")
    write(out_hash, f"  {hashlib.sha512(t).hexdigest()}", "")

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
    if tips:
        write(out_pc, "\n  Suggestions:", "yellow")
        for t in tips: write(out_pc, f"    {t}", "dim")

f_b64 = ctk.CTkFrame(content, fg_color="transparent")
title(f_b64, "Base64", "Encode or decode Base64 strings")
ctk.CTkLabel(f_b64, text="Input:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
b64_in = ctk.CTkTextbox(f_b64, height=100, fg_color=C["card"], border_width=1,
                          border_color=C["border"], text_color=C["text"],
                          font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
b64_in.pack(fill="x", pady=(2, 8))
r_b64 = irow(f_b64)
mk_btn(r_b64, "  Encode", width=110, command=lambda: do_b64(True)).pack(side="left")
mk_btn(r_b64, "  Decode", width=110, command=lambda: do_b64(False)).pack(side="left", padx=(8,0))
out_b64 = outbox(f_b64, height=200)

def do_b64(enc):
    t = b64_in.get("1.0", "end").strip(); clear(out_b64)
    try:
        result = base64.b64encode(t.encode()).decode() if enc else base64.b64decode(t.encode()).decode()
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
mk_btn(r_caesar, "  Encode", width=110, command=lambda: do_caesar(1)).pack(side="left")
mk_btn(r_caesar, "  Decode", width=110, command=lambda: do_caesar(-1)).pack(side="left", padx=(8,0))
mk_btn(r_caesar, "  ROT13",  width=100, command=lambda: do_rot13()).pack(side="left", padx=(8,0))
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
        write(out_sys, f"  RAM Used      :  {mem.used // (1024**3)} GB  ({mem.percent}%)")
        write(out_sys, f"  RAM Free      :  {mem.available // (1024**3)} GB")
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
        r = subprocess.run(cmd, capture_output=True, text=True)
        write(out_procs, r.stdout)
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
            paths = ["/"]
            write(out_disk, f"  {'Mount':<20}  {'Total':>10}  {'Used':>10}  {'Free':>10}  {'Use%':>6}", "dim")
            write(out_disk, "  " + "─" * 64, "dim")
            for path in paths:
                try:
                    total, used, free = shutil.disk_usage(path)
                    if total == 0: continue
                    pct = round(used / total * 100)
                    tag = "red" if pct > 90 else ("yellow" if pct > 75 else "green")
                    write(out_disk, f"  {path:<20}  {total//1073741824:>8} GB  {used//1073741824:>8} GB  {free//1073741824:>8} GB  {pct:>5}%", tag)
                except Exception: pass
    except Exception as e:
        write(out_disk, f"  Error: {e}", "red")

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
            write(out_http, f"  {k:<30} :  {v}")
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
        res = urllib.request.urlopen(req, timeout=8)
        write(out_site, f"  ONLINE  —  Status {res.status}", "green")
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

f_filehash = ctk.CTkFrame(content, fg_color="transparent")
title(f_filehash, "File Hash", "Compute MD5 / SHA hashes of any file")
fh_path = make_drag_drop_entry(f_filehash, "File path", "C:\\path\\to\\file.exe  or  /path/to/file")
mk_btn(f_filehash, "  Hash File", width=130, command=lambda: do_filehash()).pack(anchor="w")
out_fh = outbox(f_filehash)

def do_filehash():
    raw_path = fh_path.get().strip()
    path = raw_path.strip('"').strip("'")
    clear(out_fh)
    if not path: write(out_fh, "  Enter or browse to a file path.", "yellow"); return
    if not os.path.exists(path): write(out_fh, f"  File not found: {path}", "red"); return
    if os.path.isdir(path): write(out_fh, "  Path is a directory.", "yellow"); return
    try:
        with open(path, "rb") as f: data = f.read()
        write(out_fh, f"  File    :  {os.path.basename(path)}")
        write(out_fh, f"  Size    :  {os.path.getsize(path):,} bytes\n")
        write(out_fh, f"  MD5     :  {hashlib.md5(data).hexdigest()}", "yellow")
        write(out_fh, f"  SHA1    :  {hashlib.sha1(data).hexdigest()}", "blue")
        write(out_fh, f"  SHA256  :  {hashlib.sha256(data).hexdigest()}", "green")
    except Exception as e: write(out_fh, f"  Error: {e}", "red")

f_fileinfo = ctk.CTkFrame(content, fg_color="transparent")
title(f_fileinfo, "File Info", "View metadata and details for any file")
fi_path = make_drag_drop_entry(f_fileinfo, "File path", "C:\\path\\to\\file  or  /path/to/file")
mk_btn(f_fileinfo, "  Get Info", width=130, command=lambda: do_fileinfo()).pack(anchor="w")
out_fi = outbox(f_fileinfo)

def do_fileinfo():
    raw_path = fi_path.get().strip()
    path = raw_path.strip('"').strip("'")
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
    except Exception as e: write(out_fi, f"  Error: {e}", "red")

f_crypto = ctk.CTkFrame(content, fg_color="transparent")
title(f_crypto, "Crypto Prices", "Live cryptocurrency prices via CoinGecko")
crypto_top_row = ctk.CTkFrame(f_crypto, fg_color="transparent")
crypto_top_row.pack(fill="x", pady=(0, 8))
crypto_search_var = ctk.StringVar()
crypto_search = ctk.CTkEntry(crypto_top_row, placeholder_text="Search coin  e.g. bitcoin, solana...",
                              textvariable=crypto_search_var,
                              fg_color=C["card2"], border_color=C["border"], text_color=C["text"],
                              placeholder_text_color=C["text_muted"],
                              font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=6, border_width=1)
crypto_search.pack(side="left", expand=True, fill="x")
mk_btn(crypto_top_row, "  Search", width=100,
       command=lambda: threading.Thread(target=do_crypto_search, daemon=True).start()).pack(side="left", padx=(8,0))
mk_btn(crypto_top_row, "  Fetch All", width=110,
       command=lambda: threading.Thread(target=do_crypto, daemon=True).start()).pack(side="left", padx=(8,0))
out_crypto = outbox(f_crypto)
DEFAULT_COINS = ["bitcoin","ethereum","solana","dogecoin","cardano","ripple","litecoin","polkadot","monero"]

def do_crypto():
    clear(out_crypto); write(out_crypto, "  Fetching live prices...\n", "dim")
    try:
        ids  = ",".join(DEFAULT_COINS)
        data = json.loads(urllib.request.urlopen(
            f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd,gbp", timeout=8).read())
        clear(out_crypto)
        write(out_crypto, f"  {'Coin':<16}  {'USD':>12}  {'GBP':>12}", "dim")
        write(out_crypto, "  " + "─" * 46, "dim")
        for coin in DEFAULT_COINS:
            if coin in data:
                usd = f"${data[coin].get('usd', 0):,.2f}"
                gbp = f"£{data[coin].get('gbp', 0):,.2f}"
                write(out_crypto, f"  {coin.capitalize():<16}  {usd:>12}  {gbp:>12}", "green")
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
                usd = f"${data[cid].get('usd', 0):,.4f}"
                gbp = f"£{data[cid].get('gbp', 0):,.4f}"
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
            write(out_conv, f"\n  Rate  :  1 {frm} = {rate} {to}", "dim")
        else:
            write(out_conv, f"  Currency not found: {to}", "red")
    except Exception as e: write(out_conv, f"  Error: {e}", "red")

f_texttools = ctk.CTkFrame(content, fg_color="transparent")
title(f_texttools, "Text Tools", "Transform, analyse, and manipulate text")
ctk.CTkLabel(f_texttools, text="Input:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
text_in = ctk.CTkTextbox(f_texttools, height=100, fg_color=C["card"], border_width=1,
                           border_color=C["border"], text_color=C["text"],
                           font=ctk.CTkFont(family=FONT_MONO, size=11), corner_radius=8)
text_in.pack(fill="x", pady=(2, 8))
btn_row = irow(f_texttools)
for lbl, fn in [("UPPER", str.upper), ("lower", str.lower), ("Title", str.title),
                ("Reverse", lambda t: t[::-1])]:
    mk_btn(btn_row, lbl, width=90, command=lambda f=fn: do_text(f)).pack(side="left", padx=2)
btn_row2 = irow(f_texttools)
mk_btn(btn_row2, "Word Count",  width=110, command=lambda: do_wordcount()).pack(side="left", padx=2)
mk_btn(btn_row2, "No Spaces",   width=100, command=lambda: do_text(lambda t: t.replace(" ",""))).pack(side="left", padx=2)
mk_btn(btn_row2, "Strip Lines", width=100, command=lambda: do_text(lambda t: "\n".join(l.strip() for l in t.splitlines()))).pack(side="left", padx=2)
out_text = outbox(f_texttools, height=180)

def do_text(fn):
    t = text_in.get("1.0","end").strip(); clear(out_text); write(out_text, fn(t), "green")

def do_wordcount():
    t = text_in.get("1.0","end").strip(); clear(out_text)
    write(out_text, f"  Characters  :  {len(t)}")
    write(out_text, f"  Words       :  {len(t.split())}")
    write(out_text, f"  Lines       :  {len(t.splitlines())}")

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
mk_btn(r_qr, "Copy URL", width=100, muted=True, command=lambda: [do_qr()]).pack(side="left", padx=(8,0))
out_qr = outbox(f_qr, height=100)

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
       command=lambda: [open(NOTES_FILE,"w").write(notes_box.get("1.0","end")), None]).pack(side="left")
mk_btn(r_notes, "Clear", width=80, muted=True,
       command=lambda: notes_box.delete("1.0","end")).pack(side="left", padx=(8,0))

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
    t = raw.replace("https://","").replace("http://","").split("/")[0].strip()
    if not t: write(out_soc, "  Enter a domain.", "yellow"); return
    clear(out_soc)
    write(out_soc, f"  Resolving {t}...\n", "dim")
    try:
        results = socket.getaddrinfo(t, None)
        ips = list(dict.fromkeys(r[4][0] for r in results))
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
        flags = re.IGNORECASE if regex_flags.get() else 0
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
        ts = int(raw)
        dt_utc   = datetime.datetime.utcfromtimestamp(ts)
        dt_local = datetime.datetime.fromtimestamp(ts)
        write(out_ts, f"  Unix Timestamp  :  {ts}", "dim")
        write(out_ts, f"  UTC             :  {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC", "green")
        write(out_ts, f"  Local           :  {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
        write(out_ts, f"  ISO 8601        :  {dt_utc.isoformat()}Z", "cyan")
        write(out_ts, f"  Readable        :  {dt_utc.strftime('%A, %d %B %Y at %H:%M UTC')}")
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
out_color = outbox(f_color, height=180)

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hsl(r, g, b):
    r, g, b = r/255, g/255, b/255
    mx, mn = max(r,g,b), min(r,g,b)
    l = (mx+mn)/2
    if mx == mn: h = s = 0
    else:
        d = mx - mn
        s = d / (2 - mx - mn) if l > 0.5 else d / (mx + mn)
        if mx == r:   h = (g - b) / d + (6 if g < b else 0)
        elif mx == g: h = (b - r) / d + 2
        else:         h = (r - g) / d + 4
        h /= 6
    return round(h*360), round(s*100), round(l*100)

def do_color_convert():
    raw = color_hex.get().strip(); clear(out_color)
    try:
        r, g, b = hex_to_rgb(raw)
        h, s, l = rgb_to_hsl(r, g, b)
        hex_clean = raw if raw.startswith("#") else f"#{raw}"
        color_preview.configure(fg_color=hex_clean)
        write(out_color, f"  HEX   :  {hex_clean.upper()}", "cyan")
        write(out_color, f"  RGB   :  rgb({r}, {g}, {b})", "green")
        write(out_color, f"  HSL   :  hsl({h}, {s}%, {l}%)", "yellow")
        write(out_color, f"\n  Red   :  {r}  ({r/255*100:.1f}%)", "red")
        write(out_color, f"  Green :  {g}  ({g/255*100:.1f}%)", "green")
        write(out_color, f"  Blue  :  {b}  ({b/255*100:.1f}%)", "blue")
    except Exception as e:
        write(out_color, f"  Error: {e}", "red")

def do_color_pick():
    chosen = colorchooser.askcolor(title="Pick a colour")
    if chosen and chosen[1]:
        hex_val = chosen[1]
        color_hex.delete(0, "end")
        color_hex.insert(0, hex_val)
        do_color_convert()

f_units = ctk.CTkFrame(content, fg_color="transparent")
title(f_units, "Unit Converter", "Convert length, weight, temperature, and data size")
unit_val = lentry(f_units, "Value", "100")
ctk.CTkLabel(f_units, text="Category:", anchor="w",
             font=ctk.CTkFont(family=FONT_UI, size=11), text_color=C["text_dim"]).pack(fill="x")
unit_cat_var = ctk.StringVar(value="Length")
unit_cat = ctk.CTkOptionMenu(f_units, variable=unit_cat_var,
                              values=["Length","Weight","Temperature","Data Size","Speed"],
                              fg_color=C["card2"], button_color=C["green_dark"],
                              button_hover_color=C["green"], text_color=C["text"],
                              font=ctk.CTkFont(family=FONT_UI, size=11))
unit_cat.pack(anchor="w", pady=(2,8))
mk_btn(f_units, "  Convert All", width=140, command=lambda: do_units()).pack(anchor="w")
out_units = outbox(f_units, height=240)

UNIT_TABLES = {
    "Length": {"metres":1.0,"kilometres":0.001,"centimetres":100.0,"millimetres":1000.0,
               "miles":0.000621371,"yards":1.09361,"feet":3.28084,"inches":39.3701,"nautical mi":0.000539957},
    "Weight": {"kilograms":1.0,"grams":1000.0,"milligrams":1000000.0,"tonnes":0.001,
               "pounds":2.20462,"ounces":35.274,"stones":0.157473},
    "Data Size": {"bytes":1.0,"kilobytes":1/1024,"megabytes":1/1048576,"gigabytes":1/1073741824,
                  "terabytes":1/1099511627776,"bits":8.0},
    "Speed": {"m/s":1.0,"km/h":3.6,"mph":2.23694,"knots":1.94384,"ft/s":3.28084},
}

def do_units():
    clear(out_units)
    try: val = float(unit_val.get().strip())
    except: write(out_units, "  Enter a valid number.", "red"); return
    cat = unit_cat_var.get()
    if cat == "Temperature":
        c = val
        write(out_units, f"  Input   :  {val}°C\n", "dim")
        write(out_units, f"  Celsius     :  {c:.4f} °C", "green")
        write(out_units, f"  Fahrenheit  :  {c * 9/5 + 32:.4f} °F", "yellow")
        write(out_units, f"  Kelvin      :  {c + 273.15:.4f} K", "cyan")
        return
    table = UNIT_TABLES.get(cat, {})
    base_key = list(table.keys())[0]
    write(out_units, f"  Input  :  {val} {base_key}\n", "dim")
    for unit, rate in table.items():
        write(out_units, f"  {unit:<14}  :  {val * rate:.6g}", "green" if unit == base_key else "")

f_numtools = ctk.CTkFrame(content, fg_color="transparent")
title(f_numtools, "Number Tools", "Convert numbers between bases")
num_in = lentry(f_numtools, "Decimal number", "255")
r_num = irow(f_numtools)
for lbl, fn in [("→ Binary", lambda n: bin(int(n))),
                ("→ Hex",    lambda n: hex(int(n))),
                ("→ Octal",  lambda n: oct(int(n)))]:
    mk_btn(r_num, lbl, width=110, command=lambda f=fn: do_num(f)).pack(side="left", padx=2)
out_num = outbox(f_numtools)

def do_num(fn):
    t = num_in.get().strip(); clear(out_num)
    try: write(out_num, f"  {fn(t)}", "green")
    except Exception as e: write(out_num, f"  Error: {e}", "red")

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
for t in ["dark","light","system"]:
    ctk.CTkRadioButton(tr, text=t.capitalize(), variable=theme_var, value=t,
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
    x = app.winfo_x() + (app.winfo_width() // 2) - 180
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

make_section("OSINT",        ["IP Lookup","Email Headers","WHOIS","Reverse DNS","SSL Checker","Subnet Calc"],
             [f_ip, f_email, f_whois, f_rdns, f_ssl, f_subnet])
make_section("Port Scanner", ["Scan Ports"], [f_ps])
make_section("Network",      ["Ping","Traceroute","DNS Lookup","My IP","Netstat"],
             [f_ping, f_trace, f_dns, f_myip, f_netstat])
make_section("Discord",      ["Send Message","Embed Sender","Webhook","DM Sender",
                               "Bot Info","Channel Info","Delete Message",
                               "Server Info","Role Lister","Message Fetcher","Bot Builder"],
             [f_disc_send, f_disc_embed, f_disc_webhook, f_disc_dm,
              f_disc_info, f_disc_channel, f_disc_delete,
              f_disc_server, f_disc_roles, f_disc_fetch, f_disc_builder])
make_section("Passwords",    ["Generator","Hash Generator","Strength Checker"],
             [f_passgen, f_hasher, f_passcheck])
make_section("Encoding",     ["Base64","URL Encode","Hex Converter","Caesar / ROT13","JWT Decoder","Morse Code"],
             [f_b64, f_url_enc, f_hex_enc, f_caesar, f_jwt, f_morse])
make_section("System Info",  ["System Info","Processes","Disk Info"],
             [f_sysinfo, f_procs, f_disk])
make_section("Web Tools",    ["HTTP Headers","Site Status","Bulk IP Lookup"],
             [f_http, f_sitestatus, f_bulkip])
make_section("File Tools",   ["File Hash","File Info"], [f_filehash, f_fileinfo])
make_section("Crypto",       ["Crypto Prices","Currency Converter"], [f_crypto, f_convert])
make_section("Text Tools",   ["Text Transformer"], [f_texttools])
make_section("QR Code",      ["QR Generator"], [f_qr])
make_section("Social Media", ["Platform IP Lookup","Username Checker"], [f_social_ip, f_username])
make_section("Dev Tools",    ["JSON Formatter","Regex Tester","Diff Checker","Timestamp Converter"],
             [f_json_fmt, f_regex, f_diff, f_timestamp])
make_section("Generators",   ["UUID Generator","Colour Converter","Lorem Ipsum"],
             [f_uuid, f_color, f_lorem])
make_section("Converters",   ["Unit Converter","Number Converter"], [f_units, f_numtools])

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
