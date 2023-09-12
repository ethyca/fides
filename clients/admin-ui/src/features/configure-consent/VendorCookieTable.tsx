import { useMemo } from "react";
import { Column } from "react-table";

import { useAppSelector } from "~/app/hooks";
import { FidesTable, TitleCell } from "~/features/common/table";
import { selectAllSystems } from "~/features/system";
import { SystemResponse } from "~/types/api";

const VendorCookieTable = () => {
  const systems = useAppSelector(selectAllSystems);
  const columns: Column<SystemResponse>[] = useMemo(
    () => [
      {
        Header: "Vendor",
        accessor: "name",
        Cell: TitleCell,
      },
    ],
    []
  );
  return <FidesTable<SystemResponse> columns={columns} data={systems} />;
};

export default VendorCookieTable;
