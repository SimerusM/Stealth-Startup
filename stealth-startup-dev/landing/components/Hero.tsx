import Image from 'next/image';

export default function Hero() {
  return (
    <section className="bg-noise bg-cover h-screen">
      <div className="container mx-auto p-4 pt-6 md:p-6 lg:p-12">
        <h1 className="text-4xl md:text-6xl font-bold">Dispatch AI</h1>
        <p className="text-lg md:text-2xl">Automated Response for 911 Calls</p>
        <Image src="/dispatch-ai-logo.png" alt="Dispatch AI Logo" width={200} height={50} />
      </div>
    </section>
  );
}
