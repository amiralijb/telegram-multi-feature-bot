import requests

# کلید API برای remove.bg
API_KEY = 'wya8Mpt3KcFcZjkRQkuWk7TQ'

# URL مربوط به API
url = 'https://api.remove.bg/v1.0/removebg'

# مسیر تصویر ورودی
image_path = 'user_photo.jpg'  # مسیر فایل تصویر

# ارسال تصویر به API
def remove_background(image_path):
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            url,
            headers={'X-Api-Key': API_KEY},
            files={'image_file': image_file},
            data={'size': 'auto'}
        )

    # بررسی پاسخ از API
    if response.status_code == 200:
        # ذخیره تصویر بدون پس‌زمینه
        with open('output_image.png', 'wb') as out_file:
            out_file.write(response.content)
        print("تصویر با موفقیت پردازش و ذخیره شد.")
    else:
        print(f"خطا در پردازش تصویر. کد وضعیت: {response.status_code}")
        print(response.text)

# فراخوانی تابع برای پردازش تصویر
remove_background(image_path)
