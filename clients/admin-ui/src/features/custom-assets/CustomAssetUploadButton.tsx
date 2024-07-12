import { Button, useDisclosure } from "fidesui";
import React from "react";

import { CustomAssetType } from "~/types/api/models/CustomAssetType";

import CustomAssetUploadModal from "./CustomAssetUploadModal";

type CustomAssetUploadButtonProps = {
  assetType: CustomAssetType;
};

const CustomAssetUploadButton = ({
  assetType,
}: CustomAssetUploadButtonProps) => {
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
