import os
from flask import Flask, render_template, request, send_file
from moviepy.editor import *
from pytube import YouTube
from threading import Thread
from youtubesearchpython import VideosSearch
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

SAVE_PATH = "/tmp/static/mashup/"
# app.static_folder = "static"

# Email configuration
EMAIL_ADDRESS = "jkaur8_be21@thapar.edu"
EMAIL_PASSWORD = "obrk lbuh pmbn trcw"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/mashup", methods=["POST"])
def mashup():
    singer_name = request.form.get("singer_name")
    num_videos = int(request.form.get("num_videos"))
    duration = int(request.form.get("duration"))
    outputfilename = request.form.get("outputfilename")
    recipient_email = request.form.get("email")  # Get recipient email address

    # Validate input parameters
    if num_videos < 1 or duration < 1:
        return "num_videos and duration must be greater than 0"
    if not outputfilename.endswith(".mp3"):
        return "outputfilename must be an mp3 file"

    save_path = os.path.join(SAVE_PATH, singer_name)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Get videos and process them in parallel
    videos = get_videos(singer_name, num_videos)
    threads = []
    for video in videos:
        t = Thread(target=download_and_process_video,
                   args=(video, save_path, duration))
        t.start()
        threads.append(t)

    # Wait for all threads to finish
    for t in threads:
        t.join()

    # Merge processed audio files
    merge_mp3s(singer_name, save_path, outputfilename)

    mashup_file_path = os.path.join(save_path, outputfilename)

    # Send mashup file as a download attachment
    if os.path.exists(mashup_file_path):
        # Send the file via email
        send_email_with_attachment(recipient_email, mashup_file_path)
        return "Mashup file sent to the provided email address!"
    else:
        return "Error: Mashup file not found!"


def get_videos(singer_name, num_videos):
    prefix = "https://www.youtube.com/watch?v="
    videosSearch = VideosSearch(singer_name, limit=num_videos)
    videos = videosSearch.result()["result"]
    videos = [prefix + video["id"] for video in videos]
    return videos


def download_and_process_video(video_url, save_path, duration):
    try:
        video_title = download_video(video_url, save_path)
        audio_title = convert_to_mp3(video_title, save_path)
        trim_mp3(audio_title, duration)
    except Exception as e:
        print(f"Error processing video: {e}")


def download_video(video_url, save_path):
    save_path = os.path.join(save_path, "videos")
    yt = YouTube(video_url)
    video = yt.streams.filter(progressive=True).first()
    video_title = video.default_filename.replace(" ", "_")
    video.download(save_path, video_title)
    return video_title


def convert_to_mp3(video_title, save_path):
    mp3_save_path = save_path
    video_path = os.path.join(save_path, "videos", video_title)
    mp3_path = os.path.join(
        mp3_save_path, f"{os.path.splitext(video_title)[0]}.mp3")
    print(mp3_path)
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio.write_audiofile(mp3_path)
    audio_clip.close()
    video_clip.close()
    return mp3_path


def trim_mp3(mp3_path, duration):
    audio_clip = AudioFileClip(mp3_path)
    audio_clip = audio_clip.subclip(0, duration)
    audio_clip.write_audiofile(mp3_path)
    audio_clip.close()


def merge_mp3s(singer_name, save_path=SAVE_PATH, outputfilename="mashup.mp3", codec='mp3', bitrate='32k'):
    final_mp3_path = save_path + "/" + outputfilename
    mp3s = [
        save_path + "/" + mp3 for mp3 in os.listdir(save_path) if mp3.endswith(".mp3")
    ]
    final_clip = concatenate_audioclips([AudioFileClip(mp3) for mp3 in mp3s])
    final_clip.write_audiofile(final_mp3_path, codec=codec, bitrate=bitrate)
    final_clip.close()
    # print("Done merging and compressing mp3s to " + final_mp3_path)
    return


def send_email_with_attachment(recipient_email, attachment_path):
    msg = EmailMessage()
    msg['Subject'] = 'Mashup File'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient_email

    # Add attachment
    with open(attachment_path, 'rb') as file:
        file_data = file.read()
        file_name = os.path.basename(attachment_path)
    msg.add_attachment(file_data, maintype='audio',
                       subtype='mp3', filename=file_name)

    # Send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)


# if __name__ == "__main__":
#     app.run(debug=True)
