import { createColumnHelper } from "@tanstack/react-table";
import { forEach } from "lodash";
import { useCallback, useMemo } from "react";

import {
  BadgeCell,
  DefaultCell,
  DefaultHeaderCell,
} from "~/features/common/table/v2";
import { PreferencesSaved, UserConsentPreference } from "~/types/api";

import {
  USER_CONSENT_PREFERENCE_COLOR,
  USER_CONSENT_PREFERENCE_LABELS,
} from "../constants";

export interface TcfDetailRow {
  key: string;
  id: string | number;
  preference: UserConsentPreference;
}

const columnHelper = createColumnHelper<TcfDetailRow>();

const useTcfConsentColumns = () => {
  const mapTcfPreferencesToRowColumns = useCallback(
    (allPreferences?: PreferencesSaved | null) => {
      const results: TcfDetailRow[] = [];
      if (allPreferences) {
        const { preferences, ...tcfPreferences } = allPreferences;
        forEach(tcfPreferences, (records, key) => {
          if (records) {
            records.forEach((value) => {
              results.push({
                key,
                id: value.id,
                preference: value.preference,
              });
            });
          }
        });
      }
      return results;
    },
    [],
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor((row) => row.key, {
        id: "key",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="Type" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.id, {
        id: "id",
        cell: ({ getValue }) => <DefaultCell value={getValue()} />,
        header: (props) => <DefaultHeaderCell value="ID" {...props} />,
        enableSorting: false,
      }),
      columnHelper.accessor((row) => row.preference, {
        id: "preference",
        cell: ({ getValue }) => {
          const preference = getValue();
          const preferenceLabel =
            (preference && USER_CONSENT_PREFERENCE_LABELS[preference]) ||
            preference;

          const badgeColor =
            (preference && USER_CONSENT_PREFERENCE_COLOR[preference]) || "";

          return <BadgeCell color={badgeColor} value={preferenceLabel} />;
        },
        header: (props) => <DefaultHeaderCell value="Preference" {...props} />,
        enableSorting: false,
        size: 100,
      }),
    ],
    [],
  );

  return { tcfColumns: columns, mapTcfPreferencesToRowColumns };
};
export default useTcfConsentColumns;
