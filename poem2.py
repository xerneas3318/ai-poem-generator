import random

# Track used words to avoid repetition
used_words = set()

# Load words and tags
def load_words(filename):
    words = []
    with open(filename) as f:
        for line in f:
            parts = line.strip().split(",")
            if len(parts) >= 7:  # Updated to expect 7 parts
                word, pos, rhyme, category, main_category, anim, pos_anim = parts
                words.append({
                    'word': word,
                    'pos': pos,
                    'rhyme': rhyme,
                    'category': category,
                    'main_category': main_category,
                    'anim': anim,
                    'pos_anim': pos_anim  # New tag for animate/inanimate within POS
                })
            elif len(parts) >= 6:  # Handle old format for backward compatibility
                word, pos, rhyme, category, main_category, anim = parts
                words.append({
                    'word': word,
                    'pos': pos,
                    'rhyme': rhyme,
                    'category': category,
                    'main_category': main_category,
                    'anim': anim,
                    'pos_anim': anim  # Use existing anim tag as fallback
                })
    
    print(f"Loaded {len(words)} words from {filename}")
    return words

# Pick categories for the poem
def pick_categories(words):
    categories = list(set(w['main_category'] for w in words))
    return random.sample(categories, 2)

# Filter words by category and part of speech
def filter_words(words, main_categories, pos=None, category=None):
    filtered = [w for w in words if (w['main_category'] in main_categories or w['main_category'] == 'neutral') and (pos is None or w['pos'] == pos) and (category is None or w['category'] == category)]
    return filtered

# Check animate/inanimate compatibility
def check_animacy_compatibility(subject_word, verb_word):
    """Check if a subject and verb are compatible in terms of animacy"""
    if not subject_word or not verb_word:
        return True  # Allow if we can't determine
    
    # Get the animacy tags
    subject_anim = subject_word.get('pos_anim', subject_word.get('anim', 'inanimate'))
    verb_anim = verb_word.get('pos_anim', verb_word.get('anim', 'inanimate'))
    
    # If verb is animate-specific, subject should be animate
    if verb_anim == 'animate' and subject_anim == 'inanimate':
        print(f"  REJECTED: '{subject_word['word']}' ({subject_anim}) cannot '{verb_word['word']}' ({verb_anim})")
        return False
    
    # If verb is inanimate-specific, subject should be inanimate  
    if verb_anim == 'inanimate' and subject_anim == 'animate':
        print(f"  REJECTED: '{subject_word['word']}' ({subject_anim}) cannot '{verb_word['word']}' ({verb_anim})")
        return False
    
    print(f"  ACCEPTED: '{subject_word['word']}' ({subject_anim}) can '{verb_word['word']}' ({verb_anim})")
    return True

# Enhanced transition matrix for POS
tm = {
    'NOUN': ['VERB', 'NOUN', 'ADJECTIVE', 'PREPOSITION'],
    'VERB': ['NOUN', 'ADVERB', 'PREPOSITION'],
    'ADJECTIVE': ['NOUN'],
    'ADVERB': ['VERB', 'ADJECTIVE'],
    'ARTICLE': ['ADJECTIVE', 'NOUN'],
    'PREPOSITION': ['ARTICLE', 'NOUN'],
    'INTERJECTION': ['ARTICLE', 'NOUN'],
    'START': ['INTERJECTION', 'ARTICLE', 'NOUN', 'ADJECTIVE']
}

def get_transition_probability(prev_pos, current_pos):
    """Get the probability of transitioning from prev_pos to current_pos"""
    if prev_pos not in tm:
        return 0.1  # Low probability for unknown transitions
    
    possible_next = tm[prev_pos]
    if current_pos in possible_next:
        return 0.8  # High probability for valid transitions
    else:
        return 0.2  # Lower probability for invalid transitions

