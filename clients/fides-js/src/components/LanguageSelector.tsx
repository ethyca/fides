import { h } from "preact";
import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "preact/hooks";

import { FidesInitOptions } from "../lib/consent-types";
import {
  DEFAULT_LOCALE,
  loadMessagesFromGVLTranslations,
  Locale,
} from "../lib/i18n";
import { useI18n } from "../lib/i18n/i18n-context";
import { GVLContext } from "../lib/tcf/gvl-context";
import { fetchGvlTranslations } from "../services/api";
import MenuItem from "./MenuItem";

interface LanguageSelectorProps {
  availableLocales: Locale[];
  options: FidesInitOptions;
  isTCF?: boolean;
}

const LanguageSelector = ({
  availableLocales,
  options,
  isTCF,
}: LanguageSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const { i18n, currentLocale, setCurrentLocale, setIsLoading } = useI18n();
  const contextGvl = useContext(GVLContext);

  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  const handleToggle = () => {
    setIsOpen(!isOpen);
  };

  const handleLocaleSelect = async (locale: string) => {
    if (locale !== i18n.locale) {
      if (isTCF) {
        setIsLoading(true);
        const gvlTranslations = await fetchGvlTranslations(
          options.fidesApiUrl,
          [locale],
        );
        setIsLoading(false);
        if (gvlTranslations && Object.keys(gvlTranslations).length) {
          contextGvl.setGvlTranslations(gvlTranslations[locale]);
          loadMessagesFromGVLTranslations(
            i18n,
            gvlTranslations,
            availableLocales || [DEFAULT_LOCALE],
          );
          setCurrentLocale(locale);
          fidesDebugger(`Fides locale updated to ${locale}`);
        } else {
          // eslint-disable-next-line no-console
          console.error(`Unable to load GVL translation for ${locale}`);
        }
      } else {
        setCurrentLocale(locale);
        fidesDebugger(`Fides locale updated to ${locale}`);
      }
    }
    setIsOpen(false);
  };

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isOpen) {
        return;
      }

      const menuItems =
        menuRef.current?.querySelectorAll<HTMLButtonElement>(
          ".fides-menu-item",
        ) || [];
      const { key } = event;

      if (key === "Escape" || key === "Tab") {
        setIsOpen(false);
        return;
      }

      if (key === "ArrowUp" || key === "ArrowDown") {
        event.preventDefault();
        const focusedIndex = Array.from(menuItems).findIndex(
          (item) => item === document.activeElement,
        );

        let newIndex = focusedIndex;
        if (key === "ArrowDown") {
          newIndex =
            focusedIndex === menuItems.length - 1 ? 0 : focusedIndex + 1;
        } else if (key === "ArrowUp") {
          newIndex =
            focusedIndex === 0 ? menuItems.length - 1 : focusedIndex - 1;
        }

        menuItems[newIndex]?.focus();
      }
    },
    [isOpen],
  );

  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  useEffect(() => {
    if (isOpen) {
      const menuItems =
        menuRef.current?.querySelectorAll<HTMLButtonElement>(
          ".fides-menu-item",
        );
      menuItems?.[0]?.focus();
    } else {
      buttonRef.current?.focus();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        isOpen &&
        menuRef.current &&
        !menuRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div
      className={`fides-i18n-menu ${isOpen ? "fides-i18n-menu-open" : ""}`}
      ref={menuRef}
    >
      <div role="group" className="fides-i18n-popover" id="fides-i18n-popover">
        {i18n.availableLanguages.map((lang) => (
          <MenuItem
            key={lang.locale}
            data-testid={`fides-i18n-option-${lang.locale}`}
            id={
              currentLocale === lang.locale ? "fidesActiveMenuItem" : undefined
            }
            onClick={() => handleLocaleSelect(lang.locale)}
            isActive={currentLocale === lang.locale}
            title={lang.label_en}
            aria-label={lang.label_en}
            tabIndex={-1}
          >
            {lang.label_original}
          </MenuItem>
        ))}
      </div>
      <button
        type="button"
        className="fides-i18n-button"
        onClick={handleToggle}
        ref={buttonRef}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-controls="fides-i18n-popover"
        aria-label={`Select language, current language is ${currentLocale}`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          height="100%"
          viewBox="0 0 36 36"
          fill="currentColor"
          id="fides-i18n-icon"
        >
          <path
            fill="currentColor"
            d="M18 32.625c.52 0 1.898-.506 3.347-3.403.619-1.245 1.153-2.756 1.547-4.472h-9.788c.394 1.716.928 3.227 1.547 4.472 1.449 2.897 2.827 3.403 3.347 3.403m-5.45-11.25h10.9a32.5 32.5 0 0 0 0-6.75h-10.9a32.5 32.5 0 0 0 0 6.75m.556-10.125h9.788c-.394-1.716-.928-3.227-1.547-4.472C19.898 3.881 18.52 3.375 18 3.375s-1.898.506-3.347 3.403c-.619 1.245-1.153 2.756-1.547 4.472m13.732 3.375A35 35 0 0 1 26.993 18c0 1.153-.056 2.285-.155 3.375h5.393c.253-1.083.394-2.215.394-3.375s-.134-2.292-.394-3.375h-5.393m4.135-3.375a14.7 14.7 0 0 0-6.92-6.567c.992 1.8 1.78 4.043 2.293 6.567h4.634zm-21.326 0c.513-2.524 1.3-4.76 2.292-6.567A14.7 14.7 0 0 0 5.02 11.25h4.634zm-5.878 3.375A14.8 14.8 0 0 0 3.375 18c0 1.16.134 2.292.394 3.375h5.393A35 35 0 0 1 9.007 18c0-1.153.056-2.285.155-3.375zm20.285 16.692a14.7 14.7 0 0 0 6.919-6.567h-4.627c-.513 2.524-1.3 4.76-2.292 6.567m-12.108 0c-.991-1.8-1.779-4.043-2.292-6.567H5.02a14.7 14.7 0 0 0 6.92 6.567zM18 36a18 18 0 1 1 0-36 18 18 0 0 1 0 36"
          />
        </svg>
        {currentLocale}
        <svg
          className="fides-i18n-caret"
          xmlns="http://www.w3.org/2000/svg"
          height="100%"
          fill="currentColor"
          viewBox="0 0 24 24"
        >
          <path d="M12 13.172L16.95 8.22198L18.364 9.63598L12 16L5.63599 9.63598L7.04999 8.22198L12 13.172Z" />
        </svg>
      </button>
    </div>
  );
};

export default LanguageSelector;
