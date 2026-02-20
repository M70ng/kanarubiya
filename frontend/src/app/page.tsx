"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Copy, Loader2, BookPlus, Music2, FileText, Users, ArrowRightLeft, ChevronRight, ClipboardPaste, Sparkles } from "lucide-react"
import { convertText, addDictionaryEntry } from "@/utils/kanaApi"

export default function ConvertPage() {
  const [input, setInput] = useState("")
  const [result, setResult] = useState("")
  const [isConverting, setIsConverting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [dictDialogOpen, setDictDialogOpen] = useState(false)
  const [dictHangul, setDictHangul] = useState("")
  const [dictKana, setDictKana] = useState("")
  const [dictSubmitting, setDictSubmitting] = useState(false)
  const [dictSuccess, setDictSuccess] = useState<string | null>(null)
  const [pasteSuccess, setPasteSuccess] = useState(false)
  const [convertNumbers, setConvertNumbers] = useState(false)
  const lastSelectionRef = useRef("")

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

  const saveSelection = () => {
    lastSelectionRef.current = window.getSelection()?.toString().trim() ?? ""
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

  const openDictDialog = () => {
    setDictHangul(lastSelectionRef.current || "")
    setDictKana("")
    setDictSuccess(null)
    setDictDialogOpen(true)
  }

  const handleAddDictionary = async () => {
    if (!dictHangul.trim() || !dictKana.trim()) {
      setError("ハングルと読み（かな）を両方入力してください")
      return
    }
    setDictSubmitting(true)
    setError(null)
    setDictSuccess(null)
    try {
      await addDictionaryEntry(dictHangul, dictKana)
      setDictSuccess(`「${dictHangul}」→「${dictKana}」を辞書に追加しました。`)
      setDictHangul("")
      setDictKana("")
    } catch (e) {
      setError(e instanceof Error ? e.message : "辞書の追加に失敗しました")
    } finally {
      setDictSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-sky-flow flex flex-col">
      <svg width="0" height="0" className="absolute" aria-hidden>
        <defs>
          <linearGradient id="iconGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#475569" />
            <stop offset="0%" stopColor="#94a3b8">
              <animate attributeName="offset" values="0;0.5;1;0.5;0" dur="3s" repeatCount="indefinite" />
            </stop>
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>
        </defs>
      </svg>
      <header className="shrink-0 px-6 py-8 flex flex-col items-center justify-center text-center">
        <h1 className="sr-only">カナルビ屋 - 韓国語・ハングルをかな読みに変換</h1>
        <div className="flex flex-row items-center justify-center gap-3 sm:gap-4 mb-5">
          <img src="/icon.svg" alt="" className="h-12 w-12 sm:h-14 sm:w-14 md:h-[4.5rem] md:w-[4.5rem] rounded-xl shrink-0" />
          <img
            src="/title-logo.svg"
            alt=""
            className="w-48 sm:w-60 md:w-64 h-auto min-h-[2rem] object-contain object-center animate-fade-in-up animate-delay-100 opacity-0"
          />
        </div>
        <p className="text-lg text-slate-600/90 mt-2 animate-fade-in-up animate-delay-200 opacity-0">
          ハングル・韓国語をコピペするだけで、すぐにかな読みに変換されます！
        </p>
      </header>

      {error && (
        <div className="shrink-0 mx-6 mb-4 rounded-xl bg-red-50/90 text-red-700 px-4 py-3 text-base border border-red-100">
          {error}
        </div>
      )}

      <main className="flex-1 min-h-0 overflow-y-auto px-6 pb-10 max-w-3xl mx-auto w-full flex flex-col">
        {/* 変換例（変換前 → かな変換後） */}
        <div className="shrink-0 mb-4 rounded-xl bg-white border border-slate-200/70 overflow-hidden [border-width:0.5px]">
          <div className="flex flex-col sm:flex-row items-stretch gap-0">
            <div className="flex-1 px-4 py-3 bg-slate-50/50 sm:bg-transparent">
              <p className="text-xs text-slate-500 mb-1.5 font-bold">変換前</p>
              <p className="text-base text-slate-800 leading-relaxed whitespace-pre-wrap">그래요 난 널 사랑해 언제나 믿어</p>
            </div>
            <div className="flex items-center justify-center py-2 sm:py-0 sm:px-2 bg-slate-100/60 shrink-0 border-x border-slate-200/70">
              <span className="text-2xl text-slate-500 animate-pulse hidden sm:inline" aria-hidden>→</span>
              <span className="text-2xl text-slate-500 animate-pulse sm:hidden" aria-hidden>↓</span>
            </div>
            <div className="flex-1 px-4 py-3 bg-slate-50/30 sm:bg-transparent">
              <p className="text-xs text-slate-500 mb-1.5 font-bold">かな変換後</p>
              <p className="text-base text-slate-800 leading-relaxed whitespace-pre-wrap">グレヨ ナン ノル サランヘ オンジェナ ミド</p>
            </div>
          </div>
        </div>

        <div className="shrink-0 rounded-[1.25rem] bg-convert-frame p-3 border border-slate-200/50 animate-fade-in-up animate-delay-200 opacity-0 [border-width:0.5px]">
          {/* 入力エリア */}
          <div className="relative rounded-xl bg-white border border-slate-200/70 overflow-hidden [border-width:0.5px]">
            <div className="flex items-center justify-between gap-2 px-4 py-2 border-b border-slate-100 bg-slate-50/80">
              <span className="text-sm text-slate-500">入力</span>
              <div className="flex items-center gap-1 sm:gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleInsertSample}
                  disabled={isConverting}
                  className="h-8 px-3 text-slate-600 text-sm font-semibold font-rounded"
                >
                  <Sparkles className="h-4 w-4 mr-1 text-violet-500" />
                  例文で試す
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handlePaste}
                  disabled={isConverting}
                  className="h-8 px-3 text-slate-600 text-sm font-bold font-rounded"
                >
                  <ClipboardPaste className="h-5 w-5 mr-1.5" stroke="url(#iconGrad)" />
                  {pasteSuccess ? "貼り付け✓" : "貼り付け"}
                </Button>
              </div>
            </div>
            <Textarea
              placeholder="歌詞・韓国語を貼り付け…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="min-h-[200px] resize-none border-0 focus-visible:ring-0 rounded-b-xl px-4 pt-4 pb-14 sm:pb-14 pr-4 text-slate-800 placeholder:text-slate-400 leading-relaxed input-result-text font-rounded"
              disabled={isConverting}
            />
            <div className="absolute bottom-3 right-5">
              <Button
                size="sm"
                onClick={handleConvert}
                disabled={isConverting || !input.trim()}
                className="rounded-full h-9 sm:h-11 px-4 sm:px-6 bg-purple-700 hover:bg-purple-800 text-white text-sm sm:text-base font-medium flex items-center gap-1.5 font-rounded shadow-sm hover:shadow-md transition-all"
              >
                {isConverting ? (
                  <Loader2 className="h-4 w-4 sm:h-5 sm:w-5 animate-spin" />
                ) : (
                  <>
                    変換する
                    <ChevronRight className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                  </>
                )}
              </Button>
            </div>
          </div>
          <div className="mt-2 px-1 flex items-center gap-2 flex-wrap">
            <span className="text-[11px] text-slate-400/90 font-rounded" aria-live="polite">
              {input.length} 文字
            </span>
            <span className="text-slate-300">|</span>
            <div
              role="group"
              aria-label="数字の変換"
              className="inline-flex rounded-lg bg-slate-100/80 p-0.5 text-[11px]"
            >
              <button
                type="button"
                onClick={() => setConvertNumbers(false)}
                disabled={isConverting}
                className={`rounded-md px-2 py-1 transition-colors disabled:opacity-50 ${
                  !convertNumbers
                    ? "bg-white text-slate-700 shadow-sm font-medium"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                数字そのまま
              </button>
              <button
                type="button"
                onClick={() => setConvertNumbers(true)}
                disabled={isConverting}
                className={`rounded-md px-2 py-1 transition-colors disabled:opacity-50 ${
                  convertNumbers
                    ? "bg-white text-slate-700 shadow-sm font-medium"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                韓国語読みで変換
              </button>
            </div>
          </div>

          {/* 注意点 */}
          <div className="mt-3 px-1">
            <p className="text-sm text-slate-500 leading-relaxed space-y-1 font-semibold">
              <span className="block">・英語、記号、日本語などハングル以外の文字は変換されずにそのまま出力されます。</span>
              <span className="block">・数字は上記の切り替えで「そのまま」か「韓国語読みで変換」を選べます。</span>
              <span className="block">・精度や正確性には限界があります。ご了承ください。</span>
              <span className="block">・初回のみ起動に時間がかかり、結果が出るまで数十秒かかる場合がございます。😢すみません！😢</span>
              <span className="block">・ご自由に変換結果はお使いいただけます。</span>
            </p>
          </div>

          {/* 変換中ローディング */}
          {isConverting && (
            <div className="mt-4 flex items-center justify-center gap-2 rounded-xl border border-violet-200/60 bg-violet-50/60 py-6 px-4">
              <span className="text-sm text-violet-700/90 font-rounded">変換中です</span>
              <span className="inline-flex gap-0.5">
                <span className="loading-dot inline-block w-1.5 h-1.5 rounded-full bg-violet-400" />
                <span className="loading-dot inline-block w-1.5 h-1.5 rounded-full bg-violet-400" />
                <span className="loading-dot inline-block w-1.5 h-1.5 rounded-full bg-violet-400" />
              </span>
            </div>
          )}

          {/* 結果は出たときのみ表示 */}
          {result && (
            <>
              <div className="my-4 border-t border-slate-300/70" />
              <div className="rounded-xl bg-white border border-slate-200/80 overflow-hidden animate-scale-in">
                <div className="flex items-center justify-between gap-2 px-4 py-2 border-b border-slate-100 bg-slate-50/80">
                  <span className="text-sm text-slate-500">結果</span>
                  <div className="flex items-center gap-2">
                    <Dialog open={dictDialogOpen} onOpenChange={setDictDialogOpen}>
                      <DialogTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={openDictDialog}
                          className="h-8 px-3 text-slate-600 text-sm font-semibold font-rounded"
                        >
                          <BookPlus className="h-5 w-5 mr-1 text-violet-500" />
                          辞書に追加
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-md rounded-2xl border-sky-200/60 bg-white/95 backdrop-blur-sm p-6">
                        <DialogHeader>
                          <DialogTitle className="text-lg font-semibold text-slate-800">
                            変換漏れを辞書に追加
                          </DialogTitle>
                          <DialogDescription className="text-sm text-slate-500 mt-1">
                            ハングルと読み（かな）を入力。次回の変換で使われます。
                          </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-5">
                          <div className="grid gap-1.5">
                            <Label htmlFor="dict-hangul" className="text-base text-slate-700 font-medium">
                              ハングル
                            </Label>
                            <Input
                              id="dict-hangul"
                              value={dictHangul}
                              onChange={(e) => setDictHangul(e.target.value)}
                              placeholder="例: 뚤"
                              disabled={dictSubmitting}
                              className="rounded-xl border-sky-200/60 h-10 focus-visible:ring-sky-200 font-rounded"
                            />
                          </div>
                          <div className="grid gap-1.5">
                            <Label htmlFor="dict-kana" className="text-sm text-slate-700 font-medium">
                              読み（かな）
                            </Label>
                            <Input
                              id="dict-kana"
                              value={dictKana}
                              onChange={(e) => setDictKana(e.target.value)}
                              placeholder="例: トゥル"
                              disabled={dictSubmitting}
                              className="rounded-xl border-sky-200/60 h-11 focus-visible:ring-sky-200 font-rounded"
                            />
                          </div>
                          {dictSuccess && (
                            <p className="text-sm text-green-700 bg-green-50/90 rounded-xl px-3 py-2 border border-green-100">
                              {dictSuccess}
                            </p>
                          )}
                        </div>
                        <DialogFooter className="gap-2 pt-2">
                          <Button
                            type="button"
                            variant="ghost"
                            onClick={() => setDictDialogOpen(false)}
                            disabled={dictSubmitting}
                            className="text-slate-600 font-rounded"
                          >
                            閉じる
                          </Button>
                          <Button
                            type="button"
                            onClick={handleAddDictionary}
                            disabled={dictSubmitting || !dictHangul.trim() || !dictKana.trim()}
                            className="rounded-xl bg-sky-600 font-rounded"
                          >
                            {dictSubmitting ? "追加中…" : "追加する"}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopy}
                      className="h-8 px-3 text-slate-600 text-sm font-semibold font-rounded"
                    >
                      <Copy className="h-5 w-5 mr-1 text-violet-500" />
                      {copied ? "コピーした" : "コピー"}
                    </Button>
                  </div>
                </div>
                <pre
                  onMouseUp={saveSelection}
                  onTouchEnd={saveSelection}
                  className="min-h-[120px] overflow-auto whitespace-pre-wrap font-rounded leading-relaxed px-4 py-4 text-slate-800 select-text text-left input-result-text"
                >
                  {result}
                </pre>
              </div>
            </>
          )}
        </div>

        <section className="mt-12 pt-10 border-t border-violet-200/40">
          <div className="md:rounded-[1.25rem] md:bg-convert-frame md:p-4 md:border md:border-slate-200/50 md:[border-width:0.5px]">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
              <article className="bg-white/80 backdrop-blur-sm rounded-2xl border border-violet-200/50 p-4 md:border-violet-300/60 animate-fade-in-up animate-delay-300 opacity-0 [border-width:0.5px]">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-12 h-12 rounded-xl bg-violet-100/80 flex items-center justify-center">
                    <Music2 className="h-6 w-6 text-violet-600/90" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-slate-800 text-base mb-1">
                      最新の曲も、有名じゃないあの曲も、手軽に変換！
                    </h2>
                    <p className="text-base text-slate-600/90 leading-relaxed">
                      オリジナル歌詞を貼るだけ！発売されたばかりの新曲も、すぐにかな読みに変換して歌えます。
                    </p>
                  </div>
                </div>
              </article>
              <article className="bg-white/80 backdrop-blur-sm rounded-2xl border border-pink-200/50 p-4 md:border-pink-300/60 animate-fade-in-up animate-delay-400 opacity-0 [border-width:0.5px]">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-pink-100/80 flex items-center justify-center">
                    <FileText className="h-5 w-5 text-pink-600/90" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-slate-800 text-base mb-1">
                      韓国語スクリプトもすぐに
                    </h2>
                    <p className="text-base text-slate-600/90 leading-relaxed">
                      ドラマや動画のセリフ、どんなテキストでも、すぐにかな読みに変換して読めます。
                    </p>
                  </div>
                </div>
              </article>
              <article className="bg-white/80 backdrop-blur-sm rounded-2xl border border-sky-200/50 p-4 md:border-sky-300/60 animate-fade-in-up animate-delay-500 opacity-0 [border-width:0.5px]">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-12 h-12 rounded-xl bg-sky-100/80 flex items-center justify-center">
                    <Users className="h-6 w-6 text-sky-600/90" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-slate-800 text-base mb-1">
                      みんなで作り上げるより正確な辞書
                    </h2>
                    <p className="text-base text-slate-600/90 leading-relaxed">
                      報告機能で新たに読みを追加。あなたの追加は即時に反映されて、より正確になります。
                    </p>
                  </div>
                </div>
              </article>
              <article className="bg-white/80 backdrop-blur-sm rounded-2xl border border-purple-200/50 p-4 md:border-purple-300/60 animate-fade-in-up opacity-0 animate-delay-600 [border-width:0.5px]">
                <div className="flex items-start gap-4">
                  <div className="shrink-0 w-10 h-10 rounded-xl bg-purple-100/80 flex items-center justify-center">
                    <ArrowRightLeft className="h-5 w-5 text-purple-600/90" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-slate-800 text-base mb-1">
                      日本語→ハングルも導入予定
                    </h2>
                    <p className="text-base text-slate-600/90 leading-relaxed">
                      逆方向の変換にも対応する予定です！例）こんにちは→콘니찌외
                      お楽しみに☺
                    </p>
                  </div>
                </div>
              </article>
            </div>
          </div>
        </section>

        <section className="mt-12 pt-8 pb-6 text-center">
          <p className="text-sm text-slate-600/90 mb-3 font-rounded">問い合わせ、ご意見はこちらからお願いします</p>
          <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
            <a
              href="https://zenn.dev/m70ng"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-slate-700 hover:text-violet-600 font-medium font-rounded transition-colors"
            >
              <img src="https://zenn.dev/favicon.ico" alt="" className="w-5 h-5 rounded" width={20} height={20} />
              Zenn
            </a>
            <a
              href="https://x.com/MeowNotFound"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-slate-700 hover:text-violet-600 font-medium font-rounded transition-colors"
            >
              <img src="https://x.com/favicon.ico" alt="" className="w-5 h-5 rounded" width={20} height={20} />
              X (Twitter)
            </a>
          </div>
        </section>
      </main>

    </div>
  )
}
