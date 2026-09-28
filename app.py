import os
from flask import Flask, render_template_string, request, redirect, url_for
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = '8755176846:AAGNHyaxfWRSowqV1yPAhQfiYQ4VHO3txK0'
ADMIN_ID = 8937305240

bot = telebot.TeleBot(TOKEN, threaded=False)
app = Flask(__name__)

# আপনার Render ওয়েবসাইটের লাইভ লিংকটি এখানে বসান (শেষে স্ল্যাশ / বাদ দিয়ে)
# উদাহরণ: https://gotask-bot.onrender.com
RENDER_URL = 'https://gotask-bot.onrender.com'

user_balances = {}
pending_tasks = {}
pending_withdrawals = {}

task_counter = 0
withdraw_counter = 0

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("👤 প্রোফাইল"),
        KeyboardButton("💰 কাজ"),
        KeyboardButton("🏦 উত্তোলন"),
        KeyboardButton("🛠 সাপোর্ট"),
        KeyboardButton("👥 আমার রেফারেল"),
        KeyboardButton("📖 কীভাবে কাজ করব")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    name = message.from_user.first_name
    bot.send_message(message.chat.id, f"🌟 **GoTask Pay এ স্বাগতম, {name}!**\n\nনিচের মেনু থেকে কাজ শুরু করুন:", parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "💰 কাজ")
