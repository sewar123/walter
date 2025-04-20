import telebot
from telebot import types
import json
import os
from datetime import datetime
from datetime import datetime, timedelta


# === إعدادات البوت === #
BOT_TOKEN = '7991613561:AAFX9blq_hkr5Pq-AKlooDSqjr4EwPjZPL4'
CHANNEL_USERNAME = '@sewar1bot1'
ADMIN_IDS = [5504502257]  # عدّل حسب آيدي الأدمن الحقيقي
bot_username = 'sewar1bot'
CASH_CODE_FILE = 'cash_code.txt'
DATA_FILE = 'users.json'
GIFT_CODES_FILE = 'gift_codes.json'
WITHDRAW_FILE    = 'withdraw_requests.json'
USER_INFO_FILE  = 'user_info.json'   # ← هنا أضفنا تعريف الملف الخاص بمعلومات المستخدم
# === ملف ثابت لحفظ حسابات Ichancy === #
ICHANCY_ACCOUNTS_FILE = 'ichancy_accounts.json'


ichancy_requests = {}  # user_id -> {"name": ..., "password": ...}
ichancy_accounts = {}  # user_id -> {"name": ..., "password": ...}

bot = telebot.TeleBot(BOT_TOKEN)

# === تحميل بيانات المستخدمين === #
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

# === تحميل أكواد الجوائز === #
def load_gift_codes():
    if not os.path.exists(GIFT_CODES_FILE):
        return {}
    with open(GIFT_CODES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_gift_codes(codes):
    with open(GIFT_CODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(codes, f, ensure_ascii=False, indent=2)

gift_codes = load_gift_codes()

def load_ichancy_accounts():
    if os.path.exists(ICHANCY_ACCOUNTS_FILE):
        with open(ICHANCY_ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_ichancy_accounts():
    with open(ICHANCY_ACCOUNTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(ichancy_accounts, f, ensure_ascii=False, indent=2)

# === طلبات ومعلومات Ichancy === #
ichancy_requests = {}  # مؤقت: user_id -> {step, data}
ichancy_accounts = load_ichancy_accounts()  # user_id -> {name, password}


#########


###########


# === تحميل كود الكاش === #
def get_cash_code():
    if not os.path.exists(CASH_CODE_FILE):
        return "02600273"
    with open(CASH_CODE_FILE, 'r') as f:
        return f.read().strip()
    

# === تحميل طلبات السحب === #
if os.path.exists(WITHDRAW_FILE):
    with open(WITHDRAW_FILE, 'r', encoding='utf-8') as f:
        withdraw_requests = json.load(f)
else:
    withdraw_requests = {}

# === تحميل معلومات المستخدمين (رقم سيرياتيل كاش وتاريخ التحديث) === #
if os.path.exists(USER_INFO_FILE):
    with open(USER_INFO_FILE, 'r', encoding='utf-8') as f:
        user_info = json.load(f)
else:
    user_info = {}

# === دوال حفظ البيانات === #
def save_withdraw_requests():
    with open(WITHDRAW_FILE, 'w', encoding='utf-8') as f:
        json.dump(withdraw_requests, f, ensure_ascii=False, indent=2)

def save_user_info():
    with open(USER_INFO_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_info, f, ensure_ascii=False, indent=2)


def log_user_transaction(uid, action, amount, details=""):
    uid = str(uid)
    users[uid] = users.get(uid, {})
    users[uid]["transactions"] = users[uid].get("transactions", [])
    users[uid]["transactions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "action": action,
        "amount": amount,
        "details": details
    })
    save_users(users)

# === تعديل كود الكاش === #
@bot.message_handler(commands=['setcode'])
def set_cash_code(message):
    if message.from_user.id in ADMIN_IDS:
        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            new_code = parts[1]
            with open(CASH_CODE_FILE, 'w') as f:
                f.write(new_code)
            for uid in users:
                try:
                    bot.send_message(int(uid), f"📢 تم تغيير كود شحن سيرياتيل كاش إلى: {new_code}")
                except:
                    continue
            bot.reply_to(message, "✅ تم تحديث الكود وإبلاغ المستخدمين.")
        else:
            bot.reply_to(message, "❗ استخدم الأمر كالتالي:\n`/setcode 12345678`", parse_mode='Markdown')

users = load_users()
pending_requests = {}  # user_id -> {step, data}

# === التحقق من الاشتراك بالقناة === #
def is_user_subscribed(user_id):
    try:
        status = bot.get_chat_member(CHANNEL_USERNAME, user_id).status
        return status in ['member', 'creator', 'administrator']
    except:
        return False

# === القائمة الرئيسية === #
def main_menu(user_id):
    recharge = users.get(str(user_id), {}).get('balance', 0)
    msg = f"""🔹 القائمة الرئيسية:
رصيدك في البوت: {recharge} ل.س
رقم الايدي الخاص بك: {user_id}"""

    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("شحن وسحب حساب Ichancy ⚡️", callback_data="شحن_ايشانسي"))
    markup.row(
        types.InlineKeyboardButton("شحن البوت 📥", callback_data="شحن"),
        types.InlineKeyboardButton("سحب حوالة 📤", callback_data="سحب")
    )
    markup.row(types.InlineKeyboardButton("معلومات الملف الشخصي 🧍", callback_data="معلومات"))
    markup.row(
        types.InlineKeyboardButton("🎁 إهداء رصيد", callback_data="إهداء"),
        types.InlineKeyboardButton("أكواد الجوائز 🏆", callback_data="جوائز")
    )
    markup.row(
        types.InlineKeyboardButton("تواصل مع الدعم الفني 📨", callback_data="دعم"),
        types.InlineKeyboardButton("طلب استرداد حوالة 🔄", callback_data="استرداد")
    )
    markup.row(types.InlineKeyboardButton("برنامج الإحالات 👥", callback_data="إحالات"))
    markup.row(
        types.InlineKeyboardButton("نصائح 🎰", callback_data="نصائح"),
        types.InlineKeyboardButton("دليل الاستخدام 📖", callback_data="دليل")
    )
    markup.row(types.InlineKeyboardButton("عرض السجل المالي 🗃", callback_data="سجل"))

    # ✅ إذا كان مشرف أضف زر لوحة التحكم
    if int(user_id) in ADMIN_IDS:
        markup.row(types.InlineKeyboardButton("🛠 لوحة التحكم", callback_data="لوحة_التحكم"))

    return msg, markup

# === زر الاشتراك في القناة === #
def subscribe_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ انضمام للقناة", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}"))
    return markup

# === /start === #
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    args = message.text.split(maxsplit=1)
    referred_by = args[1] if len(args) > 1 else None

    if not is_user_subscribed(message.from_user.id):
        bot.send_message(
            message.chat.id,
            f"📢 يجب الاشتراك بقناتنا لاستخدام البوت:\n{CHANNEL_USERNAME}",
            reply_markup=subscribe_button()
        )
        return

    # المستخدم جديد
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "referrals": [],
            "recharge_log": [],
            "withdraw_log": [],
            "invited_by": referred_by if referred_by != user_id else None
        }

        # تسجيل الإحالة إذا وجدت
        if referred_by and referred_by in users and user_id not in users[referred_by]["referrals"]:
            users[referred_by]["referrals"].append(user_id)
            save_users(users)

            try:
                bot.send_message(
                    int(referred_by),
                    "👤 تم تسجيل إحالة جديدة عبر رابطك! استمر بدعوة أصدقائك لزيادة أرباحك 💸"
                )
            except:
                pass
        else:
            save_users(users)

        # شروط وأحكام للمستخدم الجديد
        terms = """📌 شروط وأحكام Faroon Ichancy:

1_ البوت مخصّص لإنشاء الحسابات والسّحب والتعبئة الفورية لموقع Ichancy .
2_ انشاء أكثر من حساب يعرّض جميع الحسابات للحظر وتجميد الرصيد.
3_ لا يحق للاعب شحن وسحب رصيد بقصد التبديل بين طرق الدفع.
4_ يتم حساب ارباح الإحالات عند وجود 3 إحالات نشطة أو أكثر.

للتواصل أو الاستفسار: @sewar1bot1
"""
        bot.send_message(message.chat.id, terms)



    # عرض القائمة الرئيسية
    msg, markup = main_menu(user_id)
    bot.send_message(message.chat.id, msg, reply_markup=markup)










#################################### ايشانسي

@bot.callback_query_handler(func=lambda call: call.data == "شحن_ايشانسي")
def ichancy_services_menu(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    if user_id in ichancy_accounts:
        acc = ichancy_accounts[user_id]
        text = f"""🔐 *معلومات حسابك في إيـشـانسي:*

👤 *اسم المستخدم:* `{acc['name']}`

🔑 *كلمة المرور:* `{acc['password']}`

🌐 *رابط الدخول:* [اضغط هنا](https://ichancy.com)
"""
    else:
        text = """🔐 *معلومات حسابك في إيـشـانسي:*

⚠️ *ليس لديك حساب إيـشانسي بعد.*

🌐 *رابط الموقع:* [اضغط هنا](https://ichancy.com)
"""

    # أزرار صفين بكل سطر (row_width=2)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("شحن الحساب ⬆️⚡️", callback_data="شحن_ichancy"),
        types.InlineKeyboardButton("سحب رصيد من حساب ⬇️⚡️", callback_data="سحب_ichancy"),
        types.InlineKeyboardButton("حساب جديد 🆕⚡️", callback_data="انشاء_ichancy"),
        types.InlineKeyboardButton("حسابي", callback_data="معلومات_ichancy"),
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="رجوع_رئيسية"))

    bot.edit_message_text(chat_id=chat_id,
                          message_id=call.message.message_id,
                          text=text,
                          reply_markup=markup,
                          parse_mode="Markdown")


