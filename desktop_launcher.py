import socket
import sys
import threading
import time
import webbrowser


DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex((host, port)) != 0


def choose_port(host: str = DEFAULT_HOST, preferred: int = DEFAULT_PORT) -> int:
    for port in range(preferred, preferred + 20):
        if port_available(host, port):
            return port
    raise RuntimeError('未找到可用端口，请关闭占用 8000-8019 的程序后重试。')


def open_browser_later(url: str) -> None:
    def open_when_ready() -> None:
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_when_ready, daemon=True).start()


def run_worker(argv: list[str]) -> int:
    if len(argv) < 3:
        print('缺少 worker 类型：open 或 login')
        return 2
    worker = argv[2]
    worker_args = argv[3:]
    if worker == 'open':
        import open_pdd_goods

        sys.argv = ['open_pdd_goods.py', *worker_args]
        open_pdd_goods.main()
        return 0
    if worker == 'login':
        import save_pdd_cookie

        sys.argv = ['save_pdd_cookie.py', *worker_args]
        save_pdd_cookie.main()
        return 0
    print(f'未知 worker 类型：{worker}')
    return 2


def parse_port(argv: list[str]) -> int:
    if '--port' not in argv:
        return DEFAULT_PORT
    index = argv.index('--port')
    try:
        return int(argv[index + 1])
    except (IndexError, ValueError):
        raise RuntimeError('--port 后面需要跟一个端口号。')


def run_server(argv: list[str]) -> None:
    import uvicorn

    from app_config import APP_CONFIG
    from web_app import app

    APP_CONFIG.ensure_data_dirs()
    preferred_port = parse_port(argv)
    port = choose_port(preferred=preferred_port)
    url = f'http://{DEFAULT_HOST}:{port}'
    print('拼多多本机自动化控制台正在启动...')
    print(f'浏览器：{APP_CONFIG.browser_path or "未找到"}')
    print(f'扩展：{APP_CONFIG.extension_dir}')
    print(f'数据目录：{APP_CONFIG.data_dir}')
    print(f'控制台地址：{url}')
    print('关闭此窗口即可停止本机控制台。')
    if '--no-browser' not in argv:
        open_browser_later(url)
    uvicorn.run(app, host=DEFAULT_HOST, port=port, reload=False)


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == '--worker':
        return run_worker(sys.argv)
    run_server(sys.argv[1:])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
