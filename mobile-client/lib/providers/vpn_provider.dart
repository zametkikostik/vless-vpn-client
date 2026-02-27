import 'package:flutter/material.dart';
import '../models/server.dart';

class VpnProvider extends ChangeNotifier {
  VpnStatus _status = VpnStatus.disconnected;
  Server? _connectedServer;
  String _errorMessage = '';
  DateTime? _connectedAt;

  VpnStatus get status => _status;
  Server? get connectedServer => _connectedServer;
  String get errorMessage => _errorMessage;
  DateTime? get connectedAt => _connectedAt;

  bool get isConnected => _status == VpnStatus.connected;
  bool get isConnecting => _status == VpnStatus.connecting;

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
      notifyListeners();
    } catch (e) {
      _status = VpnStatus.disconnected;
      _errorMessage = 'Ошибка подключения: ${e.toString()}';
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

  String get connectionDuration {
    if (_connectedAt == null) return '';
    final duration = DateTime.now().difference(_connectedAt!);
    final hours = duration.inHours.toString().padLeft(2, '0');
    final minutes = (duration.inMinutes % 60).toString().padLeft(2, '0');
    final seconds = (duration.inSeconds % 60).toString().padLeft(2, '0');
    return '$hours:$minutes:$seconds';
  }
}

enum VpnStatus {
  disconnected,
  connecting,
  connected,
  error,
}
