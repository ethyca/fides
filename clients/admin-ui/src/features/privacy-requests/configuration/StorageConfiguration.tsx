import {
  AntFlex as Flex,
  AntRadio as Radio,
  Box,
  Heading,
  RadioChangeEvent,
  Text,
} from "fidesui";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import {
  PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
  PRIVACY_REQUESTS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { usePatchConfigurationSettingsMutation } from "~/features/config-settings/config-settings.slice";
import { storageTypes } from "~/features/privacy-requests/constants";
import {
  useCreateStorageMutation,
  useGetActiveStorageQuery,
  useGetStorageDetailsQuery,
} from "~/features/privacy-requests/privacy-requests.slice";

import S3StorageConfiguration from "./S3StorageConfiguration";

const StorageConfiguration = () => {
  const { successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [storageValue, setStorageValue] = useState("");

  const { data: activeStorage } = useGetActiveStorageQuery();
  const { data: storageDetails } = useGetStorageDetailsQuery({
    type: storageValue,
  });
  const [saveStorageType, { isLoading }] = useCreateStorageMutation();
  const [saveActiveStorage] = usePatchConfigurationSettingsMutation();

  useEffect(() => {
    if (activeStorage) {
      setStorageValue(activeStorage.type);
    }
  }, [activeStorage]);

  const handleChange = async (e: RadioChangeEvent) => {
    const { value } = e.target;
    if (value === storageTypes.local) {
      const storageDetailsResult = await saveStorageType({
        type: value,
        details: {},
        format: "json",
      });
      if (isErrorResult(storageDetailsResult)) {
        handleError(storageDetailsResult.error);
      } else {
        successAlert(`Configured storage details successfully.`);
      }
    }

    const activeStorageResults = await saveActiveStorage({
      storage: {
        active_default_storage_type: value,
      },
    });

    if (isErrorResult(activeStorageResults)) {
      handleError(activeStorageResults.error);
    } else {
      setStorageValue(value);
    }
  };

  return (
    <Layout title="Configure Privacy Requests - Storage">
      <PageHeader
        heading="Privacy Requests"
        breadcrumbItems={[
          { title: "All requests", href: PRIVACY_REQUESTS_ROUTE },
          {
            title: "Configure requests",
            href: PRIVACY_REQUESTS_CONFIGURATION_ROUTE,
          },
          { title: "Storage" },
        ]}
      />
      <Heading mb={5} fontSize="md" fontWeight="semibold">
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
        <Radio.Group
          disabled={isLoading}
          onChange={handleChange}
          value={storageValue}
          data-testid="privacy-requests-storage-selection"
          className="p-3"
        >
          <Flex>
            <Radio key="local" value="local" data-testid="option-local">
              Local
            </Radio>
            <Radio key="s3" value="s3" data-testid="option-s3">
              S3
            </Radio>
          </Flex>
        </Radio.Group>
        {storageValue === "s3" && storageDetails ? (
          <S3StorageConfiguration storageDetails={storageDetails} />
        ) : null}
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
