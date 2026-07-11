<template>
  <div class="admin-page">
    <h1>{{ config.title }}</h1>

    <!-- ═══ Toolbar ═══ -->
    <div class="page-toolbar">
      <div class="toolbar-left">
        <el-button v-if="visibleActions.create" type="primary" @click="openDialog()">
          <el-icon><Plus /></el-icon>新增{{ config.title.replace('管理', '') }}
        </el-button>
        <slot name="toolbar-extra" />
      </div>
      <div class="toolbar-right">
        <!-- filter selects -->
        <el-select
          v-for="(f, key) in config.filters"
          :key="key"
          v-model="activeFilters[key]"
          :placeholder="f.label"
          clearable
          size="default"
          style="width: 120px; margin-left: 8px"
          @change="onFilterChange"
        >
          <el-option
            v-for="opt in (f.options || [])"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>
        <!-- search -->
        <el-input
          v-if="config.searchFields?.length"
          v-model="keyword"
          placeholder="搜索..."
          clearable
          style="width: 200px; margin-left: 8px"
          @input="onSearch"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
    </div>

    <!-- ═══ Table ═══ -->
    <el-table :data="items" v-loading="loading" stripe>
      <el-table-column
        v-for="col in config.columns"
        :key="col.prop"
        :prop="col.prop"
        :label="col.label"
        :width="col.width"
        :sortable="col.sortable || false"
      >
        <template #default="{ row }">
          <slot :name="`column-${col.prop}`" :row="row">
            <!-- switch -->
            <template v-if="col.type === 'switch'">
              <el-switch
                :model-value="row[col.prop]"
                size="small"
                @change="(val) => handleInlineSwitch(col.prop, row, val)"
              />
            </template>
            <!-- tag -->
            <template v-else-if="col.type === 'tag'">
              <el-tag :type="col.tagMap?.[row[col.prop]] || 'info'" size="small">
                {{ col.valueMap?.[row[col.prop]] ?? row[col.prop] }}
              </el-tag>
            </template>
            <!-- datetime -->
            <template v-else-if="col.type === 'datetime'">
              {{ fmtDate(row[col.prop]) }}
            </template>
            <!-- text (default) -->
            <template v-else>
              {{ col.valueMap?.[row[col.prop]] ?? row[col.prop] }}
            </template>
          </slot>
        </template>
      </el-table-column>

      <!-- Actions column -->
      <el-table-column v-if="hasActions" label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <slot name="actions" :row="row">
            <el-button
              v-if="visibleActions.edit"
              type="primary"
              link
              @click="openDialog(row)"
            >编辑</el-button>
            <el-button
              v-if="visibleActions.delete"
              type="danger"
              link
              @click="handleDelete(row)"
            >删除</el-button>
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <!-- ═══ Pagination ═══ -->
    <div class="page-pagination">
      <Pagination
        v-model:page="page"
        :total="total"
        :page-size="pageSize"
        @change="loadData"
      />
    </div>

    <!-- ═══ Form Dialog ═══ -->
    <el-dialog
      v-if="config.formFields?.length"
      v-model="dialogVisible"
      :title="editId ? '编辑' : '新增'"
      width="600px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form :model="form" label-position="top">
        <el-form-item
          v-for="field in config.formFields"
          :key="field.prop"
          :label="field.label"
          :required="field.required"
        >
          <!-- slot override -->
          <slot :name="`form-${field.prop}`" :form="form" :field="field">
            <!-- text -->
            <el-input
              v-if="field.type === 'text'"
              v-model="form[field.prop]"
              :placeholder="field.placeholder"
            />
            <!-- textarea -->
            <el-input
              v-else-if="field.type === 'textarea'"
              v-model="form[field.prop]"
              type="textarea"
              :rows="4"
              :placeholder="field.placeholder"
            />
            <!-- number -->
            <el-input-number
              v-else-if="field.type === 'number'"
              v-model="form[field.prop]"
              :min="field.min ?? 0"
              controls-position="right"
              style="width: 100%"
            />
            <!-- select -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="form[field.prop]"
              :placeholder="`请选择${field.label}`"
              clearable
              style="width: 100%"
            >
              <el-option
                v-for="opt in resolvedOptions(field)"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
            <!-- switch -->
            <el-switch
              v-else-if="field.type === 'switch'"
              v-model="form[field.prop]"
            />
            <!-- date -->
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="form[field.prop]"
              type="date"
              value-format="YYYY-MM-DD"
              :placeholder="`请选择${field.label}`"
              style="width: 100%"
            />
            <!-- image → ImageUploader -->
            <ImageUploader
              v-else-if="field.type === 'image'"
              v-model="form[`__img__${field.prop}`]"
              :limit="1"
            />
            <!-- tag → TagInput -->
            <TagInput
              v-else-if="field.type === 'tag'"
              v-model="form[field.prop]"
              :limit="field.limit || 10"
            />
          </slot>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- ═══ Detail slot (Posts drawer etc.) ═══ -->
    <slot name="detail" />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { Plus, Search } from '@element-plus/icons-vue'
