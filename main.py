# -*- coding: utf-8 -*-
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import FocusBehavior
from kivy.core.window import Window
from kivy.clock import Clock

import vlc
from rules_config import ANIME_SOURCES
from rule_engine import MultiRuleEngine

# 兼容手机键盘弹出时，界面自适应移动不遮挡输入框
Window.softinput_mode = "below_target"

# ========================================================
# 1. 电视遥控器专属焦点按钮组件 (兼容触摸屏与遥控器)
# ========================================================
class TVFocusButton(FocusBehavior, Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.2, 0.2, 0.2, 1)  # 默认暗灰底
        self.color = (1, 1, 1, 1)                   # 默认白色文字
        self.font_size = '18sp'

    def on_focus(self, instance, value):
        """当被遥控器选中 (聚焦) 时改变颜色和文字大小"""
        if value:
            self.background_color = (0.1, 0.5, 0.8, 1)  # 选中时变为亮蓝底
            self.color = (1, 0.9, 0, 1)                 # 文字金黄
            self.font_size = '20sp'
        else:
            self.background_color = (0.2, 0.2, 0.2, 1)
            self.color = (1, 1, 1, 1)
            self.font_size = '18sp'

# ========================================================
# 2. VLC 播放器与硬件控制包装器
# ========================================================
class TVVideoController:
    def __init__(self):
        # 参数配置支持 Android 5.1 上开启硬解且有音频播放
        self.instance = vlc.Instance("--no-xlib", "--codec=mediacodec", "--aout=opensles")
        self.player = self.instance.media_player_new()

    def play_stream(self, stream_url, rate=1.0):
        media = self.instance.media_new(stream_url)
        self.player.set_media(media)
        self.player.play()
        self.set_rate(rate)

    def set_rate(self, rate):
        self.player.set_rate(rate)

    def stop(self):
        self.player.stop()

