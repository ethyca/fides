import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const GOOGLE_CLOUD_SQL_POSTGRES_PLACEHOLDER = {
  name: "Google Cloud SQL for Postgres",
  key: "google_cloud_sql_for_postgres_placeholder",
  connection_type: ConnectionType.GOOGLE_CLOUD_SQL_POSTGRES,
  access: AccessLevel.READ,
  created_at: "",
};

export const GOOGLE_CLOUD_SQL_POSTGRES_TAGS = [
  "Database",
  "Detection",
  "Discovery",
  "DSR automation",
];

export const GoogleCloudSQLPostgresOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Google Cloud SQL for Postgres is a fully-managed relational database
      service that simplifies the setup, maintenance, management, and
      administration of Postgres databases. Connect Fides to your Google Cloud
      SQL for Postgres to detect and track changes in schemas and tables and
      automatically discover and label data categories to proactively manage
      data governance risks.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Database</ListItem>
        <ListItem>SQL database</ListItem>
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
        permission. The permissions allow Fides to read the schema of, and data
        stored in tables, and fields as well as write restricted updates based
        on your policy configurations to tables you specify as part of DSR and
        orchestration. For a complete list of permissions view the Google Cloud
        SQL for Postgres DB documentation.
      </InfoText>
      <InfoText>
        The following GCP service account permissions are needed when setting up
        Google Cloud SQL for Postgres.
      </InfoText>
      <InfoHeading text="Permissions list" />
      <InfoUnorderedList>
        <ListItem>cloudsql.instances.connect</ListItem>
        <ListItem>cloudsql.instances.get</ListItem>
        <ListItem>cloudsql.instances.login</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO = {
  placeholder: GOOGLE_CLOUD_SQL_POSTGRES_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <GoogleCloudSQLPostgresOverview />,
  tags: GOOGLE_CLOUD_SQL_POSTGRES_TAGS,
};

export default GOOGLE_CLOUD_SQL_POSTGRES_TYPE_INFO;
