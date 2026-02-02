import {
  Button,
  ChakraModal as Modal,
  ChakraModalBody as ModalBody,
  ChakraModalCloseButton as ModalCloseButton,
  ChakraModalContent as ModalContent,
  ChakraModalHeader as ModalHeader,
  ChakraModalOverlay as ModalOverlay,
  Empty,
  Form,
  Space,
  Table,
  Typography,
  useChakraToast as useToast,
} from "fidesui";
import { isEmpty } from "lodash";
import { useEffect, useState } from "react";

import { PreferencesSavedExtended } from "~/types/api";

import { getErrorMessage } from "../common/helpers";
import SearchInput from "../common/SearchInput";
import { useLazyGetCurrentPrivacyPreferencesQuery } from "./consent-reporting.slice";
import useConsentLookupTable from "./hooks/useConsentLookupTable";
import {
  filterTcfConsentPreferences,
  mapTcfPreferencesToRowColumns,
} from "./hooks/useTcfConsentTable";
import TcfConsentTable from "./TcfConsentTable";

interface ConsentLookupModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ConsentLookupModal = ({ isOpen, onClose }: ConsentLookupModalProps) => {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<
    PreferencesSavedExtended | undefined | null
  >();
  const [searchQuery, setSearchQuery] = useState("");
  const [getCurrentPrivacyPreferencesTrigger] =
    useLazyGetCurrentPrivacyPreferencesQuery();

  const toast = useToast();

  useEffect(() => {
    // reset state when modal is closed
    if (!isOpen) {
      setSearchResults(undefined);
      setIsSearching(false);
    }
  }, [isOpen]);

  const handleSearch = async (search: string) => {
    setIsSearching(true);
    const { data, isError, error } = await getCurrentPrivacyPreferencesTrigger({
      search,
    });
    const errorStatus = error && "status" in error && error?.status;
    if (isError && errorStatus !== 404) {
      const errorMsg = getErrorMessage(
        error,
        `A problem occurred while looking up the preferences.`,
      );

      toast({ status: "error", description: errorMsg });
    } else {
      setSearchResults(data || null);
    }
    setIsSearching(false);
  };

  const preferences = searchResults?.preferences || [];
  const hasPreferences = !isEmpty(preferences);

  // Check if TCF data exists for conditional rendering
  const tcfData = mapTcfPreferencesToRowColumns(searchResults);
  const filteredTcfData = filterTcfConsentPreferences(tcfData);
  const hasTcfData = !isEmpty(filteredTcfData);

  // Privacy notice preferences table
  const { tableProps, columns } = useConsentLookupTable(preferences);

  return (
    <Modal
      id="consent-lookup-modal"
      isOpen={isOpen}
      onClose={onClose}
      size="6xl"
      returnFocusOnClose={false}
      isCentered
    >
      <ModalOverlay />
      <ModalContent>
        <ModalCloseButton />
        <ModalHeader pb={2}>Consent preference lookup</ModalHeader>
        <ModalBody>
          <Typography.Paragraph>
            Use this search to look up an individual&apos;s latest consent
            record. You can search by phone number, email, external ID or device
            ID to retrieve the most recent consent preference associated with
            that exact identifier.
          </Typography.Paragraph>
          <Typography.Paragraph>
            <strong>Note:</strong> This is an exact match search—partial entries
            or similar results will not be returned. This lookup retrieves only
            the most recent consent preference, not the full consent history.
          </Typography.Paragraph>

          <Form layout="vertical" className="w-1/2">
            <Form.Item label="Subject search" className="mb-4 mt-6">
              <Space.Compact className="w-full">
                <SearchInput
                  data-testid="subject-search-input"
                  placeholder="Enter email, phone number, external ID or device ID"
                  onChange={setSearchQuery}
                  width="100%"
                  onPressEnter={() => handleSearch(searchQuery)}
                />
                <Button
                  type="primary"
                  loading={isSearching}
                  onClick={() => handleSearch(searchQuery)}
                >
                  Search
                </Button>
              </Space.Compact>
            </Form.Item>
          </Form>
          <div className="mb-4">
            {(!hasTcfData || hasPreferences) && (
              <Table
                {...tableProps}
                columns={columns}
                loading={isSearching}
                locale={{
                  emptyText: (
                    <Empty
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                      description={
                        searchResults === undefined
                          ? "Search for an email, phone number, or device ID."
                          : "No results found."
                      }
                    />
                  ),
                }}
              />
            )}
            {hasTcfData && (
              <div className="mt-4">
                <TcfConsentTable
                  tcfPreferences={searchResults}
                  loading={isSearching}
                />
              </div>
            )}
          </div>
        </ModalBody>
      </ModalContent>
    </Modal>
  );
};
export default ConsentLookupModal;
