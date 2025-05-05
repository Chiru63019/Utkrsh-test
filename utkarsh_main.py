import os
import requests
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
import logging

# Bot Configuration
API_ID = 28526237  # अपना API ID भरें
API_HASH = "936db76a74f9a52cfb2cea8a62e4c20e"  # अपना API HASH भरें
BOT_TOKEN = "8116024471:AAHeLBLqKDGgQ4sc8x_xxy0htXnOydl4AEY"  # अपना Bot Token भरें

# Initialize Bot
app = Client("utkarsh_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def delete_messages(message_list):
    """Messages auto-delete helper"""
    await asyncio.sleep(30)
    for msg in message_list:
        try:
            await msg.delete()
        except:
            pass

@app.on_message(filters.command(["utkarsh"]))
async def utkarsh_handler(client: Client, message: Message):
    user = message.from_user
    temp_msgs = []
    
    try:
        # Step 1: Get Mobile Number
        msg1 = await message.reply("📱 **Utkarsh Login**\nअपना रजिस्टर्ड मोबाइल नंबर भेजें:", quote=True)
        temp_msgs.append(msg1)
        
        mobile_msg = await client.listen(message.chat.id)
        temp_msgs.append(mobile_msg)
        mobile = mobile_msg.text

        # Step 2: Send OTP
        msg2 = await message.reply("⚡ OTP भेजा जा रहा है...", quote=True)
        otp_url = "https://utkarshclassesapi.classx.co.in/api/v1/auth/send-otp/"
        otp_res = requests.post(otp_url, json={"mobile": mobile})
        
        if otp_res.status_code != 200 or not otp_res.json().get("success"):
            await msg2.edit("❌ OTP भेजने में समस्या! कृपया बाद में प्रयास करें")
            return

        # Step 3: Verify OTP
        msg3 = await message.reply("🔢 6 अंकों का OTP भेजें (जैसे: 123456):", quote=True)
        temp_msgs.append(msg3)
        
        otp_msg = await client.listen(message.chat.id)
        temp_msgs.append(otp_msg)
        otp = otp_msg.text

        verify_url = "https://utkarshclassesapi.classx.co.in/api/v1/auth/verify-otp/"
        verify_res = requests.post(verify_url, json={"mobile": mobile, "otp": otp})
        
        if verify_res.status_code != 200 or not verify_res.json().get("success"):
            await msg3.edit("❌ गलत OTP! फिर से प्रयास करें")
            return

        # Step 4: Get Courses
        token = verify_res.json()["data"]["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        msg4 = await message.reply("📚 कोर्स लिस्ट प्राप्त की जा रही है...", quote=True)
        courses_res = requests.get(
            "https://utkarshclassesapi.classx.co.in/api/utk/course-list",
            headers=headers
        )
        
        if courses_res.status_code != 200:
            await msg4.edit("❌ कोर्स लिस्ट प्राप्त नहीं हो सकी")
            return

        courses = [
            f"**{course['id']}** - {course['course_name']}\n"
            f"Batch: {course['batch_name']}\n"
            f"Duration: {course['duration']}\n"
            for course in courses_res.json()["data"]
        ]
        
        course_list = "\n".join(courses)
        msg5 = await message.reply(
            f"📋 **उपलब्ध कोर्स:**\n\n{course_list}\n\n"
            "👉 कोर्स ID भेजें (जैसे: 123):",
            quote=True
        )
        temp_msgs.append(msg5)

        # Step 5: Get Course Content
        course_id_msg = await client.listen(message.chat.id)
        temp_msgs.append(course_id_msg)
        course_id = course_id_msg.text

        msg6 = await message.reply(f"🔍 कोर्स कंटेंट प्राप्त किया जा रहा है (ID: {course_id})...", quote=True)
        content_url = f"https://utkarshclassesapi.classx.co.in/api/utk/course-content?course_id={course_id}"
        content_res = requests.get(content_url, headers=headers)
        
        if content_res.status_code != 200:
            await msg6.edit("❌ कोर्स कंटेंट प्राप्त नहीं हो सका")
            return

        # Process Content
        content_data = content_res.json()["data"]
        output = []
        
        for chapter in content_data["chapters"]:
            output.append(f"\n📖 **Chapter {chapter['chapter_no']}:** {chapter['chapter_name']}\n")
            
            for lecture in chapter["lectures"]:
                if lecture.get("video_url"):
                    output.append(
                        f"▶️ Lecture {lecture['lecture_no']}: {lecture['title']}\n"
                        f"🔗 URL: {lecture['video_url']}\n"
                        f"⏳ Duration: {lecture['duration']}\n"
                        "━"*40 + "\n"
                    )

        if not output:
            await msg6.edit("❌ इस कोर्स में कोई वीडियो उपलब्ध नहीं है")
            return

        # Generate TXT File
        filename = f"Utkarsh_{course_id}_{user.id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

        # Send File
        await message.reply_document(
            filename,
            caption=f"✅ Utkarsh Course Links\n\nCourse ID: {course_id}\nTotal Videos: {len(output)//2}",
            quote=True
        )
        
        # Cleanup
        os.remove(filename)
        await msg6.delete()

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.reply(f"⚠️ त्रुटि हो गई: {str(e)}", quote=True)
    
    finally:
        await delete_messages(temp_msgs)

if __name__ == "__main__":
    print("Bot started...")
    app.run()
