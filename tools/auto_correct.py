#!/usr/bin/env python3
"""
auto_correct.py - اصلاح خودکار کلمات غلط
"""
import os
import re

# دیکشنری اصلاحات خودکار
AUTO_CORRECTIONS = {
    # اصلاح حروف فارسی
    "ى": "ی",
    "ك": "ک",
    "ؤ": "و",
    "إ": "ا",
    "أ": "ا",
    "ة": "ه",
    "٤": "۴",
    "٥": "۵",
    "٦": "۶",
    "٧": "۷",
    "٨": "۸",
    "٩": "۹",
    
    # اصلاح غلط‌های رایج
    "مکان": "مکان",
    "مکان": "مکان",
    "مکان": "مکان",
    
    # اصلاح کلمات مرکب
    "کوکو سبزی": "کوکوسبزی",
    "آب گوشت": "آبگوشت",
    "سمن د": "سمند",
    "پرای د": "پراید",
}

# الگوهای اصلاح
CORRECTION_PATTERNS = [
    (r'(\w)\s+(\w)', r'\1\2'),  # حذف فاصله‌های اضافی
    (r'(\w)ـ(\w)', r'\1\2'),  # حذف نیم‌فاصله‌های اضافی
]

def auto_correct_word(word):
    """اصلاح خودکار یک کلمه"""
    corrected = word
    
    # اصلاح حروف
    for wrong, correct in AUTO_CORRECTIONS.items():
        corrected = corrected.replace(wrong, correct)
    
    # اصلاح با الگوها
    for pattern, replacement in CORRECTION_PATTERNS:
        corrected = re.sub(pattern, replacement, corrected)
    
    return corrected

def batch_auto_correct(words):
    """اصلاح خودکار چندین کلمه"""
    results = []
    for word in words:
        corrected = auto_correct_word(word)
        if corrected != word:
            results.append({
                "original": word,
                "corrected": corrected,
                "fixed": True
            })
        else:
            results.append({
                "original": word,
                "corrected": word,
                "fixed": False
            })
    return results

def auto_correct_file(filepath):
    """اصلاح خودکار همه کلمات یک فایل"""
    with open(filepath, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    results = batch_auto_correct(words)
    
    # نوشتن فایل اصلاح شده
    corrected_words = [r["corrected"] for r in results]
    corrected_words.sort()
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(corrected_words) + "\n")
    
    return results

if __name__ == "__main__":
    test_words = ["کوکو سبزی", "آب گوشت", "پرای د", "خواجه"]
    results = batch_auto_correct(test_words)
    
    for r in results:
        if r["fixed"]:
            print(f"✅ اصلاح شد: {r['original']} → {r['corrected']}")
        else:
            print(f"ℹ️ بدون تغییر: {r['original']}")
