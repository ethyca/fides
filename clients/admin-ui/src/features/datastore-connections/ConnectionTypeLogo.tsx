import { Image, ImageProps } from "fidesui";
import React from "react";

import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";

import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
} from "./constants";

type ConnectionTypeLogoProps = {
  data: string | ConnectionConfigurationResponse | ConnectionSystemTypeMap;
};

const isDatastoreConnection = (
  obj: any,
): obj is ConnectionConfigurationResponse =>
  (obj as ConnectionConfigurationResponse).connection_type !== undefined;

const isConnectionSystemTypeMap = (obj: any): obj is ConnectionSystemTypeMap =>
  (obj as ConnectionSystemTypeMap).encoded_icon !== undefined;

const ConnectionTypeLogo = ({
  data,
  ...props
}: ConnectionTypeLogoProps & ImageProps) => {
  const getImageSrc = (): string => {
    if (isConnectionSystemTypeMap(data) && data.encoded_icon) {
      return `data:image/svg+xml;base64,${data.encoded_icon}`;
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
  return (
    <Image
      boxSize="32px"
      objectFit="cover"
      src={getImageSrc()}
      fallbackSrc={FALLBACK_CONNECTOR_LOGOS_PATH}
      alt={getAltValue()}
      {...props}
    />
  );
};

export default ConnectionTypeLogo;
