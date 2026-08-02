[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# 使用 ffpyplayer 替代 python-vlc，确保 Android 端视频原生解码支持
requirements = python3,kivy,requests,lxml,ffpyplayer

# 最低兼容 Android 5.1 (API 21)
android.minapi = 21
android.api = 31

# 自动同意 SDK 许可协议
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
