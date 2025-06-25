import os
import random
import re
from collections import defaultdict, Counter
from typing import List, Tuple

import nltk
from nltk import word_tokenize, pos_tag
from nltk.util import bigrams
import pronouncing

# Make sure the required nltk resources are available
def _ensure_nltk_downloads():
    required = ["punkt", "averaged_perceptron_tagger", "punkt_tab"]
    for res in required:
        try:
            if res == "punkt":
                nltk.data.find("tokenizers/punkt")
            elif res == "punkt_tab":
                nltk.data.find("tokenizers/punkt_tab")
            else:
                nltk.data.find(f"taggers/{res}")
        except LookupError:
            print(f"Downloading {res}...")
            nltk.download(res, quiet=True)

_ensure_nltk_downloads()

#############################
# Data loading & preprocessing
#############################

def load_corpus(path: str) -> List[List[Tuple[str, str]]]:
    """Load a corpus from a text file, returning a list of POS-tagged sentences.

    Each sentence is a list of (word, POS) tuples.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Corpus file '{path}' not found. Please place a Robert Frost poem corpus there."
        )

    # Read raw text and split into sentences (very naive – can be improved)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    # Replace fancy quotes/dashes etc.
    raw = re.sub(r"[\u2010-\u2015]", "-", raw)

    sentences = nltk.sent_tokenize(raw)
    tagged_sentences: List[List[Tuple[str, str]]] = []
    for sent in sentences:
        tokens = word_tokenize(sent)
        # Filter out purely punctuation tokens because they confuse the model
        tokens = [t for t in tokens if re.search(r"[A-Za-z]", t)]
        if not tokens:
            continue
        tagged = pos_tag(tokens)
        tagged_sentences.append(tagged)
    return tagged_sentences

#############################
# Model training
#############################

class HiddenMarkovPoet:
    """Very small HMM where hidden states are coarse-grained POS tags."""

    def __init__(self):
        # Probability tables
        self.transition: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.emission: defaultdict[str, Counter[str]] = defaultdict(Counter)
        self.start: Counter[str] = Counter()

    def train(self, tagged_sentences: List[List[Tuple[str, str]]]):
        for sent in tagged_sentences:
            if not sent:
                continue
            prev_state = None
            for (word, pos) in sent:
                state = self._coarse_pos(pos)
                self.emission[state][word.lower()] += 1
                if prev_state is None:
                    self.start[state] += 1
                else:
                    self.transition[prev_state][state] += 1
                prev_state = state

        # Convert to probabilities (with add-one smoothing)
        self._normalise_counters(self.start)
        for state, counter in self.transition.items():
            self._normalise_counters(counter)
        for state, counter in self.emission.items():
            self._normalise_counters(counter)

    @staticmethod
    def _coarse_pos(pos: str) -> str:
        # Group POS into broad categories for a smaller state-space
        if pos.startswith("N"):
            return "NOUN"
        if pos.startswith("V"):
            return "VERB"
        if pos.startswith("J"):
            return "ADJ"
        if pos.startswith("R"):
            return "ADV"
        return "OTHER"

    @staticmethod
    def _normalise_counters(counter: Counter[str]):
        total = sum(counter.values())
        for k in list(counter):
            counter[k] = counter[k] / total

    #############################
    # Generation helpers
    #############################

    def _sample(self, distribution: Counter[str]) -> str:
        r = random.random()
        cumulative = 0.0
        for item, prob in distribution.items():
            cumulative += prob
            if r <= cumulative:
                return item
        # Fallback (shouldn't happen due to numerical issues)
        return random.choice(list(distribution))

    def generate_sentence(self, max_len: int = 12) -> List[str]:
        sentence_states: List[str] = []
        sentence_words: List[str] = []

        first_state = self._sample(self.start)
        sentence_states.append(first_state)
        word = self._sample(self.emission[first_state])
        sentence_words.append(word)

        while len(sentence_words) < max_len:
            prev_state = sentence_states[-1]
            next_state = self._sample(self.transition[prev_state])
            sentence_states.append(next_state)
            next_word = self._sample(self.emission[next_state])
            sentence_words.append(next_word)

            # Occasionally end early if last word ends with period or we reach length
            if len(sentence_words) >= 5 and random.random() < 0.2:
                break
        return sentence_words

    #############################
    # Poem generation interface
    #############################

    def generate_poem(
        self,
        n_lines: int = 14,
        max_len: int = 12,
        rhyme: bool = True,
        rhyme_scheme: str = "AABB",
    ) -> List[str]:
        """Generate a poem of n_lines lines.

        rhyme_scheme should be something like "AABB" (repeated to length) or "ABAB".
        """
        if not rhyme:
            return [" ".join(self.generate_sentence(max_len)).capitalize() for _ in range(n_lines)]

        # Build mapping letter -> list of words that rhyme
        scheme_letters = (rhyme_scheme * ((n_lines // len(rhyme_scheme)) + 1))[:n_lines]
        groups: defaultdict[str, List[int]] = defaultdict(list)
        for idx, ch in enumerate(scheme_letters):
            groups[ch].append(idx)

        lines: List[str] = [""] * n_lines
        line_end_words: dict[str, str] = {}

        for letter, indices in groups.items():
            # Generate a line, pick last word, then generate rhymes for the rest
            anchor_line = indices[0]
            words = self.generate_sentence(max_len)
            anchor_last = self._pick_rhymeable_word(words)
            words[-1] = anchor_last
            lines[anchor_line] = " ".join(words).capitalize()
            line_end_words[letter] = anchor_last

            # Fill rest with rhymes
            rhymes = pronouncing.rhymes(anchor_last)
            if not rhymes:
                rhymes = [anchor_last]

            for idx in indices[1:]:
                candidate_rhyme = random.choice(rhymes)
                sent = self.generate_sentence(max_len)
                sent[-1] = candidate_rhyme
                lines[idx] = " ".join(sent).capitalize()

        return lines

    def _pick_rhymeable_word(self, words: List[str]) -> str:
        # Choose a word with available rhymes; fallback to last word
        for w in reversed(words):
            if pronouncing.rhymes(w):
                return w
        return words[-1]

#############################
# Convenience CLI usage
#############################

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Robert Frost-style poems using an HMM")
    parser.add_argument("corpus", help="Path to a text file containing Robert Frost poems")
    parser.add_argument("--lines", type=int, default=14, help="Number of lines in the poem")
    parser.add_argument("--scheme", default="AABB", help="Rhyme scheme, e.g. AABB or ABAB")
    args = parser.parse_args()

    tagged = load_corpus(args.corpus)
    poet = HiddenMarkovPoet()
    poet.train(tagged)

    poem = poet.generate_poem(n_lines=args.lines, rhyme_scheme=args.scheme)
    print()
    for line in poem:
        print(line)

if __name__ == "__main__":
    main() 