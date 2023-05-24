import Image from "next/image";
import Button from "../Button";
import css from "./style.module.scss";

const Header = () => (
  <header className={css.header}>
    <Image src="/logo.svg" width={204} height={68} alt="Logo" />
    <div className={css.location}>
      <img src="https://hatscripts.github.io/circle-flags/flags/br.svg" width="32" />
      <select
        id="location-select"
      >
        <option value="">Location</option>
        <option value="US-CA">California</option>
        <option value="US-VA">Virginia</option>
        <option value="US-NY">New York</option>
        <option value="US">USA</option>
        <option value="FR">France</option>
        <option value="FR-IDF">Paris</option>
      </select>
    </div>
  </header>
);

export default Header;
