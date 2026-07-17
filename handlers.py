from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction
import os
import asyncio
from gtts import gTTS
from services.ai_service import analyze_voice, analyze_text_word
import database as db

router = Router()

def get_lang_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz"),
            InlineKeyboardButton(text="🇩🇪 Deutsch", callback_data="lang_de")
        ]
    ])

def get_level_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="A1", callback_data="lvl_A1"),
            InlineKeyboardButton(text="A2", callback_data="lvl_A2")
        ],
        [
            InlineKeyboardButton(text="B1", callback_data="lvl_B1"),
            InlineKeyboardButton(text="B2", callback_data="lvl_B2")
        ]
    ])

@router.message(CommandStart())
async def cmd_start(message: Message):
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    welcome_text = (
        "Hallo! Men sizning <b>Deutsch Lehrer</b> botingizman.\n\n"
        "Iltimos, muloqot tilini tanlang:\n"
        "Bitte wählen Sie die Sprache aus:"
    )
    await message.answer(welcome_text, reply_markup=get_lang_kb(), parse_mode="HTML")

@router.callback_query(F.data.startswith("lang_"))
async def process_lang_selection(callback: CallbackQuery):
    selected_lang = callback.data.split("_")[1]
    db.set_user_pref(callback.from_user.id, "language", selected_lang)
    
    if selected_lang == "uz":
        text = "Yaxshi! Endi nemis tilini bilish darajangizni tanlang:"
    else:
        text = "Sehr gut! Bitte wählen Sie Ihr Deutschniveau aus:"
        
    await callback.message.edit_text(text, reply_markup=get_level_kb())

@router.callback_query(F.data.startswith("lvl_"))
async def process_level_selection(callback: CallbackQuery):
    selected_level = callback.data.split("_")[1]
    db.set_user_pref(callback.from_user.id, "level", selected_level)
    
    lang, _ = db.get_user_pref(callback.from_user.id)
    
    if lang == "uz":
        text = (
            f"Ajoyib! Darajangiz: <b>{selected_level}</b>.\n\n"
            "Menga istalgan mavzuda nemis tilida ovozli xabar yoki matn yuboring, men xatolaringizni to'g'irlab, yordam beraman.\n\n"
            "<i>Los geht's!</i> (Qani ketdik!)"
        )
    else:
        text = (
            f"Perfekt! Ihr Niveau: <b>{selected_level}</b>.\n\n"
            "Bitte senden Sie mir eine Sprachnachricht oder einen Text auf Deutsch. Ich werde Ihre Fehler korrigieren und Ihnen helfen, sich zu verbessern.\n\n"
            "<i>Los geht's!</i>"
        )
        
    await callback.message.edit_text(text, parse_mode="HTML")

@router.message(Command("wort"))
async def cmd_wort(message: Message):
    lang, _ = db.get_user_pref(message.from_user.id)
    if lang == "uz":
        text = "Menga istalgan nemischa so'z yoki gapni yozib yuboring. Men uni to'g'rilayman va qanday talaffuz qilinishini aytib beraman! 🎙"
    else:
        text = "Schreiben Sie mir ein beliebiges deutsches Wort oder einen Satz. Ich werde es korrigieren und Ihnen die Aussprache senden! 🎙"
    await message.answer(text)

@router.message(Command("help"))
async def cmd_help(message: Message):
    lang, _ = db.get_user_pref(message.from_user.id)
    if lang == "uz":
        help_text = (
            "<b>Yordam bo'limi:</b>\n"
            "Botga har qanday nemis tilidagi ovozli xabar yoki matn yuboring. "
            "Bot uni tahlil qilib sizga tavsiyalar beradi.\n\n"
            "/start - Til va darajani o'zgartirish\n"
            "/wort - So'z talaffuzini o'rganish\n"
            "/stats - O'z statistikangizni ko'rish"
        )
    else:
        help_text = (
            "<b>Hilfe:</b>\n"
            "Senden Sie einfach eine Sprachnachricht oder einen Text auf Deutsch. "
            "Der Bot analysiert sie und gibt Ihnen Feedback.\n\n"
            "/start - Sprache und Niveau ändern\n"
            "/wort - Aussprache lernen\n"
            "/stats - Ihre Statistiken anzeigen"
        )
    await message.answer(help_text, parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    count = db.get_user_stats(message.from_user.id)
    lang, _ = db.get_user_pref(message.from_user.id)
    if lang == "uz":
        text = f"Siz shu paytgacha jami <b>{count} ta</b> ovozli xabar yuborgansiz. Barakalla!"
    else:
        text = f"Sie haben bisher insgesamt <b>{count}</b> Sprachnachrichten gesendet. Gut gemacht!"
    await message.answer(text, parse_mode="HTML")

@router.message(F.voice)
async def handle_voice(message: Message, bot: Bot):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    
    lang, level = db.get_user_pref(message.from_user.id)
    
    if lang == "uz":
        wait_text = "<i>Ovozli xabaringiz qabul qilindi. Tahlil qilinmoqda... ⏳</i>"
        err_text = "Kechirasiz, xatolik yuz berdi. Iltimos, keyinroq qaytadan urinib ko'ring."
    else:
        wait_text = "<i>Ihre Sprachnachricht wurde empfangen. Wird analysiert... ⏳</i>"
        err_text = "Entschuldigung, ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut."

    wait_msg = await message.answer(wait_text, parse_mode="HTML")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    file_id = message.voice.file_id
    file_info = await bot.get_file(file_id)
    
    os.makedirs("temp", exist_ok=True)
    file_path = f"temp/{file_id}.ogg"
    
    await bot.download_file(file_info.file_path, destination=file_path)
    
    try:
        analysis_result = await analyze_voice(file_path, lang=lang, level=level)
        db.increment_message_count(message.from_user.id)
        await wait_msg.edit_text(analysis_result, parse_mode="HTML")
    except Exception as e:
        print(f"Error handling voice: {e}")
        await wait_msg.edit_text(err_text, parse_mode="HTML")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@router.message(F.text & ~F.text.startswith('/'))
async def handle_text(message: Message, bot: Bot):
    db.add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    lang, level = db.get_user_pref(message.from_user.id)
    
    wait_text = "<i>Matn tahlil qilinmoqda... ⏳</i>" if lang == "uz" else "<i>Wird analysiert... ⏳</i>"
    wait_msg = await message.answer(wait_text, parse_mode="HTML")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    explanation, correct_word = await analyze_text_word(message.text, lang, level)
    
    if not correct_word:
        err_text = "Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring." if lang == "uz" else "Ein Fehler ist aufgetreten."
        await wait_msg.edit_text(err_text)
        return
        
    await wait_msg.edit_text(explanation, parse_mode="HTML")
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.RECORD_VOICE)
    
    try:
        def generate_tts():
            tts = gTTS(text=correct_word, lang='de')
            os.makedirs("temp", exist_ok=True)
            path = f"temp/{message.from_user.id}_word.ogg"
            tts.save(path)
            return path
            
        audio_path = await asyncio.to_thread(generate_tts)
        audio = FSInputFile(audio_path)
        
        caption = "🎙 Talaffuz (Aussprache)" if lang == "uz" else "🎙 Aussprache"
        await message.answer_voice(audio, caption=caption)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
    except Exception as e:
        print(f"Error generating TTS: {e}")
