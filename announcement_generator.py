import openai
import pygame
import random
import time
import os
import numpy as np
from pydub import AudioSegment, effects
from scipy.signal import lfilter, butter
from scipy.io.wavfile import read, write
import json
from pydub import AudioSegment
from pydub.effects import low_pass_filter, high_pass_filter
import tempfile
import pyttsx3
import re

def check():
    """Kontrola OpenAI API klíče pouze při použití OpenAI generátoru."""
    if config.get("announcement_generator", "free") == "openai" and not openai.api_key:
        print("⚠️ Warning: OpenAI API key is not set! Switching to offline generator.")
        config["announcement_generator"] = "free"


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Složka, kde je tento skript
SAFETY_VIDEO_DIR = os.path.join(SCRIPT_DIR, "safety_videos")  # Cesta ke složce s videi


# 🌍 Pouze tyto fáze se překládají do všech jazyků
MULTILINGUAL_ANNOUNCEMENTS = {"Gate", "TaxiAfterLanding", "Safety"}

CONFIG_FILE = "config.json"

# 🔄 Funkce pro načtení konfigurace
def load_config():
    """Načte konfiguraci z config.json, pokud neexistuje, vrátí prázdné hodnoty."""
    if not os.path.exists(CONFIG_FILE):
        return {
            "captain_name": "",
            "first_officer": "",
            "openai_api_key": "",
            "announcement_generator": "" 
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 📂 Načtení konfigurace
config = load_config()

# 🔑 Použití OpenAI API klíče
openai.api_key = config.get("openai_api_key", "")

# 📢 Slovník obsahující hlášení pro jednotlivé fáze letu
ANNOUNCEMENTS = {
    "Gate": "Ladies and gentlemen, this is your captain speaking. My name is {captain_name} "
                      "and together with my first officer {first_officer}, we welcome you onboard flight {flight_number} "
                      "from {origin} to {destination} aboard our {aircraft}. Our flight duration will be {flight_duration}. "
                      "Thank you for choosing {airline} for your journey today.",
    
    "Pushback": "Cabin crew, arm doors and crosscheck.",
    
    "Takeoff": "Cabin crew, seats for takeoff.",
    
    "Descent": "Cabin crew, prepare cabin for landing.",
    
    "Final": "Cabin crew, seats for landing.",
    
    "TaxiAfterLanding": "Ladies and gentlemen, welcome to {destination}. The local time is {local_time} "
                     "and the outside temperature is {temperature} °C. Thank you for choosing {airline} "
                     "for your flight, and we wish you a pleasant holiday, a safe journey home, or a smooth continuation of your travels. "
                     "On behalf of {airline}, we wish you a wonderful day.",
    
    "Deboarding": "Cabin crew, disarm doors and crosscheck."
}


# Define FFMPEG paths correctly
FFMPEG_DIR = os.path.join(SCRIPT_DIR, "ffmpeg", "bin")  # Adjusted to include 'bin'
ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")

# Set Pydub paths for FFMPEG
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path

# Add FFMPEG/bin to system PATH
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# Hlasy pro kapitána a cabin crew
voice_captain = "onyx"
crew_voices = ["coral", "nova", "sage", "shimmer"]
voice_crew = random.choice(crew_voices)  # Náhodný hlas cabin crew

# Možné styly hlášení kapitána
captain_styles = ["profesionálně", "stroze", "přátelsky", "zkušeně"]

# 🌍 Možné jazyky
valid_languages = [
    "afrikaans", "arabic", "armenian", "azerbaijani", "belarusian", "bosnian", "bulgarian",
    "catalan", "chinese", "croatian", "czech", "danish", "dutch", "english", "estonian",
    "finnish", "french", "galician", "german", "greek", "hebrew", "hindi", "hungarian",
    "icelandic", "indonesian", "italian", "japanese", "kannada", "kazakh", "korean",
    "latvian", "lithuanian", "macedonian", "malay", "marathi", "maori", "nepali",
    "norwegian", "persian", "polish", "portuguese", "romanian", "russian", "serbian",
    "slovak", "slovenian", "spanish", "swahili", "swedish", "tagalog", "tamil", "thai",
    "turkish", "ukrainian", "urdu", "vietnamese", "welsh"
]

# Už přehrané hlášky
played_announcements = set()

def translate_safety_announcement(text, lang):
    check()
    """Přeloží bezpečnostní hlášení do zvoleného jazyka."""
    prompt = f"Přelož následující bezpečnostní hlášení do jazyka {lang}:\n\n{text}"

    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi profesionální překladatel a přeformuluješ bezpečnostní hlášení aerolinek."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


# ✈️ Hlášení pro různé fáze letu
def generate_announcement_text(phase, flight_info, flight_data):
    check()
    if phase == "Gate":
        return (f"Ladies and gentlemen, this is your captain speaking. My name is {flight_info['captain_name']} "
                f"and together with my first officer {flight_info['first_officer']}, we welcome you onboard flight "
                f"{flight_info['flight_number']} from {flight_info['origin']} to {flight_info['destination']} "
                f"aboard our {flight_info['aircraft']}. Our flight duration will be {flight_info['duration']}. "
                f"Thank you for choosing {flight_info['airline']} for your journey today.")

    elif phase == "Pushback":
        return "Cabin crew, arm doors and crosscheck"

    elif phase == "Takeoff":
        return "Cabin crew, seats for takeoff"

    elif phase == "Descent" and flight_data["altitude"] < 10000:
        return "Cabin crew, prepare cabin for landing"

    elif phase == "Final" and flight_data["altitude"] < 5000:
        return "Cabin crew, seats for landing"

    elif phase == "TaxiAfterLanding":
        return (f"Ladies and gentlemen, welcome to {flight_info['destination']}. "
                f"The local time is {time.strftime('%H:%M')} and the outside temperature is {flight_data['temperature']} °C. "
                f"Thank you for choosing {flight_info['airline']} for your flight, and we wish you a pleasant holiday, "
                f"a safe journey home, or a smooth continuation of your travels. "
                f"On behalf of {flight_info['airline']}, we wish you a wonderful day.")

    elif phase == "Deboarding":
        return "Cabin crew, disarm doors and crosscheck"

    return None


# 🎛 PA systém efekt + radio efekt
def generate_white_noise(duration_ms, volume_db=-30):
    sample_rate = 16000  
    samples = np.random.normal(0, 1, int(sample_rate * duration_ms / 1000)).astype(np.int16)
    noise = AudioSegment(samples.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1)
    return noise - abs(volume_db)

def butter_params(low_freq, high_freq, fs, order=6):
    nyq = 0.5 * fs
    low = low_freq / nyq
    high = high_freq / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, low_freq, high_freq, fs, order=6):
    b, a = butter_params(low_freq, high_freq, fs, order=order)
    return lfilter(b, a, data)

