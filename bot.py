import asyncio
import random
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "9054136450:AAELY2x5ZHANZ2dEQVszipDeRG8RojpMLu4"
MAIN_ADMIN_ID = 8650129848  # <-- СЮДА СВОЙ ID
ADMIN_USERNAME = "@bogwesi"  # <-- СЮДА СВОЙ ЮЗЕРНЕЙМ
BOT_LINK = "https://t.me/darkbtcrobot"  # <-- ССЫЛКА НА БОТА

BOT_NAME = "Dark BTC"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users_db = {}
admins_list = [MAIN_ADMIN_ID]
START_BALANCE = 1_000_000
GLOBAL_LUCK = 50

# ================= ФУНКЦИИ =================
def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            "balance": START_BALANCE,
            "premium": False,
            "games": 0,
            "wins": 0,
            "losses": 0,
            "won_money": 0,
            "lost_money": 0,
            "luck": None,
        }
    return users_db[user_id]

def parse_money(text):
    text = text.lower().replace(' ', '')
    multipliers = {
        'к': 1_000, 'кк': 1_000_000, 'лям': 1_000_000, 'млн': 1_000_000,
        'ккк': 1_000_000_000, 'млрд': 1_000_000_000,
        'т': 1_000_000_000_000, 'трлн': 1_000_000_000_000,
    }
    for suffix, mult in multipliers.items():
        if text.endswith(suffix):
            try:
                return int(float(text[:-len(suffix)]) * mult)
            except ValueError:
                return None
    try:
        return int(text)
    except ValueError:
        return None

def is_admin(user_id):
    return user_id in admins_list

def check_win(user):
    luck = user.get("luck")
    if luck is None:
        luck = GLOBAL_LUCK
    return random.randint(1, 100) <= luck

# ================= ПЕРЕХВАТЧИК СООБЩЕНИЙ =================
@dp.message()
async def catch_all_messages(message: Message, **kwargs):
    if message.from_user:
        get_user(message.from_user.id)

@dp.message(F.new_chat_members)
async def on_user_join(message: Message):
    for member in message.new_chat_members:
        if is_admin(member.id):
            await message.answer(f"👑 Здравствуйте, администратор <b>{member.first_name}</b>!", parse_mode="HTML")
        elif member.id == bot.id:
            await message.answer(f"👋 Привет! Я <b>{BOT_NAME}</b> — игровой бот.\nПиши: <code>казик 1к</code>, <code>б</code> и играй!", parse_mode="HTML")

# ================= КЛАВИАТУРЫ =================
def get_main_kb():
    kb = [
        [KeyboardButton(text="🎰 Казино"), KeyboardButton(text="💎 Магазин")],
        [KeyboardButton(text="🏆 Топ"), KeyboardButton(text="💼 Профиль")],
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="ℹ️ Все команды")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_casino_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Крутить за 100к", callback_data="bet_100k")
    kb.button(text="🎲 Крутить за 1кк (1млн)", callback_data="bet_1m")
    kb.button(text="💎 Купить Премиум", callback_data="buy_premium")
    kb.adjust(1)
    return kb.as_markup()

# ================= СТАРТ =================
@dp.message(CommandStart())
async def start_cmd(message: Message):
    get_user(message.from_user.id)
    text = (
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        f"Добро пожаловать в <b>{BOT_NAME}</b> 🎰\n\n"
        f"🎰 Казино — пиши: казик, баскет, волик и т.д.\n"
        f"📊 Статистика — напиши «баланс» или «б»\n"
        f"🏆 Топ — лучшие игроки\n\n"
        f"<i>Стартовый капитал: 1 000 000 BTC</i>"
    )
    await message.answer(text, reply_markup=get_main_kb(), parse_mode="HTML")

