import {
  Alert,
  Button,
  Card,
  Checkbox,
  Collapse,
  Flex,
  Progress,
  Select,
  Space,
  Spin,
  Tag,
  Typography,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  SeedStepStatus,
  SeedTasksConfig,
  useGetSeedProfileQuery,
  useGetSeedStatusQuery,
  useListSeedProfilesQuery,
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
    key: "sample_resources",
    label: "Sample Resources",
    description:
      "Load sample resources from demo/.fides (systems, datasets, policies).",
  },
  {
    key: "linked_connections",
    label: "Linked Connections",
    description: "Link sample connections to systems.",
  },
  {
    key: "messaging_mailgun",
    label: "Messaging (Mailgun)",
    description:
      "Configure Mailgun for messaging. Requires credentials via a secret profile.",
  },
  {
    key: "storage_s3",
    label: "Storage (S3)",
    description:
      "Configure S3 for storage. Requires credentials via a secret profile.",
  },
  {
    key: "consent_notices",
    label: "Consent Notices",
    description: "Enable default consent notices.",
  },
  {
    key: "consent_experiences",
    label: "Consent Experiences",
    description: "Enable default consent experiences.",
  },
  {
    key: "consent_preferences",
    label: "Consent Preferences",
    description:
      "Generate sample consent preference records for the Consent Report.",
  },
  {
    key: "compass_vendors",
    label: "Compass Vendors",
    description: "Enable default Compass vendors.",
  },
  {
    key: "email_templates",
    label: "Email Templates",
    description: "Update email templates with HTML versions.",
  },
  {
    key: "chat_slack",
    label: "Chat (Slack)",
    description:
      "Configure Slack chat provider for questionnaires. Requires credentials via a secret profile.",
  },
  {
    key: "privacy_assessments",
    label: "Privacy Assessments",
    description: "Generate sample privacy assessments.",
  },
  {
    key: "discovery_monitors",
    label: "Discovery Monitors",
    description:
      "Create discovery monitors. Requires credentials via a secret profile.",
  },
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