# ========================================================
# 3. App 主界面框架视图
# ========================================================
class AnimeTVAppView(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.source_keys = list(ANIME_SOURCES.keys())
        self.current_source_idx = 0
        self.engine = MultiRuleEngine(ANIME_SOURCES[self.source_keys[self.current_source_idx]])
        
        self.episodes = []
        self.current_ep_index = 0
        self.current_speed = 1.0
        self.player = TVVideoController()

        self._build_top_bar()
        self._build_main_area()
        self._build_control_bar()
        self._build_episode_list()

    def _build_top_bar(self):
        top_bar = BoxLayout(size_hint_y=0.1, spacing=10, padding=5)
        
        self.btn_source = TVFocusButton(
            text=f"当前片源: {ANIME_SOURCES[self.source_keys[0]]['name']}",
            size_hint_x=0.25
        )
        self.btn_source.bind(on_release=self.switch_source)
        
        self.input_search = TextInput(
            hint_text="输入关键字搜索番剧...",
            size_hint_x=0.55,
            multiline=False,
            font_size='18sp'
        )
        self.btn_search = TVFocusButton(text="搜索", size_hint_x=0.2)
        self.btn_search.bind(on_release=self.start_search)

        top_bar.add_widget(self.btn_source)
        top_bar.add_widget(self.input_search)
        top_bar.add_widget(self.btn_search)
        self.add_widget(top_bar)

    def _build_main_area(self):
        # 左右分栏：左侧为状态展示/播放状态提示区，右侧是搜索结果展示列表
        self.main_area = BoxLayout(size_hint_y=0.6, spacing=10, padding=5)
        
        self.video_info = Label(
            text="欢迎使用电视端追番 APP\n请通过遥控器搜索或者点击左上角切换片源",
            font_size='22sp',
            halign='center',
            size_hint_x=0.6
        )
        
        self.scroll_results = ScrollView(size_hint_x=0.4)
        self.grid_results = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.grid_results.bind(minimum_height=self.grid_results.setter('height'))
        self.scroll_results.add_widget(self.grid_results)

        self.main_area.add_widget(self.video_info)
        self.main_area.add_widget(self.scroll_results)
        self.add_widget(self.main_area)

    def _build_control_bar(self):
        control_bar = BoxLayout(size_hint_y=0.1, spacing=20, padding=10)
        
        self.btn_prev = TVFocusButton(text="< 上一集")
        self.btn_prev.bind(on_release=self.play_prev)
        
        self.btn_speed = TVFocusButton(text="倍速: 1.0X")
        self.btn_speed.bind(on_release=self.toggle_speed)
        
        self.btn_next = TVFocusButton(text="下一集 >")
        self.btn_next.bind(on_release=self.play_next)

        control_bar.add_widget(self.btn_prev)
        control_bar.add_widget(self.btn_speed)
        control_bar.add_widget(self.btn_next)
        self.add_widget(control_bar)

    def _build_episode_list(self):
        self.scroll_eps = ScrollView(size_hint_y=0.2)
        self.grid_episodes = GridLayout(cols=8, spacing=5, padding=5, size_hint_y=None)
        self.grid_episodes.bind(minimum_height=self.grid_episodes.setter('height'))
        self.scroll_eps.add_widget(self.grid_episodes)
        self.add_widget(self.scroll_eps)

    # ------------------ 业务核心方法 ------------------
    def switch_source(self, *args):
        self.current_source_idx = (self.current_source_idx + 1) % len(self.source_keys)
        source_key = self.source_keys[self.current_source_idx]
        self.engine = MultiRuleEngine(ANIME_SOURCES[source_key])
        self.btn_source.text = f"当前片源: {ANIME_SOURCES[source_key]['name']}"

    def start_search(self, *args):
        kw = self.input_search.text.strip()
        if not kw:
            return
        self.video_info.text = f"正在检索 [{kw}]..."
        threading.Thread(target=self._async_search, args=(kw,), daemon=True).start()

    def _async_search(self, kw):
        results = self.engine.search(kw)
        Clock.schedule_once(lambda dt: self._update_search_ui(results), 0)

    def _update_search_ui(self, results):
        self.grid_results.clear_widgets()
        if not results:
            self.video_info.text = "未找到相关番剧内容，请尝试点击左上角更改片源！"
            return
            
        self.video_info.text = "请从右侧列表中选择需要播放的番剧"
        for item in results:
            btn = TVFocusButton(text=item['name'], size_hint_y=None, height=50)
            btn.bind(on_release=lambda inst, url=item['url']: self.load_anime_detail(url))
            self.grid_results.add_widget(btn)

    def load_anime_detail(self, detail_url):
        self.video_info.text = "正在解析集数信息..."
        threading.Thread(target=self._async_load_detail, args=(detail_url,), daemon=True).start()

    def _async_load_detail(self, detail_url):
        episodes = self.engine.get_episodes(detail_url)
        Clock.schedule_once(lambda dt: self._update_episodes_ui(episodes), 0)

    def _update_episodes_ui(self, episodes):
        self.grid_episodes.clear_widgets()
        self.episodes = episodes
        
        if not episodes:
            self.video_info.text = "无可用播放集数，可能该片源限制展示！"
            return
            
        for idx, ep in enumerate(self.episodes):
            btn = TVFocusButton(text=ep['title'], size_hint_y=None, height=45)
            btn.bind(on_release=lambda inst, i=idx: self.select_episode(i))
            self.grid_episodes.add_widget(btn)

    def select_episode(self, index):
        self.current_ep_index = index
        ep_info = self.episodes[index]
        self.video_info.text = f"正在提取直链:\n{ep_info['title']}"
        threading.Thread(target=self._async_play, args=(ep_info,), daemon=True).start()

    def _async_play(self, ep_info):
        real_url = self.engine.parse_video_url(ep_info['page_url'])
        Clock.schedule_once(lambda dt: self._start_vlc_playback(ep_info['title'], real_url), 0)

    def _start_vlc_playback(self, title, url):
        self.video_info.text = f"当前播放: {title}\n(倍速: {self.current_speed}X)"
        self.player.play_stream(url, rate=self.current_speed)

    def play_prev(self, *args):
        if self.current_ep_index > 0:
            self.select_episode(self.current_ep_index - 1)

    def play_next(self, *args):
        if self.current_ep_index < len(self.episodes) - 1:
            self.select_episode(self.current_ep_index + 1)

    def toggle_speed(self, *args):
        self.current_speed = 2.0 if self.current_speed == 1.0 else 1.0
        self.btn_speed.text = f"倍速: {self.current_speed}X"
        self.player.set_rate(self.current_speed)
        
        if self.episodes:
            cur_title = self.episodes[self.current_ep_index]['title']
            self.video_info.text = f"当前播放: {cur_title}\n(倍速: {self.current_speed}X)"

# ========================================================
# 4. 应用程序入口
# ========================================================
class AnimeTVApp(App):
    def build(self):
        # 整体背景色调设为深蓝色视听风格
        Window.clearcolor = (0.1, 0.1, 0.15, 1)
        return AnimeTVAppView()

if __name__ == '__main__':
    AnimeTVApp().run()
