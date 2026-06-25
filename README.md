# Jasoseo Mate (자소서 메이트)

이 프로젝트는 Django 기반의 커리어/구직 관리 및 매칭 서비스입니다.

## 🛠️ 개발 환경 설정 및 실행 방법

### 1. 가상환경 활성화 (Virtual Environment)
프로젝트 루트 폴더에 Python 가상환경(`venv`)이 생성되어 있습니다. 터미널 종류에 맞게 아래 명령어를 입력하여 가상환경을 활성화하세요.

- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **Bash / Git Bash**:
  ```bash
  source venv/Scripts/activate
  ```

### 2. 패키지 설치
필요한 패키지들은 `requirements.txt` 파일에 정의되어 있으며, 가상환경이 활성화된 상태에서 아래 명령어로 설치할 수 있습니다 (이미 설치 완료됨).
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 마이그레이션 (DB Migration)
데이터베이스 테이블 생성을 위한 마이그레이션이 이미 적용되어 있습니다. 추가 변경사항이 생기면 아래 명령어를 실행하세요.
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 로컬 서버 실행
로컬 개발 서버를 실행하려면 아래 명령어를 입력하세요.
```bash
python manage.py runserver
```
이후 웹 브라우저에서 `http://127.0.0.1:8000/`으로 접속할 수 있습니다.
