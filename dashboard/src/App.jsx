import React, { useState, useEffect } from 'react';
import { Plus, Settings, RefreshCw, Smartphone, CheckCircle, XCircle, Search, Copy, Download, ExternalLink, Clock, Zap, Shield, Trash2, X, Eye } from 'lucide-react';
import { databases, QUEUE_COLL_ID, DB_ID, PROXIES_COLL_ID, ASSETS_BUCKET_ID } from './appwrite';
import { ID, Query } from 'appwrite';

const App = () => {
  const [numbers, setNumbers] = useState([]);
  const [proxies, setProxies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchPending, setSearchPending] = useState('');
  const [searchSuccess, setSearchSuccess] = useState('');
  const [searchFailed, setSearchFailed] = useState('');
  const [showProxyModal, setShowProxyModal] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [newProxy, setNewProxy] = useState({ connection_string: '', platform_username: '', platform_password: '' });
  const [selectedItem, setSelectedItem] = useState(null); // For logs modal

  // Fetch numbers from Appwrite
  const fetchNumbers = async () => {
    try {
      const res = await databases.listDocuments(DB_ID, QUEUE_COLL_ID, [
        Query.orderDesc('created_at'),
        Query.limit(100)
      ]);
      setNumbers(res.documents);
    } catch (e) {
      console.error('Error fetching numbers:', e);
    }
  };

  // Fetch proxies from Appwrite
  const fetchProxies = async () => {
    try {
      const res = await databases.listDocuments(DB_ID, PROXIES_COLL_ID, [Query.limit(50)]);
      setProxies(res.documents);
    } catch (e) {
      console.error('Error fetching proxies:', e);
    }
  };

  // Add new phone number(s) to queue - supports multiple numbers
  const handleAdd = async () => {
    if (!inputValue.trim()) return;
    setLoading(true);
    try {
      // Split by newlines, commas, spaces, or tabs
      const rawNumbers = inputValue.split(/[\n,\s\t]+/).filter(n => n.trim());
      const uniqueNumbers = [...new Set(rawNumbers.map(n => n.trim()))];

      let added = 0;
      for (const phone of uniqueNumbers) {
        if (!phone) continue;
        await databases.createDocument(DB_ID, QUEUE_COLL_ID, ID.unique(), {
          phone: phone,
          status: 'pending',
          created_at: new Date().toISOString()
        });
        added++;
      }

      setInputValue('');
      fetchNumbers();
      if (added > 1) {
        console.log(`Added ${added} numbers to queue`);
      }
    } catch (e) {
      console.error('Error adding number:', e);
      alert('Failed to add number: ' + e.message);
    }
    setLoading(false);
  };

  // Add new proxy - supports user:pass@host:port format
  const handleAddProxy = async () => {
    const input = newProxy.connection_string.trim();
    if (!input) return;
    setLoading(true);
    try {
      let connectionString = input;

      // Parse user:pass@host:port format
      if (input.includes('@')) {
        const [userPass, hostPort] = input.split('@');
        const [user, pass] = userPass.split(':');
        const [host, port] = hostPort.split(':');
        if (user && pass && host && port) {
          connectionString = `${host}:${port}:${user}:${pass}`;
        }
      }

      await databases.createDocument(DB_ID, PROXIES_COLL_ID, ID.unique(), {
        connection_string: connectionString,
        platform_username: newProxy.platform_username || null,
        platform_password: newProxy.platform_password || null,
        status: 'active',
        usage_count: 0
      });
      setNewProxy({ connection_string: '', platform_username: '', platform_password: '' });
      setShowProxyModal(false);
      fetchProxies();
    } catch (e) {
      console.error('Error adding proxy:', e);
      alert('Failed to add proxy: ' + e.message);
    }
    setLoading(false);
  };

  // Load data on mount
  useEffect(() => {
    fetchNumbers();
    fetchProxies();
    const interval = setInterval(fetchNumbers, 10000); // Auto-refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const successCount = numbers.filter(n => n.status === 'success').length;
  const pendingCount = numbers.filter(n => n.status === 'pending').length;
  const processingCount = numbers.filter(n => n.status === 'processing').length;
  const failedCount = numbers.filter(n => n.status === 'failed').length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white p-6">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      </div>

      <div className="relative w-full px-4">
        {/* Logs Modal */}
        {selectedItem && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-xl font-bold font-mono text-emerald-400">{selectedItem.phone}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${selectedItem.status === 'success' ? 'bg-emerald-500/20 text-emerald-400' : selectedItem.status === 'failed' ? 'bg-red-500/20 text-red-400' : selectedItem.status === 'processing' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'}`}>
                    {selectedItem.status?.toUpperCase()}
                  </span>
                </div>
                <button onClick={() => setSelectedItem(null)} className="p-2 hover:bg-gray-800 rounded-lg">
                  <X size={20} />
                </button>
              </div>

              {selectedItem.error_reason && (
                <div className="bg-red-500/10 text-red-400 px-3 py-2 rounded-lg text-sm font-mono mb-4">
                  ❌ {selectedItem.error_reason}
                </div>
              )}

              <div className="flex-1 overflow-y-auto bg-gray-950 rounded-lg p-4 font-mono text-sm">
                <div className="text-gray-400 text-xs mb-2">📋 Processing Logs:</div>
                {selectedItem.logs ? (
                  <pre className="whitespace-pre-wrap text-gray-300">{selectedItem.logs}</pre>
                ) : (
                  <div className="text-gray-600 italic">No logs available yet...</div>
                )}
              </div>

              <div className="flex gap-2 mt-4 justify-end">
                {selectedItem.screenshot_id && (
                  <button
                    className="px-4 py-2 bg-emerald-500/10 text-emerald-400 text-sm rounded-lg hover:bg-emerald-500 hover:text-white transition-all flex items-center gap-2"
                    onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${selectedItem.screenshot_id}/view?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                  >
                    <Smartphone size={14} /> View Screenshot
                  </button>
                )}
                {selectedItem.cookie_file_id && (
                  <button
                    className="px-4 py-2 bg-blue-500/10 text-blue-400 text-sm rounded-lg hover:bg-blue-500 hover:text-white transition-all flex items-center gap-2"
                    onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${selectedItem.cookie_file_id}/download?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                  >
                    <Download size={14} /> Download Cookies
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Proxy Modal */}
        {showProxyModal && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                <Shield className="text-emerald-500" /> Add New Proxy
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-gray-400 uppercase block mb-2">Connection String *</label>
                  <input
                    type="text"
                    placeholder="user:pass@host:port"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all font-mono text-sm"
                    value={newProxy.connection_string}
                    onChange={(e) => setNewProxy({ ...newProxy, connection_string: e.target.value })}
                  />
                  <div className="text-xs text-gray-500 mt-1">Format: user:pass@host:port (e.g., nNcDyyf3Pi:mobile;us;@proxy.soax.com:9000)</div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-gray-400 uppercase block mb-2">Platform User</label>
                    <input
                      type="text"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:border-emerald-500 outline-none transition-all"
                      value={newProxy.platform_username}
                      onChange={(e) => setNewProxy({ ...newProxy, platform_username: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-gray-400 uppercase block mb-2">Platform Pass</label>
                    <input
                      type="password"
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:border-emerald-500 outline-none transition-all"
                      value={newProxy.platform_password}
                      onChange={(e) => setNewProxy({ ...newProxy, platform_password: e.target.value })}
                    />
                  </div>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-emerald-500/20"
                    onClick={handleAddProxy}
                    disabled={loading}
                  >
                    {loading ? 'Adding...' : 'Save Proxy'}
                  </button>
                  <button
                    className="px-6 py-3 border border-gray-600 rounded-lg hover:bg-gray-800 transition-all"
                    onClick={() => setShowProxyModal(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Header */}
        <header className="flex justify-between items-center mb-8 pb-6 border-b border-gray-800/50">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <Zap className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight">
                FB OTP <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">CONTROL</span>
              </h1>
              <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold mt-1">Production Dashboard</p>
            </div>
          </div>

          <nav className="flex gap-2 bg-gray-900/50 p-1 rounded-xl border border-gray-800">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all ${activeTab === 'dashboard' ? 'bg-emerald-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              <Smartphone size={18} /> Dashboard
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium transition-all ${activeTab === 'settings' ? 'bg-emerald-500 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
            >
              <Settings size={18} /> Proxies
            </button>
          </nav>
        </header>

        {activeTab === 'dashboard' ? (
          <main>
            {/* Stats Bar */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
                  <CheckCircle className="text-emerald-500" size={24} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-emerald-500">{successCount}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Success</div>
                </div>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                  <Clock className="text-blue-500" size={24} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-blue-500">{pendingCount}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Pending</div>
                </div>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                  <RefreshCw className="text-yellow-500 animate-spin" size={24} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-yellow-500">{processingCount}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Processing</div>
                </div>
              </div>
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 flex items-center gap-4">
                <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                  <XCircle className="text-red-500" size={24} />
                </div>
                <div>
                  <div className="text-3xl font-bold text-red-500">{failedCount}</div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider">Failed</div>
                </div>
              </div>
            </div>

            {/* Quick Add Bar */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 mb-6 flex items-start gap-4">
              <span className="text-xs font-bold text-emerald-500 uppercase whitespace-nowrap px-3 py-1 bg-emerald-500/10 rounded-full mt-2">New Entry</span>
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter phone numbers (one per line, or separated by commas)&#10;+201234567890&#10;+201987654321"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all resize-none"
                rows={2}
              />
              <button
                onClick={handleAdd}
                disabled={loading}
                className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-6 py-3 rounded-lg transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2"
              >
                {loading ? <RefreshCw className="animate-spin" size={20} /> : <Plus size={20} />}
                Add
              </button>
              <button
                onClick={fetchNumbers}
                className="p-3 bg-gray-800 hover:bg-gray-700 rounded-lg transition-all"
                title="Refresh"
              >
                <RefreshCw size={20} className="text-gray-400" />
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1" style={{ minHeight: 'calc(100vh - 320px)' }}>
              {/* LEFT: PENDING QUEUE */}
              <div className="bg-gray-900/50 border border-gray-800 rounded-xl flex flex-col overflow-hidden">
                <div className="flex justify-between items-center p-4 border-b border-gray-800">
                  <h2 className="font-bold flex items-center gap-2 text-blue-400 uppercase tracking-wider text-sm">
                    <Clock size={16} /> Pending ({pendingCount + processingCount})
                  </h2>
                </div>
                <div className="overflow-y-auto flex-1 p-3">
                  <div className="space-y-2">
                    {numbers
                      .filter(n => n.status === 'pending' || n.status === 'processing')
                      .map(item => (
                        <div
                          key={item.$id}
                          className={`p-3 rounded-lg border flex justify-between items-center transition-all cursor-pointer hover:scale-[1.02] ${item.status === 'processing' ? 'bg-yellow-500/10 border-yellow-500/30 animate-pulse' : 'bg-gray-800/50 border-gray-700 hover:border-blue-500/50'}`}
                          onClick={() => setSelectedItem(item)}
                        >
                          <div>
                            <div className="font-mono text-sm font-semibold">{item.phone}</div>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${item.status === 'processing' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-blue-500/20 text-blue-400'}`}>
                              {item.status?.toUpperCase()}
                            </span>
                          </div>
                          <div className="flex gap-1">
                            <button
                              className="p-1.5 text-blue-400 hover:bg-blue-500/20 rounded transition-all"
                              onClick={(e) => { e.stopPropagation(); setSelectedItem(item); }}
                              title="View Logs"
                            >
                              <Eye size={14} />
                            </button>
                            <button
                              className="p-1.5 text-gray-500 hover:text-red-500 hover:bg-red-500/10 rounded transition-all"
                              onClick={async (e) => {
                                e.stopPropagation();
                                if (confirm("Delete?")) {
                                  await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                                  fetchNumbers();
                                }
                              }}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        </div>
                      ))}
                    {numbers.filter(n => n.status === 'pending' || n.status === 'processing').length === 0 && (
                      <div className="text-center text-gray-600 py-8 italic text-sm">Queue empty</div>
                    )}
                  </div>
                </div>
              </div>

              {/* MIDDLE: SUCCESS */}
              <div className="bg-gray-900/50 border border-emerald-500/20 rounded-xl flex flex-col overflow-hidden shadow-lg shadow-emerald-500/5">
                <div className="flex flex-col p-4 border-b border-gray-800 gap-2">
                  <h2 className="font-bold flex items-center gap-2 text-emerald-400 uppercase tracking-wider text-sm">
                    <CheckCircle size={16} /> Success ({successCount})
                  </h2>
                  <div className="relative">
                    <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search phone..."
                      value={searchSuccess}
                      onChange={(e) => setSearchSuccess(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:border-emerald-500 outline-none"
                    />
                  </div>
                </div>
                <div className="overflow-y-auto flex-1 p-3">
                  <div className="space-y-2">
                    {numbers
                      .filter(n => n.status === 'success' && (!searchSuccess || n.phone?.includes(searchSuccess)))
                      .map(item => (
                        <div
                          key={item.$id}
                          className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 hover:bg-emerald-500/10 transition-all cursor-pointer hover:scale-[1.01]"
                          onClick={() => setSelectedItem(item)}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="font-mono text-base text-emerald-100 font-bold">{item.phone}</div>
                            <span className="text-xs text-emerald-400/60">{item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}</span>
                          </div>
                          {item.result_url && (
                            <div className="flex items-center gap-2 bg-black/30 p-2 rounded mb-2 border border-emerald-500/10" onClick={e => e.stopPropagation()}>
                              <ExternalLink size={12} className="text-emerald-500 flex-shrink-0" />
                              <span className="truncate text-xs text-gray-400 flex-1 font-mono">{item.result_url}</span>
                              <button className="text-emerald-500 hover:text-white" onClick={() => navigator.clipboard.writeText(item.result_url)}>
                                <Copy size={12} />
                              </button>
                            </div>
                          )}
                          <div className="flex gap-1.5 flex-wrap" onClick={e => e.stopPropagation()}>
                            <button
                              className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded hover:bg-blue-500 hover:text-white transition-all flex items-center gap-1"
                              onClick={() => setSelectedItem(item)}
                            >
                              <Eye size={10} /> Logs
                            </button>
                            {item.screenshot_id && (
                              <button
                                className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded hover:bg-emerald-500 hover:text-white transition-all flex items-center gap-1"
                                onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.screenshot_id}/view?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                              >
                                <Smartphone size={10} /> Shot
                              </button>
                            )}
                            {item.cookies_json && (
                              <button
                                className="px-2 py-1 bg-cyan-500/10 text-cyan-400 text-xs rounded hover:bg-cyan-500 hover:text-white transition-all flex items-center gap-1"
                                onClick={() => {
                                  navigator.clipboard.writeText(item.cookies_json);
                                  alert('Cookies copied to clipboard!');
                                }}
                                title="Copy cookies JSON to clipboard"
                              >
                                <Copy size={10} /> Copy
                              </button>
                            )}
                            {item.cookie_file_id && (
                              <button
                                className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded hover:bg-blue-500 hover:text-white transition-all flex items-center gap-1"
                                onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.cookie_file_id}/download?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                              >
                                <Download size={10} /> Download
                              </button>
                            )}
                            {item.result_url && (
                              <button
                                className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded hover:bg-purple-500 hover:text-white transition-all flex items-center gap-1"
                                onClick={() => window.open(item.result_url, '_blank')}
                                title="Open recovery URL in new tab"
                              >
                                <ExternalLink size={10} /> Open URL
                              </button>
                            )}
                            <button
                              className="px-2 py-1 hover:bg-red-500/20 text-gray-500 hover:text-red-400 text-xs rounded transition-all ml-auto"
                              onClick={async () => {
                                if (confirm("Delete?")) {
                                  await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                                  fetchNumbers();
                                }
                              }}
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                          {/* Inline Cookies Display */}
                          {item.cookies_json && (
                            <details className="mt-2" onClick={e => e.stopPropagation()}>
                              <summary className="text-xs text-blue-400 cursor-pointer hover:text-blue-300">🍪 View Cookies ({(() => { try { return JSON.parse(item.cookies_json).length; } catch { return '?'; } })()} items)</summary>
                              <pre className="bg-gray-950 p-2 rounded text-xs overflow-auto max-h-40 mt-1 text-gray-300 font-mono whitespace-pre-wrap">
                                {(() => { try { return JSON.stringify(JSON.parse(item.cookies_json), null, 2); } catch { return item.cookies_json; } })()}
                              </pre>
                            </details>
                          )}
                        </div>
                      ))}
                    {successCount === 0 && (
                      <div className="text-center text-gray-600 py-8 italic text-sm">No success yet</div>
                    )}
                  </div>
                </div>
              </div>

              {/* RIGHT: FAILED */}
              <div className="bg-gray-900/50 border border-red-500/20 rounded-xl flex flex-col overflow-hidden shadow-lg shadow-red-500/5">
                <div className="flex flex-col p-4 border-b border-gray-800 gap-2">
                  <h2 className="font-bold flex items-center gap-2 text-red-400 uppercase tracking-wider text-sm">
                    <XCircle size={16} /> Failed ({failedCount})
                  </h2>
                  <div className="relative">
                    <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input
                      type="text"
                      placeholder="Search phone..."
                      value={searchFailed}
                      onChange={(e) => setSearchFailed(e.target.value)}
                      className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-8 pr-3 py-1.5 text-xs focus:border-red-500 outline-none"
                    />
                  </div>
                </div>
                <div className="overflow-y-auto flex-1 p-3">
                  <div className="space-y-2">
                    {numbers
                      .filter(n => n.status === 'failed' && (!searchFailed || n.phone?.includes(searchFailed)))
                      .map(item => (
                        <div
                          key={item.$id}
                          className="p-3 rounded-lg bg-red-500/5 border border-red-500/20 hover:bg-red-500/10 transition-all cursor-pointer hover:scale-[1.01]"
                          onClick={() => setSelectedItem(item)}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <div className="font-mono text-base text-red-100 font-bold">{item.phone}</div>
                            <span className="text-xs text-red-400/60">{item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}</span>
                          </div>
                          {item.error_reason && (
                            <div className="bg-red-500/10 text-red-400 px-2 py-1 rounded text-xs font-mono mb-2">
                              ❌ {item.error_reason}
                            </div>
                          )}
                          <div className="flex gap-1.5 flex-wrap" onClick={e => e.stopPropagation()}>
                            <button
                              className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded hover:bg-blue-500 hover:text-white transition-all flex items-center gap-1"
                              onClick={() => setSelectedItem(item)}
                            >
                              <Eye size={10} /> Logs
                            </button>
                            {item.screenshot_id && (
                              <button
                                className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded hover:bg-red-500 hover:text-white transition-all flex items-center gap-1"
                                onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.screenshot_id}/view?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                              >
                                <Smartphone size={10} /> Screenshot
                              </button>
                            )}
                            <button
                              className="px-2 py-1 hover:bg-red-500/20 text-gray-500 hover:text-red-400 text-xs rounded transition-all ml-auto"
                              onClick={async () => {
                                if (confirm("Delete?")) {
                                  await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                                  fetchNumbers();
                                }
                              }}
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </div>
                      ))}
                    {failedCount === 0 && (
                      <div className="text-center text-gray-600 py-8 italic text-sm">No failures</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </main>
        ) : (
          /* PROXIES TAB */
          <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Shield className="text-emerald-500" /> Proxy Pool
              </h2>
              <button
                className="bg-emerald-500 hover:bg-emerald-600 text-white font-bold px-5 py-2.5 rounded-lg transition-all shadow-lg shadow-emerald-500/20 flex items-center gap-2"
                onClick={() => setShowProxyModal(true)}
              >
                <Plus size={18} /> Add Proxy
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left py-3 px-4 text-xs font-bold text-gray-500 uppercase">Connection String</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-gray-500 uppercase">Platform Creds</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-gray-500 uppercase">Usage</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-gray-500 uppercase">Status</th>
                    <th className="text-left py-3 px-4 text-xs font-bold text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {proxies.map((proxy) => (
                    <tr key={proxy.$id} className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-emerald-400 truncate max-w-[250px]">{proxy.connection_string}</span>
                          <button className="text-gray-500 hover:text-white" onClick={() => navigator.clipboard.writeText(proxy.connection_string)}>
                            <Copy size={14} />
                          </button>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <div className="text-xs text-gray-400">
                          <div><span className="text-gray-600">U:</span> {proxy.platform_username || '-'}</div>
                          <div><span className="text-gray-600">P:</span> {proxy.platform_password ? '••••••' : '-'}</div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-lg font-bold">{proxy.usage_count || 0}</span>
                        <span className="text-xs text-gray-500 ml-1">runs</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`text-xs px-3 py-1 rounded-full font-bold ${proxy.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'}`}>
                          {proxy.status?.toUpperCase() || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex gap-2">
                          <button
                            className="p-2 hover:bg-emerald-500/20 rounded-lg text-emerald-500 transition-all"
                            title="Reset"
                            onClick={async () => {
                              await databases.updateDocument(DB_ID, PROXIES_COLL_ID, proxy.$id, { status: 'active', usage_count: 0 });
                              fetchProxies();
                            }}
                          >
                            <RefreshCw size={16} />
                          </button>
                          <button
                            className="p-2 hover:bg-red-500/20 rounded-lg text-red-500 transition-all"
                            onClick={async () => {
                              if (confirm("Delete proxy?")) {
                                await databases.deleteDocument(DB_ID, PROXIES_COLL_ID, proxy.$id);
                                fetchProxies();
                              }
                            }}
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                  {proxies.length === 0 && (
                    <tr>
                      <td colSpan="5" className="text-center py-16 text-gray-500 italic">No proxies in the pool</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div >
  );
};

export default App;
