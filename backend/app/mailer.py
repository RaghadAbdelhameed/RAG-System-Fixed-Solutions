import ssl
import smtplib
from email.message import EmailMessage

from .config import settings


def send_temp_password_email(to_email: str, full_name: str, temp_password: str):
    subject = "بيانات الدخول الخاصة بك - KnowledgeHub"
    body = f"""
    <div dir="rtl" style="font-family: Tahoma, Arial, sans-serif;">
      <p>مرحباً {full_name}،</p>
      <p>تم إنشاء حساب لك على منصة KnowledgeHub.</p>
      <p><b>كلمة المرور المؤقتة:</b> {temp_password}</p>
      <p>الرجاء تسجيل الدخول وتغيير كلمة المرور فوراً من هنا:
         <a href="{settings.APP_BASE_URL}/frontend/change_password.html">تغيير كلمة المرور</a>
      </p>
    </div>
    """
    if not (settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASS):
        print(f"[MOCK EMAIL] to={to_email}\nsubject={subject}\n{body}")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content("يرجى فتح هذه الرسالة ببرنامج بريد يدعم HTML.")
    msg.add_alternative(body, subtype="html")

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls(context=ctx)
        server.login(settings.SMTP_USER, settings.SMTP_PASS)
        server.send_message(msg)
