import { Input } from "fidesui";
import React from "react";

import styles from "../SidePanel.module.scss";

interface SearchProps {
  placeholder?: string;
  onSearch: (value: string) => void;
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
  value?: string;
  loading?: boolean;
}

const Search: React.FC<SearchProps> & { slotOrder: number } = ({
  placeholder = "Search...",
  onSearch,
  onChange,
  value,
  loading,
}) => (
  <div className={styles.search}>
    <Input.Search
      placeholder={placeholder}
      onSearch={onSearch}
      onChange={onChange}
      value={value}
      loading={loading}
      allowClear
    />
  </div>
);
Search.slotOrder = 2;

export default Search;
