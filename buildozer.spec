[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

requirements = python3,kivy,requests,lxml,python-vlc

android.minapi = 21
android.api = 31

# 自动同意 Google Android SDK 许可协议（云端打包必备）
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
