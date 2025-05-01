import asyncio
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen

# ========== CONFIGURATION ==========
API_ID = 28526237
API_HASH = "936db76a74f9a52cfb2cea8a62e4c20e"
BOT_TOKEN = "7780658331:AAFVkysE818mG5NFeK0UiCp_n7a3pNZmnkE"
SUDO_USERS = [6486192717]

def is_sudo(user_id):
    return user_id in SUDO_USERS

bot = Client("utkarsh_scraper_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@bot.on_message(filters.command("start"))
async def start_cmd(bot: Client, message: Message):
    await message.reply_text("Welcome to Utkarsh Scraper Bot!\n\nUse /utkarsh to begin.")

@bot.on_message(filters.command("utkarsh"))
async def utkarsh_handler(bot: Client, message: Message):
    if not is_sudo(message.from_user.id):
        return await message.reply_text("Access Denied. You are not authorized.")

    ask = await message.reply_text("Send your Utkarsh registered mobile number:")
    input1 = await bot.listen(ask.chat.id)
    phone = input1.text.strip()

    # Step 1: Send OTP (NEW WORKING API)
    r1 = requests.post(
        "https://utkarshclassesapi.classx.co.in/api/utk/send-otp",
        json={"mobile": phone}
    )

    try:
        r1_data = r1.json()
        if r1_data.get("message"):
            await ask.edit(f"✅ OTP Sent: {r1_data['message']}")
        else:
            return await ask.edit("❌ OTP भेजने में समस्या:\n\nकोई मैसेज नहीं मिला।")
    except Exception as e:
        return await ask.edit(f"❌ OTP भेजने में समस्या:\n\n{r1.text}\n\nError: {e}")

    ask_otp = await message.reply_text("Now send the OTP you received:")
    input2 = await bot.listen(ask_otp.chat.id)
    otp = input2.text.strip()

    # Step 2: Verify OTP
    r2 = requests.post(
        "https://utkarshclassesapi.classx.co.in/api/utk/verify-otp",
        json={"mobile": phone, "otp": otp}
    )

    try:
        r2_data = r2.json()
        token = r2_data["data"]["token"]
        user_id = str(r2_data["data"]["user"]["id"])
    except Exception as e:
        return await ask_otp.edit(f"❌ OTP Verification Failed:\n\n{r2.text}\n\nError: {e}")

    headers = {
        "Authorization": f"Bearer {token}",
        "User-ID": user_id
    }

    # Step 3: Get Course List
    r3 = requests.get("https://utkarshclassesapi.classx.co.in/api/utk/course-list", headers=headers)
    courses = r3.json().get("data", [])
    if not courses:
        return await message.reply_text("No courses found.")

    course_text = "**Your Courses:**\n\n"
    for course in courses:
        course_text += f"`{course['id']}` - {course['title']}\n"

    await message.reply_text(course_text)

    ask_course = await message.reply_text("Send course ID to get content:")
    input3 = await bot.listen(ask_course.chat.id)
    course_id = input3.text.strip()

    # Step 4: Fetch Content
    r4 = requests.get(f"https://utkarshclassesapi.classx.co.in/api/utk/course-content?course_id={course_id}", headers=headers)
    content_data = r4.json().get("data", {}).get("content", [])

    if not content_data:
        return await message.reply_text("No content found in this course.")

    to_write = ""
    for item in content_data:
        title = item.get("title", "Untitled")
        url = item.get("video_url") or item.get("file_url")
        if url:
            to_write += f"{title} : {url}\n"

    filename = f"utkarsh_{course_id}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(to_write)

    with open(filename, "rb") as f:
        await bot.send_document(message.chat.id, f, caption="Here is your course content.")

print("Bot is running...")
bot.run()
