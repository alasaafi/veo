from flask import Flask, render_template, request, jsonify
import os, subprocess, tempfile
from openai import OpenAI
import yt_dlp
import assemblyai as aai

app = Flask(__name__)

# --- API Key Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
aai.settings.api_key = os.environ.get("ASSEMBLYAI_API_KEY")

MODEL = "openai/gpt-4o-mini"

def process_video_and_generate_prompt(video_url):
    """
    Downloads, trims, and uses AssemblyAI to transcribe a video, 
    then generates a prompt.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path_template = os.path.join(tmpdir, "video.%(ext)s")
        short_path = os.path.join(tmpdir, "video_short.mp4")

        # --- Download and Trim (Same as before) ---
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': video_path_template,
            'cookiefile': 'cookies.txt',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_video_path = ydl.prepare_filename(info)

        trim_cmd = ["ffmpeg", "-y", "-i", downloaded_video_path, "-t", "30", short_path]
        subprocess.run(trim_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # --- Transcription with AssemblyAI (New) ---
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(short_path)

        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"AssemblyAI Error: {transcript.error}")
        
        transcript_text = transcript.text

        # --- Keyword Extraction and Prompt Generation (Same as before) ---
        words = transcript_text.split()
        freq = {}
        for w in words: freq[w] = freq.get(w, 0) + 1
        keywords = sorted(freq, key=freq.get, reverse=True)[:15]

        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        keywords_str = ", ".join(keywords)
        instruction = f"Create a single, detailed Veo 3 cinematic prompt based ONLY on these keywords: {keywords_str}."
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an AI that generates high-quality Veo 3 prompts."},
                {"role": "user", "content": instruction},
            ],
        )
        return response.choices[0].message.content.strip()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    video_url = request.form.get("url")
    if not video_url:
        return jsonify({"error": "Please provide a URL"}), 400
    
    try:
        prompt = process_video_and_generate_prompt(video_url)
        return jsonify({"prompt": prompt})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to process video. Please check the URL or try another."}), 500