import { Image, ImageProps } from "fidesui";
import React from "react";

import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

import { getDomain, getWebsiteIconUrl } from "../common/utils";
import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
} from "./constants";

type ConnectionTypeLogoProps = {
  data: string | ConnectionConfigurationResponse | ConnectionSystemTypeMap;
};

const FALLBACK_WEBSITE_LOGO_PATH =
  CONNECTOR_LOGOS_PATH + CONNECTION_TYPE_LOGO_MAP.get(ConnectionType.WEBSITE);
const isDatastoreConnection = (
  obj: any,
): obj is ConnectionConfigurationResponse =>
  (obj as ConnectionConfigurationResponse).connection_type !== undefined;

const isConnectionSystemTypeMap = (obj: any): obj is ConnectionSystemTypeMap =>
  (obj as ConnectionSystemTypeMap).encoded_icon !== undefined;

const isWebsiteConnection = (
  obj: any,
): obj is ConnectionConfigurationResponse => {
  return obj?.connection_type === ConnectionType.WEBSITE;
};

const ConnectionTypeLogo = ({
  data,
  ...props
}: ConnectionTypeLogoProps & ImageProps) => {
  const getImageSrc = (): string => {
    if (isConnectionSystemTypeMap(data) && data.encoded_icon) {
      return `data:image/svg+xml;base64,${data.encoded_icon}`;
    }

    if (isWebsiteConnection(data)) {
      const url = (data as any).secrets?.url;
      if (!url) {
        return FALLBACK_WEBSITE_LOGO_PATH;
      }
      const domain = getDomain(url);
      return getWebsiteIconUrl(domain, 100);
    }

    let item;
    if (isDatastoreConnection(data)) {
      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) =>
          (data.connection_type.toString() !== ConnectionType.SAAS &&
            data.connection_type.toString() === k) ||
          (data.connection_type.toString() === ConnectionType.SAAS &&
            data.saas_config?.type?.toString() === k.toString()),
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
      return data.name ?? data.key;
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
