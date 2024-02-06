#!/usr/bin/env python3

import logging
import string
from pathlib import Path
from typing import List

from .config import config
from .stop_words import stop_words

if Path(config.stop_words_path).is_file():
    stop_words = {line.strip() for line in Path(config.stop_words_path).read_text(encoding="utf-8").splitlines()}


punt_list = {"?", "!", ";", "？", "！", "。", "；", "……", "…", "\n"}
allow_speech_tags = {
    "an",
    "i",
    "j",
    "l",
    "n",
    "nr",
    "nrfg",
    "ns",
    "nt",
    "nz",
    "t",
    "v",
    "vd",
    "vn",
    "eng",
}


def segment(text: str) -> str:
    try:
        import jieba_fast as jieba
        import jieba_fast.posseg as pseg

        jieba.setLogLevel(logging.INFO)
    except ImportError as err:
        raise ImportError("You need to install `pip install jieba-fast` to use nlp.segment.") from err
    # 结巴分词
    jieba_result = pseg.cut(text)
    # 词性筛选
    jieba_result = [w for w in jieba_result if w.flag in allow_speech_tags]
    # 去除特殊符号
    words = [w.word.strip() for w in jieba_result if w.flag != "x"]
    # 去除停用词
    words = [word for word in words if word not in stop_words and word not in string.punctuation and len(word) > 1]
    # 英文
    words = [word.lower() for word in words]

    return " ".join(words)


def cut_sentences(text: str) -> List[str]:
    """
    Split the text into sentences.
    """
    sentences = [text]
    for sep in punt_list:
        text_list, sentences = sentences, []
        for seq in text_list:
            sentences += seq.split(sep)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    return sentences
