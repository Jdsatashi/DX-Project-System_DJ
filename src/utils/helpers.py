from src.account.models import QuyenHanUser


def create_perm(perm: str, crud: bool):
    if crud:
        create = QuyenHanUser.objects.get_or_create(maQuyenHan=f"create_{perm}", tenQuyen=f"Creating {perm}")
        retrieve = QuyenHanUser.objects.get_or_create(maQuyenHan=f"retrieve_{perm}", tenQuyen=f"Retrieving {perm}")
        get_all = QuyenHanUser.objects.get_or_create(maQuyenHan=f"get_all_{perm}", tenQuyen=f"Getting all {perm}")
        edit = QuyenHanUser.objects.get_or_create(maQuyenHan=f"edit_{perm}", tenQuyen=f"Editing {perm}")
        delete = QuyenHanUser.objects.get_or_create(maQuyenHan=f"delete_{perm}", tenQuyen=f"Deleting {perm}")
    else:
        QuyenHanUser.objects.get_or_create(maQuyenHan=f"{perm}", tenQuyen=f"{perm}")
