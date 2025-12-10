"use client";

import Link from "next/link";
import { Mail } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 mt-auto">
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-foreground">
              <span className="text-purple-500">Aztec</span>List
            </span>
            <span>© {new Date().getFullYear()} All rights reserved.</span>
          </div>

          <div className="flex items-center gap-6">
            <Link
              href="/support"
              className="flex items-center gap-1.5 hover:text-foreground transition-colors"
            >
              <Mail className="w-4 h-4" />
              Contact Support
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
