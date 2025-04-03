import {
  AntButton as Button,
  AntCard as Card,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntInput as Input,
  AntRadio as Radio,
  AntSpace as Space,
  ChevronDownIcon,
  CloseIcon,
  ConfirmationModal,
  InputGroup,
  Skeleton,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { CreateTCFConfigModal } from "./CreateTCFConfigModal";
import { useDeleteTCFConfigurationMutation } from "./tcf-config.slice";

interface TCFConfiguration {
  id: string;
  name: string;
}

interface TCFConfigurationDropdownProps {
  selectedConfigId: string;
  configurations: TCFConfiguration[];
  isLoading?: boolean;
  onConfigurationSelect: (configId: string) => void;
  onConfigurationDelete?: (configId: string) => void;
}

interface DropdownContentProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  searchResults: TCFConfiguration[];
  selectedConfigId: string;
  handleSelection: (id: string) => void;
  userCanCreateConfigs: boolean;
  userCanDeleteConfigs: boolean;
  modalOnOpen: () => void;
  onDeleteOpen: () => void;
  setConfigToDelete: (config: TCFConfiguration) => void;
  isLoading: boolean;
  setDropdownOpen: (open: boolean) => void;
  configurations: TCFConfiguration[];
}

const LoadingContent = () => (
  <Space direction="vertical" size="small">
    <Skeleton width="100%" className="h-4" />
    <Skeleton width="100%" className="h-4" />
    <Skeleton width="100%" className="h-4" />
  </Space>
);

const ConfigurationList = ({
  searchResults,
  selectedConfigId,
  handleSelection,
  userCanDeleteConfigs,
  onDeleteOpen,
  setConfigToDelete,
}: Omit<
  DropdownContentProps,
  | "searchTerm"
  | "setSearchTerm"
  | "isLoading"
  | "userCanCreateConfigs"
  | "modalOnOpen"
  | "setDropdownOpen"
  | "configurations"
>) => (
  <Radio.Group
    onChange={(e) => handleSelection(e.target.value)}
    value={selectedConfigId}
    className="flex flex-col gap-2"
  >
    {searchResults.map((config) => (
      <Flex
        key={config.id}
        className={userCanDeleteConfigs ? "justify-between" : "justify-start"}
      >
        <Radio
          value={config.id}
          name="tcf-config-id"
          data-testid="tcf-config-item"
        >
          <Text className="text-sm">{config.name}</Text>
        </Radio>
        {userCanDeleteConfigs && (
          <Button
            type="text"
            size="small"
            icon={<TrashCanOutlineIcon fontSize={16} />}
            onClick={(e) => {
              e.stopPropagation();
              setConfigToDelete(config);
              onDeleteOpen();
            }}
            data-testid="delete-config-button"
          />
        )}
      </Flex>
    ))}
  </Radio.Group>
);

const DropdownContent = ({
  searchTerm,
  setSearchTerm,
  searchResults,
  selectedConfigId,
  handleSelection,
  userCanCreateConfigs,
  userCanDeleteConfigs,
  modalOnOpen,
  onDeleteOpen,
  setConfigToDelete,
  isLoading,
  setDropdownOpen,
  configurations,
}: DropdownContentProps) => {
  const [currentSelection, setCurrentSelection] =
    useState<string>(selectedConfigId);

  useEffect(() => {
    setCurrentSelection(selectedConfigId);
  }, [selectedConfigId]);

  const handleRadioChange = (value: string) => {
    setCurrentSelection(value);
  };

  let content;
  if (isLoading) {
    content = <LoadingContent />;
  } else if (searchResults.length === 0) {
    content = <Text className="text-center">No configurations found.</Text>;
  } else {
    content = (
      <ConfigurationList
        searchResults={searchResults}
        selectedConfigId={currentSelection}
        handleSelection={handleRadioChange}
        userCanDeleteConfigs={userCanDeleteConfigs}
        onDeleteOpen={onDeleteOpen}
        setConfigToDelete={setConfigToDelete}
      />
    );
  }

  return (
    <Card
      title="TCF Configurations"
      className="min-w-[300px]"
      extra={
        <Button
          type="text"
          size="small"
          icon={<CloseIcon />}
          onClick={() => setDropdownOpen(false)}
          data-testid="close-config-dropdown"
        />
      }
      style={{
        boxShadow: "var(--ant-box-shadow)",
      }}
    >
      {configurations.length > 10 && (
        <InputGroup size="sm">
          <Input
            className="mb-4"
            placeholder="Search..."
            onChange={(e) => setSearchTerm(e.target.value)}
            value={searchTerm}
          />
        </InputGroup>
      )}

      {content}

      <Flex gap="small" className="mt-4">
        {userCanCreateConfigs && (
          <Button
            size="small"
            onClick={() => {
              modalOnOpen();
              setDropdownOpen(false);
            }}
            className="flex-1"
            data-testid="create-config-button"
          >
            + Create
          </Button>
        )}
        <Button
          size="small"
          onClick={() => handleSelection(currentSelection)}
          className="flex-1"
          data-testid="apply-config-button"
          disabled={currentSelection === selectedConfigId}
        >
          Apply
        </Button>
      </Flex>
    </Card>
  );
};

