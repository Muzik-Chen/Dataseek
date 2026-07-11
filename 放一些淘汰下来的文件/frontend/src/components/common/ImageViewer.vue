<template>
  <Teleport to="body">
    <Transition name="viewer-fade">
      <div v-if="visible" class="image-viewer-overlay" @click.self="close">
        <div class="image-viewer-toolbar">
          <span class="viewer-counter">{{ current + 1 }} / {{ images.length }}</span>
          <button class="viewer-close" @click="close" aria-label="关闭">
            <el-icon><Close /></el-icon>
          </button>
        </div>
        <button class="viewer-nav viewer-prev" v-if="images.length > 1" @click.stop="prev" aria-label="上一张">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <div class="image-viewer-body">
          <img
            :src="images[current]"
            :alt="`图片 ${current + 1}`"
            class="viewer-image"
            @click.stop
          />
        </div>
        <button class="viewer-nav viewer-next" v-if="images.length > 1" @click.stop="next" aria-label="下一张">
          <el-icon><ArrowRight /></el-icon>
        </button>
        <div class="viewer-thumbnails" v-if="images.length > 1">
          <button
            v-for="(img, idx) in images"
            :key="idx"
            :class="['thumb-btn', { active: idx === current }]"
            @click="current = idx"
          >
            <img :src="img" class="thumb-img" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Close, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const visible = ref(false)
const images = ref([])
const current = ref(0)

function open(urls, startIndex = 0) {
  images.value = Array.isArray(urls) ? urls : [urls]
  current.value = Math.max(0, Math.min(startIndex, images.value.length - 1))
  visible.value = true
  document.body.style.overflow = 'hidden'
}

function close() {
  visible.value = false
  document.body.style.overflow = ''
}

function prev() {
  current.value = current.value > 0 ? current.value - 1 : images.value.length - 1
}

function next() {
  current.value = current.value < images.value.length - 1 ? current.value + 1 : 0
}

// Keyboard — registered in lifecycle to avoid memory leaks
function onKeydown(e) {
  if (!visible.value) return
  if (e.key === 'Escape') close()
  if (e.key === 'ArrowLeft') prev()
  if (e.key === 'ArrowRight') next()
}

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
})

defineExpose({ open, close })
</script>

<style scoped>
.image-viewer-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
}
.viewer-fade-enter-active,
.viewer-fade-leave-active {
  transition: opacity 0.3s;
}
.viewer-fade-enter-from,
.viewer-fade-leave-to {
  opacity: 0;
}
.image-viewer-toolbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 16px;
  z-index: 10;
}
.viewer-counter {
  color: #fff;
  font-size: 14px;
  line-height: 36px;
}
.viewer-close {
  position: absolute;
  right: 16px;
  top: 16px;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.viewer-close:hover { background: rgba(255,255,255,0.25); }
.viewer-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
  width: 48px;
  height: 48px;
  border: none;
  border-radius: 50%;
  background: rgba(255,255,255,0.12);
  color: #fff;
  font-size: 22px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}
.viewer-nav:hover { background: rgba(255,255,255,0.25); }
.viewer-prev { left: 20px; }
.viewer-next { right: 20px; }
.image-viewer-body {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 85vw;
  max-height: 80vh;
}
.viewer-image {
  max-width: 85vw;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 4px;
}
.viewer-thumbnails {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
}
.thumb-btn {
  width: 56px;
  height: 40px;
  border: 2px solid transparent;
  border-radius: 4px;
  overflow: hidden;
  padding: 0;
  cursor: pointer;
  background: rgba(255,255,255,0.1);
  transition: border-color 0.2s;
}
.thumb-btn.active { border-color: #fff; }
.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
