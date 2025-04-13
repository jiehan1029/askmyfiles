import { Button } from "@renderer/shared/components/ui/button"
import { Folder } from 'lucide-react'
import { Skeleton } from "@renderer/shared/components/ui/skeleton"
import { Separator } from "@renderer/shared/components/ui/separator"
import { Progress } from "@renderer/shared/components/ui/progress"
import useFoldersStore from "@renderer/store/foldersStore"
import { useEffect } from "react"


export function FoldersView() {

    const foldersStore = useFoldersStore()
    console.log('*****?? ', foldersStore.syncHistoryLoaded)

    useEffect(()=>{
        if(!foldersStore.syncHistoryLoaded){
            foldersStore.fetchSyncHistory()
        }
    }, [])

    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <p className="text-sm">Your AI assistant will answer questions based on the synced folders. <br/>Supported file types: text, html, PDF, and markdown.</p>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <Button>Add Folder</Button>
            <div className="border-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                <div className="flex flex-row items-center justify-start"><Folder /><span className="pl-2 text-md">/Users/alice/docs/project-a</span></div>
                <div className="flex flex row items-center justify-between"><span className="text-sm">Not synced</span><Button variant="secondary" size="sm">Sync Now</Button></div>
            </div>
            <div className="border-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                <div className="flex flex-row items-center justify-start"><Folder /><span className="pl-2 text-md">/Users/alice/docs/project-a</span></div>
                <div className="text-sm"><Progress value={60} className="w-[100%]" /></div>
                <div className="text-sm">Syncing: 60% | 9/12 files</div>
            </div>
            {foldersStore.syncHistoryInflight && (
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
            {
                !foldersStore.syncHistoryInflight && foldersStore.syncHistory.map((doc)=>{
                    return (
                    <div className="border-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                        <div className="flex flex-row items-center justify-start"><Folder /><span className="pl-2 text-md">{doc.folder_path}</span></div>
                        <div className="text-sm">Last Synced: {new Date(Date.parse(doc.last_synced_at)).toLocaleString()} | {doc.processed_files} files</div>
                    </div>)
                })
            }
        </div>
    </>
}


export default FoldersView