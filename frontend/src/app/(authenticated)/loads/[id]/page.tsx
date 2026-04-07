"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiClient, getSSEUrl } from "@/lib/api";
import { toast } from "sonner";
import type { LoadDetail, Campaign, Call } from "@/types";
import { STATUS_LABELS, EQUIPMENT_LABELS, CALL_STATUS_LABELS } from "@/types";

function getStatusVariant(
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "outreach_in_progress":
    case "quotes_received":
    case "booked":
    case "in_progress":
    case "ringing":
      return "default";
    case "cancelled":
    case "failed":
    case "no_answer":
      return "destructive";
    case "completed":
      return "secondary";
    default:
      return "outline";
  }
}

export default function LoadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const loadId = params.id as string;

  const [load, setLoad] = useState<LoadDetail | null>(null);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingOutreach, setStartingOutreach] = useState(false);
  const [bookingCallId, setBookingCallId] = useState<string | null>(null);

  const fetchLoad = useCallback(async () => {
    try {
      const data = await apiClient<LoadDetail>(`/api/loads/${loadId}`);
      setLoad(data);
      setCampaign(data.campaign);
    } catch {
      toast.error("Failed to load details");
    } finally {
      setLoading(false);
    }
  }, [loadId]);

  useEffect(() => {
    fetchLoad();
  }, [fetchLoad]);

  // SSE for real-time updates
  useEffect(() => {
    if (
      !load ||
      (load.status !== "outreach_in_progress" &&
        load.status !== "quotes_received")
    ) {
      return;
    }

    const eventSource = new EventSource(getSSEUrl(loadId));

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "call_update") {
          setCampaign((prev) => {
            if (!prev) return prev;
            const updatedCalls = prev.calls.map((call) =>
              call.id === data.data.call_id
                ? {
                    ...call,
                    status: data.data.status,
                    quoted_rate: data.data.quoted_rate ?? call.quoted_rate,
                  }
                : call
            );
            return { ...prev, calls: updatedCalls };
          });
        }

        if (data.type === "campaign_update") {
          setCampaign((prev) =>
            prev
              ? {
                  ...prev,
                  status: data.data.status,
                  completed_calls: data.data.completed_calls,
                  best_rate: data.data.best_rate,
                }
              : prev
          );
          if (data.data.status === "completed") {
            fetchLoad();
          }
        }

        if (data.type === "new_quote") {
          setCampaign((prev) => {
            if (!prev) return prev;
            const updatedCalls = prev.calls.map((call) =>
              call.id === data.data.call_id
                ? {
                    ...call,
                    quoted_rate: data.data.quoted_rate,
                    status: "completed" as const,
                  }
                : call
            );
            return { ...prev, calls: updatedCalls };
          });
          toast.success(
            `New quote: $${data.data.quoted_rate} from ${data.data.carrier_name || "carrier"}`
          );
        }
      } catch (e) {
        console.error("SSE parse error:", e);
      }
    };

    return () => eventSource.close();
  }, [load?.status, loadId, fetchLoad]);

  async function handleStartOutreach() {
    setStartingOutreach(true);
    try {
      const newCampaign = await apiClient<Campaign>(
        `/api/loads/${loadId}/outreach`,
        { method: "POST" }
      );
      setCampaign(newCampaign);
      setLoad((prev) =>
        prev ? { ...prev, status: "outreach_in_progress" } : prev
      );
      toast.success(
        `Outreach started! Calling ${newCampaign.total_calls} carriers...`
      );
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to start outreach"
      );
    } finally {
      setStartingOutreach(false);
    }
  }

  async function handleBook(callId: string, rate: number) {
    setBookingCallId(callId);
    try {
      await apiClient(`/api/loads/${loadId}/book`, {
        method: "POST",
        body: JSON.stringify({ call_id: callId }),
      });
      toast.success(`Load booked at $${rate.toLocaleString()}!`);
      fetchLoad();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to book");
    } finally {
      setBookingCallId(null);
    }
  }

  if (loading) {
    return <p className="text-muted-foreground">Loading...</p>;
  }

  if (!load) {
    return <p className="text-destructive">Load not found.</p>;
  }

  const completedCalls =
    campaign?.calls.filter((c) => c.status === "completed") || [];
  const quotedCalls = completedCalls
    .filter((c) => c.quoted_rate !== null)
    .sort((a, b) => (a.quoted_rate || 0) - (b.quoted_rate || 0));

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <Button
            variant="ghost"
            size="sm"
            className="mb-2"
            onClick={() => router.push("/loads")}
          >
            &larr; Back to Loads
          </Button>
          <h1 className="text-2xl font-bold">
            {load.origin} &rarr; {load.destination}
          </h1>
          <p className="text-muted-foreground">
            {load.commodity} &middot; {load.weight.toLocaleString()} lbs &middot;{" "}
            {EQUIPMENT_LABELS[load.equipment_type]}
          </p>
        </div>
        <Badge variant={getStatusVariant(load.status)} className="text-sm">
          {STATUS_LABELS[load.status]}
        </Badge>
      </div>

      {/* Load info cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Pickup</CardTitle>
          </CardHeader>
          <CardContent className="font-medium">{load.pickup_date}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Delivery</CardTitle>
          </CardHeader>
          <CardContent className="font-medium">{load.delivery_date}</CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Target Rate</CardTitle>
          </CardHeader>
          <CardContent className="font-medium text-lg">
            ${load.target_rate.toLocaleString()}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Floor Rate (Max)</CardTitle>
          </CardHeader>
          <CardContent className="font-medium text-lg">
            ${load.floor_rate.toLocaleString()}
          </CardContent>
        </Card>
      </div>

      {/* Booking info */}
      {load.booking && (
        <Card className="mb-6 border-green-200 bg-green-50">
          <CardHeader>
            <CardTitle className="text-green-800">Booked</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-green-700">
              Agreed rate:{" "}
              <strong>${load.booking.agreed_rate.toLocaleString()}</strong>
              {load.booking.confirmed_at &&
                ` · Confirmed: ${new Date(load.booking.confirmed_at).toLocaleString()}`}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Action button */}
      {(load.status === "draft" || load.status === "quotes_received") && (
        <div className="mb-6">
          <Button
            size="lg"
            onClick={handleStartOutreach}
            disabled={startingOutreach}
          >
            {startingOutreach
              ? "Starting outreach..."
              : load.status === "quotes_received"
                ? "Re-run Outreach"
                : "Start AI Outreach"}
          </Button>
          <p className="text-sm text-muted-foreground mt-2">
            The AI will call carriers in parallel to find the best rate.
          </p>
        </div>
      )}

      {/* Campaign section */}
      {campaign && (
        <>
          <Separator className="my-6" />

          <Card className="mb-6">
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>Outreach Campaign</CardTitle>
                <Badge variant={getStatusVariant(campaign.status)}>
                  {campaign.status === "in_progress"
                    ? `${campaign.completed_calls}/${campaign.total_calls} calls done`
                    : campaign.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-muted rounded-full h-3 mb-4">
                <div
                  className="bg-primary h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${
                      campaign.total_calls > 0
                        ? (campaign.completed_calls / campaign.total_calls) * 100
                        : 0
                    }%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>
                  {campaign.completed_calls} of {campaign.total_calls} calls
                  completed
                </span>
                {campaign.best_rate && (
                  <span className="font-medium text-foreground">
                    Best rate: ${campaign.best_rate.toLocaleString()}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          <Tabs defaultValue="calls">
            <TabsList>
              <TabsTrigger value="calls">
                All Calls ({campaign.calls.length})
              </TabsTrigger>
              <TabsTrigger value="quotes">
                Quotes ({quotedCalls.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="calls">
              <div className="border rounded-md">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Carrier</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Quoted Rate</TableHead>
                      <TableHead>Duration</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {campaign.calls.map((call) => (
                      <TableRow key={call.id}>
                        <TableCell className="font-medium">
                          {call.carrier?.name || call.carrier_id.slice(0, 8)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={getStatusVariant(call.status)}
                            className="text-xs"
                          >
                            {CALL_STATUS_LABELS[call.status]}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {call.quoted_rate
                            ? `$${call.quoted_rate.toLocaleString()}`
                            : "-"}
                        </TableCell>
                        <TableCell>
                          {call.duration_secs ? `${call.duration_secs}s` : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="quotes">
              {quotedCalls.length === 0 ? (
                <p className="text-muted-foreground py-4">
                  No quotes received yet.
                </p>
              ) : (
                <div className="border rounded-md">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Carrier</TableHead>
                        <TableHead className="text-right">Rate</TableHead>
                        <TableHead className="text-right">vs Target</TableHead>
                        <TableHead>Transcript</TableHead>
                        {load.status !== "booked" && (
                          <TableHead className="text-right">Action</TableHead>
                        )}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {quotedCalls.map((call, idx) => {
                        const diff =
                          ((call.quoted_rate || 0) - load.target_rate) /
                          load.target_rate;
                        const isBest = idx === 0;

                        return (
                          <TableRow
                            key={call.id}
                            className={isBest ? "bg-green-50" : ""}
                          >
                            <TableCell className="font-medium">
                              {call.carrier?.name ||
                                call.carrier_id.slice(0, 8)}
                              {isBest && (
                                <Badge
                                  variant="outline"
                                  className="ml-2 text-xs"
                                >
                                  Best
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right font-bold">
                              ${call.quoted_rate?.toLocaleString()}
                            </TableCell>
                            <TableCell
                              className={`text-right ${
                                diff <= 0
                                  ? "text-green-600"
                                  : diff > 0.1
                                    ? "text-red-600"
                                    : "text-yellow-600"
                              }`}
                            >
                              {diff <= 0
                                ? `${(diff * 100).toFixed(1)}%`
                                : `+${(diff * 100).toFixed(1)}%`}
                            </TableCell>
                            <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                              {call.transcript || "-"}
                            </TableCell>
                            {load.status !== "booked" && (
                              <TableCell className="text-right">
                                <Button
                                  size="sm"
                                  onClick={() =>
                                    handleBook(call.id, call.quoted_rate || 0)
                                  }
                                  disabled={bookingCallId === call.id}
                                >
                                  {bookingCallId === call.id
                                    ? "Booking..."
                                    : "Book"}
                                </Button>
                              </TableCell>
                            )}
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
