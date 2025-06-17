<template>
  <div class="fullscreen-default">
    <!-- 当普通用户没有选择有效选项时显示空白页面 -->
    <div v-if="!shouldRedirect" class="empty-content">
      <arco-empty description="请从左侧菜单选择要管理的内容" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useUser } from '@/store/useUser';
import { storeToRefs } from 'pinia';

const router = useRouter();
const { userInfo } = storeToRefs(useUser());

// 判断是否应该重定向
const shouldRedirect = computed(() => {
  // 如果是管理员或超级管理员，重定向到模型管理
  return userInfo.value?.role === 'admin' || userInfo.value?.role === 'superadmin';
});

onMounted(() => {
  // 如果是管理员，自动重定向到模型管理
  if (shouldRedirect.value) {
    router.replace('/fullscreen-view/model-management');
  }
  // 普通用户不重定向，显示空白页面
});
</script>

<style lang="scss" scoped>
.fullscreen-default {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  
  .empty-content {
    text-align: center;
    padding: 40px;
  }
}
</style> 