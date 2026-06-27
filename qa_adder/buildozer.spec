[app]

title = QA Adder
package.name = qaadder
package.domain = com.qatool
source.dir = .
source.include_exts = py,html,css,js,json,txt
version = 1.0

requirements = python3,flask

android.permissions = INTERNET

orientation = portrait
fullscreen = 0

android.bootstrap = webview
android.port = 5000

android.api = 29
android.minapi = 29
android.ndk = 25b

android.accept_sdk_license = yes
android.arch = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
