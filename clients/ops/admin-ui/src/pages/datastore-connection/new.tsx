import AddConnection from "datastore-connections/add-connection/AddConnection";
import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import type { NextPage } from "next";

const NewDatastoreConnection: NextPage = () => (
  <ConnectionsLayout>
    <AddConnection />
  </ConnectionsLayout>
);
export default NewDatastoreConnection;
