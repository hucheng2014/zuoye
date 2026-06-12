# ⚠️ LINUX-ONLY: This script formats ext4 partitions and uses systemd.
# It will NOT work on macOS. Kept for reference only.

#!/usr/bin/env bash
set -euo pipefail

DEVICE="/dev/nvme0n1p6"
DATA_MOUNT="/data"
OLD_NTFS_MOUNT="/media/jianglei/0E3D06E40E3D06E4"
USER_NAME="jianglei"
JIAOYI_SRC="/home/${USER_NAME}/jiaoyi"
JIAOYI_DST="${DATA_MOUNT}/jiaoyi"
DOCKER_DST="${DATA_MOUNT}/docker"
BACKUP_SUFFIX="$(date +%Y%m%d-%H%M%S)"

usage() {
  cat <<'EOF'
Usage:
  sudo /Users/xaa/zuoye/tools/migrate-jiaoyi-docker-to-data.sh --yes

This script:
  1. Erases /dev/nvme0n1p6 and formats it as ext4.
  2. Mounts it permanently at /data.
  3. Moves /Users/xaa/jiaoyi to /data/jiaoyi and creates a symlink.
  4. Migrates Docker root data to /data/docker if Docker is installed.

It only operates on /dev/nvme0n1p6 and exits if the partition does not match the
expected empty 46.6G NTFS partition.
EOF
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "==> $*"
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    exec sudo -- "$0" "$@"
  fi
}

require_yes() {
  if [[ "${1:-}" != "--yes" ]]; then
    usage
    die "Refusing to run without --yes because this formats ${DEVICE}."
  fi
}

check_device() {
  [[ -b "${DEVICE}" ]] || die "${DEVICE} is not a block device."

  local root_source
  root_source="$(findmnt -no SOURCE /)"
  [[ "${root_source}" != "${DEVICE}" ]] || die "${DEVICE} is mounted as root; refusing."

  local fstype size
  fstype="$(lsblk -no FSTYPE "${DEVICE}" | head -1)"
  size="$(lsblk -bno SIZE "${DEVICE}" | head -1)"

  [[ "${fstype}" == "ntfs" || "${fstype}" == "ntfs3" ]] || die "${DEVICE} is ${fstype:-unknown}, expected NTFS."

  # Expected partition is about 46.6 GiB. Accept a tight range to avoid formatting the wrong disk.
  if (( size < 49000000000 || size > 51000000000 )); then
    die "${DEVICE} size is ${size} bytes, expected about 50,000,000,000 bytes."
  fi

  local used_kb=0
  if findmnt -rn "${DEVICE}" >/dev/null; then
    used_kb="$(du -sk "${OLD_NTFS_MOUNT}" 2>/dev/null | awk '{print $1}')"
    if [[ -n "${used_kb}" ]] && (( used_kb > 102400 )); then
      die "${DEVICE} mount has more than 100MiB of data; inspect ${OLD_NTFS_MOUNT} first."
    fi
  fi
}

format_and_mount_data() {
  info "Unmounting ${DEVICE} if currently mounted"
  if findmnt -rn "${DEVICE}" >/dev/null; then
    umount "${DEVICE}"
  fi

  info "Formatting ${DEVICE} as ext4 label=linux-data"
  mkfs.ext4 -F -L linux-data "${DEVICE}"

  local uuid
  uuid="$(blkid -s UUID -o value "${DEVICE}")"
  [[ -n "${uuid}" ]] || die "Could not read UUID for ${DEVICE} after formatting."

  info "Creating ${DATA_MOUNT} and updating /etc/fstab"
  mkdir -p "${DATA_MOUNT}"
  cp -a /etc/fstab "/etc/fstab.backup.${BACKUP_SUFFIX}"
  grep -vE "[[:space:]]${DATA_MOUNT}[[:space:]]" /etc/fstab > "/etc/fstab.tmp.${BACKUP_SUFFIX}"
  cat >> "/etc/fstab.tmp.${BACKUP_SUFFIX}" <<EOF
UUID=${uuid} ${DATA_MOUNT} ext4 defaults,noatime 0 2
EOF
  mv "/etc/fstab.tmp.${BACKUP_SUFFIX}" /etc/fstab

  mount "${DATA_MOUNT}"
  chown "${USER_NAME}:${USER_NAME}" "${DATA_MOUNT}"
}

