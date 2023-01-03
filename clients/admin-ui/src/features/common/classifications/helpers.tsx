import {
  ClassificationStatus,
  ClassifyInstanceResponseValues,
} from "~/types/api";

export const POLL_INTERVAL_SECONDS = 3;

export const checkIsClassificationFinished = (
  classifications: ClassifyInstanceResponseValues[] | undefined
) =>
  classifications
    ? classifications.every(
        (c) =>
          c.status === ClassificationStatus.COMPLETE ||
          c.status === ClassificationStatus.FAILED ||
          c.status === ClassificationStatus.REVIEWED
      )
    : false;
