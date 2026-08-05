import re


# حروف عربی → فارسی
_ARABIC_TO_PERSIAN = {
    "ك": "ک", "ي": "ی", "ؤ": "و",
    "إ": "ا", "أ": "ا", "آ": "ا",
    "ة": "ه", "ء": "",
}

# اعراب و نشانه‌های خاص
_DIACRITICS_RE = re.compile(
    "[\u0617-\u061A\u064B-\u0652\u0656-\u065F\u0670\u0640]"
)
_PUNCT_RE = re.compile(r"[^\w\s\u0600-\u06FF]")


def normalize(text: str) -> str:
    if not text:
        return ""
    text = _DIACRITICS_RE.sub("", text)
    for ar, fa in _ARABIC_TO_PERSIAN.items():
        text = text.replace(ar, fa)
    text = _PUNCT_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
