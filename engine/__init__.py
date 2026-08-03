# -*- coding: utf-8 -*-
import os
import json

class RuleEngineManager:
    """
    引擎层核心管理类：负责管理全系统的配置文件加载、本地播放历史、收藏夹以及设置信息的持久化存储。
    """
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.favorite_path = os.path.join(data_dir, "favorite.json")
        self.history_path = os.path.join(data_dir, "history.json")
        self.settings_path = os.path.join(data_dir, "settings.json")
        
        self.favorites = []
        self.history = []
        self.settings = {}
        self.load_all_data()

    def load_all_data(self):
        """加载所有的本地数据文件"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
            
        self.favorites = self._read_json(self.favorite_path)
        self.history = self._read_json(self.history_path)
        self.settings = self._read_json(self.settings_path)

    def _read_json(self, path):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_favorites(self):
        """保存收藏夹数据到本地"""
        with open(self.favorite_path, 'w', encoding='utf-8') as f:
            json.dump(self.favorites, f, ensure_ascii=False, indent=4)

    def save_history(self):
        """保存播放历史数据到本地"""
        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=4)

    def save_settings(self):
        """保存系统配置到本地"""
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=4)

    def add_favorite(self, anime_item):
        """添加番剧至收藏夹"""
        if anime_item not in self.favorites:
            self.favorites.append(anime_item)
            self.save_favorites()

    def remove_favorite(self, anime_item):
        """从收藏夹移除"""
        if anime_item in self.favorites:
            self.favorites.remove(anime_item)
            self.save_favorites()

