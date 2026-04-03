import { Button, Icons, Modal, Tooltip } from "fidesui";
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
  const displayed = revealed ? value : "•".repeat(32);

  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm font-medium">{label}</span>
      <div className="flex items-center gap-1 rounded-md border bg-gray-50 px-3 py-2 font-mono text-sm">
        <span className="flex-1 break-all">{displayed}</span>
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
      </div>
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
    <div className="flex flex-col gap-4 py-2">
      <div
        className="flex items-start gap-2 rounded-md border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-800"
        data-testid="secret-warning"
      >
        <Icons.WarningAlt className="mt-0.5 shrink-0" />
        <span>Copy this secret now. It will not be shown again.</span>
      </div>
      <SecretField label="Client ID" value={clientId} />
      <SecretField label="Client secret" value={secret} redact />
    </div>
  </Modal>
);

export default ClientSecretModal;
