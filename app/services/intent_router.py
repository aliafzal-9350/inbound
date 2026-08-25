import re
from typing import List, Optional

GREETING_PATTERNS: List[str] = [
    r"\b(salam\w*|assalam\w*|asslam\w*|asalam\w*|aslam\w*|aoa|wsalam\w*|walaikum\w*|kya haal|kya hal|kaise ho|kesy ho|kese ho|theek ho|thek ho|kya chal raha|kya haal hai|kia hal|kia haal)\b",
    r"\b(hello|hi|hy|helo|hey|how are you|how r u|how do you do|good morning|good afternoon|good evening|hey there|greetings)\b",
    r"[\u0600-\u06FF]*(سلام|السلام علیکم|وعلیکم السلام|کیا حال ہے|کیسے ہو)[\u0600-\u06FF]*"
]

NON_GREETING_INDICATORS: List[str] = [
    "timing", "timings", "time", "hours", "open", "close", "khule", "band", "kab",
    "price", "rate", "cost", "fee", "charges", "kitne", "kitna", "package", "discount",
    "book", "booking", "appointment", "slot", "reserve", "schedule", "chahiye", "karwana",
    "doctor", "haircut", "treatment", "service", "location", "address", "kahan", "phone",
    "number", "cancel", "refund", "manager", "staff", "ruined", "complaint", "estate", "real estate", "hvac"
]


def is_pure_greeting(text: str) -> bool:
    """Pre-check to determine if an utterance is purely greeting / chitchat.
    If True, the system skips vector database search (Zero-RAG Bypass)."""
    if not text:
        return False
    clean_text = text.lower().strip()
    words = clean_text.split()

    has_greeting = any(re.search(p, clean_text) for p in GREETING_PATTERNS)
    if not has_greeting:
        return False

    # If it contains explicit intent keywords (e.g. "salam timings kya hain?"), it's not a pure greeting
    has_specific_inquiry = any(re.search(rf"\b{re.escape(term)}\b", clean_text) for term in NON_GREETING_INDICATORS)
    if has_specific_inquiry:
        return False

    # Pure greetings are typically short (under 5 words, e.g. "Asslamualikom", "How are you ali", "Salam bhai kya haal hai")
    return len(words) <= 5


def generate_instant_greeting_reply(text: str, tenant_name: str = "RAVISN") -> str:
    """Generates an instant, sub-5ms greeting response matching the user's language and script."""
    clean = text.lower().strip()
    if re.search(r"[\u0600-\u06FF]", text):
        return "وعلیکم السلام! میں RAVISN سے راوی (Ravi) ہوں۔ میں آپ کے کاروبار کو خودکار بنانے میں کیسے مدد کر سکتا ہوں؟"
    elif any(re.search(rf"\b{re.escape(k)}\b", clean) for k in ["how are you", "how r u", "how do you do"]):
        return "I'm doing great, thank you! I am Ravi, the AI assistant at RAVISN. How can I help your business today?"
    elif any(re.search(rf"\b{re.escape(k)}\b", clean) for k in ["kaise ho", "kese ho", "kya haal", "kia hal", "kia haal"]):
        return "Main bilkul theek hoon, shukriya! Main Ravi hoon RAVISN se. Aap batayein main aap ki kya madad kar sakta hoon?"
    elif any(re.search(p, clean) for p in [r"\b(salam\w*|assalam\w*|asslam\w*|asalam\w*|aslam\w*|aoa|wsalam\w*|walaikum\w*)\b"]):
        return "Walaikum Assalam! Main Ravi hoon RAVISN se. Main aap ke business ko automate karne mein kaise madad kar sakta hoon?"
    else:
        return "Hello! I am Ravi, the AI assistant at RAVISN. How can I help automate your business operations today?"


