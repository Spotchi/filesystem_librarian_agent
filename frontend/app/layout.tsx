import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "./markdown.css";
import { AuthProvider } from './providers/auth-provider';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Filesystem Librarian",
  description: "A tool to help you organize and manage your files",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
