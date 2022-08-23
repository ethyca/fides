import ConnectionsContainer from "datastore-connections/ConnectionsContainer";
import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import type { NextPage } from "next";

const DatastoreConnection: NextPage = () => (
  <ConnectionsLayout>
    <ConnectionsContainer />
  </ConnectionsLayout>
);
export default DatastoreConnection;
