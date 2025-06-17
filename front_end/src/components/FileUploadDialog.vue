<!--
 * @Author: 祝占朋 wb.zhuzp01@rd.netease.com
 * @Date: 2023-11-07 19:32:26
 * @LastEditors: Ianarua 306781523@qq.com
 * @LastEditTime: 2024-08-05 17:48:27
 * @FilePath: front_end/src/components/FileUploadDialog.vue
 * @Description:
-->
<template>
  <Teleport to="body">
    <arco-modal
      v-model:visible="modalVisible"
      :title="modalTitle"
      centered
      width="480px"
      wrap-class-name="upload-file-modal"
      destroy-on-close
    >
      <div class="file">
        <div class="box">
          <div class="before-upload-box">
            <input
              class="hide input"
              type="file"
              :accept="acceptList.join(',')"
              multiple
              @change="fileChange"
              @click="e => ((e.target as HTMLInputElement).value = '')"
            />
            <div class="before-upload">
              <div class="upload-text-box">
                <SvgIcon name="upload" />
                <p>
                  <span class="upload-text">
                    {{ common.dragUrl }}
                    <span class="blue">{{ common.click }}</span>
                  </span>
                </p>
              </div>
              <p class="desc">
                {{ common.updesc1 }}
              </p>
            </div>
          </div>
          <!--          <div-->
          <!--            v-show="showUploadList && props.dialogType !== 1"-->
          <!--            class="upload-box"-->
          <!--            :class="showUploadList ? 'upload-list' : ''"-->
          <!--          >-->
          <!--            <UploadList>-->
          <!--              <template #default>-->
          <!--                <ul class="list">-->
          <!--                  <li v-for="(item, index) in uploadFileList" :key="index">-->
          <!--                    <span class="name">{{ item.file_name }}</span>-->
          <!--                    <div class="status-box">-->
          <!--                      <SvgIcon v-if="item.status != 'loading'" :name="item.status" />-->
          <!--                      <img-->
          <!--                        v-else-->
          <!--                        class="loading"-->
          <!--                        src="../assets/home/icon-loading.png"-->
          <!--                        alt="loading"-->
          <!--                      />-->
          <!--                      <span class="status">{{-->
          <!--                        item.status == 'loading' ? item.text : item.errorText-->
          <!--                      }}</span>-->
          <!--                    </div>-->
          <!--                  </li>-->
          <!--                </ul>-->
          <!--              </template>-->
          <!--            </UploadList>-->
          <!--            &lt;!&ndash;            <div class="note">{{ common.errorTip }}</div>&ndash;&gt;-->
          <!--          </div>-->
        </div>
      </div>
      <template #footer>
        <arco-button
          v-if="props.dialogType === 0"
          key="submit"
          type="primary"
          class="upload-btn"
          :disabled="!canSubmit"
          @click="handleOk"
        >
          {{ common.confirm }}
        </arco-button>
        <arco-button
          v-if="props.dialogType === 1"
          key="submit"
          type="primary"
          class="upload-btn"
          @click="handleCancel"
        >
          {{ common.cancel }}
        </arco-button>
      </template>
    </arco-modal>
  </Teleport>
</template>
<script lang="ts" setup>
import { apiBase } from '@/services';
import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { useOptiionList } from '@/store/useOptiionList';
import SvgIcon from './SvgIcon.vue';
// import UploadList from '@/components/UploadList.vue';
import { pageStatus } from '@/utils/enum';
import { IFileListItem } from '@/utils/types';
import { message, notification } from 'ant-design-vue';
import { userIdD } from '@/services/urlConfig';
import { getLanguage } from '@/language/index';
import { useUploadFiles } from '@/store/useUploadFiles';
import { useChatSetting } from '@/store/useChatSetting';
import Cookies from 'js-cookie';
// import { useLanguage } from '@/store/useLanguage';

// const { language } = storeToRefs(useLanguage());
const common = getLanguage().common;
const { setKnowledgeName, setModalVisible } = useKnowledgeModal();
const { setDefault } = useKnowledgeBase();
const { getDetails, getTempDetail } = useOptiionList();
const { modalVisible, modalTitle } = storeToRefs(useKnowledgeModal());
const { currentId, currentKbName } = storeToRefs(useKnowledgeBase());
const { uploadFileList, uploadFileListQuick } = storeToRefs(useUploadFiles()); // 上传的文件列表
const { initUploadFileList } = useUploadFiles();
const { chatSettingFormActive } = storeToRefs(useChatSetting());

