import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StreamProvider } from './realtime'
import { VehicleProvider } from './context/VehicleContext'
import LiveMap from './components/LiveMap'
import './App.css'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <StreamProvider>
        <VehicleProvider>
          <div className="App">
            <LiveMap/>
          </div>
        </VehicleProvider>
      </StreamProvider>
    </QueryClientProvider>
  )
}

export default App
