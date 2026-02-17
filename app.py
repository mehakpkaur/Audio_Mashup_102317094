import os
import zipfile
import smtplib
from email.message import EmailMessage
from flask import Flask, request, render_template_string
from yt_dlp import YoutubeDL
from pydub import AudioSegment

app = Flask(__name__)

# The HTML form matches the assignment requirements
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

def send_email(target_email, zip_path):
    msg = EmailMessage()
    msg['Subject'] = 'Your Mashup Result'
    msg['From'] = 'mkaur4_be23@thapar.edu' 
    msg['To'] = target_email
    msg.set_content('Attached is your requested mashup zip file.')

    with open(zip_path, 'rb') as f:
        msg.add_attachment(f.read(), maintype='application', subtype='zip', filename=os.path.basename(zip_path))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        # Using the App Password you provided
        smtp.login('mkaur4_be23@thapar.edu', 'rwhe zzow qjga iera') 
        smtp.send_message(msg)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Fixed: Correctly assigning variables from the form
        singer = request.form["singer"]
        n = int(request.form["num"])
        dur = int(request.form["duration"])
        email = request.form["email"]
        
        output_mp3 = "mashup.mp3"
        zip_name = "mashup_result.zip"

        # yt-dlp options to handle YouTube downloads robustly
        ydl_opts = {
            'format': 'bestaudio/best',  # Get best available audio
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'web_audio_%(id)s.%(ext)s',
            'cookiesfrombrowser': ('chrome',), 
            'noplaylist': True,
            'ignoreerrors': True,  # <--- CRITICAL: This skips the "format not available" error
            'quiet': True,
        }

        try:
            # 1. Download from YouTube
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"ytsearch{n}:{singer}"])

            # 2. Process and Merge
            combined = AudioSegment.empty()
            # Only look for the files we just downloaded
            files = [f for f in os.listdir() if f.startswith("web_audio_") and f.endswith(".mp3")]
            
            for f in files[:n]:
                audio = AudioSegment.from_file(f)
                combined += audio[:dur * 1000] # Use dur from form
                os.remove(f) # Clean up individual files
            
            combined.export(output_mp3, format="mp3")

            # 3. Create Zip file as required
            with zipfile.ZipFile(zip_name, 'w') as z:
                z.write(output_mp3)

            # 4. Send via Email
            send_email(email, zip_name)

            # Final Cleanup
            if os.path.exists(output_mp3): os.remove(output_mp3)
            if os.path.exists(zip_name): os.remove(zip_name)

            return f"<h3>✅ Success! Mashup sent to {email}</h3>"
            
        except Exception as e:
            return f"<h3>❌ Error: {str(e)}</h3>"

    return render_template_string(HTML_FORM)

if __name__ == "__main__":
    app.run(debug=True, port=5000)