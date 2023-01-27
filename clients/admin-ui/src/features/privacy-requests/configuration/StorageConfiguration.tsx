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
import NextLink from "next/link";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import { useSetActiveStorageMutation } from "~/features/privacy-requests/privacy-requests.slice";

import S3StorageConfiguration from "./S3StorageConfiguration";

const StorageConfiguration = () => {
  const [selected, setSelected] = useState("");
  const { errorAlert, successAlert } = useAlert();
  const [saveStorageType] = useSetActiveStorageMutation();

  const handleChange = async (value: string) => {
    // helpers.setSubmitting(true);
    setSelected(value);

    const payload = await saveStorageType({
      active_default_storage_type: value,
    });
    if ("error" in payload) {
      errorAlert(
        getErrorMessage(payload.error),
        `Configuring storage type has failed to save due to the following:`
      );
    } else {
      successAlert(`Configure storage type saved successfully.`);
    }
    // helpers.setSubmitting(false);
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
          onChange={handleChange}
          value={selected}
          data-testid="privacy-requests-storage-selection"
          colorScheme="secondary"
          p={3}
        >
          <Stack direction="row">
            <Radio key="local" value="local" data-testid="option-local" mr={5}>
              Local
            </Radio>
            <Radio key="s3" value="s3" data-testid="option-s3">
              S3
            </Radio>
          </Stack>
        </RadioGroup>
        {selected === "s3" ? <S3StorageConfiguration /> : null}
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
