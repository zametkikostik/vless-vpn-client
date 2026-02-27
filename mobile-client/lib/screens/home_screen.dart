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
        title: const Text('VLESS VPN Ultimate'),
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
          return RefreshIndicator(
            onRefresh: () => serverProvider.loadServers(),
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // Header with DPI Bypass badge
                  _buildHeader(vpnProvider),

                  const SizedBox(height: 24),

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

                  // DPI Bypass Status
                  _buildDpiBypassStatus(vpnProvider),

                  const SizedBox(height: 24),

                  // Server Info
                  if (serverProvider.selectedServer != null)
                    ServerCard(server: serverProvider.selectedServer!),

                  const SizedBox(height: 16),

                  // Load/Scan Servers Button
                  _buildServerActions(context, serverProvider),
                  
                  const SizedBox(height: 16),
                  
                  // Statistics
                  _buildStatistics(vpnProvider),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildHeader(VpnProvider vpnProvider) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2c3e50), Color(0xFFe74c3c)],
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.red.withOpacity(0.3),
            blurRadius: 10,
            offset: const Offset(0, 5),
          ),
        ],
      ),
      child: Row(
        children: [
          const Icon(Icons.security, size: 40, color: Colors.white),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'VLESS VPN',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'DPI Bypass + Чебурнет',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.white.withOpacity(0.9),
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: vpnProvider.dpiBypassEnabled
                  ? Colors.green
                  : Colors.orange,
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(
              vpnProvider.dpiBypassEnabled ? '✓ DPI Bypass' : '✗ DPI Bypass',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ],
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
      height: 72,
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
          elevation: 8,
          shadowColor: isConnected ? Colors.red : Colors.green,
        ),
        child: isConnecting
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  ),
                  SizedBox(width: 16),
                  Text('Подключение...', style: TextStyle(fontSize: 20)),
                ],
              )
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    isConnected ? Icons.power_off : Icons.power,
                    size: 28,
                  ),
                  const SizedBox(width: 12),
                  Text(
                    isConnected ? 'ОТКЛЮЧИТЬ' : 'ПОДКЛЮЧИТЬ',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
      ),
    );
  }

  Widget _buildDpiBypassStatus(VpnProvider vpnProvider) {
    return Card(
      color: Colors.blue.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.shield, color: Colors.blue, size: 24),
                const SizedBox(width: 8),
                const Text(
                  'DPI Bypass Настройки',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildDpiFeature('Фрагментация пакетов', '50-200 байт'),
            const SizedBox(height: 8),
            _buildDpiFeature('Padding', 'Случайные данные'),
            const SizedBox(height: 8),
            _buildDpiFeature('TLS мимикрия', 'Chrome 120+'),
            const SizedBox(height: 8),
            _buildDpiFeature(
              'Стратегия',
              vpnProvider.dpiStrategy,
              valueColor: Colors.orange,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDpiFeature(String label, String value, {Color? valueColor}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 14),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.bold,
            color: valueColor ?? Colors.green,
          ),
        ),
      ],
    );
  }

  Widget _buildServerActions(
    BuildContext context,
    ServerProvider serverProvider,
  ) {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
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
                : 'Обновить'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              // Navigate to servers screen for scanning
              Navigator.pushNamed(context, '/servers');
            },
            icon: const Icon(Icons.scan),
            label: const Text('Скан'),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.purple,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 16),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildStatistics(VpnProvider vpnProvider) {
    final stats = vpnProvider.getStatistics();
    
    return Card(
      color: Colors.grey.withOpacity(0.1),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '📊 Статистика DPI Bypass',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 12),
            _buildStatRow('Блокировок обнаружено', stats['blocks_detected'] ?? 0),
            const SizedBox(height: 8),
            _buildStatRow('Успешных обходов', stats['bypasses_successful'] ?? 0, successColor: true),
            const SizedBox(height: 8),
            _buildStatRow('Переключений стратегии', stats['strategy_switches'] ?? 0),
          ],
        ),
      ),
    );
  }

  Widget _buildStatRow(String label, int value, {bool successColor = false}) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: const TextStyle(fontSize: 14)),
        Text(
          value.toString(),
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: successColor ? Colors.green : Colors.white,
          ),
        ),
      ],
    );
  }
}
