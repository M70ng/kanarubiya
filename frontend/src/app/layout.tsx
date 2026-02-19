import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { M_PLUS_Rounded_1c } from "next/font/google";
import "../styles/globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const mplusRounded = M_PLUS_Rounded_1c({
  variable: "--font-rounded",
  weight: ["400", "500", "700"],
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "https://kanarubiya.com"),
  title: {
    default: "カナルビ屋｜韓国語・ハングルをかな読みに変換",
    template: "%s｜カナルビ屋",
  },
  description:
    "カナルビで韓国語・ハングルの歌詞やテキストをかな読みに変換。コピペするだけで読める。歌詞、ドラマのセリフ、日常会話まで。無料で使えるカナルビ（ルビ振り）ツール。",
  keywords: [
    "カナルビ",
    "韓国語 かな",
    "ハングル 読み",
    "韓国語 変換",
    "歌詞 かな",
    "ハングル かな変換",
    "韓国語 ルビ",
  ],
  icons: { icon: "/icon.svg" },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  openGraph: {
    title: "カナルビ屋｜韓国語・ハングルをかな読みに変換",
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
        className={`${geistSans.variable} ${geistMono.variable} ${mplusRounded.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
