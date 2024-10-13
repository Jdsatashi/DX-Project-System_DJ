import base64

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage

from app.logs import app_log


@shared_task
def send_report_email(nvtt_email, encoded_output_content, file_name):
    try:
        app_log.info(f"__ Sending email.....")
        email = EmailMessage(
            subject=f"Báo cáo toa của đại lý cho NVTT",
            from_email=settings.EMAIL_HOST_USER,
            to=[nvtt_email],
        )
        if encoded_output_content:
            decoded_content = base64.b64decode(encoded_output_content)
            email.attach(file_name, decoded_content,
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            email.send()
        return 'Email sent successfully'
    except Exception as e:
        return str(e)
