import openai
import pygame
import random
import time
import os
import numpy as np
from pydub import AudioSegment
from scipy.signal import lfilter, butter
from scipy.io.wavfile import read, write
import json
import pyttsx3
import re
import sys
import tempfile
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Define paths and constants
SCRIPT_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
SAFETY_VIDEO_DIR = os.path.join(SCRIPT_DIR, "safety_videos")
CONFIG_FILE = "config.json"
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp")  # Nová složka pro dočasné soubory

# Ensure safety video directory exists
if not os.path.exists(SAFETY_VIDEO_DIR):
    logger.warning(f"Folder '{SAFETY_VIDEO_DIR}' doesn't exist! Creating one...")
    os.makedirs(SAFETY_VIDEO_DIR)

# Ensure temp directory exists
if not os.path.exists(TEMP_DIR):
    logger.info(f"Creating temporary directory: {TEMP_DIR}")
    os.makedirs(TEMP_DIR)

logger.info(f"Looking for directory: {SAFETY_VIDEO_DIR}")
logger.info(f"Found directory with files: {os.listdir(SAFETY_VIDEO_DIR) if os.path.exists(SAFETY_VIDEO_DIR) else 'Folder is empty or doesnt exist'}")

# Define announcement types that require multilingual support
MULTILINGUAL_ANNOUNCEMENTS = {"Gate", "TaxiAfterLanding", "Safety", "Descent", "InflightService"}

# Define all possible announcement phases
ANNOUNCEMENTS = ["Gate", "Pushback", "Takeoff", "Descent", "Final", "TaxiAfterLanding", "Deboarding", "AirportBoarding", "LastCall", "InflightService"]

