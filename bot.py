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


# простое хранилище задач (в памяти)
user_tasks = {}


# ---------- COMMANDS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Task Planner Bot\n\n"
        "Команды:\n"
        "/add <задача>\n"
        "/list\n"
        "/clear"
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    task = " ".join(context.args)

    if not task:
        await update.message.reply_text("Напиши задачу: /add купить кофе")
        return

    user_tasks.setdefault(user_id, []).append(task)
    await update.message.reply_text(f"Добавлено: {task}")


async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    tasks = user_tasks.get(user_id, [])

    if not tasks:
        await update.message.reply_text("Задач нет 📭")
        return

    text = "📋 Твои задачи:\n"
    for i, t in enumerate(tasks, 1):
        text += f"{i}. {t}\n"

    await update.message.reply_text(text)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_tasks[user_id] = []
    await update.message.reply_text("Все задачи удалены 🧹")


# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("clear", clear))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
