import json
import os
import csv
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# -------------------- TOKEN --------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

# -------------------- FILES --------------------
DATA_FILE = "tasks.json"
EMP_FILE = "employees.csv"

# -------------------- STATES --------------------
TASK_TEXT, TASK_PRIORITY, TASK_REMINDER, TASK_DATETIME = range(4)
EMPLOYEE_SEARCH = 10

# -------------------- TASKS (JSON) --------------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# -------------------- EMPLOYEES (CSV) --------------------
def load_employees():
    if not os.path.exists(EMP_FILE):
        return []
    with open(EMP_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# -------------------- START --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Добавить задачу", "Список задач"],
        ["Удалить задачу", "Сотрудники"]
    ]

    await update.message.reply_text(
        "Привет! Я бот 😊\nВыбери действие:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# -------------------- ADD TASK --------------------
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
        await update.message.reply_text("Введите дату: YYYY-MM-DD HH:MM")
        return TASK_DATETIME
    else:
        context.user_data["datetime"] = None
        return await save_task(update, context)

async def add_datetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        dt = datetime.strptime(update.message.text, "%Y-%m-%d %H:%M")
        context.user_data["datetime"] = dt.isoformat()
        return await save_task(update, context)
    except:
        await update.message.reply_text("❌ Неверный формат!")
        return TASK_DATETIME

async def save_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)

    task = {
        "text": context.user_data.get("text"),
        "priority": context.user_data.get("priority"),
        "datetime": context.user_data.get("datetime"),
        "notified": False
    }

    data.setdefault(user_id, []).append(task)
    save_data(data)

    await update.message.reply_text("✅ Задача добавлена!")
    return ConversationHandler.END

# -------------------- LIST TASKS --------------------
async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)

    tasks = data.get(user_id, [])

    if not tasks:
        await update.message.reply_text("Список задач пуст")
        return

    text = ""
    for i, t in enumerate(tasks):
        line = f"{i+1}. {t['text']} ({t['priority']})"
        if t.get("datetime"):
            line += f" ⏰ {t['datetime']}"
        text += line + "\n"

    await update.message.reply_text(text)

# -------------------- DELETE TASK --------------------
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)
    tasks = data.get(user_id, [])

    if not tasks:
        await update.message.reply_text("Нет задач")
        return ConversationHandler.END

    text = "\n".join([f"{i+1}. {t['text']}" for i, t in enumerate(tasks)])
    await update.message.reply_text(text + "\n\nВведите номер задачи:")
    return 1

async def delete_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user_id = str(update.message.from_user.id)
    tasks = data.get(user_id, [])

    try:
        idx = int(update.message.text) - 1
        removed = tasks.pop(idx)
        save_data(data)
        await update.message.reply_text(f"🗑 Удалено: {removed['text']}")
    except:
        await update.message.reply_text("❌ Ошибка")

    return ConversationHandler.END

# -------------------- EMPLOYEES SEARCH --------------------
async def employees_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите имя или отдел:")
    return EMPLOYEE_SEARCH

async def employees_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.lower()
    employees = load_employees()

    result = [
        e for e in employees
        if query in e["name"].lower()
        or query in e["department"].lower()
    ]

    if not result:
        await update.message.reply_text("Ничего не найдено")
        return ConversationHandler.END

    text = ""
    for e in result:
        text += (
            f"👤 {e['name']}\n"
            f"🏢 {e['department']}\n"
            f"💼 {e['role']}\n"
            f"📧 {e['email']}\n\n"
        )

    await update.message.reply_text(text)
    return ConversationHandler.END

# -------------------- MAIN --------------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    add_conv = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            TASK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_text)],
            TASK_PRIORITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_priority)],
            TASK_REMINDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reminder)],
            TASK_DATETIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_datetime)],
        },
        fallbacks=[]
    )

    delete_conv = ConversationHandler(
        entry_points=[CommandHandler("delete", delete_start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_task)]
        },
        fallbacks=[]
    )

    emp_conv = ConversationHandler(
        entry_points=[CommandHandler("employees", employees_start)],
        states={
            EMPLOYEE_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, employees_search)]
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(add_conv)
    app.add_handler(delete_conv)
    app.add_handler(emp_conv)

    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
