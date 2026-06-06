import os
import socket
from quickform import create_app

app = create_app()

if __name__ == '__main__':

    #ASCII编码问题 最好不要用中文做主机名
    #用中文名会返回localhost 但是这样的话治标不治本 可能会导致Redis那种分布式的部署出现问题
    
    original_getfqdn = socket.getfqdn

    def safe_getfqdn(name=''):
        try:
            return original_getfqdn(name)
        except UnicodeDecodeError:
            return name if name else 'localhost'
            print(f"Warning: Unable to decode hostname '{name}', using fallback 'localhost'")

    socket.getfqdn = safe_getfqdn



    #修改默认配置文件请到src/quickform/config.py中修改
    from quickform.config import DEBUG, HOST, PORT
    app.run(debug=DEBUG, host=HOST, port=PORT)
