import 'package:flutter/material.dart';
import '../models/server.dart';
import '../providers/vpn_provider.dart';

class ConnectionStatusCard extends StatelessWidget {
  final VpnStatus status;
  final Server? server;
  final String duration;

  const ConnectionStatusCard({
    super.key,
    required this.status,
    required this.server,
    required this.duration,
  });

  @override
  Widget build(BuildContext context) {
    final isConnected = status == VpnStatus.connected;
    final isConnecting = status == VpnStatus.connecting;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            // Status Icon
            Container(
              width: 100,
              height: 100,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isConnected
                    ? Colors.green.withOpacity(0.2)
                    : isConnecting
                        ? Colors.orange.withOpacity(0.2)
                        : Colors.grey.withOpacity(0.2),
                border: Border.all(
                  color: isConnected
                      ? Colors.green
                      : isConnecting
                          ? Colors.orange
                          : Colors.grey,
                  width: 4,
                ),
              ),
              child: Icon(
                isConnected
                    ? Icons.security
                    : isConnecting
                        ? Icons.sync
                        : Icons.cloud_off,
                size: 50,
                color: isConnected
                    ? Colors.green
                    : isConnecting
                        ? Colors.orange
                        : Colors.grey,
              ),
            ),

            const SizedBox(height: 24),

            // Status Text
            Text(
              isConnected
                  ? 'ПОДКЛЮЧЕНО'
                  : isConnecting
                      ? 'ПОДКЛЮЧЕНИЕ...'
                      : 'ОТКЛЮЧЕНО',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: isConnected
                    ? Colors.green
                    : isConnecting
                        ? Colors.orange
                        : Colors.grey,
              ),
            ),

            if (duration.isNotEmpty && isConnected) ...[
              const SizedBox(height: 8),
              Text(
                duration,
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[400],
                ),
              ),
            ],

            if (server != null && !isConnecting) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.grey[800],
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(server!.country, style: const TextStyle(fontSize: 18)),
                    const SizedBox(width: 8),
                    Text(
                      server!.displayName,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
