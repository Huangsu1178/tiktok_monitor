"""
TikTok Monitor - Selection Dialog
两阶段选择弹窗组件：先选博主 → 再选视频
支持多选、条件排序、搜索过滤
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
)

from core.platforms import platform_label
from ui.components.theme import (
    ACCENT,
    ACCENT_HOVER,
    BG_PANEL,
    BG_SURFACE,
    BG_SURFACE_HOVER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    input_style,
)


class InfluencerSelectionStep(QWidget):
    """第一阶段：博主选择"""
    
    selection_completed = pyqtSignal(list)  # 返回选中的博主列表
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_influencers = []
        self.all_influencers = []
        self._build_ui()
        self._load_data()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # 标题
        title = QLabel("选择博主（可多选）")
        title.setStyleSheet("color: #f4f8ff; font-size: 15px; font-weight: 700;")
        layout.addWidget(title)
        
        # 排序控制
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(10)
        
        sort_label = QLabel("排序:")
        sort_label.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("默认", "default")
        self.sort_combo.addItem("粉丝数 ↓", "followers_desc")
        self.sort_combo.addItem("粉丝数 ↑", "followers_asc")
        self.sort_combo.addItem("最火视频播放 ↓", "top_video_desc")
        self.sort_combo.addItem("用户名 A-Z", "username_asc")
        self.sort_combo.addItem("用户名 Z-A", "username_desc")
        self.sort_combo.setStyleSheet(input_style(180))
        self.sort_combo.currentIndexChanged.connect(self._apply_sort)
        sort_layout.addWidget(self.sort_combo)
        
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索博主用户名或平台...")
        self.search_input.setStyleSheet(input_style(200))
        self.search_input.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_input)
        
        # 博主列表（表格形式，支持多选）
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["选择", "平台", "用户名", "粉丝数"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 50)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {BG_SURFACE_HOVER};
            }}
            QHeaderView::section {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
                padding: 8px;
                border: none;
                font-weight: 600;
            }}
        """)
        layout.addWidget(self.table)
        
        # 已选数量提示
        self.count_label = QLabel("已选: 0 个博主")
        self.count_label.setStyleSheet("color: #8fa6c9; font-size: 12px;")
        layout.addWidget(self.count_label)
    
    def _load_data(self):
        from data.database import get_all_influencers
        self.all_influencers = get_all_influencers()
        self._apply_sort()
    
    def _apply_sort(self):
        sort_key = self.sort_combo.currentData()
        
        if sort_key == "default":
            sorted_data = self.all_influencers[:]
        elif sort_key == "followers_desc":
            sorted_data = sorted(self.all_influencers, key=lambda x: x.get("follower_count", 0), reverse=True)
        elif sort_key == "followers_asc":
            sorted_data = sorted(self.all_influencers, key=lambda x: x.get("follower_count", 0))
        elif sort_key == "top_video_desc":
            sorted_data = sorted(self.all_influencers, key=lambda x: x.get("max_play_count", 0), reverse=True)
        elif sort_key == "username_asc":
            sorted_data = sorted(self.all_influencers, key=lambda x: x.get("username", ""))
        elif sort_key == "username_desc":
            sorted_data = sorted(self.all_influencers, key=lambda x: x.get("username", ""), reverse=True)
        else:
            sorted_data = self.all_influencers[:]
        
        self._render_table(sorted_data)
    
    def _apply_filter(self):
        keyword = self.search_input.text().lower()
        if not keyword:
            self._apply_sort()
            return
        
        filtered = [
            inf for inf in self.all_influencers
            if keyword in inf.get("username", "").lower() or
               keyword in platform_label(inf.get("platform")).lower()
        ]
        self._render_table(filtered)
    
    def _render_table(self, influencers):
        self.table.setRowCount(len(influencers))
        
        for row, influencer in enumerate(influencers):
            # 复选框
            checkbox = QCheckBox()
            checkbox.setChecked(influencer in self.selected_influencers)
            checkbox.stateChanged.connect(lambda state, inf=influencer: self._on_checkbox_changed(state, inf))
            self.table.setCellWidget(row, 0, checkbox)
            
            # 平台
            platform_item = QTableWidgetItem(platform_label(influencer.get("platform")))
            platform_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, platform_item)
            
            # 用户名
            username_item = QTableWidgetItem(influencer.get("username", ""))
            self.table.setItem(row, 2, username_item)
            
            # 粉丝数
            follower_count = influencer.get("follower_count", 0)
            follower_item = QTableWidgetItem(f"{follower_count:,}")
            follower_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, follower_item)
    
    def _on_checkbox_changed(self, state, influencer):
        if state == Qt.CheckState.Checked.value:
            if influencer not in self.selected_influencers:
                self.selected_influencers.append(influencer)
        else:
            if influencer in self.selected_influencers:
                self.selected_influencers.remove(influencer)
        
        self.count_label.setText(f"已选: {len(self.selected_influencers)} 个博主")
    
    def get_selected(self):
        return self.selected_influencers[:]



