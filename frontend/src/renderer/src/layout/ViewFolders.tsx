import { Button } from "@renderer/shared/components/ui/button"
import { Folder, Loader } from 'lucide-react'
import { Skeleton } from "@renderer/shared/components/ui/skeleton"
import { Separator } from "@renderer/shared/components/ui/separator"
import { Progress } from "@renderer/shared/components/ui/progress"
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
import useFoldersStore from "@renderer/store/foldersStore"
import { useEffect, useState } from "react"
import useSettingsStore from "@renderer/store/settingsStore"


export function FoldersView() {
    const foldersStore = useFoldersStore()
    const [folderPath, setFolderPath] = useState<string | null>(null)
    const [folderSyncInflight, setFolderSyncInflight] = useState<boolean>(false)
    const [folderSyncComplete, setFolderSyncComplete] = useState<boolean>(false)

    const settingsStore = useSettingsStore()
    
    const { timezone: ssTimezone, locale: ssLocale } = settingsStore

    const [locale, setLocale] = useState<string>(ssLocale)
    const [timezone, setTimezone] = useState<string>(ssTimezone)
    
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
        if(!settingsStore.settingsLoaded){
            settingsStore.fetchSettings()
        }
    }, [])

    useEffect(()=>{
        if(settingsStore.settingsLoaded){
            setLocale(ssLocale)
            setTimezone(ssTimezone)
        }
    }, [settingsStore.settingsLoaded])

    useEffect(() => {
        let socket: WebSocket | null | undefined
        if(syncTaskId){
            socket = new WebSocket(`${import.meta.env.VITE_APP_WS_BASE_URL}/ws/sync_status/${syncTaskId}`);

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data)
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

    const onClickSyncFolder = async (inputPath: string | null | undefined) => {
        setFolderSyncInflight(true)
        const syncPath = inputPath ? inputPath : folderPath
        if(syncPath){
            const res = await foldersStore.syncFolders(syncPath)
            const { task_id } = res
            setSyncTaskId(task_id)
        }
    }

    const onClickRefresh = () => {
        foldersStore.fetchSyncHistory()
    }

    const onClickDeleteAll = () => {
        foldersStore.deleteFolder("all")
    }

    const onClickDeleteFolder = (folderPath: string) => {
        foldersStore.deleteFolder(folderPath)
    }

    const onClickReSyncFolder = (fp: string) => {
        setFolderPath(fp)
        onClickSyncFolder(fp)
    }

    return <>
        <div className="p-2 pb-12 overflow-scroll">
            <p className="text-sm">Your AI assistant will answer questions based on the synced folders. <br/>Supported file types: text, html, PDF, and markdown.</p>
            <Separator style={{ marginTop: '12px', marginBottom: '12px'}} />
            <div className="flex flex-row justify-between items-center">
                <span>Total files synced: {foldersStore.numFilesSynced}</span>
                <div>
                    <Button disabled={folderSyncInflight} onClick={onClickPickFolder}>{folderSyncInflight && <Loader />}Add Folder</Button>
                    <Button variant={"secondary"} disabled={folderSyncInflight} onClick={onClickRefresh} style={{ marginLeft: '24px'}}>{folderSyncInflight && <Loader />}Refresh</Button>
                    <Button className="text-red-500" variant={"ghost"} disabled={folderSyncInflight} onClick={onClickDeleteAll} style={{ marginLeft: '24px'}}>{folderSyncInflight && <Loader />}Delete All</Button>
                </div>
            </div>
            {
                !foldersStore.syncHistoryInflight && foldersStore.syncHistory.length === 0 && (
                    <div style={{ marginTop: '24px' }}>No folder synced.</div>
                )
            }
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
                            : <>
                                <div className="flex flex row items-center justify-between">
                                    <span className="text-sm">Not synced</span>
                                    <Button disabled={folderSyncInflight} size="sm" onClick={()=>onClickSyncFolder(folderPath)}>Sync Now</Button>
                                </div>
                            </>
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
                !foldersStore.syncHistoryInflight && foldersStore.syncHistory.map((doc, idx)=>{
                    return (
                    <div key={idx} className="border-slate-200 border-solid border-2 rounded-lg p-2 my-4 w-[calc(100%-32px)]" style={{ marginTop: '12px'}}>
                        <div className="flex flex-row items-center justify-between">
                            <div className="flex flex-row items-center justify-start"><Folder /><span className="pl-2 text-md">{doc.folder_path}</span></div>
                            <Breadcrumb>
                                <BreadcrumbItem>
                                <DropdownMenu>
                                    <DropdownMenuTrigger className="flex items-center gap-1">
                                    <BreadcrumbEllipsis className="h-4 w-4 cursor-pointer" />
                                    <span className="sr-only">Toggle menu</span>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="start">
                                    <DropdownMenuItem onSelect={()=>onClickReSyncFolder(doc.folder_path)}>Re-Sync</DropdownMenuItem>
                                    <DropdownMenuItem className="text-rose-500" onSelect={()=>onClickDeleteFolder(doc.folder_path)}>Delete</DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                                </BreadcrumbItem>
                            </Breadcrumb>
                        </div>
                        <div className="text-sm">Last Synced: {new Date(doc.last_synced_at).toLocaleString(locale, {timeZone: timezone})} | {doc.processed_files} files processed / {doc.skipped_files} skipped</div>
                    </div>)
                })
            }
        </div>
    </>
}


export default FoldersView