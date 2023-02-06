import {
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  InputProps,
  InputRightElement,
  SearchLineIcon,
} from "@fidesui/react";

interface Props extends Omit<InputProps, "onChange"> {
  search?: string;
  onChange: (value: string) => void;
  withIcon?: boolean;
  withClear?: boolean;
}
const SearchBar = ({
  search,
  onChange,
  withIcon,
  withClear,
  ...props
}: Props) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  return (
    <InputGroup size="sm" minWidth="308px">
      {withIcon ? (
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
      ) : null}
      <Input
        autoComplete="off"
        type="search"
        minWidth={200}
        size="sm"
        borderRadius="md"
        value={search}
        name="search"
        onChange={handleSearchChange}
        {...props}
      />
      {withClear ? (
        <InputRightElement width="3.5rem">
          <Button
            fontWeight="light"
            size="sm"
            onClick={() => {
              onChange("");
            }}
          >
            Clear
          </Button>
        </InputRightElement>
      ) : null}
    </InputGroup>
  );
};

export default SearchBar;
