import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";

import {
  INFRASTRUCTURE_SYSTEM_FILTERS,
  InfrastructureSystemFilterLabel,
} from "../constants";

// Stable default references to prevent infinite re-renders
const DEFAULT_STATUS_FILTERS: InfrastructureSystemFilterLabel[] = [];
const DEFAULT_VENDOR_FILTERS: string[] = [];

export const useInfrastructureSystemsFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(
      parseAsStringLiteral(INFRASTRUCTURE_SYSTEM_FILTERS),
    ).withDefault(DEFAULT_STATUS_FILTERS),
  );
  const [vendorFilters, setVendorFilters] = useQueryState(
    "vendorFilters",
    parseAsArrayOf(parseAsString).withDefault(DEFAULT_VENDOR_FILTERS),
  );

  const reset = () => {
    setStatusFilters([]);
    setVendorFilters([]);
  };

  return {
    statusFilters,
    setStatusFilters,
    vendorFilters,
    setVendorFilters,
    reset,
  };
};
