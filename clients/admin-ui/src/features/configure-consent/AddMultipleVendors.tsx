import { Button, useDisclosure } from "@fidesui/react";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import { UpgradeModal } from "~/features/common/modals/UpgradeModal";
import { ADD_MULTIPLE_VENDORS_ROUTE } from "~/features/common/nav/v2/routes";

type Props = {
  onCancel: () => void;
};

export const AddMultipleVendors = ({ onCancel }: Props) => {
  const router = useRouter();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { dictionaryService: isCompassEnabled } = useFeatures();
  return (
    <>
      <UpgradeModal
        isOpen={isOpen}
        onClose={onClose}
        onConfirm={() => {
          window.open("https://fid.es/upgrade-compass");
        }}
        onCancel={() => {
          onClose();
          onCancel();
        }}
      />
      <Button
        onClick={() => {
          if (isCompassEnabled) {
            router.push(ADD_MULTIPLE_VENDORS_ROUTE);
          } else {
            onOpen();
          }
        }}
        data-testid="add-multiple-vendors-btn"
        size="sm"
        colorScheme="primary"
      >
        Add multiple vendors
      </Button>
    </>
  );
};
