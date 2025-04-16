import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const POSTGRES_PLACEHOLDER = {
  name: "Postgres",
  key: "postgres_placeholder",
  connection_type: ConnectionType.POSTGRES,
  access: AccessLevel.READ,
  created_at: "",
};

export const POSTGRES_TAGS = ["Detection", "Discovery"];

export const PostgresOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Postgres is a relational database. Connect Fides to your Postgres Datbase
      to detect and track changes in schemas and tables and automatically
      discover and label data categories to proactively manage data governance
      risks.
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
      <InfoText>
        For each database, Fides requires the following permissions, where
        &apos;username&apos; is the user set up for Fides, and
        &apos;database&apos; is the name of the database you want to connect to.
      </InfoText>
      <InfoUnorderedList>
        <ListItem>CREATE USER username WITH LOGIN;</ListItem>
        <ListItem>
          GRANT SELECT ON ALL TABLES IN SCHEMA public TO username;
        </ListItem>
        <ListItem>
          GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO username;
        </ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const POSTGRES_TYPE_INFO = {
  placeholder: POSTGRES_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <PostgresOverview />,
  tags: POSTGRES_TAGS,
};

export default POSTGRES_TYPE_INFO;
