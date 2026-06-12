# =========================================================
# TrueFilter 프로토타입 (Windows / PyQt6)
# - Ctrl+Shift+F 단축키로 커서 주변 화면 캡처 → OCR → 분석 → 오버레이 표시
# - 분석 엔진은 Strategy 패턴(보고서 §8)으로 교체 가능: MockAnalyzer / AIAnalyzer
# - 코딩 표준(보고서 §11)에 따라 파일 구조·주석·AI 생성 표기를 소급 적용함
# - 본 정합화 버전은 6/11 회의 결정에 따라 AI(Claude)가 생성하고 개발자가 검증 후 커밋함
#   (AI 로그 #3 개발자 건별 #5 — §10 미수정 결함 #4·#5는 변경 금지 제약으로 유지)
# =========================================================

# --- 1. Import ---
import sys
import json
import time
import keyboard
import pytesseract
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from mss import mss
from PIL import Image
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QProgressBar, QSlider, QListWidget, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QCursor

# --- 2. 상수 / 설정 ---
# [필수 설정] 발급받은 Gemini API 키를 입력하세요.
# 비밀키 소스 하드코딩·커밋 금지 (코딩 표준 §11, 인스펙션 결함 #6)
#  → 공개 레포에는 placeholder만 유지하고, 실제 키는 로컬에서만 주입한다.
GEMINI_API_KEY = "API_KEY"
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# 인스펙션 결함 #5: 특정 PC 절대경로 하드코딩(이식성) — 외부화는 후속 리팩토링 대상 (§10-3, §11)
TESSERACT_CMD = r'C:\Users\Ditto\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# UC-02 S2-1a: 인식 텍스트 30자 미만은 분석 대상에서 제외
MIN_TEXT_LENGTH = 30


# --- 3. 데이터 모델 ---
# AI-generated (12주차 뼈대, AI 로그 #4 건별 #1)
@dataclass
class Article:
    title: str
    source_url: str


@dataclass
class AnalysisResult:
    trust_score: int  # 0~100 (FR-02)
    bias_summary: str
    articles: List[Article]

    # AI-generated, modified: 입력 범위를 설계 기준 0~100으로 교정 (AI 로그 #4 건별 #1 수정 2)
    def get_trust_level(self) -> str:
        """FR-02: 0~100 점수를 5단계 척도로 매핑 (oo_design.md trust_level 컬럼과 동일 라벨)"""
        if self.trust_score <= 20:
            return "매우낮음"
        elif self.trust_score <= 40:
            return "낮음"
        elif self.trust_score <= 60:
            return "보통"
        elif self.trust_score <= 80:
            return "높음"
        return "매우높음"


# --- 4. 분석 전략 (Strategy 패턴, 보고서 §8) ---
# AI-generated (코드 정합화, AI 로그 #3 개발자 건별 #5)
class Analyzer(ABC):
    """분석 전략 인터페이스 (§8-3).

    계약: analyze(text) -> AnalysisResult
    - 실패 시에도 예외를 전파하지 않고 오류 정보를 담은 AnalysisResult를 반환한다.
      (워커 스레드 예외 전파 금지 — §8-3·§9-3 LSP 계약, 코딩 표준 §11)
    """

    @abstractmethod
    def analyze(self, text: str) -> AnalysisResult:
        raise NotImplementedError


# AI-generated (AI 로그 #4 건별 #2 원본 — 정합화 커밋에서 원본 기준 복원, 오프라인 시연·회귀 테스트용 전략으로 유지, §8-4)
class MockAnalyzer(Analyzer):
    """네트워크 없이 UI·스레드 동작을 검증하기 위한 더미 전략"""

    def analyze(self, text: str) -> AnalysisResult:
        time.sleep(0.5)
        return AnalysisResult(
            trust_score=75,
            bias_summary="해당 텍스트는 특정 정치적 성향에 편향되지 않은 중립적인 사실 보도에 가깝습니다.",
            articles=[
                Article("유사 기사 1: A일보 사실 확인 결과", "http://example.com/1"),
                Article("유사 기사 2: B뉴스 관련 보도", "http://example.com/2"),
                Article("유사 기사 3: C방송 팩트체크", "http://example.com/3"),
            ],
        )


