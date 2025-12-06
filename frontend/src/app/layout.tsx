import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { HeaderClient } from "@/components/custom/header-client";

export const metadata: Metadata = {
  title: "AztecList Campus",
  description: "Campus marketplace for students",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <HeaderClient />
          {children}
        </Providers>
      </body>
    </html>
  );
}
