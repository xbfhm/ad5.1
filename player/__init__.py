# -*- coding: utf-8 -*-

class TVPlayer:
    """
    专为 Android TV 端视频播放封装的控制类，
    对接 ffpyplayer 或底层硬件解码播放器，提供基础的播放、暂停、停止和倍速控制接口。
    """
    def __init__(self, player_widget=None):
        self.player_widget = player_widget
        self.current_url = ""
        self.is_playing = False
        self.speed = 1.0

    def play(self, url):
        """加载并开始播放视频流地址"""
        self.current_url = url
        self.is_playing = True
        if self.player_widget:
            # 如果绑定了具体的 Kivy 播放器控件，则更新数据源并执行播放
            self.player_widget.source = url
            self.player_widget.state = 'play'

    def pause(self):
        """暂停播放"""
        self.is_playing = False
        if self.player_widget:
            self.player_widget.state = 'pause'

    def stop(self):
        """停止播放并清空状态"""
        self.is_playing = False
        self.current_url = ""
        if self.player_widget:
            self.player_widget.state = 'stop'

    def set_playback_rate(self, rate):
        """设置播放倍速"""
        self.speed = rate
        if self.player_widget and hasattr(self.player_widget, 'set_option'):
            # 兼容部分播放内核的倍速调整接口
            pass