const renderDropdownContent = (props: DropdownContentProps) => (
  <DropdownContent {...props} />
);

export const TCFConfigurationDropdown = ({
  selectedConfigId,
  configurations,
  isLoading = false,
  onConfigurationSelect,
  onConfigurationDelete,
}: TCFConfigurationDropdownProps): JSX.Element => {
  const userCanCreateConfigs = useHasPermission([
    ScopeRegistryEnum.PRIVACY_EXPERIENCE_CREATE,
  ]);
  const userCanDeleteConfigs = useHasPermission([
    ScopeRegistryEnum.PRIVACY_EXPERIENCE_CREATE,
  ]);

  const toast = useToast({ id: "tcf-config-toast" });
  const [deleteTCFConfiguration] = useDeleteTCFConfigurationMutation();

  const {
    isOpen: modalIsOpen,
    onOpen: modalOnOpen,
    onClose: modalOnClose,
  } = useDisclosure();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const [searchTerm, setSearchTerm] = useState<string>("");
  const [configToDelete, setConfigToDelete] = useState<TCFConfiguration>();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const searchResults = useMemo(() => {
    if (!searchTerm) {
      return configurations;
    }
    return configurations.filter((config) =>
      config.name.toLowerCase().includes(searchTerm.toLowerCase()),
    );
  }, [configurations, searchTerm]);

  const selectedConfig = useMemo(
    () => configurations.find((config) => config.id === selectedConfigId),
    [configurations, selectedConfigId],
  );

  const buttonLabel = selectedConfig?.name ?? "Select Configuration";

  const handleSelection = (id: string) => {
    onConfigurationSelect(id);
    setDropdownOpen(false);
  };

  const handleDeleteConfig = async (id: string) => {
    try {
      await deleteTCFConfiguration(id).unwrap();
      onConfigurationDelete?.(id);
      setConfigToDelete(undefined);
      onDeleteClose();
      toast({
        status: "success",
        description: `Configuration "${configToDelete?.name}" was successfully deleted.`,
      });
    } catch (error: any) {
      const errorMsg = getErrorMessage(
        error,
        "A problem occurred while deleting the configuration.",
      );
      toast({ status: "error", description: errorMsg });
    }
  };

  return (
    <>
      <Dropdown
        open={dropdownOpen}
        onOpenChange={setDropdownOpen}
        trigger={["click"]}
        overlayStyle={{
          zIndex: 999, // putting this behind Chakra's modal. Can possibly remove this after Modal is migrated to Ant Design.
        }}
        dropdownRender={() =>
          renderDropdownContent({
            searchTerm,
            setSearchTerm,
            searchResults,
            selectedConfigId,
            handleSelection,
            userCanCreateConfigs,
            userCanDeleteConfigs,
            modalOnOpen,
            onDeleteOpen,
            setConfigToDelete,
            isLoading,
            setDropdownOpen,
            configurations,
          })
        }
      >
        <Button
          icon={<ChevronDownIcon />}
          iconPosition="end"
          data-testid="tcf-config-dropdown-trigger"
        >
          {buttonLabel}
        </Button>
      </Dropdown>

      <CreateTCFConfigModal
        isOpen={modalIsOpen}
        onClose={modalOnClose}
        onSuccess={(configId) => {
          onConfigurationSelect(configId);
        }}
      />

      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={() => {
          setConfigToDelete(undefined);
          onDeleteClose();
        }}
        onConfirm={() => {
          if (configToDelete) {
            handleDeleteConfig(configToDelete.id);
          }
        }}
        title="Delete configuration"
        message="Are you sure you want to delete this configuration? This action
            cannot be undone."
      />
    </>
  );
};
