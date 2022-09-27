import AddConnection from "datastore-connections/add-connection/AddConnection";
import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import type { NextPage } from "next";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import Custom404 from "../404";

const NewDatastoreConnection: NextPage = () => (
  <Flags
    authorizedFlags={["createNewConnection"]}
    renderOn={() => (
      <ConnectionsLayout>
        <AddConnection />
      </ConnectionsLayout>
    )}
    renderOff={() => <Custom404 />}
  />
);
export default NewDatastoreConnection;