def apply_pa_system_effect(filename):
    sound = AudioSegment.from_mp3(filename)
    wav_filename = filename.replace(".mp3", ".wav")
    sound.export(wav_filename, format="wav")
    fs, audio_data = read(wav_filename)
    filtered_signal = butter_bandpass_filter(audio_data, 300, 3000, fs, order=6)
    filtered_wav_filename = filename.replace(".mp3", "_radio.wav")
    write(filtered_wav_filename, fs, np.array(filtered_signal, dtype=np.int16))
    sound = AudioSegment.from_wav(filtered_wav_filename)
    white_noise = generate_white_noise(len(sound), volume_db=-30)
    final_sound = sound.overlay(white_noise)
    filtered_filename = filename.replace(".mp3", "_pa.mp3")
    final_sound.export(filtered_filename, format="mp3", bitrate="24k")
    return filtered_filename

# 🎬 **Vyhledání bezpečnostních videí**
def find_safety_videos(icao_code):
    """Najde všechna bezpečnostní videa pro danou aerolinku podle ICAO kódu."""
    if not os.path.exists(SAFETY_VIDEO_DIR):
        print(f"❌ Folder '{SAFETY_VIDEO_DIR}' doesnt exist!")
        return []
    
    videos = [
        os.path.join(SAFETY_VIDEO_DIR, file)
        for file in os.listdir(SAFETY_VIDEO_DIR)
        if file.startswith(icao_code)
    ]

    if not videos:
        print(f"❌ No video found for {icao_code}.")
    return videos


