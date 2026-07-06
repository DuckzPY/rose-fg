# rose-fg &nbsp;·&nbsp; v7.0
> A private, offline-first toolkit for network intelligence, OSINT, Discord automation, and developer utilities — built with Python and CustomTkinter.

---

## What is rose-fg?

rose-fg is a personal desktop application that consolidates a wide range of security, networking, encoding, and developer tools into a single dark-themed GUI. It is designed to be run locally with no telemetry, no accounts, and no cloud dependency. Everything runs on your machine.

It is not intended for distribution. This is a private tool.

---

## Setup & Installation

### Requirements

- Python 3.10 or higher
- A virtual environment is strongly recommended

### 1. Clone or download the project

```
git clone https://github.com/DuckzPY/rose-fg/
cd tool
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install customtkinter pillow qrcode[pil]
```

Optional but recommended for full System Info support:

```bash
pip install psutil
```

For WHOIS lookups (if the system `whois` binary is unavailable):

```bash
pip install python-whois
```
Or run the requirements.bat file to install them automatically

### 4. Run

```bash
python rose-fg.py
```

> **Important:** Always launch via the terminal with the venv active. Running the script by double-clicking or via a shortcut will likely fail with import errors because it won't use the venv's Python.

### Font Note

rose-fg uses **JetBrains Mono** and **Inter**. If these aren't installed on your system the UI will fall back to a system default — it won't crash, but it won't look as intended. Install both fonts for the best experience.

---

## Features

### OSINT
| Tool | Description |
|------|-------------|
| IP / Domain Lookup | Geolocation, ISP, ASN, proxy/VPN/hosting flags via ip-api.com |
| Email Header Analyser | Extracts IPs, sender, reply-to, routing path from raw headers |
| WHOIS Lookup | Domain registration, registrar, expiry, nameservers |
| Reverse DNS | Resolves an IP back to its hostname |
| SSL/TLS Certificate Checker | Expiry, issuer, protocol, SANs, days remaining |
| Subnet Calculator | Network address, broadcast, mask, host range, CIDR |

### Port Scanner
| Tool | Description |
|------|-------------|
| Port Scanner | Threaded TCP scanner with speed slider, presets, live progress, stop button |

### Network
| Tool | Description |
|------|-------------|
| Ping | ICMP test with 4-packet output |
| Traceroute | Route tracing with automatic tool detection (traceroute / tracepath / mtr) |
| DNS Lookup | Resolves domain to IPs with reverse lookup |
| My Public IP | External IP + city, region, country, ISP via ipify + ip-api |
| Netstat | Lists all active network connections |

### Discord
| Tool | Description |
|------|-------------|
| Send Message | Send to any channel your bot has access to |
| Embed Sender | Rich embed with title, description, colour, footer |
| Webhook Sender | POST a message via webhook URL with optional display name |
| DM Sender | Open a DM channel and send a message to any user by ID |
| Bot Info | Retrieve bot username, ID, and full server list |
| Channel Info | Name, type, topic, NSFW flag, guild ID |
| Delete Message | Delete any message by channel + message ID |
| Server Info | Member count, boost level, verification, features, locale |
| Role Lister | All roles sorted by position with colour, ID, bot-managed flag |
| Message Fetcher | Fetch up to 100 recent messages from any channel |
| Bot Builder | Generates a ready-to-run discord.py bot script |

### Passwords
| Tool | Description |
|------|-------------|
| Password Generator | Cryptographically random, configurable length/charset, generates ×5 |
| Hash Generator | MD5, SHA1, SHA256, SHA512 |
| Strength Checker | Scores 0–6 with a visual bar and improvement tips |

### Encoding
| Tool | Description |
|------|-------------|
| Base64 | Encode / decode |
| URL Encode | Percent-encode / decode |
| Hex Converter | Text ↔ hexadecimal |
| Caesar / ROT13 | Shift cipher with configurable amount + ROT13 shortcut |
| JWT Decoder | Decode header and payload, highlight expiry, no verification required |
| Morse Code | Text ↔ Morse with standard ITU table |

### System Info
| Tool | Description |
|------|-------------|
| System Info | OS, architecture, hostname, local IP, Python runtime, env vars, psutil hardware stats |
| Processes | Full process list via tasklist (Windows) or ps aux (Unix) |
| Disk Info | Per-drive usage with colour-coded percentage warnings |

### Web Tools
| Tool | Description |
|------|-------------|
| HTTP Headers | Full response header dump for any URL |
| Site Status | Online/offline check with final URL and status code |
| Bulk IP Lookup | Geolocate a list of IPs, one per line |

### File Tools
| Tool | Description |
|------|-------------|
| File Hash | MD5, SHA1, SHA256 for any file — supports drag & drop |
| File Info | Name, size, extension, permissions, created/modified/accessed timestamps |

### Crypto
| Tool | Description |
|------|-------------|
| Crypto Prices | Live USD + GBP prices for 9 default coins via CoinGecko |
| Currency Converter | Real-time exchange rates via exchangerate-api.com |

### Text Tools
| Tool | Description |
|------|-------------|
| Text Transformer | UPPER / lower / Title / Reverse, remove spaces, strip lines, word count |

### QR Code
| Tool | Description |
|------|-------------|
| QR Generator | Inline QR rendering via qrcode library + fallback URL copied to clipboard |

### Social Media
| Tool | Description |
|------|-------------|
| Platform IP Lookup | Resolve a social media domain to IPs with geolocation |
| Username Checker | Search GitHub, Twitter/X, Instagram, TikTok, Reddit |

### Dev Tools
| Tool | Description |
|------|-------------|
| JSON Formatter | Beautify or minify JSON with validation |
| Regex Tester | Find all matches with group capture and position info |
| Diff Checker | Unified diff between two text inputs |
| Timestamp Converter | Unix ↔ human date, multiple formats, current time |

### Generators
| Tool | Description |
|------|-------------|
| UUID Generator | UUID v1 and v4, bulk batches up to 100 |
| Lorem Ipsum | Randomised placeholder paragraphs |

### Converters
| Tool | Description |
|------|-------------|
| Unit Converter | Length, weight, temperature, data size, speed |
| Number Converter | Decimal → binary, hex, octal |
| Colour Converter | HEX ↔ RGB ↔ HSL with live preview swatch and colour picker |

### Notes
Persistent scratch pad. Auto-saves every 30 seconds to `~/.rose-fg_notes.txt`. Manual save and clear buttons also available.

### Settings
- Light / dark / system theme toggle
- Window opacity slider (30–100%)
- Font size slider (9–16pt)
- Default tab on launch
- Settings persist to `~/.rose-fg_settings.json`

---

## Usage Notes

- **Sidebar navigation** — sections are collapsible. Click a section header to expand/collapse it. Active tools are highlighted in red.
- **Output boxes** — all output is colour-coded: red = success, red = error, yellow = warning, cyan = info, dim = metadata.
- **Threaded operations** — network tools run in background threads so the UI never freezes. Use the Stop button in Port Scanner to interrupt a long scan.
- **Drag & drop** — File Hash and File Info support drag and drop if tkinterdnd2 is available; otherwise use the Browse button.
- **Discord tools** — require a bot token with appropriate permissions. The bot must be in the server for most guild-level tools. DM Sender requires the bot to share a server with the target user.
- **WHOIS** — uses the system `whois` binary if available, falls back to `python-whois`, and will attempt to auto-install it via pip if neither is found.

---

## File Structure

```
tool/
├── main.py               # Entire application — single file
├── rose_logo.png         # Sidebar logo (optional — falls back to animated dot)
├── .venv/                # Virtual environment (not committed)
├── README.md             # This file
```

Settings and notes are stored in the user's home directory:

```
~/.rose-fg_settings.json
~/.rose-fg_notes.txt
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `customtkinter` | Modern themed Tkinter widgets |
| `pillow` | Image handling for logo and QR display |
| `qrcode[pil]` | QR code generation |
| `psutil` *(optional)* | CPU, RAM, and hardware stats in System Info |
| `python-whois` *(optional)* | WHOIS fallback if system binary unavailable |

All other imports (`socket`, `threading`, `urllib`, `subprocess`, `ssl`, `hashlib`, `base64`, `re`, `difflib`, `uuid`, etc.) are Python standard library.

---

## Known Limitations

- Username Checker results are based on HTTP response codes only — some platforms return 200 for non-existent accounts or block bot user agents, so results may not be perfectly accurate.
- Crypto prices and exchange rates depend on free public APIs (CoinGecko, exchangerate-api) which have rate limits.
- Traceroute on Windows uses `tracert` and may be slow or blocked by firewalls.
- Port Scanner is single-threaded per port — large ranges (e.g. 1–65535) will take a long time even at max speed.
- Drag & drop file support requires `tkinterdnd2` which is not included in the default install.

---

## Privacy

- No data is sent anywhere except by the tools that explicitly make network requests (lookups, Discord API calls, crypto prices, etc.).
- No analytics, no logging, no crash reporting.
- Settings and notes are stored locally only.
- Discord bot tokens are entered per-session and never written to disk.

---

*Private project — not for redistribution.*

*Join the discord here:*
```
https://discord.gg/9g3VtekQ5y
```
*Any questions or concerns dm:*
```
fzb3 on discord
```
or
```
du.ckz on discord
