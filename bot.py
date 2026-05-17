import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# ─── SETTINGS ───────────────────────────────────────────────────────────────
BOT_TOKEN = "8121813747:AAESK2XuHQVy-wa9RDs9wnwEsiX59ntDL4I"
ADMIN_CHAT_ID = 277131469
# ────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
(
    WELCOME,
    PROJECT_TYPE,
    SERVICE,
    BUDGET,
    AREA,
    NAME,
    PHONE,
) = range(7)


# ─── KEYBOARDS ──────────────────────────────────────────────────────────────

def kb_start() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Оставить заявку →", callback_data="start_form")],
    ])


def kb_project_type() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏠 Ремонт квартиры", callback_data="pt_apartment"),
            InlineKeyboardButton("🏡 Строительство дома", callback_data="pt_house"),
        ],
        [
            InlineKeyboardButton("🏢 Коммерческий объект", callback_data="pt_commercial"),
            InlineKeyboardButton("❓ Другое", callback_data="pt_other"),
        ],
    ])


def kb_service() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Технический надзор", callback_data="svc_supervision")],
        [InlineKeyboardButton("🔑 Полное управление проектом", callback_data="svc_full")],
        [InlineKeyboardButton("🚨 Антикризис — ремонт уже идёт", callback_data="svc_crisis")],
        [InlineKeyboardButton("💬 Хочу сначала проконсультироваться", callback_data="svc_consult")],
    ])


def kb_budget() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("до 1 млн ₽", callback_data="bud_under1"),
            InlineKeyboardButton("1 — 3 млн ₽", callback_data="bud_1_3"),
        ],
        [
            InlineKeyboardButton("3 — 10 млн ₽", callback_data="bud_3_10"),
            InlineKeyboardButton("от 10 млн ₽", callback_data="bud_over10"),
        ],
    ])


def kb_area() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("до 50 м²", callback_data="area_under50"),
            InlineKeyboardButton("50 — 100 м²", callback_data="area_50_100"),
        ],
        [
            InlineKeyboardButton("100 — 200 м²", callback_data="area_100_200"),
            InlineKeyboardButton("от 200 м²", callback_data="area_over200"),
        ],
    ])


def kb_restart() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Оставить ещё одну заявку", callback_data="restart")],
    ])


# ─── LABEL MAPS ─────────────────────────────────────────────────────────────

PROJECT_TYPE_LABELS = {
    "pt_apartment": "🏠 Ремонт квартиры",
    "pt_house": "🏡 Строительство дома",
    "pt_commercial": "🏢 Коммерческий объект",
    "pt_other": "❓ Другое",
}

SERVICE_LABELS = {
    "svc_supervision": "📋 Технический надзор",
    "svc_full": "🔑 Полное управление проектом",
    "svc_crisis": "🚨 Антикризис — ремонт уже идёт",
    "svc_consult": "💬 Консультация",
}

BUDGET_LABELS = {
    "bud_under1": "до 1 млн ₽",
    "bud_1_3": "1 — 3 млн ₽",
    "bud_3_10": "3 — 10 млн ₽",
    "bud_over10": "от 10 млн ₽",
}

AREA_LABELS = {
    "area_under50": "до 50 м²",
    "area_50_100": "50 — 100 м²",
    "area_100_200": "100 — 200 м²",
    "area_over200": "от 200 м²",
}


# ─── HELPERS ────────────────────────────────────────────────────────────────

async def send_error(update: Update) -> None:
    text = "Что-то пошло не так. Напишите /start чтобы начать заново."
    if update.callback_query:
        await update.callback_query.message.reply_text(text)
    elif update.message:
        await update.message.reply_text(text)


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, user_data: dict, user) -> None:
    username = f"@{user.username}" if user.username else "не указан"
    dt = datetime.now().strftime("%d.%m.%Y %H:%M")
    text = (
        f"🔔 НОВАЯ ЗАЯВКА — ТОЧКА КОНТРОЛЯ\n\n"
        f"👤 Имя: {user_data['name']}\n"
        f"📱 Телефон: {user_data['phone']}\n"
        f"🏗 Тип проекта: {user_data['project_type']}\n"
        f"📋 Услуга: {user_data['service']}\n"
        f"💰 Бюджет: {user_data['budget']}\n"
        f"📐 Площадь: {user_data['area']}\n\n"
        f"🕐 Время: {dt}\n"
        f"👤 Telegram: {username} (id: {user.id})"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


# ─── HANDLERS ───────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    text = (
        "Здравствуйте! 👋\n"
        "Я помогу оставить заявку на управление вашим строительным проектом.\n\n"
        "Точка контроля — независимый контроль ремонта и строительства.\n"
        "Это займёт 1 минуту."
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=kb_start())
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(text, reply_markup=kb_start())
    return WELCOME


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "ℹ️ Этот бот помогает оставить заявку на услуги компании Точка контроля.\n\n"
        "Мы занимаемся независимым контролем ремонта и строительства.\n"
        "Сайт: tkcontrol.ru\n\n"
        "Нажмите кнопку, чтобы начать:"
    )
    await update.message.reply_text(text, reply_markup=kb_start())
    return WELCOME


