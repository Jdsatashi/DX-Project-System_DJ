from rest_framework import serializers


def split_data(data):
    restrict = data.pop('restrict', False)
    allow_actions = data.pop('allow_actions', None)
    allow_nhom = data.pop('allow_nhom', None)
    restrict_nhom = data.pop('restrict_nhom', None)
    allow_users = data.pop('allow_users', None)
    restrict_users = data.pop('restrict_users', None)
    quyen_data = {
        "restrict": restrict,
        "allow_actions": allow_actions,
        "allow_nhom": allow_nhom,
        "restrict_nhom": restrict_nhom,
        "allow_users": allow_users,
        "restrict_users": restrict_users,
    }
    return data, quyen_data


class BaseRestrictSerializer(serializers.ModelSerializer):
    # Get field for create quyen
    restrict = serializers.BooleanField(required=False)
    allow_actions = serializers.ListField(child=serializers.CharField(), required=False)
    allow_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_nhom = serializers.ListField(child=serializers.CharField(), required=False)
    allow_users = serializers.ListField(child=serializers.CharField(), required=False)
    restrict_users = serializers.ListField(child=serializers.CharField(), required=False)
