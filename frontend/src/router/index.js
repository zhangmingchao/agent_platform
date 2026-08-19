import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../components/Layout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'agents',
        name: 'AgentList',
        component: () => import('../views/agents/AgentList.vue'),
        meta: { title: 'Agent 管理' }
      },
      {
        path: 'agents/new',
        name: 'AgentCreate',
        component: () => import('../views/agents/AgentForm.vue'),
        meta: { title: '创建 Agent' }
      },
      {
        path: 'agents/:id/edit',
        name: 'AgentEdit',
        component: () => import('../views/agents/AgentForm.vue'),
        meta: { title: '编辑 Agent' }
      },
      {
        path: 'agents/:id/chat',
        name: 'AgentChat',
        component: () => import('../views/chat/Chat.vue'),
        meta: { title: '对话' }
      },
      {
        path: 'workflows',
        name: 'WorkflowList',
        component: () => import('../views/workflows/WorkflowList.vue'),
        meta: { title: '多 Agent 工作流' }
      },
      {
        path: 'workflows/new',
        name: 'WorkflowCreate',
        component: () => import('../views/workflows/WorkflowForm.vue'),
        meta: { title: '创建工作流' }
      },
      {
        path: 'workflows/:id/edit',
        name: 'WorkflowEdit',
        component: () => import('../views/workflows/WorkflowForm.vue'),
        meta: { title: '编辑工作流' }
      },
      {
        path: 'workflows/:id/run',
        name: 'WorkflowRun',
        component: () => import('../views/workflows/WorkflowRun.vue'),
        meta: { title: '运行工作流' }
      },
      {
        path: 'skills',
        name: 'SkillList',
        component: () => import('../views/skills/SkillList.vue'),
        meta: { title: 'Skill 管理' }
      },
      {
        path: 'mcps',
        name: 'McpList',
        component: () => import('../views/mcps/McpList.vue'),
        meta: { title: 'MCP 配置' }
      },
      {
        path: 'models',
        name: 'ModelList',
        component: () => import('../views/models/ModelList.vue'),
        meta: { title: '模型管理' }
      },
      {
        path: 'traces',
        name: 'TraceList',
        component: () => import('../views/traces/TraceList.vue'),
        meta: { title: 'Trace 调用链' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/')
  } else {
    next()
  }
})

export default router
