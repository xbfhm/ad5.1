# -*- coding: utf-8 -*-
"""
AnimeTV - 海信 VIDAA V1 电视适配版 (Android 5.1.1 / API 22 / 2GB内存 / 遥控器操作)
=============================================================================
适配要点:
  1. 纯标准库网络(无 lxml/requests), 大幅降低内存占用, 避免 OOM 闪退
  2. 瘦身中文字体(5.7MB), 加快启动, 减少内存
  3. 遥控器 DPAD 全导航 + OK 确认 + BACK 返回, 无需鼠标
  4. 1080p 大字体自适应布局
  5. 播放历史自动记忆, 开机一键续看
  6. 播放交给系统/VLC/MX Player, 支持 m3u8
  7. 所有异常捕获写日志, 不闪退
"""
import os
import sys
import threading
import traceback

# ---- Kivy 全局配置(必须在创建 Window 之前) ----
from kivy.config import Config
Config.set('graphics', 'maxfps', '30')          # 电视 UI 30fps 足够, 省电省内存
Config.set('graphics', 'multisamples', '0')     # 关闭 MSAA, 老 GPU(Mali-450) 更稳
Config.set('kivy', 'keyboard_mode', 'systemandmulti')
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.text import LabelBase

# ================================================================
# 0. 崩溃日志 + 启动打卡 (App 自己写文件, 不依赖 logcat)
# ================================================================
def _log_paths():
    paths = []
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            paths.append(os.path.join(app_storage_path(), "animetv"))
        except Exception:
            pass
        paths.append("/sdcard/Android/data/org.test.animetv/files/animetv")
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "animetv"))
    return paths

def _write_log(msg, filename):
    for base in _log_paths():
        try:
            os.makedirs(base, exist_ok=True)
            with open(os.path.join(base, filename), "a", encoding="utf-8") as f:
                f.write(msg + "\n")
                f.flush()
            return
        except Exception:
            continue

def _checkpoint(msg):
    _write_log(f"[{time_str()}] {msg}", "startup.log")

def time_str():
    import datetime
    return datetime.datetime.now().strftime("%m-%d %H:%M:%S")

def _global_excepthook(exc_type, exc_value, exc_tb):
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    _write_log(f"\n===== {time_str()} CRASH =====\n{text}", "crash.log")
    try:
        sys.__excepthook__(exc_type, exc_value, exc_tb)
    except Exception:
        pass

sys.excepthook = _global_excepthook
_checkpoint("[1] 模块加载开始")

# ---- 引擎 (纯标准库) ----
from engine.age_api import (AgeError, search, detail, episodes,
                            parse_video_url, catalog, home)
_checkpoint("[2] age_api 导入成功")

# ---- 注册中文字体 ----
_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK-TV.otf")
if not os.path.exists(_FONT):
    _FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NotoSansCJK-Regular.otf")
try:
    LabelBase.register(name="Roboto", fn_regular=_FONT)
    _checkpoint("[3] 字体注册成功 " + _FONT)
except Exception as e:
    _checkpoint(f"[3] 字体注册失败: {e}")
    LabelBase.register(name="Roboto", fn_regular=_FONT)

# ================================================================
# 1. TV 遥控器按钮 (焦点高亮)
# ================================================================
class TVButton(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0.22, 0.24, 0.30, 1)
        self.color = (0.92, 0.92, 0.95, 1)
        self.font_size = self._fs(26)
        self.bold = False
        self.padding = [10, 6]
        self._focused = False
        self.border = (0, 0, 0, 0)

    @staticmethod
    def _fs(v):
        # 1080p 基准, 按窗口宽度缩放, 保证电视上字体够大
        try:
            w = Window.width or 1920
            return max(20, int(v * w / 1920))
        except Exception:
            return v

    def set_focus(self, on):
        self._focused = on
        if on:
            self.background_color = (0.10, 0.55, 0.90, 1)
            self.color = (1, 0.95, 0.2, 1)
            self.bold = True
        else:
            self.background_color = (0.22, 0.24, 0.30, 1)
            self.color = (0.92, 0.92, 0.95, 1)
            self.bold = False

