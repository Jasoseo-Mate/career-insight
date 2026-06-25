# jobs/views.py
import os
import os
import json
import requests
from bs4 import BeautifulSoup
import urllib.parse
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import JobPost
from django.shortcuts import render
from accounts.models import Profile  # Profile 모델 임포트
from resumes.models import Experience  # Experience 모델 임포트
from django.contrib.auth.decorators import (
    login_required,
)  # login_required 데코레이터 임포트
from django.conf import settings  # settings 임포트

# 1. 메인 랜딩 페이지 뷰


def company_analysis(request):
    return render(request, "jobs/company.html")


def fetch_real_news(keyword, max_count=3):
    url = f"https://search.naver.com/search.naver?where=news&query={urllib.parse.quote(keyword)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    articles = []
    try:
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        news_links = soup.find_all("a", class_="news_tit")
        for a in news_links:
            title = a.get("title") or a.text
            href = a.get("href")
            if title and href:
                articles.append(
                    {
                        "title": title,
                        "url": href,
                        "reason": f"[{keyword}] 관련 최신 동향 파악",
                    }
                )
            if len(articles) >= max_count:
                break
    except Exception as e:
        pass
    return articles


@login_required
@require_POST
def ai_analyze_company(request):
    gmskey = getattr(settings, "GMSKEY", os.environ.get("GMSKEY"))
    if not gmskey:
        return JsonResponse(
            {"status": "error", "message": "GMSKEY 설정이 없습니다."}, status=400
        )

    try:
        body = json.loads(request.body)
        company_name = body.get("company_name", "").strip()
    except Exception:
        company_name = request.POST.get("company_name", "").strip()

    if not company_name:
        return JsonResponse(
            {"status": "error", "message": "기업명을 입력해주세요."}, status=400
        )

    real_articles = fetch_real_news(company_name, max_count=4)

    prompt = f"""당신은 '기업 분석 전문가'입니다. 기업명 "{company_name}"에 대해 심층 분석 리포트를 제공해 주십시오.
[응답 JSON 형식]
{{
  "vision": "비전 요약",
  "ideal_candidate": [
    {{"keyword": "키워드", "desc": "설명"}}
  ],
  "recent_issues": [
    "최근 이슈 1"
  ],
  "interview_tip": "면접 팁",
  "recommended_articles": [
    {{"title": "기사 제목", "search_keyword": "검색어", "reason": "이유"}}
  ]
}}
"""
    url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {gmskey}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {"role": "system", "content": "Return exact JSON only without markdown."},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        res_json = response.json()
        parsed_data = json.loads(res_json["choices"][0]["message"]["content"].strip())

        if real_articles and len(real_articles) > 0:
            parsed_data["recommended_articles"] = real_articles
        else:
            for art in parsed_data.get("recommended_articles", []):
                if "url" not in art and "search_keyword" in art:
                    art["url"] = (
                        f"https://www.google.com/search?tbm=nws&q={urllib.parse.quote(art['search_keyword'])}"
                    )

        return JsonResponse(
            {"status": "success", "data": parsed_data},
            json_dumps_params={"ensure_ascii": False},
        )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def index(request):
    return render(request, "jobs/index.html")


# 2. 사용자 마이 대시보드 뷰
@login_required  # dashboard 뷰에 login_required 데코레이터 추가
def dashboard(request):
    user_skills = []
    try:
        profile = request.user.profile
        user_skills = profile.skills.values_list("name", flat=True)
    except Profile.DoesNotExist:
        pass  # 프로필이 없는 경우 빈 리스트 유지

    context = {"user_skills": user_skills}
    return render(request, "jobs/dashboard.html", context)


