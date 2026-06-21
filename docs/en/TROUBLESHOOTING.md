# Troubleshooting

[简体中文](../TROUBLESHOOTING.md) · **English**

## The window closes immediately

Fully extract the GitHub ZIP before running it. Check `startup-error.log`. If portable Python was only partially downloaded, delete `tools/python/` and retry.

## The phone cannot open the URL

- LAN: use the same Wi-Fi and allow Private networks in Windows Firewall.
- Internet: keep the startup window open and use the new complete HTTPS URL.
- Never omit the `?token=...` part.

## Mouse works but text does not

Click the target input on the PC, open **Text Input**, then send. To control an elevated app, the server must run at the same privilege level.

## Audio or microphone fails

Allow desktop microphone access in Windows Privacy settings, select default input/output devices, close apps using exclusive audio mode, and restart the service.

## Camera fails

Allow desktop camera access and close other apps that may own the camera. The default camera (device 0) is used.

## Phone microphone fails

Use the HTTPS Internet URL and grant microphone permission in the browser.

## Tunnel timeout

Verify access to GitHub and Cloudflare. Corporate, school, or public networks may block tunnels.

## Reset

Stop the service, delete `.venv/` and `tools/`, then start again. Back up `received_files/` first.
