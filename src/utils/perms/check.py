from account.models import Perm, UserPerm


def perm_exist(perm_name: str):
    # Validate perm is dictionary and perm has value
    if not isinstance(perm_name, str) or perm_name is None:
        raise ValueError("perm must be a string \"permission\".")

    q = Perm.objects.filter(name=perm_name)
    return q.first() if q.exists() else None


def user_has_perm(user, perm_name: str):
    # Check if user
    has_obj_perm = user.perm_user.filter(name__icontains=perm_name)
    if has_obj_perm.exists():
        for perm in has_obj_perm:
            check = user.is_allow(perm.name)
            if check:
                return check
    # Get group object permission
    obj_group = user.group_user.filter(perm__name__icontains=perm_name).first()
    if obj_group is not None:
        obj_group_perm = obj_group.perm.filter(name__icontains=perm_name)
        if obj_group_perm.exists():
            for perm in obj_group_perm:
                check = user.is_group_has_perm(perm.name)
                if check:
                    return check


# def user_object_perm(user, perm):
#     all_permissions = user.get_all_allow_perms()
#     allow_list_id = []
#
#     # Get all price list ids which required permissions
#     perms_content = Perm.objects.filter(name__icontains=perm)
#     print(f"Check perm content: {perms_content}")
#     perm_list_ids = {v.object_id for v in perms_content if v.object_id}
#
#     # Get all price list ids which user has permissions
#     for perm in all_permissions:
#         if perm.startswith('list' + '_' + perm):
#             _, object_id = perm.rsplit('_', 1)
#             allow_list_id.append(object_id)
#     print(f"allow_list_id: {allow_list_id}")
#     print(f"perm_list_ids: {perm_list_ids}")
#     allow_list_id = list(perm_list_ids - set(allow_list_id))
#     return len(allow_list_id) > 0
