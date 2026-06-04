from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/update/', views.profile_update, name='profile_update'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('signup/', views.user_signup, name='signup'),
]
