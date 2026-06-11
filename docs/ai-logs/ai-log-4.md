# M2 AI 활용 로그 — 프로토타입 개발

> **대상 산출물**: `TrueFilter/main.py`
> **작성자**: 개발자,PM
> **대상 기간**: 12주차 (M2 프로토타입 구현)
> **사용 도구**: Gemini (Google)

---

## 건별 로그 #1 — Windows 플랫폼 기반 프로토타입 뼈대 생성

### 프롬프트

```
(파일 첨부: 설계 문서)

주어진 설계파일을 바탕으로 프로토타입 프로그램을 단계적으로 만들어줘.
여기서 말하는 프로토타입은 저 설계파일에서 요구하는 기능이 전부 완성되어있어야 해.
필요한 추가 정보가 있으면 추측하지 말고 나에게 물어봐야 해.
단 수정사항이 있어. 프로토타입 단계이기 때문에 플랫폼은 윈도우야. 그거에 맞춰서 적절히 제작해.
```

---

### AI 응답 요약

Gemini가 Windows 플랫폼 전환에 따른 기술 스택을 검토하고 PyQt6 기반의 클래스 구조 뼈대 코드를 생성하였다. 오버레이 창은 `Qt.WindowType.WindowStaysOnTopHint`와 `FramelessWindowHint`로 구현하고, OCR은 `mss` + `pytesseract`, 로컬 데이터는 SQLite 또는 JSON으로 관리하는 방향을 제시했다. 코드를 제공하기 전 FR-01 트리거 방식(전체 화면 루프 vs 단축키)과 외부 API 연동 여부를 확인 질문으로 먼저 물어봤다.

---

### AI 생성 원본 (주요 뼈대 코드)

```python
import time
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Article:
    title: str
    source_url: str
    summary: str
    published_at: float

    def get_summary(self) -> str:
        return self.summary

@dataclass
class AnalysisResult:
    analysis_id: str
    trust_score: int
    bias_summary: str
    timestamp: float
    articles: List[Article]

    def get_trust_level(self) -> str:
        levels = {1: "매우 낮음", 2: "낮음", 3: "보통", 4: "높음", 5: "매우 높음"}
        return levels.get(self.trust_score, "알 수 없음")

    def is_expired(self, ttl_seconds: int) -> bool:
        return (time.time() - self.timestamp) > ttl_seconds

class ArticleCache:
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 100):
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self.cache = {}

    def get(self, text_hash: str) -> Optional[AnalysisResult]:
        result = self.cache.get(text_hash)
        if result and not result.is_expired(self.ttl_seconds):
            return result
        return None

    def put(self, text_hash: str, result: AnalysisResult) -> None:
        self.cache[text_hash] = result

class OverlayService:
    def __init__(self):
        self.is_active: bool = False
        self.current_analysis_id: str = ""
        self.text_recognizer = TextRecognizer()
        self.trust_analyzer = TrustAnalyzer()
        self.cache = ArticleCache()

    def start(self):
        self.is_active = True

    def stop(self):
        self.is_active = False
```

---

### 비판적 검토

전체 클래스 구조와 Windows 환경 고려 사항은 설계 문서를 잘 반영하였다. 수정이 필요했던 부분은 코드 완성도와 실행 가능성 측면에서 미비한 부분이었다.

| # | 검토 내용 | 판단 |
|---|----------|------|
| 1 | 설계 문서의 주요 클래스(`Article`, `AnalysisResult`, `ArticleCache`, `OverlayService` 등) 구조 반영 | 적절 |
| 2 | Windows 오버레이 구현 방식(`WindowStaysOnTopHint`, `FramelessWindowHint`) 제시 | 적절 |
| 3 | 코드를 바로 제공하지 않고 트리거 방식, API 연동 여부를 먼저 확인 질문 | 적절 |
| 4 | `TextRecognizer`, `BiasAnalyzer`, `FeedbackRepository` 클래스가 뼈대에서 누락되어 실행 불가 상태 | 수정 필요 |
| 5 | `OverlayService.start()` 내부에 화면 캡처·OCR 스레드 로직이 `TODO` 주석만 있고 미구현 | 수정 필요 |
| 6 | `get_trust_level()`이 점수를 1~5 범위로 매핑하나 설계 문서의 0~100 범위와 불일치 | 수정 필요 |

---

### 수정 내용

**수정 1** — 확인 질문 응답으로 구현 방향 결정

AI가 코드 제공 전 질문한 두 항목에 팀이 직접 답변하여 구현 방향을 확정하였다.

| 확인 항목 | 결정 사항 |
|----------|----------|
| FR-01 트리거 방식 | `Ctrl+Shift+F` 단축키로 마우스 커서 주변 캡처 방식 채택 |
| 외부 API 연동 여부 | 더미 데이터(Mock) 반환 구조로 우선 구현 |

**수정 2** — 신뢰도 점수 범위 수정

`get_trust_level()`의 입력 범위를 설계 문서 기준인 0~100으로 맞추어 레벨 분류 로직을 재작성하였다.

**수정 3** — 미구현 클래스 보완 요청

