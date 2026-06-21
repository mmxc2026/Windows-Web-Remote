# API

[简体中文](../API.md) · **English**

All control endpoints require a token. GET requests accept `token` in the query string; POST requests use the `X-Control-Token` header.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/status` | Status and screen dimensions |
| GET | `/api/screen.jpg` | Current screen JPEG |
| POST | `/api/input` | Mouse, keyboard, text, and OSK |
| GET | `/api/camera.jpg` | Default camera JPEG |
| POST | `/api/camera/stop` | Stop camera capture |
| GET | `/api/audio.wav` | System or microphone WAV |
| POST | `/api/phone-mic` | Phone PCM audio block |
| POST | `/api/phone-mic/stop` | Clear phone audio queue |
| GET | `/api/files` | Shared file list |
| GET | `/api/files/download` | Download shared file |
| POST | `/api/files/upload` | Upload file to PC |

```json
{"type":"move","dx":12,"dy":-4}
{"type":"absolute","x":0.5,"y":0.5}
{"type":"click","button":"left"}
{"type":"key","keys":["ctrl","c"]}
{"type":"text","text":"Hello Windows"}
{"type":"open_keyboard"}
```

This internal API is not guaranteed to remain backward compatible.
