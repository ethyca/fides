import { Box, Table } from "fidesui";
import React, { useContext } from "react";
import { Row } from "react-table";

import { DatamapRow } from "~/features//datamap/datamap.slice";
import { SYSTEM_FIDES_KEY_COLUMN_ID } from "~/features/datamap/constants";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import GroupedTableBody from "~/features/datamap/datamap-table/GroupedTableBody";
import GroupedTableHeader from "~/features/datamap/datamap-table/GroupedTableHeader";
import { SetSelectedSystemId } from "~/features/datamap/types";

type DatamapTableProps = {} & SetSelectedSystemId;
const DatamapTable = ({ setSelectedSystemId }: DatamapTableProps) => {
  const { tableInstance } = useContext(DatamapTableContext);
  if (!tableInstance) {
    return null;
  }

  const { getTableProps, getTableBodyProps, headerGroups, prepareRow, rows } =
    tableInstance;

  const handleSubrowClick = (subRow: Row<DatamapRow>) => {
    if (subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]) {
      setSelectedSystemId(subRow.values[SYSTEM_FIDES_KEY_COLUMN_ID]);
    }
  };

  return (
    <Box boxSize="100%" overflow="auto">
      <Table {...getTableProps()} size="sm" data-testid="datamap-table">
        <GroupedTableHeader<DatamapRow> headerGroups={headerGroups} />
        <GroupedTableBody<DatamapRow>
          rowHeading="System Name"
          renderRowSubheading={(row) => row.groupByVal}
          onSubrowClick={handleSubrowClick}
          getTableBodyProps={getTableBodyProps}
          prepareRow={prepareRow}
          rows={rows}
        />
      </Table>
    </Box>
  );
};

export default DatamapTable;
