/* eslint-disable react/no-unstable-nested-components */
import { AntButton as Button, AntSelect as Select } from "fidesui";
import React, { useContext } from "react";

import {
  safeParseInt,
  useStatefulQueryParam,
} from "~/features/common/query-parameters/queryParameters";

// type QueryParam = ReturnType<InstanceType<typeof URLSearchParams>["get"]>;

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 25;

const usePaginatorState = () => {
  const [page, setPage] = useStatefulQueryParam(
    "page",
    safeParseInt,
    DEFAULT_PAGE,
  );
  const [size, internalSetSize] = useStatefulQueryParam(
    "size",
    safeParseInt,
    DEFAULT_SIZE,
  );

  const setSize = (nextSize: number) => {
    internalSetSize(nextSize);
    setPage(1);
  };

  const previous = () =>
    setPage((previousPage) => {
      const nextPage = previousPage - 1;
      if (nextPage < DEFAULT_PAGE) {
        return DEFAULT_PAGE;
      }
      return nextPage;
    });
  const next = () => setPage((previousPage) => previousPage + 1);

  return {
    previous,
    next,
    setSize,
    page,
    size,
  };
};

const PageContext = React.createContext<
  ReturnType<typeof usePaginatorState> | undefined
>(undefined);

export const PaginationContext = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  const paginationState = usePaginatorState();

  return (
    <PageContext.Provider value={paginationState}>
      {children}
    </PageContext.Provider>
  );
};

export const usePagination = () => {
  const paginationContext = useContext(PageContext);
  if (paginationContext) {
    return paginationContext;
  }

  throw new Error("Pagination Context Provider not found.");
};

export const Paginator = () => {
  const { next, page, size, previous, setSize } = usePagination();

  return (
    <div style={{ display: "flex", columnGap: "10px", alignItems: "center" }}>
      <Button onClick={previous} disabled={page === 1}>
        Previous
      </Button>
      <span>{page}</span>
      <Button onClick={next}>Next</Button>
      <Select
        style={{ width: "auto" }}
        value={size}
        onChange={setSize}
        options={[
          { label: 25, value: 25 },
          { label: 50, value: 50 },
          { label: 100, value: 100 },
        ]}
        labelRender={() => {
          return <span>{size} / page</span>;
        }}
      />
    </div>
  );
};