@login_required  # 사용자 로그인 확인
def recommended_jobs(request):
    user = request.user
    user_skills = set()

    # 사용자 Profile에서 스킬 정보 가져오기
    try:
        profile = user.profile  # related_name 'profile'을 통해 접근
        user_skills = set(profile.skills.values_list("name", flat=True))
    except Profile.DoesNotExist:
        # 사용자 프로필이 아직 없는 경우 처리 (예: 신규 사용자)
        # 현재는 빈 user_skills로 진행하지만, 더 견고한
        # 해결책은 프로필 생성 페이지로 리디렉션하거나 메시지를 표시하는 것입니다.
        pass

    # 사용자 스킬이 정의되지 않은 경우 적절한 메시지 반환
    if not user_skills:
        return JsonResponse(
            {
                "status": "info",
                "message": "프로필에 스킬 정보가 없습니다. 추천을 받으려면 스킬을 추가해주세요.",
                "jobs": [],
            },
            json_dumps_params={"ensure_ascii": False},
        )

    recommendations = []
    all_jobs = JobPost.objects.prefetch_related("required_skills").all()

    # 2. 🛠️ [임시 조치] 아직 DB에 공고 데이터를 넣지 않았다면, 화면 확인용 가짜 데이터를 보여줍니다.
    if not all_jobs.exists():
        return JsonResponse(
            {
                "status": "success",
                "message": "현재 DB에 공고가 없어서 테스트용 데이터를 보여드립니다.",
                "jobs": [
                    {
                        "id": 1,
                        "company_name": "삼성전자",
                        "title": "Python 백엔드 개발자 대규모 채용",
                        "match_rate": 100,
                        "skills": ["Python", "Django"],
                    },
                    {
                        "id": 2,
                        "company_name": "네이버",
                        "title": "웹 서비스 풀스택 개발자 모집",
                        "match_rate": 50,
                        "skills": ["Python", "Vue.js"],
                    },
                ],
            },
            json_dumps_params={"ensure_ascii": False},
        )  # 한글 깨짐 방지

    # 3. 실제 DB에 데이터가 존재할 때 작동하는 매칭 로직
    for job in all_jobs:
        job_skills = set(job.required_skills.values_list("name", flat=True))

        if not job_skills or not user_skills:
            match_rate = 0
        else:
            intersection = user_skills.intersection(job_skills)
            union = user_skills.union(job_skills)
            match_rate = int((len(intersection) / len(union)) * 100)

        recommendations.append(
            {
                "id": job.id,
                "company_name": job.company_name,
                "title": job.title,
                "match_rate": match_rate,
                "skills": list(job_skills) if job_skills else ["공통"],
            }
        )

    recommendations.sort(key=lambda x: x["match_rate"], reverse=True)

    return JsonResponse(
        {"jobs": recommendations[:10]},
        safe=False,
        json_dumps_params={"ensure_ascii": False},
    )


# jobs/views.py 파일 하단에 추가

# 기존 index, dashboard, recommended_jobs 함수는 그대로 두시고 아래를 추가하세요.


def company_analysis(request):
    # 나중에 만들 html 파일 이름
    return render(request, "jobs/company.html")


@login_required  # 사용자 로그인 확인
def my_spec(request):
    profile = None
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        pass  # 프로필이 없는 경우

    experiences = []
    if request.user.is_authenticated:
        experiences = request.user.experiences.all()  # related_name 'experiences'

    context = {"profile": profile, "experiences": experiences}
    return render(request, "jobs/myspec.html", context)


# 🌟 AI 기반 매칭 및 자소서 메이트 핵심 뷰 구현
import json
import requests
from django.views.decorators.http import require_POST
from resumes.models import CoverLetter


@login_required
def ai_matching(request):
    """
    AI 매칭 및 자소서 메이트 전용 랜딩 페이지를 렌더링합니다.
    """
    return render(request, "jobs/ai_matching.html")


