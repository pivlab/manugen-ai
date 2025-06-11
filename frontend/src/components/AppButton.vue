<template>
  <button
    class="flex justify-center items-center min-w-10 min-h-10 bg-indigo-500 text-white rounded-full hover:bg-indigo-400 transition-all"
  >
    <slot />
  </button>
</template>

<style scoped>
button :deep(.lucide) {
  height: 1.25em;
}
</style>
