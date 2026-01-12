import DiffViewClient from '@/components/DiffViewClient';

export async function generateStaticParams() {
  return [];
}

export default function DiffViewPage({ params }: { params: { id: string; changeId: string } }) {
  return <DiffViewClient serviceId={params.id} changeId={params.changeId} />;
}
