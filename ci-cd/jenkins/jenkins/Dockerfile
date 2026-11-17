# Learning-lab image only. Pin base images by digest for controlled environments.
FROM hashicorp/terraform:1.17.1 AS terraform

FROM jenkins/jenkins:lts-jdk21
USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       docker-cli git ca-certificates curl unzip \
       python3 python3-venv maven nodejs npm \
       openssh-client \
    && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip -q awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip ./aws \
    && rm -rf /var/lib/apt/lists/*

COPY --from=terraform /bin/terraform /usr/local/bin/terraform
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
COPY casc/jenkins.yaml /usr/share/jenkins/ref/casc/jenkins.yaml

RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

USER jenkins
