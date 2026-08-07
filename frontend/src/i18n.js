import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import enUS from './locales/en-US'

const savedLocale = localStorage.getItem('locale')
const browserLocale = navigator.language === 'en-US' ? 'en-US' : 'zh-CN'

const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: savedLocale || browserLocale,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS
  }
})

export default i18n
