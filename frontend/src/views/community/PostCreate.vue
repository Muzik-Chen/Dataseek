<template>
  <div class="post-create-page">
<<<<<<< HEAD
=======
    <BackButton />
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    <div class="page-header">
      <h1>✍️ 发布动态</h1>
      <p>分享你的潮汕探索故事、美食推荐或文化发现</p>
    </div>

    <div class="form-card">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="类型" prop="post_type">
          <el-radio-group v-model="form.post_type">
            <el-radio-button value="recommend">👍 推荐</el-radio-button>
            <el-radio-button value="challenge">🎯 挑战</el-radio-button>
            <el-radio-button value="social">👋 社交</el-radio-button>
            <el-radio-button value="study">📚 文化</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="给动态起个吸引人的标题" maxlength="200" show-word-limit />
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="8"
            placeholder="写下你想分享的内容..."
            maxlength="10000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="标签">
<<<<<<< HEAD
          <div class="preset-tags">
            <button
              v-for="t in presetTags"
              :key="t"
              :class="['tea-pill', 'tea-pill--sm', { active: form.tags.includes(t) }]"
              :disabled="form.tags.length >= 5"
              @click="toggleTag(t)"
            >{{ t }}</button>
          </div>
          <TagInput v-model="form.tags" :limit="5" placeholder="输入自定义标签，回车添加" />
        </el-form-item>

        <el-form-item label="图片">
          <ImageUploader v-model="form.images" :limit="9" />
=======
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            placeholder="添加标签（回车创建）"
            style="width:100%"
          >
            <el-option
              v-for="t in presetTags"
              :key="t"
              :label="t"
              :value="t"
            />
          </el-select>
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
        </el-form-item>

        <el-form-item>
          <el-button type="primary" size="large" :loading="submitting" @click="publish">
            {{ submitting ? '发布中...' : '发布动态' }}
          </el-button>
          <el-button size="large" @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createPost } from '@/api'
<<<<<<< HEAD
import TagInput from '@/components/common/TagInput.vue'
import ImageUploader from '@/components/common/ImageUploader.vue'
=======
import BackButton from '@/components/common/BackButton.vue'
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22

const router = useRouter()
const formRef = ref(null)
const submitting = ref(false)

const form = reactive({
  post_type: 'recommend',
  title: '',
  content: '',
  tags: [],
<<<<<<< HEAD
  images: [],
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
})

const presetTags = [
  '牛肉火锅', '工夫茶', '英歌舞', '肠粉', '广济桥',
  '南澳岛', '牌坊街', '小公园', '潮剧', '美食推荐',
  '旅行攻略', '非遗体验', '民俗活动', '探店', '文化知识',
]

<<<<<<< HEAD
function toggleTag(tag) {
  const idx = form.tags.indexOf(tag)
  if (idx >= 0) {
    form.tags.splice(idx, 1)
  } else if (form.tags.length < 5) {
    form.tags.push(tag)
  }
}

=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
const rules = {
  post_type: [{ required: true }],
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 200, message: '标题2-200字', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 10, message: '内容至少10个字', trigger: 'blur' },
  ],
}

async function publish() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await createPost({
      title: form.title,
      content: form.content,
      post_type: form.post_type,
      tags: form.tags,
<<<<<<< HEAD
      images: form.images,
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
    })
    ElMessage.success('发布成功！')
    router.push('/community')
  } catch (e) {
    ElMessage.error(e.message || '发布失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.post-create-page {
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-2xl) var(--space-md);
}

.page-header { margin-bottom: var(--space-2xl); }

.page-header h1 { font-size: var(--fs-2xl); color: var(--ink); margin: 0 0 var(--space-xs); }
.page-header p { color: var(--muted); margin: 0; }

.form-card {
  background: var(--surface);
  border-radius: 16px;
  padding: var(--space-2xl);
  box-shadow: 0 2px 12px oklch(0 0 0 / 0.04);
}
<<<<<<< HEAD

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
  margin-bottom: var(--space-sm);
}

.tea-pill--sm {
  padding: 2px 10px;
  font-size: var(--fs-xs);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  background: var(--bg);
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}

.tea-pill--sm:hover { border-color: var(--brand-red); color: var(--brand-red); }
.tea-pill--sm.active { background: var(--brand-red); color: #fff; border-color: var(--brand-red); }
.tea-pill--sm:disabled { opacity: 0.4; cursor: not-allowed; }
=======
>>>>>>> 21e3c77773c3c723533ac403c37b7d726a663c22
</style>
