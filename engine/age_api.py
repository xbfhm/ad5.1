# -*- coding: utf-8 -*-
"""AGE动漫 官方 API 客户端 (纯标准库实现, 无第三方依赖)

接口链路(2026年8月实测全部可用):
  search?query=关键字   -> 搜索
  detail/{id}           -> 详情+播放列表(含加密串)
  catalog?year=&season= -> 按季度浏览新番
  home-list             -> 首页最新/推荐
  解析服务 jx.wuzhoupai.com:8443/m3u8/?url={enc} -> 播放器页, 内含 m3u8 直链

说明: 加密串 age_xxx 通过解析服务换取真实 m3u8 地址, 无防盗链可直接播放。
"""
import json
import re
import ssl
import time
import urllib.parse
import urllib.request

API_BASE = "https://api.agedm.io/v2/"
JX_BASE = "https://jx.wuzhoupai.com:8443/m3u8/?url="
JX_BASE_VIP = "https://jx.wuzhoupai.com:8443/vip/?url="

# 免费 m3u8 线路优先级 (AGE 线路标签: ffm3u8=非凡 bfzym3u8=暴风 wjm3u8=无尽
# hnm3u8=红牛 lzm3u8=计算云 wolong=凤雏云 sdm3u8=闪电)
M3U8_LINES = ["ffm3u8", "bfzym3u8", "wjm3u8", "hnm3u8", "lzm3u8", "wolong", "sdm3u8"]
LINE_LABELS = {
    "ffm3u8": "非凡", "bfzym3u8": "暴风", "wjm3u8": "无尽", "hnm3u8": "红牛",
    "lzm3u8": "计算云", "wolong": "凤雏云", "sdm3u8": "闪电", "zjm3u8": "自建云",
    "kbm3u8": "快播", "bjm3u8": "八戒", "tkm3u8": "天空", "99m3u8": "九九",
    "qiyi": "爱奇艺", "qq": "腾讯", "youku": "优酷", "mgtv": "芒果",
    "bilibili": "B站", "sohu": "搜狐", "xigua": "西瓜",
}

_UA = ("Mozilla/5.0 (Linux; Android 7.0; TV) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/98.0 Mobile Safari/537.36")
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "application/json,text/html,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://m.agedm.io/",
}

# Android 5.1.1 上部分 CDN 证书链不完整, 允许降级到不验证(内容为公开视频流)
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


class AgeError(Exception):
    pass


def _fetch(url, timeout=15, retries=2):
    """GET 请求, 失败重试, 返回响应文本(bytes解码)"""
    req = urllib.request.Request(url, headers=_HEADERS)
    last_err = None
    for i in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as resp:
                data = resp.read()
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype:
                    return data.decode("utf-8", errors="replace")
                # 非 json: 按 charset 尝试
                for enc in ("utf-8", "gbk", "gb2312", "latin-1"):
                    try:
                        return data.decode(enc)
                    except Exception:
                        continue
                return data.decode("utf-8", errors="replace")
        except Exception as e:
            last_err = e
            time.sleep(0.4 * (i + 1))
    raise AgeError(f"网络请求失败: {url[:60]} ({last_err.__class__.__name__})")


def _get_json(path, params=None):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    text = _fetch(url)
    try:
        return json.loads(text)
    except Exception:
        raise AgeError("返回数据不是合法JSON")


def search(keyword, limit=30):
    """搜索番剧, 返回 [{id, name, status, premiere, type, uptodate, cover}]"""
    if not keyword:
        return []
    d = _get_json("search", {"query": keyword})
    videos = (d.get("data") or {}).get("videos") or []
    out = []
    for v in videos[:limit]:
        out.append({
            "id": v.get("id"),
            "name": v.get("name", ""),
            "status": v.get("status", ""),
            "premiere": v.get("premiere", ""),
            "type": v.get("type", ""),
            "uptodate": v.get("uptodate", ""),
        })
    return out


