"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
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
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import {
  getMessageReports,
  dismissMessageReport,
  upholdMessageReport,
  type MessageReport,
} from "@/lib/api";

function categoryLabel(category: string): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

export function MessageReportsView() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["messageReports", "open"],
    queryFn: () => getMessageReports("open"),
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["messageReports"] });
    queryClient.invalidateQueries({ queryKey: ["adminActions"] });
  };

  const dismissMutation = useMutation({
    mutationFn: dismissMessageReport,
    onSuccess: () => {
      refresh();
      toast.success("Report dismissed.");
    },
    onError: (error) => showErrorToast(error, "Failed to dismiss report"),
  });

  const upholdMutation = useMutation({
    mutationFn: upholdMessageReport,
    onSuccess: (result) => {
      refresh();
      if (result.auto_ban_triggered) {
        toast.error(`Report upheld. User auto-banned after ${result.strike_count} strikes.`);
      } else if (result.strike_issued) {
        toast.success(`Report upheld. User now has ${result.strike_count} strike(s).`);
      } else {
        toast.success("Report upheld. No strike issued (user already banned or removed).");
      }
    },
    onError: (error) => showErrorToast(error, "Failed to uphold report"),
  });

  const items: MessageReport[] = data?.items ?? [];
  const pending = dismissMutation.isPending || upholdMutation.isPending;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-b-2 border-purple-600"></div>
          <p className="text-sm text-muted-foreground">Loading message reports...</p>
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <Card className="border bg-card">
        <CardContent className="py-12 text-center">
          <ShieldCheck className="mx-auto mb-3 h-12 w-12 text-muted-foreground" />
          <p className="text-muted-foreground">No open message reports. The queue is clear.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const body = item.message?.content ?? item.message_excerpt ?? "(message unavailable)";
        return (
          <Card key={item.report_id} className="border bg-card">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center rounded-md border border-yellow-500/20 bg-yellow-500/10 px-2 py-0.5 text-xs font-semibold text-yellow-400">
                      {categoryLabel(item.category)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </div>

                  {/* The reported message body */}
                  <blockquote className="rounded-md border-l-2 border-muted-foreground/30 bg-muted/40 px-3 py-2 text-sm break-words text-foreground">
                    {body}
                  </blockquote>

                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>
                      <span className="font-medium">Author:</span>{" "}
                      {item.target_user?.username ?? "unknown"}
                    </span>
                    <span>
                      <span className="font-medium">Reported by:</span>{" "}
                      {item.reporter?.username ?? "unknown"}
                    </span>
                  </div>

                  {item.reason_text && (
                    <p className="text-sm text-foreground">
                      <span className="mr-1 text-xs font-medium tracking-wide text-muted-foreground uppercase">
                        Note:
                      </span>
                      {item.reason_text}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-shrink-0 flex-col gap-2">
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        size="sm"
                        disabled={pending}
                        className="bg-yellow-500 text-white hover:bg-yellow-600"
                      >
                        Uphold
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Uphold this report?</AlertDialogTitle>
                        <AlertDialogDescription>
                          This issues a strike to the message author. Three strikes trigger an
                          automatic ban.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => upholdMutation.mutate(item.report_id)}
                          className="bg-yellow-500 text-white hover:bg-yellow-600"
                        >
                          Uphold and strike
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => dismissMutation.mutate(item.report_id)}
                    disabled={pending}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
