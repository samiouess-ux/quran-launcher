# محرك القرآن السينمائي — Quran Launcher

هذا المستودع نسخة مستقلة لاختبار نقل محرك الفيديو الأصلي إلى Quran Launcher. العمل الحالي يتم على الفرع `feature/islamic-tiktok-engine-port` فقط.

## ما ينتجه المحرك

- تشغيل محرك Python وFFmpeg داخل GitHub Actions، وليس تسجيل فيديو داخل المتصفح.
- تجهيز 3 فيديوهات مراجعة مرشحة من مكتبة القرآن الكاملة (114 سورة و6,236 آية).
- العربية العثمانية + ترجمة Saheeh International الإنجليزية + تلاوة ماهر المعيقلي برواية حفص.
- خلفيات فيديو متحركة من الأصول التي اجتازت بوابة المراجعة، مع تدوير الاختيار.
- مقاطع من سور مختلفة، آيات كاملة، بلا صمت اصطناعي بين الآيات.
- حد أقصى 40 ثانية؛ لا تُقسّم الآية لتلائم المدة.
- حفظ MP4 داخل GitHub Actions Artifact باسم `quran-launcher-full-quran-review`.

## تشغيل Launcher من الهاتف

1. ثبّت GitHub App `Quran Launcher` على المستودع `samiouess-ux/quran-launcher` فقط، مع Repository permission: Actions = Read and write وMetadata = Read-only.
2. تأكد أن Device Flow مفعّل في إعدادات التطبيق.
3. افتح واجهة Launcher واضغط «ربط GitHub».
4. أدخل رمز التحقق الذي يظهر في صفحة GitHub الرسمية.
5. بعد ظهور نجاح الربط، اضغط «شغّل 3 فيديوهات» من نفس الصفحة. الـLauncher يرسل workflow_dispatch للفرع `feature/islamic-tiktok-engine-port` ويتابع ظهور التشغيل.
6. افتح رابط متابعة Actions عند الحاجة، ثم افتح التشغيل الناجح وقسم Artifacts ونزّل `quran-launcher-full-quran-review`.

## ملاحظات الأمان والحدود

- يستخدم Launcher GitHub App Device Flow؛ لا يوجد Client Secret أو Private Key أو Personal Access Token داخل HTML أو المستودع.
- Client ID علني بطبيعته، أما access token وrefresh token فيُحفظان في `sessionStorage` لجلسة المتصفح فقط، ولا يُكتبان إلى ملفات المشروع. إغلاق جلسة المتصفح بالكامل قد يتطلب إعادة الربط.
- هذه النسخة لم يُتحقق بعد من تشغيلها من متصفح الهاتف بحساب المستخدم؛ يلزم تثبيت GitHub App على المستودع وتجربة التفويض ثم dispatch فعلي قبل اعتبارها جاهزة.
- الفيديوهات الثلاثة مخرجات مراجعة وليست محتوى معتمدًا تلقائيًا للنشر. بوابات التحقق البشري وحقوق النص/الترجمة/التسجيل والخلفيات تبقى مغلقة.
- لا يوجد نشر تلقائي على TikTok ولا إرسال إلى Telegram.
- نجاح طلب dispatch (HTTP 204) يعني قبول GitHub لطلب التشغيل، وليس نجاح إنتاج الفيديو. يجب التأكد من نجاح Workflow ووجود Artifact.

## ضوابط ثابتة

- العربية القرآنية مع ترجمة Saheeh International الإنجليزية فقط.
- لا موسيقى؛ تلاوة قرآنية فقط.
- لا اقتطاع للآيات، ولا إضافة صمت اصطناعي بين الآيات.
- لا نشر تلقائي؛ مراجعة المستخدم مطلوبة.
- لا تعديل للمستودع الأصلي `IslamicTikTokAutomation` أو فرع `main`.
- لا تعديل لبوت Telegram أو المجدول أو إعدادات Pages أو credentials ضمن هذا التغيير.
