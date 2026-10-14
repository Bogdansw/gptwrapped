"""
topics.py - Lightweight keyword & category topic analysis system.

Performs topic categorization and word-frequency extraction locally without
external AI APIs. Supports English and Romanian stopword removal and keyword
dictionaries.

Classification Approach:
- Heuristic Keyword Matching: Weighted scoring of conversation titles (3x)
  and user message prompts (1x).
- Strongest Category Assignment: The category with the highest weighted score
  above a minimum threshold is assigned as the primary category. If no
  category meets the threshold, it is classified as 'Other'.
- This approximate classification provides a clean overview of user interest
  areas based purely on measurable keyword occurrences.
"""

from collections import Counter
import re
from typing import Dict, List, Set, Tuple

CATEGORIES = [
    "Programming / Web Development",
    "School / Education",
    "Gaming",
    "Anime / Manga",
    "Technology",
    "AI",
    "Entertainment",
    "Writing",
    "Personal / Life",
    "Travel",
    "Other"
]

CATEGORY_KEYWORDS: Dict[str, Set[str]] = {
    "Programming / Web Development": {
        # English
        "python", "javascript", "typescript", "react", "html", "css", "vue", "angular",
        "node", "nodejs", "npm", "django", "flask", "fastapi", "sql", "postgres",
        "mysql", "mongodb", "docker", "kubernetes", "git", "github", "gitlab", "api",
        "rest", "graphql", "bug", "debugging", "syntax", "function", "class", "async",
        "await", "backend", "frontend", "fullstack", "algorithm", "regex", "json",
        "compiler", "rust", "golang", "c++", "c#", "java", "kotlin", "swift", "linux",
        "bash", "powershell", "terminal", "script", "framework", "library", "refactor",
        # Romanian
        "programare", "functie", "variabila", "baza de date", "eroare", "cod", "compilare",
        "dezvoltare", "pagini web", "aplicatie", "proiect", "algoritm"
    },
    "School / Education": {
        # English
        "homework", "assignment", "essay", "thesis", "dissertation", "exam", "quiz",
        "university", "college", "school", "highschool", "course", "lesson", "professor",
        "teacher", "student", "study", "research", "paper", "citation", "apa", "mla",
        "math", "mathematics", "calculus", "algebra", "geometry", "physics", "chemistry",
        "biology", "history", "geography", "literature", "philosophy", "grade",
        # Romanian
        "tema", "teme", "facultate", "universitate", "scoala", "liceu", "profesor",
        "student", "examen", "sesiune", "curs", "laborator", "seminar", "proiect",
        "fizica", "chimie", "istorie", "geografie", "bac", "bacalaureat", "invatat"
    },
    "Gaming": {
        # English
        "game", "gaming", "gameplay", "gamer", "steam", "playstation", "xbox", "nintendo",
        "switch", "pc", "fps", "rpg", "mmorpg", "pvp", "pve", "quest", "level", "boss",
        "build", "minecraft", "fortnite", "valorant", "csgo", "counter-strike", "dota",
        "league of legends", "lol", "elden ring", "gta", "mod", "mods", "modding",
        "speedrun", "esports", "twitch", "discord", "multiplayer",
        # Romanian
        "joc", "jocuri", "jucator", "misiune", "nivel", "arme", "consola"
    },
    "Anime / Manga": {
        # English
        "anime", "manga", "manhwa", "manhua", "otaku", "cosplay", "shonen", "seinen",
        "crunchyroll", "naruto", "one piece", "bleach", "dragon ball", "attack on titan",
        "jujutsu kaisen", "demon slayer", "my hero academia", "chainsaw man", "death note",
        "fullmetal alchemist", "berserk", "hunter x hunter", "evangelion", "gundam",
        "weeb", "light novel", "studio ghibli", "hayao miyazaki",
        # Romanian
        "desene japoneze", "benzi desenate japoneze", "subtitrari anime"
    },
    "Technology": {
        # English
        "hardware", "software", "cpu", "gpu", "processor", "ram", "ssd", "nvme",
        "motherboard", "windows", "macos", "ios", "android", "iphone", "samsung",
        "laptop", "pc", "monitor", "router", "wifi", "bluetooth", "network", "server",
        "cloud", "aws", "azure", "security", "cybersecurity", "firewall", "firmware",
        "gadget", "smartwatch", "setup", "troubleshoot", "driver", "benchmark",
        # Romanian
        "tehnologie", "calculator", "placa video", "procesor", "memorie", "retea",
        "securitate", "telefon", "ecran", "sistem de operare"
    },
    "AI": {
        # English
        "ai", "artificial intelligence", "machine learning", "deep learning", "neural network",
        "llm", "large language model", "gpt", "chatgpt", "openai", "claude", "anthropic",
        "gemini", "llama", "transformer", "prompt", "fine-tuning", "rag", "embeddings",
        "midjourney", "stable diffusion", "diffusion model", "reinforcement learning",
        "nlp", "computer vision", "agent", "weights", "parameters", "token", "tokens",
        # Romanian
        "inteligenta artificiala", "invatare automata", "modele lingvistice", "retele neuronale"
    },
    "Entertainment": {
        # English
        "movie", "film", "cinema", "tv", "series", "show", "netflix", "hbo", "disney",
        "music", "song", "album", "artist", "band", "concert", "spotify", "guitar",
        "piano", "podcast", "celebrity", "actor", "actress", "director", "hollywood",
        "trailer", "soundtrack", "genre", "comedy", "drama", "thriller", "horror",
        # Romanian
        "film", "filme", "muzica", "melodie", "cantec", "spectacol", "actori",
        "regizor", "comedie", "emisiune"
    },
    "Writing": {
        # English
        "write", "writing", "story", "novel", "fiction", "character", "plot", "dialogue",
        "poem", "poetry", "script", "screenplay", "article", "blog", "copywriting",
        "proofread", "editing", "grammar", "creative writing", "worldbuilding", "prose",
        "chapter", "draft", "synopsis", "rhyme", "author",
        # Romanian
        "scriere", "poveste", "roman", "poezie", "articol", "redactare", "dialog",
        "personaj", "gramatica", "corectura", "text", "scriitor"
    },
    "Personal / Life": {
        # English
        "fitness", "workout", "gym", "diet", "nutrition", "calories", "health", "sleep",
        "routine", "habit", "motivation", "mindset", "finance", "budget", "investing",
        "money", "career", "resume", "cv", "job", "interview", "relationship", "advice",
        "gift", "birthday", "cooking", "recipe", "coffee", "meditation",
        # Romanian
        "viata", "sanatate", "sport", "sala", "dieta", "nutritie", "somn", "obicei",
        "bani", "finante", "cariera", "interviu", "sfat", "relatie", "reteta", "gatit"
    },
    "Travel": {
        # English
        "travel", "trip", "vacation", "holiday", "flight", "hotel", "airbnb", "passport",
        "visa", "destination", "itinerary", "tourist", "tourism", "sightseeing", "explore",
        "city", "beach", "mountain", "country", "ticket", "luggage", "packing", "roadtrip",
        # Romanian
        "calatorie", "vacanta", "concediu", "zbor", "avion", "cazare", "pasaport",
        "itinerar", "turism", "obiective", "munte", "mare", "drumetie"
    }
}

