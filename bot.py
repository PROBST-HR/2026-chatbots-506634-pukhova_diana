import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")


# ====== Простое хранилище задач в памяти ======
tasks = []


def format_tasks():
    if not tasks:
        return "📭 Задач пока нет"

    text = "📋 Ваши задачи:\n\n"
    for i, t in enumerate(sorted(tasks, key=lambda x: x["priority"], reverse=True), 1):
        text += f"{i}. {t['name']} (приоритет: {t['priority']})\n"
    return text


# ====== Команды ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот-планировщик задач 🚀\n\n"
        "Команды:\n"
        "/add задача приоритет(1-3)\n"
        "/list — список задач\n"
        "/clear — очистить"
    )


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args

        if len(args) < 2:
            await update.message.reply_text("Используй: /add задача приоритет(1-3)")
            return

        name = " ".join(args[:-1])
        priority = int(args[-1])

        if priority not in [1, 2, 3]:
            await update.message.reply_text("Приоритет должен быть 1, 2 или 3")
            return

        tasks.append({"name": name, "priority": priority})

        await update.message.reply_text(
            f"✅ Добавлено: {name} (приоритет {priority})"
        )

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка при добавлении задачи")


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_tasks())


async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks.clear()
    await update.message.reply_text("🧹 Все задачи удалены")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("clear", clear_tasks))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