async def welcome_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.data in ("start_form", "restart"):
        context.user_data.clear()
        await query.message.reply_text("Что планируете?", reply_markup=kb_project_type())
        return PROJECT_TYPE
    return WELCOME


async def project_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    label = PROJECT_TYPE_LABELS.get(query.data)
    if not label:
        await query.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👆",
            reply_markup=kb_project_type(),
        )
        return PROJECT_TYPE
    context.user_data["project_type"] = label
    await query.message.reply_text(
        "Какая услуга вас интересует?", reply_markup=kb_service()
    )
    return SERVICE


async def service_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    label = SERVICE_LABELS.get(query.data)
    if not label:
        await query.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👆",
            reply_markup=kb_service(),
        )
        return SERVICE
    context.user_data["service"] = label
    await query.message.reply_text(
        "Примерный бюджет проекта?", reply_markup=kb_budget()
    )
    return BUDGET


async def budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    label = BUDGET_LABELS.get(query.data)
    if not label:
        await query.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👆",
            reply_markup=kb_budget(),
        )
        return BUDGET
    context.user_data["budget"] = label
    await query.message.reply_text("Площадь объекта?", reply_markup=kb_area())
    return AREA


async def area_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    label = AREA_LABELS.get(query.data)
    if not label:
        await query.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👆",
            reply_markup=kb_area(),
        )
        return AREA
    context.user_data["area"] = label
    await query.message.reply_text("Как вас зовут?")
    return NAME


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = (update.message.text or "").strip()
    if len(name) < 2:
        await update.message.reply_text("Пожалуйста, введите ваше имя (минимум 2 символа):")
        return NAME
    context.user_data["name"] = name
    await update.message.reply_text(
        "Оставьте номер телефона — свяжемся в течение 2 часов:"
    )
    return PHONE


async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = (update.message.text or "").strip()
    digits = [c for c in phone if c.isdigit()]
    if len(digits) < 10:
        await update.message.reply_text(
            "Номер телефона должен содержать не менее 10 цифр.\n"
            "Пример: +7 900 123-45-67\n\n"
            "Попробуйте ещё раз:"
        )
        return PHONE
    context.user_data["phone"] = phone

    try:
        await notify_admin(context, context.user_data, update.effective_user)
    except Exception:
        logger.exception("Failed to notify admin")

    await update.message.reply_text(
        "✅ Заявка принята!\n\n"
        "Мы свяжемся с вами в течение 2 часов.\n\n"
        "Если хотите — можете написать нам напрямую:\n"
        "👉 @tkcontrol\n\n"
        "До встречи! 🤝",
        reply_markup=kb_restart(),
    )
    return WELCOME


async def unexpected_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Пожалуйста, используйте кнопки для ответа 👆")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling update:", exc_info=context.error)
    if isinstance(update, Update):
        await send_error(update)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            MessageHandler(filters.ALL & ~filters.COMMAND, cmd_start),
        ],
        states={
            WELCOME: [
                CallbackQueryHandler(welcome_button, pattern="^(start_form|restart)$"),
            ],
            PROJECT_TYPE: [
                CallbackQueryHandler(project_type_handler, pattern="^pt_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            ],
            SERVICE: [
                CallbackQueryHandler(service_handler, pattern="^svc_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            ],
            BUDGET: [
                CallbackQueryHandler(budget_handler, pattern="^bud_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            ],
            AREA: [
                CallbackQueryHandler(area_handler, pattern="^area_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unexpected_text),
            ],
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler),
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler),
            ],
        },
        fallbacks=[
            CommandHandler("start", cmd_start),
            CommandHandler("help", cmd_help),
        ],
        allow_reentry=False,
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_error_handler(error_handler)

    logger.info("Bot started — Точка контроля")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
