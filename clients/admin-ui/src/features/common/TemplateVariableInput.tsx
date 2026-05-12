import { Flex, Input, Typography } from "fidesui";
import { KeyboardEvent, useRef, useState } from "react";

import styles from "./TemplateVariableInput.module.css";

export interface TemplateVariable {
  name: string;
  description: string;
  example_value?: string;
}

type SharedProps = {
  variables: TemplateVariable[];
  onChange?: (value: string) => void;
  value?: string;
};

type TemplateVariableInputProps = SharedProps &
  (
    | ({ multiline?: true } & Omit<
        React.ComponentPropsWithoutRef<typeof Input.TextArea>,
        "onChange" | "value"
      >)
    | ({ multiline: false } & Omit<
        React.ComponentPropsWithoutRef<typeof Input>,
        "onChange" | "value"
      >)
  );

// Strip our custom/discriminant props before forwarding to the underlying element.
// These are not valid antd/DOM props and must not be spread onto Input or TextArea.
const CUSTOM_PROP_KEYS = [
  "variables",
  "onChange",
  "value",
  "multiline",
] as const;
type CustomPropKey = (typeof CUSTOM_PROP_KEYS)[number];

function omitCustomProps<T extends object>(obj: T): Omit<T, CustomPropKey> {
  const copy = { ...obj };
  CUSTOM_PROP_KEYS.forEach((key) => {
    delete (copy as Record<string, unknown>)[key];
  });
  return copy as Omit<T, CustomPropKey>;
}

const TemplateVariableInput = (allProps: TemplateVariableInputProps) => {
  const { multiline } = allProps;
  const { value = "", onChange, variables, placeholder } = allProps;
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cursorRef = useRef<number>(0);

  // Index of the `__` that triggered the dropdown, or null if not open
  const [triggerIndex, setTriggerIndex] = useState<number | null>(null);
  const [filterText, setFilterText] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);

  const listboxRef = useRef<HTMLDivElement>(null);

  const scrollOptionIntoView = (index: number) => {
    const options = listboxRef.current?.querySelectorAll("[role='option']");
    (options?.[index] as HTMLElement | undefined)?.scrollIntoView({
      block: "nearest",
    });
  };

  const getInputEl = (): HTMLInputElement | HTMLTextAreaElement | null =>
    wrapperRef.current?.querySelector(
      multiline === false ? "input" : "textarea",
    ) ?? null;

  const filteredVars =
    triggerIndex !== null
      ? variables.filter((v) =>
          v.name.toLowerCase().startsWith(filterText.toLowerCase()),
        )
      : [];

  const closeDropdown = () => setTriggerIndex(null);

  const selectVariable = (varName: string) => {
    const cursor = cursorRef.current;
    if (triggerIndex === null) {
      return;
    }

    const before = value.slice(0, triggerIndex);
    const after = value.slice(cursor);
    const insertion = `__${varName.toUpperCase()}__`;
    const newValue = `${before}${insertion}${after}`;
    const newCursor = triggerIndex + insertion.length;

    onChange?.(newValue);
    closeDropdown();

    setTimeout(() => {
      const el = getInputEl();
      if (el) {
        el.focus();
        el.setSelectionRange(newCursor, newCursor);
      }
    }, 0);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    const text = e.target.value;
    const cursor = e.target.selectionStart ?? text.length;
    cursorRef.current = cursor;

    const beforeCursor = text.slice(0, cursor);

    // Find the most recent trigger (`/` or `__`) before the cursor and check
    // whether the text typed after it is still a valid partial variable name.
    // Only match `/` when it immediately precedes the current word (no
    // intervening alphanumeric text), to avoid false positives on prose like
    // "access/erasure" where the cursor happens to be in "erasure".
    const slashPos = /\/([A-Za-z_]*)$/.exec(beforeCursor);
    const doubleUnderscorePos = /__([A-Za-z_]*)$/.exec(beforeCursor);

    const candidates: { pos: number; len: number }[] = [
      ...(slashPos ? [{ pos: slashPos.index, len: 1 }] : []),
      ...(doubleUnderscorePos
        ? [{ pos: doubleUnderscorePos.index, len: 2 }]
        : []),
    ];

    const match = candidates
      .sort((a, b) => b.pos - a.pos)
      .find(({ pos, len }) => {
        const afterTrigger = beforeCursor.slice(pos + len);
        return /^[A-Za-z_]*$/.test(afterTrigger);
      });

    if (match) {
      const afterTrigger = beforeCursor.slice(match.pos + match.len);
      setTriggerIndex(match.pos);
      setFilterText(afterTrigger.toUpperCase());
      setActiveIndex(0);
      onChange?.(text);
      return;
    }

    closeDropdown();
    onChange?.(text);
  };

  const handleKeyDown = (
    e: KeyboardEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    if (triggerIndex === null || filteredVars.length === 0) {
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = Math.min(activeIndex + 1, filteredVars.length - 1);
      setActiveIndex(next);
      scrollOptionIntoView(next);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = Math.max(activeIndex - 1, 0);
      setActiveIndex(prev);
      scrollOptionIntoView(prev);
    } else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      if (filteredVars[activeIndex]) {
        selectVariable(filteredVars[activeIndex].name);
      }
    } else if (e.key === "Escape") {
      closeDropdown();
    }
  };

  const handleKeyUp = (
    e: React.KeyboardEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    cursorRef.current =
      (e.target as HTMLInputElement | HTMLTextAreaElement).selectionStart ??
      cursorRef.current;
  };

  const handleClick = (
    e: React.MouseEvent<HTMLTextAreaElement | HTMLInputElement>,
  ) => {
    cursorRef.current =
      (e.target as HTMLInputElement | HTMLTextAreaElement).selectionStart ??
      cursorRef.current;
  };

  const eventProps = {
    value,
    onChange: handleChange,
    onKeyDown: handleKeyDown,
    onKeyUp: handleKeyUp,
    onClick: handleClick,
    onBlur: closeDropdown,
    placeholder,
  };

  const dropdown = triggerIndex !== null && filteredVars.length > 0 && (
    <Flex ref={listboxRef} vertical role="listbox" className={styles.dropdown}>
      {filteredVars.map((v, i) => (
        <Flex
          key={v.name}
          vertical
          role="option"
          aria-selected={i === activeIndex}
          tabIndex={-1}
          // preventDefault keeps the input focused so blur doesn't fire
          onMouseDown={(e) => {
            e.preventDefault();
            selectVariable(v.name);
          }}
          onMouseEnter={() => setActiveIndex(i)}
          className={`${styles.option}${i === activeIndex ? ` ${styles.optionActive}` : ""}`}
        >
          <Typography.Text code className="whitespace-nowrap">
            {`__${v.name.toUpperCase()}__`}
          </Typography.Text>
          {v.description && (
            <Typography.Text type="secondary" className="text-xs">
              {v.description}
            </Typography.Text>
          )}
        </Flex>
      ))}
    </Flex>
  );

  if (multiline === false) {
    return (
      <div ref={wrapperRef} className="relative">
        <Input {...omitCustomProps(allProps)} {...eventProps} />
        {dropdown}
      </div>
    );
  }

  const { rows = 4, ...textAreaProps } = omitCustomProps(allProps);
  return (
    <div ref={wrapperRef} className="relative">
      <Input.TextArea {...textAreaProps} {...eventProps} rows={rows} />
      {dropdown}
    </div>
  );
};

export default TemplateVariableInput;
