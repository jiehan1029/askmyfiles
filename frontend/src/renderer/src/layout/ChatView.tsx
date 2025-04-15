import { ChatMessageList } from '../shared/components/ui/chat/chat-message-list'
import { ChatBubble, ChatBubbleMessage, ChatBubbleAvatar } from '@renderer/shared/components/ui/chat/chat-bubble'
import { ChatInput } from '@renderer/shared/components/ui/chat/chat-input'
import { Button } from '@renderer/shared/components/ui/button'
import { CornerDownLeft } from 'lucide-react';
import RobotLogo from '@renderer/assets/logo.png'
import FacePic from '@renderer/assets/face_2.png'
import useChatStore from '@renderer/store/chatStore'
import useChatHistoryStore from '@renderer/store/chatHistoryStore';
import { useState, useEffect } from "react"


export function AppChatView() {
    const chatStore = useChatStore()
    const chatHistoryStore = useChatHistoryStore()
    const { socketIsConnected, socketError, messageInflight } = chatStore
    const [message, setMessage] = useState<string>("")
    const [chatHistoryUpdated, setChatHistoryUpdated] = useState<boolean>(false)

    useEffect(() => {
        chatStore.connectSocket()
        return () => chatStore.disconnectSocket()
    }, [])

    useEffect(()=>{
        setChatHistoryUpdated(false)
    }, [chatStore.conversationId])

    useEffect(()=>{
        if(!chatHistoryUpdated && chatStore.messageList.length >= 2){
            chatHistoryStore.getChatHistory().then(()=>{
                setChatHistoryUpdated(true)
            })
        }
    }, [chatStore.messageList.length])

    const onChangeInput = (e) => {
        setMessage(e.target.value)
    }

    const onClickSendMessage = (e)=>{
        e.preventDefault(); // prevent page reload
        setMessage("")
        if(message){
            chatStore.sendMessage(message)
        }
    }

    const onKeyDownSendMessage = (e) => {
        if(message && socketIsConnected){
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault() // prevent newline + prevent form submit
                onClickSendMessage(e)
            }
        }
    }

    return <>
        <ChatMessageList className="overflow-scroll pb-[120px]">
            {socketIsConnected
            ? (
                <ChatBubble variant='received'>
                    <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                    <ChatBubbleMessage variant='received'>
                        Hi, what can I help you today?
                    </ChatBubbleMessage>
                </ChatBubble>)
            : socketError 
                ? (
                    <ChatBubble variant='received'>
                        <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                        <ChatBubbleMessage variant='received'>
                            Sorry, I am not able to reaching the server.
                        </ChatBubbleMessage>
                    </ChatBubble>)
                : (
                    <ChatBubble variant='received'>
                        <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                        <ChatBubbleMessage variant='received'>
                            Connecting...
                        </ChatBubbleMessage>
                    </ChatBubble>)
            }
            {
                chatStore.messageList.map((msgObj, idx) => {
                    const variantStr = msgObj.from === "US" ? 'sent' : 'received'
                    const avatarStr = msgObj.from === "US" ? FacePic : RobotLogo
                    return (
                        <ChatBubble variant={variantStr} key={idx}>
                            <ChatBubbleAvatar src={avatarStr} fallback={msgObj.from} />
                            <ChatBubbleMessage variant={variantStr}>
                                {msgObj.text}
                            </ChatBubbleMessage>
                        </ChatBubble>
                    )
                })
            }
            { messageInflight && <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage isLoading />
            </ChatBubble>}
        </ChatMessageList>

        <form
            className="sticky bottom-0 rounded-lg border bg-background focus-within:ring-1 focus-within:ring-ring p-1"
        >
            <ChatInput
                placeholder="Type your message here..."
                className="min-h-12 resize-none rounded-lg bg-background border-0 p-3 shadow-none focus-visible:ring-0"
                onChange={onChangeInput}
                value={message}
                onKeyDown={onKeyDownSendMessage}
            />

            <div className="flex justify-end p-3 pt-0">
                <Button
                    size="sm"
                    disabled={!message || !socketIsConnected}
                    onClick={onClickSendMessage}
                >
                    Send Message
                    <CornerDownLeft className="size-3.5" />
                </Button>
            </div>
        </form>
    </>
}


export default AppChatView