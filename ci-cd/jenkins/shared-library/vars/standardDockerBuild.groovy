/**
 * Build a Docker image with a predictable Jenkins build-number tag.
 * Usage: standardDockerBuild(image: 'registry.example.com/team/app')
 */
def call(Map config = [:]) {
    String image = config.image ?: error("standardDockerBuild requires image: 'name'")
    if (!(image ==~ /[A-Za-z0-9._\/:\-]+/)) {
        error('Image name contains unsupported characters.')
    }

    String tag = env.BUILD_NUMBER ?: 'local'
    sh "docker build --pull -t '${image}:${tag}' ."
    return "${image}:${tag}"
}
