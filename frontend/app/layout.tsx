import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { generateMetadata as generateSEOMetadata } from "@/lib/seo";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = generateSEOMetadata({
  title: "Never Miss a Price Change",
  path: "/",
});

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
        <AuthProvider>
          <div className="app-shell">
            <div className="app-content">{children}</div>
            <footer className="app-footer">
              <a
                href="https://www.linkedin.com/in/d-g-c/"
                target="_blank"
                rel="noreferrer"
              >
                LinkedIn
              </a>
              <span className="footer-separator">•</span>
              <a
                href="https://github.com/chambies2015"
                target="_blank"
                rel="noreferrer"
              >
                GitHub
              </a>
              <span className="footer-separator">•</span>
              <a href="mailto:pricewatchdogs@gmail.com">Support</a>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
