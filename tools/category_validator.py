#!/usr/bin/env python3
"""
category_validator.py - تایید دسته‌بندی کلمات
فقط ۱۲ دسته اصلی
"""
import os
import json

# فقط ۱۲ دسته اصلی
MAIN_CATEGORIES = [
    "persian_names.txt", "surnames.txt", "cities.txt", "countries.txt",
    "foods.txt", "fruits.txt", "colors.txt", "cars.txt", "animals.txt",
    "objects.txt", "flowers.txt", "jobs.txt"
]

# کلمات کلیدی برای هر دسته
CATEGORY_KEYWORDS = {
    "persian_names.txt": [" ali", "reza", "mohammad", "hossein", "ali ", "reza ", "mohammad ", "hossein "],
    "surnames.txt": ["یان", "پور", "زاده", "یی", "نژاد"],
    "cities.txt": ["شهر", "محله", "روستا", "منطقه"],
    "countries.txt": ["کشور", "ملت", "سیستم"],
    "foods.txt": ["خوراک", "غذا", "آش", "سوپ", "کباب", "برنج", "نان", "شیرینی"],
    "fruits.txt": ["میوه", "سبزی", "صیفی"],
    "colors.txt": ["رنگ", "سرخ", "سبز", "آبی", "زرد"],
    "cars.txt": ["ماشین", "خودرو", "کامیون", "اتوبوس", "موتور"],
    "animals.txt": ["حیوان", "جانور", "پرنده", "ماهی", "سگ", "گربه"],
    "objects.txt": ["شیء", "وسیله", "ابزار", "دستگاه"],
    "flowers.txt": ["گل", "باغچه", "باغ"],
    "jobs.txt": ["شغل", "کار", "حرفه", "تخصص"],
}

# دسته‌بندی معکوس: کلمه → دسته
WORD_TO_CATEGORY = {
    "پراید": "cars.txt",
    "پژو": "cars.txt",
    "سمند": "cars.txt",
    "کامیون": "cars.txt",
    "اتوبوس": "cars.txt",
    "موتور": "cars.txt",
}

def validate_category(word, suggested_category):
    """تایید دسته‌بندی پیشنهادی"""
    # بررسی اینکه آیا دسته اصلی هست
    if suggested_category not in MAIN_CATEGORIES:
        return {
            "valid": False,
            "word": word,
            "suggested": suggested_category,
            "reason": f"دسته '{suggested_category}' جز ۱۲ دسته اصلی نیست"
        }
    
    # بررسی لیست ثابت
    if word in WORD_TO_CATEGORY:
        actual = WORD_TO_CATEGORY[word]
        if actual != suggested_category:
            return {
                "valid": False,
                "word": word,
                "suggested": suggested_category,
                "actual": actual,
                "reason": f"کلمه '{word}' واقعاً مربوط به '{actual}' هست"
            }
        return {"valid": True, "word": word}
    
    # بررسی با کلمات کلیدی
    keywords = CATEGORY_KEYWORDS.get(suggested_category, [])
    for keyword in keywords:
        if keyword in word or word in keyword:
            return {"valid": True, "word": word}
    
    # اگه پیدا نشد، بر اساس ساختار کلمه تصمیم بگیر
    if len(word) <= 4:  # کلمات کوتاه معمولاً اسم هستن
        return {"valid": True, "word": word, "note": "کلمه کوتاه - فرض بر صحت"}
    
    return {"valid": True, "word": word, "note": "عدم قطعیت - نیاز به بررسی"}

def batch_validate(words_with_categories):
    """بررسی دسته‌بندی چندین کلمه"""
    results = []
    for item in words_with_categories:
        result = validate_category(item["word"], item["category"])
        results.append(result)
    return results

if __name__ == "__main__":
    test_words = [
        {"word": "خواجه", "category": "surnames.txt"},
        {"word": "کوکوسبزی", "category": "foods.txt"},
        {"word": "دیزیچه", "category": "cities.txt"},
        {"word": "پراید", "category": "objects.txt"},  # اشتباه
        {"word": "فوتبال", "category": "sports.txt"},  # دسته جدید - رد میشه
    ]
    
    results = batch_validate(test_words)
    for r in results:
        if r["valid"]:
            print(f"✅ {r['word']}: دسته‌بندی صحیح")
        else:
            print(f"❌ {r['word']}: {r['reason']}")
