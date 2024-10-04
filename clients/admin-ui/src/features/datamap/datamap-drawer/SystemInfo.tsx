import {
  AntButton,
  Box,
  ExternalLinkIcon,
  Flex,
  SecondaryLink,
  Spacer,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import React from "react";
import * as Yup from "yup";

import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { SystemInfoFormValues } from "~/features/datamap/datamap-drawer/types";
import { useUpsertSystemsMutation } from "~/features/system/system.slice";
import { System } from "~/types/api";
import { isErrorResult } from "~/types/errors/api";

type SystemInfoProps = {
  system: System;
};

const useSystemInfo = (system: System) => {
  const [upsertSystem] = useUpsertSystemsMutation();
  const toast = useToast();
  const handleUpsertSystem = async (
    values: SystemInfoFormValues,
    helpers: FormikHelpers<SystemInfoFormValues>,
  ) => {
    const requestBody: System[] = [
      {
        ...system,
        name: values.name,
        description: values.description,
      },
    ];

    const result = await upsertSystem(requestBody);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully saved system info"));
      // this is required so the initial state doesn't flash
      helpers.resetForm({ values });
    }
  };

  const validationSchema = Yup.object().shape({
    name: Yup.string().required().label("Name"),
    description: Yup.string().required().label("Description"),
  });

  return {
    handleUpsertSystem,
    validationSchema,
  };
};

const defaultInitialValues: SystemInfoFormValues = {
  name: "",
  description: "",
};

const SystemInfo = ({ system }: SystemInfoProps) => {
  const systemHref = `/systems/configure/${system.fides_key}`;

  const { handleUpsertSystem, validationSchema } = useSystemInfo(system);
  return (
    <Box>
      <Flex alignItems="center">
        <Text
          color="gray.600"
          size="md"
          lineHeight={6}
          fontWeight="semibold"
          marginBottom={2}
        >
          System details
        </Text>
        <Spacer />
        <SecondaryLink color="complimentary.500" href={systemHref}>
          View more
          <ExternalLinkIcon ml={2} />
        </SecondaryLink>
      </Flex>
      <Box
        width="100%"
        padding={4}
        borderTop="1px solid"
        borderColor="gray.200"
      >
        <Formik
          enableReinitialize
          initialValues={
            (system as SystemInfoFormValues) ?? defaultInitialValues
          }
          validationSchema={validationSchema}
          onSubmit={handleUpsertSystem}
        >
          {({ isSubmitting, dirty, isValid }) => (
            <Form>
              <FormGuard id="SystemInfoDrawer" name="System Info" />
              <Box marginTop={3}>
                <CustomTextInput
                  label="System name"
                  name="name"
                  variant="stacked"
                />
              </Box>
              <Box marginTop={3}>
                <CustomTextArea
                  label="System Description"
                  name="description"
                  variant="stacked"
                />
              </Box>
              <Flex marginTop={6} justifyContent="flex-end">
                <AntButton
                  htmlType="submit"
                  disabled={!dirty || !isValid}
                  loading={isSubmitting}
                  type="primary"
                >
                  Save
                </AntButton>
              </Flex>
            </Form>
          )}
        </Formik>
      </Box>
    </Box>
  );
};

export default SystemInfo;
