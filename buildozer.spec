[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

# 改回标准的 python3 依赖表达，杜绝找不到编译配方的报错！
requirements = python3==3.10.11,kivy,requests,lxml,ffpyplayer

android.minapi = 21
android.api = 33

android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
