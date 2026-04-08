from flask import Flask, render_template, request, send_from_directory
import edge_tts
import asyncio
import os
import time
from deep_translator import GoogleTranslator


app = Flask(__name__)

AUDIO_FOLDER = os.path.join(app.root_path, "static", "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)

AUDIO_FILE = "audio.mp3"


VOICE_MAP = {
    "en-US": {
        "female": "en-US-AriaNeural",
        "male": "en-US-GuyNeural"
    },
    "hi-IN": {
        "female": "hi-IN-SwaraNeural",
        "male": "hi-IN-MadhurNeural"
    },
    "fr-FR": {
        "female": "fr-FR-DeniseNeural",
        "male": "fr-FR-HenriNeural"
    },
    "de-DE": {
        "female": "de-DE-KatjaNeural",
        "male": "de-DE-ConradNeural"
    }
}


def clear_old_audio():
    for f in os.listdir(AUDIO_FOLDER):
        if f.endswith(".mp3"):
            os.remove(os.path.join(AUDIO_FOLDER, f))


async def generate_tts(text, voice, rate, pitch):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )
    await communicate.save(os.path.join(AUDIO_FOLDER, AUDIO_FILE))


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        try:
            text = request.form.get("text", "").strip()
            language = request.form.get("language", "en-US")
            gender = request.form.get("gender", "female")

            # ---------- SAFE INPUT HANDLING ----------
            rate_input = request.form.get("rate", "").strip()
            pitch_input = request.form.get("pitch", "").strip()

            # Default values if empty
            if rate_input == "":
                rate_input = "0"
            if pitch_input == "":
                pitch_input = "0"

            # Convert safely (NO + sign because some TTS reject it)
            # Convert safely with + or -
            try:
                rate = f"{int(rate_input):+d}%"
            except:
                rate = "+0%"

            try:
                pitch = f"{int(pitch_input):+d}Hz"
            except:
                pitch = "+0Hz"

            print("Rate:", rate)
            print("Pitch:", pitch)

            # ---------- MAIN LOGIC ----------
            clear_old_audio()

            translated_text = GoogleTranslator(
                source="auto",
                target=language.split("-")[0]
            ).translate(text)

            voice = VOICE_MAP.get(language, {}).get(gender, "en-US-AriaNeural")

            # ---------- SAFE ASYNC FIX ----------
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(
                generate_tts(translated_text, voice, rate, pitch)
            )
            loop.close()

            return render_template(
                "index.html",
                audio_file=AUDIO_FILE,
                time=int(time.time())
            )

        except Exception as e:
            print("FULL ERROR:", e)
            return render_template(
                "index.html",
                error=str(e)
            )

    return render_template("index.html")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(AUDIO_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    
