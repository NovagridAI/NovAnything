<template>
  <div class="chat-header-menu">
    <div class="menu-container">
      <arco-dropdown trigger="click" @select="handleSelect">
        <arco-button type="primary" class="dropdown-button">
          {{ selectedOption }}
        </arco-button>
        <template #content>
          <arco-doption
            v-for="(option, index) in options"
            :key="index"
            :value="option"
          >
            {{ option }}
          </arco-doption>
        </template>
      </arco-dropdown>
      
    </div>
    <div class="icon-actions">
      <icon-list class="icon-list" @click="openFullscreenView" />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { IconList } from '@arco-design/web-vue/es/icon';
import { ref } from 'vue';
import routeController from '@/controller/router';

const { changePage } = routeController();
const selectedOption = ref('默认选项');
const options = ref(['选项1', '选项2', '选项3', '选项4']);
const isFullscreenViewOpen = ref(false);

function handleSelect(option: string) {
  selectedOption.value = option;
}

// 打开全屏视图
function openFullscreenView() {
  isFullscreenViewOpen.value = true;
  // 使用路由控制器跳转到全屏视图路由
  changePage('/fullscreen-view/knowledge');
}
</script>

<style scoped>
.chat-header-menu {
  height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.icon-list {
  font-size: 16px;
  color: #4E5969;
  cursor: pointer;
  transition: all 0.3s;
}

.icon-list:hover {
  color: #5a47e5;
  transform: scale(1.1);
}

.icon-actions {
  display: flex;
  align-items: center;
}
</style>
