"use client";

import { GoogleLogin } from "@react-oauth/google";
import { LogIn } from "lucide-react";
import { useState } from "react";
import { postJson } from "@/lib/api";

type AuthResponse = {
  item: {
    token: string;
    user: { email: string; name: string; role: string };
  };
};

export function GoogleLoginBox() {
  const [user, setUser] = useState<AuthResponse["item"]["user"] | null>(null);
  const [message, setMessage] = useState("");
  const enabled = Boolean(process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID);

  if (!enabled) {
    return (
      <div className="panel stack">
        <div className="kicker">Google login</div>
        <p className="muted">Set NEXT_PUBLIC_GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID to enable signup and login.</p>
      </div>
    );
  }

  return (
    <div className="panel stack">
      <div className="kicker">Account</div>
      {user ? (
        <p className="muted">
          Signed in as {user.email}. Role: {user.role}.
        </p>
      ) : (
        <>
          <p className="muted">Users can sign up or log in with Google. The Flask API verifies the identity token.</p>
          <GoogleLogin
            onSuccess={async (credentialResponse) => {
              const result = await postJson<AuthResponse>("/auth/google", {
                credential: credentialResponse.credential
              });
              localStorage.setItem("homestead_site_token", result.item.token);
              setUser(result.item.user);
              setMessage("Login successful.");
            }}
            onError={() => setMessage("Google login failed.")}
          />
        </>
      )}
      {message ? (
        <span className="muted">
          <LogIn size={14} /> {message}
        </span>
      ) : null}
    </div>
  );
}

