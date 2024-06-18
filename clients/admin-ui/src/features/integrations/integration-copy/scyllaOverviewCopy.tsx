import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";

const ScyllaOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Here&apos;s some example copy talking about Scylla. Lorem ipsum dolor sit
      amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
      labore et dolore magna aliqua. Faucibus a pellentesque sit amet porttitor.
      Risus nullam eget felis eget. Neque aliquam vestibulum morbi blandit. In
      ante metus dictum at tempor commodo ullamcorper a lacus. Placerat in
      egestas erat imperdiet. Elit duis tristique sollicitudin nibh sit.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Some List" />
      <InfoUnorderedList>
        <ListItem>Item 1</ListItem>
        <ListItem>Item 2</ListItem>
        <ListItem>Item 3</ListItem>
        <ListItem>Item 4</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

export const ScyllaInstructions = () => (
  <>
    <InfoHeading text="Configuring a Fides -> Scylla Integration" />
    <InfoText>
      Here&apos;s some example copy explaining how to set up Scylla. Lorem ipsum
      dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
      incididunt ut labore et dolore magna aliqua. Faucibus a pellentesque sit
      amet porttitor. Risus nullam eget felis eget. Neque aliquam vestibulum
      morbi blandit. In ante metus dictum at tempor commodo ullamcorper a lacus.
      Placerat in egestas erat imperdiet. Elit duis tristique sollicitudin nibh
      sit.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Some Other List" />
      <InfoUnorderedList>
        <ListItem>Item 5</ListItem>
        <ListItem>Item 6</ListItem>
        <ListItem>Item 7</ListItem>
        <ListItem>Item 8</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

export default ScyllaOverview;
