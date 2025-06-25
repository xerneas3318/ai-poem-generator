import random
import pronouncing
import warnings
from collections import defaultdict

# Suppress the pkg_resources deprecation warning from pronouncing
warnings.filterwarnings("ignore", category=UserWarning, module='pronouncing')

def load_word_bank(filename="words.txt"):
    word_bank = {}
    possible_paths = [
        filename,
        f"Cornell/{filename}",
        f"./{filename}",
        f"../{filename}"
    ]
    
    for filepath in possible_paths:
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split(':')
                        if len(parts) == 5:
                            # New format: word:pos:animacy:category:rhyme_group
                            word, pos, animacy, category, rhyme_group = parts
                            word_bank[word] = {
                                "pos": pos, 
                                "animacy": animacy, 
                                "category": category, 
                                "rhyme_group": rhyme_group
                            }
                        elif len(parts) == 4:
                            # Old format: word:pos:category:rhyme_group
                            word, pos, category, rhyme_group = parts
                            word_bank[word] = {
                                "pos": pos, 
                                "animacy": "unknown", 
                                "category": category, 
                                "rhyme_group": rhyme_group
                            }
                        elif len(parts) == 3:
                            # Fallback format: word:pos:category
                            word, pos, category = parts
                            word_bank[word] = {
                                "pos": pos, 
                                "animacy": "unknown", 
                                "category": category, 
                                "rhyme_group": word
                            }
                print(f"Loaded {len(word_bank)} words from {filepath}")
                return word_bank
        except FileNotFoundError:
            continue
    
    print(f"Error: {filename} not found in any of the expected locations.")
    print("Expected locations:")
    for path in possible_paths:
        print(f"  - {path}")
    print("Please ensure the words.txt file exists in one of these locations.")
    exit(1)

# Load the word bank
word_bank = load_word_bank()

# Transition matrix with probabilities
transition_matrix = {
    "adjective:weather": {
        "noun:weather": 0.3,
        "noun:nature": 0.3,
        "noun:floating": 0.2,
        "noun:emotion": 0.1,
        "noun:time": 0.1
    },
    "adjective:floating": {
        "noun:floating": 0.3,
        "noun:weather": 0.3,
        "noun:nature": 0.2,
        "noun:emotion": 0.1,
        "noun:time": 0.1
    },
    "adjective:emotion": {
        "noun:emotion": 0.4,
        "noun:floating": 0.3,
        "noun:weather": 0.2,
        "noun:time": 0.1
    },
    "adjective:nature": {
        "noun:nature": 0.4,
        "noun:weather": 0.3,
        "noun:floating": 0.2,
        "noun:emotion": 0.1
    },
    "noun:weather": {
        "verb:floating": 0.3,
        "verb:emotion": 0.3,
        "verb:action": 0.2,
        "verb:effort": 0.1,
        "adverb:floating": 0.1
    },
    "noun:floating": {
        "verb:floating": 0.4,
        "verb:emotion": 0.3,
        "verb:action": 0.2,
        "adverb:floating": 0.1
    },
    "noun:emotion": {
        "verb:emotion": 0.5,
        "verb:floating": 0.3,
        "verb:effort": 0.2
    },
    "noun:nature": {
        "verb:floating": 0.3,
        "verb:action": 0.3,
        "verb:emotion": 0.2,
        "verb:effort": 0.1,
        "adverb:floating": 0.1
    },
    "noun:time": {
        "verb:floating": 0.3,
        "verb:emotion": 0.3,
        "verb:action": 0.2,
        "verb:effort": 0.1,
        "adverb:time": 0.1
    },
    "verb:floating": {
        "adverb:floating": 0.3,
        "preposition:spatial": 0.3,
        "adverb:time": 0.2,
        "conjunction:connecting": 0.1,
        "noun:weather": 0.1
    },
    "verb:emotion": {
        "adverb:floating": 0.3,
        "adverb:time": 0.3,
        "preposition:spatial": 0.2,
        "conjunction:connecting": 0.1,
        "noun:emotion": 0.1
    },
    "verb:action": {
        "adverb:floating": 0.3,
        "preposition:spatial": 0.3,
        "adverb:time": 0.2,
        "conjunction:connecting": 0.1,
        "noun:nature": 0.1
    },
    "verb:effort": {
        "adverb:time": 0.3,
        "adverb:floating": 0.3,
        "preposition:spatial": 0.2,
        "conjunction:connecting": 0.1,
        "noun:emotion": 0.1
    },
    "adverb:floating": {
        "verb:floating": 0.5,
        "verb:emotion": 0.2,
        "verb:action": 0.2,
        "verb:effort": 0.1
    },
    "adverb:time": {
        "verb:floating": 0.3,
        "verb:emotion": 0.3,
        "verb:action": 0.2,
        "verb:effort": 0.2
    },
    "conjunction:connecting": {
        "adjective:weather": 0.2,
        "adjective:floating": 0.2,
        "adjective:emotion": 0.2,
        "adjective:nature": 0.2,
        "noun:weather": 0.1,
        "noun:floating": 0.1
    },
    "preposition:spatial": {
        "noun:weather": 0.3,
        "noun:nature": 0.3,
        "noun:floating": 0.2,
        "noun:emotion": 0.1,
        "noun:time": 0.1
    }
}

