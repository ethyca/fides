import { SystemBulkAddToGroupPayload, SystemUpsertWithGroups } from "../types";

export const useMockUpdateSystemWithGroupsMutation = () => {
  const update = async (system: SystemUpsertWithGroups) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      data: system,
    };
  };

  return [update];
};

export const useMockBulkUpdateSystemWithGroupsMutation = () => {
  const bulkUpdate = async (payload: SystemBulkAddToGroupPayload) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      data: payload,
    };
  };

  return [bulkUpdate];
};
