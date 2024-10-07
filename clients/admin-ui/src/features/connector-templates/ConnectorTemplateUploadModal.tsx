import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import {
  AntButton as Button,
  Box,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  useToast,
} from "fidesui";
import React, { useState } from "react";
import { useDropzone } from "react-dropzone";
import { useDispatch } from "react-redux";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  setConnectionOptions,
  useGetAllConnectionTypesQuery,
} from "~/features/connection-type";

import { useRegisterConnectorTemplateMutation } from "./connector-template.slice";

type RequestModalProps = {
  isOpen: boolean;
  onClose: () => void;
  testId?: string;
};

const ConnectorTemplateUploadModal = ({
  isOpen,
  onClose,
  testId = "connector-template-modal",
}: RequestModalProps) => {
  const dispatch = useDispatch();
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
  const { refetch: refetchConnectionTypes } = useGetAllConnectionTypesQuery(
    {
      search: "",
    },
    {
      skip: false,
    },
  );

  const handleSubmit = async () => {
    if (uploadedFile) {
      try {
        await registerConnectorTemplate(uploadedFile).unwrap();
        toast(
          successToastParams("Integration template uploaded successfully."),
        );

        // refresh the connection types
        const { data } = await refetchConnectionTypes();
        dispatch(setConnectionOptions(data?.items ?? []));
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
        <ModalHeader>Upload integration template</ModalHeader>
        <ModalBody>
          <Text fontSize="sm" mb={4}>
            Drag and drop your integration template zip file here, or click to
            browse your files.
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
          <Text fontSize="sm" mt={4}>
            An integration template zip file must include a SaaS config and
            dataset, but may also contain an icon (.svg) as an optional file.
          </Text>
        </ModalBody>
        <ModalFooter className="flex w-full justify-end gap-2">
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
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default ConnectorTemplateUploadModal;
