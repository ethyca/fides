import {
  Box,
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  Heading,
  Radio,
  RadioGroup,
  Stack,
  Text,
} from "@fidesui/react";
import NextLink from "next/link";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  useCreateActiveStorageMutation,
  useGetStorageDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import S3StorageConfiguration from "./S3StorageConfiguration";

interface StorageData {
  type: string;
  details: {
    auth_method: string;
    bucket: string;
  };
  format: string;
}

const StorageConfiguration = () => {
  const [existingStorageData, setExistingStorageData] = useState<StorageData>();
  const { data: existingData } = useGetStorageDetailsQuery(
    existingStorageData?.type
  );
  const { errorAlert, successAlert } = useAlert();
  const [saveStorageType, { isLoading }] = useCreateActiveStorageMutation();

  const handleChange = async (value: string) => {
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
      setExistingStorageData(existingData);
    }
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
          <BreadcrumbItem color="complimentary.500">
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
        <Box>
          To configure a Storage destination, first choose a method to store
          your results. Fides currently supports{" "}
          <Text as="span" color="complimentary.500">
            Local
          </Text>{" "}
          and{" "}
          <Text as="span" color="complimentary.500">
            S3
          </Text>{" "}
          storage methods.
        </Box>
        <Heading fontSize="md" fontWeight="semibold" mt={10}>
          Choose storage type to configure
        </Heading>
        <RadioGroup
          isDisabled={isLoading}
          onChange={handleChange}
          value={existingStorageData?.type}
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
        {existingStorageData?.type === "s3" ? (
          <S3StorageConfiguration existingStorageData={existingStorageData} />
        ) : null}
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