from time import time




# تخزين طلبات إنشاء الحسابات للمشرف
ichancy_creation_requests = {}     
# تخزين وقت إرسال طلب الإنشاء الأخير لكل مستخدم (لمنع التكرار قبل ساعة)
user_creation_times = {}           

# === بدء إنشاء حساب إيـشـانسي === #
@bot.callback_query_handler(func=lambda call: call.data == "انشاء_ichancy")
def handle_create_ichancy(call):
    user_id = str(call.from_user.id)
    chat_id = call.message.chat.id

    # تحقق من وجود حساب مسبق
    if user_id in ichancy_accounts:
        bot.answer_callback_query(call.id, show_alert=True, text="⚠️ لديك حساب بالفعل.")
        bot.send_message(chat_id, "✅ لديك حساب Ichancy محفوظ مسبقًا.")
        return

    # تحقق من رصيد المستخدم
    balance = users.get(user_id, {}).get("balance", 0)
    if balance < 10000:
        bot.answer_callback_query(call.id, show_alert=True, text="❌ رصيدك غير كافٍ لإنشاء حساب. يجب أن يكون لديك على الأقل 10000 ل.س.")
        bot.send_message(chat_id, f"💸 رصيدك الحالي: {balance} ل.س\n🚫 الحد الأدنى المطلوب: 10000 ل.س")
        return

    # التحقق من مرور ساعة منذ آخر طلب
    now = time()
    last_time = user_creation_times.get(user_id, 0)
    if now - last_time < 3600:
        bot.answer_callback_query(call.id, show_alert=True, text="⚠️ لقد أرسلت طلب إنشاء مؤخرًا. الرجاء الانتظار ساعة قبل إرسال طلب جديد.")
        return

    # حذف الطلب القديم من عند المشرف إذا موجود
    if user_id in ichancy_creation_requests:
        info = ichancy_creation_requests.pop(user_id)
        try:
            bot.delete_message(info["admin_id"], info["request_msg_id"])
        except Exception:
            pass  # تجاهل أي خطأ عند الحذف

    # تحديث وقت آخر طلب
    user_creation_times[user_id] = now

    # طلب اسم الحساب الجديد من المستخدم
    pending_requests[call.from_user.id] = {"step": "ichancy_name_request"}
    bot.send_message(chat_id, "✏️ أدخل اسم حساب إيـشـانسي الجديد 👇")
    bot.answer_callback_query(call.id)


# === استقبال اسم الحساب === #
@bot.message_handler(func=lambda m: pending_requests.get(m.from_user.id, {}).get("step") == "ichancy_name_request")
def get_ichancy_name(message):
    username = message.text.strip()
    if not username:
        bot.send_message(message.chat.id, "❗ الرجاء إدخال اسم صالح.")
        return

    pending_requests[message.from_user.id] = {
        "step": "ichancy_password_request",
        "requested_name": username
    }
    bot.send_message(message.chat.id, "🔒 أدخل كلمة مرور (أكثر من 8 خانات) 👇")


# === استقبال كلمة المرور وإرسال الطلب للمشرف === #
@bot.message_handler(func=lambda m: pending_requests.get(m.from_user.id, {}).get("step") == "ichancy_password_request")
def get_ichancy_password(message):
    password = message.text.strip()
    if len(password) < 8:
        bot.send_message(message.chat.id, "❗ كلمة المرور يجب أن تكون أكثر من 8 خانات. حاول مجددًا.")
        return

    user_id = str(message.from_user.id)
    username = pending_requests[message.from_user.id]["requested_name"]
    bot.send_message(message.chat.id, "⏳ جاري إرسال طلب إنشاء الحساب...")

    # إرسال الطلب للمشرف
    admin_id = ADMIN_IDS[0]
    request_msg = f"""📥 طلب إنشاء حساب إيـشـانسي جديد:

👤 المستخدم: [{message.from_user.first_name}](tg://user?id={user_id})
📝 الاسم المطلوب: `{username}`
🔑 كلمة المرور المطلوبة: `{password}`"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تم الإنشاء", callback_data=f"confirm_ichancy_{user_id}"))

    sent_msg = bot.send_message(admin_id, request_msg, parse_mode="Markdown", reply_markup=markup)

    # تخزين بيانات الطلب (للحذف لاحقًا إذا تكرّر)
    ichancy_creation_requests[user_id] = {
        "admin_id": admin_id,
        "request_msg_id": sent_msg.message_id
    }

    # تحديث حالة المستخدم بانتظار موافقة المشرف
    pending_requests[message.from_user.id] = {
        "step": "waiting_admin",
        "requested_name": username,
        "requested_password": password
    }


# === المشرف يؤكد الإنشاء ويطلب الصيغة === #
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_ichancy_"))
def confirm_ichancy_start(call):
    target_user_id = call.data.split("_")[-1]
    admin_id = call.from_user.id
    prompt = (f"📬 أرسل الآن اسم الحساب الحقيقي وكلمة السر للمستخدم {target_user_id}\n\n"
              "📝 بالشكل:\n`username:password`")
    sent = bot.send_message(admin_id, prompt, parse_mode="Markdown")

    # خزّن message_id للحذف لاحقًا في نفس القاموس المستخدم سابقاً
    if target_user_id in ichancy_creation_requests:
        ichancy_creation_requests[target_user_id]["confirm_msg_id"] = sent.message_id
    else:
        ichancy_creation_requests[target_user_id] = {
            "admin_id": admin_id,
            "confirm_msg_id": sent.message_id
        }

    pending_requests[admin_id] = {
        "step": "admin_send_real_account",
        "target_user_id": target_user_id
    }


# === المشرف يرسل الحساب الحقيقي === #
@bot.message_handler(func=lambda m: pending_requests.get(m.from_user.id, {}).get("step") == "admin_send_real_account")
def receive_real_account_from_admin(message):
    parts = message.text.strip().split(":")
    if len(parts) != 2:
        bot.send_message(message.chat.id,
                         "⚠️ الصيغة غير صحيحة. أرسل بالشكل: `username:password`",
                         parse_mode="Markdown")
        return
    username, password = parts
    target_user_id = pending_requests[message.from_user.id]["target_user_id"]

    # حفظ الحساب للمستخدم
    ichancy_accounts[target_user_id] = {"name": username, "password": password}
    save_ichancy_accounts()

    # حذف رسائل المشرف (طلب الإنشاء والطلب لإرسال البيانات)
    info = ichancy_creation_requests.get(target_user_id, {})
    admin_id = info.get("admin_id")
    if admin_id:
        if info.get("request_msg_id"):
            bot.delete_message(admin_id, info["request_msg_id"])
        if info.get("confirm_msg_id"):
            bot.delete_message(admin_id, info["confirm_msg_id"])

    # تنظيف الطلبات المؤقتة
    ichancy_creation_requests.pop(target_user_id, None)
    pending_requests.pop(int(target_user_id), None)
    pending_requests.pop(message.from_user.id, None)

    # إرسال الحساب للمستخدم
    bot.send_message(int(target_user_id), f"""🎉 تم إنشاء حسابك إيـشـانسي بنجاح:

👤 اسم الحساب: `{username}`
🔒 كلمة السر: `{password}`""", parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ تم إرسال معلومات الحساب للمستخدم.")


# === عرض معلومات حساب Ichancy === #
@bot.callback_query_handler(func=lambda call: call.data == "معلومات_ichancy")
def show_ichancy_info(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)
    if user_id not in ichancy_accounts:
        bot.send_message(call.message.chat.id, "⚠️ ليس لديك حساب إيـشانسي حتى الآن.")
        return
    acc = ichancy_accounts[user_id]
    text = f"""🔐 معلومات حسابك إيـشـانسي:

👤 الاسم: `{acc['name']}`
🔑 كلمة السر: `{acc['password']}`

📌 احتفظ بهذه البيانات جيدًا."""
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")


# === بدء طلب شحن إيـشانسي  عبر الزر === #
@bot.callback_query_handler(func=lambda call: call.data == "شحن_ichancy")
def start_ichancy_recharge(call):
    user_id = str(call.from_user.id)
    # تأكد من وجود حساب
    if user_id not in ichancy_accounts:
        bot.answer_callback_query(call.id, show_alert=True, text="⚠️ لا يوجد لديك حساب إيـشانسي.")
        return

    # تأكد من عدم وجود طلب شحن قيد المعالجة
    if user_id in pending_requests:
        bot.send_message(call.message.chat.id, "⚠️ طلبك قيد المعالجة من قبل المشرف.")
        return

    # أرسل رسالة مع ForceReply لالتقاط المبلغ
    msg = bot.send_message(
        call.message.chat.id,
        "💰 أدخل المبلغ المراد شحنه في حساب إيـشانسي (الحد الأدنى 10000 ل.س):",
        reply_markup=types.ForceReply(selective=True)
    )
    # سجّل خطوة الانتظار
    pending_requests[user_id] = {"step": "ichancy_recharge_amount", "message_id": msg.message_id}
    bot.answer_callback_query(call.id)


# === استقبال مبلغ الشحن من رسالة الرد === #
@bot.message_handler(func=lambda m: m.reply_to_message 
                                  and pending_requests.get(str(m.from_user.id), {}).get("step") == "ichancy_recharge_amount")
def receive_recharge_amount(message):
    user_id = str(message.from_user.id)
    data = pending_requests.get(user_id, {})
    # نتأكد إنها رسالة الرد عالرسالة الصحيحة
    if message.reply_to_message.message_id != data.get("message_id"):
        return

    # محاولة تحويل المبلغ
    try:
        amount = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❗ الرجاء إدخال رقم صحيح.", reply_markup=types.ForceReply(selective=True))
        return

    # تحقق الحد الأدنى
    if amount < 10000:
        bot.send_message(message.chat.id, "❗ الحد الأدنى للشحن هو 10000 ل.س.", reply_markup=types.ForceReply(selective=True))
        return

    # جلب الرصيد من users.json
    user_data = users.get(user_id, {})
    balance = user_data.get("balance", 0)
    if balance < amount:
        bot.send_message(message.chat.id, f"❗ رصيدك ({balance} ل.س) غير كافٍ لإتمام عملية الشحن.", reply_markup=types.ForceReply(selective=True))
        return

    # خصم الرصيد
    user_data["balance"] = balance - amount
    save_users(users)

    # أرسل طلب للمشرف
    acc = ichancy_accounts[user_id]
    admin_id = ADMIN_IDS[0]
    txt = f"""📥 طلب شحن حساب إيـشـانسي:

