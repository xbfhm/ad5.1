[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

requirements = python3,kivy,requests,lxml,ffpyplayer

android.minapi = 21
android.api = 31

# 核心重点：强制锁定 NDK r25b，拒绝使用报错的 r28c
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
