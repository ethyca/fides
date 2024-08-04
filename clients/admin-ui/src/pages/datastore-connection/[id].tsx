import ConnectionsLayout from "datastore-connections/ConnectionsLayout";
import { Box, Center, Spinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { useAlert } from "~/features/common/hooks";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/v2/routes";
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
  const { errorAlert } = useAlert();
  const connectionOptions = useAppSelector(selectConnectionTypes);
  const [isFetching, setIsFetching] = useState(false);
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
        setIsFetching(true);
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
          setIsFetching(false);
          setIsLoading(false);
        } else {
          handleError();
        }
      } catch (error) {
        handleError();
      }
    };

    const { id } = router.query;
    if (id && !isFetching && isLoading) {
      fetchConnectionData(id as string);
    }

    return () => {};
  }, [connectionOptions, dispatch, errorAlert, isFetching, isLoading, router]);

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
