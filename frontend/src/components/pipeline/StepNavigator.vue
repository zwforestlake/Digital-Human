<script setup lang="ts">
export interface WizardStep {
  key: string
  title: string
  hint: string
}

defineProps<{
  steps: readonly WizardStep[]
  activeIndex: number
}>()

const emit = defineEmits<{
  select: [index: number]
}>()
</script>

<template>
  <aside class="navigator">
    <button
      v-for="(step, index) in steps"
      :key="step.key"
      class="nav-step"
      :class="{ 'nav-step-active': index === activeIndex, 'nav-step-done': index < activeIndex }"
      type="button"
      @click="emit('select', index)"
    >
      <span class="nav-index">{{ index + 1 }}</span>
      <span class="nav-copy">
        <strong class="nav-title">{{ step.title }}</strong>
        <span class="nav-hint">{{ step.hint }}</span>
      </span>
    </button>
  </aside>
</template>

<style scoped>
.navigator {
  display: grid;
  gap: 10px;
  align-content: start;
  padding: 14px;
  border: 1px solid #d8e0e6;
  border-radius: 8px;
  background: #ffffff;
}

.nav-step {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  min-height: 62px;
  border: 1px solid #e2e8ed;
  border-radius: 8px;
  padding: 10px;
  background: #fbfcfd;
  color: #53636f;
  text-align: left;
  cursor: pointer;
}

.nav-step-active {
  border-color: #2d7da3;
  background: #eef7fa;
  color: #172026;
}

.nav-step-done {
  color: #172026;
}

.nav-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #e9eef2;
  font-weight: 700;
}

.nav-step-active .nav-index,
.nav-step-done .nav-index {
  background: #2d7da3;
  color: #ffffff;
}

.nav-copy {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.nav-title,
.nav-hint {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-title {
  font-size: 14px;
}

.nav-hint {
  font-size: 12px;
}
</style>