def find_rhyming_words(word, candidates, forbidden_words=None):
    """Find rhyming words from candidates using rhyme groups, excluding forbidden words."""
    if forbidden_words is None:
        forbidden_words = set()
    
    target_rhyme_group = None
    for w, tags in word_bank.items():
        if w == word:
            target_rhyme_group = tags.get("rhyme_group", word)
            break
    
    if target_rhyme_group is None:
        return []
    
    rhyming_words = []
    for candidate in candidates:
        if candidate in word_bank:
            candidate_rhyme_group = word_bank[candidate].get("rhyme_group", candidate)
            if (candidate_rhyme_group == target_rhyme_group and 
                candidate not in forbidden_words and 
                candidate != word):
                rhyming_words.append(candidate)
    
    return rhyming_words

TOPICS = {
    "water": ["weather", "floating", "nature"],
    "love": ["emotion", "nature"],
    "sky": ["weather", "floating"],
    "forest": ["nature", "weather"],
    "time": ["time", "emotion"],
    "flight": ["floating", "weather", "nature"],
    "night": ["time", "weather"],
    "joy": ["emotion", "nature"],
    "farewell": ["emotion", "time"],
}

def pick_topic():
    return random.choice(list(TOPICS.keys()))

def choose_article(word):
    """Return 'an' if word starts with a vowel sound, else 'a'."""
    if not word:
        return 'a'
    
    vowel_sound_words = {
        'hour', 'honor', 'honest', 'heir', 'herb', 'herbal', 'historic', 'historical',
        'hysterical', 'hysterically', 'hysterics', 'hysteric'
    }
    
    consonant_u_words = {
        'universal', 'university', 'uniform', 'union', 'unique', 'united', 'unity',
        'universe'
    }
    
    if word.lower() in vowel_sound_words:
        return 'an'
    
    if word.lower() in consonant_u_words:
        return 'a'
    
    if word[0].lower() in 'aeiou':
        return 'an'
    
    return 'a'

def pluralize(word):
    """Very basic pluralization: add 's' or 'es'."""
    if word.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return word + 'es'
    elif word.endswith('y') and word[-2] not in 'aeiou':
        return word[:-1] + 'ies'
    else:
        return word + 's'

def conjugate_verb_s(word):
    """Very basic third-person singular conjugation."""
    if word.endswith(('s', 'x', 'z', 'ch', 'sh')):
        return word + 'es'
    elif word.endswith('y') and word[-2] not in 'aeiou':
        return word[:-1] + 'ies'
    else:
        return word + 's'

