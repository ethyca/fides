import { Box, Center, Spinner, VStack } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import { useAlert, useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useCreateAccessManualWebhookMutation,
  useGetAccessManualHookQuery,
  usePatchAccessManualWebhookMutation,
} from "datastore-connections/datastore-connection.slice";
import {
  CreateAccessManualWebhookRequest,
  PatchAccessManualWebhookRequest,
} from "datastore-connections/types";
import { useRouter } from "next/router";
import React, { useEffect, useRef, useState } from "react";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";

import { replaceURL } from "../helpers";
import DSRCustomizationForm from "./DSRCustomizationForm";
import { Field } from "./types";

const DSRCustomization: React.FC = () => {
  const mounted = useRef(false);
  const router = useRouter();
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fields, setFields] = useState([] as Field[]);

  const { connection, step } = useAppSelector(selectConnectionTypeState);

  const { data, isFetching, isLoading, isSuccess } =
    useGetAccessManualHookQuery(connection!.key);

  const [createAccessManualWebhook] = useCreateAccessManualWebhookMutation();
  const [patchAccessManualWebhook] = usePatchAccessManualWebhookMutation();

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleSubmit = async (values: Field[], _actions: any) => {
    try {
      setIsSubmitting(true);
      const params:
        | CreateAccessManualWebhookRequest
        | PatchAccessManualWebhookRequest = {
        connection_key: connection?.key as string,
        body: { ...values } as any,
      };
      if (fields.length > 0) {
        await patchAccessManualWebhook(params).unwrap();
      } else {
        await createAccessManualWebhook(params).unwrap();
      }
      successAlert(
        `DSR customization ${fields.length > 0 ? "updated" : "added"}!`
      );
      router.push(DATASTORE_CONNECTION_ROUTE);
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
    if (connection?.key) {
      replaceURL(connection.key, step.href);
    }
    return () => {
      mounted.current = false;
    };
  }, [connection?.key, data, isSuccess, step.href]);

  return (
    <VStack align="stretch" gap="24px">
      <Box color="gray.700" fontSize="14px" w="572px">
        Customize your PII fields to create a friendly label name for your data
        subject request packages. This “DSR Package Label” is the label your
        data subject will see in their downloaded DSR package.
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
        />
      ) : null}
    </VStack>
  );
};

export default DSRCustomization;
