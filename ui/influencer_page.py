"""
TikTok Monitor - Influencer Management Page
Supports TikTok / Douyin account management.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from core.platforms import format_account_identity, infer_platform_from_input, normalize_influencer_input, platform_label


TABLE_STYLE = """
QTableWidget {
    background-color: #1a1a2e;
    border: 1px solid #2d3748;
    border-radius: 8px;
    color: #e2e8f0;
    gridline-color: #2d3748;
    font-size: 13px;
}
QTableWidget::item { padding: 10px 12px; border-bottom: 1px solid #2d3748; }
QTableWidget::item:selected { background-color: #2d3748; }
QHeaderView::section {
    background-color: #16213e;
    color: #a0aec0;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid #2d3748;
    font-size: 12px;
    font-weight: 600;
}
"""

BTN_PRIMARY = """
QPushButton {
    background-color: #e53e3e;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover { background-color: #c53030; }
"""

BTN_SECONDARY = """
QPushButton {
    background-color: #2d3748;
    color: #e2e8f0;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton:hover { background-color: #4a5568; }
"""

BTN_DANGER = """
QPushButton {
    background-color: transparent;
    color: #fc8181;
    border: 1px solid #fc8181;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
}
QPushButton:hover { background-color: #742a2a; }
"""


class AddInfluencerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加监控账号")
        self.setModal(True)
        self.setMinimumWidth(460)
        self.setStyleSheet(
            """
            QDialog { background-color: #1a1a2e; color: #e2e8f0; }
            QLabel { color: #e2e8f0; font-size: 14px; }
            QLineEdit, QComboBox {
                background-color: #2d3748;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus { border-color: #e53e3e; }
            QDialogButtonBox QPushButton {
                background-color: #e53e3e;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
            }
            QDialogButtonBox QPushButton:hover { background-color: #c53030; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("添加 TikTok / 抖音账号")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel("TikTok 可输入用户名或主页链接。抖音请使用主页链接或分享链接添加，不要只填昵称。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #a0aec0; font-size: 12px;")
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(12)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem("TikTok", "tiktok")
        self.platform_combo.addItem("抖音", "douyin")
        form.addRow("平台*", self.platform_combo)

        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("例如: @charlidamelio 或 https://www.douyin.com/user/xxxx")
        form.addRow("账号 / 链接*", self.account_input)

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("可选，用于列表备注")
        form.addRow("备注名称", self.display_name_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("确认添加")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setStyleSheet(
            "QPushButton { background-color: #2d3748; color: #e2e8f0; border: none; border-radius: 6px; padding: 8px 20px; }"
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        raw_input = self.account_input.text().strip()
        selected_platform = self.platform_combo.currentData()
        platform = infer_platform_from_input(raw_input) if "http" in raw_input else selected_platform
        username, profile_url = normalize_influencer_input(raw_input, platform)
        return {
            "platform": platform,
            "username": username,
            "profile_url": profile_url,
            "display_name": self.display_name_input.text().strip(),
            "account_label": format_account_identity(platform, username, profile_url),
        }


class InfluencerPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.setStyleSheet("background-color: #0f0f1a;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_row = QHBoxLayout()
        title = QLabel("账号管理")
        title.setStyleSheet("color: #e2e8f0; font-size: 22px; font-weight: bold;")
        title_row.addWidget(title)
        title_row.addStretch()

        add_btn = QPushButton("+ 添加账号")
        add_btn.setStyleSheet(BTN_PRIMARY)
        add_btn.clicked.connect(self._add_influencer)
        title_row.addWidget(add_btn)

        fetch_all_btn = QPushButton("立即抓取全部")
        fetch_all_btn.setStyleSheet(BTN_SECONDARY)
        fetch_all_btn.clicked.connect(self._fetch_all)
        title_row.addWidget(fetch_all_btn)
        layout.addLayout(title_row)

        hint = QLabel("统一管理 TikTok 和抖音账号。添加后可手动抓取，也可配合设置页里的自动抓取一起使用。")
        hint.setStyleSheet("color: #718096; font-size: 13px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setStyleSheet(TABLE_STYLE + "QTableWidget { alternate-background-color: #16213e; }")
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            ["平台", "账号", "备注", "粉丝数", "视频数", "最佳表现", "监控状态", "上次抓取", "操作", ""]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in range(3, 10):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def refresh(self):
        from data.database import get_all_influencers, get_connection

        influencers = get_all_influencers()
        conn = get_connection()
        video_counts = {}
        best_performances = {}
        for influencer in influencers:
            influencer_id = influencer["id"]
            video_counts[influencer_id] = conn.execute(
                "SELECT COUNT(*) AS cnt FROM videos WHERE influencer_id=?",
                (influencer_id,),
            ).fetchone()["cnt"]
            best_row = conn.execute(
                "SELECT MAX(play_count) AS max_play FROM videos WHERE influencer_id=?",
                (influencer_id,),
            ).fetchone()
            best_performances[influencer_id] = best_row["max_play"] if best_row and best_row["max_play"] else 0
        conn.close()

        self.table.setRowCount(len(influencers))
        for row, influencer in enumerate(influencers):
            platform = influencer.get("platform", "tiktok")
            account_text = format_account_identity(platform, influencer.get("username", ""), influencer.get("profile_url", ""))
            self.table.setItem(row, 0, QTableWidgetItem(platform_label(platform)))
            self.table.setItem(row, 1, QTableWidgetItem(account_text))
            self.table.setItem(row, 2, QTableWidgetItem(influencer.get("display_name") or ""))
            self.table.setItem(row, 3, QTableWidgetItem(self._format_number(influencer.get("follower_count", 0))))
            self.table.setItem(row, 4, QTableWidgetItem(str(video_counts.get(influencer["id"], 0))))

            best_play = best_performances.get(influencer["id"], 0)
            best_item = QTableWidgetItem(self._format_number(best_play) if best_play else "暂无数据")
            best_item.setForeground(QColor("#f6ad55" if best_play >= 1_000_000 else "#68d391" if best_play >= 100_000 else "#a0aec0"))
            self.table.setItem(row, 5, best_item)

            is_active = bool(influencer.get("is_active", 1))
            status_item = QTableWidgetItem("监控中" if is_active else "已暂停")
            status_item.setForeground(QColor("#68d391") if is_active else QColor("#a0aec0"))
            self.table.setItem(row, 6, status_item)
            self.table.setItem(row, 7, QTableWidgetItem(influencer.get("last_fetched_at") or "从未抓取"))

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            fetch_btn = QPushButton("立即抓取")
            fetch_btn.setStyleSheet(BTN_SECONDARY)
            fetch_btn.clicked.connect(lambda _, inf=influencer: self._fetch_single(inf))
            btn_layout.addWidget(fetch_btn)

            view_btn = QPushButton("查看数据")
            view_btn.setStyleSheet(BTN_SECONDARY)
            view_btn.clicked.connect(lambda _, inf=influencer: self._view_data(inf))
            btn_layout.addWidget(view_btn)
            self.table.setCellWidget(row, 8, btn_widget)

            del_btn = QPushButton("删除")
            del_btn.setStyleSheet(BTN_DANGER)
            del_btn.clicked.connect(lambda _, inf=influencer: self._delete_influencer(inf))
            self.table.setCellWidget(row, 9, del_btn)
            self.table.setRowHeight(row, 52)

    def _add_influencer(self):
        dialog = AddInfluencerDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()
        if not data["username"]:
            if data["platform"] == "douyin":
                QMessageBox.warning(self, "输入错误", "抖音账号请使用主页链接或分享链接添加，不能只填昵称。")
            else:
                QMessageBox.warning(self, "输入错误", "请输入有效的 TikTok 用户名或主页链接。")
            return

        from data.database import add_influencer

        row_id = add_influencer(
            username=data["username"],
            display_name=data["display_name"],
            profile_url=data["profile_url"],
            platform=data["platform"],
        )
        if row_id:
            self.refresh()
            QMessageBox.information(
                self,
                "添加成功",
                f"{platform_label(data['platform'])} 账号 {data['account_label']} 已加入监控列表。",
            )
            return

        QMessageBox.warning(self, "添加失败", "该账号可能已经存在于监控列表中。")

    def _fetch_single(self, influencer: dict):
        self.main_window.fetch_single(influencer)

    def _fetch_all(self):
        from ui.main_window import FetchWorker

        worker = FetchWorker(self.main_window.fetch_all_active)
        worker.signals.finished.connect(lambda _: self.refresh())
        worker.start()
        self._worker = worker

    def _view_data(self, influencer: dict):
        self.main_window.data_view_page.set_influencer(influencer)
        self.main_window.navigate_to(2)

    def _delete_influencer(self, influencer: dict):
        account_text = format_account_identity(
            influencer.get("platform"),
            influencer.get("username", ""),
            influencer.get("profile_url", ""),
        )
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除 {platform_label(influencer.get('platform'))} 账号 {account_text} 吗？\n\n相关视频数据也会被删除。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from data.database import delete_influencer

            delete_influencer(influencer["id"])
            self.refresh()

    def _format_number(self, value):
        value = value or 0
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.0f}K"
        return str(int(value))
