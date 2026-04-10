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
  Button,
  Flex,
  Modal,
  Skeleton,
  Spin,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";
import React, { useEffect, useRef, useState } from "react";

import { useAPIHelper } from "~/features/common/hooks";
import { ConnectionConfigurationResponse } from "~/types/api";

import { DSRCustomizationForm } from "./DSRCustomizationForm";
import { Field } from "./types";

type Props = {
  connectionConfig?: ConnectionConfigurationResponse | null;
};

export const DSRCustomizationModal = ({ connectionConfig }: Props) => {
  const mounted = useRef(false);
  const message = useMessage();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fields, setFields] = useState([] as Field[]);
  const [isOpen, setIsOpen] = useState(false);

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
      message.success(
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
      onClick={() => setIsOpen(true)}
    >
      Customize DSR
    </Button>
  );

  return (
    <>
      {!connectionConfig ? (
        <Tooltip
          title="Save an Integration first to customize the DSR"
          placement="top"
        >
          {DSRButton}
        </Tooltip>
      ) : (
        DSRButton
      )}
      <Modal
        open={isOpen}
        onCancel={() => setIsOpen(false)}
        centered
        destroyOnHidden
        title="Customize DSR"
        footer={null}
        width={640}
      >
        <Flex vertical gap="middle">
          <Text>
            Customize your PII fields to create a friendly label name for your
            privacy request packages. This &quot;Package Label&quot; is the
            label your user will see in their downloaded package.
          </Text>
          {mounted.current && !isLoading ? (
            <DSRCustomizationForm
              data={fields}
              isSubmitting={isSubmitting}
              onSaveClick={handleSubmit}
              onCancel={() => setIsOpen(false)}
            />
          ) : (
            <>
              <Skeleton />
            </>
          )}
        </Flex>
      </Modal>
    </>
  );
};