def select_word_with_transition(words, main_categories, pos, prev_word=None, template=None, current_index=None, selected_words=None, sentence_animacy=None):
    """Select a word considering the transition from the previous word and sentence animacy"""
    # Use animacy-aware filtering if sentence_animacy is provided
    if sentence_animacy:
        candidates = filter_words_by_animacy(words, main_categories, pos, sentence_animacy)
    else:
        candidates = filter_words(words, main_categories, pos=pos)
    
    # If no candidates in main categories, expand to neutral
    if not candidates:
        if sentence_animacy:
            candidates = filter_words_by_animacy(words, ['neutral'], pos, sentence_animacy)
        else:
            candidates = [w for w in words if w['pos'] == pos and (w['main_category'] == 'neutral' or w['main_category'] in main_categories)]
    
    # If still no candidates, use any word with this POS (but maintain animacy if possible)
    if not candidates:
        if sentence_animacy and pos in ['NOUN', 'VERB']:
            # Try to find any word with matching animacy
            candidates = [w for w in words if w['pos'] == pos and w.get('pos_anim', w.get('anim', 'inanimate')) == sentence_animacy]
        
        if not candidates:
            candidates = [w for w in words if w['pos'] == pos]
    
    if not candidates:
        return ''
    
    # Apply transition probabilities if we have a previous word
    if prev_word and prev_word.get('pos'):
        prev_pos = prev_word['pos']
        weighted_candidates = []
        
        for candidate in candidates:
            prob = get_transition_probability(prev_pos, pos)
            # Add candidate multiple times based on probability
            weight = int(prob * 10)  # Convert probability to weight
            weighted_candidates.extend([candidate] * weight)
        
        if weighted_candidates:
            candidates = weighted_candidates
    
    # Filter out recently used words
    unused_candidates = [w for w in candidates if w['word'] not in used_words]
    if unused_candidates:
        candidates = unused_candidates
    
    if not candidates:
        used_words.clear()
        if sentence_animacy:
            candidates = filter_words_by_animacy(words, main_categories, pos, sentence_animacy)
        else:
            candidates = [w for w in words if w['pos'] == pos]
    
    selected_word = random.choice(candidates)
    used_words.add(selected_word['word'])
    
    # Handle verb conjugation
    if pos == 'VERB' and template and current_index is not None:
        subject_is_plural = False
        for i in range(current_index):
            if template[i] == 'NOUN':
                subject_is_plural = False
                break
        selected_word['word'] = conjugate_verb(selected_word['word'], subject_is_plural)
    
    return selected_word

# Enhanced sentence templates (POS order) - Fixed for proper grammar
templates = [
    # Interjection starters
    ['INTERJECTION', 'ARTICLE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    ['INTERJECTION', 'ARTICLE', 'NOUN', 'VERB'],
    ['INTERJECTION', 'ARTICLE', 'NOUN', 'VERB', 'ADVERB'],
    ['INTERJECTION', 'ARTICLE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    
    # Article starters - Simple and correct
    ['ARTICLE', 'NOUN', 'VERB', 'ADVERB'],
    ['ARTICLE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'ADVERB'],
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    
    # Noun starters - All need articles
    ['ARTICLE', 'NOUN', 'VERB', 'ADVERB'],
    ['ARTICLE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    ['ARTICLE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'ADJECTIVE', 'NOUN'],
    
    # Adjective starters - Need articles
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'ADVERB'],
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'NOUN'],
    
    # Complex structures - All grammatically correct
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'PREPOSITION', 'ARTICLE', 'ADJECTIVE', 'NOUN'],
    ['INTERJECTION', 'ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB'],
    ['ARTICLE', 'NOUN', 'VERB', 'ARTICLE', 'NOUN'],
    ['ARTICLE', 'ADJECTIVE', 'NOUN', 'VERB', 'ARTICLE', 'NOUN'],
    
    # Simple, reliable templates
    ['ARTICLE', 'NOUN', 'VERB'],
    ['ARTICLE', 'NOUN', 'VERB', 'ADVERB'],
    ['INTERJECTION', 'ARTICLE', 'NOUN', 'VERB', 'ADVERB']
]

