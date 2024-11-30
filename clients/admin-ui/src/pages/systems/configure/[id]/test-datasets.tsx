import { Box, HStack } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";

import { useAppDispatch } from "~/app/hooks";
import FidesSpinner from "~/features/common/FidesSpinner";
import Layout from "~/features/common/Layout";
import { SYSTEM_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDatasetInputsQuery } from "~/features/datastore-connections";
import {
  setActiveSystem,
  useGetSystemByFidesKeyQuery,
} from "~/features/system";
import EditorSection from "~/features/test-datasets/DatasetEditorSection";
import TestResultsSection from "~/features/test-datasets/TestRunnerSection";
import { DatasetConfigSchema } from "~/types/api";

// Helper functions
const getSystemId = (query: { id?: string | string[] }): string => {
  if (!query.id) {
    return "";
  }
  return Array.isArray(query.id) ? query.id[0] : query.id;
};

const TestDatasetPage: NextPage = () => {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [selectedDataset, setSelectedDataset] =
    useState<DatasetConfigSchema | null>(null);
  const [testInput, setTestInput] = useState("{}");

  // Keep track of values for each dataset
  const datasetValuesRef = useRef<Record<string, Record<string, any>>>({});

  const systemId = getSystemId(router.query);
  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(systemId, {
    skip: !systemId,
  });

  const connectionKey = system?.connection_configs?.key || "";

  // Get dataset inputs
  const { data: inputsData, refetch: refetchInputs } = useGetDatasetInputsQuery(
    {
      connectionKey,
      datasetKey: selectedDataset?.fides_key || "",
    },
    {
      skip: !connectionKey || !selectedDataset?.fides_key,
    },
  );

  // Handle dataset input consolidation at the page level
  useEffect(() => {
    if (!selectedDataset?.fides_key || !inputsData) {
      return;
    }

    try {
      const existingValues =
        datasetValuesRef.current[selectedDataset.fides_key] || {};

      const filteredValues: Record<string, any> = {};
      Object.keys(inputsData).forEach((key) => {
        // Preserve existing stored values first
        if (key in existingValues) {
          filteredValues[key] = existingValues[key];
        }
        // Otherwise use default values
        else {
          filteredValues[key] = inputsData[key];
        }
      });

      datasetValuesRef.current[selectedDataset.fides_key] = filteredValues;
      setTestInput(JSON.stringify(filteredValues, null, 2));
    } catch (e) {
      console.error("Error parsing test input:", e);
      setTestInput(JSON.stringify(inputsData, null, 2));
    }
  }, [inputsData, selectedDataset?.fides_key]);

  // Handle input updates
  const handleInputChange = (newInput: string) => {
    setTestInput(newInput);

    if (selectedDataset?.fides_key && inputsData) {
      try {
        const parsedValues = JSON.parse(newInput);
        const validKeys = Object.keys(inputsData);

        const filteredValues: Record<string, any> = {};
        validKeys.forEach((key) => {
          if (key in parsedValues) {
            filteredValues[key] = parsedValues[key];
          }
        });

        datasetValuesRef.current[selectedDataset.fides_key] = filteredValues;
      } catch (error) {
        console.error("Error parsing modified input:", error);
      }
    }
  };

  // Handle dataset refresh/save
  const handleDatasetUpdate = async () => {
    if (selectedDataset?.fides_key && inputsData) {
      // Reset stored values
      delete datasetValuesRef.current[selectedDataset.fides_key];

      // Refetch inputs
      await refetchInputs();
    }
  };

  useEffect(() => {
    dispatch(setActiveSystem(system));
  }, [system, dispatch]);

  if (isLoading) {
    return (
      <Layout title="Systems">
        <FidesSpinner />
      </Layout>
    );
  }

  return (
    <Layout
      title="System inventory"
      mainProps={{
        paddingTop: 0,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <PageHeader
        breadcrumbs={[
          { title: "System inventory", link: SYSTEM_ROUTE },
          {
            title: system?.name || "",
            link: `/systems/configure/${systemId}#integrations`,
          },
          { title: "Test datasets" },
        ]}
        isSticky
      >
        <Box position="relative" />
      </PageHeader>
      <HStack
        alignItems="stretch"
        flex="1"
        minHeight="0"
        spacing="4"
        padding="4 4 4 0"
      >
        <EditorSection
          connectionKey={connectionKey}
          onDatasetChange={setSelectedDataset}
          onSaveOrRefresh={handleDatasetUpdate}
        />
        <TestResultsSection
          connectionKey={connectionKey}
          selectedDataset={selectedDataset}
          testInput={testInput}
          onInputChange={handleInputChange}
        />
      </HStack>
    </Layout>
  );
};

export default TestDatasetPage;
