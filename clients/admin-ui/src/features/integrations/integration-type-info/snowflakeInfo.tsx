import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const SNOWFLAKE_PLACEHOLDER = {
  name: "Snowflake",
  key: "snowflake_placeholder",
  connection_type: ConnectionType.SNOWFLAKE,
  access: AccessLevel.READ,
  created_at: "",
};

export const SNOWFLAKE_TAGS = [
  "Data warehouse",
  "Detection",
  "Discovery",
  "DSR automation",
];

export const SnowflakeOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Snowflake is a cloud-based data warehousing platform designed for handling
      large-scale data storage and analytics. It enables organizations to store,
      manage, and analyze massive amounts of data efficiently, offering features
      like scalability, performance, and flexibility.
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
        <ListItem>CREATE USER test_user PASSWORD='***';</ListItem>
        <ListItem>GRANT ROLE my_monitor_role TO USER test_user;</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const SNOWFLAKE_TYPE_INFO = {
  placeholder: SNOWFLAKE_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <SnowflakeOverview />,
  tags: SNOWFLAKE_TAGS,
};

export default SNOWFLAKE_TYPE_INFO;
