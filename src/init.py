import argparse
import logging
from pathlib import Path
import os
import csv
import shutil
import pandas as pd
from pydub import AudioSegment
import extract_audio
import split_audio
import audio_preprocessing
import transcription
import location_extraction
import communication_level_extraction
import speaker_diarization
import generate_subtitles
import detect_response_time
import communication_match

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='INFO')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    demanding_event_timestamp_path = Path(args.path) / 'de_timestamps.csv'
    demanding_event_timestamp = pd.read_csv(demanding_event_timestamp_path)
    video = extract_audio.read_video_file(Path(args.path) / 'rendered.mp4', logger)
    extract_audio.extract_audio(video, logger)

    audio = split_audio.read_audio_file('temp/extracted_audio/extracted_audio.mp3', logger)
    de_audio_paths = split_audio.split_on_demanding_event(audio, demanding_event_timestamp_path, logger)

    for demanding_event, audio_path in de_audio_paths:
        audio = split_audio.read_audio_file(audio_path, logger)
        split_audio.split_into_chunks(audio, demanding_event, logger)

        chunks_path = Path(f'temp/extracted_chunks/{demanding_event}')
        chunks_timestamps = pd.read_csv(f'temp/extracted_timestamps/{demanding_event}/timestamps.csv')

        segments = []

        export_folder_csv = Path.cwd() / f'temp/extracted_communication_levels/{demanding_event}'
        if export_folder_csv.exists() and export_folder_csv.is_dir():
            shutil.rmtree(export_folder_csv)
        Path(export_folder_csv).mkdir(parents=True, exist_ok=True)
        f = open(f'{export_folder_csv}/communication_levels.csv', 'w')
        writer = csv.writer(f)
        writer.writerow(['transcript', 'level', 'entity'])
        
        for i, chunk in enumerate(sorted(os.listdir(chunks_path))):
            logger.info(f"Processing audio chunk {chunk}")
            chunk_path = chunks_path / chunk
            speaker_diarization.segment_audio_by_speakers(chunk_path, chunk[:-4], demanding_event, logger)
            timestamps_path = Path(f'temp/extracted_timestamps/speaker_diarization/{demanding_event}') / chunk[:-4]
            timestamps = pd.read_csv(timestamps_path / 'timestamps.csv')
            previous_segment_transcript = "<|startoftranscript|>"
            chunk_audio = AudioSegment.from_mp3(chunk_path)
            export_folder_transcript_csv = Path.cwd() / f'temp/extracted_text/{demanding_event}'
            if export_folder_transcript_csv.exists() and export_folder_transcript_csv.is_dir():
                shutil.rmtree(export_folder_transcript_csv)
            Path(export_folder_transcript_csv).mkdir(parents=True, exist_ok=True)
            f = open(Path(export_folder_transcript_csv) / f'{chunk[:-4]}.csv', 'w')
            chunk_transcript_file = csv.writer(f)
            chunk_transcript_file.writerow(['start', 'transcript'])
            for row in range(len(timestamps)):
                segment_audio = chunk_audio[timestamps.at[row, 'start']*1000:timestamps.at[row, 'end']*1000]
                segment_path = Path('temp/audio.mp3')
                segment_audio.export(segment_path, format="mp3")
                segment_audio = audio_preprocessing.read_audio_file(segment_path, logger)
                audio_preprocessing.extract_mel_features(segment_audio, logger)
                audio_features = transcription.read_audio_features('temp/audio.pt', logger)
                options = {
                    "loadfrom":'models/model.acc.best',
                    "biasinglist":'data/maritime_biasing_vocabulary.txt', 
                    "modeltype":'base.en',
                    "beamsize": 5,
                    "biasing": True,
                    "maxKBlen": 1,
                    "dropentry":0.0,
                    "lm_weight": 0,
                    "ilm_weight": 0,
                    "prompt": previous_segment_transcript
                }
                result = transcription.decode_audio(audio_features, options, logger)
                if result is not None:
                    logger.info(f"{chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'start']} {timestamps.at[row, 'speaker_id']} : {result.text}")
                    chunk_transcript_file.writerow([chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'start'], result.text])
                    segments.append(generate_subtitles.Segment(chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'start'], chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'end'], f"{timestamps.at[row, 'speaker_id']} : {result.text}"))
                    location_matcher = location_extraction.create_matcher('data/location_labels', logger)
                    extracted_locations = location_extraction.find_matches(result.text, location_matcher, logger)
                    communication_level_matcher = communication_level_extraction.create_matcher('data/external_labels', 'data/internal_labels', logger)
                    communication_levels = communication_level_extraction.find_matches(result.text, communication_level_matcher, logger)
                    level, entity = communication_level_extraction.find_communication_level(communication_levels, logger)
                    previous_segment_transcript = result.text
                    writer.writerow([result.text, level, entity])

        generate_subtitles.generate_subtitle_file(demanding_event, segments)
        detect_response_time.find_response_time(demanding_event, demanding_event_timestamp[demanding_event_timestamp['demanding_event'] == demanding_event]['timestamp_start'].item(), logger)
        communication_match.find_match_score(demanding_event_timestamp[demanding_event_timestamp['demanding_event'] == demanding_event]['timestamp_start'].item(), demanding_event_timestamp[demanding_event_timestamp['demanding_event'] == demanding_event]['timestamp_end'].item(), demanding_event, logger)