def task_menu(message):
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📸 Instagram Task (3 ৳)", callback_data="task_insta"),
        InlineKeyboardButton("📘 Facebook Task (4 ৳)", callback_data="task_fb")
    )
    bot.send_message(message.chat.id, "📊 **প্লাটফর্ম সিলেক্ট করুন:**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["task_insta", "task_fb"])
def generate_task_data(call):
    is_insta = "insta" in call.data
    platform = "Instagram" if is_insta else "Facebook"
    
    fname = "Alexander Smith" if is_insta else "David Johnson"
    uname = f"user_{os.urandom(3).hex()}"
    pwd = f"Pass@{os.urandom(2).hex()}99"
    
    text = (
        f"⚡ **নতুন {platform} টাস্ক!**\n\n"
        f"এই ডিটেইলস দিয়ে অ্যাকাউন্ট খুলে নিচের **'Done & Submit'** বাটনে ক্লিক করুন:\n\n"
        f"📌 **নাম:** `{fname}`\n"
        f"👤 **ইউজারনেম:** `{uname}`\n"
        f"🔑 **পাসওয়ার্ড:** `{pwd}`\n\n"
        f"⚠️ একাউন্ট খোলার পর কনফার্ম করুন।"
    )
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Done & Submit", callback_data=f"sub_{platform}_{fname}_{uname}_{pwd}"))
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def handle_submission(call):
    global task_counter
    parts = call.data.split("_")
    platform = parts[1]
    fname = parts[2]
    uname = parts[3]
    pwd = parts[4]
    
    chat_id = call.message.chat.id
    user_name = call.from_user.first_name
    
    task_counter += 1
    t_id = str(task_counter)
    
    pending_tasks[t_id] = {
        "chat_id": chat_id,
        "user_name": user_name,
        "platform": platform,
        "fname": fname,
        "uname": uname,
        "pwd": pwd
    }
    
    bot.edit_message_text("⏳ আপনার একাউন্ট ডিটেইলস এডমিন প্যানেলে রিভিউয়ের জন্য পাঠানো হয়েছে। চেক করার পর ব্যালেন্স যোগ হবে।", chat_id, call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "👤 প্রোফাইল")
def profile_view(message):
    bal = user_balances.get(message.chat.id, 0.0)
    bot.reply_to(message, f"👤 **আপনার প্রোফাইল**\n\n💰 বর্তমান ব্যালেন্স: {bal} ৳", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🏦 উত্তোলন")
def withdraw_request(message):
    bot.reply_to(message, "টাকা উত্তোলনের জন্য আপনার বিকাশ/নগদ নম্বর এবং অ্যামাউন্ট এভাবে লিখুন:\nযেমন: `withdraw bKash 01700000000 150`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text.startswith("withdraw"))
def process_withdraw(message):
    global withdraw_counter
    try:
        parts = message.text.split()
        method = parts[1]
        number = parts[2]
        amount = float(parts[3])
        
        chat_id = message.chat.id
        bal = user_balances.get(chat_id, 0.0)
        
        if bal < amount:
            bot.reply_to(message, "⚠️ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই!")
            return
            
        withdraw_counter += 1
        w_id = str(withdraw_counter)
        
        pending_withdrawals[w_id] = {
            "chat_id": chat_id,
            "user_name": message.from_user.first_name,
            "method": method,
            "number": number,
            "amount": amount
        }
        
        bot.reply_to(message, "✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে এডমিন প্যানেলে পাঠানো হয়েছে।")
    except:
        bot.reply_to(message, "⚠️ ফরম্যাট সঠিক নয়। লিখুন: withdraw bKash 017XXXXXXXX 150")

@bot.message_handler(func=lambda message: message.text == "🛠 সাপোর্ট")
def support_section(message):
    bot.reply_to(message, "💬 কোনো সমস্যা হলে এডমিনের সাথে যোগাযোগ করুন।")

@bot.message_handler(func=lambda message: message.text == "👥 আমার রেফারেল")
def referral_section(message):
    bot.reply_to(message, "🔗 আপনার রেফারেল লিংক:\nhttps://t.me/TopOTP52_bot?start=ref12345")

@bot.message_handler(func=lambda message: message.text == "📖 কীভাবে কাজ করব")
def how_to_work(message):
    bot.reply_to(message, "📖 **কীভাবে কাজ করবেন:**\n\n১. '💰 কাজ' বাটনে ক্লিক করুন।\n২. ইনস্টাগ্রাম বা ফেসবুক সিলেক্ট করলে একটি নাম, ইউজারনেম ও পাসওয়ার্ড পাবেন।\n৩. ওই তথ্য দিয়ে একাউন্ট খুলে 'Done & Submit' দিন।\n৪. এডমিন চেক করে এপ্রুভ করলেই আপনার ব্যালেন্সে টাকা যোগ হবে।")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - GoTask Pay</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f7f6; margin: 0; padding: 20px; }
        h1, h2 { color: #333; }
        .section { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; border: 1px solid #ddd; text-align: left; }
        th { background-color: #007BFF; color: white; }
        .btn { padding: 6px 12px; text-decoration: none; color: white; border-radius: 4px; border: none; cursor: pointer; }
        .btn-success { background-color: #28a745; }
        .btn-danger { background-color: #dc3545; }
    </style>
</head>
<body>
    <h1>🛠️ Admin Control Panel</h1>

    <div class="section">
        <h2>📥 Pending Task Submissions</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>User Name</th>
                <th>Platform</th>
                <th>Full Name</th>
                <th>Username</th>
                <th>Password</th>
                <th>Action</th>
            </tr>
            {% for tid, t in tasks.items() %}
            <tr>
                <td>{{ tid }}</td>
                <td>{{ t.user_name }}</td>
                <td>{{ t.platform }}</td>
                <td><b>{{ t.fname }}</b></td>
                <td><code>{{ t.uname }}</code></td>
                <td><code>{{ t.pwd }}</code></td>
                <td>
                    <a href="/approve_task/{{ tid }}" class="btn btn-success">Approve</a>
                    <a href="/reject_task/{{ tid }}" class="btn btn-danger">Reject</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="7">No pending tasks.</td></tr>
            {% endfor %}
        </table>
    </div>

    <div class="section">
        <h2>💸 Pending Withdrawal Requests</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>User Name</th>
                <th>Method</th>
                <th>Number</th>
                <th>Amount</th>
                <th>Action</th>
            </tr>
            {% for wid, w in withdrawals.items() %}
            <tr>
                <td>{{ wid }}</td>
                <td>{{ w.user_name }}</td>
                <td>{{ w.method }}</td>
                <td><b>{{ w.number }}</b></td>
                <td>{{ w.amount }} ৳</td>
                <td>
                    <a href="/approve_withdraw/{{ wid }}" class="btn btn-success">Confirm & Pay</a>
                    <a href="/reject_withdraw/{{ wid }}" class="btn btn-danger">Reject</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="6">No pending withdrawals.</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/')
def admin_dashboard():
    return render_template_string(HTML_TEMPLATE, tasks=pending_tasks, withdrawals=pending_withdrawals)

# টেলিগ্রাম থেকে আসা মেসেজ রিসিভ করার ওয়েবহুক রুট
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Invalid message", 403

@app.route('/approve_task/<tid>')
def approve_task(tid):
    if tid in pending_tasks:
        t = pending_tasks[tid]
        reward = 3 if t['platform'] == "Instagram" else 4
        current = user_balances.get(t['chat_id'], 0.0)
        user_balances[t['chat_id']] = current + reward
        try:
            bot.send_message(t['chat_id'], f"🎉 অভিনন্দন! আপনার জমা দেওয়া {t['platform']} একাউন্ট এডমিন চেক করে **এপ্রুভ** করেছেন। আপনার একাউন্টে {reward} টাকা যোগ হয়েছে।")
        except:
            pass
        del pending_tasks[tid]
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_task/<tid>')
def reject_task(tid):
    if tid in pending_tasks:
        t = pending_tasks[tid]
        try:
            bot.send_message(t['chat_id'], f"⚠️ দুঃখিত! আপনার জমা দেওয়া {t['platform']} একাউন্টটি সঠিক না থাকায় এডমিন **রিজেক্ট** করেছেন।")
        except:
            pass
        del pending_tasks[tid]
    return redirect(url_for('admin_dashboard'))

@app.route('/approve_withdraw/<wid>')
def approve_withdraw(wid):
    if wid in pending_withdrawals:
        w = pending_withdrawals[wid]
        chat_id = w['chat_id']
        amount = w['amount']
        current = user_balances.get(chat_id, 0.0)
        if current >= amount:
            user_balances[chat_id] = current - amount
        try:
            bot.send_message(chat_id, f"✅ আপনার উইথড্র সফল হয়েছে! আপনার {w['method']} ({w['number']}) নম্বরে {amount} টাকা পাঠানো হয়েছে।")
        except:
            pass
        del pending_withdrawals[wid]
    return redirect(url_for('admin_dashboard'))

@app.route('/reject_withdraw/<wid>')
def reject_withdraw(wid):
    if wid in pending_withdrawals:
        w = pending_withdrawals[wid]
        try:
            bot.send_message(w['chat_id'], "⚠️ আপনার উইথড্র রিকোয়েস্টটি বাতিল করা হয়েছে।")
        except:
            pass
        del pending_withdrawals[wid]
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    # ওয়েবহুক সেটআপ করা
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{TOKEN}")
    app.run(host='0.0.0.0', port=port)
