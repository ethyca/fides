import {
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraSpacer as Spacer,
  ChakraText as Text,
  Icons,
  SecondaryLink,
  useMessage,
} from "fidesui";
import { Form, Formik, FormikHelpers } from "formik";
import React from "react";
import * as Yup from "yup";

import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { FormGuard } from "~/features/common/hooks/useIsAnyFormDirty";
import { SystemInfoFormValues } from "~/features/datamap/datamap-drawer/types";
import { useUpsertSystemsMutation } from "~/features/system/system.slice";
import { System } from "~/types/api";
import { isErrorResult } from "~/types/errors/api";

type SystemInfoProps = {
  system: System;
};

const useSystemInfo = (system: System) => {
  const [upsertSystem] = useUpsertSystemsMutation();
  const message = useMessage();
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
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Successfully saved system info");
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
          <Icons.Launch className="ml-2 inline" size={14} />
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
          {() => (
            <Form>
              <FormGuard id="SystemInfoDrawer" name="System Info" />
              <Box marginTop={3}>
                <CustomTextInput
                  label="System name"
                  name="name"
                  variant="stacked"
                  disabled
                />
              </Box>
              <Box marginTop={3}>
                <CustomTextArea
                  label="System description"
                  name="description"
                  variant="stacked"
                  disabled
                />
              </Box>
            </Form>
          )}
        </Formik>
      </Box>
    </Box>
  );
};

export default SystemInfo;
