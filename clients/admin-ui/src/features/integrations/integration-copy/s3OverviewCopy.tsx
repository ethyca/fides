import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const S3_PLACEHOLDER = {
  name: "Amazon S3",
  key: "s3_placeholder",
  connection_type: ConnectionType.S3,
  access: AccessLevel.READ,
  created_at: "",
};

export const S3_TAGS = ["Data Warehouse", "S3", "Tag 3", "Tag 4"];

export const S3Overview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Here&apos;s some example copy talking about Amazon S3. Lorem ipsum dolor
      sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
      labore et dolore magna aliqua. Faucibus a pellentesque sit amet porttitor.
      Risus nullam eget felis eget. Neque aliquam vestibulum morbi blandit. In
      ante metus dictum at tempor commodo ullamcorper a lacus. Placerat in
      egestas erat imperdiet. Elit duis tristique sollicitudin nibh sit.
    </InfoText>
    <ShowMoreContent>
      <InfoUnorderedList>
        <ListItem>Item 1</ListItem>
        <ListItem>Item 2</ListItem>
        <ListItem>Item 3</ListItem>
        <ListItem>Item 4</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

export const S3Instructions = () => (
  <>
    <InfoHeading text="Configuring a Fides -> Amazon S3 Integration" />
    <InfoText>
      Here&apos;s some example copy explaining how to set up Amazon S3. Lorem
      ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
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

const S3_TYPE_INFO = {
  placeholder: S3_PLACEHOLDER,
  category: ConnectionCategory.DATA_WAREHOUSE,
  overview: <S3Overview />,
  instructions: <S3Instructions />,
  tags: S3_TAGS,
};

export default S3_TYPE_INFO;
