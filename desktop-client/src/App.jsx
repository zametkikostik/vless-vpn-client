import React, { useState, useEffect } from 'react';
import { Power, RefreshCw, Shield, Zap, Globe, Activity, Server, Settings, LogOut } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

// API Base URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Connection states
const ConnectionState = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error'
};

function App() {
  // State
  const [connectionState, setConnectionState] = useState(ConnectionState.DISCONNECTED);
  const [selectedServer, setSelectedServer] = useState(null);
  const [servers, setServers] = useState([]);
  const [stats, setStats] = useState({ upload: 0, download: 0, duration: 0 });
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Check auth on mount
  useEffect(() => {
    checkAuth();
    fetchServers();
  }, []);

  // Update stats when connected
  useEffect(() => {
    let interval;
    if (connectionState === ConnectionState.CONNECTED) {
      interval = setInterval(updateStats, 1000);
    }
    return () => clearInterval(interval);
  }, [connectionState]);

  const checkAuth = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/api/v1/users/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/nodes`);
      if (res.ok) {
        const data = await res.json();
        setServers(data);
        if (data.length > 0 && !selectedServer) {
          setSelectedServer(data[0]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch servers:', error);
    }
  };

  const connect = async () => {
    if (!selectedServer) {
      toast.error('Please select a server');
      return;
    }

    setConnectionState(ConnectionState.CONNECTING);
    
    try {
      // Get VPN config
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API_BASE}/api/v1/configs/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ node_id: selectedServer.id })
      });

      if (!res.ok) throw new Error('Failed to generate config');

      const config = await res.json();
      
      // In production: Pass config to VPN engine via Tauri command
      // For now, simulate connection
      await simulateConnection();
      
      toast.success(`Connected to ${selectedServer.name}`);
    } catch (error) {
      console.error('Connection failed:', error);
      setConnectionState(ConnectionState.ERROR);
      toast.error('Connection failed');
    }
  };

  const simulateConnection = () => {
    return new Promise(resolve => {
      setTimeout(() => {
        setConnectionState(ConnectionState.CONNECTED);
        resolve();
      }, 2000);
    });
  };

  const disconnect = () => {
    setConnectionState(ConnectionState.DISCONNECTED);
    setStats({ upload: 0, download: 0, duration: 0 });
    toast.success('Disconnected');
  };

  const updateStats = () => {
    setStats(prev => ({
      upload: prev.upload + Math.random() * 1000,
      download: prev.download + Math.random() * 5000,
      duration: prev.duration + 1
    }));
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Login Form
  if (!user && !loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center p-4">
        <Toaster position="top-center" />
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 w-full max-w-md border border-white/20">
          <div className="text-center mb-8">
            <Shield className="w-16 h-16 mx-auto text-blue-400 mb-4" />
            <h1 className="text-3xl font-bold text-white mb-2">VLESS VPN SaaS</h1>
            <p className="text-gray-300">Secure. Fast. Private.</p>
          </div>
          
          <form className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all"
            >
              Sign In
            </button>
          </form>
          
          <p className="text-center text-gray-300 mt-6">
            Don't have an account?{' '}
            <button className="text-blue-400 hover:underline">Sign Up</button>
          </p>
        </div>
      </div>
    );
  }

  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-white">Loading...</p>
        </div>
      </div>
    );
  }

  // Main App
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
      <Toaster position="top-center" />
      
      {/* Header */}
      <header className="bg-white/10 backdrop-blur-lg border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-blue-400" />
            <h1 className="text-xl font-bold text-white">VLESS VPN SaaS</h1>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-300">{user?.email}</span>
            <button className="text-gray-300 hover:text-white">
              <Settings className="w-5 h-5" />
            </button>
            <button className="text-gray-300 hover:text-white">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Connection Panel */}
          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-white/20">
              {/* Connection Button */}
              <div className="text-center mb-8">
                <button
                  onClick={connectionState === ConnectionState.CONNECTED ? disconnect : connect}
                  disabled={connectionState === ConnectionState.CONNECTING}
                  className={`w-32 h-32 rounded-full flex items-center justify-center mx-auto transition-all transform hover:scale-105 ${
                    connectionState === ConnectionState.CONNECTED
                      ? 'bg-gradient-to-br from-green-400 to-emerald-600'
                      : connectionState === ConnectionState.CONNECTING
                      ? 'bg-gradient-to-br from-yellow-400 to-orange-600 animate-pulse'
                      : 'bg-gradient-to-br from-blue-400 to-purple-600'
                  }`}
                >
                  <Power className="w-16 h-16 text-white" />
                </button>
                <p className="text-white text-xl font-semibold mt-4">
                  {connectionState === ConnectionState.CONNECTED
                    ? 'Connected'
                    : connectionState === ConnectionState.CONNECTING
                    ? 'Connecting...'
                    : 'Disconnected'}
                </p>
              </div>

              {/* Stats */}
              {connectionState === ConnectionState.CONNECTED && (
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <Activity className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                    <p className="text-gray-300 text-sm">Upload</p>
                    <p className="text-white font-semibold">{formatBytes(stats.upload)}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <Activity className="w-6 h-6 text-green-400 mx-auto mb-2" />
                    <p className="text-gray-300 text-sm">Download</p>
                    <p className="text-white font-semibold">{formatBytes(stats.download)}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4 text-center">
                    <Activity className="w-6 h-6 text-purple-400 mx-auto mb-2" />
                    <p className="text-gray-300 text-sm">Duration</p>
                    <p className="text-white font-semibold">{formatDuration(stats.duration)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Server Selection */}
          <div>
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
              <div className="flex items-center space-x-2 mb-4">
                <Globe className="w-5 h-5 text-blue-400" />
                <h2 className="text-lg font-semibold text-white">Servers</h2>
              </div>
              
              <div className="space-y-2">
                {servers.map((server) => (
                  <button
                    key={server.id}
                    onClick={() => setSelectedServer(server)}
                    className={`w-full p-4 rounded-lg text-left transition-all ${
                      selectedServer?.id === server.id
                        ? 'bg-blue-500/30 border-2 border-blue-400'
                        : 'bg-white/5 border-2 border-transparent hover:bg-white/10'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{server.name}</p>
                        <p className="text-gray-400 text-sm">{server.country}</p>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center space-x-1">
                          <Zap className="w-4 h-4 text-yellow-400" />
                          <span className="text-white text-sm">{server.latency}ms</span>
                        </div>
                        <span className={`text-xs ${server.status === 'online' ? 'text-green-400' : 'text-red-400'}`}>
                          {server.status}
                        </span>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Subscription Info */}
        <div className="mt-6">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-white">Current Plan</h3>
                <p className="text-gray-300">{user?.plan?.toUpperCase()} Plan</p>
              </div>
              <button className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg text-white font-semibold hover:from-blue-600 hover:to-purple-700 transition-all">
                Upgrade Plan
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
