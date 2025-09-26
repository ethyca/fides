import { Image, ImageProps } from "fidesui";
import React from "react";

import type { MonitorAggregatedResults } from "~/features/data-discovery-and-detection/action-center/types";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import { ConnectionConfigurationResponse } from "~/types/api";
import type { ConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";
import { ConnectionType as ConnectionTypeModel } from "~/types/api/models/ConnectionType";

import { getDomain, getWebsiteIconUrl } from "../common/utils";
import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
  SAAS_TYPE_LOGO_MAP,
} from "./constants";

// Lightweight shape with only the fields this component uses
type LogoSourceLite = {
  connection_type: ConnectionTypeModel;
  saas_config?: { type?: string } | null;
  name?: string | null;
  key?: string | null;
  secrets?: { url?: string } | null;
};

type ConnectionTypeLogoProps = {
  data:
    | string
    | ConnectionConfigurationResponse
    | ConnectionSystemTypeMap
    | MonitorAggregatedResults
    | LogoSourceLite;
};

const FALLBACK_WEBSITE_LOGO_PATH =
  CONNECTOR_LOGOS_PATH +
  CONNECTION_TYPE_LOGO_MAP.get(ConnectionTypeModel.WEBSITE);

const isDatastoreConnection = (
  obj: unknown,
): obj is
  | ConnectionConfigurationResponse
  | MonitorAggregatedResults
  | LogoSourceLite =>
  !!obj && typeof obj === "object" && "connection_type" in obj;

const isConnectionSystemTypeMap = (
  obj: unknown,
): obj is ConnectionSystemTypeMap =>
  !!obj && typeof obj === "object" && "encoded_icon" in obj;

const isWebsiteConnection = (
  obj: unknown,
): obj is {
  connection_type: ConnectionTypeModel;
  secrets?: { url?: string } | null;
} =>
  isDatastoreConnection(obj) &&
  (obj as { connection_type: ConnectionTypeModel }).connection_type ===
    ConnectionTypeModel.WEBSITE;

const isSaasConnection = (
  obj: unknown,
): obj is {
  connection_type: ConnectionTypeModel;
  saas_config?: { type?: string } | null;
} =>
  isDatastoreConnection(obj) &&
  (obj as { connection_type: ConnectionTypeModel }).connection_type ===
    ConnectionTypeModel.SAAS;

const ConnectionTypeLogo = ({
  data,
  ...props
}: ConnectionTypeLogoProps & ImageProps) => {
  const getImageSrc = (): string => {
    if (isConnectionSystemTypeMap(data) && data.encoded_icon) {
      return `data:image/svg+xml;base64,${data.encoded_icon}`;
    }

    if (isWebsiteConnection(data)) {
      const url = data.secrets?.url;
      if (!url) {
        return FALLBACK_WEBSITE_LOGO_PATH;
      }
      const domain = getDomain(url);
      return getWebsiteIconUrl(domain, 100);
    }

    let item;
    if (isDatastoreConnection(data)) {
      if (isSaasConnection(data) && data.saas_config?.type) {
        // For SAAS connections, look up the logo in SAAS_TYPE_LOGO_MAP
        const saasType = data.saas_config.type as SaasConnectionTypes;
        const saasLogo = SAAS_TYPE_LOGO_MAP.get(saasType);
        if (saasLogo) {
          return CONNECTOR_LOGOS_PATH + saasLogo;
        }
        // If no specific SAAS logo found, use the generic SAAS logo
        return (
          CONNECTOR_LOGOS_PATH +
          CONNECTION_TYPE_LOGO_MAP.get(ConnectionTypeModel.SAAS)
        );
      }

      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) => data.connection_type.toString() === k.toString(),
      );
    } else if (isConnectionSystemTypeMap(data)) {
      const { identifier } = data;
      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) => k.toLowerCase() === identifier.toLowerCase(),
      );
    }
    return item
      ? CONNECTOR_LOGOS_PATH + item[1]
      : FALLBACK_CONNECTOR_LOGOS_PATH;
  };

  const getAltValue = (): string => {
    if (isDatastoreConnection(data)) {
      const maybeName = (data as { name?: string | null }).name;
      const maybeKey = (data as { key?: string | null }).key;
      return maybeName ?? maybeKey ?? "connection";
    }
    if (isConnectionSystemTypeMap(data)) {
      return data.human_readable;
    }
    return data;
  };

  const getFallbackSrc = (): string => {
    if (isWebsiteConnection(data)) {
      return FALLBACK_WEBSITE_LOGO_PATH;
    }
    return FALLBACK_CONNECTOR_LOGOS_PATH;
  };

  return (
    <Image
      boxSize="32px"
      objectFit="cover"
      src={getImageSrc()}
      fallbackSrc={getFallbackSrc()}
      alt={getAltValue()}
      {...props}
    />
  );
};

export default ConnectionTypeLogo;
