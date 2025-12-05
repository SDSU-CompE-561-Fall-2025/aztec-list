import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import { Header } from "@/components/custom/header";

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
          <Header isSignedIn={false} />
          {children}
        </Providers>
      </body>
    </html>
  );
}
