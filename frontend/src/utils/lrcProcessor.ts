// utils/lrcProcessor.ts

export interface LrcLineDetail {
  line_number: number
  original: string
  processed: string
  type: string
  timestamp: string
  original_lyrics: string
  converted_lyrics: string
  error?: string
}

export interface LrcResponse {
  original_content: string
  processed_content: string
  line_details: LrcLineDetail[]
  use_g2pk: boolean
  total_lines: number
  lyrics_lines: number
  metadata_lines: number
}

export interface LrcUploadResponse {
  success: boolean
  original_filename: string
  processed_content: string
  line_details: LrcLineDetail[]
  total_lines: number
  lyrics_lines: number
  metadata_lines: number
  temp_file_path: string
}

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

/**
 * LRCファイルの内容を変換
 */
export async function convertLrcContent(content: string, useG2pk: boolean = true): Promise<LrcResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/kanafy-ko/lrc`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content,
        use_g2pk: useG2pk
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('LRC変換エラー:', error)
    throw error
  }
}

/**
 * LRCファイルをアップロードして変換
 */
export async function uploadAndConvertLrc(file: File, useG2pk: boolean = true): Promise<LrcUploadResponse> {
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('use_g2pk', useG2pk.toString())

    const response = await fetch(`${API_BASE_URL}/api/kanafy-ko/lrc/upload`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error('LRCファイルアップロードエラー:', error)
    throw error
  }
}

/**
 * 変換されたLRCファイルをダウンロード
 */
export function downloadLrcFile(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * LRCファイルの内容を解析して歌詞とタイムスタンプを抽出
 */
export function parseLrcContent(content: string): Array<{time: number, original: string, converted?: string}> {
  const lines = content.split('\n')
  const lyrics: Array<{time: number, original: string, converted?: string}> = []
  
  for (const line of lines) {
    const trimmedLine = line.trim()
    if (!trimmedLine) continue
    
    // タイムスタンプのパターン: [mm:ss.xx] または [mm:ss:xx]
    const timestampMatch = trimmedLine.match(/\[(\d{2}):(\d{2})[.:](\d{2})\]/)
    if (timestampMatch) {
      const [, minutes, seconds, centiseconds] = timestampMatch
      const time = parseInt(minutes) * 60 + parseInt(seconds) + parseInt(centiseconds) / 100
      const lyricsText = trimmedLine.substring(timestampMatch[0].length).trim()
      
      if (lyricsText) {
        lyrics.push({
          time,
          original: lyricsText
        })
      }
    }
  }
  
  return lyrics.sort((a, b) => a.time - b.time)
}

/**
 * 変換されたLRCファイルの内容を解析
 */
export function parseConvertedLrcContent(content: string): Array<{time: number, original: string, converted: string}> {
  const lines = content.split('\n')
  const lyrics: Array<{time: number, original: string, converted: string}> = []
  
  for (const line of lines) {
    const trimmedLine = line.trim()
    if (!trimmedLine) continue
    
    // タイムスタンプのパターン: [mm:ss.xx] または [mm:ss:xx]
    const timestampMatch = trimmedLine.match(/\[(\d{2}):(\d{2})[.:](\d{2})\]/)
    if (timestampMatch) {
      const [, minutes, seconds, centiseconds] = timestampMatch
      const time = parseInt(minutes) * 60 + parseInt(seconds) + parseInt(centiseconds) / 100
      const lyricsText = trimmedLine.substring(timestampMatch[0].length).trim()
      
      if (lyricsText) {
        // 元の歌詞と変換後の歌詞を分離（仮想的な実装）
        // 実際には、変換前後の対応関係を保持する必要があります
        lyrics.push({
          time,
          original: lyricsText, // 実際には元の歌詞を保持する必要があります
          converted: lyricsText
        })
      }
    }
  }
  
  return lyrics.sort((a, b) => a.time - b.time)
} 