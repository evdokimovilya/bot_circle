from django.db import models

from apps.user_profile.models import Profile

class ProfileVideoNote(models.Model):
    class SentStatus(models.TextChoices):
        WAITING = 'waiting'
        APPROVED = 'approved'
        SENT = 'sent'

    profile = models.ForeignKey(Profile, related_name="profile_video_notes", on_delete=models.CASCADE)
    file = models.FileField(upload_to='videos', verbose_name='кружок пользователя', null=True)
    file_id = models.TextField()
    created_at = models.DateTimeField(verbose_name='дата отправки', auto_now_add=True)
    status = models.CharField(choices=SentStatus.choices, default=SentStatus.WAITING, max_length=100)
    class Meta:
        verbose_name = "Кружок пользователя"
        verbose_name_plural = "Кружки пользователей"

class PublicVideoMessage(models.Model):
    profile_from = models.ForeignKey(Profile, related_name='profile_from_messages', on_delete=models.CASCADE)
    profile_to = models.ForeignKey(Profile, related_name='profile_to', on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name='дата отправки', auto_now_add=True)
    video = models.ForeignKey(ProfileVideoNote, related_name='video_messages', on_delete=models.CASCADE)
    class Meta:
        verbose_name = "Публичные кружочки"

class Poll(models.Model):
    question = models.CharField(max_length=255, verbose_name='вопрос для голосования')
    created_at = models.DateTimeField(verbose_name='дата создания', auto_now_add=True)
    sent = models.BooleanField(default=False)
    telegram_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "голосование"
        verbose_name_plural = "голосования"


class PollOption(models.Model):
    question = models.ForeignKey(
        Poll, 
        on_delete=models.CASCADE, 
        verbose_name='вопрос для голосвания',
        related_name='poll_options'
        )
    text = models.CharField(max_length=255, verbose_name='текст')

    class Meta:
        verbose_name = "Опция голосования"
        verbose_name_plural = "Опции голосований"