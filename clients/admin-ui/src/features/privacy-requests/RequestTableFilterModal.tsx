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

import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { useRequestFilters } from "~/features/privacy-requests/hooks/useRequestFilters";

import { FilterSelect } from "../common/dropdown/FilterSelect";

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
              <FormLabel size="md" htmlFor="request-status">
                Status
              </FormLabel>
              <FilterSelect
                id="request-status"
                mode="multiple"
                options={SubjectRequestStatusOptions}
                value={statusList}
                onChange={handleStatusChange}
                data-testid="request-status-filter"
              />
            </Stack>
            <Stack>
              <FormLabel size="md" htmlFor="request-action-type">
                Request Type
              </FormLabel>
              <FilterSelect
                id="request-action-type"
                mode="multiple"
                options={SubjectRequestActionTypeOptions}
                value={actionTypeList}
                onChange={handleActionTypeChange}
                data-testid="request-action-type-filter"
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
