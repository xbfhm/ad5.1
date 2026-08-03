# -*- coding: utf-8 -*-
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.behaviors import FocusBehavior

class TVFocusButton(FocusBehavior, Button):
    """
    专为 Android TV 遥控器设计的焦点按钮组件。
    当遥控器焦点移动到该按钮时，会自动触发高亮变色与放大特效；离开时恢复。
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.2, 0.2, 1)  # 默认深灰色底
        self.color = (1, 1, 1, 1)                   # 默认白色文字
        self.font_size = '18sp'

    def on_focus(self, instance, value):
        """监听焦点状态变化"""
        if value:
            # 遥控器选中焦点时的样式
            self.background_color = (0.1, 0.5, 0.8, 1)  # 亮蓝色
            self.color = (1, 0.9, 0, 1)                 # 金黄色文字
            self.font_size = '20sp'
        else:
            # 失去焦点时的默认样式
            self.background_color = (0.2, 0.2, 0.2, 1)
            self.color = (1, 1, 1, 1)
            self.font_size = '18sp'


class TVGridPanel(GridLayout):
    """
    电视端流式布局宫格面板，用于自适应展示番剧搜索结果或选集列表。
    """
    def __init__(self, cols=5, **kwargs):
        super().__init__(**kwargs)
        self.cols = cols
        self.spacing = 10
        self.padding = 10
        self.size_hint_y = None
        self.bind(minimum_height=self.setter('height'))


class TVPlayerOverlay(BoxLayout):
    """
    电视端播放控制悬浮层组件（可用于在视频播放时通过遥控器调出暂停、快进、切换集数等菜单）。
    """
    def __init__(self, **kwargs):
        super().__init__(orientation='horizontal', **kwargs)
        self.size_hint_y = 0.15
        self.padding = 10
        self.spacing = 15
        
        # 底部控制条占位组件初始化
        self.btn_pause = TVFocusButton(text="暂停/播放")
        self.btn_next_ep = TVFocusButton(text="下一集")
        self.btn_back = TVFocusButton(text="返回列表")
        
        self.add_widget(self.btn_pause)
        self.add_widget(self.btn_next_ep)
        self.add_widget(self.btn_back)

