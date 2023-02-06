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

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  useCreateConfigurationSettingsMutation,
  useCreateStorageMutation,
} from "~/features/privacy-requests/privacy-requests.slice";

import S3StorageConfiguration from "./S3StorageConfiguration";

const StorageConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [storageValue, setStorageValue] = useState("");
  const [saveStorageType, { isLoading }] = useCreateStorageMutation();
  const [saveActiveStorage] = useCreateConfigurationSettingsMutation();

  const handleChange = async (value: string) => {
    if (value === "local") {
      const storageDetailsResult = await saveStorageType({
        type: value,
        format: "json",
      });
      if (isErrorResult(storageDetailsResult)) {
        handleError(storageDetailsResult.error);
      } else {
        successAlert(`Configure storage type details saved successfully.`);
        setStorageValue(value);
      }
    }

    const activeStorageResults = await saveActiveStorage({
      fides: {
        storage: {
          active_default_storage_type: value,
        },
      },
    });

    if (isErrorResult(activeStorageResults)) {
      handleError(activeStorageResults.error);
    } else {
      successAlert(`Configure active storage type saved successfully.`);
      setStorageValue(value);
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
        <Box mb={5}>
          Fides requires a storage destination to store and share the results of
          privacy requests. For a production setup, it is highly recommended to
          have S3 as a storage destination. Ensure you have completed the setup
          for the storage destination and have the details handy prior to the
          following steps.
        </Box>
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
          value={storageValue}
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
        {storageValue === "s3" ? <S3StorageConfiguration /> : null}
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
