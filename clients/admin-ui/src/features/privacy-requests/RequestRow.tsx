import {
  Alert,
  AlertTitle,
  Button,
  ButtonGroup,
  Checkbox,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Portal,
  Td,
  Text,
  Tr,
  useClipboard,
  useToast,
} from "@fidesui/react";
import DaysLeftTag from "common/DaysLeftTag";
import RequestType from "common/RequestType";
import { formatDate } from "common/utils";
import { useRouter } from "next/router";
import React, { useRef, useState } from "react";

import { useFeatures } from "~/features/common/features";
import { PrivacyRequestStatus as ApiPrivacyRequestStatus } from "~/types/api/models/PrivacyRequestStatus";

import PII from "../common/PII";
import RequestStatusBadge from "../common/RequestStatusBadge";
import ReprocessButton from "./buttons/ReprocessButton";
import DenyPrivacyRequestModal from "./DenyPrivacyRequestModal";
import {
  useApproveRequestMutation,
  useDenyRequestMutation,
} from "./privacy-requests.slice";
import { PrivacyRequestEntity } from "./types";

const useRequestRow = (request: PrivacyRequestEntity) => {
  const {
    flags: { navV2 },
  } = useFeatures();
  const toast = useToast();
  const hoverButtonRef = useRef<HTMLButtonElement>(null);
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [approveRequest, approveRequestResult] = useApproveRequestMutation();
  const [denyRequest] = useDenyRequestMutation();
  const handleMenuOpen = () => setMenuOpen(true);
  const handleMenuClose = () => setMenuOpen(false);
  const handleMouseEnter = () => setHovered(true);
  const handleMouseLeave = () => setHovered(false);
  const shiftFocusToHoverMenu = () => {
    if (hoverButtonRef.current) {
      hoverButtonRef.current.focus();
    }
  };
  const handleFocus = () => setFocused(true);
  const handleBlur = () => setFocused(false);
  const handleApproveRequest = () => approveRequest(request);
  const handleDenyRequest = (reason: string) =>
    denyRequest({ id: request.id, reason });
  const { onCopy } = useClipboard(request.id);
  const handleModalOpen = () => setModalOpen(true);
  const handleModalClose = () => {
    setModalOpen(false);
    setFocused(false);
    setHovered(false);
    setMenuOpen(false);
  };
  const handleIdCopy = () => {
    onCopy();
    if (typeof window !== "undefined") {
      toast({
        title: "Request ID copied",
        duration: 5000,
        render: () => (
          <Alert bg="gray.600" borderRadius="6px" display="flex">
            <AlertTitle color="white">Request ID copied</AlertTitle>
          </Alert>
        ),
        containerStyle: {
          minWidth: "0px",
        },
      });
    }
  };

  const router = useRouter();
  const handleViewDetails = () => {
    const url = `/${navV2 ? "privacy-requests" : "subject-request"}/${
      request.id
    }`;
    router.push(url);
  };
  return {
    approveRequestResult,
    hovered,
    focused,
    menuOpen,
    modalOpen,
    handleModalOpen,
    handleModalClose,
    handleMenuClose,
    handleMenuOpen,
    handleMouseEnter,
    handleMouseLeave,
    handleFocus,
    handleBlur,
    handleIdCopy,
    handleApproveRequest,
    handleDenyRequest,
    hoverButtonRef,
    shiftFocusToHoverMenu,
    handleViewDetails,
  };
};

