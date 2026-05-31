import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { getPosts, getSite } from "@/lib/api";

export async function generateMetadata(): Promise<Metadata> {
  const site = await getSite();
  return {
    title: "Blog",
    description: `Daily ${site.industry} essays for ${site.audience}.`
  };
}

export default async function BlogIndexPage() {
  const [site, posts] = await Promise.all([getSite(), getPosts()]);
  return (
    <main className="main">
      <header className="page-header">
        <p className="kicker">Blog</p>
        <h1>Writing &amp; updates</h1>
        <p className="lede">Daily {site.industry} essays for {site.audience}.</p>
      </header>
      {posts.length ? (
        <div className="grid">
          {posts.map((post) => (
            <Link className="post-card" href={`/blog/${post.slug}`} key={post.id}>
              <h3>{post.title}</h3>
              <p>{post.excerpt}</p>
              {post.tags?.length ? (
                <div className="tags">
                  {post.tags.map((tag) => (
                    <span className="tag" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
              <span className="button ghost">
                Read <ArrowRight size={16} />
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className="post-card">
          <h3>No posts yet</h3>
          <p>New articles will appear here as they are published.</p>
        </div>
      )}
    </main>
  );
}
