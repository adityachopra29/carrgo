"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { apiClient } from "@/lib/api";
import type { Load } from "@/types";
import { STATUS_LABELS, EQUIPMENT_LABELS } from "@/types";

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

export default function LoadsPage() {
  const [loads, setLoads] = useState<Load[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient<Load[]>("/api/loads")
      .then(setLoads)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Loads</h1>
        <Link href="/loads/new">
          <Button>Create New Load</Button>
        </Link>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : loads.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-muted-foreground mb-4">No loads yet.</p>
          <Link href="/loads/new">
            <Button>Create Your First Load</Button>
          </Link>
        </div>
      ) : (
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Route</TableHead>
                <TableHead>Pickup</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Commodity</TableHead>
                <TableHead className="text-right">Target Rate</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loads.map((load) => (
                <TableRow key={load.id} className="cursor-pointer">
                  <TableCell>
                    <Link
                      href={`/loads/${load.id}`}
                      className="font-medium hover:underline"
                    >
                      {load.origin} &rarr; {load.destination}
                    </Link>
                  </TableCell>
                  <TableCell>{load.pickup_date}</TableCell>
                  <TableCell>{EQUIPMENT_LABELS[load.equipment_type]}</TableCell>
                  <TableCell>{load.commodity}</TableCell>
                  <TableCell className="text-right">
                    ${load.target_rate.toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(load.status)}>
                      {STATUS_LABELS[load.status]}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
