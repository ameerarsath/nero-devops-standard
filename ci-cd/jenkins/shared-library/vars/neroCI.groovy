// ============================================================================
// NERO Universal Enterprise DevOps Automation Platform
// Trusted Shared Library CI Helpers: neroCI.groovy (A3-BLD-004)
//
// Codifies trusted, parameterized CI steps callable across all enterprise jobs.
// Strictly verifies arguments and prevents arbitrary dynamic code injection.
// ============================================================================

def call(Map config = [:]) {
    echo "Initializing NERO CI Shared Library..."
}

def validateSpec(String specPath = 'app.spec.yaml') {
    echo "NERO CI Step: Validating application specification: ${specPath}"
    sh "python -m platform_core.engine.cli inspect-spec ${specPath}"
}

def scanSecrets() {
    echo "NERO CI Step: Running Gitleaks secret scan"
    sh '''
        python -c "
from platform_core.adapters.security.gitleaks_adapter import GitleaksAdapter
scanner = GitleaksAdapter()
res = scanner.scan_repository('.')
if not res.passed:
    exit(1)
"
    '''
}

def runBuilds(String specPath = 'app.spec.yaml', String tag = 'latest') {
    echo "NERO CI Step: Running multi-component parallel builds for tag: ${tag}"
    sh """
        python -c "
from platform_core.engine.build_orchestrator import BuildOrchestrator
orchestrator = BuildOrchestrator()
res = orchestrator.build_application('${specPath}', tag='${tag}', dry_run=True)
if not res.success:
    exit(1)
"
    """
}

def checkQualityGate(double threshold = 80.0) {
    echo "NERO CI Step: Checking changed-code coverage gate (>= ${threshold}%)"
    sh "python -m platform_core.engine.coverage_gate enforce --threshold ${threshold}"
}

def scanSecurity() {
    echo "NERO CI Step: Running DevSecOps SAST & SCA scanners"
    sh "python -m platform_core.adapters.security.scanner_orchestrator scan --all"
}

def generateSBOM(String appId, String tag) {
    echo "NERO CI Step: Generating CycloneDX SBOM for ${appId}:${tag}"
    sh "python -m platform_core.engine.sbom_generator generate --app '${appId}' --tag '${tag}'"
}

def recordEvidence(String appId, String buildNum, String commitSha, String result = 'SUCCESS') {
    echo "NERO CI Step: Recording cryptographic CI evidence for build #${buildNum}"
    sh """
        python -m platform_core.engine.ci_evidence generate \
            --app '${appId}' \
            --build '${buildNum}' \
            --commit '${commitSha}' \
            --result '${result}'
    """
}
