"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";
import { api, ApiError, errorText } from "@/lib/api";
import type { ChartSettings, Place, ProfileInput } from "@/lib/types";
import { PlaceSearch } from "./PlaceSearch";
import { Alert, Button, Field, Input, Select } from "./ui";

export function isRealDate(ymd: string): boolean {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(ymd);
  if (!m) return false;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const dt = new Date(Date.UTC(y, mo - 1, d));
  return dt.getUTCFullYear() === y && dt.getUTCMonth() === mo - 1 && dt.getUTCDate() === d && y >= 1800 && y <= 2399;
}

function schema(t: (k: string) => string) {
  return z
    .object({
      name: z.string().trim().min(1, t("errName")).max(100),
      birth_date: z.string().refine(isRealDate, t("errDate")),
      birth_time: z.string().regex(/^\d{2}:\d{2}(:\d{2})?$/, t("errTime")),
      time_accuracy: z.enum(["exact", "approximate", "unknown"]),
      mode: z.enum(["search", "manual"]),
      place_name: z.string().optional(),
      latitude: z.coerce.number<number>().min(-90, t("errLat")).max(90, t("errLat")),
      longitude: z.coerce.number<number>().min(-180, t("errLon")).max(180, t("errLon")),
      tz_name: z.string().min(1, t("errTz")),
      gender: z.enum(["", "male", "female", "other"]),
      folder: z.string().max(100).optional(),
      ayanamsa: z.enum(["lahiri", "raman", "krishnamurti", "yukteshwar", "true_chitrapaksha"]),
      node_type: z.enum(["mean", "true"]),
      chart_style: z.enum(["north", "south"]),
      dasha_year_days: z.enum(["365.25", "365.2422"]),
      is_main: z.boolean(),
    })
    .refine((v) => v.mode === "manual" || !!v.place_name, { path: ["place_name"], message: t("errPlace") });
}

export type BirthFormValues = z.infer<ReturnType<typeof schema>>;

