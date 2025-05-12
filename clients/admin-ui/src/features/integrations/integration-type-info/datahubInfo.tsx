import { ListItem } from "fidesui";

import {
  InfoHeading,
  InfoText,
  InfoUnorderedList,
} from "~/features/common/copy/components";
import ShowMoreContent from "~/features/common/copy/ShowMoreContent";
import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const DATAHUB_PLACEHOLDER = {
  name: "Datahub",
  key: "datahub_placeholder",
  connection_type: ConnectionType.DATAHUB,
  access: AccessLevel.READ,
  created_at: "",
};

export const DATAHUB_TAGS = ["Sync"];

export const DATAHUB_DESCRIPTION = (
  <>
    Set up a connection to your DataHub instance by providing a name, server
    URL, and access token. You can also select the BigQuery datasets you&apos;d
    like to sync—these will be matched with corresponding datasets in DataHub.
    If no datasets are selected, all available BigQuery datasets will be
    included by default.
  </>
);

export const DatahubOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      DataHub is a metadata platform designed to help organizations manage and
      govern their data. It acts as a centralized repository for tracking and
      discovering data assets across an organization, helping data teams
      understand where their data resides, how it&apos;s used, and how it flows
      through various systems.
    </InfoText>
    <ShowMoreContent>
      <InfoHeading text="Categories" />
      <InfoUnorderedList>
        <ListItem>Data Catalog</ListItem>
      </InfoUnorderedList>
      <InfoHeading text="Permissions" />
      <InfoUnorderedList>
        <ListItem>
          The related user to the access token must have at least the Editor
          role on DataHub.
        </ListItem>
      </InfoUnorderedList>
    </ShowMoreContent>
  </>
);

const DATAHUB_TYPE_INFO = {
  placeholder: DATAHUB_PLACEHOLDER,
  category: ConnectionCategory.DATA_CATALOG,
  overview: <DatahubOverview />,
  tags: DATAHUB_TAGS,
  description: DATAHUB_DESCRIPTION,
};

export default DATAHUB_TYPE_INFO;
