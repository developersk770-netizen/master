# -- coding: utf-8 --

import re
import sqlite3
import requests
import telebot
import time
from telebot import types

# ========== CONFIG ==========
BOT_TOKEN = "8457140301:AAHsDW1kFwgc0_JlJ8J2gjXhyAWAM-cu36M"  # apna token daalna
ADMIN_ID = 7637712605              # apna telegram ID daalna
DB_FILE = "users.db"
BOT_PASSWORD = "12345678"             # 🔑 yaha apna strong password daalo

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ========== DB SETUP ==========
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
user_id INTEGER PRIMARY KEY,
credits INTEGER DEFAULT 5
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS history (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
query TEXT,
api_type TEXT,
ts DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ========== HELPERS ==========
def init_user(uid: int):
    cur.execute("INSERT OR IGNORE INTO users (user_id, credits) VALUES (?, 5)", (uid,))
    conn.commit()

def get_credits(uid: int) -> int:
    cur.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    return row[0] if row else 0

def set_credits(uid: int, val: int):
    cur.execute("UPDATE users SET credits=? WHERE user_id=?", (val, uid))
    conn.commit()

def change_credits(uid: int, delta: int):
    init_user(uid)
    cur.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    cur_ = row[0] if row else 0
    new = max(0, cur_ + delta)
    cur.execute("UPDATE users SET credits=? WHERE user_id=?", (new, uid))
    conn.commit()
    return new

def add_history(uid: int, query: str, api_type: str):
    cur.execute("INSERT INTO history (user_id, query, api_type) VALUES (?, ?, ?)", (uid, query, api_type))
    conn.commit()

def get_all_users():
    cur.execute("SELECT user_id FROM users")
    return [r[0] for r in cur.fetchall()]

def send_long(chat_id: int, text: str, reply_to: int = None):
    MAX = 4000
    if len(text) <= MAX:
        bot.send_message(chat_id, text, reply_to_message_id=reply_to)
        return
    parts = [text[i:i+MAX] for i in range(0, len(text), MAX)]
    for p in parts:
        bot.send_message(chat_id, p, reply_to_message_id=reply_to)

def clean(s):
    if s is None:
        return "N/A"
    s = str(s).replace("\u200b", "").strip()
    return re.sub(r"\s+", " ", s)

def ensure_and_charge(uid: int, chat_id: int) -> bool:
    init_user(uid)
    credits = get_credits(uid)
    if credits <= 0:
        bot.send_message(chat_id, "❌ <b>No credits left.</b>\nContact admin to recharge.")
        return False
    set_credits(uid, credits - 1)
    return True

def is_admin(uid: int) -> bool:
    return uid == ADMIN_ID

# ========== START ==========
@bot.message_handler(commands=["start"])
def cmd_start(m):
    bot.send_message(m.chat.id, "🔑 Please enter password to access bot:")
    bot.register_next_step_handler(m, check_password)

def check_password(m):
    if m.text.strip() == BOT_PASSWORD:
        uid = m.from_user.id
        init_user(uid)
        credits = get_credits(uid)

        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)  
        kb.row("🇮🇳 India Number Info", "🇵🇰 Pakistan Number Info")  
        kb.row("📮 Pincode Info", "🚘 Vehicle Info")  
        kb.row("🆔 Aadhaar Info")  
        kb.row("💳 My Credits", "📞 Contact Admin")  
        kb.row("🆔 My ID")  
        kb.row("🇵🇰 CNIC INFO")   # 🆕 Added new button
        if is_admin(uid):  
            kb.row("⚙️ Admin Panel")  

        start_text = f"""
━━━━━━━━━━━━━━━━━━
🤖 <b>InfoBot</b>  
<i>Your Digital Info Assistant 🚀</i>
━━━━━━━━━━━━━━━━━━

🔍 <b>Available Services:</b>  
🇮🇳 India Number Info  
🇵🇰 Pakistan Number Info  
🇵🇰 CNIC Info  
📮 Pincode Details  
🚘 Vehicle Info  
🆔 Aadhaar Info  

💳 <b>Your Credits:</b> <code>{credits}</code>  

⚠️ Each search costs <b>1 credit</b>.  
For recharge, please contact admin.  

✅ <b>Choose an option below to begin!</b>

━━━━━━━━━━━━━━━━━━  
© 2025 <b>InfoBot</b> | All Rights Reserved  
📞 <a href="tg://user?id={ADMIN_ID}">Contact Admin</a>  
━━━━━━━━━━━━━━━━━━
"""
        bot.send_message(m.chat.id, start_text, reply_markup=kb, disable_web_page_preview=True)
    else:
        bot.send_message(m.chat.id, "❌ ACESS DENIED PLZ CONTACT TO ADMIN FOR CORRECT PASSWORD @IG_BANZ ")

