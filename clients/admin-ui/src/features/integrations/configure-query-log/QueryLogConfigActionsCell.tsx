import { Button, Flex, Icons, Tooltip, useMessage, useModal } from "fidesui";
import { useCallback } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import {
  type QueryLogConfigResponse,
  useDeleteQueryLogConfigMutation,
  useTestQueryLogConnectionMutation,
  useTriggerQueryLogPollMutation,
} from "~/features/integrations/configure-query-log/query-log-config.slice";
import { RTKErrorResult } from "~/types/errors/api";

interface QueryLogConfigActionsCellProps {
  config: QueryLogConfigResponse;
  onEdit: () => void;
}

const QueryLogConfigActionsCell = ({
  config,
  onEdit,
}: QueryLogConfigActionsCellProps) => {
  const message = useMessage();
  const modal = useModal();
  const [deleteConfig] = useDeleteQueryLogConfigMutation();
  const [testConnection, { isLoading: isTestLoading }] =
    useTestQueryLogConnectionMutation();
  const [triggerPoll, { isLoading: isPollLoading }] =
    useTriggerQueryLogPollMutation();

  const handleTest = useCallback(async () => {
    try {
      const result = await testConnection(config.key).unwrap();
      if (result.success) {
        message.success(result.message);
      } else {
        message.error(result.message);
      }
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "Unable to test connection. Please try again.",
        ),
      );
    }
  }, [config.key, testConnection, message]);

  const handlePoll = useCallback(async () => {
    try {
      const result = await triggerPoll(config.key).unwrap();
      message.success(`${result.entries_processed} entries processed`);
    } catch (error) {
      message.error(
        getErrorMessage(error as RTKErrorResult["error"], "Poll failed."),
      );
    }
  }, [config.key, triggerPoll, message]);

  const handleDelete = useCallback(() => {
    modal.confirm({
      title: "Delete query log config",
      content: `Are you sure you want to delete "${config.name}"? This action cannot be undone.`,
      okText: "Delete",
      centered: true,
      icon: null,
      onOk: async () => {
        try {
          await deleteConfig(config.key).unwrap();
          message.success("Query log config deleted successfully");
        } catch (error) {
          message.error(
            getErrorMessage(
              error as RTKErrorResult["error"],
              "Failed to delete query log config.",
            ),
          );
        }
      },
    });
  }, [config.key, config.name, modal, deleteConfig, message]);

  return (
    <Flex gap={8}>
      <Tooltip title="Test connection">
        <Button
          onClick={handleTest}
          size="small"
          loading={isTestLoading}
          data-testid="test-query-log-btn"
          aria-label="Test connection"
        >
          Test
        </Button>
      </Tooltip>
      <Tooltip title="Poll now">
        <Button
          onClick={handlePoll}
          size="small"
          loading={isPollLoading}
          data-testid="poll-query-log-btn"
          aria-label="Poll now"
        >
          Poll
        </Button>
      </Tooltip>
      <Tooltip title="Edit">
        <Button
          onClick={onEdit}
          size="small"
          icon={<Icons.Edit />}
          data-testid="edit-query-log-btn"
          aria-label="Edit config"
        />
      </Tooltip>
      <Tooltip title="Delete">
        <Button
          onClick={handleDelete}
          size="small"
          icon={<Icons.TrashCan />}
          data-testid="delete-query-log-btn"
          aria-label="Delete config"
        />
      </Tooltip>
    </Flex>
  );
};

export default QueryLogConfigActionsCell;
