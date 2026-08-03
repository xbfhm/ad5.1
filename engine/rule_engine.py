# -*- coding: utf-8 -*-
import requests
from lxml import etree
import urllib.parse
import re

class MultiRuleEngine:
    def __init__(self, rule_dict):
        self.rule = rule_dict
        self.base_url = self.rule.get("baseURL", "")
        self.headers = {
            "User-Agent": self.rule.get("userAgent") or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": self.base_url
        }

    def _get_full_url(self, url):
        if not url:
            return ""
        if url.startswith("http"):
            return url
        return urllib.parse.urljoin(self.base_url, url)

    def _extract_attr(self, element, xpath_str, attr="text"):
        try:
            nodes = element.xpath("." + xpath_str if xpath_str.startswith("//") else xpath_str)
            if not nodes:
                return ""
            target = nodes[0]
            
            if isinstance(target, str):
                return target.strip()
            
            if attr == "text":
                return " ".join(target.xpath(".//text()")).strip()
            elif attr == "href":
                hrefs = target.xpath("./@href")
                return hrefs[0] if hrefs else ""
        except Exception:
            return ""
        return ""

    def search(self, keyword):
        search_url = self.rule["searchURL"].replace("@keyword", urllib.parse.quote(keyword))
        try:
            res = requests.get(search_url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            items = html.xpath(self.rule["searchList"])
            results = []
            
            for item in items:
                name = self._extract_attr(item, self.rule["searchName"], attr="text")
                url_str = self._extract_attr(item, self.rule["searchResult"], attr="href")
                
                if name and url_str:
                    results.append({
                        "name": name,
                        "url": self._get_full_url(url_str)
                    })
            return results
        except Exception as e:
            print(f"[{self.rule.get('name')}] 搜索错误: {e}")
            return []

    def get_episodes(self, detail_url):
        try:
            res = requests.get(detail_url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            
            roads = html.xpath(self.rule["chapterRoads"])
            if not roads:
                return []
                
            for road in roads:
                chapters = road.xpath("." + self.rule["chapterResult"])
                episodes = []
                for ch in chapters:
                    title = " ".join(ch.xpath(".//text()")).strip()
                    url_str = ch.xpath("./@href")
                    if title and url_str:
                        episodes.append({
                            "title": title,
                            "page_url": self._get_full_url(url_str[0])
                        })
                if episodes:
                    return episodes
            return []
        except Exception as e:
            print(f"[{self.rule.get('name')}] 选集错误: {e}")
            return []

    def parse_video_url(self, ep_url):
        try:
            res = requests.get(ep_url, headers=self.headers, timeout=10)
            res.encoding = 'utf-8'
            text = res.text
            
            pattern = r'(https?://[^\s\'"]+\.(?:m3u8|mp4)[^\s\'"]*)'
            match = re.search(pattern, text)
            if match:
                return match.group(1).replace("\\", "")
                
            return ep_url
        except Exception:
            return ep_url