SENTENCE_TEMPLATES = {
    "interjection_noun_verb": [
        "{interjection}, {article} {adjective} {noun} {verb} {adverb}",
        "{interjection}, {article} {adjective} {noun} {verb} {adverb}",
        "{interjection}, {article} {noun} {verb} {preposition} {article} {noun}",
        "{interjection}, {article} {noun} {verb} {preposition} {article} {noun}",
        "{interjection}, {article} {noun_plural} {verb} {adverb}",
        "{interjection}, {article} {noun} {verb_s} {adverb}"
    ],
    "adjective_noun_verb": [
        "{article} {adjective} {noun} {verb} {adverb}",
        "{article} {adjective} {noun} {verb} {adverb}",
        "{article} {adjective} {noun} {verb} {preposition} {article} {noun}",
        "{article} {noun} {verb} {adverb} and {verb}",
        "{article} {noun_plural} {verb} {adverb}",
        "{article} {noun} {verb_s} {adverb}",
        "In {article} {noun} {article} {adjective} {noun} {verb}",
        "Through {article} {noun} {article} {noun} {verb} {adverb}"
    ],
    "noun_verb_adverb": [
        "{article} {noun} {verb} {adverb} {preposition} {article} {noun}",
        "{article} {noun} {verb} {adverb}",
        "{article} {noun} {verb} {adverb}",
        "{article} {noun} {verb} and {verb} {adverb}",
        "{article} {noun_plural} {verb} {adverb}",
        "{article} {noun} {verb_s} {adverb}",
        "When {article} {noun} {verb} {adverb}",
        "Where {article} {noun} {verb} {adverb}"
    ],
    "verb_noun_adjective": [
        "{verb} {article} {adjective} {noun}",
        "{verb} {article} {adjective} {noun}",
        "{verb} {adverb} {preposition} {article} {noun}",
        "{verb} and {verb} {preposition} {article} {noun}",
        "{verb_s} {article} {adjective} {noun}",
        "{verb} {article} {adjective} {noun_plural}",
        "Let {article} {noun} {verb} {adverb}",
        "May {article} {noun} {verb} {adverb}"
    ]
}

def get_appropriate_verbs_for_noun(noun):
    """Get verbs that are appropriate for a given noun based on its animacy."""
    if noun not in word_bank:
        return []
    
    noun_tags = word_bank[noun]
    noun_animacy = noun_tags.get("animacy", "unknown")
    
    appropriate_verbs = []
    for word, tags in word_bank.items():
        if tags["pos"] == "verb":
            verb_type = tags.get("category", "unknown")
            
            # Animate nouns can perform human actions and natural phenomena
            if noun_animacy == "animate":
                if verb_type in ["human", "natural"]:
                    appropriate_verbs.append(word)
            
            # Inanimate nouns can only perform natural phenomena
            elif noun_animacy == "inanimate":
                if verb_type == "natural":
                    appropriate_verbs.append(word)
            
            # Abstract concepts can perform some natural phenomena (metaphorically)
            elif noun_animacy == "abstract":
                if verb_type == "natural":
                    appropriate_verbs.append(word)
            
            # Time concepts can perform some natural phenomena (metaphorically)
            elif noun_animacy == "time":
                if verb_type == "natural":
                    appropriate_verbs.append(word)
            
            # Unknown animacy - allow all verbs (fallback)
            else:
                appropriate_verbs.append(word)
    
    return appropriate_verbs

