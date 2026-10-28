"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { RequireUser } from "@/components/RequireUser";
import { Alert, Button, Card, Field, Input, Select } from "@/components/ui";
import { api, download, errorText } from "@/lib/api";
import type { ChartSettings, Me } from "@/lib/types";

function Settings({ me }: { me: Me }) {
  const t = useTranslations("settings");
  const qc = useQueryClient();
  const router = useRouter();
  const [name, setName] = useState(me.display_name ?? "");
  const [defs, setDefs] = useState<ChartSettings>(me.default_settings);
  const [saved, setSaved] = useState(false);
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaved(false);
    await api("/v1/me", { method: "PATCH", json: { display_name: name, default_settings: defs } });
    qc.invalidateQueries({ queryKey: ["me"] });
    setSaved(true);
  }

  async function del() {
    try {
      await api("/v1/me", { method: "DELETE", json: { confirm_email: confirm } });
      qc.clear();
      router.push("/");
      router.refresh();
    } catch (e) {
      setError(errorText(e));
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">{t("title")}</h1>
      <Card title={t("account")}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("email")} htmlFor="email"><Input id="email" value={me.email} disabled /></Field>
          <Field label={t("name")} htmlFor="dname"><Input id="dname" value={name} onChange={(e) => setName(e.target.value)} /></Field>
          <div className="flex flex-col gap-1 text-sm"><span className="font-medium">{t("language")}</span><LanguageSwitcher /></div>
        </div>
      </Card>
      <Card title={t("defaults")}>
        <p className="mb-3 text-sm text-muted">{t("defaultsHint")}</p>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={t("ayanamsa")} htmlFor="ay">
            <Select id="ay" value={defs.ayanamsa} onChange={(e) => setDefs({ ...defs, ayanamsa: e.target.value as ChartSettings["ayanamsa"] })}>
              <option value="lahiri">Lahiri (Chitrapaksha)</option>
              <option value="raman">B. V. Raman</option>
              <option value="krishnamurti">Krishnamurti (KP)</option>
              <option value="yukteshwar">Sri Yukteshwar</option>
              <option value="true_chitrapaksha">True Chitrapaksha</option>
            </Select>
          </Field>
          <Field label={t("node")} htmlFor="nd">
            <Select id="nd" value={defs.node_type} onChange={(e) => setDefs({ ...defs, node_type: e.target.value as ChartSettings["node_type"] })}>
              <option value="mean">{t("nodeMean")}</option>
              <option value="true">{t("nodeTrue")}</option>
            </Select>
          </Field>
          <Field label={t("style")} htmlFor="st">
            <Select id="st" value={defs.chart_style} onChange={(e) => setDefs({ ...defs, chart_style: e.target.value as ChartSettings["chart_style"] })}>
              <option value="north">{t("north")}</option>
              <option value="south">{t("south")}</option>
            </Select>
          </Field>
          <Field label={t("dashaYear")} htmlFor="dy">
            <Select id="dy" value={String(defs.dasha_year_days)} onChange={(e) => setDefs({ ...defs, dasha_year_days: Number(e.target.value) as 365.25 | 365.2422 })}>
              <option value="365.25">365.25</option>
              <option value="365.2422">365.2422</option>
            </Select>
          </Field>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <Button onClick={save}>{t("save")}</Button>
          {saved && <span role="status" className="text-sm text-ok">{t("saved")}</span>}
        </div>
      </Card>
      <AlertsCard />
      {me.role !== "user" && <BrandingCard me={me} />}
      <ApiKeysCard />
      <Card title={t("data")}>
        <p className="mb-3 text-sm text-muted">{t("exportHint")}</p>
        <Button variant="secondary" onClick={() => download("/v1/me/export", "jyotish-my-data.json")}>{t("export")}</Button>
      </Card>
      <Card title={t("delete")}>
        <p className="mb-3 text-sm">{t("deleteHint")}</p>
        <div className="flex flex-wrap items-end gap-3">
          <Field label={t("deleteConfirm")} htmlFor="del"><Input id="del" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="off" /></Field>
          <Button variant="danger" disabled={confirm.trim().toLowerCase() !== me.email} onClick={del}>{t("deleteButton")}</Button>
        </div>
        {error && <div className="mt-3"><Alert kind="error">{error}</Alert></div>}
      </Card>
    </div>
  );
}

type AlertPrefs = { dasha_change: boolean; major_transit: boolean; email_enabled: boolean };

