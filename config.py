import os

# --- توکن ربات تلگرام (از @BotFather بگیرید) ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# --- آدرس کامل پنل (بدون اسلش آخر) مثال: https://yourdomain.up.railway.app ---
PANEL_URL = os.environ.get("PANEL_URL", "").rstrip("/")

# --- مسیر پایه‌ی پنل، همون webBasePath که در تنظیمات x-ui گذاشتید ---
PANEL_BASE_PATH = os.environ.get("PANEL_BASE_PATH", "/managepanel/").strip("/")

# --- یوزرنیم و پسورد ادمین پنل ---
PANEL_USERNAME = os.environ.get("PANEL_USERNAME", "")
PANEL_PASSWORD = os.environ.get("PANEL_PASSWORD", "")

# --- آی‌دی همون اینباندی که از قبل توی پنل ساختید (عدد) ---
INBOUND_ID = int(os.environ.get("INBOUND_ID", "1"))

# --- آی‌دی عددی تلگرام ادمین‌ها، جدا شده با کاما. مثال: "111111,222222" ---
ADMIN_IDS = [
    int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x
]

# --- نام/برند سرویس که در کپشن کانفینگ‌ها نمایش داده می‌شه ---
SERVICE_NAME = os.environ.get("SERVICE_NAME", "MyVPN")

# --- SNI/Host که در پنل روی اینباند تنظیم کردید (برای ساخت لینک vless) ---
SNI_HOST = os.environ.get("SNI_HOST", "")

# --- مسیر WebSocket که روی اینباند گذاشتید (مثلا /cdn) ---
WS_PATH = os.environ.get("WS_PATH", "/cdn")
