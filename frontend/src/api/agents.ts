import { useQuery } from "@/util/composables";
import { ref, watchEffect } from "vue";

export const agents = ref({
  gemini: {
    name: "Gemini",
    abbrev: "Gem",
    color: "bg-indigo-500",
    running: false,
  },

  chatgpt: {
    name: "ChatGPT",
    abbrev: "GPT",
    color: "bg-emerald-500",
    running: false,
  },

  claude: {
    name: "Claude",
    abbrev: "Cla",
    color: "bg-orange-500",
    running: false,
  },
});

export const useAgentAction = <Data, Args extends unknown[]>(
  key: keyof typeof agents.value,
  func: () => Promise<Data>
) => {
  const { query, data, status } = useQuery(func, undefined);
  watchEffect(() => {
    agents.value[key].running = status.value === "loading";
  });
  return async () => {
    await query();
    return data.value;
  };
};
