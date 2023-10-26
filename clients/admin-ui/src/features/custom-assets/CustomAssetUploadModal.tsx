/* eslint-disable react/no-unescaped-entities */
import {
  Box,
  Button,
  ButtonGroup,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  useToast,
} from "@fidesui/react";
import React, { useRef, useState } from "react";
import { useDropzone } from "react-dropzone";

import DocsLink from "~/features/common/DocsLink";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useUpdateCustomAssetMutation } from "~/features/plus/plus.slice";
import { CustomAssetType } from "~/types/api/models/CustomAssetType";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  testId?: string;
  assetType: CustomAssetType;
};

const CustomAssetUploadModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  testId = "custom-asset-modal",
  assetType,
}) => {
  const initialRef = useRef(null);
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
      initialFocusRef={initialRef}
      isOpen={isOpen}
      onClose={onClose}
      size="2xl"
    >
      <ModalOverlay />
      <ModalContent textAlign="left" p={2} data-testid={testId}>
        <ModalHeader tabIndex={-1} ref={initialRef}>
          Upload stylesheet
        </ModalHeader>
        <ModalBody>
          <Text fontSize="sm" mb={4}>
            To customize the appearance of your consent experiences, you may
            upload a CSS stylesheet. To download a template as a helpful
            starting point, click{" "}
            <DocsLink
              href="https://raw.githubusercontent.com/ethyca/fides/main/clients/fides-js/src/components/fides.css"
              isExternal
            >
              here
            </DocsLink>
            .{" "}
            <DocsLink href="https://fid.es/customize-styles" isExternal>
              Learn more
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
        </ModalBody>
        <ModalFooter>
          <ButtonGroup
            size="sm"
            spacing="2"
            width="100%"
            display="flex"
            justifyContent="right"
          >
            <Button
              variant="outline"
              onClick={onClose}
              data-testid="cancel-btn"
              isDisabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              colorScheme="primary"
              type="submit"
              isDisabled={!uploadedFile || isLoading}
              onClick={handleSubmit}
              data-testid="submit-btn"
            >
              Submit
            </Button>
          </ButtonGroup>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default CustomAssetUploadModal;
