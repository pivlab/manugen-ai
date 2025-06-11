import { random } from "lodash";
import { sleep } from "@/util/misc";
import { label } from "@/api/fake";

export const api = import.meta.env.VITE_API;

export async function request<Response>(
  url: string | URL,
  options: RequestInit = {}
) {
  await sleep(random(1000, 3000));
  return { output: label() };

  url = new URL(url);
  const request = new Request(url, options);
  const response = await fetch(request);
  let error = "";
  if (!response.ok) error = "Response not OK";
  let parsed: Response | undefined;
  try {
    parsed = await response.clone().json();
  } catch (e) {
    error = "Couldn't parse response";
  }
  if (error || parsed === undefined) throw Error(error);
  return parsed;
}
