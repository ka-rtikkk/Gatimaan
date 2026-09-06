import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Gatimaan — AI-Powered Railway Block Planning",
  description:
    "Smart India Hackathon Prototype: AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways. SIMULATED DATA.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-[#eef2f7] text-slate-900`}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