function AlertsCard() {
  const t = useTranslations("settings");
  const qc = useQueryClient();
  const { data } = useQuery<AlertPrefs>({ queryKey: ["alerts"], queryFn: () => api("/v1/alerts") });
  if (!data) return null;
  async function set(k: keyof AlertPrefs, v: boolean) {
    const next = { ...data!, [k]: v };
    qc.setQueryData(["alerts"], next);
    await api("/v1/alerts", { method: "PUT", json: next });
  }
  return (
    <Card title={t("alerts")}>
      <p className="mb-2 text-sm text-muted">{t("alertsHint")}</p>
      {(["email_enabled", "dasha_change", "major_transit"] as const).map((k) => (
        <label key={k} className="flex min-h-11 items-center gap-2 text-sm">
          <input type="checkbox" className="h-5 w-5" checked={data[k]} onChange={(e) => set(k, e.target.checked)} /> {t(`alert_${k}`)}
        </label>
      ))}
    </Card>
  );
}

function BrandingCard({ me }: { me: Me }) {
  const t = useTranslations("settings");
  const qc = useQueryClient();
  const [brand, setBrand] = useState(me.brand_name ?? "");
  const [msg, setMsg] = useState<string | null>(null);
  async function save() {
    await api("/v1/me", { method: "PATCH", json: { brand_name: brand } });
    qc.invalidateQueries({ queryKey: ["me"] });
    setMsg(t("saved"));
  }
  async function upload(f: File) {
    const fd = new FormData();
    fd.append("file", f);
    try {
      await api("/v1/me/logo", { method: "POST", body: fd });
      qc.invalidateQueries({ queryKey: ["me"] });
      setMsg(t("logoSaved"));
    } catch (e) {
      setMsg(errorText(e));
    }
  }
  return (
    <Card title={t("branding")}>
      <p className="mb-3 text-sm text-muted">{t("brandingHint")}</p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t("brandName")} htmlFor="bn"><Input id="bn" value={brand} onChange={(e) => setBrand(e.target.value)} /></Field>
        <Field label={t("logo")} htmlFor="logo" hint={t("logoHint")}>
          <Input id="logo" type="file" accept="image/png,image/jpeg" onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
        </Field>
      </div>
      <div className="mt-3 flex items-center gap-3"><Button onClick={save}>{t("save")}</Button>{msg && <span role="status" className="text-sm">{msg}</span>}</div>
    </Card>
  );
}

type Key = { id: string; name: string; prefix: string; created_at: string; revoked_at: string | null; used_today: number; daily_limit: number; key?: string };

function ApiKeysCard() {
  const t = useTranslations("settings");
  const qc = useQueryClient();
  const { data } = useQuery<{ items: Key[] }>({ queryKey: ["keys"], queryFn: () => api("/v1/developer/keys") });
  const [name, setName] = useState("");
  const [fresh, setFresh] = useState<string | null>(null);
  async function create() {
    const k = await api<Key>("/v1/developer/keys", { method: "POST", json: { name } });
    setFresh(k.key ?? null);
    setName("");
    qc.invalidateQueries({ queryKey: ["keys"] });
  }
  async function revoke(id: string) {
    await api(`/v1/developer/keys/${id}`, { method: "DELETE" });
    qc.invalidateQueries({ queryKey: ["keys"] });
  }
  return (
    <Card title={t("apiKeys")}>
      <p className="mb-3 text-sm text-muted">{t("apiKeysHint")}</p>
      {fresh && <Alert kind="ok"><p>{t("keyOnce")}</p><code className="break-all font-mono">{fresh}</code></Alert>}
      <div className="mt-3 flex flex-wrap items-end gap-3">
        <Field label={t("keyName")} htmlFor="kn"><Input id="kn" value={name} onChange={(e) => setName(e.target.value)} /></Field>
        <Button onClick={create} disabled={!name.trim()}>{t("createKey")}</Button>
      </div>
      <ul className="mt-3 flex flex-col gap-2 text-sm">
        {data?.items.map((k) => (
          <li key={k.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border p-2">
            <span><strong>{k.name}</strong> · <code>{k.prefix}…</code> · {t("usage", { used: k.used_today, limit: k.daily_limit })}</span>
            {k.revoked_at ? <span className="text-muted">{t("revoked")}</span> : <Button variant="secondary" onClick={() => revoke(k.id)}>{t("revoke")}</Button>}
          </li>
        ))}
      </ul>
    </Card>
  );
}

export default function SettingsPage() {
  return <RequireUser>{(me) => <Settings me={me} />}</RequireUser>;
}
