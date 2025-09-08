from flask import Flask, render_template, request, jsonify
import os
import subprocess
import tempfile
import base64
import glob
from openai import OpenAI
import yt_dlp

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "openai/gpt-4o-mini"

def analyze_video_frames(video_url):
    """
    Downloads a video, extracts frames, and uses a vision model to generate a prompt.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # --- 1. Download Video ---
        video_path = os.path.join(tmpdir, "video.mp4")
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': video_path,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # --- 2. Extract Frames ---
        frames_dir = os.path.join(tmpdir, "frames")
        os.makedirs(frames_dir)
        # Extracts 1 frame every 5 seconds for a total of 6 frames from a 30s clip
        ffmpeg_cmd = [
            "ffmpeg", "-i", video_path, "-vf", "fps=1/5", 
            "-t", "30", f"{frames_dir}/frame-%03d.png"
        ]
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # --- 3. Encode Frames and Prepare for AI ---
        base64_images = []
        # Sort frames to maintain chronological order
        frame_files = sorted(glob.glob(os.path.join(frames_dir, "*.png")))
        
        for frame_path in frame_files:
            with open(frame_path, "rb") as image_file:
                base64_images.append(base64.b64encode(image_file.read()).decode("utf-8"))

        if not base64_images:
            raise ValueError("No frames were extracted from the video.")

        # --- 4. Analyze with Vision Model ---
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        
        # Construct the message payload for the multimodal model
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "These are frames from a video. Describe the scene, action, and style. Based on this visual information, create a single, detailed Veo 3 cinematic prompt.",
                    }
                ]
                + [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img}"},
                    }
                    for img in base64_images
                ],
            }
        ]
        
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=300,
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
        prompt = analyze_video_frames(video_url)
        return jsonify({"prompt": prompt})
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Failed to process video. It might be private, invalid, or too short."}), 500