# Load announcements from announcements.txt
def load_announcements():
    """Load announcements from announcements.txt file."""
    announcements = {}
    announcements_file = os.path.join(SCRIPT_DIR, "announcements.txt")
    
    if not os.path.exists(announcements_file):
        logger.error(f"Announcements file '{announcements_file}' not found! Using default announcements.")
        return {
            "Gate": "Ladies and gentlemen, this is your captain speaking. My name is {captain_name} and together with my first officer {first_officer}, we welcome you onboard flight {flight_number} from {origin} to {destination} aboard our {aircraft}. Our flight duration will be approximately {flight_duration}. We will be departing from gate {gate}. {food_and_beverage_info} Thank you for choosing {airline} for your journey today.",
            "Pushback": "Cabin crew, arm doors and crosscheck.",
            "Takeoff": "Cabin crew, seats for takeoff.",
            "Descent": "Ladies and gentlemen, we have started our descent to our destination. Please ensure your seatbelt is fastened, window blinds are open, seat is fully upright, and tray table is stowed. In preparation for landing, the toilets will be locked in about 5 minutes. Cabin crew, prepare the cabin for landing.",
            "Final": "Cabin crew, seats for landing.",
            "TaxiAfterLanding": "Ladies and gentlemen, welcome to {destination}. The local time is {local_time} and the outside temperature is {temperature} °C. Thank you for choosing {airline} for your flight, and we wish you a pleasant holiday, a safe journey home, or a smooth continuation of your travels. On behalf of {airline}, we wish you a wonderful day.",
            "Deboarding": "Cabin crew, disarm doors and crosscheck.",
            "AirportBoarding": "Ladies and gentlemen, your flight {flight_number} to {destination} is now ready for boarding at gate {gate}. Please have your boarding card ready for scanning and your travel document open on the picture page. {food_and_beverage_info} On behalf of {airline}, we wish you a pleasant flight.",
            "LastCall": "Ladies and gentlemen, this is the last call for boarding flight {flight_number} to {destination} at gate {gate}. All remaining passengers are requested to proceed immediately to the gate. Thank you.",
            "InflightService": "Ladies and gentlemen, we are now starting our inflight service. Today, we are offering the following food options: {food_options}. {beverage_service_info} Please have your payment ready if applicable, and thank you for your attention."
        }

    try:
        with open(announcements_file, "r", encoding="utf-8") as f:
            lines = f.read().strip().split("\n\n")  # Oddělíme jednotlivá hlášení podle prázdných řádků
            for announcement_block in lines:
                if not announcement_block.strip():
                    continue
                block_lines = announcement_block.strip().split("\n")
                if not block_lines:
                    continue
                # První řádek je klíč v hranatých závorkách, např. [Gate]
                key_line = block_lines[0].strip()
                if not (key_line.startswith("[") and key_line.endswith("]")):
                    logger.warning(f"Invalid announcement key format: {key_line}. Skipping.")
                    continue
                key = key_line[1:-1]  # Odstraníme závorky, např. [Gate] -> Gate
                # Zbytek je text hlášení
                text = " ".join(line.strip() for line in block_lines[1:])  # Spojíme řádky do jednoho textu
                announcements[key] = text
        logger.info(f"Successfully loaded announcements from {announcements_file}")
        return announcements
    except Exception as e:
        logger.error(f"Failed to load announcements from {announcements_file}: {e}. Using default announcements.")
        return {
            "Gate": "Ladies and gentlemen, this is your captain speaking. My name is {captain_name} and together with my first officer {first_officer}, we welcome you onboard flight {flight_number} from {origin} to {destination} aboard our {aircraft}. Our flight duration will be approximately {flight_duration}. We will be departing from gate {gate}. {food_and_beverage_info} Thank you for choosing {airline} for your journey today.",
            "Pushback": "Cabin crew, arm doors and crosscheck.",
            "Takeoff": "Cabin crew, seats for takeoff.",
            "Descent": "Ladies and gentlemen, we have started our descent to our destination. Please ensure your seatbelt is fastened, window blinds are open, seat is fully upright, and tray table is stowed. In preparation for landing, the toilets will be locked in about 5 minutes. Cabin crew, prepare the cabin for landing.",
            "Final": "Cabin crew, seats for landing.",
            "TaxiAfterLanding": "Ladies and gentlemen, welcome to {destination}. The local time is {local_time} and the outside temperature is {temperature} °C. Thank you for choosing {airline} for your flight, and we wish you a pleasant holiday, a safe journey home, or a smooth continuation of your travels. On behalf of {airline}, we wish you a wonderful day.",
            "Deboarding": "Cabin crew, disarm doors and crosscheck.",
            "AirportBoarding": "Ladies and gentlemen, your flight {flight_number} to {destination} is now ready for boarding at gate {gate}. Please have your boarding card ready for scanning and your travel document open on the picture page. {food_and_beverage_info} On behalf of {airline}, we wish you a pleasant flight.",
            "LastCall": "Ladies and gentlemen, this is the last call for boarding flight {flight_number} to {destination} at gate {gate}. All remaining passengers are requested to proceed immediately to the gate. Thank you.",
            "InflightService": "Ladies and gentlemen, we are now starting our inflight service. Today, we are offering the following food options: {food_options}. {beverage_service_info} Please have your payment ready if applicable, and thank you for your attention."
        }

# Načtení hlášení z announcements.txt
announcements = load_announcements()

# Set up ffmpeg for pydub
FFMPEG_DIR = os.path.join(SCRIPT_DIR, "ffmpeg", "bin")
ffmpeg_path = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
ffprobe_path = os.path.join(FFMPEG_DIR, "ffprobe.exe")
AudioSegment.converter = ffmpeg_path
AudioSegment.ffprobe = ffprobe_path
os.environ["PATH"] += os.pathsep + FFMPEG_DIR

# Voice settings
captain_voices = ["onyx", "ash"]
voice_captain = random.choice(captain_voices)
crew_voices = ["coral", "nova", "sage", "shimmer"]
voice_crew = random.choice(crew_voices)

# Captain styles
captain_styles = ["professional", "austere", "friendly", "experienced"]

# List of valid languages
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

# Track played announcements
played_announcements = set()

