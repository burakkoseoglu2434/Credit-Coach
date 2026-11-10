import type { components } from "./api/schema";

type Health = components["schemas"]["HealthResponse"];

export default function App() {
  const example: Health = { status: "ok", version: "0.1.0" };
  return <h1>Credit Coach v2 ({example.status})</h1>;
}
