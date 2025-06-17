<!--
 * @Author: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @Date: 2023-12-26 14:49:41
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-06 10:09:33
 * @FilePath: front_end/src/components/OptionList.vue
 * @Description: 
-->
<template>
  <a-config-provider :theme="{ token: { colorPrimary: '#5a47e5' } }">
    <div class="list-page">
      <!-- 当没有选中知识库时显示空白页面 -->
      <div v-if="!currentId || currentId.trim() === ''" class="empty-content">
        <arco-empty description="请选择一个知识库开始管理文档" />
      </div>
      
      <!-- 有选中知识库时显示正常内容 -->
      <div v-else class="content">
        <div class="options">
          <!-- <a-button type="primary" class="to-chat" @click="goChat">
            <LeftOutlined class="back-icon" />
            <span>{{ home.conversation }}</span>
          </a-button> -->
          <p class="kb-name">
            <span class="name">
              {{ currentKbName }}
            </span>
          </p>
        </div>
        <div class="nav-info">
          <!-- <div class="navs">
            <div :class="['nav-item', 'nav-item-active']">
              {{ navIndex === 0 ? home.docSet : home.qaSet }}
            </div>
          </div> -->

          <div class="handle-btn">
            <arco-input size="small" placeholder="搜索文件" style="width: 200px;" />

            <arco-button v-if="navIndex === 0 && shouldShowButtons" class="arco-clear-upload" @click="clearUpload"
              style="border: 1px solid #F53F3F; color: #F53F3F; background-color: #fff;">
              {{ home.clearAllFile }}
            </arco-button>
            <arco-button v-if="navIndex === 0 && shouldShowButtons" class="arco-clear-upload" @click="batchDeleteFiles"
              style="border: 1px solid #F53F3F; color: #F53F3F; background-color: #fff;"
              :disabled="selectedRowKeys.length === 0">
              批量删除 ({{ selectedRowKeys.length }})
            </arco-button>

            <arco-button v-if="navIndex === 0 && shouldShowButtons" type="primary" class="arco-file-upload" @click="showFileUpload">
              {{ home.upload }}
            </arco-button>
            <arco-button v-if="navIndex === 0 && shouldShowButtons" type="outline" class="arco-add-link" @click="showUrlUpload">
              {{ home.addUrl }}
            </arco-button>
            <arco-button v-if="navIndex === 0 && isTeamKb && (userInfo?.role === 'admin' || userInfo?.role === 'superadmin')" 
              type="outline" class="arco-manage-members" @click="showPermissionDialog">
              <TeamOutlined />
              权限设置
            </arco-button>
            <arco-button v-if="navIndex === 1 && shouldShowButtons" type="outline" class="arco-upload" @click="showEditQaSet">
              {{ home.inputQa }}
            </arco-button>
            <!-- <a-popover v-if="navIndex === 0" trigger="click" placement="top">
              <template #content>
                <TagsInput @confirm-tag="
                  newTags => {
                    tagConfirm('kb', currentId, newTags);
                  }
                " />
              </template>
<a-button type="primary" style="margin: 0px 10px; height: 40px">所有文件一键添加tag</a-button>
</a-popover>
<a-popover v-if="navIndex === 0" trigger="click" placement="top">
  <template #content>
                <TagsInput @confirm-tag="
                  newTags => {
                    tagConfirm('fileBatch', [...selectedKeys.keys()], newTags);
                  }
                " />
              </template>
  <a-button type="primary" style="height: 40px">批量添加tag</a-button>
