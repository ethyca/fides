import { Image, ImageProps } from "fidesui";
import React from "react";

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

type ConnectionTypeLogoProps = {
  data: string | ConnectionConfigurationResponse | ConnectionSystemTypeMap;
};

const FALLBACK_WEBSITE_LOGO_PATH =
  CONNECTOR_LOGOS_PATH +
  CONNECTION_TYPE_LOGO_MAP.get(ConnectionTypeModel.WEBSITE);

const isDatastoreConnection = (
  obj: any,
): obj is ConnectionConfigurationResponse =>
  (obj as ConnectionConfigurationResponse).connection_type !== undefined;

const isConnectionSystemTypeMap = (obj: any): obj is ConnectionSystemTypeMap =>
  (obj as ConnectionSystemTypeMap).encoded_icon !== undefined;

const isWebsiteConnection = (
  obj: any,
): obj is ConnectionConfigurationResponse => {
  return obj?.connection_type === ConnectionTypeModel.WEBSITE;
};

const isSaasConnection = (obj: any): obj is ConnectionConfigurationResponse => {
  return obj?.connection_type === ConnectionTypeModel.SAAS;
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