def get_template_words(template_type, topic=None, previous_word=None):
    """Get words for a specific template type, biased toward topic if provided."""
    words = {}
    function_pos = ["interjection", "preposition", "conjunction", "article"]
    
    # Always include all function words
    for word, tags in word_bank.items():
        if tags["pos"] in function_pos:
            pos = tags["pos"]
            if pos not in words:
                words[pos] = []
            words[pos].append(word)
    
    # Pick two related concepts for this sentence
    if topic:
        topic_cats = TOPICS.get(topic, [])
        # Get all available categories
        all_categories = set()
        for word, tags in word_bank.items():
            if tags["pos"] not in function_pos:
                all_categories.add(tags["category"])
        
        # Start with topic categories, then add related ones
        available_categories = list(topic_cats)
        for cat in all_categories:
            if cat not in available_categories:
                available_categories.append(cat)
        
        # Pick two related concepts
        if len(available_categories) >= 2:
            # Prefer topic-related categories
            if len(topic_cats) >= 2:
                selected_categories = random.sample(topic_cats, min(2, len(topic_cats)))
            elif len(topic_cats) == 1:
                # Pick one topic category and one related category
                other_categories = [cat for cat in available_categories if cat not in topic_cats]
                if other_categories:
                    selected_categories = topic_cats + [random.choice(other_categories)]
                else:
                    selected_categories = topic_cats
            else:
                # No topic categories, pick any two
                selected_categories = random.sample(available_categories, min(2, len(available_categories)))
        else:
            selected_categories = available_categories
        
        # Filter words by selected categories
        for word, tags in word_bank.items():
            if tags["pos"] not in function_pos and tags["category"] in selected_categories:
                pos = tags["pos"]
                if pos not in words:
                    words[pos] = []
                words[pos].append(word)
    else:
        # No topic specified, pick two random categories
        all_categories = set()
        for word, tags in word_bank.items():
            if tags["pos"] not in function_pos:
                all_categories.add(tags["category"])
        
        if len(all_categories) >= 2:
            selected_categories = random.sample(list(all_categories), 2)
        else:
            selected_categories = list(all_categories)
        
        for word, tags in word_bank.items():
            if tags["pos"] not in function_pos and tags["category"] in selected_categories:
                pos = tags["pos"]
                if pos not in words:
                    words[pos] = []
                words[pos].append(word)
    
    # If we still don't have enough words, add some from all categories
    if not words or all(len(word_list) == 0 for word_list in words.values() if word_list and not isinstance(word_list[0], tuple)):
        for word, tags in word_bank.items():
            if tags["pos"] not in function_pos:
                pos = tags["pos"]
                if pos not in words:
                    words[pos] = []
                words[pos].append(word)
    
    return words

def is_plural(word):
    """Better plural detection: check if word ends with 's' but not 'ss' or common singular words ending in 's'."""
    if not word:
        return False
    singular_s_words = {'this', 'his', 'its', 'thus', 'plus', 'minus', 'status', 'campus', 'virus', 'chorus', 'bonus', 'census', 'focus', 'genius', 'radius', 'sinus', 'terminus', 'torus', 'viscus', 'apparatus', 'corpus', 'omnibus', 'prospectus', 'rebus', 'surplus', 'torus', 'viscus', 'abacus', 'crocus', 'fungus', 'hippopotamus', 'octopus', 'platypus', 'rhinoceros', 'stadium', 'syllabus', 'terminus', 'uterus', 'villus', 'alumnus', 'bacillus', 'bronchus', 'locus', 'nucleus', 'stimulus', 'syllabus', 'thesaurus', 'umbilicus', 'uterus', 'villus', 'alumnus', 'bacillus', 'bronchus', 'locus', 'nucleus', 'stimulus', 'syllabus', 'thesaurus', 'umbilicus'}
    
    if word.lower() in singular_s_words:
        return False
    
    return word.endswith('s') and not word.endswith('ss')
    
def conjugate_verb_for_noun(verb, noun):
    """Conjugate verb based on whether the noun is singular or plural."""
    if is_plural(noun):
        return verb
    else:
        return conjugate_verb_s(verb)

