import subprocess
import sys
import os
import importlib.util
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

def check_and_install_packages():
    """检查并安装所需的包"""
    required_packages = [
        'flask',
        'flask-login', 
        'flask-sqlalchemy',
        'flask-bcrypt',
        'sqlalchemy',
        'bcrypt',
        'python-dotenv',
        'pandas',
        'matplotlib',
        'requests'
    ]
    
    # 检查每个包是否已安装
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'flask-login':
                importlib.util.find_spec('flask_login')
            elif package == 'flask-sqlalchemy':
                importlib.util.find_spec('flask_sqlalchemy')
            elif package == 'flask-bcrypt':
                importlib.util.find_spec('flask_bcrypt')
            elif package == 'python-dotenv':
                importlib.util.find_spec('dotenv')
            else:
                importlib.util.find_spec(package.replace('-', '_'))
        except (ImportError, AttributeError, ValueError):
            missing_packages.append(package)
    
    if missing_packages:
        return missing_packages
    return []

def install_package(package):
    """安装指定的Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def create_installer_gui():
    """创建安装程序GUI"""
    root = tk.Tk()
    root.title("QuickForm 一键部署安装程序")
    root.geometry("500x300")
    root.resizable(False, False)
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 标题
    title_label = ttk.Label(main_frame, text="QuickForm 一键部署安装程序", font=("微软雅黑", 14, "bold"))
    title_label.pack(pady=10)
    
    # 说明文本
    desc_label = ttk.Label(main_frame, text="此工具将自动检查并安装所需依赖库，然后启动 QuickForm", font=("微软雅黑", 10))
    desc_label.pack(pady=10)
    
    # 进度条
    progress = ttk.Progressbar(main_frame, mode='determinate')
    progress.pack(fill=tk.X, pady=10, padx=20)
    
    # 状态标签
    status_label = ttk.Label(main_frame, text="准备开始...", font=("微软雅黑", 9))
    status_label.pack(pady=10)
    
    # 详细信息标签
    detail_label = ttk.Label(main_frame, text="", font=("微软雅黑", 8), foreground="gray")
    detail_label.pack(pady=5)
    
    def install_process():
        try:
            # 检查缺失的包
            missing_packages = check_and_install_packages()
            
            if missing_packages:
                total_packages = len(missing_packages)
                status_label.config(text=f"发现 {total_packages} 个缺失的包")
                detail_label.config(text="正在安装依赖库...")
                
                # 更新进度条
                progress['maximum'] = total_packages
                
                # 安装缺失的包
                for i, package in enumerate(missing_packages):
                    status_label.config(text=f"正在安装 {package} ({i+1}/{total_packages})...")
                    progress['value'] = i + 1
                    detail_label.config(text=f"安装进度: {int((i+1)/total_packages*100)}%")
                    root.update()
                    
                    if not install_package(package):
                        messagebox.showerror("错误", f"无法安装包: {package}\n请检查网络连接后重试")
                        root.destroy()
                        return
                    time.sleep(0.1)  # 给用户一点反馈时间
                
                status_label.config(text="所有依赖库安装完成!")
                detail_label.config(text="正在启动 QuickForm...")
                root.update()
            else:
                status_label.config(text="所有依赖库已就绪!")
                detail_label.config(text="正在启动 QuickForm...")
                root.update()
            
            # 稍微延迟一下让用户看到状态
            time.sleep(1)
            
            # 启动GUI启动器
            try:
                subprocess.Popen([sys.executable, "gui_launcher.py"])
                status_label.config(text="启动器已成功启动!")
                detail_label.config(text="您现在可以关闭此窗口")
                root.update()
                
                # 3秒后自动关闭
                root.after(3000, root.destroy)
            except Exception as e:
                messagebox.showerror("错误", f"启动GUI时出错: {str(e)}")
                root.destroy()
                
        except Exception as e:
            messagebox.showerror("错误", f"安装过程中出现错误: {str(e)}")
            root.destroy()
    
    # 启动安装过程
    install_thread = threading.Thread(target=install_process)
    install_thread.daemon = True
    install_thread.start()
    
    return root

def main():
    # 检查Python版本
    if sys.version_info < (3, 6):
        messagebox.showerror("错误", "需要Python 3.6或更高版本")
        return
    
    # 创建并启动GUI
    root = create_installer_gui()
    root.mainloop()

if __name__ == "__main__":
    main()