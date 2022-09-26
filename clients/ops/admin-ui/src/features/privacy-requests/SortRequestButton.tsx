import { Flex, IconButton } from "@fidesui/react";
import { SortArrowIcon } from "common/Icon";
import React, { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  clearSortFields,
  selectPrivacyRequestFilters,
  setSortDirection,
  setSortField,
} from "./privacy-requests.slice";

type UseSortRequestButtonParams = {
  sortField: string;
  isLoading: boolean;
};

export enum ButtonState {
  ASC = "asc",
  DESC = "desc",
  UNSELECTED = "unselected",
}

const useSortRequestButton = ({
  sortField,
  isLoading,
}: UseSortRequestButtonParams) => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const dispatch = useDispatch();
  const [buttonState, setButtonState] = useState<ButtonState>(
    ButtonState.UNSELECTED
  );
  const [wasButtonJustClicked, setWasButtonJustClicked] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      setWasButtonJustClicked(false);
    }
  }, [isLoading]);

  useEffect(() => {
    if (filters.sort_direction === undefined) {
      setButtonState(ButtonState.UNSELECTED);
    }
  }, [filters]);

  const handleButtonClick = useCallback(() => {
    setWasButtonJustClicked(true);
    dispatch(setSortField(sortField));

    switch (buttonState) {
      case ButtonState.UNSELECTED:
        dispatch(setSortDirection(ButtonState.ASC));
        setButtonState(ButtonState.ASC);
        break;
      case ButtonState.ASC:
        dispatch(setSortDirection(ButtonState.DESC));
        setButtonState(ButtonState.DESC);
        break;
      case ButtonState.DESC:
        dispatch(clearSortFields());
        setButtonState(ButtonState.UNSELECTED);
        break;
      default:
        break;
    }
  }, [buttonState, setButtonState, dispatch, sortField]);

  return {
    handleButtonClick,
    buttonState,
    wasButtonJustClicked,
  };
};

type SortRequestButtonProps = {
  sortField: string;
  isLoading: boolean;
};

const SortRequestButton: React.FC<SortRequestButtonProps> = ({
  sortField,
  isLoading,
}) => {
  const { buttonState, handleButtonClick, wasButtonJustClicked } =
    useSortRequestButton({ sortField, isLoading });

  let icon = null;

  switch (buttonState) {
    case ButtonState.ASC:
      icon = <SortArrowIcon up />;
      break;
    case ButtonState.DESC:
      icon = <SortArrowIcon up={false} />;
      break;
    case ButtonState.UNSELECTED:
      icon = <SortArrowIcon />;
      break;
    default:
      icon = <SortArrowIcon />;
  }

  return (
    <Flex paddingLeft="3px">
      <IconButton
        variant="ghost"
        aria-label="Sort requests"
        icon={icon}
        isLoading={isLoading && wasButtonJustClicked}
        onClick={handleButtonClick}
      />
    </Flex>
  );
};

export default SortRequestButton;
