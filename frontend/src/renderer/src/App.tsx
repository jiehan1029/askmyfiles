import AppSideView from './layout/SideView'
import AppChatView from './layout/ChatView'
import AppHeader from './layout/Header'
import AppFooter from './layout/Footer'

function App(): JSX.Element {
  return (
    <>
      <AppHeader/>
      <main className='flex flex-initial flex-row bg-background text-foreground'>
        <section className='h-[calc(100vh-126px)] pl-1 pr-1 pt-4 bg-slate-100 w-[44px]'>
          <AppSideView />
        </section>
        <section className='h-[calc(100vh-126px)] pt-8 pb-2 pl-4 pr-4 flex flex-col w-[calc(100vw-44px)]'>
          <AppChatView />
        </section>
      </main>
      <AppFooter />
    </>
  )
}

export default App