def detail(aid):
    """详情, 返回 dict: name/cover/intro/playlists/line_order 等"""
    d = _get_json(f"detail/{aid}")
    video = d.get("video") or {}
    playlists = video.get("playlists") or {}
    jx = d.get("player_jx") or {}
    return {
        "id": video.get("id"),
        "name": video.get("name", ""),
        "name_other": video.get("name_other", ""),
        "cover": video.get("cover", ""),
        "intro": video.get("intro_clean") or video.get("intro", ""),
        "premiere": video.get("premiere", ""),
        "status": video.get("status", ""),
        "uptodate": video.get("uptodate", ""),
        "type": video.get("type", ""),
        "tags": (video.get("tags_arr") or [])[:6],
        "playlists": playlists,
        "jx_zj": jx.get("zj", JX_BASE),
        "jx_vip": jx.get("vip", JX_BASE_VIP),
    }


def episodes(detail_data):
    """从详情数据提取集数列表(优先免费m3u8线路), 返回
    [{line, line_label, title, enc, vip:bool}], 按线路分组扁平化"""
    playlists = detail_data.get("playlists") or {}
    result = []
    for line in M3U8_LINES:
        eps = playlists.get(line) or []
        label = LINE_LABELS.get(line, line)
        for title, enc in eps:
            result.append({
                "line": line,
                "line_label": label,
                "title": title,
                "enc": enc,
                "vip": False,
            })
    # 若无免费线路, 回退到 VIP 源 (qiyi 等), 仍尝试解析(部分可播)
    if not result:
        for line, eps in playlists.items():
            if line in M3U8_LINES:
                continue
            label = LINE_LABELS.get(line, line)
            for title, enc in eps:
                result.append({
                    "line": line, "line_label": label,
                    "title": title, "enc": enc, "vip": True,
                })
    return result


def parse_video_url(enc, vip=False):
    """加密串 -> m3u8 直链"""
    if not enc:
        raise AgeError("无播放标识")
    jx = JX_BASE_VIP if vip else JX_BASE
    # enc 本身已是 URL 编码串, 直接拼接, 不可再 quote(会双重编码)
    html = _fetch(jx + enc, timeout=20, retries=2)
    m = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
    if m:
        return m.group(0)
    # 兜底: 有些解析页返回 mp4
    m = re.search(r'https?://[^\s"\']+\.mp4[^\s"\']*', html)
    if m:
        return m.group(0)
    raise AgeError("解析页未找到播放地址")


def catalog(year=None, season=None, page=1, limit=24):
    """按年份/季度浏览. season: 1=1月番 4=4月番 7=7月番 10=10月番
    返回 [{id, name, premiere, status, uptodate, type}]"""
    params = {"page": page}
    if year:
        params["year"] = year
    if season:
        params["season"] = season
    d = _get_json("catalog", params)
    videos = d.get("videos") or []
    return [{
        "id": v.get("id"),
        "name": v.get("name", ""),
        "premiere": v.get("premiere", ""),
        "status": v.get("status", ""),
        "uptodate": v.get("uptodate", ""),
        "type": v.get("type", ""),
    } for v in videos[:limit]]


def home():
    """首页: 最新/推荐/周更表"""
    d = _get_json("home-list")
    out = {"latest": [], "recommend": [], "week": []}
    for k in ("latest", "recommend"):
        for v in (d.get(k) or [])[:12]:
            out[k].append({
                "id": v.get("AID"),
                "name": v.get("Title", ""),
                "new": v.get("NewTitle", ""),
                "cover": v.get("PicSmall", ""),
            })
    for wd in sorted((d.get("week_list") or {}).keys(), key=int)[:7]:
        for v in (d.get("week_list", {}).get(wd) or [])[:8]:
            out["week"].append({
                "id": v.get("id"),
                "name": v.get("name", ""),
                "isnew": bool(v.get("isnew")),
            })
    return out
