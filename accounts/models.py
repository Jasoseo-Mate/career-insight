from django.db import models
from django.conf import settings
from jobs.models import Skill # Import Skill model

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    education = models.CharField(max_length=100)          # 학력 정보
    language_score = models.IntegerField(default=0)       # 어학 성적 점수
    skills = models.ManyToManyField(Skill, related_name='users_with_skill')  # 보유 기술 스택

    def __str__(self):
        return f'{self.user.username}\'s Profile'
