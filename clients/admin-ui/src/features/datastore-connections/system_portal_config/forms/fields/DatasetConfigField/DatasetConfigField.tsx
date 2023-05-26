import {
  Box,
  Button,
  Center,
  HStack,
  Select,
  Spinner,
  Text,
  TextProps,
  VStack,
  Flex,
} from "@fidesui/react";
import { useAlert, useAPIHelper } from "common/hooks";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import React, { ChangeEvent, useEffect, useState, useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
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

import YamlEditor from "./YamlEditor";
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
        fides_key: fidesKey,//DatasetConfig.fides_key
        ctl_dataset_fides_key: values[fieldName],
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
    console.log(values[fieldName], datasetConfigFidesKey, fidesKey, allDatasetConfigs, params)

    const payload = await patchDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
  };

  const handleSubmitYaml = async (value: unknown) => {
    try {
      setIsSubmitting(true);
      // First update the datasets
      const datasets = Array.isArray(value) ? value : [value];
      const upsertResult = await upsertDatasets(datasets);
      if ("error" in upsertResult) {
        const errorMessage = getErrorMessage(upsertResult.error);
        errorAlert(errorMessage);
        return;
      }

      // Upsert was successful, so we can cast from unknown to Dataset
      const upsertedDatasets = datasets as Dataset[];
      // Then link the updated dataset to the connection config.
      // New entries will have matching keys,
      let pairs: DatasetConfigCtlDataset[] = upsertedDatasets.map((d) => ({
        fides_key: d.fides_key,
        ctl_dataset_fides_key: d.fides_key,
      }));
      // But existing entries might have their dataset keys changed from under them
      if (allDatasetConfigs && allDatasetConfigs.items.length) {
        const { items: datasetConfigs } = allDatasetConfigs;
        pairs = datasetConfigs.map((d, i) => ({
          fides_key: d.fides_key,
          // This will not handle deletions, additions, or even changing order. If we want to support
          // those, we should probably have a different UX
          ctl_dataset_fides_key: upsertedDatasets[i].fides_key,
        }));
      }

      // TODO: Update this work with new form paradigm
      // handlePatchDatasetConfig(pairs);

    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // const isDatasetSelected = field.value !== "" && field.value !== undefined;

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
    patchConnectionDatasetConfig
  };
};

type Props = {
  dropdownOptions: Option[];
};

const DatasetConfigField: React.FC<Props> = ({ dropdownOptions }) => {
  // if (allDatasets === undefined) {
  //   return (
  //     <Center>
  //       <Spinner />
  //     </Center>
  //   );
  // }

  // TODO: Automatically set the dropdown value on form load

  return (
    <Flex flexDirection="row">
      <CustomSelect
        label="Dataset"
        name={fieldName}
        options={dropdownOptions}
        isRequired
      />
      <Button>YAML</Button>

      {/* <Box data-testid="yaml-editor-section"> */}
      {/*   {isSuccess && allDatasetConfigs!?.items ? ( */}
      {/*     <YamlEditor */}
      {/*       data={allDatasetConfigs.items.map((item) => item.ctl_dataset)} */}
      {/*       isSubmitting={isSubmitting} */}
      {/*       onSubmit={handleSubmitYaml} */}
      {/*       disabled={isDatasetSelected} */}
      {/*       // Only render the cancel button if the dataset dropdown view is unavailable */}
      {/*       // onCancel={undefined} */}
      {/*     /> */}
      {/*   ) : null} */}
      {/* </Box> */}
    </Flex>
  );
};

export default DatasetConfigField;
