import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "../shared/components/ui/sheet"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../shared/components/ui/tabs"
import FoldersView from './ViewFolders'
import ChatHistoryView from './ViewChatHistory'
import { Button } from '../shared/components/ui/button'
import { FolderSync, MessagesSquare, CircleHelp } from 'lucide-react'
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "../shared/components/ui/tooltip"


export function AppSideView() {
    return (
        <Sheet>
            <SheetTrigger className='flex flex-initial flex-col'>
                <TooltipProvider>
                    <Tooltip>
                        <TooltipTrigger>
                            <Button variant="outline" size="icon"><FolderSync/></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Sync folders</p></TooltipContent>
                    </Tooltip>

                    <Tooltip>
                        <TooltipTrigger className="pb-1 pt-1">
                            <Button variant="outline" size="icon"><MessagesSquare /></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Chat history</p></TooltipContent>
                    </Tooltip>

                    <Tooltip>
                        <TooltipTrigger>
                            <Button variant="outline" size="icon"><CircleHelp /></Button>
                        </TooltipTrigger>
                        <TooltipContent side="right"><p>Help</p></TooltipContent>
                    </Tooltip>
                </TooltipProvider>
            </SheetTrigger>
            
            <SheetContent side="left" className="w-2/3 min-w-2/3 bg-background text-foreground">
                
                <SheetHeader>
                    <SheetTitle>App Title Here</SheetTitle>
                    <SheetDescription>
                        App subtitle here (brief help section)
                    </SheetDescription>
                </SheetHeader>

                <Tabs defaultValue="account" className="w-[400px]">
                    <TabsList>
                        <TabsTrigger value="folders">Folders</TabsTrigger>
                        <TabsTrigger value="chatHistory">Chat History</TabsTrigger>
                    </TabsList>
                    <TabsContent value="folders">
                        <FoldersView />
                    </TabsContent>
                    <TabsContent value="chatHistory">
                        <ChatHistoryView />
                    </TabsContent>
                </Tabs>

            </SheetContent>
        </Sheet>
    )
}

export default AppSideView