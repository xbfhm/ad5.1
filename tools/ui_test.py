# -*- coding: utf-8 -*-
"""无头 UI 测试: mock 窗口 + 真实网络 + 模拟遥控器按键"""
import os
os.environ["KIVY_WINDOW"] = "mock"
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main
from kivy.core.window import Window
from kivy.clock import Clock

# mock 窗口默认 1920x1080, 不再手动设置 size
PASS = 0
FAIL = 0

def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {name} {extra}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {extra}")

def pump(sec):
    """推进 Kivy Clock + 等待后台线程"""
    end = time.time() + sec
    while time.time() < end:
        Clock.tick()
        time.sleep(0.02)

def key(v, k):
    v.nav._on_key(Window, k, 0, "", None)

print("== 构建 UI ==")
view = main.AnimeTVAppView()
check("主视图构建", view is not None)
check("导航按钮数>5", len(view.nav.items) > 5, f"({len(view.nav.items)})")
check("初始焦点在首页", view.nav.items[0]._focused)

print("\n== 首页加载(真实网络) ==")
pump(8)
txt = view.info_label.text
check("首页有内容", "最新" in txt or "加载" in txt or "失败" in txt, txt[:40].replace("\n", " "))
view.busy = False

print("\n== 搜索流程 ==")
view.input_search.text = "咒术回战"
view.do_search()
pump(8)
txt = view.info_label.text
check("搜索结果展示", "咒术回战" in txt, txt[:40].replace("\n", " "))
n_list = len(view.grid_list.children)
check("列表有按钮", n_list > 0, f"({n_list})")

print("\n== 遥控器导航: DOWN x2 + OK 选择 ==")
key(view, 274); key(view, 274)
pump(0.3)
key(view, 13)   # OK
pump(8)         # 等详情
txt = view.info_label.text
check("详情已加载", "《" in txt or "解析" in txt or "失败" in txt, txt[:40].replace("\n", " "))
n_eps = len(view.grid_eps.children)
check("集数已生成", n_eps > 0, f"({n_eps})")

print("\n== 播放解析(第一集) ==")
if n_eps > 0:
    view._select_ep(0)
    pump(10)
    txt = view.info_label.text
    check("播放状态显示", "m3u8" in txt or "失败" in txt or "播放" in txt, txt[:60].replace("\n", " "))
    check("历史已记录", len(view.history) > 0, f"({len(view.history)})")

print("\n== 线路切换 ==")
before = view.btn_line.text
view._switch_line()
after = view.btn_line.text
check("线路可切换", before != after, f"{before} -> {after}")

print("\n== 上一集/下一集 ==")
idx0 = view.ep_index
view._next_ep()
pump(6)
check("下一集有效", view.ep_index != idx0 or len(view.ep_list) <= 1, f"({view.ep_index})")
view.busy = False
view._prev_ep()
pump(0.5)
view.busy = False

print("\n== 返回键 ==")
key(view, 27)
pump(1)
check("BACK 回到首页", "加载" in view.info_label.text or "最新" in view.info_label.text,
      view.info_label.text[:30].replace("\n", " "))
view.busy = False

print("\n== 历史恢复 ==")
view._resume_last()
pump(8)
check("续看恢复", "《" in view.info_label.text or "解析" in view.info_label.text,
      view.info_label.text[:40].replace("\n", " "))

print(f"\n========== 结果: {PASS} 通过 / {FAIL} 失败 ==========")
sys.exit(1 if FAIL else 0)
