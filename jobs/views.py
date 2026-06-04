# jobs/views.py
from django.http import JsonResponse
from .models import JobPost
from django.shortcuts import render
from accounts.models import Profile # Profile 모델 임포트
from resumes.models import Experience # Experience 모델 임포트
from django.contrib.auth.decorators import login_required # login_required 데코레이터 임포트
from django.conf import settings # settings 임포트

# 1. 메인 랜딩 페이지 뷰
def index(request):
    return render(request, 'jobs/index.html')

# 2. 사용자 마이 대시보드 뷰
@login_required # dashboard 뷰에 login_required 데코레이터 추가
def dashboard(request):
    user_skills = []
    try:
        profile = request.user.profile
        user_skills = profile.skills.values_list('name', flat=True)
    except Profile.DoesNotExist:
        pass # 프로필이 없는 경우 빈 리스트 유지
    
    context = {
        'user_skills': user_skills
    }
    return render(request, 'jobs/dashboard.html', context)

@login_required # 사용자 로그인 확인
def recommended_jobs(request):
    user = request.user
    user_skills = set()
    
    # 사용자 Profile에서 스킬 정보 가져오기
    try:
        profile = user.profile # related_name 'profile'을 통해 접근
        user_skills = set(profile.skills.values_list('name', flat=True))
    except Profile.DoesNotExist:
        # 사용자 프로필이 아직 없는 경우 처리 (예: 신규 사용자)
        # 현재는 빈 user_skills로 진행하지만, 더 견고한
        # 해결책은 프로필 생성 페이지로 리디렉션하거나 메시지를 표시하는 것입니다.
        pass
        
    # 사용자 스킬이 정의되지 않은 경우 적절한 메시지 반환
    if not user_skills:
        return JsonResponse({
            'status': 'info',
            'message': '프로필에 스킬 정보가 없습니다. 추천을 받으려면 스킬을 추가해주세요.',
            'jobs': []
        }, json_dumps_params={'ensure_ascii': False})

    recommendations = []
    all_jobs = JobPost.objects.prefetch_related('required_skills').all()
    
    # 2. 🛠️ [임시 조치] 아직 DB에 공고 데이터를 넣지 않았다면, 화면 확인용 가짜 데이터를 보여줍니다.
    if not all_jobs.exists():
        return JsonResponse({
            'status': 'success',
            'message': '현재 DB에 공고가 없어서 테스트용 데이터를 보여드립니다.',
            'jobs': [
                {
                    'id': 1,
                    'company_name': '삼성전자',
                    'title': 'Python 백엔드 개발자 대규모 채용',
                    'match_rate': 100,
                    'skills': ['Python', 'Django']
                },
                {
                    'id': 2,
                    'company_name': '네이버',
                    'title': '웹 서비스 풀스택 개발자 모집',
                    'match_rate': 50,
                    'skills': ['Python', 'Vue.js']
                }
            ]
        }, json_dumps_params={'ensure_ascii': False}) # 한글 깨짐 방지
    
    # 3. 실제 DB에 데이터가 존재할 때 작동하는 매칭 로직
    for job in all_jobs:
        job_skills = set(job.required_skills.values_list('name', flat=True))
        
        if not job_skills:
            continue
            
        intersection = user_skills.intersection(job_skills)
        union = user_skills.union(job_skills)
        
        match_rate = int((len(intersection) / len(union)) * 100)
        
        if match_rate >= 50:
            recommendations.append({
                'id': job.id,
                'company_name': job.company_name,
                'title': job.title,
                'match_rate': match_rate,
                'skills': list(job_skills)
            })
            
    recommendations.sort(key=lambda x: x['match_rate'], reverse=True)
    
    return JsonResponse({'jobs': recommendations}, safe=False, json_dumps_params={'ensure_ascii': False})


# jobs/views.py 파일 하단에 추가

# 기존 index, dashboard, recommended_jobs 함수는 그대로 두시고 아래를 추가하세요.

def company_analysis(request):
    # 나중에 만들 html 파일 이름
    return render(request, 'jobs/company.html')

@login_required # 사용자 로그인 확인
def my_spec(request):
    profile = None
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        pass # 프로필이 없는 경우

    experiences = []
    if request.user.is_authenticated:
        experiences = request.user.experiences.all() # related_name 'experiences'

    context = {
        'profile': profile,
        'experiences': experiences
    }
    return render(request, 'jobs/myspec.html', context)