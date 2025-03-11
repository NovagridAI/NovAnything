<template>
  <div class="sidebar-wrapper">
    <!-- 侧边栏切换按钮 -->
    <div class="sidebar-toggle" :class="{ 'collapsed': isCollapsed }" @click="toggleSidebar">
        <RightOutlined  v-if="isCollapsed" />
        <LeftOutlined v-else />
    </div>

    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
      <div class="sidebar-content">
        <!-- <AddInput /> -->
         知识库Bar
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import SvgIcon from './SvgIcon.vue';
import { LeftOutlined, RightOutlined } from '@ant-design/icons-vue';
import AddInput from '@/components/AddInput.vue';

const isCollapsed = ref(false);

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value;
};

// 暴露方法给父组件
defineExpose({
  isCollapsed,
  toggleSidebar
});
</script>

<style lang="scss" scoped>
.sidebar-wrapper {
  position: relative;
  height: 100%;
}

.sidebar-toggle {
  position: absolute;
  left: 240px;
  top: 20px;
  z-index: 100;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $secondaryBgColor;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  &:hover {
    background: #7B5EF2;
    transform: scale(1.05);
  }

  &.collapsed {
    left: 20px;
  }

  svg {
    width: 16px;
    height: 16px;
    color: #fff;
  }
}

.sidebar {
  width: 260px;
  background: $secondaryBgColor;
  height: 100%;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);

  &-collapsed {
    width: 0;
    overflow: hidden;
  }

  &-content {
    width: 260px;
    height: 100%;
    padding: 20px;
    overflow-y: auto;

    &::-webkit-scrollbar {
      width: 4px;
    }

    &::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 2px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }
  }
}

// 响应式处理
@media screen and (max-width: 768px) {
  .sidebar {
    position: fixed;
    z-index: 1000;
  }

  .sidebar-toggle {
    position: fixed;
  }
}
</style> 