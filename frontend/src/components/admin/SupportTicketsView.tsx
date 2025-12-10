"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Mail, Trash2 } from "lucide-react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "sonner";
import { showErrorToast } from "@/lib/errorHandling";
import {
  getSupportTickets,
  updateSupportTicketStatus,
  deleteSupportTicket,
  type SupportTicket,
} from "@/lib/api";

const STATUS_COLORS = {
  open: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  in_progress: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  resolved: "bg-green-500/10 text-green-400 border-green-500/30",
  closed: "bg-gray-500/10 text-gray-400 border-gray-500/30",
};

const STATUS_LABELS = {
  open: "Open",
  in_progress: "In Progress",
  resolved: "Resolved",
  closed: "Closed",
};

export function SupportTicketsView() {
  const queryClient = useQueryClient();

  const { data: tickets, isLoading } = useQuery<SupportTicket[]>({
    queryKey: ["support-tickets"],
    queryFn: getSupportTickets,
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ ticketId, status }: { ticketId: string; status: string }) =>
      updateSupportTicketStatus(ticketId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support-tickets"] });
      toast.success("Ticket status updated");
    },
    onError: (error) => {
      showErrorToast(error, "Failed to update ticket status");
    },
  });

  const deleteTicketMutation = useMutation({
    mutationFn: deleteSupportTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["support-tickets"] });
      toast.success("Ticket deleted");
    },
    onError: (error) => {
      showErrorToast(error, "Failed to delete ticket");
    },
  });

  const handleStatusChange = (ticketId: string, newStatus: string) => {
    updateStatusMutation.mutate({ ticketId, status: newStatus });
  };

  const handleDeleteTicket = (ticketId: string) => {
    deleteTicketMutation.mutate(ticketId);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto mb-3"></div>
          <p className="text-muted-foreground text-sm">Loading tickets...</p>
        </div>
      </div>
    );
  }

  if (!tickets || tickets.length === 0) {
    return (
      <Card className="bg-card border">
        <CardContent className="py-12 text-center">
          <Mail className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
          <p className="text-muted-foreground">No support tickets yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {tickets.map((ticket) => (
        <Card key={ticket.id} className="bg-card border">
          <CardContent className="p-5">
            <div className="space-y-4">
              {/* Header with status and date */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 text-xs font-semibold rounded-full border ${
                        STATUS_COLORS[ticket.status]
                      }`}
                    >
                      {STATUS_LABELS[ticket.status]}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {new Date(ticket.created_at).toLocaleString()}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground truncate">
                    {ticket.subject}
                  </h3>
                  <p className="text-sm text-muted-foreground">{ticket.email}</p>
                </div>

                {/* Status selector and delete button */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Select
                    value={ticket.status}
                    onValueChange={(value: string) => handleStatusChange(ticket.id, value)}
                    disabled={updateStatusMutation.isPending || deleteTicketMutation.isPending}
                  >
                    <SelectTrigger className="w-40 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="open">Open</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="resolved">Resolved</SelectItem>
                      <SelectItem value="closed">Closed</SelectItem>
                    </SelectContent>
                  </Select>

                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={deleteTicketMutation.isPending}
                        className="h-9 w-9 text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete Ticket</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete this support ticket? This action cannot be
                          undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction
                          onClick={() => handleDeleteTicket(ticket.id)}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                </div>
              </div>

              {/* Message */}
              <div className="bg-muted/50 border rounded-lg p-4">
                <p className="text-sm text-foreground whitespace-pre-wrap">{ticket.message}</p>
              </div>

              {/* Ticket ID */}
              <div className="text-xs text-muted-foreground font-mono">Ticket ID: {ticket.id}</div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
