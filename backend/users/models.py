from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='followers'
    )

    class Meta:
        unique_together = ['user', 'author']

    def __str__(self):
        return f"{self.user.username} подписан на {self.author.username}"
