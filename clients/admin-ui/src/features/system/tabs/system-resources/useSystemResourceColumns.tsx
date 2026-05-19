import { createColumnHelper } from "@tanstack/react-table";

import { DefaultCell } from "~/features/common/table/v2";
import { RelativeTimestampCell } from "~/features/common/table/v2/cells";
import { getServiceLabel } from "~/features/data-discovery-and-detection/action-center/utils/cloudInfraServiceInfo";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import SystemResourceTagsCell from "./SystemResourceTagsCell";

const useSystemResourceColumns = ({
  onResourceClick,
}: {
  onResourceClick: (resource: CloudInfraStagedResource) => void;
}) => {
  const columnHelper = createColumnHelper<CloudInfraStagedResource>();

  const name = columnHelper.accessor((row) => row.name ?? row.urn, {
    id: "name",
    cell: (props) => (
      <button
        type="button"
        onClick={() => onResourceClick(props.row.original)}
        title={props.row.original.source_id}
        data-testid={`open-resource-${props.row.original.urn}`}
        className="text-xs font-semibold text-[var(--fidesui-minos)] hover:underline"
      >
        {props.getValue()}
      </button>
    ),
    header: "Resource",
  });

  const service = columnHelper.accessor((row) => row.service, {
    id: "service",
    cell: (props) => <DefaultCell value={getServiceLabel(props.getValue())} />,
    header: "Service",
  });

  const region = columnHelper.accessor((row) => row.location, {
    id: "region",
    cell: (props) => <DefaultCell value={props.getValue()} />,
    header: "Region",
  });

  const accountId = columnHelper.accessor((row) => row.cloud_account_id, {
    id: "account_id",
    cell: (props) => <DefaultCell value={props.getValue()} />,
    header: "Account ID",
  });

  const tags = columnHelper.accessor((row) => row.tags, {
    id: "tags",
    cell: (props) => <SystemResourceTagsCell tags={props.getValue()} />,
    header: "Tags",
    size: 280,
  });

  const approved = columnHelper.accessor((row) => row.updated_at, {
    id: "approved",
    cell: (props) => <RelativeTimestampCell time={props.getValue()} />,
    header: "Approved",
  });

  return [name, service, tags, region, accountId, approved];
};

export default useSystemResourceColumns;
