import {
  parseAsArrayOf,
  parseAsString,
  parseAsStringLiteral,
  useQueryState,
} from "nuqs";

import { INFRASTRUCTURE_SYSTEM_FILTERS } from "../constants";

export const useInfrastructureSystemsFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(
      parseAsStringLiteral(INFRASTRUCTURE_SYSTEM_FILTERS),
    ).withDefault([]),
  );
  const [vendorFilters, setVendorFilters] = useQueryState(
    "vendorFilters",
    parseAsArrayOf(parseAsString).withDefault([]),
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
