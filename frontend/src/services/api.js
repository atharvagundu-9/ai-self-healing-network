const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function post(path, body = {}) {
  const response = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(payload.detail || 'Request failed')
  return payload
}

export const websocketUrl = `${API.replace(/^http/, 'ws')}/ws/telemetry`

