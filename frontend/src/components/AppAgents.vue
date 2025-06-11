<template>
  <div class="flex flex-col items-start p-5 gap-2">
    <div
      v-for="({ name, abbrev, color, running }, index) in agents"
      :class="[
        'flex justify-center items-center gap-3 min-w-10 min-h-10 text-white rounded-full transition-all',
        color,
        running ? 'px-3 py-1' : 'opacity-50',
      ]"
      :key="index"
    >
      <template v-if="running">
        <AppBrain class="h-6"/>
        {{ name }}
      </template>
      <template v-else>
        {{ abbrev }}
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { agents } from "./agents";
import AppBrain from "./AppBrain.vue";
</script>