def apply_distant_safety_effect(file_path):
    """Simuluje zvuk bezpečnostního hlášení za zavřenými dveřmi."""
    print(f"🔧 Apply sound effect (distant) {file_path}...")

    # 🛠 Načteme zvukový soubor
    try:
        sound = AudioSegment.from_file(file_path)
    except Exception as e:
        print(f"❌ Something went wrong when loading this file: {e}")
        return None

    # ✅ **Převod na mono (pokud není)**
    if sound.channels > 1:
        sound = sound.set_channels(1)

    # 🔽 **Aplikujeme low-pass filtr (měkčí zvuk, omezení vysokých frekvencí)**
    filtered_sound = sound.low_pass_filter(400).low_pass_filter(250)

    # 🔉 **Snížíme hlasitost, aby to znělo vzdáleně**
    filtered_sound = filtered_sound + 6  # 8 dB méně

    # ✅ **Vytvoříme stereo verzi**
    stereo_sound = AudioSegment.from_mono_audiosegments(filtered_sound, filtered_sound)

    # 🗂 **Uložíme dočasný soubor**
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
        temp_wav_path = temp_wav.name
        stereo_sound.export(temp_wav_path, format="wav")

    print(f"✅ Effect applied, saved to: {temp_wav_path}")
    return temp_wav_path

# 🔊 **Surround efekt pro existující videa**
def apply_surround_effect(file_path):
    sound = AudioSegment.from_wav(file_path)
    filtered_sound = sound.low_pass_filter(400).low_pass_filter(250) - 8

    surround_sound = AudioSegment.silent(duration=len(filtered_sound), frame_rate=filtered_sound.frame_rate).set_channels(8)
    front = filtered_sound - 10
    rear = filtered_sound + 5

    surround_sound = surround_sound.overlay(front.pan(-1), position=0)
    surround_sound = surround_sound.overlay(front.pan(1), position=0)
    surround_sound = surround_sound.overlay(rear.pan(-0.7), position=0)
    surround_sound = surround_sound.overlay(rear.pan(0.7), position=0)

    temp_audio_path = file_path.replace(".wav", "_surround.wav")
    surround_sound.export(temp_audio_path, format="wav")
    return temp_audio_path

# 🔊 **Přehrání bezpečnostního videa se zajištěním kompatibility**
def play_safety_video(video_path):
    """Přehrává bezpečnostní video se zvukovým efektem a opravou formátu."""
    print(f"🎬 Playing safety video: {video_path}")

    # Ujistíme se, že soubor existuje
    if not os.path.exists(video_path):
        print(f"❌ Error: File {video_path} does not exist!")
        return

    # 🛠 Aplikujeme vzdálený zvukový efekt
    processed_audio = apply_distant_safety_effect(video_path)

    # Pokud aplikace efektu selže, použijeme původní soubor
    if not processed_audio:
        print("⚠️ Warning: Unable to apply effect. Using previous file.")
        processed_audio = video_path

    # 🎵 **Oprava formátu souboru**
    try:
        sound = AudioSegment.from_file(processed_audio)

        # Konvertujeme na PCM WAV (44.1 kHz, 16-bit mono)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            temp_wav_path = temp_wav.name
            sound.set_frame_rate(44100).set_channels(1).set_sample_width(2).export(temp_wav_path, format="wav")
        
        processed_audio = temp_wav_path
        print(f"🔄 Sound converted to the right format: {processed_audio}")

    except Exception as e:
        print(f"❌ Error when converting the file: {e}")
        return

    # 🔊 **Přehrání upraveného audio souboru**
    pygame.mixer.init()
    pygame.mixer.music.load(processed_audio)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    # Po přehrání odstraníme dočasný soubor
    if os.path.exists(processed_audio):
        os.remove(processed_audio)

