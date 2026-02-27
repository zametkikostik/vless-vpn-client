import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:package_info_plus/package_info_plus.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  String _version = '';

  @override
  void initState() {
    super.initState();
    _loadVersion();
  }

  Future<void> _loadVersion() async {
    final info = await PackageInfo.fromPlatform();
    setState(() {
      _version = '${info.version} (${info.buildNumber})';
    });
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Не удалось открыть $url')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Настройки'),
      ),
      body: ListView(
        children: [
          const ListTile(
            leading: Icon(Icons.info_outline),
            title: Text('О приложении'),
            subtitle: Text('VLESS VPN Client'),
          ),
          ListTile(
            leading: const Icon(Icons.tag),
            title: const Text('Версия'),
            subtitle: Text(_version.isEmpty ? 'Загрузка...' : _version),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.code),
            title: const Text('Исходный код'),
            subtitle: const Text('GitHub'),
            trailing: const Icon(Icons.open_in_new, size: 16),
            onTap: () => _launchUrl(
              'https://github.com/zametkikostik/vless-vpn-client',
            ),
          ),
          ListTile(
            leading: const Icon(Icons.description),
            title: const Text('Документация'),
            trailing: const Icon(Icons.open_in_new, size: 16),
            onTap: () => _launchUrl(
              'https://github.com/zametkikostik/vless-vpn-client/blob/main/README.md',
            ),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.privacy_tip),
            title: const Text('Политика конфиденциальности'),
            trailing: const Icon(Icons.open_in_new, size: 16),
            onTap: () => _launchUrl(
              'https://github.com/zametkikostik/vless-vpn-client/blob/main/PRIVACY.md',
            ),
          ),
          const Divider(),
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'VLESS VPN Client - Production Version\n'
              'License: MIT',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ),
        ],
      ),
    );
  }
}
