"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { Send, Sparkles } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { type ChatMessage, useAIChat } from "@/hooks/useAIChat";
import { type AISource } from "@/lib/ai-api";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { LISTINGS_BASE_URL } from "@/lib/constants";

const ACCENT = "bg-purple-600 text-white hover:bg-purple-700";

const MARKDOWN_STYLES =
  "[&_a]:text-purple-400 [&_a]:underline [&_li]:my-0.5 [&_ol]:my-2 [&_ol]:list-decimal " +
  "[&_ol]:space-y-1 [&_ol]:pl-5 [&_p]:mb-2 [&_p:last-child]:mb-0 [&_strong]:font-semibold " +
  "[&_ul]:my-2 [&_ul]:list-disc [&_ul]:pl-5";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Turn each cited listing title mentioned in the answer into a markdown link. */
function linkifySources(content: string, sources?: AISource[]): string {
  if (!sources || sources.length === 0) return content;
  let result = content;
  // Longest titles first so a shorter title isn't matched inside a longer one.
  for (const source of [...sources].sort((a, b) => b.title.length - a.title.length)) {
    const pattern = new RegExp(escapeRegExp(source.title), "i");
    result = result.replace(pattern, (match) => `[${match}](${LISTINGS_BASE_URL}/${source.id})`);
  }
  return result;
}

function MessageBubble({
  message,
  streaming,
  onNavigate,
}: {
  message: ChatMessage;
  streaming: boolean;
  onNavigate: () => void;
}) {
  if (message.role === "user") {
    return <span className="whitespace-pre-wrap">{message.content}</span>;
  }
  if (message.content) {
    const components: Components = {
      a: ({ href, children }) => (
        <Link href={href ?? "#"} onClick={onNavigate} className="text-purple-400 underline">
          {children}
        </Link>
      ),
    };
    return (
      <div className={MARKDOWN_STYLES}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
          {linkifySources(message.content, message.sources)}
        </ReactMarkdown>
      </div>
    );
  }
  if (streaming) {
    return <span className="animate-pulse text-muted-foreground">Thinking…</span>;
  }
  return null;
}

export function AssistantSheet() {
  const { isAuthenticated } = useAuth();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const { messages, isStreaming, error, sendMessage } = useAIChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  if (!isAuthenticated) return null;

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    void sendMessage(text);
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          size="lg"
          className={`fixed right-6 bottom-6 z-50 gap-2 rounded-full shadow-lg ${ACCENT}`}
        >
          <Sparkles className="h-4 w-4" />
          Ask AI
        </Button>
      </SheetTrigger>
      <SheetContent
        side="right"
        className="flex w-full flex-col gap-0 p-0 focus:outline-hidden sm:max-w-md"
      >
        <SheetHeader className="border-b">
          <SheetTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-400" />
            Shopping assistant
          </SheetTitle>
          <SheetDescription>
            Describe what you need and I will search the listings for the best matches.
          </SheetDescription>
        </SheetHeader>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Ask me to find something. For example, try “a cheap desk for my dorm” or “something to
              listen to music”. I search real listings and link the best matches.
            </p>
          )}

          {messages.map((message, index) => (
            <div key={index} className={message.role === "user" ? "text-right" : "text-left"}>
              <div
                className={`inline-block max-w-[85%] rounded-lg px-3 py-2 text-left text-sm ${
                  message.role === "user" ? "bg-purple-600 text-white" : "bg-muted text-foreground"
                }`}
              >
                <MessageBubble
                  message={message}
                  streaming={isStreaming && index === messages.length - 1}
                  onNavigate={() => setOpen(false)}
                />
              </div>

              {message.sources && message.sources.length > 0 && (
                <div className="mt-2">
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Related listings</p>
                  <div className="flex flex-wrap gap-1.5">
                    {message.sources.map((source) => (
                      <Link
                        key={source.id}
                        href={`${LISTINGS_BASE_URL}/${source.id}`}
                        onClick={() => setOpen(false)}
                        className="rounded-full border border-purple-500/40 bg-purple-500/10 px-2 py-0.5 text-xs text-purple-300 transition-colors hover:bg-purple-500/20"
                      >
                        {source.title}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <div className="border-t p-4">
          <div className="flex items-end gap-2">
            <Textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about listings…"
              className="max-h-32 min-h-10 flex-1 resize-none"
              disabled={isStreaming}
            />
            <Button
              onClick={handleSend}
              disabled={isStreaming || !input.trim()}
              size="icon"
              aria-label="Send message"
              className={ACCENT}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
