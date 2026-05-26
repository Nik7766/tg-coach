import os
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

BASE_STYLE = """
Твій стиль спілкування — адаптивний:
- Коли людина ділиться болем, сумнівами чи труднощами — ти спочатку визнаєш її відчуття, підтримуєш і мотивуєш. Не поспішаєш з порадами.
- Коли людина просить план, кроки або конкретику — ти прямий, чіткий, по суті. Без зайвої "води".
- Ти ніколи не лестиш і не кажеш порожніх фраз. Якщо треба — говориш правду прямо, але з повагою.
- Задаєш одне потужне запитання наприкінці, якщо відчуваєш, що людина ще не до кінця розкрила суть.
- Відповідаєш стисло — 3–5 речень, якщо не просять більше. Без зайвих вступів.
- Спілкуєшся виключно українською мовою, природно і живо.
"""

SYSTEM_PROMPTS = {
    "universal":     f"Ти — персональний коуч-наставник, який охоплює всі сфери життя: кар'єру, здоров'я, мислення, звички, стосунки, фінанси. {BASE_STYLE}",
    "career":        f"Ти — коуч з кар'єрного розвитку та продуктивності. Допомагаєш знайти покликання, рости в кар'єрі, будувати особистий бренд, керувати часом і енергією. {BASE_STYLE}",
    "health":        f"Ти — коуч зі здорового способу життя. Допомагаєш з харчуванням, рухом, сном, енергією та стресом. {BASE_STYLE}",
    "mindset":       f"Ти — коуч з розвитку мислення. Допомагаєш з переконаннями, самооцінкою, страхами, фокусом і внутрішнім діалогом. {BASE_STYLE}",
    "habits":        f"Ти — коуч зі звичок та самодисципліни. Знаєш нейронауку звичок і методи побудови рутин. {BASE_STYLE}",
    "relationships": f"Ти — коуч зі стосунків та комунікації. Допомагаєш з особистими й робочими стосунками, межами, конфліктами та самотністю. {BASE_STYLE}",
    "finance":       f"Ти — коуч з особистих фінансів та фінансового мислення. Допомагаєш з бюджетом, заощадженнями, інвестиційним мисленням і стосунком до грошей. {BASE_STYLE}",
}

GREETINGS = {
    "universal":     "Вітаю! Я твій персональний коуч ✦\n\nГотовий розібратися в будь-якій сфері — від кар'єри до внутрішнього стану. Розкажи, що зараз найбільш актуально для тебе?",
    "career":        "💼 *Кар'єра та продуктивність*\n\nПоговоримо про твій шлях, цілі та можливості. Що зараз найбільше хвилює у кар'єрі?",
    "health":        "🌿 *Здоровий спосіб життя*\n\nТіло і розум — єдине ціле. З чого почнемо — енергія, сон, рух чи харчування?",
    "mindset":       "🧠 *Розвиток мислення*\n\nЧасто найбільша перешкода — всередині нас. Що зараз найбільше заважає тобі рухатися вперед?",
    "habits":        "⚡ *Звички та дисципліна*\n\nМи те, що робимо щодня. Яку звичку хочеш побудувати або позбутися?",
    "relationships": "💛 *Стосунки та комунікація*\n\nЗв'язки з людьми — основа щасливого життя. Що зараз непросто у стосунках?",
    "finance":       "💰 *Фінанси та гроші*\n\nГроші — це інструмент, а не мета. Що зараз найбільше турбує у фінансовому питанні?",
}

# In-memory user state: { user_id: { "area": str, "history": list } }
user_state = {}

def get_state(user_id):
    if user_id not in user_state:
        user_state[user_id] = {"area": "universal", "history": []}
    return user_state[user_id]

def area_keyboard():
    buttons = [
        [InlineKeyboardButton("🌟 Все", callback_data="area:universal"),
         InlineKeyboardButton("💼 Кар'єра", callback_data="area:career")],
        [InlineKeyboardButton("🌿 Здоров'я", callback_data="area:health"),
         InlineKeyboardButton("🧠 Мислення", callback_data="area:mindset")],
        [InlineKeyboardButton("⚡ Звички", callback_data="area:habits"),
         InlineKeyboardButton("💛 Стосунки", callback_data="area:relationships")],
        [InlineKeyboardButton("💰 Фінанси", callback_data="area:finance")],
    ]
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"area": "universal", "history": []}
    await update.message.reply_text(
        "✦ *Персональний Коуч*\n\nВітаю! Я твій AI-коуч, який адаптується до твоїх потреб.\n\nОбери сферу або просто напиши що на думці 👇",
        parse_mode="Markdown",
        reply_markup=area_keyboard()
    )

async def handle_area(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    area = query.data.split(":")[1]
    user_id = query.from_user.id
    user_state[user_id] = {"area": area, "history": []}
    await query.message.reply_text(GREETINGS[area], parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = get_state(user_id)
    text = update.message.text.strip()

    # Build Gemini history format
    state["history"].append({"role": "user", "parts": [text]})

    # Keep last 20 messages
    if len(state["history"]) > 20:
        state["history"] = state["history"][-20:]

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPTS[state["area"]]
        )
        chat = model.start_chat(history=state["history"][:-1])
        response = chat.send_message(text)
        reply = response.text

        state["history"].append({"role": "model", "parts": [reply]})

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Змінити сферу", callback_data="show_areas")
        ]])
        await update.message.reply_text(reply, reply_markup=keyboard)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Виникла помилка. Спробуй ще раз або напиши /start")

async def show_areas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Обери сферу для розмови:", reply_markup=area_keyboard())

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"area": "universal", "history": []}
    await update.message.reply_text(
        "Розмову скинуто. Починаємо з чистого листа 🌱",
        reply_markup=area_keyboard()
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CallbackQueryHandler(handle_area, pattern="^area:"))
    app.add_handler(CallbackQueryHandler(show_areas, pattern="^show_areas$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
