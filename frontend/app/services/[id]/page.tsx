import ServiceDetailClient from '@/components/ServiceDetailClient';

export async function generateStaticParams() {
  return [];
}

export default function ServiceDetailPage({ params }: { params: { id: string } }) {
  return <ServiceDetailClient serviceId={params.id} />;
}