def generate_sentence(words, main_categories):
    template = random.choice(templates)
    
    # Determine sentence animacy before generating words
    sentence_animacy = determine_sentence_animacy(template)
    print(f"  Sentence animacy: {sentence_animacy}")
    
    sentence = []
    selected_words = []  # Track the actual word objects, not just strings
    
    # First pass: generate all words except articles and prepositions
    prev_word = None
    for i, pos in enumerate(template):
        if pos == 'ARTICLE':
            sentence.append('')  # Placeholder for article
            selected_words.append(None)  # Placeholder for article
        elif pos == 'PREPOSITION':
            # Select appropriate preposition based on the previous verb
            if prev_word and prev_word.get('pos') == 'VERB':
                preposition = select_appropriate_preposition(prev_word['word'])
            else:
                preposition = random.choice(['in', 'on', 'at', 'to', 'from', 'with', 'by', 'through'])
            sentence.append(preposition)
            selected_words.append({'word': preposition, 'pos': 'PREPOSITION'})
        else:
            word_obj = select_word_with_transition(words, main_categories, pos, prev_word=prev_word, template=template, current_index=i, selected_words=selected_words, sentence_animacy=sentence_animacy)
            if isinstance(word_obj, dict):
                sentence.append(word_obj['word'])
                selected_words.append(word_obj)
                prev_word = word_obj  # Update previous word for next iteration
            else:
                sentence.append(word_obj)
                selected_words.append(None)
    
    # Second pass: fill in articles based on the next word
    for i, pos in enumerate(template):
        if pos == 'ARTICLE':
            next_word = ""
            if i + 1 < len(sentence):
                next_word = sentence[i + 1]
            article = select_article_before_word(next_word)
            sentence[i] = article
    
    # Basic grammar check - ensure we don't have consecutive nouns or verbs inappropriately
    result = ' '.join(sentence)
    if result:
        # Capitalize first word and add punctuation
        result = result.capitalize() + '.'
        
        # Simple validation - if sentence is too short or doesn't make sense, try again
        if len(sentence) < 3:
            return generate_sentence(words, main_categories)
            
    return result

def generate_poem(words, n_stanzas=3, sentences_per_stanza=4):
    global used_words
    used_words.clear()  # Reset used words for new poem
    
    main_categories = pick_categories(words)
    print(f"Poem categories: {main_categories}")
    
    # Create a narrative arc across stanzas
    stanza_themes = create_stanza_themes(main_categories, n_stanzas)
    
    poem = []
    for stanza_num in range(n_stanzas):
        print(f"\n--- Generating Stanza {stanza_num + 1} ---")
        print(f"Stanza theme: {stanza_themes[stanza_num]}")
        
        # Generate stanza with thematic focus
        stanza = generate_thematic_stanza(words, main_categories, stanza_themes[stanza_num], sentences_per_stanza)
        poem.extend(stanza)
        
        # Add stanza separation (except after the last stanza)
        if stanza_num < n_stanzas - 1:
            poem.append("")  # Empty line between stanzas
    
    return '\n'.join(poem)

def create_stanza_themes(main_categories, n_stanzas):
    """Create a narrative progression across stanzas"""
    themes = []
    
    if n_stanzas == 3:
        # Classic three-act structure: setup, conflict, resolution
        if 'destruction' in main_categories:
            themes = ['peace', 'chaos', 'renewal']
        elif 'nature' in main_categories:
            themes = ['awakening', 'flourishing', 'tranquility']
        else:
            themes = ['beginning', 'development', 'conclusion']
    else:
        # For other stanza counts, create progressive themes
        theme_options = ['dawn', 'day', 'dusk', 'night', 'storm', 'calm', 'growth', 'decay', 'birth', 'death']
        themes = random.sample(theme_options, n_stanzas)
    
    return themes

def generate_thematic_stanza(words, main_categories, theme, n_sentences):
    """Generate a stanza focused on a specific theme"""
    stanza = []
    
    # Select theme-appropriate words
    theme_words = select_theme_words(words, main_categories, theme)
    
    # Use some theme words repeatedly for cohesion
    repeated_words = random.sample(theme_words, min(2, len(theme_words)))
    
    for i in range(n_sentences):
        # Mix theme words with regular selection
        if i < 2 and repeated_words:  # Use repeated words in first half
            sentence = generate_sentence_with_theme(words, main_categories, theme, repeated_words[i % len(repeated_words)])
        else:
            sentence = generate_sentence(words, main_categories)
        
        stanza.append(sentence)
    
    return stanza

