import { random } from "lodash";
import { sleep } from "@/util/misc";

export const api = import.meta.env.VITE_API;

export const request = async <Response>(
  url: string | URL,
  options: RequestInit = {}
) => {
  url = new URL(url);
  const request = new Request(url, options);
  await sleep(random(1000, 3000));
  return { output: `${url.pathname} response` } as Response;

  const response = await fetch(request);
  let error = "";
  if (!response.ok) error = "Response not OK";
  let parsed: Response;
  try {
    parsed = await response.clone().json();
  } catch (e) {
    error = "Couldn't parse response";
  }
  if (error || parsed === undefined) throw Error(error);
  return parsed;
};
