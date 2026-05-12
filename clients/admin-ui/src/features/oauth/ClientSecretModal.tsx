import { Alert, Button, Flex, Icons, Input, Modal, Tooltip } from "fidesui";
import { useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";

interface ClientSecretModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientId: string;
  secret: string;
  /** "created" when shown after initial creation, "rotated" after rotation */
  context: "created" | "rotated";
}

const SecretField = ({
  label,
  value,
  redact = false,
}: {
  label: string;
  value: string;
  redact?: boolean;
}) => {
  const [revealed, setRevealed] = useState(!redact);

  const suffix = (
    <span className="flex items-center gap-1">
      {redact && (
        <Tooltip title={revealed ? "Hide" : "Reveal"} placement="top">
          <Button
            type="text"
            size="small"
            icon={revealed ? <Icons.ViewOff /> : <Icons.View />}
            aria-label={revealed ? "Hide value" : "Reveal value"}
            onClick={() => setRevealed((v) => !v)}
            data-testid={`toggle-reveal-${label.toLowerCase().replace(/\s+/g, "-")}`}
          />
        </Tooltip>
      )}
      <ClipboardButton copyText={value} size="small" />
    </span>
  );

  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm font-medium">{label}</span>
      <Input
        readOnly
        value={redact && !revealed ? "•".repeat(value.length) : value}
        suffix={suffix}
        className="font-mono"
      />
    </div>
  );
};

/**
 * Shows the plaintext client secret exactly once — after creation or rotation.
 * The user must close this modal to proceed; there is no way to retrieve the
 * secret again.
 */
const ClientSecretModal = ({
  isOpen,
  onClose,
  clientId,
  secret,
  context,
}: ClientSecretModalProps) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    title={context === "created" ? "Client created" : "Secret rotated"}
    centered
    footer={
      <div className="flex justify-end">
        <Button type="primary" onClick={onClose} data-testid="done-btn">
          Done
        </Button>
      </div>
    }
    data-testid="client-secret-modal"
  >
    <Flex gap="middle" vertical>
      <Alert
        type="warning"
        showIcon
        data-testid="secret-warning"
        title="Copy this secret now. It will not be shown again."
      />
      <SecretField label="Client ID" value={clientId} />
      <SecretField label="Client secret" value={secret} redact />
    </Flex>
  </Modal>
);

export default ClientSecretModal;
