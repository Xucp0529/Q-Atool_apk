[app]

# 应用基本信息
title = Q&A 答题
package.name = qaapp
package.domain = com.qatool
source.dir = .
source.include_exts = py,html,css,js,json,txt
version = 1.0

# 依赖
requirements = python3,flask

# 权限
android.permissions = INTERNET

# 全屏/方向
orientation = portrait
fullscreen = 0

# WebView bootstrap（Flask 应用使用）
android.bootstrap = webview
android.port = 5000

# Android API 级别
android.api = 29
android.minapi = 29
android.ndk = 25b

# 自动接受 SDK 许可证（关键！）
android.accept_sdk_license = yes

# 架构
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
