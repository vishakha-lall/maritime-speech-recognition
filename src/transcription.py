import argparse
import torch
import whisper
import logging
from dataloader import BiasingProcessor
from whisper.model import WhisperBiasing
from whisper.normalizers.english import EnglishTextNormalizer

def read_audio_features(path, logger):
    logger.info(f"Reading audio features: {path}")
    audio_features = torch.load(path)
    logger.debug(f"Audio features: {audio_features}")
    return audio_features

def get_biasing_list(logger):
    with open("data/maritime_biasing_vocabulary.txt") as fin:
        rarewords = [word.strip() for word in fin]
    # logger.debug(f"Extracted rarewords: {rarewords}")
    return rarewords

#todo - generate initial prompt with vessel name

def decode_audio(audio_features, args, logger):
    if args['loadfrom'] != '':
        biasing_model = torch.load(args['loadfrom'])
        biasing_model.eval()
        model = biasing_model.whisper
    else:
        model = whisper.load_model(args['modeltype']).eval()
        biasing_model = None
    tokenizer = whisper.tokenizer.get_tokenizer(model.is_multilingual, language="en")
    biasproc = BiasingProcessor(tokenizer, args['biasinglist'], ndistractors=args['maxKBlen'], drop=args['dropentry'])
    biasing_list = get_biasing_list(logger)
    tokenized_words = []
    for word in biasing_list:
        word = word.lower()
        wordcap = word[0:1].upper() + word[1:]
        tok_word = tokenizer.encode(" " + word)
        tokenized_words.append(tuple(tok_word))
        tokenized_words.append(tuple(tokenizer.encode(" "+wordcap)))
    origtree = biasproc.get_lextree(tokenized_words)
    # biasing_model.GNN(origtree, model.decoder.token_embedding)
    options = whisper.DecodingOptions(
        language="en",
        without_timestamps=True,
        beam_size=args['beamsize'],
        biasing=args['biasing'],
        biasingmodule=biasing_model,
        origtree=origtree,
        fp16=False,
        shallowfusion=False,
        lm_weight=args['lm_weight'],
        ilm_weight=args['ilm_weight'],
        ilme_model=None,
        prompt=args['prompt']
    )
    result = whisper.decode(model, audio_features.to(model.device), options)
    logger.debug(f"Result: {result}")
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, default='temp/audio.pt')
    parser.add_argument('--loglevel', type=str, choices=['DEBUG','INFO'], default='DEBUG')
    parser.add_argument('--beamsize', type=int, default=5)
    parser.add_argument('--loadfrom', type=str, default="models/model.acc.best")
    parser.add_argument('--biasing', action="store_true", default=True)
    parser.add_argument('--lm_weight', type=float, default=0)
    parser.add_argument('--ilm_weight', type=float, default=0)
    parser.add_argument('--deepbiasing', action="store_true")
    parser.add_argument('--attndim', type=int, default=256)
    parser.add_argument('--biasinglist', type=str, default="data/maritime_biasing_vocabulary.txt")
    parser.add_argument('--dropentry', type=float, default=0.0)
    parser.add_argument('--modeltype', type=str, default="base.en")
    parser.add_argument('--maxKBlen', type=int, default=1)
    parser.add_argument('--prompt', type=str, default='<|startoftranscript|>')
    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)
    logging.info(f"Log level: {args.loglevel}")
    logger = logging.getLogger(__name__)

    audio_features = read_audio_features(args.path, logger)
    decode_audio(audio_features, vars(args), logger)
