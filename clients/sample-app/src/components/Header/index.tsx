import Image from "next/image";
import LocationSelect from "../LocationSelect";
import css from "./style.module.scss";

const Header = () => {
  return (
    <header className={css.header}>
      <Image src="/logo.svg" width={204} height={68} alt="Logo" />
      <LocationSelect />
    </header>
  );
};

export default Header;