👤 المستخدم: [{message.from_user.first_name}](tg://user?id={user_id})
💳 حساب إيـشـانسي: `{acc['name']}`
💰 المبلغ: {amount} ل.س"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تم الشحن", callback_data=f"confirm_recharge_{user_id}_{amount}")
    )
    sent = bot.send_message(admin_id, txt, parse_mode="Markdown", reply_markup=markup)

    # خزّن الـ request للاحقًا
    ichancy_requests[user_id] = {"admin_id": admin_id, "request_msg_id": sent.message_id}
    # نظِّف الانتظار
    pending_requests.pop(user_id, None)

    bot.send_message(message.chat.id, "⏳ تم إرسال طلب الشحن للمشرف، سيتم إعلامك عند التأكيد.")


# === تأكيد الشحن من قبل المشرف === #
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_recharge_"))
def handle_admin_confirm_recharge(call):
    _, _, user_id, amount = call.data.split("_")
    info = ichancy_requests.pop(user_id, {})
    # احذف رسالة الطلب عند المشرف
    if info.get("request_msg_id"):
        bot.delete_message(info["admin_id"], info["request_msg_id"])

    # أخبر المستخدم
    bot.send_message(int(user_id), f"✅ تم شحن حسابك إيـشـانسي بمبلغ {amount} ل.س بنجاح.")
    bot.answer_callback_query(call.id, "✅ تم تأكيد الشحن.")


# === عرض معلومات حساب Ichancy للمستخدم === #
@bot.callback_query_handler(func=lambda call: call.data == "معلومات_ichancy")
def show_ichancy_info(call):
    bot.answer_callback_query(call.id)
    user_id = str(call.from_user.id)

    # تحقق إذا كان لدى المستخدم حساب
    if user_id not in ichancy_accounts:
        bot.send_message(call.message.chat.id, "⚠️ ليس لديك حساب إيـشانسي حتى الآن.")
        return

    # تحقق إذا كانت معلومات الحساب قد تم إرسالها من قبل المشرف
    acc = ichancy_accounts[user_id]
    if not acc.get("name") or not acc.get("password"):
        bot.send_message(call.message.chat.id, "⚠️ لم يتم تأكيد معلومات حسابك بعد من المشرف.")
        return

    # إذا كانت المعلومات موجودة، نعرضها
    text = f"""🔐 معلومات حسابك إيـشـانسي:

👤 الاسم: `{acc['name']}`
🔑 كلمة السر: `{acc['password']}`

📌 احتفظ بهذه البيانات جيدًا."""
    
    bot.send_message(call.message.chat.id, text, parse_mode="Markdown")



# === بدء طلب سحب إيـشانسي عبر الزر === #
from time import time  # استيراد time لحساب الوقت

# === بدء طلب سحب إيـشانسي عبر الزر === #
@bot.callback_query_handler(func=lambda call: call.data == "سحب_ichancy")
def start_ichancy_withdraw(call):
    user_id = str(call.from_user.id)

    # تأكد من وجود حساب إيـشـانسي
    if user_id not in ichancy_accounts:
        bot.answer_callback_query(call.id, show_alert=True, text="⚠️ ليس لديك حساب إيـشانسي.")
        return



    # تحقق إذا كانت قد مرت 5 دقائق منذ آخر طلب سحب
    last_request_time = user_request_times.get(user_id, 0)
    if time() - last_request_time < 300:  # 300 ثانية = 5 دقائق
        time_left = 300 - (time() - last_request_time)
        bot.answer_callback_query(call.id, show_alert=True, text=f"⚠️ لا يمكنك تقديم طلب سحب جديد قبل {int(time_left)} ثانية.")
        return

    # أرسل رسالة لالتقاط المبلغ
    msg = bot.send_message(
        call.message.chat.id,
        "💸 أدخل المبلغ المراد سحبه من حساب إيـشانسي:",
        reply_markup=types.ForceReply(selective=True)
    )
    pending_requests[user_id] = {
        "step": "ichancy_withdraw_amount",
        "message_id": msg.message_id
    }

    # تحديث الوقت الذي تم فيه تقديم طلب السحب
    user_request_times[user_id] = time()

    bot.answer_callback_query(call.id)


# إضافة متغير لتخزين الأوقات
user_request_times = {}


# === استقبال مبلغ السحب === #
@bot.message_handler(func=lambda m: m.reply_to_message and pending_requests.get(str(m.from_user.id), {}).get("step") == "ichancy_withdraw_amount")
def receive_withdraw_amount(message):
    user_id = str(message.from_user.id)
    data = pending_requests.get(user_id, {})

    # نتأكد إنها رسالة الرد عالرسالة الصحيحة
    if message.reply_to_message.message_id != data.get("message_id"):
        return

    try:
        amount = int(message.text.strip())
    except ValueError:
        bot.send_message(message.chat.id, "❗ الرجاء إدخال رقم صحيح.", reply_markup=types.ForceReply(selective=True))
        return

    # تحقق من وجود المبلغ المطلوب
    if amount <= 0:
        bot.send_message(message.chat.id, "❗ المبلغ يجب أن يكون أكبر من صفر.")
        return

    # حفظ طلب السحب وإرسال الطلب للمشرف
    acc = ichancy_accounts[user_id]
    admin_id = ADMIN_IDS[0]
    txt = f"""📥 طلب سحب من حساب إيـشانسي:

👤 المستخدم: [{message.from_user.first_name}](tg://user?id={user_id})
💳 حساب إيـشانسي: `{acc['name']}`
💰 المبلغ: {amount} ل.س"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تم السحب", callback_data=f"confirm_withdraw_{user_id}_{amount}"),
        types.InlineKeyboardButton("❌ لا يوجد رصيد", callback_data=f"no_balance_{user_id}")
    )
    sent = bot.send_message(admin_id, txt, parse_mode="Markdown", reply_markup=markup)

    # خزّن الـ request للاحقًا
    ichancy_requests[user_id] = {"admin_id": admin_id, "request_msg_id": sent.message_id}
    pending_requests.pop(user_id, None)
    bot.send_message(message.chat.id, "⏳ تم إرسال طلب السحب للمشرف، سيتم إعلامك عند التأكيد.")


# === تأكيد السحب من قبل المشرف === #
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_withdraw_"))
def handle_admin_confirm_withdraw(call):
    _, _, user_id, amount = call.data.split("_")

    # احذف رسالة الطلب عند المشرف
    info = ichancy_requests.pop(user_id, {})
    if info.get("request_msg_id"):
        bot.delete_message(info["admin_id"], info["request_msg_id"])

    # إضافة المبلغ لرصيد المستخدم في البوت
    users[user_id]["balance"] = users[user_id].get("balance", 0) + int(amount)
    save_users(users)
    log_user_transaction(user_id, "سحب إيـشانسي", int(amount), f"سحب من حساب إيـشانسي")

    # إعلام المستخدم
    bot.send_message(int(user_id), f"✅ تم سحب {amount} ل.س من حسابك إيـشانسي وإضافته إلى رصيد البوت.")
    bot.answer_callback_query(call.id, "✅ تم تأكيد السحب.")


# === لا يوجد رصيد كافي === #
@bot.callback_query_handler(func=lambda call: call.data.startswith("no_balance_"))
def handle_no_balance(call):
    _, _, user_id = call.data.split("_")

    # احذف رسالة الطلب عند المشرف
    info = ichancy_requests.pop(user_id, {})
    if info.get("request_msg_id"):
        bot.delete_message(info["admin_id"], info["request_msg_id"])

    # إعلام المستخدم
    bot.send_message(int(user_id), "❗ رصيدك في إيـشانسي أقل من المطلوب. تأكد من وجود الرصيد الكافي.")
    bot.answer_callback_query(call.id, "❗ تم رفض السحب بسبب عدم كفاية الرصيد.")


# === منعه من تقديم طلب سحب جديد إذا كان هناك طلب معلَّق === #
@bot.message_handler(func=lambda m: m.reply_to_message and pending_requests.get(str(m.from_user.id), {}).get("step") == "ichancy_withdraw_amount")
def prevent_duplicate_withdraw_request(m):
    user_id = str(m.from_user.id)




##رجوع
@bot.callback_query_handler(func=lambda call: call.data == "رجوع_رئيسية")
def back_to_main_menu(call):
    user_id = str(call.from_user.id)

    # تحقق من الاشتراك بالقناة (اختياري حسب نظامك)
    if not is_user_subscribed(call.from_user.id):
        bot.answer_callback_query(call.id, "يجب الاشتراك بالقناة أولاً.", show_alert=True)
        return

    msg, markup = main_menu(user_id)
    bot.edit_message_text(chat_id=call.message.chat.id,
                          message_id=call.message.message_id,
                          text=msg,
                          reply_markup=markup)

##################################



















@bot.callback_query_handler(func=lambda call: call.data == "معلومات")
def show_profile_info(call):
    uid = str(call.from_user.id)
    info = user_info.get(uid, {})
    number = info.get("syriatel_number", "غير محدد")
    last_update = info.get("syriatel_updated", "غير معروف")

    msg = f"""🧍 *معلومات الملف الشخصي:*

