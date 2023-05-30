import {
  IconButton,
  Flex,
  useDisclosure,
} from "@fidesui/react";
import { EditIcon } from "@chakra-ui/icons";
import { useAlert, useAPIHelper } from "common/hooks";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import React, {
  useEffect,
  useState,
  useMemo,
  useCallback,
} from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  useGetAllDatasetsQuery,
  useUpsertDatasetsMutation,
} from "~/features/dataset";
import {
  ConnectionConfigurationResponse,
  Dataset,
  DatasetConfigCtlDataset,
} from "~/types/api";

import YamlEditorModal from "./YamlEditorModal";
import { CustomSelect, Option } from "common/form/inputs";
import { useField, useFormikContext } from "formik";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";

const fieldName = "dataset";

type UseDatasetConfigField = {
  connectionConfig?: ConnectionConfigurationResponse;
};
export const useDatasetConfigField = ({
  connectionConfig,
}: UseDatasetConfigField) => {
  // const [field] = useField<string>(fieldName);
  // const { setFieldValue } = useFormikContext();

  const [patchDatasetConfig] = usePatchDatasetConfigsMutation();
  const [upsertDatasets] = useUpsertDatasetsMutation();

  const {
    data: allDatasetConfigs,
    isFetching,
    isLoading,
    isSuccess,
  } = useGetConnectionConfigDatasetConfigsQuery(connectionConfig?.key || "");

  const {
    data: allDatasets,
    isLoading: isLoadingAllDatasets,
    error: loadAllDatasetsError,
  } = useGetAllDatasetsQuery();

  const [datasetConfigFidesKey, setDatasetConfigFidesKey] = useState<
    string | undefined
  >(undefined);

  useEffect(() => {
    if (allDatasetConfigs && allDatasetConfigs.items.length) {
      console.log(allDatasetConfigs.items[0].fides_key);
      // setFieldValue(fieldName, allDatasetConfigs.items[0].fides_key);
      setDatasetConfigFidesKey(allDatasetConfigs.items[0].fides_key);
    }
  }, [allDatasetConfigs]);

  const { handleError } = useAPIHelper();

  const { errorAlert, successAlert } = useAlert();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const patchConnectionDatasetConfig = async (
    values: ConnectionConfigFormValues,
    connectionConfigKey: string
  ) => {
    /*
      If no `datasetConfigFidesKey` exists then use the `values[fieldName]`.
      This means that no `DatasetConfig` has been linked to the current
      `ConnectionConfig` yet. Otherwise, reuse the pre-existing `datasetConfigFidesKey`
      and update the current `DatasetConfig`  use the `Dataset` that's tied
      to `values[fieldName]`
     */

    let fidesKey = values[fieldName];
    if (datasetConfigFidesKey) {
      fidesKey = datasetConfigFidesKey;
    }
    const datasetPairs: DatasetConfigCtlDataset[] = [
      {
        fides_key: fidesKey, //DatasetConfig.fides_key
        ctl_dataset_fides_key: values[fieldName], //Dataset.fides_key
      },
    ];

    /*
      The BE has a unique constraint on `DatasetConfig.fides_key`. Only one
      config can be linked to a given
     */
    const params: PatchDatasetsConfigRequest = {
      connection_key: connectionConfigKey,
      dataset_pairs: datasetPairs,
    };

    const payload = await patchDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
  };

  const upsertDataset = async (value: Dataset | Dataset[]) => {
    try {
      setIsSubmitting(true);
      // First update the datasets
      const datasets = Array.isArray(value) ? (value as Dataset[]) : [value];
      const upsertResult = await upsertDatasets(datasets);
      if ("error" in upsertResult) {
        const errorMessage = getErrorMessage(upsertResult.error);
        errorAlert(errorMessage);
        return;
      }

      return datasets[0].fides_key;
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const dropdownOptions: Option[] = useMemo(() => {
    return allDatasets
      ? allDatasets.map((d) => ({
          value: d.fides_key,
          label: d.name || d.fides_key,
        }))
      : [];
  }, [allDatasets]);
  return {
    datasetConfigFidesKey,
    dropdownOptions,
    upsertDataset,
    patchConnectionDatasetConfig,
  };
};

type Props = {
  dropdownOptions: Option[];
};

const DatasetConfigField: React.FC<Props> = ({ dropdownOptions }) => {
  const [datasetDropdownOption] = useField<string>(fieldName);
  const [datasetYaml] = useField<Dataset>("datasetYaml");
  const { setFieldValue } = useFormikContext();
  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data: allDatasets, isLoading } = useGetAllDatasetsQuery();

  const setDatasetYaml = useCallback<(value: Dataset) => void>((value) => {
    setFieldValue("datasetYaml", value);
  }, []);

  useEffect(() => {
    if (allDatasets && datasetDropdownOption.value) {
      const matchingDataset = allDatasets.find(
        (d) => d.fides_key === datasetDropdownOption.value
      );
      if (matchingDataset) {
        setDatasetYaml(matchingDataset);
      }
    }
  }, [allDatasets, datasetDropdownOption.value]);

  return (
    <Flex flexDirection="row">
      <CustomSelect
        label="Dataset"
        name={fieldName}
        options={dropdownOptions}
        isRequired
      />
      <IconButton
        aria-label="edit-dataset-yaml"
        icon={<EditIcon />}
        onClick={onOpen}
        size="sm"
        variant="outline"
        isDisabled={isLoading}
      />
      <YamlEditorModal
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={onClose}
        onChange={setDatasetYaml}
        isDatasetSelected={!!datasetDropdownOption.value}
        dataset={datasetYaml.value}
      />
    </Flex>
  );
};

export default DatasetConfigField;
