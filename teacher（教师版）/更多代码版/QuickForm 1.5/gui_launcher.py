import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import sys
import os
from pathlib import Path
import webbrowser
import time
import socket
import sqlite3
from werkzeug.security import generate_password_hash

class QuickFormLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("QuickForm 启动器")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 应用状态
        self.process = None
        self.is_running = False
    
    def get_local_ip(self):
        """获取本机局域网IP地址"""
        try:
            # 创建一个UDP连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # 连接到Google DNS服务器
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # 如果获取失败，返回localhost
            return "127.0.0.1"
        
    def setup_styles(self):
        """设置界面样式"""
        self.root.configure(bg='#f0f0f0')
        
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_frame = tk.Frame(self.root, bg='#f0f0f0')
        title_frame.pack(pady=10)
        
        title_label = tk.Label(
            title_frame, 
            text="🚀 QuickForm 启动器", 
            font=('Microsoft YaHei', 16, 'bold'),
            bg='#f0f0f0',
            fg='#333'
        )
        title_label.pack()
        
        # 版权信息
        copyright_frame = tk.Frame(self.root, bg='#f0f0f0')
        copyright_frame.pack()
        
        copyright_text = tk.Label(
            copyright_frame,
            text='QuickForm是一个由温州科技高级中学和温州大学联合开发的表单服务信息系统',
            font=('Microsoft YaHei', 8),
            bg='#f0f0f0',
            fg='#888'
        )
        copyright_text.pack()
        
        link_text = tk.Label(
            copyright_frame,
            text='https://gitee.com/wstlab/quickform',
            font=('Microsoft YaHei', 8),
            bg='#f0f0f0',
            fg='#007bff',
            cursor='hand2'
        )
        link_text.pack()
        
        # 绑定链接点击事件
        link_text.bind("<Button-1>", lambda e: webbrowser.open("https://gitee.com/wstlab/quickform"))
        
        # 控制按钮区域
        control_frame = tk.Frame(self.root, bg='#f0f0f0')
        control_frame.pack(pady=10)
        
        self.start_btn = tk.Button(
            control_frame,
            text="启动服务",
            command=self.start_service,
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#28a745',
            fg='white',
            padx=20,
            pady=5,
            state='normal'
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            control_frame,
            text="停止服务",
            command=self.stop_service,
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#dc3545',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_btn = tk.Button(
            control_frame,
            text="打开应用",
            command=self.open_app,
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#007bff',
            fg='white',
            padx=20,
            pady=5,
            state='disabled'
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        # 重置密码按钮
        self.reset_pass_btn = tk.Button(
            control_frame,
            text="重置密码",
            command=self.reset_password,
            font=('Microsoft YaHei', 10, 'bold'),
            bg='#ffc107',
            fg='#212529',
            padx=20,
            pady=5
        )
        self.reset_pass_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        self.status_label = tk.Label(
            self.root,
            text="服务状态: 未运行",
            font=('Microsoft YaHei', 10),
            bg='#f0f0f0',
            fg='#666'
        )
        self.status_label.pack(pady=5)
        
        # 服务器信息
        info_frame = tk.LabelFrame(self.root, text="服务器信息", font=('Microsoft YaHei', 10, 'bold'))
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # 动态获取本机IP地址
        local_ip = self.get_local_ip()
        
        # 创建URL标签
        local_url_frame = tk.Frame(info_frame)
        local_url_frame.pack(fill=tk.X, padx=10, pady=2)
        
        local_label = tk.Label(
            local_url_frame,
            text="本地访问: ",
            font=('Microsoft YaHei', 9),
            justify=tk.LEFT
        )
        local_label.pack(side=tk.LEFT)
        
        local_url = tk.Label(
            local_url_frame,
            text="http://127.0.0.1:5001",
            font=('Microsoft YaHei', 9, 'underline'),
            fg='#007bff',
            cursor='hand2',
            justify=tk.LEFT
        )
        local_url.pack(side=tk.LEFT)
        local_url.bind("<Button-1>", lambda e: webbrowser.open("http://127.0.0.1:5001"))
        
        lan_url_frame = tk.Frame(info_frame)
        lan_url_frame.pack(fill=tk.X, padx=10, pady=2)
        
        lan_label = tk.Label(
            lan_url_frame,
            text="局域网访问: ",
            font=('Microsoft YaHei', 9),
            justify=tk.LEFT
        )
        lan_label.pack(side=tk.LEFT)
        
        lan_url = tk.Label(
            lan_url_frame,
            text=f"http://{local_ip}:5001",
            font=('Microsoft YaHei', 9, 'underline'),
            fg='#007bff',
            cursor='hand2',
            justify=tk.LEFT
        )
        lan_url.pack(side=tk.LEFT)
        lan_url.bind("<Button-1>", lambda e: webbrowser.open(f"http://{local_ip}:5001"))
        
        # 终端输出区域
        output_frame = tk.LabelFrame(self.root, text="服务输出", font=('Microsoft YaHei', 10, 'bold'))
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 9),
            state='disabled'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def log_message(self, message):
        """向输出区域添加消息"""
        self.output_text.config(state='normal')
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')
        self.root.update_idletasks()
    
    def start_service(self):
        """启动QuickForm服务"""
        if self.is_running:
            return
            
        try:
            self.log_message("正在启动 QuickForm 服务...")
            self.log_message("当前工作目录: " + os.getcwd())
            
            # 更新状态
            self.is_running = True
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.status_label.config(text="服务状态: 启动中...")
            
            # 启动Flask应用
            self.process = subprocess.Popen(
                [sys.executable, 'app.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # 启动线程读取输出
            self.read_thread = threading.Thread(target=self.read_output)
            self.read_thread.daemon = True
            self.read_thread.start()
            
            # 稍后更新状态
            self.root.after(2000, self.confirm_service_running)
            
        except Exception as e:
            self.log_message(f"启动失败: {str(e)}")
            self.is_running = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.status_label.config(text="服务状态: 启动失败")
    
    def confirm_service_running(self):
        """确认服务已运行"""
        if self.is_running:
            self.status_label.config(text="服务状态: 运行中 - 端口 5001")
            self.open_btn.config(state='normal')
            self.log_message("✅ 服务启动成功! 访问地址: http://127.0.0.1:5001")
    
    def read_output(self):
        """读取子进程输出"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_message(line.rstrip())
        except:
            pass
    
    def stop_service(self):
        """停止QuickForm服务"""
        if not self.is_running or not self.process:
            return
            
        try:
            self.log_message("正在停止 QuickForm 服务...")
            
            # 终止进程
            self.process.terminate()
            try:
                self.process.wait(timeout=5)  # 等待最多5秒
            except subprocess.TimeoutExpired:
                self.process.kill()  # 强制终止
            
            self.is_running = False
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            self.open_btn.config(state='disabled')
            self.status_label.config(text="服务状态: 已停止")
            self.log_message("✅ 服务已停止")
            
        except Exception as e:
            self.log_message(f"停止服务时出错: {str(e)}")
    
    def open_app(self):
        """打开应用网页"""
        # 提供选项让用户选择打开本地地址还是局域网地址
        local_ip = self.get_local_ip()
        choice = messagebox.askquestion("选择访问地址", 
                                      f"选择要打开的地址:\n\n"
                                      f"1. 本地访问 (127.0.0.1)\n"
                                      f"2. 局域网访问 ({local_ip})\n\n"
                                      f"点击'是'打开本地地址，点击'否'打开局域网地址")
        
        if choice == 'yes':
            webbrowser.open("http://127.0.0.1:5001")
        else:
            webbrowser.open(f"http://{local_ip}:5001")
    
    def reset_password(self):
        """重置管理员密码"""
        # 询问用户是否确认重置密码
        if not messagebox.askyesno("确认重置", "您确定要重置管理员密码吗？\n这将把wst用户的密码重置为'quickform'，并清除所有AI配置中的API密钥。"):
            return
            
        try:
            # 获取数据库路径
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quickform.db')
            
            # 连接到SQLite数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            self.log_message("正在清理数据库中的API密钥信息...")
            
            # 清除ai_config中的api信息
            try:
                cursor.execute("UPDATE ai_config SET deepseek_api_key = NULL, doubao_api_key = NULL, doubao_secret_key = NULL, qwen_api_key = NULL, glm_api_key = NULL, siliconflow_api_key = NULL")
                self.log_message("✅ 已清除所有AI配置中的API密钥信息")
            except sqlite3.Error as e:
                self.log_message(f"⚠️ 清除AI配置信息时出错: {e}")
            
            # 将管理员"wst"的密码改为"quickform"
            self.log_message("正在重置管理员密码...")
            try:
                # 生成密码哈希
                hashed_password = generate_password_hash('quickform')
                
                # 更新管理员密码
                cursor.execute(
                    "UPDATE user SET password = ? WHERE username = ?",
                    (hashed_password, 'wst')
                )
                
                if cursor.rowcount > 0:
                    self.log_message("✅ 管理员密码重置成功！")
                else:
                    self.log_message("⚠️ 未找到管理员用户'wst'")
            except sqlite3.Error as e:
                self.log_message(f"❌ 重置管理员密码时出错: {e}")
                messagebox.showerror("错误", f"密码重置失败:\n{e}")
                conn.close()
                return
            
            # 提交更改
            conn.commit()
            conn.close()
            
            self.log_message("✅ 数据库重置完成！")
            self.log_message("管理员账号: wst")
            self.log_message("新密码: quickform")
            messagebox.showinfo("成功", "管理员密码已重置为默认值！\n\n账号: wst\n密码: quickform\n\n注意：AI配置中的API密钥已被清除。")
            
        except Exception as e:
            self.log_message(f"❌ 密码重置失败: {str(e)}")
            messagebox.showerror("错误", f"密码重置失败:\n{str(e)}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.is_running:
            if messagebox.askokcancel("退出", "服务正在运行，确定要退出吗？"):
                self.stop_service()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    root = tk.Tk()
    app = QuickFormLauncher(root)
    root.mainloop()

if __name__ == "__main__":
    main()