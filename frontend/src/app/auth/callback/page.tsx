"use client";

import { useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";

const REDIRECT_URI =
  process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI ||
  "http://localhost:3000/auth/callback";

function CallbackHandler() {
  const router = useRouter();
  const params = useSearchParams();
  const { loginWithGoogle } = useAuth();

  useEffect(() => {
    const code = params.get("code");
    const state = params.get("state");

    if (!code || !state) return;

    // CSRF check — read state but do NOT remove it yet.
    // React 18 Strict Mode runs effects twice. We leave the CSRF state in
    // sessionStorage so both runs can pass the check. The processingKey
    // (keyed to the auth code) ensures only one backend call is made.
    const storedState = sessionStorage.getItem("google_oauth_state");

    if (state !== storedState) {
      toast.error("Invalid OAuth state. Please try again.");
      router.replace("/login");
      return;
    }

    // Dedup guard: auth codes are single-use. If Strict Mode fires this
    // effect a second time, the processing key is already set → skip.
    const processingKey = `google_oauth_processing_${code}`;
    if (sessionStorage.getItem(processingKey)) return;
    sessionStorage.setItem(processingKey, "1");

    loginWithGoogle(code, REDIRECT_URI)
      .then(() => {
        sessionStorage.removeItem("google_oauth_state");
        sessionStorage.removeItem(processingKey);
        router.replace("/dashboard");
      })
      .catch((err: unknown) => {
        sessionStorage.removeItem("google_oauth_state");
        sessionStorage.removeItem(processingKey);
        toast.error(err instanceof Error ? err.message : "Google login failed");
        router.replace("/login");
      });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/30">
      <p className="text-muted-foreground">Completing Google sign-in...</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-muted/30">
          <p className="text-muted-foreground">Loading...</p>
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}
