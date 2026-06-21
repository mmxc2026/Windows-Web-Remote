<div align="center">

# Windows Web Remote

**用手机浏览器远程查看和控制 Windows 电脑**

无需安装手机 App · 支持局域网与临时 HTTPS 外网连接

**简体中文** · [English](README_EN.md)

[快速开始](#快速开始) · [功能](#功能) · [使用指南](docs/USAGE.md) · [故障排查](docs/TROUBLESHOOTING.md) · [安全说明](SECURITY.md)

</div>

> [!WARNING]
> 本项目可以控制电脑的鼠标、键盘、摄像头、麦克风和文件。仅限在自己的电脑和可信设备上使用，切勿公开包含 `token` 的完整控制网址。

## 功能

| 类别 | 支持能力 |
| --- | --- |
| 屏幕 | 实时预览、全屏显示、触摸定位 |
| 鼠标 | 移动、单击、双击、拖拽、长按右键、双指滚动 |
| 键盘 | 快捷键、中文文字输入、Windows 屏幕键盘 |
| 电脑音频 | 系统声音和默认麦克风传到手机 |
| 手机音频 | 按住说话、持续实时对讲 |
| 摄像头 | 查看电脑默认摄像头 |
| 文件 | 手机上传文件、手机下载共享文件 |
| 网络 | 局域网模式、Cloudflare Quick Tunnel 临时外网模式 |
| 安全 | 每次启动生成新的随机访问密钥 |

## 下载后直接使用

1. 在 GitHub 仓库页面点击 **Code → Download ZIP**。
2. 完整解压 ZIP，不要在压缩包预览窗口中直接运行。
3. 根据需要双击：
   - `start-local.bat`：手机和电脑位于同一 Wi-Fi。
   - `start-internet.bat`：手机通过移动网络或其他 Wi-Fi 连接。
4. 用手机打开启动窗口显示的完整网址。

首次运行需要联网下载约 100 MB 的便携 Python 和媒体依赖。所有运行环境都保存在项目目录中，不会修改系统 Python。

## 快速开始

### 局域网模式

1. 电脑和手机连接同一 Wi-Fi。
2. 双击 `start-local.bat`。
3. Windows 防火墙询问时，仅允许**专用网络**。
4. 手机打开窗口显示的 `http://...` 完整地址。

### 外网模式

1. 双击 `start-internet.bat`。
2. 首次运行会自动准备便携 Python、项目依赖和 Cloudflare Tunnel。
3. 手机打开窗口显示的 `https://...` 完整地址。
4. 保持启动窗口开启；关闭窗口后临时公网地址立即失效。

## 系统要求

- 64 位 Windows 10 或 Windows 11
- 现代手机浏览器，如 Chrome、Edge 或 Safari
- 首次运行时可访问 Python、PyPA、GitHub 和 Cloudflare 的网络环境
- 使用声音和摄像头时，Windows 需允许桌面应用访问相应设备

## 文件传输

| 方向 | 操作 | 保存位置 |
| --- | --- | --- |
| 手机 → 电脑 | 手机页面点击“上传到电脑” | `received_files/` |
| 电脑 → 手机 | 把文件放入共享目录，手机点击“刷新下载” | `shared_files/` |

这两个目录中的实际文件默认被 `.gitignore` 排除，不会误传到 GitHub。

## 文档

| 文档 | 内容 |
| --- | --- |
| [使用指南](docs/USAGE.md) | 触摸、全屏、文字、音频、摄像头和文件传输 |
| [故障排查](docs/TROUBLESHOOTING.md) | 启动、网络、声音、摄像头和输入问题 |
| [架构说明](docs/ARCHITECTURE.md) | 服务端、手机端和外网隧道结构 |
| [API 文档](docs/API.md) | 内部 HTTP API 和输入消息格式 |
| [安全说明](SECURITY.md) | 风险边界和安全使用建议 |
| [更新日志](CHANGELOG.md) | 版本功能记录 |

## 项目结构

```text
windows-web-remote/
├─ server.py
├─ requirements.txt
├─ start-local.bat
├─ start-internet.bat
├─ scripts/
│  └─ start.ps1
├─ web/
│  └─ index.html
├─ docs/
├─ received_files/
└─ shared_files/
```

## 安全与限制

- 完整网址中的 `token` 等同于临时控制密码，请勿截图、转发或公开。
- 外网模式依赖第三方 Cloudflare Quick Tunnel，仅建议个人临时使用。
- 无法控制 Windows 登录、UAC 安全桌面或模拟 `Ctrl+Alt+Delete`。
- 默认无法控制权限级别高于本程序的管理员应用。
- 摄像头、声音和大文件传输会消耗电脑上行带宽。
- 本项目没有账号系统、多因素认证、设备审批或生产级审计功能。

## 开发

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py --token development-token
```

然后打开：

```text
http://127.0.0.1:8765/?token=development-token
```

## 卸载

关闭服务后删除整个项目文件夹即可。若要保留手机上传的文件，请先备份 `received_files/`。

## 许可证

本仓库尚未选择开源许可证。公开发布前请根据授权意愿添加许可证；未添加许可证时默认保留所有权利。
