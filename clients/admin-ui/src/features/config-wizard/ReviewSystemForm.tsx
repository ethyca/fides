import { Box, Button, Heading, Stack, Text, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React from "react";
import { CustomTextInput } from "~/features/common/form/inputs";
import { useGetOrganizationByFidesKeyQuery } from "../config-wizard/organization.slice";
import { useGetSystemByFidesKeyQuery } from "../system/system.slice";
import { System } from "../system/types";

type FormValues = Partial<System>;

const ReviewSystemForm: NextPage<{
  handleChangeStep: Function;
  handleCancelSetup: Function;
}> = ({ handleCancelSetup, handleChangeStep }) => {
  // TODO FUTURE: Need a way to check for an existing fides key from the start of the wizard
  // not just use this default
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(
    "default_organization"
  );
  const { data: existingOrg } = useGetOrganizationByFidesKeyQuery(
    "default_organization"
  );

  const toast = useToast();

  const initialValues = {
    name: existingOrg?.name,
    system_name: existingSystem?.name,
    // system_key: existingSystem?.key,
    system_description: existingSystem?.description,
    system_type: existingSystem?.system_type,
    system_tags: existingSystem?.system_dependencies,
  };

  const handleSubmit = async (values: FormValues) => {
    // setIsLoading(true);
    // handleResult(updateSystemResult);
    // setIsLoading(false);
  };

  console.log(existingSystem);

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize={true}
      onSubmit={handleSubmit}
    >
      {({ values }) => (
        <Form>
          <Stack ml="100px" spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              Review {existingOrg?.name}
            </Heading>
            <div>Let’s quickly review our declaration before registering</div>
            <Stack>
              <CustomTextInput
                disabled
                id="system_name"
                name="system_name"
                label="System name"
              />
              {/* <CustomTextInput
                disabled
                id="system_key"
                name="system_key"
                label="System key"
              /> */}
              <CustomTextInput
                disabled
                id="system_description"
                name="system_description"
                label="Description"
              />
              <CustomTextInput
                disabled
                id="system_type"
                name="system_type"
                label="System type"
              />
              <CustomTextInput
                disabled
                id="system_tags"
                name="system_tags"
                label="System tags"
              />
              <Text>Privacy declarations:</Text>
            </Stack>
            <Box>
              <Button
                onClick={() => handleCancelSetup()}
                mr={2}
                size="sm"
                variant="outline"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                colorScheme="primary"
                size="sm"
                // disabled={
                // }
                // isLoading={isLoading}
              >
                Confirm and Continue
              </Button>
            </Box>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};
export default ReviewSystemForm;
