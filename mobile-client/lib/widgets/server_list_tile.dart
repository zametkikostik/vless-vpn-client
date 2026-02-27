import 'package:flutter/material.dart';
import '../models/server.dart';

class ServerListTile extends StatelessWidget {
  final Server server;
  final bool isSelected;
  final VoidCallback onTap;

  const ServerListTile({
    super.key,
    required this.server,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Text(
        server.country,
        style: const TextStyle(fontSize: 28),
      ),
      title: Text(
        server.displayName,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      subtitle: Row(
        children: [
          _buildLatencyIndicator(server.latency),
          const SizedBox(width: 8),
          if (server.isWorking)
            const Text(
              '✓ Рабочий',
              style: TextStyle(color: Colors.green, fontSize: 12),
            ),
        ],
      ),
      trailing: isSelected
          ? const Icon(Icons.check_circle, color: Colors.green)
          : null,
      onTap: onTap,
    );
  }

  Widget _buildLatencyIndicator(int latency) {
    Color color;
    String label;

    if (latency < 50) {
      color = Colors.green;
      label = 'Отл';
    } else if (latency < 100) {
      color = Colors.lightGreen;
      label = 'Хор';
    } else if (latency < 200) {
      color = Colors.orange;
      label = 'Сред';
    } else {
      color = Colors.red;
      label = 'Плох';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: color.withOpacity(0.2),
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}
