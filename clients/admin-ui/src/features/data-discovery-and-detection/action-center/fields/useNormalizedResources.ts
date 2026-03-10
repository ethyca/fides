import { SkipToken } from "@reduxjs/toolkit/query";
import _ from "lodash";

import useNodeMap, { mapNodes } from "~/features/common/hooks/useNodeMap";
import { useGetStagedResourceDetailsQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";

import { useGetMonitorFieldsQuery } from "./monitor-fields.slice";
import { MonitorResource } from "./types";

const useNormalizedResources = (
  listQueryParams: Exclude<
    Parameters<typeof useGetMonitorFieldsQuery>[0],
    SkipToken
  >,
  detailsParams: Exclude<
    Parameters<typeof useGetStagedResourceDetailsQuery>[0],
    SkipToken
  >,
) => {
  const listQuery = useGetMonitorFieldsQuery(listQueryParams);
  const detailsQuery = useGetStagedResourceDetailsQuery(detailsParams, {
    skip: !detailsParams.stagedResourceUrn,
  });

  const {
    update: updateResources,
    nodes,
    reset: resetNormalizedState,
  } = useNodeMap<MonitorResource>();

  const refetchListQuery = () => {
    resetNormalizedState();
    listQuery.refetch();
  };

  const refetchDetailsQuery = () => {
    resetNormalizedState();
    detailsQuery.refetch();
  };

  if (listQuery.data?.items) {
    updateResources(
      mapNodes(
        listQuery.data.items.map((item) => ({ key: item.urn, ...item })),
      ),
    );
  }

  /** disabling for now. */
  // if (detailsQuery.currentData) {
  //   updateResources(
  //     mapNodes([
  //       {
  //         key: detailsQuery.currentData.urn,
  //         ...detailsQuery.currentData,
  //       },
  //     ]),
  //   );
  // }

  return {
    listQuery: {
      ...listQuery,
      nodes: _.chain(listQuery.data?.items)
        .defaultTo([])
        .flatMap((item) =>
          _.chain(nodes.get(item.urn))
            .thru((node) => (node ? [node] : []))
            .value(),
        )
        .thru(mapNodes)
        .value(),
      refetch: refetchListQuery,
    },
    detailsQuery: {
      ...detailsQuery,
      node: detailsParams.stagedResourceUrn
        ? nodes.get(detailsParams.stagedResourceUrn)
        : undefined,
      refetch: refetchDetailsQuery,
    },
    nodes,
  };
};

export default useNormalizedResources;
