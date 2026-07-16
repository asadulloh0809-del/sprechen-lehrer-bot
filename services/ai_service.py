import os
from groq import AsyncGroq
import config

client = AsyncGroq(api_key=config.GROQ_API_KEY)

async def analyze_voice(file_path: str, lang: str = "uz", level: str = "A2") -> str:
    # Tilni va darajani sozlash
    if lang == "de":
        teacher_lang = "Nemis (Deutsch)"
        explanation_lang = "NEMIS TILIDA (auf Deutsch)"
    else:
        teacher_lang = "O'zbek (Uzbek)"
        explanation_lang = "O'ZBEK TILIDA"
        
    SYSTEM_PROMPT = f"""
Sen tajribali nemis tili o'qituvchisisan. Isming "Deutsch Lehrer". {teacher_lang} tilida gaplashuvchi o'quvchilarga nemis tilining "Sprechen" ko'nikmasini rivojlantirishda yordam berasan.

O'quvchining joriy darajasi: {level}. 
Tushuntirishlarni aynan shu daraja doirasida, o'quvchiga tushunarli qilib ber. Agar daraja A1-A2 bo'lsa juda sodda tilda, B1-B2 bo'lsa murakkabroq tushuntir.

Senga o'quvchi aytgan gapning matni yuboriladi. Sening vazifang:
1. Matnni tahlil qilib, grammatik va logik xatolarni topish.
2. Fikrni qanday qilib tabiiyroq va to'g'riroq ifodalash mumkinligini yozib berish.
3. Yo'l qo'yilgan xatolarni {explanation_lang} tushunarli qilib tushuntirib berish.

Javobingni Telegram qabul qilishi uchun FAQAT HTML taglaridan (<b>, <i>, <u>, <s>, <code>, <pre>) foydalanib yozgin. Markdown (**, *) ishlata ko'rma!

Javobing strukturasi taxminan shunday bo'lishi kerak:
<b>Sizning matningiz:</b> (o'quvchi nima deganini yozing)
<b>Xatolar va tushuntirish:</b> ({explanation_lang} tushuntirish)
<b>Yaxshiroq variant:</b> (Nemis tilida to'g'ri variantni yozish)

Eslatma: O'quvchiga doim do'stona va ruhlantiruvchi ohangda murojaat qil.
"""

    try:
        # Asinxron Whisper
        with open(file_path, "rb") as file:
            transcription = await client.audio.transcriptions.create(
                file=(file_path, file.read()),
                model="whisper-large-v3",
                language="de"
            )
        
        user_text = transcription.text
        
        if not user_text or len(user_text.strip()) == 0:
            if lang == "de":
                return "Entschuldigung, ich konnte leider nichts verstehen. Bitte sprechen Sie noch einmal, etwas lauter und deutlicher."
            else:
                return "Kechirasiz, ovozli xabaringizdan hech qanday so'zni tushuna olmadim. Iltimos, qaytadan, balandroq va aniqroq gapirib yuboring."

        # Asinxron Llama 3 tahlil
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"O'quvchi shunday dedi: '{user_text}'"
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error in ai_service: {e}")
        if lang == "de":
            return "Entschuldigung, beim Analysieren der Nachricht ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut."
        else:
            return "Kechirasiz, xabarni tahlil qilishda xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring."
