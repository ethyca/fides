import { Center, Spinner } from "@fidesui/react";
import { debounce } from "common/utils";
import React, { useEffect, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "../../app/hooks";
import {
  selectConnectionTypeState,
  setConnectionOptions,
  useGetAllConnectionTypesQuery,
} from "../connection-type";
import ConnectionFilters from "./ConnectionFilters";
import ConnectionGrid from "./ConnectionGrid";
import ConnectionsEmptyState from "./ConnectionsEmptyState";
import ConnectionHeading from "./ConnectionsHeader";
import {
  selectDatastoreConnectionFilters,
  setOrphanedFromSystem,
  useGetAllDatastoreConnectionsQuery,
} from "./datastore-connection.slice";
import { DatastoreConnectionParams } from "./types";

const ConnectionsContainer: React.FC = () => {
  const mounted = useRef(false);
  const dispatch = useAppDispatch();
  const { connectionOptions } = useAppSelector(selectConnectionTypeState);
  const filters = useAppSelector(selectDatastoreConnectionFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<DatastoreConnectionParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
  );

  const { data: connectionTypesData } = useGetAllConnectionTypesQuery(
    {
      search: "",
    },
    { skip: connectionOptions.length > 0 }
  );

  const {
    data: datastoreConnectionsData,
    isFetching,
    isLoading,
    isSuccess,
  } = useGetAllDatastoreConnectionsQuery(cachedFilters);

  const hasData = datastoreConnectionsData!?.items?.length > 0;

  useEffect(() => {
    dispatch(setOrphanedFromSystem(true));
  }, [dispatch]);

  useEffect(() => {
    mounted.current = true;
    if (connectionOptions.length === 0 && connectionTypesData?.items) {
      dispatch(setConnectionOptions(connectionTypesData.items));
    }
    updateCachedFilters.current(filters);
    return () => {
      mounted.current = false;
    };
  }, [connectionOptions.length, connectionTypesData?.items, dispatch, filters]);

  return (
    <>
      <ConnectionHeading />
      {mounted.current && <ConnectionFilters />}
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {mounted.current &&
        isSuccess &&
        (hasData ? (
          <ConnectionGrid
            items={datastoreConnectionsData!?.items}
            total={datastoreConnectionsData!?.total}
          />
        ) : (
          <ConnectionsEmptyState />
        ))}
    </>
  );
};

export default ConnectionsContainer;