const props = defineProps({
  // 0为知识库上传，1为快速开始上传
  dialogType: {
    type: Number,
    require: true,
    default: 0,
  },

  temporaryId: {
    type: String,
    require: false,
    default: '',
  },
});

const timer = ref();

// const uploadFileList = ref([]); // 本次上传文件列表

//控制确认按钮 是否能提交
const canSubmit = computed(() => {
  // 增强验证逻辑
  const hasValidKbId = props.dialogType === 2 
    ? (props.temporaryId && props.temporaryId.length > 0)
    : (currentId.value && currentId.value.length > 0);
    
  return (
    hasValidKbId &&
    uploadFileList.value.length > 0 &&
    uploadFileList.value.every(item => item.status != 'loading')
  );
});

watch(
  () => modalVisible.value,
  () => {
    setKnowledgeName(currentKbName.value);
    // showUploadList.value = !!uploadFileList.value.length;
    // 如果是快速开始的便捷上传，将quick的引用给uploadFileList，因为便捷上传和知识库上传用两个data
    if (props.dialogType === 1) {
      uploadFileList.value = uploadFileListQuick.value;
    }
    if (!modalVisible.value && (props.dialogType === 0 || props.dialogType === 2)) {
      initUploadFileList();
    }
    
    // 检查知识库选择状态
    if (modalVisible.value) {
      const hasValidKbId = props.dialogType === 2 
        ? (props.temporaryId && props.temporaryId.length > 0)
        : (currentId.value && currentId.value.length > 0);
        
      if (!hasValidKbId && props.dialogType !== 1) {
        console.warn('知识库ID缺失:', {
          dialogType: props.dialogType,
          temporaryId: props.temporaryId,
          currentId: currentId.value
        });
      }
    }
  }
);

//是否显示上传文件列表 默认不显示
// const showUploadList = ref(false);

//允许上传的文件格式
const acceptList = [
  '.md',
  '.txt',
  '.pdf',
  '.jpg',
  '.png',
  '.jpeg',
  '.doc',
  '.docx',
  '.xls',
  '.xlsx',
  '.ppt',
  '.pptx',
  '.jsonl',
  '.eml',
  '.csv',
  // '.mp3',
  // '.wav',
];

// 文件大小限制
const fileSizeLimit = {
  document: 30 * 1024 * 1024, // 单个文档小于30M
  image: 5 * 1024 * 1024, // 单张图片小于5M
};

// 文件总大小限制
const totalSizeLimit = 125 * 1024 * 1024; // 文件总大小不超过125MB

//上传前校验
const beforeFileUpload = async (file, index) => {
  return new Promise((resolve, reject) => {
    console.log(file);
    // 检查文件扩展名是否被接受
    if (file.name && acceptList.includes('.' + file.name.split('.').pop().toLowerCase())) {
      // 根据文件类型设置大小限制
      const limit = file.type.startsWith('image/') ? fileSizeLimit.image : fileSizeLimit.document;
      const fileType = file.type.startsWith('image/') ? '图片' : '文档';

      // 检查文件大小是否超过限制
      if (file.size > limit) {
        reject(`单个${fileType}太大，不能超过 ${limit / 1024 / 1024} MB`);
        return;
      }

      // 如果文件通过所有检查，将其添加到上传列表
      uploadFileList.value.push({
        file_name: file.name,
        file: file,
        status: 'loading',
        text: common.uploading,
        file_id: '',
        order: uploadFileList.value.length,
        bytes: 0,
      });
      resolve(index);
    } else {
      reject(`${file.name}的文件格式不符`);
    }
  });
};

//input上传
const fileChange = e => {
  const files: FileList = e.target.files;
  
  // 先检查文件总大小
  let totalFilesSize = 0;
  for (const file of files) {
    totalFilesSize += file.size;
    if (totalFilesSize >= totalSizeLimit) {
      message.error('文件总大小超过125MB');
      return; // 直接返回，不继续处理
    }
  }
  
  // 处理每个文件
  Array.from(files).forEach(async (file: any, index) => {
    try {
      await beforeFileUpload(file, index);
    } catch (e) {
      message.error(e);
    }
  });
  
  // 延迟执行上传，确保所有文件都已处理完成
  setTimeout(() => {
    if (uploadFileList.value.length > 0) {
      console.log('开始上传，文件数量:', uploadFileList.value.length);
      uplolad();
    } else {
      console.log('没有有效的文件需要上传');
    }
  }, 100); // 增加延迟时间确保异步处理完成
};

