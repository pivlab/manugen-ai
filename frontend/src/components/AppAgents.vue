<template>
  <template v-for="(agents, id) in agentsWorking" :key="id">
    <Teleport :to="`#${id}`">
      <div class="flex flex-wrap gap-2">
        <AppAgent
          v-for="(agent, index) in agents"
          :key="index"
          :agent="agent"
        />
      </div>
    </Teleport>
  </template>
</template>

<script lang="ts">
import { ref } from "vue";
import type { AgentId } from "@/api/agents";

/** singleton component to render certain agent badges in certain dom nodes by id */

/** map of dom node ids to agent ids show badges for */
export const agentsWorking = ref<Record<string, AgentId[]>>({});
</script>

<script setup lang="ts">
import AppAgent from "@/components/AppAgent.vue";
</script>
