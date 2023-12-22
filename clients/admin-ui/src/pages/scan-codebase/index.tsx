import {
    Box,
    Button,
    Heading,
    Spinner,
    Center,
    Flex,
    Breadcrumb,
    BreadcrumbItem,
    Checkbox
} from "@fidesui/react";
import NextLink from "next/link";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import { CustomTextInput } from "~/features/common/form/inputs";

import Layout from "~/features/common/Layout";
import CheckboxGrid from "./CheckboxGrid";
import DonutChart from "./DonutChart";
import GitHubCodeViewer from "./GitHubCodeViewer";
// import ScanCodebaseTable from "~/features/dataset/DatasetTable";

const ScanCodebase: NextPage = () => {
    const isLoading = false;
    const isFetching = false;
    let formValues = { url: null };
    const handleSubmit = async (values: any) => {
        formValues.url = values.url;
        console.log(values);
    };
    const piiTags = [
        "Name",
        "Email",
        "Phone number",
        "Driver's license number",
        "Payment information",
        "Shipping information",
        "Date of birth",
        "Healthcare or medical information",
        "IP address",
        "Usernames and passwords",
        "Race or ethnicity",
        "Religious beliefs"
    ];
    const fileData = [
        { fileType: 'Python', percentage: 57 },
        { fileType: 'Typescript', percentage: 24 },
        { fileType: 'HTML', percentage: 13 },
        { fileType: 'CSS', percentage: 6 },
    ];
    const githubUrl = 'https://raw.githubusercontent.com/ethyca/fides/d84f6bde4dcd1fe595bae3f05efff0a0c9984cd1/src/fides/api/main.py#L12-L18';
    const githubUrl2 = 'https://raw.githubusercontent.com/ethyca/fides/d84f6bde4dcd1fe595bae3f05efff0a0c9984cd1/clients/admin-ui/src/home/HomeBanner.tsx#L19-L26';
    return (
        <Layout title="Scan codebase">
            <Heading mb={2} fontSize="2xl" fontWeight="semibold">
                PII Scanner
            </Heading>
            <Box mb={6}>
                <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
                    <BreadcrumbItem>
                        <NextLink href="/scan-codebase">PII Scanner</NextLink>
                    </BreadcrumbItem>
                    <BreadcrumbItem>
                        <NextLink href="#">Initial form</NextLink>
                    </BreadcrumbItem>
                </Breadcrumb>
            </Box>
            {(isFetching || isLoading) && (
                <Center>
                    <Spinner />
                </Center>
            )}
            {/* initial form */}
            <Formik
                initialValues={formValues
                }
                onSubmit={handleSubmit}
            >
                {({ isSubmitting, dirty, isValid }) => (
                    <Form>
                        <Box marginTop={3}>
                            <CustomTextInput
                                label="Github URL"
                                name="url"
                                variant="stacked"
                            />
                        </Box>
                        <Flex marginTop={6} justifyContent="flex-end">
                            <Button
                                textAlign="right"
                                type="submit"
                                disabled={!dirty || !isValid}
                                colorScheme="primary"
                                isLoading={isSubmitting}
                                size="sm"
                            >
                                Save
                            </Button>
                        </Flex>
                    </Form>
                )}
            </Formik>
            <DonutChart data={fileData} />
            <CheckboxGrid options={piiTags} />
            <GitHubCodeViewer url={githubUrl} language="python" />
            <GitHubCodeViewer url={githubUrl2} language="javascript" />
        </Layout>
    );
};

export default ScanCodebase;
