<template>
    <div class="knowledge-list">
        <div class="logo">NovAnything</div>

        <!-- 骨架屏 -->
        <template v-if="!Array.isArray(knowledgeBaseList)">
            <arco-skeleton animation>
                <arco-skeleton-line :rows="8" />
            </arco-skeleton>
        </template>

        <!-- 正常内容 -->
        <template v-else>
            <arco-collapse :default-active-key="['team', 'personal']">
                <!-- 团队知识库 -->
                <arco-collapse-item key="team">
                    <template #header>
                        <div class="collapse-header">
                            <span>团队知识库</span>
                        </div>
                    </template>
                    <div class="knowledge-group">
                        <div v-for="(item, index) in teamKnowledgeList" :key="index"
                            :class="['knowledge-item', { 'item-active': selectList.includes(item?.kb_id) }]"
                            @click="selectKnowledgeBase(item)">
                            <img class="item-icon" 
                                :src="selectList.includes(item?.kb_id) ? menuActiveImg : menuDefaultImg" 
                                alt="文件夹"
                                :class="{ 'icon-active': selectList.includes(item?.kb_id) }" />
                            <span class="item-name" :class="{ 'text-active': selectList.includes(item?.kb_id) }">
                                {{ item?.kb_name || '未命名知识库' }}
                            </span>
                        </div>
                        <div v-if="teamKnowledgeList.length === 0" class="empty-tip">暂无团队知识库</div>
                    </div>
                </arco-collapse-item>

                <!-- 个人知识库 -->
                <arco-collapse-item key="personal">
                    <template #header>
                        <div class="collapse-header">
                            <span>个人知识库</span>
                        </div>
                    </template>
                    <div class="knowledge-group">
                        <div v-for="(item, index) in personalKnowledgeList" :key="index"
                            :class="['knowledge-item', { 'item-active': selectList.includes(item?.kb_id) }]"
                            @click="selectKnowledgeBase(item)">
                            <img class="item-icon" 
                                :src="selectList.includes(item?.kb_id) ? menuActiveImg : menuDefaultImg" 
                                alt="文件夹"
                                :class="{ 'icon-active': selectList.includes(item?.kb_id) }" />
                            <span class="item-name" :class="{ 'text-active': selectList.includes(item?.kb_id) }">
                                {{ item?.kb_name || '未命名知识库' }}
                            </span>
                        </div>
                        <div v-if="personalKnowledgeList.length === 0" class="empty-tip">暂无个人知识库</div>
                    </div>
                </arco-collapse-item>
            </arco-collapse>
        </template>
    </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { IKnowledgeItem } from '@/utils/types';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import { storeToRefs } from 'pinia';

// 导入图片资源
import menuActiveImg from '../assets/home/menu-active.png';
import menuDefaultImg from '../assets/home/menu-default.png';

const { setCurrentId } = useKnowledgeBase();
const { selectList, currentId } = storeToRefs(useKnowledgeBase());
const { knowledgeBaseList = [], getList }: any = storeToRefs(useKnowledgeBase());

console.log(knowledgeBaseList)

onMounted(async () => {
    //   await getList();
});

// 分离团队和个人知识库
const teamKnowledgeList = computed(() => {
    return knowledgeBaseList.value.filter(item => item.kb_type === 'team')
});

const personalKnowledgeList = computed(() => {
    return knowledgeBaseList.value.filter(item => item.kb_type === 'personal')
});

// 选择知识库
const selectKnowledgeBase = (item: IKnowledgeItem) => {
    const id = item.kb_id;

    // 设置当前选中的知识库ID
    setCurrentId(id);

    if (selectList.value.includes(id)) {
        const index = selectList.value.findIndex(Iitem => Iitem === id);
        if (index !== -1) {
            selectList.value.splice(index, 1);
        }
    } else {
        selectList.value.push(id);
    }
};
</script>

<style lang="scss" scoped>
.logo {
    cursor: pointer;
    display: flex;
    background: linear-gradient(79deg, #0256FF 0%, #5602FF 100%);
    color: transparent;
    background-clip: text;
    font-size: 22px;
    font-weight: 700;
    padding-left: 24px;
    padding-top: 24px;
    padding-bottom: 24px;
}



.knowledge-list {
    border-right: 1px solid #D8D8D8;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #fff;
    padding: 0 8px;
    box-sizing: border-box;
    overflow-x: hidden;
}

:deep(.arco-collapse) {
    padding: 0px 24px;
    border: none;
    background-color: transparent;
    width: 100%;
    box-sizing: border-box;
}

:deep(.arco-collapse-item) {
    border: none;

    .arco-collapse-item-content {
        padding: 0;
        background-color: transparent;
    }

    .knowledge-item {
        margin-bottom: 12px;
        padding: 6px 12px;
    }

    .arco-collapse-item-header {
        border: none;
        padding-left: 16px;
    }

    .arco-icon-hover {
        left: 0;
    }

    // .arco-collapse-item-header {
    //     border: none;
    //     padding: 8px 0;
    //     display: flex;
    //     align-items: center;

    //     .arco-collapse-item-header-title {
    //         flex: 1;
    //     }

    //     .arco-collapse-item-header-icon {
    //         margin-right: 8px;
    //     }
    // }

    // .arco-collapse-item-content-box {
    //     padding: 0;
    // }
}

.collapse-header {
    display: flex;
    align-items: center;
    font-weight: 400;
    font-size: 16px;
    padding-left: 8px;
    color: $mainFontColor;
}

.knowledge-group {
    padding: 0 0 8px 0;
}

.knowledge-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    margin: 2px 0;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.3s ease;
    width: 100%;
    box-sizing: border-box;

    &:hover {
        background-color: #E0EAFF;

    }

    .item-icon {
        width: 32px;
        height: 32px;
        margin-right: 8px;
        opacity: 0.6;
    }

    .item-name {
        flex: 1;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: #4e5969;
        min-width: 0;
    }

    .icon-active {
        opacity: 1;
    }

    .text-active {
        color: #0256FF;
        font-weight: 500;
    }
}

.item-active {
    background-color: #E0EAFF;
}

.empty-tip {
    padding: 8px 12px;
    color: #86909c;
    font-size: 14px;
    text-align: center;
}
</style>