# 📢 **Generování bezpečnostního hlášení**
def generate_safety_announcement_text(aircraft_type):
    """Vrátí text bezpečnostního hlášení pro dané letadlo."""
    return (
        f"Ladies and gentlemen, on behalf of the crew I ask that you please direct your attention "
        f"to the monitors as we review the emergency procedures. There are emergency exits on this "
        f"aircraft type {aircraft_type}. Take a minute to locate the exit closest to you. Note that the nearest exit may be behind you. Count the number of rows to this exit. Should the cabin experience sudden pressure loss, stay calm and listen for instructions from the cabin crew. Oxygen masks will drop down from above your seat. Place the mask over your mouth and nose, like this. Pull the strap to tighten it. If you are traveling with children, make sure that your own mask is on first before helping your children. In the unlikely event of an emergency landing and evacuation, leave your carry-on items behind. Life rafts are located below your seats and emergency lighting will lead you to your closest exit and slide. We ask that you make sure that all carry-on luggage is stowed away safely during the flight. While we wait for take off, please take a moment to review the safety data card in the seat pocket in front of you."
    )

# 🔊 **Přehrání bezpečnostního hlášení nebo videa**
def play_safety_announcement(aircraft_type, selected_video=None, primary_lang="english", secondary_langs=[]):
    """Spustí bezpečnostní video nebo vygeneruje bezpečnostní hlášení ve všech vybraných jazycích."""
    
    generator = config.get("announcement_generator", "openai")  # Defaultně OpenAI

    if selected_video and os.path.exists(selected_video):
        print(f"🎬 Playing safety video: {selected_video}")
        play_safety_video(selected_video)
        return

    print(f"🎙️ Generating safety video for {aircraft_type}...")

    base_text = generate_safety_announcement_text(aircraft_type)

    if generator == "openai":
        check()
        # 🌍 Překládáme pouze pokud je zapnutý OpenAI generator
        langs_to_generate = [primary_lang] + secondary_langs
        audio_files = []

        for lang in langs_to_generate:
            translated_text = translate_and_rephrase_announcement(base_text, lang, "profesionálně")
            filename = f"safety_announcement_{lang}.mp3"
            filtered_filename = generate_announcement(lang, translated_text, voice_crew, filename)
            audio_files.append(filtered_filename)

        # 🔊 Přehrání OpenAI hlášení
        pygame.mixer.init()
        for idx, file in enumerate(audio_files):
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            if idx < len(audio_files) - 1:
                time.sleep(2)  # ⏳ Pauza mezi jazyky

    elif generator == "free":
        # ✅ Free varianta (pyttsx3) pro offline režim
        print("🎤 Initializing pyttsx3 (offline TTS for safety announcement)...")
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        # 🔄 Výběr hlasů (fallback na první hlas pokud není nalezen male/female)
        male_voice = next((voice for voice in voices if "male" in voice.name.lower()), voices[0])
        female_voice = next((voice for voice in voices if "female" in voice.name.lower()), voices[1])

        print(f"🎙️ Free offline safety announcement: {base_text}")

        engine.setProperty('rate', 125)  # Nastavení rychlosti
        engine.setProperty('volume', 1.0)  # Nastavení hlasitosti

        # 👨‍✈️ Kapitán → Mužský hlas
        engine.setProperty('voice', female_voice.id)
        engine.say(base_text)
        engine.runAndWait()

    print("✅ Safety demo done.")

def clean_text(text):
    """Odebere všechny emoji a ne-ASCII znaky z textu."""
    text = text.encode("ascii", "ignore").decode()  # Odstraní znaky mimo ASCII
    text = re.sub(r'[^\x00-\x7F]+', '', text)  # Další pojistka proti ne-ASCII znakům
    return text

