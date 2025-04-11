import AppSideView, { SidebarProvider, SidebarTrigger } from './layout/SideView'

function App(): JSX.Element {
  return (
    <>
      <SidebarProvider>
        <AppSideView />
        <main>
          <SidebarTrigger />
          <div>
            other contents here 
          </div>
        </main>
      </SidebarProvider>
    </>
  )
}

export default App
