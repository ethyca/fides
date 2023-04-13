import { Image, ImageProps } from "@fidesui/react";
import React from "react";

import { ConnectionSystemTypeMap, ConnectionType } from "~/types/api";
import { isConnectionSystemTypeMap } from "~/types/api/models/ConnectionSystemTypeMap";

import {
  CONNECTION_TYPE_LOGO_MAP,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
} from "./constants";
import { DatastoreConnection, isDatastoreConnection } from "./types";

type ConnectionTypeLogoProps = {
  data: string | DatastoreConnection | ConnectionSystemTypeMap;
};

const ConnectionTypeLogo: React.FC<ConnectionTypeLogoProps & ImageProps> = ({
  data,
  ...props
}) => {
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
            data.saas_config?.type?.toString() === k.toString())
      );
    } else if (isConnectionSystemTypeMap(data)) {
      const { identifier } = data;
      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) => k.toLowerCase() === identifier.toLowerCase()
      );
    }
    return item
      ? CONNECTOR_LOGOS_PATH + item[1]
      : FALLBACK_CONNECTOR_LOGOS_PATH;
  };
  const getAltValue = (): string => {
    if (isDatastoreConnection(data)) {
      return data.name;
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
