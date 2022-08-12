import { chakra, Heading, Stack } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";

const ViewYourDataMapPage: NextPage<{}> = () => (
  <chakra.form w="100%">
    <Stack spacing={10}>
      <Heading as="h3" size="lg">
        View your Data Map!
      </Heading>
      <div>
        Congratulations, you have built your first data map on Fides! From here
        you can easily extend this by adding additional systems.
      </div>
    </Stack>
  </chakra.form>
);
export default ViewYourDataMapPage;
