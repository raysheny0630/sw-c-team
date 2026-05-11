# TrueFilter — M2 객체지향 분석 다이어그램

> **작성 기준**: Chap-8 객체지향 분석 (9주차 강의) 절차에 따라 작성  
> **작성자**: 분석가 (정주승) | **검토**: PM (김지우)  
> **버전**: v1.0 | **작성일**: 2026-05-11  
> **연관 문서**: [요구사항 정의서](requirements.md) · [WBS](wbs.md)

---

## 목차

1. [기능 모델링 — 유스케이스 다이어그램](#1-기능-모델링--유스케이스-다이어그램)
2. [유스케이스 설명서](#2-유스케이스-설명서)
3. [구조 모델링 — 클래스 다이어그램](#3-구조-모델링--클래스-다이어그램)
4. [행위 모델링 — 순차 다이어그램](#4-행위-모델링--순차-다이어그램)
5. [산출물 간 일관성 점검](#5-산출물-간-일관성-점검)

---

## 1. 기능 모델링 — 유스케이스 다이어그램

### 1-1. 액터 식별

강의 기준: 액터는 역할 중심으로 식별하며, 시스템 외부에 존재하는 상호작용 대상 전체를 포함한다.

| 액터 | 유형 | 역할 설명 |
|------|------|-----------|
| **사용자** | Primary Actor | SNS 피드를 탐색하며 신뢰도·편향도 분석 결과를 소비하는 주체. 페르소나: 단국이(20세) |
| **FactCheck API** | Secondary Actor (EIF) | 외부 뉴스 신뢰도 DB·팩트체크 결과를 제공하는 외부 시스템. 사람이 아닌 외부 서비스 |

### 1-2. 유스케이스 다이어그램

> GitHub Mermaid 렌더링 기준. 시스템 경계는 `subgraph`로 표현한다.

```mermaid
flowchart LR
    User(["👤 사용자"])
    ExtAPI(["🌐 FactCheck API\n외부 시스템"])

    subgraph SYS ["TrueFilter 시스템 경계"]
        direction TB

        UC01(["UC-01\n오버레이 활성화하기"])
        UC02(["UC-02\n신뢰도 확인하기"])
        UC03(["UC-03\n편향도 분석 확인하기"])
        UC04(["UC-04\n오버레이 UI 설정하기"])
        UC05(["UC-05\n오분석 피드백 전송하기"])

        UCsub1(["텍스트 인식하기\n«sub»"])
        UCsub2(["팩트체크 API 조회하기\n«sub»"])
        UCsub3(["유사 기사 조회하기\n«extend»"])
    end

    User -->|시작| UC01
    User -->|시작| UC02
    User -->|시작| UC03
    User -->|시작| UC04
    User -->|시작| UC05

    UC02 -- "«include»" --> UCsub1
    UC02 -- "«include»" --> UCsub2
    UC03 -- "«include»" --> UC02
    UC03 -- "«extend»\n[사용자가 버튼 클릭]" --> UCsub3

    UCsub2 --> ExtAPI
    UCsub3 --> ExtAPI
```

**설계 근거**

- UC-03(편향도 확인)이 UC-02(신뢰도 확인)를 `«include»`하는 이유: 편향도 분석을 위해서는 반드시 먼저 텍스트 인식과 출처 신뢰도 계산이 선행되어야 한다(FR-01, FR-02 의존).
- `유사 기사 조회하기`를 `«extend»`로 처리한 이유: AI 인터뷰 Q5 피드백("판단해주는 느낌이면 거부감") 반영 — 사용자가 명시적으로 버튼을 눌러야만 근거 기사를 펼치도록 설계(FR-04).

---

## 2. 유스케이스 설명서

강의 기준: 유스케이스별로 식별부 + 정상 시나리오 + 예외 처리를 작성한다.

---

### UC-02 신뢰도 확인하기

#### 식별부

| 항목 | 내용 |
|------|------|
| **Use Case Name** | 신뢰도 확인하기 |
| **ID** | UC-02 |
| **Importance Level** | High |
| **Primary Actor** | 사용자 |
| **Use Case Type** | Detail, Essential |
| **Stakeholders** | 사용자 — SNS 피드 탐색 중 뉴스의 신뢰도를 즉시 알고 싶다<br>운영자 — 오분석률을 낮추어 서비스 신뢰를 유지하고 싶다 |
| **Brief Description** | SNS 화면에 뉴스 텍스트가 감지되면 출처 공신력·팩트체크 결과·인용 여부를 합산하여 5단계 신뢰도 점수를 오버레이로 표시한다 |
| **Trigger** | SNS 앱 화면에 뉴스 제목 또는 본문이 표시될 때 오버레이 서비스가 자동으로 감지 |
| **Relationships** | Association: 사용자<br>Include: 텍스트 인식하기, 팩트체크 API 조회하기<br>Extend: (없음) |

#### 정상 시나리오 (Normal Flow of Events)

1. 사용자가 SNS 앱을 실행하여 피드를 스크롤한다.
2. TrueFilter 오버레이 서비스가 화면 캡처를 감지하고 텍스트 인식을 실행한다.
   - `«include»` **텍스트 인식하기**: `TextRecognizer`가 화면 비트맵에서 뉴스 텍스트를 추출한다.
3. 시스템이 `ArticleCache`에서 동일 텍스트 해시를 조회한다.
   - [캐시 히트] → Step 5로 이동
   - [캐시 미스] → Step 4로 이동
4. 시스템이 팩트체크 API를 조회한다.
   - `«include»` **팩트체크 API 조회하기**: `FactCheckAPI.query(text)`를 호출하여 결과를 수신한다.
   - `TrustAnalyzer`가 출처 공신력(40%) + 팩트체크 결과(40%) + 인용 여부(20%) 가중합으로 점수를 계산한다.
   - 계산 결과를 `ArticleCache`에 저장한다.
5. 시스템이 신뢰도 5단계 게이지를 오버레이로 출력한다. (요구사항: **2초 이내**, NFR-01)
6. 사용자가 오버레이를 확인한다.

#### 예외 처리 (Alternative / Exceptional Flow)

| 식별자 | 예외 상황 | 처리 |
|--------|-----------|------|
| S2-1a | FactCheck API 응답 지연 (2초 초과) | 타임아웃 처리 후 "분석 중" 상태 표시; 캐시에 결과 도착 시 업데이트 |
| S4-1a | 인식된 텍스트가 뉴스가 아닌 경우 (짧은 텍스트, 광고 등) | 오버레이 미표시; 최소 30자 이상 뉴스 패턴 텍스트에만 분석 실행 |
| S4-2a | FactCheck API 응답 오류 (HTTP 5xx) | 출처 공신력·인용 여부만으로 부분 점수 계산 후 "팩트체크 정보 미포함" 표시 |

---

### UC-05 오분석 피드백 전송하기

#### 식별부

| 항목 | 내용 |
|------|------|
| **Use Case Name** | 오분석 피드백 전송하기 |
| **ID** | UC-05 |
| **Importance Level** | Low |
| **Primary Actor** | 사용자 |
| **Use Case Type** | Detail, Optional |
| **Trigger** | 사용자가 오버레이의 피드백 버튼을 클릭 |
| **Relationships** | Association: 사용자 |

#### 정상 시나리오

1. 사용자가 오버레이에서 피드백 아이콘을 탭한다.
2. 시스템이 피드백 입력 폼(코멘트 필드 + 전송 버튼)을 오버레이 하단에 표시한다.
3. 사용자가 오분석 내용을 입력하고 전송 버튼을 탭한다.
4. 시스템이 `FeedbackRepository.save(analysisId, comment)`를 호출한다.
5. 시스템이 "피드백이 전송되었습니다" 확인 메시지를 1.5초간 표시 후 폼을 닫는다.

#### 예외 처리

| 식별자 | 예외 상황 | 처리 |
|--------|-----------|------|
| S3-1a | 코멘트 필드가 비어 있는 상태로 전송 | 전송 버튼 비활성화; "내용을 입력해주세요" 안내 표시 |
| S4-1a | 네트워크 오프라인 상태 | 로컬 큐에 저장 후 네트워크 복구 시 자동 재전송 |

---

## 3. 구조 모델링 — 클래스 다이어그램

강의 기준: 객체 식별 방식 1(문장 분석) + 방식 2(일반 객체 목록)를 혼용하여 클래스를 도출하고,  
CRC 카드 명세 후 클래스 다이어그램을 작성한다.

### 3-1. 객체 식별 근거

유스케이스 설명서 정상 시나리오에서 문장 분석(방식 1)으로 도출:

| 문장 요소 | 매핑 결과 |
|-----------|-----------|
| 일반 명사: 텍스트, 신뢰도, 편향도, 피드백, 기사, 설정, 캐시 | 클래스 후보 |
| 동사: 인식하다, 계산하다, 조회하다, 저장하다, 표시하다 | 클래스 연산 |
| 형용사: 활성화된, 암호화된, 만료된 | 클래스 속성 |
| 고유 명사: FactCheckAPI | 외부 인터페이스 클래스 인스턴스 |

### 3-2. 클래스 다이어그램

```mermaid
classDiagram
    direction TB

    class User {
        -userId : String
        +activateOverlay() void
        +adjustOverlay(pos, opacity) void
        +sendFeedback(id, comment) void
        +requestBiasDetail(analysisId) void
    }

    class OverlayService {
        -isActive : Boolean
        -position : Point
        -opacity : Float
        +start() void
        +stop() void
        +onScreenCapture(bitmap) void
        +showResult(result) void
    }

    class TextRecognizer {
        -minLength : int = 30
        +recognize(bitmap) String
        +isNewsText(text) Boolean
    }

    class TrustAnalyzer {
        -wSource : Float = 0.4
        -wFactCheck : Float = 0.4
        -wCitation : Float = 0.2
        +analyze(text, factResult) AnalysisResult
        +calculateScore(s, f, c) int
    }

    class BiasAnalyzer {
        +analyze(text) String
        +fetchSimilarArticles(text) List~Article~
    }

    class AnalysisResult {
        -analysisId : String
        -textHash : String
        -trustScore : int
        -trustLevel : String
        -biasSummary : String
        -similarArticles : List~Article~
        -timestamp : DateTime
        +getTrustLevel() String
        +isExpired() Boolean
    }

    class UserSettings {
        -overlayPosition : Point
        -overlayOpacity : Float
        +update(pos, opacity) void
    }

    class ArticleCache {
        -store : Map~String_AnalysisResult~
        -ttlSeconds : int = 3600
        +get(hash) AnalysisResult
        +put(hash, result) void
        +isExpired(hash) Boolean
    }

    class FeedbackRepository {
        -queue : List~Feedback~
        +save(analysisId, comment) void
        +flush() void
    }

    class FactCheckAPI {
        <<interface>>
        +query(text) FactCheckResult
    }

    class Article {
        -title : String
        -url : String
        -source : String
        -publishedAt : DateTime
    }

    %% 관계 정의
    User --> OverlayService : 사용
    User o-- UserSettings : 소유

    OverlayService *-- TextRecognizer : 포함(Composition)
    OverlayService *-- TrustAnalyzer : 포함(Composition)
    OverlayService *-- BiasAnalyzer : 포함(Composition)
    OverlayService o-- ArticleCache : 집합(Aggregation)
    OverlayService o-- FeedbackRepository : 집합(Aggregation)

    TrustAnalyzer ..> FactCheckAPI : 의존(Dependency)
    BiasAnalyzer ..> FactCheckAPI : 의존(Dependency)

    TrustAnalyzer ..> AnalysisResult : 생성
    BiasAnalyzer ..> AnalysisResult : 보완

    AnalysisResult o-- Article : 포함 0..*
    ArticleCache o-- AnalysisResult : 저장
```

### 3-3. 관계 기수성 설명

| 관계 | 기수성 | 근거 |
|------|--------|------|
| `OverlayService` → `TextRecognizer` | 1 : 1 | 인식 모듈은 서비스당 하나만 필요 |
| `AnalysisResult` → `Article` | 1 : 0..5 | FR-04: 유사 기사 최대 5건 |
| `ArticleCache` → `AnalysisResult` | 1 : 0..* | 캐시는 여러 분석 결과를 보관 |
| `User` → `UserSettings` | 1 : 1 | 사용자별 설정은 하나 |

---

## 4. 행위 모델링 — 순차 다이어그램

강의 기준: 유스케이스별로 순차 다이어그램을 작성하며, ABCD 규칙(Actor → Boundary → Control → Data 순)으로 객체를 배치한다.

---

### SD-02 신뢰도 확인하기 (UC-02)

```mermaid
sequenceDiagram
    autonumber
    actor       User    as 👤 사용자
    participant OUI     as :OverlayUI<br/>[Boundary]
    participant Ctrl    as :AnalysisController<br/>[Control]
    participant TR      as :TextRecognizer<br/>[Data]
    participant Cache   as :ArticleCache<br/>[Data]
    participant TA      as :TrustAnalyzer<br/>[Data]
    participant Ext     as :FactCheckAPI<br/>[External]

    User  ->> OUI   : SNS 피드 스크롤 (화면 변경 감지)
    OUI   ->> Ctrl  : onScreenCapture(bitmap)
    Ctrl  ->> TR    : recognize(bitmap)
    TR    -->> Ctrl : extractedText

    Ctrl  ->> TR    : isNewsText(extractedText)
    TR    -->> Ctrl : true / false

    alt [뉴스 텍스트가 아닌 경우]
        Ctrl -->> OUI : 오버레이 미표시
    else [뉴스 텍스트 감지]
        Ctrl  ->> Cache : get(textHash)

        alt [캐시 미스 — 신규 분석 필요]
            Cache -->> Ctrl : null
            Ctrl  ->> Ext   : query(extractedText)
            Ext   -->> Ctrl : factCheckResult
            Ctrl  ->> TA    : analyze(extractedText, factCheckResult)
            TA    -->> Ctrl : analysisResult
            Ctrl  ->> Cache : put(textHash, analysisResult)
        else [캐시 히트 — 저장된 결과 재사용]
            Cache -->> Ctrl : analysisResult
        end

        Ctrl  ->> OUI   : showResult(analysisResult)
        OUI   -->> User : 신뢰도 5단계 게이지 표시 ← NFR-01: 2초 이내
    end
```

**ABCD 배치 근거**

| 위치 | 객체 | 분류 |
|------|------|------|
| 좌 1 | 사용자 | Actor |
| 좌 2 | OverlayUI | Boundary (화면 인터페이스) |
| 중 1 | AnalysisController | Control (비즈니스 흐름 제어) |
| 중 2 | TextRecognizer, ArticleCache, TrustAnalyzer | Data (도메인 데이터 처리) |
| 우   | FactCheckAPI | External Actor |

---

### SD-05 오분석 피드백 전송하기 (UC-05)

```mermaid
sequenceDiagram
    autonumber
    actor       User    as 👤 사용자
    participant OUI     as :OverlayUI<br/>[Boundary]
    participant FCtrl   as :FeedbackController<br/>[Control]
    participant Repo    as :FeedbackRepository<br/>[Data]

    User  ->> OUI   : 피드백 아이콘 탭
    OUI   -->> User : 피드백 입력 폼 표시

    User  ->> OUI   : 코멘트 입력 후 전송 버튼 탭

    alt [코멘트 필드가 비어 있는 경우]
        OUI -->> User : "내용을 입력해주세요" 안내 표시
    else [코멘트 정상 입력]
        OUI   ->> FCtrl : submitFeedback(analysisId, comment)

        alt [네트워크 오프라인]
            FCtrl ->> Repo : enqueue(analysisId, comment)
            Repo  -->> FCtrl : queued
            FCtrl ->> OUI   : showMessage("네트워크 복구 시 자동 전송됩니다")
        else [네트워크 정상]
            FCtrl ->> Repo : save(analysisId, comment)
            Repo  -->> FCtrl : saved
            FCtrl ->> OUI   : showConfirmation()
            OUI   -->> User : "피드백이 전송되었습니다" (1.5초 후 자동 닫힘)
        end
    end
```

---

### SD-04 오버레이 UI 설정하기 (UC-04)

```mermaid
sequenceDiagram
    autonumber
    actor       User    as 👤 사용자
    participant OUI     as :OverlayUI<br/>[Boundary]
    participant SCtrl   as :SettingsController<br/>[Control]
    participant US      as :UserSettings<br/>[Data]

    User  ->> OUI   : 오버레이 드래그 (위치 변경)
    OUI   ->> SCtrl : onPositionChanged(newPoint)
    SCtrl ->> US    : update(newPoint, currentOpacity)
    US    -->> SCtrl: saved
    SCtrl ->> OUI   : applyPosition(newPoint)
    OUI   -->> User : 오버레이 위치 즉시 반영

    User  ->> OUI   : 투명도 슬라이더 조작
    OUI   ->> SCtrl : onOpacityChanged(value)
    SCtrl ->> US    : update(currentPosition, value)
    US    -->> SCtrl: saved
    SCtrl ->> OUI   : applyOpacity(value)
    OUI   -->> User : 오버레이 투명도 즉시 반영
```

---

## 5. 산출물 간 일관성 점검

강의 기준: 설계 단계 진입 전 기능 모델 ↔ 구조 모델 ↔ 행위 모델 간 일관성을 검증한다.

### 5-1. 기능 모델 ↔ 구조 모델 점검

| 유스케이스 설명서 등장 명사 | 대응 클래스 | 일치 여부 |
|---------------------------|------------|-----------|
| 텍스트 | `TextRecognizer` | ✅ |
| 신뢰도 점수 | `TrustAnalyzer`, `AnalysisResult.trustScore` | ✅ |
| 편향도 요약 | `BiasAnalyzer`, `AnalysisResult.biasSummary` | ✅ |
| 유사 기사 | `Article`, `AnalysisResult.similarArticles` | ✅ |
| 피드백 | `FeedbackRepository` | ✅ |
| 설정 (위치·투명도) | `UserSettings` | ✅ |
| 캐시 | `ArticleCache` | ✅ |
| 팩트체크 API | `FactCheckAPI` (interface) | ✅ |

### 5-2. 구조 모델 ↔ 행위 모델 점검

| 순차 다이어그램 메시지 | 대응 클래스 연산 | 일치 여부 |
|----------------------|----------------|-----------|
| `recognize(bitmap)` | `TextRecognizer.recognize()` | ✅ |
| `isNewsText(text)` | `TextRecognizer.isNewsText()` | ✅ |
| `get(textHash)` | `ArticleCache.get()` | ✅ |
| `put(textHash, result)` | `ArticleCache.put()` | ✅ |
| `query(text)` | `FactCheckAPI.query()` | ✅ |
| `analyze(text, factResult)` | `TrustAnalyzer.analyze()` | ✅ |
| `showResult(result)` | `OverlayService.showResult()` | ✅ |
| `save(analysisId, comment)` | `FeedbackRepository.save()` | ✅ |
| `update(pos, opacity)` | `UserSettings.update()` | ✅ |

### 5-3. 요구사항 커버리지

| FR/NFR | 커버하는 산출물 |
|--------|----------------|
| FR-01 (텍스트 인식) | UC-02 + `TextRecognizer` + SD-02 |
| FR-02 (신뢰도 5단계 계산) | UC-02 + `TrustAnalyzer` + SD-02 |
| FR-03 (오버레이 위치·투명도) | UC-04 + `UserSettings` + SD-04 |
| FR-04 (편향도 요약 + 유사기사) | UC-03 + `BiasAnalyzer` + `Article` |
| FR-05 (피드백 전송) | UC-05 + `FeedbackRepository` + SD-05 |
| NFR-01 (2초 이내 응답) | SD-02 step 14 주석으로 명시 |
| NFR-02 (TLS 1.3 암호화) | `FactCheckAPI` 연동 구현 시 반영 예정 |
| NFR-03 (3분 내 활성화) | UC-01 + `OverlayService.start()` |

---

*최종 수정: 2026-05-11 | 담당: 정주승 (분석가)*
