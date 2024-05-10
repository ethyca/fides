import { Heading, Stack, Text } from "@fidesui/react";
import React from "react";

interface Props {
  stackProps: React.ComponentProps<typeof Stack>;
  headingProps: React.ComponentProps<typeof Heading>;
}

export const ExampleComponent = ({ stackProps, headingProps }: Props) => (
    <Stack {...stackProps}>
      <Heading {...headingProps}>An Example Component</Heading>
      <Text>This is just an example of a FidesUI component and its story.</Text>
    </Stack>
  );
