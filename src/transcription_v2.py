import torch

from transformers import pipeline


def load_model(path, logger):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    logger.info(f'Loading ASR model from {path}')
    return pipeline("automatic-speech-recognition", model=path, chunk_length_s=30, device=device)


def get_transcript_for_segment(pipeline, audio, sample_rate, logger):
    print(audio.shape)
    result = pipeline({"raw": audio.numpy().squeeze(),
                      "sampling_rate": sample_rate})
    logger.debug(f'Transcription result {result}')
    return result['text']
