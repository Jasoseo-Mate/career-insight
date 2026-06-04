from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings # settings 임포트
from django.contrib.auth.decorators import login_required
from .models import Profile
from jobs.models import Skill # 프로필 내 스킬 관리에 필요
from django.contrib.auth import authenticate, login, logout # 인증 기능 임포트
from django.contrib.auth.forms import AuthenticationForm # 인증 폼 임포트

@login_required
def profile_update(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    # 현재는 템플릿만 렌더링합니다. 나중에 폼 처리를 추가할 예정입니다.
    context = {
        'profile': profile,
        'all_skills': Skill.objects.all() # 선택을 위해 모든 스킬을 템플릿으로 전달
    }
    return render(request, 'accounts/profile_form.html', context)

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # settings.LOGIN_REDIRECT_URL로 리디렉션
                return redirect(settings.LOGIN_REDIRECT_URL) # settings.LOGIN_REDIRECT_URL로 리디렉션
            else:
                form.add_error(None, '잘못된 사용자 이름 또는 비밀번호입니다.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    # settings.LOGOUT_REDIRECT_URL로 리디렉션
    return redirect(settings.LOGOUT_REDIRECT_URL) # settings.LOGOUT_REDIRECT_URL로 리디렉션

def user_signup(request):
    # 실제 회원가입 로직 (폼 처리 등)은 나중에 구현
    return render(request, 'accounts/signup.html')

