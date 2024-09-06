from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMessage
from marketing.order.api.views import generate_order_excel
from marketing.order.models import Order
from user_system.daily_email.models import EmailDetail, UserGetMail
from utils.constants import mail_type
from utils.helpers import local_time


def send_daily_email(date_get):
    email_detail = EmailDetail.objects.filter(email_type=mail_type.report_order).first()

    user_get_mails = UserGetMail.objects.filter(email_detail=email_detail)

    orders = Order.objects.filter(date_company_get=date_get).exclude(status='deactivate').order_by('-date_get')

    workbook = generate_order_excel(orders)

    excel_data = BytesIO()
    workbook.save(excel_data)
    excel_data.seek(0)

    context = {
        'subject': email_detail.name,
        'body_message': email_detail.description,
    }

    emails = [user_get_mail.user.email for user_get_mail in user_get_mails
              if user_get_mail.user.email and user_get_mail.user.email != '']

    send_bulk_email(emails, context, date_get, excel_data)

    # Cập nhật last_sent cho từng user
    for user_get_mail in user_get_mails:
        user_get_mail.last_sent = local_time()
        user_get_mail.save()


def send_bulk_email(emails, context, date_get, excel_data):
    email = EmailMessage(
        subject=context['subject'],
        body=context['body_message'],
        from_email=settings.EMAIL_HOST_USER,
        to=emails,
    )
    file_name = f"Báo cáo {date_get}.xlsx"
    email.attach(file_name, excel_data.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    email.send()
