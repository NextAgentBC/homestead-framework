import { getMessages } from "./api";

export const LOCALES = (process.env.NEXT_PUBLIC_SITE_LOCALES || "en,zh")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
export const DEFAULT_LOCALE = process.env.NEXT_PUBLIC_DEFAULT_LOCALE || LOCALES[0] || "en";

export function isLocale(value?: string): boolean {
  return !!value && LOCALES.includes(value);
}
export function normalizeLocale(value?: string): string {
  return isLocale(value) ? (value as string) : DEFAULT_LOCALE;
}
export function langLabel(locale: string): string {
  const labels: Record<string, string> = { en: "EN", zh: "中文" };
  return labels[locale] || locale.toUpperCase();
}

// Build canonical + hreflang alternates for a locale-agnostic path (e.g. "",
// "/blog", "/blog/my-post"). Used in each page's generateMetadata for SEO.
export function alternatesFor(locale: string, path: string) {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || "").replace(/\/$/, "");
  const languages: Record<string, string> = {};
  for (const l of LOCALES) languages[l] = `${base}/${l}${path}`;
  return { canonical: `${base}/${locale}${path}`, languages };
}

export type Messages = Record<string, string>;

// Built-in chrome strings. Chinese works out of the box; the API UiMessages
// catalog (editable by the agent) overlays/overrides these per locale.
const EN: Messages = {
  "nav.blog": "Blog",
  "nav.contact": "Contact",
  "nav.menu": "Menu",
  "home.latest": "Latest",
  "home.read": "Read",
  "home.noPosts": "No posts yet",
  "home.noPostsBody": "New articles will appear here as they are published.",
  "home.newsletterKicker": "Newsletter",
  "home.newsletterTitle": "Stay in the loop",
  "newsletter.placeholder": "you@example.com",
  "newsletter.button": "Subscribe",
  "newsletter.subscribing": "Subscribing...",
  "newsletter.subscribed": "Subscribed. Check your inbox if email is configured.",
  "newsletter.failed": "Subscription failed. Check the API logs.",
  "newsletter.emailAria": "Email address",
  "blog.kicker": "Blog",
  "blog.title": "Writing & updates",
  "blog.lede": "Daily {industry} essays for {audience}.",
  "blog.empty": "No posts yet",
  "blog.read": "Read",
  "contact.kicker": "Contact",
  "contact.title": "Get in touch",
  "contact.lede": "Questions, ideas, or want to work together? Send a message and we'll get back to you.",
  "contact.responseTitle": "Response time",
  "contact.responseBody": "We usually reply within a day or two.",
  "contact.newsletterTitle": "Newsletter",
  "contact.newsletterBody": "Prefer updates? Subscribe from the home page.",
  "contact.blogTitle": "Blog",
  "contact.blogBody": "Read the latest on the blog.",
  "contactForm.emailPlaceholder": "you@example.com",
  "contactForm.messagePlaceholder": "Message",
  "contactForm.send": "Send",
  "contactForm.sending": "Sending...",
  "contactForm.sent": "Message sent.",
  "contactForm.failed": "Message failed. Check API configuration.",
  "footer.pages": "Pages",
  "footer.more": "More",
  "footer.blog": "Blog",
  "footer.contact": "Contact",
  "footer.tagline": "{industry} site built on the Homestead framework — Next.js, Flask, Cloudflare.",
  "meta.blog": "Blog",
  "meta.contact": "Contact"
};

const ZH: Messages = {
  "nav.blog": "博客",
  "nav.contact": "联系",
  "nav.menu": "菜单",
  "home.latest": "最新",
  "home.read": "阅读",
  "home.noPosts": "暂无文章",
  "home.noPostsBody": "文章发布后将显示在这里。",
  "home.newsletterKicker": "订阅",
  "home.newsletterTitle": "保持关注",
  "newsletter.placeholder": "you@example.com",
  "newsletter.button": "订阅",
  "newsletter.subscribing": "订阅中…",
  "newsletter.subscribed": "已订阅。如已配置邮箱，请查收。",
  "newsletter.failed": "订阅失败，请检查 API 日志。",
  "newsletter.emailAria": "电子邮箱",
  "blog.kicker": "博客",
  "blog.title": "文章与动态",
  "blog.lede": "为{audience}带来每日{industry}内容。",
  "blog.empty": "暂无文章",
  "blog.read": "阅读",
  "contact.kicker": "联系",
  "contact.title": "与我们联系",
  "contact.lede": "有问题、想法，或想合作？给我们留言，我们会尽快回复。",
  "contact.responseTitle": "回复时间",
  "contact.responseBody": "我们通常在一到两天内回复。",
  "contact.newsletterTitle": "订阅",
  "contact.newsletterBody": "想收到更新？请在首页订阅。",
  "contact.blogTitle": "博客",
  "contact.blogBody": "在博客上阅读最新内容。",
  "contactForm.emailPlaceholder": "you@example.com",
  "contactForm.messagePlaceholder": "留言",
  "contactForm.send": "发送",
  "contactForm.sending": "发送中…",
  "contactForm.sent": "已发送。",
  "contactForm.failed": "发送失败，请检查 API 配置。",
  "footer.pages": "页面",
  "footer.more": "更多",
  "footer.blog": "博客",
  "footer.contact": "联系",
  "footer.tagline": "基于 Homestead 框架构建的{industry}网站 —— Next.js、Flask、Cloudflare。",
  "meta.blog": "博客",
  "meta.contact": "联系"
};

const BUILTIN: Record<string, Messages> = { en: EN, zh: ZH };

export async function loadMessages(locale: string): Promise<Messages> {
  const base = BUILTIN[locale] || BUILTIN[DEFAULT_LOCALE] || EN;
  const api = await getMessages(locale); // agent-editable overrides
  return { ...base, ...api };
}

export function t(messages: Messages, key: string, vars?: Record<string, string | number>): string {
  let value = messages[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      value = value.split(`{${k}}`).join(String(v));
    }
  }
  return value;
}