📱 رقم سيرياتيل كاش: `{number}`
🕓 آخر تعديل: {last_update}
💰 الرصيد الحالي: {users.get(uid, {}).get('balance', 0)} ل.س"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✏️ تعديل رقم سيرياتيل", callback_data="edit_syriatel"))
    bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "edit_syriatel")
def edit_syriatel_start(call):
    uid = str(call.from_user.id)
    info = user_info.get(uid, {})
    last_update_str = info.get("syriatel_updated")

    if last_update_str:
        try:
            last_update = datetime.strptime(last_update_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                last_update = datetime.strptime(last_update_str, "%Y-%m-%d")
            except:
                last_update = None

        if last_update:
            days_since = (datetime.now() - last_update).days
            if days_since < 14:
                remaining = 14 - days_since
                bot.answer_callback_query(call.id, show_alert=True, text=f"❌ لا يمكنك تعديل الرقم الآن.\n🕓 يمكنك المحاولة مجددًا بعد {remaining} يوم(أيام).")
                return

    pending_requests[call.from_user.id] = {"step": "editing_syriatel"}
    bot.send_message(call.message.chat.id, "📱 أرسل رقم سيرياتيل كاش الجديد:")







bot_username = 'sewar1bot'
# === منطق الشحن === #
@bot.callback_query_handler(func=lambda c: c.data == "شحن")
def handle_recharge(call):
    user_id = str(call.from_user.id)
    balance = users[user_id].get("balance", 0)
    msg = f"""
💰 *شحن رصيد البوت*
رصيدك الحالي: {balance}

اختر وسيلة الدفع التي ترغب بها:
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("سيرياتيل كاش", callback_data="سيرياتيل"),
        types.InlineKeyboardButton("بيمو", callback_data="بيمو"),
        types.InlineKeyboardButton("عملات رقمية", callback_data="رقمي")
    )
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="رجوع"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg, reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda c: c.data == "سيرياتيل")
def syriatel_cash_handler(call):
    user_id = str(call.from_user.id)
    code = get_cash_code()
    msg = f"""
📲 *قم بالتحويل يدويًا إلى التاجر صاحب الرقم ثم أرسل رقم عملية التحويل بعد تحويل المبلغ.*

📌 كود التاجر:    `{code}\n`
💡 أقل مبلغ شحن: 10,000 ل.س
"""
    cancel_btn = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel_btn.add("❌ إلغاء العملية")
    bot.send_message(call.message.chat.id, msg, reply_markup=cancel_btn, parse_mode='Markdown')
    bot.register_next_step_handler(call.message, handle_transaction_number)

def handle_transaction_number(message):
    if message.text == "❌ إلغاء العملية":
        bot.send_message(message.chat.id, "❌ تم إلغاء عملية الشحن.", reply_markup=types.ReplyKeyboardRemove())
        return

    txn_id = message.text.strip()
    if len(txn_id) not in [12, 15] or not txn_id.isdigit():
        bot.send_message(message.chat.id, "⚠️ رقم العملية غير صحيح، الرجاء إعادة المحاولة.")
        bot.register_next_step_handler(message, handle_transaction_number)
        return

    # تحقق من تكرار الرقم
    for user in users.values():
        for log in user.get("recharge_log", []):
            if txn_id == log.get("txn_id"):
                bot.send_message(message.chat.id, "⚠️ رقم العملية مستخدم مسبقًا.")
                return

    user_id = str(message.from_user.id)
    pending_requests[user_id] = {"step": "amount", "txn_id": txn_id}
    bot.send_message(message.chat.id, "💵 الآن أرسل المبلغ الذي قمت بشحنه (مثال: 30000)")
    bot.register_next_step_handler(message, handle_transaction_amount)

def handle_transaction_amount(message):
    if message.text == "❌ إلغاء العملية":
        bot.send_message(message.chat.id, "❌ تم إلغاء عملية الشحن.", reply_markup=types.ReplyKeyboardRemove())
        return

    try:
        amount = int(message.text.strip())
        if amount < 10000:
            bot.send_message(message.chat.id, "⚠️ الحد الأدنى للشحن هو 10,000 ل.س")
            return

        user_id = str(message.from_user.id)
        txn_data = pending_requests.get(user_id, {})
        txn_id = txn_data.get("txn_id")
        username = message.from_user.username or "NoUsername"

        info = f"""
📥 طلب شحن جديد:

👤 المستخدم: {message.from_user.first_name} (@{username})
🆔 ID: {user_id}
🔢 رقم العملية: {txn_id}
💰 المبلغ: {amount} ل.س
🕒 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ قبول الطلب", callback_data=f"قبول_{user_id}_{txn_id}_{amount}"),
            types.InlineKeyboardButton("❌ رفض الطلب", callback_data=f"رفض_{user_id}")
        )
        bot.send_message(ADMIN_IDS[0], info, reply_markup=markup)
        bot.send_message(message.chat.id, "⏳ جاري معالجة طلبك، سيتم الرد قريبًا.", reply_markup=types.ReplyKeyboardRemove())

    except ValueError:
        bot.send_message(message.chat.id, "⚠️ المبلغ يجب أن يكون رقمًا. أعد المحاولة.")
        bot.register_next_step_handler(message, handle_transaction_amount)



# === قبول طلب الشحن === #
@bot.callback_query_handler(func=lambda c: c.data.startswith("قبول_"))
def accept_request(call):
    _, uid, txn_id, amount = call.data.split("_")
    amount = int(amount)

    # 1) إضافة المبلغ إلى رصيد المحال
    users[uid]['balance'] += amount
    users[uid]['recharge_log'].append({
        "method": "سيرياتيل كاش (يدوي)",
        "amount": amount,
        "txn_id": txn_id,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_users(users)

    bot.send_message(
        int(uid),
        f"✅ تم إضافة {amount} ل.س إلى رصيدك، وأصبح الآن {users[uid]['balance']} ل.س"
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="✅ تم قبول الطلب."
    )

    # 2) إذا كان هناك محيل، نحسب له 5% من الشحن
    referred_by = users[uid].get("invited_by")
    if referred_by and referred_by in users:
        # هنا لا نتحقق من عدد الإحالات لأن المكافأة دائماً تُعطى
        bonus = int(amount * 0.05)
        users[referred_by]['balance'] += bonus
        save_users(users)
        try:
            bot.send_message(
                int(referred_by),
                f"🎉 لقد تمت إضافة مكافأة بقيمة {bonus} ل.س إلى رصيدك من إحدى إحالاتك النشطة!"
            )
        except:
            pass



# === رفض طلب الشحن === #
@bot.callback_query_handler(func=lambda c: c.data.startswith("رفض_"))
def reject_recharge_request(call):
    if call.from_user.id not in ADMIN_IDS:
        return

    # الحصول على ID المستخدم من بيانات الـ callback_data
    parts = call.data.split("_")
    user_id = parts[1]

    # إزالة بيانات الطلب المعلقة
    if user_id in pending_requests:
        del pending_requests[user_id]

    # إرسال رسالة للمستخدم تفيد بأنه تم رفض طلب الشحن
    bot.send_message(user_id, "❌ تم رفض طلب الشحن: رقم عملية التحويل غير صحيح أو البيانات غير متطابقة.")

    # إعلام المشرف بأنه تم رفض الطلب
    bot.answer_callback_query(call.id, "تم رفض طلب الشحن.")

    # حذف الرسالة الخاصة بالطلب من المشرف
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)


################### نظام الاحالات
bot_username = 'sewar1bot'
# === زر برنامج الإحالات === #
@bot.callback_query_handler(func=lambda c: c.data == "إحالات")
def referral_main(call):
    user_id = str(call.from_user.id)
    referrals = users.get(user_id, {}).get("referrals", [])
    count = len(referrals)

    msg = f"""👥 *نظام الإحالات*

عدد الأشخاص الذين سجلوا باستخدام رابطك: *{count}* إحالة.

قم بدعوة أصدقائك لزيادة أرباحك! 💸"""
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📎 رابط الإحالة", callback_data="رابط_الإحالة"))
    markup.add(types.InlineKeyboardButton("📘 شرح نظام الإحالات", callback_data="شرح_الإحالات"))
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="رجوع"))
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=msg, reply_markup=markup, parse_mode="Markdown")

# === رابط الإحالة === #
@bot.callback_query_handler(func=lambda c: c.data == "رابط_الإحالة")
def show_referral_link(call):
    user_id = call.from_user.id
    bot_username = bot.get_me().username
    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    msg = f"""🔗 *رابط الإحالة الخاص بك:*

`{referral_link}`

انسخه وشاركه مع أصدقائك لزيادة أرباحك! ✅
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="إحالات"))
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=msg, reply_markup=markup, parse_mode="Markdown")

# === شرح نظام الإحالات === #
@bot.callback_query_handler(func=lambda c: c.data == "شرح_الإحالات")
def explain_referral_system(call):
    msg = """📘 *شرح نظام الإحالات:*

