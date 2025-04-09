<template>
    <div class="temp-file-container" v-if="tempDetail && tempDetail.length > 0">
        <div class="temp-file-item" v-for="(item, index) in tempDetail" :key="index">
            <div v-if="item.status !== 'green' && item.status !== 'red'" class="temp-file-loading-container">
                <icon-loading class="temp-file-loading" />
            </div>
            <div class="temp-file-item-icon">
                <icon-file />
            </div>
            <div class="temp-file-item-name" :class="getStatusClass(item.status)">{{ item.fileIdName }}</div>
            <div class="temp-file-delete" @click="handleDeleteFile(item)">
                <icon-close />
            </div>
        </div>
    </div>
</template>

<script lang="ts" setup>
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { useOptiionList } from '@/store/useOptiionList';
import { IconFile, IconLoading, IconClose } from '@arco-design/web-vue/es/icon';
import { Message } from '@arco-design/web-vue';
import urlResquest from '@/services/urlConfig';
import { storeToRefs } from 'pinia';
import { ref, onUnmounted } from 'vue';

const { tempId } = storeToRefs(useKnowledgeBase());
const { tempDetail } = storeToRefs(useOptiionList());
const pollingTimer = ref<any>(null);
const POLLING_INTERVAL = 5000; // 5秒轮询一次

const fetchFileList = async () => {
    if (!tempId.value) return;
    
    try {
        const res = await urlResquest.fileList({ kb_id: tempId.value });
        tempDetail.value = res.data.details.map(item => ({
            fileId: item.file_id,
            fileIdName: item.file_name,
            status: item.status.toLowerCase()
        }));
        
        // 检查是否所有文件都已经是最终状态(green或red)
        const hasProcessingFiles = tempDetail.value?.some(
            file => file.status !== 'green' && file.status !== 'red'
        );
        
        // 如果还有处理中的文件，继续轮询；否则清除定时器
        if (hasProcessingFiles) {
            startPolling();
        } else if (pollingTimer.value) {
            clearTimeout(pollingTimer.value);
            pollingTimer.value = null;
        }
    } catch (error) {
        Message.error('临时文件列表失败');
        if (pollingTimer.value) {
            clearTimeout(pollingTimer.value);
            pollingTimer.value = null;
        }
    }
};

const startPolling = () => {
    // 清除现有的计时器，防止重复
    if (pollingTimer.value) {
        clearTimeout(pollingTimer.value);
    }
    
    // 设置新的计时器
    pollingTimer.value = setTimeout(fetchFileList, POLLING_INTERVAL);
};

onMounted(async () => {
    await fetchFileList();
});

onUnmounted(() => {
    // 组件卸载时清理定时函数
    if (pollingTimer.value) {
        clearTimeout(pollingTimer.value);
        pollingTimer.value = null;
    }
});

const handleDeleteFile = async (item: any) => {
    try {
        await urlResquest.deleteFile({ file_ids: [item.fileId], kb_id: tempId.value });
        Message.success('文件删除成功');
        // 从列表中移除已删除的文件
        if (tempDetail.value) {
            tempDetail.value = tempDetail.value.filter(file => file.fileId !== item.fileId);
        }
    } catch (error) {
        Message.error('删除文件失败');
        console.error('删除文件出错:', error);
    }
};

const getStatusClass = (status: string): string => {
    if (!status) return '';

    if (status.toLowerCase() === 'green' ||
        status.toLowerCase() === '成功' ||
        status.toLowerCase() === 'success') {
        return 'status-green';
    } else if (status.toLowerCase() === 'yellow' ||
        status.toLowerCase() === '处理中' ||
        status.toLowerCase() === 'processing') {
        return 'status-yellow';
    } else if (status.toLowerCase() === 'red' ||
        status.toLowerCase() === '失败' ||
        status.toLowerCase() === 'failed') {
        return 'status-red';
    } else if (status.toLowerCase() === 'blue' ||
        status.toLowerCase() === '等待中' ||
        status.toLowerCase() === 'waiting') {
        return 'status-blue';
    }

    return '';
};
</script>

<style lang="scss" scoped>
.temp-file-container {
    display: flex;
    gap: 44px;
    margin: 16px 36px;

    .temp-file-item {
        position: relative;

        .temp-file-loading-container {
            position: absolute;
            top: 0;
            left: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;

            .temp-file-loading {
                font-size: 18px;
                color: #666666;
            }
        }

        .temp-file-item-icon {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;

            :deep(.arco-icon) {
                font-size: 44px;
                color: #666666;
            }
        }

        .temp-file-item-name {
            max-width: 120px;
            text-align: center;
            margin-top: 8px;
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;

            &.status-green {
                color: #00B42A;
            }

            &.status-yellow {
                color: #FF7D00;
            }

            &.status-red {
                color: #F53F3F;
            }

            &.status-blue {
                color: #165DFF;
            }
        }
        
        .temp-file-delete {
            position: absolute;
            top: -8px;
            right: -8px;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background-color: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.3s;
            
            :deep(.arco-icon) {
                font-size: 14px;
                color: white;
            }
        }
        
        &:hover {
            .temp-file-delete {
                opacity: 1;
            }
        }
    }
}
</style>