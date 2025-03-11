<!--
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-02 15:15:50
 * @FilePath: front_end/src/views/Home.vue
 * @Description: 
-->

<template>
  <div class="page">
    <div class="layout-wrapper">
      <!-- 使用侧边栏组件 -->
      <CollapsibleSidebar ref="sidebarRef">
        <!-- 侧边栏内容 -->
        <div class="sidebar-menu">
          <!-- 这里可以放置侧边栏的内容 -->
        </div>
      </CollapsibleSidebar>

      <!-- 主内容区 -->
      <div class="container" :class="{ 'container-expanded': isSidebarCollapsed }">
        <div v-if="showDefault === pageStatus.initing" class="initing"></div>
        <DefaultPage v-if="showDefault === pageStatus.default" @change="change" />
        <Chat v-else-if="showDefault === pageStatus.normal" />
        <OptionList v-else-if="showDefault === pageStatus.optionlist" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { pageStatus } from '@/utils/enum';
import DefaultPage from '@/components/Defaultpage.vue';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import Chat from '@/components/Chat.vue';
import OptionList from '@/components/OptionList.vue';
import { ref, computed } from 'vue';
import CollapsibleSidebar from '@/components/CollapsibleSidebar.vue';

const { showDefault } = storeToRefs(useKnowledgeBase());

const { setDefault, getList } = useKnowledgeBase();

const sidebarRef = ref();
const isSidebarCollapsed = computed(() => sidebarRef.value?.isCollapsed);

//开始回答后执行的操作
//1.展示聊天界面
//2.默认知识库显示出来
const change = str => {
  setDefault(str);
  getList();
};

onMounted(() => {
  getList();
});
</script>

<style lang="scss" scoped>
.page {
  position: relative;
  height: 100%;
}

.layout-wrapper {
  display: flex;
  height: 100%;
}

.container {
  flex: 1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 0;
  
  &-expanded {
    margin-left: 0;
  }
}

.sidebar-menu {
  color: #fff;
  // 添加你的侧边栏菜单样式
}

.page {
  width: 100%;
  height: 100%;
}

.container {
  //padding-top: 0;
  width: 100%;
  height: 100%;
  background-color: $mainBgColor;

  .initing {
    width: 100%;
    height: 100%;
    background: #f3f6fd;
    border-radius: 12px 0 0 0;
  }
}
</style>
