import { Skeleton, Stack } from "@fidesui/react";
import { FC } from "react";

type Props = {
  rowHeight: number;
  numRows: number;
};

export const TableSkeletonLoader: FC<Props> = ({ rowHeight, numRows }) => {
  const rows = [];
  for (let i = 0; i < numRows; i += 1) {
    rows.push(<Skeleton height={`${rowHeight}px`} key={i} />);
  }

  return <Stack>{rows}</Stack>;
};
