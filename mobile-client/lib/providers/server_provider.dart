import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/server.dart';

class ServerProvider extends ChangeNotifier {
  List<Server> _servers = [];
  Server? _selectedServer;
  bool _isLoading = false;
  String _errorMessage = '';

  List<Server> get servers => _servers;
  Server? get selectedServer => _selectedServer;
  bool get isLoading => _isLoading;
  String get errorMessage => _errorMessage;

  List<Server> get workingServers => 
      _servers.where((s) => s.isWorking).toList();

  Future<void> loadServers({String url = ''}) async {
    _isLoading = true;
    _errorMessage = '';
    notifyListeners();

    try {
      // Default: load from GitHub
      if (url.isEmpty) {
        url = 'https://raw.githubusercontent.com/zametkikostik/vless-vpn-client/main/vpn-client-aggregator/data/servers.json';
      }

      final response = await http.get(Uri.parse(url));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        if (data is List) {
          _servers = data.map((s) => Server.fromJson(s)).toList();
        } else if (data is Map && data['servers'] is List) {
          _servers = (data['servers'] as List)
              .map((s) => Server.fromJson(s))
              .toList();
        }

        // Sort by latency
        _servers.sort((a, b) => a.latency.compareTo(b.latency));
        
        // Auto-select best server
        if (_servers.isNotEmpty && _selectedServer == null) {
          _selectedServer = _servers.first;
        }
      } else {
        _errorMessage = 'Ошибка загрузки: ${response.statusCode}';
      }
    } catch (e) {
      _errorMessage = 'Ошибка сети: ${e.toString()}';
    }

    _isLoading = false;
    notifyListeners();
  }

  void selectServer(Server server) {
    _selectedServer = server;
    notifyListeners();
  }

  Future<void> scanServers() async {
    // TODO: Implement server scanning
    notifyListeners();
  }
}
