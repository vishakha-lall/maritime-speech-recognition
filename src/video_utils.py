import argparse
import pandas as pd

from multiprocessing import cpu_count

from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip


def extract_audio(video_path, extracted_path):
    video = VideoFileClip(str(video_path), target_resolution=(360, 640))
    audio = video.audio
    audio.write_audiofile(extracted_path / 'extracted_audio.mp3')
    video.close()
    audio.close()


def create_subtitle_clip(subtitles):
    def generator(txt):
        return TextClip(txt, font='Arial', fontsize=24, color='white', bg_color='black')
    subtitle_list = [((float(subtitle['start'])/1000, float(subtitle['end'])/1000),
                      f"{subtitle['speaker']}: {subtitle['text']}") for subtitle in subtitles]
    return SubtitlesClip(subtitle_list, generator)


def generate_subtitle_file(subtitle_path, transcripts, video_path):
    video = VideoFileClip(video_path, target_resolution=(360, 640))
    subtitle_clip = create_subtitle_clip(transcripts)
    final_video = CompositeVideoClip(
        [video, subtitle_clip.set_position(('center', 'bottom'))])
    final_video.write_videofile(
        f'{subtitle_path}/rendered_video_with_subtitles.mp4', threads=32, fps=24)
    video.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--csvpath', type=str, required=True)
    parser.add_argument('--resultpath', type=str, required=True)
    parser.add_argument('--videopath', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='DEBUG')
    args = parser.parse_args()

    transcripts = pd.read_csv(args.csvpath).to_dict('records')
    generate_subtitle_file(args.resultpath, transcripts, args.videopath)
