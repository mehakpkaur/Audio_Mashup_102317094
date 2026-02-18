import sys
import os
import smtplib
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from email.message import EmailMessage


def download_and_process(singer, n, duration, output_file):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song_%(id)s.%(ext)s',
        'quiet': False,
        'noplaylist': True,
        'ignoreerrors': True,
        'cookiesfrombrowser': ('chrome',),
    }

    search_query = f"ytsearch{n + 5}:{singer}"
    print(f"🚀 Searching and downloading videos for {singer}...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return False

    files = [f for f in os.listdir() if f.startswith("song_") and f.endswith(".mp3")]

    if len(files) < n:
        print(f"⚠️ Only found {len(files)} valid videos. Proceeding with available files.")
    else:
        files = files[:n]

    combined = AudioSegment.empty()

    print(f"✂️ Trimming first {duration}s and merging...")

    for file in files:
        try:
            audio = AudioSegment.from_file(file)
            snippet = audio[:duration * 1000]
            combined += snippet
        except Exception as e:
            print(f"Error processing {file}: {e}")
        finally:
            if os.path.exists(file):
                os.remove(file)

    combined.export(output_file, format="mp3")
    print(f"✅ Mashup created successfully: {output_file}")
    return True


def send_email(receiver_email, file_path):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ Sender email credentials not set in environment variables.")
        return

    msg = EmailMessage()
    msg["Subject"] = "Your Mashup is Ready 🎵"
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg.set_content("Hi,\n\nPlease find your mashup attached.\n\nRegards")

    with open(file_path, "rb") as f:
        file_data = f.read()
        file_name = f.name

    msg.add_attachment(file_data, maintype="audio", subtype="mp3", filename=file_name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print("📧 Email sent successfully!")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")


if __name__ == "__main__":

    if len(sys.argv) != 6:
        print("Usage: python3.11 102317094.py <SingerName> <NumVideos> <Duration> <OutputName> <UserEmail>")
        sys.exit(1)

    try:
        name = sys.argv[1]
        num = int(sys.argv[2])
        dur = int(sys.argv[3])
        out = sys.argv[4]
        user_email = sys.argv[5]

        if num <= 10 or dur <= 20:
            print("Error: Number of videos must be > 10 and duration must be > 20 seconds.")
        else:
            success = download_and_process(name, num, dur, out)
            if success:
                send_email(user_email, out)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
