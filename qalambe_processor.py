#!/usr/bin/env python3
"""
qalambe_processor.py - پردازشگر اصلی بازی اسم و فامیل
فقط ۱۲ دسته اصلی
"""
import os
import sys
from datetime import datetime

# اضافه کردن مسیر tools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "tools"))

from spell_checker import spell_check_all_files, fix_persian_text
from category_validator import validate_category, batch_validate
from duplicate_finder import check_new_word, find_duplicates
from auto_correct import auto_correct_word, batch_auto_correct
from smart_decision import SmartDecisionMaker

# فقط ۱۲ دسته اصلی
MAIN_CATEGORIES = [
    "persian_names.txt", "surnames.txt", "cities.txt", "countries.txt",
    "foods.txt", "fruits.txt", "colors.txt", "cars.txt", "animals.txt",
    "objects.txt", "flowers.txt", "jobs.txt"
]

class QalambeProcessor:
    """پردازشگر اصلی بازی اسم و فامیل"""
    
    def __init__(self, db_dir="/tmp/esm-o-famil-db"):
        self.db_dir = db_dir
        self.decision_maker = SmartDecisionMaker(db_dir)
        self.files = self.load_all_files()
    
    def load_all_files(self):
        """بارگذاری فقط ۱۲ فایل اصلی"""
        files = {}
        for fname in MAIN_CATEGORIES:
            path = os.path.join(self.db_dir, fname)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    files[fname] = [line.strip() for line in f if line.strip()]
        return files
    
    def process_words(self, words_with_categories):
        """پردازش کلمات"""
        results = []
        
        for item in words_with_categories:
            word = item["word"]
            game_category = item["file"]
            
            # بررسی اینکه آیا دسته اصلی هست
            if game_category not in MAIN_CATEGORIES:
                results.append({
                    "original": word,
                    "corrected": word,
                    "category": game_category,
                    "decision": {
                        "decision": "reject",
                        "reason": f"دسته '{game_category}' جز ۱۲ دسته اصلی نیست"
                    }
                })
                continue
            
            # ۱. اصلاح خودکار
            corrected_word = auto_correct_word(word)
            
            # ۲. تصمیم‌گیری هوشمند
            all_words = []
            for words in self.files.values():
                all_words.extend(words)
            
            decision = self.decision_maker.decide_word(
                corrected_word, 
                game_category, 
                all_words
            )
            
            # ۳. ذخیره نتیجه
            if decision["decision"] == "accept":
                # اضافه کردن به فایل
                if game_category in self.files:
                    self.files[game_category].append(corrected_word)
                    self.files[game_category].sort()
                    
                    # نوشتن فایل
                    filepath = os.path.join(self.db_dir, game_category)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("\n".join(self.files[game_category]) + "\n")
            
            results.append({
                "original": word,
                "corrected": corrected_word,
                "category": game_category,
                "decision": decision
            })
        
        return results
    
    def update_readme(self):
        """بروزرسانی README"""
        # شمارش کلمات
        counts = {}
        total = 0
        for fname, words in self.files.items():
            counts[fname] = len(words)
            total += len(words)
        
        # تولید محتوای README
        readme_content = f"""# 🎮 دیتابیس بازی اسم و فامیل (Esm O Famil DataBase)

دیتابیس جامع کلمات فارسی برای بازی اسم و فامیل

---

## 📊 آمار کلی

| دسته | تعداد کلمه | فایل |
|------|-----------|------|
"""
        
        # مرتب کردن بر اساس تعداد
        sorted_files = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)
        
        emojis = {
            "persian_names.txt": "👤", "surnames.txt": "👨‍👩‍👧", "cities.txt": "🏙️",
            "countries.txt": "🌍", "foods.txt": "🍽️", "fruits.txt": "🍎",
            "colors.txt": "🎨", "cars.txt": "🚗", "animals.txt": "🐾",
            "objects.txt": "📦", "flowers.txt": "🌸", "jobs.txt": "💼",
        }
        
        names = {
            "persian_names.txt": "اسامی ایرانی", "surnames.txt": "فامیلی‌ها",
            "cities.txt": "شهرها", "countries.txt": "کشورها", "foods.txt": "غذاها",
            "fruits.txt": "میوه‌ها", "colors.txt": "رنگ‌ها", "cars.txt": "ماشین‌ها",
            "animals.txt": "حیوانات", "objects.txt": "اشیاء", "flowers.txt": "گل‌ها",
            "jobs.txt": "مشاغل",
        }
        
        for fname in sorted_files:
            emoji = emojis.get(fname, "📝")
            name = names.get(fname, fname)
            readme_content += f"| {emoji} {name} | {counts[fname]:,} | `{fname}` |\n"
        
        readme_content += f"| **مجموع** | **{total:,}** | |\n"
        
        readme_content += f"""

---

## 📁 ساختار فایل‌ها

هر فایل شامل لیستی از کلمات فارسی هست:
- هر خط یک کلمه
- بدون تکرار
- مرتب شده (الفبایی)

---

## 🤖 مشارکت خودکار

این دیتابیس توسط ربات **قلمبه** به صورت خودکار بروزرسانی میشه:
- کلمات جدید از بازی جمع‌آوری میشن
- بعد از بررسی تکرار، اضافه میشن
- فورک و PR خودکار ایجاد میشه

---

*آخرین بروزرسانی: {datetime.now().strftime('%Y/%m/%d %H:%M')}*
"""
        
        # نوشتن README
        readme_path = os.path.join(self.db_dir, "README.md")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
    
    def get_stats(self):
        """آمار کلی"""
        total = sum(len(words) for words in self.files.values())
        return {
            "total_files": len(self.files),
            "total_words": total,
            "files": {fname: len(words) for fname, words in self.files.items()}
        }

if __name__ == "__main__":
    # مثال استفاده
    processor = QalambeProcessor()
    
    # کلمات نمونه
    test_words = [
        {"word": "خوجه", "file": "surnames.txt"},
        {"word": "کوکوسبزی", "file": "foods.txt"},
        {"word": "دیزیچه", "file": "cities.txt"},
    ]
    
    # پردازش
    results = processor.process_words(test_words)
    
    # نمایش نتایج
    print("📊 نتایج پردازش:")
    for r in results:
        print(f"  {r['original']} → {r['corrected']} ({r['category']})")
        print(f"    تصمیم: {r['decision']['decision']}")
        print(f"    دلیل: {r['decision']['reason']}")
    
    # بروزرسانی README
    processor.update_readme()
    print("\n✅ README بروزرسانی شد")
