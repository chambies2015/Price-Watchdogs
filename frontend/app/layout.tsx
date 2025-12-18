import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Price Watchdogs - Never Miss a Price Change",
    template: "%s | Price Watchdogs"
  },
  description: "Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change, plans are removed, or free tiers disappear. Never miss a price change again.",
  keywords: ["SaaS monitoring", "price tracking", "subscription monitoring", "price alerts", "SaaS pricing", "price change detection"],
  authors: [{ name: "Price Watchdogs" }],
  creator: "Price Watchdogs",
  publisher: "Price Watchdogs",
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"),
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "/",
    siteName: "Price Watchdogs",
    title: "Price Watchdogs - Never Miss a Price Change",
    description: "Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change, plans are removed, or free tiers disappear.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Price Watchdogs - Monitor SaaS Pricing Changes",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Price Watchdogs - Never Miss a Price Change",
    description: "Monitor SaaS pricing pages and subscription changes. Get instant alerts when prices change.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