1. انسخ رابط الإحالة الخاص بك وشاركه مع أصدقائك.
2. عندما يسجل أحد من خلاله، يتم احتسابه كإحالة لك.
3. بمجرد أن تقوم 3 من إحالاتك بشحن رصيد، تحصل على *5%* من قيمة شحناتهم كمكافأة 🎁

📌 احرص أن تكون الإحالات حقيقية ونشطة للحصول على المكافآت.

بالتوفيق! 🌟
"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="إحالات"))
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=msg, reply_markup=markup, parse_mode="Markdown")


################## رجوع 

@bot.callback_query_handler(func=lambda c: c.data == "رجوع")
def go_back(call):
    user_id = str(call.from_user.id)
    msg, markup = main_menu(user_id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=msg,
        reply_markup=markup
    )



################## اكواد الهدايا 

# === زر اكواد الجوائز === #
@bot.callback_query_handler(func=lambda c: c.data == "جوائز")
def gift_code_prompt(call):
    cancel = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel.add("❌ إلغاء")
    bot.send_message(
        call.message.chat.id,
        "يتم الحصول على كود الهدية من قبل الأدمن من خلال مسابقات وجوائز.\n"
        "ادخل كود الهدية لشحن رصيدك بقيمته 👇",
        reply_markup=cancel
    )
    bot.register_next_step_handler(call.message, handle_gift_code_input)



# === زر اكواد الجوائز === #
@bot.callback_query_handler(func=lambda c: c.data == "جوائز")
def gift_code_prompt(call):
    cancel = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    cancel.add("❌ إلغاء")
    bot.send_message(
        call.message.chat.id,
        "يتم الحصول على كود الهدية من قبل الأدمن من خلال مسابقات وجوائز.\n"
        "ادخل كود الهدية لشحن رصيدك بقيمته 👇",
        reply_markup=cancel
    )
    bot.register_next_step_handler(call.message, handle_gift_code_input)


def handle_gift_code_input(message):
    text = message.text.strip()
    if text == "❌ إلغاء":
        bot.send_message(message.chat.id, "❌ تم إلغاء عملية إدخال الكود.", reply_markup=types.ReplyKeyboardRemove())
        return

    user_id = str(message.from_user.id)
    code_data = gift_codes.get(text)

    if not code_data:
        bot.send_message(message.chat.id, "⚠️ الكود خاطئ، حاول مرة أخرى.", reply_markup=types.ReplyKeyboardRemove())
        return

    if code_data["used_by"]:
        prev = code_data["used_info"]
        bot.send_message(
            message.chat.id,
            f"❌ عذرًا، لقد تم استخدام هذا الكود مسبقًا.\n"
            f"🔗 المستخدم: @{prev.get('username','')}\n"
            f"🆔 معرف المستخدم: {prev.get('id','')}",
            reply_markup=types.ReplyKeyboardRemove()
        )
        return

    # الكود صحيح وغير مستخدم
    value = code_data["value"]
    # تحديث رصيد المستخدم
    users[user_id]["balance"] = users[user_id].get("balance",0) + value
    users[user_id]["recharge_log"].append({
        "method": f"كود هدية ({text})",
        "amount": value,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "txn_id": text
    })
    # علامة الاستخدام
    code_data["used_by"] = user_id
    code_data["used_info"] = {
        "username": message.from_user.username or "",
        "id": user_id
    }
    save_users(users)
    save_gift_codes(gift_codes)

    bot.send_message(
        message.chat.id,
        f"🎉 تهانينا! تم تحصيل قيمة الكود وهي: {value} ل.س\n"
        f"رصيدك الحالي: {users[user_id]['balance']} ل.س",
        reply_markup=types.ReplyKeyboardRemove()
    )



#################3 لوحة تحكم المشرف 

# ✅ إعداد لوحة التحكم وكافة الأوامر المرتبطة بها مع ترتيب وتنظيم

from telebot import types

@bot.callback_query_handler(func=lambda call: call.data == "لوحة_التحكم")
def control_panel(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك.")
        return

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("👥 عدد المستخدمين", callback_data="عدد_المستخدمين"),
        types.InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="رسالة_جماعية")
    )
    markup.row(
        types.InlineKeyboardButton("💰 تعديل رصيد مستخدم", callback_data="تعديل_رصيد"),
        types.InlineKeyboardButton("🔑 تعديل كود الكاش", callback_data="تعديل_كود")
    )
    markup.row(
        types.InlineKeyboardButton("➕ إضافة كود هدية", callback_data="إضافة_كود_هدية"),
        types.InlineKeyboardButton("📜 عرض أكواد الهدايا", callback_data="عرض_أكواد_الهدايا")
    )
    markup.row(
        types.InlineKeyboardButton("❌ حذف كود هدية", callback_data="حذف_كود"),
        types.InlineKeyboardButton("✉️ رسالة لمستخدم", callback_data="رسالة_لمستخدم")
    )
    markup.row(
        types.InlineKeyboardButton("⚠️ خطأ في رقم عملية التحويل", callback_data="خطأ")
    )

    bot.edit_message_text("🛠 لوحة التحكم:\nاختر ما تريد فعله:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# === عدد المستخدمين ===
@bot.callback_query_handler(func=lambda call: call.data == "عدد_المستخدمين")
def count_users(call):
    if call.from_user.id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "❌ غير مصرح لك.")
        return

    count = len(users)
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, f"📊 عدد المستخدمين المسجلين في البوت: {count}")

