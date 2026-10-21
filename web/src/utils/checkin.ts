export interface ParsedCheckinPayload {
  activityId: number
  code: string
}

const CODE_PATTERN = /^[0-9A-Z]{8}$/

function fromParams(params: URLSearchParams): ParsedCheckinPayload | null {
  const rawId = params.get('activity_id') || params.get('activityId') || params.get('id')
  const rawCode = params.get('code') || params.get('checkin_code')
  if (!rawId || !rawCode) return null
  const activityId = Number(rawId)
  const code = rawCode.trim().toUpperCase()
  if (!Number.isInteger(activityId) || activityId <= 0) return null
  if (!CODE_PATTERN.test(code)) return null
  return { activityId, code }
}

export function parseCheckinPayload(raw: string): ParsedCheckinPayload | null {
  const text = (raw || '').trim()
  if (!text) return null

  if (text.startsWith('campushub://')) {
    const queryIndex = text.indexOf('?')
    if (queryIndex === -1) return null
    return fromParams(new URLSearchParams(text.slice(queryIndex + 1)))
  }

  try {
    const url = new URL(text)
    if (url.searchParams.has('code')) return fromParams(url.searchParams)
  } catch {
    // 非链接内容交给下面的纯文本格式处理
  }

  const parts = text.split(/\s+/)
  if (parts.length === 2 && /^\d+$/.test(parts[0]) && CODE_PATTERN.test(parts[1].toUpperCase())) {
    return { activityId: Number(parts[0]), code: parts[1].toUpperCase() }
  }

  if (CODE_PATTERN.test(text.toUpperCase())) {
    return { activityId: 0, code: text.toUpperCase() }
  }

  return null
}