import adminApi from '@/api/admin'
import api from '@/api/request'
import ImageUploader from '@/components/common/ImageUploader.vue'
import TagInput from '@/components/common/TagInput.vue'
import Pagination from '@/components/common/Pagination.vue'
import { toast } from '@/utils/toast'
import { confirmDelete } from '@/utils/dialog'
import { debounce } from '@/utils/debounce'

const props = defineProps({
  config: { type: Object, required: true },
})

// ── computed config shortcuts ──────────────────────────
const actions = computed(() => props.config.actions || [])
const visibleActions = computed(() => ({
  create: actions.value.includes('create'),
  edit: actions.value.includes('edit'),
  delete: actions.value.includes('delete'),
}))
const hasActions = computed(() => visibleActions.value.edit || visibleActions.value.delete)
const pageSize = computed(() => props.config.pageSize || 20)
const resourceApi = computed(() => {
  // resolve `config.resource` → adminApi[resource]
  return adminApi[props.config.resource] || null
})

// ── state ─────────────────────────────────────────────
const items = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const keyword = ref('')
const activeFilters = reactive({})

// init activeFilters from config
watch(() => props.config.filters, (filters) => {
  if (filters) {
    for (const key of Object.keys(filters)) {
      if (!(key in activeFilters)) activeFilters[key] = ''
    }
  }
}, { immediate: true })

// dialog
const dialogVisible = ref(false)
const editId = ref(null)
const saving = ref(false)
const form = reactive({})

// ── data loading ──────────────────────────────────────

function buildParams() {
  const params = { page: page.value, page_size: pageSize.value }
  if (keyword.value) params.keyword = keyword.value
  // append activeFilters (non-empty values)
  for (const key of Object.keys(activeFilters)) {
    if (activeFilters[key] !== '' && activeFilters[key] !== null && activeFilters[key] !== undefined) {
      params[key] = activeFilters[key]
    }
  }
  return params
}

async function loadData() {
  if (!resourceApi.value?.list) {
    console.warn(`[AdminCrud] adminApi.${props.config.resource}.list not found`)
    return
  }
  loading.value = true
  try {
    const data = await resourceApi.value.list(buildParams())
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    toast.error(e?.message || '加载失败')
  } finally {
    loading.value = false
  }
}

// ── search & filter ───────────────────────────────────

const onSearch = debounce(() => {
  page.value = 1
  loadData()
}, 300)

function onFilterChange() {
  page.value = 1
  loadData()
}

// ── form helpers ──────────────────────────────────────

