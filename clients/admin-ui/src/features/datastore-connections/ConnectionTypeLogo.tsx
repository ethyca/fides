import {
  AntAvatar as Avatar,
  AntAvatarProps as AvatarProps,
  EthycaLogo,
  Icons,
} from "fidesui";
import React, { useMemo } from "react";

import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import type { ConnectionConfigurationResponse } from "~/types/api";
import type { ConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";
import { ConnectionType as ConnectionTypeModel } from "~/types/api/models/ConnectionType";

import { getBrandIconUrl, getDomain } from "../common/utils";
import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
  SAAS_TYPE_LOGO_MAP,
} from "./constants";

type SaasConfigLite = {
  type?: string | null;
  name?: string | null;
  fides_key?: string | null;
};

type SecretsLite = {
  url?: string | null;
};

type ConnectionLike = {
  connection_type: ConnectionTypeModel;
  name?: string | null;
  key?: string | null;
  saas_config?: SaasConfigLite | null;
  secrets?: SecretsLite | null;
};

type SystemTypeLike = Pick<
  ConnectionSystemTypeMap,
  "identifier" | "human_readable" | "encoded_icon"
>;

export enum ConnectionLogoKind {
  CONNECTION = "connection",
  SYSTEM = "system",
  STATIC = "static",
}

export type ConnectionLogoSource =
  | {
      kind: ConnectionLogoKind.CONNECTION;
      connectionType: ConnectionTypeModel;
      name?: string | null;
      key?: string | null;
      saasType?: string | null;
      websiteUrl?: string | null;
    }
  | {
      kind: ConnectionLogoKind.SYSTEM;
      identifier: string;
      humanReadable: string;
      encodedIcon?: string | null;
    }
  | {
      kind: ConnectionLogoKind.STATIC;
      key: string;
    };

const FALLBACK_WEBSITE_LOGO_PATH =
  CONNECTOR_LOGOS_PATH +
  CONNECTION_TYPE_LOGO_MAP.get(ConnectionTypeModel.WEBSITE);

const connectionLikeToLogo = (
  connection: ConnectionLike,
): ConnectionLogoSource => ({
  kind: ConnectionLogoKind.CONNECTION,
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
  monitor: ConnectionLike,
): ConnectionLogoSource => connectionLikeToLogo(monitor);

export const connectionLogoFromSystemType = (
  system: SystemTypeLike,
): ConnectionLogoSource => ({
  kind: ConnectionLogoKind.SYSTEM,
  identifier: system.identifier,
  humanReadable: system.human_readable,
  encodedIcon: system.encoded_icon ?? null,
});

export const connectionLogoFromKey = (key: string): ConnectionLogoSource => ({
  kind: ConnectionLogoKind.STATIC,
  key,
});

const isWebsite = (connectionType: ConnectionTypeModel) =>
  connectionType === ConnectionTypeModel.WEBSITE ||
  connectionType === ConnectionTypeModel.TEST_WEBSITE;

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
  if (data.kind === ConnectionLogoKind.SYSTEM) {
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

  if (data.kind === ConnectionLogoKind.CONNECTION) {
    if (isWebsite(data.connectionType)) {
      if (!data.websiteUrl) {
        return FALLBACK_WEBSITE_LOGO_PATH;
      }
      const domain = getDomain(data.websiteUrl);
      const brandIconUrl = getBrandIconUrl(domain, 100);
      return brandIconUrl;
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
  if (data.kind === ConnectionLogoKind.CONNECTION) {
    return data.name ?? data.key ?? "connection";
  }
  if (data.kind === ConnectionLogoKind.SYSTEM) {
    return data.humanReadable;
  }
  return data.key || "connection";
};

const getFallbackIcon = (data: ConnectionLogoSource, size: number) => {
  if (
    data.kind === ConnectionLogoKind.CONNECTION &&
    isWebsite(data.connectionType)
  ) {
    return <Icons.Wikis size={size} />;
  }
  return <EthycaLogo width={size} height={size} />;
};

type ConnectionTypeLogoProps = {
  data: ConnectionLogoSource;
};

const ConnectionTypeLogo = ({
  data,
  size,
  ...props
}: ConnectionTypeLogoProps & AvatarProps) => {
  const imageSrc = useMemo(() => getImageSrc(data), [data]);
  const fallbackIcon = useMemo(
    () => getFallbackIcon(data, (size as number) ?? 32),
    [data, size],
  );
  const altValue = useMemo(() => getAltValue(data), [data]);
  return (
    <Avatar
      shape="square"
      src={imageSrc}
      size={size ?? 32}
      icon={fallbackIcon}
      style={{
        backgroundColor: "transparent",
        color: "var(--ant-color-text)",
      }}
      alt={altValue}
      {...props}
    />
  );
};

export default ConnectionTypeLogo;