# ================================================================
# 2. 系统播放器控制器 (Intent 调外部播放器)
# ================================================================
class TVPlayer:
    """优先 VLC -> MX Player -> 系统播放器; 支持 m3u8/mp4"""
    PACKAGES = [
        ("org.videolan.vlc", "VLC"),
        ("com.mxtech.videoplayer.ad", "MX Player"),
        ("com.mxtech.videoplayer", "MX Player"),
    ]

    def play(self, url):
        if platform != 'android':
            print("[非Android环境] 视频地址:", url)
            return "非Android环境, 无法调起播放器"
        try:
            from jnius import autoclass, cast
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            mime = "application/x-mpegURL" if ".m3u8" in url else "video/*"

            activity = cast('android.app.Activity', PythonActivity.mActivity)
            pm = activity.getPackageManager()
            intent = Intent(Intent.ACTION_VIEW)
            intent.setDataAndType(Uri.parse(url), mime)
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

            # 1) 依次尝试指定播放器
            for pkg, name in self.PACKAGES:
                try:
                    pm.getPackageInfo(pkg, 0)
                    intent.setPackage(pkg)
                    activity.startActivity(intent)
                    return f"已交给 {name} 播放"
                except Exception:
                    continue
            # 2) 回退系统播放器
            intent2 = Intent(Intent.ACTION_VIEW)
            intent2.setDataAndType(Uri.parse(url), mime)
            intent2.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            activity.startActivity(intent2)
            return "已交给系统播放器"
        except Exception as e:
            _write_log(f"播放器调用失败: {e}\nurl={url}", "crash.log")
            return f"播放器调用失败: {e}"

# ================================================================
# 3. 遥控器焦点导航
# ================================================================
class FocusNav:
    KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT = 273, 274, 276, 275
    KEY_OK, KEY_SPACE, KEY_BACK, KEY_BACKSPACE = 13, 32, 27, 8

    def __init__(self, view):
        self.view = view
        self.items = []          # 可导航按钮列表
        self.index = -1
        self.editable = None     # 搜索输入框
        Window.bind(on_key_down=self._on_key)

    def add(self, btn):
        self.items.append(btn)
        if self.index < 0:
            self.index = 0
            btn.set_focus(True)

    def clear(self, keep=()):
        for b in self.items:
            if b not in keep:
                b.set_focus(False)
        self.items = [b for b in self.items if b in keep]
        if self.items:
            self._set_index(0)
        else:
            self.index = -1

    def _set_index(self, i):
        if 0 <= i < len(self.items):
            if self.index >= 0 and self.index < len(self.items):
                self.items[self.index].set_focus(False)
            self.index = i
            self.items[i].set_focus(True)
            self._ensure_visible(self.items[i])

    def focus_first(self):
        if self.items:
            self._set_index(0)

    def _ensure_visible(self, w):
        """焦点按钮滚入可视区域"""
        sv = None
        node = w
        for _ in range(6):
            if node is None:
                break
            if isinstance(node, ScrollView):
                sv = node
                break
            node = node.parent
        if sv is None:
            return
        try:
            # 按钮在 ScrollView 内的坐标
            sx, sy = w.to_window(w.x, w.y)
            svx, svy = sv.to_window(sv.x, sv.y)
            svw, svh = sv.width, sv.height
            rx, ry = sx - svx, sy - svy
            if ry < 0:
                sv.scroll_y = min(1.0, sv.scroll_y + (-ry) / (sv.height or 1))
            elif ry + w.height > svh:
                sv.scroll_y = max(0.0, sv.scroll_y - (ry + w.height - svh) / (sv.height or 1))
        except Exception:
            pass

    def _nearest(self, dx, dy):
        if not self.items:
            return -1
        cur = self.items[self.index] if 0 <= self.index < len(self.items) else None
        best, best_d = -1, 1e18
        for i, w in enumerate(self.items):
            if w is cur:
                continue
            c1 = (cur.center_x, cur.center_y) if cur else (0, 0)
            c2 = (w.center_x, w.center_y)
            vx, vy = c2[0] - c1[0], c2[1] - c1[1]
            # 方向过滤
            if dx > 0 and vx <= 8:
                continue
            if dx < 0 and vx >= -8:
                continue
            if dy > 0 and vy <= 8:
                continue
            if dy < 0 and vy >= -8:
                continue
            d = vx * vx + vy * vy
            if d < best_d:
                best_d, best = d, i
        return best

    def _on_key(self, window, key, scancode, codepoint, modifier, **kw):
        try:
            if key == self.KEY_BACK or key == self.KEY_BACKSPACE:
                return self.view.on_back()
            if self.editable is not None and self.editable.focus:
                # 输入框聚焦时: OK=收起并搜索, 其他交给输入框
                if key == self.KEY_OK or key == self.KEY_SPACE:
                    self.editable.focus = False
                    self.view.do_search()
                    return True
                return False
            if key == self.KEY_OK or key == self.KEY_SPACE:
                if 0 <= self.index < len(self.items):
                    btn = self.items[self.index]
                    if hasattr(btn, 'on_ok'):
                        btn.on_ok()
                    else:
                        btn.dispatch('on_release')
                return True
            if key == self.KEY_UP:
                i = self._nearest(0, -1)
            elif key == self.KEY_DOWN:
                i = self._nearest(0, 1)
            elif key == self.KEY_LEFT:
                i = self._nearest(-1, 0)
            elif key == self.KEY_RIGHT:
                i = self._nearest(1, 0)
            else:
                return False
            if i >= 0:
                self._set_index(i)
            return True
        except Exception as e:
            _write_log(f"按键处理异常: {e}", "crash.log")
            return False