# AI-generated, modified: google-generativeai 라이브러리 → REST 직접 호출 전면 교체,
#                         HTTP 오류 코드 UI 출력 보강 (AI 로그 #4 건별 #3 수정 1·2)
class AIAnalyzer(Analyzer):
    """생성형 AI(Gemini) REST API 직접 호출 전략 (5/18 회의 결정 3)"""

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.endpoint = GEMINI_ENDPOINT

    def analyze(self, text: str) -> AnalysisResult:
        if text == "OCR_FAILED_DUMMY_TEXT" or len(text.strip()) < MIN_TEXT_LENGTH:
            # UC-02 S2-1a(30자 미만): 제품 비전은 오버레이 미표시이나,
            # 수동 트리거 프로토타입에서는 사유 메시지를 표시한다
            return AnalysisResult(0, "인식된 텍스트가 없거나 30자 미만이어서 분석하지 않습니다.", [])

        prompt = f"""
        당신은 뉴스 및 SNS 텍스트의 신뢰도와 편향성을 분석하는 팩트체크 시스템 'TrueFilter'입니다.
        아래 [입력 텍스트]를 분석하여 반드시 제시된 JSON 형식으로만 응답하십시오. (마크다운 백틱 없이 순수 JSON만 출력할 것)

        [입력 텍스트]
        {text}

        [분석 조건]
        1. trust_score: 텍스트의 논리성, 출처 명확성을 바탕으로 0~100 사이의 신뢰도 점수 산출
        2. bias_summary: 텍스트의 정치/사회적 편향성에 대해 객관적으로 1문장으로 요약
        3. articles: 이 주제와 관련된 검색 가능한 실제 기사 또는 가상의 관련 기사 제목 3개 제공

        [출력 JSON 포맷]
        {{
          "trust_score": 85,
          "bias_summary": "이 텍스트는 특정 정치적 입장을 대변하고 있으나 팩트에 기반하여 서술되었습니다.",
          "articles": [
            {{"title": "관련 주제 뉴스 기사 제목 1", "source_url": "https://news.naver.com"}},
            {{"title": "관련 주제 뉴스 기사 제목 2", "source_url": "https://news.naver.com"}}
          ]
        }}
        """

        try:
            url = f"{self.endpoint}?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt}]}]}

            response = requests.post(url, headers=headers, json=payload)

            # API 오류 가시화: 상태 코드·응답 본문을 UI에 그대로 노출 (§8-3)
            if response.status_code != 200:
                return AnalysisResult(0, f"API 호출 오류 ({response.status_code}): {response.text}", [])

            result_json = response.json()
            raw_text = result_json['candidates'][0]['content']['parts'][0]['text']

            # JSON 파싱 방어: 코드블록 구문 제거·파싱 예외를 전략 내부에 격리 (§8-3)
            raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_text)

            articles = [Article(a.get('title', ''), a.get('source_url', '')) for a in data.get('articles', [])]

            return AnalysisResult(
                trust_score=int(data.get('trust_score', 0)),
                bias_summary=data.get('bias_summary', "편향도 분석 결과를 가져오지 못했습니다."),
                articles=articles,
            )

        except Exception as e:
            # 실패 시에도 예외 대신 오류 결과 반환 — Analyzer 계약 (§8-3·§9-3)
            return AnalysisResult(0, f"AI 분석 중 오류가 발생했습니다: {str(e)}", [])


# --- 5. 비동기 처리 스레드 ---
# AI-generated, modified: 전략 주입 구조 명시화 (§8 정합화 — AI 로그 #3 개발자 건별 #5)
class AnalysisThread(QThread):
    analysis_completed = pyqtSignal(AnalysisResult)
    error_occurred = pyqtSignal(str)

    def __init__(self, analyzer: Optional[Analyzer] = None):
        super().__init__()
        # §8 Strategy: 컨텍스트는 Analyzer 인터페이스에만 의존 —
        # Mock/AI/FactCheck(향후) 전략 교체 시 본 클래스는 수정하지 않는다 (OCP, §9-2)
        self.analyzer: Analyzer = analyzer if analyzer is not None else AIAnalyzer()

    def run(self):
        # NOTE(§9-1): 캡처+OCR+분석 호출이 한 메서드에 있는 SRP 위반은 식별된 상태로 유지
        #             (개선 방향: 캡처·OCR을 TextRecognizer 클래스로 추출 — 후속 과제)
        try:
            # 1. 화면 캡처 (FR-01: 단축키 트리거 시 커서 주변 영역)
            with mss() as sct:
                x, y = QCursor.pos().x(), QCursor.pos().y()
                monitor = {"top": max(0, y - 300), "left": max(0, x - 400), "width": 800, "height": 600}
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 2. OCR 텍스트 추출 (Tesseract 미설치 시 더미 텍스트 폴백)
            try:
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
                extracted_text = pytesseract.image_to_string(img, lang='kor+eng')
            except Exception:
                extracted_text = "OCR_FAILED_DUMMY_TEXT"

            # 3. 분석 전략 실행 (§8)
            result = self.analyzer.analyze(extracted_text)

            self.analysis_completed.emit(result)

        except Exception as e:
            self.error_occurred.emit(str(e))


