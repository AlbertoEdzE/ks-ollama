import React, { useEffect, useState } from 'react'
import { healthz, login, createUser, logout, listUsers, setUserPassword, ollamaChat, updateUser, listCredentials, createCredential, revokeCredential, listAudit, ollamaEmbeddings } from './api'

export default function App() {
  const [healthy, setHealthy] = useState<boolean>(false)
  const [username, setUsername] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [token, setToken] = useState<string | null>(null)
  const [loginError, setLoginError] = useState<string>('')
  const [email, setEmail] = useState<string>('')
  const [message, setMessage] = useState<string>('')
  const [users, setUsers] = useState<any[]>([])
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null)
  const [newPassword, setNewPassword] = useState<string>('')
  const [model, setModel] = useState<string>('llama3.2:latest')
  const [prompt, setPrompt] = useState<string>('')
  const [chatResponse, setChatResponse] = useState<string>('')
  const [isActive, setIsActive] = useState<boolean>(true)
  const [rolesText, setRolesText] = useState<string>('user')
  const [creds, setCreds] = useState<any[]>([])
  const [newCredLabel, setNewCredLabel] = useState<string>('api-key')
  const [newCredSecret, setNewCredSecret] = useState<string | null>(null)
  const [audit, setAudit] = useState<any[]>([])
  const [auditLimit, setAuditLimit] = useState<number>(50)
  const [auditFilter, setAuditFilter] = useState<string>('')
  const [embModel, setEmbModel] = useState<string>('nomic-embed-text')
  const [embInput, setEmbInput] = useState<string>('hello world')
  const [embSize, setEmbSize] = useState<number>(0)
  useEffect(() => { healthz().then(setHealthy).catch(() => setHealthy(false)) }, [])
  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!username.trim() || !password.trim()) {
      setLoginError('Username and password are required')
      return
    }
    try {
      console.info('ui.login.submit', { username })
      const accessToken = await login(username, password)
      setToken(accessToken)
      setLoginError('')
      setMessage('')
    } catch (error: any) {
      setToken(null)
      setLoginError(error.message || 'Login failed')
      console.error('ui.login.error', { username, error: String(error && error.message ? error.message : error) })
    }
  }
  const handleCreateUser = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!token) {
      setMessage('You must be logged in to create users')
      return
    }
    if (!email.trim()) {
      setMessage('Email is required')
      return
    }
    try {
      const user = await createUser(token, email)
      setMessage(`Created ${user.email}`)
      setEmail('')
    } catch (error: any) {
      setMessage(error.message || 'Create failed')
    }
  }
  const handleLogout = async () => {
    await logout(token)
    setToken(null)
    setEmail('')
    setMessage('')
  }
  const refreshUsers = async () => {
    if (!token) return
    try {
      const items = await listUsers(token)
      setUsers(items)
      if (selectedUserId) {
        const sel = items.find((u: any) => u.id === selectedUserId)
        if (sel) {
          setIsActive(sel.is_active)
          setRolesText((sel.roles || []).join(','))
        }
      }
    } catch (e: any) {
      setMessage(e.message || 'Failed to load users')
    }
  }
  useEffect(() => { if (token) { refreshUsers() } }, [token])
  useEffect(() => {
    const load = async () => {
      if (!token || !selectedUserId) { setCreds([]); return }
      try {
        const c = await listCredentials(token, selectedUserId)
        setCreds(c)
      } catch (e: any) {
        setMessage(e.message || 'Failed to load credentials')
      }
    }
    load()
  }, [token, selectedUserId])
  const handleUpdateUser = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedUserId) return
    try {
      const roles = rolesText.split(',').map(s => s.trim()).filter(Boolean)
      await updateUser(token, selectedUserId, { is_active: isActive, roles })
      setMessage('User updated')
      refreshUsers()
    } catch (e: any) {
      setMessage(e.message || 'Failed to update user')
    }
  }
  const handleCreateCredential = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedUserId) return
    try {
      const res = await createCredential(token, selectedUserId, newCredLabel)
      setNewCredSecret(res.plaintext)
      const c = await listCredentials(token, selectedUserId)
      setCreds(c)
    } catch (e: any) {
      setMessage(e.message || 'Failed to create credential')
    }
  }
  const handleRevoke = async (id: number) => {
    if (!token) return
    try {
      await revokeCredential(token, id)
      if (selectedUserId) {
        const c = await listCredentials(token, selectedUserId)
        setCreds(c)
      }
    } catch (e: any) {
      setMessage(e.message || 'Failed to revoke credential')
    }
  }
  const handleLoadAudit = async () => {
    if (!token) return
    try {
      const rows = await listAudit(token, auditLimit)
      const filtered = auditFilter ? rows.filter((r: any) => String(r.event_type).includes(auditFilter)) : rows
      setAudit(filtered)
    } catch (e: any) {
      setMessage(e.message || 'Failed to load audit')
    }
  }
  const handleEmbeddings = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token) return
    try {
      const v = await ollamaEmbeddings(token, embModel, embInput)
      setEmbSize(v.length)
    } catch (e: any) {
      setEmbSize(0)
      setMessage(e.message || 'Failed embeddings')
    }
  }
  const handleSetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !selectedUserId || !newPassword.trim()) return
    try {
      await setUserPassword(token, selectedUserId, newPassword)
      setNewPassword('')
      setMessage('Password updated')
    } catch (e: any) {
      setMessage(e.message || 'Failed to set password')
    }
  }
  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !prompt.trim()) {
      setChatResponse('')
      return
    }
    try {
      const res = await ollamaChat(token, model, prompt)
      setChatResponse(res)
    } catch (e: any) {
      setChatResponse(`Error: ${e.message}`)
    }
  }
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b bg-white">
        <div className="mx-auto max-w-5xl p-4">
          <h1 className="text-2xl font-semibold">User Management</h1>
          <p className="text-sm text-gray-600">Backend status: {healthy ? 'OK' : 'Unavailable'}</p>
        </div>
      </header>
      <main className="mx-auto max-w-5xl p-4 grid gap-6 md:grid-cols-2">
        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-medium mb-2">Sign in</h2>
          <form onSubmit={handleLogin} className="space-y-3">
            <div className="flex flex-col">
              <label className="text-sm mb-1" htmlFor="login-username">Username</label>
              <input
                id="login-username"
                className="border rounded px-3 py-2"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
              />
            </div>
            <div className="flex flex-col">
              <label className="text-sm mb-1" htmlFor="login-password">Password</label>
              <input
                id="login-password"
                className="border rounded px-3 py-2"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
              />
            </div>
            <button type="submit" className="inline-flex items-center px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">
              Sign in
            </button>
          </form>
          {loginError && <div role="alert" className="mt-3 rounded border border-red-200 bg-red-50 text-red-700 px-3 py-2">{loginError}</div>}
          {token && (
            <div className="mt-3 flex items-center justify-between">
              <p className="text-sm">Signed in</p>
              <button type="button" className="px-3 py-2 rounded bg-gray-200 hover:bg-gray-300" onClick={handleLogout}>
                Sign out
              </button>
            </div>
          )}
        </section>
        <section className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-medium mb-2">Create user</h2>
          <form onSubmit={handleCreateUser} className="space-y-3">
            <div className="flex flex-col">
              <label className="text-sm mb-1">Email</label>
              <input
                className="border rounded px-3 py-2"
                placeholder="email@example.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>
            <button type="submit" disabled={!token} className="inline-flex items-center px-4 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50">
              Create
            </button>
          </form>
          <div className="text-sm text-gray-700 mt-3">{message}</div>
        </section>
        {token && (
          <section className="bg-white rounded-lg shadow p-4 md:col-span-2">
            <h2 className="text-lg font-medium mb-2">Admin panel</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium">Users & roles</h3>
                  <button onClick={refreshUsers} className="text-sm px-3 py-1 rounded bg-gray-100 hover:bg-gray-200">Refresh</button>
                </div>
                <ul className="divide-y border rounded">
                  {users.map(u => (
                    <li key={u.id} className="p-2 flex items-center justify-between">
                      <div>
                        <div className="font-medium">{u.email}</div>
                        <div className="text-xs text-gray-600">id {u.id}</div>
                      </div>
                      <button className={`text-sm px-2 py-1 rounded ${selectedUserId===u.id ? 'bg-blue-600 text-white' : 'bg-gray-100 hover:bg-gray-200'}`} onClick={() => setSelectedUserId(u.id)}>
                        {selectedUserId===u.id ? 'Selected' : 'Select'}
                      </button>
                    </li>
                  ))}
                  {users.length === 0 && <li className="p-2 text-sm text-gray-600">No users yet</li>}
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-2">Set user password</h3>
                <form onSubmit={handleSetPassword} className="space-y-3">
                  <div className="flex flex-col">
                    <label className="text-sm mb-1">Selected user id</label>
                    <input className="border rounded px-3 py-2" value={selectedUserId ?? ''} disabled />
                  </div>
                  <div className="flex flex-col">
                    <label className="text-sm mb-1">New password</label>
                    <input className="border rounded px-3 py-2" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} />
                  </div>
                  <button disabled={!selectedUserId || !newPassword} className="inline-flex items-center px-4 py-2 rounded bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50">Update password</button>
                </form>
                <hr className="my-4" />
                <h3 className="font-medium mb-2">User settings</h3>
                <form onSubmit={handleUpdateUser} className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" checked={isActive} onChange={e => setIsActive(e.target.checked)} />
                    <span>Active</span>
                  </label>
                  <div className="flex flex-col">
                    <label className="text-sm mb-1">Roles (comma-separated)</label>
                    <input className="border rounded px-3 py-2" value={rolesText} onChange={e => setRolesText(e.target.value)} />
                  </div>
                  <button disabled={!selectedUserId} className="inline-flex items-center px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50">Save settings</button>
                </form>
                <hr className="my-4" />
                <h3 className="font-medium mb-2">Credentials</h3>
                <form onSubmit={handleCreateCredential} className="flex items-end gap-2">
                  <div className="flex-1">
                    <label className="text-sm mb-1 block">Label</label>
                    <input className="border rounded px-3 py-2 w-full" value={newCredLabel} onChange={e => setNewCredLabel(e.target.value)} />
                  </div>
                  <button disabled={!selectedUserId} className="px-3 py-2 rounded bg-emerald-600 text-white hover:bg-emerald-700">Issue</button>
                </form>
                {newCredSecret && <div className="mt-2 text-sm"><span className="font-medium">One-time secret:</span> <code className="bg-gray-100 px-2 py-1 rounded">{newCredSecret}</code></div>}
                <ul className="mt-3 divide-y border rounded">
                  {creds.map(c => (
                    <li key={c.id} className="p-2 flex items-center justify-between">
                      <div className="text-sm">
                        <div>{c.label || 'credential'} · id {c.id}</div>
                        <div className="text-xs text-gray-600">{c.revoked ? 'revoked' : 'active'}</div>
                      </div>
                      {!c.revoked && <button onClick={() => handleRevoke(c.id)} className="text-sm px-2 py-1 rounded bg-red-600 text-white hover:bg-red-700">Revoke</button>}
                    </li>
                  ))}
                  {creds.length === 0 && <li className="p-2 text-sm text-gray-600">No credentials</li>}
                </ul>
              </div>
            </div>
          </section>
        )}
        {token && (
          <section className="bg-white rounded-lg shadow p-4 md:col-span-2">
            <h2 className="text-lg font-medium mb-2">Ollama chat</h2>
            <form onSubmit={handleChat} className="space-y-3">
              <div className="flex flex-col md:flex-row gap-2">
                <div className="flex-1">
                  <label className="text-sm mb-1">Model</label>
                  <input className="border rounded px-3 py-2 w-full" value={model} onChange={e => setModel(e.target.value)} />
                </div>
              </div>
              <div className="flex flex-col">
                <label className="text-sm mb-1">Prompt</label>
                <textarea className="border rounded px-3 py-2 min-h-[100px]" value={prompt} onChange={e => setPrompt(e.target.value)} />
              </div>
              <button className="inline-flex items-center px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700">Send</button>
            </form>
            {chatResponse && <pre className="mt-3 whitespace-pre-wrap rounded border bg-gray-50 p-3">{chatResponse}</pre>}
          </section>
        )}
        {token && (
          <section className="bg-white rounded-lg shadow p-4 md:col-span-2">
            <h2 className="text-lg font-medium mb-2">Embeddings</h2>
            <form onSubmit={handleEmbeddings} className="space-y-3">
              <div className="flex flex-col md:flex-row gap-2">
                <div className="flex-1">
                  <label className="text-sm mb-1">Model</label>
                  <input className="border rounded px-3 py-2 w-full" value={embModel} onChange={e => setEmbModel(e.target.value)} />
                </div>
              </div>
              <div className="flex flex-col">
                <label className="text-sm mb-1">Text</label>
                <textarea className="border rounded px-3 py-2 min-h-[100px]" value={embInput} onChange={e => setEmbInput(e.target.value)} />
              </div>
              <button className="inline-flex items-center px-4 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700">Generate</button>
            </form>
            <div className="text-sm mt-2">Vector length: {embSize}</div>
          </section>
        )}
        {token && (
          <section className="bg-white rounded-lg shadow p-4 md:col-span-2">
            <h2 className="text-lg font-medium mb-2">Audit log</h2>
            <div className="flex items-end gap-2">
              <div>
                <label className="text-sm mb-1 block">Limit</label>
                <input className="border rounded px-3 py-2 w-24" type="number" min={1} max={500} value={auditLimit} onChange={e => setAuditLimit(parseInt(e.target.value || '0', 10))} />
              </div>
              <div className="flex-1">
                <label className="text-sm mb-1 block">Filter by event type</label>
                <input className="border rounded px-3 py-2 w-full" value={auditFilter} onChange={e => setAuditFilter(e.target.value)} />
              </div>
              <button onClick={handleLoadAudit} className="px-3 py-2 rounded bg-gray-900 text-white">Load</button>
            </div>
            <div className="mt-3 overflow-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left">
                    <th className="p-2">Time</th>
                    <th className="p-2">Event</th>
                    <th className="p-2">User</th>
                    <th className="p-2">IP</th>
                    <th className="p-2">Agent</th>
                  </tr>
                </thead>
                <tbody>
                  {audit.map((row: any, idx: number) => (
                    <tr key={idx} className="border-t">
                      <td className="p-2">{row.occurred_at}</td>
                      <td className="p-2">{row.event_type}</td>
                      <td className="p-2">{row.user_id ?? '-'}</td>
                      <td className="p-2">{row.ip ?? '-'}</td>
                      <td className="p-2">{row.user_agent ?? '-'}</td>
                    </tr>
                  ))}
                  {audit.length === 0 && (
                    <tr><td className="p-2 text-gray-600" colSpan={5}>No records</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
