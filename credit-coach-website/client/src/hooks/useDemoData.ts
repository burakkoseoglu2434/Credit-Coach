import { useQuery } from "@tanstack/react-query";

import { fetchJson } from "@/lib/api";
import type { DemoIndex } from "@shared/demo-schema";

type DemoPayload<T = unknown> = {
  slug: string;
  title: string;
  category: string;
  summary: string;
  type: "json" | "markdown";
  content: T;
};

export function useDemoIndex() {
  return useQuery({
    queryKey: ["demo-index"],
    queryFn: () => fetchJson<DemoIndex>("/api/demo/index"),
  });
}

export function useDemoItem<T = unknown>(slug: string) {
  return useQuery({
    queryKey: ["demo-item", slug],
    queryFn: () => fetchJson<DemoPayload<T>>(`/api/demo/${slug}`),
  });
}
