from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings  # settings 임포트
from django.contrib.auth.decorators import login_required
from .models import Profile
from jobs.models import Skill  # 프로필 내 스킬 관리에 필요
from django.contrib.auth import authenticate, login, logout  # 인증 기능 임포트
from django.contrib.auth.forms import AuthenticationForm  # 인증 폼 임포트
from .forms import CustomUserCreationForm  # 사용자 정의 회원가입 폼 임포트

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Profile, Education, Certificate, Activity, Project
from .forms import (
    ProfileForm,
    EducationForm,
    CertificateForm,
    ActivityForm,
    ProjectForm,
)


@login_required
def profile_dashboard(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    educations = Education.objects.filter(user=request.user)
    certificates = Certificate.objects.filter(user=request.user)
    activities = Activity.objects.filter(user=request.user)
    projects = Project.objects.filter(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile_dashboard")
    else:
        form = ProfileForm(instance=profile)

    context = {
        "form": form,
        "profile": profile,
        "educations": educations,
        "certificates": certificates,
        "activities": activities,
        "projects": projects,
        "all_skills": Skill.objects.all(),
    }
    return render(request, "accounts/profile_dashboard.html", context)


# --- Education CRUD Views ---


class EducationListView(LoginRequiredMixin, ListView):
    model = Education
    template_name = "accounts/education_list.html"

    def get_queryset(self):
        return Education.objects.filter(user=self.request.user)


class EducationCreateView(LoginRequiredMixin, CreateView):
    model = Education
    form_class = EducationForm
    template_name = "accounts/education_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class EducationUpdateView(LoginRequiredMixin, UpdateView):
    model = Education
    form_class = EducationForm
    template_name = "accounts/education_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


class EducationDeleteView(LoginRequiredMixin, DeleteView):
    model = Education
    template_name = "accounts/education_confirm_delete.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


# --- Certificate CRUD Views ---


class CertificateListView(LoginRequiredMixin, ListView):
    model = Certificate
    template_name = "accounts/certificate_list.html"

    def get_queryset(self):
        return Certificate.objects.filter(user=self.request.user)


class CertificateCreateView(LoginRequiredMixin, CreateView):
    model = Certificate
    form_class = CertificateForm
    template_name = "accounts/certificate_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CertificateUpdateView(LoginRequiredMixin, UpdateView):
    model = Certificate
    form_class = CertificateForm
    template_name = "accounts/certificate_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


class CertificateDeleteView(LoginRequiredMixin, DeleteView):
    model = Certificate
    template_name = "accounts/certificate_confirm_delete.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


# --- Activity CRUD Views ---


class ActivityListView(LoginRequiredMixin, ListView):
    model = Activity
    template_name = "accounts/activity_list.html"

    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)


class ActivityCreateView(LoginRequiredMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = "accounts/activity_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = "accounts/activity_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    model = Activity
    template_name = "accounts/activity_confirm_delete.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


# --- Project CRUD Views ---


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "accounts/project_list.html"

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "accounts/project_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "accounts/project_form.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = "accounts/project_confirm_delete.html"
    success_url = reverse_lazy("accounts:profile_dashboard")


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # settings.LOGIN_REDIRECT_URL로 리디렉션
                return redirect(
                    settings.LOGIN_REDIRECT_URL
                )  # settings.LOGIN_REDIRECT_URL로 리디렉션
            else:
                form.add_error(None, "잘못된 사용자 이름 또는 비밀번호입니다.")
    else:
        form = AuthenticationForm()
    return render(request, "accounts/login.html", {"form": form})


@login_required
def user_logout(request):
    logout(request)
    # settings.LOGOUT_REDIRECT_URL로 리디렉션
    return redirect(
        settings.LOGOUT_REDIRECT_URL
    )  # settings.LOGOUT_REDIRECT_URL로 리디렉션


def user_signup(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"  # 백엔드 명시
            login(request, user)  # 회원가입 후 자동 로그인
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


import json
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import os


@login_required
@require_POST
def ai_recommend_skills(request):
    """
    사용자의 학력, 대외활동, 자격증, 프로젝트 스펙을 바탕으로
    DB에 존재하는 Skill 중 적합한 것을 추천합니다.
    """
    user = request.user
    gmskey = os.environ.get("GMSKEY") or getattr(settings, "GMSKEY", None)

    if not gmskey:
        return JsonResponse(
            {"status": "error", "message": "GMSKEY 설정이 없습니다."}, status=400
        )

    # 사용자 스펙 수집
    educations = "\n".join(
        [f"- {e.school_name} {e.major} ({e.degree})" for e in user.educations.all()]
    )
    certificates = "\n".join(
        [f"- {c.name} ({c.issuer})" for c in user.certificates.all()]
    )
    activities = "\n".join(
        [f"- {a.title}: {a.description}" for a in user.activities.all()]
    )
    projects = "\n".join([f"- {p.title}: {p.description}" for p in user.projects.all()])

    if not any([educations, certificates, activities, projects]):
        return JsonResponse(
            {
                "status": "info",
                "message": "스펙 정보(학력, 자격증, 대외활동, 프로젝트)를 먼저 추가해주세요.",
                "recommended_skill_ids": [],
            }
        )

    all_skills = list(Skill.objects.values("id", "name"))
    skills_context = ", ".join([f"{s['id']}:{s['name']}" for s in all_skills])

    prompt = f"""
    당신은 커리어 컨설턴트 AI입니다. 구직자가 작성한 스펙(학력, 자격증, 대외활동, 프로젝트)을 분석하여,
    아래 목록에 있는 '보유 가능성이 높은 스킬'을 추천해 주십시오.

    [구직자 스펙]
    - 학력: {educations or '없음'}
    - 자격증: {certificates or '없음'}
    - 대외활동: {activities or '없음'}
    - 프로젝트: {projects or '없음'}

    [선택 가능한 스킬 목록 (ID:이름)]
    {skills_context}

    [지시사항]
    위 스킬 목록 중에서 구직자의 스펙과 연관성이 높은 스킬의 ID만 배열 형태로 반환하십시오.
    반드시 마크다운 없이 순수 JSON 배열만 반환하십시오.
    예시: [1, 5, 12]
    """

    url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {gmskey}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-nano",
        "messages": [
            {
                "role": "system",
                "content": "You are a career consultant. Return only a JSON array of integers representing skill IDs.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_object"
        },  # Wait, to return array, we can wrap it in an object like {"ids": [1,2,3]}
    }

    # 수정: json_object를 위해 포맷 변경
    payload["messages"][0][
        "content"
    ] = 'You are a career consultant. Return a JSON object with a single key "ids" containing an array of integers representing skill IDs. Example: {"ids": [1, 2, 3]}'

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        res_json = response.json()

        candidate_text = res_json["choices"][0]["message"]["content"]
        parsed_data = json.loads(candidate_text.strip())
        recommended_ids = parsed_data.get("ids", [])

        return JsonResponse(
            {"status": "success", "recommended_skill_ids": recommended_ids}
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
