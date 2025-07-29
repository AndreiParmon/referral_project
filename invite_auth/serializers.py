from rest_framework import serializers

from invite_auth.models import User


class RequestCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)


class VerifyCodeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=13)
    code = serializers.CharField(max_length=4)


class ProfileSerializer(serializers.ModelSerializer):
    activated_invite_code = serializers.CharField(source='used_invite_code', allow_blank=True)
    invited_users = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('phone', 'invite_code', 'activated_invite_code', 'invited_users')

    def get_invited_users(self, obj):
        return [user.phone for user in obj.invited_users.all()]


class ActivateInviteCodeSerializer(serializers.Serializer):
    invite_code = serializers.CharField(max_length=6)

    def validate_invite_code(self, value):
        if len(value) != 6:
            raise serializers.ValidationError("Инвайт-Код должен быть длиной 6 символов.")

        try:
            user = User.objects.get(invite_code=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Инфайт-код не существует.")

        return value
