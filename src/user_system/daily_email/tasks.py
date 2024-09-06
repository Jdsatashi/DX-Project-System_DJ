import base64
from datetime import datetime, timedelta
from io import BytesIO

from celery import shared_task
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import EmailMessage

from app.logs import app_log
from marketing.order.api.views import generate_order_excel
from marketing.order.models import Order


@shared_task
def send_order_report_email_task(email, subject, context, date_get):
    send_order_report_email(email, subject, context, date_get)


def send_order_report_email(email: list, subject, context, date_get):
    today = datetime.now().date()
    start_date = date_get
    end_date = date_get + timedelta(days=1)
    app_log.info(f"Test date: {start_date} - {end_date}")
    orders = Order.objects.filter(date_company_get__gte=start_date, date_company_get__lt=end_date).exclude(status='deactivate').order_by('-date_get')
    app_log.info(f"Data: {orders.count()} items")
    workbook = generate_order_excel(orders)

    excel_data = BytesIO()
    workbook.save(excel_data)
    excel_data.seek(0)

    # Tạo và render template HTML cho email
    html_content = render_to_string('email/report_mail.html', context)

    # Tạo đối tượng EmailMessage
    email_message = EmailMessage(
        subject=subject,
        body=html_content,
        from_email=settings.EMAIL_HOST_USER,
        to=email,
    )
    email_message.content_subtype = "html"  # Đặt nội dung email là HTML

    # Đính kèm file Excel
    filename = f"Bao_cao_don_hang_{today}.xlsx"
    email_message.attach(filename, excel_data.getvalue(),
                         'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    try:
        result = email_message.send()
        if result == len(email):  # Kiểm tra xem tất cả email đã được gửi thành công chưa
            app_log.info("Email sent successfully to all recipients.")
            return True
        else:
            app_log.warning(f"Email was only sent to {result}/{len(email)} recipients.")
            return False
    except Exception as e:
        app_log.error(f"Failed to send email: {e}")
        return False


def send_report_order_email(email, date_get, use_async: bool):
    context = {
        'subject': f'Báo cáo đơn hàng {date_get}',
        'body_message': 'Đính kèm là báo cáo đơn hàng của bạn.',
    }

    if use_async:
        send_order_report_email_task.apply_async((email, context['subject'], context, date_get), countdown=10)
    else:
        send_order_report_email(email, context['subject'], context, date_get)
