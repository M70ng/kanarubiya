import type { Metadata } from "next";
import { siteUrl } from "@/lib/site-url";
import "../styles/globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "カナルビ変換サイト｜韓国語・ハングルをかな読みに変換",
    template: "%s｜カナルビ変換サイト",
  },
  description:
    "韓国語の歌詞や文章をカタカナの読み方に変換する無料のカナルビ変換サイト。ハングルを入力・貼り付けするだけで使えます。",
  keywords: [
    "カナルビ",
    "カナルビ変換サイト",
    "カナルビ 変換",
    "韓国語 かな",
    "ハングル 読み",
    "韓国語 変換",
    "歌詞 かな",
    "ハングル かな変換",
    "韓国語 ルビ",
  ],
  alternates: { canonical: "/" },
  icons: { icon: "/icon.svg" },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  openGraph: {
    title: "カナルビ変換サイト｜韓国語・ハングルをかな読みに変換",
    description:
      "韓国語・ハングルをコピペするだけでかな読みに。歌詞や日常会話に。無料のカナルビツール。",
    type: "website",
    locale: "ja_JP",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className="antialiased"
      >
        {children}
      </body>
    </html>
  );
}
