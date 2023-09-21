import { Button, useDisclosure } from "@fidesui/react";
import React from "react";

import CustomAssetUploadModal from "./CustomAssetUploadModal";

interface CustomAssetUploadButtonProps {
  assetKey: string;
}

const CustomAssetUploadButton: React.FC<CustomAssetUploadButtonProps> = ({
  assetKey,
}) => {
  const uploadCustomAssetModal = useDisclosure();

  return (
    <>
      <Button
        variant="outline"
        size="sm"
        ml={2}
        onClick={uploadCustomAssetModal.onOpen}
      >
        Upload stylesheet
      </Button>
      <CustomAssetUploadModal
        isOpen={uploadCustomAssetModal.isOpen}
        onClose={uploadCustomAssetModal.onClose}
        assetKey={assetKey}
      />
    </>
  );
};

export default CustomAssetUploadButton;
