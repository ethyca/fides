import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const MYSQL_PLACEHOLDER = {
  name: "MySQL",
  key: "mysql_placeholder",
  connection_type: ConnectionType.MYSQL,
  access: AccessLevel.READ,
  created_at: "",
};

export const MYSQL_TAGS = ["Database", "Detection", "Discovery", "MySQL"];

export const MySQLOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>Add infotext</InfoText>
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
          CREATE USER &apos;username&apos; IDENTIFIED WITH authentication_plugin
          BY &apos;password&apos;;
        </ListItem>
        <ListItem>
          GRANT SELECT, INSERT ON database.* TO
          &apos;username&apos;@&apos;%&apos;;
        </ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const MYSQL_TYPE_INFO = {
  placeholder: MYSQL_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <MySQLOverview />,
  tags: MYSQL_TAGS,
};

export default MYSQL_TYPE_INFO;
