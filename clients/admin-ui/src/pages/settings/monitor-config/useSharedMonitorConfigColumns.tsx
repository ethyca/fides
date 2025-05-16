import { AntButton, AntFlex, AntTableProps, Icons, useToast } from "fidesui";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import { MONITOR_CONFIG_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useDeleteSharedMonitorConfigMutation } from "~/features/monitors/shared-monitor-config.slice";
import { SharedMonitorConfig } from "~/types/api/models/SharedMonitorConfig";
import { isErrorResult } from "~/types/errors";

const useSharedMonitorConfigColumns = () => {
  const [deleteMonitorConfig] = useDeleteSharedMonitorConfigMutation();

  const router = useRouter();

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

  const columns: AntTableProps<SharedMonitorConfig>["columns"] = [
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
          <AntFlex className="gap-2">
            <AntButton
              size="small"
              onClick={() => router.push(`${MONITOR_CONFIG_ROUTE}/${data.id}`)}
              icon={<Icons.Edit />}
            />
            <AntButton
              size="small"
              onClick={() => handleDeleteMonitorConfig(data.id!)}
              icon={<Icons.TrashCan />}
            />
          </AntFlex>
        );
      },
    },
  ];

  return columns;
};

export default useSharedMonitorConfigColumns;
