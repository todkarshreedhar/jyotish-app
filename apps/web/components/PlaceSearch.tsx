"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useId, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Place } from "@/lib/types";
import { Input } from "./ui";

/** Accessible combobox: type a town, pick it from the list (US-14). */
export function PlaceSearch({ value, onPick, invalid, inputId }: { value: string; onPick: (p: Place) => void; invalid?: boolean; inputId: string }) {
  const t = useTranslations("form");
  const locale = useLocale();
  const [q, setQ] = useState(value);
  const [items, setItems] = useState<Place[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);
  const listId = useId();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const picked = useRef(value);

  useEffect(() => setQ(value), [value]);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (q.trim().length < 2 || q === picked.current) {
      setItems([]);
      return;
    }
    timer.current = setTimeout(async () => {
      setLoading(true);
      try {
        const r = await api<{ items: Place[] }>(`/v1/places/search?q=${encodeURIComponent(q.trim())}&limit=8`);
        setItems(r.items);
        setOpen(true);
        setActive(r.items.length ? 0 : -1);
      } catch {
        setItems([]);
      } finally {
        setLoading(false);
      }
    }, 200);
  }, [q]);

  function pick(p: Place) {
    const label = locale !== "en" && p.name_deva ? `${p.name_deva} (${p.label})` : p.label;
    picked.current = label;
    setQ(label);
    setOpen(false);
    onPick({ ...p, label });
  }

  return (
    <div className="relative">
      <Input
        id={inputId}
        role="combobox"
        aria-expanded={open && items.length > 0}
        aria-controls={open && items.length > 0 ? listId : undefined}
        aria-autocomplete="list"
        aria-activedescendant={open && items.length > 0 && active >= 0 ? `${listId}-${active}` : undefined}
        autoComplete="off"
        placeholder={t("placePlaceholder")}
        value={q}
        invalid={invalid}
        onChange={(e) => setQ(e.target.value)}
        onFocus={() => items.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (!open || !items.length) return;
          if (e.key === "ArrowDown") { e.preventDefault(); setActive((a) => (a + 1) % items.length); }
          if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => (a - 1 + items.length) % items.length); }
          if (e.key === "Enter" && active >= 0) { e.preventDefault(); pick(items[active]); }
          if (e.key === "Escape") setOpen(false);
        }}
      />
      {loading && <span className="absolute right-3 top-3 text-xs text-muted">…</span>}
      {open && items.length > 0 && (
        <ul id={listId} role="listbox" className="absolute z-20 mt-1 max-h-72 w-full overflow-auto rounded-lg border border-border bg-surface shadow-lg">
          {items.map((p, i) => (
            <li
              key={p.id}
              id={`${listId}-${i}`}
              role="option"
              aria-selected={i === active}
              onMouseDown={(e) => { e.preventDefault(); pick(p); }}
              className={`cursor-pointer px-3 py-2 text-sm ${i === active ? "bg-surface-2" : ""}`}
            >
              <span className="font-medium">{p.label}</span>
              {locale !== "en" && p.name_deva && <span className="ml-2 text-muted">{p.name_deva}</span>}
              <span className="block text-xs text-muted">{p.latitude.toFixed(3)}, {p.longitude.toFixed(3)} · {p.tz_name}</span>
            </li>
          ))}
        </ul>
      )}
      {open && !loading && q.trim().length >= 2 && items.length === 0 && q !== picked.current && (
        <p className="mt-1 text-xs text-muted">{t("noPlaces")}</p>
      )}
    </div>
  );
}
