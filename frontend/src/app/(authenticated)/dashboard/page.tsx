"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import type { Load } from "@/types";
import { STATUS_LABELS } from "@/types";

function getStatusVariant(
  status: string
): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case "outreach_in_progress":
    case "quotes_received":
    case "booked":
      return "default";
    case "cancelled":
      return "destructive";
    default:
      return "secondary";
  }
}

export default function Dashboard() {
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient<Load[]>("/api/loads")
      .then(setLoads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const statusCounts = loads.reduce(
    (acc, load) => {
      acc[load.status] = (acc[load.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link href="/loads/new">
          <Button>Create New Load</Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Total Loads
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{loads.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Active Outreach
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {statusCounts["outreach_in_progress"] || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Quotes Received
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {statusCounts["quotes_received"] || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">
              Booked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {statusCounts["booked"] || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Loads</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : loads.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground mb-4">
                No loads yet. Create your first load to get started.
              </p>
              <Link href="/loads/new">
                <Button>Create Load</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {loads.slice(0, 10).map((load) => (
                <Link
                  key={load.id}
                  href={`/loads/${load.id}`}
                  className="flex items-center justify-between p-3 rounded-md border hover:bg-muted/50 transition-colors"
                >
                  <div>
                    <p className="font-medium">
                      {load.origin} &rarr; {load.destination}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {load.commodity} &middot;{" "}
                      {load.weight.toLocaleString()} lbs
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-medium">
                        ${load.target_rate.toLocaleString()}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        target rate
                      </p>
                    </div>
                    <Badge variant={getStatusVariant(load.status)}>
                      {STATUS_LABELS[load.status]}
                    </Badge>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
