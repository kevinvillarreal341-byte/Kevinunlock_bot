import sqlite3
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os
TOKEN = os.getenv("TOKEN")

def init_db():
    conn = sqlite3.connect("seriales.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispositivos (
            serial TEXT PRIMARY KEY,
            marca TEXT,
            modelo TEXT,
            estado TEXT
        )
    """)
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 Kevin Unlock", url="https://kevinunlock.netlify.app/")],
        [InlineKeyboardButton("📜 Reglas del grupo", url="https://t.me/username")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Bienvenido a *Kevin Unlock Bot*\n\n"
        "Usa `/check` para consultar, `/add` para registrar un serial, y `/list` para ver todos.\n\n"
        "Ejemplo:\n`/check 123456789`\n`/add 111111111 Samsung A14 Liberado`",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def add_serial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 4:
        await update.message.reply_text("❌ Usa el comando así:\n`/add SERIAL MARCA MODELO ESTADO`", parse_mode="Markdown")
        return

    serial, marca, modelo, estado = context.args[0], context.args[1], context.args[2], " ".join(context.args[3:])
    conn = sqlite3.connect("seriales.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO dispositivos VALUES (?, ?, ?, ?)", (serial, marca, modelo, estado))
        conn.commit()
        await update.message.reply_text(f"✅ Serial `{serial}` registrado correctamente.", parse_mode="Markdown")
    except sqlite3.IntegrityError:
        await update.message.reply_text("⚠️ Ese serial ya está registrado.")
    finally:
        conn.close()

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("❌ Usa `/check SERIAL`", parse_mode="Markdown")
        return

    serial = context.args[0]
    conn = sqlite3.connect("seriales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT marca, modelo, estado FROM dispositivos WHERE serial = ?", (serial,))
    result = cursor.fetchone()
    conn.close()

    if result:
        marca, modelo, estado = result
        info = f"📱 *Serial:* `{serial}`\n- Marca: {marca}\n- Modelo: {modelo}\n- Estado: {estado}"
    else:
        try:
            url = f"https://kevinunlock-api.onrender.com/api/check?serial={serial}"
            response = requests.get(url)
            data = response.json()
            if "error" in data:
                info = f"⚠️ {data['error']}"
            else:
                info = f"📱 *Serial:* `{serial}`\n- Marca: {data['marca']}\n- Modelo: {data['modelo']}\n- Estado: {data['estado']}"
        except Exception as e:
            info = f"❌ Error al conectar con la API: {e}"

    await update.message.reply_text(info, parse_mode="Markdown")

async def list_serials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("seriales.db")
    cursor = conn.cursor()
    cursor.execute("SELECT serial, marca, modelo, estado FROM dispositivos")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📂 No hay seriales registrados todavía.")
        return

    text = "📋 *Lista de seriales registrados:*\n\n"
    for serial, marca, modelo, estado in rows:
        text += f"`{serial}` → {marca} {modelo} ({estado})\n"

    await update.message.reply_text(text, parse_mode="Markdown")

init_db()
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add_serial))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("list", list_serials))

print("🤖 Bot de Kevin Unlock con base de datos iniciado...")
app.run_polling()
