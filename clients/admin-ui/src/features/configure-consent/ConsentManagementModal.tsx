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
              <>
                {Object.entries(systemPurposeSummary.purposes || {}).length >
                  0 && <Typography.Text strong>Purposes</Typography.Text>}
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
                                <Typography.Text strong>
                                  Data Categories
                                </Typography.Text>
                                <Space size={[0, 2]} wrap>
                                  {systemPurposeSummary.purposes[
                                    purposeName
                                  ].data_uses?.map((data_use) => (
                                    <Tag key={data_use}>{data_use}</Tag>
                                  ))}
                                </Space>
                              </Flex>
                              <Flex className="my-4" vertical>
                                <Typography.Text strong>
                                  Data Categories
                                </Typography.Text>
                                <Space size={[0, 2]} wrap>
                                  {systemPurposeSummary.purposes[
                                    purposeName
                                  ].legal_bases?.map((legal_base) => (
                                    <Tag key={legal_base}>{legal_base}</Tag>
                                  ))}
                                </Space>
                              </Flex>
                            </AccordionPanel>
                          </>
                        )}
                      </AccordionItem>
                    ),
                  )}
                </Accordion>
                <div className="my-4">
                  <Typography.Text strong>Features</Typography.Text>
                  <Space size={[0, 2]} wrap>
                    {systemPurposeSummary.features?.map((feature) => (
                      <Tag key={feature}>{feature}</Tag>
                    ))}
                  </Space>
                </div>
                <div className="my-4">
                  <Typography.Text strong>Data Categories</Typography.Text>
                  <Space size={[0, 2]} wrap>
                    {systemPurposeSummary.data_categories?.map((category) => (
                      <Tag key={category}>{category}</Tag>
                    ))}
                  </Space>
                </div>
              </>
            )
          )}
        </ModalBody>

        <ModalFooter>
          <Button size="small" onClick={onClose}>
            Close{" "}
          </Button>
          <Spacer />
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
