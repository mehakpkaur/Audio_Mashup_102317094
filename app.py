import os
import zipfile
import smtplib
import re
from email.message import EmailMessage
from flask import Flask, request, render_template_string
from yt_dlp import YoutubeDL
from pydub import AudioSegment

app = Flask(__name__)

# ---------------- HTML FORM ---------------- #
HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>Mashup Web Service</title></head>
<body>
    <h2>🎵 Mashup Generator Service</h2>
    <form method="POST">
        Singer Name: <input type="text" name="singer" required><br><br>
        Number of Videos (>10): <input type="number" name="num" min="11" required><br><br>
        Duration (>20 sec): <input type="number" name="duration" min="21" required><br><br>
        Email Id: <input type="email" name="email" required><br><br>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""

# ---------------- EMAIL FUNCTION ---------------- #
def send_email(receiver_email, zip_path):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        raise Exception("Sender credentials not set in environment variables.")

    msg = EmailMessage()
    msg["Subject"] = "Your Mashup Result 🎵"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content("Please find your mashup zip file attached.")

    with open(zip_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="zip",
            filename=os.path.basename(zip_path)
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(msg)

# ---------------- ROUTE ---------------- #
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            singer = request.form["singer"].strip()
            n = int(request.form["num"])
            dur = int(request.form["duration"])
            email = request.form["email"].strip()

            # ---------------- VALIDATIONS ---------------- #
            if n <= 10:
                return "<h3>❌ Number of videos must be greater than 10.</h3>"

            if dur <= 20:
                return "<h3>❌ Duration must be greater than 20 seconds.</h3>"

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return "<h3>❌ Invalid Email Address.</h3>"

            output_mp3 = "mashup.mp3"
            zip_name = "mashup_result.zip"

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': 'web_audio_%(id)s.%(ext)s',
                'noplaylist': True,
                'ignoreerrors': True,
                'quiet': True
            }

            # ---------------- DOWNLOAD ---------------- #
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch{n + 5}:{singer}"])

            # ---------------- PROCESS ---------------- #
            combined = AudioSegment.empty()
            files = sorted(
                [f for f in os.listdir() if f.startswith("web_audio_") and f.endswith(".mp3")]
            )

            if len(files) < n:
                return "<h3>❌ Not enough videos found.</h3>"

            for file in files[:n]:
                audio = AudioSegment.from_file(file)
                combined += audio[:dur * 1000]
                os.remove(file)

            combined.export(output_mp3, format="mp3")

            # ---------------- ZIP ---------------- #
            with zipfile.ZipFile(zip_name, "w") as z:
                z.write(output_mp3)

            # ---------------- EMAIL ---------------- #
            send_email(email, zip_name)

            # ---------------- CLEANUP ---------------- #
            os.remove(output_mp3)
            os.remove(zip_name)

            return f"<h3>✅ Mashup successfully sent to {email}</h3>"

        except Exception as e:
            return f"<h3>❌ Error: {str(e)}</h3>"

    return render_template_string(HTML_FORM)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
