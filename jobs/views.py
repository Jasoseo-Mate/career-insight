# jobs/views.py
from django.http import JsonResponse
from .models import JobPost
from django.shortcuts import render


# 1. 메인 랜딩 페이지 뷰
def index(request):
    return render(request, 'jobs/index.html')

# 2. 사용자 마이 대시보드 뷰
def dashboard(request):
    return render(request, 'jobs/dashboard.html')

# 💡 로그인 문지기(@login_required)는 완전히 제외했습니다.
def recommended_jobs(request):
    
    # 1. 🛠️ [임시 조치] 로그인 기능이 없으므로, 내 스킬셋을 강제로 지정합니다.
    user_skills = {'Python', 'Django'}  
    
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

def my_spec(request):
    # 나중에 만들 html 파일 이름
    return render(request, 'jobs/myspec.html')