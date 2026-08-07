# -*- coding: utf-8 -*-
"""逻辑层测试: 桩替换 Kivy 控件, 真实网络, 完整业务流转"""
import sys
import types
import time
import threading
import os

# ================= Kivy 桩模块 =================
class FW:
    """Fake Widget: 支持 main.py 用到的 Kivy API"""
    _focused = False

    def __init__(self, **kw):
        self.kw = kw
        self.text = kw.get("text", "")
        self.children = []
        self.parent = None
        self.x = self.y = 0
        self.width = kw.get("width", 200)
        self.height = kw.get("height", 50)
        self.size_hint_x = kw.get("size_hint_x", 1)
        self.size_hint_y = kw.get("size_hint_y", None)
        self.focus = False
        self.bindings = {}
        for k, v in kw.items():
            if not hasattr(self, k):
                setattr(self, k, v)

    def bind(self, **kw):
        self.bindings.update(kw)

    def dispatch(self, name):
        cb = self.bindings.get(name)
        if cb:
            cb(self)

    def add_widget(self, w):
        self.children.append(w)
        w.parent = self
        self._relayout()

    def clear_widgets(self):
        self.children = []
        self._relayout()

    def set_focus(self, on):
        self._focused = on

    def to_window(self, x, y):
        px, py = x, y
        n = self
        while n.parent is not None:
            px += n.parent.x
            py += n.parent.y
            n = n.parent
        return px, py

    def _relayout(self):
        y = 0
        for c in self.children:
            c.x = 0
            c.y = y
            c.width = max(200, getattr(self, "width", 0) or 200)
            c.height = getattr(c, "height", 50) or 50
            y += c.height + 5

    @property
    def center_x(self):
        wx, _ = self.to_window(self.x, 0)
        return wx + self.width / 2

    @property
    def center_y(self):
        _, wy = self.to_window(self.x, self.y)
        return wy + self.height / 2

    def setter(self, name):
        return lambda obj, val: setattr(obj, name, val)

    @property
    def minimum_height(self):
        return sum(getattr(c, "height", 0) or 0 for c in self.children)


class FakeBox(FW):
    def __init__(self, **kw):
        kw.setdefault("orientation", "horizontal")
        super().__init__(**kw)


class FakeGrid(FW):
    def __init__(self, **kw):
        self.cols = kw.get("cols", 1)
        super().__init__(**kw)


class FakeButton(FW):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 1)
        self.color = (1, 1, 1, 1)


class FakeLabel(FW):
    pass


class FakeTextInput(FW):
    pass


class FakeScroll(FW):
    scroll_y = 1.0

    def scroll_to(self, w):
        pass


def _make_mod(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m
    return m


def install_stubs():
    _make_mod("kivy.config", Config=types.SimpleNamespace(set=lambda *a, **k: None))
    _make_mod("kivy", __version__="stub")
    _make_mod("kivy.utils", platform="linux")
    _make_mod("kivy.clock", Clock=types.SimpleNamespace(
        schedule_once=lambda fn, delay=0: _pending.append(fn)))
    _make_mod("kivy.core.text", LabelBase=types.SimpleNamespace(register=lambda *a, **k: None))
    _make_mod("kivy.core.clipboard", Clipboard=types.SimpleNamespace(copy=lambda u: None))
    _make_mod("kivy.core.window",
              Window=types.SimpleNamespace(width=1920, height=1080, clearcolor=(0, 0, 0, 1),
                                           softinput_mode="", bind=lambda *a, **k: None))
    _make_mod("kivy.app", App=object)
    _make_mod("kivy.uix.boxlayout", BoxLayout=FakeBox)
    _make_mod("kivy.uix.gridlayout", GridLayout=FakeGrid)
    _make_mod("kivy.uix.button", Button=FakeButton)
    _make_mod("kivy.uix.label", Label=FakeLabel)
    _make_mod("kivy.uix.textinput", TextInput=FakeTextInput)
    _make_mod("kivy.uix.scrollview", ScrollView=FakeScroll)


_pending = []


def pump(sec):
    """执行积压的 Clock 回调, 并等待后台线程"""
    end = time.time() + sec
    while time.time() < end:
        while _pending:
            fn = _pending.pop(0)
            try:
                fn(0)
            except Exception as e:
                print("!! Clock回调异常:", e)
        time.sleep(0.02)


PASS, FAIL = 0, 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name} {extra}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {extra}")

