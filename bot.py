from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import sqlite3
import pandas as pd
import os
import sys

TOKEN = "7576651813:AAFe2vu-HaojRWQp7ca6KUV1IgEso866t0Q"

def connect_db():
    return sqlite3.connect("prices.db", check_same_thread=False)

db = connect_db()
cursor = db.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS items (description TEXT, price REAL)")
db.commit()

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Totale", callback_data='total')],
                [InlineKeyboardButton("Esporta Excel", callback_data='export')],
                [InlineKeyboardButton("Cancella Dati", callback_data='delete_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        await update.message.reply_text("Scegli un'opzione:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Scegli un'opzione:", reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update, context)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_menu(update, context)

async def add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.rsplit(" ", 1)
    
    if len(parts) != 2 or not parts[1].replace('.', '', 1).isdigit():
        await update.message.reply_text("Formato non valido! Usa: Descrizione Prezzo")
        return
    
    description, price = parts[0], float(parts[1])
    cursor.execute("INSERT INTO items VALUES (?, ?)", (description, price))
    db.commit()
    await update.message.reply_text(f"Aggiunto: {description} - €{price:.2f}")
    await show_menu(update, context)

async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT description, price FROM items")
    items = cursor.fetchall()
    
    if not items:
        await update.callback_query.message.reply_text("Nessun prodotto aggiunto.")
        return
    
    total = sum(price for _, price in items)
    response = "Lista prodotti:\n"
    response += "\n".join([f"{desc}: €{price:.2f}" for desc, price in items])
    response += f"\n\nTotale: €{total:.2f}"
    await update.callback_query.message.reply_text(response)
    await show_menu(update, context)

async def export_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT * FROM items")
    data = cursor.fetchall()
    
    if not data:
        await update.callback_query.message.reply_text("Nessun dato da esportare.")
        return
    
    df = pd.DataFrame(data, columns=["Descrizione", "Prezzo"])
    filename = "lista_prezzi.xlsx"
    df.to_excel(filename, index=False)
    
    await update.callback_query.message.reply_document(document=open(filename, "rb"))
    await show_menu(update, context)

async def delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT description FROM items")
    items = cursor.fetchall()
    
    if not items:
        await update.callback_query.message.reply_text("Nessun prodotto da eliminare.")
        return
    
    keyboard = [[InlineKeyboardButton(desc, callback_data=f'delete_{desc}') for (desc,) in items]]
    keyboard.append([InlineKeyboardButton("Elimina tutto", callback_data='clear')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Scegli cosa eliminare:", reply_markup=reply_markup)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("DELETE FROM items")
    db.commit()
    await update.callback_query.message.reply_text("Dati cancellati!")
    await show_menu(update, context)

async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE, item: str):
    cursor.execute("DELETE FROM items WHERE description = ?", (item,))
    db.commit()
    await update.callback_query.message.reply_text(f"Eliminato: {item}")
    await show_menu(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "total":
        await total(update, context)
    elif query.data == "export":
        await export_excel(update, context)
    elif query.data == "delete_menu":
        await delete_menu(update, context)
    elif query.data == "clear":
        await clear(update, context)
    elif query.data.startswith("delete_"):
        item = query.data.replace("delete_", "")
        await delete_item(update, context, item)

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("menu", menu))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_item))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot in esecuzione...")
app.run_polling()
