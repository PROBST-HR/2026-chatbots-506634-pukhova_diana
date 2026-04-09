import os
import json
import csv
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# ---------------- TOKEN ----------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# ---------------- FILES ----------------
DATA_FILE = "tasks.json"
EMP_FILE = "employees.csv"

# ---------------- STATES ----------------
TASK_TEXT, TASK_PRIORITY, TASK_REMINDER, TASK_DATETIME = range(4)
EMP_SEARCH = 10


# ---------------- TASK STORAGE ----------------
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Добавить задачу", "Список задач"],
        ["Удалить задачу", "Сотрудники"]
    ]
    await update.message.reply_text(
        "Привет! Я HR-бот 🤖",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# ---------------- ADD TASK ----------------
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите задачу:", reply_markup=ReplyKeyboardRemove())
    return TASK_TEXT


async def add_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["text"] = update.message.text
    await update.message.reply_text("Приоритет: высокий / средний / низкий")
    return TASK_PRIORITY


async def add_priority(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["priority"] = update.message.text
    await update.message.reply_text("Нужно напоминание? (да/нет)")
    return TASK_REMINDER


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == "да":
        await update.message.reply_text("Дата: YYYY-MM-DD HH:MM")
        return TASK_DATETIME

    context.user_data["datetime"] = None
    return await save_task(update, context)


async def add_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dt = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        context.user_data["datetime"] = dt.isoformat()
        return await save_task(update, context)
    except:
        await update.message.reply_text("Ошибка формата")
        return TASK_DATETIME


async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)

    task = {
        "text": context.user_data["text"],
        "priority": context.user_data["priority"],
        "datetime": context.user_data.get("datetime"),
        "notified": False
    }

    data.setdefault(user_id, []).append(task)
    save_data(data)

    await update.message.reply_text("✅ Задача добавлена!")
    return ConversationHandler.END


# ---------------- LIST TASKS ----------------
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)
    tasks = data.get(user_id, [])

    if not tasks:
        await update.message.reply_text("Список пуст")
        return

    msg = ""
    for i, t in enumerate(tasks):
        msg += f"{i+1}. {t['text']} ({t['priority']})\n"

    await update.message.reply_text(msg)


# ---------------- DELETE ----------------
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)
    tasks = data.get(user_id, [])

    if not tasks:
        await update.message.reply_text("Нет задач")
        return ConversationHandler.END

    msg = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(tasks)])
    await update.message.reply_text(msg + "\nВведите номер:")
    return 1


async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)
    tasks = data.get(user_id, [])

    try:
        idx = int(update.message.text) - 1
        removed = tasks.pop(idx)
        save_data(data)
        await update.message.reply_text(f"Удалено: {removed['text']}")
    except:
        await update.message.reply_text("Ошибка")

    return ConversationHandler.END


# ---------------- EMPLOYEES (CSV without pandas) ----------------
def load_employees():
    with open(EMP_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


async def employees_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя или отдел:")
    return EMP_SEARCH


async def employees_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()

    try:
        data = load_employees()

        result = [
            r for r in data
            if query in r["name"].lower() or query in r["department"].lower()
        ]

        if not result:
            await update.message.reply_text("Ничего не найдено")
            return ConversationHandler.END

        msg = ""
        for r in result:
            msg += (
                f"👤 {r['name']}\n"
                f"🏢 {r['department']}\n"
                f"💼 {r['role']}\n"
                f"📧 {r['email']}\n\n"
            )

        await update.message.reply_text(msg)

    except FileNotFoundError:
        await update.message.reply_text("employees.csv не найден")

    return ConversationHandler.END


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Добавить задачу$"), add_start)],
        states={
            TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_text)],
            TASK_PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_priority)],
            TASK_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reminder)],
            TASK_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_datetime)],
        },
        fallbacks=[],
    )

    delete_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Удалить задачу$"), delete_start)],
        states={1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task)]},
        fallbacks=[],
    )

    emp_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Сотрудники$"), employees_start)],
        states={EMP_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, employees_search)]},
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^Список задач$"), list_tasks))

    app.add_handler(add_conv)
    app.add_handler(delete_conv)
    app.add_handler(emp_conv)

    print("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