</a-popover> -->
          </div>
          <div v-if="navIndex === 0 && hasUploadingFiles" class="nav-progress">
            <UploadProgress :data-source="dataSource" />
          </div>
        </div>
        <!-- 可滚动的表格区域 -->
        <div class="table-container">
          <arco-table 
            v-model:selectedKeys="selectedRowKeys"
            :loading="loading" 
            :row-selection="shouldShowSelection ? { type: 'checkbox', showCheckedAll: true } : null" 
            :data="dataSource" :columns="columns"
            :pagination="kbPaginationConfig" row-key="fileId" @page-change="current => kbOnChange({ current })"
            @selection-change="onSelectionChange"
            :scroll="{ y: '75vh' }"
            size="small">
            <template #fileIdName="{ record }">
              <arco-tooltip :content="record.fileIdName" :disabled="!isTextTruncated(record.fileIdName, 200)">
                <div class="file-name-cell">{{ record.fileIdName }}</div>
              </arco-tooltip>
            </template>
            <template #status="{ record }">
              <div class="status-container">
                <div class="status-box">
                  <div class="icon-file-status">
                    <LoadingImg v-if="record.status === 'gray' || record.status === 'yellow'" class="loading-icon" 
                      style="width: 14px !important; height: 14px !important; max-width: 14px !important; max-height: 14px !important;" />
                    <SvgIcon v-else class="status-icon" :name="record.status === 'green' ? 'success' : 'error'" />
                  </div>
                  <span class="status-text">{{ parseStatus(record.status) }}</span>
                </div>
              </div>
            </template>
            <template #options="{ record }">
              <arco-popconfirm v-if="shouldShowButtons" class-name="del-pop" position="tr" content-class="del-pop-content"
                :content="common.deleteTitle" @ok="confirm">
                <!-- :disabled="record.status == 'gray' || record.status === 'yellow'" -->
                <arco-button type="text" class="delete-item" @click="deleteItem(record)">
                  {{ common.delete }}
                </arco-button>
              </arco-popconfirm>
              <arco-button type="text" class="view-item" :disabled="!(record.status === 'green')"
                @click="viewItem(record)">
                {{ common.view }}
              </arco-button>
            </template>
            <template #remark="{ record }">
              <div v-if="typeof record.remark === 'string'">{{ record.remark }}</div>
              <div v-else>
                <p v-for="(value, key) in record.remark" :key="key">
                  {{ `${key}: ${value}` }}
                </p>
              </div>
            </template>
          </arco-table>
        </div>

      </div>
    </div>
    <ChunkViewDialog :kb-id="currentId" :file-id="fileId" :file-name="fileIdName" />
    <FileUploadDialog :dialog-type="0" />
    <PermissionDialog v-model:visible="permissionDialogVisible" :kb-id="currentId" @confirm="handlePermissionConfirm"
      @cancel="handlePermissionCancel" />
    <UrlUploadDialog />
  </a-config-provider>
</template>
<script lang="ts" setup>
import urlResquest from '@/services/urlConfig';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { useUser } from '@/store/useUser';
import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import { useChunkView } from '@/store/useChunkView';
import { useOptiionList } from '@/store/useOptiionList';
import { pageStatus } from '@/utils/enum';
import { resultControl } from '@/utils/utils';
import { message, Modal } from 'ant-design-vue';
import { Message } from '@arco-design/web-vue';
import { h, nextTick } from 'vue';
import { getLanguage } from '@/language';
import LoadingImg from '@/components/LoadingImg.vue';
import UploadProgress from '@/components/UploadProgress.vue';
import ChunkViewDialog from '@/components/ChunkViewDialog.vue';
import FileUploadDialog from '@/components/FileUploadDialog.vue';
import { LeftOutlined, QuestionCircleOutlined, UserOutlined, PlusOutlined, MinusOutlined, TeamOutlined, UsergroupAddOutlined } from '@ant-design/icons-vue';
import Tags from '@/components/Tags.vue';
import TagsInput from '@/components/TagsInput.vue';
import PermissionDialog from './PermissionDialog.vue';
import UrlUploadDialog from '@/components/UrlUploadDialog.vue';

const { setDefault } = useKnowledgeBase();
const { currentKbName, currentId, knowledgeBaseList } = storeToRefs(useKnowledgeBase());
const { userInfo } = storeToRefs(useUser());
const { setModalVisible, setUrlModalVisible, setModalTitle } = useKnowledgeModal();
const { showChunkModel, fileId, kbId, fileIdName } = storeToRefs(useChunkView());
const {
  getDetails,
  setEditQaSet,
  setEditModalVisible,
  getFaqList,
  setFaqType,
  setPageNum,
  setKbPageNum,
} = useOptiionList();
const {
  dataSource,
  faqList,
  timer,
  faqTimer,
  total,
  pageNum,
  pageSize,
  loading,
  kbTotal,
  kbPageNum,
  kbPageSize,
} = storeToRefs(useOptiionList());