# === إرسال رسالة جماعية ===
@bot.callback_query_handler(func=lambda call: call.data == "رسالة_جماعية")
def broadcast_prompt(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "📝 أرسل الآن الرسالة التي تريد إرسالها لجميع المستخدمين.")
    pending_requests[call.from_user.id] = {"step": "awaiting_broadcast"}

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_broadcast")
def handle_broadcast(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    text = message.text
    success = 0
    failed = 0
    for user_id in users:
        try:
            bot.send_message(int(user_id), text)
            success += 1
        except:
            failed += 1

    bot.send_message(message.chat.id, f"📬 تم إرسال الرسالة إلى {success} مستخدم.\n❌ فشل الإرسال إلى {failed}.")
    pending_requests.pop(message.from_user.id)
# === تعديل رصيد مستخدم ===
@bot.callback_query_handler(func=lambda call: call.data == "تعديل_رصيد")
def ask_user_id_for_balance_edit(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "🔢 أرسل آيدي المستخدم المراد تعديل رصيده.")
    pending_requests[call.from_user.id] = {"step": "awaiting_user_id_for_balance"}

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_user_id_for_balance")
def show_current_balance_and_ask_for_edit(message):
    user_id = message.text.strip()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على المستخدم.")
        pending_requests.pop(message.from_user.id)
        return

    # عرض الرصيد الحالي
    current_balance = users[user_id].get("balance", 0)
    bot.send_message(message.chat.id, f"💵 الرصيد الحالي للمستخدم هو: {current_balance} ل.س")

    # إعطاء المشرف خيار الزيادة أو الخصم
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("➕ زيادة رصيد", "➖ خصم رصيد")
    markup.add("❌ إلغاء")
    bot.send_message(message.chat.id, "اختر ما تريد فعله:", reply_markup=markup)
    pending_requests[message.from_user.id] = {"step": "awaiting_balance_change", "target_user": user_id}

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_balance_change")
def handle_balance_change(message):
    user_id = pending_requests[message.from_user.id].get("target_user")
    if not user_id:
        return

    if message.text == "➕ زيادة رصيد":
        bot.send_message(message.chat.id, "🔢 أرسل القيمة التي تريد إضافتها.")
        pending_requests[message.from_user.id] = {"step": "awaiting_add_balance", "target_user": user_id}
    elif message.text == "➖ خصم رصيد":
        bot.send_message(message.chat.id, "🔢 أرسل القيمة التي تريد خصمها.")
        pending_requests[message.from_user.id] = {"step": "awaiting_deduct_balance", "target_user": user_id}
    else:
        bot.send_message(message.chat.id, "❌ تم إلغاء العملية.")
        pending_requests.pop(message.from_user.id)

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_add_balance")
def add_balance(message):
    try:
        amount = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❗ يجب إرسال رقم صحيح.")
        return

    user_id = pending_requests[message.from_user.id].get("target_user")
    if not user_id:
        return

    # تحديث الرصيد
    users[user_id]["balance"] += amount
    save_users(users)

    # إعلام المستخدم والمشرف
    bot.send_message(message.chat.id, f"✅ تم إضافة {amount} ل.س إلى رصيد المستخدم.")
    bot.send_message(int(user_id), f"📢 تم إضافة {amount} ل.س إلى رصيدك.")
    pending_requests.pop(message.from_user.id)

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_deduct_balance")
def deduct_balance(message):
    try:
        amount = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❗ يجب إرسال رقم صحيح.")
        return

    user_id = pending_requests[message.from_user.id].get("target_user")
    if not user_id:
        return

    # تحديث الرصيد
    users[user_id]["balance"] -= amount
    save_users(users)

    # إعلام المستخدم والمشرف
    bot.send_message(message.chat.id, f"✅ تم خصم {amount} ل.س من رصيد المستخدم.")
    bot.send_message(int(user_id), f"📢 تم خصم {amount} ل.س من رصيدك.")
    pending_requests.pop(message.from_user.id)

# === تعديل كود سيرياتيل كاش ===
@bot.callback_query_handler(func=lambda call: call.data == "تعديل_كود")
def ask_new_cash_code(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "🔑 أرسل الكود الجديد لسيرياتيل كاش:")
    pending_requests[call.from_user.id] = {"step": "awaiting_new_cash_code"}

@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_new_cash_code")
def save_new_cash_code(message):
    code = message.text.strip()
    with open(CASH_CODE_FILE, 'w') as f:
        f.write(code)

    for uid in users:
        try:
            bot.send_message(int(uid), f"📢 تم تغيير كود شحن سيرياتيل كاش إلى: {code}")
        except:
            continue

    bot.send_message(message.chat.id, "✅ تم حفظ الكود وإبلاغ المستخدمين.")
    pending_requests.pop(message.from_user.id)







# === عرض أكواد الهدايا ===
@bot.callback_query_handler(func=lambda call: call.data == "عرض_أكواد_الهدايا")
def show_gift_codes(call):
    if not gift_codes:
        bot.send_message(call.message.chat.id, "❗ لا يوجد أكواد هدايا حالياً.")
        return

    msg = "🎁 الأكواد المتاحة:\n\n"
    for code, data in gift_codes.items():
        msg += f"🔸 الكود: `{code}`\n"
        msg += f"💰 القيمة: {data.get('value', 0)} ل.س\n"
        if data.get("used_by"):
            username = data["used_info"].get("username", "")
            uid = data["used_info"].get("id", "")
            msg += f"✅ الحالة: مستخدم بواسطة @{username} (ID: {uid})\n"
        else:
            msg += f"🔓 الحالة: غير مستخدم\n"
        
        # إضافة خط فاصل بين كل كود والآخر
        msg += "\n" + "-" * 50 + "\n"  # خط فاصل بعرض 50 "-" بين الأكواد

    bot.send_message(call.message.chat.id, msg, parse_mode="Markdown")




@bot.callback_query_handler(func=lambda call: call.data == "إضافة_كود_هدية")
def ask_gift_code(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "🎁 أرسل الكود الجديد وقيمته بهذا الشكل:\nCODE123 500", parse_mode="Markdown")
    pending_requests[call.from_user.id] = {"step": "awaiting_new_gift_code"}


@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_new_gift_code")
def save_gift_code(message):
    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        bot.send_message(message.chat.id, "❌ تنسيق غير صحيح. أرسل بالشكل:\nCODE123 500", parse_mode="Markdown")
        return

    code, value = parts
    if code in gift_codes:
        bot.send_message(message.chat.id, "⚠️ هذا الكود موجود مسبقاً.")
        return

    gift_codes[code] = {
        "value": int(value),
        "used_by": None,
        "used_info": {}
    }
    save_gift_codes(gift_codes)
    bot.send_message(message.chat.id, f"✅ تم حفظ كود الهدية {code} بقيمة {value} ل.س")
    pending_requests.pop(message.from_user.id)











# === إرسال رسالة لمستخدم محدد ===
@bot.callback_query_handler(func=lambda call: call.data == "رسالة_لمستخدم")
def dm_user_prompt(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "✉️ *أرسل آيدي المستخدم الذي تريد إرسال رسالة له:*", parse_mode="Markdown")
    pending_requests[call.from_user.id] = {"step": "awaiting_dm_user_id"}


@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_dm_user_id")
def dm_user_get_id(message):
    user_id = message.text.strip()

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ *لم يتم العثور على المستخدم.*", parse_mode="Markdown")
        pending_requests.pop(message.from_user.id)
        return

    pending_requests[message.from_user.id] = {
        "step": "awaiting_dm_text",
        "target_user": user_id
    }

    # إضافة زر رجوع اختياري
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_dm"))

    bot.send_message(message.chat.id, "✉️ *الآن أرسل نص الرسالة التي تريد إرسالها للمستخدم:*", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "cancel_dm")
def cancel_dm(call):
    pending_requests.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ تم إلغاء العملية.")



from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import re

def escape_markdown_v2(text):
    return re.sub(r'([_*[\]()~`>#+-=|{}.!\\])', r'\\\1', text)


@bot.message_handler(commands=["test"])
def send_test_message(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back"))

    msg = (
        "*📨 رد الدعم:*\n"
        "```"
        f"{escape_markdown_v2('هذه رسالة تجريبية من الدعم')}"
        "```\n"
        "هذه الرسالة لا يمكن الرد عليها. لإرسال رسالة أخرى يرجى الضغط على \"إرسال رسالة للدعم من القائمة الرئيسية\""
    )

    bot.send_message(message.chat.id, msg, reply_markup=markup, parse_mode="MarkdownV2")




def escape_markdown(text):
    # تطهير النص من رموز Markdown
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_dm_text")
def dm_user_send(message):
    state = pending_requests.pop(message.from_user.id)
    target = state.get("target_user")
    text = escape_markdown(message.text)

    # تنسيق مشابه للصورة 100%
    msg = (
        "📨 *رد الدعم:*\n"
        f"```{text}```\n"
        "هذه الرسالة لا يمكن الرد عليها. لإرسال رسالة أخرى يرجى الضغط على \"إرسال رسالة للدعم من القائمة الرئيسية\""
    )

    bot.send_message(int(target), msg, parse_mode="Markdown")
    bot.send_message(message.chat.id, "✅ تم إرسال الرسالة للمستخدم.")



# === خطأ في رقم عملية التحويل ===
@bot.callback_query_handler(func=lambda call: call.data == "خطأ")
def handle_error_request(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    bot.send_message(call.message.chat.id, "🔢 أرسل آيدي المستخدم الذي ترغب في إرسال رسالة الخطأ له.")
    pending_requests[call.from_user.id] = {"step": "awaiting_user_id_for_error"}

# === معالجة آيدي المستخدم ===
@bot.message_handler(func=lambda message: pending_requests.get(message.from_user.id, {}).get("step") == "awaiting_user_id_for_error")
def handle_user_id_for_error(message):
    user_id = message.text.strip()
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على المستخدم.")
        pending_requests.pop(message.from_user.id)
        return

    # إرسال رسالة للمستخدم
    bot.send_message(user_id, "⚠️ خطأ رقم عملية التحويل غير صحيحة أو مستخدمة مسبقًا.")
    
    # إبلاغ المشرف
    bot.send_message(message.chat.id, f"✅ تم إرسال رسالة الخطأ للمستخدم {user_id}.")
    pending_requests.pop(message.from_user.id)





############################## السحب من البوت
from datetime import datetime, timedelta
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === اختيار طريقة السحب ===
@bot.callback_query_handler(func=lambda call: call.data == "سحب")
def withdraw_method_select(call):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("Syriatel Cash", callback_data="withdraw_syriatel"),
        InlineKeyboardButton("BEMO", callback_data="withdraw_bemo"),
        InlineKeyboardButton("BAEER", callback_data="withdraw_baeer"),
        InlineKeyboardButton("حوالة", callback_data="withdraw_hawala")
    )
    bot.send_message(call.message.chat.id, "💳 *اختر طريقة السحب:*", parse_mode="Markdown", reply_markup=markup)








from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


# === بدء سحب سيرياتيل كاش ===
@bot.callback_query_handler(func=lambda call: call.data == "withdraw_syriatel")
def withdraw_syriatel_start(call):
    uid = str(call.from_user.id)
    now = datetime.now()
    user_data = user_info.get(uid, {})
    last_update = user_data.get("syriatel_updated")

    # إذا تمّ إدخال الرقم خلال 30 يوم
    if last_update:
        try:
            lu = datetime.strptime(last_update, "%Y-%m-%d %H:%M")
            if now - lu < timedelta(days=30) and user_data.get("syriatel_number"):
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_syriatel"))
                bot.send_message(call.message.chat.id,
                    "📌 هذا الطلب سيكون الطلب رقم 1 خلال الـ24 ساعة وسيتم اقتطاع عمولة بنسبة 10.0% من المبلغ\n\n"
                    "💰 أرسل المبلغ المراد سحبه:",
                    reply_markup=markup)
                pending_requests[call.from_user.id] = {"step": "awaiting_syriatel_amount"}
                return
        except ValueError:
            bot.send_message(call.message.chat.id, "❌ حدث خطأ في تاريخ آخر تحديث.")
            return

    # وإلا نطلب رقم سيرياتيل
    markup = InlineKeyboardMarkup()
    cancel_button = InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_syriatel")
    markup.add(cancel_button)

    bot.send_message(call.message.chat.id,
        "📱 *أدخل رقم سيرياتيل كاش الخاص بك لاستلام المبلغ:*",
        parse_mode="Markdown", reply_markup=markup)
    pending_requests[call.from_user.id] = {"step": "awaiting_syriatel_number"}


# === حفظ رقم سيرياتيل ===
@bot.message_handler(func=lambda m: pending_requests.get(m.from_user.id, {}).get("step") == "awaiting_syriatel_number")
def save_syriatel_number(m):
    uid = str(m.from_user.id)
    user_info.setdefault(uid, {})["syriatel_number"] = m.text.strip()
    user_info[uid]["syriatel_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_user_info()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ إلغاء العملية", callback_data="cancel_syriatel"))

    bot.send_message(m.chat.id,
        "📌 هذا الطلب سيكون الطلب رقم 1 خلال الـ24 ساعة وسيتم اقتطاع عمولة بنسبة 10.0% من المبلغ\n\n"
        "💰 أرسل المبلغ المراد سحبه:",
        reply_markup=markup)
    pending_requests[m.from_user.id] = {"step": "awaiting_syriatel_amount"}


# === إلغاء عملية السحب ===
@bot.callback_query_handler(func=lambda call: call.data == "cancel_syriatel")
def cancel_withdraw(call):
    pending_requests.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ تم إلغاء عملية السحب بنجاح.")
    bot.delete_message(call.message.chat.id, call.message.message_id)


# === معالجة مبلغ السحب ===
@bot.message_handler(func=lambda m: pending_requests.get(m.from_user.id, {}).get("step") == "awaiting_syriatel_amount" and m.text.isdigit())
def handle_syriatel_amount(m):
    uid = str(m.from_user.id)
    amount = int(m.text)
    balance = users[uid]["balance"]

    if amount < 30000:
        return bot.send_message(m.chat.id, "❌ المبلغ المطلوب سحبه أقل من الحد الأدنى للسحب وهو 30,000 ل.س.")

    if amount > balance:
        return bot.send_message(m.chat.id, "❌ لا تملك رصيد كافٍ.")

    commission = int(amount * 0.10)
    net = amount - commission
    users[uid]["balance"] -= amount
    save_users(users)

    request_id = f"{uid}_{int(datetime.now().timestamp())}"
    withdraw_requests[request_id] = {
        "user_id": uid,
        "method": "سيرياتيل كاش",
        "amount": amount,
        "commission": commission,
        "net": net,
        "number": user_info[uid]["syriatel_number"],
        "status": "قيد المعالجة",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "admin_messages": []
    }
    save_withdraw_requests()

    user_msg = (
        f"✅ تم تسجيل طلب السحب الخاص بك\n\n"
        f"*طريقة السحب:* سيرياتيل كاش\n"
        f"*المبلغ:* {amount} ل.س\n"
        f"*رقم سيرياتيل:* `{user_info[uid]['syriatel_number']}`\n"
        f"*العمولة:* {commission} ل.س\n"
        f"*الصافي:* {net} ل.س\n"
        f"*الرصيد المتبقي:* {users[uid]['balance']} ل.س\n"
        f"*الحالة:* جاري المعالجة"
    )
    bot.send_message(m.chat.id, user_msg, parse_mode="Markdown")

    recover_markup = InlineKeyboardMarkup()
    recover_markup.add(
        InlineKeyboardButton("📤 طلب استرداد حوالة 🔄", callback_data=f"recover_{request_id}")
    )
    bot.send_message(m.chat.id,
        "في حال لم يتم معالجة الطلب، يمكنك طلب استرداده من هنا:",
        reply_markup=recover_markup)

    admin_markup = InlineKeyboardMarkup()
    admin_markup.add(
        InlineKeyboardButton("✅ قبول الطلب", callback_data=f"approve_{request_id}"),
        InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{request_id}")
    )
    for admin in ADMIN_IDS:
        admin_full_msg = f"📥 طلب سحب جديد من المستخدم `{uid}`:\n\n{user_msg}"
        sent = bot.send_message(admin, admin_full_msg, parse_mode="Markdown", reply_markup=admin_markup)
        withdraw_requests[request_id]["admin_messages"].append(
            {"chat_id": admin, "message_id": sent.message_id}
        )
    save_withdraw_requests()
    pending_requests.pop(m.from_user.id, None)


# === استرداد الحوالة ===
@bot.callback_query_handler(func=lambda c: c.data.startswith("recover_"))
def recover_withdraw_request(c):
    req_id = c.data.split("_",1)[1]
    req = withdraw_requests.get(req_id)
    if not req:
        return bot.answer_callback_query(c.id, "❌ لا يوجد طلب قيد المعالجة.", show_alert=True)

    uid = str(c.from_user.id)
    if uid != req["user_id"]:
        return bot.answer_callback_query(c.id, "❌ هذا الطلب لا يخصك.", show_alert=True)

    users[uid]["balance"] += req["amount"]
    save_users(users)

    for info in req.get("admin_messages", []):
        try:
            bot.delete_message(info["chat_id"], info["message_id"])
            bot.send_message(info["chat_id"],
                f"⚠️ طلب سحب `{req_id}` تم استرداده من قبل المستخدم `{uid}`، "
                f"تمت إعادة {req['amount']} ل.س إلى رصيده.",
                parse_mode="Markdown")
        except:
            pass

    withdraw_requests.pop(req_id)
    save_withdraw_requests()
    bot.edit_message_text("✅ تم استرداد المبلغ وإعادته إلى رصيدك بنجاح.",
                          c.message.chat.id, c.message.message_id)


# === الموافقة على السحب ===
@bot.callback_query_handler(func=lambda c: c.data.startswith("approve_"))
def approve_withdraw(c):
    req_id = c.data.split("_",1)[1]
    req = withdraw_requests.pop(req_id, None)
    if not req:
        return bot.answer_callback_query(c.id, "❌ الطلب غير موجود.", show_alert=True)

    save_withdraw_requests()
    bot.send_message(int(req["user_id"]), f"✅ تم سحب المبلغ {req['net']} ل.س عبر سيرياتيل كاش.")
    log_user_transaction(
        req["user_id"], "سحب سيرياتيل كاش", -req["amount"],
        f"رقم السيرياتيل: {req['number']} | عمولة: {req['commission']} | صافي: {req['net']}"
    )
    bot.delete_message(c.message.chat.id, c.message.message_id)


# === رفض السحب ===
@bot.callback_query_handler(func=lambda c: c.data.startswith("reject_"))
def reject_withdraw(c):
    req_id = c.data.split("_",1)[1]
    req = withdraw_requests.pop(req_id, None)
    if not req:
        return bot.answer_callback_query(c.id, "❌ الطلب غير موجود.", show_alert=True)

    users[req["user_id"]]["balance"] += req["amount"]
    save_users(users)
    save_withdraw_requests()
    bot.send_message(int(req["user_id"]), f"❌ تم رفض طلب السحب الخاص بك وتمت إعادة {req['amount']} ل.س إلى رصيدك.")
    bot.delete_message(c.message.chat.id, c.message.message_id)
##########3 سجل السحب والشحن

@bot.callback_query_handler(func=lambda call: call.data == "سجل")
def show_log_options(call):
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📥 سجل الشحن", callback_data="log_recharge"),
        InlineKeyboardButton("📤 سجل السحب", callback_data="log_withdraw"),
    )
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_to_main"))
    bot.edit_message_text("📊 *اختر نوع السجل الذي تود عرضه:*", call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "log_recharge")
