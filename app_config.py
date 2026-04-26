import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def is_frozen_app() -> bool:
    return bool(getattr(sys, 'frozen', False))


def app_dir() -> Path:
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    return Path(getattr(sys, '_MEIPASS', app_dir())).resolve()


BASE_DIR = app_dir()
RESOURCE_DIR = resource_dir()


def resolve_path(value: str | Path, base_dir: Path = BASE_DIR, fallback_base: Path | None = None) -> Path:
    path = Path(os.path.expandvars(str(value))).expanduser()
    if path.is_absolute():
        return path
    resolved = base_dir / path
    if fallback_base:
        fallback = fallback_base / path
        if not resolved.exists() and fallback.exists():
            return fallback
    return resolved


def resolve_resource_path(value: str | Path) -> Path:
    return resolve_path(value, base_dir=BASE_DIR, fallback_base=RESOURCE_DIR)


def config_file_path() -> Path:
    override = os.environ.get('PDD_CONFIG_FILE')
    return resolve_path(override) if override else BASE_DIR / 'app_config.json'


def read_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def discover_playwright_chromium() -> Path | None:
    roots = [
        Path(os.environ.get('LOCALAPPDATA', '')) / 'ms-playwright',
        Path.home() / 'AppData' / 'Local' / 'ms-playwright',
    ]
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(root.glob('chromium-*/chrome-win*/chrome.exe'))

    def version_key(path: Path) -> int:
        parent = next((part for part in path.parts if part.startswith('chromium-')), 'chromium-0')
        try:
            return int(parent.split('-', 1)[1])
        except (IndexError, ValueError):
            return 0

    candidates = [path for path in candidates if path.exists()]
    return sorted(candidates, key=version_key, reverse=True)[0] if candidates else None


