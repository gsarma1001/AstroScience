import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nakshatra AI — Discover Your Cosmic Blueprint",
  description:
    "Explore Vedic astrology with thoughtful birth chart tools and traditional Jyotisha interpretations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
