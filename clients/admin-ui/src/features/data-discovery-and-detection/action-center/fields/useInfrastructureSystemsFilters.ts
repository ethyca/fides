import { parseAsArrayOf, parseAsString, useQueryState } from "nuqs";

import { DiffStatus } from "~/types/api/models/DiffStatus";

// Initial default values for "New" filter
const INITIAL_STATUS_FILTERS = [DiffStatus.ADDITION];
const INITIAL_VENDOR_FILTERS: string[] = [];
const DEFAULT_DATA_USES_FILTERS: string[] = [];

export const useInfrastructureSystemsFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_STATUS_FILTERS),
  );
  const [vendorFilters, setVendorFilters] = useQueryState(
    "vendorFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_VENDOR_FILTERS),
  );
  const [dataUsesFilters, setDataUsesFilters] = useQueryState(
    "dataUsesFilters",
    parseAsArrayOf(parseAsString).withDefault(DEFAULT_DATA_USES_FILTERS),
  );

  const reset = () => {
    setStatusFilters([]);
    setVendorFilters([]);
    setDataUsesFilters([]);
  };

  return {
    statusFilters,
    setStatusFilters,
    vendorFilters,
    setVendorFilters,
    dataUsesFilters,
    setDataUsesFilters,
    reset,
  };
};