def browser_version(browser_path: Path | None) -> str:
    if not browser_path or not browser_path.exists():
        return ''
    manifest_versions = sorted(browser_path.parent.glob('*.manifest'), reverse=True)
    for manifest in manifest_versions:
        if re.match(r'^\d+\.\d+\.\d+\.\d+\.manifest$', manifest.name):
            return 'Chromium ' + manifest.stem
    directory_versions = sorted(
        [path.name for path in browser_path.parent.iterdir() if path.is_dir() and re.match(r'^\d+\.\d+\.\d+\.\d+$', path.name)],
        reverse=True,
    )
    if directory_versions:
        normalized = str(browser_path).lower().replace('/', '\\')
        product = 'Google Chrome' if '\\google\\chrome\\application\\chrome.exe' in normalized else 'Chromium'
        return f'{product} {directory_versions[0]}'
    try:
        completed = subprocess.run(
            [str(browser_path), '--version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ''
    version = (completed.stdout or completed.stderr or '').strip()
    return version.replace('\ufffd', '').strip()


def browser_major(version_text: str) -> int | None:
    match = re.search(r'(\d+)\.', version_text)
    return int(match.group(1)) if match else None


def is_unsupported_system_chrome(browser_path: Path | None, version_text: str) -> bool:
    if not browser_path:
        return False
    normalized = str(browser_path).lower().replace('/', '\\')
    major = browser_major(version_text)
    if major is None or major < 137:
        return False
    if 'chrome for testing' in version_text.lower():
        return False
    is_google_chrome = (
        version_text.lower().startswith('google chrome')
        or '\\google\\chrome\\application\\chrome.exe' in normalized
    )
    return is_google_chrome


@dataclass(slots=True)
class AppConfig:
    base_dir: Path
    resource_dir: Path
    config_file: Path
    browser_path: Path | None
    extension_dir: Path
    data_dir: Path
    user_data_dir: Path
    cookie_file: Path
    runs_dir: Path
    uploads_dir: Path
    state_file: Path
    sources: dict[str, str] = field(default_factory=dict)
    browser_version: str = ''
    browser_supported: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    legacy_cookie_file: Path = BASE_DIR / 'pdd_cookies.json'
    legacy_user_data_dir: Path = BASE_DIR / 'chrome_user_data'
    legacy_state_file: Path = BASE_DIR / 'web_state.json'
    legacy_uploads_dir: Path = BASE_DIR / 'uploads'

    def ensure_data_dirs(self) -> None:
        for path in [self.data_dir, self.user_data_dir, self.runs_dir, self.uploads_dir, self.state_file.parent]:
            path.mkdir(parents=True, exist_ok=True)


def load_app_config() -> AppConfig:
    cfg_file = config_file_path()
    raw = read_json_file(cfg_file)
    sources: dict[str, str] = {}

    env_data_dir = os.environ.get('PDD_DATA_DIR')
    if env_data_dir:
        data_dir = resolve_path(env_data_dir)
        sources['data_dir'] = 'env:PDD_DATA_DIR'
    elif raw.get('data_dir'):
        data_dir = resolve_path(raw['data_dir'])
        sources['data_dir'] = str(cfg_file)
    else:
        data_dir = BASE_DIR / 'data'
        sources['data_dir'] = 'default'

    def data_child(key: str, default_name: str) -> Path:
        if raw.get(key):
            sources[key] = str(cfg_file)
            return resolve_path(raw[key])
        sources[key] = 'data_dir'
        return data_dir / default_name

    env_extension = os.environ.get('PDD_EXTENSION_DIR')
    if env_extension:
        extension_dir = resolve_resource_path(env_extension)
        sources['extension_dir'] = 'env:PDD_EXTENSION_DIR'
    elif raw.get('extension_dir'):
        extension_dir = resolve_resource_path(raw['extension_dir'])
        sources['extension_dir'] = str(cfg_file)
    else:
        extension_dir = RESOURCE_DIR / 'extensions' / 'fuduo_3_1_27'
        sources['extension_dir'] = 'default'

    env_browser = os.environ.get('PDD_BROWSER_PATH')
    bundled_browser = RESOURCE_DIR / 'browsers' / 'chromium' / 'chrome-win64' / 'chrome.exe'
    browser_path: Path | None
    if env_browser:
        browser_path = resolve_resource_path(env_browser)
        sources['browser_path'] = 'env:PDD_BROWSER_PATH'
    elif raw.get('browser_path'):
        browser_path = resolve_resource_path(raw['browser_path'])
        sources['browser_path'] = str(cfg_file)
    elif bundled_browser.exists():
        browser_path = bundled_browser
        sources['browser_path'] = 'default:bundled'
    else:
        browser_path = discover_playwright_chromium()
        sources['browser_path'] = 'fallback:playwright' if browser_path else 'missing'

    user_data_dir = data_child('user_data_dir', 'chrome_user_data')
    cookie_file = data_child('cookie_file', 'pdd_cookies.json')
    runs_dir = data_child('runs_dir', 'runs')
    uploads_dir = data_child('uploads_dir', 'uploads')
    state_file = data_child('state_file', 'web_state.json')

    version = browser_version(browser_path)
    errors: list[str] = []
    warnings: list[str] = []
    browser_supported = True

    if not browser_path:
        browser_supported = False
        errors.append('未找到可用浏览器。请运行 prepare_deploy.py 准备随包 Chromium，或设置 PDD_BROWSER_PATH。')
    elif not browser_path.exists():
        browser_supported = False
        errors.append(f'浏览器程序不存在：{browser_path}')
    elif is_unsupported_system_chrome(browser_path, version):
        browser_supported = False
        errors.append(
            f'当前浏览器是官方 Chrome {version or ""}，不支持命令行加载未打包扩展。'
            '请使用随包 Chromium 或 Chrome for Testing。'
        )
    elif sources.get('browser_path') == 'fallback:playwright':
        warnings.append('未找到随包 Chromium，当前临时使用本机 Playwright Chromium。部署到其他电脑前请运行 prepare_deploy.py。')

    if not extension_dir.exists():
        errors.append(f'扩展目录不存在：{extension_dir}')

    legacy_cookie_file = BASE_DIR / 'pdd_cookies.json'
    if legacy_cookie_file.exists() and not cookie_file.exists():
        warnings.append(f'检测到旧 Cookie 文件：{legacy_cookie_file}；新位置为：{cookie_file}。请刷新登录或手动迁移。')

    legacy_user_data_dir = BASE_DIR / 'chrome_user_data'
    if legacy_user_data_dir.exists() and not user_data_dir.exists():
        warnings.append(f'检测到旧浏览器 profile：{legacy_user_data_dir}；新位置为：{user_data_dir}。建议重新扫码登录。')

    return AppConfig(
        base_dir=BASE_DIR,
        resource_dir=RESOURCE_DIR,
        config_file=cfg_file,
        browser_path=browser_path,
        extension_dir=extension_dir,
        data_dir=data_dir,
        user_data_dir=user_data_dir,
        cookie_file=cookie_file,
        runs_dir=runs_dir,
        uploads_dir=uploads_dir,
        state_file=state_file,
        sources=sources,
        browser_version=version,
        browser_supported=browser_supported,
        errors=errors,
        warnings=warnings,
        legacy_cookie_file=legacy_cookie_file,
        legacy_user_data_dir=legacy_user_data_dir,
        legacy_state_file=BASE_DIR / 'web_state.json',
        legacy_uploads_dir=BASE_DIR / 'uploads',
    )


APP_CONFIG = load_app_config()
