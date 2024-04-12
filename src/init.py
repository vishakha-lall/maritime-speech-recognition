import argparse
import logging
from pathlib import Path
import os
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='INFO')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    video = extract_audio.read_video_file(args.path, logger)
    extract_audio.extract_audio(video, logger)

    audio = split_audio.read_audio_file('temp/extracted_audio/extracted_audio.mp3', logger)
    split_audio.split_into_chunks(audio, logger)

    chunks_path = Path('temp/extracted_chunks')
    chunks_timestamps = pd.read_csv('temp/extracted_timestamps/timestamps.csv')

    segments = []

    for i, chunk in enumerate(sorted(os.listdir(chunks_path))):
        logger.info(f"Processing audio chunk {chunk}")
        chunk_path = chunks_path / chunk
        speaker_diarization.segment_audio_by_speakers(chunk_path, chunk[:-4], logger)
        timestamps_path = Path('temp/extracted_timestamps/speaker_diarization') / chunk[:-4]
        timestamps = pd.read_csv(timestamps_path / 'timestamps.csv')
        previous_segment_transcript = "<|startoftranscript|>"
        chunk_audio = AudioSegment.from_mp3(chunk_path)
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
                "beamsize": 3,
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
                segments.append(generate_subtitles.Segment(chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'start'], chunks_timestamps[chunks_timestamps['chunk_id']==i]['start'].item() + timestamps.at[row, 'end'], f"{timestamps.at[row, 'speaker_id']} : {result.text}"))
                location_matcher = location_extraction.create_matcher('data/location_labels', logger)
                extracted_locations = location_extraction.find_matches(result.text, location_matcher, logger)
                communication_level_matcher = communication_level_extraction.create_matcher('data/external_labels', 'data/internal_labels', logger)
                communication_levels = communication_level_extraction.find_matches(result.text, communication_level_matcher, logger)
                communication_level_extraction.find_communication_level(communication_levels, logger)
                previous_segment_transcript = result.text

    generate_subtitles.generate_subtitle_file(segments)
    # previous_chunk_transcript = "<|startoftranscript|>"
    # chunks_path = Path('temp/extracted_chunks')
    # for chunk in sorted(os.listdir(chunks_path)):
    #     logger.info(f"Processing audio chunk {chunk}")
    #     chunk_path = chunks_path / chunk
    #     audio = audio_preprocessing.read_audio_file(chunk_path, logger)
    #     audio_preprocessing.extract_mel_features(audio, logger)
    #     audio_features = transcription.read_audio_features('temp/audio.pt', logger)
    #     options = {
    #         "loadfrom":'models/model.acc.best',
    #         "biasinglist":'data/maritime_biasing_vocabulary.txt', 
    #         "modeltype":'base.en',
    #         "beamsize": 3,
    #         "biasing": True,
    #         "maxKBlen": 1,
    #         "dropentry":0.0,
    #         "lm_weight": 0,
    #         "ilm_weight": 0,
    #         "prompt": previous_chunk_transcript
    #     }
    #     result = transcription.decode_audio(audio_features, options, logger)
    #     if result is not None:
    #         logger.info(f"Detected transcript {result.text}")
    #         location_matcher = location_extraction.create_matcher('data/location_labels', logger)
    #         extracted_locations = location_extraction.find_matches(result.text, location_matcher, logger)
    #         communication_level_matcher = communication_level_extraction.create_matcher('data/external_labels', 'data/internal_labels', logger)
    #         communication_levels = communication_level_extraction.find_matches(result.text, communication_level_matcher, logger)
    #         communication_level_extraction.find_communication_level(communication_levels, logger)
