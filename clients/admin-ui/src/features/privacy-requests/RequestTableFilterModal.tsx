import {
  AntButton as Button,
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
import {
  SubjectRequestActionTypeMap,
  SubjectRequestStatusMap,
} from "~/features/privacy-requests/constants";
import { useRequestFilters } from "~/features/privacy-requests/hooks/useRequestFilters";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

interface RequestTableFilterModalProps extends Omit<ModalProps, "children"> {
  onFilterChange: () => void;
}
export const RequestTableFilterModal = ({
  onClose,
  onFilterChange,
  ...props
}: RequestTableFilterModalProps): JSX.Element => {
  const {
    handleStatusChange,
    handleActionTypeChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    from,
    to,
    status: statusList,
    action_type: actionTypeList,
  } = useRequestFilters(onFilterChange);

  return (
    <Modal onClose={onClose} size="xl" {...props}>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader borderBottomWidth={1} borderBottomColor="gray.200">
          All Filters
        </ModalHeader>
        <ModalCloseButton />
        <ModalBody py={4} sx={{ "& label": { mb: 0 } }}>
          <Stack gap={4}>
            <Stack>
              <FormLabel size="md" id="request-date-range-label">
                Date range
              </FormLabel>
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
                    aria-describedby="request-date-range-label"
                  />
                </InputGroup>
                <InputGroup size="sm" flex={1}>
                  <InputLeftAddon
                    as="label"
                    htmlFor="to-date"
                    borderRadius="md"
                  >
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
                    aria-describedby="request-date-range-label"
                  />
                </InputGroup>
              </HStack>
            </Stack>
            <Stack>
              <FormLabel size="md" id="request-status-label">
                Status
              </FormLabel>
              <MultiSelectTags<PrivacyRequestStatus>
                options={SubjectRequestStatusMap}
                value={statusList}
                onChange={handleStatusChange}
                aria-describedby="request-status-label"
              />
            </Stack>
            <Stack>
              <FormLabel size="md" id="request-action-type-label">
                Request Type
              </FormLabel>
              <MultiSelectTags<ActionType>
                options={SubjectRequestActionTypeMap}
                value={actionTypeList}
                onChange={handleActionTypeChange}
                aria-describedby="request-action-type-label"
              />
            </Stack>
          </Stack>
        </ModalBody>
        <ModalFooter justifyContent="space-between">
          <Button type="text" onClick={handleClearAllFilters}>
            Clear all
          </Button>
          <Button type="primary" onClick={onClose}>
            Done
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};
