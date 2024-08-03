import { h } from "preact";
import { useState } from "preact/hooks";

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

  const rangeStart = currentPage === 1 ? 1 : (currentPage - 1) * PAGE_SIZE + 1;
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

const PreviousIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="12"
    height="12"
    fill="currentColor"
  >
    <path d="m5.914 6 2.475 2.475-.707.707L4.5 6l3.182-3.182.707.707L5.914 6Z" />
  </svg>
);

const NextIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="12"
    height="12"
    fill="currentColor"
  >
    <path d="M7.086 6 4.61 3.525l.707-.707L8.5 6 5.318 9.182l-.707-.707L7.086 6Z" />
  </svg>
);

const PagingButtons = <T,>({
  nextPage,
  previousPage,
  rangeStart,
  rangeEnd,
  disableNext,
  disablePrevious,
  totalItems,
}: Omit<PagingData<T>, "activeChunk" | "totalPages">) => (
  <div className="fides-paging-buttons">
    <span className="fides-paging-info">
      {rangeStart}-{rangeEnd} / {totalItems}
    </span>
    <div className="fides-flex-center">
      <button
        className="fides-paging-previous-button"
        type="button"
        onClick={previousPage}
        disabled={disablePrevious}
        aria-label="Previous page"
      >
        <PreviousIcon />
      </button>
      <button
        className="fides-paging-next-button"
        type="button"
        onClick={nextPage}
        disabled={disableNext}
        aria-label="Next page"
      >
        <NextIcon />
      </button>
    </div>
  </div>
);
export default PagingButtons;
