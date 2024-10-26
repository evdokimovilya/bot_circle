from django.db import models
from django.apps import apps

class Profile(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    has_limit = models.BooleanField(default=True)
    block_bot = models.BooleanField(default=False)
    nickname = models.CharField(max_length=15, blank=True, null=True)


    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return self.get_username()

    def get_username(self):
        return f"{self.telegram_id}"
    
    def get_or_create_profile(self, telegram_id):
        if not Profile.objects.filter(telegram_id=telegram_id):
            profile = Profile.objects.create(
                telegram_id=telegram_id
                )
        else:
            profile = Profile.objects.get(telegram_id=telegram_id)
        return profile