<div align="center">

# Windows Web Remote

**View and control a Windows PC from a phone browser**

No mobile app required · Local network and temporary HTTPS access

[简体中文](README.md) · **English**

[Quick Start](#quick-start) · [Features](#features) · [User Guide](docs/en/USAGE.md) · [Troubleshooting](docs/en/TROUBLESHOOTING.md) · [Security](SECURITY_EN.md)

</div>

> [!WARNING]
> This project can control the mouse, keyboard, camera, microphone, and files on a PC. Use it only on computers and devices you own and trust. Never publish a complete control URL containing its `token`.

## Features

| Category | Capabilities |
| --- | --- |
| Display | Live preview, fullscreen mode, direct touch positioning |
| Mouse | Move, click, double-click, drag, long-press right-click, two-finger scroll |
| Keyboard | Shortcuts, Unicode text input, Windows On-Screen Keyboard |
| PC audio | Stream system output and the default microphone to the phone |
| Phone audio | Push-to-talk and continuous talk to the PC |
| Camera | View the PC's default camera |
| Files | Upload from the phone and download shared PC files |
| Network | LAN mode and temporary Cloudflare Quick Tunnel mode |
| Access | A new random access token on every start |

## Use After Download

1. On GitHub, select **Code → Download ZIP**.
2. Fully extract the ZIP. Do not run it inside the archive preview.
3. Double-click `start-local.bat` for the same Wi-Fi, or `start-internet.bat` for another network.
4. Open the complete URL shown in the startup window on the phone.

The first run downloads about 100 MB of portable Python and media dependencies. Everything stays inside the project directory.

## Quick Start

### Local Network

1. Connect the PC and phone to the same Wi-Fi.
2. Double-click `start-local.bat`.
3. Allow **Private networks** only if Windows Firewall asks.
4. Open the complete `http://...` URL shown in the window.

### Internet

1. Double-click `start-internet.bat`.
2. The first run prepares portable Python, dependencies, and Cloudflare Tunnel.
3. Open the complete `https://...` URL shown in the window.
4. Keep the startup window open; closing it invalidates the temporary URL.

## Requirements

- 64-bit Windows 10 or Windows 11
- A modern phone browser such as Chrome, Edge, or Safari
- First-run access to Python, PyPA, GitHub, and Cloudflare
- Windows permission for desktop apps to use the microphone or camera

## File Transfer

| Direction | Action | Location |
| --- | --- | --- |
| Phone → PC | Select “Upload to PC” | `received_files/` |
| PC → Phone | Place a file in the shared directory and refresh | `shared_files/` |

Runtime files in these directories are excluded by `.gitignore`.

## Documentation

| Document | Description |
| --- | --- |
| [User Guide](docs/en/USAGE.md) | Touch, fullscreen, text, audio, camera, and files |
| [Troubleshooting](docs/en/TROUBLESHOOTING.md) | Startup, network, audio, camera, and input issues |
| [Architecture](docs/en/ARCHITECTURE.md) | Server, browser client, and tunnel design |
| [API](docs/en/API.md) | Internal HTTP endpoints and input messages |
| [Security](SECURITY_EN.md) | Threat boundaries and safe-use guidance |
| [Changelog](CHANGELOG.md) | Release history |

## Project Layout

```text
windows-web-remote/
├─ server.py
├─ requirements.txt
├─ start-local.bat
├─ start-internet.bat
├─ scripts/start.ps1
├─ web/index.html
├─ docs/
├─ received_files/
└─ shared_files/
```

## Security and Limitations

- The token in the complete URL acts as a temporary control password.
- Internet mode depends on Cloudflare Quick Tunnel and is intended for temporary personal use.
- Windows sign-in, the UAC secure desktop, and `Ctrl+Alt+Delete` cannot be controlled.
- Elevated applications normally cannot be controlled by a non-elevated server.
- Camera, audio, and large transfers consume PC upload bandwidth.
- There are no accounts, MFA, device approval, or production-grade audit logs.

## Development

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py --token development-token
```

Open `http://127.0.0.1:8765/?token=development-token`.

## Uninstall

Stop the service and delete the project directory. Back up `received_files/` first if needed.

## License

No open-source license has been selected. Without a license, all rights are reserved by default.
