"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { apiClient, getApiBaseUrl } from "@/lib/api";
import { toast } from "sonner";
import type { Carrier, EquipmentType } from "@/types";
import { EQUIPMENT_LABELS } from "@/types";

export default function CarriersPage() {
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [form, setForm] = useState({
    name: "",
    mc_number: "",
    dot_number: "",
    phone: "",
    email: "",
    equipment_types: [] as string[],
  });

  function resetForm() {
    setForm({
      name: "",
      mc_number: "",
      dot_number: "",
      phone: "",
      email: "",
      equipment_types: [],
    });
  }

  async function fetchCarriers() {
    try {
      const data = await apiClient<Carrier[]>("/api/carriers");
      setCarriers(data);
    } catch {
      toast.error("Failed to load carriers");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchCarriers();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiClient("/api/carriers", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          dot_number: form.dot_number || null,
          email: form.email || null,
          lanes: [],
        }),
      });
      toast.success("Carrier added");
      setDialogOpen(false);
      resetForm();
      fetchCarriers();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to create carrier"
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleImport(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const file = formData.get("file") as File;
    if (!file) return;

    setSubmitting(true);
    try {
      const uploadForm = new FormData();
      uploadForm.append("file", file);

      const token = localStorage.getItem("token");
      const response = await fetch(`${getApiBaseUrl()}/api/carriers/import`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: uploadForm,
      });
      const result = await response.json();

      if (!response.ok) throw new Error(result.detail);

      toast.success(
        `Imported ${result.created} carriers (${result.skipped} skipped)`
      );
      setImportDialogOpen(false);
      fetchCarriers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Import failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string, name: string) {
    if (!confirm(`Delete carrier "${name}"?`)) return;
    try {
      await apiClient(`/api/carriers/${id}`, { method: "DELETE" });
      toast.success("Carrier deleted");
      fetchCarriers();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete");
    }
  }

  function toggleEquipment(type: string) {
    setForm((prev) => ({
      ...prev,
      equipment_types: prev.equipment_types.includes(type)
        ? prev.equipment_types.filter((t) => t !== type)
        : [...prev.equipment_types, type],
    }));
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Carriers</h1>
        <div className="flex gap-2">
          <Dialog open={importDialogOpen} onOpenChange={setImportDialogOpen}>
            <DialogTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background px-4 py-2 hover:bg-accent hover:text-accent-foreground">
              Import CSV
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import Carriers from CSV</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleImport} className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  CSV should have columns: name, mc_number, dot_number, phone,
                  email, equipment_types
                </p>
                <Input name="file" type="file" accept=".csv" required />
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Importing..." : "Import"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger className="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground px-4 py-2 hover:bg-primary/90">
              Add Carrier
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add New Carrier</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <Label>Company Name</Label>
                  <Input
                    value={form.name}
                    onChange={(e) =>
                      setForm((p) => ({ ...p, name: e.target.value }))
                    }
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>MC Number</Label>
                    <Input
                      value={form.mc_number}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, mc_number: e.target.value }))
                      }
                      placeholder="MC-123456"
                      required
                    />
                  </div>
                  <div>
                    <Label>DOT Number</Label>
                    <Input
                      value={form.dot_number}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, dot_number: e.target.value }))
                      }
                      placeholder="DOT-123456"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Phone</Label>
                    <Input
                      value={form.phone}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, phone: e.target.value }))
                      }
                      placeholder="+15551234567"
                      required
                    />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={form.email}
                      onChange={(e) =>
                        setForm((p) => ({ ...p, email: e.target.value }))
                      }
                    />
                  </div>
                </div>
                <div>
                  <Label>Equipment Types</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {Object.entries(EQUIPMENT_LABELS).map(([value, label]) => (
                      <Badge
                        key={value}
                        variant={
                          form.equipment_types.includes(value)
                            ? "default"
                            : "outline"
                        }
                        className="cursor-pointer"
                        onClick={() => toggleEquipment(value)}
                      >
                        {label}
                      </Badge>
                    ))}
                  </div>
                </div>
                <Button type="submit" disabled={submitting}>
                  {submitting ? "Adding..." : "Add Carrier"}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : carriers.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-muted-foreground mb-4">
            No carriers yet. Add carriers manually or import from CSV.
          </p>
        </div>
      ) : (
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>MC #</TableHead>
                <TableHead>Phone</TableHead>
                <TableHead>Equipment</TableHead>
                <TableHead>Compliant</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {carriers.map((carrier) => (
                <TableRow key={carrier.id}>
                  <TableCell className="font-medium">{carrier.name}</TableCell>
                  <TableCell>{carrier.mc_number}</TableCell>
                  <TableCell>{carrier.phone}</TableCell>
                  <TableCell>
                    <div className="flex gap-1 flex-wrap">
                      {carrier.equipment_types.map((et) => (
                        <Badge key={et} variant="outline" className="text-xs">
                          {EQUIPMENT_LABELS[et as EquipmentType] || et}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    {carrier.is_compliant &&
                    carrier.authority_active &&
                    carrier.insurance_valid ? (
                      <Badge variant="secondary">Compliant</Badge>
                    ) : (
                      <Badge variant="destructive">Issues</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(carrier.id, carrier.name)}
                    >
                      Delete
                    </Button>
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
