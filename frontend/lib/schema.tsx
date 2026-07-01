// Shared JSON-LD builders. Pure functions — callers fetch the data and pass it
// in. Rendered through the same inline <script type="application/ld+json">
// pattern the blog detail page already uses, so no new dependency is needed.
import type { Nap, Site } from "./api";

export type JsonLd = Record<string, unknown>;

// Drop empty values ("" / null / undefined / []) so unset NAP fields never
// emit empty JSON-LD properties, which structured-data validators flag.
function prune(obj: JsonLd): JsonLd {
  const out: JsonLd = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined || value === null || value === "") continue;
    if (Array.isArray(value) && value.length === 0) continue;
    out[key] = value;
  }
  return out;
}

function cityList(areas: string[]): { "@type": "City"; name: string }[] {
  return (areas || []).filter(Boolean).map((a) => ({ "@type": "City", name: a }));
}

// Site-level LocalBusiness node, rendered once per page (from the layout).
// Other nodes reference it by @id instead of duplicating the NAP.
//
// Deliberately NO aggregateRating / review here: Google's structured-data
// policy forbids self-serving reviews (ratings a business marks up about
// itself on its own site), and we have no real review data. Do not "help"
// by adding placeholder ratings — fake review markup risks a manual action.
export function localBusinessJsonLd(
  site: Site,
  nap: Nap,
  opts?: { areaServedOverride?: string[]; url?: string }
): JsonLd {
  const address = prune({
    "@type": "PostalAddress",
    streetAddress: nap.street,
    addressLocality: nap.city,
    addressRegion: nap.region,
    postalCode: nap.postalCode,
    addressCountry: nap.country
  });
  return prune({
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "@id": `${site.url}#business`,
    name: nap.legalName || site.name,
    telephone: nap.phone,
    email: nap.email,
    // Omit the address wrapper entirely when every field is unset ("@type" alone remains).
    address: Object.keys(address).length > 1 ? address : undefined,
    // Geo only when both coordinates are actually set — a lone lat is meaningless.
    geo:
      nap.latitude !== null && nap.longitude !== null
        ? { "@type": "GeoCoordinates", latitude: nap.latitude, longitude: nap.longitude }
        : undefined,
    openingHoursSpecification: (nap.hours || []).map((h) =>
      prune({ "@type": "OpeningHoursSpecification", dayOfWeek: h.day, opens: h.opens, closes: h.closes })
    ),
    areaServed: cityList(opts?.areaServedOverride ?? nap.serviceAreas),
    url: opts?.url || site.url
  });
}

// One Service node per real service; provider references the LocalBusiness @id.
export function serviceJsonLd(
  site: Site,
  nap: Nap,
  { serviceType, description, areaServed, url }: { serviceType: string; description: string; areaServed?: string[]; url: string }
): JsonLd {
  return prune({
    "@context": "https://schema.org",
    "@type": "Service",
    serviceType,
    name: serviceType,
    description,
    provider: { "@id": `${site.url}#business` },
    areaServed: cityList(areaServed ?? nap.serviceAreas),
    url
  });
}

// FAQPage from a faq block's {q, a} items. Returns null when nothing usable —
// callers can push results straight into renderJsonLdScripts.
export function faqPageJsonLd(items: { q?: string; a?: string }[]): JsonLd | null {
  const pairs = (items || []).filter((item) => (item.q || "").trim() && (item.a || "").trim());
  if (!pairs.length) return null;
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: pairs.map((item) => ({
      "@type": "Question",
      name: item.q,
      acceptedAnswer: { "@type": "Answer", text: item.a }
    }))
  };
}

export function breadcrumbJsonLd(crumbs: { name: string; url: string }[]): JsonLd {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: crumbs.map((crumb, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: crumb.name,
      item: crumb.url
    }))
  };
}

// One <script> per node (instead of a combined @graph) so each block can be
// pasted into the Rich Results Test / validator.schema.org independently.
export function renderJsonLdScripts(nodes: (JsonLd | null | undefined)[]): React.ReactElement[] {
  return nodes
    .filter((node): node is JsonLd => Boolean(node))
    .map((node, i) => (
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(node) }} key={i} />
    ));
}
