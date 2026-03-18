import { Switch, SwitchProps, Typography, useMessage, useModal } from "fidesui";

import { isErrorResult, RTKResult } from "~/types/errors";

import { getErrorMessage } from "../../helpers";

const { Text } = Typography;

interface EnableCellProps extends Omit<SwitchProps, "value" | "onToggle"> {
  enabled: boolean;
  onToggle: (data: boolean) => Promise<RTKResult>;
  title: string;
  message: string;
  isDisabled?: boolean;
}

export const EnableCell = ({
  enabled,
  onToggle,
  title,
  message: messageText,
  isDisabled,
  ...props
}: EnableCellProps) => {
  const modal = useModal();
  const messageApi = useMessage();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    const result = await onToggle(enable);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    }
  };

  const handleToggle = async (checked: boolean) => {
    if (checked) {
      await handlePatch({ enable: true });
    } else {
      modal.confirm({
        title,
        content: <Text>{messageText}</Text>,
        okText: "Confirm",
        centered: true,
        icon: null,
        onOk: () => handlePatch({ enable: false }),
      });
    }
  };

  return (
    <Switch
      checked={enabled}
      onChange={handleToggle}
      disabled={isDisabled}
      data-testid="toggle-switch"
      {...props}
    />
  );
};
