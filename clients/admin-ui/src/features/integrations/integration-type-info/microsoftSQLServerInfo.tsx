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
      Microsoft SQL Server, is a relational database management system (RDBMS)
      developed by Microsoft. It is designed to store, manage, and retrieve data
      as requested by other software applications, which may run either on the
      same computer or across a network.
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
        For detecting databases, Fides requires a user with the following
        permissions/role:
      </InfoText>
      <InfoUnorderedList>
        <ListItem>
          CREATE LOGIN username WITH PASSWORD = &apos;password&apos;;
        </ListItem>
        <ListItem>GRANT SELECT, INSERT, UPDATE TO username;</ListItem>
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
