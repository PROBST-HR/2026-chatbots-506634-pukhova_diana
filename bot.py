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


# ====== Хранилище задач ======
tasks = []


def format_tasks():
    if not tasks:
        return "📭 Задач нет"

    text = "📋 Ваши задачи:\n\n"

    for i, t in enumerate(sorted(tasks, key=lambda x: x["priority"], reverse=True), 1):
        status = "✅" if t["done"] else "❌"
        text += f"{i}. {status} {t['name']} (p{t['priority']})\n"

    return text


# ====== Команды ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот задач 🚀\n\n"
        "/add задача приоритет\n"
        "/list\n"
        "/done номер\n"
        "/clear"
    )


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args

        if len(args) < 2:
            await update.message.reply_text("Формат: /add задача приоритет(1-3)")
            return

        name = " ".join(args[:-1])
        priority = int(args[-1])

        tasks.append({
            "name": name,
            "priority": priority,
            "done": False
        })

        await update.message.reply_text("✅ Добавлено")

    except:
        await update.message.reply_text("Ошибка")


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_tasks())


async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        index = int(context.args[0]) - 1

        sorted_tasks = sorted(tasks, key=lambda x: x["priority"], reverse=True)

        if index < 0 or index >= len(sorted_tasks):
            await update.message.reply_text("Неверный номер")
            return

        task = sorted_tasks[index]
        task["done"] = True

        await update.message.reply_text(f"✔ Выполнено: {task['name']}")

    except:
        await update.message.reply_text("Формат: /done номер")


async def clear_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks.clear()
    await update.message.reply_text("🧹 Очищено")


# ====== main ======

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("done", done_task))
    app.add_handler(CommandHandler("clear", clear_tasks))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
