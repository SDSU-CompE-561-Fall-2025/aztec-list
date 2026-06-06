/**
 * Shared block/unblock state for a target user.
 *
 * Wraps the "users I've blocked" query plus the block/unblock mutations so the
 * message thread and the profile page stay in sync (both read the same
 * `blockedUsers` query key) without duplicating the logic.
 */

"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import { useAuth } from "@/contexts/AuthContext";
import { blockUser, unblockUser, listMyBlocks } from "@/lib/messaging-api";

interface UseBlockUserResult {
  isBlocked: boolean;
  block: () => void;
  unblock: () => void;
  isPending: boolean;
}

export function useBlockUser(targetUserId: string, targetUserName: string): UseBlockUserResult {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: blockedUsers } = useQuery({
    queryKey: ["blockedUsers"],
    queryFn: listMyBlocks,
    enabled: !!user,
    staleTime: 1000 * 30,
  });

  const isBlocked = (blockedUsers ?? []).some((b) => b.blocked_user_id === targetUserId);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["blockedUsers"] });
    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };

  const blockMutation = useMutation({
    mutationFn: () => blockUser(targetUserId),
    onSuccess: () => {
      invalidate();
      toast.success(`You blocked ${targetUserName}. They can no longer message you.`);
    },
    onError: (error) => showErrorToast(error, "Failed to block user"),
  });

  const unblockMutation = useMutation({
    mutationFn: () => unblockUser(targetUserId),
    onSuccess: () => {
      invalidate();
      toast.success(`You unblocked ${targetUserName}.`);
    },
    onError: (error) => showErrorToast(error, "Failed to unblock user"),
  });

  return {
    isBlocked,
    block: () => blockMutation.mutate(),
    unblock: () => unblockMutation.mutate(),
    isPending: blockMutation.isPending || unblockMutation.isPending,
  };
}
