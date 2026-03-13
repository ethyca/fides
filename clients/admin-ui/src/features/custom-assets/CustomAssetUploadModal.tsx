/* eslint-disable react/no-unescaped-entities */
import {
  Button,
  ChakraBox as Box,
  ChakraText as Text,
  Modal,
  useChakraToast as useToast,
} from "fidesui";
import React, { useState } from "react";
import { useDropzone } from "react-dropzone";

import DocsLink from "~/features/common/DocsLink";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateCustomAssetMutation } from "~/features/plus/plus.slice";
import { CustomAssetType } from "~/types/api/models/CustomAssetType";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  testId?: string;
  assetType: CustomAssetType;
};

const CustomAssetUploadModal = ({
  isOpen,
  onClose,
  testId = "custom-asset-modal",
  assetType,
}: RequestModalProps) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const toast = useToast();
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      const fileExtension = file.name.split(".").pop()?.toLowerCase();

      if (fileExtension !== "css") {
        toast(errorToastParams("Only css files are allowed."));
        return;
      }

      setUploadedFile(acceptedFiles[0]);
    },
  });

  const [updateCustomAsset, { isLoading }] = useUpdateCustomAssetMutation();

  const handleSubmit = async () => {
    if (uploadedFile) {
      const result = await updateCustomAsset({
        assetType,
        file: uploadedFile,
      });
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      toast(successToastParams("Stylesheet uploaded successfully"));
      onClose();
    }
  };

  const renderFileText = () => {
    if (uploadedFile) {
      return <Text>{uploadedFile.name}</Text>;
    }
    if (isDragActive) {
      return <Text>Drop the file here...</Text>;
    }
    return <Text>Click or drag and drop your file here.</Text>;
  };

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      width={MODAL_SIZE.md}
      centered
      destroyOnClose
      data-testid={testId}
      title="Upload stylesheet"
      footer={
        <div className="flex w-full justify-end gap-2">
          <Button
            onClick={onClose}
            data-testid="cancel-btn"
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="primary"
            htmlType="submit"
            disabled={!uploadedFile || isLoading}
            onClick={handleSubmit}
            data-testid="submit-btn"
          >
            Submit
          </Button>
        </div>
      }
    >
      <Text fontSize="sm" mb={4}>
        To customize the appearance of your consent experiences, you may upload
        a CSS stylesheet.{" "}
        <DocsLink href="https://raw.githubusercontent.com/ethyca/fides/main/clients/fides-js/src/components/fides.css">
          Download a template
        </DocsLink>{" "}
        as a helpful starting point.
        <DocsLink href="https://fid.es/customize-styles">
          Learn more about customizing styles
        </DocsLink>
        .
      </Text>
      <Box
        {...getRootProps()}
        bg={isDragActive ? "gray.100" : "gray.50"}
        border="2px dashed"
        borderColor={isDragActive ? "gray.300" : "gray.200"}
        borderRadius="md"
        cursor="pointer"
        minHeight="150px"
        display="flex"
        alignItems="center"
        justifyContent="center"
        textAlign="center"
      >
        <input {...getInputProps()} />
        {renderFileText()}
      </Box>
    </Modal>
  );
};

export default CustomAssetUploadModal;