def fill_template(template, words, topic=None, force_last_word=None):
    """Fill a template with appropriate words, handling 'a/an', 'the', pluralization, and verb conjugation."""
    try:
        filled_parts = []
        i = 0
        parts = template.split()
        last_noun = None
        previous_word = None
        
        while i < len(parts):
            part = parts[i]
            
            if part == '{article}':
                next_word = None
                if i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if next_part.startswith('{') and '}' in next_part:
                        end_brace = next_part.index('}')
                        placeholder = next_part[1:end_brace]
                        pos_mapping = {
                            "interjection": "interjection",
                            "adjective": "adjective", 
                            "noun": "noun",
                            "verb": "verb",
                            "adverb": "adverb",
                            "preposition": "preposition",
                            "noun_plural": "noun",
                            "verb_s": "verb"
                        }
                        pos = pos_mapping.get(placeholder, placeholder)
                        
                        template_words = get_template_words("any", topic, previous_word)
                        
                        if pos in template_words and template_words[pos]:
                            next_word = random.choice(template_words[pos])
                        else:
                            fallback_words = [w for w, t in word_bank.items() if t["pos"] == pos]
                            next_word = random.choice(fallback_words) if fallback_words else "word"
                
                if next_word:
                    article = choose_article(next_word)
                else:
                    article = "the"
                
                filled_parts.append(article)
                i += 1
                continue
            
            if part.startswith('{') and '}' in part:
                end_brace = part.index('}')
                placeholder = part[1:end_brace]
                trailing = part[end_brace+1:]
                pos_mapping = {
                    "interjection": "interjection",
                    "adjective": "adjective", 
                    "noun": "noun",
                    "verb": "verb",
                    "adverb": "adverb",
                    "preposition": "preposition",
                    "noun_plural": "noun",
                    "verb_s": "verb"
                }
                pos = pos_mapping.get(placeholder, placeholder)
                
                if force_last_word and i == len(parts) - 1:
                    word = force_last_word
                else:
                    template_words = get_template_words("any", topic, previous_word)
                    
                    # If this is a verb and we have a subject noun, use appropriate verbs
                    if pos == "verb" and last_noun is not None:
                        appropriate_verbs = get_appropriate_verbs_for_noun(last_noun)
                        if appropriate_verbs:
                            # Filter to topic-appropriate verbs if possible
                            if topic and template_words.get("verb"):
                                topic_verbs = set(template_words["verb"])
                                appropriate_topic_verbs = [v for v in appropriate_verbs if v in topic_verbs]
                                if appropriate_topic_verbs:
                                    word = random.choice(appropriate_topic_verbs)
                                else:
                                    word = random.choice(appropriate_verbs)
                            else:
                                word = random.choice(appropriate_verbs)
                        else:
                            # Fallback to any verb if no appropriate ones found
                            if pos in template_words and template_words[pos]:
                                word = random.choice(template_words[pos])
                            else:
                                fallback_words = [w for w, t in word_bank.items() if t["pos"] == pos]
                                word = random.choice(fallback_words) if fallback_words else "word"
                    else:
                        # Normal word selection for non-verbs or when no subject noun
                        if pos in template_words and template_words[pos]:
                            word = random.choice(template_words[pos])
                        else:
                            fallback_words = [w for w, t in word_bank.items() if t["pos"] == pos]
                            word = random.choice(fallback_words) if fallback_words else "word"
                
                if placeholder == "noun_plural":
                    word = pluralize(word)
                elif pos == "noun":
                    pass
                
                if placeholder == "verb_s":
                    word = conjugate_verb_s(word)
                elif pos == "verb" and last_noun is not None:
                    word = conjugate_verb_for_noun(word, last_noun)
                
                if pos == "noun":
                    last_noun = word
                
                filled_parts.append(word + trailing)
                previous_word = word
            
            elif part == '{verb}':
                pos = 'verb'
                if force_last_word and i == len(parts) - 1:
                    word = force_last_word
                else:
                    template_words = get_template_words("any", topic, previous_word)
                    
                    # If we have a subject noun, use appropriate verbs
                    if last_noun is not None:
                        appropriate_verbs = get_appropriate_verbs_for_noun(last_noun)
                        if appropriate_verbs:
                            # Filter to topic-appropriate verbs if possible
                            if topic and template_words.get("verb"):
                                topic_verbs = set(template_words["verb"])
                                appropriate_topic_verbs = [v for v in appropriate_verbs if v in topic_verbs]
                                if appropriate_topic_verbs:
                                    word = random.choice(appropriate_topic_verbs)
                                else:
                                    word = random.choice(appropriate_verbs)
                            else:
                                word = random.choice(appropriate_verbs)
                        else:
                            # Fallback to any verb if no appropriate ones found
                            if pos in template_words and template_words[pos]:
                                word = random.choice(template_words[pos])
                            else:
                                fallback_words = [w for w, t in word_bank.items() if t["pos"] == pos]
                                word = random.choice(fallback_words) if fallback_words else "word"
                    else:
                        # Normal word selection when no subject noun
                        if pos in template_words and template_words[pos]:
                            word = random.choice(template_words[pos])
                        else:
                            fallback_words = [w for w, t in word_bank.items() if t["pos"] == pos]
                            word = random.choice(fallback_words) if fallback_words else "word"
                
                if last_noun is not None:
                    word = conjugate_verb_for_noun(word, last_noun)
                
                filled_parts.append(word)
                previous_word = word
            else:
                filled_parts.append(part)
            
            i += 1
        
        result = " ".join(filled_parts)
        return result
    except Exception as e:
        return f"Error filling template: {e}"