# Load configuration
def load_config():
    if not os.path.exists(CONFIG_FILE):
        logger.warning(f"Config file '{CONFIG_FILE}' not found. Using default configuration.")
        return {
            "captain_name": "",
            "first_officer": "",
            "openai_api_key": "",
            "announcement_generator": "free",
            "primary_language": "english",
            "secondary_languages": [],
            "airport_announcement_languages": [],
            "captain_style": "professional",
            "flight_data_file": "",
            "chime_start": "none",
            "chime_end": "none",
            "enable_airport_announcement": True
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Initialize OpenAI API key
config = load_config()
openai.api_key = config.get("openai_api_key", "")

def check():
    """Check OpenAI API key only if using OpenAI generator."""
    config = load_config()  # Reload config to ensure it's up-to-date
    if config.get("announcement_generator", "free") == "openai" and not openai.api_key:
        logger.warning("OpenAI API key is not set! Switching to offline generator.")
        config["announcement_generator"] = "free"
    return config

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
    try:
        sound = AudioSegment.from_mp3(filename)
        # Upravíme cesty k dočasným souborům
        wav_filename = os.path.join(TEMP_DIR, os.path.basename(filename).replace(".mp3", ".wav"))
        sound.export(wav_filename, format="wav")
        fs, audio_data = read(wav_filename)
        filtered_signal = butter_bandpass_filter(audio_data, 300, 3000, fs, order=6)
        filtered_wav_filename = os.path.join(TEMP_DIR, os.path.basename(filename).replace(".mp3", "_radio.wav"))
        write(filtered_wav_filename, fs, np.array(filtered_signal, dtype=np.int16))
        sound = AudioSegment.from_wav(filtered_wav_filename)
        white_noise = generate_white_noise(len(sound), volume_db=-30)
        final_sound = sound.overlay(white_noise)
        filtered_filename = os.path.join(TEMP_DIR, os.path.basename(filename).replace(".mp3", "_pa.mp3"))
        final_sound.export(filtered_filename, format="mp3", bitrate="24k")
        # Clean up temporary files
        for temp_file in [wav_filename, filtered_wav_filename]:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        return filtered_filename
    except Exception as e:
        logger.error(f"Failed to apply PA system effect to {filename}: {e}")
        return filename

def apply_airport_pa_effect(filename):
    """Apply airport PA effect to the audio file with a cathedral-like resonance."""
    try:
        logger.info(f"Applying airport PA effect to {filename}...")
        # Načtení zvuku
        sound = AudioSegment.from_mp3(filename)
        wav_filename = os.path.join(TEMP_DIR, os.path.basename(filename).replace(".mp3", ".wav"))
        sound.export(wav_filename, format="wav")
        
        # Aplikace frekvenčního filtru (rozšíříme pásmo pro jasnější zvuk)
        fs, audio_data = read(wav_filename)
        filtered_signal = butter_bandpass_filter(audio_data, 150, 4000, fs, order=6)  # Rozšířené pásmo 150-4000 Hz
        write(wav_filename, fs, np.array(filtered_signal, dtype=np.int16))
        filtered_sound = AudioSegment.from_wav(wav_filename)

        # Přidání dvou ozvěn pro "katedrální" efekt
        delay_1_ms = 100  # První ozvěna po 100 ms
        delay_2_ms = 250  # Druhá ozvěna po 250 ms

        # Vytvoření ozvěn s různými útlumy
        silence_1 = AudioSegment.silent(duration=delay_1_ms)
        silence_2 = AudioSegment.silent(duration=delay_2_ms)

        echo_1 = filtered_sound - 10  # První ozvěna o 10 dB tišší
        echo_2 = filtered_sound - 15  # Druhá ozvěna o 15 dB tišší

        delayed_echo_1 = silence_1 + echo_1
        delayed_echo_2 = silence_2 + echo_2

        # Kombinace původního zvuku s ozvěnami
        sound_with_echo = filtered_sound.overlay(delayed_echo_1)
        sound_with_echo = sound_with_echo.overlay(delayed_echo_2)

        # Přidání jemného šumu simulujícího ruch na letišti
        white_noise = generate_white_noise(len(sound_with_echo), volume_db=-35)  # Tišší šum (-35 dB)
        final_sound = sound_with_echo.overlay(white_noise)

        # Export výsledného zvuku
        filtered_filename = os.path.join(TEMP_DIR, os.path.basename(filename).replace(".mp3", "_airport_pa.mp3"))
        final_sound.export(filtered_filename, format="mp3", bitrate="32k")

        # Vyčištění dočasných souborů
        if os.path.exists(wav_filename):
            os.remove(wav_filename)
        logger.info(f"Airport PA effect applied, saved as: {filtered_filename}")
        return filtered_filename
    except Exception as e:
        logger.error(f"Failed to apply airport PA effect to {filename}: {e}")
        return filename

def find_safety_videos(icao_code):
    if not os.path.exists(SAFETY_VIDEO_DIR):
        logger.error(f"Folder '{SAFETY_VIDEO_DIR}' doesn't exist!")
        return []
    videos = [os.path.join(SAFETY_VIDEO_DIR, file) for file in os.listdir(SAFETY_VIDEO_DIR) if file.startswith(icao_code)]
    if not videos:
        logger.warning(f"No video found for {icao_code}.")
    return videos

def apply_distant_safety_effect(file_path):
    try:
        logger.info(f"Applying sound effect (distant) to {file_path}...")
        sound = AudioSegment.from_file(file_path)
        if sound.channels > 1:
            sound = sound.set_channels(1)
        filtered_sound = sound.low_pass_filter(400).low_pass_filter(250)
        filtered_sound = filtered_sound + 6
        stereo_sound = AudioSegment.from_mono_audiosegments(filtered_sound, filtered_sound)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=TEMP_DIR) as temp_wav:
            temp_wav_path = temp_wav.name
            stereo_sound.export(temp_wav_path, format="wav")
        logger.info(f"Effect applied, saved to: {temp_wav_path}")
        return temp_wav_path
    except Exception as e:
        logger.error(f"Failed to apply distant safety effect to {file_path}: {e}")
        return None

