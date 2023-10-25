import ConfirmationModal from "~/features/common/ConfirmationModal";

type Props = {
  onConfirm: () => void;
  onCancel: () => void;
  isOpen: boolean;
  onClose: () => void;
};

export const UpgradeModal = ({
  onCancel,
  onConfirm,
  isOpen,
  onClose,
}: Props) => (
  <ConfirmationModal
    isOpen={isOpen}
    onClose={onClose}
    onCancel={onCancel}
    isCentered
    title="Upgrade to choose vendors"
    message="To choose vendors and have system information auto-populated using Fides Compass, you will need to upgrade Fides. Meanwhile, you can manually add individual systems using the button below."
    cancelButtonText="Add vendors manually"
    continueButtonText="Upgrade"
    onConfirm={onConfirm}
  />
);