# ========== MY ID ==========
@bot.message_handler(commands=["myid"])
def cmd_myid(m):
    bot.reply_to(m, f"🆔 Your Telegram ID: <code>{m.from_user.id}</code>")

@bot.message_handler(func=lambda c: c.text == "🆔 My ID")
def btn_myid(m):
    bot.send_message(m.chat.id, f"🆔 Your Telegram ID: <code>{m.from_user.id}</code>")

# ========== MAIN MENU ==========
@bot.message_handler(func=lambda c: c.text == "📞 Contact Admin")
def contact_admin_btn(m):
    bot.send_message(m.chat.id,
        f"📞 Contact Admin: <a href='tg://user?id={ADMIN_ID}'>Admin</a>",
        disable_web_page_preview=True)

@bot.message_handler(func=lambda c: c.text == "💳 My Credits")
def my_credits_btn(m):
    bot.send_message(m.chat.id, f"💳 Your Credits: <b>{get_credits(m.from_user.id)}</b>")

# ========= Shortcuts =========
@bot.message_handler(func=lambda c: c.text == "🇮🇳 India Number Info")
def ask_number(m):
    bot.send_message(m.chat.id,"📲 Send 10-digit Indian number:")
    bot.register_next_step_handler(m, handle_number)

@bot.message_handler(func=lambda c: c.text == "🇵🇰 Pakistan Number Info")
def ask_pak_number(m):
    bot.send_message(m.chat.id,"📲 Send Pakistan number with country code (923XXXXXXXXX):")
    bot.register_next_step_handler(m, handle_pak_number)

@bot.message_handler(func=lambda c: c.text == "📮 Pincode Info")
def ask_pincode(m):
    bot.send_message(m.chat.id,"🏤 Send 6-digit pincode:")
    bot.register_next_step_handler(m, handle_pincode)

@bot.message_handler(func=lambda c: c.text == "🚘 Vehicle Info")
def ask_vehicle(m):
    bot.send_message(m.chat.id,"🚗 Send vehicle number:")
    bot.register_next_step_handler(m, handle_vehicle)

@bot.message_handler(func=lambda c: c.text == "🆔 Aadhaar Info")
def ask_aadhar(m):
    bot.send_message(m.chat.id,"🆔 Send 12-digit Aadhaar number:")
    bot.register_next_step_handler(m, handle_aadhar)

@bot.message_handler(func=lambda c: c.text == "🇵🇰 CNIC INFO")
def ask_cnic(m):
    bot.send_message(m.chat.id,"🆔 Send 13-digit CNIC number:")
    bot.register_next_step_handler(m, handle_cnic)

# ========= HANDLERS =========
def handle_number(m):
    uid = m.from_user.id
    num = m.text.strip()
    if not re.fullmatch(r"\d{10}", num):
        return bot.send_message(m.chat.id, "⚠️ Invalid 10-digit number.")
    if not ensure_and_charge(uid, m.chat.id): return
    try:
        resp = requests.get(f"https://private-9e6q.onrender.com/search/?q={num}", timeout=30).json()
        records = resp.get("results", [])
        if not records: return bot.send_message(m.chat.id, "📭 No Information Found!")
        for rec in records:
            out = f"""
👤 Name: {clean(rec.get('name'))}
👨‍👩‍👦 Father: {clean(rec.get('father_name'))}
📱 Mobile: {clean(rec.get('mobile'))}
📞 ALT : {clean(rec.get('alternate_mobile'))}
📧 Email: {clean(rec.get('email'))}
🆔 Aadhaar: {clean(rec.get('aadhar'))}
🌍 Circle: {clean(rec.get('circle'))}
🏠 Address: {clean(rec.get('address'))}
"""
            bot.send_message(m.chat.id, out)
        add_history(uid, num, "NUMBER")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{e}</code>")