def play_safety_video(video_path):
    if not os.path.exists(video_path):
        logger.error(f"File {video_path} does not exist!")
        return
    processed_audio = apply_distant_safety_effect(video_path)
    if not processed_audio:
        logger.warning("Unable to apply effect. Using original file.")
        processed_audio = video_path
    try:
        sound = AudioSegment.from_file(processed_audio)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav", dir=TEMP_DIR) as temp_wav:
            temp_wav_path = temp_wav.name
            sound.set_frame_rate(44100).set_channels(1).set_sample_width(2).export(temp_wav_path, format="wav")
        processed_audio = temp_wav_path
        logger.info(f"Sound converted to the right format: {processed_audio}")
        pygame.mixer.init()
        pygame.mixer.music.load(processed_audio)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        logger.error(f"Error when playing safety video {processed_audio}: {e}")
    finally:
        pygame.mixer.quit()
        # Clean up temporary files
        if os.path.exists(processed_audio):
            os.remove(processed_audio)
        logger.info(f"Audio playback finished. Temporary files cleaned up.")

def generate_safety_announcement_text(aircraft_type):
    return (
        f"Ladies and gentlemen, on behalf of the crew, I ask that you please direct your attention "
        f"to the monitors as we review the emergency procedures. This aircraft type {aircraft_type} has emergency exits. "
        f"Take a moment to locate the exit closest to you. Note that the nearest exit may be behind you. "
        f"Count the number of rows to this exit. Should the cabin experience sudden pressure loss, stay calm and listen for instructions from the cabin crew. "
        f"Oxygen masks will drop down from above your seat. Place the mask over your mouth and nose, like this. "
        f"Pull the strap to tighten it. If you are traveling with children, make sure that your own mask is on first before helping your children. "
        f"In the unlikely event of an emergency landing and evacuation, leave your carry-on items behind. "
        f"Life rafts are located below your seats, and emergency lighting will lead you to your closest exit and slide. "
        f"We ask that you ensure all carry-on luggage is stowed away safely during the flight. "
        f"While we wait for takeoff, please take a moment to review the safety data card in the seat pocket in front of you."
    )

