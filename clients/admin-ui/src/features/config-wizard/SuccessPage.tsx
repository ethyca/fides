import { Button, chakra, Heading, Stack } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

import { useGetSystemByFidesKeyQuery } from "~/features/system/system.slice";

const SuccessPage: NextPage<{
  handleChangeStep: Function;
  handleChangeReviewStep: Function;
  systemFidesKey: string;
}> = ({ handleChangeStep, handleChangeReviewStep, systemFidesKey }) => {
  const { data: existingSystem } = useGetSystemByFidesKeyQuery(systemFidesKey);

  return (
    <chakra.form w="100%">
      <Stack ml="100px" spacing={10}>
        <Heading as="h3" color="green.500" size="lg">
          {existingSystem?.name} successfully registered!
        </Heading>

        <Button
          onClick={() => {
            handleChangeStep(4);
            handleChangeReviewStep(5);
          }}
          mr={2}
          size="sm"
          variant="outline"
        >
          Add next system
        </Button>
        <Button
          onClick={() => {
            handleChangeStep(5);
          }}
          colorScheme="primary"
          size="sm"
        >
          Continue
        </Button>
      </Stack>
    </chakra.form>
  );
};
export default SuccessPage;
