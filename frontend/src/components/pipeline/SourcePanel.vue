<script setup lang="ts">
const name = defineModel<string>('name', { required: true })
const douyinUrl = defineModel<string>('douyinUrl', { required: true })

defineProps<{
  isBusy: boolean
  projectCreated: boolean
}>()

const emit = defineEmits<{
  create: []
  upload: [file: File]
}>()

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    emit('upload', file)
  }
}
</script>

<template>
  <section class="panel">
    <h2 class="panel-title">视频来源</h2>

    <label class="field">
      <span class="field-label">项目名称</span>
      <input v-model="name" class="input" type="text" />
    </label>

    <label class="field">
      <span class="field-label">抖音视频网址</span>
      <input v-model="douyinUrl" class="input" type="url" placeholder="https://v.douyin.com/..." />
    </label>

    <button class="secondary-button" :disabled="isBusy" @click="emit('create')">
      {{ projectCreated ? '更新项目' : '创建项目' }}
    </button>

    <label class="upload">
      <span>上传本地视频</span>
      <input class="file-input" type="file" accept="video/*" :disabled="!projectCreated" @change="handleFileChange" />
    </label>
  </section>
</template>

<style scoped>
.panel {
  padding: 18px;
  border: 1px solid #d7dee3;
  border-radius: 8px;
  background: #ffffff;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 18px;
}

.field {
  display: grid;
  gap: 7px;
  margin-bottom: 14px;
}

.field-label {
  color: #53636f;
  font-size: 13px;
}

.input {
  width: 100%;
  min-width: 0;
  height: 38px;
  box-sizing: border-box;
  border: 1px solid #c9d3da;
  border-radius: 8px;
  padding: 0 11px;
  color: #172026;
}

.secondary-button,
.upload {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 38px;
  box-sizing: border-box;
  border-radius: 8px;
  font-weight: 700;
}

.secondary-button {
  border: 1px solid #0b6bcb;
  background: #ffffff;
  color: #0b6bcb;
  cursor: pointer;
}

.secondary-button:disabled {
  border-color: #9fb2c2;
  color: #718390;
  cursor: not-allowed;
}

.upload {
  margin-top: 12px;
  border: 1px dashed #8ea1ae;
  color: #364a57;
  cursor: pointer;
}

.file-input {
  display: none;
}
</style>
