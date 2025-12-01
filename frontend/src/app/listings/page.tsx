import { getListings } from '@/lib/utils';
import Card from '@/ui/card';
import Header from '@/ui/header';

export default function Home() {
  return (
    <>
      <Header/>
      <p>General search page that has categories + query params</p>
      <Card/>
    </>
  );
}