# ================= КАЗИНО =================
@dp.message(F.text == "🎰 Казино")
async def open_casino(message: Message):
    await message.answer(
        "🎰 <b>Казино</b>\n\nПиши в чат: <code>казик 1к</code>, <code>баскет 2кк</code>",
        reply_markup=get_casino_kb(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("bet_"))
async def process_bet(call: CallbackQuery):
    user = get_user(call.from_user.id)
    bet = 100_000 if call.data == "bet_100k" else 1_000_000

    if user["balance"] < bet:
        await call.answer("❌ Недостаточно BTC!", show_alert=True)
        return

    user["balance"] -= bet
    user["games"] += 1
    win = check_win(user)

    if win:
        user["balance"] += bet * 2
        user["wins"] += 1
        user["won_money"] += bet
        result = f"🎉 <b>ПОБЕДА!</b>\n+{bet:,} BTC"
    else:
        user["losses"] += 1
        user["lost_money"] += bet
        result = f"😢 <b>Проигрыш...</b>\n-{bet:,} BTC"

    await call.message.edit_text(
        f"{result}\n\n💰 Баланс: <b>{user['balance']:,} BTC</b>",
        reply_markup=get_casino_kb(),
        parse_mode="HTML"
    )
    await call.answer()

# ================= ПРЕМИУМ =================
@dp.callback_query(F.data == "buy_premium")
async def buy_premium(call: CallbackQuery):
    user = get_user(call.from_user.id)
    if user["premium"]:
        await call.answer("У тебя уже есть Премиум! 👑", show_alert=True)
        return

    text = f"👑 <b>Покупка Премиум</b> в {BOT_NAME}\n\nНапиши админу: <b>{ADMIN_USERNAME}</b>\nСтоимость: 5 000 000 BTC"
    if ADMIN_USERNAME.startswith("@"):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME[1:]}")]
        ])
        await call.message.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# ================= ТОП =================
@dp.message(F.text == "🏆 Топ")
@dp.message(Command("top"))
async def show_top(message: Message):
    sorted_users = sorted(users_db.items(), key=lambda i: i[1]["balance"], reverse=True)
    if not sorted_users:
        await message.answer("Топ пуст.")
        return
    text = f"🏆 <b>Мировой Топ {BOT_NAME}</b> 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_users[:10], 1):
        try:
            info = await bot.get_chat(uid)
            name = info.first_name
        except:
            name = f"Игрок {uid}"
        mark = "👑 " if data["premium"] else ""
        text += f"{i}. {mark}<b>{name}</b> — {data['balance']:,} BTC\n"
    await message.answer(text, parse_mode="HTML")

# ================= СТАВКИ ТЕКСТОМ =================
@dp.message(F.text.regexp(r'(?i)^(казино|казик|каз|баскет|баскетбол|волик|волейбол)\s+(.+)$'))
async def text_bet(message: Message):
    user = get_user(message.from_user.id)
    command, amount_text = message.text.lower().split(' ', 1)
    amount = parse_money(amount_text)

    if amount is None:
        await message.answer("❌ Формат: <b>казик 100к</b>", parse_mode="HTML")
        return

    max_limit = 1_000_000_000_000 if user["premium"] else 5_000_000
    if amount > max_limit:
        await message.answer(f"❌ Максимальная ставка: {'1 триллион' if user['premium'] else '5 миллионов'} BTC", parse_mode="HTML")
        return
    if amount < 1000:
        await message.answer("❌ Минимум 1000 BTC")
        return
    if user["balance"] < amount:
        await message.answer(f"❌ Недостаточно BTC! Баланс: {user['balance']:,}")
        return

    user["balance"] -= amount
    user["games"] += 1
    win = check_win(user)

    icon = "🏀" if "баскет" in command else "🏐" if "волик" in command or "волейбол" in command else "🎰"

    if win:
        user["balance"] += amount * 2
        user["wins"] += 1
        user["won_money"] += amount
        await message.answer(f"{icon} <b>ПОБЕДА!</b>\n+{amount:,} BTC\nБаланс: {user['balance']:,} BTC", parse_mode="HTML")
    else:
        user["losses"] += 1
        user["lost_money"] += amount
        await message.answer(f"{icon} <b>Проигрыш!</b>\n-{amount:,} BTC\nБаланс: {user['balance']:,} BTC", parse_mode="HTML")

# ================= СТАТИСТИКА =================
@dp.message(F.text.lower().in_({"баланс", "кэш", "б", "бал", "бабки", "📊 статистика"}))
async def show_stats(message: Message):
    user = get_user(message.from_user.id)
    net_profit = user["won_money"] - user["lost_money"]
    profit_from_start = user["balance"] - START_BALANCE
    sign = "📈" if net_profit >= 0 else "📉"
    luck = user.get("luck") if user.get("luck") is not None else GLOBAL_LUCK

    text = (
        f"📊 <b>Статистика — {message.from_user.first_name}</b>\n\n"
        f"💰 <b>Баланс:</b> {user['balance']:,} BTC\n"
        f"🏦 <b>Начальный капитал:</b> {START_BALANCE:,} BTC\n\n"
        f"🎮 <b>Игр:</b> {user['games']}\n"
        f"✅ <b>Побед:</b> {user['wins']}\n"
        f"❌ <b>Проигрышей:</b> {user['losses']}\n\n"
        f"💸 <b>Выиграно:</b> {user['won_money']:,} BTC\n"
        f"🔥 <b>Проиграно:</b> {user['lost_money']:,} BTC\n"
        f"{sign} <b>Профит:</b> {net_profit:,} BTC\n"
        f"📊 <b>Поднял с 1 млн:</b> {profit_from_start:,} BTC\n"
        f"🍀 <b>Твоя удача:</b> {luck}%"
    )
    await message.answer(text, parse_mode="HTML")

