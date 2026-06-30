# Converge for 002-consolidated-installer

## ما تم إغلاقه

| العنصر | الحالة | ملاحظات |
|--------|--------|----------|
| `scripts/CHECK_HEALTH.bat` | ✅ محذوف | تم دمج الفحص الصحي داخل `ARGUS_INSTALLER.ps1`. |
| `INSTALL.bat` موجه إلى `scripts/INSTALL_EVERYTHING.ps1` | ✅ محدث | الآن يشير إلى `scripts/ARGUS_INSTALLER.ps1`. |
| مراجع `CHECK_HEALTH.bat` في `LAUNCH_CLI.bat` و `LAUNCH_STUDIO.bat` | ✅ محدثة | تم تعديلها لاستخدام الأمر `health` أو `INSTALL.bat health`. |
| ملفات `.bat` القديمة في `Setup/` | ✅ مؤرشفة في `archive/` | تركت للغرض التصحيحي فقط. |

## ما يزال مفتوحًا

- إضافة خيار `-WhatIf` للسكريبت. 
- إنشاء CI workflow لتشغيل اختبارات Pester. 
- تحديث وثائق `README.md` لتوضيح الاستخدام الجديد.
