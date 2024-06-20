import datetime
from django.db import connection

from account.models import GroupPermPerms


def run():
    # Tên bảng trung gian cũ
    old_table_name = 'users_group_perm_perm'

    # Truy vấn trực tiếp bảng trung gian cũ
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT groupperm_id, perm_id FROM {old_table_name}")
        old_relations = cursor.fetchall()

    # Tạo các bản ghi mới trong bảng trung gian mới
    for relation in old_relations:
        group_id, perm_id = relation
        GroupPermPerms.objects.create(
            perm_id=perm_id,
            group_id=group_id,
            allow=True,  # Hoặc giá trị mặc định nào bạn muốn
            created_at=datetime.datetime.utcnow()  # Hoặc timezone.now() nếu không có sẵn
        )
