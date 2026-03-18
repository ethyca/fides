import type { MessageInstance } from "antd/lib/message/interface";

let globalMessageApi: MessageInstance | null = null;

/**
 * Store the messageApi instance from FidesUIProvider so it can be
 * used outside the React component tree (e.g. Redux middleware).
 */
export const setGlobalMessageApi = (api: MessageInstance | null) => {
  globalMessageApi = api;
};

export const getGlobalMessageApi = () => globalMessageApi;
