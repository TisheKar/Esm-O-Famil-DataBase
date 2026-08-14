# 🎮 دیتابیس بازی اسم و فامیل (Esm O Famil DataBase)

دیتابیس جامع کلمات فارسی برای بازی اسم و فامیل

---

## 📊 آمار کلی

| دسته | تعداد کلمه | فایل |
|------|-----------|------|
| 🐾 حیوانات | ۳۴۸ | `animals.txt` |
| 🚗 ماشین‌ها | ۴۴۱ | `cars.txt` |
| 🏙️ شهرها | ۷۷۹ | `cities.txt` |
| 🎨 رنگ‌ها | ۱۸۲ | `colors.txt` |
| 🌍 کشورها | ۱۹۶ | `countries.txt` |
| 🌸 گل‌ها | ۴۲۲ | `flowers.txt` |
| 🍽️ غذاها | ۴۷۰ | `foods.txt` |
| 🍎 میوه‌ها | ۱۹۷ | `fruits.txt` |
| 💼 مشاغل | ۸۵۰ | `jobs.txt` |
| 📦 اشیاء | ۹۸۶ | `objects.txt` |
| 👤 اسامی ایرانی | ۱,۴۹۷ | `persian_names.txt` |
| 👨‍👩‍👧 فامیلی‌ها | ۱,۱۷۵ | `surnames.txt` |
| **مجموع** | **7,543** | |

---

## 📁 ساختار فایل‌ها

هر فایل شامل لیستی از کلمات فارسی هست:
- هر خط یک کلمه
- بدون تکرار
- مرتب شده

### نمونه:

**animals.txt:**
```
آهو
ببر
پلنگ
تمساح
...
```

**cars.txt:**
```
پراید
پژو
سمند
کامیون
...
```

---

## 🎯 نحوه استفاده

### پایتون:
```python
def load_words(category):
    with open(f'{category}.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

animals = load_words('animals')
print(f'تعداد حیوانات: {len(animals)}')
```

### جاوا اسکریپت:
```javascript
const fs = require('fs');

function loadWords(category) {
    const content = fs.readFileSync(`${category}.txt`, 'utf-8');
    return content.split('\n').filter(line => line.trim());
}

const animals = loadWords('animals');
console.log(`تعداد حیوانات: ${animals.length}`);
```

---

## 📝 قوانین بازی

1. حرف اول کلمه مشخص میشه
2. بازیکن‌ها باید برای هر دسته کلمه پیدا کنن
3. اگه کسی کلمه تکراری بگه یا اشتباه بنویسه، امتیاز منفی میگیره
4. سریع‌ترین بازیکن برنده میشه

---

## 🔧 مشارکت

اگه کلمه‌ای کم هست یا اشتباه داره:
1. Fork کنید
2. فایل مربوطه رو ادیت کنید
3. Pull Request بزنید

---

## 📄 مجوز

این دیتابیس رایگان و اوپن‌سورس هست.

---

## 👨‍💻 سازنده

**سامی** - توسعه‌دهنده پایتون

**گیت‌هاب:** [TisheKar](https://github.com/TisheKar)
