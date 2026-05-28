<script>
  import './app.css';

  let report = null;
  let loading = false;
  let customBundle = '';
  let activeTab = 'completeness';

  const API_BASE = 'http://localhost:8000';

  const gradeColors = {
    'A': '#4caf50',
    'B': '#009688',
    'C': '#ffeb3b',
    'D': '#ff9800',
    'F': '#f44336'
  };

  async function analyze(endpoint, method = 'GET', body = null) {
    loading = true;
    report = null;
    try {
      const options = { method };
      if (body) {
        options.headers = { 'Content-Type': 'application/json' };
        options.body = JSON.stringify(body);
      }
      const response = await fetch(`${API_BASE}${endpoint}`, options);
      if (!response.ok) throw new Error('Analysis failed');
      report = await response.json();
    } catch (e) {
      alert(e.message);
    } finally {
      loading = false;
    }
  }

  function handleCustomAnalyze() {
    try {
      const parsed = JSON.parse(customBundle);
      analyze('/analyze', 'POST', parsed);
    } catch (e) {
      alert('Invalid JSON input');
    }
  }
</script>

<div class="container">
  <h1>FHIR Bundle Quality Analyzer</h1>

  <!-- Section 1: Input Controls -->
  <div class="section">
    <div class="controls">
      <div class="button-group">
        <button on:click={() => analyze('/analyze/sample')} disabled={loading}>
          Analyze Clean Bundle
        </button>
        <button on:click={() => analyze('/analyze/degraded')} disabled={loading}>
          Analyze Degraded Bundle
        </button>
      </div>

      <div>
        <textarea 
          bind:value={customBundle} 
          placeholder="Paste FHIR Bundle JSON here..." 
          disabled={loading}
        ></textarea>
        <div class="button-group" style="margin-top: 10px;">
          <button on:click={handleCustomAnalyze} disabled={loading}>
            Analyze Custom Bundle
          </button>
        </div>
      </div>
    </div>
    {#if loading}
      <div class="loader">Analyzing...</div>
    {/if}
  </div>

  {#if report}
    <!-- Section 2: Score Overview -->
    <div class="section">
      <div class="grade-container">
        <div class="grade" style="color: {gradeColors[report.grade] || 'white'}">
          {report.grade}
        </div>
        <div class="score-text">
          Overall Score: {report.overall_weighted_score}
        </div>
      </div>

      <div class="cards-row">
        <div class="card">
          <div>Completeness</div>
          <div class="score-text">{report.completeness.overall_score}</div>
          <div class="progress-bg">
            <div class="progress-fill" style="width: {report.completeness.overall_score * 100}%"></div>
          </div>
        </div>
        <div class="card">
          <div>Code Coverage</div>
          <div class="score-text">{report.code_coverage.overall_score}</div>
          <div class="progress-bg">
            <div class="progress-fill" style="width: {report.code_coverage.overall_score * 100}%"></div>
          </div>
        </div>
        <div class="card">
          <div>Temporal Consistency</div>
          <div class="score-text">{report.temporal.overall_score}</div>
          <div class="progress-bg">
            <div class="progress-fill" style="width: {report.temporal.overall_score * 100}%"></div>
          </div>
        </div>
        <div class="card">
          <div>Duplicate Detection</div>
          <div class="score-text">{report.duplicates.overall_score}</div>
          <div class="progress-bg">
            <div class="progress-fill" style="width: {report.duplicates.overall_score * 100}%"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 3: Issue Details -->
    <div class="section">
      <div class="tabs">
        <button class="tab {activeTab === 'completeness' ? 'active' : ''}" on:click={() => activeTab = 'completeness'}>Completeness</button>
        <button class="tab {activeTab === 'coverage' ? 'active' : ''}" on:click={() => activeTab = 'coverage'}>Code Coverage</button>
        <button class="tab {activeTab === 'temporal' ? 'active' : ''}" on:click={() => activeTab = 'temporal'}>Temporal</button>
        <button class="tab {activeTab === 'duplicates' ? 'active' : ''}" on:click={() => activeTab = 'duplicates'}>Duplicates</button>
      </div>

      <div class="tab-content">
        {#if activeTab === 'completeness'}
          <table>
            <thead>
              <tr>
                <th>Resource Type</th>
                <th>Resource ID</th>
                <th>Missing Fields</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {#each report.completeness.by_resource_type as type}
                {#each type.instances as inst}
                  <tr>
                    <td>{type.resource_type}</td>
                    <td class="mono">{inst.resource_id}</td>
                    <td>{inst.missing_fields.join(', ')}</td>
                    <td>{inst.score}</td>
                  </tr>
                {/each}
              {/each}
            </tbody>
          </table>
        {:else if activeTab === 'coverage'}
          <table>
            <thead>
              <tr>
                <th>Resource Type</th>
                <th>Resource ID</th>
                <th>Has Coding</th>
                <th>Systems Found</th>
              </tr>
            </thead>
            <tbody>
              {#each report.code_coverage.by_resource_type as type}
                {#each type.instances as inst}
                  <tr>
                    <td>{type.resource_type}</td>
                    <td class="mono">{inst.resource_id}</td>
                    <td>{inst.score === 1 ? 'Yes' : 'No'}</td>
                    <td>{inst.score === 1 ? 'Recognized' : 'None'}</td>
                  </tr>
                {/each}
              {/each}
            </tbody>
          </table>
        {:else if activeTab === 'temporal'}
          <table>
            <thead>
              <tr>
                <th>Resource Type</th>
                <th>Resource ID</th>
                <th>Violation Type</th>
                <th>Dates</th>
              </tr>
            </thead>
            <tbody>
              {#each report.temporal.by_resource_type as type}
                {#each type.instances as inst}
                  {#each inst.violations as v}
                    <tr>
                      <td>{type.resource_type}</td>
                      <td class="mono">{inst.resource_id}</td>
                      <td>{v.violation_type}</td>
                      <td class="mono">{JSON.stringify(v.conflicting_dates)}</td>
                    </tr>
                  {/each}
                {/each}
              {/each}
            </tbody>
          </table>
        {:else if activeTab === 'duplicates'}
          <table>
            <thead>
              <tr>
                <th>Resource Type</th>
                <th>ID 1</th>
                <th>ID 2</th>
                <th>Similarity</th>
                <th>Text 1</th>
                <th>Text 2</th>
              </tr>
            </thead>
            <tbody>
              {#each report.duplicates.by_resource_type as type}
                {#each type.duplicates as dup}
                  <tr>
                    <td>{type.resource_type}</td>
                    <td class="mono">{dup.resource_id_1}</td>
                    <td class="mono">{dup.resource_id_2}</td>
                    <td>{dup.similarity}</td>
                    <td>{dup.text_1}</td>
                    <td>{dup.text_2}</td>
                  </tr>
                {/each}
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    </div>
  {/if}
</div>
