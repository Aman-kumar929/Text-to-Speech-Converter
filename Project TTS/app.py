from flask import Flask, render_template, request, send_from_directory
import edge_tts
import asyncio
import os
import time
from googletrans import Translator

app = Flask(__name__)

AUDIO_FOLDER = os.path.join(app.root_path, "static", "audio")
os.makedirs(AUDIO_FOLDER, exist_ok=True)

translator = Translator()
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
        text = request.form["text"]
        language = request.form["language"]
        gender = request.form.get("gender", "female")

        rate = request.form.get("rate", "+0%") or "+0%"
        pitch = request.form.get("pitch", "+0Hz") or "+0Hz"

        clear_old_audio()

        translated_text = translator.translate(text, dest=language.split("-")[0]).text

        voice = VOICE_MAP.get(language, {}).get(gender)
        if not voice:
            voice = "en-US-AriaNeural"

        asyncio.run(generate_tts(translated_text, voice, rate, pitch))

        return render_template("index.html",audio_file=AUDIO_FILE,time=int(time.time()))

    return render_template("index.html")


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(AUDIO_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    
