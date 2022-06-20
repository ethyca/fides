import { Box, Button, Heading, Stack, useToast } from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import { Form, Formik } from "formik";
import type { NextPage } from "next";
import React from "react";

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

  const toast = useToast();

  const initialValues = {
    name: "name",
  };

  const handleSubmit = async (values: FormValues) => {
    const handleResult = (
      result: { data: {} } | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if ("error" in result) {
        toast({
          status: "error",
          description: "errorMsg",
        });
      } else {
        toast.closeAll();
        handleChangeStep(6);
        handleChangeStep(5);
      }
    };

    // setIsLoading(true);

    // handleResult(updateSystemResult);

    // setIsLoading(false);
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
    >
      {({ values }) => (
        <Form>
          <Stack ml="100px" spacing={10}>
            <Heading as="h3" size="lg">
              {/* TODO FUTURE: Path when describing system from infra scanning */}
              {/* Review {existingSystem?.name} */}
              Review
            </Heading>
            <div>Let’s quickly review our declaration before registering</div>
            <Stack>Body</Stack>
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
                //   !values.name ||
                //   !values.description ||
                //   !values.system_type ||
                //   (values.system_dependencies &&
                //     values.system_dependencies.length <= 0)
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
