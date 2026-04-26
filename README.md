# 拼多多本机自动化控制台

本项目提供一个本机 Web 控制台，用于刷新登录、上传 Excel 和图片、配置批处理参数、启动拼多多商品自动化任务、查看持久日志并导出审核结果。

## 启动

```powershell
python web_app.py
```

打开：

```text
http://127.0.0.1:8000
```

## 跨电脑部署

仓库默认使用随包 Chromium 和英文稳定扩展目录：

- 浏览器：`browsers/chromium/chrome-win64/chrome.exe`
- 扩展：`extensions/fuduo_3_1_27`
- 私有数据：`data/`

如果刚拉取的仓库没有浏览器文件，先运行：

```powershell
python prepare_deploy.py
```

浏览器目录使用 Git LFS 管理，克隆后如缺少大文件可执行：

```powershell
git lfs pull
```

## 配置

复制 `app_config.example.json` 为 `app_config.json` 后可自定义路径。环境变量也可覆盖：

- `PDD_CONFIG_FILE`
- `PDD_BROWSER_PATH`
- `PDD_EXTENSION_DIR`
- `PDD_DATA_DIR`

相对路径一律相对项目目录解析。

## 安全说明

`data/`、Cookie、浏览器 profile、上传历史和运行结果都属于本机私有数据，已在 `.gitignore` 中排除，不应提交或打包分享。