# ================= ПРОФИЛЬ =================
@dp.message(F.text == "💼 Профиль")
async def profile(message: Message):
    user = get_user(message.from_user.id)
    status = "👑 Премиум" if user["premium"] else "👤 Обычный"
    max_bet = "1 Триллион" if user["premium"] else "5 Миллионов"
    admin_mark = " | 🛡 Админ" if is_admin(message.from_user.id) else ""
    text = (
        f"💼 <b>Профиль в {BOT_NAME}</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 {message.from_user.first_name}\n"
        f"💰 Баланс: <b>{user['balance']:,} BTC</b>\n"
        f"📊 Статус: {status}{admin_mark}\n"
        f"📈 Лимит ставки: {max_bet}"
    )
    await message.answer(text, parse_mode="HTML")

# ================= МАГАЗИН =================
@dp.message(F.text == "💎 Магазин")
async def shop(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Купить Премиум", callback_data="buy_premium")]
    ])
    await message.answer(
        f"💎 <b>Магазин {BOT_NAME}</b>\n\n👑 <b>Премиум</b> — 5 000 000 BTC\nЛимит ставки: 1 ТРИЛЛИОН BTC",
        reply_markup=kb, parse_mode="HTML"
    )

# ================= РАССЫЛКА (/say) =================
@dp.message(Command("say"))
async def admin_say(message: Message):
    if not is_admin(message.from_user.id):
        return
        
    text_to_send = message.text.replace("/say", "").strip()
    if not text_to_send:
        await message.answer("❌ Напиши текст после команды. Пример:\n<code>/say Привет всем! Заходите играть!</code>", parse_mode="HTML")
        return

    await message.answer(f"⏳ Начинаю рассылку для {len(users_db)} пользователей...")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Играть", url=BOT_LINK)]
    ])

    success = 0
    failed = 0

    for user_id in list(users_db.keys()):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=text_to_send,
                reply_markup=kb,
                parse_mode="HTML"
            )
            success += 1
            await asyncio.sleep(0.05)
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            failed += 1

    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📩 Дошло: {success}\n"
        f"❌ Не дошло: {failed}",
        parse_mode="HTML"
    )

# ================= АДМИН ПАНЕЛЬ =================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет прав.")
        return
    
    is_main = message.from_user.id == MAIN_ADMIN_ID
    admin_cmds = (
        "👑 <b>Управление админами:</b>\n"
        "/setadmin @username или ID — выдать админку\n"
        "/unsetadmin @username или ID — забрать админку\n"
        "/admins — список всех админов\n\n"
    ) if is_main else ""
    
    await message.answer(
        f"👑 <b>Админ-панель {BOT_NAME}</b>\n\n"
        f"{admin_cmds}"
        "💰 <b>Деньги:</b>\n"
        "/give ID СУММА — выдать BTC\n"
        "/take ID СУММА — забрать BTC\n\n"
        "👑 <b>Випка:</b>\n"
        "/premium ID — выдать Премиум\n"
        "/unpremium ID — забрать Премиум\n\n"
        "🍀 <b>Удача:</b>\n"
        "/luck ID ПРОЦЕНТ — подкрутить удачу\n"
        "/setluck ПРОЦЕНТ — удача для всех\n\n"
        "📢 <b>Реклама:</b>\n"
        "/say ТЕКСТ — рассылка всем\n\n"
        f"<i>Глобальная удача: {GLOBAL_LUCK}%</i>\n"
        f"<i>Пользователей в базе: {len(users_db)}</i>",
        parse_mode="HTML"
    )

# ================= УПРАВЛЕНИЕ АДМИНАМИ =================
async def resolve_user_id(target: str) -> int | None:
    if target.startswith("@"):
        try:
            chat = await bot.get_chat(target)
            return chat.id
        except:
            return None
    else:
        try:
            return int(target)
        except:
            return None