const uplolad = async () => {
  const userID = userIdD();
  
  // 验证kb_id是否有效
  let targetKbId = '';
  if (props.dialogType === 2) {
    targetKbId = props.temporaryId;
  } else {
    targetKbId = currentId.value;
  }
  
  // 增强验证
  if (!targetKbId || targetKbId.trim() === '') {
    message.error('请先选择知识库后再上传文件');
    return;
  }
  
  // 在关闭对话框前先保存需要上传的文件列表
  const list = [];
  uploadFileList.value.forEach((file: IFileListItem) => {
    if (file.status == 'loading') {
      list.push(file);
    }
  });
  
  // 注释掉立即关闭对话框的逻辑，改为在上传成功后关闭
  
  if (list.length === 0) {
    message.warn('没有需要上传的文件');
    return;
  }
  
  const formData = new FormData();
  for (let i = 0; i < list.length; i++) {
    formData.append('files', list[i]?.file);
  }
  
  // 使用验证过的kb_id
  formData.append('kb_id', targetKbId);
  
  formData.append('user_id', userID);
          formData.append('chunk_size', (chatSettingFormActive.value?.chunkSize || 800).toString());
  // 上传模式，soft：文件名重复的文件不再上传，strong：文件名重复的文件强制上传
  formData.append('mode', 'soft');
  
  console.log('上传参数:', {
    kb_id: targetKbId,
    user_id: userID,
    files_count: list.length,
    dialog_type: props.dialogType
  });
  
  openNotification(0);
  fetch(apiBase + '/local_doc_qa/upload_files', {
    method: 'POST',
    body: formData,
    credentials: 'include',
    headers: {
      'Authorization': `Bearer ${Cookies.get('token')}`
    }
  })
    .then(response => {
      if (response.ok) {
        return response.json(); // 将响应解析为 JSON
      } else {
        throw new Error('上传失败');
      }
    })
    .then(data => {
      // 在此处对接口返回的数据进行处理
      if (data.code === 200) {
        if (data.data.length === 0) {
          // 上传相同文件
          message.warn(data.msg || '出错了');
          // handleCancel();
          notification.close('upload');
          if (props.dialogType === 1) {
            list.forEach(item => {
              uploadFileList.value[item.order].status = 'error';
              uploadFileList.value[item.order].errorText = data?.msg || common.upFailed;
            });
          }
          return;
        }
        
        // 检查是否有失败的文件
        const failedFiles = data.data.filter(file => file.status === 'error' || file.status === 'skipped');
        const successFiles = data.data.filter(file => file.status === 'green' || file.status === 'gray');
        
        if (successFiles.length > 0) {
          openNotification(1);
        } else {
          // 如果没有成功的文件，关闭上传中的通知
          notification.close('upload');
        }
        
        // 显示详细的结果信息
        if (failedFiles.length > 0) {
          const failureDetails = failedFiles.map(file => `${file.file_name}（${file.error_reason}）`).join('；');
          if (successFiles.length > 0) {
            message.warn(`部分文件上传失败：${failureDetails}`);
          } else {
            message.error(`文件上传失败：${failureDetails}`);
          }
        }
        
        if (props.dialogType === 1) {
          // 为每个上传的文件设置状态
          data.data.forEach((fileResult, index) => {
            // 找到对应的文件
            const uploadItem = list.find(item => {
              // 通过文件名匹配
              return uploadFileList.value[item.order].file_name === fileResult.file_name;
            });
            
            if (uploadItem) {
              let status = fileResult.status;
              if (status === 'green' || status === 'gray') {
                status = 'success';
                uploadFileList.value[uploadItem.order].errorText = common.upSucceeded;
              } else {
                status = 'error';
                uploadFileList.value[uploadItem.order].errorText = fileResult.error_reason || common.upFailed;
              }
              uploadFileList.value[uploadItem.order].status = status;
              uploadFileList.value[uploadItem.order].file_id = fileResult.file_id;
              uploadFileList.value[uploadItem.order].bytes = fileResult.bytes || 0;
            }
          });
        }
        
        // 上传成功后立即关闭弹窗
        if (props.dialogType === 1 || props.dialogType === 0 || props.dialogType === 2) {
          handleCancel();
        }
      } else {
        message.error(data.msg || '出错了');
        notification.close('upload');
        list.forEach(item => {
          uploadFileList.value[item.order].status = 'error';
          uploadFileList.value[item.order].errorText = data?.msg || common.upFailed;
        });
      }
    })
    .catch(e => {
      console.error('文件上传错误:', e);
      message.error(e.message || e.msg || '上传失败');
      notification.close('upload');
    })
    .finally(() => {
      if (props.dialogType === 2) {
        getTempDetail();
      } else {
        getDetails();
      }
    });
};

