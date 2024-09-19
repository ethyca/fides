import {
  ErrorMessage,
  Label,
  Option,
  SelectInput,
  SelectProps,
  StringField,
} from "common/form/inputs";
import { useAlert, useAPIHelper } from "common/hooks";
import QuestionTooltip from "common/QuestionTooltip";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { ConnectionConfigFormValues } from "datastore-connections/system_portal_config/types";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { Flex, FormControl } from "fidesui";
import { useField } from "formik";
import React, { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  useGetAllFilteredDatasetsQuery,
  useUpsertDatasetsMutation,
} from "~/features/dataset";
import {
  ConnectionConfigurationResponse,
  Dataset,
  DatasetConfigCtlDataset,
} from "~/types/api";

const DATASET_FIELD_NAME = "dataset";

export const DatasetSelect = ({
  label,
  labelProps,
  tooltip,
  options,
  isDisabled,
  isRequired,
  isSearchable,
  isClearable,
  size = "sm",
  isMulti,
  singleValueBlock,
  onChange,
  isFormikOnChange,
  ...props
}: SelectProps & StringField) => {
  const [field, meta] = useField(props);
  const isInvalid = !!(meta.touched && meta.error);
  return (
    <FormControl
      display="flex"
      flexDirection="row"
      isInvalid={isInvalid}
      isRequired={isRequired}
    >
      {label ? (
        <Label htmlFor={props.id || props.name} {...labelProps}>
          {label}
        </Label>
      ) : null}
      <Flex
        alignItems="center"
        data-testid={`input-${field.name}`}
        width="100%"
      >
        <Flex flexDir="column" flexGrow={1} mr="2" width="100%">
          <SelectInput
            options={options}
            fieldName={field.name}
            size={size}
            isSearchable={isSearchable === undefined ? isMulti : isSearchable}
            isClearable={isClearable}
            isMulti={isMulti}
            isDisabled={isDisabled}
            singleValueBlock={singleValueBlock}
            menuPosition={props.menuPosition}
            onChange={!isFormikOnChange ? onChange : undefined}
          />

          <ErrorMessage
            isInvalid={isInvalid}
            message={meta.error}
            fieldName={field.name}
          />
        </Flex>
        {tooltip ? <QuestionTooltip label={tooltip} /> : null}
      </Flex>
    </FormControl>
  );
};

type UseDatasetConfigField = {
  connectionConfig?: ConnectionConfigurationResponse | null;
};
export const useDatasetConfigField = ({
  connectionConfig,
}: UseDatasetConfigField) => {
  const [patchDatasetConfig] = usePatchDatasetConfigsMutation();
  const [upsertDatasets] = useUpsertDatasetsMutation();

  const { data: allDatasetConfigs, isLoading: isLoadingDatasetConfigs } =
    useGetConnectionConfigDatasetConfigsQuery(connectionConfig?.key || "");

  const { data: allDatasets } = useGetAllFilteredDatasetsQuery(
    {
      onlyUnlinkedDatasets: allDatasetConfigs
        ? allDatasetConfigs.items.length === 0
        : false,
    },
    {
      skip: isLoadingDatasetConfigs,
    },
  );

  const [datasetConfigFidesKey, setDatasetConfigFidesKey] = useState<
    string | undefined
  >(undefined);

  useEffect(() => {
    if (allDatasetConfigs && allDatasetConfigs.items.length) {
      setDatasetConfigFidesKey(allDatasetConfigs.items[0].fides_key);
    }
  }, [allDatasetConfigs]);

  const { handleError } = useAPIHelper();

  const { errorAlert, successAlert } = useAlert();

  const patchConnectionDatasetConfig = async (
    values: ConnectionConfigFormValues,
    connectionConfigKey: string,
  ) => {
    /*
      If no `datasetConfigFidesKey` exists then use the `values[fieldName]`.
      This means that no `DatasetConfig` has been linked to the current
      `ConnectionConfig` yet. Otherwise, reuse the pre-existing `datasetConfigFidesKey`
      and update the current `DatasetConfig`  use the `Dataset` that's tied
      to `values[fieldName]`
     */

    let fidesKey = values[DATASET_FIELD_NAME];
    if (datasetConfigFidesKey) {
      fidesKey = datasetConfigFidesKey;
    }
    const datasetPairs: DatasetConfigCtlDataset[] = [
      {
        fides_key: fidesKey, // DatasetConfig.fides_key
        ctl_dataset_fides_key: values[DATASET_FIELD_NAME], // Dataset.fides_key
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
      // First update the datasets
      const datasets = Array.isArray(value) ? (value as Dataset[]) : [value];
      const upsertResult = await upsertDatasets(datasets);
      if ("error" in upsertResult) {
        const errorMessage = getErrorMessage(upsertResult.error);
        errorAlert(errorMessage);
        return;
      }

      // eslint-disable-next-line consistent-return
      return datasets[0].fides_key;
    } catch (error) {
      handleError(error);
    }
  };

  const dropdownOptions: Option[] = useMemo(
    () =>
      allDatasets
        ? allDatasets.map((d) => ({
            value: d.fides_key,
            label: `${d.name} (${d.fides_key})` || d.fides_key,
          }))
        : [],
    [allDatasets],
  );
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

const DatasetConfigField = ({ dropdownOptions }: Props) => {
  return (
    <Flex flexDirection="row">
      <DatasetSelect
        label="Dataset"
        labelProps={{
          fontWeight: "semibold",
          fontSize: "sm",
          minWidth: "150px",
        }}
        name={DATASET_FIELD_NAME}
        options={dropdownOptions}
      />
    </Flex>
  );
};

export default DatasetConfigField;
