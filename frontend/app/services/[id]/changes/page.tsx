import ChangeHistoryClient from '@/components/ChangeHistoryClient';

export async function generateStaticParams() {
  return [];
}

export default function ChangeHistoryPage({ params }: { params: { id: string } }) {
  return <ChangeHistoryClient serviceId={params.id} />;
}
