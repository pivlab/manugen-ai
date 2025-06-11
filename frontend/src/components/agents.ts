import { sample } from "lodash";
import { ref } from "vue";

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

window.setInterval(() => {
  agents.value[
    sample(Object.keys(agents.value)) as keyof typeof agents.value
  ].running = Math.random() > 0.5;
}, 500);
