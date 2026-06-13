import os
import hashlib
import socket
import ipaddress
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _get_fernet():
    from cryptography.fernet import Fernet
    from .config import ENCRYPTION_KEY
    return Fernet(ENCRYPTION_KEY)


def encrypt_value(plaintext):
    if not plaintext:
        return plaintext
    try:
        return _get_fernet().encrypt(plaintext.encode('utf-8')).decode('utf-8')
    except Exception as e:
        logger.error(f"加密失败: {e}")
        return plaintext


def decrypt_value(ciphertext):
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        return ciphertext


_PRIVATE_PREFIXES = (
    '10.', '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.',
    '172.24.', '172.25.', '172.26.', '172.27.',
    '172.28.', '172.29.', '172.30.', '172.31.',
    '192.168.', '169.254.', '127.', '0.',
)


def validate_url_safe(url, allow_private=False):
    """检查 URL 是否安全，防止 SSRF 攻击。"""
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError(f"无效的 URL: {url}")

    if parsed.scheme not in ('http', 'https'):
        raise ValueError(f"不允许的协议: {parsed.scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL 缺少主机名")

    if not allow_private:
        try:
            for result in socket.getaddrinfo(hostname, None):
                ip_str = result[4][0]
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                    raise ValueError(f"不允许访问内部网络地址: {hostname} -> {ip_str}")
        except socket.gaierror:
            raise ValueError(f"无法解析主机名: {hostname}")

    return True
