import {
  Button,
  Flex,
  Space,
  Spin,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  DATASET_DETAIL_ROUTE,
  DATASET_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  useGetDatasetByKeyQuery,
  useUpdateDatasetMutation,
} from "~/features/dataset/dataset.slice";
import DatasetNodeEditor from "~/features/test-datasets/DatasetNodeEditor";
import { removeNulls } from "~/features/test-datasets/helpers";
import { Dataset } from "~/types/api";

const DatasetGraphEditorPage: NextPage = () => {
  const router = useRouter();
  const messageApi = useMessage();
  const datasetId = router.query.datasetId as string;

  const {
    data: serverDataset,
    isError,
    error,
  } = useGetDatasetByKeyQuery(datasetId, { skip: !datasetId });
  const [updateDataset] = useUpdateDatasetMutation();

  const [localDataset, setLocalDataset] = useState<Dataset | undefined>();
  const savedDatasetJson = useRef<string>("");
  const [editorKey, setEditorKey] = useState(0);

  // Initialize local state from server data
  useEffect(() => {
    if (serverDataset) {
      const cleaned = removeNulls(serverDataset) as Dataset;
      setLocalDataset(cleaned);
      savedDatasetJson.current = JSON.stringify(cleaned);
    }
  }, [serverDataset]);

  const isDirty = useMemo(() => {
    if (!localDataset) {
      return false;
    }
    return JSON.stringify(localDataset) !== savedDatasetJson.current;
  }, [localDataset]);

  const handleDatasetChange = useCallback((updated: Dataset) => {
    setLocalDataset(updated);
  }, []);

  const handleSave = useCallback(async () => {
    if (!localDataset) {
      return;
    }

    const result = await updateDataset(localDataset);

    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }

    const cleaned = removeNulls(result.data) as Dataset;
    setLocalDataset(cleaned);
    savedDatasetJson.current = JSON.stringify(cleaned);
    messageApi.success("Successfully saved dataset");
  }, [localDataset, updateDataset, messageApi]);

  const handleReset = useCallback(() => {
    if (!savedDatasetJson.current) {
      return;
    }
    setLocalDataset(JSON.parse(savedDatasetJson.current) as Dataset);
    setEditorKey((k) => k + 1);
  }, []);

  const datasetName = serverDataset?.name || datasetId;

  if (isError) {
    return (
      <Layout title="Datasets">
        <ErrorPage
          error={error}
          defaultMessage={`Could not load dataset ${datasetId}`}
        />
      </Layout>
    );
  }

  return (
    <Layout title={`Edit ${datasetName}`}>
      <PageHeader
        heading="Datasets"
        breadcrumbItems={[
          { title: "All datasets", href: DATASET_ROUTE },
          {
            title: datasetName,
            href: {
              pathname: DATASET_DETAIL_ROUTE,
              query: { datasetId: encodeURIComponent(datasetId) },
            },
          },
          { title: "Visual editor" },
        ]}
        rightContent={
          <Space>
            {isDirty && (
              <Typography.Text type="warning" className="text-xs">
                Unsaved changes
              </Typography.Text>
            )}
            {isDirty && (
              <Button data-testid="discard-btn" onClick={handleReset}>
                Reset
              </Button>
            )}
            <Tooltip
              title="Save your changes to update the dataset in the database."
              placement="top"
            >
              <Button type="primary" disabled={!isDirty} onClick={handleSave}>
                Save
              </Button>
            </Tooltip>
          </Space>
        }
      />
      <Flex
        vertical
        style={{
          flex: "1 1 auto",
          minHeight: 0,
          height: "100%",
          borderRadius: 8,
          overflow: "hidden",
          border: "1px solid var(--fidesui-neutral-200)",
        }}
      >
        {localDataset ? (
          <DatasetNodeEditor
            key={editorKey}
            dataset={localDataset}
            onDatasetChange={handleDatasetChange}
            allowAddCollection
            allowNameEditing
          />
        ) : (
          <Spin />
        )}
      </Flex>
    </Layout>
  );
};

export default DatasetGraphEditorPage;