`TextRecognizer`, `BiasAnalyzer`, `FeedbackRepository`가 누락된 상태였으므로, 다음 단계 코드 생성 시 포함하도록 방향을 확정하였다.

---

### 최종 반영 결과

데이터 모델 클래스(`Article`, `AnalysisResult`) 구조와 `ArticleCache` 로직은 AI 원본을 기반으로 채택하였다. **신뢰도 점수 범위 수정 1건**, **미구현 클래스 목록 정리 후 다음 단계 요청**을 팀이 직접 처리하였다.

---

## 건별 로그 #2 — 단축키 트리거 및 더미 데이터 구조 완성

### 프롬프트

```
ㅇㅇ / 더미 데이터를 반환하는 구조로 작성해
(단축키 Ctrl+Shift+F 방식과 더미 데이터 구조 선택 응답)
```

---

### AI 응답 요약

Gemini가 `keyboard` 라이브러리 기반 단축키 감지, `QThread` 비동기 처리, `MockAnalyzer` 더미 반환 구조를 포함한 실행 가능한 전체 `main.py`를 생성하였다. GUI 스레드 충돌 방지를 위해 `pyqtSignal`을 활용하였고, Tesseract 미설치 시 더미 텍스트로 폴백하는 방어 로직도 사전 설계하여 포함하였다.

---

### AI 생성 원본 (핵심 구조)

```python
class MockAnalyzer:
    def analyze(self, text: str) -> AnalysisResult:
        time.sleep(0.5)
        return AnalysisResult(
            trust_score=75,
            bias_summary="해당 텍스트는 특정 정치적 성향에 편향되지 않은 중립적인 사실 보도에 가깝습니다.",
            articles=[
                Article("유사 기사 1: A일보 사실 확인 결과", "http://example.com/1"),
                Article("유사 기사 2: B뉴스 관련 보도", "http://example.com/2"),
                Article("유사 기사 3: C방송 팩트체크", "http://example.com/3")
            ]
        )

class AnalysisThread(QThread):
    analysis_completed = pyqtSignal(AnalysisResult)

    def run(self):
        with mss() as sct:
            x, y = QCursor.pos().x(), QCursor.pos().y()
            monitor = {"top": max(0, y - 300), "left": max(0, x - 400),
                       "width": 800, "height": 600}
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        try:
            extracted_text = pytesseract.image_to_string(img, lang='kor+eng')
        except Exception:
            extracted_text = "OCR_FAILED_DUMMY_TEXT"
        analyzer = MockAnalyzer()
        result = analyzer.analyze(extracted_text)
        self.analysis_completed.emit(result)

keyboard.add_hotkey('ctrl+shift+f', lambda: overlay.hotkey_pressed.emit())
```

---

### 비판적 검토

| # | 검토 내용 | 판단 |
|---|----------|------|
| 1 | `pyqtSignal`로 워커 스레드 → 메인 GUI 스레드 간 데이터 전달하여 크래시 방지 | 적절 |
| 2 | `QThread` 비동기 처리로 UI 프리징 없이 NFR-01(2초 이내) 충족 구조 | 적절 |
| 3 | Tesseract 미설치 시 `OCR_FAILED_DUMMY_TEXT` 폴백 처리 | 적절 |
| 4 | 투명도 슬라이더(FR-03), 드래그 이동(FR-03), 닫기 버튼 포함 | 적절 |
| 5 | `MockAnalyzer`의 더미 데이터가 항상 고정값(`trust_score: 75`)으로 반환되어 시연 시 설득력 낮음 | 수정 필요 |
| 6 | 피드백 버튼(`오류 신고`) 클릭 시 터미널에 `print`만 출력되고 FR-05 기능 미구현 상태 | 향후 과제 |

---

### 수정 내용

**수정 1** — 더미 고정값 문제 → AI API 연동으로 대체 방향 결정

시연에서 항상 동일한 `trust_score: 75`가 출력되면 분석 기능이 실제로 동작하는 것처럼 보이지 않는다고 판단하였다. 실제 텍스트에 따라 동적으로 결과가 달라지도록 `MockAnalyzer`를 Gemini API를 호출하는 `AIAnalyzer`로 교체하는 것을 다음 단계 목표로 확정하였다.

---

### 최종 반영 결과

단축키 트리거, 비동기 스레드, 오버레이 UI 구조는 AI 원본을 기반으로 채택하였다. **더미 고정값의 시연 한계 식별 후 AI API 연동 단계로 진행** 결정을 팀이 내렸다.

---

## 건별 로그 #3 — Gemini AI API 연동 및 오류 해결

### 프롬프트

```
이제 우리 프로젝트 목적에 좀 더 맞는 프로토타입으로 바꾸고 싶어.
일단 API는 없으니 AI API 등을 활용하여 목적과 유사한 기능을 시연할 수 있게 할래.
```

---

### AI 응답 요약

Gemini가 `google-generativeai` 라이브러리를 사용해 `MockAnalyzer`를 `AIAnalyzer`로 교체하는 코드를 생성하였다. 프롬프트에 신뢰도·편향도·유사 기사 JSON 포맷을 명시하여 모델이 구조화된 응답을 반환하도록 설계하였다. 이후 실행 과정에서 403 → 404 순으로 오류가 발생하였고, Gemini가 각 오류에 대해 여러 차례 수정 방안을 제시하였다.