def show_recharge_log(call):
    uid = str(call.from_user.id)
    log = users.get(uid, {}).get("recharge_log", [])
    if not log:
        bot.edit_message_text("❌ لا يوجد سجل شحن بعد.", call.message.chat.id, call.message.message_id)
        return

    msg_lines = ["📥 *سجل الشحن الخاص بك:*", ""]
    for i, item in enumerate(reversed(log), start=1):
        msg_lines.append(
            f"---------------------------\n"
            f"{i}- {item['method']}\n"
            f"القيمة المشحونة: {item['amount']}\n"
            f"التاريخ: {item['timestamp']}"
        )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="سجل"))
    bot.edit_message_text("\n\n".join(msg_lines), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "log_withdraw")
def show_withdraw_log(call):
    uid = str(call.from_user.id)
    log = users.get(uid, {}).get("transactions", [])
    if not log:
        bot.edit_message_text("❌ لا يوجد سجل سحب بعد.", call.message.chat.id, call.message.message_id)
        return

    msg_lines = ["📤 *سجل السحب الخاص بك:*", ""]
    for i, item in enumerate(reversed(log), start=1):
        msg_lines.append(
            f"---------------------------\n"
            f"{i}- {item['action']}\n"
            f"المبلغ: {item['amount']} ل.س\n"
            f"التفاصيل: {item['details']}\n"
            f"التاريخ: {item['time']}"
        )

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="سجل"))
    bot.edit_message_text("\n\n".join(msg_lines), call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def go_back_main(call):
    # مثلاً ترجع المستخدم للوحة الرئيسية
    bot.edit_message_text("🏠 مرحباً بك في القائمة الرئيسية.", call.message.chat.id, call.message.message_id)









############################## رسالة للدعم 
from telebot import types

ADMIN_IDS = [5504502257]  # تأكد أنّ هذا الآي دي بدأ المحادثة مع البوت

# ========== حالة الانتظار بين الخطوات ==========
pending_requests = {}

# --- 1. زر “تواصل مع الدعم الفني 📨” ---
@bot.callback_query_handler(func=lambda call: call.data == "دعم")
def handle_support_button(call):
    uid = call.from_user.id
    pending_requests[uid] = {"step": "awaiting_support_message"}
    bot.send_message(uid, "✍️ قم بكتابة رسالتك أو إرسال صورة هنا 👇")

# --- 2. استقبال نص أو صورة من المستخدم ---
@bot.message_handler(func=lambda msg: pending_requests.get(msg.from_user.id, {}).get("step") == "awaiting_support_message")
def handle_support_input(msg):
    uid = msg.from_user.id
    pending_requests[uid] = {
        "step": "awaiting_support_confirmation",
        "type": msg.content_type,
        "text": msg.text or msg.caption or "",
        "file_id": msg.photo[-1].file_id if msg.content_type == "photo" else None
    }
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ تأكيد الإرسال", callback_data="تأكيد_دعم"),
        types.InlineKeyboardButton("❌ إلغاء",       callback_data="إلغاء_دعم")
    )
    bot.send_message(uid, "هل تريد تأكيد إرسال هذه الرسالة للدعم؟", reply_markup=markup)