export function BirthForm({
  initial,
  defaults,
  onSubmit,
  submitLabel,
  showFolder,
}: {
  initial?: Partial<ProfileInput>;
  defaults: ChartSettings;
  onSubmit: (p: ProfileInput) => Promise<unknown>;
  submitLabel: string;
  showFolder?: boolean;
}) {
  const t = useTranslations("form");
  const [serverError, setServerError] = useState<string | null>(null);
  const [advanced, setAdvanced] = useState(false);
  const s = initial?.settings ?? defaults;
  const {
    register, handleSubmit, control, watch, setValue, setError, formState: { errors, isSubmitting },
  } = useForm<BirthFormValues>({
    resolver: zodResolver(schema(t)),
    defaultValues: {
      name: initial?.name ?? "",
      birth_date: initial?.birth_date ?? "",
      birth_time: initial?.birth_time?.slice(0, 5) ?? "",
      time_accuracy: initial?.time_accuracy ?? "exact",
      mode: initial && !initial.place_name ? "manual" : "search",
      place_name: initial?.place_name ?? "",
      latitude: initial?.latitude ?? ("" as unknown as number),
      longitude: initial?.longitude ?? ("" as unknown as number),
      tz_name: initial?.tz_name ?? "",
      gender: initial?.gender ?? "",
      folder: initial?.folder ?? "",
      ayanamsa: s.ayanamsa,
      node_type: s.node_type,
      chart_style: s.chart_style,
      dasha_year_days: String(s.dasha_year_days) as "365.25" | "365.2422",
      is_main: initial?.is_main ?? false,
    },
  });
  const mode = watch("mode");
  const accuracy = watch("time_accuracy");
  const lat = watch("latitude");
  const lon = watch("longitude");

  // Manual coordinates: look up the time zone automatically.
  useEffect(() => {
    if (mode !== "manual") return;
    const la = Number(lat), lo = Number(lon);
    if (!Number.isFinite(la) || !Number.isFinite(lo) || String(lat) === "" || String(lon) === "") return;
    if (Math.abs(la) > 90 || Math.abs(lo) > 180) return;
    const h = setTimeout(async () => {
      try {
        const r = await api<{ tz_name: string | null }>(`/v1/places/timezone?lat=${la}&lon=${lo}`);
        if (r.tz_name) setValue("tz_name", r.tz_name, { shouldValidate: true });
      } catch { /* user can type it */ }
    }, 300);
    return () => clearTimeout(h);
  }, [mode, lat, lon, setValue]);

  async function submit(v: BirthFormValues) {
    setServerError(null);
    const body: ProfileInput = {
      name: v.name,
      birth_date: v.birth_date,
      birth_time: v.birth_time.length === 5 ? `${v.birth_time}:00` : v.birth_time,
      time_accuracy: v.time_accuracy,
      latitude: Number(v.latitude),
      longitude: Number(v.longitude),
      place_name: v.mode === "search" ? v.place_name || null : null,
      tz_name: v.tz_name,
      utc_offset_minutes: null,
      gender: v.gender || null,
      folder: v.folder || null,
      settings: { ayanamsa: v.ayanamsa, node_type: v.node_type, chart_style: v.chart_style, dasha_year_days: Number(v.dasha_year_days) as 365.25 | 365.2422 },
      is_main: v.is_main,
    };
    try {
      await onSubmit(body);
    } catch (e) {
      if (e instanceof ApiError && Array.isArray(e.detail)) {
        for (const d of e.detail as { loc: string[]; msg: string }[]) {
          const f = d.loc[d.loc.length - 1] as keyof BirthFormValues;
          setError(f, { message: d.msg });
        }
      }
      setServerError(errorText(e));
    }
  }

  const err = (k: keyof BirthFormValues) => errors[k]?.message as string | undefined;

  return (
    <form onSubmit={handleSubmit(submit)} className="flex flex-col gap-5" noValidate>
      <Field label={t("name")} htmlFor="name" error={err("name")}>
        <Input id="name" autoComplete="off" {...register("name")} invalid={!!errors.name} aria-describedby={errors.name ? "name-error" : undefined} />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t("date")} htmlFor="birth_date" error={err("birth_date")} hint={t("dateHint")}>
          <Input id="birth_date" type="date" min="1800-01-01" max="2399-12-31" {...register("birth_date")} invalid={!!errors.birth_date} aria-describedby={errors.birth_date ? "birth_date-error" : "birth_date-hint"} />
        </Field>
        <Field label={t("time")} htmlFor="birth_time" error={err("birth_time")} hint={t("timeHint")}>
          <Input id="birth_time" type="time" step="60" {...register("birth_time")} invalid={!!errors.birth_time} aria-describedby={errors.birth_time ? "birth_time-error" : "birth_time-hint"} />
        </Field>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="text-sm font-medium">{t("accuracy")}</legend>
        <div className="flex flex-wrap gap-3">
          {(["exact", "approximate", "unknown"] as const).map((a) => (
            <label key={a} className="flex min-h-11 items-center gap-2 rounded-lg border border-border px-3">
              <input type="radio" value={a} {...register("time_accuracy")} /> {t(`accuracy_${a}`)}
            </label>
          ))}
        </div>
        {accuracy !== "exact" && <Alert kind="warn">{t("accuracyNote")}</Alert>}
      </fieldset>

      <fieldset className="flex flex-col gap-3">
        <legend className="text-sm font-medium">{t("place")}</legend>
        <div className="flex gap-2" role="radiogroup" aria-label={t("place")}>
          {(["search", "manual"] as const).map((m) => (
            <label key={m} className="flex min-h-11 items-center gap-2 rounded-lg border border-border px-3 text-sm">
              <input type="radio" value={m} {...register("mode")} /> {t(`mode_${m}`)}
            </label>
          ))}
        </div>
        {mode === "search" ? (
          <Field label={t("town")} htmlFor="place" error={err("place_name")} hint={t("townHint")}>
            <Controller
              control={control}
              name="place_name"
              render={({ field }) => (
                <PlaceSearch
                  inputId="place"
                  value={field.value ?? ""}
                  invalid={!!errors.place_name}
                  onPick={(p: Place) => {
                    field.onChange(p.label);
                    setValue("latitude", p.latitude, { shouldValidate: true });
                    setValue("longitude", p.longitude, { shouldValidate: true });
                    setValue("tz_name", p.tz_name, { shouldValidate: true });
                  }}
                />
              )}
            />
          </Field>
        ) : (
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label={t("lat")} htmlFor="latitude" error={err("latitude")} hint={t("latHint")}>
              <Input id="latitude" inputMode="decimal" {...register("latitude")} invalid={!!errors.latitude} />
            </Field>
            <Field label={t("lon")} htmlFor="longitude" error={err("longitude")} hint={t("lonHint")}>
              <Input id="longitude" inputMode="decimal" {...register("longitude")} invalid={!!errors.longitude} />
            </Field>
            <Field label={t("tz")} htmlFor="tz_name" error={err("tz_name")} hint={t("tzHint")}>
              <Input id="tz_name" {...register("tz_name")} invalid={!!errors.tz_name} />
            </Field>
          </div>
        )}
        {mode === "search" && watch("tz_name") && (
          <p className="text-xs text-muted">{Number(lat).toFixed(4)}, {Number(lon).toFixed(4)} · {watch("tz_name")}</p>
        )}
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t("gender")} htmlFor="gender" hint={t("genderHint")}>
          <Select id="gender" {...register("gender")}>
            <option value="">{t("genderNone")}</option>
            <option value="male">{t("male")}</option>
            <option value="female">{t("female")}</option>
            <option value="other">{t("other")}</option>
          </Select>
        </Field>
        {showFolder && (
          <Field label={t("folder")} htmlFor="folder" hint={t("folderHint")}>
            <Input id="folder" {...register("folder")} />
          </Field>
        )}
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="h-5 w-5" {...register("is_main")} /> {t("isMain")}
      </label>

      <div>
        <button type="button" className="text-sm font-medium text-primary underline" aria-expanded={advanced} onClick={() => setAdvanced((a) => !a)}>
          {t("advanced")}
        </button>
        {advanced && (
          <div className="mt-3 grid gap-4 rounded-lg bg-surface-2 p-3 sm:grid-cols-2">
            <Field label={t("ayanamsa")} htmlFor="ayanamsa" hint={t("ayanamsaHint")}>
              <Select id="ayanamsa" {...register("ayanamsa")}>
                <option value="lahiri">Lahiri (Chitrapaksha)</option>
                <option value="raman">B. V. Raman</option>
                <option value="krishnamurti">Krishnamurti (KP)</option>
                <option value="yukteshwar">Sri Yukteshwar</option>
                <option value="true_chitrapaksha">True Chitrapaksha</option>
              </Select>
            </Field>
            <Field label={t("node")} htmlFor="node_type">
              <Select id="node_type" {...register("node_type")}>
                <option value="mean">{t("nodeMean")}</option>
                <option value="true">{t("nodeTrue")}</option>
              </Select>
            </Field>
            <Field label={t("style")} htmlFor="chart_style">
              <Select id="chart_style" {...register("chart_style")}>
                <option value="north">{t("north")}</option>
                <option value="south">{t("south")}</option>
              </Select>
            </Field>
            <Field label={t("dashaYear")} htmlFor="dasha_year_days" hint={t("dashaYearHint")}>
              <Select id="dasha_year_days" {...register("dasha_year_days")}>
                <option value="365.25">365.25</option>
                <option value="365.2422">365.2422</option>
              </Select>
            </Field>
          </div>
        )}
      </div>

      {serverError && <Alert kind="error">{serverError}</Alert>}
      <Button type="submit" busy={isSubmitting} className="self-start">{submitLabel}</Button>
    </form>
  );
}
