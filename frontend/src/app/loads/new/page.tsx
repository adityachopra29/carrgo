"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import type { Load, EquipmentType } from "@/types";
import { EQUIPMENT_LABELS } from "@/types";

export default function NewLoadPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    origin: "",
    destination: "",
    pickup_date: "",
    delivery_date: "",
    equipment_type: "dry_van" as EquipmentType,
    weight: "",
    commodity: "",
    target_rate: "",
    floor_rate: "",
    notes: "",
  });

  function updateField(field: string, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);

    try {
      const payload = {
        ...form,
        weight: parseFloat(form.weight),
        target_rate: parseFloat(form.target_rate),
        floor_rate: parseFloat(form.floor_rate),
        notes: form.notes || null,
      };

      const load = await apiClient<Load>("/api/loads", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      toast.success("Load created successfully");
      router.push(`/loads/${load.id}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create load");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Create New Load</h1>

      <form onSubmit={handleSubmit}>
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Route Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="origin">Origin</Label>
                <Input
                  id="origin"
                  placeholder="e.g. Bolingbrook, IL"
                  value={form.origin}
                  onChange={(e) => updateField("origin", e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="destination">Destination</Label>
                <Input
                  id="destination"
                  placeholder="e.g. Columbus, GA"
                  value={form.destination}
                  onChange={(e) => updateField("destination", e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="pickup_date">Pickup Date</Label>
                <Input
                  id="pickup_date"
                  type="date"
                  value={form.pickup_date}
                  onChange={(e) => updateField("pickup_date", e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="delivery_date">Delivery Date</Label>
                <Input
                  id="delivery_date"
                  type="date"
                  value={form.delivery_date}
                  onChange={(e) => updateField("delivery_date", e.target.value)}
                  required
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Freight Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="equipment_type">Equipment Type</Label>
                <Select
                  value={form.equipment_type}
                  onValueChange={(v) => v && updateField("equipment_type", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(EQUIPMENT_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="weight">Weight (lbs)</Label>
                <Input
                  id="weight"
                  type="number"
                  placeholder="e.g. 40000"
                  value={form.weight}
                  onChange={(e) => updateField("weight", e.target.value)}
                  required
                />
              </div>
            </div>
            <div>
              <Label htmlFor="commodity">Commodity</Label>
              <Input
                id="commodity"
                placeholder="e.g. Consumer Electronics"
                value={form.commodity}
                onChange={(e) => updateField("commodity", e.target.value)}
                required
              />
            </div>
          </CardContent>
        </Card>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Rate</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="target_rate">Target Rate ($)</Label>
                <Input
                  id="target_rate"
                  type="number"
                  placeholder="e.g. 1800"
                  value={form.target_rate}
                  onChange={(e) => updateField("target_rate", e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Ideal rate you want to pay
                </p>
              </div>
              <div>
                <Label htmlFor="floor_rate">Floor Rate ($)</Label>
                <Input
                  id="floor_rate"
                  type="number"
                  placeholder="e.g. 2200"
                  value={form.floor_rate}
                  onChange={(e) => updateField("floor_rate", e.target.value)}
                  required
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Maximum rate you&apos;ll accept
                </p>
              </div>
            </div>
            <div>
              <Label htmlFor="notes">Notes (optional)</Label>
              <Textarea
                id="notes"
                placeholder="Any special instructions..."
                value={form.notes}
                onChange={(e) => updateField("notes", e.target.value)}
              />
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-4">
          <Button type="submit" disabled={submitting}>
            {submitting ? "Creating..." : "Create Load"}
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => router.push("/loads")}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}
