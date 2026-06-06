"use client";

import { Ban } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useBlockUser } from "@/hooks/useBlockUser";

interface BlockUserButtonProps {
  userId: string;
  userName: string;
}

/**
 * A standalone block / unblock button with a confirmation dialog. Used on the
 * profile page; the message thread uses the same {@link useBlockUser} hook inline.
 */
export function BlockUserButton({ userId, userName }: BlockUserButtonProps) {
  const { isBlocked, block, unblock, isPending } = useBlockUser(userId, userName);

  if (isBlocked) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={unblock}
        disabled={isPending}
        className="gap-1.5"
      >
        <Ban className="h-4 w-4" />
        Unblock
      </Button>
    );
  }

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={isPending}
          className="gap-1.5 text-destructive hover:text-destructive"
        >
          <Ban className="h-4 w-4" />
          Block
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Block {userName}?</AlertDialogTitle>
          <AlertDialogDescription>
            They will no longer be able to message you, and any conversation with them will be
            hidden from your inbox. You can unblock them at any time.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={block}
            className="text-destructive-foreground bg-destructive hover:bg-destructive/90"
          >
            Block
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
