// utils/kanaApi.ts - 韓国語→かな変換APIクライアント

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''

export interface ConvertTextResponse {
  original: string
  phonetic_hangul: string
  kana: string
  use_g2pk: boolean
  error?: string
}

/**
 * 単一テキストをかな読みに変換（メインAPI）
 */
export async function convertText(text: string, useG2pk: boolean = true): Promise<ConvertTextResponse> {
  const response = await fetch(`${API_BASE_URL}/api/kanafy-ko`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, use_g2pk: useG2pk }),
  })
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  return response.json()
}

/**
 * 変換漏れ報告: ハングルと読みをユーザー辞書に追加
 */
export async function addDictionaryEntry(hangul: string, kana: string): Promise<{ success: boolean; hangul: string; kana: string }> {
  const url = `${API_BASE_URL}/api/kanafy-ko/dictionary`
  let response: Response
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hangul: hangul.trim(), kana: kana.trim() }),
    })
  } catch (e) {
    const msg = e instanceof Error ? e.message : ''
    if (msg.includes('fetch') || msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
      const apiHint = API_BASE_URL ? API_BASE_URL : 'http://localhost:8000（開発時は Next が /api をここに転送）'
      throw new Error(`バックエンドに接続できません。${apiHint} で API が起動しているか確認してください。`)
    }
    throw e
  }
  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    const detail = typeof err?.detail === 'string' ? err.detail : ''
    if (response.status === 404) {
      const apiHint = API_BASE_URL ? API_BASE_URL : 'http://localhost:8000'
      throw new Error(`辞書APIが見つかりません（404）。バックエンドを再起動するか、${apiHint} で起動しているか確認してください。`)
    }
    throw new Error(detail || `HTTP error! status: ${response.status}`)
  }
  return response.json()
}

/**
 * 複数行を一括でかな読みに変換
 */
export async function convertBatch(texts: string[], useG2pk: boolean = true): Promise<ConvertTextResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/kanafy-ko/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texts, use_g2pk: useG2pk }),
  })
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  const data = await response.json()
  return data.results ?? []
}
