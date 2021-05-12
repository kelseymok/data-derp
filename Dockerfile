FROM python:3.7

# Install OpenJDK 8
RUN apt update
RUN apt-get install -y software-properties-common
RUN wget -qO - https://adoptopenjdk.jfrog.io/adoptopenjdk/api/gpg/key/public | apt-key add -
RUN add-apt-repository -y https://adoptopenjdk.jfrog.io/adoptopenjdk/deb/
RUN apt-get update
RUN apt-get install -y adoptopenjdk-8-hotspot

# Install NodeJS (for Plotly - JupyterLab integration)
RUN curl -fsSL https://deb.nodesource.com/setup_15.x | bash -
RUN apt-get install -y nodejs
    
# Install libraries
RUN python -m pip install pip==21.0.1
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install JupyterLab renderer support
RUN jupyter labextension install jupyterlab-plotly@4.14.3

# Install Terraform CLI
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg | apt-key add -
RUN apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
RUN apt-get update && apt-get install terraform

# Install SAML2AWS
RUN CURRENT_VERSION=$(curl -Ls https://api.github.com/repos/Versent/saml2aws/releases/latest | grep 'tag_name' | cut -d'v' -f2 | cut -d'"' -f1) && \
    wget -c https://github.com/Versent/saml2aws/releases/download/v${CURRENT_VERSION}/saml2aws_${CURRENT_VERSION}_linux_amd64.tar.gz -O - | tar -xzv -C /usr/local/bin && \
    chmod u+x /usr/local/bin/saml2aws && \
    saml2aws --version

# Install Bootstrap deps
RUN apt-get install -y jq

# Environment variables
ENV ENVIRONMENT=local