<template>
  <Teleport to="body">
    <Transition name="overlay-fade">
      <div v-if="visible" class="search-overlay" @click.self="close">
        <div class="search-overlay__panel">
          <div class="search-overlay__input">
            <el-input
              ref="searchInput"
              v-model="keyword"
              placeholder="搜索美食、非遗、民俗活动..."
              size="large"
              :prefix-icon="Search"
              clearable
              @input="onInput"
              @keyup.enter="onSearch"
              @keyup.esc="close"
            >
              <template #suffix>
                <kbd class="search-shortcut">Esc</kbd>
              </template>
            </el-input>
          </div>

          <div v-if="!keyword.trim()" class="search-overlay__hot">
            <p class="search-overlay__label">热门搜索</p>
            <el-tag
              v-for="kw in hotKeywords"
              :key="kw"
              size="large"
              effect="plain"
              class="search-overlay__tag"
              @click="keyword = kw; onSearch()"
            >
              {{ kw }}
            </el-tag>
          </div>

          <div v-else class="search-overlay__results">
            <div v-if="searching" class="search-overlay__loading">
              <el-icon class="is-loading" :size="24"><Loading /></el-icon>
              <span>搜索中...</span>
            </div>

            <template v-else>
              <div v-if="results.foods?.length > 0" class="search-overlay__group">
                <p class="search-overlay__group-title">🍜 美食 ({{ results.foods.length }})</p>
                <div
                  v-for="item in results.foods.slice(0, 3)"
                  :key="item.id"
                  class="search-overlay__item"
                  @click="goTo('/foods/' + item.id)"
                >
                  <span class="search-overlay__item-name">{{ item.name }}</span>
                  <span class="search-overlay__item-type">{{ item.type === 'shop' ? '店铺' : '菜品' }}</span>
                </div>
              </div>

              <div v-if="results.heritages?.length > 0" class="search-overlay__group">
                <p class="search-overlay__group-title">🎭 非遗 ({{ results.heritages.length }})</p>
                <div
                  v-for="item in results.heritages.slice(0, 3)"
                  :key="item.id"
                  class="search-overlay__item"
                  @click="goTo('/heritages/' + item.id)"
                >
                  <span class="search-overlay__item-name">{{ item.name }}</span>
                  <el-tag size="small">{{ item.category }}</el-tag>
                </div>
              </div>

              <div v-if="results.events?.length > 0" class="search-overlay__group">
                <p class="search-overlay__group-title">📅 民俗活动 ({{ results.events.length }})</p>
                <div
                  v-for="item in results.events.slice(0, 3)"
                  :key="item.id"
                  class="search-overlay__item"
                  @click="goTo('/festival')"
                >
                  <span class="search-overlay__item-name">{{ item.name }}</span>
                  <span class="search-overlay__item-type">{{ item.region }}</span>
                </div>
              </div>

              <div v-if="isEmpty" class="search-overlay__empty">
                <EmptyState description="没有找到相关内容，换个关键词试试" />
              </div>
            </template>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, Loading } from '@element-plus/icons-vue'
import { getFoods, getHeritages, getEvents } from '@/api'
import EmptyState from './EmptyState.vue'
import { debounce } from '@/utils/debounce'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const keyword = ref('')
const searching = ref(false)
const searchInput = ref(null)
const results = reactive({ foods: [], heritages: [], events: [] })

const hotKeywords = ['牛肉火锅', '英歌舞', '工夫茶', '粿品', '生腌', '广济桥', '南澳岛', '营老爷']

const isEmpty = computed(() => {
  return keyword.value.trim() && !searching.value &&
    results.foods.length === 0 && results.heritages.length === 0 && results.events.length === 0
})

function close() {
  visible.value = false
  keyword.value = ''
  results.foods = []
  results.heritages = []
  results.events = []
}

function goTo(path) {
  close()
  router.push(path)
}

const doSearch = debounce(async () => {
  const kw = keyword.value.trim()
  if (!kw) {
    results.foods = []
    results.heritages = []
    results.events = []
    return
  }

  searching.value = true
  try {
    const [foodsRes, heritagesRes, eventsRes] = await Promise.all([
      getFoods({ keyword: kw, page_size: 3 }).catch(() => ({ items: [] })),
      getHeritages({ keyword: kw, page_size: 3 }).catch(() => ({ items: [] })),
      getEvents({ keyword: kw, page_size: 3 }).catch(() => ({ items: [] })),
    ])

    results.foods = foodsRes?.items || (Array.isArray(foodsRes) ? foodsRes : [])
    results.heritages = heritagesRes?.items || (Array.isArray(heritagesRes) ? heritagesRes : [])
    results.events = eventsRes?.items || (Array.isArray(eventsRes) ? eventsRes : [])
  } finally {
    searching.value = false
  }
}, 300)

function onInput() {
  doSearch()
}

function onSearch() {
  if (keyword.value.trim()) {
    router.push('/search?keyword=' + encodeURIComponent(keyword.value.trim()))
    close()
  }
}

watch(visible, (v) => {
  if (v) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

// 全局快捷键 Ctrl+K
function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    visible.value = !visible.value
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.search-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: var(--z-modal-backdrop, 300);
  display: flex;
  justify-content: center;
  padding-top: 15vh;
}

.search-overlay__panel {
  width: 560px;
  max-height: 70vh;
  background: #fff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  overflow-y: auto;
}

.search-overlay__input {
  padding: 20px 20px 0;
}

.search-shortcut {
  padding: 2px 6px;
  background: #eee;
  border-radius: 4px;
  font-size: 11px;
  color: #999;
  border: 1px solid #ddd;
}

.search-overlay__hot,
.search-overlay__results {
  padding: 16px 20px 20px;
}

.search-overlay__label {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 10px;
}

.search-overlay__tag {
  margin: 4px;
  cursor: pointer;
}

.search-overlay__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--muted);
}

.search-overlay__group {
  margin-bottom: 16px;
}

.search-overlay__group-title {
  font-size: var(--fs-sm);
  font-weight: 600;
  margin-bottom: 8px;
}

.search-overlay__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}

.search-overlay__item:hover {
  background: var(--surface);
}

.search-overlay__item-name {
  font-size: var(--fs-sm);
}

.search-overlay__item-type {
  font-size: 12px;
  color: var(--muted);
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.2s;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

@media (max-width: 767px) {
  .search-overlay__panel {
    width: 90vw;
    max-height: 80vh;
  }
}
</style>
