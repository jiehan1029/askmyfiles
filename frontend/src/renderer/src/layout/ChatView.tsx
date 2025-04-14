import { ChatMessageList } from '../shared/components/ui/chat/chat-message-list'
import { ChatBubble, ChatBubbleMessage, ChatBubbleAvatar } from '@renderer/shared/components/ui/chat/chat-bubble'
import { ChatInput } from '@renderer/shared/components/ui/chat/chat-input'
import { Button } from '@renderer/shared/components/ui/button'
import { CornerDownLeft } from 'lucide-react';
import RobotLogo from '@renderer/assets/logo.png'
import FacePic from '@renderer/assets/face_2.png'
import useChatStore from '@renderer/store/chatStore'
import { useState, useEffect, useRef } from "react"


export function AppChatView() {
    const chatStore = useChatStore()
    const [wsConnected, setWsConnected] = useState<boolean>(false)
    const [wsError, setWsError] = useState<boolean>(false)
    const [message, setMessage] = useState<string>("")
    const [answerInflight, setAnswerInflight] = useState<boolean>(false)
    
    const socket = useRef<WebSocket | null>(null);

    useEffect(() => {
        socket.current = new WebSocket(`${import.meta.env.VITE_APP_WS_BASE_URL}/ws/chat`)
        socket.current.onopen = () => {
            console.log(" WebSocket connection opened");
            setWsConnected(true)
        }
        socket.current.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log("Chat answer:", data)
            if(data.status === "complete"){
                setAnswerInflight(false)
                chatStore.addMessageToList(data.answer, "AI")
            }else if(data.status === "error"){
                setAnswerInflight(false)
                chatStore.addMessageToList(data.error, "AI")
            }
        }
        socket.current.onclose = (event) => {
            console.log("WebSocket connection closed:", event.code, event.reason)
            setWsConnected(false)
        }
    
        socket.current.onerror = (error) => {
            console.error("WebSocket error:", error)
            setWsError(true)
            setWsConnected(false)
        }
        
        return () => socket.current?.close();
    }, [])


    const onChangeInput = (e) => {
        setMessage(e.target.value)
    }

    const onClickSendMessage = (e)=>{
        e.preventDefault(); // prevent page reload
        setMessage("")
        if(message){
            setAnswerInflight(true)
            chatStore.addMessageToList(message, "US")
            const payload = {
                question: message,
                history_limit: 10 // only include last 10 turns (Q+A pairs)
            }
            if(chatStore.conversationId){
                payload["conversation_id"] = chatStore.conversationId
            }
            socket.current?.send(JSON.stringify(payload))
        }
    }

    const onKeyDownSendMessage = (e) => {
        if(message && wsConnected){
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault() // prevent newline + prevent form submit
                onClickSendMessage(e)
            }
        }
    }

    return <>
        <ChatMessageList className="overflow-scroll pb-[120px]">
            {wsConnected
            ? (
                <ChatBubble variant='received'>
                    <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                    <ChatBubbleMessage variant='received'>
                        Hi, what can I help you today?
                    </ChatBubbleMessage>
                </ChatBubble>)
            : wsError 
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
            { answerInflight && <ChatBubble variant='received'>
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
                    disabled={!message || !wsConnected}
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