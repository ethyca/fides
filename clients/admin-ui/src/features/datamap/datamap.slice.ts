import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  COLUMN_NAME_MAP,
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_DESCRIPTION,
  SYSTEM_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from "~/features/datamap/constants";
import { DATAMAP_GROUPING, Page_DatamapReport_ } from "~/types/api";

export interface DataCategoryNode {
  value: string;
  label: string;
  description?: string;
  children: DataCategoryNode[];
}

export interface DatamapRow {
  [fieldName: string]: string;
}

/** A column in the table. Derived from API response client-side. */
export interface DatamapColumn {
  isVisible: boolean;
  /** The human-readable name for this column */
  text: string;
  /** The field that this column exists as on rows */
  value: string;
  id: number;
}

export interface Filters {
  [fieldValue: string]: string[];
}

export type DatamapResponse = DatamapRow[];

export type DatamapTableData = {
  columns: DatamapColumn[];
  rows: DatamapRow[];
};

type View = "map" | "table";

const DEFAULT_ACTIVE_COLUMNS = [
  SYSTEM_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_DESCRIPTION,
];

const DEPRECATED_COLUMNS = [
  "third_country_combined",
  "system.third_country_safeguards",
  "dataset.fides_key",
  "system.link_to_processor_contract",
];

// API endpoints
const datamapApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMinimalDatamapReport: build.query<
      Page_DatamapReport_,
      {
        groupBy: DATAMAP_GROUPING;
        pageIndex: number;
        pageSize: number;
        search: string;
        dataUses?: string;
        dataCategories?: string;
        dataSubjects?: string;
      }
    >({
      query: ({
        groupBy,
        pageIndex,
        pageSize,
        search,
        dataUses,
        dataCategories,
        dataSubjects,
      }) => {
        let queryString = `page=${pageIndex}&size=${pageSize}&group_by=${groupBy}`;
        if (dataUses) {
          queryString += `&${dataUses}`;
        }
        if (dataCategories) {
          queryString += `&${dataCategories}`;
        }
        if (dataSubjects) {
          queryString += `&${dataSubjects}`;
        }
        if (search) {
          queryString += `&search=${search}`;
        }
        return {
          url: `plus/datamap/minimal?${queryString}`,
        };
      },
    }),
    getDatamap: build.query<DatamapTableData, { organizationName: string }>({
      query: ({ organizationName }) => ({
        url: `plus/datamap/${organizationName}`,
        method: "GET",
        params: {
          include_deprecated_columns: true,
        },
      }),
      providesTags: ["Datamap"],
      transformResponse: (data: DatamapResponse) => {
        const columnHeaderData = Object.entries(data[0]).filter(
          ([value]) => DEPRECATED_COLUMNS.indexOf(value) === -1
        );

        const NON_DEFAULT_COLUMNS = columnHeaderData
          .filter(([value]) => DEFAULT_ACTIVE_COLUMNS.indexOf(value) === -1)
          .map(([value]) => value);

        const DEFAULT_COLUMN_ORDER: { [key: string]: number } = {};

        for (let i = 0, len = DEFAULT_ACTIVE_COLUMNS.length; i < len; i += 1) {
          DEFAULT_COLUMN_ORDER[DEFAULT_ACTIVE_COLUMNS[i]] = i;
        }

        for (let i = 0, len = NON_DEFAULT_COLUMNS.length; i < len; i += 1) {
          DEFAULT_COLUMN_ORDER[NON_DEFAULT_COLUMNS[i]] =
            i + DEFAULT_ACTIVE_COLUMNS.length;
        }

        return {
          columns: columnHeaderData
            .sort(
              (a, b) => DEFAULT_COLUMN_ORDER[a[0]] - DEFAULT_COLUMN_ORDER[b[0]]
            )
            .map(([value, displayText], index) => ({
              isVisible: DEFAULT_ACTIVE_COLUMNS.indexOf(value) > -1,
              text:
                value in COLUMN_NAME_MAP ? COLUMN_NAME_MAP[value] : displayText,
              value,
              id: index,
            })),
          rows: data.slice(1),
        };
      },
    }),
  }),
});

export const {
  useGetDatamapQuery,
  useLazyGetDatamapQuery,
  useGetMinimalDatamapReportQuery,
} = datamapApi;

export interface SettingsState {
  columns?: DatamapColumn[];
  view: View;
  isGettingStarted: boolean;
}

const initialState: SettingsState = {
  columns: undefined,
  view: "map",
  isGettingStarted: false,
};

export const mergeColumns = <T extends { value: string }>(
  columns: T[] | undefined,
  updatedColumns: T[]
) => {
  /*
  this happens the first load of the table when no columns
  are in localStorage
   */
  if (!columns) {
    return updatedColumns;
  }

  const currentColumnKeys = new Set(columns.map((column) => column.value));
  const updatedColumnKeys = new Set(
    updatedColumns.map((column) => column.value)
  );

  const newColumnKeys = new Set(
    [...updatedColumnKeys].filter((x) => !currentColumnKeys.has(x))
  );

  /*
  A column can get "removed" when a custom field is deleted
  or renamed. The column keys are not done by id but by the
  custom field name. So when a name changes so does the key.
  This requires removing any cached column that isn't in the
  updated columns.
   */
  const removedColumns = new Set(
    [...currentColumnKeys].filter((x) => !updatedColumnKeys.has(x))
  );

  return [
    ...columns.filter((column) => !removedColumns.has(column.value)),
    ...updatedColumns.filter((column) => newColumnKeys.has(column.value)),
  ];
};

// Settings slice
export const datamapSlice = createSlice({
  name: "datamap",
  initialState,
  reducers: {
    // Sets the ordering and activation of the columns
    setColumns(draftState, { payload }: PayloadAction<DatamapColumn[]>) {
      draftState.columns = payload;
    },
    // Load columns for the first time. If columns are already loaded, no-op.
    loadColumns(draftState, { payload }: PayloadAction<DatamapColumn[]>) {
      draftState.columns = mergeColumns<DatamapColumn>(
        draftState.columns,
        payload
      );
    },
    setView(draftState, { payload }: PayloadAction<View>) {
      draftState.view = payload;
    },
    setIsGettingStarted(draftState, { payload }: PayloadAction<boolean>) {
      draftState.isGettingStarted = payload;
    },
  },
});

export const selectSettings = (state: RootState) => state.datamap;

export const selectColumns = createSelector(
  selectSettings,
  (settings) => settings.columns
);

export const selectIsMapOpen = createSelector(
  selectSettings,
  (settings) => settings.view === "map"
);

export const selectIsGettingStarted = createSelector(
  selectSettings,
  (settings) => settings.isGettingStarted
);

export const { setColumns, loadColumns, setView, setIsGettingStarted } =
  datamapSlice.actions;

export const { reducer } = datamapSlice;
