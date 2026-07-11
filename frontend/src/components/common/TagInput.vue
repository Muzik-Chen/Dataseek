<template>
  <div class="tag-input-wrap">
    <el-tag
      v-for="(tag, idx) in tags"
      :key="idx"
      closable
      :disable-transitions="false"
      class="tag-item"
      @close="removeTag(idx)"
    >
      {{ tag }}
    </el-tag>
    <el-input
      v-if="tags.length < limit"
      ref="inputRef"
      v-model="inputValue"
      :placeholder="placeholder"
      :maxlength="maxLength"
      size="small"
      class="tag-input"
      @keyup.enter.prevent="addTag"
      @blur="addTag"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  limit: { type: Number, default: 5 },
  maxLength: { type: Number, default: 10 },
  placeholder: { type: String, default: '输入标签，回车添加' },
})

const emit = defineEmits(['update:modelValue'])

const inputValue = ref('')
const inputRef = ref(null)

const tags = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val),
})

function addTag() {
  const val = inputValue.value.trim()
  if (!val) return
  if (tags.value.includes(val)) { inputValue.value = ''; return }
  if (val.length < 2) return // 最少2个字符
  if (tags.value.length >= props.limit) return
  tags.value = [...tags.value, val]
  inputValue.value = ''
}

function removeTag(idx) {
  const newTags = [...tags.value]
  newTags.splice(idx, 1)
  tags.value = newTags
}
</script>

<style scoped>
.tag-input-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  min-height: 36px;
  padding: 4px 8px;
  border: 1px solid var(--el-border-color, #dcdfe6);
  border-radius: var(--radius-md, 8px);
  background: var(--el-bg-color, #fff);
  cursor: text;
  transition: border-color 0.2s;
}
.tag-input-wrap:focus-within {
  border-color: var(--el-color-primary, #409eff);
}
.tag-item {
  margin: 0;
}
.tag-input {
  flex: 1;
  min-width: 100px;
}
.tag-input :deep(.el-input__wrapper) {
  box-shadow: none;
  padding: 0;
  background: transparent;
}
.tag-input :deep(.el-input__wrapper:hover),
.tag-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: none;
}
.tag-input :deep(.el-input__inner) {
  height: 28px;
  line-height: 28px;
}
</style>
