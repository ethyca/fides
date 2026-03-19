import {
  Button,
  Flex,
  Icons,
  Spin,
  Text,
  Tooltip,
  useMessage,
  useModal,
} from "fidesui";
import { useCallback } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  type MonitorDeletionImpact,
  useDeleteDiscoveryMonitorMutation,
  useExecuteDiscoveryMonitorMutation,
  useExecuteIdentityProviderMonitorMutation,
  useExecuteInfraMonitorMutation,
  useLazyGetMonitorDeletionImpactQuery,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const WEBSITE_SCAN_SUCCESS_MESSAGE =
  "Scanning your website now. Once the monitor is finished, results can be found in the action center.";

const DeleteMonitorMessage = ({
  deletionImpact,
  isLoadingImpact,
}: {
  deletionImpact?: MonitorDeletionImpact;
  isLoadingImpact: boolean;
}) => {
  if (isLoadingImpact) {
    return <Spin />;
  }

  // Note: staged_resource_count is intentionally omitted from this modal.
  // Showing staged resource counts introduces more confusion than value:
  // counts aligned with the action center would misrepresent the fact that
  // some approved/ignored staged resources are also being deleted, while
  // misaligned counts are simply confusing. The BE API still exposes this
  // count for anyone who wants to inspect it directly.
  const linkedDatasets = deletionImpact?.linked_datasets ?? [];
  const activeTaskCount = deletionImpact?.active_task_count ?? 0;
  const systemCount = deletionImpact?.associated_system_count ?? 0;

  return (
    <Flex vertical gap={12}>
      <Text>
        Are you sure you want to delete this discovery monitor?{" "}
        <Text strong>This action cannot be undone.</Text>
      </Text>

      <Text>
        All action center resources discovered by this monitor will be
        permanently deleted.
      </Text>

      {activeTaskCount > 0 && (
        <Text strong type="warning">
          This monitor has {activeTaskCount} active task
          {activeTaskCount !== 1 ? "s" : ""} that will be cancelled.
        </Text>
      )}

      {systemCount > 0 && (
        <Text>
          <Text strong>
            {systemCount} system{systemCount !== 1 ? "s" : ""}
          </Text>{" "}
          associated with this monitor&apos;s resources will be affected.
        </Text>
      )}

      {linkedDatasets.length > 0 && (
        <Flex vertical gap={4} className="mt-1">
          <Text strong type="warning">
            The following dataset{linkedDatasets.length !== 1 ? "s" : ""} will
            lose linked data source metadata:
          </Text>
          <ul className="ml-5 list-disc">
            {linkedDatasets.map((dataset) => (
              <li key={dataset.fides_key}>
                <Text>{dataset.name ?? dataset.fides_key}</Text>
              </li>
            ))}
          </ul>
        </Flex>
      )}
    </Flex>
  );
};

const MonitorConfigActionsCell = ({
  monitorId,
  isWebsiteMonitor,
  isOktaMonitor,
  isAWSMonitor,
  onEditClick,
}: {
  monitorId?: string | null;
  isWebsiteMonitor?: boolean;
  isOktaMonitor?: boolean;
  isAWSMonitor?: boolean;
  onEditClick: () => void;
}) => {
  const modal = useModal();
  const message = useMessage();

  const [deleteMonitor] = useDeleteDiscoveryMonitorMutation();
  const [fetchDeletionImpact] = useLazyGetMonitorDeletionImpactQuery();

  // Use the appropriate execute endpoint based on monitor type
  const [executeRegularMonitor, { isLoading: executeRegularIsLoading }] =
    useExecuteDiscoveryMonitorMutation();

  const [executeOktaMonitor, { isLoading: executeOktaIsLoading }] =
    useExecuteIdentityProviderMonitorMutation();

  const [executeInfraMonitor, { isLoading: executeInfraIsLoading }] =
    useExecuteInfraMonitorMutation();

  const executeIsLoading = isOktaMonitor
    ? executeOktaIsLoading
    : isAWSMonitor
      ? executeInfraIsLoading
      : executeRegularIsLoading;

  const handleOpenDeleteModal = useCallback(async () => {
    if (!monitorId) {
      return;
    }
    const { data } = await fetchDeletionImpact({
      monitor_config_id: monitorId,
    });
    modal.confirm({
      title: "Delete monitor",
      content: (
        <DeleteMonitorMessage deletionImpact={data} isLoadingImpact={false} />
      ),
      okText: "Delete",
      centered: true,
      icon: null,
      onOk: async () => {
        const result = await deleteMonitor({
          monitor_config_id: monitorId,
        });
        if (isErrorResult(result)) {
          message.error(
            getErrorMessage(
              result.error,
              "A problem occurred deleting this monitor",
            ),
          );
        } else {
          message.success("Monitor deleted successfully");
        }
      },
    });
  }, [monitorId, modal, fetchDeletionImpact, deleteMonitor, message]);

  if (!monitorId) {
    return null;
  }

  const handleExecute = async () => {
    let result;
    if (isOktaMonitor) {
      result = await executeOktaMonitor({ monitor_config_key: monitorId });
    } else if (isAWSMonitor) {
      result = await executeInfraMonitor({ monitor_config_key: monitorId! });
    } else {
      result = await executeRegularMonitor({ monitor_config_id: monitorId });
    }

    if (isErrorResult(result)) {
      message.error(
        getErrorMessage(
          result.error,
          "A problem occurred initiating monitor execution",
        ),
      );
    } else {
      message.success(
        isWebsiteMonitor
          ? WEBSITE_SCAN_SUCCESS_MESSAGE
          : "Monitor execution successfully started",
      );
    }
  };

  return (
    <Flex gap={8}>
      <Tooltip title="Edit">
        <Button
          onClick={onEditClick}
          size="small"
          icon={<Icons.Edit />}
          data-testid="edit-monitor-btn"
          aria-label="Edit monitor"
        />
      </Tooltip>
      <Tooltip title="Delete">
        <Button
          onClick={handleOpenDeleteModal}
          size="small"
          icon={<Icons.TrashCan />}
          aria-label="Delete monitor"
          data-testid="delete-monitor-btn"
        />
      </Tooltip>
      <ActionButton
        onClick={handleExecute}
        title="Scan"
        loading={executeIsLoading}
      />
    </Flex>
  );
};

export default MonitorConfigActionsCell;
