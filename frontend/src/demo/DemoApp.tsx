import App from "../App";

/**
 * The standalone /demo entry intentionally renders the same V0.5 product
 * surface as the project homepage. Keeping one interface prevents the public
 * demo from drifting back to an older workflow contract.
 */
export function DemoApp() {
  return <App />;
}
