from rest_framework_simplejwt.exceptions import TokenError

from account.models import RefreshToken
from rest_framework_simplejwt.tokens import RefreshToken as RestRefreshToken, AccessToken

from app.logs import app_log


def deactivate_user_token(user):
    token_obj = RefreshToken.objects.filter(user=user, status="active").first()
    # Update deactivate other activate token
    if token_obj:
        token_obj.status = "expired"
        token_obj.save()
        _token = RestRefreshToken(token_obj.refresh_token)
        _token.blacklist()


def deactivate_user_phone_token(user, phone):
    token_obj = RefreshToken.objects.filter(user=user, phone_number=phone, status="active").first()
    # Update deactivate other activate token
    if token_obj:
        try:
            token_obj.status = "expired"
            token_obj.save()
            _token = RestRefreshToken(token_obj.refresh_token)
            _token.blacklist()
        except TokenError:
            app_log.warning(f"deactive user phone token error: {phone}")
            pass
