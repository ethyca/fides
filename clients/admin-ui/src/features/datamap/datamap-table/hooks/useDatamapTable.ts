import {
  createColumnHelper,
  getCoreRowModel,
  getFacetedRowModel,
  getFacetedUniqueValues,
  getFilteredRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { useContext, useEffect, useMemo, useRef } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useGetAllDataSubjectsQuery } from "~/features/data-subjects/data-subject.slice";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";
import {
  DatamapRow,
  loadColumns,
  selectColumns,
  setIsGettingStarted,
  useGetDatamapQuery,
} from "~/features/datamap";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import { accordionMultifieldFilter } from "~/features/datamap/datamap-table/filters/accordion-multifield-filter/helpers";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";

const columnHelper = createColumnHelper<DatamapRow>();

const FILTER_TYPES = {
  multifield: accordionMultifieldFilter,
};

export const useDatamapTable = () => {
  const dispatch = useAppDispatch();
  const { updateTableInstance } = useContext(DatamapTableContext);
  /*
   * This is intentionally hardcoded to the prod env.
   * Making it not required being hardcoded would
   * require pulling a lot of code from core.
   * This is a minimal impl to use until we have a
   * better way to share code to the plus ui.
   */
  const columnData = useAppSelector(selectColumns);
  const { data: responseData, isLoading } = useGetDatamapQuery({
    organizationName: "default_organization",
  });

  useGetAllDataCategoriesQuery();
  useGetAllDataUsesQuery();
  useGetAllDataSubjectsQuery();

  const checkedGettingStarted = useRef(false);

  useEffect(() => {
    // Load the columns into Redux the first time they come back from the server
    // so we can use them to build the settings modal and the spatial datamap
    if (responseData) {
      const { columns, rows } = responseData;

      dispatch(loadColumns(columns));

      // Only check for empty data on the first query response.
      if (!checkedGettingStarted.current) {
        checkedGettingStarted.current = true;
        if (rows.length === 0) {
          dispatch(setIsGettingStarted(true));
        } else {
          dispatch(setIsGettingStarted(false));
        }
      }
    }
  }, [responseData, dispatch]);

  const data = useMemo(
    () => (responseData ? responseData.rows : []),
    [responseData],
  );

  const columns = useMemo(
    () =>
      (columnData || []).map(({ text, value: columnName }) =>
        columnHelper.accessor((row) => row[columnName], {
          id: columnName,
          header: text,
          cell: ({ getValue }) => {
            const value = getValue();
            if (Array.isArray(value)) {
              return value.join(", ");
            }
            return value;
          },
          filterFn: FILTER_TYPES.multifield,
        }),
      ),
    [columnData],
  );

  // This is memoized under the hood of the table library, and only is recreated
  // when one of its data sources (columns, data) changes. Since they are also
  // memoized, we avoid recreating the table until we receive settings changes
  const tableInstance = useReactTable<DatamapRow>({
    columns,
    data,
    filterFns: FILTER_TYPES,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getFacetedRowModel: getFacetedRowModel(),
    getFacetedUniqueValues: getFacetedUniqueValues(),
    manualPagination: true,
    columnResizeMode: "onChange",
  });

  // When the table is created for the first time, store a reference to it on
  // context, so that the export modal can access the table instance for export
  // purposes
  useEffect(
    () => updateTableInstance(tableInstance),
    [tableInstance, updateTableInstance],
  );

  return {
    ...tableInstance,
    isLoading,
  };
};
