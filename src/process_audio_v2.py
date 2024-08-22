import shutil
import logging
import argparse
import split_audio
import video_utils
import pandas as pd
import transcription_v2
import concurrent.futures
import speaker_diarization
import split_audio_by_voice_activity_detection

from tqdm import tqdm
from pathlib import Path
from communication_analysis import get_communication_adherance, get_communication_entities, setup_pipeline


def create_export_path(results_path, demanding_event, logger):
    export_folder = Path.cwd() / f'{results_path}/{demanding_event}'
    if export_folder.exists() and export_folder.is_dir():
        shutil.rmtree(export_folder)
    Path(export_folder).mkdir(parents=True, exist_ok=True)
    logger.debug(f'Export path created: {export_folder}')
    return export_folder


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_path', type=str, required=True)
    parser.add_argument('--csv_path', type=str, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='INFO')
    parser.add_argument('--results_path', type=str, default='temp')
    parser.add_argument('--subject_id', type=str, default='test_subject')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    demanding_event_timestamp_path = Path(args.csv_path)
    video_utils.extract_audio(Path(args.video_path),
                              Path('temp/extracted_audio/'))

    de_audio = split_audio.split_on_demanding_event(
        'temp/extracted_audio/extracted_audio.mp3', demanding_event_timestamp_path, logger)

    model = transcription_v2.load_model('./models/transcription_model', logger)
    llm_model, llm_tokenizer = setup_pipeline(logger)

    results_path = Path(args.results_path) / args.subject_id
    full_transcript_df = pd.DataFrame()

    for demanding_event, audio, sample_rate in de_audio:
        logger.info(
            f'Processing demanding event {demanding_event} for {args.subject_id}')
        results_path_demanding_event = create_export_path(
            results_path, demanding_event, logger)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_speaker_map = executor.submit(
                speaker_diarization.build_speaker_map, audio, sample_rate, demanding_event, logger)
            future_segments = executor.submit(
                split_audio_by_voice_activity_detection.split_into_chunks, audio, sample_rate, demanding_event, logger)
            speaker_map = future_speaker_map.result()
            segments = future_segments.result()
        transcript_by_segment_and_speaker = []
        for segment_id, segment in tqdm(enumerate(segments)):
            segment_start = segment[0]
            segment_end = segment[1]
            segments_by_speakers = speaker_diarization.identify_speakers_in_segment(
                segment_start, segment_end, demanding_event, logger, speaker_map)
            for segment_by_speaker in segments_by_speakers:
                segment_by_speaker_start = segment_by_speaker[0]
                segment_by_speaker_end = segment_by_speaker[1]
                speaker = segment_by_speaker[2]
                logger.debug(
                    f'Processing segment between {segment_by_speaker_start} and {segment_by_speaker_end}')
                print(audio.shape)
                segment_audio = audio[:, int(segment_by_speaker_start * sample_rate / 1000):int(
                    segment_by_speaker_end * sample_rate / 1000)]
                print(segment_audio.shape)
                segment_transcript = transcription_v2.get_transcript_for_segment(
                    model, segment_audio, sample_rate, logger)
                if segment_transcript != '':
                    transcript_by_segment_and_speaker.append({
                        'segment_id': segment_id,
                        'start': segment_by_speaker_start,
                        'end': segment_by_speaker_end,
                        'speaker': speaker,
                        'text': segment_transcript})
        transcript_df = pd.DataFrame(transcript_by_segment_and_speaker)
        full_transcript_df = pd.concat(
            [full_transcript_df, transcript_df], ignore_index=True)
        transcript_df.to_csv(results_path_demanding_event / 'transcript.csv')
        logger.info(
            f'Transcript for {args.subject_id} {demanding_event} saved in {results_path_demanding_event}')
        get_communication_entities(
            transcript_by_segment_and_speaker, results_path_demanding_event, llm_model, llm_tokenizer, logger)
        get_communication_adherance(
            transcript_by_segment_and_speaker, demanding_event, results_path_demanding_event, llm_model, llm_tokenizer, logger)
    full_transcript_df.to_csv(results_path / 'transcript.csv')

    # video_utils.generate_subtitle_file(
    #     results_path, full_transcript_df.to_dict('records'), args.video_path)