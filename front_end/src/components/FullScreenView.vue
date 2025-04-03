<template>
    <div class="fullscreen-view" :class="{ 'closing': isClosing }">
        <arco-layout>
            <arco-layout-header>
                <div class="bac">
                    <div class="logo">NovAnything</div>

                    <div class="back-button" @click="goBack">
                        <icon-close class="icon-left" />
                    </div>
                </div>
                <div class="fullscreen-content">
                </div>
            </arco-layout-header>
            <arco-layout>
                <arco-layout-sider width=240>
                    <FullScreenSider />
                </arco-layout-sider>
                <arco-layout-content>
                    <router-view />
                </arco-layout-content>
            </arco-layout>
        </arco-layout>

    </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { IconClose } from '@arco-design/web-vue/es/icon';
import FullScreenSider from '@/components/FullScreenSider.vue';
import { useRoute, useRouter } from 'vue-router';
import routeController from '@/controller/router';

const route = useRoute();
const router = useRouter();
const { changePage } = routeController();
const isClosing = ref(false);

function getPageTitle() {
    const path = route.path;
    if (path.includes('/knowledge')) {
        return '知识库管理';
    }
    return '全屏视图';
}

function goBack() {
    isClosing.value = true;
    setTimeout(() => {
        router.push('/');
    }, 200);
}
</script>

<style lang="scss" scoped>
.fullscreen-view {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: #fff;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    animation: slide-in 0.4s cubic-bezier(0.25, 0.1, 0.25, 1);
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}

.fullscreen-view.closing {
    animation: slide-out 0.4s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
}

.bac {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid #D8D8D8;
    color: #fff;
    transition: all 0.3s ease;
}

.back-button {
    display: flex;
    align-items: center;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.2s ease;
    font-size: 20px;
    color: #4E5969;

    &:hover {
        color: $baseColor;
    }
}

.title {
    font-size: 18px;
    font-weight: 500;
    opacity: 0;
    animation: fade-in 0.3s ease 0.2s forwards;
}

@keyframes slide-in {
    from {
        transform: translateY(100%);
        opacity: 0.5;
    }

    70% {
        transform: translateY(-2%);
        opacity: 1;
    }

    to {
        transform: translateY(0);
        opacity: 1;
    }
}

@keyframes slide-out {
    from {
        transform: translateY(0);
        opacity: 1;
    }

    to {
        transform: translateY(100%);
        opacity: 0;
    }
}

@keyframes fade-in {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
    opacity: 0;
    transform: translateY(20px);
}

.fade-leave-to {
    opacity: 0;
    transform: translateY(-20px);
}

.logo {
    cursor: pointer;
    background-image: linear-gradient(to right, #3b82f6, #4f46e5);
    color: transparent;
    background-clip: text;
    font-size: 22px;
    font-weight: 700;
}
</style>