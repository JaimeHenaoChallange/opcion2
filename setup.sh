#!/bin/bash

# Colores para el output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Función para mostrar mensajes
show_success() { echo -e "\n${GREEN}✅ $1${NC}"; }
show_error() { echo -e "\n${RED}❌ $1${NC}"; }
show_process() { echo -e "\n${YELLOW}⏳ $1${NC}"; }
show_info() { echo -e "\n${YELLOW}ℹ️  $1${NC}"; }
show_separator() { echo -e "\n${GREEN}════════════════════════════════════════════${NC}"; }

# Función para manejar errores
handle_error() {
    local exit_code=$1
    local message="$2"
    if [ $exit_code -ne 0 ]; then
        show_error "$message"
        exit $exit_code
    fi
}

# Función para mostrar el banner de bienvenida
show_banner() {
    clear
    echo -e "${GREEN}"
    echo "███████╗████████╗███████╗██╗   ██╗██████╗ "
    echo "██╔════╝╚══██╔══╝██╔════╝██║   ██║██╔══██╗"
    echo "███████╗   ██║   █████╗  ██║   ██║██████╔╝"
    echo "╚════██║   ██║   ██╔══╝  ██║   ██║██╔═══╝ "
    echo "███████║   ██║   ███████╗╚██████╔╝██║     "
    echo "╚══════╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝     "
    echo "=========================================="
    echo "  Bienvenido al sistema de configuración  "
    echo "=========================================="
    echo -e "${NC}"
}

# Función para verificar conexión SSH con GitHub
check_ssh_connection() {
    show_process "Verificando conexión SSH con GitHub..."
    if ssh -T git@github.com 2>&1 | grep -q "success"; then
        show_success "Conexión SSH con GitHub verificada"
        return 0
    else
        show_error "No se pudo establecer conexión SSH con GitHub"
        return 1
    fi
}

# Función para configurar SSH
setup_ssh() {
    show_process "Configurando SSH..."
    if [ ! -f ~/.ssh/id_ed25519 ]; then
        echo -e "${YELLOW}Introduce tu email para generar la clave SSH:${NC}"
        read -r email
        if [[ -z "$email" ]]; then
            show_error "El email no puede estar vacío."
            return 1
        fi
        ssh-keygen -t ed25519 -C "$email" -f ~/.ssh/id_ed25519 -N ""
        handle_error $? "Error al generar la clave SSH."
        eval "$(ssh-agent -s)"
        ssh-add ~/.ssh/id_ed25519
        handle_error $? "Error al añadir la clave SSH al agente."
        show_success "Clave SSH generada correctamente. Añádela a GitHub:"
        cat ~/.ssh/id_ed25519.pub
    else
        show_info "Ya existe una clave SSH configurada."
    fi
}

# Función para verificar dependencias
check_dependencies() {
    show_process "Verificando dependencias..."
    local deps=("kubectl" "git" "argocd" "ssh")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            show_error "Dependencia faltante: $dep"
            return 1
        fi
    done
    show_success "Todas las dependencias están instaladas."
}

# Función para verificar conexión a Kubernetes
check_kubernetes() {
    show_process "Verificando conexión a Kubernetes..."
    if kubectl get nodes &>/dev/null; then
        show_success "Conexión a Kubernetes establecida."
    else
        show_error "No hay conexión con Kubernetes. Verifica que Minikube está corriendo."
        return 1
    fi
}

# Función para instalar el cliente de ArgoCD (argocd-cli)
install_argocd_cli() {
    show_process "Instalando el cliente de ArgoCD (argocd-cli)..."
    local version="v2.8.3" # Cambia la versión si es necesario
    curl -sSL -o /usr/local/bin/argocd "https://github.com/argoproj/argo-cd/releases/download/${version}/argocd-linux-amd64"
    chmod +x /usr/local/bin/argocd
    handle_error $? "Error al instalar el cliente de ArgoCD."
    show_success "Cliente de ArgoCD instalado correctamente."
}

# Función para configurar el port-forward de ArgoCD en segundo plano
start_argocd_port_forward() {
    show_process "Iniciando port-forward de ArgoCD en segundo plano..."
    kubectl port-forward svc/argocd-server -n argocd 8080:443 >/dev/null 2>&1 &
    local pid=$!
    echo $pid > /tmp/argocd_port_forward.pid
    show_success "Port-forward de ArgoCD iniciado en http://localhost:8080 (PID: $pid)"
}