def handle_aadhar(m):
    uid = m.from_user.id
    aid = m.text.strip()
    if not re.fullmatch(r"\d{12}", aid):
        return bot.send_message(m.chat.id, "⚠️ Invalid Aadhaar number.")
    if not ensure_and_charge(uid, m.chat.id): return
    try:
        resp = requests.get(f"https://private-9e6q.onrender.com/search/?q={aid}", timeout=30).json()
        records = resp.get("results", [])
        if not records: return bot.send_message(m.chat.id, "📭 No Aadhaar Data Found!")
        for rec in records:
            out = f"""
👤 Name: {clean(rec.get('name'))}
👨‍👩‍👦 Father: {clean(rec.get('father_name'))}
🎂 DOB: {clean(rec.get('dob'))}
🆔 Aadhaar: {clean(rec.get('aadhar'))}
📱 Mobile: {clean(rec.get('mobile'))}
📞 ALT : {clean(rec.get('alternate_mobile'))}
📧 Email: {clean(rec.get('email'))}
🏠 Address: {clean(rec.get('address'))}
"""
            bot.send_message(m.chat.id, out)
        add_history(uid, aid, "AADHAAR")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{e}</code>")

def handle_pak_number(m):
    uid = m.from_user.id
    num = m.text.strip()
    if not re.fullmatch(r"923\d{9}", num):
        return bot.send_message(m.chat.id, "⚠️ Invalid Pakistan number.")
    if not ensure_and_charge(uid, m.chat.id): return
    try:
        resp = requests.get(f"https://allnetworkdata.com/?number={num}", timeout=20).json()
        if not resp: return bot.send_message(m.chat.id, "❌ No data found.")
        out = f"""
👤 Name: {clean(resp.get('name'))}
🆔 CNIC: {clean(resp.get('cnic'))}
🏠 Address: {clean(resp.get('address'))}
📞 Numbers: {", ".join(resp.get('numbers', []))}
"""
        bot.send_message(m.chat.id, out)
        add_history(uid, num, "PAK_NUMBER")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{e}</code>")

def handle_pincode(m):
    uid = m.from_user.id
    pin = m.text.strip()
    if not re.fullmatch(r"\d{6}", pin):
        return bot.send_message(m.chat.id,"⚠️ Invalid pincode.")
    if not ensure_and_charge(uid, m.chat.id): return
    try:
        res = requests.get(f"https://pincode-info-j4tnx.vercel.app/pincode={pin}",timeout=20).json()
        offices = res[0].get("PostOffice", []) if res else []
        if not offices: return bot.send_message(m.chat.id,"❌ No pincode data.")
        blocks = [f"🏢 {po['Name']}\n📍 {po['District']}, {po['State']}\n📮 {po['Pincode']}" for po in offices]
        send_long(m.chat.id, f"📮 Pincode Info {pin}\n\n" + "\n\n".join(blocks))
        add_history(uid,pin,"PINCODE")
    except Exception as e:
        bot.send_message(m.chat.id,f"⚠️ Error: <code>{e}</code>")

def handle_vehicle(m):
    uid = m.from_user.id
    rc = m.text.strip().upper()
    if not ensure_and_charge(uid, m.chat.id):
        return
    try:
        url = f"https://rc-info-ng.vercel.app/?rc={rc}"
        r = requests.get(url, timeout=20).json()
        if not isinstance(r, dict) or not r:
            bot.send_message(m.chat.id, "❌ No vehicle data found.")
            return
        fields = {
            "RC Number": r.get("rc_number"),
            "Owner": r.get("owner_name"),
            "Father": r.get("father_name"),
            "Owner Serial No": r.get("owner_serial_no"),
            "Model Name": r.get("model_name"),
            "Maker Model": r.get("maker_model"),
            "Vehicle Class": r.get("vehicle_class"),
            "Fuel Type": r.get("fuel_type"),
            "Registration Date": r.get("registration_date"),
            "Insurance Company": r.get("insurance_company"),
            "Insurance No": r.get("insurance_no"),
            "Insurance Expiry": r.get("insurance_expiry") or r.get("insurance_upto"),
            "Fitness Upto": r.get("fitness_upto"),
            "Tax Upto": r.get("tax_upto"),
            "PUC No": r.get("puc_no"),
            "Financier": r.get("financier_name"),
            "RTO": r.get("rto"),
            "Address": r.get("address"),
            "City": r.get("city"),
            "Phone": r.get("phone"),
        }
        lines = ["🚘 <b>Vehicle Info</b>\n━━━━━━━━━━━━━━"]
        for k, v in fields.items():
            lines.append(f"• <b>{k}:</b> {clean(v)}")
        out = "\n".join(lines)
        send_long(m.chat.id, out, reply_to=m.message_id)
        add_history(uid, rc, "VEHICLE")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Error fetching vehicle info.\n<code>{e}</code>")

