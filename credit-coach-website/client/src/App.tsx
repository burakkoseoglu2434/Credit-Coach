import { Route, Switch } from "wouter";

import { SiteShell } from "./components/SiteShell";
import { ContactPage } from "./pages/ContactPage";
import { DemoCenterPage } from "./pages/DemoCenterPage";
import { HomePage } from "./pages/HomePage";
import { InvestorPage } from "./pages/InvestorPage";
import { ModulesPage } from "./pages/ModulesPage";
import { ProductPage } from "./pages/ProductPage";
import { ProofPage } from "./pages/ProofPage";

export default function App() {
  return (
    <SiteShell>
      <Switch>
        <Route path="/" component={HomePage} />
        <Route path="/product" component={ProductPage} />
        <Route path="/modules" component={ModulesPage} />
        <Route path="/demo" component={DemoCenterPage} />
        <Route path="/proof" component={ProofPage} />
        <Route path="/investor" component={InvestorPage} />
        <Route path="/contact" component={ContactPage} />
      </Switch>
    </SiteShell>
  );
}
