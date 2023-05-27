import { useContext, useEffect, useMemo, useRef } from "react";
import {
  AggregatorFn,
  useExpanded,
  useFilters,
  useFlexLayout,
  useGlobalFilter,
  useGroupBy,
  useResizeColumns,
  useTable,
} from "react-table";

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
import {
  SYSTEM_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from "~/features/datamap/constants";
import CustomCell from "~/features/datamap/datamap-table/CustomCell";
import DatamapTableContext from "~/features/datamap/datamap-table/DatamapTableContext";
import AccordionMultifieldFilter, {
  accordionMultifieldFilter,
} from "~/features/datamap/datamap-table/filters/accordion-multifield-filter";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy";

const DEFAULT_COLUMN = {
  minWidth: 30,
  width: 150,
  maxWidth: 300,
  Cell: CustomCell,
  Filter: AccordionMultifieldFilter,
  filter: "multifield",
};

type Column = {
  id: string;
  accessor: (row: DatamapRow) => string;
  Header: string;
  isVisible: boolean;
  aggregate: AggregatorFn<DatamapRow>;
};

const FILTER_TYPES = {
  multifield: accordionMultifieldFilter,
};

export const useTableInstance = () => {
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
    [responseData]
  );

  const columns = useMemo(
    () =>
      (columnData || []).map(({ text, value: columnName, isVisible }) => ({
        id: columnName,
        // A custom accessor is required because ReactTable interprets a column name with dots like
        // "dataset.name" as a nested lookup on the row.
        accessor: (row: DatamapRow) => row[columnName],
        Header: text,
        isVisible,
        aggregate: (
          leafValues: string[],
          aggregatedValues: string[]
        ): string => {
          const uniqueValues = new Set<string>(aggregatedValues);
          leafValues.forEach((leaf) => {
            if (!uniqueValues.has(leaf)) {
              uniqueValues.add(leaf);
            }
          });

          return Array.from(uniqueValues.values()).join(", ");
        },
      })) as unknown as Column[],
    [columnData]
  );

  // This is memoized under the hood of the table library, and only is recreated
  // when one of its data sources (columns, data) changes. Since they are also
  // memoized, we avoid recreating the table until we receive settings changes
  const tableInstance = useTable<DatamapRow>(
    {
      columns,
      data,
      defaultColumn: DEFAULT_COLUMN,
      filterTypes: FILTER_TYPES,
      initialState: {
        groupBy: [SYSTEM_NAME, SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME],
      },
    },
    useFilters,
    useGlobalFilter,
    useFlexLayout,
    useResizeColumns,
    useGroupBy,
    useExpanded
  );

  // When the table is created for the first time, store a reference to it on
  // context, so that the export modal can access the table instance for export
  // purposes
  useEffect(
    () => updateTableInstance(tableInstance),
    [tableInstance, updateTableInstance]
  );

  // Whenever the columns are updated in the settings modal, we need to re-
  // calculate which columns are hidden, since in react-table the hidden columns
  // are extracted from the raw column data and passed as a separate object
  useEffect(() => {
    tableInstance.setHiddenColumns(
      columnData
        ?.filter((column) => !column.isVisible)
        .map((column) => column.value) || []
    );
  }, [columnData, tableInstance]);

  return {
    ...tableInstance,
    isLoading,
  };
};
