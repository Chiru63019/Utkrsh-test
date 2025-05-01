import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen

# ================== CONFIG ==================
API_ID = 28526237
API_HASH = "936db76a74f9a52cfb2cea8a62e4c20e"
BOT_TOKEN = "7780658331:AAFVkysE818mG5NFeK0UiCp_n7a3pNZmnkE"
SUDO_USERS = [6486192717]

def one(user_id):
    return user_id in SUDO_USERS

# =============== START BOT ===============
bot = Client("utkarsh_scraper_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_command(bot: Client, message: Message):
    await message.reply_text("Hello! Use /utkarsh to scrape Utkarsh Classes content.")

@bot.on_message(filters.command("utkarsh"))
async def utkarsh_handler(bot: Client, message: Message):
    if not one(message.from_user.id):
        return await message.reply_text("✨ Hello Sir,\n\nYou are not authorized to use this bot.")
    
    editable = await message.reply_text("Send your Utkarsh registered mobile number:")
    input1 = await bot.listen(editable.chat.id)
    phone = input1.text.strip()

    # Step 1: Send OTP (✅ updated)
    send_otp_url = "https://utkarshclassesapi.classx.co.in/api/v1/auth/send-otp/"
    send_headers = {
        "Content-Type": "application/json",
        "User-Agent": "okhttp/4.9.1"
    }

    r1 = requests.post(send_otp_url, json={"mobile": phone}, headers=send_headers)

    try:
        r1_data = r1.json()
        error_msg = r1_data.get("message") or r1_data.get("error") or str(r1_data)
    except Exception as e:
        error_msg = f"❌ Server ने सही जवाब नहीं भेजा:\n\n{r1.text}\n\nError: {e}"

    if r1.status_code != 200 or not r1.text.strip().startswith("{"):
        return await editable.edit(f"❌ OTP भेजने में समस्या:\n\n{error_msg}")
    
    await editable.edit("✅ OTP sent successfully. Now send the OTP you received:")
    input2 = await bot.listen(editable.chat.id)
    otp = input2.text.strip()

    # Step 2: Verify OTP (✅ updated)
    verify_url = "https://utkarshclassesapi.classx.co.in/api/v1/auth/verify-otp/"
    r2 = requests.post(verify_url, json={"mobile": phone, "otp": otp}, headers=send_headers)

    try:
        data = r2.json()
    except:
        return await editable.edit("OTP verification failed. Server response invalid.")

    if "access_token" not in data:
        return await editable.edit("❌ OTP verification failed.")

    token = data["access_token"]
    user_id = str(data.get("user", {}).get("id") or "0")

    headers = {
        "Authorization": f"Bearer {token}",
        "User-ID": user_id,
    }

    # Step 3: Get Courses
    r3 = requests.get("https://utkarshclassesapi.classx.co.in/api/utk/course-list", headers=headers)
    courses = r3.json().get("data", [])
    if not courses:
        return await editable.edit("No courses found.")

    text = "**Your Courses:**\n\n"
    for c in courses:
        text += f"`{c['id']}` - {c['title']}\n"
    await editable.edit(text)

    editable2 = await message.reply_text("Send a Course ID to fetch content:")
    input3 = await bot.listen(editable2.chat.id)
    course_id = input3.text.strip()

    # Step 4: Get Course Content
    content_url = f"https://utkarshclassesapi.classx.co.in/api/utk/course-content?course_id={course_id}"
    r4 = requests.get(content_url, headers=headers)
    content_data = r4.json().get("data", {}).get("content", [])

    if not content_data:
        return await message.reply_text("No content found in this course.")

    to_write = ""
    for item in content_data:
        title = item.get("title", "Untitled")
        url = item.get("video_url") or item.get("file_url")
        if url:
            to_write += f"{title}:{url}\n"

    filename = f"utkarsh_{course_id}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(to_write)

    with open(filename, "rb") as f:
        await bot.send_document(message.chat.id, f, caption="Here is your txt file.")

print("Bot is running...")
bot.run()
