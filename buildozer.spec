[app]
title = AnimeTV
package.name = animetv
package.domain = org.test
version = 0.1

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,otf

# 锁定 Python 3.11 及其主机版本，并加入兼容的 sh 版本以防报错
requirements = python3==3.11.0,hostpython3==3.11.0,kivy,requests,lxml,ffpyplayer,sh==1.14.3

android.minapi = 21
android.api = 33
android.ndk = 25b
android.ndk_api = 21
android.accept_sdk_license = True

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK
android.uses_cleartext_traffic = True

orientation = landscape
android.archs = arm64-v8a, armeabi-v7a
