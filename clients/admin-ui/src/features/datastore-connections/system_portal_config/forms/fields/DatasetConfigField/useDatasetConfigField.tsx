import { Option } from "common/form/inputs";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePutDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { useMessage } from "fidesui";
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

  const connectionKey = connectionConfig?.key ?? "";
  const { currentData } = useGetConnectionConfigDatasetConfigsQuery(
    connectionKey,
    {
      skip: !connectionKey,
    },
  );

  const initialDatasets = currentData?.items?.map((d) => d.fides_key) ?? [];
  const initialDatasetOptions =
    currentData?.items?.map((d) => ({
      value: d.fides_key,
      label: d.ctl_dataset.name || d.fides_key,
    })) ?? [];

  const { data: unlinkedDatasets } = useGetAllFilteredDatasetsQuery({
    onlyUnlinkedDatasets: true,
    minimal: true,
  });

  const unlinkedDatasetOptions: Option[] = useMemo(
    () =>
      unlinkedDatasets?.map((d) => ({
        value: d.fides_key,
        label: d.name || d.fides_key,
      })) ?? [],
    [unlinkedDatasets],
  );

  const message = useMessage();

  const patchConnectionDatasetConfig = async (
    values: ConnectionConfigFormValues,
    connectionConfigKey: string,
    { showSuccessAlert = true }: { showSuccessAlert?: boolean } = {},
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
      message.error(payload.failed[0].message);
    } else if (showSuccessAlert) {
      message.success("Dataset successfully updated!");
    }
  };

  const dropdownOptions = [...initialDatasetOptions, ...unlinkedDatasetOptions];

  return {
    dropdownOptions,
    initialDatasets,
    patchConnectionDatasetConfig,
  };
};
