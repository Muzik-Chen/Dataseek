<template>
  <div class="search-bar" :class="{ focused: isFocused }">
    <el-icon class="search-icon" :size="18"><Search /></el-icon>
    <input
      ref="inputRef"
      :value="modelValue"
      type="text"
      :placeholder="placeholder"
      class="search-input"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
      @keydown.enter="onEnter"
      autocomplete="off"
    />
    <transition name="fade">
      <div v-if="isFocused && hotKeywords.length" class="hot-dropdown">
        <span class="hot-label">热门搜索</span>
        <div class="hot-tags">
          <button
            v-for="kw in hotKeywords"
            :key="kw"
            class="hot-tag"
            @mousedown.prevent="selectHot(kw)"
          >{{ kw }}</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '搜索…' },
  hotKeywords: { type: Array, default: () => [] },
  debounceMs: { type: Number, default: 300 },
})

const emit = defineEmits(['update:modelValue', 'search'])

const isFocused = ref(false)
const inputRef = ref(null)
let debounceTimer = null

function onInput(e) {
  const value = e.target.value
  emit('update:modelValue', value)
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('search', value)
  }, props.debounceMs)
}

function onFocus() { isFocused.value = true }
function onBlur() {
  setTimeout(() => { isFocused.value = false }, 200)
}

function onEnter(e) {
  clearTimeout(debounceTimer)
  emit('search', e.target.value)
}

function selectHot(keyword) {
  emit('update:modelValue', keyword)
  emit('search', keyword)
  isFocused.value = false
}
</script>

<style scoped>
.search-bar {
  position: relative;
  display: flex;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--el-border-color);
  border-radius: var(--radius-full);
  padding: 0 var(--space-md);
  height: 38px;
  width: 240px;
  transition: border-color 0.2s, box-shadow 0.2s, width 0.2s;
}

.search-bar.focused {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px oklch(0.52 0.16 248 / 0.12);
  width: 280px;
}

.search-icon {
  color: var(--muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: none;
  font-size: var(--fs-sm);
  color: var(--ink);
  padding: 0 var(--space-sm);
  outline: none;
  font-family: inherit;
}

.search-input::placeholder {
  color: oklch(0.65 0.005 248);
}

.hot-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--bg);
  border: 1px solid var(--el-border-color-light);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  box-shadow: var(--shadow-lg);
  z-index: var(--z-dropdown);
}

.hot-label {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-sm);
  display: block;
}

.hot-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.hot-tag {
  padding: 4px var(--space-md);
  font-size: var(--fs-sm);
  color: var(--primary);
  background: var(--primary-light);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: background 0.2s;
  font-family: inherit;
}

.hot-tag:hover {
  background: oklch(0.85 0.04 248);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to { opacity: 0; }

@media (max-width: 767px) {
  .search-bar { width: 160px; }
  .search-bar.focused { width: 200px; }
}
</style>
