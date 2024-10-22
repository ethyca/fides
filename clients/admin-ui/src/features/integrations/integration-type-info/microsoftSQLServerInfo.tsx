import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const MICROSOFT_SQL_SERVER_PLACEHOLDER = {
  name: "Microsoft SQL Server",
  key: "microsoft_sql_server_placeholder",
  connection_type: ConnectionType.MSSQL,
  access: AccessLevel.READ,
  created_at: "",
};

export const MICROSOFT_SQL_SERVER_TAGS = [
  "Database",
  "Detection",
  "Discovery",
  "Microsoft SQL Server",
];

export const MicrosoftSQLServerOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Amazon RDS MySQL is a fully-managed relational database service that
      simplifies the setup, maintenance, management, and administration of MySQL
      databases. Connect Fides to your Amazon RDS MySQL to detect and track
      changes in schemas and tables and automatically discover and label data
      categories to proactively manage data governance risks.
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
      <InfoText>
        For detecting database RDS instances and clusters, Fides requires an IAM
        user with the following permissions/role:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>rds:DescribeDBClusters</ListItem>
        <ListItem>rds:DescribeDBInstances</ListItem>
        <ListItem>rds-db:connect</ListItem>
      </InfoUnorderedList>
      <InfoText>
        And per database instance and database it requires the following
        permissions, where &apos;username&apos; is the user set up for Fides,
        and &apos;database&apos; is the database name, you want to connect to.
      </InfoText>
      <InfoUnorderedList>
        <ListItem>
          CREATE USER &apos;username&apos; IDENTIFIED WITH
          AWSAuthenticationPlugin AS &apos;RDS&apos;;
        </ListItem>
        <ListItem>
          GRANT SELECT, INSERT ON database.* TO
          &apos;username&apos;@&apos;%&apos;;
        </ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const MICROSOFT_SQL_SERVER_TYPE_INFO = {
  placeholder: MICROSOFT_SQL_SERVER_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <MicrosoftSQLServerOverview />,
  tags: MICROSOFT_SQL_SERVER_TAGS,
};

export default MICROSOFT_SQL_SERVER_TYPE_INFO;
