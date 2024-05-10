export const blockPageScrolling = () => {
  document.body.classList.add("fides-no-scroll");
};
export const unblockPageScrolling = () => {
  document.body.classList.remove("fides-no-scroll");
};
