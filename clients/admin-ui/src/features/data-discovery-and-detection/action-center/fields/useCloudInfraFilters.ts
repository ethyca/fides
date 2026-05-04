import { parseAsArrayOf, parseAsString, useQueryState } from "nuqs";

// No default status filter — page settings toggles control ignored/approved visibility
const INITIAL_STATUS_FILTERS: string[] = [];
const INITIAL_LOCATION_FILTERS: string[] = [];
const INITIAL_SERVICE_FILTERS: string[] = [];
const INITIAL_ACCOUNT_FILTERS: string[] = [];

export const useCloudInfraFilters = () => {
  const [statusFilters, setStatusFilters] = useQueryState(
    "statusFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_STATUS_FILTERS),
  );
  const [locationFilters, setLocationFilters] = useQueryState(
    "locationFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_LOCATION_FILTERS),
  );
  const [serviceFilters, setServiceFilters] = useQueryState(
    "serviceFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_SERVICE_FILTERS),
  );
  const [accountFilters, setAccountFilters] = useQueryState(
    "accountFilters",
    parseAsArrayOf(parseAsString).withDefault(INITIAL_ACCOUNT_FILTERS),
  );

  const reset = () => {
    setStatusFilters(INITIAL_STATUS_FILTERS);
    setLocationFilters(INITIAL_LOCATION_FILTERS);
    setServiceFilters(INITIAL_SERVICE_FILTERS);
    setAccountFilters(INITIAL_ACCOUNT_FILTERS);
  };

  return {
    statusFilters,
    setStatusFilters,
    locationFilters,
    setLocationFilters,
    serviceFilters,
    setServiceFilters,
    accountFilters,
    setAccountFilters,
    reset,
  };
};
