export type Site = {
  name: string;
  url: string;
  industry: string;
  audience: string;
  region: string;
  googleClientId: string;
  locales: string[];
  defaultLocale: string;
};

export type BlogPost = {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  bodyMarkdown?: string;
  tags: string[];
  author: string;
  publishedAt: string | null;
  metaTitle: string;
  metaDescription: string;
  canonicalUrl: string;
  geoRegion: string;
};

export type SitePage = {
  id: number;
  title: string;
  slug: string;
  navLabel: string;
  navOrder: number;
  showInNav: boolean;
  bodyMarkdown?: string;
  metaTitle: string;
  metaDescription: string;
  canonicalUrl?: string;
  status?: string;
  publishedAt?: string | null;
  sections?: Section[];
};

export type SectionCta = { label: string; href: string };

export type SectionLayout = {
  columns?: number;
  align?: "left" | "center";
  media?: "none" | "left" | "right" | "top";
  tone?: "plain" | "tint" | "inverse";
};

export type Section = {
  type: string;
  variant?: string;
  content?: {
    kicker?: string;
    eyebrow?: string;
    badge?: string;
    headline?: string;
    headlineAccent?: string;
    subhead?: string;
    cta?: SectionCta;
    secondaryCta?: SectionCta;
    heading?: string;
    text?: string;
    icon?: string;
    layout?: SectionLayout;
    left?: { title?: string; items?: string[] };
    right?: { title?: string; items?: string[] };
    items?: {
      kind?: string;
      icon?: string;
      title?: string;
      body?: string;
      caption?: string;
      value?: string;
      label?: string;
      quote?: string;
      author?: string;
      role?: string;
      name?: string;
      price?: string;
      period?: string;
      features?: string[];
      featured?: boolean;
      q?: string;
      a?: string;
      image?: string;
      href?: string;
      cta?: SectionCta;
    }[];
  };
};

export type DesignProfile = {
  name: string;
  source: string;
  industry: string;
  personality: string;
  competitorUrls: string[];
  tokens: {
    colors: {
      ink: string;
      muted: string;
      paper: string;
      surface: string;
      line: string;
      primary: string;
      accent: string;
      highlight: string;
      link: string;
      surfaceInverse: string;
      inkInverse: string;
      onPrimary: string;
    };
    typography: {
      body: string;
      heading: string;
      mono: string;
    };
    radius: {
      card: string;
      control: string;
      pill: string;
    };
    layout: {
      contentMaxWidth: string;
      heroMinHeight: string;
      density: string;
      cardPadding: string;
      sectionGap: string;
    };
  };
  voice: {
    headlineStyle: string;
    tone: string;
  };
  notes: string;
  sections?: Section[];
  availableLocales?: string[];
};

export const fallbackDesign: DesignProfile = {
  name: "Editorial Operator",
  source: "fallback",
  industry: "education",
  personality: "clear, useful, trustworthy, modern",
  competitorUrls: [],
  tokens: {
    colors: {
      ink: "#18211f",
      muted: "#66736f",
      paper: "#faf8f3",
      surface: "#ffffff",
      line: "#d9dfd7",
      primary: "#216e5f",
      accent: "#b54945",
      highlight: "#c79b3b",
      link: "#356b9f",
      surfaceInverse: "#0b0f1a",
      inkInverse: "#f6f9ff",
      onPrimary: "#ffffff"
    },
    typography: {
      body: "var(--font-sans), system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      heading: "var(--font-sans), system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      mono: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
    },
    radius: {
      card: "8px",
      control: "8px",
      pill: "999px"
    },
    layout: {
      contentMaxWidth: "1120px",
      heroMinHeight: "58vh",
      density: "comfortable",
      cardPadding: "20px",
      sectionGap: "54px"
    }
  },
  voice: {
    headlineStyle: "plain offer or brand name",
    tone: "practical and calm"
  },
  notes: "Fallback design profile.",
  sections: []
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

type NextRequestInit = RequestInit & { next?: { revalidate?: number } };

async function fetchJson<T>(path: string, init?: NextRequestInit): Promise<T> {
  const { next, cache, headers, ...rest } = init ?? {};
  // Respect a per-call caching choice; otherwise default to ISR revalidate=300.
  // (Avoid no-store in the root layout — it forces build-time prerender to fetch and can hang the build.)
  const caching = cache ? { cache } : { next: next ?? { revalidate: 300 } };
  const response = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...((headers as Record<string, string>) || {})
    },
    ...caching
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

// Append ?locale= only for a non-empty locale; the backend treats the default
// or an unknown locale as the base content, so this stays harmless either way.
function localeQuery(locale?: string): string {
  return locale ? `?locale=${encodeURIComponent(locale)}` : "";
}

export async function getSite(): Promise<Site> {
  try {
    // no-store: site name / locales / config must reflect changes immediately,
    // like design + content (the layout is force-dynamic, so this is safe).
    const data = await fetchJson<{ item: Site }>("/site", { cache: "no-store" });
    return data.item;
  } catch {
    return {
      name: "Oracle Site",
      url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
      industry: "education",
      audience: "students and independent creators",
      region: "United States",
      googleClientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
      locales: (process.env.NEXT_PUBLIC_SITE_LOCALES || "en,zh").split(",").map((s) => s.trim()).filter(Boolean),
      defaultLocale: process.env.NEXT_PUBLIC_DEFAULT_LOCALE || "en"
    };
  }
}

export async function getPosts(locale?: string): Promise<BlogPost[]> {
  try {
    const data = await fetchJson<{ items: BlogPost[] }>(`/blogs${localeQuery(locale)}`, { cache: "no-store" });
    return data.items;
  } catch {
    return [];
  }
}

export async function getDesign(locale?: string): Promise<DesignProfile> {
  try {
    // no-store: applying a style preset / editing the design must reflect immediately.
    const data = await fetchJson<{ item: DesignProfile }>(`/design${localeQuery(locale)}`, { cache: "no-store" });
    return data.item;
  } catch {
    return fallbackDesign;
  }
}

export async function getPost(slug: string, locale?: string): Promise<BlogPost | null> {
  try {
    // no-store: editing/translating a post must reflect immediately (matches getPage/getPosts).
    const data = await fetchJson<{ item: BlogPost }>(`/blogs/${slug}${localeQuery(locale)}`, { cache: "no-store" });
    return data.item;
  } catch {
    return null;
  }
}

export async function getPages(locale?: string): Promise<SitePage[]> {
  try {
    // no-store + the layout's force-dynamic: the nav always reflects currently
    // published pages, so a new page shows in the menu immediately.
    const data = await fetchJson<{ items: SitePage[] }>(`/pages${localeQuery(locale)}`, { cache: "no-store" });
    return data.items;
  } catch {
    return [];
  }
}

export async function getPage(slug: string, locale?: string): Promise<SitePage | null> {
  try {
    const data = await fetchJson<{ item: SitePage }>(`/pages/${slug}${localeQuery(locale)}`, { cache: "no-store" });
    return data.item;
  } catch {
    return null;
  }
}

export async function getMessages(locale: string): Promise<Record<string, string>> {
  try {
    const data = await fetchJson<{ item: { messages: Record<string, string> } }>(`/i18n/${locale}`, { cache: "no-store" });
    return data.item.messages || {};
  } catch {
    return {};
  }
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  return fetchJson<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    cache: "no-store"
  });
}
