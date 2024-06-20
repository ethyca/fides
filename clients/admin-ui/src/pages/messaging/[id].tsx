import {
  Box,
  ConfirmationModal,
  Heading,
  Spinner,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { MESSAGING_ROUTE } from "~/features/common/nav/v2/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  MessagingTemplateCreateOrUpdate,
  useDeleteMessagingTemplateByIdMutation,
  useGetMessagingTemplateByIdQuery,
  useUpdateMessagingTemplateByIdMutation,
} from "~/features/messaging-templates/messaging-templates.slice";
import PropertySpecificMessagingTemplateForm, {
  FormValues,
} from "~/features/messaging-templates/PropertySpecificMessagingTemplateForm";
import { isErrorResult } from "~/types/errors";

const EditPropertyPage: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  // to test- http://localhost:3000/messaging/mes_0512f494-f62d-4d9a-9e73-c3abca6c6849
  const templateId = router.query.id;

  const { data: messagingTemplate, isLoading } =
    useGetMessagingTemplateByIdQuery(templateId as string);

  const [updateMessagingTemplate] = useUpdateMessagingTemplateByIdMutation();
  const [deleteMessagingTemplate] = useDeleteMessagingTemplateByIdMutation();

  const handleSubmit = async (values: FormValues) => {
    const templateData: MessagingTemplateCreateOrUpdate = {
      is_enabled: values.is_enabled,
      content: {
        subject: values.content.subject,
        body: values.content.body,
      },
      properties: [],
    };
    values.properties?.forEach((property) =>
      templateData.properties?.push(property.id)
    );

    const result = await updateMessagingTemplate({
      templateId: templateId as string,
      template: templateData as MessagingTemplateCreateOrUpdate,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(`Messaging template cannot be updated because another enabled messaging template already exists with the same template type and property.`));
      return;
    }

    toast(successToastParams(`Messaging template updated successfully`));
  };

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const handleDelete = async () => {
    const result = await deleteMessagingTemplate(templateId as string);

    if (isErrorResult(result)) {
      toast(errorToastParams(`Messaging template cannot be deleted because it is the only template of its type. Consider disabling this template instead.`));
      return;
    }

    toast(successToastParams(`Messaging template deleted successfully`));

    router.push(MESSAGING_ROUTE);
  };

  if (!messagingTemplate) {
    return null;
  }

  if (isLoading) {
    return <Spinner />;
  }

  return (
    <Layout title="Configure Message">
      <Box data-testid="add-messaging-template">
        <Heading marginBottom={2} fontSize="2xl">
          Configure message
        </Heading>
        <Box maxWidth="720px">
          <Text fontSize="sm">Configure this message</Text>
          <Box padding={2}>
            <PropertySpecificMessagingTemplateForm
              template={messagingTemplate}
              handleSubmit={handleSubmit}
              handleDelete={onDeleteOpen}
            />
          </Box>
        </Box>
      </Box>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title="Delete message template"
        message={
          <Text>
            You are about to permanently delete this template message. Are you
            sure you would like to continue?
          </Text>
        }
      />
    </Layout>
  );
};

export default EditPropertyPage;
