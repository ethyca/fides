#!/usr/bin/env bash
set -euo pipefail

# Dockerless environment bootstrapper for Fides.
# - Verifies required tooling is available
# - Installs PostgreSQL + Redis binaries when possible
# - Adjusts PATH for the current shell and offers guidance for persistence

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ADDED_PATHS=()
INFO_MESSAGES=()
CONDA_ENV_NAME="fides"
CONDA_REQUIRED_PYTHON="3.10"
CONDA_EXECUTABLE=""
CONDA_ENV_READY=false

command_in_path() {
  command -v "$1" >/dev/null 2>&1
}

add_path_if_needed() {
  local dir="$1"
  if [ -d "$dir" ] && [[ ":$PATH:" != *":$dir:"* ]]; then
    export PATH="$dir:$PATH"
    ADDED_PATHS+=("$dir")
  fi
}

detect_python_command() {
  local python_cmd
  if command_in_path python; then
    python_cmd="python"
  elif command_in_path python3; then
    python_cmd="python3"
  else
    python_cmd=""
  fi
  printf '%s' "$python_cmd"
}

detect_conda_candidate() {
  local candidate
  for candidate in \
    "$HOME/miniconda3/bin/conda" \
    "$HOME/miniconda3/condabin/conda" \
    "$HOME/anaconda3/bin/conda" \
    "$HOME/anaconda3/condabin/conda"; do
    if [ -x "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

download_conda_installer() {
  local url="$1"
  local destination="$2"
  if command_in_path curl; then
    curl -fsSL "$url" -o "$destination"
    return $?
  fi
  if command_in_path wget; then
    wget -qO "$destination" "$url"
    return $?
  fi
  INFO_MESSAGES+=("Install curl or wget to download Miniconda automatically.")
  return 1
}

install_conda() {
  local installer_url=""
  local installer_tmp
  local installer_path
  installer_tmp="$(mktemp -t fides_conda_installer.XXXXXXXXXX)"
  installer_path="${installer_tmp}.sh"
  mv "$installer_tmp" "$installer_path"

  case "$OS_NAME" in
    Linux)
      case "$ARCH" in
        aarch64|arm64)
          installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh"
          ;;
        *)
          installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
          ;;
      esac
      ;;
    Darwin)
      case "$ARCH" in
        arm64)
          installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-arm64.sh"
          ;;
        *)
          installer_url="https://repo.anaconda.com/miniconda/Miniconda3-latest-MacOSX-x86_64.sh"
          ;;
      esac
      ;;
    *)
      INFO_MESSAGES+=("Unsupported OS for automatic Miniconda install. Install Conda manually.")
      return 1
      ;;
  esac

  if ! download_conda_installer "$installer_url" "$installer_path"; then
    INFO_MESSAGES+=("Failed to download Miniconda installer from $installer_url. Install Conda manually.")
    return 1
  fi

  chmod +x "$installer_path"
  if ! "$installer_path" -b -p "$HOME/miniconda3" >/dev/null; then
    INFO_MESSAGES+=("Miniconda installer failed. See $installer_path for debugging and install manually.")
    return 1
  fi

  add_path_if_needed "$HOME/miniconda3/bin"
  CONDA_EXECUTABLE="$HOME/miniconda3/bin/conda"
  rm -f "$installer_path"
  return 0
}

ensure_conda() {
  if [ -n "$CONDA_EXECUTABLE" ] && [ -x "$CONDA_EXECUTABLE" ]; then
    return 0
  fi

  if command_in_path conda; then
    CONDA_EXECUTABLE="$(command -v conda)"
    return 0
  fi

  if CONDA_EXECUTABLE="$(detect_conda_candidate)"; then
    add_path_if_needed "$(dirname "$CONDA_EXECUTABLE")"
    return 0
  fi

  echo "Conda not found; installing Miniconda..."
  if install_conda; then
    return 0
  fi

  INFO_MESSAGES+=("Conda is required. Install Miniconda manually (expected at ~/miniconda3).")
  return 1
}

