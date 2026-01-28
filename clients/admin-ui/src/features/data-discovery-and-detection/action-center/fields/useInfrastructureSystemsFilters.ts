import { parseAsArrayOf, parseAsString, useQueryState } from "nuqs";

// Stable default references to prevent infinite re-renders
const DEFAULT_STATUS_FILTERS: string[] = [];
const DEFAULT_VENDOR_FILTERS: string[] = [];
const DEFAULT_DATA_USES_FILTERS: string[] = [];

export const useInfrastructureSystemsFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(parseAsString).withDefault(DEFAULT_STATUS_FILTERS),
  );
  const [vendorFilters, setVendorFilters] = useQueryState(
    "vendorFilters",
    parseAsArrayOf(parseAsString).withDefault(DEFAULT_VENDOR_FILTERS),
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