console.log(dataSource.value);
const home = getLanguage().home;
const common = getLanguage().common;
const bots = getLanguage().bots;

const navIndex = computed(() => computedKbType.value);

const computedKbType = computed(() => {
  if (currentId.value.endsWith('_FAQ')) {
    return 1;
  } else {
    return 0;
  }
});

// 判断当前知识库是否为团队知识库
const isTeamKb = computed(() => {
  const currentKb = knowledgeBaseList.value.find(kb => kb.kb_id === currentId.value);
  return currentKb?.kb_type === 'team';
});

// 判断是否应该显示操作按钮（管理员对团队知识库可以上传文件）
const shouldShowButtons = computed(() => {
  if (userInfo.value?.role === 'superadmin') {
    return true; // 超级管理员在所有知识库都显示按钮
  }
  if (userInfo.value?.role === 'admin') {
    return true; // 管理员可以操作个人知识库和团队知识库
  }
  return !isTeamKb.value; // 普通用户只在个人知识库显示按钮
});

// 判断是否应该显示勾选框（普通用户在团队知识库不显示）
const shouldShowSelection = computed(() => {
  return shouldShowButtons.value;
});

// 判断是否有正在上传的文件（进度条显示逻辑）
const hasUploadingFiles = computed(() => {
  return dataSource.value.some(item => item.status === 'gray' || item.status === 'yellow');
});

const columns = [
  {
    title: home.documentId,
    dataIndex: 'fileId',
    key: 'fileId',
    width: '16%',
  },
  {
    title: home.documentName,
    dataIndex: 'fileIdName',
    key: 'fileIdName',
    width: '18%',
    ellipsis: true,
    slotName: 'fileIdName',
  },
  // {
  //   title: home.documentTag,
  //   dataIndex: 'fileTag',
  //   key: 'fileTag',
  //   width: '12%',
  // },
  {
    title: home.documentStatus,
    dataIndex: 'status',
    key: 'status',
    width: '10%',
    ellipsis: true,
    slotName: 'status',
  },
  {
    title: home.fileSize,
    dataIndex: 'bytes',
    key: 'bytes',
    width: '8%',
  },
  {
    title: home.contentLength,
    dataIndex: 'contentLength',
    key: 'contentLength',
    width: '10%',
  },
  {
    title: home.creationDate,
    dataIndex: 'createtime',
    key: 'createtime',
    width: '10%',
  },
  {
    title: home.remark,
    dataIndex: 'remark',
    key: 'remark',
    width: '18%',
    slotName: 'remark',
  },
  {
    title: home.operate,
    key: 'options',
    width: '10%',
    slotName: 'options',
  },
];

const qaColumns = [
  {
    title: 'ID',
    dataIndex: 'id',
    key: 'id',
    width: '8%',
  },
  {
    title: home.question,
    dataIndex: 'question',
    key: 'question',
    width: '43%',
    ellipsis: true,
  },
  {
    title: home.status,
    dataIndex: 'status',
    key: 'status',
    width: '10%',
    ellipsis: true,
  },
  {
    title: home.characterCount,
    dataIndex: 'bytes',
    key: 'bytes',
    width: '10%',
  },
  {
    title: home.creationDate,
    dataIndex: 'createtime',
    key: 'createtime',
    width: '11%',
  },
  {
    title: home.operate,
    key: 'options',
    width: '10%',
    slotName: 'options',
  },
];

const tagConfirm = async (
  type: 'file' | 'fileBatch' | 'kb',
  id: string[] | string,
  newTags: Array<string>
) => {
  if (type === 'file') {
    console.log(type, id, newTags);
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        file_ids: id,
        is_replace: true,
      })
    );
    Message.success('成功修改标签');
  } else if (type === 'fileBatch') {
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        file_ids: id,
        is_replace: false,
      })
    );
    Message.success('成功批量添加标签');
    selectedKeys.value.clear();
    await getDetails();
  } else if (type === 'kb') {
    console.log(type, id, newTags);
    await resultControl(
      await urlResquest.updateTags({
        tags: newTags,
        kb_id: id,
        is_replace: false,
      })
    );
    Message.success('成功为所有文件添加标签');
    await getDetails();
  }
};

