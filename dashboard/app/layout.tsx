import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PC Dashboard Monitor — Sensores ao Vivo",
  description: "Monitore CPU, GPU, RAM e armazenamento do seu PC em tempo real de qualquer lugar.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className="h-full">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
