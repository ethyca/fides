import {
  useGetAllDatastoreConnectionsQuery,
  useGetAllEnabledAccessManualHooksQuery as useGetManualIntegrationsQuery,
} from "datastore-connections/datastore-connection.slice";
import {
  AntButton as Button,
  AntTypography as Typography,
  Box,
  Flex,
  Stack,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import { useGetTasksQuery } from "~/features/manual-tasks/manual-tasks.slice";
import {
  ConnectionConfigurationResponse,
  ConnectionType,
  ManualFieldStatus,
} from "~/types/api";

import { PRIVACY_REQUESTS_ROUTE } from "../common/nav/routes";
import ManualProcessingList from "./manual-processing/ManualProcessingList";
import { PrivacyRequestEntity } from "./types";

type PrivacyRequestDetailsManualTaskTabProps = {
  subjectRequest: PrivacyRequestEntity;
  onComplete?: () => void;
};

const PrivacyRequestDetailsManualTaskTab = ({
  subjectRequest,
  onComplete,
}: PrivacyRequestDetailsManualTaskTabProps) => {
  const router = useRouter();

  // Fetch new manual task connections
  const { data: connectionsResponse } = useGetAllDatastoreConnectionsQuery({});
  const manualTaskConnections = useMemo(
    () =>
      connectionsResponse?.items?.filter(
        (connection: ConnectionConfigurationResponse) =>
          connection.connection_type === ConnectionType.MANUAL_TASK,
      ) || [],
    [connectionsResponse],
  );

  // Fetch legacy manual webhook connections
  const { data: legacyManualIntegrations } = useGetManualIntegrationsQuery();
  const hasLegacyManualIntegrations =
    (legacyManualIntegrations || []).length > 0;

  // Fetch tasks for this privacy request
  const { data: tasksData } = useGetTasksQuery({
    page: 1,
    size: 100,
    privacyRequestId: subjectRequest.id,
  });

  const tasks = tasksData?.items || [];
  const totalTasks = tasks.length;
  const pendingTasks = tasks.filter(
    (task) => task.status === ManualFieldStatus.NEW,
  ).length;

  const hasManualTaskConnections = manualTaskConnections.length > 0;
  const hasAnyManualFeatures =
    hasManualTaskConnections || hasLegacyManualIntegrations;

  const handleViewTasksClick = () => {
    router.push({
      pathname: PRIVACY_REQUESTS_ROUTE,
      query: { privacy_request_id: subjectRequest.id },
      hash: "#manual-tasks",
    });
  };

  if (!hasAnyManualFeatures) {
    return (
      <Box p={4}>
        <Typography.Text type="secondary">
          No manual tasks or legacy manual steps configured for this request.
        </Typography.Text>
      </Box>
    );
  }

  return (
    <Stack spacing={6}>
      {/* New Manual Tasks Section */}
      {hasManualTaskConnections && (
        <Box>
          <Typography.Title level={4} style={{ marginBottom: 12 }}>
            Manual tasks
          </Typography.Title>
          <Stack spacing={2}>
            <Typography.Text>
              <strong>{totalTasks}</strong> task{totalTasks !== 1 ? "s" : ""}{" "}
              linked to this privacy request
            </Typography.Text>
            <Typography.Text>
              <strong>{pendingTasks}</strong> pending task
              {pendingTasks !== 1 ? "s" : ""}
            </Typography.Text>
            {totalTasks > 0 && (
              <div className="mt-2">
                <Button type="primary" onClick={handleViewTasksClick}>
                  View all tasks for this request →
                </Button>
              </div>
            )}
          </Stack>
        </Box>
      )}

      {/* Legacy Manual Steps Section */}
      {hasLegacyManualIntegrations && (
        <Box>
          <Flex alignItems="center" style={{ marginBottom: 12 }}>
            <Typography.Title level={4} style={{ margin: 0, marginRight: 8 }}>
              Manual steps (legacy)
            </Typography.Title>
            <InfoTooltip label="This is the legacy manual steps feature. The new manual tasks feature provides more advanced capabilities and better user experience." />
          </Flex>
          <ManualProcessingList
            subjectRequest={subjectRequest}
            onComplete={onComplete || (() => {})}
          />
        </Box>
      )}
    </Stack>
  );
};

export default PrivacyRequestDetailsManualTaskTab;
