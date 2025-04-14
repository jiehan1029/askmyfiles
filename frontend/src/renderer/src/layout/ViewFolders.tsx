import { Button } from "@renderer/shared/components/ui/button"
import { Folder, Loader } from 'lucide-react'
import { Skeleton } from "@renderer/shared/components/ui/skeleton"
import { Separator } from "@renderer/shared/components/ui/separator"
import { Progress } from "@renderer/shared/components/ui/progress"
import useFoldersStore from "@renderer/store/foldersStore"
import { useEffect, useState } from "react"


export function FoldersView() {

    const foldersStore = useFoldersStore()
    const [folderPath, setFolderPath] = useState<string | null>(null)
    const [folderSyncInflight, setFolderSyncInflight] = useState<boolean>(false)
    const [folderSyncComplete, setFolderSyncComplete] = useState<boolean>(false)
    
    type folderSyncPogressType = {
        percent: number
        current: number
        total: number
    }
    const [folderSyncPogress, setfolderSyncPogress] = useState<folderSyncPogressType | null>(null)
    const [syncTaskId, setSyncTaskId] = useState<string | null>(null)

    useEffect(()=>{
        if(!foldersStore.syncHistoryLoaded){
            foldersStore.fetchSyncHistory()
        }
    }, [])

    useEffect(() => {
        let socket: WebSocket | null | undefined
        if(syncTaskId){
            // todo jie use env var
            socket = new WebSocket(`ws://localhost:8000/ws/sync_status/${syncTaskId}`);

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log("websocket data=", data)
                if(data.status === "in_progress"){
                    setFolderSyncInflight(true)
                    setFolderSyncComplete(false)
                    setfolderSyncPogress({
                        percent: Math.floor((data.current/data.total)*100),
                        current: data.current,
                        total: data.total
                    })
                }else if(data.status === "complete"){
                    setfolderSyncPogress({
                        percent: 100,
                        current: data.current,
                        total: data.total
                    })
                    setFolderSyncComplete(true)
                    setFolderSyncInflight(false)
                    // re fetch sync history and reset state
                    setTimeout(async () => {
                        await foldersStore.fetchSyncHistory()
                        setFolderPath(null)
                        setFolderSyncComplete(false)
                        setSyncTaskId(null)
                        setfolderSyncPogress(null)
                    }, 1000);
                }else {
                    // todo: error handling
                    setfolderSyncPogress({
                        percent: 0,
                        current: data.current,
                        total: data.total
                    })
                    setFolderSyncComplete(false)
                    setFolderSyncInflight(false)
                }
            }

            socket.onerror = (e) => {
                console.error("WebSocket error", e)
                // todo: error handling
            }           
        }
        return () => {
            if(socket){
                socket.close()
            }
        } 
    }, [syncTaskId])


    const onClickPickFolder = async () => {
        const path = await window.api.selectFolder();
        if (path) {
            setFolderPath(path);
        }
    }

    const onClickSyncFolder = async () => {
        setFolderSyncInflight(true)
        console.log({folderPath})
        if(folderPath){
            const res = await foldersStore.syncFolders(folderPath)
            const { task_id } = res
            setSyncTaskId(task_id)
        }
    }

    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <p className="text-sm">Your AI assistant will answer questions based on the synced folders. <br/>Supported file types: text, html, PDF, and markdown.</p>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <Button disabled={folderSyncInflight} onClick={onClickPickFolder}>{folderSyncInflight && <Loader />}Add Folder</Button>
            {folderPath && (
                <div className="border-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                    <div className="flex flex-row items-center justify-start"><Folder /><span className="pl-2 text-md">{folderPath}</span></div>
                    {
                        folderSyncComplete 
                        ? <div className="flex flex row items-center justify-between"><span className="text-sm">Sync completed!</span></div>
                        : folderSyncInflight && folderSyncPogress
                            ? <>
                                <div className="text-sm"><Progress value={folderSyncPogress.percent} className="w-[100%]" /></div>
                                <div className="text-sm">Syncing: {folderSyncPogress.percent}% | {folderSyncPogress.current}/{folderSyncPogress.total} files</div>
                            </>
                            : <div className="flex flex row items-center justify-between"><span className="text-sm">Not synced</span><Button variant="secondary" size="sm" onClick={onClickSyncFolder}>Sync Now</Button></div>
                    }
                </div>
            )}
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
                        <div className="text-sm">Last Synced: {new Date(Date.parse(doc.last_synced_at)).toLocaleString("en-US", {timeZone: "America/Los_Angeles"})} | {doc.processed_files} files</div>
                    </div>)
                })
            }
        </div>
    </>
}


export default FoldersView