import {
  Box,
  Button,
  Modal,
  ModalContent,
  ModalOverlay,
  Text,
  useToast,
} from "@fidesui/react";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import { getErrorMessage } from "../common/helpers";
import { errorToastParams, successToastParams } from "../common/toast";
import { useRegisterConnectorTemplateMutation } from "./connector-template.slice";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
};

const ConnectorTemplateUploadModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const toast = useToast();
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      const fileExtension = file.name.split(".").pop()?.toLowerCase();

      if (fileExtension !== "zip") {
        toast(errorToastParams("Only zip files are allowed."));
        return;
      }

      setUploadedFile(acceptedFiles[0]);
    },
  });

  const [registerConnectorTemplate, { isLoading }] =
    useRegisterConnectorTemplateMutation();

  const handleSubmit = async () => {
    if (uploadedFile) {
      try {
        await registerConnectorTemplate(uploadedFile).unwrap();
        toast(successToastParams("Connector template uploaded successfully."));
        onClose();
      } catch (error) {
        toast(errorToastParams(getErrorMessage(error as FetchBaseQueryError)));
      } finally {
        setUploadedFile(null);
      }
    }
  };

  const renderFileText = () => {
    if (uploadedFile) {
      return <Text fontSize="sm">{uploadedFile.name}</Text>;
    }
    if (isDragActive) {
      return <Text fontSize="sm">Drop the file here...</Text>;
    }
    return <Text fontSize="sm">Click or drag and drop your file here.</Text>;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <ModalOverlay />
      <ModalContent top={[0, "150px"]} maxWidth="600px" mx={5} my={3} p={4}>
        <Text fontSize="lg" fontWeight="bold" mb={2}>
          Upload Connector Template
        </Text>
        <Text color="gray.700" fontSize="sm" mb={4}>
          Drag and drop your connector template zip file here, or click to
          browse your files.
        </Text>
        <Box
          {...getRootProps()}
          bg={isDragActive ? "gray.100" : "gray.50"}
          border="2px dashed"
          borderColor={isDragActive ? "gray.300" : "gray.200"}
          borderRadius="md"
          cursor="pointer"
          minHeight="100px"
          display="flex"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
        >
          <input {...getInputProps()} />
          {renderFileText()}
        </Box>
        <Text color="gray.700" fontSize="sm" mt={4} mb={4}>
          A connector template zip file must include a SaaS config and dataset,
          but may also contain an icon (.svg) and custom functions (.py) as
          optional files.
        </Text>
        <Button
          mt={4}
          colorScheme="primary"
          type="submit"
          isDisabled={!uploadedFile || isLoading}
          onClick={handleSubmit}
          data-testid="submit-btn"
          mx="auto"
        >
          Submit
        </Button>
      </ModalContent>
    </Modal>
  );
};

export default ConnectorTemplateUploadModal;