const ALL_TASK_KEYS = SEED_SCENARIOS.map((s) => s.key);

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
  const [selectedProfile, setSelectedProfile] = useState<string | undefined>();
  const [taskOverrides, setTaskOverrides] = useState<
    Partial<Record<keyof SeedTasksConfig, boolean>>
  >({});
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [triggerSeed, { isLoading: isTriggering, isError: isTriggerError }] =
    useTriggerSeedMutation();
  const { data: profiles } = useListSeedProfilesQuery();
  const { data: profileDetail, isFetching: isLoadingProfile } =
    useGetSeedProfileQuery(selectedProfile!, {
      skip: !selectedProfile,
    });

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

  // Clear overrides when profile changes
  useEffect(() => {
    setTaskOverrides({});
  }, [selectedProfile]);

  const resolvedTasks = useMemo((): SeedTasksConfig => {
    const tasks: SeedTasksConfig = {};
    ALL_TASK_KEYS.forEach((key) => {
      if (taskOverrides[key] !== undefined) {
        tasks[key] = taskOverrides[key];
      } else if (profileDetail) {
        tasks[key] = profileDetail.tasks[key] ?? false;
      } else {
        tasks[key] = false;
      }
    });
    return tasks;
  }, [taskOverrides, profileDetail]);

  const enabledCount = useMemo(
    () => Object.values(resolvedTasks).filter(Boolean).length,
    [resolvedTasks],
  );

  const overrideCount = Object.keys(taskOverrides).length;

  const handleToggle = useCallback(
    (key: keyof SeedTasksConfig) => {
      const currentValue = resolvedTasks[key] ?? false;
      const profileDefault = profileDetail?.tasks[key] ?? false;
      const newValue = !currentValue;

      setTaskOverrides((prev) => {
        const next = { ...prev };
        if (newValue === profileDefault) {
          // Toggling back to the profile default — remove the override
          delete next[key];
        } else {
          next[key] = newValue;
        }
        return next;
      });
    },
    [resolvedTasks, profileDetail],
  );

  const handleSeed = useCallback(async () => {
    const request: {
      secret_profile?: string;
      tasks: SeedTasksConfig;
    } = {
      secret_profile: selectedProfile,
      tasks: {},
    };

    // Only send overrides as explicit task values — let the backend
    // merge profile defaults for non-overridden tasks.
    if (selectedProfile) {
      ALL_TASK_KEYS.forEach((key) => {
        if (taskOverrides[key] !== undefined) {
          request.tasks[key] = taskOverrides[key];
        }
      });
    }

    const result = await triggerSeed(request)
      .unwrap()
      .catch(() => null);
    if (result) {
      setExecutionId(result.execution_id);
    }
  }, [selectedProfile, taskOverrides, triggerSeed]);

  const isRunning = !!executionId || isTriggering;
  const showStatus = statusData && statusData.status !== "pending";

  return (
    <Card title="Sample data seeding" style={{ maxWidth: 780 }}>
      <Paragraph type="secondary">
        Select a seed profile to populate this environment with synthetic sample
        data for demos and testing. Seeding is idempotent — it is safe to run
        multiple times. Not for production use.
      </Paragraph>

      <Space direction="vertical" size="middle" className="mb-6 w-full">
        <Flex vertical gap="small">
          <Text strong>Seed profile</Text>
          {profiles && profiles.length > 0 ? (
            <Select
              aria-label="Seed profile"
              placeholder="Select a seed profile..."
              value={selectedProfile}
              onChange={(value) => setSelectedProfile(value)}
              disabled={isRunning}
              loading={isLoadingProfile}
              style={{ width: 320 }}
              options={profiles.map((p) => ({ label: p, value: p }))}
            />
          ) : (
            <Alert
              type="info"
              message="No seed profiles configured. Set FIDESPLUS__SAMPLE_DATA__PROFILES to configure 1Password-backed profiles."
              showIcon
            />
          )}
        </Flex>

        {isLoadingProfile ? (
          <Spin size="small">
            <Text type="secondary">Loading profile details...</Text>
          </Spin>
        ) : null}

        {profileDetail && !isLoadingProfile ? (
          <Text type="secondary">
            This profile enables{" "}
            <Text strong>
              {Object.values(profileDetail.tasks).filter(Boolean).length}
            </Text>{" "}
            scenarios by default. {enabledCount} will run
            {overrideCount > 0 ? ` (${overrideCount} overridden)` : ""}.
          </Text>
        ) : null}
      </Space>

      {profileDetail ? (
        <Collapse
          className="mb-6"
          items={[
            {
              key: "overrides",
              label: (
                <Text>
                  Scenario overrides
                  {overrideCount > 0 ? (
                    <Tag color="info" className="ml-2">
                      {overrideCount}
                    </Tag>
                  ) : null}
                </Text>
              ),
              children: (
                <Space direction="vertical" size="small" className="w-full">
                  <Flex justify="space-between" align="center" className="mb-2">
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      Toggle scenarios on or off. Checked items match the
                      profile default unless overridden.
                    </Text>
                    {overrideCount > 0 ? (
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setTaskOverrides({})}
                        disabled={isRunning}
                      >
                        Reset to defaults
                      </Button>
                    ) : null}
                  </Flex>
                  {SEED_SCENARIOS.map((scenario) => {
                    const isDefault =
                      profileDetail.tasks[scenario.key] ?? false;
                    const isOverridden =
                      taskOverrides[scenario.key] !== undefined;

                    return (
                      <Checkbox
                        key={scenario.key}
                        checked={resolvedTasks[scenario.key] ?? false}
                        onChange={() => handleToggle(scenario.key)}
                        disabled={isRunning}
                      >
                        <Text strong>{scenario.label}</Text>
                        {isOverridden ? (
                          <Tag
                            color="info"
                            className="ml-2"
                            style={{ fontSize: 11 }}
                          >
                            overridden
                          </Tag>
                        ) : (
                          <Tag className="ml-2" style={{ fontSize: 11 }}>
                            default: {isDefault ? "on" : "off"}
                          </Tag>
                        )}
                        <br />
                        <Text type="secondary">{scenario.description}</Text>
                      </Checkbox>
                    );
                  })}
                </Space>
              ),
            },
          ]}
        />
      ) : null}

      <Flex gap="small" align="center">
        <Button
          type="primary"
          onClick={handleSeed}
          disabled={!selectedProfile || enabledCount === 0 || isRunning}
          loading={isRunning}
        >
          {isRunning ? "Seeding..." : `Seed data (${enabledCount} scenarios)`}
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
