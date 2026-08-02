[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# 显式锁定 Python 为稳定的 3.10 版本，彻底规避 python 3.14 编译崩溃！
requirements = python3==3.10.13,kivy,requests,lxml,ffpyplayer

android.minapi = 21
android.api = 31

# 锁定稳定版 NDK r25b
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

# 允许自动更新/修复 Android SDK
android.skip_update = False

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
