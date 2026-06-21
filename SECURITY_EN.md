# Security Policy

[简体中文](SECURITY.md) · **English**

Windows Web Remote is designed for temporary control between devices owned by the same user. It is not a public, multi-user, or unattended production remote-access service.

## Risks

- Anyone with the complete tokenized URL may control the PC and access enabled media or shared files.
- Quick Tunnel traffic is relayed through Cloudflare.
- There are no accounts, MFA, device approval, permission roles, or audit logs.
- Uploaded files are saved but not scanned.

## Safe Use

1. Never publish or forward the complete control URL.
2. Stop the service immediately after use.
3. Allow Private networks only for LAN mode.
4. Avoid LAN mode on public Wi-Fi.
5. Share only intentional files through `shared_files/`.
6. Avoid administrator mode unless it is required.
7. Review `git status` before every public push.

## Excluded Sensitive Files

`.gitignore` excludes runtime environments, Cloudflared, uploaded/shared files, logs, Python caches, and local tool metadata.

Before publishing, add a private security contact. Do not disclose active control URLs or tokens in public issues.
