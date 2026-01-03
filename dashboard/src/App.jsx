import React, { useState, useEffect } from 'react';
import { Plus, Settings, RefreshCw, FileText, Smartphone, CheckCircle, XCircle, Search, Copy, Download, ExternalLink } from 'lucide-react';
import { databases, QUEUE_COLL_ID, DB_ID, PROXIES_COLL_ID, ASSETS_BUCKET_ID } from './appwrite';
import { ID, Query } from 'appwrite';

const App = () => {
  const [numbers, setNumbers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchTerm, setSearchTerm] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [proxies, setProxies] = useState([]);
  const [showProxyModal, setShowProxyModal] = useState(false);
  const [newProxy, setNewProxy] = useState({ connection_string: '', platform_username: '', platform_password: '' });

  const fetchProxies = async () => {
    try {
      const response = await databases.listDocuments(DB_ID, PROXIES_COLL_ID, [
        Query.orderDesc('usage_count'),
      ]);
      setProxies(response.documents);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNumbers = async () => {
    try {
      const response = await databases.listDocuments(DB_ID, QUEUE_COLL_ID, [
        Query.orderDesc('created_at'),
        Query.limit(50)
      ]);
      setNumbers(response.documents);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchNumbers();
    fetchProxies();
    const interval = setInterval(() => {
      fetchNumbers();
      fetchProxies();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAdd = async () => {
    if (!inputValue) return;
    try {
      setLoading(true);
      await databases.createDocument(DB_ID, QUEUE_COLL_ID, ID.unique(), {
        phone: inputValue,
        status: 'pending',
        created_at: new Date().toISOString()
      });
      setInputValue('');
      fetchNumbers();
    } catch (e) {
      alert("Error adding number: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProxy = async () => {
    if (!newProxy.connection_string) return;
    try {
      setLoading(true);
      await databases.createDocument(DB_ID, PROXIES_COLL_ID, ID.unique(), {
        ...newProxy,
        status: 'active',
        usage_count: 0
      });
      setNewProxy({ connection_string: '', platform_username: '', platform_password: '' });
      setShowProxyModal(false);
      fetchProxies();
    } catch (e) {
      alert("Error adding proxy: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Proxy Modal */}
      {showProxyModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card w-full max-w-md">
            <h3 className="text-xl font-bold mb-6">Add New Proxy</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs font-bold text-gray-500 uppercase block mb-1">Connection String</label>
                <input
                  type="text"
                  placeholder="host:port:user:pass"
                  className="input-field"
                  value={newProxy.connection_string}
                  onChange={(e) => setNewProxy({ ...newProxy, connection_string: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500 uppercase block mb-1">Platform Username (Ref)</label>
                <input
                  type="text"
                  className="input-field"
                  value={newProxy.platform_username}
                  onChange={(e) => setNewProxy({ ...newProxy, platform_username: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs font-bold text-gray-500 uppercase block mb-1">Platform Password (Ref)</label>
                <input
                  type="password"
                  className="input-field"
                  value={newProxy.platform_password}
                  onChange={(e) => setNewProxy({ ...newProxy, platform_password: e.target.value })}
                />
              </div>
              <div className="flex gap-3 mt-6">
                <button className="glow-btn bg-emerald-500 w-full" onClick={handleAddProxy} disabled={loading}>
                  {loading ? 'Adding...' : 'Save Proxy'}
                </button>
                <button className="p-3 border border-gray-700 rounded-lg w-full hover:bg-gray-800" onClick={() => setShowProxyModal(false)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-gray-800 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Smartphone className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">FB OTP <span className="text-emerald-500">CONTROL</span></h1>
            <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Production Environment</p>
          </div>
        </div>

        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${activeTab === 'dashboard' ? 'bg-emerald-500/10 text-emerald-400' : 'text-gray-400 hover:bg-gray-800'}`}
          >
            <Smartphone size={18} /> Dashboard
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${activeTab === 'settings' ? 'bg-emerald-500/10 text-emerald-400' : 'text-gray-400 hover:bg-gray-800'}`}
          >
            <Settings size={18} /> Proxies
          </button>
        </nav>
      </header>

      {activeTab === 'dashboard' ? (
        <main>
          {/* Quick Actions & Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="glass-card flex flex-col justify-between">
              <label className="text-xs font-bold text-emerald-500 uppercase mb-4">Add New Number</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="+1234567890"
                  className="input-field"
                  onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
                />
                <button
                  onClick={handleAdd}
                  disabled={loading}
                  className="glow-btn px-4"
                >
                  {loading ? <RefreshCw className="animate-spin" size={20} /> : <Plus size={20} />}
                </button>
              </div>
            </div>

            <div className="glass-card flex gap-6 items-center">
              <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                <CheckCircle size={24} />
              </div>
              <div>
                <div className="text-2xl font-bold">{numbers.filter(n => n.status === 'success').length}</div>
                <div className="text-sm text-gray-400">Session Success</div>
              </div>
            </div>

            <div className="glass-card flex gap-6 items-center">
              <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-500">
                <RefreshCw size={24} />
              </div>
              <div>
                <div className="text-2xl font-bold">{numbers.filter(n => n.status === 'pending').length}</div>
                <div className="text-sm text-gray-400">Pending Queue</div>
              </div>
            </div>
          </div>

          {/* Table Container */}
          <div className="glass-card">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <FileText className="text-emerald-500" size={20} /> Results Explorer
              </h2>
              <div className="flex gap-4">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 text-gray-500" size={16} />
                  <input
                    type="text"
                    placeholder="Search phone..."
                    className="input-field pl-10 h-10 py-0 w-64"
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
                <button onClick={fetchNumbers} className="p-2 hover:bg-gray-800 rounded-lg text-gray-400 transition-colors">
                  <RefreshCw size={20} />
                </button>
              </div>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Phone Number</th>
                    <th>Status</th>
                    <th>Result URL</th>
                    <th>Assets</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(searchTerm ? numbers.filter(n => n.phone.includes(searchTerm)) : numbers).map((item) => (
                    <tr key={item.$id}>
                      <td className="font-medium">{item.phone}</td>
                      <td>
                        <span className={`badge badge-${item.status}`}>
                          {item.status.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        {item.result_url ? (
                          <div className="flex items-center gap-2 text-xs bg-gray-900 p-2 rounded border border-gray-800">
                            <span className="truncate max-w-[200px] text-gray-400 font-mono">{item.result_url}</span>
                            <button className="text-emerald-500 hover:text-emerald-400" onClick={() => navigator.clipboard.writeText(item.result_url)}>
                              <Copy size={14} />
                            </button>
                          </div>
                        ) : '-'}
                      </td>
                      <td>
                        <div className="flex gap-2">
                          {item.screenshot_id && (
                            <button
                              className="p-2 bg-emerald-500/10 text-emerald-500 rounded hover:bg-emerald-500/20 transition-all border border-emerald-500/20"
                              title="View Screenshot"
                              onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.screenshot_id}/view?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                            >
                              <Smartphone size={14} />
                            </button>
                          )}
                          {item.cookie_file_id && (
                            <button
                              className="p-2 bg-blue-500/10 text-blue-500 rounded hover:bg-blue-500/20 transition-all border border-blue-500/20"
                              title="Download Cookies"
                              onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.cookie_file_id}/download?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                            >
                              <Download size={14} />
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="text-xs text-gray-400">
                        {new Date(item.created_at).toLocaleString()}
                      </td>
                      <td>
                        <button className="p-2 hover:bg-gray-800 rounded-lg text-gray-500 hover:text-white" onClick={async () => {
                          if (confirm("Delete this entry?")) {
                            await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                            fetchNumbers();
                          }
                        }}>
                          <XCircle size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {numbers.length === 0 && (
                    <tr>
                      <td colSpan="6" className="text-center py-12 text-gray-500 italic">No numbers found in queue. Add one to begin.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      ) : (
        <div className="glass-card">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <Settings className="text-emerald-500" /> Proxy Management pool
            </h2>
            <button className="glow-btn px-4 text-sm" onClick={() => setShowProxyModal(true)}>
              <Plus size={16} className="inline mr-2" /> Add Proxy
            </button>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Connection String</th>
                  <th>Platform Creds</th>
                  <th>Usage</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {proxies.map((proxy) => (
                  <tr key={proxy.$id}>
                    <td className="font-mono text-xs text-emerald-400">
                      <div className="flex items-center gap-2">
                        <span className="truncate max-w-[200px]">{proxy.connection_string}</span>
                        <button className="text-gray-500 hover:text-white" onClick={() => navigator.clipboard.writeText(proxy.connection_string)}>
                          <Copy size={12} />
                        </button>
                      </div>
                    </td>
                    <td>
                      <div className="text-xs text-gray-400">
                        <div><span className="text-gray-600">U:</span> {proxy.platform_username || '-'}</div>
                        <div><span className="text-gray-600">P:</span> {proxy.platform_password ? '••••••••' : '-'}</div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-1">
                        <span className="text-lg font-bold text-white">{proxy.usage_count || 0}</span>
                        <span className="text-xs text-gray-500">runs</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${proxy.status === 'active' ? 'badge-success' : 'badge-failed'}`}>
                        {proxy.status.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button className="p-2 hover:bg-gray-800 rounded text-red-500" onClick={async () => {
                          if (confirm("Delete proxy?")) {
                            await databases.deleteDocument(DB_ID, PROXIES_COLL_ID, proxy.$id);
                            fetchProxies();
                          }
                        }}>
                          <XCircle size={14} />
                        </button>
                        <button className="p-2 hover:bg-gray-800 rounded text-emerald-500" title="Reset Status" onClick={async () => {
                          await databases.updateDocument(DB_ID, PROXIES_COLL_ID, proxy.$id, { status: 'active', usage_count: 0 });
                          fetchProxies();
                        }}>
                          <RefreshCw size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {proxies.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center py-12 text-gray-500 italic">No proxies added to the pool.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