def handle_cnic(m):
    uid = m.from_user.id
    cnic = m.text.strip()
    if not re.fullmatch(r"\d{13}", cnic):
        return bot.send_message(m.chat.id, "⚠️ Invalid CNIC number (must be 13 digits).")
    if not ensure_and_charge(uid, m.chat.id): return
    try:
        resp = requests.get(f"https://allnetworkdata.com/?number={cnic}", timeout=20).json()
        if not resp: return bot.send_message(m.chat.id, "❌ No CNIC data found.")
        out = f"""
👤 Name: {clean(resp.get('name'))}
🆔 CNIC: {clean(resp.get('cnic'))}
🏠 Address: {clean(resp.get('address'))}
📞 Numbers: {", ".join(resp.get('numbers', []))}
"""
        bot.send_message(m.chat.id, out)
        add_history(uid, cnic, "CNIC")
    except Exception as e:
        bot.send_message(m.chat.id, f"⚠️ Error: <code>{e}</code>")

# ========= Admin Panel =========
@bot.message_handler(func=lambda c: c.text=="⚙️ Admin Panel")
def admin_panel(m):
    if not is_admin(m.from_user.id): return
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👤 All Users","📜 User History")
    kb.row("➕ Add Credit","➖ Remove Credit")
    kb.row("📢 Broadcast","⬅️ Back")
    bot.send_message(m.chat.id,"⚙️ Admin Panel",reply_markup=kb)

@bot.message_handler(func=lambda c: c.text=="⬅️ Back")
def back_btn(m): cmd_start(m)

@bot.message_handler(func=lambda c: c.text=="👤 All Users")
def all_users_btn(m):
    if not is_admin(m.from_user.id): return
    cur.execute("SELECT user_id, credits FROM users"); rows=cur.fetchall()
    out="📋 Users:\n" + "\n".join([f"{u} — 💳 {c}" for u,c in rows])
    send_long(m.chat.id,out)

@bot.message_handler(func=lambda c: c.text=="➕ Add Credit")
def add_credit_btn(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id,"Format: user_id credits")
    bot.register_next_step_handler(m,process_add_credit)

def process_add_credit(m):
    try: uid,amt=map(int,m.text.split()); new=change_credits(uid,amt); bot.send_message(m.chat.id,f"✅ Added {amt}. Now {new}")
    except: bot.send_message(m.chat.id,"❌ Invalid format.")

@bot.message_handler(func=lambda c: c.text=="➖ Remove Credit")
def rem_credit_btn(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id,"Format: user_id credits")
    bot.register_next_step_handler(m,process_rem_credit)

def process_rem_credit(m):
    try: uid,amt=map(int,m.text.split()); new=change_credits(uid,-amt); bot.send_message(m.chat.id,f"✅ Removed {amt}. Now {new}")
    except: bot.send_message(m.chat.id,"❌ Invalid format.")

@bot.message_handler(func=lambda c: c.text=="📜 User History")
def history_btn(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id,"📜 Send user_id to fetch history:")
    bot.register_next_step_handler(m,process_history)

def process_history(m):
    try:
        uid=int(m.text.strip())
        cur.execute("SELECT query, api_type, ts FROM history WHERE user_id=? ORDER BY id DESC LIMIT 20",(uid,))
        rows=cur.fetchall()
        if not rows:
            return bot.send_message(m.chat.id,"❌ No history found.")
        out="📜 Last 20 queries:\n\n"
        for q,t,ts in rows:
            out+=f"[{ts}] ({t}) {q}\n"
        send_long(m.chat.id,out)
    except:
        bot.send_message(m.chat.id,"❌ Invalid user id.")

@bot.message_handler(func=lambda c: c.text=="📢 Broadcast")
def broadcast_btn(m):
    if not is_admin(m.from_user.id): return
    bot.send_message(m.chat.id,"📢 Send broadcast message:")
    bot.register_next_step_handler(m,process_broadcast)

def process_broadcast(m):
    if not is_admin(m.from_user.id): return
    users=get_all_users(); sent=0; fail=0
    for u in users:
        try:
            bot.send_message(u,m.text)
            sent+=1
            time.sleep(0.05)
        except:
            fail+=1
    bot.send_message(m.chat.id,f"✅ Broadcast done.\nSent: {sent}, Failed: {fail}")

# ========= POLLING =========
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)