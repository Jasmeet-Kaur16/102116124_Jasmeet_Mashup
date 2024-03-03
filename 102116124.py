from moviepy.editor import *
from pytube import YouTube
from threading import Thread
from youtubesearchpython import VideosSearch


SAVE_PATH = "static/mashup/"


def get_videos(singer_name, num_videos):
    """
    Get videos from youtube
    """
    prefix = "https://www.youtube.com/watch?v="
    videosSearch = VideosSearch(singer_name, limit=num_videos)
    videos = videosSearch.result()["result"]
    videos = [prefix + video["id"] for video in videos]
    return videos


def download_video(video_url, save_path=SAVE_PATH):
    save_path = save_path + "/videos"
    yt = YouTube(video_url)
    video = yt.streams.first()
    video_title = video.default_filename.replace(" ", "_")
    video.download(save_path, video_title)
    return video_title


def convert_to_mp3(video_title, save_path=SAVE_PATH):
    mp3_save_path = save_path
    video_path = save_path + "/videos/" + video_title
    mp3_path = mp3_save_path + "/" + video_title.split(".")[0] + ".mp3"
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(mp3_path)
    audio_clip.close()
    video_clip.close()
    return mp3_path


def trim_mp3(mp3_path, duration):
    audio_clip = AudioFileClip(mp3_path)
    audio_clip = audio_clip.subclip(0, duration)
    audio_clip.write_audiofile(mp3_path)
    audio_clip.close()
    print("Done trimming " + mp3_path)


def download_and_process_video(video_url, save_path, duration):
    video_title = download_video(video_url, save_path)
    audio_title = convert_to_mp3(video_title, save_path)
    trim_mp3(audio_title, duration)


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


def mashup(singer_name, num_videos, duration, outputfilename):
    save_path = SAVE_PATH + singer_name
    videos = get_videos(singer_name, num_videos)

    threads = []
    for video in videos:
        t = Thread(target=download_and_process_video,
                   args=(video, save_path, duration))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # merge mp3s
    merge_mp3s(singer_name, save_path, outputfilename)


def main():
    if len(sys.argv) != 5:
        print(
            "Usage: python 102116124.py <singer_name> <num_videos> <duration> <outputfilename>"
        )
        return

    singer_name = sys.argv[1]
    num_videos = int(sys.argv[2])
    duration = int(sys.argv[3])
    outputfilename = sys.argv[4]

    if num_videos < 1 or duration < 1:
        print("num_videos and duration must be greater than 0")
        return

    if not outputfilename.endswith(".mp3"):
        print("outputfilename must be an mp3 file")
        return

    mashup(singer_name, num_videos, duration, outputfilename)


if __name__ == "__main__":
    main()
