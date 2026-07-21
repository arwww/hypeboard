import { Link } from 'react-router-dom';

import { DisclaimerBanner } from '../components/DisclaimerBanner';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { SourceTable } from '../components/SourceTable';
import { useDashboardData } from '../hooks/useDashboardData';

const dimensions = [
  {
    number: '01',
    title: 'Attention',
    copy: 'How strongly the public is engaging with a stock right now. The first version uses Wikimedia Pageviews and can incorporate a configured public social feed.',
  },
  {
    number: '02',
    title: 'Trading Activity',
    copy: 'How unusual trading volume, the absolute daily move and the volatility shock are relative to the stock’s own recent history.',
  },
  {
    number: '03',
    title: 'Retail Proxy',
    copy: 'How many public characteristics are consistent with retail-oriented activity. This is an inference layer and never a measured broker-customer share.',
  },
  {
    number: '04',
    title: 'Market Impact',
    copy: 'How sensitively the stock reacts to incremental attention or trading, using price movement per dollar volume and available liquidity proxies.',
  },
  {
    number: '05',
    title: 'Confidence',
    copy: 'How complete, recent and independent the evidence is, including observation history and the quality of each proxy.',
  },
];

export function MethodologyPage() {
  const { data, loading, error } = useDashboardData();
  if (loading) return <div className="container page-space"><LoadingState label="Loading methodology metadata…" /></div>;
  if (error || !data) return <div className="container page-space"><ErrorState message={error ?? 'Methodology data unavailable'} /></div>;

  return (
    <div className="container methodology-page page-space">
      <div className="breadcrumb"><Link to="/">Dashboard</Link><span>/</span><span>Methodology</span></div>
      <header className="methodology-hero">
        <span className="eyebrow">Transparent by design</span>
        <h1>How Hypeboard measures public market attention.</h1>
        <p>Hypeboard is a relative signal system built from public proxies. It is designed to make the reasoning inspectable rather than to imply access to private broker order flow.</p>
      </header>

      <section className="method-callout">
        <div className="method-callout-score">85</div>
        <div>
          <h2>A Hype Score of 85 does not mean “85% retail ownership”.</h2>
          <p>It means the stock has a very high combined attention-and-activity reading compared with the observed universe, under score model v{data.meta.score_version}.</p>
        </div>
      </section>

      <section className="method-section">
        <div className="section-heading">
          <div><span className="section-kicker">Signal framework</span><h2>Five separate dimensions</h2></div>
        </div>
        <div className="dimension-grid">
          {dimensions.map((dimension) => (
            <article key={dimension.number}>
              <span>{dimension.number}</span>
              <h3>{dimension.title}</h3>
              <p>{dimension.copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="method-section formula-section">
        <div className="section-heading">
          <div><span className="section-kicker">Versioned score model</span><h2>Current formula</h2></div>
          <span className="version-pill">v{data.meta.score_version}</span>
        </div>
        <div className="formula-card">
          <div className="formula-line"><strong>Hype Score</strong><span>=</span></div>
          <div className="weight-row"><span style={{ width: '40%' }}>40% Attention</span><span style={{ width: '35%' }}>35% Trading</span><span style={{ width: '15%' }}>15% Retail Proxy</span><span style={{ width: '10%' }}>10% Impact</span></div>
          <p>Inputs are normalized through rolling medians, Median Absolute Deviation, capped extremes and cross-sectional percentile ranks. A configured minimum history and minimum component coverage apply.</p>
        </div>
        <div className="subformula-grid">
          <article><h3>Attention Score</h3><p><strong>55%</strong> Wikipedia/search shock<br /><strong>45%</strong> public social attention</p></article>
          <article><h3>Trading Score</h3><p><strong>60%</strong> unusual volume<br /><strong>25%</strong> absolute daily move<br /><strong>15%</strong> volatility shock</p></article>
          <article><h3>Retail Proxy</h3><p><strong>50%</strong> short-term retail-oriented signals<br /><strong>30%</strong> short-sale volume change<br /><strong>20%</strong> additional proxies</p></article>
          <article><h3>Impact Score</h3><p><strong>45%</strong> move per dollar volume<br /><strong>30%</strong> liquidity indicators<br /><strong>25%</strong> attention shock size</p></article>
        </div>
      </section>

      <section className="method-section">
        <div className="section-heading"><div><span className="section-kicker">Data provenance</span><h2>Sources, timing and current state</h2></div></div>
        <SourceTable sources={data.meta.sources} />
      </section>

      <section className="method-section confidence-method">
        <div>
          <span className="section-kicker">Evidence quality</span>
          <h2>Confidence is separate from hype.</h2>
          <p>A high signal with weak coverage is not presented as equally reliable as a high signal backed by several fresh, independent categories.</p>
        </div>
        <ol>
          <li><strong>Data completeness</strong><span>Are required fields available without treating missing values as zero?</span></li>
          <li><strong>Freshness</strong><span>How close are the observations to the expected publication cadence?</span></li>
          <li><strong>Independent sources</strong><span>How many distinct public providers support the reading?</span></li>
          <li><strong>History length</strong><span>Is there enough history for a robust rolling comparison?</span></li>
          <li><strong>Proxy quality</strong><span>How directly does the public metric support the intended interpretation?</span></li>
        </ol>
      </section>

      <section className="method-section limits-grid">
        <article>
          <span className="section-kicker">Explicitly measured</span>
          <h2>What Hypeboard can show</h2>
          <ul>
            <li>Relative public-attention shocks</li>
            <li>Unusual trading activity versus history</li>
            <li>Public short-sale-volume patterns</li>
            <li>Data completeness and freshness</li>
            <li>Deterministic, data-backed score drivers</li>
          </ul>
        </article>
        <article>
          <span className="section-kicker">Explicitly not measured</span>
          <h2>What Hypeboard cannot know</h2>
          <ul>
            <li>Exact Robinhood or Trade Republic ownership</li>
            <li>Exact retail share of stock-level order flow</li>
            <li>Private account positions or personal data</li>
            <li>Investment quality or future returns</li>
            <li>Whether short-sale volume equals short interest</li>
          </ul>
        </article>
      </section>

      <section className="method-section update-method">
        <div>
          <span className="section-kicker">Update behavior</span>
          <h2>Daily, resilient and explicit about gaps.</h2>
        </div>
        <p>The pipeline isolates provider failures, uses timeouts and bounded retries, preserves the latest successful real observations and marks cached or stale sources. Weekends and holidays do not create duplicate trading days, while attention data may continue to advance.</p>
      </section>

      <DisclaimerBanner notice={data.meta.legal_notice} />
    </div>
  );
}
