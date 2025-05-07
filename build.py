import PyInstaller.__main__
import os
import shutil

def build_client():
    # 清理旧的构建文件
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
        
    # 构建Windows可执行文件
    PyInstaller.__main__.run([
        'client/main.py',
        '--onefile',
        '--name=cysteria-client',
        '--add-data=.env;.',
        '--hidden-import=cryptography',
        '--hidden-import=asyncio',
        '--hidden-import=ssl',
        '--hidden-import=dotenv',
        '--noconsole',
        '--icon=assets/icon.ico'
    ])
    
    print("Build completed. Executable is in the dist directory.")

if __name__ == "__main__":
    build_client() 