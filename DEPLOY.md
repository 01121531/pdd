# 部署教程

这份教程用于把项目部署到一台新的 Windows 电脑。默认方式是直接使用仓库里的随包 Chromium 和扩展目录，避免系统 Chrome 版本变化导致扩展无法加载。

## 1. 环境准备

需要安装：

- Python 3.10 或更高版本
- Git
- Git LFS

安装后打开 PowerShell，确认命令可用：

```powershell
python --version
git --version
git lfs version
```

如果 `git lfs version` 不存在，先安装 Git LFS，然后执行：

```powershell
git lfs install
```

## 2. 克隆项目

```powershell
git clone https://github.com/01121531/pdd.git
cd pdd
git lfs pull
```

`git lfs pull` 会拉取随包 Chromium 的大文件。如果跳过这一步，`browsers/chromium/chrome-win64/chrome.exe` 可能只是一个很小的 LFS 指针文件，浏览器无法启动。

## 免安装 EXE 部署

如果已经拿到打包后的 `PDDConsole` 文件夹，不需要安装 Python，也不需要执行 `pip install`。

使用方式：

1. 把整个 `PDDConsole` 文件夹复制到目标电脑。
2. 双击 `PDDConsole.exe`。
3. 程序会自动打开 `http://127.0.0.1:8000` 或附近可用端口。
4. 首次使用点击“刷新登录”扫码。

注意：不要只复制 `PDDConsole.exe` 单个文件。随包 Chromium、扩展和 Python 运行库都在同一个发布文件夹内，必须一起带走。

如果需要自己重新打包，在源码目录执行：

```powershell
pip install -r requirements.txt
python build_exe.py
```

生成目录：

```text
dist/PDDConsole/
```

## 3. 安装 Python 依赖

建议使用虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如果 PowerShell 阻止激活脚本，可在当前窗口执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. 检查浏览器和扩展

默认路径如下：

- 浏览器：`browsers/chromium/chrome-win64/chrome.exe`
- 扩展：`extensions/fuduo_3_1_27`
- 本机私有数据：`data/`

如果浏览器或扩展目录缺失，可以从当前机器的可用目录复制：

```powershell
python prepare_deploy.py
```

也可以手动指定来源：

```powershell
python prepare_deploy.py --browser-source "C:\path\to\chrome-win64" --extension-source "C:\path\to\fuduo_3_1_27"
```

## 5. 可选配置

默认不需要创建 `app_config.json`。如果要改路径，复制示例文件：

```powershell
Copy-Item app_config.example.json app_config.json
```

可配置项：

```json
{
  "browser_path": "browsers/chromium/chrome-win64/chrome.exe",
  "extension_dir": "extensions/fuduo_3_1_27",
  "data_dir": "data",
  "user_data_dir": "data/chrome_user_data",
  "cookie_file": "data/pdd_cookies.json",
  "runs_dir": "data/runs",
  "uploads_dir": "data/uploads",
  "state_file": "data/web_state.json"
}
```

环境变量也可以覆盖配置：

- `PDD_CONFIG_FILE`
- `PDD_BROWSER_PATH`
- `PDD_EXTENSION_DIR`
- `PDD_DATA_DIR`

注意：不建议使用新版系统 Chrome 作为 `browser_path`，因为新版官方 Chrome 可能阻止命令行加载未打包扩展。优先使用仓库随包 Chromium。

## 6. 启动网站

```powershell
python web_app.py
```

访问：

```text
http://127.0.0.1:8000
```

网站只监听 `127.0.0.1`，默认不暴露到局域网。

## 7. 首次登录

首次部署的新电脑不会带 Cookie，也不会带旧浏览器 profile。

操作步骤：

1. 打开控制台首页。
2. 查看“部署环境”区域，确认浏览器和扩展存在。
3. 点击“刷新登录”。
4. 在弹出的专用 Chromium 中扫码登录拼多多后台。
5. 登录成功后会生成 `data/pdd_cookies.json`。

`data/` 是本机私有目录，不要提交到 Git，也不要发给别人。

## 8. 启动任务

1. 上传 Excel。
2. 上传两张替换图片，或选择页面中保留的历史上传文件。
3. 填写原文、新文、限量金额、每组条数、审核超时等参数。
4. 点击启动任务。
5. 在任务历史中查看状态、日志和结果导出。

日志会写入：

```text
data/runs/<job_id>/run.log
```

刷新页面后，历史日志仍可查看。

## 9. 结果和导出

每次任务都会生成独立目录：

```text
data/runs/<job_id>/
```

常见文件：

- `inputs/`：本次上传的 Excel 和图片
- `run.log`：运行日志
- `review_results.json`：审核结果
- `restore_results.json`：恢复结果
- `config.json`：本次任务配置

页面提供导出按钮，可导出不通过商品、成功商品或全部结果。

## 10. 更新部署

以后更新代码：

```powershell
git pull
git lfs pull
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python web_app.py
```

更新不会覆盖 `data/` 里的 Cookie、profile、上传历史和任务记录。

## 11. 常见问题

### 浏览器无法启动

先确认文件存在：

```powershell
Test-Path browsers/chromium/chrome-win64/chrome.exe
```

如果返回 `False`，执行：

```powershell
git lfs pull
```

### 页面提示扩展目录不存在

确认：

```powershell
Test-Path extensions/fuduo_3_1_27/manifest.json
```

如果缺失，从可用机器复制扩展目录，或执行 `python prepare_deploy.py --extension-source "<扩展目录>"`。

### 商品页面一直提示插件入口未加载

优先检查首页“部署环境”：

- 浏览器路径是否为随包 Chromium。
- 扩展路径是否存在。
- 是否误用了新版系统 Chrome。

然后重新点击“刷新登录”，让程序用新的 `data/chrome_user_data` 生成专用 profile。

### Git LFS 拉取失败

确认 Git LFS 已安装：

```powershell
git lfs install
git lfs pull
```

如果网络环境无法拉取 LFS 文件，可以在一台可用电脑运行 `python prepare_deploy.py`，然后把 `browsers/` 和 `extensions/` 目录复制到目标电脑。

### 端口被占用

默认端口是 `8000`。如果被占用，可以临时用 Python 启动自定义端口：

```powershell
python -c "import uvicorn; uvicorn.run('web_app:app', host='127.0.0.1', port=8001)"
```

然后访问：

```text
http://127.0.0.1:8001
```

## 12. 不要分发的文件

这些文件和目录属于每台电脑自己的私有数据，已经被 `.gitignore` 排除：

- `data/`
- `chrome_user_data/`
- `pdd_cookies.json`
- `runs/`
- `uploads/`
- `web_state.json`
- `app_config.json`
- Excel 和图片输入文件

打包给其他电脑时，只分发代码、`browsers/`、`extensions/`、`app_config.example.json` 和说明文档。