move_jiaoyi() {
  if [[ ! -d "${JIAOYI_SRC}" && ! -L "${JIAOYI_SRC}" ]]; then
    info "${JIAOYI_SRC} not found; skipping jiaoyi migration"
    return
  fi

  if [[ -L "${JIAOYI_SRC}" ]]; then
    info "${JIAOYI_SRC} is already a symlink; skipping jiaoyi migration"
    return
  fi

  info "Copying ${JIAOYI_SRC} to ${JIAOYI_DST}"
  mkdir -p "${JIAOYI_DST}"
  rsync -aHAX --info=progress2 "${JIAOYI_SRC}/" "${JIAOYI_DST}/"
  chown -R "${USER_NAME}:${USER_NAME}" "${JIAOYI_DST}"

  info "Replacing ${JIAOYI_SRC} with symlink to ${JIAOYI_DST}"
  mv "${JIAOYI_SRC}" "${JIAOYI_SRC}.migrated.${BACKUP_SUFFIX}"
  ln -s "${JIAOYI_DST}" "${JIAOYI_SRC}"
}

stop_docker_if_present() {
  if ! command -v docker >/dev/null 2>&1; then
    return 1
  fi

  if systemctl list-unit-files docker.service >/dev/null 2>&1; then
    info "Stopping Docker service"
    systemctl stop docker.socket 2>/dev/null || true
    systemctl stop docker.service 2>/dev/null || true
    return 0
  fi

  return 1
}

start_docker_if_present() {
  if systemctl list-unit-files docker.service >/dev/null 2>&1; then
    info "Starting Docker service"
    systemctl start docker.service 2>/dev/null || true
  fi
}

move_docker() {
  if [[ ! -d /var/lib/docker ]]; then
    info "/var/lib/docker not found; skipping Docker migration"
    return
  fi

  local stopped=0
  if stop_docker_if_present; then
    stopped=1
  else
    info "Docker service not managed by systemd or not installed; attempting offline data move only"
  fi

  mkdir -p "${DOCKER_DST}"

  if [[ -e "${DOCKER_DST}/.docker-migrated" ]]; then
    info "${DOCKER_DST} already marked migrated; skipping Docker data copy"
  else
    info "Copying /var/lib/docker to ${DOCKER_DST}"
    rsync -aHAX --numeric-ids --info=progress2 /var/lib/docker/ "${DOCKER_DST}/"
    touch "${DOCKER_DST}/.docker-migrated"
  fi

  info "Configuring Docker data-root=${DOCKER_DST}"
  mkdir -p /etc/docker
  if [[ -f /etc/docker/daemon.json ]]; then
    cp -a /etc/docker/daemon.json "/etc/docker/daemon.json.backup.${BACKUP_SUFFIX}"
    python3 - "${DOCKER_DST}" <<'PY'
import json
import sys
from pathlib import Path

path = Path("/etc/docker/daemon.json")
data_root = sys.argv[1]
try:
    data = json.loads(path.read_text())
except Exception:
    data = {}
data["data-root"] = data_root
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
PY
  else
    cat > /etc/docker/daemon.json <<EOF
{
  "data-root": "${DOCKER_DST}"
}
EOF
  fi

  if (( stopped == 1 )); then
    start_docker_if_present
    sleep 3
    docker info --format 'DockerRootDir={{.DockerRootDir}}' || true
  fi
}

final_report() {
  info "Final disk status"
  df -h / "${DATA_MOUNT}" || true
  echo
  ls -ld "${DATA_MOUNT}" "${JIAOYI_SRC}" "${JIAOYI_DST}" 2>/dev/null || true
  echo
  echo "Old jiaoyi backup, if migration succeeded:"
  ls -ld "${JIAOYI_SRC}.migrated."* 2>/dev/null || true
  echo
  echo "After verifying everything works, you may remove the backup with:"
  echo "  sudo rm -rf ${JIAOYI_SRC}.migrated.${BACKUP_SUFFIX}"
}

main() {
  require_root "$@"
  require_yes "${1:-}"
  check_device
  format_and_mount_data
  move_jiaoyi
  move_docker
  final_report
}

main "$@"
