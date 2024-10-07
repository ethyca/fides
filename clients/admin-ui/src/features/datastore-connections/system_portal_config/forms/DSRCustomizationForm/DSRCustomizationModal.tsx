import { useAlert, useAPIHelper } from "common/hooks";
import {
  useCreateAccessManualWebhookMutation,
  useGetAccessManualHookQuery,
  usePatchAccessManualWebhookMutation,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateAccessManualWebhookRequest,
  PatchAccessManualWebhookRequest,
} from "datastore-connections/types";
import {
  AntButton as Button,
  Box,
  Center,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Spinner,
  Tooltip,
  useDisclosure,
  VStack,
} from "fidesui";
import React, { useEffect, useRef, useState } from "react";

import { ConnectionConfigurationResponse } from "~/types/api";

import DSRCustomizationForm from "./DSRCustomizationForm";
import { Field } from "./types";

type Props = {
  connectionConfig?: ConnectionConfigurationResponse | null;
};

const DSRCustomizationModal = ({ connectionConfig }: Props) => {
  const mounted = useRef(false);
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fields, setFields] = useState([] as Field[]);

  const { isOpen, onOpen, onClose } = useDisclosure();

  const { data, isFetching, isLoading, isSuccess } =
    useGetAccessManualHookQuery(connectionConfig ? connectionConfig.key : "", {
      skip: !connectionConfig,
    });

  const [createAccessManualWebhook] = useCreateAccessManualWebhookMutation();
  const [patchAccessManualWebhook] = usePatchAccessManualWebhookMutation();

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleSubmit = async (values: Field[], _actions: any) => {
    try {
      setIsSubmitting(true);
      const params:
        | CreateAccessManualWebhookRequest
        | PatchAccessManualWebhookRequest = {
        connection_key: connectionConfig!.key as string,
        body: { ...values } as any,
      };
      if (fields.length > 0) {
        await patchAccessManualWebhook(params).unwrap();
      } else {
        await createAccessManualWebhook(params).unwrap();
      }
      successAlert(
        `DSR customization ${fields.length > 0 ? "updated" : "added"}!`,
      );
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    mounted.current = true;
    if (isSuccess && data) {
      setFields(data.fields);
    }
    return () => {
      mounted.current = false;
    };
  }, [data, isSuccess]);

  const DSRButton = (
    <Button
      disabled={!connectionConfig || isSubmitting}
      loading={isSubmitting}
      onClick={onOpen}
    >
      Customize DSR
    </Button>
  );

  return (
    <>
      {!connectionConfig ? (
        <Tooltip
          label="Save an Integration first to customize the DSR"
          placement="top"
          shouldWrapChildren
        >
          {DSRButton}
        </Tooltip>
      ) : (
        DSRButton
      )}
      <Modal isCentered isOpen={isOpen} size="lg" onClose={onClose}>
        <ModalOverlay />
        <ModalContent minWidth="775px">
          <ModalHeader>Customize DSR</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack align="stretch" gap="16px">
              <Box color="gray.700" fontSize="14px">
                Customize your PII fields to create a friendly label name for
                your privacy request packages. This “Package Label” is the label
                your user will see in their downloaded package.
              </Box>
              {(isFetching || isLoading) && (
                <Center>
                  <Spinner />
                </Center>
              )}
              {mounted.current && !isLoading ? (
                <DSRCustomizationForm
                  data={fields}
                  isSubmitting={isSubmitting}
                  onSaveClick={handleSubmit}
                  onCancel={onClose}
                />
              ) : null}
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </>
  );
};

export default DSRCustomizationModal;
