<template>
  <footer class="app-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-logo">潮</span>
        <span>潮汕文化宣传平台</span>
      </div>
      <p class="footer-copy">&copy; 2026 潮汕文化宣传平台</p>
    </div>
  </footer>
</template>

<style scoped>
.app-footer {
  margin-top: var(--space-4xl);
  padding: var(--space-2xl) 0;
  border-top: 1px solid var(--el-border-color-light);
  background: var(--surface);
}

.footer-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--space-md);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--space-md);
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: var(--fs-sm);
  font-weight: 600;
  color: var(--ink);
}

.footer-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: var(--primary);
  color: #fff;
  font-size: var(--fs-sm);
  font-weight: 700;
  border-radius: 4px;
}

.footer-copy {
  font-size: var(--fs-sm);
  color: var(--muted);
}
</style>
