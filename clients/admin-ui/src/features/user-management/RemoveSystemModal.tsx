import {
    Box,
    Button,
    ButtonGroup,
    Modal, ModalBody, ModalCloseButton,
    ModalContent,
    ModalFooter, ModalHeader,
    ModalOverlay,
    UseDisclosureReturn,
    useToast,
} from "@fidesui/react";
import React from "react";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {System} from "~/types/api";
import {useRemoveUserManagedSystemMutation} from "./user-management.slice";

const useRemoveSystemModal = ({
                                onClose,
                            }: { onClose: () => void }) => {
    const toast = useToast();
    const [removeUserManagedSystemTrigger] = useRemoveUserManagedSystemMutation();

    const handleRemoveSystem = async (system: System, activeUserId: string) => {
        if (!activeUserId) {
            return;
        }
        const result = await removeUserManagedSystemTrigger({
            userId: activeUserId,
            systemKey: system.fides_key,
        });
        if (isErrorResult(result)) {
            toast(errorToastParams(getErrorMessage(result.error)));
        } else {
            toast(successToastParams("Successfully removed system"));
            onClose();
        }
    };

    return {
        handleRemoveSystem,
    };
};

const RemoveSystemModal = ({system,
                            activeUserId,
                             ...modal
                         }: { system: System, activeUserId: string } & UseDisclosureReturn) => {
    const { isOpen, onClose } = modal;
    const { handleRemoveSystem } = useRemoveSystemModal({
        onClose,
    });

    return (
        <Modal isCentered isOpen={isOpen} onClose={onClose}>
            <ModalOverlay />
            <ModalContent data-testid="delete-user-modal">
                <ModalHeader>Remove System</ModalHeader>
                <ModalCloseButton />
                <ModalBody>
                    <Box>
                        Are you sure you want to remove this system?
                    </Box>
                </ModalBody>
                <ModalFooter>
                    <ButtonGroup size="sm" spacing="2" width="100%">
                        <Button onClick={onClose} variant="outline" width="50%">
                            Cancel
                        </Button>
                        <Button
                            colorScheme="primary"
                            onClick={() => handleRemoveSystem(system, activeUserId)}
                            type="submit"
                            width="50%"
                            data-testid="submit-btn"
                        >
                            Yes, Remove System
                        </Button>
                    </ButtonGroup>
                </ModalFooter>
            </ModalContent>
        </Modal>
    );
};

export default RemoveSystemModal;
