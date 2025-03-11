<template>
  <div class="account-container">
    <!-- <CollapsibleSidebar /> -->
    <div class="account-content">
      <!-- Tab 导航 -->
      <div class="tabs-wrapper">
        <div class="tabs-nav">
          <button v-for="tab in tabs" :key="tab.id" @click="activeTab = tab.id"
            :class="['tab-button', { active: activeTab === tab.id }]">
            <div class="tab-content">
              <!-- <svg-icon :name="tab.icon" class="tab-icon"></svg-icon> -->
              <span>{{ tab.name }}</span>
            </div>
          </button>
        </div>
        <div class="action-buttons">
          <template v-if="activeTab === 'department'">
            <a-input
              placeholder="搜索部门"
              style="width: 200px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" :disabled="false" @click="inviteMember">
              <template #icon><UserAddOutlined /></template>
              邀请成员
            </a-button>
          </template>
          
          <template v-if="activeTab === 'group'">
            <a-button type="primary" @click="createGroup">
              <template #icon><PlusOutlined /></template>
              创建群组
            </a-button>
          </template>

          <template v-if="activeTab === 'member'">
            <a-input
              placeholder="搜索成员"
              style="width: 200px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" :disabled="false" @click="inviteMember">
              <template #icon><UserAddOutlined /></template>
              邀请成员
            </a-button>
          </template>

          <template v-if="activeTab === 'permission'">
            <a-input
              placeholder="搜索成员/部门/群组名称"
              style="width: 240px; margin-right: 16px"
              @search="onSearch"
            />
            <a-button type="primary" @click="addPermission">
              <template #icon><PlusOutlined /></template>
              添加权限
            </a-button>
          </template>
        </div>
      </div>

      <!-- Tab 内容区域 -->
      <div class="tab-panel">
        <transition name="fade" mode="out-in">
          <div class="tab-inner" v-if="activeTab === 'member'">
            <Member />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'department'">
            <Department />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'group'">
            <Group />
          </div>
          <div class="tab-inner" v-else-if="activeTab === 'permission'">
            <Permission />
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { UserAddOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { Input, Button } from 'ant-design-vue';
import CollapsibleSidebar from '@/components/CollapsibleSidebar.vue';
import Member from '@/components/Account/Member.vue';
import Department from '@/components/Account/Department.vue';
import Group from '@/components/Account/Group.vue';
import Permission from '@/components/Account/Permission.vue';

const tabs = [
  {
    id: 'member',
    name: '成员',
    icon: 'user'
  },
  {
    id: 'department',
    name: '部门',
    icon: 'shield'
  },
  {
    id: 'group',
    name: '群组',
    icon: 'bell'
  },
  {
    id: 'permission',
    name: '权限',
    icon: 'credit-card'
  }
];

const activeTab = ref('member');

const onSearch = (value: string) => {
  console.log('搜索:', value);
};

const inviteMember = () => {
  console.log('邀请成员');
};

const createGroup = () => {
  console.log('创建群组');
};

const addPermission = () => {
  console.log('添加权限');
};
</script>

<style scoped lang="scss">
.account-container {
  display: flex;
  height: 100vh;
}

.account-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 24px;
  background-color: $mainBgColor;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #667085;
}

.tabs-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.tabs-nav {
  background-color: $secondaryBgColor;
  padding: 4px 4px;
  border-radius: 8px;
  width: auto;
  margin-bottom: 0;
}

.action-buttons {
  display: flex;
  align-items: center;
}

.tab-button {
  flex: 1;
  width: 146px;
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  color: $textColor;

  &:hover:not(.active) {
    background-color: #f4f4f5;
    color: #667085;
  }

  &.active {
    background-color: $mainBgColor;
    color: $textTitleColor;
    box-shadow: $shadow;
  }
}

.tab-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.tab-icon {
  width: 20px;
  height: 20px;
}

.tab-panel {
  background-color: #fff;
  flex: 1;
  border-radius: 12px;
  padding: 24px;
  min-height: 300px;

  .tab-inner {
    height: 100%;
    flex: 1;
  }
  // box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

// 响应式设计
@media screen and (max-width: 768px) {
  .tabs-wrapper {
    flex-direction: column;
    gap: 16px;
  }

  .tabs-nav {
    width: 100%;
  }

  .action-buttons {
    width: 100%;
    flex-direction: column;
    gap: 12px;
    
    .ant-input-search {
      width: 100% !important;
      margin-right: 0;
      margin-bottom: 8px;
    }

    .ant-btn {
      width: 100%;
    }
  }
}

// 添加过渡效果
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.fade-enter-to,
.fade-leave-from {
  opacity: 1;
  transform: translateX(0);
}
</style>
