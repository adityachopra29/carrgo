export interface User {
  id: string;
  email: string;
  full_name: string;
  company_name: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type LoadStatus = "draft" | "outreach_in_progress" | "quotes_received" | "booked" | "completed" | "cancelled";
export type CallStatus = "queued" | "ringing" | "in_progress" | "completed" | "failed" | "no_answer" | "voicemail";
export type CampaignStatus = "pending" | "in_progress" | "completed" | "cancelled";
export type EquipmentType = "dry_van" | "reefer" | "flatbed" | "step_deck" | "power_only";

export interface Load {
  id: string;
  origin: string;
  destination: string;
  pickup_date: string;
  delivery_date: string;
  equipment_type: EquipmentType;
  weight: number;
  commodity: string;
  target_rate: number;
  floor_rate: number;
  status: LoadStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Carrier {
  id: string;
  name: string;
  mc_number: string;
  dot_number: string | null;
  phone: string;
  email: string | null;
  equipment_types: EquipmentType[];
  lanes: LanePreference[];
  is_compliant: boolean;
  authority_active: boolean;
  insurance_valid: boolean;
  notes: string | null;
  created_at: string;
}

export interface LanePreference {
  origin_state: string;
  destination_state: string;
}

export interface Campaign {
  id: string;
  load_id: string;
  status: CampaignStatus;
  total_calls: number;
  completed_calls: number;
  best_rate: number | null;
  created_at: string;
  calls: Call[];
}

export interface Call {
  id: string;
  campaign_id: string;
  carrier_id: string;
  carrier?: Carrier;
  vapi_call_id: string | null;
  status: CallStatus;
  duration_secs: number | null;
  transcript: string | null;
  quoted_rate: number | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface Booking {
  id: string;
  load_id: string;
  carrier_id: string;
  call_id: string;
  agreed_rate: number;
  status: string;
  confirmed_at: string | null;
  created_at: string;
}

export interface LoadDetail extends Load {
  campaign: Campaign | null;
  booking: Booking | null;
}

export const EQUIPMENT_LABELS: Record<EquipmentType, string> = {
  dry_van: "Dry Van",
  reefer: "Reefer",
  flatbed: "Flatbed",
  step_deck: "Step Deck",
  power_only: "Power Only",
};

export const STATUS_LABELS: Record<LoadStatus, string> = {
  draft: "Draft",
  outreach_in_progress: "Outreach In Progress",
  quotes_received: "Quotes Received",
  booked: "Booked",
  completed: "Completed",
  cancelled: "Cancelled",
};

export const CALL_STATUS_LABELS: Record<CallStatus, string> = {
  queued: "Queued",
  ringing: "Ringing",
  in_progress: "In Progress",
  completed: "Completed",
  failed: "Failed",
  no_answer: "No Answer",
  voicemail: "Voicemail",
};
