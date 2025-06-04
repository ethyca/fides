import {
  AntButton as Button,
  AntFlex as Flex,
  AntTableProps as TableProps,
  Icons,
  useToast,
} from "fidesui";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useDeleteSharedMonitorConfigMutation } from "~/features/monitors/shared-monitor-config.slice";
import { SharedMonitorConfig } from "~/types/api/models/SharedMonitorConfig";
import { isErrorResult } from "~/types/errors";

const useSharedMonitorConfigColumns = ({
  onEditClick,
}: {
  onEditClick: (row: SharedMonitorConfig) => void;
}) => {
  const [deleteMonitorConfig] = useDeleteSharedMonitorConfigMutation();
  const toast = useToast();

  const handleDeleteMonitorConfig = async (id: string) => {
    const result = await deleteMonitorConfig({ id });
    if (isErrorResult(result)) {
      toast(
        errorToastParams(
          getErrorMessage(
            result.error,
            "A problem occurred deleting this config",
          ),
        ),
      );
    } else {
      toast(successToastParams("Monitor config deleted successfully"));
    }
  };

  const columns: TableProps<SharedMonitorConfig>["columns"] = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, data) => {
        return (
          <Flex className="gap-2">
            <Button
              size="small"
              onClick={() => onEditClick(data)}
              icon={<Icons.Edit />}
              data-testid="edit-btn"
            />
            <Button
              size="small"
              onClick={() => handleDeleteMonitorConfig(data.id!)}
              icon={<Icons.TrashCan />}
            />
          </Flex>
        );
      },
    },
  ];

  return columns;
};

export default useSharedMonitorConfigColumns;