def play_safety_announcement(aircraft_type, selected_video=None, primary_lang="english", secondary_langs=None):
    if secondary_langs is None:
        secondary_langs = []
    config = load_config()
    generator = config.get("announcement_generator", "openai")
    if selected_video and os.path.exists(selected_video):
        logger.info(f"Playing safety video: {selected_video}")
        play_safety_video(selected_video)
        return
    logger.info(f"Generating safety announcement for {aircraft_type}...")
    base_text = generate_safety_announcement_text(aircraft_type)
    if generator == "openai":
        config = check()
        langs_to_generate = [primary_lang] + secondary_langs
        audio_files = []
        for lang in langs_to_generate:
            try:
                translated_text = translate_and_rephrase_announcement(base_text, lang, "professional")
                filename = f"safety_announcement_{lang}.mp3"
                # Upravíme cestu k souboru
                temp_filename = os.path.join(TEMP_DIR, filename)
                filtered_filename = generate_announcement(config, translated_text, voice_crew, filename)
                audio_files.append(filtered_filename)
            except Exception as e:
                logger.error(f"Failed to generate safety announcement for {lang}: {e}")
                continue
        try:
            pygame.mixer.init()
            for idx, file in enumerate(audio_files):
                pygame.mixer.music.load(file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                if idx < len(audio_files) - 1:
                    time.sleep(2)
        except Exception as e:
            logger.error(f"Error playing safety announcements: {e}")
        finally:
            pygame.mixer.quit()
            # Clean up audio files
            for file in audio_files:
                if os.path.exists(file):
                    os.remove(file)
    elif generator == "free":
        logger.info("Initializing pyttsx3 (offline TTS for safety announcement)...")
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            female_voice = next((voice for voice in voices if "female" in voice.name.lower()), voices[1])
            logger.info(f"Free offline safety announcement: {base_text}")
            engine.setProperty('rate', 125)
            engine.setProperty('volume', 1.0)
            engine.setProperty('voice', female_voice.id)
            engine.say(base_text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"Failed to play safety announcement with pyttsx3: {e}")
    logger.info("Safety demo done.")

def clean_text(text):
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def translate_and_rephrase_announcement(text, lang, style):
    text = clean_text(text)
    prompt = f"Translate and rephrase the following announcement into {lang} in a {style} style:\n\n{text}"
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an airline captain rephrasing announcements for passengers."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Failed to translate announcement to {lang}: {e}")
        return text  # Fallback to original text

def generate_announcement(config, text, voice, filename, speed=1.0):
    logger.info(f"Generating announcement: ({voice}, speed: {speed}x)")
    # Upravíme cestu k souboru, aby vedla do složky temp
    temp_filename = os.path.join(TEMP_DIR, filename)
    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            speed=speed
        )
        with open(temp_filename, "wb") as f:
            f.write(response.content)
        logger.info(f"Announcement saved as: {temp_filename}")
        return apply_pa_system_effect(temp_filename)
    except Exception as e:
        logger.error(f"Failed to generate announcement for {temp_filename}: {e}")
        return None

def generate_beverage_service_info(beverage_service):
    if beverage_service == "dry":
        return "Non-alcoholic beverages will be available during the flight."
    elif beverage_service == "complimentary":
        return "Complimentary beverages, including alcohol, will be available."
    elif beverage_service == "paid":
        return "Beverages are available for purchase, including alcoholic options."
    return ""

def generate_food_and_beverage_info(food_options, beverage_service):
    food_info = f"We will be offering {food_options}." if food_options else ""
    beverage_info = generate_beverage_service_info(beverage_service) if beverage_service else ""
    if food_info and beverage_info:
        return f"{food_info} {beverage_info}"
    return food_info or beverage_info or "No food or beverage service information available."

