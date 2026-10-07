import Link from "next/link";

export default function NotFound() {
  return (
    <main>
      <h1>That page is not in the tournament.</h1>
      <p className="lede">
        <Link href="/">Back to the table.</Link>
      </p>
    </main>
  );
}
