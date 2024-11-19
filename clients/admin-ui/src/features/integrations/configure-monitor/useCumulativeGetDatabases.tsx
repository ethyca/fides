import { useMemo, useState } from "react";

import {
  useGetDatabasesByConnectionQuery,
  useLazyGetDatabasesByConnectionQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const EMPTY_RESPONSE = {
  items: [] as string[],
  total: 1,
  page: 1,
  size: 50,
  pages: 0,
};

const useCumulativeGetDatabases = (integrationKey: string) => {
  const [showLongLoadingMessage, setShowLongLoadingMessage] = useState(false);

  const [nextPage, setNextPage] = useState(2);
  const { data: initialResult, isLoading: initialIsLoading } =
    useGetDatabasesByConnectionQuery({
      page: 1,
      size: 25,
      connection_config_key: integrationKey,
    });

  useMemo(
    () =>
      setTimeout(() => {
        if (initialIsLoading) {
          setShowLongLoadingMessage(true);
        }
      }, 5000),
    [initialIsLoading],
  );

  const { items: initialDatabases, total: totalDatabases } =
    initialResult || EMPTY_RESPONSE;

  const reachedEnd = !!initialResult?.pages && nextPage > initialResult.pages;

  const [databases, setDatabases] = useState<string[]>(initialDatabases);

  const [
    refetchTrigger,
    { isLoading: refetchIsLoading, isFetching: refetchIsFetching },
  ] = useLazyGetDatabasesByConnectionQuery();

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
    showLongLoadingMessage,
  };
};

export default useCumulativeGetDatabases;