const kbPaginationConfig = computed(() => ({
  current: kbPageNum.value,
  pageSize: kbPageSize.value,
  total: kbTotal.value,
  showSizeChanger: false,
  showTotal: total => `共 ${total} 条`,
}));

const paginationConfig = computed(() => ({
  current: pageNum.value,
  pageSize: pageSize.value,
  total: total.value,
  showSizeChanger: false,
  showTotal: total => `共 ${total} 条`,
}));

let optionItem: any = {};

const deleteItem = item => {
  optionItem = item;
};

// const fileId = ref('');
// const fileIdName = ref('');

const viewItem = async item => {
  fileId.value = item.fileId;
  fileIdName.value = item.fileIdName;
  showChunkModel.value = true;
  console.log(fileId.value)
};

const confirm = async () => {
  try {
    await resultControl(
      await urlResquest.deleteFile({ file_ids: [optionItem.fileId], kb_id: currentId.value })
    );
    Message.success('删除成功');
    await getDetails();
    if (kbPageNum.value !== 1 && dataSource.value.length === 0) {
      kbPageNum.value -= 1;
      await getDetails();
    }
  } catch (e) {
    Message.error(e.msg || '删除失败');
  }
};

let qaOptionItem: any = {};

const deleteQaItem = item => {
  qaOptionItem = item;
};

const qaConfirm = async () => {
  try {
    await resultControl(
      await urlResquest.deleteFile({
        kb_id: `${currentId.value}_FAQ`,
        file_ids: [qaOptionItem.faqId],
      })
    );
    Message.success('删除成功');
    await getFaqList();
    if (pageNum.value !== 1 && faqList.value.length === 0) {
      pageNum.value -= 1;
      await getFaqList();
    }
  } catch (e) {
    Message.error(e.msg || '删除失败');
  }
};

const editQaItem = item => {
  setFaqType('edit');
  setEditQaSet(item);
  setEditModalVisible(true);
};
const goChat = () => {
  setDefault(pageStatus.normal);
};

const showFileUpload = () => {
  setModalVisible(true);
  setModalTitle(home.upload);
};

const showUrlUpload = () => {
  setUrlModalVisible(true);
  setModalTitle(common.addUrl);
};

const showEditQaSet = () => {
  setFaqType('upload');
  setEditModalVisible(true);
};

const clearUpload = () => {
  Modal.confirm({
    title: home.clearAllFile,
    content: h('p', home.clearAllFileConfirm),
    centered: true,
    maskClosable: true,
    okText: common.confirm,
    okType: 'danger',
    async onOk() {
      try {
        await resultControl(await urlResquest.clearUpload({ status: 'gray', kb_ids: [] }));
        Message.success('操作成功');
        getDetails();
      } catch (e) {
        Message.error(e.msg || '操作失败');
      }
    },
  });
};

const parseStatus = status => {
  let str: string;
  switch (status) {
    case 'gray':
      str = common.inLine;
      break;
    case 'yellow':
      str = common.parsing;
      break;
    case 'green':
      str = common.succeeded;
      break;
    default:
      str = common.failed;
      break;
  }
  return str;
};

const parseFaqStatus = status => {
  let str = common.failed;
  switch (status) {
    case 'gray':
      str = common.uploadCompleted;
      break;
    case 'yellow':
      str = common.inLine;
      break;
    case 'green':
      str = common.learningCompleted;
      break;
    default:
      break;
  }
  return str;
};

const onChange = pagination => {
  const { current } = pagination;
  setPageNum(current);
  getFaqList();
};

const kbOnChange = pagination => {
  setKbPageNum(pagination.current);
  getDetails();
};

const selectedKeys = ref<Map<string, string>>(new Map());
const selectedRowKeys = ref<string[]>([]);

const onSelectionChange = (rowKeys: string[]) => {
  console.log('=== onSelectionChange 事件 ===');
  console.log('参数rowKeys:', rowKeys);
  console.log('当前selectedRowKeys.value:', selectedRowKeys.value);
  
  // 直接使用传入的rowKeys更新选中状态
  selectedRowKeys.value = [...rowKeys];
  console.log('更新后的selectedRowKeys:', selectedRowKeys.value);
  
  // 强制触发响应式更新
  nextTick(() => {
    console.log('nextTick后的selectedRowKeys:', selectedRowKeys.value);
  });
};

