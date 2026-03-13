import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  Button,
  Flex,
  Icons,
  Select,
  Space,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { useUpdateDatasetMutation } from "~/features/dataset";
import { useGetConnectionConfigDatasetConfigsQuery } from "~/features/datastore-connections";
import { Dataset } from "~/types/api";

import { selectCurrentDataset, setCurrentDataset } from "./dataset-test.slice";
import DatasetNodeEditor from "./DatasetNodeEditor";
import { removeNulls } from "./helpers";

interface EditorSectionProps {
  connectionKey: string;
}

const EditorSection = ({ connectionKey }: EditorSectionProps) => {
  const messageApi = useMessage();
  const dispatch = useAppDispatch();
  const [updateDataset] = useUpdateDatasetMutation();

  const [localDataset, setLocalDataset] = useState<Dataset | undefined>();
  const currentDataset = useAppSelector(selectCurrentDataset);

  const {
    data: datasetConfigs,
    isLoading: isDatasetConfigsLoading,
    refetch: refetchDatasets,
  } = useGetConnectionConfigDatasetConfigsQuery(connectionKey, {
    skip: !connectionKey,
  });

  const datasetOptions = useMemo(
    () =>
      (datasetConfigs?.items || []).map((item) => ({
        value: item.fides_key,
        label: item.fides_key,
      })),
    [datasetConfigs?.items],
  );

  useEffect(() => {
    if (datasetConfigs?.items.length) {
      if (
        !currentDataset ||
        !datasetConfigs.items.find(
          (item) => item.fides_key === currentDataset.fides_key,
        )
      ) {
        const initialDataset = datasetConfigs.items[0];
        dispatch(setCurrentDataset(initialDataset));
      }
    }
  }, [datasetConfigs, currentDataset, dispatch]);

  useEffect(() => {
    if (currentDataset?.ctl_dataset) {
      setLocalDataset(removeNulls(currentDataset.ctl_dataset) as Dataset);
    }
  }, [currentDataset]);

  const handleDatasetChange = async (value: string) => {
    const selectedConfig = datasetConfigs?.items.find(
      (item) => item.fides_key === value,
    );
    if (selectedConfig) {
      dispatch(setCurrentDataset(selectedConfig));
    }
  };

  const handleLocalDatasetChange = useCallback((updated: Dataset) => {
    setLocalDataset(updated);
  }, []);

  const handleSave = async () => {
    if (!currentDataset || !localDataset) {
      return;
    }

    const result = await updateDataset(localDataset);

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }

    dispatch(
      setCurrentDataset({
        fides_key: currentDataset.fides_key,
        ctl_dataset: result.data,
      }),
    );
    messageApi.success("Successfully modified dataset");
    await refetchDatasets();
  };

  const handleRefresh = async () => {
    try {
      const { data } = await refetchDatasets();
      const refreshedDataset = data?.items.find(
        (item) => item.fides_key === currentDataset?.fides_key,
      );
      if (refreshedDataset?.ctl_dataset) {
        setLocalDataset(removeNulls(refreshedDataset.ctl_dataset) as Dataset);
      }
      messageApi.success("Successfully refreshed datasets");
    } catch (error) {
      messageApi.error(getErrorMessage(error as FetchBaseQueryError));
    }
  };

  return (
    <Flex
      align="stretch"
      flex="1"
      gap="small"
      vertical
      style={{ height: "100%", minHeight: 0 }}
    >
      <Flex align="center" justify="space-between">
        <Space>
          <Typography.Title level={3} style={{ margin: 0 }}>
            Edit dataset:
          </Typography.Title>
          <Select
            id="format"
            aria-label="Select a dataset"
            data-testid="export-format-select"
            value={currentDataset?.fides_key || ""}
            options={datasetOptions}
            onChange={handleDatasetChange}
            className="w-64"
          />
        </Space>
        <Space>
          <Tooltip
            title="Refresh to load the latest data from the database. This will overwrite any unsaved local changes."
            placement="top"
          >
            <Button
              size="small"
              data-testid="refresh-btn"
              onClick={handleRefresh}
              loading={isDatasetConfigsLoading}
              icon={<Icons.Renew />}
              aria-label="Refresh"
            />
          </Tooltip>
          <Tooltip
            title="Save your changes to update the dataset in the database."
            placement="top"
          >
            <Button htmlType="submit" size="small" onClick={handleSave}>
              Save
            </Button>
          </Tooltip>
        </Space>
      </Flex>
      <div
        style={{
          flex: "1 1 auto",
          minHeight: 0,
          borderRadius: 8,
          overflow: "hidden",
          border: "1px solid #E2E8F0",
        }}
      >
        {localDataset && (
          <DatasetNodeEditor
            dataset={localDataset}
            onDatasetChange={handleLocalDatasetChange}
          />
        )}
      </div>
    </Flex>
  );
};

export default EditorSection;
