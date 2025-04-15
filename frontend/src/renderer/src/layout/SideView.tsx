import {
    Sheet,
    SheetContent,
    SheetTrigger,
} from "../shared/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../shared/components/ui/tabs"
import FoldersView from './ViewFolders'
import ChatHistoryView from './ViewChatHistory'
import HelpView from "./ViewHelp"
import { Button } from '../shared/components/ui/button'
import { FolderSync, MessagesSquare, CircleHelp } from 'lucide-react'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "../shared/components/ui/tooltip"
import { useState } from "react"


export function AppSideView() {
    const [tabOnOpen, setTabOnOpen] = useState<string>('help')
    const [sheetIsOpen, setSheetIsOpen] = useState<boolean>(false)

    const onClickSideIcon = (e)=>{
        setTabOnOpen(e.target.value)
    }

    const closeSideView = ()=>{
        setSheetIsOpen(false)
    }

    return (
        <Sheet open={sheetIsOpen} onOpenChange={setSheetIsOpen}>
            <SheetTrigger className='flex flex-initial flex-col'>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger>
                            <Button variant="outline" size="icon" value="folders" onClick={onClickSideIcon}><FolderSync/></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Sync folders</p></TooltipContent>
                    </Tooltip>

                    <Tooltip>
                        <TooltipTrigger className="pb-1 pt-1">
                            <Button variant="outline" size="icon" value="chatHistory" onClick={onClickSideIcon}><MessagesSquare /></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Chat history</p></TooltipContent>
                    </Tooltip>

                    <Tooltip>
                        <TooltipTrigger>
                            <Button variant="outline" size="icon" value="help" onClick={onClickSideIcon}><CircleHelp /></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Help</p></TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </SheetTrigger>
            
            <SheetContent side="left" className="pt-2 w-2/3 min-w-2/3 bg-background text-foreground overflow-scroll">

                <Tabs defaultValue={tabOnOpen}>
                    <TabsList className="pl-8 pr-8 w-[calc(100%-40px)]">
                        <TabsTrigger value="folders">Folders</TabsTrigger>
                        <TabsTrigger value="chatHistory">Chat History</TabsTrigger>
                        <TabsTrigger value="help">Help</TabsTrigger>
                    </TabsList>
                    <TabsContent value="folders">
                        <FoldersView />
                    </TabsContent>
                    <TabsContent value="chatHistory">
                        <ChatHistoryView closeSideView={closeSideView} />
                    </TabsContent>
                    <TabsContent value="help">
                        <HelpView />
                    </TabsContent>
                </Tabs>

            </SheetContent>
        </Sheet>
    )
}

export default AppSideView