# ================================================================
# 4. 主界面
# ================================================================
class AnimeTVAppView(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', **kw)
        _checkpoint("[4] 主视图初始化")
        self.history_file = self._history_path()
        self.history = self._load_history()
        self.detail_data = None      # 当前番详情
        self.ep_list = []            # 当前集列表(含线路)
        self.ep_index = 0            # 当前集序号(在 ep_list 内)
        self.current_line = None     # 当前线路
        self.cur_aid = None
        self.cur_name = ""
        self.busy = False            # 防重复操作
        self.player = TVPlayer()
        self.nav = FocusNav(self)

        self._build_ui()
        _checkpoint("[5] UI 构建完成")
        # 初始展示
        self._show_home()
        self.nav.focus_first()

    # ---------- 数据存储 ----------
    @staticmethod
    def _history_path():
        if platform == 'android':
            try:
                from android.storage import app_storage_path
                d = app_storage_path()
            except Exception:
                d = "/sdcard/Android/data/org.test.animetv/files"
        else:
            d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        return os.path.join(d, "history.json")

    def _load_history(self):
        try:
            if os.path.exists(self.history_file):
                import json
                with open(self.history_file, encoding="utf-8") as f:
                    data = json.load(f)
                # 清洗: 只保留有效记录
                return [h for h in data if isinstance(h, dict) and h.get("aid")]
        except Exception:
            pass
        return []

    def _save_history(self):
        try:
            import json
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history[:20], f, ensure_ascii=False)
        except Exception:
            pass

    # ---------- UI 构建 ----------
    def _px(self, v):
        try:
            w = Window.width or 1920
            return max(18, int(v * w / 1920))
        except Exception:
            return v

    def _mk_button(self, text, cb=None, on_ok=None, height=None, fs=26):
        b = TVButton(text=text)
        if height:
            b.size_hint_y = None
            b.height = self._px(height)
        if fs:
            b.font_size = self._px(fs)
        if cb:
            b.bind(on_release=cb)
        if on_ok:
            b.on_ok = on_ok
        self.nav.add(b)
        return b

    def _build_ui(self):
        # ---- 顶部栏 ----
        top = BoxLayout(size_hint_y=None, height=self._px(64), spacing=self._px(8),
                        padding=[self._px(10), self._px(4)])
        self.btn_home = self._mk_button("首页", cb=lambda *a: self._show_home())
        self.btn_catalog = self._mk_button("新番", cb=lambda *a: self._show_catalog())
        self.btn_history = self._mk_button("历史", cb=lambda *a: self._show_history())
        self.input_search = TextInput(
            hint_text="输入番剧名搜索...", multiline=False,
            font_size=self._px(26), size_hint_x=0.34,
            foreground_color=(1, 1, 1, 1), cursor_color=(1, 1, 1, 1),
            background_color=(0.12, 0.13, 0.17, 1), padding=[self._px(10), self._px(12)])
        self.nav.editable = self.input_search
        self.btn_search = self._mk_button("搜索", cb=lambda *a: self.do_search(), fs=28)
        self.btn_resume = self._mk_button("续看", cb=lambda *a: self._resume_last())
        top.add_widget(self.btn_home)
        top.add_widget(self.btn_catalog)
        top.add_widget(self.btn_history)
        top.add_widget(self.input_search)
        top.add_widget(self.btn_search)
        top.add_widget(self.btn_resume)
        self.add_widget(top)

        # ---- 主区域: 左信息 / 右列表 ----
        main = BoxLayout(size_hint_y=0.58, spacing=self._px(8), padding=self._px(8))
        self.info_label = Label(
            text="", font_size=self._px(30), halign='left', valign='top',
            color=(0.85, 0.87, 0.92, 1), size_hint_x=0.55)
        self.info_label.bind(size=lambda *a: setattr(self.info_label, 'text_size',
                                                     (self.info_label.width * 0.95, None)))
        self.scroll_list = ScrollView(size_hint_x=0.45)
        self.grid_list = GridLayout(cols=1, spacing=self._px(4), size_hint_y=None,
                                    padding=[0, self._px(4)])
        self.grid_list.bind(minimum_height=self.grid_list.setter('height'))
        self.scroll_list.add_widget(self.grid_list)
        main.add_widget(self.info_label)
        main.add_widget(self.scroll_list)
        self.add_widget(main)

        # ---- 控制栏 ----
        ctrl = BoxLayout(size_hint_y=None, height=self._px(60), spacing=self._px(10),
                         padding=[self._px(10), self._px(4)])
        self.btn_prev = self._mk_button("◀ 上一集", cb=lambda *a: self._prev_ep())
        self.btn_play = self._mk_button("▶ 播放", cb=lambda *a: self._play_current(), fs=30)
        self.btn_next = self._mk_button("下一集 ▶", cb=lambda *a: self._next_ep())
        self.btn_line = self._mk_button("线路: -", cb=lambda *a: self._switch_line())
        self.btn_copy = self._mk_button("复制直链", cb=lambda *a: self._copy_url())
        ctrl.add_widget(self.btn_prev)
        ctrl.add_widget(self.btn_play)
        ctrl.add_widget(self.btn_next)
        ctrl.add_widget(self.btn_line)
        ctrl.add_widget(self.btn_copy)
        self.add_widget(ctrl)

        # ---- 集数区 ----
        self.scroll_eps = ScrollView(size_hint_y=None, height=self._px(130))
        self.grid_eps = GridLayout(cols=10, spacing=self._px(5), size_hint_y=None,
                                   padding=[self._px(8), self._px(5)])
        self.grid_eps.bind(minimum_height=self.grid_eps.setter('height'))
        self.scroll_eps.add_widget(self.grid_eps)
        self.add_widget(self.scroll_eps)

    # ---------- 状态提示 ----------
    def _info(self, text):
        self.info_label.text = text

    def _busy(self, msg):
        self.busy = True
        self._info("⏳ " + msg + "\n\n请稍候...")

    # ---------- 线程工具 ----------
    def _thread(self, fn):
        # 入口已做 busy 检查, 这里直接启动
        threading.Thread(target=fn, daemon=True).start()

    def _ui(self, fn):
        Clock.schedule_once(lambda dt: self._safe(fn), 0)

    def _safe(self, fn):
        try:
            fn()
        except Exception as e:
            _write_log(f"UI回调异常: {e}\n{traceback.format_exc()}", "crash.log")
            self._info(f"出错了: {e}")

    # ---------- 首页 / 目录 / 历史 ----------
    def _show_home(self):
        if self.busy:
            return
        self._busy("正在加载首页...")
        self._thread(lambda: self._load_home_worker())

    def _load_home_worker(self):
        try:
            h = home()
        except Exception as e:
            self._ui(lambda: self._home_error(str(e)))
            return
        self._ui(lambda: self._render_list(
            title="🔥 最新更新 / 本周新番",
            items=[{"name": f"{i['name']}  {i['new']}", "id": i["id"]} for i in h["latest"]]
                   + [{"name": ("NEW " if w["isnew"] else "") + w["name"], "id": w["id"]}
                      for w in h["week"]]))

    def _home_error(self, msg):
        self.busy = False
        self._info(f"首页加载失败: {msg}\n\n可尝试「搜索」或「新番」")

    def _show_catalog(self):
        if self.busy:
            return
        self._busy("正在加载新番目录...")
        self._thread(lambda: self._catalog_worker())

    def _catalog_worker(self):
        try:
            items = []
            for season, label in ((1, "2026冬季"), (4, "2026春季"), (7, "2026夏季")):
                for v in catalog(2026, season, 1, 8):
                    items.append({"name": f"{label} | {v['name']}", "id": v["id"]})
        except Exception as e:
            self._ui(lambda: self._home_error(str(e)))
            return
        self._ui(lambda: self._render_list(title="📺 2026 新番一览(每季前8部)",
                                           items=items))

    def _show_history(self):
        if not self.history:
            self.busy = False
            self._info("暂无播放历史\n\n看过的番会记录在这里, 点击「续看」可快速回到上次位置")
            return
        items = [{"name": f"{h['name']}  ▶ {h['ep']}", "id": h["aid"], "ep": h.get("ep", 0),
                  "line": h.get("line")} for h in self.history]
        self._render_list(title="🕘 播放历史(OK=恢复播放)", items=items)

    def _resume_last(self):
        if not self.history:
            self.busy = False
            self._info("暂无历史记录")
            return
        h = self.history[0]
        self._open_anime(h["aid"], h["name"], h.get("ep", 0), h.get("line"))

    # ---------- 搜索 ----------
    def do_search(self):
        if self.busy:
            return
        kw = self.input_search.text.strip()
        if not kw:
            self.busy = False
            self._info("请输入番剧名称, 如: 海贼王 / 咒术回战 / 葬送的芙莉莲")
            return
        self._busy(f"正在搜索 [{kw}] ...")
        self._thread(lambda: self._search_worker(kw))

    def _search_worker(self, kw):
        try:
            rs = search(kw)
        except Exception as e:
            self._ui(lambda: self._home_error(str(e)))
            return
        self._ui(lambda: self._render_search(rs, kw))

    def _render_search(self, rs, kw):
        self.busy = False
        if not rs:
            self._info(f"未找到 [{kw}] 相关番剧\n\n换个关键词试试, 或看看「新番」「首页」")
            self._clear_list()
            return
        items = [{"name": f"{r['name']}  ({r['premiere']} {r['status']})", "id": r["id"]}
                 for r in rs]
        self._render_list(title=f"🔍 搜索结果: {kw} ({len(rs)})", items=items)

    # ---------- 通用列表渲染 ----------
    def _clear_list(self):
        self.grid_list.clear_widgets()
        for b in list(self.nav.items):
            if b.parent is self.grid_list:
                self.nav.items.remove(b)

    def _render_list(self, title, items, prefix=""):
        self.busy = False
        self._clear_list()
        self._info(title + "\n\n" + (prefix or "↑ 使用遥控器上下键选择, OK 键进入"))
        for it in items:
            b = self._mk_button(it["name"], cb=lambda inst, i=it: self._on_item(i),
                                height=56, fs=28)
            self.grid_list.add_widget(b)
        self.nav.focus_first()

    def _on_item(self, item):
        aid = item.get("id")
        if not aid:
            return
        name = item.get("name", "")
        # 去掉前缀标签
        for pre in ("🔥", "📺", "🕘", "NEW ", "2026冬季 | ", "2026春季 | ", "2026夏季 | "):
            name = name.replace(pre, "")
        self._open_anime(aid, name.split("▶")[0].strip(), item.get("ep", 0), item.get("line"))

    # ---------- 番剧详情 ----------
    def _open_anime(self, aid, name, ep_index=0, line=None):
        if self.busy:
            return
        self._busy(f"正在解析《{name}》...")
        self.cur_aid = aid
        self.cur_name = name
        self._thread(lambda: self._detail_worker(aid, ep_index, line))

    def _detail_worker(self, aid, ep_index, line):
        try:
            d = detail(aid)
            eps = episodes(d)
        except Exception as e:
            self._ui(lambda: self._detail_error(str(e)))
            return
        self._ui(lambda: self._render_detail(d, eps, ep_index, line))

    def _detail_error(self, msg):
        self.busy = False
        self._info(f"解析失败: {msg}\n\n该片可能暂未上源, 可尝试其他番剧")

    def _render_detail(self, d, eps, ep_index, line):
        self.busy = False
        if not eps:
            self._info(f"《{d['name']}》暂无可用播放线路\n\n版权番可能只有VIP源(爱奇艺/腾讯等)")
            self._clear_eps()
            return
        self.detail_data = d
        self.ep_list = eps
        # 选择线路: 默认 free 线路中第一条; 若指定则按指定
        lines = []
        for e in eps:
            if e["line"] not in lines:
                lines.append(e["line"])
        if line and line in lines:
            self.current_line = line
        else:
            self.current_line = eps[0]["line"]
        # 计算该番内集序号(非全局序号)
        self.ep_index = min(max(ep_index, 0), len(eps) - 1)

        tags = " ".join(d.get("tags", []))
        info = (f"《{d['name']}》\n\n"
                f"类型: {d.get('type','')} | 首播: {d.get('premiere','')}\n"
                f"状态: {d.get('status','')} | {d.get('uptodate','')}\n"
                f"标签: {tags}\n\n"
                f"简介: {(d.get('intro') or '暂无')[:150]}\n\n"
                f"⬇ 下方选择集数, OK 播放; 左右键切换线路")
        self._info(info)

        # 集数列表(全部, 长番自动分页显示前 300)
        self._render_eps(eps)

    def _render_eps(self, eps):
        self.grid_eps.clear_widgets()
        max_show = 300
        shown = eps[:max_show]
        for i, e in enumerate(shown):
            b = self._mk_button(e["title"], cb=lambda inst, i=i: self._select_ep(i),
                                height=50, fs=24)
            b.on_ok = lambda i=i: self._select_ep(i)
            self.grid_eps.add_widget(b)
        if len(eps) > max_show:
            self._mk_button(f"…共{len(eps)}集, 用「上一集/下一集」连续观看",
                            height=50, fs=22)
        self._update_line_btn()
        self._update_play_btn()

    def _clear_eps(self):
        self.grid_eps.clear_widgets()
        self.ep_list = []

    # ---------- 选集 / 播放 ----------
    def _select_ep(self, i):
        if self.busy or not self.ep_list:
            return
        self.ep_index = min(i, len(self.ep_list) - 1)
        e = self.ep_list[self.ep_index]
        self._info(f"《{self.cur_name}》 {e['title']}\n\n⏳ 正在获取播放地址...")
        self.busy = True
        self._thread(lambda: self._play_worker())

    def _play_current(self):
        if self.busy or not self.ep_list:
            if not self.ep_list:
                self.busy = False
                self._info("请先选择一部番剧")
            return
        e = self.ep_list[self.ep_index]
        self._info(f"《{self.cur_name}》 {e['title']}\n\n⏳ 正在获取播放地址...")
        self.busy = True
        self._thread(lambda: self._play_worker())

    def _play_worker(self):
        """按当前线路解析直链, 失败自动尝试其他线路"""
        eps = self.ep_list
        idx = self.ep_index
        order = []
        if self.current_line:
            for i, e in enumerate(eps):
                if e["line"] == self.current_line:
                    order.append(i)
        if idx not in order:
            order = [idx]
        tried = []
        for i in order:
            e = eps[i]
            tried.append(e["line_label"])
            try:
                url = parse_video_url(e["enc"], e["vip"])
                # 保存历史
                self._add_history(self.cur_aid, self.cur_name, e["title"], i, e["line"])
                self._ui(lambda url=url, e=e: self._play_ui(url, e))
                return
            except Exception:
                continue
        self._ui(lambda tried=tried: self._play_fail(tried))

    def _play_ui(self, url, e):
        self.busy = False
        msg = self.player.play(url)
        self._update_play_btn()
        self._info(f"《{self.cur_name}》 {e['title']}\n"
                   f"线路: {e['line_label']}  [{msg}]\n\n"
                   f"m3u8: {url}\n\n"
                   f"📌 若播放器未自动打开, 请安装 VLC / MX Player")
        # 调试: 复制到剪贴板
        try:
            from kivy.core.clipboard import Clipboard
            Clipboard.copy(url)
        except Exception:
            pass

    def _play_fail(self, tried):
        self.busy = False
        self._info(f"播放失败: 线路 {','.join(tried)} 均无法解析\n\n"
                   f"可按「线路」键切换其他线路重试, 或换一部番")

    def _add_history(self, aid, name, ep, ep_idx, line):
        try:
            self.history = [h for h in self.history if h.get("aid") != aid]
            self.history.insert(0, {"aid": aid, "name": name, "ep": ep,
                                    "ep_idx": ep_idx, "line": line,
                                    "t": int(__import__("time").time())})
            self._save_history()
        except Exception:
            pass

    # ---------- 上一集 / 下一集 ----------
    def _prev_ep(self):
        if self.ep_index > 0:
            self._select_ep(self.ep_index - 1)

    def _next_ep(self):
        if self.ep_index < len(self.ep_list) - 1:
            self._select_ep(self.ep_index + 1)
        else:
            self.busy = False
            self._info("已经是最后一集了")

    # ---------- 切换线路 ----------
    def _switch_line(self):
        if not self.ep_list:
            self.busy = False
            return
        lines = []
        for e in self.ep_list:
            if e["line"] not in lines:
                lines.append(e["line"])
        if not lines:
            return
        cur = self.current_line if self.current_line in lines else lines[0]
        i = lines.index(cur)
        self.current_line = lines[(i + 1) % len(lines)]
        self._update_line_btn()
        e = self.ep_list[self.ep_index]
        self._info(f"已切换到线路: {e['line_label']}\n\n按 OK 开始播放")
        self.busy = False

    def _update_line_btn(self):
        if self.ep_list:
            e = self.ep_list[self.ep_index]
            self.btn_line.text = f"线路: {e['line_label']}"

    def _update_play_btn(self):
        if self.ep_list:
            e = self.ep_list[self.ep_index]
            self.btn_play.text = f"▶ 播放 {e['title']}"

    def _copy_url(self):
        self.busy = False
        self._info("复制功能: 播放时会自动复制直链到剪贴板\n可粘贴到手机浏览器/播放器测试")

    # ---------- 返回键 ----------
    def on_back(self):
        # 已聚焦输入框 -> 收起
        if self.nav.editable is not None and self.nav.editable.focus:
            self.nav.editable.focus = False
            return True
        # 其他情况: 返回首页(不退出, 防止误退)
        if self.cur_aid is not None:
            self.cur_aid = None
            self._show_home()
        return True

# ================================================================
# 5. App
# ================================================================
class AnimeTVApp(App):
    title = "AnimeTV 追番"

    def build(self):
        _checkpoint("[6] App.build()")
        Window.clearcolor = (0.08, 0.09, 0.13, 1)
        return AnimeTVAppView()

    def on_pause(self):
        return True

if __name__ == '__main__':
    _checkpoint("[7] 启动 Kivy")
    AnimeTVApp().run()
    _checkpoint("[99] 正常退出")
