import os
import requests
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from jobs.models import JobPost, Skill


class Command(BaseCommand):
    help = "워크넷 OpenAPI를 호출하여 실시간 채용 정보를 가져와 데이터베이스에 동기화합니다."

    def handle(self, *args, **options):
        # 1. API 키 확인
        api_key = os.environ.get("WORKNET_API_KEY")
        if not api_key:
            raise CommandError(
                "오류: .env 파일에 WORKNET_API_KEY가 등록되어 있지 않습니다.\n"
                "키를 등록한 뒤 다시 실행해 주세요."
            )

        self.stdout.write("워크넷 채용정보 OpenAPI로부터 데이터를 가져오는 중...")

        # 2. API 호출을 위한 기본 파라미터
        # 워크24 (고용24) 신규 OpenAPI 엔드포인트 적용
        url = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"
        params = {
            "authKey": api_key,
            "callTp": "L",
            "returnType": "XML",
            "startPage": "1",
            "display": "30",  # 30개의 구인 정보를 수집
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()

            # 3. XML 파싱 시작
            root = ET.fromstring(response.text)

            # 워크넷 API 에러 메시지 체크 (인증 실패 시 xml 루트에 message 또는 error가 담김)
            message_node = root.find(".//message")
            if message_node is not None:
                if "유효" in message_node.text:
                    self.stdout.write(
                        self.style.WARNING(
                            "API 키가 만료되었거나 유효하지 않습니다. UI 테스트를 위해 임시 공고 3개를 생성합니다."
                        )
                    )
                    self._create_dummy_jobs()
                    return
                raise CommandError(f"워크넷 API 서버 오류: {message_node.text}")

            wanted_nodes = root.findall(".//wanted")
            if not wanted_nodes:
                self.stdout.write(
                    self.style.WARNING(
                        "가져온 채용 정보가 없습니다. API 키 상태 또는 파라미터를 점검해 주세요."
                    )
                )
                return

            self.stdout.write(
                f"총 {len(wanted_nodes)}개의 공고 데이터를 확인했습니다. DB 적재를 시작합니다..."
            )

            # 미리 등록되어 있는 Skill 스택 로드 (기술 태깅 매핑용)
            skills = list(Skill.objects.all())
            created_count = 0
            updated_count = 0

            for wanted in wanted_nodes:
                # 4. 개별 필드 추출
                company_name = wanted.findtext("corpNm", "").strip()
                title = wanted.findtext("wantedTitle", "").strip()
                sal_tp_nm = wanted.findtext("salTpNm", "").strip()
                sal = wanted.findtext("sal", "").strip()
                req_spec = wanted.findtext("career", "").strip()  # 경력 정보로 대체
                close_dt = wanted.findtext("closeDt", "").strip()
                info_url = wanted.findtext("wantedInfoUrl", "").strip()

                if not company_name or not title:
                    continue

                # 5. 직무 설명(description) 조립
                description = f"""[워크넷 채용 공고]
- 급여 요건: {sal_tp_nm} {sal}
- 자격 요건: {req_spec}
- 마감 기한: {close_dt}
- 상세 공고 이동: {info_url}

본 공고는 고용노동부 워크넷 OpenAPI 동기화를 통해 생성된 채용 정보입니다."""

                # 6. DB 저장 (동일한 회사명 & 공고 제목이 있다면 기존 데이터 유지 또는 업데이트)
                job, created = JobPost.objects.get_or_create(
                    company_name=company_name,
                    title=title,
                    defaults={"description": description},
                )

                if created:
                    created_count += 1
                else:
                    # 기존 공고의 경우 설명란만 리뉴얼
                    job.description = description
                    job.save()
                    updated_count += 1

                # 7. 기술 스택(Skill) 태깅 처리 (제목과 설명 분석)
                target_text = (title + " " + req_spec).lower()
                for skill in skills:
                    keywords = skill.name.split("/")
                    for keyword in keywords:
                        kw = keyword.strip().lower()
                        if kw and kw in target_text:
                            job.required_skills.add(skill)
                            break

            self.stdout.write(
                self.style.SUCCESS(
                    f"동기화 완료: 신규 공고 {created_count}개 생성, 기존 공고 {updated_count}개 업데이트."
                )
            )

        except requests.exceptions.RequestException as e:
            msg = f"네트워크 통신 중 오류가 발생했습니다: {e}"
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)
        except ET.ParseError as e:
            msg = f"XML 데이터를 분석하는 데 실패했습니다. 응답 결과에 문제가 있을 수 있습니다.\n에러: {e}"
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)
        except Exception as e:
            msg = f"알 수 없는 시스템 오류: {e}"
            self.stdout.write(self.style.ERROR(msg))
            raise CommandError(msg)

    def _create_dummy_jobs(self):
        # API 실패 시 UI를 테스트하기 위해 사람인(Saramin)에서 실제 채용 공고를 스크래핑하여 제공
        self.stdout.write(
            self.style.WARNING(
                "워크넷 API 연동 지연으로 인해 사람인(Saramin)에서 실제 최신 채용 공고를 스크래핑합니다..."
            )
        )

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            self.stdout.write(
                self.style.ERROR(
                    "BeautifulSoup4가 설치되어 있지 않아 임시 더미 데이터를 사용합니다."
                )
            )
            self._create_static_dummy_jobs()
            return

        # cat_kewd=84 (IT) 필터를 제거하고 최신 전체 직무 공고를 가져옵니다.
        url = "https://www.saramin.co.kr/zf_user/jobs/list/domestic"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")

            jobs = soup.select(".list_item")
            if not jobs:
                self.stdout.write(
                    self.style.WARNING(
                        "스크래핑 결과가 없습니다. 임시 더미 데이터를 사용합니다."
                    )
                )
                self._create_static_dummy_jobs()
                return

            skills = list(Skill.objects.all())
            created_count = 0

            for job_node in jobs[:15]:  # 상위 15개 실제 공고 스크래핑
                company_node = job_node.select_one(".company_nm .str_tit")
                title_node = job_node.select_one(".job_tit .str_tit")

                if not company_node or not title_node:
                    continue

                company = company_node.text.strip()
                title = title_node.text.strip()
                link = "https://www.saramin.co.kr" + title_node["href"]

                # 채용 조건 (경력, 학력, 근무지 등)
                conditions = [
                    cond.text.strip() for cond in job_node.select(".job_condition span")
                ]
                cond_text = " / ".join(conditions) if conditions else "회사 내규에 따름"

                # 직무 키워드
                sectors = [sec.text.strip() for sec in job_node.select(".job_sector a")]
                sector_text = ", ".join(sectors)

                description = f"""[웹 스크래핑 채용 공고]
- 자격 요건: {cond_text}
- 직무 분야: {sector_text}
- 상세 공고 이동: {link}

본 공고는 API 접근 제한으로 인해 사람인(Saramin)에서 임시로 수집된 실제 채용 정보입니다."""

                import random

                sizes = ["대기업", "중견기업", "중소기업", "스타트업"]
                assigned_size = random.choice(sizes)

                job, created = JobPost.objects.get_or_create(
                    company_name=company,
                    title=title,
                    defaults={
                        "description": description,
                        "company_size": assigned_size,
                    },
                )

                if created:
                    created_count += 1
                else:
                    job.description = description
                    job.save()

                target_text = (title + " " + sector_text).lower()
                for skill in skills:
                    # standardized skills like '마케팅/광고/홍보' -> split by '/' and check
                    keywords = skill.name.split("/")
                    for keyword in keywords:
                        # Clean keyword
                        kw = keyword.strip().lower()
                        if kw and kw in target_text:
                            job.required_skills.add(skill)
                            break  # add once per skill

            self.stdout.write(
                self.style.SUCCESS(
                    f"UI 테스트를 위한 실제 공고 {created_count}개 스크래핑이 완료되었습니다."
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"스크래핑 중 오류 발생: {e}"))
            self._create_static_dummy_jobs()

    def _create_static_dummy_jobs(self):
        dummy_data = [
            {
                "company": "CJ제일제당",
                "title": "마케팅/브랜드 기획 신입 및 경력",
                "desc": "[고용24 연동 테스트 공고]\n- 급여 요건: 회사 내규에 따름\n- 자격 요건: 마케팅 기획 경험 및 원활한 커뮤니케이션\n- 마감 기한: 2026-12-31",
                "size": "대기업",
                "skills": ["마케팅/광고/홍보", "경영/기획/전략"],
            },
            {
                "company": "삼성물산",
                "title": "B2B 영업/해외영업 신입 채용",
                "desc": "[고용24 연동 테스트 공고]\n- 급여 요건: 회사 내규에 따름\n- 자격 요건: 비즈니스 영어 가능자, 강한 책임감\n- 마감 기한: 2026-11-30",
                "size": "대기업",
                "skills": ["B2B/B2C 영업", "어학/번역/외국어"],
            },
            {
                "company": "카카오뱅크",
                "title": "백엔드/데이터 엔지니어",
                "desc": "[고용24 연동 테스트 공고]\n- 급여 요건: 연봉 6,000만원\n- 자격 요건: 관련 개발 경험자\n- 마감 기한: 2026-10-15",
                "size": "대기업",
                "skills": ["백엔드/서버 개발", "데이터 분석/AI 개발"],
            },
            {
                "company": "LG생활건강",
                "title": "재무/회계팀 결원 충원",
                "desc": "[고용24 연동 테스트 공고]\n- 급여 요건: 회사 내규에 따름\n- 자격 요건: 회계/재무 관련 전공자 또는 자격증 소지자\n- 마감 기한: 2026-10-31",
                "size": "대기업",
                "skills": ["재무/회계/세무"],
            },
        ]

        created_count = 0

        for item in dummy_data:
            job, created = JobPost.objects.get_or_create(
                company_name=item["company"],
                title=item["title"],
                defaults={"description": item["desc"], "company_size": item["size"]},
            )
            if created:
                created_count += 1
                for skill_name in item["skills"]:
                    skill_obj = Skill.objects.filter(name=skill_name).first()
                    if skill_obj:
                        job.required_skills.add(skill_obj)

        self.stdout.write(
            self.style.SUCCESS(
                f"UI 테스트를 위한 임시 공고 {created_count}개 생성이 완료되었습니다."
            )
        )
