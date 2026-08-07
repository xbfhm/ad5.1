# -*- coding: utf-8 -*-
import sys, os, time, types, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_pending = []
class FW:
    _focused = False
    def __init__(self, **kw):
        self.kw = kw; self.text = kw.get("text",""); self.children=[]
        self.parent=None; self.x=self.y=0; self.width=200; self.height=50
        self.size_hint_x=kw.get("size_hint_x",1); self.size_hint_y=kw.get("size_hint_y",None)
        self.focus=False; self.bindings={}
        for k,v in kw.items():
            if not hasattr(self,k): setattr(self,k,v)
    def bind(self,**kw): self.bindings.update(kw)
    def dispatch(self,name):
        cb=self.bindings.get(name)
        if cb: cb(self)
    def add_widget(self,w): self.children.append(w); w.parent=self
    def clear_widgets(self): self.children=[]
    def set_focus(self,on): self._focused=on
    def to_window(self,x,y):
        px,py=x,y; n=self
        while n.parent is not None: px+=n.parent.x; py+=n.parent.y; n=n.parent
        return px,py
    def setter(self,name): return lambda obj,val: setattr(obj,name,val)
    @property
    def minimum_height(self): return 0
class FakeBox(FW): pass
class FakeGrid(FW): pass
class FakeButton(FW): pass
class FakeLabel(FW): pass
class FakeTextInput(FW): pass
class FakeScroll(FW): scroll_y=1.0

def mm(name, **attrs):
    m=types.ModuleType(name)
    for k,v in attrs.items(): setattr(m,k,v)
    sys.modules[name]=m

mm("kivy.config", Config=types.SimpleNamespace(set=lambda *a,**k: None))
mm("kivy", __version__="s")
mm("kivy.utils", platform="linux")
mm("kivy.clock", Clock=types.SimpleNamespace(schedule_once=lambda fn,d=0: _pending.append(fn)))
mm("kivy.core.text", LabelBase=types.SimpleNamespace(register=lambda *a,**k: None))
mm("kivy.core.clipboard", Clipboard=types.SimpleNamespace(copy=lambda u: None))
mm("kivy.core.window", Window=types.SimpleNamespace(width=1920,height=1080,clearcolor=(0,0,0,1),softinput_mode="",bind=lambda *a,**k:None))
mm("kivy.app", App=object)
mm("kivy.uix.boxlayout", BoxLayout=FakeBox)
mm("kivy.uix.gridlayout", GridLayout=FakeGrid)
mm("kivy.uix.button", Button=FakeButton)
mm("kivy.uix.label", Label=FakeLabel)
mm("kivy.uix.textinput", TextInput=FakeTextInput)
mm("kivy.uix.scrollview", ScrollView=FakeScroll)

import main
view = main.AnimeTVAppView()

def pump(sec):
    end=time.time()+sec
    while time.time()<end:
        while _pending:
            fn=_pending.pop(0)
            try: fn(0)
            except Exception as e: print("CB ERR:", e)
        time.sleep(0.02)

pump(8)  # 等首页完成
print("首页完成后 busy:", view.busy)
view.input_search.text = "葬送的芙莉莲"
view.do_search()
pump(8)
print("搜索后:", view.info_label.text[:50].replace("\n"," "), "| busy:", view.busy)
print("结果按钮:", len(view.grid_list.children))
if view.grid_list.children:
    it = view.grid_list.children[0].kw.get("text","")
    print("第一项:", it)
    view.grid_list.children[0].dispatch("on_release")
    print("点击后立即:", view.info_label.text[:50].replace("\n"," "), "| busy:", view.busy)
    pump(12)
    print("12s后:", view.info_label.text[:90].replace("\n"," "))
    print("busy:", view.busy, "| ep_list:", len(view.ep_list), "| eps按钮:", len(view.grid_eps.children))

# ---- 续: 选集播放验证 (若未执行过) ----
if view.ep_list and not view.history:
    print("\n== 选集播放 ==")
    view._select_ep(0)
    pump(20)
    print("解析结果:", view.info_label.text[:80].replace("\n"," "))
    print("busy:", view.busy, "| 历史:", len(view.history))
    if view.history:
        print("历史首条:", view.history[0]["name"], view.history[0]["ep"])
    view._switch_line()
    print("线路切换:", view.btn_line.text)
    i0 = view.ep_index
    view.busy = False
    view._next_ep()
    print("下一集:", i0, "->", view.ep_index)
    view.busy = False
    key(view, 27)
    pump(1)
    print("BACK:", view.info_label.text[:30].replace("\n"," "))
