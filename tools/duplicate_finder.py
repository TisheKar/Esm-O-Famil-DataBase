#!/usr/bin/env python3
"""
duplicate_finder.py - پیدا کردن کلمات تکراری
"""
import os
from collections import defaultdict

def find_duplicates(db_dir):
    """پیدا کردن کلمات تکراری در همه فایل‌ها"""
    files = [f for f in os.listdir(db_dir) if f.endswith('.txt')]
    
    # دیتابیس کلمات
    word_files = defaultdict(list)
    
    for fname in files:
        path = os.path.join(db_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    word_files[word].append(fname)
    
    # پیدا کردن تکراری‌ها
    duplicates = {}
    for word, files_list in word_files.items():
        if len(files_list) > 1:
            duplicates[word] = files_list
    
    return duplicates

def find_similar_words(db_dir):
    """پیدا کردن کلمات مشابه (نوشته متفاوت)"""
    files = [f for f in os.listdir(db_dir) if f.endswith('.txt')]
    all_words = []
    
    for fname in files:
        path = os.path.join(db_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                word = line.strip()
                if word:
                    all_words.append((word, fname))
    
    similar = []
    for i, (word1, file1) in enumerate(all_words):
        for word2, file2 in all_words[i+1:]:
            if word1 != word2 and file1 != file2:
                # بررسی شباهت
                if (word1 in word2 or word2 in word1 or 
                    len(set(word1) & set(word2)) > len(word1) * 0.7):
                    similar.append({
                        "word1": word1,
                        "file1": file1,
                        "word2": word2,
                        "file2": file2
                    })
    
    return similar

def check_new_word(word, db_dir):
    """بررسی کلمه جدید در برابر دیتابیس"""
    files = [f for f in os.listdir(db_dir) if f.endswith('.txt')]
    
    for fname in files:
        path = os.path.join(db_dir, fname)
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                existing = line.strip()
                if existing == word:
                    return {"exists": True, "file": fname}
                # بررسی شباهت
                if (word in existing or existing in word or 
                    len(set(word) & set(existing)) > len(word) * 0.7):
                    return {"exists": True, "file": fname, "similar": existing}
    
    return {"exists": False}

if __name__ == "__main__":
    import sys
    db_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/esm-o-famil-db"
    
    # پیدا کردن تکراری‌ها
    duplicates = find_duplicates(db_dir)
    if duplicates:
        print(f"⚠️ {len(duplicates)} کلمه تکراری پیدا شد:")
        for word, files in duplicates.items():
            print(f"  {word}: {', '.join(files)}")
    else:
        print("✅ کلمه تکراری پیدا نشد")
    
    # پیدا کردن کلمات مشابه
    similar = find_similar_words(db_dir)
    if similar:
        print(f"\n🔍 {len(similar)} کلمه مشابه پیدا شد:")
        for s in similar[:10]:  # فقط ۱۰ تای اول
            print(f"  {s['word1']} ({s['file1']}) ↔ {s['word2']} ({s['file2']})")