# --- 6. Overlay UI ---
# AI-generated, modified: 신뢰도 5단계 라벨 표시(FR-02), 피드백 버튼 복원(FR-05 — print 수준) (정합화 — AI 로그 #3 개발자 건별 #5)
class OverlayWindow(QWidget):
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()
        # 시연 기본 전략: AIAnalyzer
        # (오프라인 테스트 시 AnalysisThread(MockAnalyzer())로 교체 — 호출부 그 외 수정 없음, §8-4)
        self.worker = AnalysisThread()
        self.worker.analysis_completed.connect(self.update_ui_with_result)
        self.hotkey_pressed.connect(self.start_analysis)
        self.oldPos = self.pos()
        self.current_result: Optional[AnalysisResult] = None

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.resize(350, 420)

        self.setStyleSheet("""
            QWidget { background-color: rgba(30, 30, 30, 230); color: white; border-radius: 10px; }
            QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; width: 10px; }
            QSlider::handle:horizontal { background: #4CAF50; width: 15px; border-radius: 7px; }
        """)

        layout = QVBoxLayout()
        self.status_label = QLabel("TrueFilter - 대기 중 (Ctrl+Shift+F)")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)

        layout.addWidget(QLabel("신뢰도 점수 (AI 산출, 5단계)"))
        self.trust_bar = QProgressBar()
        self.trust_bar.setValue(0)
        layout.addWidget(self.trust_bar)

        # FR-02: 0~100 점수의 5단계 레벨 라벨
        self.level_label = QLabel("레벨: -")
        layout.addWidget(self.level_label)

        layout.addWidget(QLabel("편향도 분석 결과"))
        self.bias_label = QLabel("분석 결과가 여기에 표시됩니다.")
        self.bias_label.setWordWrap(True)
        self.bias_label.setStyleSheet("background-color: rgba(50, 50, 50, 200); padding: 5px;")
        layout.addWidget(self.bias_label)

        layout.addWidget(QLabel("유사 기사 제안"))
        self.article_list = QListWidget()
        layout.addWidget(self.article_list)

        control_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)  # FR-03: 투명도 조절
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v / 100.0))
        control_layout.addWidget(QLabel("투명도"))
        control_layout.addWidget(self.opacity_slider)

        # FR-05: 피드백 전송 — 프로토타입 미구현 (인스펙션 결함 #4, 미수정 — 우선순위 '하', 향후 과제)
        feedback_btn = QPushButton("오류 신고")
        feedback_btn.clicked.connect(self.send_feedback)
        control_layout.addWidget(feedback_btn)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.hide)
        control_layout.addWidget(close_btn)

        layout.addLayout(control_layout)
        self.setLayout(layout)

    def start_analysis(self):
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.show()
        self.status_label.setText("AI 분석 중... (약 2~4초 소요)")
        self.trust_bar.setValue(0)
        self.level_label.setText("레벨: -")
        self.bias_label.setText("화면의 텍스트를 읽고 AI가 분석하고 있습니다.")
        self.article_list.clear()
        if not self.worker.isRunning():
            self.worker.start()

    def update_ui_with_result(self, result: AnalysisResult):
        self.current_result = result
        self.status_label.setText("분석 완료")
        self.trust_bar.setValue(result.trust_score)
        self.level_label.setText(f"레벨: {result.get_trust_level()} ({result.trust_score}점)")  # FR-02 5단계 매핑
        self.bias_label.setText(result.bias_summary)
        for article in result.articles:
            self.article_list.addItem(f"[{article.title}]")

    def send_feedback(self):
        # FR-05 미구현: 실제 전송·저장 없이 콘솔 출력만 수행 (§10-2 결함 #4 — 미수정, 향후 과제)
        print("[TrueFilter] 피드백 전송 요청 — FR-05는 프로토타입 범위에서 미구현 (print 수준)")

    def mousePressEvent(self, event):  # FR-03: 드래그 이동
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.oldPos:
            return
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()


# --- 7. 엔트리 포인트 ---
def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = OverlayWindow()
    keyboard.add_hotkey('ctrl+shift+f', lambda: overlay.hotkey_pressed.emit())  # FR-01 트리거
    print("TrueFilter AI 프로토타입 실행 준비 완료.")
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
