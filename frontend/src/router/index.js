// 路由表负责建立“浏览器 URL → Vue 页面组件”的映射。
import {createRouter, createWebHistory} from 'vue-router'

// 每一项是一个可访问页面；component 使用动态 import，实现按页面懒加载。
const routes = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/Login.vue'),
        // 登录页是唯一明确允许未登录访问的页面。
        meta: {requiresAuth: false}
    },
    {
        path: '/register',
        name: 'Register',
        component: () => import('../views/Register.vue'),
        meta: {requiresAuth: false}
    },
    {
        path: '/',
        // Layout 是登录后页面的共同外壳，包含侧边栏、顶部栏和子页面插槽。
        component: () => import('../components/Layout.vue'),
        meta: {requiresAuth: true},
        redirect: '/dashboard',
        // children 会渲染到 Layout.vue 里的 <router-view />。
        children: [
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('../views/Dashboard.vue'),
                meta: {title: '仪表盘'}
            },
            {
                path: 'agents',
                name: 'AgentList',
                component: () => import('../views/agents/AgentList.vue'),
                meta: {title: 'Agent 管理'}
            },
            {
                path: 'agents/new',
                name: 'AgentCreate',
                component: () => import('../views/agents/AgentForm.vue'),
                meta: {title: '创建 Agent'}
            },
            {
                // :id 是动态参数，例如 /agents/12/edit 中 route.params.id === '12'。
                path: 'agents/:id/edit',
                name: 'AgentEdit',
                component: () => import('../views/agents/AgentForm.vue'),
                meta: {title: '编辑 Agent'}
            },
            {
                path: 'crews',
                name: 'CrewList',
                component: () => import('../views/crews/CrewList.vue'),
                meta: {title: 'Crew 管理'}
            },
            {
                path: 'crews/new',
                name: 'CrewCreate',
                component: () => import('../views/crews/CrewForm.vue'),
                meta: {title: '创建 Crew'}
            },
            {
                path: 'crews/:id/edit',
                name: 'CrewEdit',
                component: () => import('../views/crews/CrewForm.vue'),
                meta: {title: '编辑 Crew'}
            },
            {
                path: 'crews/:id/chat',
                name: 'CrewChat',
                component: () => import('../views/chat/Chat.vue'),
                meta: {title: 'Crew 对话', targetType: 'crew'}
            },
            {
                path: 'flows',
                name: 'FlowList',
                component: () => import('../views/flows/FlowList.vue'),
                meta: {title: 'Flow 编排'}
            },
            {
                path: 'flows/new',
                name: 'FlowCreate',
                component: () => import('../views/flows/FlowForm.vue'),
                meta: {title: '创建 Flow'}
            },
            {
                path: 'flows/:id/edit',
                name: 'FlowEdit',
                component: () => import('../views/flows/FlowForm.vue'),
                meta: {title: '编辑 Flow'}
            },
            {
                path: 'flows/:id/chat',
                name: 'FlowChat',
                component: () => import('../views/chat/Chat.vue'),
                meta: {title: 'Flow 对话', targetType: 'flow'}
            },
            {
                path: 'skills',
                name: 'SkillList',
                component: () => import('../views/skills/SkillList.vue'),
                meta: {title: 'Skill 管理'}
            },
            {
                path: 'mcps',
                name: 'McpList',
                component: () => import('../views/mcps/McpList.vue'),
                meta: {title: 'MCP 配置'}
            },
            {
                path: 'traces',
                name: 'TraceList',
                component: () => import('../views/traces/TraceList.vue'),
                meta: {title: 'Trace 调用链'}
            }
        ]
    }
]

// HTML5 history 模式会让 URL 更干净，不显示 # 号。
const router = createRouter({
    history: createWebHistory(),
    routes
})

// 全局前置守卫：每次切换路由前检查登录状态。
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    if (to.meta.requiresAuth !== false && !token) {
        // 目标页面需要登录、但本地没有 token：跳到登录页。
        next('/login')
    } else if (to.path === '/login' && token) {
        // 已登录用户再次访问登录页，直接回到系统首页。
        next('/')
    } else {
        next()
    }
})

export default router
