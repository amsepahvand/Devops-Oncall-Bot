def bot_guide(update, context):
    guide_message = (
        "*📖 توضیحات اولیه نحوه استفاده از ربات*\n\n"
        "*1. اضافه کردن نفرات 👥* \n"
        "برای ساخت لیست آنکال چند تا نکته وجود داره که حتما باید مد نظر قرار بدین : \n"
        "اول اینکه برای ساخت لیست آنکال باید نفرات رو اضافه کنید توجه داشته باشید که برای راحتی شما اضافه کردن نفرات فقط با فوروارد یکی از مسیج های تلگرام اونها ممکنه پس اون فرد باید امکان فوروارد مسیجش از داخل تنظیمات تلگرام موقتا باز کنه\n"
        "برای حذف هر نفر هم میتونی روی حذف افراد بزنی بعد هرکی رو خواستی حذف کنی روی ضربدر جلوی اسمش بزنی\n\n"
        
        "*2. تنظیم شیفت ها ⏰* \n"
        "مطمئن بشین که شیفت ها به درستی تنظیم شده باشن بصورت پیشفرض روی هر ۲۴ ساعت برای تغییر شیفت تنظیم شدن\n\n"
        
        "*3.ساخت لیست آنکال 📆*\n"
        "برای اینکه تیکت ها به درستی به نفرات اساین بشن باید یک لیست آنکال بسازید فراموش نکنید که این موضوع باید هر ماه انجام بشه و چنانچه زمان ساختن لیست جدید تاریخی از زمان ساخت تا یک ماه بعدش وجود داشته بهتون هشدار میده و باید تایید کنید که بازنویسی بشه .\n\n"
        
        "*4.ارسال لیست فعلی 🗒*\n"
        "با این گزینه میتونی لیست فعلی و مدت روزهایی که مونده رو به گروه ارسال کنی"

        "*5. اضافه کردن مدیر 👤*\n"
        "ممکنه نیاز داشته باشین افرادی مه ربات اضافه بشن و بتونن پنل ادمین رو ببینن اما داخل لیست آنکال نباشن میتونید از گزینه اضافه کردن مدیر استفاده کنید و مثل روال اضافه کردن مابقی افراد ، مدیر جدید به ربات اضافه کنید.\n\n"
        
        "*6. اتصال ربات به جیرا 🌀*\n"
        "برای اتصال ربات به جیرا چند تا نکته مهم وجود داره \n"
        "اول اینکه اکانتی که میسازید باید داخل پروژه مورد نظر ادمین باشه\n"
        "برای این کار در نوار بغل پروژه به مسیر project setting > user & role برید\n"
        " دوم اینکه توانایی اساین کردن issue  داخل پروژه رو داشته باشه\n"
        "سوم اینکه کاربرای آنکال اگه قراره تیکت های جیرا بهشون اساین بشه  قابلیت اساین issue داخل جیرا بهشون داده شده باشه\n"
        "برای این کار به project > project setting > permissions برید\n"
        "بعد از این موارد مشخصات خواسته شده داخل ربات رو مرحله به مرحله با دقت پر کنید اگه به درستی وارد بشه یه تیکت تستی میسازه و بهتون پیعام فعال سازی میده\n"
        "از این به بعد میتونید انتخاب کنید تیکت های مشتریاتون روی جیرا ساخته بشه یا نه(فعال/غیرفعال کنید)\n\n"

        "*7.تغییر مشخصات جیرا 🔧*\n"
        "اینجا میتونی مشخصات جیرا رو ببینی یا اگه میخوای تغییرشون بدی فقط کافیه روی هر گزینه ای که میخوای بزنی و بعد مقدار جدید رو وارد کنی\n\n"

        "*8.اتواساین تیکت ها 📌*\n"
        "برای اینکه تیکت های جیرا به افراد آنکال اساین بشن توی قسمت مشاهده لیست نفرات روی گزینه Jira Username جلوی اسم هر نفر بزنید و یوزنیمی که افراد داخل جیرا دارن رو وارد کنید دقت کنید که یوزنیم جیراشون وارد بشه نه اسم نفرات بعد از اون وقتی یه تیکت داخل گروه آنکال بیاد هرکی رو دکمه مشاهده نشده بزنه تیکت توی جیرا به اون نفر اساین میشه\n\n"

        "*9.تغییر گروه آنکال 📬*\n"
        "با این گزینه میتونید گروهی که ربات تیکت ها رو اونجا ارسال میکنه عوض کنید فقط به یاد داشته باید آیدی عددی گروه رو برای ربات ارسال کنید که با - شروع میشه و بعد از عوض کردن حدود ده ثانیه صبر کنید تا ربات ریستارت بشه\n\n "

    )

    context.bot.send_message(chat_id=update.effective_chat.id,text=guide_message,parse_mode='Markdown')


def bot_features(update, context):
    features_message = (
        "*🚀 قابلیت های ربات*\n\n"
        "*1. ارسال تیکت های شما به تیم پاسخگو* 📬\n"
        "میتونید یه گروه بسازید و از اونجا تیکت های مشتریاتون رو مدیریت کنید \n\n"
        
        "*2. امکان نوتیفای تیم آنکال* 🔔\n"
        "بصورت اتوماتیک نفراتی که بعنوان آنکال اضافه شدن زمانی که کاربر تیکتی ثبت کنه مطلع می شوند\n\n"
        
        "*3. اضافه کردن مدیران* 👥\n"
        "میتونید افرادی رو بعنوان مدیر ربات اضافه کنید که داخل لیست آنکال قرار نگیرند اما بتونن ربات رو مدیریت کنن\n\n"
        
        "*4. تنظیم دوره های تغییر شیفت* ⏱\n"
        "میتونید مشخص کنید شیفت ها هر چند روز یکبار تغییر کنند\n\n"
        
        "*5. ساخت لیست آنکال بصورت اتوماتیک* 📅\n"
        "ربات میتونه بر اساس تعداد نفرات و زمانبندی شیفت لیست آنکال رو برای مدت ۳۰ روز آتی بسازه\n\n"
        
        "*6. امکان اتصال به جیرا* 🌀\n"
        "میتونید ربات رو به جیرا وصل کنید تا هم براتون توی جیرا تیکت ها رو ذخیره کنه و هم اگه برای افراد نام کاربری جیرا ساخته باشید تیکت ها رو بهشون اساین کنه\n\n"

        "*7. نمایش تاریخچه تیکت های هر نفر به خودش* 🎫\n"
        "مشتری های شما وقتی تیکت میزنن میتونن ببینن مسئول تیکتشون چه کسی هست و چنانچه به جیرا وصل باشه شماره تیکت جیراشون رو ببینن ، ضمنا داخل بخش تیکت های من میتونن وضعیت تسک توی جیرا رو هم متوجه بشن که توی چه وضعیتی قرار داره\n\n"
    )

    context.bot.send_message(chat_id=update.effective_chat.id,text=features_message,parse_mode='Markdown')