---

### AI 생성 원본 (AIAnalyzer 핵심 로직)

```python
class AIAnalyzer:
    def analyze(self, text: str) -> AnalysisResult:
        prompt = f"""
        당신은 뉴스 및 SNS 텍스트의 신뢰도와 편향성을 분석하는 팩트체크 시스템 'TrueFilter'입니다.
        아래 [입력 텍스트]를 분석하여 반드시 제시된 JSON 형식으로만 응답하십시오.

        [출력 JSON 포맷]
        {{
          "trust_score": 85,
          "bias_summary": "...",
          "articles": [
            {{"title": "관련 기사 제목", "source_url": "https://news.naver.com"}}
          ]
        }}
        """
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(raw_text)
        ...
```

---

### 비판적 검토

| # | 검토 내용 | 판단 |
|---|----------|------|
| 1 | 프롬프트에 JSON 출력 포맷을 명시하여 파싱 가능한 구조화 응답 유도 | 적절 |
| 2 | 마크다운 코드블록 제거(`replace('```json', '')`) 처리 포함 | 적절 |
| 3 | API 호출 실패 시 `except Exception`으로 오류 메시지를 UI에 출력하는 방어 로직 | 적절 |
| 4 | `google-generativeai` 라이브러리가 PC에 남은 `gcloud` 로컬 자격 증명을 우선 참조하여 403 오류 발생 — 라이브러리 내부 인증 우선순위를 고려하지 않음 | 수정 필요 |
| 5 | 403 해결을 위해 `os.environ` 삭제 → `%APPDATA%\gcloud` 파일 삭제 → 환경 변수 직접 삭제 순으로 여러 방법을 제시하였으나 각 방법의 전제 조건이 실제 환경과 달라 반복 실패 | 수정 필요 |
| 6 | 최종 해결책으로 제시한 REST API 직접 호출 방식은 `google-generativeai` 라이브러리를 우회하므로 자격 증명 충돌을 원천 차단하는 올바른 접근 | 적절 |
| 7 | REST API URL의 모델명(`gemini-1.5-flash`, `gemini-1.0-pro-latest`)을 여러 번 변경하는 과정에서 404가 반복 발생 — 계정별 활성화 모델 목록을 사전에 확인하지 않고 추측으로 시도한 것이 원인 | 수정 필요 |

---

### 수정 내용

**수정 1** — `google-generativeai` 라이브러리 제거 → `requests` 라이브러리로 REST API 직접 호출

`google-generativeai`의 내부 인증 모듈이 시스템에 캐싱된 `gcloud` 자격 증명을 코드에 명시된 API 키보다 우선 적용하여 403이 발생하였다. 라이브러리 의존을 완전히 제거하고 `requests.post()`로 REST 엔드포인트에 직접 POST 요청하는 방식으로 교체하여 충돌을 원천 차단하였다.

| AI 원본 방식 | 수정 후 방식 |
|------------|------------|
| `genai.configure(api_key=...)` + `genai.GenerativeModel(...)` | `requests.post(url, headers=headers, json=payload)` |
| 라이브러리 내부 인증 로직에 의존 | GEMINI_API_KEY를 URL 파라미터로 직접 전달 |

**수정 2** — HTTP 오류 코드를 UI에 직접 출력하도록 방어 로직 보강

AI가 제시한 `except Exception` 처리만으로는 어떤 HTTP 오류인지 UI에서 확인이 불가능하였다. `response.status_code != 200` 분기를 추가하여 상태 코드와 서버 응답 본문을 UI에 출력하도록 수정하였다.

```python
if response.status_code != 200:
    return AnalysisResult(0, f"API 호출 오류 ({response.status_code}): {response.text}", [])
```

**수정 3** — 모델명 결정 방식 개선 방향 도출

AI가 `gemini-1.5-flash` → `gemini-1.5-flash-latest` → `gemini-1.0-pro-latest` → `gemini-1.5-flash` 순으로 모델명을 반복 변경하면서 404가 지속되었다. 이는 계정별 활성화 모델 목록을 사전에 확인하지 않고 추측으로 시도한 것이 원인이므로, 향후 API 연동 시에는 먼저 `GET /v1beta/models` 엔드포인트로 사용 가능한 모델 목록을 조회한 뒤 모델명을 결정하는 절차를 거치기로 하였다.

---

### 최종 반영 결과

`prototype/main.py`의 `AIAnalyzer` 클래스에 반영 완료.  
`google-generativeai` 라이브러리를 `requests` 직접 호출 방식으로 **전면 교체**, **HTTP 오류 코드 UI 출력 로직 추가**, **Tesseract 경로(`C:\Users\Ditto\AppData\Local\Programs\Tesseract-OCR\tesseract.exe`) 하드코딩 반영**을 팀이 직접 수정·보완하였다.

---

*작성일: 2026-05-19 | 작성자: 개발자, PM*
