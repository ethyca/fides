import React, { useCallback, useState } from "react";

import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";

import SaaSVersionModal from "../SaaSVersionModal";

interface PendingModalState {
  connectionKey: string;
  version: string;
}

interface ActiveModalState {
  connectorType: string;
  version: string;
}

/**
 * Hook providing a version detail modal keyed by connection key + version string.
 * Resolves connector_type via the connection config before opening the modal.
 */
export const useSaaSVersionModal = () => {
  const [pending, setPending] = useState<PendingModalState | null>(null);
  const [active, setActive] = useState<ActiveModalState | null>(null);

  const { data: connection } = useGetDatastoreConnectionByKeyQuery(
    pending?.connectionKey ?? "",
    { skip: !pending?.connectionKey },
  );

  // Once the connection resolves, promote pending to active so the modal opens.
  // connectorType is captured into active so the modal doesn't depend on the
  // query after pending is cleared (skip: true returns undefined data).
  // If the connection has no saas_config.type (non-SaaS), bail out silently
  // so pending doesn't stay set indefinitely.
  React.useEffect(() => {
    if (!pending || !connection) return;
    if (connection.saas_config?.type) {
      setActive({ connectorType: connection.saas_config.type, version: pending.version });
    }
    setPending(null);
  }, [pending, connection]);

  const openVersionModal = useCallback((connectionKey: string, version: string) => {
    setPending({ connectionKey, version });
  }, []);

  const handleClose = useCallback(() => setActive(null), []);

  const modal = active ? (
    <SaaSVersionModal
      isOpen
      onClose={handleClose}
      connectorType={active.connectorType}
      version={active.version}
    />
  ) : null;

  return { openVersionModal, modal };
};
