import {
  AntButton as Button,
  DeleteIcon,
  EditIcon,
  Tooltip,
  useDisclosure,
} from "fidesui";

import useQueryResultToast from "~/features/common/form/useQueryResultToast";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import ActionButton from "~/features/data-discovery-and-detection/ActionButton";
import {
  useDeleteDiscoveryMonitorMutation,
  useExecuteDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";

const MonitorConfigActionsCell = ({
  monitorId,
  onEditClick,
}: {
  monitorId: string;
  onEditClick: () => void;
}) => {
  const [deleteMonitor] = useDeleteDiscoveryMonitorMutation();
  const { toastResult: toastDeleteResult } = useQueryResultToast({
    defaultErrorMsg: "A problem occurred deleting this monitor",
    defaultSuccessMsg: "Monitor deleted successfully",
  });

  const [executeMonitor, { isLoading: executeIsLoading }] =
    useExecuteDiscoveryMonitorMutation();
  const { toastResult: toastExecuteResult } = useQueryResultToast({
    defaultErrorMsg: "A problem occurred initiating monitor execution",
    defaultSuccessMsg: "Monitor execution successfully started",
  });

  const handleDelete = async () => {
    const result = await deleteMonitor({
      monitor_config_id: monitorId,
    });
    toastDeleteResult(result);
  };

  const { isOpen, onOpen, onClose } = useDisclosure();

  const handleExecute = async () => {
    const result = await executeMonitor({
      monitor_config_id: monitorId,
    });
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
      />
      <div className="flex gap-2">
        <Tooltip label="Edit">
          <Button
            onClick={onEditClick}
            size="small"
            icon={<EditIcon />}
            data-testid="edit-monitor-btn"
            aria-label="Edit monitor"
          />
        </Tooltip>
        <Tooltip label="Delete">
          <Button
            onClick={onOpen}
            size="small"
            icon={<DeleteIcon />}
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
