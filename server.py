
from flask import Flask, request, render_template
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
from emotion_detection import emotion_detector

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    emotion = None
    if request.method == "POST":
        user_text = request.form.get("user_text")
        if user_text:
            emotion = emotion_detector(user_text)
    return render_template("index.html", result=emotion)

if __name__ == "__main__":
    app.run(debug=True)
