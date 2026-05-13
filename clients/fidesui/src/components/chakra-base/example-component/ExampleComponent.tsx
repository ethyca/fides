import {
  ChakraHeading as Heading,
  type ChakraHeadingProps as HeadingProps,
  ChakraStack as Stack,
  type ChakraStackProps as StackProps,
  ChakraText as Text,
} from "fidesui";
import React from "react";

interface Props {
  stackProps: StackProps;
  headingProps: HeadingProps;
}

export const ExampleComponent = ({ stackProps, headingProps }: Props) => (
  <Stack {...stackProps}>
    <Heading {...headingProps}>An Example Component</Heading>
    <Text>This is just an example of a FidesUI component and its story.</Text>
  </Stack>
);
