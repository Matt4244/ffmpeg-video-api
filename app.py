from flask import Flask, request, send_file
import requests
import uuid
import os
import ffmpeg
import textwrap

app = Flask(__name__)

OUTPUT_DIR = "output"
FONT_PATH = "./Poppins-Bold.ttf"  # Assure-toi que ce fichier est bien présent

os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_text(text, max_width=28):
    return '\n'.join(textwrap.wrap(text, width=max_width, break_long_words=False))

@app.route("/", methods=["GET"])
def index():
    return "✅ API is running on Render!"

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

        # Formater le texte et calculer la hauteur du fond
        wrapped_text = wrap_text(raw_text)
        lines = wrapped_text.count('\n') + 1
        box_height = 40 + lines * 48

        # Traitement FFmpeg
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                vf=(
                    f"drawbox=x=0:y=ih-{box_height}:w=iw:h={box_height}:color=#C7A15C@1:t=fill,"
                    f"drawtext=fontfile={FONT_PATH}:text='{wrapped_text}':"
                    f"fontcolor=white:fontsize=36:x=(w-text_w)/2:y=h-{box_height}+((box_height-text_h)/2)"
                ),
                vcodec='libx264',
                acodec='copy',
                movflags='+faststart'
            )
            .run(overwrite_output=True)
        )

        return send_file(output_path, mimetype='video/mp4')

    except Exception as e:
        return {"error": str(e)}, 500
