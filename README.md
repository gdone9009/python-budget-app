# 📊 파일 기반 가계부 콘솔 프로그램 (python-budget-app)

## 1. 프로젝트 개요
이 프로젝트는 외부 라이브러리(Pandas 등) 없이 파이썬 표준 라이브러리만을 활용하여 구축한 CLI 기반 가계부 프로그램입니다. 

단순한 입출력 수준을 넘어 **대용량 데이터 스트리밍(Generator)**, **관심사 분리(Layered Architecture)**, **원자적 파일 저장(Atomic File I/O)** 등 실무적인 소프트웨어 아키텍처 패턴을 적용하여 확장성과 유지보수성을 극대화한 것이 특징입니다.

## 2. 개발 환경 및 기술 스택
- **Language:** Python 3.10 이상
- **Libraries:** 순수 파이썬 표준 라이브러리 (`argparse`, `csv`, `os`, `re`, `datetime` 등)
- **Interface:** CLI (Command Line Interface)

## 3. 데이터 저장 위치 및 CSV 스키마
프로그램 종료 후에도 데이터가 유실되지 않도록 최소 3개의 CSV 파일로 분리하여 영구 저장합니다 [4].
- `data/transactions.csv`: 가계부 거래 내역
- `data/categories.csv`: 참조 무결성을 위한 등록 카테고리 목록
- `data/budgets.csv`: 월별 설정 예산 목록

### 📌 Import / Export CSV 스키마 규칙
외부 데이터를 가져오거나 내보낼 때 지켜야 하는 필수 규격입니다 [3]. (UTF-8 인코딩, 헤더 포함)

| column | required | 설명 |
|---|---|---|
| date | Y | YYYY-MM-DD 형식의 날짜 |
| type | Y | `income` (수입) / `expense` (지출) |
| category | Y | 등록된 카테고리명 (categories.csv에 존재해야 함) |
| amount | Y | 0보다 큰 양수 정수 |
| memo | N | 문자열 (선택) |
| tags | N | 쉼표(,)로 구분된 문자열 (선택) |

## 4. 프로젝트 폴더 및 파일 구조
이 프로그램은 실무 백엔드 구조를 모방하여 프레젠테이션, 서비스, 데이터 계층으로 역할을 명확히 분리하였습니다.

```text
📦 python-budget-app/
┣ 📂 data/                  # 영구 데이터 저장소 (프로그램 실행 시 자동 생성)
┃ ┣ 📜 transactions.csv     
┃ ┣ 📜 categories.csv       
┃ ┗ 📜 budgets.csv          
┣ 📜 budget_app/__main__.py # 프로그램 실행 진입점
┣ 📜 budget_app/cli.py      # 터미널 명령어 파싱 및 분기 (컨트롤러/프레젠테이션 계층)
┣ 📜 budget_app/services.py # 핵심 비즈니스 로직 및 유효성 검증 (서비스 계층)
┣ 📜 budget_app/repositories.py # 파일 I/O, 제너레이터 스트리밍 및 원자적 쓰기 (데이터 계층)
┣ 📜 budget_app/models.py   # 데이터 모델 및 타입 힌트 엄격 정의
┣ 📜 budget_app/utils.py    # 공통 예외 처리 및 로깅 데코레이터
┗ 📜 README.md              # 프로젝트 기술 문서
```
💡 설계의 핵심: 화면에 글자를 뿌리고 입력받는 작업(print, input)은 오직 cli.py에서만 수행하며, services.py는 순수한 데이터 검증과 비즈니스 로직만 수행합니다. 이를 통해 향후 웹 프레임워크(FastAPI 등)로 이식할 때 로직을 100% 재사용할 수 있습니다.

## 5. 실행 방법 및 주요 명령어 예시
이 프로그램은 모듈 단위 실행을 권장합니다
. 최상단 폴더 위치에서 아래 명령어들을 실행합니다. 모든 명령어는 -h 또는 --help를 통해 도움말을 볼 수 있습니다.
① 카테고리 및 예산 설정
데이터 무결성(FK 제약조건)을 위해 거래를 등록하기 전, 반드시 카테고리를 먼저 생성해야 합니다.
### 카테고리 추가
python -m budget_app category add 식비
python -m budget_app category add 월급

### 카테고리 목록 조회
python -m budget_app category list

### 특정 월의 목표 예산 설정
python -m budget_app budget set --month 2024-05 --amount 500000
② 거래 내역 추가 (대화형 인터페이스)
python -m budget_app add
### 터미널 프롬프트의 질문에 따라 날짜, 타입(income/expense), 금액 등을 한 줄씩 입력
③ 거래 목록 조회 및 월별 요약 통계
### 최신 거래 내역 10건 조회 (스트리밍)
python -m budget_app list --limit 10

### 월별 지출/수입 요약 및 예산 초과(%) 경고 알림 기능
python -m budget_app summary --month 2024-05 --top 3
④ 데이터 내보내기/가져오기
### 특정 월의 데이터를 CSV로 내보내기
python -m budget_app export --out export.csv --month 2024-05

### 위 스키마 규격에 맞는 외부 CSV 파일의 데이터를 일괄 검증 후 가져오기
python -m budget_app import --from import.csv

## 6. 핵심 트러블슈팅 및 배운 점
### 6-1. ModuleNotFoundError 경로 문제 해결
문제 상황: 터미널에서 python -m budget_app add 실행 시, budget_app 패키지 내부 파일들끼리 서로 모듈을 찾지 못해 오류 발생.
원인 및 해결: 파이썬 실행 위치와 모듈 인식 경로가 일치하지 않아 발생한 현상. from .cli import main, from .services import ... 처럼 명시적으로 상대 경로(점 .)를 찍어주어 패키지 내부 의존성 연결 문제를 우아하게 해결함.
### 6-2. Generator(yield)를 활용한 대용량 파일 OOM 방지
배운 점: 수십만 건의 거래 내역을 리스트([])에 담아 한 번에 반환하면 메모리 터짐(OOM) 현상이 발생할 수 있음. 이를 방지하기 위해 파일 전체를 읽지 않고 yield를 사용한 제너레이터 스트리밍 필터링 방식으로 전환하여 메모리 효율을 극대화함.
### 6-3. 원자적 파일 교체(Atomic Replacement)를 통한 데이터 증발 방지
<<<<<<< HEAD
배운 점: 수정이나 삭제 도중 전원이 꺼지면 기존 데이터가 날아갈 수 있음. 이를 방어하기 위해 repositories.py에서 임시 파일(.temp)에 먼저 변경 데이터를 안전하게 쓰고, 작업이 성공했을 때만 원본 파일을 덮어쓰도록 트랜잭션 개념을 파이썬 스크립트로 직접 구현해 냄.
=======
배운 점: 수정이나 삭제 도중 전원이 꺼지면 기존 데이터가 날아갈 수 있음. 이를 방어하기 위해 repositories.py에서 임시 파일(.temp)에 먼저 변경 데이터를 안전하게 쓰고, 작업이 성공했을 때만 원본 파일을 덮어쓰도록 트랜잭션 개념을 파이썬 스크립트로 직접 구현해 냄.
>>>>>>> 3a3a7ae7fd40cb842f3a182dcbcb3449acd3be68