def select_theme_words(words, main_categories, theme):
    """Select words that fit the theme"""
    theme_words = []
    
    # Map themes to word characteristics
    theme_mapping = {
        'peace': ['calm', 'quiet', 'gentle', 'soft', 'tranquil', 'serene'],
        'chaos': ['storm', 'thunder', 'lightning', 'crash', 'shatter', 'destroy'],
        'renewal': ['bloom', 'grow', 'shine', 'glow', 'awaken', 'rise'],
        'awakening': ['dawn', 'morning', 'light', 'wake', 'begin', 'start'],
        'flourishing': ['bloom', 'grow', 'thrive', 'flourish', 'prosper', 'expand'],
        'tranquility': ['calm', 'peaceful', 'quiet', 'still', 'gentle', 'soft'],
        'dawn': ['morning', 'light', 'sunrise', 'awaken', 'begin', 'dawn'],
        'day': ['bright', 'sun', 'warm', 'active', 'alive', 'vibrant'],
        'dusk': ['evening', 'twilight', 'fade', 'dim', 'settle', 'quiet'],
        'night': ['dark', 'moon', 'star', 'sleep', 'dream', 'silent'],
        'storm': ['thunder', 'lightning', 'rain', 'wind', 'crash', 'roar'],
        'calm': ['gentle', 'soft', 'quiet', 'peaceful', 'tranquil', 'serene'],
        'growth': ['grow', 'bloom', 'flourish', 'expand', 'develop', 'thrive'],
        'decay': ['wilt', 'fade', 'wither', 'decay', 'rot', 'die'],
        'birth': ['begin', 'start', 'awaken', 'emerge', 'arise', 'born'],
        'death': ['end', 'fade', 'die', 'perish', 'cease', 'finish']
    }
    
    # Get theme-appropriate words
    theme_keywords = theme_mapping.get(theme, [])
    
    for word in words:
        if (word['main_category'] in main_categories or word['main_category'] == 'neutral'):
            # Check if word matches theme keywords
            word_text = word['word'].lower()
            for keyword in theme_keywords:
                if keyword in word_text or word_text in keyword:
                    theme_words.append(word)
                    break
    
    return theme_words

def generate_sentence_with_theme(words, main_categories, theme, theme_word):
    """Generate a sentence that incorporates a specific theme word"""
    template = random.choice(templates)
    
    # Determine sentence animacy before generating words
    sentence_animacy = determine_sentence_animacy(template)
    print(f"  Sentence animacy: {sentence_animacy}")
    
    sentence = []
    selected_words = []
    
    # First pass: generate all words except articles and prepositions
    prev_word = None
    for i, pos in enumerate(template):
        if pos == 'ARTICLE':
            sentence.append('')
            selected_words.append(None)
        elif pos == 'PREPOSITION':
            # Select appropriate preposition based on the previous verb
            if prev_word and prev_word.get('pos') == 'VERB':
                preposition = select_appropriate_preposition(prev_word['word'])
            else:
                preposition = random.choice(['in', 'on', 'at', 'to', 'from', 'with', 'by', 'through'])
            sentence.append(preposition)
            selected_words.append({'word': preposition, 'pos': 'PREPOSITION'})
        else:
            # Try to use theme word if it matches the POS and animacy
            if theme_word and theme_word['pos'] == pos:
                # Check if theme word matches sentence animacy
                theme_anim = theme_word.get('pos_anim', theme_word.get('anim', 'inanimate'))
                if pos in ['NOUN', 'VERB']:
                    if theme_anim == sentence_animacy or theme_anim == 'both':
                        word_obj = theme_word
                        sentence.append(word_obj['word'])
                        selected_words.append(word_obj)
                        prev_word = word_obj
                        theme_word = None  # Use it only once
                    else:
                        # Theme word doesn't match animacy, use regular selection
                        word_obj = select_word_with_transition(words, main_categories, pos, prev_word=prev_word, template=template, current_index=i, selected_words=selected_words, sentence_animacy=sentence_animacy)
                        if isinstance(word_obj, dict):
                            sentence.append(word_obj['word'])
                            selected_words.append(word_obj)
                            prev_word = word_obj
                        else:
                            sentence.append(word_obj)
                            selected_words.append(None)
                else:
                    # For non-noun/verb POS, use theme word
                    word_obj = theme_word
                    sentence.append(word_obj['word'])
                    selected_words.append(word_obj)
                    prev_word = word_obj
                    theme_word = None  # Use it only once
            else:
                word_obj = select_word_with_transition(words, main_categories, pos, prev_word=prev_word, template=template, current_index=i, selected_words=selected_words, sentence_animacy=sentence_animacy)
                if isinstance(word_obj, dict):
                    sentence.append(word_obj['word'])
                    selected_words.append(word_obj)
                    prev_word = word_obj
                else:
                    sentence.append(word_obj)
                    selected_words.append(None)
    
    # Second pass: fill in articles
    for i, pos in enumerate(template):
        if pos == 'ARTICLE':
            next_word = ""
            if i + 1 < len(sentence):
                next_word = sentence[i + 1]
            article = select_article_before_word(next_word)
            sentence[i] = article
    
    result = ' '.join(sentence)
    if result:
        result = result.capitalize() + '.'
        if len(sentence) < 3:
            return generate_sentence_with_theme(words, main_categories, theme, theme_word)
    
    return result

