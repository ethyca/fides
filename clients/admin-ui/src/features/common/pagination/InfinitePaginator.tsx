import {
  AntButton as Button,
  AntFlex as Flex,
  AntSelect as Select,
  Icons,
} from "fidesui";
import React from "react";

import { usePaginationContext } from "~/features/common/pagination/PaginationProvider";

export const InfinitePaginator = ({
  disableNext,
}: {
  disableNext?: boolean;
}) => {
  const { nextPage, pageIndex, pageSize, previousPage, updatePageSize } =
    usePaginationContext();
  return (
    <Flex gap="middle" align="center" justify="right">
      <Button
        onClick={previousPage}
        disabled={pageIndex === 1}
        icon={<Icons.ChevronLeft aria-hidden />}
        aria-label="Previous"
      />
      <span aria-label={`Page ${pageIndex}`}>{pageIndex}</span>
      <Button
        onClick={nextPage}
        disabled={disableNext}
        icon={<Icons.ChevronRight aria-hidden />}
        aria-label="Next"
      />
      <Select
        className="w-auto"
        value={pageSize}
        onChange={updatePageSize}
        options={[
          { label: 25, value: 25 },
          { label: 50, value: 50 },
          { label: 100, value: 100 },
        ]}
        // eslint-disable-next-line react/no-unstable-nested-components
        labelRender={({ value }) => <span>{value} / page</span>}
      />
    </Flex>
  );
};
