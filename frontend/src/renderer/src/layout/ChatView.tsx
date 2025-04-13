import { ChatMessageList } from '../shared/components/ui/chat/chat-message-list'
import { ChatBubble, ChatBubbleMessage, ChatBubbleAvatar } from '@renderer/shared/components/ui/chat/chat-bubble'
import { ChatInput } from '@renderer/shared/components/ui/chat/chat-input'
import { Button } from '@renderer/shared/components/ui/button'
import { CornerDownLeft } from 'lucide-react';
import RobotLogo from '@renderer/assets/logo.png'
import FacePic from '@renderer/assets/face_2.png'

export function AppChatView() {
    return <>
        <ChatMessageList className="overflow-scroll pb-[120px]">
            <ChatBubble variant='sent'>
                <ChatBubbleAvatar src={FacePic} fallback='US' />
                <ChatBubbleMessage variant='sent'>
                Hello, how has your day been? I hope you are doing well.
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage variant='received'>
                Hi, I am doing well, thank you for asking. How can I help you today?
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='sent'>
                <ChatBubbleAvatar src={FacePic} fallback='US' />
                <ChatBubbleMessage variant='sent'>
                Hello, how has your day been? I hope you are doing well.
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='sent'>
                <ChatBubbleAvatar src={FacePic} fallback='US' />
                <ChatBubbleMessage variant='sent'>
                Hello, how has your day been? I hope you are doing well.
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage variant='received'>
                Hi, I am doing well, thank you for asking. How can I help you today?
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage variant='received'>
                Hi, I am doing well, thank you for asking. How can I help you today?
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='sent'>
                <ChatBubbleAvatar src={FacePic} fallback='US' />
                <ChatBubbleMessage variant='sent'>
                Hello, how has your day been? I hope you are doing well.
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage variant='received'>
                Hi, I am doing well, thank you for asking. How can I help you today?
                </ChatBubbleMessage>
            </ChatBubble>

            <ChatBubble variant='received'>
                <ChatBubbleAvatar src={RobotLogo} fallback='AI' />
                <ChatBubbleMessage isLoading />
            </ChatBubble>
        </ChatMessageList>

        <form
            className="sticky bottom-0 rounded-lg border bg-background focus-within:ring-1 focus-within:ring-ring p-1"
        >
            <ChatInput
                placeholder="Type your message here..."
                className="min-h-12 resize-none rounded-lg bg-background border-0 p-3 shadow-none focus-visible:ring-0"
            />

            <div className="flex justify-end p-3 pt-0">
                <Button size="sm">
                    Send Message
                    <CornerDownLeft className="size-3.5" />
                </Button>
            </div>
        </form>
    </>
}


export default AppChatView