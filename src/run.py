import os
import socket
from quickform import create_app

app = create_app()

if __name__ == '__main__':
    # 修复socket.getfqdn()的UnicodeDecodeError问题
    original_getfqdn = socket.getfqdn

    def safe_getfqdn(name=''):
        try:
            return original_getfqdn(name)
        except UnicodeDecodeError:
            return name if name else 'localhost'

    socket.getfqdn = safe_getfqdn

    # 启动应用
    app.run(debug=True, host='0.0.0.0', port=5001)
