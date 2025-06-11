<template>
  <svg viewBox="-1 -1 2 2" class="overflow-visible">
    <g transform="scale(1.25)">
      <line
        v-for="([a, b], index) in links"
        :key="index"
        stroke="currentColor"
        :stroke-width="size / 3"
        :x1="a.x"
        :y1="a.y"
        :x2="b.x"
        :y2="b.y"
        path-length="1"
        class="animate"
        :style="{
          animationDuration: duration + 's',
          animationDelay: linkDelay + a.d * stagger + 's',
        }"
      />
      <circle
        v-for="({ x, y, d }, index) in points"
        :key="index"
        fill="currentColor"
        :r="size"
        :cx="x"
        :cy="y"
        class="animate"
        :style="{
          animationDuration: duration + 's',
          animationDelay: d * stagger + 's',
        }"
      />
    </g>
  </svg>
</template>

<script setup lang="ts">
import { nextTick, ref } from "vue";
import { useIntervalFn } from "@vueuse/core";
import { range } from "lodash";
import PoissonDiskSampling from "poisson-disk-sampling";

const size = 0.1;
const spacing = 4;
const minDistance = size * spacing;
const maxDistance = size * (spacing + 1);
const linkDistance = size * (spacing + 2);
const duration = 1;
const stagger = 1;
const linkDelay = 0.25;

const dist = (ax: number, ay: number, bx = 0, by = 0) =>
  Math.sqrt((bx - ax) ** 2 + (by - ay) ** 2);

type Point = { x: number; y: number; d: number };

const points = ref<Point[]>([]);
const links = ref<[Point, Point][]>([]);

const generate = async () => {
  points.value = [];
  links.value = [];

  await nextTick();

  points.value = new PoissonDiskSampling({
    shape: [2, 2],
    minDistance,
    maxDistance,
    tries: 10,
  })
    .fill()
    .map(([x, y]) => ({ x: x - 1, y: y - 1, d: dist(x - 1, y - 1) }))
    .filter(({ d }) => d <= 1)
    .sort((a, b) => a.d - b.d);

  const indices = range(points.value.length);
  for (const ai of indices)
    for (const bi of indices)
      if (bi > ai) {
        const a = points.value[ai];
        const b = points.value[bi];
        if (dist(a.x, a.y, b.x, b.y) < linkDistance) links.value.push([a, b]);
      }
};

generate();
useIntervalFn(generate, (duration + stagger) * 1000);
</script>

<style scoped>
circle.animate {
  animation: pulse both linear;
  transform-box: fill-box;
  transform-origin: center;
}

@keyframes pulse {
  0% {
    scale: 0;
  }

  50% {
    scale: 1;
  }

  100% {
    scale: 0;
  }
}

line.animate {
  animation: draw both linear;
  stroke-dasharray: 1 1;
}

@keyframes draw {
  from {
    stroke-dashoffset: 3;
  }

  to {
    stroke-dashoffset: 1;
  }
}
</style>