# Función para detener el port-forward de ArgoCD
stop_argocd_port_forward() {
    if [ -f /tmp/argocd_port_forward.pid ]; then
        local pid
        pid=$(cat /tmp/argocd_port_forward.pid)
        show_process "Deteniendo port-forward de ArgoCD (PID: $pid)..."
        kill $pid && rm -f /tmp/argocd_port_forward.pid
        show_success "Port-forward de ArgoCD detenido."
    else
        show_info "No se encontró un port-forward activo para detener."
    fi
}

# Función para configurar ArgoCD
setup_argocd() {
    show_process "Configurando ArgoCD..."
    kubectl create namespace argocd 2>/dev/null || true
    handle_error $? "Error al crear el namespace de ArgoCD."
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    handle_error $? "Error al aplicar los manifiestos de ArgoCD."
    kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s
    handle_error $? "Error al esperar que los pods de ArgoCD estén listos."
    show_success "ArgoCD instalado/actualizado correctamente."
}

# Función para obtener la contraseña inicial de ArgoCD
get_argocd_password() {
    show_process "Obteniendo contraseña inicial de ArgoCD..."
    local password
    password=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    handle_error $? "Error al obtener la contraseña inicial de ArgoCD."
    show_success "Contraseña inicial de ArgoCD: $password"
}

# Función para sincronizar aplicaciones de ArgoCD
sync_argocd_apps() {
    show_process "Sincronizando aplicaciones de ArgoCD..."
    argocd app list -o name | xargs -I {} argocd app sync {}
    handle_error $? "Error al sincronizar las aplicaciones de ArgoCD."
    show_success "Todas las aplicaciones han sido sincronizadas."
}

# Menú principal
show_menu() {
    clear
    echo -e "${GREEN}=== Menú Principal ===${NC}"
    echo "1. GitHub"
    echo "2. ArgoCD"
    echo "3. Gestión Kubernetes y Sistema"
    echo "4. Salir"
    echo -e "${YELLOW}Selecciona una opción:${NC}"
}

# Submenú GitHub
show_github_menu() {
    clear
    echo -e "${GREEN}=== Menú GitHub ===${NC}"
    echo "1. Verificar/Configurar SSH"
    echo "2. Volver al Menú Principal"
    echo -e "${YELLOW}Selecciona una opción:${NC}"
}

# Submenú ArgoCD
show_argocd_menu() {
    clear
    echo -e "${GREEN}=== Menú ArgoCD ===${NC}"
    echo "1. Instalar/Actualizar ArgoCD"
    echo "2. Instalar cliente de ArgoCD (argocd-cli)"
    echo "3. Obtener contraseña inicial"
    echo "4. Sincronizar aplicaciones"
    echo "5. Iniciar port-forward de ArgoCD"
    echo "6. Detener port-forward de ArgoCD"
    echo "7. Volver al Menú Principal"
    echo -e "${YELLOW}Selecciona una opción:${NC}"
}

# Submenú Gestión Kubernetes y Sistema
show_kubernetes_menu() {
    clear
    echo -e "${GREEN}=== Menú Gestión Kubernetes y Sistema ===${NC}"
    echo "1. Verificar dependencias"
    echo "2. Verificar conexión a Kubernetes"
    echo "3. Volver al Menú Principal"
    echo -e "${YELLOW}Selecciona una opción:${NC}"
}

# Mostrar el banner de bienvenida
show_banner

# Loop principal
while true; do
    show_menu
    read -r opt
    case $opt in
        1)
            while true; do
                show_github_menu
                read -r github_opt
                case $github_opt in
                    1) setup_ssh ;;
                    2) break ;;
                    *) show_error "Opción inválida." ;;
                esac
                read -p "Presiona Enter para continuar..."
            done
            ;;
        2)
            while true; do
                show_argocd_menu
                read -r argocd_opt
                case $argocd_opt in
                    1) setup_argocd ;;
                    2) install_argocd_cli ;;
                    3) get_argocd_password ;;
                    4) sync_argocd_apps ;;
                    5) start_argocd_port_forward ;;
                    6) stop_argocd_port_forward ;;
                    7) break ;;
                    *) show_error "Opción inválida." ;;
                esac
                read -p "Presiona Enter para continuar..."
            done
            ;;
        3)
            while true; do
                show_kubernetes_menu
                read -r kubernetes_opt
                case $kubernetes_opt in
                    1) check_dependencies ;;
                    2) check_kubernetes ;;
                    3) break ;;
                    *) show_error "Opción inválida." ;;
                esac
                read -p "Presiona Enter para continuar..."
            done
            ;;
        4)
            show_success "¡Hasta luego!"
            exit 0
            ;;
        *)
            show_error "Opción inválida."
            read -p "Presiona Enter para continuar..."
            ;;
    esac
done