// 判断文本是否会被截断
const isTextTruncated = (text: string, maxWidth: number) => {
  if (!text) return false;
  
  // 创建一个临时的测量元素
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d');
  context.font = '14px PingFang SC, Arial, sans-serif'; // 与表格字体一致
  
  const textWidth = context.measureText(text).width;
  return textWidth > maxWidth;
};

// 清空选中状态
const clearSelection = () => {
  console.log('清空选中状态');
  selectedRowKeys.value = [];
  console.log('清空后的selectedRowKeys:', selectedRowKeys.value);
};

watch(
  currentId,
  () => {
    // 清空选中状态
    clearSelection();
    setKbPageNum(1);
    setPageNum(1);
    getDetails();
  },
  {
    immediate: true,
  }
);

// 监听dataSource变化，清空不存在的选中项
watch(
  dataSource,
  (newDataSource) => {
    if (selectedRowKeys.value.length > 0 && newDataSource.length > 0) {
      const validFileIds = newDataSource.map(item => item.fileId);
      const filteredSelected = selectedRowKeys.value.filter(id => validFileIds.includes(id));
      if (filteredSelected.length !== selectedRowKeys.value.length) {
        selectedRowKeys.value = filteredSelected;
        console.log('清理无效的选中项，剩余选中:', selectedRowKeys.value);
      }
    }
  },
  { deep: true }
);

// 禁用滚轮事件的变量
let preventWheel;
let preventKeyboardScroll;
let knowledgeManagementElement;

onMounted(() => {
  // 移除滚动锁定代码
});

onBeforeUnmount(() => {
  clearTimeout(timer.value);
  clearTimeout(faqTimer.value);
  setKbPageNum(1);
  setPageNum(1);
});

const permissionDialogVisible = ref(false);

const showPermissionDialog = () => {
  permissionDialogVisible.value = true;
};

const handlePermissionConfirm = (data) => {
  console.log('权限设置确认:', data);
  Message.success('权限设置已保存');
};

const handlePermissionCancel = () => {
  console.log('权限设置取消');
};

const batchDeleteFiles = () => {
  console.log('=== 批量删除函数被调用 ===');
  console.log('selectedRowKeys.value:', selectedRowKeys.value);
  console.log('dataSource.value length:', dataSource.value.length);
  
  if (selectedRowKeys.value.length === 0) {
    console.log('没有选中的文件，显示警告');
    Message.warning('请先选择要删除的文件');
    return;
  }

  // 直接从dataSource中找到选中的文件信息
  const selectedFiles = dataSource.value.filter(item => selectedRowKeys.value.includes(item.fileId));
  const selectedFileIds = selectedFiles.map(item => item.fileId);
  const selectedFileNames = selectedFiles.map(item => item.fileIdName);
  
  console.log('找到的选中文件数量:', selectedFiles.length);
  console.log('选中的文件IDs:', selectedFileIds);
  console.log('选中的文件名:', selectedFileNames);

  if (selectedFiles.length === 0) {
    console.log('未找到匹配的文件，可能是数据不同步');
    Message.warning('选中的文件数据异常，请刷新页面后重试');
    return;
  }

  Modal.confirm({
    title: '批量删除文件',
    content: h('div', [
      h('p', `确定要删除以下 ${selectedFileIds.length} 个文件吗？删除后无法恢复。`),
      h('div', {
        style: {
          maxHeight: '200px',
          overflowY: 'auto',
          marginTop: '12px',
          padding: '8px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px'
        }
      }, selectedFileNames.map(name => h('div', { style: { padding: '2px 0' } }, `• ${name}`)))
    ]),
    centered: true,
    maskClosable: true,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        await resultControl(
          await urlResquest.deleteFile({ 
            file_ids: selectedFileIds, 
            kb_id: currentId.value 
          })
        );
        Message.success(`成功删除 ${selectedFileIds.length} 个文件`);
        // 清空选中状态
        clearSelection();
        // 刷新文件列表
        await getDetails();
        // 如果当前页没有数据了，返回上一页
        if (kbPageNum.value !== 1 && dataSource.value.length === 0) {
          kbPageNum.value -= 1;
          await getDetails();
        }
      } catch (e) {
        Message.error(e.msg || '批量删除失败');
      }
    },
  });
};


