import { Center, Spinner } from "@fidesui/react";
import { debounce } from "common/utils";
import React, { useEffect, useRef, useState } from "react";

import { useAppSelector } from "../../app/hooks";
import ConnectionFilters from "./ConnectionFilters";
import ConnectionGrid from "./ConnectionGrid";
import ConnectionsEmptyState from "./ConnectionsEmptyState";
import ConnectionHeading from "./ConnectionsHeader";
import {
  selectDatastoreConnectionFilters,
  useGetAllDatastoreConnectionsQuery,
} from "./datastore-connection.slice";
import { DatastoreConnectionParams } from "./types";

const ConnectionsContainer: React.FC = () => {
  const filters = useAppSelector(selectDatastoreConnectionFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const mounted = useRef(false);
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<DatastoreConnectionParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
  );

  useEffect(() => {
    mounted.current = true;
    updateCachedFilters.current(filters);
    return () => {
      mounted.current = false;
    };
  }, [setCachedFilters, filters]);

  const { data, isFetching, isLoading } =
    useGetAllDatastoreConnectionsQuery(cachedFilters);

  const hasData = data!?.items.length > 0;

  return (
    <>
      <ConnectionHeading hasConnections={hasData} />
      {mounted.current && <ConnectionFilters />}
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {!mounted.current && !hasData && <ConnectionsEmptyState />}
      {hasData && <ConnectionGrid items={data!?.items} total={data!?.total} />}
    </>
  );
};

export default ConnectionsContainer;
