import sys
import os
from yt_dlp import YoutubeDL
from pydub import AudioSegment

def download_and_process(singer, n, duration, output_file):
    # Updated options to be more robust against YouTube's format changes
    ydl_opts = {
        'format': 'bestaudio/best', # Get best available audio
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song_%(id)s.%(ext)s',
        'quiet': False,
        'noplaylist': True,
        'ignoreerrors': True, # Skip a video if it's blocked/unavailable
        'cookiesfrombrowser': ('chrome',), 
    }

    # We search for slightly more than N to account for failures
    search_query = f"ytsearch{n + 5}:{singer}"
    print(f"🚀 Searching and downloading videos for {singer}...")
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
    except Exception as e:
        print(f"❌ Critical Download Error: {e}")
        return

    # Filter for the files we actually managed to download
    files = [f for f in os.listdir() if f.startswith("song_") and f.endswith(".mp3")]
    
    if len(files) < n:
        print(f"⚠️ Only found {len(files)} valid videos. Proceeding with what we have.")
    else:
        files = files[:n] # Only use the requested amount

    combined = AudioSegment.empty()
    
    print(f"✂️  Trimming first {duration}s and Merging...")
    for file in files:
        try:
            audio = AudioSegment.from_file(file)
            snippet = audio[:duration * 1000] #
            combined += snippet
        except Exception as processing_error:
            print(f"Could not process {file}: {processing_error}")
        finally:
            if os.path.exists(file):
                os.remove(file) 

    combined.export(output_file, format="mp3")
    print(f"✅ Mashup created successfully: {output_file}")

if __name__ == "__main__":
    # Parameter check as per assignment instructions
    if len(sys.argv) != 5:
        print("Usage: python3.11 102317094.py <SingerName> <NumVideos> <Duration> <OutputName>")
        sys.exit(1)

    try:
        name = sys.argv[1]
        num = int(sys.argv[2])
        dur = int(sys.argv[3])
        out = sys.argv[4]

        # Validating N > 10 and Duration > 20
        if num <= 10 or dur <= 20:
            print("Error: Number of videos must be > 10 and duration > 20.")
        else:
            download_and_process(name, num, dur, out)
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 