def translate_and_rephrase_announcement(text, lang, style):
    """ Přeloží a přeformuluje hlášení do požadovaného jazyka a stylu. """
    text = clean_text(text)  # ✅ Odstranění emoji a ne-ASCII znaků

    prompt = f"Přelož a přeformuluj následující hlášení do jazyka {lang} ve stylu {style}:\n\n{text}"
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi letecký kapitán a přeformulováváš hlášení pro pasažéry."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# 📢 Přehrání hlášení
def play_announcement(phase, flight_info, flight_data, primary_lang, secondary_langs, style):
    """Přehrává hlášení podle vybraného generátoru (OpenAI nebo Free)."""
    if phase in played_announcements:
        return

    generator = config.get("announcement_generator", "openai")  # Defaultně OpenAI

    print(f"🛫 Announcment for phase of flight: {phase}")

    # 📝 Načtení textu hlášení
    text = ANNOUNCEMENTS.get(phase)
    if not text:
        return

    # 🔄 Doplníme proměnné do hlášení
    text = text.format(
        captain_name=flight_info["captain_name"],
        first_officer=flight_info["first_officer"],
        flight_number=flight_info["flight_number"],
        origin=flight_info.get("origin", flight_info.get("origin_iata", "N/A")),
        destination=flight_info["destination"],
        aircraft=flight_info["aircraft"],
        airline=flight_info["airline"],
        flight_duration=flight_info["duration"],
        local_time=time.strftime('%H:%M'),
        temperature=flight_data.get("temperature", "N/A")
    )

    if generator == "openai":
        check()
        # 🌍 Překládáme jen fáze, které to vyžadují
        langs_to_generate = [primary_lang] + secondary_langs if phase in MULTILINGUAL_ANNOUNCEMENTS else [primary_lang]

        # 🎙 OpenAI TTS
        audio_files = []
        for lang in langs_to_generate:
            translated_text = translate_and_rephrase_announcement(text, lang, style)
            filename = f"announcement_{phase}_{lang}.mp3"
            filtered_filename = generate_announcement(lang, translated_text, voice_captain, filename)
            audio_files.append(filtered_filename)

        # 🔊 Přehrání OpenAI hlášení
        pygame.mixer.init()
        for idx, file in enumerate(audio_files):
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            if idx < len(audio_files) - 1:
                time.sleep(2)  # ⏳ Pauza mezi jazyky

    elif generator == "free":
        # ✅ Inicializace pyttsx3 jen pokud je potřeba (OFFLINE varianta)
        print("🎤 Initializing pyttsx3 (offline TTS)...")
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')

        # 🔄 Výběr hlasů (fallback na první hlas pokud není nalezen male/female)
        male_voice = next((voice for voice in voices if "male" in voice.name.lower()), voices[0])
        female_voice = next((voice for voice in voices if "female" in voice.name.lower()), voices[1])

        print(f"🎙️ Free offline announcement: {text}")

        engine.setProperty('rate', 125)  # Nastavení rychlosti
        engine.setProperty('volume', 1.0)  # Nastavení hlasitosti

        # 👨‍✈️ Kapitán → Mužský hlas
        engine.setProperty('voice', male_voice.id)
        engine.say(text)
        engine.runAndWait()

    played_announcements.add(phase)


# 🔧 Funkce pro generování audia
def generate_announcement(lang, text, voice, filename):
    """ Vygeneruje hlášení pomocí OpenAI TTS a aplikuje PA efekt """
    print(f"🎙️ Generating announcement: ({lang.upper()} - {voice})")

    # Odeslání požadavku na OpenAI API
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )

    # Uložení MP3 souboru
    with open(filename, "wb") as f:
        f.write(response.content)

    print(f"✅ Announcement saved as: {filename}")

    return apply_pa_system_effect(filename)