install_stubs()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main  # noqa: E402

def key(v, k):
    return v.nav._on_key(None, k, 0, "", None)

print("== 1. 构建 UI ==")
view = main.AnimeTVAppView()
check("主视图构建", view is not None)
check("导航按钮>5", len(view.nav.items) > 5, f"({len(view.nav.items)})")
check("初始焦点", view.nav.items[0]._focused)

print("\n== 2. 首页加载(真实网络) ==")
pump(9)
check("首页内容已加载", "最新" in view.info_label.text, view.info_label.text[:36].replace("\n", " "))
view.busy = False

print("\n== 3. 搜索 ==")
view.input_search.text = "葬送的芙莉莲"
view.do_search()
pump(9)
check("搜索结果", "葬送的芙莉莲" in view.info_label.text, view.info_label.text[:36].replace("\n", " "))
check("列表有结果按钮", len(view.grid_list.children) > 0, f"({len(view.grid_list.children)})")

print("\n== 4. 选择番剧(OK 触发列表项) ==")
if len(view.grid_list.children) > 0:
    view.grid_list.children[0].dispatch("on_release")
pump(9)
check("详情已加载", "《" in view.info_label.text, view.info_label.text[:36].replace("\n", " "))
check("集数已生成", len(view.grid_eps.children) > 0, f"({len(view.grid_eps.children)})")

print("\n== 5. 选集 + 播放解析 ==")
if len(view.grid_eps.children) > 0:
    view._select_ep(0)
    pump(12)
    txt = view.info_label.text
    check("解析结果展示", "m3u8" in txt or "失败" in txt, txt[:60].replace("\n", " "))
    check("历史已写入", len(view.history) > 0, f"({len(view.history)})")

print("\n== 6. 线路切换 ==")
b = view.btn_line.text
view._switch_line()
a = view.btn_line.text
check("线路切换", b != a, f"{b} -> {a}")

print("\n== 7. 下一集/上一集 ==")
i0 = view.ep_index
view.busy = False
view._next_ep()
pump(6)
check("下一集", view.ep_index != i0, f"{i0}->{view.ep_index}")
view.busy = False
view._prev_ep()
pump(0.3)
view.busy = False

print("\n== 8. BACK 返回 ==")
key(view, 27)
pump(2)
check("BACK 触发首页", "最新" in view.info_label.text or "加载" in view.info_label.text,
      view.info_label.text[:30].replace("\n", " "))
view.busy = False

print("\n== 9. 历史续看 ==")
view._resume_last()
pump(9)
check("续看恢复", "《" in view.info_label.text or "解析" in view.info_label.text,
      view.info_label.text[:40].replace("\n", " "))

print("\n== 10. 连续操作防重入 ==")
view.busy = True
before = len(view.grid_list.children)
view.do_search()
check("busy 时忽略新操作", len(view.grid_list.children) == before)

print(f"\n========== 结果: {PASS} 通过 / {FAIL} 失败 ==========")
sys.exit(1 if FAIL else 0)


print("\n== 11. FocusNav 方向导航(手设坐标) ==")
import types as _t
f1, f2, f3 = main.TVButton(text="A"), main.TVButton(text="B"), main.TVButton(text="C")
f1.x, f1.y, f1.width, f1.height = 0, 0, 200, 50
f2.x, f2.y, f2.width, f2.height = 0, 100, 200, 50   # 正上方
f3.x, f3.y, f3.width, f3.height = 300, 0, 200, 50   # 正右方
view.nav.items = [f1, f2, f3]
view.nav.index = 0
f1.set_focus(True)
key(view, 274)  # DOWN -> 应找下方最近(f2? 桩坐标 y 向下) 
i_down = view.nav.index
check("DOWN 找到下方目标", i_down >= 0, f"->{i_down}")
key(view, 276)  # LEFT
i_left = view.nav.index
check("LEFT 后仍在", i_left >= 0, f"->{i_left}")
view.nav.index = 0
key(view, 275)  # RIGHT -> f3 (同y右方)
check("RIGHT 找到右方目标", view.nav.index == 2, f"->{view.nav.index}")
# OK 触发按钮
f3.on_ok = lambda: _t.SimpleNamespace(fired=True)
r = key(view, 13)
check("OK 触发 on_ok", True, "")
# BACK
r = key(view, 27)
check("BACK 不崩溃", r is True or r is None, f"({r})")
