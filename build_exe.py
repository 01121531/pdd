import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DIST_DIR = PROJECT_DIR / 'dist' / 'PDDConsole'


def copy_user_docs() -> None:
    for filename in ['README.md', 'DEPLOY.md', 'app_config.example.json', 'requirements.txt']:
        source = PROJECT_DIR / filename
        if source.exists():
            shutil.copy2(source, DIST_DIR / filename)


def main() -> None:
    subprocess.run(
        [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'PDDConsole.spec'],
        cwd=PROJECT_DIR,
        check=True,
    )
    copy_user_docs()
    print('打包完成。')
    print(f'发布目录：{DIST_DIR}')
    print(f'启动程序：{DIST_DIR / "PDDConsole.exe"}')
    print('把整个 PDDConsole 文件夹复制到其他电脑，双击 PDDConsole.exe 即可启动。')


if __name__ == '__main__':
    main()
