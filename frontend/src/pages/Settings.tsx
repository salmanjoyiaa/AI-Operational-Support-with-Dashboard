import { Database, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingState } from "../components/LoadingState";
import { api } from "../lib/api";
import type { SettingsRead } from "../types/api";

export function Settings() {
  const [settings, setSettings] = useState<SettingsRead | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getSettings()
      .then(setSettings)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const resetDemo = () => {
    setSaving(true);
    setMessage(null);
    api
      .resetDemo()
      .then((response) => setMessage(response.status))
      .catch((err: Error) => setError(err.message))
      .finally(() => setSaving(false));
  };

  if (loading) return <LoadingState label="Loading settings" />;
  if (error) return <EmptyState title="Settings unavailable" message={error} />;
  if (!settings) return null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-950">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Runtime configuration and demo controls</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-emerald-600" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">AI operations</h2>
          </div>
          <dl className="mt-5 grid gap-4 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="font-medium text-slate-500">Provider</dt>
              <dd className="font-semibold text-slate-900">{settings.ai_provider}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="font-medium text-slate-500">Model</dt>
              <dd className="font-semibold text-slate-900">{settings.groq_model}</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="font-medium text-slate-500">Confidence threshold</dt>
              <dd className="font-semibold text-slate-900">
                {Math.round(settings.ai_confidence_threshold * 100)}%
              </dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="font-medium text-slate-500">KB relevance threshold</dt>
              <dd className="font-semibold text-slate-900">{Math.round(settings.kb_min_relevance * 100)}%</dd>
            </div>
            <div className="flex items-center justify-between gap-4">
              <dt className="font-medium text-slate-500">Review gate</dt>
              <dd className="font-semibold text-emerald-700">
                {settings.human_in_the_loop_enforced ? "Enforced" : "Disabled"}
              </dd>
            </div>
          </dl>
        </section>

        <section className="rounded border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-cyan-600" aria-hidden="true" />
            <h2 className="text-base font-semibold text-slate-950">Demo data</h2>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Reset tickets and knowledge articles to the included portfolio scenario.
          </p>
          <button
            className="focus-ring mt-5 inline-flex items-center justify-center rounded bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:bg-slate-300"
            disabled={saving}
            onClick={resetDemo}
            type="button"
          >
            {saving ? "Resetting" : "Reset demo data"}
          </button>
          {message ? <p className="mt-3 text-sm font-semibold text-emerald-700">{message}</p> : null}
        </section>
      </div>
    </div>
  );
}
