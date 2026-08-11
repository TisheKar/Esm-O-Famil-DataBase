#!/usr/bin/env python3
"""
spell_checker.py - بررسی غلط‌های املایی کلمات فارسی
"""
import os
import re

# حروف فارسی که ممکنه اشتباه نوشته بشن
common_misspellings = {
    "ى": "ی",  # یای املایی
    "ك": "ک",  # کاف عربی
    "ؤ": "و",  # واو مجهول
    "إ": "ا",  # الف با همزه
    "أ": "ا",  # الف با همزه
    "ة": "ه",  # تاء مربوطه
    "٤": "۴",  # عدد عربی
    "٥": "۵",  # عدد عربی
    "٦": "۶",  # عدد عربی
    "٧": "۷",  # عدد عربی
    "٨": "۸",  # عدد عربی
    "٩": "۹",  # عدد عربی
}

def fix_persian_text(text):
    """اصلاح خودکار حروف فارسی"""
    for wrong, correct in common_misspellings.items():
        text = text.replace(wrong, correct)
    return text

def check_word(word, all_words):
    """بررسی کلمه و پیشنهاد اصلاح"""
    fixed = fix_persian_text(word)
    
    if fixed != word:
        return {
            "original": word,
            "fixed": fixed,
            "issue": "غلط املایی",
            "suggestion": fixed
        }
    
    # بررسی تکراری با نوشته متفاوت
    for existing in all_words:
        if existing != word and (fixed in existing or existing in fixed):
            return {
                "original": word,
                "fixed": word,
                "issue": "شباهت به کلمه موجود",
                "suggestion": existing
            }
    
    return None

def spell_check_all_files(db_dir):
    """بررسی املایی همه فایل‌ها"""
    files = [f for f in os.listdir(db_dir) if f.endswith('.txt')]
    issues = []
    
    for fname in files:
        path = os.path.join(db_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            words = [line.strip() for line in f if line.strip()]
        
        all_words = []
        for other_fname in files:
            if other_fname != fname:
                other_path = os.path.join(db_dir, other_fname)
                with open(other_path, "r", encoding="utf-8") as f:
                    all_words.extend([line.strip() for line in f if line.strip()])
        
        for word in words:
            result = check_word(word, all_words)
            if result:
                result["file"] = fname
                issues.append(result)
    
    return issues

if __name__ == "__main__":
    import sys
    db_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/esm-o-famil-db"
    issues = spell_check_all_files(db_dir)
    
    if issues:
        print(f"⚠️ {len(issues)} مشکل املایی پیدا شد:")
        for issue in issues:
            print(f"  {issue['file']}: {issue['original']} → {issue['fixed']} ({issue['issue']})")
    else:
        print("✅ همه کلمات صحیح هستند")
