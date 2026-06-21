# API

**简体中文** · [English](en/API.md)

所有控制 API 均要求访问 token。GET 请求可使用查询参数 `token`，POST 请求使用 `X-Control-Token` 请求头。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/status` | 状态和屏幕尺寸 |
| GET | `/api/screen.jpg` | 当前屏幕 JPEG |
| POST | `/api/input` | 鼠标、键盘、文字和屏幕键盘 |
| GET | `/api/camera.jpg` | 默认摄像头 JPEG |
| POST | `/api/camera/stop` | 停止摄像头 |
| GET | `/api/audio.wav` | 系统声音或麦克风 WAV |
| POST | `/api/phone-mic` | 手机 PCM 音频块 |
| POST | `/api/phone-mic/stop` | 清空手机音频播放队列 |
| GET | `/api/files` | 共享文件列表 |
| GET | `/api/files/download` | 下载共享文件 |
| POST | `/api/files/upload` | 上传文件到电脑 |

## 输入示例

```json
{"type":"move","dx":12,"dy":-4}
{"type":"absolute","x":0.5,"y":0.5}
{"type":"click","button":"left"}
{"type":"scroll","amount":-1}
{"type":"key","keys":["ctrl","c"]}
{"type":"text","text":"你好 Windows"}
{"type":"open_keyboard"}
```

## 注意

此 API 仅供项目自带页面使用，未承诺稳定兼容。不要把 token 写入源码或提交到 GitHub。
