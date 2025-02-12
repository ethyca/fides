import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import { Box, Center, Spinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useAlert } from "~/features/common/hooks";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/routes";
import {
  connectionTypeApi,
  selectConnectionTypes,
  setConnection,
  setConnectionOption,
} from "~/features/connection-type";
import { datastoreConnectionApi } from "~/features/datastore-connections";
import EditConnection from "~/features/datastore-connections/edit-connection/EditConnection";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

const EditDatastoreConnection: NextPage = () => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { id } = router.query;
  const { errorAlert } = useAlert();
  const connectionOptions = useAppSelector(selectConnectionTypes);
  const [isLoading, setIsLoading] = useState(true);

  const getConnectionOption = (
    data: ConnectionConfigurationResponse,
    options: ConnectionSystemTypeMap[],
  ): ConnectionSystemTypeMap | undefined => {
    const item = options.find(
      (option) =>
        (option.identifier === data.connection_type &&
          option.identifier !== ConnectionType.SAAS) ||
        option.identifier === data.saas_config?.type,
    );
    return item;
  };

  useEffect(() => {
    const handleError = () => {
      errorAlert(`An error occurred while loading ${router.query.id}`);
      router.push(DATASTORE_CONNECTION_ROUTE, undefined, { shallow: true });
    };

    const fetchConnectionData = async (key: string) => {
      try {
        const promises: any[] = [];
        promises.push(
          dispatch(
            datastoreConnectionApi.endpoints.getDatastoreConnectionByKey.initiate(
              key,
            ),
          ),
        );
        if (connectionOptions.length === 0) {
          promises.push(
            dispatch(
              connectionTypeApi.endpoints.getAllConnectionTypes.initiate({
                search: "",
              }),
            ),
          );
        }
        const results = await Promise.allSettled(promises);
        if (results.every((result) => result.status === "fulfilled")) {
          dispatch(setConnection((results[0] as any).value.data));
          const options: ConnectionSystemTypeMap[] = [
            ...(results[1]
              ? (results[1] as any).value.data.items
              : connectionOptions),
          ];
          const item = getConnectionOption(
            (results[0] as any).value.data,
            options,
          );
          dispatch(setConnectionOption(item));
          setIsLoading(false);
        } else {
          handleError();
        }
      } catch (error) {
        handleError();
      }
    };

    if (id) {
      fetchConnectionData(id as string);
    }

    return () => {};
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <>
      {isLoading && (
        <Box display="flex" h="100vh" justifyContent="center">
          <Center>
            <Spinner />
          </Center>
        </Box>
      )}
      {!isLoading && (
        <ConnectionsLayout>
          <EditConnection />
        </ConnectionsLayout>
      )}
    </>
  );
};
export default EditDatastoreConnection;