# --- 3. تأكيد أو إلغاء الإرسال ---
@bot.callback_query_handler(func=lambda call: call.data in ["تأكيد_دعم", "إلغاء_دعم"])
def support_decision(call):
    uid = call.from_user.id
    state = pending_requests.get(uid, {})
    if call.data == "إلغاء_دعم":
        pending_requests.pop(uid, None)
        bot.edit_message_text("❌ تم إلغاء الإرسال.", call.message.chat.id, call.message.message_id)
        return

    # تم التأكيد
    bot.edit_message_text("✅ تم الإرسال. سيتم الرد عليك بأقرب وقت.", call.message.chat.id, call.message.message_id)

    # إرسال إلى المشرفين
    for admin_id in ADMIN_IDS:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📨 الرد على المستخدم", callback_data=f"رد_دعم:{uid}"))
        try:
            if state["type"] == "text":
                bot.send_message(
                    admin_id,
                    f"<b>📥 رسالة من المستخدم (ID: {uid}):</b>\n\n{state['text']}",
                    parse_mode="HTML",
                    reply_markup=markup
                )
            else:
                bot.send_photo(
                    admin_id,
                    state["file_id"],
                    caption=f"<b>📥 صورة من المستخدم (ID: {uid}):</b>\n\n{state['text']}",
                    parse_mode="HTML",
                    reply_markup=markup
                )
        except:
            # إما الآي دي خطأ أو المستخدم لم يبدأ المحادثة
            pass

    pending_requests.pop(uid, None)

# --- 4. المشرف يضغط “📨 الرد على المستخدم” ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("رد_دعم:"))
def reply_to_user_prompt(call):
    admin_id = call.from_user.id
    if admin_id not in ADMIN_IDS:
        return

    target_id      = int(call.data.split(":")[1])
    admin_chat_id  = call.message.chat.id
    admin_msg_id   = call.message.message_id

    pending_requests[admin_id] = {
        "step": "replying_to_user",
        "target_user":   target_id,
        "admin_chat_id": admin_chat_id,
        "admin_msg_id":  admin_msg_id
    }
    bot.send_message(admin_chat_id, f"📝 اكتب الآن ردك للمستخدم (ID: {target_id}):")

# --- 5. المشرف يرسل الرد فعليًا ---
@bot.message_handler(func=lambda msg: pending_requests.get(msg.from_user.id, {}).get("step") == "replying_to_user")
def send_reply_to_user(msg):
    admin_id    = msg.from_user.id
    state       = pending_requests.pop(admin_id, {})
    target_id   = state.get("target_user")
    admin_chat  = state.get("admin_chat_id")
    admin_msg   = state.get("admin_msg_id")
    reply_text  = msg.text or ""

    # إرسال الرد للمستخدم بصيغة HTML
    reply_msg = (
        f"<b>📨 رد الدعم:</b>\n"
        f"<pre>{reply_text}</pre>\n"
        "هذه الرسالة لا يمكن الرد عليها.\n"
        "للتواصل من جديد اضغط \"تواصل مع الدعم الفني 📨\" من القائمة الرئيسية."
    )
    try:
        bot.send_message(target_id, reply_msg, parse_mode="HTML")
    except Exception as e:
        bot.send_message(admin_chat, f"❌ فشل إرسال الرد للمستخدم: {e}")

    # تأكيد للمشرف
    bot.send_message(admin_chat, "✅ تم إرسال الرد للمستخدم.")

    # حذف رسالة الدعم عند المشرف
    try:
        bot.delete_message(admin_chat, admin_msg)
    except:
        pass

    # حذف رسالة المشرف نفسها
    try:
        bot.delete_message(admin_chat, msg.message_id)
    except:
        pass



################### اهداء رصيد

@bot.callback_query_handler(func=lambda call: call.data == "إهداء")
def gift_balance(call):
    user_id = str(call.from_user.id)
    
    # إرسال إشعار للمستخدم بأنه سيتم تطبيق العمولة
    msg = "📢 سيتم تطبيق عمولة 10% على عملية الإهداء.\nمن فضلك، أدخل ID المستخدم الذي ترغب في إهدائه رصيد."
    bot.send_message(call.message.chat.id, msg)

    # وضع المستخدم في خطوة انتظار إدخال الـ ID
    pending_requests[user_id] = {"step": "gift", "data": {}}

@bot.message_handler(func=lambda message: pending_requests.get(str(message.from_user.id), {}).get("step") == "gift")
def handle_gift_input(message):
    user_id = str(message.from_user.id)
    gift_data = pending_requests[user_id]["data"]
    
    # تقسيم الرسالة المرسلة
    parts = message.text.split()
    
    # إذا كان النص يحتوي على ID والمبلغ
    if len(parts) == 2:
        target_user_id = parts[0]
        try:
            amount = float(parts[1])
        except ValueError:
            bot.send_message(message.chat.id, "❗ الرجاء إدخال مبلغ صحيح.")
            return
        
        # التأكد من أن المبلغ أكبر من 0 وأن المستخدم يملك رصيدًا كافيًا
        if amount <= 0:
            bot.send_message(message.chat.id, "❗ يجب أن يكون المبلغ أكبر من 0.")
            return
        
        user_balance = users.get(user_id, {}).get('balance', 0)
        if user_balance < amount:
            bot.send_message(message.chat.id, "❗ لا يوجد لديك رصيد كافٍ لإتمام الإهداء.")
            return
        
        # تطبيق العمولة 10%
        commission = amount * 0.10
        final_amount = amount - commission
        
        # خصم المبلغ من حساب المرسل
        users[user_id]['balance'] -= amount
        
        # إضافة المبلغ إلى حساب المهدى إليه
        if target_user_id in users:
            users[target_user_id]['balance'] += final_amount
        else:
            bot.send_message(message.chat.id, "❗ لم يتم العثور على هذا المستخدم.")
            return
        
        # حفظ البيانات بعد الإهداء
        save_users(users)

        # إرسال إشعارات
        bot.send_message(user_id, f"✅ تم خصم {amount} ل.س من رصيدك.\nتم إرسال {final_amount} ل.س إلى المستخدم {target_user_id}.")
        bot.send_message(target_user_id, f"🎁 تم إهدائك {final_amount} ل.س من المستخدم {user_id}.")
        
        # إشعار للمشرف
        for admin_id in ADMIN_IDS:
            bot.send_message(admin_id, f"📢 تم إتمام عملية إهداء:\n- المرسل: {user_id}\n- المبلغ: {amount} ل.س\n- تم خصم عمولة 10%\n- المبلغ النهائي المرسل: {final_amount} ل.س\n- المستقبل: {target_user_id}")

        # إنهاء انتظار الرد
        del pending_requests[user_id]
        
    else:
        bot.send_message(message.chat.id, "❗ يجب إدخال ID المستخدم والمبلغ المطلوب إهدائه، على سبيل المثال:\n`123456 100`")




#################################################################

@bot.callback_query_handler(func=lambda call: call.data in ["withdraw_bemo", "withdraw_baeer", "withdraw_hawala"])
def handle_withdraw_request(call):
    # إرسال رسالة للمستخدم بأن السحب متوقف حالياً
    bot.send_message(call.message.chat.id, "❌ السحب متوقف حالياً. يرجى المحاولة لاحقاً.")


####################################################################### شروحات 

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data == "دليل":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("📥 شحن رصيد في البوت", callback_data="شرح_شحن_بوت"))
        markup.row(types.InlineKeyboardButton("📤 سحب رصيد من البوت", callback_data="شرح_سحب_بوت"))
        markup.row(types.InlineKeyboardButton("🧾 انشاء حساب ايشانسي", callback_data="شرح_انشاء_ايشانسي"))
        markup.row(types.InlineKeyboardButton("💳 شحن حساب ايشانسي", callback_data="شرح_شحن_ايشانسي"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="📘 اختر شرح من القائمة التالية:", reply_markup=markup)

    elif call.data == "شرح_شحن_بوت":
        text = """📥 كيفية شحن رصيد ضمن البوت:
1- اضغط على شحن رصيد في البوت.
2- قم باختيار طريقة الدفع المناسبة لك.
3- قم بإرسال المبلغ المراد شحن البوت به إلى العنوان المطلوب (أقل مبلغ يمكن شحنه هو 5000 ل.س)
4- بعد إرسال المبلغ، ادخل كود عملية التحويل والمبلغ المرسل.
✅ تم شحن البوت بنجاح."""
        bot.send_message(call.message.chat.id, text)

    elif call.data == "شرح_سحب_بوت":
        text = """📤 كيفية سحب رصيد من البوت:
1- اضغط على سحب رصيد من البوت.
2- اختر طريقة السحب المناسبة.
3- ادخل معلوماتك حسب الطريقة.
4- ادخل المبلغ المراد سحبه.
✅ تم السحب."""
        bot.send_message(call.message.chat.id, text)

    elif call.data == "شرح_انشاء_ايشانسي":
        text = """🧾 خطوات انشاء حساب ايشانسي:
1- اضغط على ايشانسي.
2- اضغط على "حساب ايشانسي جديد".
3- ادخل اسم للحساب.
4- اختر كلمة سر (8 أرقام أو أكثر).
5- ادخل المبلغ المطلوب شحن الحساب به (بالليرة السورية).
6- انتظر 15 ثانية.
✅ تم انشاء الحساب."""
        bot.send_message(call.message.chat.id, text)

    elif call.data == "شرح_شحن_ايشانسي":
        text = """💳 خطوات شحن حساب ايشانسي:
1- اضغط على ايشانسي.
2- اضغط على "شحن حساب ايشانسي".
3- ادخل اسم أو معرف الحساب المراد شحنه.
4- ادخل المبلغ المطلوب.
5- انتظر 15 ثانية.
✅ تم شحن الحساب."""
        bot.send_message(call.message.chat.id, text)















# === بدء التشغيل === #
print("✅ البوت يعمل الآن...")
bot.infinity_polling()



