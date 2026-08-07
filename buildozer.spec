[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.2

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf
source.exclude_dirs = tools,.github,.git,bin,.buildozer
source.exclude_patterns = tools/*,buildozer.spec

# 低内存关键: 移除 requests/lxml(原生库大且吃内存), 全部用标准库
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pyjnius

android.minapi = 21
android.api = 33
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True
android.fullscreen = 1
android.wakelock = True

# 该电视为 arm64-v8a (MStar MSD6A828), 单架构减半体积加快安装
android.archs = arm64-v8a

orientation = landscape

[buildozer]
log_level = 2
warn_on_root = 1
