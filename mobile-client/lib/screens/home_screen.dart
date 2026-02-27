import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/vpn_provider.dart';
import '../providers/server_provider.dart';
import '../widgets/server_card.dart';
import '../widgets/connection_status.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('VLESS VPN'),
        actions: [
          IconButton(
            icon: const Icon(Icons.list),
            onPressed: () => Navigator.pushNamed(context, '/servers'),
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: () => Navigator.pushNamed(context, '/settings'),
          ),
        ],
      ),
      body: Consumer2<VpnProvider, ServerProvider>(
        builder: (context, vpnProvider, serverProvider, child) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                // Connection Status
                ConnectionStatusCard(
                  status: vpnProvider.status,
                  server: vpnProvider.connectedServer ?? serverProvider.selectedServer,
                  duration: vpnProvider.connectionDuration,
                ),
                
                const SizedBox(height: 24),
                
                // Connect Button
                _buildConnectButton(context, vpnProvider, serverProvider),
                
                const SizedBox(height: 32),
                
                // Server Info
                if (serverProvider.selectedServer != null)
                  ServerCard(server: serverProvider.selectedServer!),
                
                const SizedBox(height: 16),
                
                // Load Servers Button
                if (serverProvider.servers.isEmpty)
                  ElevatedButton.icon(
                    onPressed: serverProvider.isLoading
                        ? null
                        : () => serverProvider.loadServers(),
                    icon: serverProvider.isLoading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.refresh),
                    label: Text(serverProvider.isLoading
                        ? 'Загрузка...'
                        : 'Загрузить серверы'),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildConnectButton(
    BuildContext context,
    VpnProvider vpnProvider,
    ServerProvider serverProvider,
  ) {
    final isConnected = vpnProvider.isConnected;
    final isConnecting = vpnProvider.isConnecting;
    final hasServer = serverProvider.selectedServer != null;

    return SizedBox(
      width: double.infinity,
      height: 64,
      child: ElevatedButton(
        onPressed: !isConnecting && hasServer
            ? () {
                if (isConnected) {
                  vpnProvider.disconnect();
                } else {
                  vpnProvider.connect(serverProvider.selectedServer!);
                }
              }
            : null,
        style: ElevatedButton.styleFrom(
          backgroundColor: isConnected
              ? Colors.red
              : isConnecting
                  ? Colors.orange
                  : Colors.green,
          foregroundColor: Colors.white,
        ),
        child: isConnecting
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  SizedBox(width: 12),
                  Text('Подключение...', style: TextStyle(fontSize: 18)),
                ],
              )
            : Text(
                isConnected ? 'ОТКЛЮЧИТЬ' : 'ПОДКЛЮЧИТЬ',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
      ),
    );
  }
}
