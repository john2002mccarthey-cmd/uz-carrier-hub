
import asyncio, csv, io, os, sqlite3
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()}
DB = os.getenv("DB_PATH", "carriers.sqlite3")
dp = Dispatcher()
LANG = {}

T = {
"uz": ["Tilni tanlang", "UZ CARRIER HUB'ga xush kelibsiz! 🚛 /register orqali transportni ro‘yxatdan o‘tkazing.",
"Ism-familiyangiz:", "Telefon raqamingiz:", "Kim sifatida? (Truck owner / Company / Driver)",
"Kompaniya nomi (bo‘lmasa -):", "Transport turi (Gazel, Isuzu, Fura, Reefer, Flatbed...)",
"Yuk ko‘tarish quvvati (tonna):", "Kuzov turi (tent, ref, bort, izoterm...)",
"Hozirgi joylashuv (shahar/davlat):", "Ishlaydigan yo‘nalishlar:", "Qachon bo‘sh bo‘lasiz?",
"Qo‘shimcha ma’lumot (ixtiyoriy, bo‘lmasa -):", "✅ Arizangiz qabul qilindi. Admin tekshiruvini kuting.",
"Bekor qilindi.", "Faqat admin uchun.", "Buyruqlar: /register /cancel /lang /help\nAdmin: /stats /pending /search so‘z /export"],
"ru": ["Выберите язык", "Добро пожаловать в UZ CARRIER HUB! 🚛 Для регистрации отправьте /register.",
"Имя и фамилия:", "Номер телефона:", "Кем регистрируетесь? (Владелец / Компания / Водитель)",
"Название компании (если нет — -):", "Тип транспорта (Газель, Isuzu, фура, реф, платформа...)",
"Грузоподъёмность (тонн):", "Тип кузова:", "Текущее местоположение:", "Рабочие маршруты:",
"Когда будете свободны?", "Дополнительная информация (необязательно, иначе -):",
"✅ Заявка принята. Ожидайте проверки администратора.", "Отменено.", "Только для администратора.",
"Команды: /register /cancel /lang /help\nАдмин: /stats /pending /search слово /export"],
"en": ["Choose language", "Welcome to UZ CARRIER HUB! 🚛 Send /register to register your vehicle.",
"Full name:", "Phone number:", "Registering as? (Truck owner / Company / Driver)",
"Company name (or -):", "Vehicle type (Gazel, Isuzu, Truck, Reefer, Flatbed...)",
"Payload capacity (tons):", "Body type:", "Current location (city/country):", "Operating routes:",
"When available?", "Additional notes (optional, or -):",
"✅ Registration received. Please wait for admin verification.", "Cancelled.", "Admin only.",
"Commands: /register /cancel /lang /help\nAdmin: /stats /pending /search term /export"]
}
FIELDS = ["full_name","phone","carrier_type","company","truck_type","capacity","body_type","location","routes","availability","notes"]
class Form(StatesGroup):
    full_name=State(); phone=State(); carrier_type=State(); company=State(); truck_type=State()
    capacity=State(); body_type=State(); location=State(); routes=State(); availability=State(); notes=State()

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS carriers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        telegram_id INTEGER UNIQUE, username TEXT, language TEXT, full_name TEXT, phone TEXT,
        carrier_type TEXT, company TEXT, truck_type TEXT, capacity TEXT, body_type TEXT,
        location TEXT, routes TEXT, availability TEXT, notes TEXT, status TEXT DEFAULT 'pending')""")

def tr(uid, i): return T[LANG.get(uid,"uz")][i]
def is_admin(uid): return uid in ADMINS
def record(cid):
    with db() as c: return c.execute("SELECT * FROM carriers WHERE id=?", (cid,)).fetchone()
def card(r):
    return (f"#{r['id']} | {r['status']}\n{r['full_name']} | {r['phone']}\n"
    f"{r['carrier_type']} | {r['company']}\n{r['truck_type']} | {r['capacity']} t | {r['body_type']}\n"
    f"Location: {r['location']}\nRoutes: {r['routes']}\nAvailable: {r['availability']}\n"
    f"Telegram: @{r['username'] or '-'}\nNotes: {r['notes']}")

@dp.message(CommandStart())
async def start(m):
    kb=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 O‘zbekcha",callback_data="lang:uz")],
        [InlineKeyboardButton(text="🇷🇺 Русский",callback_data="lang:ru")],
        [InlineKeyboardButton(text="🇬🇧 English",callback_data="lang:en")]])
    await m.answer(T["uz"][0], reply_markup=kb)

@dp.callback_query(F.data.startswith("lang:"))
async def setlang(c):
    LANG[c.from_user.id]=c.data.split(":")[1]
    await c.message.answer(tr(c.from_user.id,1)); await c.answer()

@dp.message(Command("lang"))
async def lang_cmd(m): await start(m)

@dp.message(Command("help"))
async def help_cmd(m): await m.answer(tr(m.from_user.id,15))

@dp.message(Command("register"))
async def register(m,s):
    await s.clear(); await s.set_state(Form.full_name); await m.answer(tr(m.from_user.id,2))

async def next_step(m,s,field,next_state,index):
    await s.update_data(**{field:m.text or ""})
    await s.set_state(next_state); await m.answer(tr(m.from_user.id,index))

@dp.message(Form.full_name)
async def f1(m,s): await next_step(m,s,"full_name",Form.phone,3)
@dp.message(Form.phone)
async def f2(m,s): await next_step(m,s,"phone",Form.carrier_type,4)
@dp.message(Form.carrier_type)
async def f3(m,s): await next_step(m,s,"carrier_type",Form.company,5)
@dp.message(Form.company)
async def f4(m,s): await next_step(m,s,"company",Form.truck_type,6)
@dp.message(Form.truck_type)
async def f5(m,s): await next_step(m,s,"truck_type",Form.capacity,7)
@dp.message(Form.capacity)
async def f6(m,s): await next_step(m,s,"capacity",Form.body_type,8)
@dp.message(Form.body_type)
async def f7(m,s): await next_step(m,s,"body_type",Form.location,9)
@dp.message(Form.location)
async def f8(m,s): await next_step(m,s,"location",Form.routes,10)
@dp.message(Form.routes)
async def f9(m,s): await next_step(m,s,"routes",Form.availability,11)
@dp.message(Form.availability)
async def f10(m,s): await next_step(m,s,"availability",Form.notes,12)

@dp.message(Form.notes)
async def finish(m,s,bot):
    await s.update_data(notes="" if m.text=="-" else (m.text or ""))
    d=await s.get_data()
    vals=[m.from_user.id,m.from_user.username or "",LANG.get(m.from_user.id,"uz")]+[d.get(k,"") for k in FIELDS]
    with db() as c:
        cur=c.execute("""INSERT INTO carriers
        (telegram_id,username,language,full_name,phone,carrier_type,company,truck_type,capacity,body_type,location,routes,availability,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username,language=excluded.language,
        full_name=excluded.full_name,phone=excluded.phone,carrier_type=excluded.carrier_type,
        company=excluded.company,truck_type=excluded.truck_type,capacity=excluded.capacity,
        body_type=excluded.body_type,location=excluded.location,routes=excluded.routes,
        availability=excluded.availability,notes=excluded.notes,status='pending'""",vals)
        cid=c.execute("SELECT id FROM carriers WHERE telegram_id=?",(m.from_user.id,)).fetchone()["id"]
    await s.clear(); await m.answer(tr(m.from_user.id,13))
    r=record(cid); buttons=InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Verify",callback_data=f"verify:{cid}"),
        InlineKeyboardButton(text="❌ Reject",callback_data=f"reject:{cid}")]])
    for aid in ADMINS:
        try: await bot.send_message(aid,"🆕 New carrier application\n"+card(r),reply_markup=buttons)
        except Exception: pass

@dp.message(Command("cancel"))
async def cancel(m,s): await s.clear(); await m.answer(tr(m.from_user.id,14))

@dp.callback_query(F.data.startswith(("verify:","reject:")))
async def moderate(c):
    if not is_admin(c.from_user.id): return await c.answer("Admin only",show_alert=True)
    action,cid=c.data.split(":"); status="verified" if action=="verify" else "rejected"
    with db() as con: con.execute("UPDATE carriers SET status=? WHERE id=?",(status,int(cid)))
    await c.message.edit_reply_markup(reply_markup=None); await c.answer("Updated")
    try:
        r=record(int(cid))
        await c.bot.send_message(r["telegram_id"], f"Carrier profile status: {status}")
    except Exception: pass

@dp.message(Command("stats"))
async def stats_cmd(m):
    if not is_admin(m.from_user.id): return await m.answer(tr(m.from_user.id,14))
    with db() as c:
        total=c.execute("SELECT COUNT(*) n FROM carriers").fetchone()["n"]
        pending=c.execute("SELECT COUNT(*) n FROM carriers WHERE status='pending'").fetchone()["n"]
        verified=c.execute("SELECT COUNT(*) n FROM carriers WHERE status='verified'").fetchone()["n"]
    await m.answer(f"Total: {total}\nPending: {pending}\nVerified: {verified}")

@dp.message(Command("pending"))
async def pending(m):
    if not is_admin(m.from_user.id): return await m.answer(tr(m.from_user.id,14))
    with db() as c: rows=c.execute("SELECT * FROM carriers WHERE status='pending' ORDER BY id DESC LIMIT 30").fetchall()
    if not rows: return await m.answer("No pending applications.")
    for r in rows: await m.answer(card(r))

@dp.message(Command("search"))
async def search(m):
    if not is_admin(m.from_user.id): return await m.answer(tr(m.from_user.id,14))
    term=m.text.partition(" ")[2].strip()
    if not term: return await m.answer("Usage: /search <name, phone, truck, city, route>")
    q=f"%{term}%"
    with db() as c:
        rows=c.execute("""SELECT * FROM carriers WHERE full_name LIKE ? OR phone LIKE ? OR company LIKE ?
        OR truck_type LIKE ? OR location LIKE ? OR routes LIKE ? ORDER BY id DESC LIMIT 30""",(q,q,q,q,q,q)).fetchall()
    if not rows: return await m.answer("No matches.")
    for r in rows: await m.answer(card(r))

@dp.message(Command("export"))
async def export(m):
    if not is_admin(m.from_user.id): return await m.answer(tr(m.from_user.id,14))
    with db() as c: rows=c.execute("SELECT * FROM carriers ORDER BY id DESC").fetchall()
    out=io.StringIO(); w=csv.writer(out)
    if rows:
        w.writerow(rows[0].keys())
        for r in rows: w.writerow(list(r))
    await m.answer_document(BufferedInputFile(out.getvalue().encode("utf-8-sig"),filename="uz_carrier_hub.csv"))

async def main():
    if not TOKEN: raise RuntimeError("Set BOT_TOKEN in .env")
    init(); await dp.start_polling(Bot(TOKEN))

if __name__=="__main__": asyncio.run(main())
