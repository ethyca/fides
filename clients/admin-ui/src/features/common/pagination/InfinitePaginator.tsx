import {
  AntButton as Button,
  AntFlex as Flex,
  AntSelect as Select,
  Icons,
} from "fidesui";
import React from "react";

import { usePagination } from "./usePagination";

export const InfinitePaginator = ({
  disableNext,
  pagination,
}: {
  disableNext?: boolean;
  pagination: ReturnType<typeof usePagination>;
}) => {
  return (
    <Flex gap="middle" align="center" justify="right">
      <Button
        onClick={pagination.previousPage}
        disabled={pagination.pageIndex === 1}
        icon={<Icons.ChevronLeft aria-hidden />}
        aria-label="Previous"
      />
      <span aria-label={`Page ${pagination.pageIndex}`}>
        {pagination.pageIndex}
      </span>
      <Button
        onClick={pagination.nextPage}
        disabled={disableNext}
        icon={<Icons.ChevronRight aria-hidden />}
        aria-label="Next"
      />
      <Select
        className="w-auto"
        value={pagination.pageSize}
        onChange={pagination.updatePageSize}
        options={pagination.pageSizeOptions.map((option) => ({
          label: option,
          value: option,
        }))}
        // eslint-disable-next-line react/no-unstable-nested-components
        labelRender={({ value }) => <span>{value} / page</span>}
        aria-label="Select page size"
      />
    </Flex>
  );
};