STOPWORDS_EN = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "aren't", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "can't", "cannot", "could", "couldn't", "did",
    "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", "each", "few",
    "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him",
    "himself", "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in",
    "into", "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than",
    "that", "that's", "the", "their", "theirs", "them", "themselves", "then", "there",
    "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd",
    "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
    "yours", "yourself", "yourselves",
    # Conversational filler
    "please", "help", "write", "create", "make", "explain", "give", "tell", "show",
    "chatgpt", "hello", "hi", "hey", "thanks", "thank", "much", "know", "want", "need",
    "like", "using", "example", "simple", "good", "best", "way", "get", "find", "use",
    "one", "two", "also", "just", "well", "see", "think", "look", "try", "new"
}

STOPWORDS_RO = {
    "ai", "ale", "alea", "altceva", "alta", "am", "ar", "are", "as", "asa", "asemenea",
    "asta", "astea", "astfel", "asupra", "atare", "atat", "atata", "atatea", "atatia",
    "atunci", "au", "avea", "avem", "avut", "azi", "buna", "ca", "calatorie", "cam",
    "cand", "care", "cat", "cate", "cati", "cativa", "ce", "cea", "ceea", "cei", "cel",
    "cele", "celor", "ceva", "chiar", "cinci", "cine", "cineva", "contra", "cu", "cum",
    "cumva", "da", "daca", "dar", "datorita", "de", "deci", "deja", "deoarece", "departe",
    "desi", "din", "dincolo", "dintr", "dintre", "doar", "doi", "doilea", "doua", "drept",
    "dupa", "ea", "ei", "el", "ele", "era", "eram", "erati", "este", "esti", "eu", "face",
    "fara", "fata", "fecare", "fii", "fim", "fiti", "foarte", "fost", "frumos", "i", "ia",
    "iar", "ieri", "ii", "il", "imi", "in", "inainte", "inapoi", "inca", "incat", "insa",
    "intr", "intre", "iti", "la", "langa", "le", "li", "lor", "lui", "ma", "mai", "mare",
    "mari", "mea", "mei", "mele", "mereu", "meu", "mi", "mie", "mine", "mod", "mult",
    "multa", "multe", "multi", "multumesc", "ne", "nevoie", "ni", "nici", "niciodata",
    "nimeni", "nimic", "niste", "noastra", "noastre", "noi", "nostri", "nostru", "noua",
    "nu", "opt", "ori", "oricare", "orice", "oricine", "orisi", "orisiunde", "pana",
    "patru", "pe", "pentru", "peste", "pana", "plus", "poate", "pot", "prea", "prima",
    "primul", "prin", "putin", "putina", "putini", "sa", "salut", "sase", "sau", "se",
    "si", "sie", "siesi", "sir", "spre", "sub", "sunt", "suntem", "sunteti", "sus", "ta",
    "tai", "tale", "tau", "te", "ti", "tie", "tine", "toata", "toate", "tocmai", "tot",
    "toti", "totusi", "trebui", "trebuie", "trei", "tu", "un", "una", "unde", "undeva",
    "unei", "unele", "uneori", "unii", "unor", "unu", "unui", "unul", "va", "varianta",
    "vezi", "vi", "voastra", "voastre", "voi", "vostri", "vostru", "vou", "voua", "vreo",
    "vreun", "vreau", "zi", "zile",
    # Romanian conversational filler
    "rog", "ajuta-ma", "ajuta", "mersi", "arata", "arata-mi", "da-mi", "scrie"
}

