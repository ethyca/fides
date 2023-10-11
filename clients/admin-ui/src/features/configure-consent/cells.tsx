import { Box } from "@fidesui/react";
import { CellProps } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { MapCell } from "~/features/common/table";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";

import { CookieBySystem } from "./vendor-transform";

export const DataUseCell = (cellProps: CellProps<CookieBySystem, string>) => {
  useGetAllDataUsesQuery();
  const dataUses = useAppSelector(selectDataUses);

  const map = new Map(
    dataUses.map((dataUse) => [
      dataUse.fides_key,
      dataUse.name || dataUse.fides_key,
    ])
  );

  // eslint-disable-next-line react/destructuring-assignment
  if (cellProps.value === "N/A") {
    return <Box p={2}>N/A</Box>;
  }

  return (
    <Box>
      <MapCell isPlainText map={map} {...cellProps} />
    </Box>
  );
};
