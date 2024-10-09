import { Box, Heading, Radio, RadioGroup, Stack, Text } from "fidesui";
import { useEffect, useState } from "react";

import { isErrorResult } from "~/features/common/helpers";
import { useAlert, useAPIHelper } from "~/features/common/hooks";
import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/v2/BackButton";
import { PRIVACY_REQUESTS_CONFIGURATION_ROUTE } from "~/features/common/nav/v2/routes";
import { storageTypes } from "~/features/privacy-requests/constants";
import {
  useCreateStorageMutation,
  useGetActiveStorageQuery,
  useGetStorageDetailsQuery,
  usePatchConfigurationSettingsMutation,
} from "~/features/privacy-requests/privacy-requests.slice";
import { StorageTypeApiAccepted } from "~/types/api";

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

  const handleChange = async (value: StorageTypeApiAccepted) => {
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
        active_default_storage_type: value as StorageTypeApiAccepted,
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
      <BackButton backPath={PRIVACY_REQUESTS_CONFIGURATION_ROUTE} />
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
        {storageValue === "s3" && storageDetails ? (
          <S3StorageConfiguration storageDetails={storageDetails} />
        ) : null}
      </Box>
    </Layout>
  );
};

export default StorageConfiguration;