</script>

<style lang="scss" scoped>
.list-page {
  width: 100%;
  height: 100% !important;
  max-height: 100% !important;
  font-family: PingFang SC;
  display: flex;
  flex-direction: column;
  overflow: hidden !important;

  .content {
    flex: 1;
    min-height: 0;
    padding: 24px 32px;
    background: $mainBgColor;
    border-radius: 12px 0 0 0;
    display: flex;
    flex-direction: column;
    overflow: hidden !important;
  }
  
  .empty-content {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    max-height: 100vh;
    background: $mainBgColor;
    border-radius: 12px 0 0 0;
    overflow: hidden;
  }
}

.options {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;

  .to-chat {
    display: flex;
    align-items: center;
    height: 40px;
    padding: 8px 20px;
    font-size: 16px;

    .back-icon {
      font-size: 16px;
    }

    span {
      font-size: 16px;
      font-weight: 500;
      color: #ffffff;
    }
  }

  .kb-name {
    margin: 0 20px 0 0pxpx;
    font-size: 20px;
    font-weight: 500;
    color: #222222;

    .name {
      margin-right: 20px;
    }

    .id {
      font-size: 14px;
      font-weight: 400;
      color: #999;
    }
  }

  .kb-tag {
    flex: 1;
    display: flex;
    justify-content: flex-end;
  }
}

.nav-info {
  flex-shrink: 0;
  width: 100%;
  margin: 16px 0 10px 0;
  display: flex;
  justify-content: space-between;

  .navs {
    height: 40px;
    padding: 4px;
    border-radius: 8px;
    background: $secondaryBgColor;
    display: flex;

    .nav-item {
      min-width: 100px;
      padding: 0 20px;
      height: 32px;
      font-size: 16px;
      color: #666666;
      border-radius: 6px;
      text-align: center;
      line-height: 32px;
    }

    .nav-item-active {
      background: #fff;
      font-weight: 500;
      color: $baseColor;
    }
  }

  .nav-progress {
    width: 40%;
    margin: 0 10px 0;
    display: flex;
    align-items: center;
    flex-shrink: 0;
  }

  .handle-btn {
    display: flex;
    gap: 10px;

    .upload {
      cursor: pointer;
      height: 40px;
      padding: 8px 20px;
      border-radius: 4px;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;
      color: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }

    .add-link {
      cursor: pointer;
      height: 40px;
      margin-left: 16px;
      padding: 8px 20px;
      border-radius: 4px;
      background: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }

    .manage-members {
      cursor: pointer;
      height: 40px;
      margin-left: 16px;
      padding: 8px 20px;
      border-radius: 4px;
      background: #ffffff;
      border: 1px solid $baseColor;
      color: $baseColor;
      font-size: 16px;
      font-weight: 500;
      line-height: 24px;

      &:hover {
        border: 1px solid lighten($baseColor, 20%);
        color: lighten($baseColor, 20%);
      }
    }
  }
}

