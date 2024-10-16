import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const RDS_POSTGRES_PLACEHOLDER = {
  name: "Amazon RDS Postgres",
  key: "rds_postgres_placeholder",
  connection_type: ConnectionType.RDS_POSTGRES,
  access: AccessLevel.READ,
  created_at: "",
};

export const RDS_POSTGRES_TAGS = [
  "Database",
  "Detection",
  "Discovery",
  "DSR automation",
];

export const RDSPostgresOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Amazon RDS Postgres is a fully-managed relational database service that
      simplifies the setup, maintenance, management, and administration of
      Postgres databases. Connect Fides to your Amazon RDS Postgres to detect
      and track changes in schemas and tables and automatically discover and
      label data categories to proactively manage data governance risks.
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
        <ListItem>CREATE USER username WITH LOGIN;</ListItem>
        <ListItem>GRANT rds_iam TO username;</ListItem>
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

const RDS_POSTGRES_TYPE_INFO = {
  placeholder: RDS_POSTGRES_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <RDSPostgresOverview />,
  tags: RDS_POSTGRES_TAGS,
};

export default RDS_POSTGRES_TYPE_INFO;
