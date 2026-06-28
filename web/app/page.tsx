import { redirect } from "next/navigation";

// The marketing / case-study landing page is built in a later milestone.
// For now, send visitors straight into the product.
export default function Home() {
  redirect("/ask");
}
