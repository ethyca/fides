import {
  Button,
  FormLabel,
  HStack,
  Input,
  InputGroup,
  InputLeftAddon,
  Modal,
  ModalBody,
  ModalCloseButton,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  ModalProps,
  Stack,
} from "fidesui";

import { MultiSelectTags } from "~/features/common/dropdown/MultiSelectTags";
import { useRequestFilters } from "~/features/privacy-requests/hooks/useRequestFilters";

export const RequestTableFilterModal = ({
  onClose,
  ...props
}: Omit<ModalProps, "children">): JSX.Element => {
  const {
    handleStatusChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    from,
    selectedStatusList,
    statusList,
    to,
  } = useRequestFilters();

  return (
    <Modal onClose={onClose} size="xl" {...props}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader borderBottomWidth={1} borderBottomColor="gray.200">
          All Filters
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody py={4}>
          <Stack gap={4}>
            <HStack gap={3}>
              <InputGroup size="sm" flex={1}>
                <InputLeftAddon
                  as="label"
                  htmlFor="from-date"
                  borderRadius="md"
                >
                  From
                </InputLeftAddon>
                <Input
                  type="date"
                  name="From"
                  value={from}
                  max={to || undefined}
                  onChange={handleFromChange}
                  borderRadius="md"
                  id="from-date"
                />
              </InputGroup>
              <InputGroup size="sm" flex={1}>
                <InputLeftAddon as="label" htmlFor="to-date" borderRadius="md">
                  To
                </InputLeftAddon>
                <Input
                  type="date"
                  borderRadius="md"
                  name="To"
                  value={to}
                  min={from || undefined}
                  onChange={handleToChange}
                  id="to-date"
                />
              </InputGroup>
            </HStack>
            <Stack>
              <FormLabel id="request-status-label">Status</FormLabel>
              <MultiSelectTags
                list={statusList}
                selectedList={selectedStatusList}
                onChange={handleStatusChange}
                aria-describedby="request-status-label"
              />
            </Stack>
          </Stack>
        </ModalBody>
        <ModalFooter justifyContent="space-between">
          <Button size="sm" variant="ghost" onClick={handleClearAllFilters}>
            Clear all
          </Button>
          <Button size="sm" colorScheme="primary" onClick={onClose}>
            Done
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
