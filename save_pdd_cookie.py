import argparse
import contextlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

from DrissionPage import ChromiumOptions, ChromiumPage

from app_config import APP_CONFIG

BASE_DIR = APP_CONFIG.base_dir
EXTENSION_DIR = APP_CONFIG.extension_dir
USER_DATA_DIR = APP_CONFIG.user_data_dir
DEBUG_PORT: int | None = None
BROWSER_PATH: Path | None = APP_CONFIG.browser_path
LOGIN_URL = 'https://mms.pinduoduo.com/login/'
SUCCESS_URL = 'https://mms.pinduoduo.com/home'
OUTPUT_FILE = APP_CONFIG.cookie_file
POLL_INTERVAL = 2
TIMEOUT = 300


class CallbackWriter:
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.buffer = ''

    def write(self, text: str) -> int:
        if not text:
            return 0
        self.buffer += text
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self.callback(line)
        return len(text)

    def flush(self) -> None:
        if self.buffer:
            self.callback(self.buffer)
            self.buffer = ''


def build_page(
    user_data_dir: Path = USER_DATA_DIR,
    debug_port: int | None = None,
    browser_path: Path | None = None,
) -> ChromiumPage:
    config_errors = list(APP_CONFIG.errors)
    if config_errors and browser_path == APP_CONFIG.browser_path and EXTENSION_DIR == APP_CONFIG.extension_dir:
        raise RuntimeError('；'.join(config_errors))
    if not EXTENSION_DIR.exists():
        raise FileNotFoundError(f'未找到扩展目录：{EXTENSION_DIR}')
    if browser_path and not browser_path.exists():
        raise FileNotFoundError(f'未找到浏览器程序：{browser_path}')

    options = ChromiumOptions()
    if browser_path:
        options.set_browser_path(str(browser_path))
    options.set_user_data_path(str(user_data_dir))
    if debug_port:
        options.set_local_port(debug_port)
    options.set_argument('--remote-allow-origins', '*')
    options.add_extension(str(EXTENSION_DIR))
    options.headless(False)
    return ChromiumPage(addr_or_opts=options)


def is_login_success(page: ChromiumPage) -> bool:
    current_url = page.url or ''
    parsed_url = urlparse(current_url)
    normalized_path = parsed_url.path.rstrip('/')
    return normalized_path == '/home'


def save_cookies(page: ChromiumPage, output_file: Path) -> None:
    cookies = page.cookies(all_info=True) or []
    cookie_dict = {
        cookie['name']: cookie['value']
        for cookie in cookies
        if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie
    }

    payload = {
        'saved_at': datetime.now().isoformat(timespec='seconds'),
        'login_url': LOGIN_URL,
        'success_url': SUCCESS_URL,
        'current_url': page.url,
        'cookie_dict': cookie_dict,
        'cookies': cookies,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def _run_login(
    output_file: Path = OUTPUT_FILE,
    user_data_dir: Path = USER_DATA_DIR,
    timeout: int = TIMEOUT,
    debug_port: int | None = None,
    browser_path: Path | None = None,
) -> None:
    page = build_page(user_data_dir=user_data_dir, debug_port=debug_port, browser_path=browser_path)

    try:
        print(f'正在使用固定用户目录启动浏览器：{user_data_dir}')
        print(f'浏览器程序：{browser_path.resolve() if browser_path else "系统默认 Chrome"}')
        print(f'正在加载扩展目录：{EXTENSION_DIR}')
        print(f'调试端口：{debug_port or "DrissionPage 默认"}')
        print(f'Chrome 扩展启动参数：--load-extension={EXTENSION_DIR.resolve()}，--remote-allow-origins=*')
        print(f'正在打开登录页：{LOGIN_URL}')
        page.get(LOGIN_URL)
        print(f'请在浏览器中扫码登录，只有跳转到 {SUCCESS_URL} 才会保存 Cookie...')

        start = time.time()
        while time.time() - start < timeout:
            if is_login_success(page):
                save_cookies(page, output_file)
                print(f'登录成功，Cookie 已保存到：{output_file.resolve()}')
                return
            time.sleep(POLL_INTERVAL)

        print('等待扫码登录超时，未检测到跳转到 /home，未保存 Cookie。')
    finally:
        page.quit()
        print('浏览器已关闭。')


def run_login(
    output_file: Path = OUTPUT_FILE,
    user_data_dir: Path = USER_DATA_DIR,
    timeout: int = TIMEOUT,
    debug_port: int | None = None,
    browser_path: Path | None = None,
    log_callback: Callable[[str], None] | None = None,
) -> None:
    if log_callback is None:
        _run_login(
            output_file=output_file,
            user_data_dir=user_data_dir,
            timeout=timeout,
            debug_port=debug_port,
            browser_path=browser_path,
        )
        return

    writer = CallbackWriter(log_callback)
    with contextlib.redirect_stdout(writer), contextlib.redirect_stderr(writer):
        try:
            _run_login(
                output_file=output_file,
                user_data_dir=user_data_dir,
                timeout=timeout,
                debug_port=debug_port,
                browser_path=browser_path,
            )
        finally:
            writer.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description='扫码登录并保存拼多多 Cookie')
    parser.add_argument('--output', default=str(OUTPUT_FILE), help='Cookie 输出文件')
    parser.add_argument('--user-data-dir', default=str(USER_DATA_DIR), help='Chrome 用户目录')
    parser.add_argument('--timeout', type=int, default=TIMEOUT, help='等待扫码登录的秒数')
    parser.add_argument('--debug-port', type=int, default=None, help='Chrome 调试端口')
    parser.add_argument('--browser-path', default='', help='浏览器程序路径')
    args = parser.parse_args()
    run_login(
        output_file=Path(args.output),
        user_data_dir=Path(args.user_data_dir),
        timeout=max(1, args.timeout),
        debug_port=args.debug_port,
        browser_path=Path(args.browser_path) if args.browser_path else None,
    )


if __name__ == '__main__':
    main()
