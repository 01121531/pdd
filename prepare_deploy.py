import argparse
import shutil
from pathlib import Path

from app_config import BASE_DIR, APP_CONFIG, discover_playwright_chromium


BUNDLED_BROWSER_DIR = BASE_DIR / 'browsers' / 'chromium' / 'chrome-win64'
BUNDLED_BROWSER_EXE = BUNDLED_BROWSER_DIR / 'chrome.exe'
BUNDLED_EXTENSION_DIR = BASE_DIR / 'extensions' / 'fuduo_3_1_27'
LEGACY_EXTENSION_DIR = BASE_DIR / '富多插件3.1.27'


def copy_tree(source: Path, target: Path, overwrite: bool) -> None:
    if source.resolve() == target.resolve():
        print(f'来源已是目标目录，跳过：{target}')
        return
    if target.exists() and overwrite:
        shutil.rmtree(target)
    if target.exists():
        print(f'已存在，跳过：{target}')
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f'正在复制：{source} -> {target}')
    shutil.copytree(source, target)


def resolve_browser_source(explicit: str) -> Path:
    if explicit:
        source = Path(explicit).expanduser()
        if source.is_file():
            return source.parent
        return source
    if BUNDLED_BROWSER_EXE.exists():
        return BUNDLED_BROWSER_DIR
    if APP_CONFIG.browser_path and APP_CONFIG.browser_path.exists() and APP_CONFIG.browser_path != BUNDLED_BROWSER_EXE:
        return APP_CONFIG.browser_path.parent
    discovered = discover_playwright_chromium()
    if discovered:
        return discovered.parent
    raise FileNotFoundError('未找到可复制的 Chromium。请用 --browser-source 指定 chrome.exe 或 chrome-win64 目录。')


def resolve_extension_source(explicit: str) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    if BUNDLED_EXTENSION_DIR.exists():
        return BUNDLED_EXTENSION_DIR
    if APP_CONFIG.extension_dir.exists():
        return APP_CONFIG.extension_dir
    if LEGACY_EXTENSION_DIR.exists():
        return LEGACY_EXTENSION_DIR
    raise FileNotFoundError('未找到扩展目录。请用 --extension-source 指定扩展目录。')


def ensure_example_config() -> None:
    example = BASE_DIR / 'app_config.example.json'
    if example.exists():
        return
    example.write_text(
        '{\n'
        '  "browser_path": "browsers/chromium/chrome-win64/chrome.exe",\n'
        '  "extension_dir": "extensions/fuduo_3_1_27",\n'
        '  "data_dir": "data",\n'
        '  "user_data_dir": "data/chrome_user_data",\n'
        '  "cookie_file": "data/pdd_cookies.json",\n'
        '  "runs_dir": "data/runs",\n'
        '  "uploads_dir": "data/uploads",\n'
        '  "state_file": "data/web_state.json"\n'
        '}\n',
        encoding='utf-8',
    )


def main() -> None:
    parser = argparse.ArgumentParser(description='准备跨电脑部署所需的浏览器和扩展文件')
    parser.add_argument('--browser-source', default='', help='chrome.exe 或 chrome-win64 目录')
    parser.add_argument('--extension-source', default='', help='富多扩展目录')
    parser.add_argument('--overwrite', action='store_true', help='覆盖已存在的 browsers/extensions 目标目录')
    args = parser.parse_args()

    browser_source = resolve_browser_source(args.browser_source)
    extension_source = resolve_extension_source(args.extension_source)

    copy_tree(browser_source, BUNDLED_BROWSER_DIR, args.overwrite)
    copy_tree(extension_source, BUNDLED_EXTENSION_DIR, args.overwrite)
    ensure_example_config()

    print('部署文件准备完成。')
    print(f'浏览器：{BUNDLED_BROWSER_EXE}')
    print(f'扩展：{BUNDLED_EXTENSION_DIR}')
    print('注意：data/、Cookie、profile、runs、uploads 不会被复制，属于每台电脑自己的私有数据。')


if __name__ == '__main__':
    main()
