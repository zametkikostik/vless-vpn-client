import 'package:flutter/material.dart';
import 'package:flutter_vpn/flutter_vpn.dart';
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

      // Prepare VLESS config
      final config = _buildVlessConfig(server);
      
      await Vpn.prepare();
      await Vpn.start(config);

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
    try {
      await Vpn.stop();
    } catch (e) {
      // Ignore errors on disconnect
    }

    _status = VpnStatus.disconnected;
    _connectedServer = null;
    _connectedAt = null;
    notifyListeners();
  }

  String _buildVlessConfig(Server server) {
    // Build VLESS URL
    final vlessUrl = 'vless://${server.uuid}@${server.host}:${server.port}';
    final params = <String, String>{
      'security': server.security,
      'sni': server.sni,
      'pbk': server.pbk,
      'sid': server.sid,
      'fp': 'chrome',
      'flow': server.flow,
      'type': 'tcp',
    };
    
    final queryString = params.entries
        .where((e) => e.value.isNotEmpty)
        .map((e) => '${e.key}=${e.value}')
        .join('&');
    
    return '$vlessUrl?$queryString#${Uri.encodeComponent(server.name)}';
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
