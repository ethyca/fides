import React from "react";

import { ExampleComponent } from "./ExampleComponent";

export default {
  title: "Components/ExampleComponent",
  component: ExampleComponent,
};

// This example shows how to template a component story with args that can be used from the
// storybook UI: https://storybook.js.org/docs/react/writing-stories/args
interface Args {
  bg: string;
  headingColor: string;
}
const Template = ({ bg, headingColor }: Args) => (
  <ExampleComponent
    stackProps={{ bg }}
    headingProps={{ color: headingColor }}
  />
);

export const ExampleComponentStory = Template.bind({});
Object.assign(ExampleComponentStory, {
  args: {
    bg: "gray.100",
    headingColor: "primary.500",
  },
});
