/**
 * Run safe, non-mutating Terraform checks in a repository subdirectory.
 * Usage: standardTerraformChecks(directory: 'infra/environments/local', backend: false)
 */
def call(Map config = [:]) {
    String directory = config.directory ?: '.'
    if (!(directory ==~ /[A-Za-z0-9._\/-]+/)) {
        error('Terraform directory contains unsupported characters.')
    }
    boolean backend = config.backend == true

    dir(directory) {
        sh 'terraform fmt -check -recursive'
        sh("terraform init -input=false ${backend ? '' : '-backend=false'}")
        sh 'terraform validate'
        sh 'terraform plan -input=false -no-color'
    }
}
