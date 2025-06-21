<template>
  <button
    :class="activeClasses"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">

import { defineProps, computed } from 'vue';

type PropTypes = {
  isActive?: boolean
};

const activeClasses = computed(() => {
  return {
    'flex': true,
    'justify-center': true,
    'items-center': true,
    'min-w-10': true,
    'min-h-10': true,
    'bg-indigo-500': !props.isActive,
    'bg-indigo-900': props.isActive,
    'text-white': true,
    'rounded-full': true,
    'hover:bg-indigo-400': true,
    'transition-all': true,
  }
});

const props = defineProps<PropTypes>();
</script>

<style scoped>
button :deep(.lucide) {
  height: 1.25em;
}
</style>
