<!--
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2024-01-09 15:28:56
 * @LastEditors: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @LastEditTime: 2024-01-11 10:43:58
 * @FilePath: /QAnything/front_end/src/layout/index.vue
 * @Description: 
-->
<script lang="ts" setup>
import Head from '@/components/Head.vue';
import Sider from '@/components/Sider.vue';
import KnowledgeList from '@/components/KnowledgeList.vue';
</script>
<style lang="scss" scoped></style>

<template>
  <arco-layout>
    <!-- <Head /> -->
    <arco-layout>
      <arco-layout-sider :width="320">
        <!-- <Sider /> -->
        <KnowledgeList />
      </arco-layout-sider>
      <arco-layout>
        <arco-layout-content>
          <router-view></router-view>
        </arco-layout-content>
      </arco-layout>
    </arco-layout>
  </arco-layout>
</template>
