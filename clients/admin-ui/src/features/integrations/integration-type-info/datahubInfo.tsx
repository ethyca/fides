import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const DATAHUB_PLACEHOLDER = {
  name: "Datahub",
  key: "datahub_placeholder",
  connection_type: ConnectionType.DATAHUB,
  access: AccessLevel.READ,
  created_at: "",
};

export const DATAHUB_TAGS = ["Data catalog"];

export const DatahubOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      DataHub is a metadata platform designed to help organizations manage and
      govern their data. It acts as a centralized repository for tracking and
      discovering data assets across an organization, helping data teams
      understand where their data resides, how it&apos;s used, and how it flows
      through various systems.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Database</ListItem>
        <ListItem>SQL database</ListItem>
        <ListItem>Storage system</ListItem>
        <ListItem>Data detection</ListItem>
        <ListItem>Data discovery</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Permissions" />
      <InfoUnorderedList>
        <ListItem>CREATE ROLE my_monitor_role;</ListItem>
        <ListItem>
          GRANT USAGE ON DATABASE DATABASE_1 TO ROLE my_monitor_role;
        </ListItem>
        <ListItem>
          GRANT USAGE ON SCHEMA DATABASE_1.TEST_SCHEMA TO ROLE my_monitor_role;
        </ListItem>
        <ListItem>
          GRANT SELECT ON ALL TABLES IN SCHEMA DATABASE_1.TEST_SCHEMA TO ROLE
          my_monitor_role;
        </ListItem>
        <ListItem>CREATE USER test_user PASSWORD=&apos;***&apos;;</ListItem>
        <ListItem>GRANT ROLE my_monitor_role TO USER test_user;</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const DATAHUB_TYPE_INFO = {
  placeholder: DATAHUB_PLACEHOLDER,
  category: ConnectionCategory.DATA_CATALOG,
  overview: <DatahubOverview />,
  tags: DATAHUB_TAGS,
};

export default DATAHUB_TYPE_INFO;
