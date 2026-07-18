[app]
title = The Vault
package.name = thevault
package.domain = com.schmitty
source.dir = .
source.include_exts = py,png,jpg,jpeg,json,kv,atlas,wav,mp3,ogg,ttf
version = 0.9.0
requirements = python3,kivy==2.3.1,pyjnius
orientation = landscape
fullscreen = 1
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/splash.png

android.api = 35
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True
android.permissions = READ_EXTERNAL_STORAGE
android.logcat_filters = *:S python:D
android.copy_libs = 1

[buildozer]
log_level = 2
warn_on_root = 1
