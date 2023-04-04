import { createSelector, createSlice, PayloadAction } from '@reduxjs/toolkit';

import type { RootState } from '~/app/store';
import { baseApi } from '~/features/common/api.slice';
import {
  COLUMN_NAME_MAP,
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_DESCRIPTION,
  SYSTEM_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGAL_BASIS,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
} from '~/features/datamap/constants';
import { DataCategory } from '~/types/api';

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

type View = 'map' | 'table';

const DEFAULT_ACTIVE_COLUMNS = [
  SYSTEM_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_NAME,
  SYSTEM_PRIVACY_DECLARATION_DATA_USE_LEGAL_BASIS,
  DATA_CATEGORY_COLUMN_ID,
  SYSTEM_PRIVACY_DECLARATION_DATA_SUBJECTS_NAME,
  SYSTEM_DESCRIPTION,
];

const DEPRECATED_COLUMNS = [
  'third_country_combined',
  'system.third_country_safeguards',
  'system.data_protection_impact_assessment.is_required',
  'system.data_protection_impact_assessment.progress',
  'dataset.fides_key',
  'system.link_to_processor_contract',
  'system.privacy_declaration.data_use.legitimate_interest',
  // 'system.fides_key', it looks like this is needed for the graph. Disable properly later.
];

// API endpoints
const datamapApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getDatamap: build.query<DatamapTableData, { organizationName: string }>({
      query: ({ organizationName }) => ({
        url: `datamap/${organizationName}`,
        method: 'GET',
        params: {
          include_deprecated_columns: true,
        },
      }),
      providesTags: ['Datamap'],
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

export const { useGetDatamapQuery, useLazyGetDatamapQuery } = datamapApi;

const dataCategoriesApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllDataCategories: build.query<DataCategory[], void>({
      query: () => ({ url: `data_category` }),
      providesTags: () => ['Data Category'],
    }),
  }),
});

export const { useGetAllDataCategoriesQuery } = dataCategoriesApi;

// Selectors
const emptyDataCategories: DataCategory[] = [];
export const selectDataCategories = createSelector(
  dataCategoriesApi.endpoints.getAllDataCategories.select(),
  ({ data }: { data?: DataCategory[] }) => data ?? emptyDataCategories
);

export const selectDataCategoriesMap = createSelector(
  selectDataCategories,
  (dataCategories) => new Map(dataCategories.map((c) => [c.fides_key, c]))
);

export interface SettingsState {
  columns?: DatamapColumn[];
  view: View;
  isGettingStarted: boolean;
}

const initialState: SettingsState = {
  columns: undefined,
  view: 'map',
  isGettingStarted: false,
};

// Settings slice
export const datamapSlice = createSlice({
  name: 'datamap',
  initialState,
  reducers: {
    // Sets the ordering and activation of the columns
    setColumns(draftState, { payload }: PayloadAction<DatamapColumn[]>) {
      draftState.columns = payload;
    },
    // Load columns for the first time. If columns are already loaded, no-op.
    loadColumns(draftState, { payload }: PayloadAction<DatamapColumn[]>) {
      if (draftState.columns) {
        return;
      }

      draftState.columns = payload;
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
  (settings) => settings.view === 'map'
);

export const selectIsGettingStarted = createSelector(
  selectSettings,
  (settings) => settings.isGettingStarted
);

export const { setColumns, loadColumns, setView, setIsGettingStarted } =
  datamapSlice.actions;

export const { reducer } = datamapSlice;
