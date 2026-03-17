import {
  Button,
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalContent as ModalContent,
  ChakraModalFooter as ModalFooter,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  ChakraUseDisclosureReturn as UseDisclosureReturn,
  Icons,
  Tooltip,
} from "fidesui";
import { useState } from "react";

import ClipboardButton from "~/features/common/ClipboardButton";

interface ClientSecretModalProps
  extends Pick<UseDisclosureReturn, "isOpen" | "onClose"> {
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
  const displayed = revealed ? value : "•".repeat(Math.min(value.length, 32));

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
  <Modal isOpen={isOpen} onClose={onClose} isCentered size="lg">
    <ModalOverlay />
    <ModalContent data-testid="client-secret-modal">
      <ModalHeader>
        {context === "created" ? "Client created" : "Secret rotated"}
      </ModalHeader>
      <ModalBody>
        <div className="flex flex-col gap-4">
          <div
            className="flex items-start gap-2 rounded-md border border-yellow-300 bg-yellow-50 px-3 py-2 text-sm text-yellow-800"
            data-testid="secret-warning"
          >
            <Icons.WarningAlt className="mt-0.5 shrink-0" />
            <span>Copy this secret now. It will not be shown again.</span>
          </div>
          <SecretField
            label="Client ID"
            value={clientId}
            data-testid="client-id-display"
          />
          <SecretField
            label="Client secret"
            value={secret}
            redact
            data-testid="client-secret-display"
          />
        </div>
      </ModalBody>
      <ModalFooter>
        <div className="flex justify-end w-full">
          <Button type="primary" onClick={onClose} data-testid="done-btn">
            Done
          </Button>
        </div>
      </ModalFooter>
    </ModalContent>
  </Modal>
);

export default ClientSecretModal;
