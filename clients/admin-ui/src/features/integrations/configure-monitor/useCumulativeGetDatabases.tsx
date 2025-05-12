import { useEffect, useRef, useState } from "react";

import {
  useGetAvailableDatabasesByConnectionQuery,
  useLazyGetAvailableDatabasesByConnectionQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const TIMEOUT_DELAY = 5000;

const EMPTY_RESPONSE = {
  items: [] as string[],
  total: 1,
  page: 1,
  size: 50,
  pages: 0,
};

const useCumulativeGetDatabases = (
  integrationKey: string,
  onTimeout?: () => void,
) => {
  const [nextPage, setNextPage] = useState(2);

  const { data: initialResult, isLoading: initialIsLoading } =
    useGetAvailableDatabasesByConnectionQuery({
      page: 1,
      size: 25,
      connection_config_key: integrationKey,
    });

  const initialLoadingRef = useRef(initialIsLoading);

  const { items: initialDatabases, total: totalDatabases } =
    initialResult ?? EMPTY_RESPONSE;

  const reachedEnd = !!initialResult?.pages && nextPage > initialResult.pages;

  const [databases, setDatabases] = useState<string[]>(initialDatabases);

  useEffect(() => {
    initialLoadingRef.current = initialIsLoading;
    // this needs to be in this hook or else it will be set to [] instead of the actual result
    setDatabases(initialDatabases);
  }, [initialIsLoading, initialDatabases]);

  useEffect(() => {
    const t = setTimeout(() => {
      if (initialLoadingRef.current && onTimeout) {
        onTimeout();
      }
    }, TIMEOUT_DELAY);
    return () => clearTimeout(t);
    // this should only run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const [
    refetchTrigger,
    { isLoading: refetchIsLoading, isFetching: refetchIsFetching },
  ] = useLazyGetAvailableDatabasesByConnectionQuery();

  const isLoading = refetchIsLoading || refetchIsFetching || initialIsLoading;

  const fetchMore = async () => {
    if (reachedEnd) {
      return;
    }
    const result = await refetchTrigger({
      connection_config_key: integrationKey,
      size: 25,
      page: nextPage + 1,
    });
    if (result.isError) {
      return;
    }
    setNextPage(nextPage + 1);
    setDatabases([...databases, ...(result.data?.items ?? [])]);
  };

  return {
    databases,
    totalDatabases,
    fetchMore,
    initialIsLoading,
    isLoading,
    reachedEnd,
  };
};

export default useCumulativeGetDatabases;
