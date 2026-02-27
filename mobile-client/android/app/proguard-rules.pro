## Flutter wrapper
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.**  { *; }
-keep class io.flutter.util.**  { *; }
-keep class io.flutter.view.**  { *; }
-keep class io.flutter.**  { *; }
-keep class io.flutter.plugins.**  { *; }

## VLESS VPN
-keep class com.example.vless_vpn.** { *; }
-dontwarn com.example.vless_vpn.**

## HTTP and Network
-keepattributes Signature
-keepattributes *Annotation*
-keep class okhttp3.** { *; }
-keep interface okhttp3.** { *; }
-dontwarn okhttp3.**
-dontwarn okio.**

## Flutter VPN
-keep class com.adylabs.vpnproxy.** { *; }
-dontwarn com.adylabs.vpnproxy.**