const RequestRow: React.FC<{
  isChecked: boolean;
  onCheckChange: (id: string, checked: boolean) => void;
  request: PrivacyRequestEntity;
}> = ({ isChecked, onCheckChange, request }) => {
  const {
    hovered,
    handleMenuOpen,
    handleMenuClose,
    handleMouseEnter,
    handleMouseLeave,
    handleApproveRequest,
    handleDenyRequest,
    handleIdCopy,
    menuOpen,
    approveRequestResult,
    hoverButtonRef,
    modalOpen,
    handleModalClose,
    handleModalOpen,
    shiftFocusToHoverMenu,
    handleFocus,
    handleBlur,
    focused,
    handleViewDetails,
  } = useRequestRow(request);
  const showMenu = hovered || menuOpen || focused;

  return (
    <Tr
      key={request.id}
      _hover={{ bg: "gray.50" }}
      bg={showMenu ? "gray.50" : "white"}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      height="36px"
    >
      <Td px={0}>
        <Checkbox
          aria-label="Select request"
          isChecked={!!isChecked}
          isDisabled={request.status !== "error"}
          onChange={(e) => onCheckChange(request.id, e.target.checked)}
        />
      </Td>
      <Td pl={0} py={1}>
        <RequestStatusBadge status={request.status} />
      </Td>
      <Td py={1}>
        <DaysLeftTag
          daysLeft={request.days_left}
          includeText={false}
          status={request.status as ApiPrivacyRequestStatus}
        />
      </Td>
      <Td py={1}>
        <RequestType rules={request.policy.rules} />
      </Td>
      <Td py={1}>
        <Text fontSize="xs">
          <PII
            data={
              request.identity
                ? request.identity.email || request.identity.phone_number || ""
                : ""
            }
          />
        </Text>
      </Td>
      <Td py={1}>
        <Text fontSize="xs">{formatDate(request.created_at)}</Text>
      </Td>
      <Td py={1}>
        <Text fontSize="xs">
          <PII data={request.reviewer ? request.reviewer.username : ""} />
        </Text>
      </Td>
      <Td py={1}>
        <Text isTruncated fontSize="xs" maxWidth="87px">
          {request.id}
        </Text>
      </Td>
      <Td pr={0} py={1} textAlign="end" position="relative">
        <Button
          size="xs"
          variant="ghost"
          mr={2.5}
          onFocus={shiftFocusToHoverMenu}
          tabIndex={showMenu ? -1 : 0}
        >
          <MoreIcon color="gray.700" w={18} h={18} />
        </Button>
        <ButtonGroup
          isAttached
          variant="outline"
          position="absolute"
          right={2.5}
          top="50%"
          transform="translate(1px, -50%)"
          opacity={showMenu ? 1 : 0}
          pointerEvents={showMenu ? "auto" : "none"}
          onFocus={handleFocus}
          onBlur={handleBlur}
          shadow="base"
          borderRadius="md"
        >
          {request.status === "error" && (
            <ReprocessButton
              buttonProps={{ mr: "-px", size: "xs" }}
              handleBlur={handleBlur}
              subjectRequest={request}
            />
          )}
          {request.status === "pending" && (
            <>
              <Button
                size="xs"
                mr="-px"
                bg="white"
                onClick={() => {
                  handleApproveRequest();
                  handleBlur();
                }}
                isLoading={approveRequestResult.isLoading}
                _loading={{
                  opacity: 1,
                  div: { opacity: 0.4 },
                }}
                _hover={{
                  bg: "gray.100",
                }}
                ref={hoverButtonRef}
              >
                Approve
              </Button>
              <Button
                size="xs"
                mr="-px"
                bg="white"
                onClick={handleModalOpen}
                _loading={{
                  opacity: 1,
                  div: { opacity: 0.4 },
                }}
                _hover={{
                  bg: "gray.100",
                }}
              >
                Deny
              </Button>
              <DenyPrivacyRequestModal
                isOpen={modalOpen}
                handleMenuClose={handleModalClose}
                handleDenyRequest={handleDenyRequest}
              />
            </>
          )}
          <Menu onOpen={handleMenuOpen} onClose={handleMenuClose}>
            <MenuButton
              as={Button}
              size="xs"
              bg="white"
              ref={request.status !== "pending" ? hoverButtonRef : null}
            >
              <MoreIcon color="gray.700" w={18} h={18} />
            </MenuButton>
            <Portal>
              <MenuList shadow="xl">
                <MenuItem
                  _focus={{ color: "complimentary.500", bg: "gray.100" }}
                  onClick={handleIdCopy}
                >
                  <Text fontSize="sm">Copy Request ID</Text>
                </MenuItem>
                <MenuItem
                  _focus={{ color: "complimentary.500", bg: "gray.100" }}
                  onClick={handleViewDetails}
                >
                  <Text fontSize="sm">View Details</Text>
                </MenuItem>
              </MenuList>
            </Portal>
          </Menu>
        </ButtonGroup>
      </Td>
    </Tr>
  );
};

export default RequestRow;