ensure_conda_env() {
  if ! ensure_conda; then
    return 1
  fi

  local conda_hook
  if ! conda_hook="$("$CONDA_EXECUTABLE" shell.bash hook 2>/dev/null)"; then
    INFO_MESSAGES+=("Unable to load Conda shell integration from $CONDA_EXECUTABLE.")
    return 1
  fi

  eval "$conda_hook"

  local conda_base
  if ! conda_base="$($CONDA_EXECUTABLE info --base 2>/dev/null)"; then
    INFO_MESSAGES+=("Unable to determine Conda base path.")
    return 1
  fi

  export CONDA_BASE="$conda_base"

  if ! conda env list | awk '!/^#/ {print $1}' | grep -qx "$CONDA_ENV_NAME"; then
    echo "Creating Conda environment '$CONDA_ENV_NAME' (python=$CONDA_REQUIRED_PYTHON)..."
    if ! conda create -y -n "$CONDA_ENV_NAME" "python=$CONDA_REQUIRED_PYTHON"; then
      INFO_MESSAGES+=("Failed to create Conda env '$CONDA_ENV_NAME'. Create it manually.")
      return 1
    fi
  fi

  echo "Activating Conda environment '$CONDA_ENV_NAME'..."
  if ! conda activate "$CONDA_ENV_NAME"; then
    INFO_MESSAGES+=("Failed to activate Conda env '$CONDA_ENV_NAME'. Activate manually with 'conda activate $CONDA_ENV_NAME'.")
    return 1
  fi

  CONDA_ENV_READY=true
  return 0
}

maybe_enter_conda_shell() {
  if [ "$CONDA_ENV_READY" != true ]; then
    return
  fi
  if [ -n "${CI:-}" ]; then
    return
  fi
  if [ ! -t 1 ]; then
    return
  fi
  if [ "${BASH_SOURCE[0]}" != "$0" ]; then
    return
  fi

  if [ -z "${CONDA_BASE:-}" ]; then
    return
  fi

  echo
  echo "Launching an interactive shell with '$CONDA_ENV_NAME' activated. Exit the shell to return." 
  local temp_rc
  temp_rc="$(mktemp)"
  cat >"$temp_rc" <<EOF
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV_NAME"
trap 'rm -f "$temp_rc"' EXIT
EOF

  exec "${SHELL:-/bin/bash}" --rcfile "$temp_rc" -i
}

ensure_path_hints() {
  local label="$1"
  shift || true
  local pattern
  shopt -s nullglob
  for pattern in "$@"; do
    for candidate in $pattern; do
      if [ -x "$candidate/$label" ]; then
        add_path_if_needed "$candidate"
      fi
    done
  done
  shopt -u nullglob
}

ensure_pip() {
  local python_cmd
  python_cmd="$(detect_python_command)"

  if [ -z "$python_cmd" ]; then
    INFO_MESSAGES+=("python3 not found; install Python 3 or activate the Conda environment manually.")
    return 1
  fi

  if "$python_cmd" -m pip --version >/dev/null 2>&1 || command_in_path pip3; then
    if [ "$CONDA_ENV_READY" = false ]; then
      add_path_if_needed "$HOME/.local/bin"
    fi
    return 0
  fi

  echo "Bootstrapping pip via $python_cmd..."
  if "$python_cmd" -m ensurepip --upgrade >/dev/null 2>&1; then
    if [ "$CONDA_ENV_READY" = false ]; then
      add_path_if_needed "$HOME/.local/bin"
    fi
    return 0
  fi

  if [ -n "$PACKAGE_MANAGER" ] && [ "$CONDA_ENV_READY" = false ]; then
    case "$PACKAGE_MANAGER" in
      apt)
        sudo apt-get update >/dev/null 2>&1 || true
        sudo apt-get install -y python3-pip >/dev/null 2>&1 || true
        ;;
      dnf)
        sudo dnf install -y python3-pip >/dev/null 2>&1 || true
        ;;
      yum)
        sudo yum install -y python3-pip >/dev/null 2>&1 || true
        ;;
      brew)
        brew install python >/dev/null 2>&1 || true
        ;;
    esac
    if "$python_cmd" -m pip --version >/dev/null 2>&1 || command_in_path pip3; then
      add_path_if_needed "$HOME/.local/bin"
      return 0
    fi
  fi

  INFO_MESSAGES+=("Failed to bootstrap pip; install python3-pip manually or ensure the Conda environment provides pip.")
  return 1
}

