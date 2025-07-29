from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import UserManager
import random
import string


def generate_invite_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))


class User(AbstractUser):
    username = None
    phone = models.CharField(_('phone number'), max_length=13, unique=True)

    invite_code = models.CharField(max_length=6, unique=True, blank=True)
    used_invite_code = models.CharField(max_length=6, blank=True, null=True)
    invited_users = models.ManyToManyField('self', symmetrical=False, related_name='invited_by', blank=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.invite_code:
            while True:
                code = generate_invite_code()
                if not User.objects.filter(invite_code=code).exists():
                    self.invite_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone
