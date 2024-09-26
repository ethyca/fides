import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const RDS_MYSQL_PLACEHOLDER = {
  name: "Amazon RDS MySQL",
  key: "rds_mysql_placeholder",
  connection_type: ConnectionType.RDS_MYSQL,
  access: AccessLevel.READ,
  created_at: "",
};

export const RDS_MYSQL_TAGS = [
  "Database",
  "Detection",
  "Discovery",
  "DSR automation",
];

export const GoogleCloudSQLMySQLOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Amazon RDS MySQL is a fully-managed relational database service
      that simplifies the setup, maintenance, management, and administration of
      MySQL databases. Connect Fides to your Amazon RDS MySQL to
      detect and track changes in schemas and tables and automatically discover
      and label data categories to proactively manage data governance risks.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Database</ListItem>
        <ListItem>NoSQL database</ListItem>
        <ListItem>Storage system</ListItem>
        <ListItem>Data detection</ListItem>
        <ListItem>Data discovery</ListItem>
        <ListItem>DSR automation</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Permissions" />
      <InfoText>
        For detection and discovery, Fides requires a user with the SELECT
        permission on the database. If you intend to automate governance for DSR
        or Consent, Fides requires a user with the SELECT, UPDATE, and DELETE
        The permissions allow Fides to read the schema of, and data stored in
        tables, and fields as well as write restricted updates based on your
        policy configurations to tables you specify as part of DSR and Consent
        orchestration. For a complete list of permissions view the Amazon RDS
        DB documentation.
      </InfoText>
      <InfoHeading text="Permissions list" />
      <InfoUnorderedList>
        <ListItem>GRANT SELECT</ListItem>
        <ListItem>GRANT UPDATE</ListItem>
        <ListItem>GRANT DELETE</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const RDS_MYSQL_TYPE_INFO = {
  placeholder: RDS_MYSQL_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <GoogleCloudSQLMySQLOverview />,
  tags: RDS_MYSQL_TAGS,
};

export default RDS_MYSQL_TYPE_INFO;
