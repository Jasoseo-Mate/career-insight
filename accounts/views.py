from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings # settings 임포트
from django.contrib.auth.decorators import login_required
from .models import Profile
from jobs.models import Skill # 프로필 내 스킬 관리에 필요
from django.contrib.auth import authenticate, login, logout # 인증 기능 임포트
from django.contrib.auth.forms import AuthenticationForm # 인증 폼 임포트
from .forms import CustomUserCreationForm # 사용자 정의 회원가입 폼 임포트

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Education, Certificate, Activity, Project
from .forms import ProfileForm, EducationForm, CertificateForm, ActivityForm, ProjectForm

@login_required
def profile_dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    educations = Education.objects.filter(user=request.user)
    certificates = Certificate.objects.filter(user=request.user)
    activities = Activity.objects.filter(user=request.user)
    projects = Project.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile_dashboard')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'educations': educations,
        'certificates': certificates,
        'activities': activities,
        'projects': projects,
        'all_skills': Skill.objects.all(),
    }
    return render(request, 'accounts/profile_dashboard.html', context)

# --- Education CRUD Views ---

class EducationListView(LoginRequiredMixin, ListView):
    model = Education
    template_name = 'accounts/education_list.html'
    
    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)

class EducationCreateView(LoginRequiredMixin, CreateView):
    model = Education
    form_class = EducationForm
    template_name = 'accounts/education_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class EducationUpdateView(LoginRequiredMixin, UpdateView):
    model = Education
    form_class = EducationForm
    template_name = 'accounts/education_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

class EducationDeleteView(LoginRequiredMixin, DeleteView):
    model = Education
    template_name = 'accounts/education_confirm_delete.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

# --- Certificate CRUD Views ---

class CertificateListView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = 'accounts/certificate_list.html'
    
    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)

class CertificateCreateView(LoginRequiredMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'accounts/certificate_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class CertificateUpdateView(LoginRequiredMixin, UpdateView):
    model = Certificate
    form_class = CertificateForm
    template_name = 'accounts/certificate_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

class CertificateDeleteView(LoginRequiredMixin, DeleteView):
    model = Certificate
    template_name = 'accounts/certificate_confirm_delete.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

# --- Activity CRUD Views ---

class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = 'accounts/activity_list.html'
    
    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)

class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'accounts/activity_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'accounts/activity_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = 'accounts/activity_confirm_delete.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

# --- Project CRUD Views ---

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'accounts/project_list.html'
    
    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'accounts/project_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'accounts/project_form.html'
    success_url = reverse_lazy('accounts:profile_dashboard')

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'accounts/project_confirm_delete.html'
    success_url = reverse_lazy('accounts:profile_dashboard')




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
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend' # 백엔드 명시
            login(request, user) # 회원가입 후 자동 로그인
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

