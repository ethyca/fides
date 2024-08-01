import { getErrorMessage } from "common/helpers";
import { MESSAGING_ROUTE } from "common/nav/v2/routes";
import { Box, Heading, Spinner, Text, useToast } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  MessagingTemplateCreateOrUpdate,
  useGetMessagingTemplateDefaultQuery,
} from "~/features/messaging-templates/messaging-templates.slice";
import { useCreateMessagingTemplateByTypeMutation } from "~/features/messaging-templates/messaging-templates.slice.plus";
import PropertySpecificMessagingTemplateForm, {
  FormValues,
} from "~/features/messaging-templates/PropertySpecificMessagingTemplateForm";
import { isErrorResult } from "~/types/errors";

const AddMessagingTemplatePage: NextPage = () => {
  const toast = useToast();
  const router = useRouter();
  const { templateType } = router.query;
  const [createMessagingTemplate] = useCreateMessagingTemplateByTypeMutation();
  const { data: messagingTemplate, isLoading } =
    useGetMessagingTemplateDefaultQuery(templateType as string);

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
    const result = await createMessagingTemplate({
      templateType: templateType as string,
      template: templateData,
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    toast(successToastParams(`Messaging template created successfully`));
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
            />
          </Box>
        </Box>
      </Box>
    </Layout>
  );
};

export default AddMessagingTemplatePage;
