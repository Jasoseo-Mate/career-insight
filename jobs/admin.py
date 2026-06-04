# jobs/admin.py
from django.contrib import admin
from .models import Skill, JobPost

# 관리자 페이지에서 데이터를 관리할 수 있도록 모델 등록
admin.site.register(Skill)

admin.site.register(JobPost)