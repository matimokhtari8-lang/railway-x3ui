"""
ساخت لینک vless:// از روی UUID کلاینت و تنظیمات اینباند.
چون در سناریوی شما فقط یک اینباند (VLESS + WS + TLS، پشت nginx روی
پورت ۴۴۳) از قبل وجود داره، این ماژول ساده نگه داشته شده. اگر بعدا
پروتکل/ترنسپورت دیگه‌ای اضافه کردید، این تابع رو گسترش بدید.
"""
from urllib.parse import quote
import config


def build_vless_link(client_uuid: str, remark: str) -> str:
    host = config.SNI_HOST or config.PANEL_URL.replace("https://", "").replace("http://", "")
    path = config.WS_PATH if config.WS_PATH.startswith("/") else f"/{config.WS_PATH}"

    params = (
        f"encryption=none"
        f"&security=tls"
        f"&sni={host}"
        f"&fp=chrome"
        f"&type=ws"
        f"&host={host}"
        f"&path={quote(path, safe='')}"
    )
    return f"vless://{client_uuid}@{host}:443?{params}#{quote(remark, safe='')}"