@login_required
@require_POST
def ai_analyze_spec(request):
    """
    사용자의 전체 스펙 정보를 수집하여 SSAFY GMS API (gpt-5.4-nano)를 통해 분석 및 최적 기업을 추천받습니다.
    """
    user = request.user
    gmskey = (
        os.environ.get("GMSKEY") or settings.GMSKEY
        if hasattr(settings, "GMSKEY")
        else os.environ.get("GMSKEY")
    )

    if not gmskey:
        # API 키가 없으면 친절한 경고 반환
        return JsonResponse(
            {
                "status": "error",
                "message": ".env 파일에 GMSKEY가 등록되어 있지 않습니다. 키를 등록한 뒤 시도해 주세요.",
            },
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )

    # 1. 사용자의 DB 데이터 수집 및 문자열 화
    profile_bio = ""
    skills_list = []
    try:
        profile = user.profile
        profile_bio = profile.bio
        skills_list = list(profile.skills.values_list("name", flat=True))
    except Profile.DoesNotExist:
        pass

    educations = user.educations.all()
    edu_text = "\n".join(
        [
            f"- {e.school_name} {e.major} ({e.degree}, {e.start_date}~{e.end_date or '재학중'})"
            for e in educations
        ]
    )

    certificates = user.certificates.all()
    cert_text = "\n".join(
        [
            f"- {c.name} (발급기관: {c.issuer}, 취득일: {c.date_acquired})"
            for c in certificates
        ]
    )

    activities = user.activities.all()
    act_text = "\n".join(
        [
            f"- {a.title}: {a.description} ({a.start_date}~{a.end_date or '진행중'})"
            for a in activities
        ]
    )

    projects = user.projects.all()
    proj_text = "\n".join(
        [f"- {p.title}: {p.description} (URL: {p.url or '없음'})" for p in projects]
    )

    experiences = user.experiences.all()
    exp_text = "\n".join(
        [
            f"- {ex.title} at {ex.company}: {ex.description} ({ex.start_date}~{ex.end_date or '진행중'})"
            for ex in experiences
        ]
    )

    # 2. GMS 프롬프트 구성
    spec_summary = f"""
    [구직자 스펙 정보 요약]
    - 보유 기술 스택: {', '.join(skills_list) if skills_list else '없음'}
    - 한 줄 자기소개: {profile_bio or '없음'}
    
    - 학력 사항:
    {edu_text if edu_text else '없음'}
    
    - 자격증:
    {cert_text if cert_text else '없음'}
    
    - 대외활동:
    {act_text if act_text else '없음'}
    
    - 프로젝트 경험:
    {proj_text if proj_text else '없음'}
    
    - 경력 및 경험:
    {exp_text if exp_text else '없음'}
    """

    prompt = f"""
    당신은 모든 산업 및 직무 분야의 취업 준비생들을 위한 최고의 커리어 컨설턴트 AI입니다.
    아래 구직자의 인적 사항 및 스펙 요약을 바탕으로 프로페셔널한 맞춤 기업 분석 및 매칭을 해 주십시오.
    
    {spec_summary}
    
    다음 2가지 미션을 완벽히 수행해 주세요.
    1. 이 구직자의 전체적인 강점과 장점을 한글 2-3줄 요약평으로 제공하십시오.
    2. 구직자의 주 무기(기술, 전공, 프로젝트, 대외활동 등)를 저격할 수 있는 해당 분야의 대표적인 한국 내 기업(실존 기업 위주) 3곳을 매칭해 추천해 주십시오.
       각 기업별로 다음 구조를 파싱할 수 있게 제공해야 합니다:
       - 기업명 (name)
       - 추천하는 적합 직무 (role, 예: '마케팅 기획', '해외 영업', '데이터 분석가', '인사 담당자' 등)
       - 추천 상세 이유 (reason, 사용자의 스펙 요소를 구체적으로 거론하며 논리적으로 설명)
       - 추천 매칭율 (match_rate, 0~100 사이의 정수)
       - 해당 기업 지원 시 자기소개서에 쓰기 가장 좋은 킬러 문항 2가지 (recommended_questions, 예: '이전 프로젝트에서 매출을 20% 상승시킨 전략은 무엇인가요?', '팀 내 갈등을 해결하고 목표를 달성한 경험')
    
    [응답 조건]
    - 반드시 마크다운 블록(```json) 없이 오직 원시 JSON 데이터만을 반환해야 합니다.
    - JSON의 Key 구조는 정확히 아래의 형식을 만족해 주십시오:
    {{
      "overall_analysis": "전반적인 강점 분석 요약 내용...",
      "recommended_companies": [
        {{
          "name": "기업명",
          "role": "추천 직무",
          "reason": "구체적인 매칭 사유...",
          "match_rate": 88,
          "recommended_questions": ["추천 자소서 질문 문항 1", "추천 자소서 질문 문항 2"]
        }}
      ]
    }}
    """

    # 3. GMS API 호출 (OpenAI Chat Completion 스펙)
    url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {gmskey}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {
                "role": "system",
                "content": "당신은 모든 산업 및 직무 분야의 구직자들을 위한 최고의 커리어 컨설턴트 AI입니다. 반드시 요구하는 형태의 JSON 포맷으로만 응답해야 합니다. 마크다운 기호(예: ```json 등)는 절대 포함하지 마십시오.",
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        res_json = response.json()

        # GMS / OpenAI 결과 텍스트 파싱
        candidate_text = res_json["choices"][0]["message"]["content"]
        parsed_data = json.loads(candidate_text.strip())

        return JsonResponse(
            {"status": "success", "data": parsed_data},
            json_dumps_params={"ensure_ascii": False},
        )

    except Exception as e:
        # 혹시 response_format에 대한 에러가 날 수 있으므로 상세 에러 반환
        return JsonResponse(
            {
                "status": "error",
                "message": f"GMS API 분석 요청 중 오류가 발생했습니다: {str(e)}",
            },
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )


@login_required
@require_POST
def ai_generate_coverletter(request):
    """
    선택된 기업, 직무, 질문 문항과 구직자의 스펙을 조합하여 SSAFY GMS API (gpt-5.4-nano)로 완성도 높은 자소서 초안을 만듭니다.
    """
    user = request.user
    gmskey = (
        os.environ.get("GMSKEY") or settings.GMSKEY
        if hasattr(settings, "GMSKEY")
        else os.environ.get("GMSKEY")
    )

    if not gmskey:
        return JsonResponse(
            {"status": "error", "message": "GMSKEY 설정이 없습니다."}, status=400
        )

    try:
        body = json.loads(request.body)
        company_name = body.get("company_name")
        role = body.get("role")
        question = body.get("question")
    except Exception:
        company_name = request.POST.get("company_name")
        role = request.POST.get("role")
        question = request.POST.get("question")

    if not all([company_name, role, question]):
        return JsonResponse(
            {
                "status": "error",
                "message": "기업명, 직무, 질문 문항은 필수 입력 항목입니다.",
            },
            status=400,
        )

    # 사용자의 스펙 요약 수집
    profile_bio = ""
    skills_list = []
    try:
        profile = user.profile
        profile_bio = profile.bio
        skills_list = list(profile.skills.values_list("name", flat=True))
    except Profile.DoesNotExist:
        pass

    educations = user.educations.all()
    edu_text = "\n".join(
        [f"- {e.school_name} {e.major} ({e.degree})" for e in educations]
    )
    certificates = user.certificates.all()
    cert_text = "\n".join([f"- {c.name}" for c in certificates])
    projects = user.projects.all()
    proj_text = "\n".join([f"- {p.title}: {p.description}" for p in projects])
    experiences = user.experiences.all()
    exp_text = "\n".join(
        [f"- {ex.title} at {ex.company}: {ex.description}" for ex in experiences]
    )

    prompt = f"""
    당신은 취업 준비생의 자소서를 전문적으로 첨삭하고 완성해주는 글쓰기 마스터 AI입니다.
    다음 구직자의 정보와 지원하려는 기업 및 문항 정보를 확인한 뒤, 논리 정연하고 설득력 있는 자기소개서 초안을 작성해 주십시오.
    
    [지원 목표]
    - 기업명: {company_name}
    - 희망 직무: {role}
    - 작성할 자소서 질문 문항: "{question}"
    
    [지원자 스펙 요약]
    - 보유 스킬: {', '.join(skills_list)}
    - 자기소개: {profile_bio}
    - 학력: {edu_text}
    - 자격증: {cert_text}
    - 프로젝트: {proj_text}
    - 경력/경험: {exp_text}
    
    [작성 원칙]
    1. 사람다운 자연스러운 어투: '다각적인', '혁신적인', '이바지하겠습니다' 등 AI 특유의 기계적인 표현을 절대 쓰지 마십시오. 담백한 사람의 문체로 작성하십시오.
    2. 차별화: 지원자의 경험 속 구체적인 의사결정, 수치화된 성과를 1개 이상 끌어와 "이 사람만 쓸 수 있는 문장"을 만드십시오.
    3. 절대 금지 표현: "성실하고 책임감이 강한 사람입니다" 같이 공허한 문장은 사용하지 마십시오. 모든 주장에는 근거가 따라와야 합니다.
    4. 구조: 본론은 'STAR(상황-과제-행동-결과)' 흐름으로 자연스럽게 구성하십시오. 소제목 작성 시 기호 대신 깔끔하게 작성하십시오. (예: [소제목: 매출 300% 상승])
    5. 세련된 강조(Color Highlighting): 생성된 자소서는 서식이 지원되는 HTML 에디터에 출력됩니다. 인사담당자가 스키밍할 때 핵심 수치나 역량이 한눈에 띌 수 있도록 HTML 태그를 적용해 파란색으로 굵게 강조하십시오.
       사용 태그 예시: <strong class="text-secondary font-bold">매출 300% 상승</strong>
       (주의: 너무 많은 단어에 색을 넣지 말고, 핵심 키워드 단위로만 색깔을 입히십시오. 마크다운 별표(**)나 이모지는 절대 사용하지 마십시오.)
    6. 기업 연결: 지원 기업과 지원자의 경험을 억지스럽지 않게 연결하십시오.
    7. 분량 및 톤: 800자 내외, 정중하고 담백한 경어체.
    
    위 원칙을 모두 반영해, 기계가 쓴 티가 나지 않는 '실제 합격자의 깔끔하고 프로페셔널한 자기소개서 초안'을 완성해 주십시오. (마크다운 없이 텍스트 본문에 태그만 포함)
    """

    url = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {gmskey}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-5.4-mini",
        "messages": [
            {
                "role": "system",
                "content": "당신은 취업 준비생의 자소서를 전문적으로 첨삭하고 완성해주는 글쓰기 마스터 AI입니다.",
            },
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        res_json = response.json()

        result_content = res_json["choices"][0]["message"]["content"]
        return JsonResponse(
            {"status": "success", "coverletter_draft": result_content},
            json_dumps_params={"ensure_ascii": False},
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": f"자기소개서 초안 작성 중 오류가 발생했습니다: {str(e)}",
            },
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )


@login_required
@require_POST
def ai_save_coverletter(request):
    """
    AI로 생성하고 다듬은 자기소개서를 DB (CoverLetter 모델)에 성공적으로 저장합니다.
    """
    try:
        body = json.loads(request.body)
        company_name = body.get("company_name")
        role = body.get("role")
        title = body.get("title")
        content = body.get("content")
    except Exception:
        company_name = request.POST.get("company_name")
        role = request.POST.get("role")
        title = request.POST.get("title")
        content = request.POST.get("content")

    if not all([company_name, role, title, content]):
        return JsonResponse(
            {"status": "error", "message": "모든 필드를 정확하게 입력해 주세요."},
            status=400,
        )

    # 1. JobPost FK 매핑 해결을 위한 가상 JobPost 조회 또는 생성
    # CoverLetter 모델의 job_post 필수 제약조건을 우아하게 우회
    job_post, _ = JobPost.objects.get_or_create(
        company_name=company_name,
        title=role,
        defaults={
            "description": f"AI 매칭을 통해 가상으로 생성된 {company_name}의 {role} 채용 공고입니다."
        },
    )

    # 2. CoverLetter 생성 및 저장
    try:
        cover_letter = CoverLetter.objects.create(
            user=request.user, job_post=job_post, title=title, content=content
        )
        return JsonResponse(
            {
                "status": "success",
                "message": f"{company_name} - {role} 자기소개서가 성공적으로 저장되었습니다!",
                "id": cover_letter.id,
            },
            json_dumps_params={"ensure_ascii": False},
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": f"자기소개서 저장 중 오류가 발생했습니다: {str(e)}",
            },
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )


@login_required
def sync_worknet_jobs(request):
    """
    관리자 또는 사용자의 요청에 의해 워크넷 공고 데이터를 데이터베이스와 싱크합니다.
    """
    api_key = os.environ.get("WORKNET_API_KEY")
    if not api_key:
        return JsonResponse(
            {
                "status": "error",
                "message": "서버에 WORKNET_API_KEY 설정이 정의되어 있지 않습니다. .env를 확인해 주세요.",
            },
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )

    try:
        from django.core.management import call_command

        # call_command를 사용해 fetch_worknet_jobs 커맨드 실행
        call_command("fetch_worknet_jobs")

        current_count = JobPost.objects.count()
        return JsonResponse(
            {
                "status": "success",
                "message": "성공적으로 워크넷 채용 공고가 최신 상태로 동기화되었습니다!",
                "current_total": current_count,
            },
            json_dumps_params={"ensure_ascii": False},
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": f"동기화 작업 수행 중 오류가 발생했습니다: {str(e)}",
            },
            status=500,
            json_dumps_params={"ensure_ascii": False},
        )
