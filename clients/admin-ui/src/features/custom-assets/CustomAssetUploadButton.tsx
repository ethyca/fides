import { Button, useDisclosure } from "@fidesui/react";
import React from "react";

import { CustomAssetType } from "~/types/api/models/CustomAssetType";

import CustomAssetUploadModal from "./CustomAssetUploadModal";

type CustomAssetUploadButtonProps = {
  assetType: CustomAssetType;
};

const CustomAssetUploadButton: React.FC<CustomAssetUploadButtonProps> = ({
  assetType,
}) => {
  const uploadCustomAssetModal = useDisclosure();

  return (
    <>
      <Button
        variant="outline"
        size="xs"
        ml={2}
        onClick={uploadCustomAssetModal.onOpen}
      >
        Upload stylesheet
      </Button>
      <CustomAssetUploadModal
        isOpen={uploadCustomAssetModal.isOpen}
        onClose={uploadCustomAssetModal.onClose}
        assetType={assetType}
      />
    </>
  );
};

export default CustomAssetUploadButton;
