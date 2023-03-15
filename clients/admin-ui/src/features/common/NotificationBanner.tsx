import {
  useDisclosure,
  Alert,
  AlertIcon,
  Box,
  AlertDescription,
  CloseButton,
} from "@fidesui/react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import {
  selectShowNotificationBanner,
  setShowNotificationBanner,
} from "./features";

const DESCRIPTION =
  "Ethyca has updated how permissions work from a scope-based model to a role-based permissions scheme. To update user roles, please log in as your root user and upgrade the roles as you see fit.";

const NotificationBanner = () => {
  const showBanner = useAppSelector(selectShowNotificationBanner);
  const dispatch = useAppDispatch();

  // if the user hasn't logged out, it's possible `showBanner` can be undefined
  // since the redux store hasn't reinitialized. in this case, we _do_ want to show the banner
  const defaultIsOpen = showBanner === undefined ? true : showBanner;

  const { isOpen: isVisible, onClose } = useDisclosure({
    defaultIsOpen,
  });

  const handleClose = () => {
    dispatch(setShowNotificationBanner(false));
    onClose();
  };

  if (!isVisible) {
    return null;
  }

  return (
    <Alert status="info" overflow="visible">
      <AlertIcon />
      <Box>
        <AlertDescription>{DESCRIPTION}</AlertDescription>
      </Box>
      <CloseButton
        alignSelf="flex-start"
        position="relative"
        right={-1}
        top={-1}
        onClick={handleClose}
      />
    </Alert>
  );
};

export default NotificationBanner;
