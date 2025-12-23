import {
  AntButton as Button,
  AntTooltip as Tooltip,
  Icons,
  useDisclosure,
} from "fidesui";

import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  useDeleteDiscoveryMonitorMutation,
  useExecuteDiscoveryMonitorMutation,
  useExecuteIdentityProviderMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const WEBSITE_SCAN_SUCCESS_MESSAGE =
  "Scanning your website now. Once the monitor is finished, results can be found in the action center.";

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

  if (!monitorId) {
    return null;
  }

  const handleDelete = async () => {
    const result = await deleteMonitor({
      monitor_config_id: monitorId,
    });
    toastDeleteResult(result);
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
        message="Are you sure you want to delete this discovery monitor?"
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
            onClick={onOpen}
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
