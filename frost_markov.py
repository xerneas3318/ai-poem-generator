import os
import random
import re
from collections import defaultdict, Counter
from typing import List, Tuple

import nltk
from nltk import word_tokenize
import pronouncing


def _ensure_nltk():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", quiet=True)

_ensure_nltk()

START = "<START>"
END = "<END>"

class TrigramModel:
    def __init__(self):
        # mapping (w1, w2) -> Counter of next words
        self.model: defaultdict[Tuple[str, str], Counter[str]] = defaultdict(Counter)

    def train(self, corpus_path: str):
        if not os.path.exists(corpus_path):
            raise FileNotFoundError(corpus_path)

        with open(corpus_path, "r", encoding="utf-8") as f:
            text = f.read()

        # normalise dashes/quotes and convert to lowercase
        text = re.sub(r"[\u2010-\u2015]", "-", text)
        sentences = nltk.sent_tokenize(text)

        for sentence in sentences:
            tokens = [START, START] + word_tokenize(sentence.lower()) + [END]
            for w1, w2, w3 in nltk.trigrams(tokens):
                self.model[(w1, w2)][w3] += 1

        # convert counters to probabilities
        for key, counter in self.model.items():
            total = sum(counter.values())
            for word in counter:
                counter[word] /= total

    def _sample_next(self, context: Tuple[str, str]) -> str:
        choices = self.model.get(context)
        if not choices:
            # unseen context, back off to any word after second token
            return random.choice(list(self.model[(context[1],) + (random.choice(list(self.model.keys()))[1],)][0]))
        r = random.random()
        cumulative = 0.0
        for word, prob in choices.items():
            cumulative += prob
            if r <= cumulative:
                return word
        return random.choice(list(choices))

    def generate_sentence(self, max_len: int = 15) -> List[str]:
        w1, w2 = START, START
        sentence = []
        while True:
            next_word = self._sample_next((w1, w2))
            if next_word == END or len(sentence) >= max_len:
                break
            sentence.append(next_word)
            w1, w2 = w2, next_word
        return sentence


def build_poem(model: TrigramModel, n_lines: int = 14, scheme: str = "AABB") -> List[str]:
    scheme = (scheme * ((n_lines // len(scheme)) + 1))[:n_lines]
    groups: defaultdict[str, List[int]] = defaultdict(list)
    for idx, letter in enumerate(scheme):
        groups[letter].append(idx)

    lines = ["" for _ in range(n_lines)]
    for letter, idxs in groups.items():
        anchor_idx = idxs[0]
        anchor_words = model.generate_sentence()
        anchor_last = _pick_rhymeable(anchor_words)
        anchor_words[-1] = anchor_last
        lines[anchor_idx] = _beautify(anchor_words)

        rhymes = pronouncing.rhymes(anchor_last) or [anchor_last]
        for i in idxs[1:]:
            sent = model.generate_sentence()
            sent[-1] = random.choice(rhymes)
            lines[i] = _beautify(sent)
    return lines


def _pick_rhymeable(words: List[str]) -> str:
    for w in reversed(words):
        if pronouncing.rhymes(w):
            return w
    return words[-1]


def _beautify(tokens: List[str]) -> str:
    if not tokens:
        return ""
    line = " ".join(tokens)
    # Capitalise first letter, fix spacing around punctuation
    line = line.capitalize()
    line = re.sub(r"\s+([,.;!?])", r"\1", line)
    return line


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Robert Frost-style poems using a trigram Markov model")
    parser.add_argument("corpus", help="Path to Frost corpus")
    parser.add_argument("--lines", type=int, default=14)
    parser.add_argument("--scheme", default="AABB")
    args = parser.parse_args()

    model = TrigramModel()
    model.train(args.corpus)

    poem = build_poem(model, n_lines=args.lines, scheme=args.scheme)
    print()
    for line in poem:
        print(line)

if __name__ == "__main__":
    main() 