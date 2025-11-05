import type React from "react"
import "./globals.css"
import type { Metadata } from "next"
import { Inter } from "next/font/google"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "WhatsApp Anniversary Messages",
  description: "A collection of our special moments",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="light">
      {/*
        Note: Currently forcing light mode with className="light" on <html>.

        To add dark mode support later:
        1. Import ThemeProvider: import { ThemeProvider } from "@/components/theme-provider"
        2. Remove className="light" from <html>
        3. Add suppressHydrationWarning to <html>
        4. Wrap {children} with:
           <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
             {children}
           </ThemeProvider>
        5. Add a theme toggle button in your UI
      */}
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}