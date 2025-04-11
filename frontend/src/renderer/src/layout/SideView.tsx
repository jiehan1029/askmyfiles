import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    // SidebarGroup,
    SidebarHeader,
    SidebarProvider, SidebarTrigger
} from "../shared/components/ui/sidebar"

export function AppSideView() {
    return (
        <Sidebar>
        <SidebarHeader />
        <SidebarContent>
            test content here
        </SidebarContent>
        <SidebarFooter />
        </Sidebar>
    )
}

export default AppSideView
export { SidebarProvider, SidebarTrigger }