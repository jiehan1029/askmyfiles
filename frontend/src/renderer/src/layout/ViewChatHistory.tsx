import { Separator } from "@renderer/shared/components/ui/separator"
import { useEffect, useState } from 'react'
import useChatHistoryStore from "@renderer/store/chatHistoryStore"
import useChatStore from "@renderer/store/chatStore"
import { Skeleton } from "@renderer/shared/components/ui/skeleton"
import {
    Breadcrumb,
    BreadcrumbEllipsis,
    BreadcrumbItem
} from "@renderer/shared/components/ui/breadcrumb"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@renderer/shared/components/ui/dropdown-menu"
import { toast } from "sonner"
import useSettingsStore from "@renderer/store/settingsStore"


export function ChatHistoryView({ closeSideView }) {
    const chatHistoryStore = useChatHistoryStore()
    const chatStore = useChatStore()
    const settingsStore = useSettingsStore()

    const { timezone: ssTimezone, locale: ssLocale } = settingsStore

    const [locale, setLocale] = useState<string>(ssLocale)
    const [timezone, setTimezone] = useState<string>(ssTimezone)

    useEffect(()=>{
        if(!chatHistoryStore.chatHistoryLoaded){
            chatHistoryStore.getChatHistory()
        }
        if(!settingsStore.settingsLoaded){
            settingsStore.fetchSettings()
        }
        console.log("use locale and timezone: ", locale, timezone)
    }, [])

    useEffect(()=>{
        if(settingsStore.settingsLoaded){
            setLocale(ssLocale)
            setTimezone(ssTimezone)
        }
    }, [settingsStore.settingsLoaded])

    const onClickDeleteConversation = (conversationId: string)=>{
        chatHistoryStore.deleteChatHistory(conversationId)
    }

    const onClickContinueConversation = async (conversationId: string)=>{
        await chatStore.getConversationMessages(conversationId)
        closeSideView()
        toast("Continue your conversation with AI assistant!")
    }

    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <p className="text-sm">View or continue on past conversations.</p>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            {chatHistoryStore.chatHistoryInflight && (
                <>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
                <div style={{ marginTop: '12px'}}>
                    <Skeleton className="h-4 w-[calc(100%-32px)]" style={{ marginBottom: '8px'}} />
                    <Skeleton className="h-4 w-[calc(60%)]" />
                </div>
                </>
            )}
            {!chatHistoryStore.chatHistoryInflight && chatHistoryStore.chatHistory.map((chatRec)=>(
                <div key={chatRec.conversation_id} className="hover:bg-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)] flex flex-row justify-between items-start" style={{ marginTop: '12px'}}>
                    <div>
                        <div className="text-sm italic">{new Date(chatRec.created_at).toLocaleString(locale, {timeZone: timezone})}</div>
                        <div className="text-md h-[26px] overflow-y-hidden overflow-x-clip">{chatRec.summary}</div>
                    </div>
                    <Breadcrumb>
                        <BreadcrumbItem>
                        <DropdownMenu>
                            <DropdownMenuTrigger className="flex items-center gap-1">
                            <BreadcrumbEllipsis className="h-4 w-4 cursor-pointer" />
                            <span className="sr-only">Toggle menu</span>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start">
                            <DropdownMenuItem onSelect={()=>onClickContinueConversation(chatRec.conversation_id)}>Continue</DropdownMenuItem>
                            <DropdownMenuItem className="text-rose-500" onSelect={()=>onClickDeleteConversation(chatRec.conversation_id)}>Delete</DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                        </BreadcrumbItem>
                    </Breadcrumb>
                </div>
            ))}
        </div>
    </>
}


export default ChatHistoryView