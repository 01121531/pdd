# 拼多多本机自动化控制台

本项目提供一个只监听本机的 Web 控制台，用于刷新登录、上传 Excel 和图片、配置批处理参数、启动拼多多商品自动化任务、查看持久日志，并导出审核结果。

## 快速启动

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
git lfs pull
python web_app.py
```

打开：

```text
http://127.0.0.1:8000
```

首次使用请在页面点击“刷新登录”，扫码后会在本机 `data/` 目录生成 Cookie 和浏览器 profile。

## 部署教程

完整的新电脑部署、配置迁移、浏览器/扩展准备、常见问题处理见 [DEPLOY.md](DEPLOY.md)。

## 默认目录

- 浏览器：`browsers/chromium/chrome-win64/chrome.exe`
- 扩展：`extensions/fuduo_3_1_27`
- 私有数据：`data/`
- 配置示例：`app_config.example.json`

复制 `app_config.example.json` 为 `app_config.json` 后可自定义路径。相对路径一律相对项目目录解析。

## 安全说明

`data/`、Cookie、浏览器 profile、上传历史和运行结果都属于本机私有数据，已在 `.gitignore` 中排除，不应提交或打包分享。
