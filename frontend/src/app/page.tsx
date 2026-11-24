"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Copy, Loader2, ClipboardPaste, RotateCcw } from "lucide-react"
import { convertText } from "@/utils/kanaApi"

export default function ConvertPage() {
  const [input, setInput] = useState("")
  const [result, setResult] = useState("")
  const [isConverting, setIsConverting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
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
    setError(null)
    setResult("")
    setIsConverting(true)
    try {
      const res = await convertText(text, true, convertNumbers)
      setResult(res.kana)
    } catch (e) {
      setError(e instanceof Error ? e.message : "変換に失敗しました")
    } finally {
      setIsConverting(false)
    }
  }

  const handleCopy = async () => {
    if (!result) return
    await navigator.clipboard.writeText(result)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
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
                <div className="flex items-baseline gap-3"><h2 className="font-bold">かな読み</h2></div>
                {result && <div className="flex items-center gap-1">
                  <Button variant="ghost" size="sm" onClick={handleCopy} className="rounded-none px-2 text-sm text-[#67655f] hover:bg-[#e3e3dd]"><Copy className="mr-1.5 h-4 w-4" />{copied ? "コピー済み" : "コピー"}</Button>
                </div>}
              </div>
              {result ? <pre className="input-result-text min-h-[240px] flex-1 whitespace-pre-wrap break-words p-5 font-sans text-[#20201e] sm:min-h-[300px] sm:p-7">{result}</pre> : <div className="min-h-[200px] flex-1 p-5 text-sm leading-7 text-[#9b9990] sm:min-h-[300px] sm:p-7" aria-live="polite">{isConverting ? "変換しています。少々お待ちください。" : "変換結果がここに表示されます。"}</div>}
              <div className="px-5 pb-5 text-xs text-[#8a887f] sm:px-7 sm:pb-7"></div>
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
