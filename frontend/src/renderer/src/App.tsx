import AppSideView from './layout/SideView'
import AppChatView from './layout/ChatView'
import AppHeader from './layout/Header'
import AppFooter from './layout/Footer'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./shared/components/ui/tooltip"
import { Button } from '@renderer/shared/components/ui/button'
import { SquarePen, RefreshCw } from 'lucide-react'
import { Separator } from "@renderer/shared/components/ui/separator"
import useChatStore from './store/chatStore'
import { Toaster } from '@renderer/shared/components/ui/sonner'
import { toast } from "sonner"


function App(): JSX.Element {
  const chatStore = useChatStore()

  const onClickNewChat = ()=>{
    toast("You started a new conversation!")
    chatStore.startNewConversation()
  }

  const onClickReconnectChat = ()=>{
    toast("Reconnect to chat server...")
    chatStore.connectSocket()
  }

  return (
    <>
      <AppHeader/>
      <main className='flex flex-initial flex-row bg-background text-foreground'>
        <section className='h-[calc(100vh-126px)] pl-1 pr-1 pt-4 bg-slate-100 w-[44px]'>
          <AppSideView />
          <Separator style={{marginTop: '16px', marginBottom: '16px'}} />
          <TooltipProvider>
            <Tooltip>
                <TooltipTrigger>
                    <Button variant="outline" size="icon" onClick={onClickNewChat}><SquarePen /></Button>
                </TooltipTrigger>
                <TooltipContent side="right"><p>New Chat</p></TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <TooltipProvider>
            <Tooltip>
                <TooltipTrigger className="pt-1 pb-1">
                    <Button variant="outline" size="icon" onClick={onClickReconnectChat}><RefreshCw /></Button>
                </TooltipTrigger>
                <TooltipContent side="right"><p>Reconnect Chat</p></TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </section>
        <section className='relative h-[calc(100vh-126px)] pt-1 pb-2 pl-4 pr-4 flex flex-col w-[calc(100vw-44px)] overflow-hidden'>
          <AppChatView />
        </section>
      </main>
      <Toaster position="top-right"/>
      <AppFooter />
    </>
  )
}

export default App