def generate_template_line(template_type, topic=None, enforce_rhyme_with=None, forbidden_words=None):
    """Generate a line using templates. If enforcing a rhyme, pick the rhyme word first and build the sentence around it."""
    templates = SENTENCE_TEMPLATES.get(template_type, SENTENCE_TEMPLATES["adjective_noun_verb"])
    
    if not enforce_rhyme_with:
        template = random.choice(templates)
        words = get_template_words(template_type, topic)
        return fill_template(template, words, topic)
    
    rhyming_templates = []
    rhymable_types = ["noun", "adjective", "verb"]
    for t in templates:
        parts = t.split()
        if parts and parts[-1].startswith('{') and parts[-1].endswith('}'):
            placeholder = parts[-1][1:-1]
            if placeholder in rhymable_types:
                rhyming_templates.append((t, placeholder))
    
    if not rhyming_templates:
        rhyming_templates = [(random.choice(templates), None)]
    
    max_attempts = 20
    attempt = 0
    best_line = None
    
    while attempt < max_attempts:
        template, placeholder = random.choice(rhyming_templates)
        
        if placeholder:
            pos = placeholder
            candidates = [w for w, t in word_bank.items() if t["pos"] == pos]
            rhyming_candidates = find_rhyming_words(enforce_rhyme_with, candidates, forbidden_words)
            
            if rhyming_candidates:
                chosen_rhyme = random.choice(rhyming_candidates)
                words = get_template_words(template_type, topic)
                line = fill_template(template, words, topic, force_last_word=chosen_rhyme)
                
                if line and line.split()[-1] == chosen_rhyme:
                    print(f"[RHYME SUCCESS] Attempt {attempt+1}: '{enforce_rhyme_with}' rhymed with '{chosen_rhyme}' (built-in)")
                    return line
        
        if attempt >= 10:
            all_words = list(word_bank.keys())
            rhyming_candidates = find_rhyming_words(enforce_rhyme_with, all_words, forbidden_words)
            
            if rhyming_candidates:
                chosen_rhyme = random.choice(rhyming_candidates)
                word_pos = word_bank[chosen_rhyme]["pos"]
                for t in templates:
                    parts = t.split()
                    if parts and parts[-1].startswith('{') and parts[-1].endswith('}'):
                        placeholder = parts[-1][1:-1]
                        if placeholder == word_pos or placeholder in ["noun", "adjective", "verb"]:
                            words = get_template_words(template_type, topic)
                            line = fill_template(t, words, topic, force_last_word=chosen_rhyme)
                            if line and line.split()[-1] == chosen_rhyme:
                                print(f"[RHYME SUCCESS] Attempt {attempt+1}: '{enforce_rhyme_with}' rhymed with '{chosen_rhyme}' (any type)")
                                return line
        
        words = get_template_words(template_type, topic)
        line = fill_template(template, words, topic)

        if best_line is None:
            best_line = line
        
        attempt += 1
    
    print(f"[RHYME FAIL] Could not rhyme with '{enforce_rhyme_with}' after {max_attempts} attempts. Using best effort.")
    return best_line

