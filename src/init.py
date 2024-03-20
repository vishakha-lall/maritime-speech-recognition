import argparse
import logging
from pathlib import Path
import os
import extract_audio
import split_audio
import audio_preprocessing
import transcription

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

    previous_chunk_transcript = "We are analysing the recorded maritime communication from vessel Cosulich Adventurer "
    chunks_path = Path('temp/extracted_chunks')
    for chunk in sorted(os.listdir(chunks_path)):
        logger.info(f"Processing audio chunk {chunk}")
        chunk_path = chunks_path / chunk
        audio = audio_preprocessing.read_audio_file(chunk_path, logger)
        audio_preprocessing.extract_mel_features(audio, logger)
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
            "prompt": previous_chunk_transcript
        }
        transcription.decode_audio(audio_features, options, logger)
        break
