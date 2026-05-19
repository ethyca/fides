import { useEffect, useMemo, useState } from "react";

import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { MOCK_SYSTEM_RESOURCES } from "./mockResources";

export interface PaginatedResources {
  items: CloudInfraStagedResource[];
  total: number;
  pages: number;
  page: number;
  size: number;
}

interface UseMockSystemResourcesArgs {
  search: string;
  service: string;
  region: string;
  page: number;
  size: number;
}

const matchesSearch = (
  resource: CloudInfraStagedResource,
  search: string,
): boolean => {
  if (!search) {
    return true;
  }
  const needle = search.toLowerCase();
  if (resource.name?.toLowerCase().includes(needle)) {
    return true;
  }
  if (resource.source_id.toLowerCase().includes(needle)) {
    return true;
  }
  if (resource.tags) {
    return Object.entries(resource.tags).some(
      ([k, v]) =>
        k.toLowerCase().includes(needle) || v.toLowerCase().includes(needle),
    );
  }
  return false;
};

export const useMockSystemResources = ({
  search,
  service,
  region,
  page,
  size,
}: UseMockSystemResourcesArgs) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isFetching, setIsFetching] = useState(true);

  useEffect(() => {
    setIsFetching(true);
    const timer = setTimeout(() => {
      setIsLoading(false);
      setIsFetching(false);
    }, 250);
    return () => clearTimeout(timer);
  }, [search, service, region, page, size]);

  const data = useMemo<PaginatedResources>(() => {
    const filtered = MOCK_SYSTEM_RESOURCES.filter(
      (r) =>
        matchesSearch(r, search) &&
        (service === "all" || r.service === service) &&
        (region === "all" || r.location === region),
    );
    const total = filtered.length;
    const pages = Math.max(1, Math.ceil(total / size));
    const safePage = Math.min(Math.max(1, page), pages);
    const start = (safePage - 1) * size;
    const items = filtered.slice(start, start + size);
    return { items, total, pages, page: safePage, size };
  }, [search, service, region, page, size]);

  return { data, isLoading, isFetching };
};
