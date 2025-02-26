import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const SCYLLA_PLACEHOLDER = {
  name: "Scylla",
  key: "scylla_placeholder",
  connection_type: ConnectionType.SCYLLA,
  access: AccessLevel.READ,
  created_at: "",
};

export const SCYLLA_TAGS = [
  "Database",
  "Detection",
  "Discovery",
  "DSR automation",
  "ScyllaDB",
];

export const ScyllaOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      ScyllaDB is an open-sources distributed NoSQL data store designed to be
      compatible with Apache Cassandra. Connect Fides to your ScyllaDB to detect
      and track changes in keyspaces and tables and automatically discover and
      label data categories to proactively manage data governance risks.
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
        permission on all keyspaces. If you intend to automate governance for
        DSR or Consent, Fides requires the role to to be granted SELECT and
        MODIFY on all keyspaces. The permissions allow Fides to read the schema
        of, and data stored in keyspaces, tables, and fields as well as write
        restricted updates based on your policy configurations to tables you
        specify as part of DSR and Consent orchestration. For a complete list of
        permissions view the Scylla DB documentation.
      </InfoText>
      <InfoHeading text="Permissions list" />
      <InfoUnorderedList>
        <ListItem>SELECT ALL KEYSPACES</ListItem>
        <ListItem>MODIFY ALL KEYSPACES</ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const SCYLLA_TYPE_INFO = {
  placeholder: SCYLLA_PLACEHOLDER,
  category: ConnectionCategory.DATABASE,
  overview: <ScyllaOverview />,
  tags: SCYLLA_TAGS,
};

export default SCYLLA_TYPE_INFO;
