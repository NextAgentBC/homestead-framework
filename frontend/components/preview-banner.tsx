"use client";

import { useRouter } from "next/navigation";
import { PREVIEW_COOKIE } from "@/lib/api";
import { t, type Messages } from "@/lib/i18n";

// Per-visitor industry preview is a client-set, server-read cookie. Setting it and
// calling router.refresh() re-renders the (force-dynamic) layout + home with that
// industry's template — nothing is written to the database.
export function setPreview(industry: string) {
  try {
    document.cookie = `${PREVIEW_COOKIE}=${encodeURIComponent(industry)}; path=/; max-age=86400; samesite=lax`;
  } catch {
    /* storage blocked — preview just won't persist */
  }
}

export function clearPreview() {
  try {
    document.cookie = `${PREVIEW_COOKIE}=; path=/; max-age=0; samesite=lax`;
  } catch {
    /* ignore */
  }
}

export function PreviewBanner({ label, messages }: { label: string; messages: Messages }) {
  const router = useRouter();
  return (
    <div className="preview-banner" role="status" aria-live="polite">
      <span className="preview-banner-text">
        🎭 <strong>{t(messages, "preview.label", { label })}</strong>
        <span className="preview-banner-note"> · {t(messages, "preview.note")}</span>
      </span>
      <button
        type="button"
        className="preview-banner-reset"
        onClick={() => {
          clearPreview();
          router.refresh();
        }}
      >
        {t(messages, "preview.reset")} ✕
      </button>
    </div>
  );
}