.table {
  height: 100%;
  margin-bottom: 0;
  overflow: auto;
  border-radius: 12px;
  background-color: #fff;

  &::-webkit-scrollbar {
    width: 0;
  }

  .options {
    width: 80px;
    display: flex;
    justify-content: space-between;
  }

  .delete-item {
    padding: 2px;
    font-size: 14px;
    font-weight: normal;
    line-height: 22px;
    margin-right: 5px;
    color: #ff524c;
  }

  .view-item {
    padding: 2px;
    font-size: 14px;
    font-weight: normal;
    line-height: 22px;
    margin-right: 5px;
    color: #4d71ff;
  }

  .edit-item {
    padding: 0;
  }

  .file-status {
    width: 16px !important;
    height: 16px !important;
    min-width: 16px !important;
    min-height: 16px !important;
    max-width: 16px !important;
    max-height: 16px !important;
    display: inline-block !important;
    overflow: hidden !important;
    
    // 特别针对LoadingImg组件的img元素
    :deep(.img) {
      width: 16px !important;
      height: 16px !important;
      max-width: 16px !important;
      max-height: 16px !important;
    }
    
    // 特别针对svg元素
    :deep(svg) {
      width: 16px !important;
      height: 16px !important;
      max-width: 16px !important;
      max-height: 16px !important;
    }
    
    // 针对SvgIcon组件
    :deep(.svg-icon) {
      width: 16px !important;
      height: 16px !important;
      max-width: 16px !important;
      max-height: 16px !important;
    }
  }

  .file-name-cell {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: pointer;
    
    &:hover {
      color: #5a47e5;
    }
  }

  .status-container {
    display: flex;
    align-items: center;
    width: 100%;
    height: 22px;
  }

  .status-box {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    height: 22px;
    line-height: 22px;

    .icon-file-status {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      height: 14px;
      flex-shrink: 0;
      vertical-align: middle;
      
      // 强制所有子元素的大小
      * {
        width: 14px !important;
        height: 14px !important;
        max-width: 14px !important;
        max-height: 14px !important;
        font-size: 14px !important;
        vertical-align: middle !important;
      }
      
      .loading-icon {
        width: 14px !important;
        height: 14px !important;
        display: inline-block !important;
        vertical-align: middle !important;
        overflow: hidden !important;
        
        // 强制内部所有元素的大小
        :deep(*) {
          width: 14px !important;
          height: 14px !important;
          max-width: 14px !important;
          max-height: 14px !important;
          vertical-align: middle !important;
        }
        
        // 特别针对LoadingImg组件的img元素
        :deep(.img) {
          width: 14px !important;
          height: 14px !important;
          max-width: 14px !important;
          max-height: 14px !important;
        }
      }
      
      .status-icon {
        width: 14px !important;
        height: 14px !important;
        font-size: 14px !important;
        vertical-align: middle !important;
      }
    }

    .status-text {
      font-size: 14px;
      line-height: 22px;
      height: 22px;
      color: inherit;
      vertical-align: middle;
      display: inline-block;
    }
  }
}

:deep(.ant-table-wrapper .ant-table-thead > tr > th) {
  font-size: 14px !important;
  font-weight: 500 !important;
  line-height: 24px !important;
  padding: 15px 16px 15px 36px !important;
  color: #222222 !important;
  background-color: lighten($baseColor, 45%);
  text-align: left !important;

  .small {
    font-size: 12px !important;
  }

  &:before {
    width: 0 !important;
  }
}

:deep(.ant-table-tbody > tr > td) {
  font-size: 14px;
  font-weight: normal;
  line-height: 22px;
  color: #666666;
  background-color: #fff;
  padding: 16px 16px 16px 36px !important;
  border: 0 !important;
  box-shadow: inset 0px -1px 0px 0px rgba(0, 0, 0, 0.05);
  text-align: left !important;
  vertical-align: middle !important;

  &:hover {
    background-color: rgba(233, 237, 247, 0.3);
  }
}

// 特别针对ArcoDesign表格的单元格样式
:deep(.arco-table-td) {
  vertical-align: middle !important;
  
  .status-container {
    display: flex !important;
    align-items: center !important;
    width: 100% !important;
    height: 22px !important;
  }
  
  .status-box {
    display: inline-flex !important;
    align-items: center !important;
    vertical-align: middle !important;
  }
}

:deep(.ant-pagination) {
  margin: 16px 20px !important;
}

:deep(.ant-pagination-item) {
  box-sizing: border-box !important;
  border: 1px solid #dde2ec !important;
}

:deep(.ant-pagination-item-active) {
  background: #5a47e5 !important;
  color: #fff !important;

  a {
    color: #fff !important;
  }
}

:deep(.options > .ant-btn) {
  height: auto;
}

:deep(.ant-btn-link) {
  color: #5a47e5;
}

:deep(.ant-btn-link:disabled) {
  color: rgba(0, 0, 0, 0.25);
}

:deep(.ant-table-empty .ant-table-placeholder .ant-table-cell) {
  color: #999999 !important;
}

