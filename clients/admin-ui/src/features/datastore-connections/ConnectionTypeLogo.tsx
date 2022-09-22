import { Image } from "@fidesui/react";
import React from "react";

import {
  CONNECTION_TYPE_LOGO_MAP,
  ConnectionType,
  CONNECTOR_LOGOS_PATH,
  FALLBACK_CONNECTOR_LOGOS_PATH,
} from "./constants";
import { DatastoreConnection, isDatastoreConnection } from "./types";

type ConnectionTypeLogoProps = {
  data: string | DatastoreConnection;
};

const ConnectionTypeLogo: React.FC<ConnectionTypeLogoProps> = ({ data }) => {
  const getImageSrc = (): string => {
    let item;
    if (isDatastoreConnection(data)) {
      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) =>
          (data.connection_type.toString() !== ConnectionType.SAAS &&
            data.connection_type.toString() === k) ||
          (data.connection_type.toString() === ConnectionType.SAAS &&
            data.saas_config?.type?.toString() === k.toString())
      );
    } else {
      item = [...CONNECTION_TYPE_LOGO_MAP].find(
        ([k]) => k.toLowerCase() === data.toLowerCase()
      );
    }
    return item
      ? CONNECTOR_LOGOS_PATH + item[1]
      : FALLBACK_CONNECTOR_LOGOS_PATH;
  };
  return (
    <Image
      boxSize="32px"
      objectFit="cover"
      src={getImageSrc()}
      fallbackSrc={FALLBACK_CONNECTOR_LOGOS_PATH}
      alt={isDatastoreConnection(data) ? data.name : data}
    />
  );
};

export default ConnectionTypeLogo;
