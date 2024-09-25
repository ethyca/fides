import { Option } from "common/form/inputs";
import { useAlert } from "common/hooks";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePutDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { useMemo } from "react";

import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import {
  ConnectionConfigurationResponse,
  DatasetConfigCtlDataset,
} from "~/types/api";

type UseDatasetConfigField = {
  connectionConfig?: ConnectionConfigurationResponse | null;
};
export const useDatasetConfigField = ({
  connectionConfig,
}: UseDatasetConfigField) => {
  const [putDatasetConfig] = usePutDatasetConfigsMutation();

  const { data } = useGetConnectionConfigDatasetConfigsQuery(
    connectionConfig?.key ?? "",
  );

  const initialDatasets = data?.items?.map((d) => d.fides_key) ?? [];
  const initialDatasetOptions = initialDatasets.map((d) => ({
    label: d,
    value: d,
  }));

  const { data: unlinkedDatasets } = useGetAllFilteredDatasetsQuery({
    onlyUnlinkedDatasets: true,
  });

  const unlinkedDatasetOptions: Option[] = useMemo(
    () =>
      unlinkedDatasets?.map((d) => ({
        value: d.fides_key,
        label: `${d.name} (${d.fides_key})` || d.fides_key,
      })) ?? [],
    [unlinkedDatasets],
  );

  const { errorAlert, successAlert } = useAlert();

  const patchConnectionDatasetConfig = async (
    values: ConnectionConfigFormValues,
    connectionConfigKey: string,
  ) => {
    const newDatasetPairs: DatasetConfigCtlDataset[] =
      values.dataset?.map((datasetKey) => ({
        fides_key: datasetKey,
        ctl_dataset_fides_key: datasetKey,
      })) ?? [];

    const params: PatchDatasetsConfigRequest = {
      connection_key: connectionConfigKey,
      dataset_pairs: newDatasetPairs,
    };

    const payload = await putDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
  };

  const dropdownOptions = [...initialDatasetOptions, ...unlinkedDatasetOptions];

  return {
    dropdownOptions,
    initialDatasets,
    patchConnectionDatasetConfig,
  };
};
