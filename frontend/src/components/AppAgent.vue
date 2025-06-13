<template>
  <div
    :class="[
      'flex justify-center items-center gap-3 min-w-10 min-h-10 px-3 py-1  rounded-full overflow-hidden transition-all',
      bgColor,
      textColor,
    ]"
  >
    <AppBrain class="h-6" />
    {{ name }}
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { agents } from "@/api/agents";
import AppBrain from "@/components/AppBrain.vue";

type Props = {
  agent: keyof typeof agents;
};

const { agent } = defineProps<Props>();

const name = computed(() => agents[agent].name);
const bgColor = computed(() => agents[agent].bgColor);
const textColor = computed(() => agents[agent].textColor);
</script>
