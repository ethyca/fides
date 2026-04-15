import { Checkbox, Flex, Modal, Spin, Text, useMessage } from "fidesui";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import { useSetSystemLinksMutation } from "~/features/integrations/system-links.slice";

interface LinkExistingIntegrationModalProps {
  open: boolean;
  onClose: () => void;
  systemFidesKey: string;
}

const LinkExistingIntegrationModal = ({
  open,
  onClose,
  systemFidesKey,
}: LinkExistingIntegrationModalProps) => {
  const [selected, setSelected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [setSystemLinks] = useSetSystemLinksMutation();
  const message = useMessage();

  const { data, isFetching } = useGetAllDatastoreConnectionsQuery({
    page: 1,
    size: 100,
    orphaned_from_system: true,
  });

  const options = useMemo(
    () =>
      (data?.items ?? []).map((item) => ({
        label: item.name ?? item.key,
        value: item.key,
      })),
    [data],
  );

  const resetAndClose = () => {
    setSelected([]);
    onClose();
  };

  const handleLink = async () => {
    if (selected.length === 0) {
      return;
    }
    setSubmitting(true);
    try {
      await Promise.all(
        selected.map((connectionKey) =>
          setSystemLinks({
            connectionKey,
            body: { links: [{ system_fides_key: systemFidesKey }] },
          }).unwrap(),
        ),
      );
      message.success(
        `Linked ${selected.length} integration${selected.length !== 1 ? "s" : ""}.`,
      );
      resetAndClose();
    } catch (error) {
      const rtkError = error as Parameters<typeof getErrorMessage>[0];
      message.error(getErrorMessage(rtkError));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title="Link existing integration"
      open={open}
      onCancel={resetAndClose}
      onOk={handleLink}
      okText="Link"
      okButtonProps={{
        disabled: selected.length === 0 || submitting,
        loading: submitting,
      }}
      width={520}
    >
      <Text type="secondary" className="mb-4 block">
        Choose one or more integrations to connect to this system. Only
        integrations not yet linked to a system are shown.
      </Text>
      {isFetching && (
        <Flex justify="center" className="py-4">
          <Spin />
        </Flex>
      )}
      {!isFetching && options.length === 0 && (
        <Text type="secondary">No available integrations to link.</Text>
      )}
      {!isFetching && options.length > 0 && (
        <Checkbox.Group
          value={selected}
          onChange={(values) => setSelected(values as string[])}
          options={options}
          className="flex flex-col gap-2"
        />
      )}
    </Modal>
  );
};

export default LinkExistingIntegrationModal;
