import { getErrorMessage } from "common/helpers";
import {
  Box,
  ConfirmationModal,
  Spinner,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { MESSAGING_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  MessagingTemplateCreateOrUpdate,
  useDeleteMessagingTemplateByIdMutation,
  useGetMessagingTemplateByIdQuery,
} from "~/features/messaging-templates/messaging-templates.slice";
import { usePutMessagingTemplateByIdMutation } from "~/features/messaging-templates/messaging-templates.slice.plus";
import PropertySpecificMessagingTemplateForm, {
  FormValues,
} from "~/features/messaging-templates/PropertySpecificMessagingTemplateForm";
import { isErrorResult } from "~/types/errors";

const EditPropertyPage: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const templateId = router.query.id;

  const { data: messagingTemplate, isLoading } =
    useGetMessagingTemplateByIdQuery(templateId as string);

  const [putMessagingTemplate] = usePutMessagingTemplateByIdMutation();
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
      templateData.properties?.push(property.id),
    );

    const result = await putMessagingTemplate({
      templateId: templateId as string,
      template: templateData as MessagingTemplateCreateOrUpdate,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
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
      toast(errorToastParams(getErrorMessage(result.error)));
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
      <PageHeader
        heading="Messaging"
        breadcrumbItems={[
          { title: "Messaging", href: MESSAGING_ROUTE },
          { title: "Configure message" },
        ]}
      >
        <Box data-testid="add-messaging-template">
          <Box maxWidth="720px">
            <Box padding={2}>
              <PropertySpecificMessagingTemplateForm
                template={messagingTemplate}
                handleSubmit={handleSubmit}
                handleDelete={onDeleteOpen}
              />
            </Box>
          </Box>
        </Box>
      </PageHeader>
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