/* 表格容器样式 */
.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  
  :deep(.arco-table-pagination-wrapper) {
    background: #fff !important;
    border-top: 1px solid #e5e6eb !important;
    padding: 16px !important;
    text-align: center;
    box-shadow: 0 -2px 8px rgba(0,0,0,0.1) !important;
  }
  
  // 自定义表格loading样式 - 大幅缩小loading图标
  :deep(.arco-spin) {
    .arco-spin-icon {
      width: 14px !important;
      height: 14px !important;
      font-size: 14px !important;
      max-width: 14px !important;
      max-height: 14px !important;
    }
    
    // 如果是表格的loading遮罩
    &.arco-spin-loading {
      .arco-spin-icon {
        width: 16px !important;
        height: 16px !important;
        font-size: 16px !important;
        max-width: 16px !important;
        max-height: 16px !important;
      }
    }
  }
  
  // 针对表格整体的loading状态
  :deep(.arco-table-loading) {
    .arco-spin {
      .arco-spin-icon {
        width: 16px !important;
        height: 16px !important;
        font-size: 16px !important;
        max-width: 16px !important;
        max-height: 16px !important;
      }
    }
  }
  
  // 强制限制所有loading相关的元素大小
  :deep(.arco-spin-loading-layer) {
    .arco-spin-icon {
      width: 16px !important;
      height: 16px !important;
      font-size: 16px !important;
      max-width: 16px !important;
      max-height: 16px !important;
    }
  }
  
  // 强制限制表格内部的所有loading动画
  :deep(.arco-table-td) {
    .arco-spin {
      .arco-spin-icon {
        width: 14px !important;
        height: 14px !important;
        font-size: 14px !important;
        max-width: 14px !important;
        max-height: 14px !important;
      }
    }
  }
  
  // 如果有其他的loading组件，也强制限制大小
  :deep(.loading-indicator) {
    width: 14px !important;
    height: 14px !important;
    max-width: 14px !important;
    max-height: 14px !important;
    
    * {
      width: 14px !important;
      height: 14px !important;
      max-width: 14px !important;
      max-height: 14px !important;
    }
  }
}

// 全局强制所有loading相关的样式
:deep(.arco-spin-icon) {
  width: 14px !important;
  height: 14px !important;
  font-size: 14px !important;
  max-width: 14px !important;
  max-height: 14px !important;
}

// 针对表格内的所有spin图标
.table-container :deep(.arco-spin-icon) {
  width: 14px !important;
  height: 14px !important;
  font-size: 14px !important;
  max-width: 14px !important;
  max-height: 14px !important;
}

// 特别针对LoadingImg组件强制限制大小
.table-container :deep(.loading-icon) {
  width: 14px !important;
  height: 14px !important;
  max-width: 14px !important;
  max-height: 14px !important;
  overflow: hidden !important;
  
  .img {
    width: 14px !important;
    height: 14px !important;
    max-width: 14px !important;
    max-height: 14px !important;
  }
}

// 更强力的全局样式控制LoadingImg
:deep(.loading-icon) {
  width: 14px !important;
  height: 14px !important;
  max-width: 14px !important;
  max-height: 14px !important;
  
  img, .img {
    width: 14px !important;
    height: 14px !important;
    max-width: 14px !important;
    max-height: 14px !important;
  }
}
</style>

<style lang="scss">
.del-pop {
  margin-right: 10px;

  .ant-popover-content {
    .ant-btn-default {
      padding: 1px 8px;
      border: 1px solid rgba(0, 0, 0, 0.15) !important;

      span {
        line-height: 1;
      }
    }

    .ant-popover-inner {
      padding: 12px 16px;
      transform: translateX(44px);
    }

    .ant-popconfirm-message-icon {
      svg {
        font-size: 16px;
      }
    }

    .ant-popconfirm-message-title {
      width: 168px;
      height: 36px;
      line-height: 36px;
    }

    .ant-popconfirm-message {
      align-items: center !important;
    }
  }
}

.qa-del-pop {
  .ant-popover-inner {
    padding-top: 20px;
    height: 100px;
  }

  .ant-popconfirm-buttons {
    margin-top: 16px;
  }

  .ant-btn-sm {
    width: 60px;
  }

  .ant-btn-sm.ant-btn-loading {
    width: auto !important;
  }
}
</style>