install_python_packages() {
  if [ $# -eq 0 ]; then
    return 0
  fi
  if ensure_pip; then
    local python_cmd
    python_cmd="$(detect_python_command)"
    if [ -z "$python_cmd" ]; then
      INFO_MESSAGES+=("Cannot install Python packages because no python executable is available.")
      return 1
    fi
    echo "Installing Python packages: $*"
    if [ "$CONDA_ENV_READY" = true ]; then
      if ! "$python_cmd" -m pip install "$@"; then
        INFO_MESSAGES+=("Failed to install Python packages into Conda env: $* (try running manually).")
      fi
    else
      if ! "$python_cmd" -m pip install --user "$@"; then
        INFO_MESSAGES+=("Failed to install Python packages: $* (try running manually).")
      fi
    fi
  fi
}

OS_NAME="$(uname -s)"
ARCH="$(uname -m)"
PACKAGE_MANAGER=""
INSTALL_POSTGRES_CMD=""
INSTALL_REDIS_CMD=""

case "$OS_NAME" in
  Linux)
    if command_in_path apt-get; then
      PACKAGE_MANAGER="apt"
      INSTALL_POSTGRES_CMD="sudo apt-get update && sudo apt-get install -y postgresql"
      INSTALL_REDIS_CMD="sudo apt-get update && sudo apt-get install -y redis-server"
    elif command_in_path dnf; then
      PACKAGE_MANAGER="dnf"
      INSTALL_POSTGRES_CMD="sudo dnf install -y postgresql-server"
      INSTALL_REDIS_CMD="sudo dnf install -y redis"
    elif command_in_path yum; then
      PACKAGE_MANAGER="yum"
      INSTALL_POSTGRES_CMD="sudo yum install -y postgresql-server"
      INSTALL_REDIS_CMD="sudo yum install -y redis"
    fi
    ;;
  Darwin)
    if command_in_path brew; then
      PACKAGE_MANAGER="brew"
      INSTALL_POSTGRES_CMD="brew install postgresql@14"
      INSTALL_REDIS_CMD="brew install redis"
    fi
    ;;
esac

if ensure_conda_env; then
  :
else
  INFO_MESSAGES+=("Conda environment '$CONDA_ENV_NAME' is not active for this shell. Install or activate it manually if needed.")
fi

MISSING_POSTGRES_CMDS=()
for pg_cmd in initdb pg_ctl pg_isready psql; do
  if ! command_in_path "$pg_cmd"; then
    MISSING_POSTGRES_CMDS+=("$pg_cmd")
  fi

done

MISSING_REDIS_CMDS=()
if ! command_in_path redis-server; then
  MISSING_REDIS_CMDS+=("redis-server")
fi

MISSING_EXTRA_CMDS=()
for extra_cmd in uvicorn fides; do
  if ! command_in_path "$extra_cmd"; then
    MISSING_EXTRA_CMDS+=("$extra_cmd")
  fi

done

