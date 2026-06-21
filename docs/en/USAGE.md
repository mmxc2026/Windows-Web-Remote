# User Guide

[简体中文](../USAGE.md) · **English**

## First Run

Double-click `start-local.bat` or `start-internet.bat`. The launcher finds Python, downloads a private portable runtime when necessary, installs dependencies, and prints the phone URL. First-run downloads are approximately 100 MB.

If startup fails, inspect `startup-error.log`.

## Touch Controls

| Gesture | Action |
| --- | --- |
| Tap | Left click |
| Double tap | Double click |
| Hold and move | Left-button drag |
| Long press | Right click |
| One-finger touchpad move | Move pointer |
| Two-finger touchpad move | Scroll |

## Fullscreen and Text

- Select **Fullscreen** to show only the PC display.
- Select **Text Input**, type in the visible phone field, then select **Send**.
- Select **PC Keyboard** to open Windows On-Screen Keyboard through `Win+R → osk`.
- Click the target PC input field before sending text.

## Audio and Camera

- **PC Sound** streams the current Windows output.
- **PC Microphone** streams the default PC microphone.
- **PC Camera** opens the default camera until the camera view is closed.
- **Push to Talk** sends the phone microphone only while held.
- **Live Talk** continuously sends the phone microphone until disabled.

Use headphones for two-way audio to prevent feedback.

## Files

- Phone uploads are saved to `received_files/`; the per-file limit is 512 MB.
- Put PC files in `shared_files/`, then refresh the phone download list.

## Stop

Close the startup window or press `Ctrl+C`. A temporary public URL becomes invalid immediately.
