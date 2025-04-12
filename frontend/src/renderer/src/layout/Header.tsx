import LogoOutlined from '../assets/logo_outline_2.svg'

export function AppHeader() {
    return <>
        <header
            className="w-screen flex flex-row items-center justify-center p-2 bg-slate-300 text-secondary-foreground font-mono"
            style={{ height: '96px'}}
        >
            <img alt="logo" className="logo w-[80px]" src={LogoOutlined}/> 
            <div className="text-left" style={{ marginLeft: '12px' }}>
                <h1 className="text-4xl italic">AskMyFiles</h1>
                <sub>A local AI assistant for your documents.</sub>
            </div>
        </header>
    </>
}


export default AppHeader