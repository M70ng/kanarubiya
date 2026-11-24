"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Copy, Loader2, ClipboardPaste, RotateCcw, Volume2, Square, Download } from "lucide-react"
import { convertText } from "@/utils/kanaApi"

export default function ConvertPage() {
  const [input, setInput] = useState("")
  const [result, setResult] = useState("")
  const [source, setSource] = useState("")
  const [activeLine, setActiveLine] = useState<number | null>(null)
  const [playing, setPlaying] = useState(false)
  const [speechAvailable, setSpeechAvailable] = useState(false)
  const [readingRate, setReadingRate] = useState(0.9)
  const [copyKind, setCopyKind] = useState<"paired" | "kana" | null>(null)
  const speechGeneration = useRef(0)
  const speechUtterance = useRef<SpeechSynthesisUtterance | null>(null)

  useEffect(() => {
    setSpeechAvailable("speechSynthesis" in window && "SpeechSynthesisUtterance" in window)
    return () => {
      speechGeneration.current += 1
      if ("speechSynthesis" in window) window.speechSynthesis.cancel()
    }
  }, [])

  const stopReading = () => {
    speechGeneration.current += 1
    if ("speechSynthesis" in window) window.speechSynthesis.cancel()
    speechUtterance.current = null
    setPlaying(false)
    setActiveLine(null)
  }

  const startReading = () => {
    if (!speechAvailable || !source) return
    const synth = window.speechSynthesis
    const voice = synth.getVoices().find((item) => /^ko(?:[-_]|$)/i.test(item.lang))
    if (!voice) {
      setError("韓国語の読み上げ音声が見つかりません。端末の音声設定をご確認ください。")
      return
    }
    stopReading()
    setError(null)
    setPlaying(true)
    const generation = speechGeneration.current
    const lines = source.split("\n")
    const speakLine = (index: number) => {
      if (generation !== speechGeneration.current) return
      while (index < lines.length && !lines[index].trim()) index += 1
      if (index >= lines.length) {
        speechUtterance.current = null
        setPlaying(false)
        setActiveLine(null)
        return
      }
      const utterance = new SpeechSynthesisUtterance(lines[index])
      utterance.lang = "ko-KR"
      utterance.voice = voice
      utterance.rate = readingRate
      utterance.onstart = () => {
        if (generation === speechGeneration.current) setActiveLine(index)
      }
      utterance.onend = () => speakLine(index + 1)
      utterance.onerror = () => {
        if (generation !== speechGeneration.current) return
        setPlaying(false)
        setActiveLine(null)
        setError("読み上げを開始できませんでした。端末の音声設定をご確認ください。")
      }
      speechUtterance.current = utterance
      synth.speak(utterance)
    }
    speakLine(0)
  }

  const sourceLines = source.split("\n")
  const resultLines = result.split("\n")
  const linesMatch = sourceLines.length === resultLines.length
  const pairedText = linesMatch
    ? sourceLines.map((line, index) => line.trim() ? `${line}\n${resultLines[index]}` : "").join("\n\n")
    : `【韓国語】\n${source}\n\n【かな読み】\n${result}`

  const [isConverting, setIsConverting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pasteSuccess, setPasteSuccess] = useState(false)
  const [convertNumbers, setConvertNumbers] = useState(false)

  const SAMPLE_TEXTS = [
    { label: "歌詞っぽい", text: "그래요 난 널 사랑해 언제나 믿어" },
    { label: "このアプリ", text: "이 앱 진짜 대박이당! 이렇게 좋은 앱을 만들어주셔서 감사하네여ㅠㅠ" },
    { label: "日常会話", text: "뭐 해요? 저는 한국어 공부하고 있어요. 내일도 한국어 공부할거에요!" },
    { label: "このアプリ", text: "여러분! 카나루비야라는 앱 알아요? 이 앱으로 한국어 노래 가사 읽기가 엄청 쉬워졌네요!" },
    { label: "短い会話", text: "어제 소녀시대 콘서트를 갔는데 연출 짱이었어요. 가길 잘했어요ㅎㅎ" },
  ] as const
  const [sampleIndex, setSampleIndex] = useState(0)
  const handleInsertSample = () => {
    setInput(SAMPLE_TEXTS[sampleIndex].text)
    setSampleIndex((i) => (i + 1) % SAMPLE_TEXTS.length)
  }

  const handleConvert = async () => {
    const text = input.trim()
    if (!text) {
      setError("歌詞を入力してください")
      return
    }
    stopReading()
    setError(null)
    setResult("")
    setSource("")
    setIsConverting(true)
    try {
      const res = await convertText(text, true, convertNumbers)
      setSource(text.replace(/\r\n?/g, "\n"))
      setResult(res.kana.replace(/\r\n?/g, "\n"))
    } catch (e) {
      setError(e instanceof Error ? e.message : "変換に失敗しました")
    } finally {
      setIsConverting(false)
    }
  }

  const handleCopy = async (kind: "paired" | "kana") => {
    try {
      await navigator.clipboard.writeText(kind === "paired" ? pairedText : result)
      setCopyKind(kind)
      setTimeout(() => setCopyKind(null), 2000)
    } catch {
      setError("コピーできませんでした。テキストを選択してコピーしてください。")
    }
  }

  const handleDownload = () => {
    const blob = new Blob([pairedText], { type: "text/plain;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.download = "カナルビ.txt"
    link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      setInput((prev) => prev + (prev ? "\n" : "") + text)
      setPasteSuccess(true)
      setTimeout(() => setPasteSuccess(false), 1500)
    } catch {
      setError("クリップボードの読み取りができませんでした")
    }
  }

  return (
    <div className="min-h-screen bg-[#f4f3ef] text-[#20201e]">
      <header className="border-b border-[#cccac2]">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between px-5 py-5 sm:px-10 lg:px-14">
          <Link href="/" className="text-xl font-black tracking-[-0.08em] sm:text-2xl" aria-label="カナルビ変換サイト ホーム">カナルビ変換サイト<span className="ml-1 text-[#d74b29]">.</span></Link>
          <span className="text-sm text-[#77766f]">韓国語のかな変換</span>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-5 pb-12 sm:px-10 lg:px-14">
        <div className="pb-8 pt-10 sm:pb-10 sm:pt-14">
          <h1 className="text-3xl font-bold tracking-[-0.04em] sm:text-4xl">韓国語を、カタカナの読み方に変換</h1>
          <p className="mt-4 text-base leading-7 text-[#625f58]">韓国語の歌詞や文章を入力して、変換ボタンを押すだけ。</p>
          <div className="mt-6 flex flex-wrap items-baseline gap-x-3 gap-y-1 text-sm text-[#6e6b63]">
            <span className="font-bold text-[#44423d]">変換例</span>
            <span lang="ko" className="text-base text-[#34332f]">안녕하세요</span>
            <span aria-hidden="true" className="text-[#a19e95]">→</span>
            <span className="text-base text-[#34332f]">アンニョンハセヨ</span>
          </div>
        </div>

        {error && <div role="alert" className="mb-4 border-l-2 border-[#d74b29] bg-[#fbece7] px-4 py-3 text-sm text-[#9d321b]">{error}</div>}

        <section aria-label="かな変換" className="border border-[#a9a79f] bg-[#fbfaf7]">
          <div className="grid md:grid-cols-2">
            <div className="flex min-w-0 flex-col border-b border-[#cccac2] md:border-b-0 md:border-r">
              <div className="flex min-h-[68px] flex-wrap items-center justify-between gap-2 border-b border-[#dedcd5] px-5 py-3 sm:px-7">
                <div className="flex items-baseline gap-3"><h2 className="font-bold">韓国語</h2></div>
                <div className="flex items-center gap-1">
                  <Button type="button" variant="ghost" size="sm" onClick={handleInsertSample} disabled={isConverting} className="rounded-none px-2 text-sm text-[#67655f] hover:bg-[#efeee9]"><RotateCcw className="mr-1.5 h-4 w-4" />例文を入れる</Button>
                  <Button type="button" variant="ghost" size="sm" onClick={handlePaste} disabled={isConverting} className="rounded-none px-2 text-sm text-[#67655f] hover:bg-[#efeee9]"><ClipboardPaste className="mr-1.5 h-4 w-4" />{pasteSuccess ? "貼り付け済み" : "貼り付け"}</Button>
                </div>
              </div>
              <Textarea aria-label="韓国語を入力" maxLength={10000} placeholder={"韓国語を入力、または貼り付け"} value={input} onChange={(e) => setInput(e.target.value)} disabled={isConverting} className="input-result-text min-h-[240px] flex-1 resize-y rounded-none border-0 bg-transparent p-5 text-[#20201e] shadow-none placeholder:text-[#b0aea6] focus-visible:ring-0 focus-visible:ring-offset-0 sm:min-h-[300px] sm:p-7" />
              <div className="flex flex-wrap items-center justify-between gap-3 px-5 pb-5 sm:px-7 sm:pb-7"><span className="text-sm text-[#8a887f]" aria-live="polite">{input.length} / 10,000 文字</span><Button onClick={handleConvert} disabled={isConverting || !input.trim()} className="h-12 min-w-[150px] rounded-none bg-[#20201e] px-7 text-sm font-bold text-white hover:bg-[#d74b29]">{isConverting ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />変換中</> : "かな読みに変換"}</Button></div>
            </div>
            <div className="flex min-w-0 flex-col bg-[#edede8]">
              <div className="flex min-h-[68px] flex-wrap items-center justify-between gap-2 border-b border-[#d7d6cf] px-5 py-3 sm:px-7">
                <h2 className="font-bold">変換結果</h2>
                {result && <Button variant="ghost" size="sm" onClick={() => handleCopy("kana")} className="rounded-none px-2 text-sm text-[#67655f] hover:bg-[#e3e3dd]"><Copy className="mr-1.5 h-4 w-4" />{copyKind === "kana" ? "コピー済み" : "カタカナをコピー"}</Button>}
              </div>
              {result ? <>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-[#d7d6cf] px-5 py-3 sm:px-7">
                  <button type="button" onClick={playing ? stopReading : startReading} disabled={!speechAvailable} className="inline-flex items-center gap-2 text-sm font-bold text-[#34332f] hover:text-[#d74b29] disabled:opacity-50">{playing ? <><Square className="h-4 w-4" />読み上げを止める</> : <><Volume2 className="h-4 w-4" />韓国語を読み上げる</>}</button>
                  <label className="flex items-center gap-2 text-sm text-[#67655f]">速度 <select aria-label="読み上げ速度" value={readingRate} disabled={playing} onChange={(e) => setReadingRate(Number(e.target.value))} className="rounded-none border border-[#c7c5bc] bg-transparent px-2 py-1 text-[#34332f]"><option value={0.7}>ゆっくり</option><option value={0.9}>ふつう</option><option value={1.1}>速め</option></select></label>
                  {!speechAvailable && <span className="text-sm text-[#716f68]">このブラウザは読み上げに対応していません</span>}
                </div>
                <div className="min-h-[240px] flex-1 px-5 py-3 sm:min-h-[300px] sm:px-7">
                  {!linesMatch && <p role="status" className="my-3 text-sm text-[#8a4a32]">行数が一致しなかったため、原文と読みを分けて表示しています。</p>}
                  {linesMatch ? sourceLines.map((line, index) => line.trim() ? <div key={index} className={`-mx-3 border-l-2 px-3 py-3 transition-colors ${activeLine === index ? "border-[#d74b29] bg-[#e5ded3]" : "border-transparent"}`} aria-current={activeLine === index ? "true" : undefined}><p lang="ko" className="whitespace-pre-wrap break-words text-base leading-7 text-[#77746d]">{line}</p><p className="mt-1 whitespace-pre-wrap break-words text-lg font-medium leading-8 text-[#20201e]">{resultLines[index]}</p></div> : <div key={index} className="h-5" aria-hidden="true" />) : <><p className="mt-3 text-sm font-bold text-[#716f68]">韓国語</p><pre lang="ko" className="mt-2 whitespace-pre-wrap break-words font-sans text-base leading-7 text-[#77746d]">{source}</pre><p className="mt-5 text-sm font-bold text-[#716f68]">かな読み</p><pre className="mt-2 whitespace-pre-wrap break-words font-sans text-lg leading-8">{result}</pre></>}
                </div>
                <div className="flex flex-wrap gap-x-5 gap-y-3 border-t border-[#d7d6cf] px-5 py-4 sm:px-7">
                  <button type="button" onClick={() => handleCopy("paired")} className="inline-flex items-center gap-2 text-sm font-bold text-[#54514b] hover:text-[#d74b29]"><Copy className="h-4 w-4" />{copyKind === "paired" ? "コピー済み" : "原文と読みをコピー"}</button>
                  <button type="button" onClick={handleDownload} className="inline-flex items-center gap-2 text-sm font-bold text-[#54514b] hover:text-[#d74b29]"><Download className="h-4 w-4" />テキスト保存</button>
                </div>
              </> : <div className="min-h-[200px] flex-1 p-5 text-sm leading-7 text-[#9b9990] sm:min-h-[300px] sm:p-7" aria-live="polite">{isConverting ? "変換しています。少々お待ちください。" : "変換結果がここに表示されます。"}</div>}
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-[#cccac2] px-5 py-4 sm:px-7">
            <span className="text-sm font-bold">数字の読み方</span>
            <div role="group" aria-label="数字の変換" className="flex flex-wrap items-center gap-4 text-sm">
              <button type="button" aria-pressed={!convertNumbers} onClick={() => setConvertNumbers(false)} disabled={isConverting} className={`border-b-2 py-1 ${!convertNumbers ? "border-[#d74b29] font-bold text-[#20201e]" : "border-transparent text-[#8a887f]"}`}>そのまま</button>
              <button type="button" aria-pressed={convertNumbers} onClick={() => setConvertNumbers(true)} disabled={isConverting} className={`border-b-2 py-1 ${convertNumbers ? "border-[#d74b29] font-bold text-[#20201e]" : "border-transparent text-[#8a887f]"}`}>韓国語読み</button>
            </div>
          </div>
        </section>

        <div className="border-b border-[#cccac2] py-7">
          <details className="w-full text-sm leading-7 text-[#625f58]">
            <summary className="cursor-pointer font-bold text-[#34332f]">ご利用について</summary>
            <div className="mt-5 max-w-3xl space-y-5">
              <div>
                <h3 className="font-bold text-[#34332f]">変換について</h3>
                <p className="mt-1">ハングル以外の英語・日本語・記号などは、そのまま出力されます。</p>
                <p>読み方の精度には限界があります。目安としてお使いください。</p>
              </div>
              <div>
                <h3 className="font-bold text-[#34332f]">数字の読み方</h3>
                <p className="mt-1">入力欄の下にある設定で、数字をそのまま残すか、韓国語の読み方に変換するかを選べます。</p>
                <p>英字と混ざった数字は、そのまま出力されます。</p>
              </div>
              <div>
                <h3 className="font-bold text-[#34332f]">変換にかかる時間</h3>
                <p className="mt-1">初回はシステムの起動に時間がかかり、結果が出るまで数十秒かかる場合があります。</p>
              </div>
              <p>読み上げには端末の韓国語音声を使います。音声の有無や声は端末によって異なります。</p>
              <p>変換結果は自由にお使いいただけます。</p>
            </div>
          </details>
        </div>
        <footer className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2 py-5 text-sm text-[#85827b]">
          <span>ご意見・お問い合わせ</span>
          <a href="https://zenn.dev/m70ng" target="_blank" rel="noopener noreferrer" className="text-[#625f58] underline-offset-4 hover:underline">Zenn</a>
          <a href="https://x.com/MeowNotFound" target="_blank" rel="noopener noreferrer" className="text-[#625f58] underline-offset-4 hover:underline">X</a>
        </footer>
      </main>
    </div>
  )
}
