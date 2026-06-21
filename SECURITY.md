# Security Policy

## 适用场景

Windows Web Remote 设计用于用户本人设备之间的临时远程控制。请勿将其部署为公开服务、多人共享服务或无人值守的生产级远控平台。

## 重要风险

- 完整控制网址包含随机 token。任何获得该网址的人都可能控制电脑并访问媒体或共享文件。
- Quick Tunnel 地址经过第三方 Cloudflare 网络转发。
- 本项目没有账号系统、多因素认证、设备审批、权限分级或审计日志。
- 手机上传的文件可能包含恶意内容；程序只负责保存，不负责扫描。

## 安全使用建议

1. 不要截图、转发或公开完整控制网址。
2. 使用结束后立即关闭服务。
3. 局域网模式只允许 Windows 防火墙“专用网络”。
4. 不要在公共 Wi-Fi 中使用局域网模式。
5. `shared_files/` 中只放置准备公开给手机的文件。
6. 不要以管理员身份运行，除非确实需要控制管理员应用。
7. 定期更新 Python 依赖和 Cloudflare Tunnel。

## 敏感文件

`.gitignore` 默认排除：

- `.venv/`
- `tools/cloudflared.exe`
- `received_files/` 和 `shared_files/` 中的实际文件
- `startup-error.log`
- Python 缓存和本地工具元数据

提交前仍应执行 `git status`，确认没有个人文件、访问地址或日志。

## 报告安全问题

公开发布后，请在此处补充私密安全联系方式。不要在公开 Issue 中披露仍可利用的控制地址或 token。