/** Build a blank form object from formFields. */
function createEmptyForm() {
  const obj = {}
  for (const field of props.config.formFields || []) {
    if (field.type === 'switch') {
      obj[field.prop] = false
    } else if (field.type === 'tag') {
      obj[field.prop] = []
    } else if (field.type === 'number') {
      obj[field.prop] = field.min ?? 0
    } else {
      obj[field.prop] = ''
    }
    // internal image array key
    if (field.type === 'image') {
      obj[`__img__${field.prop}`] = []
    }
  }
  return obj
}

function populateForm(row) {
  Object.assign(form, createEmptyForm())
  for (const field of props.config.formFields || []) {
    if (field.type === 'image') {
      // row.image_url → img array for ImageUploader
      form[`__img__${field.prop}`] = row[field.prop] ? [row[field.prop]] : []
    } else if (field.type === 'date') {
      form[field.prop] = row[field.prop] || ''
    } else if (field.prop in row) {
      form[field.prop] = row[field.prop] ?? form[field.prop]
    }
  }
}

function openDialog(row) {
  if (row) {
    editId.value = row.id
    populateForm(row)
  } else {
    editId.value = null
    Object.assign(form, createEmptyForm())
  }
  dialogVisible.value = true
}

function resetForm() {
  editId.value = null
  Object.assign(form, createEmptyForm())
}

// ── save ─────────────────────────────────────────────

async function handleSave() {
  // build payload from form, resolving image fields
  const payload = { ...form }
  for (const field of props.config.formFields || []) {
    if (field.type === 'image') {
      const imgArr = form[`__img__${field.prop}`] || []
      payload[field.prop] = imgArr[0] || ''
      delete payload[`__img__${field.prop}`]
    }
  }
  // clean internal keys
  for (const key of Object.keys(payload)) {
    if (key.startsWith('__img__')) delete payload[key]
  }

  saving.value = true
  try {
    if (editId.value) {
      await resourceApi.value.update(editId.value, payload)
      toast.success('更新成功')
    } else {
      await resourceApi.value.create(payload)
      toast.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    toast.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// ── delete ───────────────────────────────────────────

async function handleDelete(row) {
  try {
    await confirmDelete('确认删除', `确定删除该项吗？此操作不可撤销。`)
  } catch {
    return // user cancelled
  }
  try {
    await resourceApi.value.delete(row.id)
    toast.success('已删除')
    loadData()
  } catch (e) {
    toast.error(e?.message || '删除失败')
  }
}

// ── inline switch toggle ─────────────────────────────

async function handleInlineSwitch(prop, row, val) {
  if (!resourceApi.value?.update) return
  try {
    await resourceApi.value.update(row.id, { [prop]: val })
    row[prop] = val
    toast.success(val ? '已启用' : '已禁用')
  } catch (e) {
    toast.error(e?.message || '操作失败')
    // revert on failure? the switch already flipped in UI via v-model
    // reload to be safe
    loadData()
  }
}

// ── utilities ────────────────────────────────────────

function fmtDate(val) {
  if (!val) return ''
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

/** Resolve select options — returns field.options (static), or fetches from field.optionsSource. */
const selectCache = reactive({})
function resolvedOptions(field) {
  if (field.options?.length) return field.options
  if (field.optionsSource && !selectCache[field.optionsSource]) {
    fetchSelectOptions(field)
    return []
  }
  return selectCache[field.optionsSource] || []
}

async function fetchSelectOptions(field) {
  try {
    const data = await api.get(field.optionsSource)
    selectCache[field.optionsSource] = Array.isArray(data) ? data : (data.items || data.options || [])
  } catch {
    selectCache[field.optionsSource] = []
  }
}

// ── lifecycle ────────────────────────────────────────

onMounted(() => {
  loadData()
})

// Expose for parent ref access
defineExpose({ loadData })
</script>

<style scoped>
.admin-page { padding: 0; }
.admin-page h1 {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 24px;
  color: var(--text-primary, #1a1a1a);
}
.page-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 12px;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.toolbar-right { display: flex; align-items: center; }
.page-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
