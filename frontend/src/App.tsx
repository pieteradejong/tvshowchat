// App.tsx
import { FC } from 'react';
import Search from './components/Search';

const App: FC = () => {
  return (
    <div>
      <h1>TV Show Q&A Engine</h1>
      <Search />
    </div>
  );
}

export default App;