class SelectionDialog(QDialog):
    """通用选择弹窗"""
    
    # 信号：返回选中的数据列表
    selection_completed = pyqtSignal(list)
    
    def __init__(self, parent=None, title="选择", selection_type="influencer", 
                 allow_multiple=True, sort_options=None):
        """
        初始化选择弹窗
        
        Args:
            parent: 父窗口
            title: 弹窗标题
            selection_type: 选择类型 ('influencer' 或 'video')
            allow_multiple: 是否允许多选
            sort_options: 排序选项列表
        """
        super().__init__(parent)
        self.selection_type = selection_type
        self.allow_multiple = allow_multiple
        self.selected_items = []
        self.all_data = []
        
        # 默认排序选项
        if sort_options is None:
            if selection_type == "influencer":
                self.sort_options = [
                    ("默认", "default"),
                    ("用户名 A-Z", "username_asc"),
                    ("用户名 Z-A", "username_desc"),
                    ("平台", "platform"),
                ]
            else:  # video
                self.sort_options = [
                    ("默认", "default"),
                    ("播放量降序", "play_count_desc"),
                    ("播放量升序", "play_count_asc"),
                    ("点赞数降序", "like_count_desc"),
                    ("点赞数升序", "like_count_asc"),
                    ("评论数降序", "comment_count_desc"),
                    ("发布时间降序", "published_at_desc"),
                    ("发布时间升序", "published_at_asc"),
                ]
        else:
            self.sort_options = sort_options
        
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        self._build_ui()
        self._load_data()
    
    def _build_ui(self):
        """构建UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title_label = QLabel(self.windowTitle())
        title_label.setStyleSheet("color: #f4f8ff; font-size: 18px; font-weight: 700;")
        layout.addWidget(title_label)
        
        # 如果是视频选择，先显示博主选择
        if self.selection_type == "video":
            influencer_layout = QHBoxLayout()
            influencer_layout.setSpacing(12)
            
            influencer_label = QLabel("选择博主:")
            influencer_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
            influencer_layout.addWidget(influencer_label)
            
            self.influencer_combo = QComboBox()
            self.influencer_combo.setStyleSheet(input_style(200))
            self.influencer_combo.addItem("请选择博主", None)
            self.influencer_combo.currentIndexChanged.connect(self._on_influencer_selected)
            influencer_layout.addWidget(self.influencer_combo)
            
            influencer_layout.addStretch()
            layout.addLayout(influencer_layout)
        
        # 排序控制区
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(12)
        
        sort_label = QLabel("排序方式:")
        sort_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        sort_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        for label, value in self.sort_options:
            self.sort_combo.addItem(label, value)
        self.sort_combo.setStyleSheet(input_style(200))
        self.sort_combo.currentIndexChanged.connect(self._apply_sort)
        sort_layout.addWidget(self.sort_combo)
        
        sort_layout.addStretch()
        layout.addLayout(sort_layout)
        
        # 搜索框（可选）
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)
        
        search_label = QLabel("搜索:")
        search_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
        search_layout.addWidget(search_label)
        
        self.search_input = QComboBox()
        self.search_input.setEditable(True)
        self.search_input.setStyleSheet(input_style(200))
        self.search_input.setPlaceholderText("输入关键词搜索...")
        self.search_input.lineEdit().textChanged.connect(self._apply_filter)
        search_layout.addWidget(self.search_input)
        
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        # 列表区域
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER};
                border-radius: 12px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                padding: 8px;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {BORDER};
                border-radius: 6px;
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background-color: {BG_SURFACE};
            }}
            QListWidget::item:selected {{
                background-color: {BG_SURFACE_HOVER};
                border: 1px solid {ACCENT};
            }}
            """
        )
        
        if self.allow_multiple:
            self.list_widget.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        else:
            self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.list_widget)
        
        # 已选数量标签
        if self.allow_multiple:
            self.count_label = QLabel("已选: 0")
            self.count_label.setStyleSheet("color: #8fa6c9; font-size: 13px;")
            layout.addWidget(self.count_label)
        
        # 按钮区
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_PANEL};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {BG_SURFACE};
            }}
            """
        )
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("确认选择")
        confirm_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            """
        )
        confirm_btn.clicked.connect(self._confirm_selection)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self):
        """加载数据"""
        from data.database import get_all_influencers, get_videos_by_influencer
        
        if self.selection_type == "influencer":
            self.all_data = get_all_influencers()
            self._apply_sort()
        else:  # video
            # 视频需要先选择博主，这里只加载博主列表
            self.all_influencers = get_all_influencers()
            self.all_data = []
            
            # 加载博主下拉框
            if hasattr(self, 'influencer_combo'):
                for influencer in self.all_influencers:
                    label = f"{platform_label(influencer.get('platform'))} | @{influencer.get('username', '')}"
                    self.influencer_combo.addItem(label, influencer)
    
    def _on_influencer_selected(self, index: int):
        """博主选择改变"""
        from data.database import get_videos_by_influencer
        
        influencer = self.influencer_combo.itemData(index)
        if not influencer:
            self.all_data = []
            self._apply_filter()
            return
        
        # 加载该博主的视频
        videos = get_videos_by_influencer(influencer["id"], 100)
        for video in videos:
            video["influencer_username"] = influencer.get("username", "")
            video["influencer_platform"] = influencer.get("platform", "")
        
        self.all_data = videos
        self._apply_sort()
    
    def _apply_sort(self):
        """应用排序"""
        sort_value = self.sort_combo.currentData()
        
        if self.selection_type == "influencer":
            if sort_value == "username_asc":
                self.all_data.sort(key=lambda x: x.get("username", "").lower())
            elif sort_value == "username_desc":
                self.all_data.sort(key=lambda x: x.get("username", "").lower(), reverse=True)
            elif sort_value == "platform":
                self.all_data.sort(key=lambda x: (x.get("platform", ""), x.get("username", "")))
        else:  # video
            if sort_value == "play_count_desc":
                self.all_data.sort(key=lambda x: x.get("play_count", 0), reverse=True)
            elif sort_value == "play_count_asc":
                self.all_data.sort(key=lambda x: x.get("play_count", 0))
            elif sort_value == "like_count_desc":
                self.all_data.sort(key=lambda x: x.get("like_count", 0), reverse=True)
            elif sort_value == "like_count_asc":
                self.all_data.sort(key=lambda x: x.get("like_count", 0))
            elif sort_value == "comment_count_desc":
                self.all_data.sort(key=lambda x: x.get("comment_count", 0), reverse=True)
            elif sort_value == "published_at_desc":
                self.all_data.sort(key=lambda x: x.get("published_at", ""), reverse=True)
            elif sort_value == "published_at_asc":
                self.all_data.sort(key=lambda x: x.get("published_at", ""))
        
        self._apply_filter()
    
    def _apply_filter(self):
        """应用过滤"""
        search_text = self.search_input.currentText().lower()
        
        self.list_widget.clear()
        
        filtered_data = self.all_data
        if search_text:
            if self.selection_type == "influencer":
                filtered_data = [
                    item for item in self.all_data
                    if search_text in item.get("username", "").lower() or
                       search_text in item.get("platform", "").lower()
                ]
            else:  # video
                filtered_data = [
                    item for item in self.all_data
                    if search_text in (item.get("description") or item.get("title") or "").lower() or
                       search_text in item.get("influencer_username", "").lower()
                ]
        
        for item in filtered_data:
            if self.selection_type == "influencer":
                label = f"{platform_label(item.get('platform'))} | @{item.get('username', '')}"
            else:  # video
                desc = (item.get("description") or item.get("title") or "无描述").replace("\n", " ")
                username = item.get("influencer_username", "")
                play_count = item.get("play_count", 0)
                label = f"@{username} | {desc[:50]}{'...' if len(desc) > 50 else ''} | 播放: {play_count:,}"
            
            list_item = QListWidgetItem(label)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            
            if self.allow_multiple:
                list_item.setFlags(list_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                list_item.setCheckState(Qt.CheckState.Unchecked)
            
            self.list_widget.addItem(list_item)
        
        if self.allow_multiple:
            self._update_count()
    
    def _update_count(self):
        """更新已选数量"""
        count = 0
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                count += 1
        self.count_label.setText(f"已选: {count}")
    
    def _confirm_selection(self):
        """确认选择"""
        self.selected_items = []
        
        if self.allow_multiple:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    data = item.data(Qt.ItemDataRole.UserRole)
                    if data:
                        self.selected_items.append(data)
        else:
            selected_items = self.list_widget.selectedItems()
            if selected_items:
                data = selected_items[0].data(Qt.ItemDataRole.UserRole)
                if data:
                    self.selected_items.append(data)
        
        self.selection_completed.emit(self.selected_items)
        self.accept()
    
    def get_selected_items(self):
        """获取选中的数据"""
        return self.selected_items


def show_influencer_selection(parent=None, title="选择博主", allow_multiple=True, sort_options=None):
    """显示博主选择弹窗"""
    dialog = SelectionDialog(
        parent=parent,
        title=title,
        selection_type="influencer",
        allow_multiple=allow_multiple,
        sort_options=sort_options
    )
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        return dialog.get_selected_items()
    return []


def show_video_selection(parent=None, title="选择视频", allow_multiple=True, sort_options=None):
    """显示视频选择弹窗"""
    dialog = SelectionDialog(
        parent=parent,
        title=title,
        selection_type="video",
        allow_multiple=allow_multiple,
        sort_options=sort_options
    )
    result = dialog.exec()
    if result == QDialog.DialogCode.Accepted:
        return dialog.get_selected_items()
    return []
