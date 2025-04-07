<template>
  <div class="fullscreen-sider">
    <arco-menu
      :selected-keys="[activeMenu]"
      :open-keys="expandedKeys"
      @menu-item-click="handleMenuClick"
      @sub-menu-click="handleSubMenuClick"
      :auto-open-selected="true"
      :auto-scroll-into-view="true"
    >
      <arco-menu-item key="user-settings">
        <template #icon><icon-settings /></template>
        模型设置
      </arco-menu-item>
      
      <arco-sub-menu key="knowledge-management">
        <template #icon><icon-folder /></template>
        <template #title>知识库管理</template>
        <arco-menu-item key="personal-knowledge">
          <template #icon><icon-file /></template>
          个人知识库
        </arco-menu-item>
        <arco-menu-item key="organization-knowledge">
          <template #icon><icon-file /></template>
          团队知识库
        </arco-menu-item>
      </arco-sub-menu>
      
      <arco-menu-item key="organization-management">
        <template #icon><icon-user /></template>
        组织管理
      </arco-menu-item>
    </arco-menu>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  IconSettings,  
  IconUserGroup,
  IconUser,
  IconFolder,
  IconFile
} from '@arco-design/web-vue/es/icon';

const router = useRouter();
const route = useRoute();

// 当前激活的菜单项
const activeMenu = ref('personal-knowledge');
const expandedKeys = ref<string[]>(['knowledge-management']);

// 路由映射
const menuRouteMap = {
  'user-settings': '/fullscreen-view/user-settings',
  'personal-knowledge': '/fullscreen-view/knowledge/personal',
  'organization-knowledge': '/fullscreen-view/knowledge/organization',
  'organization-management': '/fullscreen-view/organization-management'
};

// 监听路由变化
router.afterEach(() => {
  initActiveMenu();
});

// 初始化激活菜单
onMounted(() => {
  initActiveMenu();
});

// 根据当前路由设置激活的菜单项
const initActiveMenu = () => {
  const currentPath = route.path;
  
  // 反向查找路由映射
  for (const [key, path] of Object.entries(menuRouteMap)) {
    if (currentPath.includes(path)) {
      activeMenu.value = key;
      
      // 如果是子菜单项，确保父菜单展开
      if (key.includes('knowledge')) {
        expandedKeys.value = ['knowledge-management'];
      }
      
      break;
    }
  }
};

// 处理菜单项点击
const handleMenuClick = (key: string) => {
  const targetPath = menuRouteMap[key];
  if (targetPath) {
    router.push(targetPath);
  }
};

// 处理子菜单点击
const handleSubMenuClick = (key: string) => {
  // 子菜单展开/折叠逻辑
  if (expandedKeys.value.includes(key)) {
    expandedKeys.value = expandedKeys.value.filter(k => k !== key);
  } else {
    expandedKeys.value.push(key);
  }
};
</script>

<style lang="scss" scoped>
.fullscreen-sider {
  height: 100%;
  border-right: 1px solid var(--color-border);
  
  :deep(.arco-menu) {
    width: 100%;
    height: 100%;
    box-shadow: none;
    border-right: none;
  }
  
  :deep(.arco-menu-inner) {
    padding: 40px 20px;
  }
  
  :deep(.arco-menu-item) {
    height: 40px;
    line-height: 40px;
    margin: 4px 0;
    width: 200px;

    &.arco-menu-selected {
      font-weight: 500;
    }
  }
  
  :deep(.arco-menu-icon) {
    margin-right: 10px;
  }
  
  :deep(.arco-sub-menu-title) {
    height: 40px;
    line-height: 40px;
  }
  
  :deep(.arco-sub-menu-inner) {
    padding-left: 16px;
  }
}
</style>
