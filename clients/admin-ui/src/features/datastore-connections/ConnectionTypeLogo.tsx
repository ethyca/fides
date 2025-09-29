import { Image, ImageProps } from "fidesui";
import React from "react";

import type { MonitorAggregatedResults } from "~/features/data-discovery-and-detection/action-center/types";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import type { ConnectionConfigurationResponse } from "~/types/api";
import type { ConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";
import { ConnectionType as ConnectionTypeModel } from "~/types/api/models/ConnectionType";

import { getDomain, getWebsiteIconUrl } from "../common/utils";
import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
  SAAS_TYPE_LOGO_MAP,
} from "./constants";

export type ConnectionLogoSource =
  | {
      kind: "connection";
      connectionType: ConnectionTypeModel;
      name?: string | null;
      key?: string | null;
      saasType?: string | null;
      websiteUrl?: string | null;
    }
  | {
      kind: "system";
      identifier: string;
      humanReadable: string;
      encodedIcon?: string | null;
    }
  | {
      kind: "static";
      key: string;
    };

type ConnectionLike = {
  connection_type: ConnectionTypeModel;
  name?: string | null;
  key?: string | null;
  saas_config?: { type?: string | null } | null;
  secrets?: { url?: string | null } | null;
};

type SystemTypeLike = Pick<
  ConnectionSystemTypeMap,
  "identifier" | "human_readable" | "encoded_icon"
>;

const FALLBACK_WEBSITE_LOGO_PATH =
  CONNECTOR_LOGOS_PATH +
  CONNECTION_TYPE_LOGO_MAP.get(ConnectionTypeModel.WEBSITE);

const connectionLikeToLogo = (
  connection: ConnectionLike,
): ConnectionLogoSource => ({
  kind: "connection",
  connectionType: connection.connection_type,
  name: connection.name ?? null,
  key: connection.key ?? null,
  saasType: connection.saas_config?.type ?? null,
  websiteUrl: connection.secrets?.url ?? null,
});

export const connectionLogoFromConfiguration = (
  connection: Pick<
    ConnectionConfigurationResponse,
    "connection_type" | "name" | "key" | "saas_config" | "secrets"
  >,
): ConnectionLogoSource => connectionLikeToLogo(connection);

export const connectionLogoFromMonitor = (
  monitor: Pick<
    MonitorAggregatedResults,
    "connection_type" | "name" | "key" | "saas_config" | "secrets"
  >,
): ConnectionLogoSource => connectionLikeToLogo(monitor);

export const connectionLogoFromSystemType = (
  system: SystemTypeLike,
): ConnectionLogoSource => ({
  kind: "system",
  identifier: system.identifier,
  humanReadable: system.human_readable,
  encodedIcon: system.encoded_icon ?? null,
});

export const connectionLogoFromKey = (key: string): ConnectionLogoSource => ({
  kind: "static",
  key,
});

const resolveSaasLogo = (saasType?: string | null) => {
  if (!saasType) {
    return undefined;
  }
  const typed = saasType as SaasConnectionTypes;
  return SAAS_TYPE_LOGO_MAP.get(typed);
};

const buildStaticLogoPath = (key: string) => {
  if (!key) {
    return FALLBACK_CONNECTOR_LOGOS_PATH;
  }
  if (key.startsWith("data:")) {
    return key;
  }
  if (key.startsWith("http")) {
    return key;
  }
  const normalizedKey = key.endsWith(".svg") ? key : `${key}.svg`;
  return CONNECTOR_LOGOS_PATH + normalizedKey;
};

const getImageSrc = (data: ConnectionLogoSource): string => {
  if (data.kind === "system") {
    if (data.encodedIcon) {
      return `data:image/svg+xml;base64,${data.encodedIcon}`;
    }
    const item = [...CONNECTION_TYPE_LOGO_MAP].find(
      ([key]) => key.toLowerCase() === data.identifier.toLowerCase(),
    );
    return item
      ? CONNECTOR_LOGOS_PATH + item[1]
      : FALLBACK_CONNECTOR_LOGOS_PATH;
  }

  if (data.kind === "connection") {
    if (data.connectionType === ConnectionTypeModel.WEBSITE) {
      if (!data.websiteUrl) {
        return FALLBACK_WEBSITE_LOGO_PATH;
      }
      const domain = getDomain(data.websiteUrl);
      return getWebsiteIconUrl(domain, 100);
    }

    if (data.connectionType === ConnectionTypeModel.SAAS) {
      const saasLogo = resolveSaasLogo(data.saasType);
      if (saasLogo) {
        return CONNECTOR_LOGOS_PATH + saasLogo;
      }
    }

    const mappedLogo = CONNECTION_TYPE_LOGO_MAP.get(data.connectionType);
    return mappedLogo
      ? CONNECTOR_LOGOS_PATH + mappedLogo
      : FALLBACK_CONNECTOR_LOGOS_PATH;
  }

  return buildStaticLogoPath(data.key);
};

const getAltValue = (data: ConnectionLogoSource): string => {
  if (data.kind === "connection") {
    return data.name ?? data.key ?? "connection";
  }
  if (data.kind === "system") {
    return data.humanReadable;
  }
  return data.key || "connection";
};

const getFallbackSrc = (data: ConnectionLogoSource): string => {
  if (
    data.kind === "connection" &&
    data.connectionType === ConnectionTypeModel.WEBSITE
  ) {
    return FALLBACK_WEBSITE_LOGO_PATH;
  }
  return FALLBACK_CONNECTOR_LOGOS_PATH;
};

type ConnectionTypeLogoProps = {
  data: ConnectionLogoSource;
};

const ConnectionTypeLogo = ({
  data,
  ...props
}: ConnectionTypeLogoProps & ImageProps) => {
  return (
    <Image
      boxSize="32px"
      objectFit="cover"
      src={getImageSrc(data)}
      fallbackSrc={getFallbackSrc(data)}
      alt={getAltValue(data)}
      {...props}
    />
  );
};

export default ConnectionTypeLogo;