# Simple pluralization rules
def pluralize(word):
    if word.endswith('y') and not word.endswith(('ay', 'ey', 'iy', 'oy', 'uy')):
        return word[:-1] + 'ies'
    elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
        return word + 'es'
    else:
        return word + 's'

# Simple verb conjugation for present tense
def conjugate_verb(word, subject_is_plural=False):
    print(f"  Conjugating '{word}' (plural: {subject_is_plural})")
    if subject_is_plural:
        result = word  # Base form for plural subjects
        print(f"  Result: '{result}' (plural form)")
        return result
    else:
        # Simple rules for third person singular
        # First, check if the word already ends with 's' to avoid double suffixes
        if word.endswith('s'):
            result = word  # Already conjugated
            print(f"  Result: '{result}' (already ends with 's')")
            return result
        
        if word.endswith('y') and not word.endswith(('ay', 'ey', 'iy', 'oy', 'uy')):
            result = word[:-1] + 'ies'
            print(f"  Result: '{result}' (y -> ies)")
            return result
        elif word.endswith(('s', 'sh', 'ch', 'x', 'z')):
            result = word + 'es'
            print(f"  Result: '{result}' (add 'es')")
            return result
        else:
            result = word + 's'
            print(f"  Result: '{result}' (add 's')")
            return result

# Check if subject is plural
def is_plural_subject(template, current_index):
    # Look for articles that indicate plural
    for i in range(current_index):
        if template[i] == 'ARTICLE':
            # Check if the article is plural
            return True  # We'll handle this in word selection
    return False

# Proper article selection based on the next word
def select_article_before_word(next_word):
    if not next_word:
        return 'the'  # Default fallback
    
    # Words that start with vowel sounds (including silent h words)
    vowel_sound_words = {
        'a', 'e', 'i', 'o', 'u',  # vowels
        'hour', 'honor', 'honest', 'heir', 'herb'  # silent h words
    }
    
    # Check if the word starts with a vowel sound
    if next_word.lower() in vowel_sound_words or next_word.lower().startswith(('a', 'e', 'i', 'o', 'u')):
        return 'an'
    else:
        return 'a'

