# AI Poem Generator

An intelligent poem generator that uses Hidden Markov Models (HMM) to create coherent, thematic poetry with proper grammar and animacy constraints.

## Features

- **Hidden Markov Model**: Uses transition matrices to ensure natural word flow
- **Animacy Awareness**: Prevents illogical combinations like "rain sleeps" by determining sentence animacy before generation
- **Thematic Generation**: Creates poems with narrative arcs across multiple stanzas
- **Grammar Correction**: Ensures proper article usage and preposition selection
- **Part-of-Speech Tagging**: Comprehensive word database with POS, rhyming groups, and categories
- **Verb Conjugation**: Automatically conjugates verbs based on subject plurality

## How It Works

1. **Category Selection**: Randomly picks 2 main categories (e.g., nature, destruction)
2. **Stanza Theming**: Creates narrative progression across stanzas (peace → chaos → renewal)
3. **Animacy Determination**: Analyzes template structure to decide if sentence should be animate or inanimate
4. **Word Selection**: Uses transition probabilities and animacy constraints to select appropriate words
5. **Grammar Processing**: Applies articles, prepositions, and verb conjugation

## Files

- `poem2.py`: Main poem generator with HMM implementation
- `words2.txt`: Comprehensive word database with 7 tags per word:
  - Word
  - Part of Speech
  - Rhyming Group
  - Category
  - Main Category
  - Animate/Inanimate
  - POS-specific Animate/Inanimate

## Usage

```bash
python poem2.py
```

## Example Output

```
Poem categories: ['nature', 'destruction']

--- Generating Stanza 1 ---
Stanza theme: peace
  Sentence animacy: animate
  Sentence animacy: inanimate
  Sentence animacy: inanimate
  Sentence animacy: animate

Hooray a fox moans speedily.
A dark storm drifts quietly.
A stream shines by a smoldering hurricane.
Farewell a tiger moans fast.

An ash glows in a sun.
Adieu a rabbit speaks rapidly.
A fish laughs noisily.
A lake glows off a watching flame.

An earthquake shines a fire.
A glowing rain smashes a blizzard.
Goodbye a bear knows up a bird.
A mountain floats to a fearing volcano.
```

## Technical Details

- **Transition Matrix**: Influences word selection based on previous word's POS
- **Animacy Filtering**: Ensures subject-verb compatibility
- **Template System**: 20+ grammatically correct sentence templates
- **Preposition Mapping**: Verb-specific preposition selection for natural combinations

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library) 