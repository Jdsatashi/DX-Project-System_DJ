from datetime import time

from django.db import models

from account.models import User
from utils.constants import mail_type


# Create your models here.
class EmailDetail(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    email_type = models.CharField(max_length=255, unique=True)
    # template_name = models.CharField(max_length=255, null=False, help_text="Tên file template HTML cho loại email
    # này") frequency = models.CharField( max_length=20, choices=[('daily', 'Hàng ngày'), ('weekly', 'Hàng tuần'),
    # ('monthly', 'Hàng tháng')], default='daily' )
    note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class UserGetMail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_get_mail')
    email_detail = models.ForeignKey(EmailDetail, on_delete=models.CASCADE, related_name='user_get_mail')

    last_sent = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'email_detail')


def create_auto_mail():
    if not EmailDetail.objects.filter(email_type=mail_type.report_order).exists():
        detail = EmailDetail.objects.create(name='báo cáo toa mỗi ngày',
                                            description='Báo cáo các toa thuốc phát sinh trong ngày',
                                            email_type=mail_type.report_order)
    if not EmailDetail.objects.filter(email_type=mail_type.report_nvtt).exists():
        detail2 = EmailDetail.objects.create(name='báo cáo toa mỗi ngày cho nvtt',
                                             description='Báo cáo các toa thuốc phát sinh trong ngày',
                                             email_type=mail_type.report_nvtt)
        nvtt_get_mails = User.objects.filter(group_user__name='nvtt')
        add_nvtt = detail2.user_get_mail.add(nvtt_get_mails)
