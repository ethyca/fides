import { useRouter } from "next/router";

import ConfirmationModal from "~/features/common/ConfirmationModal";

type Props = {
  nonUpgradeLink: string;
  upgradeLink: string;
  isOpen: boolean;
  isSystem: boolean;
  onClose: () => void;
};

export const UpgradeModal = ({
  nonUpgradeLink,
  upgradeLink,
  isOpen,
  isSystem,
  onClose,
}: Props) => {
  const router = useRouter();
  const templateWord = isSystem ? "system" : "vendor";

  return (
    <ConfirmationModal
      isOpen={isOpen}
      onClose={onClose}
      onCancel={() => {
        router.push(nonUpgradeLink);
      }}
      isCentered
      title={`Upgrade to add multiple ${templateWord}s at once!`}
      message={`You will need to upgrade your subscription to add multiple ${templateWord}s at once. In the meantime you can continue here to add indivual ${templateWord}s manually.`}
      cancelButtonText={`Add ${templateWord}s manually`}
      continueButtonText="Upgrade"
      onConfirm={() => {
        window.open(upgradeLink);
      }}
    />
  );
};
