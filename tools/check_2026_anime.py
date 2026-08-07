# -*- coding: utf-8 -*-
"""检测 AGE 动漫 2026 年 1-7 月新番能否正常解析播放。

流程: catalog?year=2026&season=N -> detail/{id} -> jx 解析 -> m3u8 验证
"""
import requests, re, json, time, sys, io, os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = "https://api.agedm.io/v2/"
JX = "https://jx.wuzhoupai.com:8443/m3u8/?url="
HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
           "Referer": "https://m.agedm.io/"}
M3U8_LINES = ["ffm3u8", "bfzym3u8", "wjm3u8", "hnm3u8", "lzm3u8", "wolong", "sdm3u8"]

def get_json(path, retries=2):
    for i in range(retries):
        try:
            r = requests.get(BASE + path, headers=HEADERS, timeout=15)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
                return r.json()
        except Exception:
            pass
        time.sleep(0.5)
    return None

def fetch_catalog(season):
    videos, page = [], 1
    while True:
        d = get_json(f"catalog?year=2026&season={season}&page={page}")
        if not d or not d.get("videos"):
            break
        videos.extend(d["videos"])
        total = d.get("total", 0)
        if len(videos) >= total:
            break
        page += 1
        time.sleep(0.15)
    return videos

def extract_m3u8(html):
    m = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
    if m:
        return m[0]
    return ""

def check_anime(v):
    aid = v["id"]
    name = v["name"]
    res = {"id": aid, "name": name, "premiere": v.get("premiere", ""),
           "status": v.get("status", ""), "result": "", "detail": ""}
    d = get_json(f"detail/{aid}")
    if not d or "video" not in d:
        res["result"] = "详情接口失败"
        return res
    video = d["video"]
    playlists = video.get("playlists", {}) or {}
    if not playlists:
        res["result"] = "无播放线路"
        return res
    # 依次尝试所有 m3u8 线路, 任一条成功即可
    tried = []
    for line in M3U8_LINES:
        if line not in playlists or not playlists[line]:
            continue
        tried.append(line)
        eps = playlists[line]
        enc, ep_title = eps[0][1], eps[0][0]
        try:
            r = requests.get(JX + enc, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                continue
            m3u8 = extract_m3u8(r.text)
            if not m3u8:
                continue
            for attempt in range(3):
                try:
                    r2 = requests.get(m3u8, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=15)
                    if r2.status_code == 200 and r2.text.strip().startswith("#EXTM3U"):
                        res["result"] = "可播放"
                        res["detail"] = f"{line} {ep_title} -> {m3u8}"
                        return res
                    break
                except Exception:
                    if attempt < 2:
                        time.sleep(1.2)
                        continue
                    break
        except Exception:
            continue
    res["result"] = "全部线路失败"
    res["detail"] = f"尝试线路: {','.join(tried) or '无'}"
    return res

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=0, help="1/4/7 指定季度, 0=全部")
    args = ap.parse_args()

    seasons = {"冬季(1-3月)": 1, "春季(4-6月)": 4, "夏季(7-9月)": 7}
    if args.season:
        seasons = {k: v for k, v in seasons.items() if v == args.season}

    # 断点缓存
    CACHE = "/tmp/check_cache.json"
    done = {}
    if os.path.exists(CACHE):
        try:
            with open(CACHE, encoding="utf-8") as f:
                done = {r["id"]: r for r in json.load(f)}
        except Exception:
            done = {}

    all_results = list(done.values())
    for label, s in seasons.items():
        vids = fetch_catalog(s)
        todo = [v for v in vids if v["id"] not in done]
        print(f"\n===== 2026{label} season={s}: {len(vids)} 部, 待测 {len(todo)} =====", flush=True)
        results = []
        with ThreadPoolExecutor(max_workers=4) as ex:
            futs = {ex.submit(check_anime, v): v for v in todo}
            for i, f in enumerate(as_completed(futs), 1):
                res = f.result()
                results.append(res)
                done[res["id"]] = res
                # 每部完成立即落盘, 中断不丢进度
                with open(CACHE, "w", encoding="utf-8") as fh:
                    json.dump(list(done.values()), fh, ensure_ascii=False)
                print(f"[{i}/{len(todo)}] {res['result']:12s} {res['name'][:36]} ({res['premiere']})", flush=True)
        all_results = list(done.values())
        time.sleep(1)

    print("\n\n========== 汇总 ==========")
    from collections import Counter
    cnt = Counter(r["result"] for r in all_results)
    for k, v in cnt.most_common():
        print(f"{k}: {v}")
    ok = [r for r in all_results if r["result"] == "可播放"]
    print(f"\n可播放: {len(ok)}/{len(all_results)} ({len(ok)*100//max(1,len(all_results))}%)")
    print("\n不可播放列表:")
    for r in all_results:
        if r["result"] != "可播放":
            print(f"  [{r['result']}] {r['name']} ({r['premiere']}) {r['detail'][:70]}")
    with open("/tmp/check_result.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
