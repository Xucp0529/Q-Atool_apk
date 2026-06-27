[app]

# 应用基本信息
title = Q&A 添加题目
package.name = qaadder
package.domain = com.qatool
source.dir = .
source.include_exts = py,html,css,js,json,txt
version = 1.0

# 依赖
requirements = python3,flask

# 应用入口
main.py = main.py

# 权限
android.permissions = INTERNET

# 方向
orientation = portrait
fullscreen = 0


[android]

# Android API 级别
android.api = 29
android.minapi = 29
android.ndk = 25b

# WebView bootstrap（Flask 应用使用）
android.bootstrap = webview
android.port = 5000

# 自动接受 SDK 许可证
android.accept_sdk_license = True

# 架构
android.arch = arm64-v8a

# 关闭安全浏览
android.webview_enable_safebrowsing = 0


[buildozer]

# 构建日志级别
log_level = 2
warn_on_root = 1
