import { Plus, RefreshCw } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { Badge } from "../components/Badge";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import type { KnowledgeArticle } from "../types/api";

const initialForm = {
  title: "",
  category: "technical",
  content: "",
  source_url: ""
};

export function KnowledgeBase() {
  const [articles, setArticles] = useState<KnowledgeArticle[]>([]);
  const [form, setForm] = useState(initialForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadArticles = () => {
    setLoading(true);
    api
      .getArticles()
      .then(setArticles)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadArticles();
  }, []);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setError(null);
    api
      .createArticle({
        title: form.title,
        category: form.category,
        content: form.content,
        source_url: form.source_url || undefined
      })
      .then(() => {
        setForm(initialForm);
        loadArticles();
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-950">Knowledge Base</h1>
          <p className="mt-1 text-sm text-slate-500">Source articles used for semantic retrieval</p>
        </div>
        <button
          className="focus-ring inline-flex items-center justify-center gap-2 rounded border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-white"
          onClick={loadArticles}
          type="button"
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" />
          Refresh
        </button>
      </div>

      <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
        <form className="grid gap-4 lg:grid-cols-[1fr_220px]" onSubmit={handleSubmit}>
          <input
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm"
            placeholder="Article title"
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
            required
          />
          <select
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm"
            value={form.category}
            onChange={(event) => setForm({ ...form, category: event.target.value })}
          >
            {["billing", "refund", "technical", "account", "sales", "other"].map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <input
            className="focus-ring rounded border border-slate-300 px-3 py-2 text-sm lg:col-span-2"
            placeholder="Source URL"
            value={form.source_url}
            onChange={(event) => setForm({ ...form, source_url: event.target.value })}
          />
          <textarea
            className="focus-ring min-h-32 rounded border border-slate-300 px-3 py-2 text-sm lg:col-span-2"
            placeholder="Article content"
            value={form.content}
            onChange={(event) => setForm({ ...form, content: event.target.value })}
            required
          />
          <div className="lg:col-span-2">
            <button
              className="focus-ring inline-flex items-center justify-center gap-2 rounded bg-cyan-600 px-4 py-2 text-sm font-semibold text-white hover:bg-cyan-700 disabled:bg-slate-300"
              disabled={saving}
              type="submit"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Add article
            </button>
          </div>
        </form>
        {error ? <p className="mt-3 text-sm font-medium text-rose-600">{error}</p> : null}
      </section>

      {loading ? (
        <LoadingState label="Loading articles" />
      ) : articles.length ? (
        <div className="grid gap-4 lg:grid-cols-2">
          {articles.map((article) => (
            <article key={article.id} className="rounded border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-slate-950">{article.title}</h2>
                  <p className="mt-1 text-sm text-slate-500">{article.source_url ?? "Internal source"}</p>
                </div>
                <Badge value={article.category} tone="purple" />
              </div>
              <p className="mt-4 max-h-32 overflow-hidden text-sm leading-6 text-slate-600">{article.content}</p>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No articles" message="Create an article to make retrieval available." />
      )}
    </div>
  );
}
