"""
Main entry point for the dual-platform monitor app.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

# 导入 config.py 会自动加载 .env 文件（若不存在则从 .env.example 复制）
import config

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication, QLabel


def create_splash():
    splash_label = QLabel()
    splash_label.setFixedSize(480, 280)
    splash_label.setStyleSheet(
        """
        QLabel {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #0d1522, stop:0.52 #142033, stop:1 #213551);
            border: 1px solid #34506f;
            border-radius: 18px;
        }
        """
    )
    splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash_label.setText(
        """
        <div style='text-align:center; color:white; font-family:"Microsoft YaHei","Segoe UI",sans-serif;'>
            <div style='font-size:46px; margin-bottom:12px; color:#ff7a59; font-weight:800;'>SV</div>
            <div style='font-size:24px; font-weight:bold; color:#edf3ff;'>Short Video Monitor</div>
            <div style='font-size:14px; color:#aab9cf; margin-top:8px;'>TikTok / 抖音双平台监控与分析</div>
            <div style='font-size:12px; color:#7f8ea7; margin-top:24px;'>正在初始化...</div>
        </div>
        """
    )
    splash_label.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
    return splash_label


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Short Video Monitor")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("ManusAI")

    font = QFont("Microsoft YaHei UI", 10) if sys.platform == "win32" else QFont("PingFang SC", 10)
    app.setFont(font)

    splash = create_splash()
    splash.show()
    app.processEvents()

    def load_main():
        from ui.main_window import MainWindow

        window = MainWindow()
        window.show()
        splash.close()

    QTimer.singleShot(1200, load_main)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
