"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { api, ApiError } from "./api";
import type { Chart, Me, Names, Panchang, Profile, ProfileInput, Report, Strength, Transits, VargaCode } from "./types";

export function useMe() {
  return useQuery<Me | null>({
    queryKey: ["me"],
    queryFn: async () => {
      try {
        return await api<Me>("/v1/me");
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) return null;
        throw e;
      }
    },
    staleTime: 60_000,
  });
}

export function useConfig() {
  return useQuery<{ google_enabled: boolean; consent_version: string; version: string; environment: string }>({
    queryKey: ["config"],
    queryFn: () => api("/v1/config"),
    staleTime: Infinity,
  });
}

export function useNames() {
  const locale = useLocale();
  return useQuery<Names>({ queryKey: ["names", locale], queryFn: () => api(`/v1/names?lang=${locale}`), staleTime: Infinity });
}

export function useProfiles() {
  return useQuery<{ items: Profile[]; count: number; limit: number; folders: string[] }>({
    queryKey: ["profiles"],
    queryFn: () => api("/v1/profiles"),
  });
}

export function useProfile(id: string) {
  return useQuery<Profile>({ queryKey: ["profile", id], queryFn: () => api(`/v1/profiles/${id}`) });
}

export function useChart(id: string, vargas: VargaCode[], bhavaChalit = false) {
  const v = [...new Set(["D1", "D9", ...vargas])].join(",");
  return useQuery<Chart>({
    queryKey: ["chart", id, v, bhavaChalit],
    queryFn: () => api(`/v1/profiles/${id}/chart?vargas=${v}&bhava_chalit=${bhavaChalit}`),
    staleTime: 5 * 60_000,
  });
}

export function useReadings(id: string) {
  const locale = useLocale();
  return useQuery<{ ruleset_version: string; readings: import("./types").Reading[] }>({
    queryKey: ["readings", id, locale],
    queryFn: () => api(`/v1/profiles/${id}/readings?lang=${locale}`),
  });
}

export function useTransits(id: string, on: string) {
  return useQuery<Transits>({ queryKey: ["transits", id, on], queryFn: () => api(`/v1/profiles/${id}/transits?on=${on}`) });
}

export function useStrength(id: string, enabled = true) {
  return useQuery<Strength>({ queryKey: ["strength", id], queryFn: () => api(`/v1/profiles/${id}/strength`), enabled });
}

export function usePanchang(on: string, lat: number | null, lon: number | null, tz: string | null) {
  return useQuery<Panchang>({
    queryKey: ["panchang", on, lat, lon, tz],
    queryFn: () => api(`/v1/panchang?on=${on}&lat=${lat}&lon=${lon}${tz ? `&tz=${encodeURIComponent(tz)}` : ""}`),
    enabled: lat !== null && lon !== null,
    staleTime: 60 * 60_000,
  });
}

export function useReports() {
  return useQuery<{ items: Report[] }>({
    queryKey: ["reports"],
    queryFn: () => api("/v1/reports"),
    refetchInterval: (q) => (q.state.data?.items.some((r) => r.status === "queued" || r.status === "running") ? 2000 : false),
  });
}

export function useSaveProfile(id?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ProfileInput) =>
      id ? api<Profile>(`/v1/profiles/${id}`, { method: "PUT", json: body }) : api<Profile>("/v1/profiles", { method: "POST", json: body }),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ["profiles"] });
      qc.invalidateQueries({ queryKey: ["profile", p.id] });
      qc.invalidateQueries({ queryKey: ["chart", p.id] });
      qc.invalidateQueries({ queryKey: ["readings", p.id] });
      qc.invalidateQueries({ queryKey: ["transits", p.id] });
      qc.invalidateQueries({ queryKey: ["strength", p.id] });
    },
  });
}
