import {Box, Heading, Spinner, Text, useToast} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
    MessagingTemplateCreateOrUpdate, useDeleteMessagingTemplateByIdMutation,
    useGetMessagingTemplateByIdQuery,
    useUpdateMessagingTemplateByIdMutation
} from "~/features/messaging-templates/property-specific-messaging-templates.slice";
import PropertySpecificMessagingTemplateForm
    , {FormValues} from "~/features/messaging-templates/PropertySpecificMessagingTemplateForm";
import { isErrorResult } from "~/types/errors";

const EditPropertyPage: NextPage = () => {
    const toast = useToast();
    const router = useRouter();
    // to test- http://localhost:3000/messaging/mes_0512f494-f62d-4d9a-9e73-c3abca6c6849
    const templateId = router.query.id;

    const { data: messagingTemplate, isLoading } = useGetMessagingTemplateByIdQuery(templateId as string);

    const [updateMessagingTemplate] = useUpdateMessagingTemplateByIdMutation();
    const [deleteMessagingTemplate] = useDeleteMessagingTemplateByIdMutation();

    const handleSubmit = async (values: FormValues) => {
        const { id, ...updateValues } = values;

        const result = await updateMessagingTemplate({templateId: templateId as string, template: updateValues as MessagingTemplateCreateOrUpdate});

        if (isErrorResult(result)) {
            toast(errorToastParams(getErrorMessage(result.error)));
            return;
        }

        toast(successToastParams(`Messaging template updated successfully`));
    };

    const handleDelete = async (id: string) => {
        const result = await deleteMessagingTemplate(id);

        if (isErrorResult(result)) {
            toast(errorToastParams(getErrorMessage(result.error)));
            return;
        }

        toast(successToastParams(`Messaging template deleted successfully`));
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
                    <Text fontSize="sm">
                        Configure this message
                    </Text>
                    <Box padding={2}>
                        <PropertySpecificMessagingTemplateForm template={messagingTemplate} handleSubmit={handleSubmit} handleDelete={handleDelete} />
                    </Box>
                </Box>
            </Box>
        </Layout>
    );
};

export default EditPropertyPage;
