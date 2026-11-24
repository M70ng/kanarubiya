// utils/kanaApi.ts - 韓国語→かな変換APIクライアント

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? ''

export interface ConvertTextResponse {
  original: string
  phonetic_hangul: string
  kana: string
  use_g2pk: boolean
  convert_numbers?: boolean
  error?: string
}

/**
 * 単一テキストをかな読みに変換（メインAPI）
 */
export async function convertText(
  text: string,
  useG2pk: boolean = true,
  convertNumbers: boolean = false
): Promise<ConvertTextResponse> {
  const response = await fetch(`${API_BASE_URL}/api/kanafy-ko`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, use_g2pk: useG2pk, convert_numbers: convertNumbers }),
  })
  if (response.status === 429) throw new Error('アクセスが集中しています。少し待ってからもう一度お試しください。')
  if (response.status === 413 || response.status === 422) throw new Error('入力が長すぎます。10,000文字以内でお試しください。')
  if (!response.ok) throw new Error('変換に失敗しました。時間をおいてもう一度お試しください。')
  return response.json()
}

/**
 * 複数行を一括でかな読みに変換
 */
export async function convertBatch(
  texts: string[],
  useG2pk: boolean = true,
  convertNumbers: boolean = false
): Promise<ConvertTextResponse[]> {
  const response = await fetch(`${API_BASE_URL}/api/kanafy-ko/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texts, use_g2pk: useG2pk, convert_numbers: convertNumbers }),
  })
  if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
  const data = await response.json()
  return data.results ?? []
}
