/**
 * Messages page - main messaging interface
 */

"use client";

import { useState, useEffect, useCallback, useSyncExternalStore } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ConversationList } from "@/components/messages/ConversationList";
import { MessageThread } from "@/components/messages/MessageThread";
import { Button } from "@/components/ui/button";
import { ChevronLeft, MessageSquare } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useQuery } from "@tanstack/react-query";
import { createUserQueryOptions } from "@/queryOptions/createUserQueryOptions";

export default function MessagesPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();

  // Use useSyncExternalStore for proper hydration detection without effect setState
  const isHydrated = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  // Initialize state from URL params directly to avoid effect setState
  const conversationFromUrl = searchParams.get("conversation");
  const userFromUrl = searchParams.get("user");
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(
    conversationFromUrl,
  );
  const [selectedOtherUserId, setSelectedOtherUserId] = useState<string | null>(userFromUrl);
  const [isMobileThreadView, setIsMobileThreadView] = useState(!!conversationFromUrl);

  // Fetch other user data
  const { data: otherUser } = useQuery({
    ...createUserQueryOptions(selectedOtherUserId || ""),
    enabled: !!selectedOtherUserId,
  });

  // All hooks must be called before any early returns
  const handleSelectConversation = useCallback(
    (conversationId: string, otherUserId: string) => {
      setSelectedConversationId(conversationId);
      setSelectedOtherUserId(otherUserId);
      setIsMobileThreadView(true);

      // Update URL
      router.push(`/messages?conversation=${conversationId}&user=${otherUserId}`);
    },
    [router],
  );

  const handleBackToList = useCallback(() => {
    setIsMobileThreadView(false);
    router.push("/messages");
  }, [router]);

  // Redirect to login if not authenticated (after hydration)
  useEffect(() => {
    if (isHydrated && !user) {
      router.push("/login?redirect=/messages");
    }
  }, [user, isHydrated, router]);

  if (!isHydrated || !user) {
    return null;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <div className="flex flex-1 overflow-hidden">
        {/* Conversation List - Desktop: always visible, Mobile: hide when thread is shown */}
        <div
          className={`w-full border-r bg-background md:w-80 lg:w-96 ${
            isMobileThreadView ? "hidden md:block" : "block"
          }`}
        >
          <ConversationList
            selectedConversationId={selectedConversationId ?? undefined}
            onSelectConversation={handleSelectConversation}
          />
        </div>

        {/* Message Thread - Desktop: always visible, Mobile: show when conversation selected */}
        <div
          className={`flex-1 ${
            isMobileThreadView || selectedConversationId
              ? "flex flex-col"
              : "hidden md:flex md:flex-col"
          }`}
        >
          {selectedConversationId && selectedOtherUserId && otherUser ? (
            <>
              {/* Mobile Back Button */}
              <div className="border-b p-2 md:hidden">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBackToList}
                  className="gap-2"
                  aria-label="Back to conversations"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Back to conversations
                </Button>
              </div>

              <MessageThread
                key={selectedConversationId}
                conversationId={selectedConversationId}
                otherUserId={selectedOtherUserId}
                otherUserName={otherUser.username}
              />
            </>
          ) : (
            <div className="hidden flex-1 items-center justify-center p-8 text-center md:flex">
              <div className="max-w-sm space-y-4">
                <MessageSquare className="mx-auto h-16 w-16 text-muted-foreground" />
                <div>
                  <h2 className="text-lg font-semibold">No conversation selected</h2>
                  <p className="mt-2 text-muted-foreground">
                    Choose a conversation from the list to view messages
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
