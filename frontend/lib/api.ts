export type Site = {
  name: string;
  url: string;
  industry: string;
  audience: string;
  region: string;
  googleClientId: string;
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
      link: "#356b9f"
    },
    typography: {
      body: "Arial, Helvetica, sans-serif",
      heading: "Arial, Helvetica, sans-serif",
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
  notes: "Fallback design profile."
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

type NextRequestInit = RequestInit & { next?: { revalidate?: number } };

async function fetchJson<T>(path: string, init?: NextRequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    next: { revalidate: 300 }
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function getSite(): Promise<Site> {
  try {
    const data = await fetchJson<{ item: Site }>("/site");
    return data.item;
  } catch {
    return {
      name: "Oracle Site",
      url: process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
      industry: "education",
      audience: "students and independent creators",
      region: "United States",
      googleClientId: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ""
    };
  }
}

export async function getPosts(): Promise<BlogPost[]> {
  try {
    const data = await fetchJson<{ items: BlogPost[] }>("/blogs");
    return data.items;
  } catch {
    return [];
  }
}

export async function getDesign(): Promise<DesignProfile> {
  try {
    const data = await fetchJson<{ item: DesignProfile }>("/design");
    return data.item;
  } catch {
    return fallbackDesign;
  }
}

export async function getPost(slug: string): Promise<BlogPost | null> {
  try {
    const data = await fetchJson<{ item: BlogPost }>(`/blogs/${slug}`);
    return data.item;
  } catch {
    return null;
  }
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  return fetchJson<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    cache: "no-store"
  });
}
