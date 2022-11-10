import { Badge, Tooltip } from "@fidesui/react";

import { ClassificationStatus } from "~/types/api";

type Resource = "dataset" | "system";

const classificationStatuses = (resource: Resource) => ({
  [ClassificationStatus.PROCESSING]: {
    title: "Processing",
    tooltip: `This ${resource} is currently being ${
      resource === "dataset" && "generated and"
    } classified. You will be notified when this process is complete`,
    color: "orange",
  },
  [ClassificationStatus.CREATED]: {
    title: "Processing",
    tooltip: `This ${resource} is currently being ${
      resource === "dataset" && "generated and"
    } and classified. You will be notified when this process is complete`,
    color: "orange",
  },
  [ClassificationStatus.COMPLETE]: {
    title: "Awaiting Review",
    tooltip: `This ${resource} has been automatically classified. Review the results and update the ${resource}.`,
    color: "orange",
  },
  [ClassificationStatus.REVIEWED]: {
    title: "Classified",
    tooltip: `This ${resource} has been classified.`,
    color: "green",
  },
  [ClassificationStatus.FAILED]: {
    title: "Failed",
    tooltip: `This ${resource} must be manually updated.`,
    color: "red",
  },
  unknown: {
    title: "Unknown",
    tooltip: `This ${resource} must be manually updated.`,
    color: "gray",
  },
});

const ClassificationStatusBadge = ({
  status,
  resource,
}: {
  status: ClassificationStatus | undefined;
  resource: Resource;
}) => {
  const statusDisplay = classificationStatuses(resource)[status ?? "unknown"];
  return (
    <Tooltip label={statusDisplay.tooltip}>
      <Badge variant="solid" colorScheme={statusDisplay.color}>
        {statusDisplay.title}
      </Badge>
    </Tooltip>
  );
};

export default ClassificationStatusBadge;
