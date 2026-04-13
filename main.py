"""
Main entry point for the dual-platform monitor app.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

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
                stop:0 #0f0f1a, stop:0.5 #1a1a2e, stop:1 #16213e);
            border-radius: 12px;
        }
        """
    )
    splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    splash_label.setText(
        """
        <div style='text-align:center; color:white;'>
            <div style='font-size:44px; margin-bottom:12px;'>SV</div>
            <div style='font-size:24px; font-weight:bold; color:#e2e8f0;'>Short Video Monitor</div>
            <div style='font-size:14px; color:#718096; margin-top:8px;'>TikTok / 抖音双平台监控与分析</div>
            <div style='font-size:12px; color:#4a5568; margin-top:24px;'>正在初始化...</div>
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

    font = QFont("Microsoft YaHei", 10) if sys.platform == "win32" else QFont("PingFang SC", 10)
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
