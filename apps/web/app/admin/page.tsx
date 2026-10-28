"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { RequireUser } from "@/components/RequireUser";
import { Alert, Button, Card, Field, Input, Table } from "@/components/ui";
import { api, errorText } from "@/lib/api";

type U = { id: string; email: string; role: string; created_at: string };
type Log = { who: string | null; what: string; target: string | null; reason: string | null; when: string };

/** US-12: support tools. Opening birth details needs a written reason and is logged. */
function Admin() {
  const t = useTranslations("admin");
  const [q, setQ] = useState("");
  const [users, setUsers] = useState<U[]>([]);
  const [sel, setSel] = useState<Record<string, unknown> | null>(null);
  const [reason, setReason] = useState("");
  const [birth, setBirth] = useState<Record<string, unknown>[] | null>(null);
  const [log, setLog] = useState<Log[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function search() {
    setError(null);
    try { setUsers((await api<{ items: U[] }>(`/v1/admin/users?email=${encodeURIComponent(q)}`)).items); } catch (e) { setError(errorText(e)); }
  }
  async function open(id: string) {
    setBirth(null);
    setSel(await api(`/v1/admin/users/${id}`));
    setLog((await api<{ items: Log[] }>(`/v1/admin/audit?user_id=${id}`)).items);
  }
  async function viewBirth() {
    try {
      setBirth((await api<{ items: Record<string, unknown>[] }>(`/v1/admin/users/${sel!.id}/birth-details`, { method: "POST", json: { reason } })).items);
      setLog((await api<{ items: Log[] }>(`/v1/admin/audit?user_id=${sel!.id}`)).items);
    } catch (e) { setError(errorText(e)); }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <Field label={t("email")} htmlFor="aq"><Input id="aq" value={q} onChange={(e) => setQ(e.target.value)} /></Field>
          <Button onClick={search} disabled={q.length < 3}>{t("search")}</Button>
        </div>
        <ul className="mt-3 flex flex-col gap-1 text-sm">
          {users.map((u) => <li key={u.id}><button className="underline" onClick={() => open(u.id)}>{u.email}</button> · {u.role}</li>)}
        </ul>
      </Card>
      {error && <Alert kind="error">{error}</Alert>}
      {sel && (
        <Card title={String(sel.email)}>
          <pre className="overflow-auto rounded bg-surface-2 p-2 text-xs">{JSON.stringify(sel, null, 2)}</pre>
          <div className="mt-3 flex flex-wrap items-end gap-3">
            <Field label={t("reason")} htmlFor="reason" hint={t("reasonHint")}><Input id="reason" value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
            <Button variant="secondary" onClick={viewBirth} disabled={reason.trim().length < 10}>{t("viewBirth")}</Button>
          </div>
          {birth && <pre className="mt-3 overflow-auto rounded bg-surface-2 p-2 text-xs">{JSON.stringify(birth, null, 2)}</pre>}
          <h2 className="mt-4 font-semibold">{t("audit")}</h2>
          <Table caption={t("audit")}>
            <thead><tr><th scope="col">{t("when")}</th><th scope="col">{t("who")}</th><th scope="col">{t("what")}</th><th scope="col">{t("reason")}</th></tr></thead>
            <tbody>{log.map((l, i) => <tr key={i}><td>{new Date(l.when).toLocaleString()}</td><td className="font-mono text-xs">{l.who?.slice(0, 8) ?? "—"}</td><td>{l.what}</td><td>{l.reason ?? ""}</td></tr>)}</tbody>
          </Table>
        </Card>
      )}
    </div>
  );
}

export default function AdminPage() {
  return <RequireUser admin>{() => <Admin />}</RequireUser>;
}
