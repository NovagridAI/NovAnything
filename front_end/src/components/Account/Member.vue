<template>
  <div>
    <!-- <h1>Member</h1> -->
    <a-table :columns="columns" :data-source="dataSource" :pagination="false">
      <template #bodyCell="{ column }">
        <template v-if="column.key === 'operation'">
          <a-space :size="16">
            <a-tooltip title="停用用户">
              <stop-outlined @click="handleStop" />
            </a-tooltip>
            <a-tooltip title="升级为管理员">
              <user-switch-outlined @click="handleUpgrade" />
            </a-tooltip>
            <a-tooltip title="删除用户">
              <delete-outlined class="delete-icon" @click="handleDelete" />
            </a-tooltip>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script>
import { StopOutlined, UserSwitchOutlined, DeleteOutlined } from '@ant-design/icons-vue';

export default {
  components: {
    StopOutlined,
    UserSwitchOutlined,
    DeleteOutlined,
  },
  data() {
    return {
      columns: [
        {
          title: '用户名',
          dataIndex: 'username',
          key: 'username',
        },
        {
          title: '登录方式',
          dataIndex: 'loginType',
          key: 'loginType',
        },
        {
          title: '部门',
          dataIndex: 'department',
          key: 'department',
        },
        {
          title: '加入/更新时间',
          dataIndex: 'updateTime',
          key: 'updateTime',
        },
        {
          title: '操作',
          key: 'operation',
        },
      ],
      dataSource: [
        {
          key: '1',
          username: 'Member',
          loginType: '-',
          department: '已加入部门',
          updateTime: '2025-03-10 09:06:34',
        },
        // 可以添加更多数据
      ],
    };
  },
  methods: {
    handleStop() {
      // 处理停用用户的逻辑
      console.log('停用用户');
    },
    handleUpgrade() {
      // 处理升级为管理员的逻辑
      console.log('升级为管理员');
    },
    handleDelete() {
      // 处理删除用户的逻辑
      console.log('删除用户');
    },
  },
};
</script>

<style scoped>
.anticon {
  font-size: 16px;
  cursor: pointer;
}
.anticon:hover {
  color: #1890ff;
}
.delete-icon {
  color: #ff4d4f;
}
.delete-icon:hover {
  color: #ff7875;
}
</style>

