import { ref, shallowRef } from "vue";

export const useQuery = <Data, Args extends unknown[]>(
  func: (...args: Args) => Promise<Data>,
  defaultValue: Data
) => {
  const status = ref<"" | "loading" | "error" | "success">("");

  const data = shallowRef<Data>(defaultValue);

  let latest: Symbol;

  async function query(...args: Args): Promise<void> {
    const current = Symbol();
    latest = current;

    const isLatest = () =>
      current === latest ? true : console.warn("Stale query");

    try {
      status.value = "loading";
      data.value = defaultValue;

      const result = await func(...args);

      if (isLatest()) {
        data.value = result;
        status.value = "success";
      }
    } catch (error) {
      if (isLatest()) {
        console.error(error);
        status.value = "error";
      }
    }
  }

  return { query, data, status };
};
