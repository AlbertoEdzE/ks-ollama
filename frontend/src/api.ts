export const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8080'

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

async function fetchWithRetry(input: string, init: RequestInit, attempts = 3, backoffMs = 300): Promise<Response> {
  let lastError: unknown
  for (let i = 0; i < attempts; i += 1) {
    try {
      const res = await fetch(input, init)
      return res
    } catch (err: any) {
      lastError = err
      if (!(err instanceof TypeError) || i === attempts - 1) {
        console.error('API request failed', { url: input, error: String(err) })
        throw err
      }
      console.warn('Network error, retrying API request', { url: input, attempt: i + 1 })
      await delay(backoffMs * (i + 1))
    }
  }
  if (lastError instanceof TypeError) {
    throw new Error(`Network error contacting API at ${input}`)
  }
  throw lastError instanceof Error ? lastError : new Error('Unknown network error')
}

export async function healthz(): Promise<boolean> {
  try {
    const r = await fetchWithRetry(`${API_BASE}/healthz`, { method: 'GET' }, 2, 200)
    return r.ok
  } catch {
    return false
  }
}

export async function login(username: string, password: string): Promise<string> {
  try {
    const traceId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
    console.info('auth.login.request', { traceId, username, url: `${API_BASE}/auth/login` })
    const r = await fetchWithRetry(
      `${API_BASE}/auth/login`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Trace-Id': traceId },
        body: JSON.stringify({ username, password })
      },
      3,
      300
    )
    console.info('auth.login.response', { traceId, status: r.status })
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
  const r = await fetchWithRetry(
    `${API_BASE}/users`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ email })
    },
    2,
    200
  )
  if (!r.ok) throw new Error(`Create failed: ${r.status}`)
  return r.json()
}

export async function logout(token: string | null): Promise<void> {
  const headers: Record<string, string> = {}
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  await fetchWithRetry(
    `${API_BASE}/auth/logout`,
    {
      method: 'POST',
      headers
    },
    2,
    200
  )
}

export async function listUsers(token: string, limit = 50, offset = 0): Promise<any[]> {
  const r = await fetchWithRetry(
    `${API_BASE}/users?limit=${limit}&offset=${offset}`,
    { headers: { Authorization: `Bearer ${token}` } },
    2,
    200
  )
  if (!r.ok) throw new Error(`List users failed: ${r.status}`)
  return r.json()
}

export async function setUserPassword(token: string, userId: number, password: string): Promise<void> {
  const r = await fetchWithRetry(
    `${API_BASE}/users/${userId}/password`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ password })
    },
    2,
    200
  )
  if (!r.ok) throw new Error(`Set password failed: ${r.status}`)
}
export async function updateUser(token: string, userId: number, patch: { is_active?: boolean; roles?: string[]; display_name?: string }): Promise<any> {
  const r = await fetchWithRetry(
    `${API_BASE}/users/${userId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(patch)
    },
    2,
    200
  )
  if (!r.ok) throw new Error(`Update user failed: ${r.status}`)
  return r.json()
}

export async function ollamaChat(token: string, model: string, prompt: string): Promise<string> {
  const r = await fetchWithRetry(
    `${API_BASE}/ollama/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ model, prompt })
    },
    2,
    300
  )
  if (!r.ok) {
    let extra = ''
    try {
      const errBody = await r.json()
      if (errBody && errBody.detail) {
        extra = ` ${String(errBody.detail)}`
      }
    } catch {
      // ignore body parse errors
    }
    throw new Error(`Chat failed: ${r.status}${extra}`)
  }
  const data = await r.json()
  return data.response as string
}

export async function ollamaEmbeddings(token: string, model: string, input: string): Promise<number[]> {
  const r = await fetchWithRetry(
    `${API_BASE}/ollama/embeddings`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ model, input })
    },
    2,
    300
  )
  if (!r.ok) {
    let extra = ''
    try {
      const errBody = await r.json()
      if (errBody && errBody.detail) {
        extra = ` ${String(errBody.detail)}`
      }
    } catch {
      // ignore body parse errors
    }
    throw new Error(`Embeddings failed: ${r.status}${extra}`)
  }
  const data = await r.json()
  return data.embedding as number[]
}
export async function listCredentials(token: string, userId?: number): Promise<any[]> {
  const url = userId ? `${API_BASE}/credentials?user_id=${userId}` : `${API_BASE}/credentials`
  const r = await fetchWithRetry(url, { headers: { Authorization: `Bearer ${token}` } }, 2, 200)
  if (!r.ok) throw new Error(`List credentials failed: ${r.status}`)
  return r.json()
}
export async function createCredential(token: string, userId: number, label?: string): Promise<{ credential_id: number; plaintext: string | null }> {
  const r = await fetchWithRetry(
    `${API_BASE}/credentials`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ user_id: userId, label })
    },
    2,
    200
  )
  if (!r.ok) throw new Error(`Create credential failed: ${r.status}`)
  const data = await r.json()
  return { credential_id: data.credential_id, plaintext: data.plaintext ?? null }
}
export async function revokeCredential(token: string, credentialId: number): Promise<void> {
  const r = await fetchWithRetry(
    `${API_BASE}/credentials/${credentialId}/revoke`,
    {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    },
    2,
    200
  )
  if (!r.ok) throw new Error(`Revoke credential failed: ${r.status}`)
}
export async function listAudit(token: string, limit = 100): Promise<any[]> {
  const r = await fetchWithRetry(
    `${API_BASE}/audit?limit=${limit}`,
    { headers: { Authorization: `Bearer ${token}` } },
    2,
    200
  )
  if (!r.ok) throw new Error(`List audit failed: ${r.status}`)
  return r.json()
}
