import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Radio,
  RadioGroup,
  Stack,
} from "@fidesui/react";
import { Formik, Form } from "formik";
import NextLink from "next/link";
import { CustomSelect, CustomTextInput } from "~/features/common/form/inputs";
import Layout from "~/features/common/Layout";

const StorageConfiguration = () => {
  //  Need to keep track of steps

  const initialValues = {
    format: "",
  };

  return (
    <Layout title="Configure Privacy Requests - Storage">
      <Box mb={8}>
        <Breadcrumb fontWeight="medium" fontSize="sm" color="gray.600">
          <BreadcrumbItem>
            <BreadcrumbLink as={NextLink} href="/privacy-requests">
              Privacy requests
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem>
            <BreadcrumbLink as={NextLink} href="/privacy-requests/configure">
              Configuration
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbItem color="purple.400">
            <BreadcrumbLink
              as={NextLink}
              href="/privacy-requests/configure/storage"
              isCurrentPage
            >
              Configure storage
            </BreadcrumbLink>
          </BreadcrumbItem>
        </Breadcrumb>
      </Box>

      <Heading mb={5} fontSize="2xl" fontWeight="semibold">
        Configure storage
      </Heading>

      <Box display="flex" flexDirection="column" width="50%">
        To configure a Storage destination, first choose a method to store your
        results. Fides currently supports Local and S3 storage methods.
        <Heading fontSize="md" fontWeight="semibold" mt={10}>
          Choose storage type to configure
        </Heading>
        <RadioGroup
          //   onChange={handleChange}
          //   value={selected.value}
          //   data-testid={`input-${field.name}`}
          colorScheme="secondary"
          p={3}
        >
          <Stack direction="row">
            <Radio
              // key={o.value}
              // value={o.value}
              // data-testid={`option-${o.value}`}
              mr={5}
            >
              Local
            </Radio>
            <Radio
            // key={o.value}
            // value={o.value}
            // data-testid={`option-${o.value}`}
            >
              S3
            </Radio>
          </Stack>
        </RadioGroup>
        {/* Local route */}
        {/* S3 route */}
        <Heading fontSize="md" fontWeight="semibold" mt={10}>
          S3 storage configuration
        </Heading>
        <Stack>
          <Formik initialValues={initialValues} onSubmit={() => {}}>
            <Form id="s3-privacy-requests-storage-configuration">
              <CustomSelect
                name="format"
                label="Format"
                options={[
                  { label: "json", value: "json" },
                  { label: "csv", value: "csv" },
                ]}
              />
              <CustomTextInput
                name="auth_method"
                label="Auth method"
                placeholder="Optional"
              />
              <CustomTextInput
                name="bucket"
                label="Bucket"
                placeholder="Optional"
              />
            </Form>
          </Formik>
        </Stack>
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
