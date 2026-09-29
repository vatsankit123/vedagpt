import { lazy } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
const ChatPage = lazy(() => import('@/pages/ChatPage').then((m) => ({ default: m.ChatPage })))
const AboutPage = lazy(() => import('@/pages/AboutPage').then((m) => ({ default: m.AboutPage })))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })))
export const router = createBrowserRouter([
  { element: <AppShell />, errorElement: <ErrorBoundary />, children: [
    { index: true, element: <ChatPage /> },
    { path: 'about', element: <AboutPage /> },
    { path: '*', element: <NotFoundPage /> },
  ]},
])