@dp.message(Command("setadmin"))
async def cmd_setadmin(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("⛔ Только главный админ может выдавать админку!")
        return
    try:
        _, target = message.text.split()
    except:
        await message.answer("❌ /setadmin @username или ID")
        return
    uid = await resolve_user_id(target)
    if not uid:
        await message.answer("❌ Не нашёл такого пользователя. Пусть он сначала напишет боту /start.")
        return
    if uid in admins_list:
        await message.answer("ℹ️ Он уже админ.")
        return
    admins_list.append(uid)
    get_user(uid)
    await message.answer(f"✅ <b>{target}</b> теперь админ! У него есть все твои функции.", parse_mode="HTML")

@dp.message(Command("unsetadmin"))
async def cmd_unsetadmin(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        await message.answer("⛔ Только главный админ может снимать админку!")
        return
    try:
        _, target = message.text.split()
    except:
        await message.answer("❌ /unsetadmin @username или ID")
        return
    uid = await resolve_user_id(target)
    if not uid:
        await message.answer("❌ Не нашёл такого пользователя.")
        return
    if uid == MAIN_ADMIN_ID:
        await message.answer("❌ Нельзя снять с себя главную админку!")
        return
    if uid in admins_list:
        admins_list.remove(uid)
        await message.answer(f"✅ С <b>{target}</b> снята админка.", parse_mode="HTML")
    else:
        await message.answer("ℹ️ Он и так не админ.")

@dp.message(Command("admins"))
async def cmd_admins_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    text = "👑 <b>Список админов:</b>\n\n"
    for i, uid in enumerate(admins_list, 1):
        try:
            info = await bot.get_chat(uid)
            name = info.first_name
            username = f" (@{info.username})" if info.username else ""
        except:
            name = "Неизвестный"
            username = ""
        role = " 👑 ГЛАВНЫЙ" if uid == MAIN_ADMIN_ID else ""
        text += f"{i}. <b>{name}</b>{username}{role}\n🆔 <code>{uid}</code>\n\n"
    await message.answer(text, parse_mode="HTML")

# ================= ДЕНЬГИ / ВИП / УДАЧА =================
@dp.message(Command("give"))
async def admin_give(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _, tid, amt_text = message.text.split()
        tid = int(tid); amount = parse_money(amt_text)
        if amount is None: raise ValueError
    except:
        await message.answer("❌ /give ID СУММА")
        return
    get_user(tid)["balance"] += amount
    await message.answer(f"✅ Выдано {amount:,} BTC → {tid}")

@dp.message(Command("take"))
async def admin_take(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _, tid, amt_text = message.text.split()
        tid = int(tid); amount = parse_money(amt_text)
        if amount is None: raise ValueError
    except:
        await message.answer("❌ /take ID СУММА")
        return
    get_user(tid)["balance"] -= amount
    await message.answer(f"✅ Забрано {amount:,} BTC у {tid}")

@dp.message(Command("premium"))
async def admin_premium(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _, tid = message.text.split()
        tid = int(tid)
    except:
        await message.answer("❌ /premium ID")
        return
    get_user(tid)["premium"] = True
    await message.answer(f"✅ Юзеру {tid} выдан 👑 Премиум")

@dp.message(Command("unpremium"))
async def admin_unpremium(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _, tid = message.text.split()
        tid = int(tid)
    except:
        await message.answer("❌ /unpremium ID")
        return
    get_user(tid)["premium"] = False
    await message.answer(f"✅ У юзера {tid} забрали Премиум")

@dp.message(Command("luck"))
async def admin_luck(message: Message):
    if not is_admin(message.from_user.id): return
    try:
        _, tid, luck_str = message.text.split()
        tid = int(tid); luck = int(luck_str)
        if not (1 <= luck <= 100): raise ValueError
    except:
        await message.answer("❌ /luck ID ПРОЦЕНТ (от 1 до 100)")
        return
    get_user(tid)["luck"] = luck
    await message.answer(f"🍀 Удача игрока {tid} установлена на <b>{luck}%</b>", parse_mode="HTML")

@dp.message(Command("setluck"))
async def admin_setluck(message: Message):
    global GLOBAL_LUCK
    if not is_admin(message.from_user.id): return
    try:
        _, luck_str = message.text.split()
        luck = int(luck_str)
        if not (1 <= luck <= 100): raise ValueError
    except:
        await message.answer("❌ /setluck ПРОЦЕНТ (от 1 до 100)")
        return
    GLOBAL_LUCK = luck
    await message.answer(f"🌍 Глобальная удача для всех: <b>{luck}%</b>", parse_mode="HTML")

# ================= ЗАПУСК =================
async def main():
    print(f"Бот {BOT_NAME} запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())