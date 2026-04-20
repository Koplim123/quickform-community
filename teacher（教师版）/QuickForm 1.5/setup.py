import sys
from cx_Freeze import setup, Executable

# 依赖项排除列表（可选，用于减小文件大小）
build_exe_options = {
    "packages": ["os", "tkinter", "subprocess", "threading", "time", "webbrowser", "socket"],
    "excludes": ["unittest", "tkinter.test", "email", "http", "urllib", "xml", "pydoc"]
}

# GUI应用程序的基本设置
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # 不显示控制台窗口

shortcut_table = [
    ("DesktopShortcut",  # Shortcut
     "DesktopFolder",  # Directory
     "QuickForm Launcher",  # Name
     "TARGETDIR",  # Component
     "[TARGETDIR]gui_launcher.exe",  # Target
     None,  # Arguments
     None,  # Description
     None,  # Hotkey
     None,  # Icon
     None,  # IconIndex
     None,  # ShowCmd
     "TARGETDIR"  # WkDir
     )
]

msi_data = {"Shortcut": shortcut_table}

bdist_msi_options = {'data': msi_data}

executables = [
    Executable(
        "gui_launcher.py",
        base=base,
        target_name="QuickForm_Launcher.exe",
        icon=None  # 可以添加图标文件路径
    )
]

setup(
    name="QuickForm Launcher",
    version="1.3",
    description="QuickForm可视化启动器",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables
)