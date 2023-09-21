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
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import React, { useState } from "react";
import { useDropzone } from "react-dropzone";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import { useUpdateCustomAssetMutation } from "~/features/plus/plus.slice";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  testId?: string;
  assetKey: string;
};

const CustomAssetUploadModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  testId = "custom-asset-modal",
  assetKey,
}) => {
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
      try {
        await updateCustomAsset({ assetKey, file: uploadedFile }).unwrap();
        toast(successToastParams("Custom asset uploaded successfully"));
      } catch (error) {
        toast(errorToastParams(getErrorMessage(error as FetchBaseQueryError)));
      } finally {
        setUploadedFile(null);
      }
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
    <Modal isOpen={isOpen} onClose={onClose} size="2xl">
      <ModalOverlay />
      <ModalContent textAlign="left" p={2} data-testid={testId}>
        <ModalHeader>Upload custom asset</ModalHeader>
        <ModalBody>
          <Text fontSize="sm" mb={4}>
            Drag and drop your CSS file here, or click to browse your files.
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
