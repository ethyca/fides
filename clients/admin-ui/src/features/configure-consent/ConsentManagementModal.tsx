/* eslint-disable react/no-array-index-key */
import {
  Button,
  ChakraAccordion as Accordion,
  ChakraAccordionButton as AccordionButton,
  ChakraAccordionIcon as AccordionIcon,
  ChakraAccordionItem as AccordionItem,
  ChakraAccordionPanel as AccordionPanel,
  ChakraBox as Box,
  ChakraSpacer as Spacer,
  Flex,
  Modal,
  Space,
  Spin,
  Tag,
  Typography,
  useChakraDisclosure as useDisclosure,
} from "fidesui";

import { MODAL_SIZE } from "~/features/common/modals/modal-sizes";
import { useGetSystemPurposeSummaryQuery } from "~/features/plus/plus.slice";

const { Text, Title } = Typography;

export const useConsentManagementModal = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  return { isOpen, onOpen, onClose };
};

type Props = {
  isOpen: boolean;
  onClose: () => void;
  fidesKey: string;
};

export const ConsentManagementModal = ({
  isOpen,
  onClose,
  fidesKey,
}: Props) => {
  const { data: systemPurposeSummary, isLoading } =
    useGetSystemPurposeSummaryQuery(fidesKey);

  const listRender = (label: string, list: string[]) => (
    <>
      <Title level={5}>{label}</Title>
      {list?.length ? (
        <div>
          <Space size={[0, 2]} wrap>
            {list?.map((item) => <Tag key={item}>{item}</Tag>)}
          </Space>
        </div>
      ) : (
        <Text italic>no known {label.toLowerCase()}</Text>
      )}
    </>
  );

  return (
    <Modal
      open={isOpen}
      onCancel={onClose}
      width={MODAL_SIZE.lg}
      centered
      destroyOnHidden
      title={systemPurposeSummary ? systemPurposeSummary?.name : "Vendor"}
      footer={
        <>
          <Button size="small" onClick={onClose}>
            Close
          </Button>
          <Spacer />
        </>
      }
    >
      {isLoading ? (
        <Spin />
      ) : (
        !!systemPurposeSummary && (
          <Typography>
            <Title level={5}>Purposes</Title>
            {Object.entries(systemPurposeSummary.purposes || {}).length > 0 ? (
              <Accordion allowMultiple>
                {Object.entries(systemPurposeSummary.purposes).map(
                  ([purposeName], index: number) => (
                    <AccordionItem key={index}>
                      {({ isExpanded }) => (
                        <>
                          <AccordionButton
                            backgroundColor={isExpanded ? "gray.50" : "unset"}
                          >
                            <Box flex="1" textAlign="left">
                              {purposeName}
                            </Box>
                            <AccordionIcon />
                          </AccordionButton>
                          <AccordionPanel backgroundColor="gray.50">
                            <Flex className="my-4" vertical>
                              {listRender(
                                "Data uses",
                                systemPurposeSummary.purposes[purposeName]
                                  .data_uses,
                              )}
                            </Flex>
                            <Flex className="my-4" vertical>
                              {listRender(
                                "Legal basis",
                                systemPurposeSummary.purposes[purposeName]
                                  .legal_bases,
                              )}
                            </Flex>
                          </AccordionPanel>
                        </>
                      )}
                    </AccordionItem>
                  ),
                )}
              </Accordion>
            ) : (
              <Text italic>no known purposes</Text>
            )}
            <div className="my-4">
              {listRender("Features", systemPurposeSummary.features)}
            </div>
            <div className="my-4">
              {listRender(
                "Data categories",
                systemPurposeSummary.data_categories,
              )}
            </div>
          </Typography>
        )
      )}
    </Modal>
  );
};
