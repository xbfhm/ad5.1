[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.3

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf,ttf
source.exclude_dirs = tools,.github,.git,bin,.buildozer
source.exclude_patterns = tools/*,buildozer.spec

# 低内存关键: 移除 requests/lxml(原生库大且吃内存), 全部用标准库
# ffpyplayer: 内置播放器(ffmpeg 内核, 支持 m3u8), 无需外部播放器
requirements = python3==3.11.9,hostpython3==3.11.9,kivy==2.3.0,pyjnius,ffpyplayer=vendor/ffpyplayer-4.5.1
# ffpyplayer 用本地修补版: 原版引用 ffmpeg6 已移除的 avfft.h 导致编译失败, 已删掉无用声明

android.minapi = 21
android.api = 26
# targetSdk 26: 模仿云视听等TV大厂的低targetSdk宽适配策略, 老系统行为最贴近
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True
android.fullscreen = 1
android.wakelock = True

# 双架构保险: 电视系统若为32位镜像(部分电视厂), v7a 也能运行
android.archs = arm64-v8a, armeabi-v7a

orientation = landscape

[buildozer]
log_level = 2
warn_on_root = 1
