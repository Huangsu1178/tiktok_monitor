# AB对比分析页面修改指南

## 概述
AB对比分析页面 (`ui/ab_comparison_page.py`) 需要手动修改以使用新的视频列表管理器。

## 需要修改的内容

### 1. 删除旧的选择器相关方法
删除以下方法（约在250-500行）：
- `_build_group_selector()`
- `_open_influencer_dialog()`
- `_on_group_influencer_changed()`
- `_open_video_dialog()`
- `_on_video_selection_changed()`
- `_get_selected_group_videos()`

### 2. 替换 `_build_controls()` 方法

将原有的 `_build_controls()` 方法（约在180-260行）替换为：

```python
def _build_controls(self) -> QWidget:
    """构建控制区"""
    controls = QFrame()
    controls.setStyleSheet(
        f"""
        QFrame {{
            background-color: {BG_PANEL};
            border: 1px solid {BORDER};
            border-radius: 16px;
        }}
        """
    )
    layout = QVBoxLayout(controls)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(14)
    
    # 视频列表管理器（AB对比模式）
    self.video_list_manager = VideoListManager(mode="ab_comparison")
    self.video_list_manager.videos_changed.connect(self._on_add_videos_requested)
    self.video_list_manager.analyze_requested.connect(self._run_analysis_with_videos)
    layout.addWidget(self.video_list_manager)
    
    return controls

def _on_add_videos_requested(self, data):
    """添加视频请求"""
    # data 是一个字典，包含 {"group": "A"} 或 {"group": "B"}
    if isinstance(data, dict) and "group" in data:
        group = data["group"]
        self._open_add_dialog_for_group(group)

def _open_add_dialog_for_group(self, group: str):
    """为指定组打开添加对话框"""
    selected_videos = show_two_stage_selection(
        parent=self,
        title=f"选择{group}组视频",
        allow_multiple=True
    )
    
    if selected_videos:
        self.video_list_manager.add_videos(selected_videos, group=group)
```

### 3. 替换 `_run_analysis()` 方法

将原有的 `_run_analysis()` 方法替换为：

```python
def _run_analysis_with_videos(self, video_groups):
    """执行分析（从视频列表管理器调用）"""
    if not isinstance(video_groups, dict):
        return
    
    group_a_videos = video_groups.get("group_a", [])
    group_b_videos = video_groups.get("group_b", [])
    
    if not group_a_videos:
        self._show_status("请至少选择1个A组视频", "#ffb86b")
        return
    if not group_b_videos:
        self._show_status("请至少选择1个B组视频", "#ffb86b")
        return
    
    group_a_label = "A组"
    group_b_label = "B组"
    
    # 从视频中获取博主信息
    if group_a_videos and "influencer_username" in group_a_videos[0]:
        group_a_label = group_a_videos[0]["influencer_username"]
    if group_b_videos and "influencer_username" in group_b_videos[0]:
        group_b_label = group_b_videos[0]["influencer_username"]
    
    self._render_loading()
    self._start_worker(
        group_a_videos=group_a_videos,
        group_b_videos=group_b_videos,
        group_a_label=group_a_label,
        group_b_label=group_b_label
    )
```

### 4. 替换 `refresh()` 方法

将原有的 `refresh()` 方法替换为：

```python
def refresh(self):
    """刷新数据"""
    # 重置视频列表
    if hasattr(self, 'video_list_manager'):
        self.video_list_manager.videos_a = []
        self.video_list_manager.videos_b = []
        self.video_list_manager._render_ab_list()
```

### 5. 替换 `_set_busy()` 方法

将原有的 `_set_busy()` 方法替换为：

```python
def _set_busy(self, busy: bool):
    """设置忙状态"""
    if hasattr(self, 'video_list_manager'):
        self.video_list_manager.analyze_btn.setEnabled(not busy)
    
    if busy:
        self._loading_base = "AB对比分析中"
        self._loading_step = 0
        self._loading_timer.start(380)
        self._tick_loading()
    else:
        self._loading_timer.stop()
```

### 6. 删除旧的组件引用

在 `__init__` 方法中删除：
```python
self._group_a_videos = []
self._group_b_videos = []
```

在 `_build_controls()` 或相关方法中删除对以下组件的引用：
- `self.group_a_influencer_btn`
- `self.group_a_video_btn`
- `self.group_a_count_label`
- `self.group_b_influencer_btn`
- `self.group_b_video_btn`
- `self.group_b_count_label`

## 修改后的效果

修改完成后，AB对比分析页面将：
1. 显示两个独立的视频列表（A组和B组）
2. 每个列表都有"添加视频"、"清空"按钮
3. 点击"添加视频"会打开两阶段选择弹窗（先选博主→再选视频）
4. 列表显示格式：`[平台] @[博主] | 视频描述 | ▶ 播放量`
5. 支持删除单个视频
6. 两组都有视频后才能点击"开始对比分析"

## 测试建议

修改完成后，建议测试：
1. 添加A组视频
2. 添加B组视频
3. 删除视频
4. 清空列表
5. 开始对比分析
6. 刷新页面（清空所有选择）
