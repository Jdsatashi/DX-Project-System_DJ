from rest_framework_simplejwt.tokens import AccessToken

from account.models import Perm, UserPerm, User
from app.logs import app_log


def perm_exist(perm_name: str):
    # Validate perm is dictionary and perm has value
    q = Perm.objects.filter(name=perm_name)
    return q.first()


def user_id_from_token(token):
    try:
        decoded_data = AccessToken(token)
        # Lấy user_id từ payload
        user_id = decoded_data['user_id']
        return user_id
    except Exception as e:
        app_log.info(f"Error decoding token: {str(e)}")
        return None


def get_user_by_token(access_tokne):
    user_id = user_id_from_token(access_tokne)
    if user_id:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            app_log.info("User does not exist.")
            raise ValueError({"message": "User from Token does not exist."})
    raise ValueError({"message": "Token is invalid."})


# def user_object_perm(user, perm):
#     all_permissions = user.get_all_allow_perms()
#     allow_list_id = []
#
#     # Get all price list ids which required permissions
#     perms_content = Perm.objects.filter(name__icontains=perm)
#     app_log.info(f"Check perm content: {perms_content}")
#     perm_list_ids = {v.object_id for v in perms_content if v.object_id}
#
#     # Get all price list ids which user has permissions
#     for perm in all_permissions:
#         if perm.startswith('list' + '_' + perm):
#             _, object_id = perm.rsplit('_', 1)
#             allow_list_id.append(object_id)
#     app_log.info(f"allow_list_id: {allow_list_id}")
#     app_log.info(f"perm_list_ids: {perm_list_ids}")
#     allow_list_id = list(perm_list_ids - set(allow_list_id))
#     return len(allow_list_id) > 0
