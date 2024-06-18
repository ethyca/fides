import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const SCYLLA_PLACEHOLDER = {
  name: "Scylla",
  key: "scylla_placeholder",
  connection_type: ConnectionType.SCYLLA,
  access: AccessLevel.READ,
  created_at: "",
};

export const SCYLLA_TAGS = ["Database", "DynamoDB", "Tag 3", "Tag 4"];

export const ScyllaOverview = () => (
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

const SCYLLA_TYPE_INFO = {
  placeholder: SCYLLA_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <ScyllaOverview />,
  instructions: <ScyllaInstructions />,
  tags: SCYLLA_TAGS,
};

export default SCYLLA_TYPE_INFO;
