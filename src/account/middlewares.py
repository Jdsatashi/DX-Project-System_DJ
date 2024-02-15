# custom_authentication.py
from django.contrib.auth.middleware import MiddlewareMixin
from django.utils.functional import SimpleLazyObject
from django.contrib.auth.models import AnonymousUser


class CustomAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'user'), (
            "The CustomAuthenticationMiddleware requires authentication middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: self.get_user(request))

    def get_user(self, request):
        if not hasattr(request, '_cached_user'):
            request._cached_user = self._get_user(request)
        return request._cached_user

    def _get_user(self, request):
        user = request.user if request.user.is_authenticated else AnonymousUser()
        if user.is_authenticated:
            user_permissions = set(user.get_all_permissions())
            for role in user.role_set.all():
                user_permissions.update(role.permissions.values_list('codename', flat=True))
            user.user_permissions = user_permissions
        return user