def play_announcement(phase, flight_info, flight_data, all_langs_sorted, airport_langs, airport_order, style):
    # Ladící výpis pro kontrolu vstupních parametrů
    logger.info(f"Starting play_announcement for phase: {phase}")
    logger.debug(f"flight_info: {flight_info}")
    logger.debug(f"flight_data: {flight_data}")
    logger.debug(f"all_langs_sorted: {all_langs_sorted}")
    logger.debug(f"airport_langs: {airport_langs}")
    logger.debug(f"airport_order: {airport_order}")
    logger.debug(f"style: {style}")

    # Kontrola, zda už hlášení nebylo přehráno
    if phase in played_announcements:
        logger.info(f"Announcement for phase {phase} already played. Skipping.")
        return

    config = load_config()
    generator = config.get("announcement_generator", "openai")
    logger.info(f"Announcement for phase of flight: {phase}, using generator: {generator}")

    # Načtení textu hlášení
    text = announcements.get(phase)
    if not text:
        logger.warning(f"No announcement text found for phase {phase}.")
        return

    # Přidání food_and_beverage_info a beverage_service_info do flight_info
    food_options = flight_info.get("food_options", "")
    beverage_service = flight_info.get("beverage_service", "")
    flight_info["food_and_beverage_info"] = generate_food_and_beverage_info(food_options, beverage_service)
    flight_info["beverage_service_info"] = generate_beverage_service_info(beverage_service)
    logger.debug(f"Updated flight_info with food_and_beverage_info: {flight_info['food_and_beverage_info']}")
    logger.debug(f"Updated flight_info with beverage_service_info: {flight_info['beverage_service_info']}")

    # Formátování local_time na HH:MM
    local_time = flight_data.get("local_time", time.strftime('%H:%M'))
    if local_time and ":" in local_time:
        # Pokud je formát HH:MM:SS, ořízneme sekundy
        local_time = local_time[:5]  # Vezmeme pouze první 5 znaků (HH:MM)
    flight_data["local_time"] = local_time
    logger.debug(f"Formatted local_time: {local_time}")

    # Nahrazení placeholderů v textu
    try:
        formatted_text = text
        for key, value in flight_info.items():
            placeholder = "{" + key + "}"
            formatted_text = formatted_text.replace(placeholder, str(value))
            logger.debug(f"Replacing placeholder {placeholder} with {value}")

        for key, value in flight_data.items():
            placeholder = "{" + key + "}"
            formatted_text = formatted_text.replace(placeholder, str(value))
            logger.debug(f"Replacing placeholder {placeholder} with {value}")

        text = formatted_text
        logger.info(f"Formatted announcement text: {text}")
    except KeyError as e:
        logger.error(f"Missing key in flight_info or flight_data: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error during placeholder replacement: {e}")
        return

    # Generování hlášení
    if generator == "openai":
        config = check()
        chime_start = config.get("chime_start", "none")
        chime_end = config.get("chime_end", "none")
        chime_dir = os.path.join(SCRIPT_DIR, "airport_chimes")
        logger.debug(f"Chime settings: start={chime_start}, end={chime_end}, dir={chime_dir}")

        # Určení jazyků pro generování hlášení
        if phase == "AirportBoarding" or phase == "LastCall":  # LastCall je letištní hlášení
            langs_to_generate = airport_langs
        elif phase in MULTILINGUAL_ANNOUNCEMENTS:  # InflightService je multijazyčné
            langs_to_generate = all_langs_sorted
        else:
            langs_to_generate = [flight_info.get("primary_lang", "english")]
        logger.info(f"Languages to generate for phase {phase}: {langs_to_generate}")

        # Seznam audio souborů (včetně chime, pokud jsou nastaveny)
        audio_files = []

        # Přidání chime na začátek (pokud je nastaveno)
        if (phase == "AirportBoarding" or phase == "LastCall") and chime_start != "none":
            chime_start_path = os.path.join(chime_dir, chime_start)
            if os.path.exists(chime_start_path):
                if not chime_start_path.endswith(".mp3"):
                    chime_start_mp3 = os.path.join(TEMP_DIR, os.path.basename(chime_start_path).replace(os.path.splitext(chime_start_path)[1], ".mp3"))
                    AudioSegment.from_file(chime_start_path).export(chime_start_mp3, format="mp3")
                else:
                    chime_start_mp3 = chime_start_path
                # Ztlumíme chime o 5 dB
                chime_audio = AudioSegment.from_mp3(chime_start_mp3) - 5
                chime_start_filtered = os.path.join(TEMP_DIR, os.path.basename(chime_start_mp3).replace(".mp3", "_attenuated.mp3"))
                chime_audio.export(chime_start_filtered, format="mp3")
                chime_start_filtered = apply_airport_pa_effect(chime_start_filtered)
                audio_files.append(chime_start_filtered)
                logger.info(f"Adding chime at start with PA effect: {chime_start_filtered}")
            else:
                logger.warning(f"Chime {chime_start_path} does not exist!")

        # Generování hlášení pro každý jazyk
        for lang in langs_to_generate:
            logger.info(f"Generating announcement for language: {lang}")
            translated_text = translate_and_rephrase_announcement(text, lang, style)
            filename = f"announcement_{phase}_{lang}.mp3"
            selected_voice = random.choice(crew_voices) if phase in ["AirportBoarding", "LastCall"] else \
                            (voice_crew if phase in ["TaxiAfterLanding", "InflightService"] else voice_captain)
            speed = 1.2 if phase in ["AirportBoarding", "LastCall"] else 1.0
            logger.debug(f"Using voice: {selected_voice}, speed: {speed}")
            filtered_filename = generate_announcement(config, translated_text, selected_voice, filename, speed)
            if filtered_filename:
                audio_files.append(filtered_filename)
                logger.info(f"Generated audio file: {filtered_filename}")
            else:
                logger.warning(f"Failed to generate audio for language {lang}")

        # Přidání chime na konec (pokud je nastaveno)
        if (phase == "AirportBoarding" or phase == "LastCall") and chime_end != "none":
            chime_end_path = os.path.join(chime_dir, chime_end)
            if os.path.exists(chime_end_path):
                if not chime_end_path.endswith(".mp3"):
                    chime_end_mp3 = os.path.join(TEMP_DIR, os.path.basename(chime_end_path).replace(os.path.splitext(chime_end_path)[1], ".mp3"))
                    AudioSegment.from_file(chime_end_path).export(chime_end_mp3, format="mp3")
                else:
                    chime_end_mp3 = chime_end_path
                # Ztlumíme chime o 5 dB
                chime_audio = AudioSegment.from_mp3(chime_end_mp3) - 5
                chime_end_filtered = os.path.join(TEMP_DIR, os.path.basename(chime_end_mp3).replace(".mp3", "_attenuated.mp3"))
                chime_audio.export(chime_end_filtered, format="mp3")
                chime_end_filtered = apply_airport_pa_effect(chime_end_filtered)
                audio_files.append(chime_end_filtered)
                logger.info(f"Adding chime at end with PA effect: {chime_end_filtered}")
            else:
                logger.warning(f"Chime {chime_end_path} does not exist!")

        # Kombinace audio souborů pro AirportBoarding a LastCall (včetně chime)
        if (phase == "AirportBoarding" or phase == "LastCall") and audio_files:
            combined_filename = os.path.join(TEMP_DIR, f"announcement_{phase}_combined.mp3")
            combined_audio = None
            for audio_file in audio_files:
                audio_segment = AudioSegment.from_file(audio_file)
                if combined_audio is None:
                    combined_audio = audio_segment
                else:
                    combined_audio += audio_segment
            combined_audio.export(combined_filename, format="mp3")
            final_filename = apply_airport_pa_effect(combined_filename)
            audio_files = [final_filename]
            logger.info(f"Combined audio files into: {final_filename}")

        # Přehrání audio souborů
        if audio_files:
            try:
                pygame.mixer.init()
                for idx, file in enumerate(audio_files):
                    logger.info(f"Playing audio file: {file}")
                    pygame.mixer.music.load(file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    if idx < len(audio_files) - 1 and phase not in ["AirportBoarding", "LastCall"]:
                        time.sleep(2)
            except Exception as e:
                logger.error(f"Error playing announcements: {e}")
            finally:
                pygame.mixer.quit()
                # Clean up audio files
                for file in audio_files:
                    if os.path.exists(file):
                        os.remove(file)
                        logger.debug(f"Cleaned up audio file: {file}")
        else:
            logger.warning(f"No audio files generated for phase {phase}")

    # Offline generátor (pyttsx3)
    elif generator == "free":
        logger.info("Initializing pyttsx3 (offline TTS)...")
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            male_voice = next((voice for voice in voices if "male" in voice.name.lower()), voices[0])
            female_voice = next((voice for voice in voices if "female" in voice.name.lower()), voices[1])
            logger.info(f"Free offline announcement: {text}")
            engine.setProperty('rate', 150 if phase in ["AirportBoarding", "LastCall"] else 125)
            engine.setProperty('volume', 1.0)
            engine.setProperty('voice', female_voice.id if phase in ["AirportBoarding", "LastCall"] else male_voice.id)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"Failed to play announcement with pyttsx3: {e}")

    # Označení hlášení jako přehráno
    played_announcements.add(phase)
    logger.info(f"Announcement for phase {phase} completed and marked as played.")