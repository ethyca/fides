/* eslint-disable import/prefer-default-export */


import config from "../config/config.json";

export const hostUrl =
  process.env.NODE_ENV === "development"
    ? config.fidesops_host_development
    : config.fidesops_host_production;