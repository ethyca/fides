import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";
import { useEffect } from "react";

import { INFRASTRUCTURE_SYSTEM_FILTERS } from "../constants/InfrastructureSystemsFilters.const";

export const useInfrastructureSystemsFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(parseAsStringLiteral(INFRASTRUCTURE_SYSTEM_FILTERS)),
  );
  const [vendorFilters, setVendorFilters] = useQueryState(
    "vendorFilters",
    parseAsArrayOf(parseAsString),
  );

  // Set initial state: no filters selected by default
  useEffect(() => {
    if (statusFilters === null) {
      setStatusFilters([]);
    }
    if (vendorFilters === null) {
      setVendorFilters([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const resetToInitialState = () => {
    setStatusFilters([]);
    setVendorFilters([]);
  };

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
    resetToInitialState,
  };
};
