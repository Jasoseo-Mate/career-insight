import os
import requests
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from jobs.models import JobPost, Skill

class Command(BaseCommand):
    help = '워크넷 OpenAPI를 호출하여 실시간 채용 정보를 가져와 데이터베이스에 동기화합니다.'

    def handle(self, *args, **options):
        # 1. API 키 확인
        api_key = os.environ.get('WORKNET_API_KEY')
        if not api_key:
            raise CommandError(
                '오류: .env 파일에 WORKNET_API_KEY가 등록되어 있지 않습니다.\n'
                '키를 등록한 뒤 다시 실행해 주세요.'
            )

        self.stdout.write('워크넷 채용정보 OpenAPI로부터 데이터를 가져오는 중...')
        
        # 2. API 호출을 위한 기본 파라미터
        url = "http://openapi.work.go.kr/opi/opi/opia/wantedApi.do"
        params = {
            "authKey": api_key,
            "callTp": "L",
            "returnType": "XML",
            "startPage": "1",
            "display": "30"  # 30개의 구인 정보를 수집
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # 3. XML 파싱 시작
            root = ET.fromstring(response.text)
            
            # 워크넷 API 에러 메시지 체크 (인증 실패 시 xml 루트에 message 또는 error가 담김)
            message_node = root.find('.//message')
            if message_node is not None:
                raise CommandError(f"워크넷 API 서버 오류: {message_node.text}")

            wanted_nodes = root.findall('.//wanted')
            if not wanted_nodes:
                self.stdout.write(self.style.WARNING(
                    "가져온 채용 정보가 없습니다. API 키 상태 또는 파라미터를 점검해 주세요."
                ))
                return

            self.stdout.write(f"총 {len(wanted_nodes)}개의 공고 데이터를 확인했습니다. DB 적재를 시작합니다...")

            # 미리 등록되어 있는 Skill 스택 로드 (기술 태깅 매핑용)
            skills = list(Skill.objects.all())
            created_count = 0
            updated_count = 0

            for wanted in wanted_nodes:
                # 4. 개별 필드 추출
                company_name = wanted.findtext('company', '').strip()
                title = wanted.findtext('title', '').strip()
                sal_tp_nm = wanted.findtext('salTpNm', '').strip()
                sal = wanted.findtext('sal', '').strip()
                req_spec = wanted.findtext('reqSpec', '').strip()
                close_dt = wanted.findtext('closeDt', '').strip()
                info_url = wanted.findtext('wantedInfoUrl', '').strip()

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
                    defaults={'description': description}
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
                    skill_name_lower = skill.name.lower()
                    # 예: 'python'이 제목에 있으면 매핑
                    if skill_name_lower in target_text:
                        job.required_skills.add(skill)

            self.stdout.write(self.style.SUCCESS(
                f"동기화 완료: 신규 공고 {created_count}개 생성, 기존 공고 {updated_count}개 업데이트."
            ))

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
