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
  title: "カナルビ屋",
  description: "歌詞・韓国語を入力してかな読みに変換。カナルビ屋",
  icons: { icon: "/icon.svg" },
  robots: {
    index: false,
    follow: false,
    googleBot: { index: false, follow: false },
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
