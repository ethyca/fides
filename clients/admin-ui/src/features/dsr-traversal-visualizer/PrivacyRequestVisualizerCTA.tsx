import { Button, Modal, Select } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { useGetAllPropertiesQuery } from "~/features/properties/property.slice";

const PrivacyRequestVisualizerCTA = () => {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [propertyId, setPropertyId] = useState<string | undefined>();
  const { data } = useGetAllPropertiesQuery({ page: 1, size: 100 });
  const properties = data?.items ?? [];

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        data-testid="open-traversal-visualizer"
      >
        Preview traversal
      </Button>
      <Modal
        open={open}
        onCancel={() => setOpen(false)}
        title="Preview a property's traversal"
        okText="Open"
        okButtonProps={{ disabled: !propertyId }}
        onOk={() => {
          if (!propertyId) {
            return;
          }
          router.push(
            `/privacy-requests/visualizer/${encodeURIComponent(propertyId)}/access`,
          );
        }}
      >
        <Select
          placeholder="Select a property"
          value={propertyId}
          onChange={setPropertyId}
          options={properties.map((p) => ({ value: p.id, label: p.name }))}
          style={{ width: "100%" }}
        />
      </Modal>
    </>
  );
};

export default PrivacyRequestVisualizerCTA;
