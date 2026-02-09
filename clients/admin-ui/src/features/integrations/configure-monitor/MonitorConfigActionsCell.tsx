import {
  Button,
  Icons,
  Tooltip,
  useChakraDisclosure as useDisclosure,
} from "fidesui";
import { useCallback, useState } from "react";

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
  deletionImpact?: MonitorDeletionImpact | null;
  isLoadingImpact: boolean;
}) => {
  if (isLoadingImpact) {
    return <span className="text-gray-600">Loading deletion impact...</span>;
  }

  const resourceCount = deletionImpact?.staged_resource_count ?? 0;
  const linkedDatasets = deletionImpact?.linked_datasets ?? [];
  const activeTaskCount = deletionImpact?.active_task_count ?? 0;

  return (
    <div className="flex flex-col gap-3">
      <span className="text-gray-600">
        Are you sure you want to delete this discovery monitor?{" "}
        <strong>This action cannot be undone.</strong>
      </span>

      {activeTaskCount > 0 && (
        <span className="font-semibold text-orange-700">
          ⚠ This monitor has{" "}
          <strong>
            {activeTaskCount} active task{activeTaskCount !== 1 ? "s" : ""}
          </strong>{" "}
          that will be cancelled.
        </span>
      )}

      {resourceCount > 0 && (
        <span className="text-gray-600">
          This will also permanently delete{" "}
          <strong>
            {resourceCount} staged resource{resourceCount !== 1 ? "s" : ""}
          </strong>{" "}
          discovered by this monitor.
        </span>
      )}

      {linkedDatasets.length > 0 && (
        <div className="mt-1">
          <span className="font-semibold text-orange-700">
            ⚠ The following dataset{linkedDatasets.length !== 1 ? "s" : ""} will
            lose linked data source metadata:
          </span>
          <ul className="ml-5 mt-1 list-disc">
            {linkedDatasets.map((dataset) => (
              <li key={dataset.fides_key} className="text-gray-700">
                {dataset.name ?? dataset.fides_key}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
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
  const [deletionImpact, setDeletionImpact] =
    useState<MonitorDeletionImpact | null>(null);
  const [isLoadingImpact, setIsLoadingImpact] = useState(false);

  const [deleteMonitor, { isLoading: isDeleting }] =
    useDeleteDiscoveryMonitorMutation();
  const [fetchDeletionImpact] = useLazyGetMonitorDeletionImpactQuery();

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

  const handleOpenDeleteModal = useCallback(async () => {
    if (!monitorId) {
      return;
    }
    setIsLoadingImpact(true);
    setDeletionImpact(null);
    onOpen();

    try {
      const result = await fetchDeletionImpact({
        monitor_config_id: monitorId,
      }).unwrap();
      setDeletionImpact(result);
    } catch {
      // If fetching impact fails, still allow deletion with basic message
      setDeletionImpact(null);
    } finally {
      setIsLoadingImpact(false);
    }
  }, [monitorId, onOpen, fetchDeletionImpact]);

  const handleCloseDeleteModal = useCallback(() => {
    onClose();
    setDeletionImpact(null);
  }, [onClose]);

  if (!monitorId) {
    return null;
  }

  const handleDelete = async () => {
    const result = await deleteMonitor({
      monitor_config_id: monitorId,
    });
    toastDeleteResult(result);
    handleCloseDeleteModal();
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
        onClose={handleCloseDeleteModal}
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
      <div className="flex gap-2">
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
      </div>
    </>
  );
};

export default MonitorConfigActionsCell;
