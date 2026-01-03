import React, { useState, useEffect } from 'react';
import { Plus, Settings, RefreshCw, FileText, Smartphone, CheckCircle, XCircle, Search, Copy, Download, ExternalLink } from 'lucide-react';
import { databases, QUEUE_COLL_ID, DB_ID, PROXIES_COLL_ID, ASSETS_BUCKET_ID } from './appwrite';
import { ID, Query } from 'appwrite';

const App = () => {
  const [numbers, setNumbers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchPending, setSearchPending] = useState('');
  const [searchSuccess, setSearchSuccess] = useState('');
  const [showProxyModal, setShowProxyModal] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [newProxy, setNewProxy] = useState({ connection_string: '', platform_username: '', platform_password: '' });

  // ... (fetchProxies, fetchNumbers, handleAdd, handleAddProxy definitions remain same, assume they are available in scope or previous lines)

  return (
    <div className="app-container">
      {/* Proxy Modal - kept same */}
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
          {/* Quick Add Bar */}
          <div className="glass-card mb-6 flex items-center justify-between gap-4 p-4">
            <div className="flex-1 flex gap-2 items-center">
              <span className="text-xs font-bold text-emerald-500 uppercase whitespace-nowrap mr-2">New Entry</span>
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Enter phone number (+123...)"
                className="input-field h-10"
                onKeyPress={(e) => e.key === 'Enter' && handleAdd()}
              />
              <button
                onClick={handleAdd}
                disabled={loading}
                className="glow-btn px-6 h-10 flex items-center justify-center"
              >
                {loading ? <RefreshCw className="animate-spin" size={20} /> : <Plus size={20} />}
              </button>
            </div>
            <div className="flex gap-4 border-l border-gray-700 pl-4">
              <div className="text-center px-4">
                <span className="block text-2xl font-bold text-emerald-500">{numbers.filter(n => n.status === 'success').length}</span>
                <span className="text-xxs uppercase tracking-wider text-gray-500">Success</span>
              </div>
              <div className="text-center px-4">
                <span className="block text-2xl font-bold text-blue-500">{numbers.filter(n => n.status === 'pending').length}</span>
                <span className="text-xxs uppercase tracking-wider text-gray-500">Pending</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-250px)]">

            {/* LEFT COLUMN: PENDING QUEUE */}
            <div className="glass-card flex flex-col h-full overflow-hidden">
              <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-800">
                <h2 className="font-bold flex items-center gap-2 text-blue-400 uppercase tracking-wider text-sm">
                  <RefreshCw size={16} /> Pending Queue
                </h2>
                <div className="relative w-48">
                  <Search className="absolute left-3 top-2.5 text-gray-500" size={14} />
                  <input
                    type="text"
                    placeholder="Search pending..."
                    className="input-field pl-9 h-9 text-sm"
                    onChange={(e) => setSearchPending(e.target.value)}
                  />
                </div>
              </div>

              <div className="overflow-y-auto flex-1 pr-2 custom-scrollbar">
                <div className="space-y-2">
                  {numbers
                    .filter(n => n.status === 'pending')
                    .filter(n => n.phone.includes(searchPending))
                    .map(item => (
                      <div key={item.$id} className="p-3 rounded bg-gray-900/50 border border-gray-800 flex justify-between items-center hover:border-blue-500/30 transition-colors">
                        <div>
                          <div className="font-mono text-lg">{item.phone}</div>
                          <div className="text-xs text-gray-500">{new Date(item.created_at).toLocaleTimeString()}</div>
                        </div>
                        <button className="text-gray-600 hover:text-red-500 p-2" onClick={async () => {
                          if (confirm("Delete this entry?")) {
                            await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                            fetchNumbers();
                          }
                        }}>
                          <XCircle size={18} />
                        </button>
                      </div>
                    ))}
                  {numbers.filter(n => n.status === 'pending').length === 0 && (
                    <div className="text-center text-gray-600 py-10 italic">Queue is empty</div>
                  )}
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: SESSION SUCCESS */}
            <div className="glass-card flex flex-col h-full overflow-hidden border-emerald-500/20 shadow-emerald-900/10">
              <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-800">
                <h2 className="font-bold flex items-center gap-2 text-emerald-400 uppercase tracking-wider text-sm">
                  <CheckCircle size={16} /> Session Success
                </h2>
                <div className="relative w-48">
                  <Search className="absolute left-3 top-2.5 text-gray-500" size={14} />
                  <input
                    type="text"
                    placeholder="Search success..."
                    className="input-field pl-9 h-9 text-sm"
                    onChange={(e) => setSearchSuccess(e.target.value)}
                  />
                </div>
              </div>

              <div className="overflow-y-auto flex-1 pr-2 custom-scrollbar">
                <div className="grid grid-cols-1 gap-3">
                  {numbers
                    .filter(n => n.status === 'success')
                    .filter(n => n.phone.includes(searchSuccess))
                    .map(item => (
                      <div key={item.$id} className="p-4 rounded-lg bg-emerald-900/10 border border-emerald-500/20 hover:bg-emerald-900/20 transition-all">
                        <div className="flex justify-between items-start mb-2">
                          <div className="font-mono text-xl text-emerald-100 font-bold">{item.phone}</div>
                          <span className="text-xs text-emerald-400/50 bg-emerald-500/10 px-2 py-1 rounded">{new Date(item.created_at).toLocaleDateString()}</span>
                        </div>

                        {item.result_url && (
                          <div className="flex items-center gap-2 bg-black/40 p-2 rounded mb-3 border border-emerald-500/10">
                            <ExternalLink size={12} className="text-emerald-500" />
                            <div className="truncate text-xs text-gray-400 flex-1 font-mono hover:text-white cursor-text select-all">
                              {item.result_url}
                            </div>
                            <button className="text-emerald-500 hover:text-white" onClick={() => navigator.clipboard.writeText(item.result_url)}>
                              <Copy size={14} />
                            </button>
                          </div>
                        )}

                        <div className="flex gap-2 justify-end">
                          {item.screenshot_id && (
                            <button
                              className="px-3 py-1.5 bg-emerald-500/10 text-emerald-400 text-xs rounded hover:bg-emerald-500 hover:text-white transition-all flex items-center gap-2"
                              onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.screenshot_id}/view?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                            >
                              <Smartphone size={12} /> Screenshot
                            </button>
                          )}
                          {item.cookie_file_id && (
                            <button
                              className="px-3 py-1.5 bg-blue-500/10 text-blue-400 text-xs rounded hover:bg-blue-500 hover:text-white transition-all flex items-center gap-2"
                              onClick={() => window.open(`${import.meta.env.VITE_APPWRITE_ENDPOINT}/storage/buckets/${ASSETS_BUCKET_ID}/files/${item.cookie_file_id}/download?project=${import.meta.env.VITE_APPWRITE_PROJECT_ID}`)}
                            >
                              <Download size={12} /> Cookies
                            </button>
                          )}
                          <button className="px-3 py-1.5 hover:bg-red-500/20 text-gray-500 hover:text-red-400 text-xs rounded transition-all" onClick={async () => {
                            if (confirm("Delete this entry?")) {
                              await databases.deleteDocument(DB_ID, QUEUE_COLL_ID, item.$id);
                              fetchNumbers();
                            }
                          }}>
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
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