ALL_STOPWORDS = STOPWORDS_EN.union(STOPWORDS_RO)


def clean_text_tokens(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words, stripping punctuation."""
    if not text:
        return []
    # Match words including hyphens and apostrophes
    words = re.findall(r"\b[a-zA-ZăâîșțĂÂÎȘȚ0-9+#.-]{2,}\b", text.lower())
    return words


def classify_conversation(title: str, user_texts: List[str]) -> Tuple[str, Dict[str, float]]:
    """
    Classify a conversation into the strongest category.
    Weighted scoring: Title tokens count for 3 points, message tokens count for 1 point.
    Returns: (best_category_name, dict_of_all_scores)
    """
    scores: Dict[str, float] = {cat: 0.0 for cat in CATEGORIES if cat != "Other"}

    # Process title
    title_tokens = clean_text_tokens(title)
    title_joined = " ".join(title_tokens)

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in title_joined:
                    scores[cat] += 4.0
            else:
                if kw in title_tokens:
                    scores[cat] += 3.0

    # Process user messages (sample up to first 5 messages to capture intent)
    combined_user_text = " ".join(user_texts[:5]).lower()
    user_tokens = clean_text_tokens(combined_user_text)

    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if " " in kw:
                if kw in combined_user_text:
                    scores[cat] += 2.0
            else:
                if kw in user_tokens:
                    scores[cat] += 1.0

    # Determine highest scoring category
    best_cat = "Other"
    best_score = 0.0
    for cat, score in scores.items():
        if score > best_score:
            best_score = score
            best_cat = cat

    # Require a minimum evidence threshold of 2.0 points
    if best_score < 2.0:
        best_cat = "Other"

    return best_cat, scores


def extract_meaningful_words(texts: List[str], top_n: int = 20) -> List[Tuple[str, int]]:
    """
    Extract the most common meaningful words, removing English and Romanian stopwords.
    """
    counter = Counter()
    for text in texts:
        tokens = clean_text_tokens(text)
        for token in tokens:
            # Skip stopwords, pure numbers, and very short tokens
            if token in ALL_STOPWORDS or token.isdigit() or len(token) < 3:
                continue
            counter[token] += 1
    return counter.most_common(top_n)


def extract_revisited_subjects(titles: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
    """
    Identify recurring subjects or title themes across conversations.
    Finds keywords or multi-word patterns that appear across the most distinct titles.
    """
    word_to_titles: Dict[str, Set[int]] = {}

    for idx, title in enumerate(titles):
        tokens = clean_text_tokens(title)
        seen_in_title = set()
        for token in tokens:
            if token in ALL_STOPWORDS or token.isdigit() or len(token) < 3:
                continue
            if token not in seen_in_title:
                seen_in_title.add(token)
                word_to_titles.setdefault(token, set()).add(idx)

    # Rank by number of distinct conversation titles containing the word
    ranked = sorted(
        [(word, len(indices)) for word, indices in word_to_titles.items() if len(indices) > 1],
        key=lambda x: x[1],
        reverse=True
    )
    return ranked[:top_n]
