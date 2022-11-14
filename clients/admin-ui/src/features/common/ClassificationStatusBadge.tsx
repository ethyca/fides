import { Badge, Tooltip } from "@fidesui/react";

import { ClassificationStatus, GenerateTypes } from "~/types/api";

const classificationStatuses = (resource: GenerateTypes) => {
  const resourceSingular =
    resource === GenerateTypes.DATASETS ? "dataset" : "system";
  return {
    [ClassificationStatus.PROCESSING]: {
      title: "Processing",
      tooltip: `This ${resourceSingular} is currently being ${
        resourceSingular === "dataset" && "generated and"
      } classified. You will be notified when this process is complete`,
      color: "orange",
    },
    [ClassificationStatus.CREATED]: {
      title: "Processing",
      tooltip: `This ${resourceSingular} is currently being ${
        resourceSingular === "dataset" && "generated and"
      } and classified. You will be notified when this process is complete`,
      color: "orange",
    },
    [ClassificationStatus.COMPLETE]: {
      title: "Awaiting Review",
      tooltip: `This ${resourceSingular} has been automatically classified. Review the results and update the ${resourceSingular}.`,
      color: "orange",
    },
    [ClassificationStatus.REVIEWED]: {
      title: "Classified",
      tooltip: `This ${resourceSingular} has been classified.`,
      color: "green",
    },
    [ClassificationStatus.FAILED]: {
      title: "Failed",
      tooltip: `This ${resourceSingular} must be manually updated.`,
      color: "red",
    },
    unknown: {
      title: "Unknown",
      tooltip: `This ${resourceSingular} must be manually updated.`,
      color: "gray",
    },
  };
};

const ClassificationStatusBadge = ({
  status,
  resource,
}: {
  status: ClassificationStatus | undefined;
  resource: GenerateTypes;
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
