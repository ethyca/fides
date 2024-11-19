/* eslint-disable react/no-array-index-key */
import {
  Accordion,
  AccordionButton,
  AccordionIcon,
  AccordionItem,
  AccordionPanel,
  AntButton as Button,
  AntFlex as Flex,
  AntSpace as Space,
  AntTag as Tag,
  AntTypography as Typography,
  Box,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Spacer,
  Spinner,
  useDisclosure,
} from "fidesui";

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
      isOpen={isOpen}
      onClose={onClose}
      size="xxl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent maxWidth="800px">
        <ModalHeader>
          {systemPurposeSummary ? systemPurposeSummary?.name : "Vendor"}
        </ModalHeader>
        <ModalBody>
          {isLoading ? (
            <Flex className="h-80 w-full" align="center" justify="center">
              <Spinner />
            </Flex>
          ) : (
            !!systemPurposeSummary && (
              <Typography>
                <Title level={5}>Purposes</Title>
                {Object.entries(systemPurposeSummary.purposes || {}).length >
                0 ? (
                  <Accordion allowMultiple>
                    {Object.entries(systemPurposeSummary.purposes).map(
                      ([purposeName], index: number) => (
                        <AccordionItem key={index}>
                          {({ isExpanded }) => (
                            <>
                              <AccordionButton
                                backgroundColor={
                                  isExpanded ? "gray.50" : "unset"
                                }
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
        </ModalBody>

        <ModalFooter>
          <Button size="small" onClick={onClose}>
            Close
          </Button>
          <Spacer />
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