def generate_rhyme_friendly_line(template_type, topic=None):
    """Generate a line that ends with a word that has rhyming partners."""
    templates = SENTENCE_TEMPLATES.get(template_type, SENTENCE_TEMPLATES["adjective_noun_verb"])
    
    rhyming_templates = []
    rhymable_types = ["noun", "adjective", "verb"]
    for t in templates:
        parts = t.split()
        if parts and parts[-1].startswith('{') and parts[-1].endswith('}'):
            placeholder = parts[-1][1:-1]
            if placeholder in rhymable_types:
                rhyming_templates.append((t, placeholder))
    
    if not rhyming_templates:
        rhyming_templates = [(random.choice(templates), None)]
    
    max_attempts = 10
    for attempt in range(max_attempts):
        template, placeholder = random.choice(rhyming_templates)
        
        if placeholder:
            pos = placeholder
            candidates = [w for w, t in word_bank.items() if t["pos"] == pos]
            
            rhyme_friendly_words = []
            for word in candidates:
                rhyming_partners = find_rhyming_words(word, list(word_bank.keys()))
                if len(rhyming_partners) >= 2:
                    rhyme_friendly_words.append(word)
            
            if rhyme_friendly_words:
                chosen_word = random.choice(rhyme_friendly_words)
                words = get_template_words(template_type, topic)
                line = fill_template(template, words, topic, force_last_word=chosen_word)
                if line and line.split()[-1] == chosen_word:
                    return line
        
        words = get_template_words(template_type, topic)
        line = fill_template(template, words, topic)
        if line:
            return line
    
    template = random.choice(templates)
    words = get_template_words(template_type, topic)
    return fill_template(template, words, topic)

def generate_poem(num_stanzas=3, lines_per_stanza=4, topic=None):
    poem = []
    
    if topic is None:
        topic = pick_topic()
    
    template_types = list(SENTENCE_TEMPLATES.keys())
    
    for stanza in range(num_stanzas):
        stanza_lines = []
        rhyme_A = None
        rhyme_B = None
        forbidden_words = set()
        
        for line_idx in range(lines_per_stanza):
            if line_idx == 0:
                template_type = "interjection_noun_verb"
                line = generate_rhyme_friendly_line(template_type, topic)
                stanza_lines.append(line)
                if line:
                    last_word = line.split()[-1]
                    rhyme_A = last_word
                    forbidden_words.add(last_word)
            elif line_idx == 1:
                template_type = "adjective_noun_verb"
                line = generate_rhyme_friendly_line(template_type, topic)
                stanza_lines.append(line)
                if line:
                    last_word = line.split()[-1]
                    rhyme_B = last_word
                    forbidden_words.add(last_word)
            elif line_idx == 2:
                template_type = random.choice(template_types)
                line = generate_template_line(template_type, topic, enforce_rhyme_with=rhyme_A, forbidden_words=forbidden_words)
                stanza_lines.append(line)
                if line:
                    last_word = line.split()[-1]
                    forbidden_words.add(last_word)
            elif line_idx == 3:
                template_type = random.choice(template_types)
                line = generate_template_line(template_type, topic, enforce_rhyme_with=rhyme_B, forbidden_words=forbidden_words)
                stanza_lines.append(line)
                if line:
                    last_word = line.split()[-1]
                    forbidden_words.add(last_word)
        
        poem.append(stanza_lines)
        if stanza < num_stanzas - 1:
            poem.append([])
    
    print(f"[Poem Topic: {topic.capitalize()}]")
    return poem

def print_poem(poem):
    for stanza in poem:
        if isinstance(stanza, list):
            for line in stanza:
                if line:
                    print(line.capitalize())
            print()
        else:
            print(stanza)

if __name__ == "__main__":
    poem = generate_poem(num_stanzas=3, lines_per_stanza=4)
    print_poem(poem)

