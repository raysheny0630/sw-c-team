import sys
import json
import keyboard
import pytesseract
import requests
from mss import mss
from PIL import Image
from dataclasses import dataclass
from typing import List
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QProgressBar, QSlider, QListWidget, QPushButton, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QCursor

# ---------------------------------------------------------
# [필수 설정] 발급받은 Gemini API 키를 입력하세요.
# ---------------------------------------------------------
GEMINI_API_KEY = "API_KEY"

# --- 1. Data Models ---
@dataclass
class Article:
    title: str
    source_url: str

@dataclass
class AnalysisResult:
    trust_score: int
    bias_summary: str
    articles: List[Article]

# --- 2. AI Analyzer Module (REST API 직접 통신 방식) ---
class AIAnalyzer:
    def analyze(self, text: str) -> AnalysisResult:
        if text == "OCR_FAILED_DUMMY_TEXT" or len(text.strip()) < 10:
            return AnalysisResult(0, "인식된 텍스트가 없거나 너무 짧아 분석할 수 없습니다.", [])

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
            # 여기 url 변수가 새로 추가되었습니다.
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                return AnalysisResult(0, f"API 호출 오류 ({response.status_code}): {response.text}", [])
            
            result_json = response.json()
            raw_text = result_json['candidates'][0]['content']['parts'][0]['text']
            
            raw_text = raw_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(raw_text)
            
            articles = [Article(a.get('title', ''), a.get('source_url', '')) for a in data.get('articles', [])]
            
            return AnalysisResult(
                trust_score=int(data.get('trust_score', 0)),
                bias_summary=data.get('bias_summary', "편향도 분석 결과를 가져오지 못했습니다."),
                articles=articles
            )

        except Exception as e:
            return AnalysisResult(0, f"AI 분석 중 오류가 발생했습니다: {str(e)}", [])

# --- 3. 이후의 Thread 및 UI 클래스는 이전과 동일하게 유지하시면 됩니다 ---
# (이하 생략)
# --- 3. 비동기 처리 스레드 ---
class AnalysisThread(QThread):
    analysis_completed = pyqtSignal(AnalysisResult)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            # 1. 화면 캡처
            with mss() as sct:
                x, y = QCursor.pos().x(), QCursor.pos().y()
                monitor = {"top": max(0, y - 300), "left": max(0, x - 400), "width": 800, "height": 600}
                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

            # 2. OCR 텍스트 추출 (경로 확인 필수)
            try:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Ditto\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
                extracted_text = pytesseract.image_to_string(img, lang='kor+eng')
            except Exception:
                extracted_text = "OCR_FAILED_DUMMY_TEXT"

            # 3. AI 분석 실행 (Gemini API 호출)
            analyzer = AIAnalyzer()
            result = analyzer.analyze(extracted_text)
            
            self.analysis_completed.emit(result)

        except Exception as e:
            self.error_occurred.emit(str(e))

# --- 4. Overlay UI 클래스 (이전과 동일) ---
class OverlayWindow(QWidget):
    hotkey_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.initUI()
        self.worker = AnalysisThread()
        self.worker.analysis_completed.connect(self.update_ui_with_result)
        self.hotkey_pressed.connect(self.start_analysis)
        self.oldPos = self.pos()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.resize(350, 400)
        
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

        layout.addWidget(QLabel("신뢰도 점수 (AI 산출)"))
        self.trust_bar = QProgressBar()
        self.trust_bar.setValue(0)
        layout.addWidget(self.trust_bar)

        layout.addWidget(QLabel("편향도 분석 결과"))
        self.bias_label = QLabel("분석 결과가 여기에 표시됩니다.")
        self.bias_label.setWordWrap(True)
        self.bias_label.setStyleSheet("background-color: rgba(50, 50, 50, 200); padding: 5px;")
        layout.addWidget(self.bias_label)

        layout.addWidget(QLabel("유사 기사 제안"))
        self.article_list = QListWidget()
        layout.addWidget(self.article_list)

        control_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(20, 100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v / 100.0))
        control_layout.addWidget(QLabel("투명도"))
        control_layout.addWidget(self.opacity_slider)

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
        self.bias_label.setText("화면의 텍스트를 읽고 AI가 분석하고 있습니다.")
        self.article_list.clear()
        if not self.worker.isRunning():
            self.worker.start()

    def update_ui_with_result(self, result: AnalysisResult):
        self.status_label.setText("분석 완료")
        self.trust_bar.setValue(result.trust_score)
        self.bias_label.setText(result.bias_summary)
        for article in result.articles:
            self.article_list.addItem(f"[{article.title}]")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if not self.oldPos: return
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = OverlayWindow()
    keyboard.add_hotkey('ctrl+shift+f', lambda: overlay.hotkey_pressed.emit())
    print("TrueFilter AI 프로토타입 실행 준비 완료.")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
