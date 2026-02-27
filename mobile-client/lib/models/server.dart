import 'package:flutter/material.dart';

class Server {
  final String id;
  final String host;
  final int port;
  final String uuid;
  final String security;
  final String sni;
  final String pbk;
  final String sid;
  final String country;
  final String name;
  final int latency;
  final bool isWorking;
  final String flow;

  Server({
    required this.id,
    required this.host,
    required this.port,
    required this.uuid,
    this.security = 'reality',
    this.sni = '',
    this.pbk = '',
    this.sid = '',
    this.country = '🌍',
    this.name = '',
    this.latency = 9999,
    this.isWorking = false,
    this.flow = 'xtls-rprx-vision',
  });

  factory Server.fromJson(Map<String, dynamic> json) {
    return Server(
      id: json['id'] ?? DateTime.now().millisecondsSinceEpoch.toString(),
      host: json['host'] ?? json['address'] ?? '',
      port: json['port'] ?? 443,
      uuid: json['uuid'] ?? '',
      security: json['security'] ?? 'reality',
      sni: json['sni'] ?? json['serverName'] ?? '',
      pbk: json['pbk'] ?? json['publicKey'] ?? '',
      sid: json['sid'] ?? json['shortId'] ?? '',
      country: json['country'] ?? '🌍',
      name: json['name'] ?? '',
      latency: json['latency'] ?? 9999,
      isWorking: json['is_working'] ?? json['isWorking'] ?? false,
      flow: json['flow'] ?? 'xtls-rprx-vision',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'host': host,
      'port': port,
      'uuid': uuid,
      'security': security,
      'sni': sni,
      'pbk': pbk,
      'sid': sid,
      'country': country,
      'name': name,
      'latency': latency,
      'is_working': isWorking,
      'flow': flow,
    };
  }

  String get address => '$host:$port';
  
  String get displayName => name.isNotEmpty ? name : address;
}
