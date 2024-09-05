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
from segment_orm_crud import create_segment
from client_orm_crud import get_client_by_id
from session_orm_crud import get_session_by_id
from transcript_orm_crud import create_transcript
from speaker_diarization_orm_crud import create_speaker_diarization
from communication_analysis import get_communication_adherance, get_communication_entities, setup_pipeline
from demanding_event_session_mapping_orm_crud import get_demanding_event_session_mapping_by_session_id, get_demanding_event_session_mapping_by_session_id_demanding_event_id


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
    parser.add_argument('--session_id', type=int, required=True)
    parser.add_argument('--loglevel', type=str,
                        choices=['DEBUG', 'INFO'], default='INFO')
    parser.add_argument('--results_path', type=str, default='temp')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f'Log level: {args.loglevel}')
    logger = logging.getLogger(__name__)

    demanding_event_session_mappings = get_demanding_event_session_mapping_by_session_id(
        args.session_id)

    video_utils.extract_audio(Path(args.video_path),
                              Path('temp/extracted_audio/'))

    de_audio = split_audio.split_on_demanding_event(
        'temp/extracted_audio/extracted_audio.mp3', demanding_event_session_mappings, logger)

    model = transcription_v2.load_model('./models/transcription_model', logger)
    llm_model, llm_tokenizer = setup_pipeline(logger)

    session = get_session_by_id(args.session_id)
    client = get_client_by_id(session.client_id)
    results_path = Path(args.results_path) / str(session.date) / f'{client.alias}_{session.subject_id}' / f'exer_{session.exercise_id}'
    full_transcript_df = pd.DataFrame()

    for demanding_event, audio, sample_rate in de_audio:
        logger.info(
            f'Processing demanding event {demanding_event.type} for {session.subject_id}')
        demanding_event_session_mapping = get_demanding_event_session_mapping_by_session_id_demanding_event_id(
            session.id, demanding_event.id)
        demanding_event_start, demanding_event_end = demanding_event_session_mapping.time_start, demanding_event_session_mapping.time_end
        results_path_demanding_event = create_export_path(
            results_path, demanding_event.type, logger)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_speaker_map = executor.submit(
                speaker_diarization.build_speaker_map, audio, sample_rate, demanding_event.type, logger)
            future_segments = executor.submit(
                split_audio_by_voice_activity_detection.split_into_chunks, audio, sample_rate, demanding_event.type, logger)
            speaker_map = future_speaker_map.result()
            segments = future_segments.result()
        transcript_by_segment_and_speaker = []
        for segment in tqdm(segments):
            segment_start = segment[0]
            segment_end = segment[1]
            segment_id = create_segment(
                session.id, demanding_event.id, (segment_start+(demanding_event_start*1000))/1000, (segment_end+(demanding_event_start*1000))/1000)
            segments_by_speakers = speaker_diarization.identify_speakers_in_segment(
                segment_start, segment_end, demanding_event.type, logger, speaker_map)
            for segment_by_speaker in segments_by_speakers:
                segment_by_speaker_start = segment_by_speaker[0]
                segment_by_speaker_end = segment_by_speaker[1]
                speaker = segment_by_speaker[2]
                speaker_diarization_id = create_speaker_diarization(
                    segment_id, speaker, (segment_by_speaker_start+(demanding_event_start*1000))/1000, (segment_by_speaker_end+(demanding_event_start*1000))/1000)
                logger.debug(
                    f'Processing segment between {segment_by_speaker_start} and {segment_by_speaker_end}')
                segment_audio = audio[:, int(segment_by_speaker_start * sample_rate / 1000):int(
                    segment_by_speaker_end * sample_rate / 1000)]
                segment_transcript = transcription_v2.get_transcript_for_segment(
                    model, segment_audio, sample_rate, logger)
                if segment_transcript != '':
                    create_transcript(
                        segment_id, speaker_diarization_id, segment_transcript)
                    transcript_by_segment_and_speaker.append({
                        'segment_id': segment_id,
                        'start': (segment_by_speaker_start+(demanding_event_start*1000))/1000,
                        'end': (segment_by_speaker_end+(demanding_event_start*1000))/1000,
                        'speaker': speaker,
                        'text': segment_transcript})
        transcript_df = pd.DataFrame(transcript_by_segment_and_speaker)
        full_transcript_df = pd.concat(
            [full_transcript_df, transcript_df], ignore_index=True)
        transcript_df.to_csv(results_path_demanding_event / 'transcript.csv')
        logger.info(
            f'Transcript for {session.subject_id} {demanding_event.type} saved in {results_path_demanding_event}')
        get_communication_entities(
            transcript_by_segment_and_speaker, results_path_demanding_event, llm_model, llm_tokenizer, logger)
        get_communication_adherance(
            transcript_by_segment_and_speaker, demanding_event.type, results_path_demanding_event, llm_model, llm_tokenizer, logger)
    full_transcript_df.to_csv(results_path / 'transcript.csv')

    # video_utils.generate_subtitle_file(
    #     results_path, full_transcript_df.to_dict('records'), args.video_path)
