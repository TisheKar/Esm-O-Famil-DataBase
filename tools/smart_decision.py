#!/usr/bin/env python3
"""
smart_decision.py - تصمیم‌گیری هوشمند بدون نیاز به ادمین
"""
import os
import json
from datetime import datetime

class SmartDecisionMaker:
    """تصمیم‌گیر هوشمند برای بازی اسم و فامیل"""
    
    def __init__(self, db_dir):
        self.db_dir = db_dir
        self.log_file = os.path.join(db_dir, "decision_log.json")
        self.load_log()
    
    def load_log(self):
        """بارگذاری لاگ تصمیمات"""
        if os.path.exists(self.log_file):
            with open(self.log_file, "r", encoding="utf-8") as f:
                self.log = json.load(f)
        else:
            self.log = []
    
    def save_log(self):
        """ذخیره لاگ تصمیمات"""
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.log, f, ensure_ascii=False, indent=2)
    
    def add_decision(self, word, category, decision, reason):
        """اضافه کردن تصمیم به لاگ"""
        self.log.append({
            "timestamp": datetime.now().isoformat(),
            "word": word,
            "category": category,
            "decision": decision,
            "reason": reason
        })
        self.save_log()
    
    def decide_word(self, word, game_category, all_words):
        """تصمیم‌گیری هوشمند برای یک کلمه"""
        
        # ۱. بررسی تکراری
        if word in all_words:
            return {
                "decision": "reject",
                "reason": f"کلمه '{word}' از قبل وجود دارد"
            }
        
        # ۲. بررسی دسته‌بندی
        category_check = self.validate_category(word, game_category)
        if not category_check["valid"]:
            return {
                "decision": "reject",
                "reason": f"کلمه '{word}' مربوط به '{category_check['actual']}' نیست"
            }
        
        # ۳. بررسی املایی
        if self.has_spelling_error(word):
            return {
                "decision": "correct",
                "reason": f"غلط املایی - اصلاح خودکار انجام شد"
            }
        
        # ۴. تصمیم نهایی
        self.add_decision(word, game_category, "accept", "تصمیم خودکار")
        return {
            "decision": "accept",
            "reason": f"کلمه '{word}' به '{game_category}' اضافه شد"
        }
    
    def validate_category(self, word, category):
        """تایید دسته‌بندی"""
        # اینجا میشه از category_validator.py استفاده کرد
        from category_validator import validate_category
        return validate_category(word, category)
    
    def has_spelling_error(self, word):
        """بررسی غلط املایی"""
        # اینجا میشه از spell_checker.py استفاده کرد
        from spell_checker import fix_persian_text
        return fix_persian_text(word) != word
    
    def get_stats(self):
        """آمار تصمیمات"""
        if not self.log:
            return {"total": 0, "accepted": 0, "rejected": 0, "corrected": 0}
        
        total = len(self.log)
        accepted = sum(1 for d in self.log if d["decision"] == "accept")
        rejected = sum(1 for d in self.log if d["decision"] == "reject")
        corrected = sum(1 for d in self.log if d["decision"] == "correct")
        
        return {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "corrected": corrected
        }

if __name__ == "__main__":
    import sys
    db_dir = sys.argv[1] if len(sys.argv) > 1 else "/tmp/esm-o-famil-db"
    
    decision_maker = SmartDecisionMaker(db_dir)
    stats = decision_maker.get_stats()
    
    print("📊 آمار تصمیمات:")
    print(f"  مجموع: {stats['total']}")
    print(f"  پذیرفته: {stats['accepted']}")
    print(f"  رد شده: {stats['rejected']}")
    print(f"  اصلاح شده: {stats['corrected']}")