// 0 上传中，1 上传成功,
const openNotification = (type: 0 | 1) => {
  notification[type ? 'success' : 'info']({
    key: 'upload',
    message: type ? '上传完成' : '上传中',
    description: type ? '' : '最多需要30s',
    duration: type ? 2.5 : 0,
  });
};

const handleOk = async () => {
  setModalVisible(false);
  setDefault(pageStatus.optionlist);
  await getDetails();
};

const handleCancel = () => {
  setModalVisible(false);
};

onBeforeUnmount(() => {
  if (timer.value) {
    clearTimeout(timer.value);
  }
});
</script>
<style lang="scss" scoped>
.file {
  margin-top: 16px;
  display: flex;

  .box {
    flex: 1;
    height: 248px;
    border-radius: 6px;
    background: #f9f9fc;
    box-sizing: border-box;
    border: 1px dashed #ededed;
  }
}

.line-url {
  margin-top: 16px;
  height: 100px;
  display: flex;
  overflow: auto;

  .mt9 {
    margin-top: 9px;
  }

  :deep(.ant-input) {
    height: 30px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 12px;
  }
}

.label {
  display: block;
  width: 82px;
  min-width: 82px;
  text-align: right;
  margin-right: 16px;
  color: $title1;

  .red {
    color: red;
  }
}

.before-upload-box {
  position: relative;
  width: 100%;
  height: 100%;

  &.uploading {
    height: 62px;
    border-bottom: 1px solid #ededed;
  }

  .hide {
    opacity: 0;
  }

  .input {
    position: absolute;
    width: 100%;
    height: 100%;
    z-index: 100;
  }

  .before-upload {
    width: 100%;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }

  .upload-text-box {
    display: flex;
    align-items: center;
    justify-content: center;

    svg {
      width: 16px;
      height: 16px;
      margin-right: 4px;
      cursor: pointer;
    }

    .upload-text {
      font-weight: 500;
      font-size: 14px;
      color: $title1;
    }

    .blue {
      color: $baseColor;
      cursor: pointer;
    }
  }

  .desc {
    color: $title3;
    text-align: center;
    margin-top: 8px;
    padding: 0 20px;
  }
}

.upload-box {
  &.upload-list {
    height: 188px;
  }

  .list {
    height: 188px;

    overflow: auto;

    li {
      display: flex;
      align-items: center;
      justify-content: space-around;
      height: 22px;
      margin-bottom: 20px;
      padding: 0 20px 0 16px;

      &:first-child {
        margin-top: 20px;
      }

      svg {
        width: 16px;
        height: 16px;
        margin-right: 4px;
      }

      .name {
        flex: 1;
        width: 0;
        margin-right: 20px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .status-box {
        display: flex;
        width: auto;
        align-items: center;
        justify-content: start;
        margin-right: 5px;

        .loading {
          width: 16px;
          height: 16px;
          margin-right: 4px;
          animation: 2s linear infinite loading;
        }

        .status {
          width: 60px;
          font-size: 14px;
          line-height: 22px;
          height: 22px;
          color: $title1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .delete {
        line-height: 22px;
        color: $title2;
        cursor: pointer;
      }
    }
  }

  .note {
    font-family: PingFang SC;
    font-size: 12px;
    font-weight: normal;
    margin-top: 12px;
    color: #999999;
    width: 330px;
  }
}

:deep(.ant-input) {
  height: 40px;
}

.upload-btn {
  background: $baseColor !important;
}
</style>
<style lang="scss">
@keyframes loading {
  0% {
    transform: rotate(0deg);
  }

  50% {
    transform: rotate(180deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
