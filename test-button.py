#!/usr/bin/env python3
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QTextEdit
import sys

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Тест кнопки")
window.setGeometry(100, 100, 400, 300)

layout = QVBoxLayout()

text = QTextEdit()
text.setPlaceholderText("Лог нажатий...")

def on_click():
    text.append("✅ Кнопка нажата!")
    print("Кнопка нажата!")

btn = QPushButton("Нажми меня")
btn.clicked.connect(on_click)

layout.addWidget(btn)
layout.addWidget(text)
window.setLayout(layout)

window.show()
print("Окно создано, нажмите кнопку")
sys.exit(app.exec_())
