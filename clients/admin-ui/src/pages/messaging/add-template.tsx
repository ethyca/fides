import {Box, Heading, Spinner, Text, useToast} from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
    useCreateMessagingTemplateByTypeMutation, useGetMessagingTemplateDefaultQuery
} from "~/features/messaging-templates/property-specific-messaging-templates.slice";
import PropertySpecificMessagingTemplateForm
    , {FormValues} from "~/features/messaging-templates/PropertySpecificMessagingTemplateForm";
import { isErrorResult } from "~/types/errors";


const AddMessagingTemplatePage: NextPage = () => {
    // to test: http://localhost:3000/messaging/add-template?templateType=subject_identity_verification
    const toast = useToast();
    const router = useRouter();
    const { templateType } = router.query;
    const [createMessagingTemplate] =
        useCreateMessagingTemplateByTypeMutation();
    const { data: messagingTemplate, isLoading } = useGetMessagingTemplateDefaultQuery(templateType as string);


    const handleSubmit = async (values: FormValues) => {
        // const templateData: MessagingTemplateCreateOrUpdate = {
        //     is_enabled: values.is_enabled,
        //     content: {
        //         subject: values.content.subject,
        //         body: values.content.body,
        //     },
        //     properties: values.properties
        // }
        const result = await createMessagingTemplate({templateType: templateType as string, template: values});

        if (isErrorResult(result)) {
            toast(errorToastParams(getErrorMessage(result.error)));
            return;
        }

        toast(successToastParams(`Messaging template created successfully`));
        // todo- route back to template list
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
                        <PropertySpecificMessagingTemplateForm template={messagingTemplate} handleSubmit={handleSubmit} />
                    </Box>
                </Box>
            </Box>
        </Layout>
    );
};

export default AddMessagingTemplatePage;
