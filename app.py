from flask import Flask, request, send_file
import requests
import uuid
import os
import subprocess

app = Flask(__name__)

OUTPUT_DIR = "output"
FONT_PATH = "./Poppins-Bold.ttf"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_text(text, max_chars=30):
    return '\n'.join([text[i:i+max_chars] for i in range(0, len(text), max_chars)])

@app.route("/render", methods=["POST"])
def render():
    data = request.json
    video_url = data.get("video_url")
    raw_text = data.get("text")

    if not video_url or not raw_text:
        return {"error": "Missing video_url or text"}, 400

    try:
        video_id = str(uuid.uuid4())
        input_path = f"{OUTPUT_DIR}/{video_id}_input.mp4"
        output_path = f"{OUTPUT_DIR}/{video_id}_output.mp4"

        # Télécharger la vidéo
        r = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        # Préparer le texte
        wrapped_text = wrap_text(raw_text, max_chars=30)

        # Appliquer les filtres avec réencodage (NE PAS utiliser codec copy ici)
        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", f"drawbox=x=0:y=ih-160:w=iw:h=100:color=#C7A15C@1:t=fill,"
                   f"drawtext=fontfile={FONT_PATH}:text='{wrapped_text}':"
                   "fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-125",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",  # encoder aussi l'audio proprement
            output_path
        ]

        subprocess.run(cmd, check=True)

        return send_file(output_path, mimetype='video/mp4')

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
