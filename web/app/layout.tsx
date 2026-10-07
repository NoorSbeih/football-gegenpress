import type { Metadata } from "next";
import Link from "next/link";
import { Barlow_Condensed, Source_Sans_3 } from "next/font/google";
import { Scale } from "./components/Scale";
import { getCompetition } from "@/lib/data";
import "./globals.css";

const display = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["500", "600"],
  variable: "--font-display",
});

const text = Source_Sans_3({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-text",
});

export const metadata: Metadata = {
  title: "Gegenpress",
  description: "The eight seconds after a team loses the ball. World Cup 2022.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  const competition = getCompetition();
  return (
    <html lang="en" className={`${display.variable} ${text.variable}`}>
      <body>
        <header className="site-header">
          <Link href="/" className="wordmark">
            Gegenpress
            <Scale label="Eight-second scale" />
          </Link>
          <nav aria-label="Views">
            <Link href="/">Table</Link>
            <Link href={`/match/${competition.default_match_id}`}>Match tape</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
