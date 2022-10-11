import { Center, Spinner } from "@fidesui/react";
import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  reset,
  selectConnectionTypeState,
  setConnection,
  setConnectionOption,
} from "~/features/connection-type";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import EditConnection from "~/features/datastore-connections/edit-connection/EditConnection";

import Custom404 from "../404";

const EditDatastoreConnection: NextPage = () => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { connection, connectionOption, connectionOptions } = useAppSelector(
    selectConnectionTypeState
  );

  const { data, isFetching, isLoading, isSuccess } =
    useGetDatastoreConnectionByKeyQuery(router.query.id as string);

  useEffect(() => {
    if (data) {
      dispatch(setConnection(data));
      dispatch(
        setConnectionOption(
          connectionOptions.find(
            (option) =>
              option.identifier === connection?.connection_type ||
              connection?.saas_config?.type
          )
        )
      );
    }
    return () => {
      // Reset the connection type slice to its initial state
      dispatch(reset());
    };
  }, [connection, connectionOption, connectionOptions, data, dispatch]);

  return (
    <>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess &&
        (data ? (
          <ConnectionsLayout>
            {connection && <EditConnection />}
          </ConnectionsLayout>
        ) : (
          <Custom404 />
        ))}
    </>
  );
};
export default EditDatastoreConnection;
