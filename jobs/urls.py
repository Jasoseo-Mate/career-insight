# jobs/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # 기존에 있던 것들
    path('', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommended/', views.recommended_jobs, name='recommended_jobs'),
    
    # 💡 새로 추가된 메뉴 이동용 URL (여기에 등록된 name을 HTML에서 {% url 'name' %}으로 부릅니다)
    path('company/', views.company_analysis, name='company_analysis'),
    path('myspec/', views.my_spec, name='my_spec'),
]