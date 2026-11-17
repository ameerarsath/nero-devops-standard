import subprocess
import time
import sys

def run_groovy(script_code):
    p = subprocess.Popen(
        ["docker", "exec", "-i", "jenkins", "java", "-jar", "/tmp/jenkins-cli.jar", "-s", "http://localhost:8080/", "groovy", "="],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = p.communicate(input=script_code)
    return p.returncode, stdout, stderr

GROOVY_APPROVE = """
import jenkins.model.Jenkins
import org.jenkinsci.plugins.workflow.support.steps.input.InputAction

def job = Jenkins.instance.getItemByFullName('billing-prod')
def build = job.getLastBuild()
if (build == null) {
    println('No build found')
    return
}
println('Inspecting build #' + build.number)
def action = build.getAction(InputAction.class)
if (action == null) {
    println('No pending InputAction found')
    return
}
def executions = action.getExecutions()
if (executions.isEmpty()) {
    println('Executions list is empty')
    return
}

for (exec in executions) {
    def id = exec.getId()
    def msg = exec.getInput().getMessage()
    println('Found execution id: ' + id + ', message: ' + msg)
    if (id.equalsIgnoreCase('qa-technical-approval')) {
        println('Approving Gate 1: QA / Technical Lead with qa-lead...')
        exec.proceed([APPROVER_NAME: 'qa-lead'])
        println('Gate 1 Approved!')
    } else if (id.equalsIgnoreCase('ops-release-approval')) {
        println('Approving Gate 2: Operations Lead with ops-lead...')
        exec.proceed([APPROVER_NAME: 'ops-lead'])
        println('Gate 2 Approved!')
    } else {
        println('Unknown execution id: ' + id)
    }
}
"""

if __name__ == '__main__':
    rc, out, err = run_groovy(GROOVY_APPROVE)
    print("STDOUT:\n", out)
    if err:
        print("STDERR:\n", err)
