<template>
  <div class="permission-table">
    <a-table :columns="columns" :data-source="[]" :pagination="false">
      <!-- 成员部分 -->
      <template #expandable="{ record }">
        <a-space>
          <CaretDownOutlined v-if="record.expanded" />
          <CaretRightOutlined v-else />
          {{ record.type }}
        </a-space>
      </template>

      <!-- 名称列 -->
      <template #name="{ record }">
        <a-space>
          <a-avatar :size="24" :src="record.avatar" />
          {{ record.name }}
        </a-space>
      </template>

      <!-- 复选框列 -->
      <template #workspacePermission="{ record }">
        <a-checkbox v-model:checked="record.workspacePermission" />
      </template>

      <template #adminPermission="{ record }">
        <a-checkbox v-model:checked="record.adminPermission" />
      </template>

      <!-- 操作列 -->
      <template #action="{ record }">
        <a-button v-if="record.type !== '成员'" type="link" danger @click="handleDelete(record)">
          <DeleteOutlined />
        </a-button>
      </template>
    </a-table>
  </div>
</template>

<script>
import { defineComponent } from 'vue'
import { 
  CaretDownOutlined, 
  CaretRightOutlined,
  DeleteOutlined 
} from '@ant-design/icons-vue'

export default defineComponent({
  name: 'Permission',
  components: {
    CaretDownOutlined,
    CaretRightOutlined,
    DeleteOutlined
  },
  data() {
    return {
      columns: [
        {
          title: '成员 / 部门 / 群组',
          dataIndex: 'name',
          slots: { customRender: 'name' }
        },
        {
          title: '工作台/知识库创建',
          dataIndex: 'workspacePermission',
          slots: { customRender: 'workspacePermission' }
        },
        {
          title: '管理员',
          dataIndex: 'adminPermission',
          slots: { customRender: 'adminPermission' }
        },
        {
          title: '操作',
          key: 'action',
          slots: { customRender: 'action' }
        }
      ]
    }
  },
  methods: {
    handleDelete(record) {
      // 处理删除逻辑
      console.log('删除', record)
    }
  }
})
</script>

<style scoped>
.permission-table {
  width: 100%;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
}

:deep(.ant-table-tbody > tr > td) {
  padding: 12px 8px;
}
</style>