if [ ${#MISSING_POSTGRES_CMDS[@]} -gt 0 ]; then
  echo "PostgreSQL utilities missing: ${MISSING_POSTGRES_CMDS[*]}"
  if [ -n "$PACKAGE_MANAGER" ]; then
    echo "Installing PostgreSQL via $PACKAGE_MANAGER..."
    if [ -n "$INSTALL_POSTGRES_CMD" ]; then
      bash -lc "$INSTALL_POSTGRES_CMD"
    fi
  else
    INFO_MESSAGES+=("Install PostgreSQL manually (missing: ${MISSING_POSTGRES_CMDS[*]}).")
  fi
fi

if [ ${#MISSING_REDIS_CMDS[@]} -gt 0 ]; then
  echo "redis-server missing"
  if [ -n "$PACKAGE_MANAGER" ]; then
    echo "Installing Redis via $PACKAGE_MANAGER..."
    if [ -n "$INSTALL_REDIS_CMD" ]; then
      bash -lc "$INSTALL_REDIS_CMD"
    fi
  else
    INFO_MESSAGES+=("Install Redis manually (missing: ${MISSING_REDIS_CMDS[*]}).")
  fi
fi

# Ensure common PostgreSQL binary directories are considered for PATH
ensure_path_hints initdb \
  /usr/lib/postgresql/*/bin \
  /usr/local/opt/postgresql/bin \
  /usr/local/opt/postgresql@14/bin \
  /opt/homebrew/opt/postgresql/bin \
  /opt/homebrew/opt/postgresql@14/bin

# Re-check after attempted install
MISSING_POSTGRES_CMDS=()
for pg_cmd in initdb pg_ctl pg_isready psql; do
  if ! command_in_path "$pg_cmd"; then
    MISSING_POSTGRES_CMDS+=("$pg_cmd")
  fi

done

if [ ${#MISSING_POSTGRES_CMDS[@]} -gt 0 ]; then
  INFO_MESSAGES+=("Still missing PostgreSQL utilities: ${MISSING_POSTGRES_CMDS[*]}.")
fi

if ! command_in_path redis-server; then
  INFO_MESSAGES+=("redis-server still missing after attempted install.")
fi

PYTHON_PACKAGES=()
NEED_FIDES_INSTALL=false
if declare -p MISSING_EXTRA_CMDS >/dev/null 2>&1; then
  for missing in "${MISSING_EXTRA_CMDS[@]:-}"; do
    case "$missing" in
      uvicorn)
        PYTHON_PACKAGES+=("uvicorn")
        ;;
      fides)
        NEED_FIDES_INSTALL=true
        ;;
    esac
  done
fi

if [ ${#PYTHON_PACKAGES[@]} -gt 0 ]; then
  install_python_packages "${PYTHON_PACKAGES[@]}"
fi

if [ "$NEED_FIDES_INSTALL" = true ]; then
  echo "Installing Fides CLI from local source..."
  if ensure_pip; then
    if ! python3 -m pip install --user -e "$PROJECT_ROOT"; then
      INFO_MESSAGES+=("Failed to install local Fides CLI; activate your environment manually and rerun.")
    else
      add_path_if_needed "$HOME/.local/bin"
    fi
  fi
fi

# Re-check extra commands after attempted installs
MISSING_EXTRA_CMDS=()
for extra_cmd in uvicorn fides; do
  if ! command_in_path "$extra_cmd"; then
    MISSING_EXTRA_CMDS+=("$extra_cmd")
  fi
done

if declare -p MISSING_EXTRA_CMDS >/dev/null 2>&1 && [ ${#MISSING_EXTRA_CMDS[@]:-0} -gt 0 ]; then
  INFO_MESSAGES+=("Still missing CLI commands: ${MISSING_EXTRA_CMDS[*]}. Install them manually or activate the appropriate environment.")
fi

if [ ${#ADDED_PATHS[@]} -gt 0 ]; then
  echo "Added to PATH for this shell: ${ADDED_PATHS[*]}"
  INFO_MESSAGES+=("Persist PATH updates by adding export lines for the directories above to your shell profile.")
fi

echo
if [ ${#INFO_MESSAGES[@]} -gt 0 ]; then
  echo "Next steps:"
  for msg in "${INFO_MESSAGES[@]}"; do
    echo " - $msg"
  done
else
  echo "All required commands are available. You're ready to run dockerless/dev.sh."
fi

maybe_enter_conda_shell
