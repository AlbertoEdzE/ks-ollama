export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080'

export async function healthz(): Promise<boolean> {
  const r = await fetch(`${API_BASE}/healthz`)
  return r.ok
}

export async function login(username: string, password: string): Promise<string> {
  try {
    const r = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    if (!r.ok) {
      if (r.status === 401) {
        throw new Error('Invalid credentials')
      }
      throw new Error(`Login failed: ${r.status}`)
    }
    const data = await r.json()
    return data.access_token
  } catch (err: any) {
    if (err instanceof TypeError) {
      throw new Error('Network error contacting API')
    }
    throw err
  }
}

export async function createUser(token: string, email: string): Promise<any> {
  const r = await fetch(`${API_BASE}/users`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ email })
  })
  if (!r.ok) throw new Error(`Create failed: ${r.status}`)
  return r.json()
}

export async function logout(token: string | null): Promise<void> {
  const headers: Record<string, string> = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  await fetch(`${API_BASE}/auth/logout`, {
    method: 'POST',
    headers
  })
}

export async function listUsers(token: string, limit = 50, offset = 0): Promise<any[]> {
  const r = await fetch(`${API_BASE}/users?limit=${limit}&offset=${offset}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!r.ok) throw new Error(`List users failed: ${r.status}`)
  return r.json()
}

export async function setUserPassword(token: string, userId: number, password: string): Promise<void> {
  const r = await fetch(`${API_BASE}/users/${userId}/password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ password })
  })
  if (!r.ok) throw new Error(`Set password failed: ${r.status}`)
}
export async function updateUser(token: string, userId: number, patch: { is_active?: boolean; roles?: string[]; display_name?: string }): Promise<any> {
  const r = await fetch(`${API_BASE}/users/${userId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(patch)
  })
  if (!r.ok) throw new Error(`Update user failed: ${r.status}`)
  return r.json()
}

export async function ollamaChat(token: string, model: string, prompt: string): Promise<string> {
  const r = await fetch(`${API_BASE}/ollama/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ model, prompt })
  })
  if (!r.ok) throw new Error(`Chat failed: ${r.status}`)
  const data = await r.json()
  return data.response as string
}

export async function ollamaEmbeddings(token: string, model: string, input: string): Promise<number[]> {
  const r = await fetch(`${API_BASE}/ollama/embeddings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ model, input })
  })
  if (!r.ok) throw new Error(`Embeddings failed: ${r.status}`)
  const data = await r.json()
  return data.embedding as number[]
}
export async function listCredentials(token: string, userId?: number): Promise<any[]> {
  const url = userId ? `${API_BASE}/credentials?user_id=${userId}` : `${API_BASE}/credentials`
  const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } })
  if (!r.ok) throw new Error(`List credentials failed: ${r.status}`)
  return r.json()
}
export async function createCredential(token: string, userId: number, label?: string): Promise<{ credential_id: number; plaintext: string | null }> {
  const r = await fetch(`${API_BASE}/credentials`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ user_id: userId, label })
  })
  if (!r.ok) throw new Error(`Create credential failed: ${r.status}`)
  const data = await r.json()
  return { credential_id: data.credential_id, plaintext: data.plaintext ?? null }
}
export async function revokeCredential(token: string, credentialId: number): Promise<void> {
  const r = await fetch(`${API_BASE}/credentials/${credentialId}/revoke`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` }
  })
  if (!r.ok) throw new Error(`Revoke credential failed: ${r.status}`)
}
export async function listAudit(token: string, limit = 100): Promise<any[]> {
  const r = await fetch(`${API_BASE}/audit?limit=${limit}`, { headers: { Authorization: `Bearer ${token}` } })
  if (!r.ok) throw new Error(`List audit failed: ${r.status}`)
  return r.json()
}
