import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AppProviders } from "@/components/providers/app-providers";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cinema Plus",
  description: "Next.js frontend foundation for Cinema Plus.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="dark flex min-h-screen flex-col bg-background text-foreground antialiased">
        <AppProviders>
          <Navbar />
          <main className="flex-grow flex flex-col">{children}</main>
          <Footer />
        </AppProviders>
      </body>
    </html>
  );
}
