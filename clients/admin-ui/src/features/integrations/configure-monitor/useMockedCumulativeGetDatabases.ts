import { useState } from "react";

const EMPTY_RESPONSE = {
  items: [] as string[],
  total: 1,
  page: 1,
  size: 50,
  pages: 0,
};

const paginatedMock = [
  {
    items: Array.from({ length: 25 }, (_, i) => `Database ${i}`),
    total: 100,
    page: 1,
    size: 25,
    pages: 4,
  },
  {
    items: Array.from({ length: 25 }, (_, i) => `Database ${i + 25}`),
    total: 100,
    page: 2,
    size: 25,
    pages: 4,
  },
  {
    items: Array.from({ length: 25 }, (_, i) => `Database ${i + 50}`),
    total: 100,
    page: 3,
    size: 25,
    pages: 4,
  },
  {
    items: Array.from({ length: 25 }, (_, i) => `Database ${i + 75}`),
    total: 100,
    page: 4,
    size: 25,
    pages: 4,
  },
];

const useMockedCumulativeGetDatabases = (integrationKey: string) => {
  const [nextPage, setNextPage] = useState(2);

  const initialResult = paginatedMock[nextPage - 2];

  const { items: initialDatabases, total: totalDatabases } =
    initialResult ?? EMPTY_RESPONSE;

  const reachedEnd = !!initialResult?.pages && nextPage > initialResult.pages;

  const [databases, setDatabases] = useState<string[]>(initialDatabases);
  const [isLoading, setIsLoading] = useState(false);

  const refetchTrigger = ({ connection_config_key, size, page }) =>
    new Promise<{ data: { items: string[] }; isError: boolean }>((resolve) => {
      setTimeout(() => {
        resolve({
          isError: false,
          data: paginatedMock[page - 1],
        });
      }, 500);
    });

  const fetchMore = async () => {
    if (reachedEnd) {
      return;
    }
    setIsLoading(true);
    const result: { data: { items: string[] } } = await refetchTrigger({
      connection_config_key: integrationKey,
      size: 25,
      page: nextPage,
    });
    setIsLoading(false);
    setNextPage(nextPage + 1);
    setDatabases([...databases, ...(result.data?.items ?? [])]);
  };

  return { databases, totalDatabases, fetchMore, isLoading, reachedEnd };
};

export default useMockedCumulativeGetDatabases;
