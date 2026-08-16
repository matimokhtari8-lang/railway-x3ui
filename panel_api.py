"""
یک کلاینت ساده برای API پنل 3x-ui.
فقط از عملیات‌های لازم برای ربات فروش استفاده می‌کنه: لاگین، خوندن
اینباند موجود، و افزودن کلاینت جدید به همون اینباند.
"""
import json
import time
import uuid
import requests


class PanelError(Exception):
    pass


class PanelAPI:
    def __init__(self, base_url: str, base_path: str, username: str, password: str):
        self.root = base_url.rstrip("/")
        self.base_path = base_path.strip("/")
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._logged_in = False

    def _url(self, path: str) -> str:
        return f"{self.root}/{self.base_path}/{path.lstrip('/')}"

    def login(self):
        resp = self.session.post(
            self._url("login"),
            data={"username": self.username, "password": self.password},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise PanelError(f"ورود به پنل ناموفق بود: {data.get('msg')}")
        self._logged_in = True

    def _ensure_login(self):
        if not self._logged_in:
            self.login()

    def _request(self, method: str, path: str, **kwargs):
        self._ensure_login()
        resp = self.session.request(method, self._url(path), timeout=20, **kwargs)
        # اگر سشن منقضی شده باشه پنل معمولا صفحه‌ی لاگین (HTML) برمی‌گردونه
        if resp.status_code in (401, 403) or "text/html" in resp.headers.get("content-type", ""):
            self.login()
            resp = self.session.request(method, self._url(path), timeout=20, **kwargs)
        try:
            data = resp.json()
        except ValueError:
            raise PanelError("پاسخ غیرمنتظره از پنل دریافت شد.")
        if not data.get("success", False):
            raise PanelError(data.get("msg", "خطای نامشخص از پنل"))
        return data.get("obj")

    def get_inbound(self, inbound_id: int) -> dict:
        return self._request("GET", f"api/inbounds/get/{inbound_id}")

    def add_client(
        self,
        inbound_id: int,
        email: str,
        days: int = 0,
        traffic_gb: float = 0,
        limit_ip: int = 0,
    ) -> str:
        """
        یک کلاینت جدید به اینباند اضافه می‌کنه و UUID ساخته‌شده رو برمی‌گردونه.
        days=0 یعنی بدون انقضا، traffic_gb=0 یعنی بدون محدودیت ترافیک.
        """
        client_uuid = str(uuid.uuid4())
        expiry_time = 0
        if days > 0:
            expiry_time = int((time.time() + days * 86400) * 1000)

        total_bytes = int(traffic_gb * 1024 * 1024 * 1024) if traffic_gb > 0 else 0

        client_obj = {
            "id": client_uuid,
            "flow": "",
            "email": email,
            "limitIp": limit_ip,
            "totalGB": total_bytes,
            "expiryTime": expiry_time,
            "enable": True,
            "tgId": "",
            "subId": uuid.uuid4().hex[:16],
            "reset": 0,
        }
        payload = {
            "id": inbound_id,
            "settings": json.dumps({"clients": [client_obj]}),
        }
        self._request("POST", "api/inbounds/addClient", json=payload)
        return client_uuid
