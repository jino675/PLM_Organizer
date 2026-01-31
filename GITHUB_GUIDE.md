# PLM Organizer - GitHub 업로드 가이드

## ✅ 완료된 작업
- [x] Git 설치 완료 (v2.52.0)
- [x] 로컬 저장소 초기화
- [x] 사용자 정보 설정 (jino.ryu / jino675@users.noreply.github.com)
- [x] 첫 커밋 생성 (16개 파일)

## 📤 GitHub에 업로드하는 방법

### 1단계: GitHub에서 새 Repository 만들기
1. https://github.com 접속 후 로그인
2. 우측 상단 `+` 버튼 클릭 → `New repository` 선택
3. Repository 설정:
   - **Repository name**: `PLMOrganizer`
   - **Description**: (선택) "Auto file organizer for PLM downloads"
   - **Privacy**: 
     - ✅ **Private** (추천 - 회사 프로젝트이므로)
     - ⚠️ Public (전 세계 공개)
   - ⚠️ **중요**: "Add README", ".gitignore", "license" 체크박스 **모두 해제**
4. `Create repository` 클릭

### 2단계: PowerShell에서 아래 명령어 실행
GitHub에서 생성된 화면에 나오는 주소를 복사한 후:

```powershell
cd "C:\Users\fbwls\OneDrive\문서\PLMOrganizer"

# GitHub 저장소 연결 (아래 <your-username>를 실제 주소로 변경)
& "C:\Program Files\Git\cmd\git.exe" remote add origin https://github.com/<your-username>/PLMOrganizer.git

# 기본 브랜치 이름 설정
& "C:\Program Files\Git\cmd\git.exe" branch -M main

# 업로드!
& "C:\Program Files\Git\cmd\git.exe" push -u origin main
```

### 3단계: GitHub 로그인 창이 뜨면
- 브라우저 로그인 창이 자동으로 열림
- GitHub 계정으로 로그인
- 권한 허용

### 4단계: 완료!
업로드가 끝나면 GitHub 페이지를 새로고침하면 모든 파일이 보입니다.

---

### ⚠️ 클론 에러 발생 시 (`unable to access`, `Connection reset`)
회사 보안망에서 Git 접속을 차단할 때 발생합니다. 아래 명령어를 차례대로 입력해 보세요.

```powershell
# 1. SSL 인증서 검증 무시
& "C:\Program Files\Git\cmd\git.exe" config --global http.sslVerify false

# 2. HTTP 버전 고정 (Connection reset 해결용)
& "C:\Program Files\Git\cmd\git.exe" config --global http.version HTTP/1.1

# 3. 그래도 안 되면? -> "방법 2: ZIP 다운로드"를 사용하세요.
```

## 🏢 회사 PC에서 다운로드하는 방법

### 방법 1: Git Clone (권장)
```powershell
# 원하는 폴더로 이동
cd C:\Users\<회사계정>\Documents

# 다운로드
git clone https://github.com/jino675/PLMOrganizer.git
cd PLMOrganizer
run.bat
```

### 방법 2: ZIP 다운로드 (Git 없을 때)
1. GitHub Repository 페이지 접속
2. 초록색 `Code` 버튼 → `Download ZIP`
3. 압축 해제 후 `run.bat` 실행

---

## 🔄 나중에 코드 업데이트하는 방법

집에서 코드를 수정한 후:
```powershell
cd "C:\Users\fbwls\OneDrive\문서\PLMOrganizer"
& "C:\Program Files\Git\cmd\git.exe" add .
& "C:\Program Files\Git\cmd\git.exe" commit -m "수정 내용 설명"
& "C:\Program Files\Git\cmd\git.exe" push
```

회사에서 최신 버전 받기:
```powershell
cd C:\...\PLMOrganizer
git pull
```
