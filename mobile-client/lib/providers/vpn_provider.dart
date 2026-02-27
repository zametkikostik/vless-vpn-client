import 'package:flutter/material.dart';
import '../models/server.dart';

class VpnProvider extends ChangeNotifier {
  VpnStatus _status = VpnStatus.disconnected;
  Server? _connectedServer;
  String _errorMessage = '';
  DateTime? _connectedAt;
  
  // DPI Bypass settings
  bool _dpiBypassEnabled = true;
  String _dpiStrategy = 'fragmentation';
  int _fragmentSizeMin = 50;
  int _fragmentSizeMax = 200;
  int _fragmentIntervalMin = 10;
  int _fragmentIntervalMax = 50;

  VpnStatus get status => _status;
  Server? get connectedServer => _connectedServer;
  String get errorMessage => _errorMessage;
  DateTime? get connectedAt => _connectedAt;
  
  // DPI Bypass getters
  bool get dpiBypassEnabled => _dpiBypassEnabled;
  String get dpiStrategy => _dpiStrategy;
  int get fragmentSizeMin => _fragmentSizeMin;
  int get fragmentSizeMax => _fragmentSizeMax;
  int get fragmentIntervalMin => _fragmentIntervalMin;
  int get fragmentIntervalMax => _fragmentIntervalMax;

  bool get isConnected => _status == VpnStatus.connected;
  bool get isConnecting => _status == VpnStatus.connecting;
  
  // Statistics
  int _blocksDetected = 0;
  int _bypassesSuccessful = 0;
  int _strategySwitches = 0;

  int get blocksDetected => _blocksDetected;
  int get bypassesSuccessful => _bypassesSuccessful;
  int get strategySwitches => _strategySwitches;

  Future<void> connect(Server server) async {
    try {
      _status = VpnStatus.connecting;
      _errorMessage = '';
      notifyListeners();

      // TODO: Implement actual VPN connection using native platform channel
      // For now, simulate connection for UI testing
      await Future.delayed(const Duration(seconds: 2));

      _status = VpnStatus.connected;
      _connectedServer = server;
      _connectedAt = DateTime.now();
      _bypassesSuccessful++;
      notifyListeners();
      
      // Show notification
      await _showConnectionNotification(server);
    } catch (e) {
      _status = VpnStatus.disconnected;
      _errorMessage = 'Ошибка подключения: ${e.toString()}';
      _blocksDetected++;
      notifyListeners();
      rethrow;
    }
  }

  Future<void> disconnect() async {
    // TODO: Implement actual VPN disconnection
    _status = VpnStatus.disconnected;
    _connectedServer = null;
    _connectedAt = null;
    notifyListeners();
  }

  void setDpiBypassEnabled(bool enabled) {
    _dpiBypassEnabled = enabled;
    notifyListeners();
  }

  void setDpiStrategy(String strategy) {
    _dpiStrategy = strategy;
    _strategySwitches++;
    notifyListeners();
  }

  void setFragmentConfig({
    int? sizeMin,
    int? sizeMax,
    int? intervalMin,
    int? intervalMax,
  }) {
    if (sizeMin != null) _fragmentSizeMin = sizeMin;
    if (sizeMax != null) _fragmentSizeMax = sizeMax;
    if (intervalMin != null) _fragmentIntervalMin = intervalMin;
    if (intervalMax != null) _fragmentIntervalMax = intervalMax;
    notifyListeners();
  }

  String get connectionDuration {
    if (_connectedAt == null) return '';
    final duration = DateTime.now().difference(_connectedAt!);
    final hours = duration.inHours.toString().padLeft(2, '0');
    final minutes = (duration.inMinutes % 60).toString().padLeft(2, '0');
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    return '$hours:$minutes:$seconds';
  }

  Map<String, dynamic> getStatistics() {
    return {
      'blocks_detected': _blocksDetected,
      'bypasses_successful': _bypassesSuccessful,
      'strategy_switches': _strategySwitches,
      'current_strategy': _dpiStrategy,
    };
  }

  Future<void> _showConnectionNotification(Server server) async {
    const androidDetails = AndroidNotificationDetails(
      'vless_vpn_channel',
      'VLESS VPN',
      channelDescription: 'VPN connection status',
      importance: Importance.high,
      priority: Priority.high,
      icon: '@mipmap/ic_launcher',
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await flutterLocalNotificationsPlugin.show(
      0,
      'VLESS VPN Подключен',
      '${server.country} ${server.host}:${server.port}\nDPI Bypass активен',
      details,
    );
  }
}

enum VpnStatus {
  disconnected,
  connecting,
  connected,
  error,
}
