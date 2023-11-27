import { useState } from "preact/hooks";
import { h } from "preact";
import { chunkItems, PAGE_SIZE } from "../lib/paging";

interface PagingData<T> {
  activeChunk: T[];
  totalPages: number;
  nextPage: () => void;
  previousPage: () => void;
  disableNext: boolean;
  disablePrevious: boolean;
  rangeStart: number;
  rangeEnd: number;
  totalItems: number;
}

export const usePaging = <T,>(items: T[]): PagingData<T> => {
  const [currentPage, setCurrentPage] = useState(1);
  const chunks = chunkItems(items);
  const totalPages = chunks.length;
  const disableNext = currentPage >= totalPages;
  const disablePrevious = currentPage <= 1;

  const nextPage = () => {
    if (!disableNext) {
      setCurrentPage(currentPage + 1);
    }
  };

  const previousPage = () => {
    if (!disablePrevious) {
      setCurrentPage(currentPage - 1);
    }
  };

  const rangeStart = currentPage === 1 ? 1 : (currentPage - 1) * PAGE_SIZE;
  const rangeEnd =
    currentPage === totalPages ? items.length : currentPage * PAGE_SIZE;

  const activeChunk = chunks[currentPage - 1];

  return {
    activeChunk,
    totalPages: chunks.length,
    nextPage,
    previousPage,
    disableNext,
    disablePrevious,
    rangeStart,
    rangeEnd,
    totalItems: items.length,
  };
};

const PagingButtons = <T,>({
  nextPage,
  previousPage,
  rangeStart,
  rangeEnd,
  disableNext,
  disablePrevious,
  totalItems,
}: Omit<PagingData<T>, "activeChunk" | "totalPages">) => (
  <div>
    <span>
      {rangeStart}-{rangeEnd} of {totalItems}
    </span>
    <button type="button" onClick={previousPage} disabled={disablePrevious}>
      {"<"}
    </button>
    <button type="button" onClick={nextPage} disabled={disableNext}>
      {">"}
    </button>
  </div>
);
export default PagingButtons;
