import { Heading, ListItem, Text, UnorderedList } from "fidesui";
import { ReactNode } from "react";

const InfoHeading = ({ text }: { text: string }) => (
  <Heading fontSize="sm" mt={6} mb={1}>
    {text}
  </Heading>
);

const InfoText = ({ children }: { children: ReactNode }) => (
  <Text fontSize="xs" mb={4}>
    {children}
  </Text>
);

const InfoUnorderedList = ({ children }: { children: ReactNode }) => (
  <UnorderedList fontSize="xs">{children}</UnorderedList>
);

const BigQueryOverview = () => (
  <>
    <InfoHeading text="Overview" />
    <InfoText>
      Continuously monitor BigQuery to detect and track schema-level changes,
      automatically discover and label data categories as well as automatically
      process DSR (privacy requests) and consent enforcement to proactively
      manage data governance risks.
    </InfoText>
    <InfoHeading text="Categories" />
    <InfoUnorderedList>
      <ListItem>Data Warehouse</ListItem>
      <ListItem>Storage system</ListItem>
      <ListItem>Cloud provider</ListItem>
      <ListItem>Data detection</ListItem>
      <ListItem>Data discovery</ListItem>
      <ListItem>DSR automation</ListItem>
      <ListItem>Consent orchestration</ListItem>
    </InfoUnorderedList>
    <InfoHeading text="Permissions" />
    <InfoText>
      For detection and discovery, Fides requires a read-only BigQuery service
      account with limited permissions. If you intend to automate governance for
      DSR or Consent, Fides requires a read-and-write BigQuery service account
      to any project you would like Fides to govern.
    </InfoText>
    <InfoText>
      A BigQuery administrator can create the necessary role for Fides using
      BigQuery&apos;s roles guide and assign this to a service account using
      BigQuery&apos;s service account guide.
    </InfoText>
    <InfoText>
      The permissions allow Fides to read the schema of, and data stored in
      projects, datasets and tables as well write restricted updates based on
      your policy configurations to tables you specify as part of DSR and
      Consent orchestration.
    </InfoText>
    <InfoHeading text="Permissions list" />
    <InfoUnorderedList>
      <ListItem>bigquery.jobs.create</ListItem>
      <ListItem>bigquery.jobs.list</ListItem>
      <ListItem>bigquery.routines.get</ListItem>
      <ListItem>bigquery.routines.list</ListItem>
      <ListItem>bigquery.datasets.get</ListItem>
      <ListItem>bigquery.tables.get</ListItem>
      <ListItem>bigquery.tables.getData</ListItem>
      <ListItem>bigquery.tables.list</ListItem>
      <ListItem>bigquery.tables.updateData</ListItem>
      <ListItem>bigquery.projects.get</ListItem>
    </InfoUnorderedList>
  </>
);

export default BigQueryOverview;
