# -*- coding: utf-8 -*-

ANIME_SOURCES = {
    "age": {
        "name": "AGE动漫",
        "api": "1",
        "baseURL": "https://www.agedm.io",
        "searchURL": "https://www.agedm.io/search?query=@keyword",
        "searchList": "//div[2]/div/section/div/div/div/div",
        "searchName": "//div/div[2]/h5/a",
        "searchResult": "//div/div[2]/h5/a",
        "chapterRoads": "//div[2]/div/section/div/div[2]/div[2]/div[2]/div",
        "chapterResult": "//ul/li/a",
        "useWebview": True
    },
    "1ani": {
        "name": "1ANI动漫",
        "api": "1",
        "baseURL": "https://anime.d1dm.xyz",
        "searchURL": "https://anime.d1dm.xyz/vodsearch/-------------.html?wd=@keyword",
        "searchList": "//div[@class='module-search-item']",
        "searchName": "//h3/a",
        "searchResult": "//h3/a",
        "chapterRoads": "//div[@class='module-blocklist scroll-box scroll-box-y']",
        "chapterResult": "//a",
        "useWebview": True
    },
    "anfuns": {
        "name": "AnFuns",
        "api": "1",
        "baseURL": "https://www.anfuns.org",
        "searchURL": "https://www.anfuns.org/search.html?wd=@keyword",
        "searchList": "//div[2]/div/div[2]/div/div/div[1]/div/div[2]/div/ul/li/div",
        "searchName": "//div/div[2]/div[1]/a",
        "searchResult": "//div/div[2]/div[1]/a",
        "chapterRoads": "//div[2]/div[2]/div/div/div[2]/div/div[1]/div[2]/div",
        "chapterResult": "//div/div/ul/li/a",
        "useWebview": True
    },
    "233dm": {
        "name": "233动漫",
        "api": "2",
        "baseURL": "https://www.233dm.cc",
        "searchURL": "https://www.233dm.cc/vs.html?wd=@keyword",
        "searchList": "//div[@class='movie-ul']/div",
        "searchName": "//div[@class='title']",
        "searchResult": "//a",
        "chapterRoads": "//div[@class='tab-content']/div",
        "chapterResult": "//a",
        "useWebview": True
    }
}
