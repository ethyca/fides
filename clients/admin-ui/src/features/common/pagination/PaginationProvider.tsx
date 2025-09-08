import React, { PropsWithChildren, useContext } from "react";

import { useAntPagination } from "./useAntPagination";
import { usePagination } from "./usePagination";

const PaginationContext = React.createContext<
  undefined | ReturnType<typeof usePagination>
>(undefined);

export const usePaginationContext = () => {
  const paginationContext = useContext(PaginationContext);

  if (!paginationContext) {
    throw new Error(
      "To use usePaginationContext wrap your component tree in <PaginationProvider />",
    );
  }

  return paginationContext;
};

export const PaginationProvider = ({
  children,
  config,
}: PropsWithChildren<{
  config?: Partial<Parameters<typeof usePagination>[0]>;
}>) => {
  const pagination = usePagination(config);
  return (
    <PaginationContext.Provider value={pagination}>
      {children}
    </PaginationContext.Provider>
  );
};

const AntPaginationContext = React.createContext<
  undefined | ReturnType<typeof useAntPagination>
>(undefined);

export const useAntPaginationContext = () => {
  const paginationContext = useContext(AntPaginationContext);

  if (!paginationContext) {
    throw new Error(
      "To use useAntPaginationContext wrap your component tree in <AntPaginationProvider />",
    );
  }

  return paginationContext;
};

export const AntPaginationProvider = ({
  children,
  config,
}: PropsWithChildren<{
  config?: Partial<Parameters<typeof useAntPagination>[0]>;
}>) => {
  const pagination = useAntPagination(config);
  return (
    <AntPaginationContext.Provider value={pagination}>
      {children}
    </AntPaginationContext.Provider>
  );
};
