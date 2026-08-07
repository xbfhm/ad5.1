# -*- coding: utf-8 -*-
"""把 16.5MB 的 NotoSansCJK-Regular.otf 裁剪成面向番剧场景的瘦身版。

覆盖范围:
  - ASCII (0x20-0x7E)
  - GB2312 全部 6763 个汉字 (一级+二级)
  - GBK 扩展区常用字 (GBK 全部, 约 2.1 万汉字, 保证生僻番剧名/日文汉字可显示)
  - 常用标点 / 全角符号 / 番剧常用特殊符号

输出: NotoSansCJK-TV.otf (预期 5~8MB, 原文件 16.5MB)
"""
import os
import sys
from fontTools import subset

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NotoSansCJK-Regular.otf")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "NotoSansCJK-TV.otf")

def gb2312_chars():
    chars = set()
    for area in range(16, 88):          # 区位 16-87
        for pos in range(1, 95):        # 位 01-94
            b1, b2 = area + 0xA0, pos + 0xA0
            if 0xA1 <= b2 <= 0xFE and 0xA1 <= b1 <= 0xFE:
                try:
                    chars.add(bytes([b1, b2]).decode("gb2312"))
                except Exception:
                    pass
    return chars

def gbk_extra_chars():
    chars = set()
    for b1 in range(0x81, 0xFE):
        for b2 in range(0x40, 0xFF):
            if b2 == 0x7F:
                continue
            try:
                chars.add(bytes([b1, b2]).decode("gbk"))
            except Exception:
                pass
    return chars

def main():
    chars = set(chr(c) for c in range(0x20, 0x7F))          # ASCII 可打印
    chars |= gb2312_chars()
    chars |= gbk_extra_chars()
    # 常用符号补充 (全角标点、番剧标题常见符号)
    chars |= set("·—–…「」『』『』【】〖〗《》〈〉～！？，。、；：（）·★☆※○●◎◇◆▲△■□→←↑↓×÷±°①②③④⑤⑥⑦⑧⑨⑩・〜♪♡★☆")
    chars |= set("①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳")
    chars.discard("\n")
    chars.discard("\r")
    chars.discard("\t")

    text = "".join(sorted(chars))
    print(f"覆盖字符数: {len(text)}")

    options = subset.Options()
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.recalc_bounds = True
    options.drop_tables += ["FFTM", "GSUB", "GPOS", "GDEF"]  # 保留 GSUB/GPOS? 关掉更小
    options.flavor = None

    subsetter = subset.Subsetter(options=options)
    from fontTools.ttLib import TTFont
    font = TTFont(SRC, lazy=True)
    subsetter.populate(text=text)
    subsetter.subset(font)
    font.save(DST)

    old = os.path.getsize(SRC) / 1024 / 1024
    new = os.path.getsize(DST) / 1024 / 1024
    print(f"原始: {old:.1f}MB -> 瘦身: {new:.1f}MB (省 {(1-new/old)*100:.0f}%)")

if __name__ == "__main__":
    main()
