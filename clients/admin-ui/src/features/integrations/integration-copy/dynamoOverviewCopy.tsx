import { Collapse, ListItem } from "fidesui";
import { useState } from "react";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
  ToggleShowMore,
} from "~/features/common/copy/components";

const DynamoOverview = () => {
  const [showingMore, setShowingMore] = useState(false);

  return (
    <>
      <InfoHeading text="Overview" />
      <InfoText>
        Here&apos;s some example copy talking about DynamoDB. Lorem ipsum dolor
        sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
        ut labore et dolore magna aliqua. Faucibus a pellentesque sit amet
        porttitor. Risus nullam eget felis eget. Neque aliquam vestibulum morbi
        blandit. In ante metus dictum at tempor commodo ullamcorper a lacus.
        Placerat in egestas erat imperdiet. Elit duis tristique sollicitudin
        nibh sit.
      </InfoText>
      <Collapse in={showingMore}>
        <InfoHeading text="Some List" />
        <InfoUnorderedList>
          <ListItem>Item 1</ListItem>
          <ListItem>Item 2</ListItem>
          <ListItem>Item 3</ListItem>
          <ListItem>Item 4</ListItem>
        </InfoUnorderedList>
      </Collapse>
      <ToggleShowMore
        showingMore={showingMore}
        onClick={() => setShowingMore(!showingMore)}
      />
    </>
  );
};

export default DynamoOverview;
