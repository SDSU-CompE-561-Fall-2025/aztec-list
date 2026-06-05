"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { showErrorToast } from "@/lib/errorHandling";
import {
  reportMessage,
  MESSAGE_REPORT_CATEGORIES,
  type MessageReportCategory,
} from "@/lib/messaging-api";

interface ReportMessageDialogProps {
  messageId: string | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReportMessageDialog({ messageId, open, onOpenChange }: ReportMessageDialogProps) {
  const [category, setCategory] = useState<MessageReportCategory | "">("");
  const [reasonText, setReasonText] = useState("");

  const reportMutation = useMutation({
    mutationFn: () =>
      reportMessage(messageId as string, category as MessageReportCategory, reasonText),
    onSuccess: () => {
      toast.success("Report submitted. Our moderators will review it.");
      onOpenChange(false);
      setCategory("");
      setReasonText("");
    },
    onError: (error) => showErrorToast(error, "Failed to submit report"),
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Report message</DialogTitle>
          <DialogDescription>
            Tell us what is wrong with this message. Reports are confidential.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="space-y-1.5">
            <Label htmlFor="report-category">Reason</Label>
            <Select value={category} onValueChange={(v) => setCategory(v as MessageReportCategory)}>
              <SelectTrigger id="report-category">
                <SelectValue placeholder="Choose a reason" />
              </SelectTrigger>
              <SelectContent>
                {MESSAGE_REPORT_CATEGORIES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="report-detail">Details (optional)</Label>
            <Textarea
              id="report-detail"
              value={reasonText}
              onChange={(e) => setReasonText(e.target.value)}
              maxLength={1000}
              rows={3}
              placeholder="Add any context that will help our moderators."
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => reportMutation.mutate()}
            disabled={!category || !messageId || reportMutation.isPending}
            className="bg-red-600 text-white hover:bg-red-700"
          >
            {reportMutation.isPending ? "Submitting..." : "Submit report"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
