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
import { useEffect, useState } from "react"
import useSettingsStore from './store/settingsStore'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from "@renderer/shared/components/ui/alert-dialog"


function App(): JSX.Element {
  const [alertOpen, setAlertOpen] = useState<boolean>(false)
  const chatStore = useChatStore()
  const settingStore = useSettingsStore()

  useEffect(()=>{
    settingStore.fetchSettings()
  }, [])

  useEffect(()=>{
    if(settingStore.settingsLoaded){
      if(!settingStore.llmProvider){
        setAlertOpen(true)
      }else if(!settingStore.llmModel){
        setAlertOpen(true)
      } else if(!settingStore.llmApiToken && (settingStore.llmProvider !== "ollama")){
        setAlertOpen(true)
      } else {
        setAlertOpen(false)
      }
    }
  }, [settingStore.settingsLoaded])

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

      <AlertDialog open={alertOpen} onOpenChange={setAlertOpen}>
        <AlertDialogContent className="bg-background text-foreground">
          <AlertDialogHeader>
            <AlertDialogTitle>Finish setting up the app</AlertDialogTitle>
            <AlertDialogDescription>
            To get started, complete the app settings. Click the gear icon in the left sidebar to configure it.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogAction onClick={()=>setAlertOpen(false)}>Got it</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}

export default App
