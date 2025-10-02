import {
  AntMessage as message,
  AntSwitch as Switch,
  AntSwitchProps as SwitchProps,
  AntTypography as Typography,
  useDisclosure,
} from "fidesui";

import { isErrorResult, RTKResult } from "~/types/errors";

import { getErrorMessage } from "../../helpers";
import ConfirmationModal from "../../modals/ConfirmationModal";

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
  const modal = useDisclosure();
  const [messageApi, messageContext] = message.useMessage();
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
      modal.onOpen();
    }
  };

  return (
    <>
      {messageContext}
      <Switch
        checked={enabled}
        onChange={handleToggle}
        disabled={isDisabled}
        data-testid="toggle-switch"
        {...props}
      />
      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          handlePatch({ enable: false });
          modal.onClose();
        }}
        title={title}
        message={<Text>{messageText}</Text>}
        continueButtonText="Confirm"
        isCentered
      />
    </>
  );
};
