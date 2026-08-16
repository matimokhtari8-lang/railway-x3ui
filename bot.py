# -*- coding: utf-8 -*-
"""
ربات تلگرام فروش/ساخت کانفینگ برای 3x-ui.
از قبل یک اینباند روی پنل ساخته شده (INBOUND_ID) و این ربات فقط روی
همون اینباند کلاینت جدید می‌سازه — کاربر نهایی هیچ‌وقت با مفهوم
اینباند سر و کار نداره، فقط دکمه می‌زنه و کانفینگ می‌گیره.
"""
import io
import logging
from datetime import datetime

import qrcode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import config
import storage
from link_builder import build_vless_link
from panel_api import PanelAPI, PanelError

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

panel = PanelAPI(config.PANEL_URL, config.PANEL_BASE_PATH, config.PANEL_USERNAME, config.PANEL_PASSWORD)

DURATIONS = [
    ("🟢 ۷ روز", 7),
    ("🔵 ۳۰ روز", 30),
    ("🟣 ۹۰ روز", 90),
    ("⚪ نامحدود", 0),
]

TRAFFICS = [
    ("🟢 ۱۰ گیگ", 10),
    ("🔵 ۵۰ گیگ", 50),
    ("🟣 ۱۰۰ گیگ", 100),
    ("⚪ نامحدود", 0),
]


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🟣 ساخت کانفینگ جدید", callback_data="new")],
            [InlineKeyboardButton("📦 کانفینگ‌های من", callback_data="mine")],
            [InlineKeyboardButton("ℹ️ راهنما", callback_data="help")],
        ]
    )


def durations_kb() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(label, callback_data=f"dur:{days}") for label, days in DURATIONS]
    return InlineKeyboardMarkup([row[:2], row[2:], [InlineKeyboardButton("⬅️ بازگشت", callback_data="back:menu")]])


def traffics_kb() -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(label, callback_data=f"gb:{gb}") for label, gb in TRAFFICS]
    return InlineKeyboardMarkup([row[:2], row[2:], [InlineKeyboardButton("⬅️ بازگشت", callback_data="back:new")]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"سلام 👋 به ربات *{config.SERVICE_NAME}* خوش اومدید.\n\n"
        "از دکمه‌های زیر برای ساخت یا مشاهده‌ی کانفینگ‌هاتون استفاده کنید.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_kb(),
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back:menu" or data == "help_back":
        await query.edit_message_text(
            f"سلام 👋 به ربات *{config.SERVICE_NAME}* خوش اومدید.\n\n"
            "از دکمه‌های زیر برای ساخت یا مشاهده‌ی کانفینگ‌هاتون استفاده کنید.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(),
        )

    elif data == "help":
        await query.edit_message_text(
            "ℹ️ *راهنما*\n\n"
            "۱. روی «ساخت کانفینگ جدید» بزنید.\n"
            "۲. مدت اعتبار و حجم ترافیک رو انتخاب کنید.\n"
            "۳. لینک و QR کد کانفینگ براتون ارسال می‌شه.\n"
            "۴. لینک رو در اپلیکیشن کلاینت (v2rayNG، Streisand، Shadowrocket و ...) وارد کنید.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back:menu")]]),
        )

    elif data == "new" or data == "back:new":
        await query.edit_message_text(
            "⏳ مدت اعتبار کانفینگ رو انتخاب کنید:",
            reply_markup=durations_kb(),
        )

    elif data.startswith("dur:"):
        days = int(data.split(":")[1])
        context.user_data["days"] = days
        await query.edit_message_text(
            "📊 حالا حجم ترافیک مورد نظرتون رو انتخاب کنید:",
            reply_markup=traffics_kb(),
        )

    elif data.startswith("gb:"):
        gb = int(data.split(":")[1])
        days = context.user_data.get("days", 30)
        await query.edit_message_text("⚙️ در حال ساخت کانفینگ، چند لحظه صبر کنید...")
        await create_and_send_config(query, context, days, gb)

    elif data == "mine":
        configs = storage.get_configs(query.from_user.id)
        if not configs:
            text = "هنوز هیچ کانفینگی نساختید."
        else:
            lines = ["📦 *کانفینگ‌های شما:*\n"]
            for c in configs[-10:]:
                exp = "نامحدود" if c["days"] == 0 else f"{c['days']} روزه"
                gb = "نامحدود" if c["gb"] == 0 else f"{c['gb']} گیگ"
                lines.append(f"• `{c['remark']}` — {exp}، {gb}")
            text = "\n".join(lines)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ بازگشت", callback_data="back:menu")]]),
        )


async def create_and_send_config(query, context: ContextTypes.DEFAULT_TYPE, days: int, gb: int):
    user = query.from_user
    remark = f"{config.SERVICE_NAME}-{user.id}-{int(datetime.now().timestamp())}"

    try:
        client_uuid = panel.add_client(
            inbound_id=config.INBOUND_ID,
            email=remark,
            days=days,
            traffic_gb=gb,
        )
    except PanelError as e:
        await query.edit_message_text(f"❌ خطا در ساخت کانفینگ:\n{e}", reply_markup=main_menu_kb())
        return
    except Exception:
        log.exception("unexpected error while creating client")
        await query.edit_message_text("❌ یک خطای غیرمنتظره رخ داد. بعدا دوباره امتحان کنید.", reply_markup=main_menu_kb())
        return

    link = build_vless_link(client_uuid, remark)

    storage.add_config(
        user.id,
        {"remark": remark, "uuid": client_uuid, "days": days, "gb": gb, "link": link},
    )

    exp_text = "نامحدود ♾️" if days == 0 else f"{days} روز 📅"
    gb_text = "نامحدود ♾️" if gb == 0 else f"{gb} گیگابایت 📶"

    caption = (
        f"✅ کانفینگ شما ساخته شد!\n\n"
        f"⏳ اعتبار: {exp_text}\n"
        f"📊 ترافیک: {gb_text}\n\n"
        f"🔗 لینک اتصال:\n`{link}`"
    )

    qr_img = qrcode.make(link)
    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    buf.seek(0)

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=buf,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_kb(),
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in config.ADMIN_IDS:
        return
    await update.message.reply_text(f"📈 تعداد کل کانفینگ‌های ساخته‌شده: {storage.total_count()}")


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN تنظیم نشده. متغیر محیطی BOT_TOKEN رو ست کنید.")

    app = Application.builder().token(config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(on_button))

    log.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
