FROM ubuntu:24.04

# Instala dependencias y limpia cache
RUN apt-get update && apt-get install -y \
    sudo curl git vim bash-completion \
    curl \
    git \
    vim \
    postgresql-client \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crea el usuario "jaime" y agrégalo al grupo sudo
RUN useradd -ms /bin/bash jaime && \
    echo 'jaime:jaime' | chpasswd && \
    usermod -aG sudo jaime && \
    echo 'jaime ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Crear el directorio ~/.ssh con permisos correctos
RUN mkdir -p /home/jaime/.ssh && \
    chown -R jaime:jaime /home/jaime/.ssh && \
    chmod 700 /home/jaime/.ssh

# Cambia al usuario "jaime"
USER jaime

# Establece el directorio de trabajo
WORKDIR /workspace

# Configura el entorno
ENV HOME /home/jaime

# Configurar alias y hacerlos persistentes
RUN echo "\n# Alias generales" >> ~/.bashrc && \
    echo "alias update='sudo apt update && sudo apt upgrade -y'" >> ~/.bashrc && \
    echo "alias c='clear'" >> ~/.bashrc && \
    echo "alias py='python3'" >> ~/.bashrc && \
    echo "alias v='vim'" >> ~/.bashrc && \
    echo "alias ll='ls -la'" >> ~/.bashrc && \
    echo "alias duh='du -sh'" >> ~/.bashrc && \
    echo "alias rmd='sudo find . -name \".DS_Store\" -depth -exec rm {} \\;'" >> ~/.bashrc && \
    echo "\n# Alias Git" >> ~/.bashrc && \
    echo "alias gst='git status'" >> ~/.bashrc && \
    echo "alias gp='git pull'" >> ~/.bashrc && \
    echo "alias gpu='git push'" >> ~/.bashrc && \
    echo "alias gpo='git push origin'" >> ~/.bashrc && \
    echo "alias gcb='git checkout -b'" >> ~/.bashrc && \
    echo "alias gcm='git checkout main'" >> ~/.bashrc && \
    echo "alias gbd='git branch -D'" >> ~/.bashrc && \
    echo "alias gc='git commit -am'" >> ~/.bashrc && \
    echo "\n# Alias Kubernetes" >> ~/.bashrc && \
    echo "alias k='kubectl'" >> ~/.bashrc && \
    echo "alias g='get'" >> ~/.bashrc && \
    echo "\n# Alias Minikube" >> ~/.bashrc && \
    echo "alias mi='minikube'" >> ~/.bashrc && \
    echo "alias mis='minikube start'" >> ~/.bashrc && \
    echo "alias mist='minikube stop'" >> ~/.bashrc && \
    echo "alias mip='minikube profile'" >> ~/.bashrc

# Aplica los alias en cada inicio
RUN echo "source ~/.bashrc" >> ~/.bash_profile

# Ejecutar bash por defecto
CMD ["/bin/bash"]