# Better preposition selection based on verb context
def select_appropriate_preposition(verb_word, context=None):
    """Select an appropriate preposition based on the verb and context"""
    if not verb_word:
        return random.choice(['in', 'on', 'at', 'to', 'from', 'with', 'by', 'through'])
    
    verb = verb_word.lower()
    
    # Verb-specific preposition mappings
    verb_prepositions = {
        'jump': ['over', 'across', 'through', 'into', 'onto'],
        'run': ['through', 'across', 'around', 'to', 'from'],
        'walk': ['through', 'across', 'around', 'to', 'from'],
        'fly': ['over', 'through', 'across', 'to', 'from'],
        'swim': ['through', 'across', 'in', 'to', 'from'],
        'climb': ['up', 'over', 'through', 'onto'],
        'fall': ['off', 'from', 'through', 'into'],
        'flow': ['through', 'across', 'into', 'over'],
        'drift': ['through', 'across', 'over', 'in'],
        'float': ['through', 'across', 'over', 'in'],
        'burn': ['through', 'across', 'over', 'in'],
        'crash': ['into', 'through', 'against', 'onto'],
        'shatter': ['into', 'against', 'through', 'onto'],
        'destroy': ['through', 'across', 'over', 'in'],
        'grow': ['in', 'through', 'across', 'over'],
        'bloom': ['in', 'through', 'across', 'over'],
        'shine': ['through', 'across', 'over', 'in'],
        'glow': ['through', 'across', 'over', 'in'],
        'sparkle': ['through', 'across', 'over', 'in'],
        'twinkle': ['through', 'across', 'over', 'in'],
        'roar': ['through', 'across', 'over', 'in'],
        'rumble': ['through', 'across', 'over', 'in'],
        'howl': ['through', 'across', 'over', 'in'],
        'scream': ['through', 'across', 'over', 'in'],
        'whisper': ['through', 'across', 'over', 'in'],
        'speak': ['to', 'with', 'through', 'across'],
        'listen': ['to', 'for', 'through', 'across'],
        'watch': ['over', 'through', 'across', 'in'],
        'see': ['through', 'across', 'over', 'in'],
        'hear': ['through', 'across', 'over', 'in'],
        'feel': ['through', 'across', 'over', 'in'],
        'touch': ['through', 'across', 'over', 'in'],
        'love': ['through', 'across', 'over', 'in'],
        'hate': ['through', 'across', 'over', 'in'],
        'fear': ['through', 'across', 'over', 'in'],
        'hope': ['for', 'through', 'across', 'over'],
        'dream': ['of', 'about', 'through', 'across'],
        'think': ['about', 'of', 'through', 'across'],
        'know': ['about', 'of', 'through', 'across'],
        'learn': ['about', 'from', 'through', 'across'],
        'teach': ['to', 'about', 'through', 'across'],
        'grow': ['in', 'through', 'across', 'over'],
        'bloom': ['in', 'through', 'across', 'over'],
        'wilt': ['in', 'through', 'across', 'over'],
        'wither': ['in', 'through', 'across', 'over'],
        'fade': ['in', 'through', 'across', 'over'],
        'shine': ['through', 'across', 'over', 'in'],
        'glow': ['through', 'across', 'over', 'in'],
        'sparkle': ['through', 'across', 'over', 'in'],
        'twinkle': ['through', 'across', 'over', 'in'],
        'blaze': ['through', 'across', 'over', 'in'],
        'roar': ['through', 'across', 'over', 'in'],
        'rumble': ['through', 'across', 'over', 'in'],
        'howl': ['through', 'across', 'over', 'in'],
        'scream': ['through', 'across', 'over', 'in'],
        'wail': ['through', 'across', 'over', 'in'],
        'moan': ['through', 'across', 'over', 'in'],
        'groan': ['through', 'across', 'over', 'in']
    }
    
    # Check if we have specific prepositions for this verb
    if verb in verb_prepositions:
        return random.choice(verb_prepositions[verb])
    
    # Default prepositions for general use
    default_prepositions = ['in', 'on', 'at', 'to', 'from', 'with', 'by', 'through', 'across', 'over', 'around', 'into', 'onto', 'off', 'up', 'down']
    
    return random.choice(default_prepositions)

# Determine sentence animacy before generation
def determine_sentence_animacy(template):
    """Determine if a sentence should be animate or inanimate based on template structure"""
    # Look for patterns that suggest animate subjects
    animate_indicators = ['INTERJECTION', 'VERB']  # Interjections often suggest animate subjects
    inanimate_indicators = ['ARTICLE', 'ADJECTIVE']  # Articles/adjectives often suggest objects
    
    # Count indicators
    animate_count = sum(1 for pos in template if pos in animate_indicators)
    inanimate_count = sum(1 for pos in template if pos in inanimate_indicators)
    
    # If template starts with interjection, likely animate
    if template[0] == 'INTERJECTION':
        return 'animate'
    
    # If template has more animate indicators, choose animate
    if animate_count > inanimate_count:
        return 'animate'
    elif inanimate_count > animate_count:
        return 'inanimate'
    else:
        # Random choice for balanced templates
        return random.choice(['animate', 'inanimate'])

def filter_words_by_animacy(words, main_categories, pos, sentence_animacy, category=None):
    """Filter words by category, POS, and sentence animacy"""
    filtered = []
    
    for word in words:
        # Check main category and POS
        if (word['main_category'] in main_categories or word['main_category'] == 'neutral') and word['pos'] == pos:
            if category is None or word['category'] == category:
                # Check animacy compatibility
                word_anim = word.get('pos_anim', word.get('anim', 'inanimate'))
                
                # For subjects (nouns), they should match sentence animacy
                if pos == 'NOUN' and word_anim == sentence_animacy:
                    filtered.append(word)
                # For verbs, they should be compatible with sentence animacy
                elif pos == 'VERB':
                    if sentence_animacy == 'animate' and word_anim in ['animate', 'both']:
                        filtered.append(word)
                    elif sentence_animacy == 'inanimate' and word_anim in ['inanimate', 'both']:
                        filtered.append(word)
                # For other POS, include them (they don't affect animacy)
                elif pos not in ['NOUN', 'VERB']:
                    filtered.append(word)
    
    return filtered

if __name__ == "__main__":
    words = load_words("words2.txt")
    poem = generate_poem(words)
    print(poem)
