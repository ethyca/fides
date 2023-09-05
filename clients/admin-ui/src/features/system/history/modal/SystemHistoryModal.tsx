import {
  Badge,
  Heading,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalHeader,
  ModalOverlay,
  Spacer,
} from "@fidesui/react";

import { SystemHistory } from "~/types/api/models/SystemHistory";

import SelectedHistoryProvider from "./SelectedHistoryContext";
import SystemDataForm from "./SystemDataForm";

const getBadges = (before, after) => {
  const badges = [];
  const specialFields = new Set(["egress", "ingress", "privacy_declarations"]);

  if (before.egress || after.egress || before.ingress || after.ingress) {
    badges.push("Data Flow");
  }

  if (
    (before.privacy_declarations && before.privacy_declarations.length > 0) ||
    (after.privacy_declarations && after.privacy_declarations.length > 0)
  ) {
    badges.push("Data Uses");
  }

  const hasOtherFields = [...Object.keys(before), ...Object.keys(after)].some(
    (key) => !specialFields.has(key)
  );
  if (hasOtherFields) {
    badges.unshift("System Information");
  }

  return badges;
};

interface Props {
  selectedHistory: SystemHistory;
  isOpen: boolean;
  onClose: () => void;
}

const SystemHistoryModal = ({ selectedHistory, isOpen, onClose }: Props) => (
    <Modal isOpen={isOpen} onClose={onClose} size="3xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader
          style={{
            backgroundColor: "#F7FAFC",
            borderTopLeftRadius: "8px",
            borderTopRightRadius: "8px",
            borderBottom: "1px solid #E2E8F0",
          }}
        >
          <Heading size="xs">
            <span style={{ verticalAlign: "middle" }}>Diff review</span>
            {selectedHistory && (
              <>
                {getBadges(selectedHistory.before, selectedHistory.after).map(
                  (badge, index) => (
                    <Badge
                      // eslint-disable-next-line react/no-array-index-key
                      key={index}
                      marginLeft="8px"
                      fontSize="10px"
                      padding="0px 4px"
                      variant="solid"
                      lineHeight="18px"
                      height="18px"
                      backgroundColor="#718096"
                      borderRadius="2px"
                    >
                      {badge}
                    </Badge>
                  )
                )}
              </>
            )}
          </Heading>
          <>
            <Spacer />
            <ModalCloseButton />
          </>
        </ModalHeader>
        <ModalBody paddingTop={0} paddingBottom={6}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
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
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );

export default SystemHistoryModal;
