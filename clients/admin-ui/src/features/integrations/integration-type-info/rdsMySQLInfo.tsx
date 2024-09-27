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
        For detecting database RDS instances and clusters, Fides requires an IAM
        user with the following permissions/role:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>rds:DescribeDBClusters</ListItem>
        <ListItem>rds:DescribeDBInstances</ListItem>
        <ListItem>rds-db:connect</ListItem>
      </InfoUnorderedList>
      <InfoText>
        And per database it requires the following permissions:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>CREATE USER 'username_you_configured' IDENTIFIED WITH AWSAuthenticationPlugin AS 'RDS';</ListItem>
        <ListItem>ALTER USER 'username_you_configured'@'%' REQUIRE SSL;</ListItem>
        <ListItem>GRANT ALL PRIVILEGES ON database_you_configured.* TO 'username_you_configured'@'%';</ListItem>
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
