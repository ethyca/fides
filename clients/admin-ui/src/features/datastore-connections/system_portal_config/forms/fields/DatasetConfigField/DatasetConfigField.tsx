import {
  ErrorMessage,
  Label,
  Option,
  SelectInput,
  SelectProps,
  StringField,
} from "common/form/inputs";
import { useAlert } from "common/hooks";
import QuestionTooltip from "common/QuestionTooltip";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { Flex, FormControl } from "fidesui";
import { useField } from "formik";
import React, { useMemo } from "react";

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
  const [patchDatasetConfig] = usePatchDatasetConfigsMutation();

  const { data } = useGetConnectionConfigDatasetConfigsQuery(
    connectionConfig?.key ?? "",
  );

  const initialDatasets = data?.items?.map((d) => d.fides_key) ?? [];

  const { data: allDatasets } = useGetAllFilteredDatasetsQuery({
    onlyUnlinkedDatasets: false,
  });

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

    const payload = await patchDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
  };

  const dropdownOptions: Option[] = useMemo(
    () =>
      allDatasets?.map((d) => ({
        value: d.fides_key,
        label: `${d.name} (${d.fides_key})` || d.fides_key,
      })) ?? [],
    [allDatasets],
  );

  return {
    dropdownOptions,
    initialDatasets,
    patchConnectionDatasetConfig,
  };
};
