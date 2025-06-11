import { range, sample, startCase } from "lodash";

export const words =
  "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum".split(
    " "
  );

export const phrases = () =>
  range(1, 10 + 1).map((index) =>
    Array(index)
      .fill(null)
      .map(() => sample(words))
      .join(" ")
  );

export const label = () => {
  let label = sample([...phrases(), undefined]);
  if (label) label = startCase(label);
  return label;
};
