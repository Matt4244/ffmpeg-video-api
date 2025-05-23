from flask import Flask, request, send_file
import requests
import uuid
import os
import ffmpeg
import textwrap

app = Flask(__name__)

OUTPUT_DIR = "output"
FONT_PATH = "./Poppins-Bold.ttf"  # Assure-toi que ce fichier existe ici

os.makedirs(OUTPUT_DIR, exist_ok=True)

def wrap_text(text, max_width=28):
    # Ne coupe pas les mots
    return '\n'.join(textwrap.wrap(text, width=max_width, break_long_words=False))

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

        print(f"Downloading video from: {video_url}")
        r = requests.get(video_url, stream=True)
        with open(input_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

        wrapped_text = wrap_text(raw_text)
        lines = wrapped_text.count('\n') + 1
        box_height = 40 + lines * 48  # Hauteur dynamique
        safe_text = wrapped_text.replace(":", '\\:').replace("'", "\\'")

        drawbox_y = f"ih-{box_height}"
        drawtext_y = f"h-{box_height}+((box_height-text_h)/2)"

        filter_str = (
            f"drawbox=x=0:y={drawbox_y}:w=iw:h={box_height}:color=#C7A15C@1:t=fill,"
            f"drawtext=fontfile={FONT_PATH}:text='{safe_text}':"
            f"fontcolor=white:fontsize=36:x=(w-text_w)/2:y={drawtext_y}"
        )

        print("FFmpeg filter string:")
        print(filter_str)

        stream = ffmpeg.input(input_path).output(
            output_path,
            vf=filter_str,
            vcodec='libx264',
            acodec='copy',
            movflags='+faststart'
        )

        print("FFmpeg command:")
        print(" ".join(stream.compile()))

        stream.run(overwrite_output=True)

        print(f"Rendered video at: {output_path}")
        return send_file(output_path, mimetype='video/mp4')

    except Exception as e:
        print("Error occurred:", str(e))
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
