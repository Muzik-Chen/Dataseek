<template>
  <div class="image-uploader">
    <div class="image-uploader__list">
      <div
        v-for="(url, idx) in modelValue"
        :key="idx"
        class="image-uploader__item"
        draggable="true"
        @dragstart="onDragStart(idx)"
        @dragover.prevent
        @drop="onDrop(idx)"
      >
        <el-image :src="url" fit="cover" class="image-uploader__thumb" />
        <div class="image-uploader__overlay">
          <el-button
            text
            circle
            size="small"
            type="danger"
            :icon="Delete"
            @click.stop="removeImage(idx)"
          />
        </div>
        <div v-if="uploading[idx]" class="image-uploader__progress">
          <el-progress :percentage="progress[idx]" :stroke-width="4" />
        </div>
      </div>

      <div
        v-if="modelValue.length < limit"
        class="image-uploader__add"
        @click="triggerUpload"
      >
        <el-icon :size="32"><Plus /></el-icon>
        <span>{{ modelValue.length }}/{{ limit }}</span>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      :accept="accept"
      multiple
      hidden
      @change="handleFiles"
    />

    <p class="image-uploader__hint">支持 {{ acceptLabels }}，单张不超过 {{ maxSizeMB }}MB</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { toast } from '@/utils/toast'
import { validateFileSize, validateImageType } from '@/utils/validators'
<<<<<<< HEAD
import api from '@/api/request'
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  limit: { type: Number, default: 9 },
  maxSizeMB: { type: Number, default: 5 },
  accept: { type: String, default: 'image/jpeg,image/png,image/gif,image/webp' },
})

const emit = defineEmits(['update:modelValue'])

const acceptLabels = 'JPG/PNG/GIF/WebP'
const fileInput = ref(null)
const uploading = ref({})
const progress = ref({})

function triggerUpload() {
  fileInput.value?.click()
}

async function handleFiles(e) {
  const files = Array.from(e.target.files)
  e.target.value = ''

  const remaining = props.limit - props.modelValue.length
  if (files.length > remaining) {
    toast.warning(`最多还能上传 ${remaining} 张`)
    return
  }

  for (const file of files) {
    if (!validateImageType(file)) {
      toast.warning(`"${file.name}" 格式不支持，请上传 JPG/PNG/GIF/WebP`)
      continue
    }
    if (!validateFileSize(file, props.maxSizeMB)) {
      toast.warning(`"${file.name}" 超过 ${props.maxSizeMB}MB 限制`)
      continue
    }

<<<<<<< HEAD
    // 先插入占位 URL 用于显示上传进度
    const placeholderIdx = props.modelValue.length
    const newUrls = [...props.modelValue, '']
    emit('update:modelValue', newUrls)

    try {
      uploading.value[placeholderIdx] = true
      progress.value[placeholderIdx] = 0

      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (event) => {
          if (event.total) {
            progress.value[placeholderIdx] = Math.round((event.loaded / event.total) * 100)
          }
        },
      })

      // 替换占位 URL 为真实 URL
      const uploadedUrls = [...props.modelValue]
      uploadedUrls[placeholderIdx] = response.url
      emit('update:modelValue', uploadedUrls)
    } catch (e) {
      // 上传失败，移除占位
      const cleanedUrls = props.modelValue.filter((_, i) => i !== placeholderIdx)
      emit('update:modelValue', cleanedUrls)
      toast.error(e.message || '上传失败')
    } finally {
      delete uploading.value[placeholderIdx]
      delete progress.value[placeholderIdx]
    }
=======
    // 本地预览（实际项目中应上传到服务器获取 URL）
    const localUrl = URL.createObjectURL(file)
    const newUrls = [...props.modelValue, localUrl]
    emit('update:modelValue', newUrls)
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
  }
}

function removeImage(idx) {
  const newUrls = props.modelValue.filter((_, i) => i !== idx)
  emit('update:modelValue', newUrls)
}

let dragIdx = null
function onDragStart(idx) {
  dragIdx = idx
}

function onDrop(idx) {
  if (dragIdx === null || dragIdx === idx) return
  const newUrls = [...props.modelValue]
  const [moved] = newUrls.splice(dragIdx, 1)
  newUrls.splice(idx, 0, moved)
  emit('update:modelValue', newUrls)
  dragIdx = null
}
</script>

<style scoped>
.image-uploader__list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.image-uploader__item {
  width: 120px;
  height: 120px;
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
  cursor: grab;
}

.image-uploader__thumb {
  width: 100%;
  height: 100%;
}

.image-uploader__overlay {
  position: absolute;
  top: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-uploader__item:hover .image-uploader__overlay {
  opacity: 1;
}

.image-uploader__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 4px;
  background: rgba(0, 0, 0, 0.5);
}

.image-uploader__add {
  width: 120px;
  height: 120px;
  border: 2px dashed var(--color-border, #ddd);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--muted);
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.image-uploader__add:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.image-uploader__hint {
  font-size: 12px;
  color: var(--muted);
  margin-top: 8px;
}
</style>
