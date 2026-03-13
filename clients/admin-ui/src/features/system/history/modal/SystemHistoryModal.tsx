import { ChakraFlex as Flex, Modal, Tag } from "fidesui";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { SystemHistoryResponse } from "~/types/api";

import SelectedHistoryProvider from "./SelectedHistoryContext";
import SystemDataForm from "./SystemDataForm";

const getBadges = (before: Record<string, any>, after: Record<string, any>) => {
  const badges = [];
  const specialFields = new Set([
    "egress",
    "ingress",
    "privacy_declarations",
    "vendor_id",
  ]);

  if (before.egress || after.egress || before.ingress || after.ingress) {
    badges.push("Data Flow");
  }

  const hasPrivacyDeclarations =
    (before.privacy_declarations && before.privacy_declarations.length > 0) ||
    (after.privacy_declarations && after.privacy_declarations.length > 0);

  if (hasPrivacyDeclarations) {
    badges.push("Data Uses");
  }

  const hasOtherFields = [...Object.keys(before), ...Object.keys(after)].some(
    (key) => !specialFields.has(key),
  );

  if (!hasPrivacyDeclarations && hasOtherFields) {
    badges.unshift("System Information");
  }

  return badges;
};

interface Props {
  selectedHistory: SystemHistoryResponse;
  isOpen: boolean;
  onClose: () => void;
}

const SystemHistoryModal = ({ selectedHistory, isOpen, onClose }: Props) => (
  <Modal
    open={isOpen}
    onCancel={onClose}
    centered
    destroyOnClose
    width={MODAL_SIZE.xl}
    title={
      <span className="pr-6">
        Change detail
        {selectedHistory &&
          getBadges(selectedHistory.before, selectedHistory.after).map(
            (badge, index) => (
              <Tag
                // eslint-disable-next-line react/no-array-index-key
                key={index}
                color="minos"
                className="ml-2"
              >
                {badge}
              </Tag>
            ),
          )}
      </span>
    }
    footer={null}
  >
    <Flex justifyContent="space-between">
      <div style={{ flex: "0 50%", marginRight: "12px" }}>
        <SelectedHistoryProvider
          selectedHistory={selectedHistory}
          formType="before"
        >
          <SystemDataForm initialValues={selectedHistory?.before} />
        </SelectedHistoryProvider>
      </div>
      <div style={{ flex: "0 50%", marginLeft: "12px" }}>
        <SelectedHistoryProvider
          selectedHistory={selectedHistory}
          formType="after"
        >
          <SystemDataForm initialValues={selectedHistory?.after} />
        </SelectedHistoryProvider>
      </div>
    </Flex>
  </Modal>
);

export default SystemHistoryModal;
