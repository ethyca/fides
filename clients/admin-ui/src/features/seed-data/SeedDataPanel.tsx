import {
  Alert,
  Button,
  Card,
  Checkbox,
  Flex,
  Progress,
  Space,
  Tag,
  Typography,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import {
  SeedStepStatus,
  SeedTasksConfig,
  useGetSeedStatusQuery,
  useTriggerSeedMutation,
} from "~/features/seed-data/seed-data.slice";

const { Paragraph, Text } = Typography;

interface SeedScenario {
  key: keyof SeedTasksConfig;
  label: string;
  description: string;
}

const SEED_SCENARIOS: SeedScenario[] = [
  {
    key: "pbac",
    label: "PBAC (Access Control)",
    description:
      "Seed data purposes, data consumers, datasets, a mock query log integration, and 60 days of access control history.",
  },
  {
    key: "dashboard",
    label: "Dashboard (Landing Page)",
    description:
      "Populate the landing page dashboard with privacy requests, system coverage metrics, audit activity, staged resources, and 30 days of trend history.",
  },
];

const STATUS_COLORS = {
  pending: "default",
  in_progress: "info",
  complete: "success",
  skipped: "warning",
  error: "error",
} as const;

const StepStatusTag = ({ status }: { status: SeedStepStatus }) => {
  const color =
    STATUS_COLORS[status.status as keyof typeof STATUS_COLORS] ?? "default";
  return <Tag color={color}>{status.status.replace("_", " ")}</Tag>;
};

const computeProgress = (steps: Record<string, SeedStepStatus>): number => {
  const entries = Object.values(steps);
  if (entries.length === 0) {
    return 0;
  }
  const done = entries.filter(
    (step) =>
      step.status === "complete" ||
      step.status === "skipped" ||
      step.status === "error",
  ).length;
  return Math.round((done / entries.length) * 100);
};

const SeedDataPanel = () => {
  const [selectedTasks, setSelectedTasks] = useState<
    Set<keyof SeedTasksConfig>
  >(new Set());
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [triggerSeed, { isLoading: isTriggering, isError: isTriggerError }] =
    useTriggerSeedMutation();

  // Poll for status when an execution is in progress
  const { data: statusData } = useGetSeedStatusQuery(executionId!, {
    skip: !executionId,
    // Seed tasks complete within seconds; 2s polling is intentional for this dev-only tool.
    pollingInterval: 2000,
  });

  // Stop polling when execution completes
  useEffect(() => {
    if (
      statusData &&
      (statusData.status === "complete" || statusData.status === "error")
    ) {
      setExecutionId(null);
    }
  }, [statusData]);

  const handleToggle = useCallback((key: keyof SeedTasksConfig) => {
    setSelectedTasks((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }, []);

  const handleSeed = useCallback(async () => {
    const tasks: SeedTasksConfig = {};
    selectedTasks.forEach((key) => {
      tasks[key] = true;
    });

    const result = await triggerSeed({ tasks })
      .unwrap()
      .catch(() => null);
    if (result) {
      setExecutionId(result.execution_id);
    }
  }, [selectedTasks, triggerSeed]);

  const isRunning = !!executionId || isTriggering;
  const showStatus = statusData && statusData.status !== "pending";

  return (
    <Card title="Seed scenarios" style={{ maxWidth: 720 }}>
      <Paragraph type="secondary">
        Select which data scenarios to seed into this environment. Seeding is
        idempotent — it is safe to run multiple times.
      </Paragraph>

      <Space direction="vertical" size="middle" className="mb-6 w-full">
        {SEED_SCENARIOS.map((scenario) => (
          <Checkbox
            key={scenario.key}
            checked={selectedTasks.has(scenario.key)}
            onChange={() => handleToggle(scenario.key)}
            disabled={isRunning}
          >
            <Text strong>{scenario.label}</Text>
            <br />
            <Text type="secondary">{scenario.description}</Text>
          </Checkbox>
        ))}
      </Space>

      <Flex gap="small" align="center">
        <Button
          type="primary"
          onClick={handleSeed}
          disabled={selectedTasks.size === 0 || isRunning}
          loading={isRunning}
        >
          {isRunning ? "Seeding..." : "Seed data"}
        </Button>
      </Flex>

      {isTriggerError ? (
        <Alert
          type="error"
          message="Failed to start seed. Please try again."
          className="mt-4"
          showIcon
        />
      ) : null}

      {showStatus ? (
        <Flex vertical gap="small" className="mt-4">
          <Progress
            percent={computeProgress(statusData.steps)}
            status={statusData.status === "error" ? "exception" : undefined}
          />
          <Space direction="vertical" size="small" className="mt-2 w-full">
            {Object.entries(statusData.steps).map(([stepName, stepStatus]) => (
              <Flex key={stepName} justify="space-between" align="center">
                <Text>{stepName.replace(/_/g, " ")}</Text>
                <StepStatusTag status={stepStatus} />
              </Flex>
            ))}
          </Space>
          {statusData.error ? (
            <Alert
              type="error"
              message={statusData.error}
              className="mt-2"
              showIcon
            />
          ) : null}
          {statusData.status === "complete" ? (
            <Alert
              type="success"
              message="Seed completed successfully"
              className="mt-2"
              showIcon
            />
          ) : null}
        </Flex>
      ) : null}
    </Card>
  );
};

export default SeedDataPanel;
