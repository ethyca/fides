import {
  Button,
  Flex,
  Icons,
  Spin,
  Text,
  Tooltip,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import { useCallback } from "react";

import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  type MonitorDeletionImpact,
  useDeleteDiscoveryMonitorMutation,
  useExecuteDiscoveryMonitorMutation,
  useExecuteIdentityProviderMonitorMutation,
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
  onEditClick,
}: {
  monitorId?: string | null;
  isWebsiteMonitor?: boolean;
  isOktaMonitor?: boolean;
  onEditClick: () => void;
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [deleteMonitor, { isLoading: isDeleting }] =
    useDeleteDiscoveryMonitorMutation();
  const [
    fetchDeletionImpact,
    { data: deletionImpact, isLoading: isLoadingImpact },
  ] = useLazyGetMonitorDeletionImpactQuery();

  const { toastResult: toastDeleteResult } = useQueryResultToast({
    defaultErrorMsg: "A problem occurred deleting this monitor",
    defaultSuccessMsg: "Monitor deleted successfully",
  });

  // Use Identity Provider Monitor endpoint for Okta, otherwise use regular endpoint
  const [executeRegularMonitor, { isLoading: executeRegularIsLoading }] =
    useExecuteDiscoveryMonitorMutation();

  const [executeOktaMonitor, { isLoading: executeOktaIsLoading }] =
    useExecuteIdentityProviderMonitorMutation();

  const executeIsLoading = isOktaMonitor
    ? executeOktaIsLoading
    : executeRegularIsLoading;

  const { toastResult: toastExecuteResult } = useQueryResultToast({
    defaultErrorMsg: "A problem occurred initiating monitor execution",
    defaultSuccessMsg: isWebsiteMonitor
      ? WEBSITE_SCAN_SUCCESS_MESSAGE
      : "Monitor execution successfully started",
  });

  const handleOpenDeleteModal = useCallback(() => {
    if (!monitorId) {
      return;
    }
    fetchDeletionImpact({ monitor_config_id: monitorId });
    onOpen();
  }, [monitorId, onOpen, fetchDeletionImpact]);

  if (!monitorId) {
    return null;
  }

  const handleDelete = async () => {
    const result = await deleteMonitor({
      monitor_config_id: monitorId,
    });
    toastDeleteResult(result);
    onClose();
  };

  const handleExecute = async () => {
    const result = isOktaMonitor
      ? await executeOktaMonitor({ monitor_config_key: monitorId })
      : await executeRegularMonitor({ monitor_config_id: monitorId });
    toastExecuteResult(result);
  };

  return (
    <>
      <ConfirmationModal
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={handleDelete}
        title="Delete monitor"
        message={
          <DeleteMonitorMessage
            deletionImpact={deletionImpact}
            isLoadingImpact={isLoadingImpact}
          />
        }
        continueButtonText="Delete"
        isCentered
        isLoading={isDeleting}
      />
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
    </>
  );
};

export default MonitorConfigActionsCell;
